"""
Bank Fraud-Rule Processing Architecture Simulator
=================================================
Jupyter / Streamlit Entrypoint
"""

import sys
import os

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from streamlit_app import *
