"""
scoring.py — Rule-based heuristic risk scoring engine for ChurnWatch.

SCORING FORMULA
===============
Each customer receives a heuristic risk score from 0 to 100 based on the
following weighted signals. Scores are indicators only — they are not
statistically validated churn probabilities.

  Signal                        Condition               Points
  ----------------------------  ----------------------  ------
  days_since_last_activity      > 60 days               +30
  days_since_last_activity      30–60 days              +15
  engagement_change_30d         < -30%                  +25
  engagement_change_30d         -30% to -10%            +12
  purchase_frequency            < 1 purchase/month      +20
  unresolved_tickets            >= 3 tickets            +15
  unresolved_tickets            1–2 tickets             +8
  tenure_months (loyalty buff)  > 24 months             -10
  Maximum possible score                                100

Risk Classification:
  High   → 70–100
  Medium → 40–69
  Low    →  0–39

Public API
----------
  score_customers(df) -> pd.DataFrame
      Returns df with three new columns appended:
        - risk_score   (int, 0–100)
        - risk_level   (str, "Low" / "Medium" / "High")
        - risk_factors (list of dicts with keys: factor, contribution, detail)
"""

from __future__ import annotations

import pandas as pd


# ---------------------------------------------------------------------------
# Scoring rules — each entry is (factor_name, contribution, test_fn, detail_fn)
# ---------------------------------------------------------------------------

def _build_scoring_rules() -> list[tuple]:
    """Return the ordered list of scoring rule tuples."""
    return [
        (
            "days_since_last_activity",
            30,
            lambda row: row["days_since_last_activity"] > 60,
            lambda row: f"Last active {row['days_since_last_activity']} days ago (threshold: >60 days)",
        ),
        (
            "days_since_last_activity",
            15,
            lambda row: 30 < row["days_since_last_activity"] <= 60,
            lambda row: f"Last active {row['days_since_last_activity']} days ago (threshold: 30–60 days)",
        ),
        (
            "engagement_change_30d",
            25,
            lambda row: row["engagement_change_30d"] < -0.30,
            lambda row: f"Engagement declined {abs(row['engagement_change_30d']) * 100:.1f}% over 30 days (threshold: >30% drop)",
        ),
        (
            "engagement_change_30d",
            12,
            lambda row: -0.30 <= row["engagement_change_30d"] < -0.10,
            lambda row: f"Engagement declined {abs(row['engagement_change_30d']) * 100:.1f}% over 30 days (threshold: 10–30% drop)",
        ),
        (
            "purchase_frequency",
            20,
            lambda row: row["purchase_frequency"] < 1.0,
            lambda row: f"Purchase frequency {row['purchase_frequency']:.2f}/month (threshold: <1/month)",
        ),
        (
            "unresolved_tickets",
            15,
            lambda row: row["unresolved_tickets"] >= 3,
            lambda row: f"{row['unresolved_tickets']} unresolved support tickets (threshold: ≥3)",
        ),
        (
            "unresolved_tickets",
            8,
            lambda row: 1 <= row["unresolved_tickets"] < 3,
            lambda row: f"{row['unresolved_tickets']} unresolved support ticket(s) (threshold: 1–2)",
        ),
        (
            "tenure_months",
            -10,
            lambda row: row["tenure_months"] > 24,
            lambda row: f"Long-tenure customer ({row['tenure_months']} months) — loyalty buffer applied",
        ),
    ]


_SCORING_RULES = _build_scoring_rules()


def _score_single(row: pd.Series) -> tuple[int, str, list[dict]]:
    """
    Score a single customer row.

    Returns
    -------
    (risk_score, risk_level, risk_factors)
    """
    total = 0
    factors = []

    for factor_name, contribution, test_fn, detail_fn in _SCORING_RULES:
        if test_fn(row):
            total += contribution
            factors.append({
                "factor": factor_name,
                "contribution": contribution,
                "detail": detail_fn(row),
            })

    # Clamp to [0, 100]
    score = max(0, min(100, total))

    # Classify
    if score >= 70:
        level = "High"
    elif score >= 40:
        level = "Medium"
    else:
        level = "Low"

    # Sort factors by absolute contribution descending (positive risks first)
    factors.sort(key=lambda f: f["contribution"], reverse=True)

    return score, level, factors


def score_customers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Score all customers in the DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Customer data with columns matching data.REQUIRED_COLUMNS.

    Returns
    -------
    pd.DataFrame — original df with three new columns appended:
        risk_score   (int)
        risk_level   (str)
        risk_factors (list of dicts)
    """
    result = df.copy()

    scores, levels, factors_list = [], [], []

    for _, row in result.iterrows():
        s, l, f = _score_single(row)
        scores.append(s)
        levels.append(l)
        factors_list.append(f)

    result["risk_score"] = scores
    result["risk_level"] = levels
    result["risk_factors"] = factors_list

    return result
