"""
app.py — ChurnWatch: Customer Retention Intelligence
Streamlit web application with executive dashboard, customer drilldown,
and IBM watsonx.ai pilot section.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from data import generate_synthetic_data, load_and_validate_csv, REQUIRED_COLUMNS
from scoring import score_customers
from recommendations import get_recommendations

# ---------------------------------------------------------------------------
# Page config — must be first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ChurnWatch — Customer Retention Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — IBM-inspired enterprise styling
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* Import font */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Header bar */
.churnwatch-header {
    background: linear-gradient(135deg, #0F62FE 0%, #0043CE 100%);
    color: white;
    padding: 1.5rem 2rem;
    border-radius: 8px;
    margin-bottom: 1.5rem;
}
.churnwatch-header h1 {
    margin: 0;
    font-size: 1.8rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: white;
}
.churnwatch-header p {
    margin: 0.3rem 0 0 0;
    font-size: 0.95rem;
    opacity: 0.85;
    color: white;
}

/* KPI cards */
.kpi-card {
    background: #f4f4f4;
    border-left: 4px solid #0F62FE;
    border-radius: 6px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
}
.kpi-card.danger { border-left-color: #da1e28; }
.kpi-card.warning { border-left-color: #f1c21b; }
.kpi-card.success { border-left-color: #24a148; }

/* Risk level badges */
.badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.03em;
}
.badge-high   { background: #ffd7d9; color: #da1e28; }
.badge-medium { background: #fef3cd; color: #9e4a00; }
.badge-low    { background: #defbe6; color: #0e6027; }

/* Score circle */
.score-display {
    text-align: center;
    padding: 1rem;
}
.score-number {
    font-size: 3.5rem;
    font-weight: 700;
    line-height: 1;
}
.score-high   { color: #da1e28; }
.score-medium { color: #f1c21b; }
.score-low    { color: #24a148; }

/* Factor row */
.factor-row {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.6rem 0.8rem;
    background: #f9f9f9;
    border-radius: 6px;
    margin-bottom: 0.4rem;
    border-left: 3px solid #0F62FE;
}
.factor-contribution {
    font-weight: 700;
    font-size: 0.85rem;
    min-width: 40px;
    text-align: right;
}
.factor-detail { font-size: 0.9rem; color: #393939; }

/* Recommendation card */
.rec-card {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.75rem;
}
.rec-action {
    font-weight: 600;
    color: #0043CE;
    font-size: 0.95rem;
    margin-bottom: 0.3rem;
}
.rec-rationale {
    font-size: 0.88rem;
    color: #525252;
    line-height: 1.5;
}

/* Pilot section */
.pilot-banner {
    background: #edf5ff;
    border: 1px solid #0F62FE;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
}
.pilot-badge {
    display: inline-block;
    background: #0F62FE;
    color: white;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 0.15rem 0.5rem;
    border-radius: 3px;
    letter-spacing: 0.08em;
    margin-bottom: 0.5rem;
}
.pilot-rec-card {
    background: #f0f4ff;
    border: 1px solid #a6c8ff;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.75rem;
    position: relative;
}

/* Section divider */
.section-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #161616;
    border-bottom: 2px solid #e0e0e0;
    padding-bottom: 0.4rem;
    margin-bottom: 1rem;
}

/* Disclaimer box */
.disclaimer {
    background: #f4f4f4;
    border-radius: 6px;
    padding: 0.8rem 1rem;
    font-size: 0.82rem;
    color: #6f6f6f;
    line-height: 1.5;
}

/* Hide Streamlit default elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "df_scored" not in st.session_state:
    st.session_state.df_scored = None
if "watsonx_connected" not in st.session_state:
    st.session_state.watsonx_connected = False
if "watsonx_api_key" not in st.session_state:
    st.session_state.watsonx_api_key = ""
if "watsonx_project_id" not in st.session_state:
    st.session_state.watsonx_project_id = ""
if "show_watsonx_form" not in st.session_state:
    st.session_state.show_watsonx_form = False

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="churnwatch-header">
    <h1>📊 ChurnWatch</h1>
    <p>Customer Retention Intelligence &nbsp;·&nbsp; Heuristic Risk Analysis &nbsp;·&nbsp; IBM Bobathon 2026</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📊 ChurnWatch")
    st.markdown("*Customer Retention Intelligence*")
    st.divider()

    st.markdown("### Load Data")

    if st.button("🗂️ Load Sample Dataset", use_container_width=True, type="primary"):
        with st.spinner("Generating synthetic customer data..."):
            raw_df = generate_synthetic_data(n=100, seed=42)
            st.session_state.df_scored = score_customers(raw_df)
        st.success("✅ 100 customers loaded and scored.")

    st.markdown("**— or —**")

    uploaded_file = st.file_uploader(
        "Upload CSV",
        type=["csv"],
        help=f"Required columns: {', '.join(REQUIRED_COLUMNS)}",
    )
    if uploaded_file is not None:
        try:
            with st.spinner("Validating and scoring uploaded data..."):
                raw_df = load_and_validate_csv(uploaded_file)
                st.session_state.df_scored = score_customers(raw_df)
            st.success(f"✅ {len(st.session_state.df_scored)} customers loaded.")
        except ValueError as e:
            st.error(str(e))

    st.divider()

    # Filters — only show when data is loaded
    if st.session_state.df_scored is not None:
        st.markdown("### Filters")
        risk_filter = st.selectbox(
            "Risk Level",
            options=["All", "High", "Medium", "Low"],
            index=0,
        )
        segment_filter = st.selectbox(
            "Segment",
            options=["All"] + sorted(st.session_state.df_scored["segment"].unique().tolist()),
            index=0,
        )
    else:
        risk_filter = "All"
        segment_filter = "All"

    st.divider()
    st.markdown("### 🤖 watsonx.ai")
    if st.session_state.watsonx_connected:
        st.success("Connected (Pilot Mode)")
        if st.button("Disconnect", use_container_width=True):
            st.session_state.watsonx_connected = False
            st.session_state.watsonx_api_key = ""
            st.session_state.watsonx_project_id = ""
            st.session_state.show_watsonx_form = False
            st.rerun()
    else:
        if st.button("Connect watsonx.ai →", use_container_width=True):
            st.session_state.show_watsonx_form = not st.session_state.show_watsonx_form
            st.rerun()

        if st.session_state.show_watsonx_form:
            with st.form("watsonx_form"):
                api_key = st.text_input("API Key", type="password", placeholder="Enter watsonx.ai API key")
                project_id = st.text_input("Project ID", placeholder="Enter Project ID")
                submitted = st.form_submit_button("Connect", use_container_width=True)
                if submitted:
                    if api_key and project_id:
                        st.session_state.watsonx_api_key = api_key
                        st.session_state.watsonx_project_id = project_id
                        st.session_state.watsonx_connected = True
                        st.session_state.show_watsonx_form = False
                        st.rerun()
                    else:
                        st.warning("Please enter both API Key and Project ID.")

    st.divider()
    st.caption("Built at IBM Bobathon · ASU Polytechnic · Nov 2026")

# ---------------------------------------------------------------------------
# Main content — requires data to be loaded
# ---------------------------------------------------------------------------
if st.session_state.df_scored is None:
    st.markdown("""
    <div style="text-align:center; padding: 4rem 2rem; color: #6f6f6f;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">👈</div>
        <h3 style="color: #393939;">Load a dataset to get started</h3>
        <p>Click <strong>Load Sample Dataset</strong> in the sidebar to see ChurnWatch in action,<br>
        or upload your own CSV with customer engagement metrics.</p>
        <br>
        <div style="background:#f4f4f4; border-radius:8px; padding:1rem; display:inline-block; text-align:left; font-size:0.85rem;">
            <strong>Required CSV columns:</strong><br>
            <code>customer_id, segment, days_since_last_activity,<br>
            engagement_change_30d, purchase_frequency,<br>
            tenure_months, unresolved_tickets, monthly_revenue</code>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------
