from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from backend.calculator import hitung_carbon, konversi_metafora, cek_level
from backend.chatbot import get_saran, chat_lanjutan, analisis_tagihan
from fastapi.responses import FileResponse
from fastapi import UploadFile, File
import pdfplumber
from PIL import Image
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

try:
    app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
except Exception as e:
    print(f"Warning: Frontend directory tidak ditemukan - {e}")

# ============ MODEL DATA ============
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

# ============ ROUTE HITUNG CARBON ============
@app.post("/hitung")
def hitung(data: InputCarbon):
    """Hitung footprint carbon dari input user"""
    try:
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
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============ ROUTE CHAT LANJUTAN ============
@app.post("/chat")
def chat(data: ChatRequest):
    """Chat lanjutan dengan AI"""
    try:
        riwayat = [{"role": m.role, "content": m.content} 
                   for m in data.riwayat_chat]
        balasan = chat_lanjutan(data.nama, data.hasil_carbon, riwayat)
        return {"balasan": balasan}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============ ROUTE UPLOAD TAGIHAN ============
#ROUTE UPLOAD TAGIHAN
@app.post("/upload-tagihan")
async def upload_tagihan(file: UploadFile = File(...)):
    try:
        konten = await file.read()
        print(f"File received: {file.filename}, type: {file.content_type}")
        
        if file.content_type == "application/pdf":
            with pdfplumber.open(io.BytesIO(konten)) as pdf:
                for page in pdf.pages:
                    teks += page.extract_text() or ""
        
        elif file.content_type in ["image/jpeg", "image/png", "image/jpg"]:
            b64 = base64.b64encode(konten).decode("utf-8")
            response = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": [
                         {"type": "image_url", "image_url": {"url": f"data:{file.content_type};base64,{b64}"}},
                         {"type": "text", "text": 'Analisis tagihan ini, ekstrak dalam JSON: {"kategori": "listrik/air/transportasi/sampah/lainnya", "nilai": angka, "deskripsi": "...", "confidence": "tinggi/sedang/rendah"}. Balas HANYA JSON.'}
                    ]
                }]
            )
            hasil_ai = response.choices[0].message.content
        
        else:
            raise HTTPException(
                status_code=400, 
                detail="Format tidak didukung. Gunakan PDF atau gambar."
            )
        
        if not teks.strip():
            raise HTTPException(
                status_code=400, 
                detail="Tidak bisa membaca teks dari file."
            )
        
        # Analisis dengan AI
        hasil_ai = analysis_tagihan(teks)
        
        # Parse JSON
        try:
        hasil = json.loads(hasil_ai)
    except Exception as e:
        print(f"JSON parse error: {e}, raw: {hasil_ai}")
        hasil = {"raw": hasil_ai}

    return {"analisis": hasil}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ============ ROUTE ROOT ============
@app.get("/")
def root():
    """Serve frontend"""
    return FileResponse("frontend/index.html")

@app.get("/health")
def health_check():
    """Health check"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
