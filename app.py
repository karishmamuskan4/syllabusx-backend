from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
import json
import os 

app = Flask(__name__)
CORS(app) 

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

@app.route('/api/analyze', methods=['POST'])
def analyze_gap():
    data = request.json
    syllabus = data.get('syllabus', '')
    profession = data.get('profession', '') # 'jd' ki jagah ab 'profession' aayega
    
    if not syllabus or not profession:
        return jsonify({"status": "error", "message": "Syllabus and Profession are required!"}), 400
        
    if not client:
        return jsonify({"status": "error", "message": "Groq API Key is missing on Render!"}), 500

    try:
    
        prompt = f"""
        You are a Principal Engineer and Senior Technical Recruiter at a Fortune 500 tech company.
        Your task is to conduct a ruthless, highly accurate gap analysis between a student's college syllabus and the current, cutting-edge industry requirements for the following role:

        TARGET PROFESSION: {profession}
        STUDENT SYLLABUS: {syllabus}

        Analyze this like a strict industry expert. Do not hallucinate skills that are already present in the syllabus.

        CRITICAL INSTRUCTIONS & RUBRIC:
        1. "matchScore": Calculate a highly accurate, realistic percentage (0-100) representing how industry-ready this syllabus makes the student for the target profession. Be strict and objective.
        2. "matchingSkills": List the precise skills from the syllabus that are genuinely useful for the target profession.
        3. "missingSkills": Provide EXACTLY 10 critical, high-level conceptual skills, methodologies, or computer science fundamentals missing from the syllabus (e.g., "Microservices Architecture", "Agile Methodologies", "System Design", "CI/CD"). Do NOT include specific software names here.
        4. "industryTools": Provide EXACTLY 5 specific software tools, frameworks, libraries, or cloud platforms that dominate this profession today (e.g., "Docker", "React.js", "AWS", "Figma", "Kubernetes").
        5. "marketTrendsAdvice": Provide EXACTLY 5 actionable, hyper-specific pieces of advice based on current global tech market trends (e.g., "GenAI integration is becoming mandatory for full-stack roles", "Shift focus towards Rust for memory-safe systems programming").

        Return ONLY a valid, minified JSON object. Absolutely no markdown, no conversational text, no backticks outside the JSON.
        
        {{
            "matchScore": 45,
            "matchingSkills": ["skill1", "skill2"],
            "missingSkills": ["concept1", "concept2", "concept3", "concept4", "concept5", "concept6", "concept7", "concept8", "concept9", "concept10"],
            "industryTools": ["tool1", "tool2", "tool3", "tool4", "tool5"],
            "marketTrendsAdvice": ["trend1", "trend2", "trend3", "trend4", "trend5"]
        }}
        """
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300
        )
        
        ai_response = completion.choices[0].message.content.strip()
        
        # Cleanup extra markdown if AI sends it
        if "```json" in ai_response:
            ai_response = ai_response.split("```json")[1].split("```")[0].strip()
        elif "```" in ai_response:
            ai_response = ai_response.split("```")[1].strip()
            
        result_data = json.loads(ai_response)
        result_data["status"] = "success"
        
        return jsonify(result_data)
        
    except Exception as e:
        # Agar koi code phat-ta hai toh Render ke logs me exact error dikhega
        print(f"AI Error details: {e}") 
        return jsonify({"status": "error", "message": "AI failed to process. Check Render Logs.", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)