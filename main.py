def analyze_with_gemini(image_path, text_data=""):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
You are a pharmaceutical medicine detection AI.
Analyze the medicine image and OCR text.
OCR TEXT:
{text_data}
IMPORTANT: Return ONLY STRICT VALID JSON. Do NOT return markdown or ```json.
JSON FORMAT:
{{
  "drug_present": true,
  "medicines": [
    {{
      "brand_name": "Paracetamol",
      "generic_name": "Paracetamol",
      "confidence": 95,
      "dosage": "500mg",
      "manufacturer": "Unknown",
      "risk_level": "low",
      "description": "Pain reliever",
      "warnings": "Do not overdose",
      "side_effects": "Nausea",
      "composition": ["Paracetamol"],
      "risk_reason": "Safe at normal dosage"
    }}
  ]
}}
"""

        with Image.open(image_path) as img:
            response = model.generate_content(
                [prompt, img],
                generation_config={
                    "temperature": 0,
                    "response_mime_type": "application/json"
                }
            )

        # Catch safety blocks or empty responses
        if not response.parts:
            print("GEMINI ERROR: Response was blocked or empty.")
            return {"drug_present": False, "medicines": []}

        raw = response.text.strip()

        # --- THE FIX: Clean up any accidental Markdown from Gemini ---
        if raw.startswith("```"):
            raw = raw.replace("```json", "").replace("```", "").strip()
        # -------------------------------------------------------------

        print("\n===== GEMINI RESPONSE =====")
        print(raw)

        parsed = json.loads(raw)

        if "medicines" not in parsed:
            parsed["medicines"] = []

        return parsed

    except Exception as e:
        print("GEMINI PARSE ERROR:", str(e))
        return {
            "drug_present": False,
            "medicines": []
        }
