import json
import re

def parse_gemini_response(response_json):
    if "error" in response_json:
        raise RuntimeError(f"Gemini API error: {response_json['error'].get('message')}")
        
    raw_content = response_json["candidates"][0]["content"]["parts"][0]["text"].strip()
    
    # Robust extraction in case the model ignored instructions and wrapped in code blocks
    json_content = raw_content
    if json_content.startswith("```"):
        json_content = re.sub(r'^```(?:json)?\s*', '', json_content)
        json_content = re.sub(r'\s*```$', '', json_content)
        
    return json.loads(json_content.strip())

# Simulate a standard Gemini API response
simulated_response = {
    "candidates": [
        {
            "content": {
                "parts": [
                    {
                        "text": "```json\n{\n  \"match_score\": 95,\n  \"missing_keywords\": [\"Kubernetes\", \"Docker\"],\n  \"tailored_resume_summary\": \"Experienced developer.\",\n  \"tailored_achievements\": [\"A1\", \"A2\", \"A3\"],\n  \"cold_outreach_email\": \"Hi manager.\"\n}\n```"
                    }
                ]
            }
        }
    ]
}

try:
    data = parse_gemini_response(simulated_response)
    print("Parsed score:", data["match_score"])
    print("Missing keywords:", data["missing_keywords"])
    print("TEST PASSED: parsed simulated Gemini response successfully.")
except Exception as e:
    print("TEST FAILED:", e)
