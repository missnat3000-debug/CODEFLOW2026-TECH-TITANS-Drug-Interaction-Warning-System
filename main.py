from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import google.generativeai as genai
import cv2
import requests
import os
import json
import io
import sys
from werkzeug.utils import secure_filename

if sys.platform.startswith("win"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except:
        pass

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

GEMINI_API_KEY = "AIzaSyCnfhOQ9AHDdwib04U7QKY8K5TUGm1rNRg"

if GEMINI_API_KEY != "AIzaSyCnfhOQ9AHDdwib04U7QKY8K5TUGm1rNRg":
    genai.configure(api_key=GEMINI_API_KEY)
try:
    import easyocr

    reader = easyocr.Reader(['en'])
    print("EasyOCR Loaded")
except Exception as e:
    print("EasyOCR Error:", e)
    reader = None

@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "Medicine Scanner API Running"
    })
@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "success": False,
        "error": "Route not found"
    }), 404
def detect_qr(image_path):
    try:
        img = cv2.imread(image_path)

        detector = cv2.QRCodeDetector()

        data, bbox, _ = detector.detectAndDecode(img)

        if data:
            return data.strip()

    except Exception as e:
        print("QR ERROR:", e)

    return None

def lookup_barcode(barcode):
    try:
        url = f"https://api.fda.gov/drug/ndc.json?search=package_ndc:{barcode}&limit=1"

        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()

            if "results" in data:
                item = data["results"][0]

                return {
                    "brand_name": item.get("brand_name", "Unknown"),
                    "generic_name": item.get("generic_name", "Unknown"),
                    "manufacturer": item.get("labeler_name", "Unknown"),
                    "product_type": item.get("product_type", "Medicine")
                }

    except Exception as e:
        print("FDA LOOKUP ERROR:", e)

    return None

def analyze_with_gemini(image_path, text_data=""):

    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        return {
            "drug_present": True,
            "medicines": [
                {
                    "brand_name": "Demo Medicine",
                    "generic_name": "paracetamol",
                    "dosage": "500mg",
                    "category": "Painkiller",
                    "confidence": 95,
                    "risk_level": "low",
                    "description": "Used for fever and pain",
                    "warnings": "Do not exceed daily dosage"
                }
            ]
        }

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        image = Image.open(image_path)

        prompt = f"""
Analyze this medicine image.

OCR TEXT:
{text_data}

Return ONLY valid JSON:

{{
  "drug_present": true,
  "medicines": [
    {{
      "brand_name": "",
      "generic_name": "",
      "dosage": "",
      "category": "",
      "confidence": 90,
      "risk_level": "",
      "description": "",
      "warnings": ""
    }}
  ]
}}
"""

        response = model.generate_content([prompt, image])

        text = response.text.strip()

        if text.startswith("```"):
            text = text.replace("```json", "")
            text = text.replace("```", "")

        return json.loads(text)

    except Exception as e:
        print("GEMINI ERROR:", e)

        return {
            "drug_present": False,
            "medicines": []
        }

@app.route("/scan", methods=["POST"])
def scan():

    try:

        if "image" not in request.files:
            return jsonify({
                "success": False,
                "error": "No image uploaded"
            }), 400

        file = request.files["image"]

        filename = secure_filename(file.filename)

        image_path = os.path.join(UPLOAD_FOLDER, filename)

        file.save(image_path)
        extracted_text = ""

        if reader:
            try:
                result = reader.readtext(image_path)

                extracted_text = " ".join([x[1] for x in result])

            except Exception as e:
                print("OCR ERROR:", e)

        print("OCR:", extracted_text)

        medicines = []

        qr = detect_qr(image_path)

        if qr:
            print("QR FOUND:", qr)

            barcode_data = lookup_barcode(qr)

            if barcode_data:
                medicines.append(barcode_data)
        ai_result = analyze_with_gemini(
            image_path,
            extracted_text
        )

        ai_medicines = ai_result.get("medicines", [])

        medicines.extend(ai_medicines)
        unique = {}

        for med in medicines:
            key = med.get("generic_name", "").lower()

            if key:
                unique[key] = med

        medicines = list(unique.values())

        try:
            if os.path.exists(image_path):
                os.remove(image_path)
        except:
            pass
        return jsonify({
            "success": True,
            "drug_present": len(medicines) > 0,
            "total_medicines_detected": len(medicines),
            "medicines": medicines
        })

    except Exception as e:

        print("SCAN ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/scan-barcode", methods=["POST"])
def scan_barcode():

    try:

        data = request.get_json()

        barcode = data.get("barcode")

        if not barcode:
            return jsonify({
                "success": False,
                "error": "No barcode provided"
            }), 400

        result = lookup_barcode(barcode)

        if not result:
            return jsonify({
                "success": False,
                "error": "Barcode not found"
            }), 404

        return jsonify({
            "success": True,
            "drug_present": True,
            "total_medicines_detected": 1,
            "medicines": [result]
        })

    except Exception as e:

        print("BARCODE ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
if __name__ == "__main__":

    print("\nMedicine Scanner API Starting...\n")

    print("OPEN:")
    print("http://127.0.0.1:5000/\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
