"""
data.py — Data layer for ChurnWatch: Customer Retention Intelligence

Provides:
  - generate_synthetic_data(n, seed): produces a realistic synthetic customer DataFrame
  - load_and_validate_csv(file): validates an uploaded CSV against required columns
  - REQUIRED_COLUMNS: the canonical list of columns the application expects
"""

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "customer_id",
    "segment",
    "days_since_last_activity",
    "engagement_change_30d",
    "purchase_frequency",
    "tenure_months",
    "unresolved_tickets",
    "monthly_revenue",
]


def generate_synthetic_data(n: int = 80, seed: int = 42) -> pd.DataFrame:
    """
    Generate a realistic synthetic customer dataset with n rows.

    Distributions are designed to produce a meaningful mix of Low, Medium,
    and High risk customers so the dashboard looks informative on first load.

    Parameters
    ----------
    n : int
        Number of customer records to generate (default 80).
    seed : int
        Random seed for reproducibility (default 42).

    Returns
    -------
    pd.DataFrame with columns matching REQUIRED_COLUMNS.
    """
    rng = np.random.default_rng(seed)

    segments = ["Enterprise", "Mid-Market", "SMB"]
    segment_weights = [0.25, 0.40, 0.35]

    # Base distributions — designed to yield ~15% High, ~35% Medium, ~50% Low
    # for a compelling enterprise demo
    days_since_activity = np.concatenate([
        rng.integers(1, 20, size=int(n * 0.25)),    # recently active (low risk)
        rng.integers(20, 60, size=int(n * 0.30)),   # moderate inactivity
        rng.integers(61, 180, size=n - int(n * 0.25) - int(n * 0.30)),  # high inactivity
    ])
    rng.shuffle(days_since_activity)

    # Engagement change: realistic mix with meaningful at-risk portion
    engagement_change = np.concatenate([
        rng.uniform(0.00, 0.25, size=int(n * 0.25)),     # flat / slight growth
        rng.uniform(-0.10, 0.00, size=int(n * 0.20)),    # minimal decline
        rng.uniform(-0.30, -0.10, size=int(n * 0.30)),   # moderate decline (+12 pts)
        rng.uniform(-0.65, -0.30, size=n - int(n * 0.25) - int(n * 0.20) - int(n * 0.30)),  # steep decline (+25 pts)
    ])
    rng.shuffle(engagement_change)

    # Purchase frequency: more customers below the 1/month threshold
    purchase_frequency = np.concatenate([
        rng.uniform(0.1, 0.95, size=int(n * 0.35)),  # below 1/month (risk flag, +20 pts)
        rng.uniform(1.0, 3.0, size=int(n * 0.40)),   # healthy
        rng.uniform(3.0, 8.0, size=n - int(n * 0.35) - int(n * 0.40)),  # high frequency
    ])
    rng.shuffle(purchase_frequency)

    # Tenure: realistic mix — new, mid, and long-term accounts
    tenure_months = np.concatenate([
        rng.integers(1, 12, size=int(n * 0.25)),      # new customers (no loyalty buffer)
        rng.integers(12, 24, size=int(n * 0.30)),     # mid-tenure
        rng.integers(25, 72, size=n - int(n * 0.25) - int(n * 0.30)),  # long-term (loyalty buffer)
    ])
    rng.shuffle(tenure_months)

    # Unresolved support tickets: weighted toward 0 but with meaningful at-risk tail
    ticket_choices = [0, 0, 0, 0, 1, 1, 2, 2, 3, 4, 5]
    unresolved_tickets = rng.choice(ticket_choices, size=n)

    # Monthly revenue: varies by segment feel — log-normal for realistic spread
    monthly_revenue = np.round(
        np.exp(rng.normal(loc=8.5, scale=1.0, size=n)), 0
    ).clip(500, 50000)

    assigned_segments = rng.choice(segments, size=n, p=segment_weights)

    customer_ids = [f"CUST-{str(i + 1001).zfill(4)}" for i in range(n)]

    df = pd.DataFrame({
        "customer_id": customer_ids,
        "segment": assigned_segments,
        "days_since_last_activity": days_since_activity.astype(int),
        "engagement_change_30d": np.round(engagement_change, 3),
        "purchase_frequency": np.round(purchase_frequency, 2),
        "tenure_months": tenure_months.astype(int),
        "unresolved_tickets": unresolved_tickets.astype(int),
        "monthly_revenue": monthly_revenue.astype(float),
    })

    return df.reset_index(drop=True)


def load_and_validate_csv(file) -> pd.DataFrame:
    """
    Load and validate a CSV file uploaded via Streamlit.

    Parameters
    ----------
    file : UploadedFile
        A Streamlit UploadedFile object (from st.file_uploader).

    Returns
    -------
    pd.DataFrame with validated data.

    Raises
    ------
    ValueError if required columns are missing, with a descriptive message
    listing the missing column names.
    """
    df = pd.read_csv(file)

    # Normalize column names: strip whitespace, lowercase
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"The uploaded CSV is missing the following required columns: "
            f"{', '.join(missing)}.\n\n"
            f"Required columns: {', '.join(REQUIRED_COLUMNS)}"
        )

    # Return only the required columns in canonical order
    return df[REQUIRED_COLUMNS].reset_index(drop=True)
