from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
import re
import json
import os 

app = Flask(__name__)
CORS(app) 


GROQ_API_KEY = os.getenv("GROQ_API_KEY")


if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None

def extract_tokens(text):
    """Text se important tech keywords nikalne ka logic"""
    text = text.lower()
    # capture alphanumeric and symbols like #, +, . (e.g. c++, node.js)
    words = re.findall(r'\b[a-z0-9#\+\.]+\b', text)
    stopwords = {'the', 'and', 'a', 'of', 'to', 'in', 'is', 'for', 'with', 'on', 'an', 'by', 'using', 'from', 'we', 'our', 'experience', 'skills'}
    return set([word for word in words if word not in stopwords and len(word) > 1])

@app.route('/api/analyze', methods=['POST'])
def analyze_gap():
    data = request.json
    syllabus = data.get('syllabus', '')
    jd = data.get('jd', '')
    
    if not syllabus or not jd:
        return jsonify({"status": "error", "message": "Syllabus and JD are required!"}), 400
        
    # Base Token Extraction
    syllabus_tokens = extract_tokens(syllabus)
    jd_tokens = extract_tokens(jd)
    
    # Structural Matching
    matching_skills = list(jd_tokens.intersection(syllabus_tokens))
    missing_skills = list(jd_tokens.difference(syllabus_tokens))
    
    # Density Score
    match_score = round((len(matching_skills) / len(jd_tokens)) * 100) if len(jd_tokens) > 0 else 0

    # Groq Integration for Industry Trends
    market_trends = []
    

    if client and GROQ_API_KEY:
        try:
            prompt = f"""
            You are a technical career advisor. Analyze this Job Description: '{jd[:500]}'
            The student is missing these skills: {", ".join(missing_skills[:10])}
            Suggest exactly 6 high-demand modern tech tools, frameworks, or ecosystem skills the student should learn to bridge this gap.
            Return ONLY a raw JSON array of strings. Example: ["Docker", "Next.js", "Kubernetes", "Redis"]
            """
            
            completion = client.chat.completions.create(
                model="llama3-8b-8192", 
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=150
            )
            
            ai_response = completion.choices[0].message.content.strip()
            # Clean formatting if AI adds markdown code blocks
            if "```json" in ai_response:
                ai_response = ai_response.split("```json")[1].split("```")[0].strip()
            elif "```" in ai_response:
                ai_response = ai_response.split("```")[1].strip()
                
            market_trends = json.loads(ai_response)
        except Exception as e:
            print(f"AI Error: {e}")
            market_trends = missing_skills[:6] # Fallback if AI fails
    else:
        # Agar Render pe API key set nahi ki hai, toh fallback daal diya
        market_trends = missing_skills[:6]

    return jsonify({
        "status": "success",
        "matchScore": match_score,
        "matchingSkills": matching_skills,
        "missingSkills": missing_skills,
        "marketTrendsAdvice": market_trends
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)