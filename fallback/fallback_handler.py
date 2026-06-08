"""
Fallback Handler
----------------
This module handles failures gracefully so the app never crashes
with an ugly error message.

WHY FALLBACKS MATTER in agentic systems:
  - LLM APIs can time out or hit rate limits
  - External APIs (Tavily, Remotive) can be down
  - Agents can get stuck in loops or return empty output
  - Network issues can occur mid-workflow

FALLBACK STRATEGIES used here:
  1. Retry once before giving up
  2. Return a human-readable error message (not a stack trace)
  3. Log the failure for debugging via Langfuse
"""

import time
import traceback


def safe_crew_run(crew, user_inputs: dict, max_retries: int = 2) -> str:
    """
    Runs the CrewAI crew with retry logic and graceful error handling.

    Args:
        crew: the assembled CrewAI Crew object
        user_inputs: the original user inputs (for error messages)
        max_retries: how many times to retry on failure (default: 2)

    Returns:
        The crew's final output as a string, or a friendly error message.
    """

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            print(f"\n{'='*50}")
            print(f"Starting crew (attempt {attempt}/{max_retries})...")
            print(f"{'='*50}\n")

            result = crew.kickoff()

            # CrewAI returns a CrewOutput object — extract the string
            output = str(result)

            if not output or len(output.strip()) < 50:
                raise ValueError(
                    "Crew returned an empty or very short result. "
                    "This may indicate an agent failed silently."
                )

            print(f"\nCrew completed successfully on attempt {attempt}.")
            return output

        except ValueError as e:
            # Empty output — retry immediately
            last_error = str(e)
            print(f"\n[WARN] Attempt {attempt} returned empty output: {last_error}")

        except Exception as e:
            last_error = str(e)
            error_trace = traceback.format_exc()
            print(f"\n[ERROR] Attempt {attempt} failed with error:\n{error_trace}")

            if attempt < max_retries:
                wait_seconds = attempt * 5  # Wait 5s, then 10s before retrying
                print(f"Retrying in {wait_seconds} seconds...\n")
                time.sleep(wait_seconds)

    # All retries exhausted — return a friendly fallback message
    return _build_fallback_message(user_inputs, last_error)


def _build_fallback_message(user_inputs: dict, error: str) -> str:
    """
    Builds a helpful, user-friendly message when the crew completely fails.
    Instead of showing a raw error, we guide the user on what to do next.
    """
    job_title = user_inputs.get("job_title", "the requested role")
    location = user_inputs.get("location", "your location")

    return f"""
⚠️  **The job search assistant encountered an issue and could not complete your request.**

**What we were trying to do:**
Search for '{job_title}' positions in '{location}' and provide a personalized career report.

**What likely went wrong:**
{error[:300] if error else "An unexpected error occurred."}

**What you can do:**
1. Check that your API keys in the `.env` file are valid (OPENAI_API_KEY, TAVILY_API_KEY)
2. Verify your internet connection
3. Try again in a few minutes (API rate limits sometimes cause temporary failures)
4. Simplify your job title (e.g. use 'Data Scientist' instead of 'Senior ML Research Scientist')

**Manual alternatives while the assistant is down:**
- Job search: https://www.linkedin.com/jobs or https://remotive.com
- Salary research: https://www.glassdoor.com or https://www.levels.fyi

We apologize for the inconvenience. Please try again shortly.
""".strip()
