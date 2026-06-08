"""
Resume Matcher Tool  ← NEW CUSTOM TOOL (built for this assignment)
--------------------
This tool takes a candidate's skills/experience summary and a job description,
then scores how well they match (0-100) with a breakdown of strengths and gaps.

This is the custom tool required by the assignment. It simulates what a recruiter
would do manually — comparing a CV against a job post and giving a fit score.
"""

import os
from crewai.tools import tool
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


@tool("Resume Matcher Tool")
def resume_matcher_tool(input_text: str) -> str:
    """
    Score how well a candidate matches a job description.

    Input format (separate with '---'):
        CANDIDATE PROFILE:
        <candidate's skills, experience, education>
        ---
        JOB DESCRIPTION:
        <the job posting or summary>

    Output: A match score (0-100), key strengths, skill gaps, and a hire recommendation.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return "ERROR: OPENAI_API_KEY not found in environment variables."

    if "---" not in input_text:
        return (
            "FALLBACK: Please provide both a candidate profile and job description, "
            "separated by '---'. \n"
            "Format:\nCANDIDATE PROFILE:\n<your skills>\n---\nJOB DESCRIPTION:\n<job post>"
        )

    parts = input_text.split("---", 1)
    candidate_profile = parts[0].strip()
    job_description = parts[1].strip()

    if len(candidate_profile) < 20 or len(job_description) < 20:
        return "FALLBACK: Both the candidate profile and job description must have meaningful content."

    try:
        client = OpenAI(api_key=api_key)

        prompt = f"""You are an expert recruiter. Evaluate how well this candidate matches the job.

CANDIDATE PROFILE:
{candidate_profile}

JOB DESCRIPTION:
{job_description}

Provide your evaluation in this exact format:

**Match Score: X/100**

**Strengths (what the candidate has that the job needs):**
- ...

**Skill Gaps (what the job needs that the candidate lacks):**
- ...

**Recommendation:** [Strong Match / Good Match / Partial Match / Poor Match]

**Summary:** (2-3 sentences explaining the score)
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=600,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"FALLBACK: Resume matching failed. Error: {str(e)}"
