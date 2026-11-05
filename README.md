# 📊 ChurnWatch — Customer Churn Analytics

> **Identify at-risk customers before they leave. Understand why. Act fast.**

Customer retention is an important challenge for businesses. While some customers are at greater risk of leaving than others, identifying these customers and determining how to retain them isn't always straightforward.

ChurnWatch is a Python-based Streamlit application designed to analyze customer engagement statistics, visualize churn risk across a portfolio, and provide actionable retention recommendations. Through ChurnWatch, users can explore customer-level statistics, filter by risk level and market segment, and visualize patterns that may indicate a higher likelihood of customer churn — helping businesses make more informed, data-driven retention decisions.

This project was developed during a one-hour hackathon collaboration with IBM at Arizona State University Polytechnic, November 2026.

---

## ✨ Features

- **Instant Demo** — Load 100 realistic synthetic customers in one click. No external data required.
- **CSV Upload** — Bring your own customer data. ChurnWatch validates your file and scores it automatically.
- **Heuristic Risk Scoring** — Every customer receives a transparent 0–100 risk score based on five observable behavioral signals.
- **Executive Dashboard** — KPI cards, a risk distribution donut chart, and a segment breakdown bar chart give instant portfolio visibility.
- **Customer Table** — Filter by risk level and segment. Risk scores shown as progress bars.
- **Customer Drilldown** — Select any customer to see their exact score, every contributing factor with its point value, and specific retention recommendations grounded in their actual metrics.
- **watsonx.ai Pilot Section** — A structured integration path for IBM watsonx.ai. Configure an API key and Project ID to unlock AI-generated retention recommendations.

---

## 🚀 Getting Started

### Already set up? Quick start

```bash
# Activate the virtual environment
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# Launch the app
streamlit run app.py
```

Or via the entry point:

```bash
python main.py
```

The app will open in your browser at `http://localhost:8501`.

---

### First time setup

**Prerequisites:** Python 3.10 or higher

```bash
# 1. Clone the repository
git clone https://github.com/your-username/churnwatch.git
cd churnwatch

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the application
streamlit run app.py
```

---

## 📁 Project Structure

```
churnwatch/
├── app.py               # Streamlit UI — dashboard, drilldown, watsonx.ai pilot
├── data.py              # Synthetic data generator + CSV ingestion & validation
├── scoring.py           # Rule-based heuristic risk scoring engine
├── recommendations.py   # Data-grounded retention recommendation logic
├── requirements.txt     # Pinned Python dependencies
└── main.py              # Entry point: launches Streamlit via subprocess
```

---

## 📐 How Risk Scoring Works

ChurnWatch evaluates each customer across five observable behavioral signals and assigns a heuristic risk score from **0 to 100**. The scoring formula is fully transparent — no black box.

| Signal | Condition | Points |
|---|---|---|
| Days since last activity | > 60 days | +30 |
| Days since last activity | 30–60 days | +15 |
| Engagement change (30d) | Decline > 30% | +25 |
| Engagement change (30d) | Decline 10–30% | +12 |
| Purchase frequency | < 1 purchase/month | +20 |
| Unresolved support tickets | ≥ 3 tickets | +15 |
| Unresolved support tickets | 1–2 tickets | +8 |
| Tenure (loyalty buffer) | > 24 months | −10 |

**Risk Classifications:**

| Level | Score Range | Interpretation |
|---|---|---|
| 🔴 High | 70–100 | Immediate intervention recommended |
| 🟡 Medium | 40–69 | Monitor closely; consider proactive outreach |
| 🟢 Low | 0–39 | Healthy engagement; standard cadence |

> **Disclaimer:** Risk scores are heuristic churn risk indicators derived from a deterministic rule set. They are *not* statistically validated churn probabilities and are designed to support — not replace — human judgment. No customer data is transmitted to external services.

---

## 🤖 watsonx.ai Integration

