
import requests
import json


def analyze_resume(resume_text, user_goal):

    prompt = f"""
You are a senior software engineer and hiring manager.

Evaluate the resume based on the user's career goal.

User goal:
"{user_goal}"

STRICT RULES:
- Extract only relevant skills for this career goal.
- Ignore irrelevant skills and tools.
- Identify genuine missing skills based on the user's goal.
- Generate a roadmap only for the missing skills.
- Make the result specific to the user's career goal.
- Generate useful interview questions for the target role.
- Return ONLY valid JSON.
- Do not use Markdown.
- Do not add any explanation outside the JSON.

Return exactly this JSON structure:

{{
    "skills": [],
    "missing_skills": [],
    "roadmap": [],
    "interview_questions": []
}}

Resume:
{resume_text}
"""

    try:

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:3b",
                "prompt": prompt,
                "stream": False,
                "format": "json"
            },
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        content = data.get("response", "").strip()

        if not content:
            raise ValueError("Ollama returned an empty response.")

        result = json.loads(content)

        return {
            "skills": result.get("skills", []),
            "missing_skills": result.get("missing_skills", []),
            "roadmap": result.get("roadmap", []),
            "interview_questions": result.get(
                "interview_questions", []
            )
        }

    except requests.exceptions.ConnectionError:

        return {
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "error": "Ollama is not running. Please start Ollama and try again."
        }

    except requests.exceptions.Timeout:

        return {
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "error": "Ollama took too long to respond."
        }

    except json.JSONDecodeError:

        return {
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "error": "Ollama returned an invalid JSON response."
        }

    except Exception as e:

        return {
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "error": str(e)
        }