df = st.session_state.df_scored.copy()

if risk_filter != "All":
    df = df[df["risk_level"] == risk_filter]
if segment_filter != "All":
    df = df[df["segment"] == segment_filter]

full_df = st.session_state.df_scored  # unfiltered, for KPI calculations

# ---------------------------------------------------------------------------
# KPI Cards — always reflect active filters
# ---------------------------------------------------------------------------
total = len(df)
total_portfolio = len(full_df)
high_df = df[df["risk_level"] == "High"]
medium_df = df[df["risk_level"] == "Medium"]
n_high = len(high_df)
n_medium = len(medium_df)
pct_high = (n_high / total * 100) if total > 0 else 0
revenue_at_risk = high_df["monthly_revenue"].sum()

# Show a filter-active notice when filters are applied
filter_active = risk_filter != "All" or segment_filter != "All"
if filter_active:
    active_filters = []
    if risk_filter != "All":
        active_filters.append(f"Risk: **{risk_filter}**")
    if segment_filter != "All":
        active_filters.append(f"Segment: **{segment_filter}**")
    st.info(
        f"🔍 Filters active — {' · '.join(active_filters)} · "
        f"Showing {total} of {total_portfolio} customers",
        icon=None,
    )

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Customers in View",
        value=f"{total:,}",
        delta=f"of {total_portfolio} total" if filter_active else "Total analyzed",
        delta_color="off",
    )
