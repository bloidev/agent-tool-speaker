from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sounddevice as sd
import soundfile as sf
from piper import PiperVoice
import io
import os
import wave
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Local TTS Piper")

# Ruta al modelo descargado
MODEL_PATH = os.path.join("models", "es_MX-claude-high.onnx")
voice = None

# Validar que los archivos existan al iniciar
if not os.path.exists(MODEL_PATH):
    logger.warning(f"⚠️ ADVERTENCIA: No se encontró el modelo en {MODEL_PATH}")
    logger.warning("Descarga los archivos .onnx y .onnx.json desde Hugging Face y ponlos en la carpeta /models")
else:
    try:
        voice = PiperVoice.load(MODEL_PATH)
        logger.info("✅ Modelo de Piper cargado correctamente")
    except Exception as e:
        logger.error(f"❌ Error cargando el modelo: {e}")

class TTSRequest(BaseModel):
    text: str

@app.post("/speak")
async def speak(data: TTSRequest):
    if not data.text.strip():
        raise HTTPException(status_code=400, detail="Texto vacío")

    if voice is None:
        logger.error("❌ Modelo de Piper no está disponible")
        raise HTTPException(status_code=503, detail="Modelo de Piper no disponible. Descarga el modelo en la carpeta /models")

    try:
        logger.info(f"🔊 Sintetizando: {data.text}")

        # Generar audio usando el generador de Piper
        audio_bytes_list = []
        samplerate = 22050

        for chunk in voice.synthesize(data.text):
            # Cada chunk es un AudioChunk con audio_int16_bytes
            audio_bytes_list.append(chunk.audio_int16_bytes)
            samplerate = chunk.sample_rate

        # Concatenar todos los bytes
        audio_bytes = b"".join(audio_bytes_list)
        logger.info(f"📊 Audio generado: {len(audio_bytes)} bytes")

        # Convertir bytes PCM 16-bit a numpy array float32
        audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        # Reproducir audio en los parlantes
        logger.info(f"▶️ Reproduciendo audio ({len(audio_data)} muestras a {samplerate}Hz)")
        sd.play(audio_data, samplerate)
        sd.wait()
        logger.info("✅ Audio reproducido exitosamente")

        return {"status": "success", "text": data.text}
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)