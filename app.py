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
       # Pura dimaag AI ko de diya
        prompt = f"""
        Act as an expert technical career advisor. 
        Target Profession: {profession}
        Student's College Syllabus: {syllabus}
        
        Compare the syllabus against the real-world industry requirements for the target profession. 
        Return ONLY a valid JSON object in this exact format. 
        CRITICAL: You MUST provide exactly 10 crucial skills in the "missingSkills" array.
        {{
            "matchScore": 45,
            "matchingSkills": ["skill1", "skill2"],
            "missingSkills": ["missing1", "missing2", "missing3", "missing4", "missing5", "missing6", "missing7", "missing8", "missing9", "missing10"],
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