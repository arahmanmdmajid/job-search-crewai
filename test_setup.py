"""
Setup Verification Script
--------------------------
Run this BEFORE running app.py to confirm everything is configured correctly.
It checks:
  1. All required Python packages are installed
  2. All required API keys are present in .env
  3. Tavily API is reachable
  4. OpenAI API key is valid
  5. Langfuse keys (optional)

Usage:
    python test_setup.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 55)
print("  Job Search CrewAI — Setup Verification")
print("=" * 55)

errors = []
warnings = []

# ---- 1. Check packages ---- #
print("\n📦 Checking installed packages...")

packages = {
    "crewai": "crewai",
    "langfuse": "langfuse",
    "gradio": "gradio",
    "openai": "openai",
    "requests": "requests",
    "dotenv": "python-dotenv",
}

for import_name, package_name in packages.items():
    try:
        __import__(import_name)
        print(f"  ✅ {package_name}")
    except ImportError:
        print(f"  ❌ {package_name} — run: pip install {package_name}")
        errors.append(f"Missing package: {package_name}")

# ---- 2. Check API keys ---- #
print("\n🔑 Checking API keys in .env...")

openai_key = os.getenv("OPENAI_API_KEY", "")
tavily_key = os.getenv("TAVILY_API_KEY", "")
langfuse_secret = os.getenv("LANGFUSE_SECRET_KEY", "")
langfuse_public = os.getenv("LANGFUSE_PUBLIC_KEY", "")

if openai_key and openai_key != "your_openai_api_key_here":
    print(f"  ✅ OPENAI_API_KEY found (ends in ...{openai_key[-4:]})")
else:
    print("  ❌ OPENAI_API_KEY missing or not set")
    errors.append("OPENAI_API_KEY not configured")

if tavily_key and tavily_key != "your_tavily_api_key_here":
    print(f"  ✅ TAVILY_API_KEY found (ends in ...{tavily_key[-4:]})")
else:
    print("  ❌ TAVILY_API_KEY missing or not set")
    errors.append("TAVILY_API_KEY not configured")

if langfuse_secret and langfuse_secret != "your_langfuse_secret_key_here":
    print(f"  ✅ LANGFUSE_SECRET_KEY found")
else:
    print("  ⚠️  LANGFUSE_SECRET_KEY not set (monitoring will be disabled)")
    warnings.append("Langfuse monitoring not configured")

if langfuse_public and langfuse_public != "your_langfuse_public_key_here":
    print(f"  ✅ LANGFUSE_PUBLIC_KEY found")
else:
    print("  ⚠️  LANGFUSE_PUBLIC_KEY not set (monitoring will be disabled)")

# ---- 3. Test Tavily connectivity ---- #
print("\n🌐 Testing Tavily API connection...")
try:
    import requests
    if tavily_key and tavily_key != "your_tavily_api_key_here":
        resp = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": tavily_key, "query": "test", "max_results": 1},
            timeout=8,
        )
        if resp.status_code == 200:
            print("  ✅ Tavily API is reachable and key is valid")
        elif resp.status_code == 401:
            print("  ❌ Tavily API key is invalid (401 Unauthorized)")
            errors.append("Invalid TAVILY_API_KEY")
        else:
            print(f"  ⚠️  Tavily returned status {resp.status_code}")
            warnings.append(f"Tavily status: {resp.status_code}")
    else:
        print("  ⏭️  Skipped (no Tavily key configured)")
except Exception as e:
    print(f"  ⚠️  Could not reach Tavily: {e}")
    warnings.append("Tavily unreachable")

# ---- 4. Test OpenAI connectivity ---- #
print("\n🤖 Testing OpenAI API connection...")
try:
    from openai import OpenAI
    if openai_key and openai_key != "your_openai_api_key_here":
        client = OpenAI(api_key=openai_key)
        resp = client.models.list()
        print("  ✅ OpenAI API is reachable and key is valid")
    else:
        print("  ⏭️  Skipped (no OpenAI key configured)")
except Exception as e:
    print(f"  ❌ OpenAI connection failed: {str(e)[:100]}")
    errors.append("OpenAI API connection failed")

# ---- Summary ---- #
print("\n" + "=" * 55)
if errors:
    print(f"❌ {len(errors)} error(s) found — fix these before running app.py:")
    for e in errors:
        print(f"   • {e}")
else:
    print("✅ All critical checks passed!")

if warnings:
    print(f"\n⚠️  {len(warnings)} warning(s) — optional but recommended:")
    for w in warnings:
        print(f"   • {w}")

if not errors:
    print("\n🚀 Ready to run! Start the app with:")
    print("   python app.py")
    print("   Then open: http://localhost:7860")

print("=" * 55)
sys.exit(1 if errors else 0)