ChurnWatch includes a built-in integration path for [IBM watsonx.ai](https://www.ibm.com/products/watsonx-ai). The **AI-Powered Recommendations (Pilot)** section in the app is designed to connect to a watsonx.ai foundation model to generate personalized, narrative-style retention recommendations grounded in each customer's actual engagement profile.

### What a full integration would enable

- A foundation model (e.g., `ibm/granite-13b-chat-v2`) receives a structured prompt with the customer's scored profile, risk factors, segment, and revenue context
- The model returns a personalized retention recommendation in natural language — more actionable than rule-based bullet points
- Responses are grounded in the customer's actual metrics, not generic outputs

### How to connect

1. Obtain watsonx.ai API credentials and a Project ID from [IBM watsonx.ai](https://www.ibm.com/products/watsonx-ai)
2. Click **"Connect watsonx.ai →"** in the sidebar
3. Enter your API key and Project ID
4. The Pilot section will update to reflect the live integration status

> No customer data is transmitted to external services unless you explicitly configure and connect watsonx.ai credentials.

---

## 🛠 Tech Stack

| Component | Technology |
|---|---|
| Application framework | [Streamlit](https://streamlit.io) >= 1.32 |
| Data processing | [pandas](https://pandas.pydata.org) >= 2.0, [NumPy](https://numpy.org) >= 1.26 |
| Visualizations | [Plotly](https://plotly.com/python/) >= 5.20 |
| Language | Python 3.10+ |
| Styling | Custom CSS with IBM Design Language |

---

## 📋 CSV Upload Format

To upload your own customer data, your CSV must contain the following columns (column names are case-insensitive):

| Column | Type | Description |
|---|---|---|
| `customer_id` | string | Unique customer identifier |
| `segment` | string | Customer segment (e.g. Enterprise, Mid-Market, SMB) |
| `days_since_last_activity` | integer | Days since the customer last engaged |
| `engagement_change_30d` | float | Engagement change over 30 days as a decimal (e.g. -0.40 = −40%) |
| `purchase_frequency` | float | Average purchases per month |
| `tenure_months` | integer | Customer tenure in months |
| `unresolved_tickets` | integer | Number of open support tickets |
| `monthly_revenue` | float | Monthly recurring revenue from this customer (USD) |

---

## 🏗 Future Enhancements

### AI & Intelligence
- **Live watsonx.ai integration** — Connect IBM watsonx.ai foundation models to generate personalized, narrative-style retention recommendations grounded in each customer's actual profile
- **Additional LLM support** — Extend the AI recommendation layer to support other providers (OpenAI, Anthropic, Google Gemini) so teams can use whichever model fits their infrastructure
- **ML-based scoring** — Replace heuristic rules with a trained gradient boosting model (XGBoost/LightGBM) validated on historical churn data, with SHAP-based explainability to preserve transparency

### Data & Uploads
- **Multi-dataset support** — Upload and switch between multiple CSV files without losing prior results; compare portfolios side by side
- **Combined dataset analysis** — Merge multiple uploaded CSVs into a single unified view, with a source column tracking which file each customer came from
- **CRM integration** — Salesforce / HubSpot connectors for live customer data ingestion, replacing manual CSV exports

### Monitoring & Automation
- **Alert system** — Automated email/Slack alerts when a customer crosses a risk threshold
- **Cohort analysis** — Track how a customer's risk score changes over time across multiple data uploads
- **Scheduled scoring** — Run ChurnWatch on a cadence (daily/weekly) and surface customers whose risk increased since the last run

---

## ⚖️ Disclaimer

ChurnWatch is a proof-of-concept prototype. Risk scores are heuristic indicators based on observable engagement signals and are not statistically validated predictions of customer churn. All synthetic data is randomly generated and does not represent any real individuals or organizations.

---

*Developed at the IBM Hackathon · Arizona State University Polytechnic · November 2026*  
*Special thanks to Emily Placet and Raj Kumar for their guidance and feedback.*  
*AI-assisted development powered by [IBM Bob](https://www.ibm.com/products/bob)*
