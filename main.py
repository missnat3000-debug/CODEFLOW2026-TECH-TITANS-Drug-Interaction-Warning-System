from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import google.generativeai as genai
import io
import json
import re

app = Flask(__name__)
CORS(app)

# PUT YOUR GEMINI API KEY HERE
genai.configure(api_key="YOUR_GEMINI_API_KEY")

model = genai.GenerativeModel("gemini-1.5-flash")

@app.route("/")
def home():
    return jsonify({
        "message": "MedPlus Gemini Backend Running"
    })

@app.route("/scan", methods=["POST"])
def scan():
    try:

        if "image" not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        file = request.files["image"]

        image = Image.open(file.stream)

        prompt = """
You are a medical AI assistant.

Analyze the uploaded medicine image carefully.

Tasks:
1. Detect ALL medicine names visible.
2. Identify generic names if possible.
3. Identify dosage strength.
4. Detect dangerous drug interactions.
5. Detect controlled substances.
6. Return risk level for every medicine.

Return ONLY valid JSON in this format:

{
  "medicines": [
    {
      "brand_name": "Paracetamol",
      "generic_name": "Acetaminophen",
      "dosage": "500mg",
      "confidence": 98,
      "risk_level": "SAFE",
      "risk_warning": "Usually safe when taken correctly"
    }
  ],
  "interactions": [
    {
      "type": "SEVERE",
      "drugs": ["Warfarin", "Aspirin"],
      "warning": "High bleeding risk"
    }
  ]
}

Rules:
- Never hallucinate medicine names
- Only detect visible medicines
- If no medicine found return empty arrays
- Use medical knowledge for interactions
"""

        response = model.generate_content([prompt, image])

        text = response.text

        # Clean markdown
        text = re.sub(r"```json", "", text)
        text = re.sub(r"```", "", text)

        data = json.loads(text)

        return jsonify(data)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
