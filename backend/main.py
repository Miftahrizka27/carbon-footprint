from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from backend.calculator import hitung_carbon, konversi_metafora, cek_level
from backend.chatbot import get_saran, chat_lanjutan
from fastapi.responses import FileResponse
from fastapi import UploadFile, File
import pdfplumber
from PIL import Image
import pytesseract
import io
import json
import tempfile
import os

app = FastAPI()

# Izinkan frontend akses backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# Model data input
class InputCarbon(BaseModel):
    nama: str
    listrik_kwh: float
    air_liter: float
    transportasi_km: float
    sampah_kg: float

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    nama: str
    hasil_carbon: dict
    riwayat_chat: List[ChatMessage]

# Route hitung carbon
@app.post("/hitung")
def hitung(data: InputCarbon):
    hasil = hitung_carbon(
        data.listrik_kwh,
        data.air_liter,
        data.transportasi_km,
        data.sampah_kg
    )
    metafora = konversi_metafora(hasil["total"])
    level = cek_level(hasil["total"])
    saran = ""

    if level == "tinggi":
        saran = get_saran(data.nama, hasil, level)

    return {
        "nama": data.nama,
        "hasil": hasil,
        "metafora": metafora,
        "level": level,
        "saran": saran
    }

# Route chat lanjutan
@app.post("/chat")
def chat(data: ChatRequest):
    riwayat = [{"role": m.role, "content": m.content} 
               for m in data.riwayat_chat]
    balasan = chat_lanjutan(data.nama, data.hasil_carbon, riwayat)
    return {"balasan": balasan}

# Route upload tagihan
@app.post("/upload-tagihan")
async def upload_tagihan(file: UploadFile = File(...)):
    teks = ""
    
    konten = await file.read()
    
    if file.content_type == "application/pdf":
        with pdfplumber.open(io.BytesIO(konten)) as pdf:
            for page in pdf.pages:
                teks += page.extract_text() or ""
    
    elif file.content_type in ["image/jpeg", "image/png", "image/jpg"]:
        img = Image.open(io.BytesIO(konten))
        teks = pytesseract.image_to_string(img, lang="ind+eng")
    
    else:
        return {"error": "Format tidak didukung. Gunakan PDF atau gambar."}
    
    if not teks.strip():
        return {"error": "Tidak bisa membaca teks dari file."}
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(teks)
        tmp_path = f.name
    
    hasil_ai = analisis_tagihan(teks)
    os.unlink(tmp_path)
    
    try:
        hasil = json.loads(hasil_ai)
    except:
        hasil = {"raw": hasil_ai}
    
    return {"teks": teks, "analisis": hasil}

# Route cek server
@app.get("/")
def root():
    return FileResponse("frontend/index.html")