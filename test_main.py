import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import numpy as np
from main import app, TTSRequest

client = TestClient(app)




class TestTTSRequest:
    """Pruebas para el modelo de datos TTSRequest"""

    def test_valid_request(self):
        """Verifica que TTSRequest acepta texto válido"""
        request = TTSRequest(text="Hola mundo")
        assert request.text == "Hola mundo"

    def test_empty_text_validation(self):
        """Verifica que TTSRequest acepta texto vacío (validación en endpoint)"""
        request = TTSRequest(text="")
        assert request.text == ""

    def test_long_text(self):
        """Verifica que TTSRequest maneja textos largos"""
        long_text = "a" * 5000
        request = TTSRequest(text=long_text)
        assert request.text == long_text


class TestSpeakEndpoint:
    """Pruebas para el endpoint POST /speak"""

    @patch('main.voice')
    @patch('soundfile.read')
    @patch('sounddevice.play')
    @patch('sounddevice.wait')
    def test_speak_success(self, mock_wait, mock_play, mock_sf_read, mock_voice):
        """Verifica que /speak genera audio exitosamente"""
        mock_voice.synthesize.return_value = None
        mock_sf_read.return_value = (np.array([0.1, 0.2, 0.3]), 22050)

        response = client.post("/speak", json={"text": "Hola"})

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["text"] == "Hola"
        mock_voice.synthesize.assert_called_once()
        mock_play.assert_called_once()
        mock_wait.assert_called_once()

    def test_speak_empty_text(self):
        """Verifica que /speak rechaza texto vacío"""
        response = client.post("/speak", json={"text": ""})

        assert response.status_code == 400
        assert "vacío" in response.json()["detail"].lower()

    def test_speak_whitespace_only(self):
        """Verifica que /speak rechaza solo espacios en blanco"""
        response = client.post("/speak", json={"text": "   \n\t  "})

        assert response.status_code == 400

    @patch('main.voice')
    @patch('soundfile.read')
    @patch('sounddevice.play')
    @patch('sounddevice.wait')
    def test_speak_spanish_text(self, mock_wait, mock_play, mock_sf_read, mock_voice):
        """Verifica que /speak maneja correctamente texto en español"""
        mock_voice.synthesize.return_value = None
        mock_sf_read.return_value = (np.array([0.1, 0.2]), 22050)

        response = client.post("/speak", json={"text": "¡Hola! ¿Cómo estás?"})

        assert response.status_code == 200
        assert response.json()["text"] == "¡Hola! ¿Cómo estás?"

    @patch('main.voice')
    @patch('soundfile.read')
    @patch('sounddevice.play')
    @patch('sounddevice.wait')
    def test_speak_with_synthesize_error(self, mock_wait, mock_play, mock_sf_read, mock_voice):
        """Verifica manejo de errores en synthesize"""
        mock_voice.synthesize.side_effect = Exception("Error de síntesis")

        response = client.post("/speak", json={"text": "Hola"})

        assert response.status_code == 500

    @patch('main.voice')
    @patch('soundfile.read')
    @patch('sounddevice.play')
    @patch('sounddevice.wait')
    def test_speak_with_audio_read_error(self, mock_wait, mock_play, mock_sf_read, mock_voice):
        """Verifica manejo de errores en lectura de audio"""
        mock_voice.synthesize.return_value = None
        mock_sf_read.side_effect = Exception("Error leyendo audio")

        response = client.post("/speak", json={"text": "Hola"})

        assert response.status_code == 500

    def test_speak_missing_text_field(self):
        """Verifica que /speak rechaza peticiones sin campo text"""
        response = client.post("/speak", json={})

        assert response.status_code == 422

    def test_speak_invalid_json(self):
        """Verifica manejo de JSON inválido"""
        response = client.post("/speak", data="invalid", headers={"Content-Type": "application/json"})

        assert response.status_code == 422


class TestEndpoints:
    """Pruebas de disponibilidad de endpoints"""

    def test_app_startup(self):
        """Verifica que la aplicación se inicia correctamente"""
        assert app.title == "Local TTS Piper"

    def test_post_speak_exists(self):
        """Verifica que el endpoint /speak existe"""
        response = client.post("/speak", json={"text": "test"})
        assert response.status_code in [200, 500]

    def test_docs_available(self):
        """Verifica que la documentación está disponible"""
        response = client.get("/docs")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
