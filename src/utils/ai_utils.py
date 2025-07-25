import os
import logging
import vertexai
from vertexai.generative_models import GenerativeModel

# --- CONFIGURAZIONE CENTRALE AI (FINALE E CORRETTA) ---
PROJECT_ID = os.getenv('GCP_PROJECT')
LOCATION = "global"

# Modelli aggiornati alla versione 2.5 come da analisi finale
PLANNING_MODEL = "gemini-2.5-pro"
EXECUTION_MODEL = "gemini-2.5-flash"

_is_vertex_ai_initialized = False
_model_instances = {}

def get_gemini_model(model_name: str) -> GenerativeModel:
    """Inizializza e restituisce un'istanza del modello Gemini specificato."""
    global _is_vertex_ai_initialized, _model_instances
    
    if model_name in _model_instances:
        return _model_instances[model_name]

    try:
        if not _is_vertex_ai_initialized:
            if not PROJECT_ID:
                raise ValueError("Variabile d'ambiente GCP_PROJECT non impostata.")
            
            logging.info(f"Inizializzazione di Vertex AI per il progetto '{PROJECT_ID}' in '{LOCATION}'...")
            vertexai.init(project=PROJECT_ID, location=LOCATION)
            _is_vertex_ai_initialized = True
            logging.info("✅ Connessione a Vertex AI stabilita.")

        logging.info(f"Caricamento del modello AI: {model_name}")
        model = GenerativeModel(model_name=model_name)
        _model_instances[model_name] = model
        return model
    except Exception as e:
        logging.error(f"❌ Fallimento critico durante l'inizializzazione di Vertex AI: {e}", exc_info=True)
        raise

def generate_response(model: GenerativeModel, prompt: str) -> str:
    """Chiama il modello AI fornito per generare una risposta."""
    try:
        logging.info(f"Invio richiesta al modello '{model._model_name}'...")
        response = model.generate_content(prompt)
        
        if not response.candidates:
             raise ValueError("La risposta dell'API non contiene candidati validi.")
        return response.text
    except Exception as e:
        logging.error(f"❌ Errore durante la chiamata a Gemini: {e}", exc_info=True)
        return None