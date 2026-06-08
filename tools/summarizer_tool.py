"""
Job Description Summarizer Tool
---------------------------------
Ported from the original job-search-assistant project.
Uses GPT-4o-mini to convert a raw job description into a clean,
structured bullet-point summary covering key sections.
"""

import os
from crewai.tools import tool
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


@tool("Job Description Summarizer")
def summarizer_tool(job_description: str) -> str:
    """
    Summarize a raw job description into structured bullet points.
    Input: raw job description text (paste the full job posting)
    Output: clean summary with Role Overview, Responsibilities, Required Skills,
            Nice-to-Haves, and any Red Flags.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return "ERROR: OPENAI_API_KEY not found in environment variables."

    if not job_description or len(job_description.strip()) < 50:
        return "FALLBACK: Job description is too short or empty. Please provide the full job posting text."

    try:
        client = OpenAI(api_key=api_key)

        prompt = f"""Summarize the following job description into clear, concise bullet points
under these headings:

1. **Role Overview** – What is this job in 1-2 sentences?
2. **Key Responsibilities** – What will the person do day-to-day?
3. **Required Skills** – Must-have qualifications and experience
4. **Nice-to-Haves** – Bonus skills or preferred qualifications
5. **Red Flags** – Anything concerning or unusually demanding?

Job Description:
{job_description}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=800,
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"FALLBACK: Could not summarize job description. Error: {str(e)}"
