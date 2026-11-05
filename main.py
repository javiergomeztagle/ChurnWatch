"""
ChurnWatch — Customer Retention Intelligence
Entry point: launches the Streamlit application.

Usage:
    python main.py
    # or directly:
    streamlit run app.py
"""

import subprocess
import sys

if __name__ == "__main__":
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless", "false"],
        check=True,
    )
