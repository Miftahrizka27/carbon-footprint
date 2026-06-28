import pickle
import os

# Emission factors (kg CO2 per unit)
EMISSION_FACTORS = {
    "listrik": 0.87,      # kg CO2 per kWh (Indonesia)
    "air": 0.001,         # kg CO2 per liter
    "transportasi": 0.21, # kg CO2 per km (motor/mobil rata-rata)
    "sampah": 2.5,        # kg CO2 per kg sampah makanan
}

RATA_RATA_INDONESIA = { # berdasarkan ESDM (2022)
    "listrik": 87,
    "air": 3,
    "transportasi": 63,
    "sampah": 12.5,
    "total": 165.5
}

# DT
_model = None

def _load_model():
    """Load model Decision Tree"""
    global _model
    if _model is None:
        model_path = os.path.join(os.path.dirname(__file__), "carbon_model.pkl")
        if os.path.exists(model_path):
            with open(model_path, "rb") as f:
                _model = pickle.load(f)
        else:
            print("⚠️  carbon_model.pkl tidak ditemukan, fallback ke if-else.")
    return _model


# MAIN
def hitung_carbon(listrik_kwh, air_liter, transportasi_km, sampah_kg): # berdasarkan Kementerian ESDM (2022)
    hasil = {
        "listrik": listrik_kwh * EMISSION_FACTORS["listrik"],
        "air": air_liter * EMISSION_FACTORS["air"],
        "transportasi": transportasi_km * EMISSION_FACTORS["transportasi"],
        "sampah": sampah_kg * EMISSION_FACTORS["sampah"],
    }
    hasil["total"] = sum(hasil.values())
    return hasil


def konversi_metafora(total_co2):
    return {
        "pohon": round(total_co2 / 21, 2),    
        "rupiah": round(total_co2 * 500),     
    }


def cek_potensi_hemat(listrik_kwh, air_liter, transportasi_km, sampah_kg):
    model = _load_model()
    if model is not None:
        fitur = [[listrik_kwh, air_liter, transportasi_km, sampah_kg]]
        prediksi = model.predict(fitur)[0]
        return round(prediksi, 2)
    return 0.0

def cek_level(total_co2): # dari DEN 2022
    if total_co2 < 150:
        # Di bawah rata-rata nasional — bagus
        return "rendah"
    elif total_co2 < 300:
        # Sekitar rata-rata hingga 1.5x rata-rata nasional
        return "sedang"
    else:
        # Di atas 1.5x rata-rata — perlu perhatian
        return "tinggi"
    
