import os
import logging
import vertexai
from vertexai.generative_models import GenerativeModel

# --- CONFIGURAZIONE CENTRALE AI ---
PROJECT_ID = os.getenv('GCP_PROJECT')
LOCATION = "europe-west1"  # Regione per le API Vertex AI

# Modello per task complessi (pianificazione)
PLANNING_MODEL = "gemini-1.5-pro-latest"
# Modello per task veloci (generazione codice)
EXECUTION_MODEL = "gemini-1.5-flash-001"

_model_instances = {}

def get_gemini_model(model_name: str) -> GenerativeModel:
    """
    Inizializza e restituisce un'istanza del modello Gemini specificato.
    Usa un sistema di caching per non reinizializzare lo stesso modello.
    """
    global _model_instances
    if model_name in _model_instances:
        return _model_instances[model_name]

    try:
        if not PROJECT_ID:
            logging.error("La variabile d'ambiente GCP_PROJECT non è impostata nel workflow.")
            raise ValueError("GCP_PROJECT non trovato.")
        
        # Inizializza Vertex AI solo la prima volta
        if not vertexai.preview.global_config.project:
             logging.info(f"Prima inizializzazione di Vertex AI per il progetto '{PROJECT_ID}' in '{LOCATION}'...")
             vertexai.init(project=PROJECT_ID, location=LOCATION)
             logging.info("✅ Connessione a Vertex AI stabilita con successo.")

        logging.info(f"Caricamento del modello AI: {model_name}")
        model = GenerativeModel(model_name=model_name)
        _model_instances[model_name] = model
        return model

    except Exception as e:
        logging.error(f"❌ Fallimento critico durante l'inizializzazione di Vertex AI o il caricamento del modello: {e}", exc_info=True)
        raise

def generate_response(model: GenerativeModel, prompt: str, timeout: int = 600) -> str:
    """
    Chiama il modello AI fornito per generare una risposta.
    """
    try:
        logging.info(f"Invio richiesta al modello '{model._model_name}' (timeout: {timeout}s)...")
        generation_config = {"request_timeout": float(timeout)}
        response = model.generate_content(prompt, generation_config=generation_config)
        
        if not response.candidates:
             raise ValueError("La risposta dell'API non contiene candidati validi.")

        return response.text
    except Exception as e:
        logging.error(f"❌ Errore durante la chiamata a Gemini: {e}", exc_info=True)
        return None