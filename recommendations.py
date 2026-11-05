"""
recommendations.py — Retention recommendation logic for ChurnWatch.

Maps observed risk factors to specific, data-grounded retention actions.
All recommendations reference the customer's actual metrics — no generic boilerplate.

Public API
----------
  get_recommendations(customer_row, risk_factors) -> list[dict]
      Returns a list of recommendation dicts ordered by factor contribution.
      Each dict has keys:
        - action    (str) — the recommended retention action
        - rationale (str) — why this action is suggested, citing actual data
"""

from __future__ import annotations

import pandas as pd


# ---------------------------------------------------------------------------
# Recommendation rules keyed to risk factor names
# ---------------------------------------------------------------------------

def get_recommendations(
    customer_row: pd.Series,
    risk_factors: list[dict],
) -> list[dict]:
    """
    Generate data-grounded retention recommendations for a single customer.

    Parameters
    ----------
    customer_row : pd.Series
        A single row from the scored customer DataFrame.
    risk_factors : list[dict]
        The risk_factors list produced by scoring.py for this customer.
        Each dict has keys: factor, contribution, detail.

    Returns
    -------
    list[dict] — recommendations ordered by factor contribution (highest first).
    Each dict has keys: action, rationale.
    """
    if not risk_factors:
        return [{
            "action": "Continue standard engagement cadence",
            "rationale": (
                f"{customer_row['customer_id']} shows no significant risk indicators. "
                "Maintain regular check-ins and monitor for changes in activity."
            ),
        }]

    recommendations = []

    # Track which factor names have already generated a recommendation
    # to avoid duplicate entries when multiple rules share a factor name
    seen_factors = set()

    # Process factors in contribution order (already sorted by scoring.py)
    for factor in risk_factors:
        fname = factor["factor"]
        contribution = factor["contribution"]

        if fname in seen_factors:
            continue

        if fname == "days_since_last_activity" and contribution > 0:
            days = int(customer_row["days_since_last_activity"])
            urgency = "immediately" if days > 60 else "within the next week"
            recommendations.append({
                "action": f"Schedule a customer success outreach call {urgency}",
                "rationale": (
                    f"{customer_row['customer_id']} has not been active for {days} days. "
                    "Direct outreach can re-establish engagement before the relationship deteriorates further."
                ),
            })
            seen_factors.add(fname)

        elif fname == "engagement_change_30d" and contribution > 0:
            pct = abs(customer_row["engagement_change_30d"]) * 100
            severity = "significant" if pct > 30 else "moderate"
            recommendations.append({
                "action": "Initiate a personalized product re-onboarding session",
                "rationale": (
                    f"Engagement has declined {pct:.1f}% over the past 30 days — a {severity} drop. "
                    "A tailored onboarding refresh can reconnect the customer with product value."
                ),
            })
            seen_factors.add(fname)

        elif fname == "purchase_frequency" and contribution > 0:
            freq = customer_row["purchase_frequency"]
            recommendations.append({
                "action": "Assign a dedicated account manager to investigate purchase behavior",
                "rationale": (
                    f"Purchase frequency has dropped to {freq:.2f} transactions/month — below the 1/month threshold. "
                    "An account manager should identify whether this is budget-driven, competitive, or product-related."
                ),
            })
            seen_factors.add(fname)

        elif fname == "unresolved_tickets" and contribution > 0:
            tickets = int(customer_row["unresolved_tickets"])
            recommendations.append({
                "action": f"Escalate {tickets} unresolved support ticket(s) to a senior support engineer",
                "rationale": (
                    f"{customer_row['customer_id']} has {tickets} unresolved support ticket(s). "
                    "Unresolved issues are a leading indicator of churn — prioritize resolution before next contact."
                ),
            })
            seen_factors.add(fname)

        elif fname == "tenure_months" and contribution < 0:
            # Loyalty buffer — customer is long-tenure, low risk
            tenure = int(customer_row["tenure_months"])
            recommendations.append({
                "action": "Recognize long-term loyalty with a proactive renewal incentive",
                "rationale": (
                    f"{customer_row['customer_id']} has been a customer for {tenure} months. "
                    "A proactive loyalty offer can reinforce retention and deepen the relationship."
                ),
            })
            seen_factors.add(fname)

    # If somehow no recommendations were generated (edge case), fall back
    if not recommendations:
        recommendations.append({
            "action": "Review account health with the customer success team",
            "rationale": (
                f"{customer_row['customer_id']} has flagged risk indicators that warrant manual review."
            ),
        })

    return recommendations
