from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from backend.calculator import hitung_carbon, konversi_metafora, cek_level
from backend.chatbot import get_saran, chat_lanjutan, analisis_tagihan, client
from fastapi.responses import FileResponse
from fastapi import UploadFile, File
import pdfplumber
import io
import json
import base64

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
except Exception as e:
    print(f"Warning: {e}")

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

@app.post("/hitung")
def hitung(data: InputCarbon):
    try:
        hasil = hitung_carbon(data.listrik_kwh, data.air_liter, data.transportasi_km, data.sampah_kg)
        metafora = konversi_metafora(hasil["total"])
        level = cek_level(hasil["total"])
        saran = ""
        if level == "tinggi":
            saran = get_saran(data.nama, hasil, level)
        return {"nama": data.nama, "hasil": hasil, "metafora": metafora, "level": level, "saran": saran}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/chat")
def chat(data: ChatRequest):
    try:
        riwayat = [{"role": m.role, "content": m.content} for m in data.riwayat_chat]
        balasan = chat_lanjutan(data.nama, data.hasil_carbon, riwayat)
        return {"balasan": balasan}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/upload-tagihan")
async def upload_tagihan(file: UploadFile = File(...)):
    try:
        konten = await file.read()

        if file.content_type == "application/pdf":
            teks = ""
            with pdfplumber.open(io.BytesIO(konten)) as pdf:
                for page in pdf.pages:
                    teks += page.extract_text() or ""
            if not teks.strip():
                raise HTTPException(status_code=400, detail="Tidak bisa membaca teks dari PDF.")
            hasil_ai = analisis_tagihan(teks)

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
            raise HTTPException(status_code=400, detail="Format tidak didukung. Gunakan PDF atau gambar.")

        try:
            hasil = json.loads(hasil_ai)
        except:
            hasil = {"raw": hasil_ai}

        return {"analisis": hasil}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return FileResponse("frontend/index.html")

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
