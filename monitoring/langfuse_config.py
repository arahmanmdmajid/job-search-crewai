"""
Langfuse Monitoring Configuration
-----------------------------------
Langfuse is an open-source observability platform for LLM applications.
It records every LLM call, tool call, agent step, input, output,
latency, and token usage — all visible in a web dashboard.

HOW IT WORKS with CrewAI:
  CrewAI has built-in support for Langfuse via environment variables.
  When LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY are set in .env,
  CrewAI automatically sends traces to your Langfuse dashboard.
  No manual instrumentation needed for basic tracking!

WHAT GETS TRACKED:
  - Each agent's execution (who ran, when, how long)
  - Every LLM call (prompt sent, response received, tokens used)
  - Every tool call (which tool, what input, what output)
  - Errors and failed steps
  - Total cost (if OpenAI key is linked)

Dashboard: https://cloud.langfuse.com
"""

import os
from dotenv import load_dotenv

load_dotenv()


def setup_langfuse():
    """
    Validates that Langfuse environment variables are present
    and prints the monitoring status.

    CrewAI picks up these env vars automatically:
      - LANGFUSE_SECRET_KEY
      - LANGFUSE_PUBLIC_KEY
      - LANGFUSE_HOST
    """

    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if secret_key and public_key:
        # Keys are set — CrewAI will automatically send traces
        print(f"📊 Langfuse monitoring ENABLED")
        print(f"   Dashboard: {host}")
        print(f"   Traces will appear in your Langfuse project after the run.\n")
        return True
    else:
        # Keys are missing — monitoring will be skipped but app still works
        print("⚠️  Langfuse monitoring DISABLED")
        print("   Set LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY in your .env")
        print("   to enable observability. Get free keys at cloud.langfuse.com\n")
        return False


def get_monitoring_status() -> dict:
    """
    Returns the current monitoring configuration as a dict.
    Used by the UI to show the user whether monitoring is active.
    """
    return {
        "enabled": bool(
            os.getenv("LANGFUSE_SECRET_KEY") and os.getenv("LANGFUSE_PUBLIC_KEY")
        ),
        "host": os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        "project": "job-search-crewai",
    }
