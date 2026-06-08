"""
Agents Definition
-----------------
This file defines all 4 agents in our CrewAI job search system.

Think of each agent as a specialist employee:
- They have a ROLE (job title)
- A GOAL (what they're trying to achieve)
- A BACKSTORY (personality/expertise — this shapes how the LLM responds)
- TOOLS (what they're allowed to use)

Agents do NOT talk to each other directly.
They each complete a TASK and pass the output to the next task in the workflow.
"""

import os
from crewai import Agent
from dotenv import load_dotenv
from tools.search_tool import job_search_tool
from tools.salary_tool import salary_tool
from tools.summarizer_tool import summarizer_tool
from tools.resume_tool import resume_matcher_tool

load_dotenv()


def create_agents():
    """
    Creates and returns all 4 agents.
    Called from crew.py when the workflow starts.
    """

    # ------------------------------------------------------------------ #
    # AGENT 1: Job Researcher
    # Responsibility: Search the web for relevant job listings
    # Tool used: job_search_tool (Tavily API)
    # ------------------------------------------------------------------ #
    job_researcher = Agent(
        role="Job Market Researcher",
        goal=(
            "Find the most relevant and up-to-date job listings based on the "
            "user's job title, skills, and location preferences."
        ),
        backstory=(
            "You are a seasoned recruitment researcher with 10 years of experience "
            "scouring the web for job opportunities. You know how to craft precise "
            "search queries to surface the best listings quickly. You always provide "
            "structured, readable results and never fabricate job postings."
        ),
        tools=[job_search_tool],
        verbose=True,           # Print what this agent is thinking/doing
        allow_delegation=False, # This agent does its own work, doesn't pass to others
        max_iter=3,             # Try at most 3 times before giving up
    )

    # ------------------------------------------------------------------ #
    # AGENT 2: Salary Analyst
    # Responsibility: Research compensation for the target role
    # Tool used: salary_tool (Remotive API)
    # ------------------------------------------------------------------ #
    salary_analyst = Agent(
        role="Compensation & Salary Analyst",
        goal=(
            "Research and report accurate salary ranges and compensation benchmarks "
            "for the target job title so the candidate can negotiate with confidence."
        ),
        backstory=(
            "You are a compensation specialist who helps job seekers understand their "
            "market value. You dig into salary databases and job postings to extract "
            "real pay data. You are honest when data is unavailable and always suggest "
            "alternative research strategies when needed."
        ),
        tools=[salary_tool],
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )

    # ------------------------------------------------------------------ #
    # AGENT 3: Job Analyst
    # Responsibility: Summarize job descriptions into clean bullet points
    # Tool used: summarizer_tool (GPT-powered custom tool)
    # ------------------------------------------------------------------ #
    job_analyst = Agent(
        role="Job Description Analyst",
        goal=(
            "Analyze and summarize job descriptions into clear, structured bullet points "
            "so the candidate quickly understands what the role requires."
        ),
        backstory=(
            "You are a career coach and job description expert. You have read thousands "
            "of job postings and can instantly identify what matters versus what is "
            "corporate fluff. You highlight red flags, key requirements, and hidden "
            "expectations that candidates often miss."
        ),
        tools=[summarizer_tool],
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )

    # ------------------------------------------------------------------ #
    # AGENT 4: Career Advisor
    # Responsibility: Match the candidate's profile to the jobs found,
    #                 score the fit, and give a final recommendation
    # Tool used: resume_matcher_tool (NEW custom tool)
    # ------------------------------------------------------------------ #
    career_advisor = Agent(
        role="Career Advisor & Resume Matcher",
        goal=(
            "Evaluate how well the candidate's skills and experience match the "
            "job requirements, provide a fit score, identify gaps, and give "
            "a clear, actionable final recommendation."
        ),
        backstory=(
            "You are a senior career advisor who has helped hundreds of professionals "
            "land their dream jobs. You combine recruiter-level insight with empathy. "
            "You give honest scores, celebrate genuine strengths, and offer constructive "
            "advice on skill gaps — never sugarcoating but always encouraging."
        ),
        tools=[resume_matcher_tool],
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )

    return job_researcher, salary_analyst, job_analyst, career_advisor
