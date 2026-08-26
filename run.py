"""
AI Business Process Recovery Agent - Main Runner
"""

import uvicorn
import os
import sys

if __name__ == "__main__":
    # Ensure current directory is in python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    print("=" * 75)
    print("  AI Process Recovery Agent – LangGraph – Human-in-the-Loop")
    print("  Autonomous Business Workflow Recovery System powered by LangGraph AI")
    print("=" * 75)
    print("  Server URL  : http://127.0.0.1:8000")
    print("  API Docs    : http://127.0.0.1:8000/docs")
    print("=" * 70)

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)
