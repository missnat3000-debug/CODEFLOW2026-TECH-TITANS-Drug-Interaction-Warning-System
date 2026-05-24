from dotenv import load_dotenv
import os
import io
import sys
import json
import traceback
import uuid

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from PIL import Image
import google.generativeai as genai
import easyocr
import cv2
import requests

load_dotenv()

# =========================
# UTF-8 FIX (Windows)
# =========================
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

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing in .env")

genai.configure(api_key=GEMINI_API_KEY)

# =========================
# OCR INIT
# =========================
try:
    reader = easyocr.Reader(['en'])
    print("EasyOCR Loaded Successfully")
except:
    reader = None


# =========================
# UTIL FUNCTIONS
# =========================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def detect_qr(image_path):
    try:
        img = cv2.imread(image_path)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(img)
        return data.strip() if data else None
    except:
        return None


def extract_text(image_path):
    if not reader:
        return ""
    try:
        results = reader.readtext(image_path)
        return " ".join([r[1] for r in results]).strip()
    except:
        return ""


def lookup_barcode(barcode):
    try:
        url = f"https://api.fda.gov/drug/ndc.json?search=package_ndc:{barcode}&limit=1"
        r = requests.get(url, timeout=10)

        if r.status_code != 200:
            return None

        data = r.json()
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

    except:
        return None


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

# =========================
# FRONTEND ROUTE (FIXED)
# =========================
@app.route("/")
def serve_frontend():
    return send_from_directory(os.getcwd(), "front.html")


# =========================
# API STATUS ROUTE
# =========================
@app.route("/api")
def api_home():
    return jsonify({"success": True, "message": "Medicine Scanner API Running"})


# =========================
# SCAN IMAGE
# =========================
@app.route("/scan", methods=["POST"])
def scan():
    image_path = None

    try:
        if "image" not in request.files:
            return jsonify({"success": False, "error": "No image uploaded"}), 400

        file = request.files["image"]

        if file.filename == "":
            return jsonify({"success": False, "error": "Empty filename"}), 400

        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Invalid file type"}), 400

        ext = file.filename.rsplit(".", 1)[1]
        filename = f"{uuid.uuid4()}.{ext}"
        image_path = os.path.join(UPLOAD_FOLDER, filename)

        file.save(image_path)

        text = extract_text(image_path)
        qr = detect_qr(image_path)

        medicines = []

        if qr:
            bar = lookup_barcode(qr)
            if bar:
                medicines.append(bar)

        ai = analyze_with_gemini(image_path, text)
        medicines.extend(ai.get("medicines", []))

        # remove duplicates
        unique = {}
        for m in medicines:
            key = m.get("generic_name", "").lower()
            if key:
                unique[key] = m

        return jsonify({
            "success": True,
            "drug_present": len(unique) > 0,
            "total_medicines_detected": len(unique),
            "ocr_text": text,
            "medicines": list(unique.values())
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)


# =========================
# BARCODE API
# =========================
@app.route("/scan-barcode", methods=["POST"])
def scan_barcode():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid JSON"}), 400

        barcode = data.get("barcode")
        if not barcode:
            return jsonify({"success": False, "error": "Barcode missing"}), 400

        result = lookup_barcode(barcode)

        if not result:
            return jsonify({"success": False, "error": "Medicine not found"}), 404

        return jsonify({
            "success": True,
            "drug_present": True,
            "total_medicines_detected": 1,
            "medicines": [result]
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    print("Medicine Scanner API Starting...")
    print("[http://127.0.0.1:5000/](http://127.0.0.1:5000/)")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