with col2:
    st.metric(
        label="🔴 High-Risk Customers",
        value=f"{n_high}",
        delta=f"{pct_high:.1f}% of view",
        delta_color="inverse",
    )
with col3:
    st.metric(
        label="💰 Monthly Revenue at Risk",
        value=f"${revenue_at_risk:,.0f}",
        delta="High-risk in current view",
        delta_color="inverse",
    )
with col4:
    st.metric(
        label="🟡 Medium-Risk Customers",
        value=f"{n_medium}",
        delta=f"{n_medium / total * 100:.1f}% of view" if total > 0 else "0%",
        delta_color="off",
    )

st.divider()

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown('<div class="section-title">Risk Distribution</div>', unsafe_allow_html=True)

    risk_counts = df["risk_level"].value_counts().reindex(["High", "Medium", "Low"], fill_value=0)
    colors = {"High": "#da1e28", "Medium": "#f1c21b", "Low": "#24a148"}

    fig_donut = go.Figure(data=[go.Pie(
        labels=risk_counts.index.tolist(),
        values=risk_counts.values.tolist(),
        hole=0.55,
        marker_colors=[colors[l] for l in risk_counts.index],
        textinfo="label+percent",
        textfont_size=13,
        hovertemplate="<b>%{label}</b><br>Customers: %{value}<br>Share: %{percent}<extra></extra>",
    )])
    fig_donut.update_layout(
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        height=280,
        paper_bgcolor="white",
        annotations=[dict(
            text=f"<b>{total}</b><br>customers",
            x=0.5, y=0.5,
            font_size=14,
            showarrow=False,
        )],
    )
    st.plotly_chart(fig_donut, use_container_width=True)

with chart_col2:
    st.markdown('<div class="section-title">Risk by Segment</div>', unsafe_allow_html=True)

    seg_risk = (
        df.groupby(["segment", "risk_level"])
        .size()
        .reset_index(name="count")
    )

    fig_bar = px.bar(
        seg_risk,
        x="segment",
        y="count",
        color="risk_level",
        color_discrete_map={"High": "#da1e28", "Medium": "#f1c21b", "Low": "#24a148"},
        barmode="group",
        labels={"count": "Customers", "segment": "Segment", "risk_level": "Risk Level"},
        category_orders={"risk_level": ["High", "Medium", "Low"]},
    )
    fig_bar.update_layout(
        height=280,
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend_title_text="Risk Level",
        xaxis=dict(gridcolor="#f4f4f4"),
        yaxis=dict(gridcolor="#f4f4f4"),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Customer Table
# ---------------------------------------------------------------------------
st.markdown('<div class="section-title">Customer Risk Table</div>', unsafe_allow_html=True)

display_df = df[[
    "customer_id", "segment", "tenure_months",
    "monthly_revenue", "risk_score", "risk_level",
]].sort_values("risk_score", ascending=False).copy()

display_df["monthly_revenue"] = display_df["monthly_revenue"].apply(lambda x: f"${x:,.0f}")
display_df.columns = [
    "Customer ID", "Segment", "Tenure (mo.)", "Monthly Revenue", "Risk Score", "Risk Level"
]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    height=300,
    column_config={
        "Risk Score": st.column_config.ProgressColumn(
            "Risk Score",
            min_value=0,
            max_value=100,
            format="%d",
        ),
    },
)

