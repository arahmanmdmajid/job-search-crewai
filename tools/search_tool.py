"""
Job Search Tool
---------------
Ported from the original job-search-assistant project.
Uses the Tavily API to search for live job listings on the web.

In CrewAI, tools are wrapped with @tool decorator so agents can call them.
"""

import os
import requests
from crewai.tools import tool
from dotenv import load_dotenv

load_dotenv()


@tool("Job Search Tool")
def job_search_tool(query: str) -> str:
    """
    Search for job listings on the web using the Tavily API.
    Input: a job search query (e.g. 'Python developer jobs in Malaysia 2024')
    Output: a formatted list of job listings with titles, URLs, and summaries.
    """
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        return "ERROR: TAVILY_API_KEY not found in environment variables."

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "advanced",
                "max_results": 5,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if not results:
            return "No job listings found for that query."

        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(
                f"{i}. {r.get('title', 'No title')}\n"
                f"   URL: {r.get('url', 'N/A')}\n"
                f"   {r.get('content', 'No description')[:300]}...\n"
            )

        return "\n".join(formatted)

    except requests.exceptions.Timeout:
        return "FALLBACK: Tavily API timed out. Please try a more specific search query."
    except requests.exceptions.ConnectionError:
        return "FALLBACK: Could not connect to Tavily API. Check your internet connection."
    except requests.exceptions.HTTPError as e:
        return f"FALLBACK: Tavily API error ({e.response.status_code}). Check your API key."
    except Exception as e:
        return f"FALLBACK: Unexpected error during job search: {str(e)}"
