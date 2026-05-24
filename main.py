from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

from PIL import Image
import google.generativeai as genai
import easyocr
import cv2
import requests

import os
import io
import sys
import json
import traceback
import uuid

if sys.platform.startswith("win"):
    try:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer,
            encoding="utf-8"
        )

        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer,
            encoding="utf-8"
        )
    except:
        pass

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

if not GEMINI_API_KEY:
    raise ValueError("Gemini API Key Missing")

genai.configure(api_key=GEMINI_API_KEY)

try:
    reader = easyocr.Reader(['en'])
    print("EasyOCR Loaded Successfully")

except Exception as e:
    print("EasyOCR Failed:", e)
    reader = None

def allowed_file(filename):
    return (
        "." in filename and
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )

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

        url = (
            f"https://api.fda.gov/drug/ndc.json"
            f"?search=package_ndc:{barcode}&limit=1"
        )

        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()

        if "results" not in data:
            return None

        item = data["results"][0]

        return {
            "brand_name": item.get("brand_name", "Unknown"),
            "generic_name": item.get("generic_name", "Unknown"),
            "manufacturer": item.get("labeler_name", "Unknown"),
            "product_type": item.get("product_type", "Medicine"),
            "confidence": 95,
            "risk_level": "medium",
            "description": "Detected via barcode database",
            "warnings": "Verify with packaging"
        }

    except Exception as e:
        print("FDA LOOKUP ERROR:", e)

    return None

def extract_text(image_path):

    if not reader:
        return ""

    try:

        results = reader.readtext(image_path)

        text = " ".join(
            [item[1] for item in results]
        )
        return text.strip()
    except Exception as e:
        print("OCR ERROR:", e)
        return ""

def analyze_with_gemini(image_path, text_data=""):

    try:

        model = genai.GenerativeModel(
            "gemini-1.5-flash"
        )

        image = Image.open(image_path)

        prompt = f"""
Analyze this medicine image carefully.

OCR TEXT:
{text_data}

Identify medicines if present.

Return ONLY VALID JSON.

Format:

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
Do not return markdown.
Do not return explanations.
Only return JSON.
"""

        response = model.generate_content(
            [prompt, image]
        )

        if not response.text:
            return {
                "drug_present": False,
                "medicines": []
            }

        text = response.text.strip()
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

        try:
            parsed = json.loads(text)

            if "medicines" not in parsed:
                parsed["medicines"] = []

            return parsed

        except Exception as json_error:

            print("JSON PARSE ERROR:", json_error)
            print("RAW RESPONSE:", text)

            return {
                "drug_present": False,
                "medicines": []
            }
    except Exception as e:

        print("GEMINI ERROR:")
        traceback.print_exc()

        return {
            "drug_present": False,
            "medicines": []
        }
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

@app.route("/scan", methods=["POST"])
def scan():
    image_path = None

    try:

        if "image" not in request.files:
            return jsonify({
                "success": False,
                "error": "No image uploaded"
            }), 400

        file = request.files["image"]
        if file.filename == "":
            return jsonify({
                "success": False,
                "error": "Empty filename"
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "error": "Invalid file type"
            }), 400

        extension = file.filename.rsplit(".", 1)[1]

        filename = (
            f"{uuid.uuid4()}.{extension}"
        )

        filename = secure_filename(filename)

        image_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )
        file.save(image_path)

        print("IMAGE SAVED:", image_path)

        extracted_text = extract_text(image_path)

        print("OCR TEXT:", extracted_text)

        medicines = []

        qr_data = detect_qr(image_path)

        if qr_data:

            print("QR FOUND:", qr_data)

            barcode_result = lookup_barcode(qr_data)

            if barcode_result:
                medicines.append(barcode_result)

        ai_result = analyze_with_gemini(
            image_path,
            extracted_text
        )

        ai_medicines = ai_result.get(
            "medicines",
            []
        )
        medicines.extend(ai_medicines)
        unique = {}

        for med in medicines:

            key = med.get(
                "generic_name",
                ""
            ).lower()

            if key:
                unique[key] = med

        medicines = list(unique.values())
        return jsonify({
            "success": True,
            "drug_present": len(medicines) > 0,
            "total_medicines_detected": len(medicines),
            "ocr_text": extracted_text,
            "medicines": medicines
        })

    except Exception as e:

        print("SCAN ERROR:")
        traceback.print_exc()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        try:
            if image_path and os.path.exists(image_path):
                os.remove(image_path)

        except Exception as cleanup_error:
            print("CLEANUP ERROR:", cleanup_error)

@app.route("/scan-barcode", methods=["POST"])
def scan_barcode():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid JSON"
            }), 400

        barcode = data.get("barcode")

        if not barcode:
            return jsonify({
                "success": False,
                "error": "Barcode missing"
            }), 400

        result = lookup_barcode(barcode)

        if not result:
            return jsonify({
                "success": False,
                "error": "Medicine not found"
            }), 404

        return jsonify({
            "success": True,
            "drug_present": True,
            "total_medicines_detected": 1,
            "medicines": [result]
        })

    except Exception as e:

        print("BARCODE ERROR:")
        traceback.print_exc()

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
        debug=False,
        threaded=True
    )
