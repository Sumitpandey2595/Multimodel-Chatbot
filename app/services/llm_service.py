import os
import logging
from typing import Optional, List, Dict, Any
from backend.app.config import settings

logger = logging.getLogger("uvicorn.error")

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

class LLMService:
    """
    Clean abstraction layer for Multimodal LLM interactions.
    Currently integrates Google Gemini (with multimodal vision & embeddings support).
    If no API key is provided, gracefully operates in interactive demo mode.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.DEFAULT_LLM_MODEL
        self.embedding_model = settings.EMBEDDING_MODEL
        self._init_client()

    def _init_client(self):
        if self.api_key and HAS_GENAI:
            try:
                genai.configure(api_key=self.api_key)
                logger.info(f"Gemini AI service initialized with model '{self.model_name}'.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini AI: {e}")
        else:
            logger.info("Gemini API key not detected. Operating in simulated demo mode.")

    def is_configured(self) -> bool:
        return bool(self.api_key and HAS_GENAI)

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generates text completion with optional conversation context.
        """
        if not self.is_configured():
            return self._mock_text_response(prompt, conversation_history)

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction
            )

            # Build history if provided
            if conversation_history:
                chat = model.start_chat(history=[
                    {
                        "role": "user" if msg["role"] == "user" else "model",
                        "parts": [msg["content"]]
                    }
                    for msg in conversation_history
                ])
                response = chat.send_message(prompt)
            else:
                response = model.generate_content(prompt)

            return response.text.strip()
        except Exception as e:
            logger.error(f"Error in Gemini text generation: {e}")
            return f"I encountered an error communicating with the AI service: {str(e)}. Please check your API key in .env."

    def generate_multimodal(
        self,
        prompt: str,
        image_path: str,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Processes image + text prompt using multimodal vision capabilities.
        """
        if not self.is_configured():
            return (
                f"[Multimodal Image Analysis Demo Mode]\n"
                f"Received your question: \"{prompt}\" along with image: '{os.path.basename(image_path)}'.\n\n"
                f"To enable live visual understanding and diagram explanation, add your GEMINI_API_KEY to backend/.env."
            )

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction
            )
            # Upload image file to Gemini File API or send as inline bytes
            uploaded_file = genai.upload_file(image_path)
            response = model.generate_content([uploaded_file, prompt])
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error in Gemini multimodal image analysis: {e}")
            return f"Error analyzing image: {str(e)}. Please verify file format and API key."

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generates vector embedding for a single text chunk.
        """
        if not self.is_configured():
            return self._generate_fallback_embedding(text)

        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.warning(f"Error generating Gemini embedding ({e}); using local fallback vector.")
            return self._generate_fallback_embedding(text)

    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generates vector embedding for a search query.
        """
        if not self.is_configured():
            return self._generate_fallback_embedding(query)

        try:
            result = genai.embed_content(
                model=self.embedding_model,
                content=query,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            logger.warning(f"Error generating query embedding ({e}); using local fallback vector.")
            return self._generate_fallback_embedding(query)

    async def transcribe_audio_native(self, audio_path: str) -> str:
        """
        Transcribes audio natively using Gemini multimodal audio understanding.
        """
        if not self.is_configured():
            return "Audio received. Add GEMINI_API_KEY to .env for real-time AI transcription."

        try:
            model = genai.GenerativeModel(model_name=self.model_name)
            audio_file = genai.upload_file(audio_path)
            prompt = "Please provide an accurate, word-for-word transcription of this audio recording."
            response = model.generate_content([audio_file, prompt])
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error transcribing audio with Gemini: {e}")
            return f"Audio transcription error: {str(e)}"

    def _generate_fallback_embedding(self, text: str, dim: int = 768) -> List[float]:
        """
        Deterministic, local frequency-based vector representation (dim=768).
        Ensures RAG works out of the box even without network or API keys.
        """
        import hashlib
        import math

        vector = [0.0] * dim
        words = text.lower().split()
        if not words:
            return vector

        for word in words:
            # Hash word into bucket
            h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if (h // dim) % 2 == 0 else -1.0
            vector[idx] += sign

        # Normalize vector
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector

    def _mock_text_response(self, prompt: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Friendly demo response when GEMINI_API_KEY is not set."""
        p_lower = prompt.lower()
        if "name" in p_lower:
            return "Hello! I am your Multimodal AI Chatbot assistant. I can help with documents, web search, images, audio, and personal support."
        elif "hello" in p_lower or "hi" in p_lower:
            return "Hello there! How can I assist you today? You can ask me questions, upload a document (PDF/DOCX), share an image, or ask for web-searched information."
        else:
            return (
                f"I received your message: \"{prompt}\".\n\n"
                f"**Note:** To enable live responses from Google Gemini, add your `GEMINI_API_KEY` to the `.env` file in the `backend/` folder and restart the server.\n\n"
                f"All local RAG parsing, text chunking, file uploads, document generation, and web searches are fully operational!"
            )

llm_service = LLMService()
