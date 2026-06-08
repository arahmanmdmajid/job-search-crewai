"""
Tasks Definition
----------------
This file defines the 4 tasks in our workflow.

A TASK in CrewAI is:
- A specific piece of work assigned to ONE agent
- Has a clear description (what to do)
- Has an expected_output (what the result should look like)
- Can use the previous task's output via {context}

The order tasks run in is defined in crew.py.

WORKFLOW:
  Task 1 (Research Jobs)
      ↓ output passed to ↓
  Task 2 (Research Salary)   &   Task 3 (Summarize Jobs)   ← run in parallel
      ↓ both outputs passed to ↓
  Task 4 (Match & Advise)
"""

from crewai import Task


def create_tasks(agents, user_inputs: dict):
    """
    Creates and returns all 4 tasks.

    Args:
        agents: tuple of (job_researcher, salary_analyst, job_analyst, career_advisor)
        user_inputs: dict with keys:
            - job_title: str  (e.g. "Data Scientist")
            - location: str   (e.g. "Malaysia" or "Remote")
            - candidate_profile: str (user's skills and experience summary)
            - job_description: str  (a specific job posting to analyze, optional)
    """

    job_researcher, salary_analyst, job_analyst, career_advisor = agents

    job_title = user_inputs.get("job_title", "Software Engineer")
    location = user_inputs.get("location", "Remote")
    candidate_profile = user_inputs.get("candidate_profile", "Not provided")
    job_description = user_inputs.get("job_description", "Not provided")

    # ------------------------------------------------------------------ #
    # TASK 1: Find Job Listings
    # Agent: Job Researcher
    # Input: job title + location from the user
    # Output: a list of 3-5 relevant job listings with links and summaries
    # ------------------------------------------------------------------ #
    task_research_jobs = Task(
        description=(
            f"Search for current job listings for the role: '{job_title}' in '{location}'.\n\n"
            f"Use the Job Search Tool to find at least 3-5 relevant openings.\n"
            f"For each listing, capture:\n"
            f"  - Job title and company name\n"
            f"  - Location and work type (remote/hybrid/on-site)\n"
            f"  - A brief description of what the role involves\n"
            f"  - The URL/source link\n\n"
            f"If no results are found, try a broader search query. "
            f"Do NOT fabricate any job listings."
        ),
        expected_output=(
            "A structured list of 3-5 job listings with:\n"
            "- Job title, company, location\n"
            "- Short description of each role\n"
            "- Source URL for each listing"
        ),
        agent=job_researcher,
    )

    # ------------------------------------------------------------------ #
    # TASK 2: Research Salary
    # Agent: Salary Analyst
    # Input: job title (same as Task 1)
    # Output: salary ranges and compensation benchmarks
    # Note: this task runs INDEPENDENTLY from Task 3 (no dependency)
    # ------------------------------------------------------------------ #
    task_research_salary = Task(
        description=(
            f"Research the current salary range and compensation benchmarks "
            f"for the role: '{job_title}'.\n\n"
            f"Use the Salary Research Tool to find real salary data from job postings.\n"
            f"Report:\n"
            f"  - Salary range (min / typical / max if available)\n"
            f"  - Whether salaries vary by location or experience level\n"
            f"  - Any notable benefits or equity mentioned\n\n"
            f"If explicit salary figures are unavailable, clearly state that "
            f"and suggest where the candidate can find this information."
        ),
        expected_output=(
            "A salary report covering:\n"
            "- Salary range for the role\n"
            "- Observations about pay variation\n"
            "- Recommended resources if data was limited"
        ),
        agent=salary_analyst,
    )

    # ------------------------------------------------------------------ #
    # TASK 3: Summarize a Job Description
    # Agent: Job Analyst
    # Input: the job description text provided by the user
    # Output: structured bullet-point summary
    # Note: this task also runs INDEPENDENTLY from Task 2
    # ------------------------------------------------------------------ #
    task_summarize_job = Task(
        description=(
            f"Analyze and summarize the following job description for the role '{job_title}'.\n\n"
            f"Job Description:\n{job_description}\n\n"
            f"Use the Job Description Summarizer tool to break it down into:\n"
            f"  1. Role Overview\n"
            f"  2. Key Responsibilities\n"
            f"  3. Required Skills\n"
            f"  4. Nice-to-Haves\n"
            f"  5. Red Flags (if any)\n\n"
            f"If no job description was provided by the user, write a brief note "
            f"that no specific posting was given and skip the summarization."
        ),
        expected_output=(
            "A structured summary of the job description with clear sections:\n"
            "Role Overview, Responsibilities, Required Skills, Nice-to-Haves, Red Flags"
        ),
        agent=job_analyst,
    )

    # ------------------------------------------------------------------ #
    # TASK 4: Match Candidate & Give Final Advice
    # Agent: Career Advisor
    # Input: candidate profile + job description summary from Task 3
    #        + job listings from Task 1 + salary data from Task 2
    # Output: fit score, strengths, gaps, and a final recommendation
    # ------------------------------------------------------------------ #
    task_match_and_advise = Task(
        description=(
            f"You have received the following from the previous agents:\n"
            f"  - Job listings for '{job_title}' in '{location}'\n"
            f"  - Salary research for '{job_title}'\n"
            f"  - A summarized job description (if provided)\n\n"
            f"Now evaluate how well this candidate fits the role.\n\n"
            f"Candidate Profile:\n{candidate_profile}\n\n"
            f"Use the Resume Matcher Tool by passing:\n"
            f"CANDIDATE PROFILE:\n{candidate_profile}\n---\n"
            f"JOB DESCRIPTION:\n{job_description}\n\n"
            f"Then provide a FINAL REPORT that includes:\n"
            f"  1. Match score and breakdown\n"
            f"  2. Top strengths the candidate brings\n"
            f"  3. Skill gaps to address\n"
            f"  4. Which specific job listings to apply to first\n"
            f"  5. Salary negotiation advice based on the research\n"
            f"  6. 2-3 actionable next steps for the candidate"
        ),
        expected_output=(
            "A comprehensive final report with:\n"
            "- Match score (0-100) with explanation\n"
            "- Strengths and skill gaps\n"
            "- Top job listings to apply to\n"
            "- Salary negotiation tips\n"
            "- Actionable next steps"
        ),
        agent=career_advisor,
        context=[task_research_jobs, task_research_salary, task_summarize_job],
        # ↑ This tells CrewAI: wait for tasks 1, 2, and 3 to finish,
        #   then pass ALL their outputs as context to this task.
    )

    return [task_research_jobs, task_research_salary, task_summarize_job, task_match_and_advise]
