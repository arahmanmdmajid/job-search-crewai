---
title: Job Search CrewAI Assistant
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: "5.0.0"
app_file: app.py
pinned: false
short_description: Multi-agent job search assistant built with CrewAI
---

# Job Search CrewAI Assistant

A multi-agent AI job search assistant built with **CrewAI**, featuring 4 specialist agents that collaborate to find jobs, research salaries, summarize job descriptions, and score your profile fit.

## Setup

Set the following **Secrets** in your HF Space settings:

| Secret Name | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `TAVILY_API_KEY` | Tavily search API key (free at app.tavily.com) |
| `LANGFUSE_SECRET_KEY` | Langfuse monitoring secret key |
| `LANGFUSE_PUBLIC_KEY` | Langfuse monitoring public key |
| `LANGFUSE_BASE_URL` | `https://cloud.langfuse.com` |

## How it works

Four AI agents work in sequence:
1. **Job Researcher** — finds live job listings via Tavily
2. **Salary Analyst** — researches compensation via Remotive
3. **Job Analyst** — summarizes job descriptions with GPT-4o-mini
4. **Career Advisor** — scores your fit and gives recommendations

Source: [github.com/arahmanmdmajid/job-search-crewai](https://github.com/arahmanmdmajid/job-search-crewai)
