"""
Crew Assembly
-------------
This file is the HEART of the application.
It brings together agents + tasks and kicks off the workflow.

Think of it as the "project manager" that:
  1. Hires the agents (imports from agents.py)
  2. Assigns the work (imports from tasks.py)
  3. Decides the process (sequential vs hierarchical)
  4. Starts the crew and returns the final result

PROCESS TYPES in CrewAI:
  - Process.sequential  → Tasks run ONE AFTER ANOTHER (like an assembly line)
  - Process.hierarchical → A manager agent decides who does what (more complex)

We use SEQUENTIAL here because our workflow has a clear order:
  Research → [Salary + Summarize in parallel] → Match & Advise
"""

import os
from datetime import datetime
from crewai import Crew, Process
from agents import create_agents
from tasks import create_tasks
from monitoring.langfuse_config import setup_langfuse
from fallback.fallback_handler import safe_crew_run


def run_job_search_crew(user_inputs: dict) -> str:
    """
    Main entry point. Builds and runs the crew.

    Args:
        user_inputs: dict with:
            - job_title (str)
            - location (str)
            - candidate_profile (str)
            - job_description (str)

    Returns:
        Final report as a string.
    """

    # Step 1: Set up Langfuse monitoring (tracks everything that happens)
    setup_langfuse()

    # Step 2: Create all agents
    agents = create_agents()

    # Step 3: Create all tasks, injecting the user's inputs
    tasks = create_tasks(agents, user_inputs)

    # Step 4: Assemble the Crew
    crew = Crew(
        agents=list(agents),
        tasks=tasks,
        process=Process.sequential,
        # sequential means:
        #   Task 1 runs → Task 2 runs → Task 3 runs → Task 4 runs
        #   Each task can see previous tasks' outputs via context=[...]
        verbose=True,
        # verbose=True prints a live log of what each agent is thinking
        # and doing — great for learning and debugging!
    )

    # Step 5: Run the crew with fallback protection
    # (if something crashes, fallback_handler catches it gracefully)
    result = safe_crew_run(crew, user_inputs)

    # Step 6: Auto-save the result to the outputs/ folder
    _save_result(result, user_inputs)

    return result


def _save_result(result: str, user_inputs: dict):
    """
    Saves the crew's output to the outputs/ folder as a markdown file.
    Filename includes the job title and a timestamp so results don't overwrite each other.
    """
    try:
        os.makedirs("outputs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        job_title_slug = user_inputs.get("job_title", "result").replace(" ", "_").lower()
        filename = f"outputs/{job_title_slug}_{timestamp}.md"

        header = (
            f"# Job Search Report\n\n"
            f"- **Job Title:** {user_inputs.get('job_title')}\n"
            f"- **Location:** {user_inputs.get('location')}\n"
            f"- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"---\n\n"
        )

        with open(filename, "w", encoding="utf-8") as f:
            f.write(header + result)

        print(f"\nResult saved to: {filename}")

    except Exception as e:
        # Non-critical -- don't crash the app if saving fails
        print(f"[WARN] Could not save result to file: {e}")
