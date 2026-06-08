"""
Salary Research Tool
--------------------
Ported from the original job-search-assistant project.
Uses the Remotive API (free, no key needed) to look up salary data
from remote job listings for a given job title.
"""

import requests
from crewai.tools import tool


@tool("Salary Research Tool")
def salary_tool(job_title: str) -> str:
    """
    Look up salary information for a given job title using the Remotive API.
    Input: a job title (e.g. 'Data Scientist', 'Frontend Developer')
    Output: salary ranges and compensation data found in remote job postings.
    """
    try:
        response = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"search": job_title, "limit": 10},
            timeout=10,
        )
        response.raise_for_status()
        jobs = response.json().get("jobs", [])

        if not jobs:
            return f"No salary data found for '{job_title}' on Remotive."

        salary_info = []
        found_salaries = 0

        for job in jobs:
            salary = job.get("salary", "").strip()
            company = job.get("company_name", "Unknown")
            title = job.get("title", "Unknown")

            if salary:
                salary_info.append(f"- {title} at {company}: {salary}")
                found_salaries += 1

        if found_salaries == 0:
            return (
                f"Found {len(jobs)} job listings for '{job_title}' on Remotive, "
                f"but none included explicit salary figures. "
                f"Typical remote roles in this field range widely — "
                f"recommend checking Glassdoor or LinkedIn for benchmarks."
            )

        result = f"Salary data for '{job_title}' from Remotive ({found_salaries} listings):\n"
        result += "\n".join(salary_info)
        return result

    except requests.exceptions.Timeout:
        return "FALLBACK: Remotive API timed out. Salary data unavailable right now."
    except requests.exceptions.ConnectionError:
        return "FALLBACK: Could not connect to Remotive API. Check your internet connection."
    except Exception as e:
        return f"FALLBACK: Error fetching salary data: {str(e)}"
