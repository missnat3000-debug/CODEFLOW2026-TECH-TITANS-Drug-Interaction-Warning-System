from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import shutil
import os
import pytesseract
from PIL import Image
import re
app = FastAPI(
    title="MedPlus API",
    description="OCR Based Drug Interaction Warning System",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

drug_interactions = {
    ("warfarin", "aspirin"): {
        "severity": "Severe",
        "message": "Concurrent use increases the risk of internal bleeding."
    },

    ("paracetamol", "alcohol"): {
        "severity": "Moderate",
        "message": "May increase liver damage risk."
    },

    ("ibuprofen", "diclofenac"): {
        "severity": "High",
        "message": "Can increase stomach bleeding risk."
    },

    ("metformin", "alcohol"): {
        "severity": "Moderate",
        "message": "May increase lactic acidosis risk."
    }
}

class InteractionResponse(BaseModel):
    detected_medicines: List[str]
    severity: str
    warning: str
@app.get("/")
def home():
    return {
        "message": "Welcome to MedPlus Drug Interaction API"
    }
def extract_text(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text.lower()
def find_medicines(text):
    medicines_found = []

    medicine_list = [
        "warfarin",
        "aspirin",
        "paracetamol",
        "ibuprofen",
        "diclofenac",
        "metformin",
        "alcohol"
    ]

    for medicine in medicine_list:
        if re.search(rf"\b{medicine}\b", text):
            medicines_found.append(medicine)

    return medicines_found

def check_interaction(medicines):

    for drug1 in medicines:
        for drug2 in medicines:

            if drug1 != drug2:

                pair = (drug1, drug2)
                reverse_pair = (drug2, drug1)

                if pair in drug_interactions:
                    interaction = drug_interactions[pair]

                    return {
                        "severity": interaction["severity"],
                        "warning": interaction["message"]
                    }

                elif reverse_pair in drug_interactions:
                    interaction = drug_interactions[reverse_pair]

                    return {
                        "severity": interaction["severity"],
                        "warning": interaction["message"]
                    }

    return {
        "severity": "Safe",
        "warning": "No dangerous interaction detected."
    }

@app.post("/scan", response_model=InteractionResponse)
async def scan_medicine(file: UploadFile = File(...)):

    # Validate image
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file must be an image"
        )

    # Save uploaded image
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # OCR Extraction
    extracted_text = extract_text(file_path)

    # Detect Medicines
    medicines = find_medicines(extracted_text)

    if not medicines:
        return {
            "detected_medicines": [],
            "severity": "Unknown",
            "warning": "No medicines detected from image."
        }

    # Check Interaction
    result = check_interaction(medicines)

    return {
        "detected_medicines": medicines,
        "severity": result["severity"],
        "warning": result["warning"]
    }