st.caption(f"Showing {len(df)} of {total} customers · Sorted by risk score (highest first)")

st.divider()

# ---------------------------------------------------------------------------
# Customer Drilldown
# ---------------------------------------------------------------------------
st.markdown('<div class="section-title">Customer Drilldown</div>', unsafe_allow_html=True)

sorted_ids = (
    full_df.sort_values("risk_score", ascending=False)["customer_id"].tolist()
)

selected_id = st.selectbox(
    "Select a customer to inspect",
    options=sorted_ids,
    format_func=lambda cid: (
        f"{cid} — "
        + full_df[full_df['customer_id'] == cid]['risk_level'].values[0]
        + f" Risk (Score: {full_df[full_df['customer_id'] == cid]['risk_score'].values[0]})"
    ),
)

if selected_id:
    customer = full_df[full_df["customer_id"] == selected_id].iloc[0]
    risk_factors = customer["risk_factors"]
    recommendations = get_recommendations(customer, risk_factors)

    level = customer["risk_level"]
    score = customer["risk_score"]
    score_color_class = f"score-{level.lower()}"
    badge_class = f"badge-{level.lower()}"
    level_color = {"High": "#da1e28", "Medium": "#f1c21b", "Low": "#24a148"}[level]

    dd_col1, dd_col2 = st.columns([1, 2])

    with dd_col1:
        st.markdown(f"""
        <div style="background:#f9f9f9; border-radius:10px; padding:1.5rem; text-align:center;">
            <div style="font-size:0.85rem; color:#6f6f6f; margin-bottom:0.5rem;">HEURISTIC RISK SCORE</div>
            <div class="score-number {score_color_class}" style="font-size:4rem; font-weight:700; color:{level_color};">{score}</div>
            <div style="margin:0.5rem 0;">
                <span class="badge {badge_class}">{level} Risk</span>
            </div>
            <hr style="border-color:#e0e0e0; margin:1rem 0;">
            <div style="font-size:0.82rem; color:#525252; text-align:left;">
                <b>Segment:</b> {customer['segment']}<br>
                <b>Tenure:</b> {customer['tenure_months']} months<br>
                <b>Monthly Revenue:</b> ${customer['monthly_revenue']:,.0f}<br>
                <b>Days Inactive:</b> {customer['days_since_last_activity']}<br>
                <b>Engagement Δ30d:</b> {customer['engagement_change_30d']*100:+.1f}%<br>
                <b>Purchases/mo:</b> {customer['purchase_frequency']:.2f}<br>
                <b>Open Tickets:</b> {customer['unresolved_tickets']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with dd_col2:
        st.markdown("**Contributing Risk Factors**")
        if risk_factors:
            positive_factors = [f for f in risk_factors if f["contribution"] > 0]
            buffer_factors = [f for f in risk_factors if f["contribution"] < 0]

            for f in positive_factors:
                contrib = f["contribution"]
                contrib_color = "#da1e28" if contrib >= 20 else "#f1c21b" if contrib >= 10 else "#6f6f6f"
                st.markdown(f"""
                <div class="factor-row">
                    <span class="factor-contribution" style="color:{contrib_color};">+{contrib}</span>
                    <span class="factor-detail">{f['detail']}</span>
                </div>
                """, unsafe_allow_html=True)

            for f in buffer_factors:
                st.markdown(f"""
                <div class="factor-row" style="border-left-color:#24a148;">
                    <span class="factor-contribution" style="color:#24a148;">{f['contribution']}</span>
                    <span class="factor-detail">{f['detail']}</span>
                </div>
                """, unsafe_allow_html=True)

            total_pts = sum(f["contribution"] for f in positive_factors)
            buffer_pts = sum(f["contribution"] for f in buffer_factors)
            st.caption(
                f"Risk signals: +{total_pts} pts · Loyalty buffer: {buffer_pts} pts · "
                f"Net heuristic score: **{score}**"
            )
        else:
            st.success("No risk signals detected for this customer.")

        st.markdown("**Recommended Retention Actions**")
        for rec in recommendations:
            st.markdown(f"""
            <div class="rec-card">
                <div class="rec-action">▶ {rec['action']}</div>
                <div class="rec-rationale">{rec['rationale']}</div>
            </div>
            """, unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------------------------
# watsonx.ai Pilot Section
# ---------------------------------------------------------------------------
st.markdown('<div class="section-title">🤖 AI-Powered Recommendations (Pilot)</div>', unsafe_allow_html=True)

st.markdown("""
<div class="pilot-banner">
    <span class="pilot-badge">PILOT MODE</span>
    <p style="margin:0; font-size:0.9rem; color:#0043CE;">
        <strong>This section is designed to connect to IBM watsonx.ai foundation models.</strong><br>
        In pilot mode, rule-based recommendations are displayed below as a preview of what AI-generated
        retention recommendations would look like. To enable generative AI recommendations,
        configure your watsonx.ai API credentials using the <em>Connect watsonx.ai</em> button in the sidebar.
    </p>
</div>
""", unsafe_allow_html=True)

if selected_id:
    st.markdown(f"**AI Pilot Recommendations for `{selected_id}`**")
    if st.session_state.watsonx_connected:
        st.info(
            "watsonx.ai credentials configured. In a full integration, a foundation model "
            "would generate personalized narrative recommendations here based on this customer's profile.",
            icon="ℹ️",
        )

    for i, rec in enumerate(recommendations, 1):
        st.markdown(f"""
        <div class="pilot-rec-card">
            <span class="pilot-badge">PILOT RECOMMENDATION {i}</span>
            <div class="rec-action" style="margin-top:0.4rem;">▶ {rec['action']}</div>
            <div class="rec-rationale">{rec['rationale']}</div>
        </div>
        """, unsafe_allow_html=True)

    if not st.session_state.watsonx_connected:
        col_btn, _ = st.columns([1, 3])
        with col_btn:
            if st.button("🔗 Connect watsonx.ai to Unlock AI Recommendations", use_container_width=True):
                st.session_state.show_watsonx_form = True
                st.rerun()
else:
    st.info("Select a customer above to see AI pilot recommendations.", icon="👆")

st.divider()

# ---------------------------------------------------------------------------
# About / Disclaimer footer
# ---------------------------------------------------------------------------
with st.expander("ℹ️ About ChurnWatch & Scoring Disclaimer"):
    st.markdown("""
    **ChurnWatch** is a heuristic customer retention intelligence tool built to help customer success
    teams identify and prioritize at-risk accounts.

    #### How Risk Scoring Works
    ChurnWatch applies a transparent, rule-based scoring formula that evaluates each customer across
    five observable behavioral signals:

    | Signal | High-Risk Condition | Points |
    |---|---|---|
    | Days since last activity | > 60 days | +30 |
    | Days since last activity | 30–60 days | +15 |
    | Engagement change (30d) | Decline > 30% | +25 |
    | Engagement change (30d) | Decline 10–30% | +12 |
    | Purchase frequency | < 1/month | +20 |
    | Unresolved support tickets | ≥ 3 tickets | +15 |
    | Unresolved support tickets | 1–2 tickets | +8 |
    | Tenure (loyalty buffer) | > 24 months | −10 |

    **Classifications:** High = 70–100 · Medium = 40–69 · Low = 0–39

    #### ⚠️ Disclaimer
    Risk scores are **heuristic churn risk indicators** derived from a deterministic rule set.
    They are *not* statistically validated churn probabilities and should be used to support —
    not replace — human judgment. No customer data is transmitted to external services.

    #### watsonx.ai Integration Path
    ChurnWatch is architecturally ready for IBM watsonx.ai integration. With valid API credentials,
    the Pilot section would invoke a foundation model to generate personalized, narrative-style
    retention recommendations grounded in each customer's actual engagement profile.
    """)
