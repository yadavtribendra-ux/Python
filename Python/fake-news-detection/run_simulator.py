"""
Main Launcher for Bank Fraud Architecture Simulator
===================================================
Run `py -3 run_simulator.py` to run the CLI benchmark,
or `py -3 run_simulator.py --gui` to launch the interactive Streamlit dashboard.
"""

import sys
import os
import subprocess


def main():
    if "--gui" in sys.argv or "-g" in sys.argv:
        print("[*] Launching Streamlit Interactive Architecture Dashboard...")
        subprocess.run(["streamlit", "run", "streamlit_app.py"])
    else:
        from cli import main as cli_main
        cli_main()


if __name__ == "__main__":
    main()
