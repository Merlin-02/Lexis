"""Módulo opcional de integración con Groq API para desambiguar referencias jurídicas dudosas (Fase 7)."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

from .modelos import ReferenciaRota

# Cargar .env desde Code/.env si existe
RUTA_ENV = Path(__file__).resolve().parent.parent / ".env"
if RUTA_ENV.exists():
    load_dotenv(RUTA_ENV)
else:
    load_dotenv()

MODELO_GROQ_DEFECTO = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


class DesambiguadorGroqLexis:
    """
    Cliente opcional de Groq para resolver casos ambiguos (`relativa_ambigua`, `ley_ambigua`)
    que el motor determinista de expresiones regulares clasificó con confianza baja.
    Si no hay conexión o no se solicita explícitamente, el sistema opera 100% por reglas.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        modelo: str = MODELO_GROQ_DEFECTO,
    ) -> None:
        self.api_key = os.getenv("GROQ_API_KEY") if api_key is None else api_key
        self.modelo = modelo
        self._cliente = None

    @property
    def disponible(self) -> bool:
        """Indica si hay una API Key configurada para usar Groq."""
        return bool(self.api_key)

    def _obtener_cliente(self):
        if self._cliente is None:
            if not self.api_key:
                raise RuntimeError("No se encontró GROQ_API_KEY en el entorno ni en Code/.env.")
            from groq import Groq

            self._cliente = Groq(api_key=self.api_key)
        return self._cliente

    def desambiguar_referencia(
        self,
        referencia: ReferenciaRota,
        articulos_vecinos: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Envía el fragmento (`snippet`) de una referencia ambigua al LLM en Groq
        para obtener una sugerencia estructurada en JSON con los artículos destino probables.
        """
        if not self.disponible:
            return {
                "origen_id": referencia.origen_id,
                "resuelta_por_llm": False,
                "motivo": "GROQ_API_KEY no disponible",
                "destinos_sugeridos": [],
            }

        vecinos_str = (
            ", ".join(articulos_vecinos)
            if articulos_vecinos
            else "No especificados"
        )
        system_msg = (
            "Eres un analista jurídico experto en legislación mexicana y del Estado de Tlaxcala. "
            "Analiza el fragmento legal y determina a qué artículo(s) o ley se refiere la expresión ambigua. "
            "Responde ÚNICAMENTE con un objeto JSON válido con las llaves: "
            '{"destinos_sugeridos": ["..."], "justificacion": "...", "confianza": "media"}'
        )
        user_msg = (
            f"Artículo origen: {referencia.origen_id} (Ley: {referencia.ley_origen})\n"
            f"Expresión detectada: {referencia.texto_referencia}\n"
            f"Motivo de ambigüedad: {referencia.motivo}\n"
            f"Artículos inmediatamente anteriores en la secuencia: {vecinos_str}\n"
            f"Contexto del artículo:\n\"{referencia.snippet}\"\n\n"
            "Devuelve el JSON con los IDs o números de artículos sugeridos."
        )

        try:
            cliente = self._obtener_cliente()
            resp = cliente.chat.completions.create(
                model=self.modelo,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.1,
                max_tokens=300,
            )
            texto_resp = (resp.choices[0].message.content or "").strip()
            inicio = texto_resp.find("{")
            fin = texto_resp.rfind("}")
            if inicio != -1 and fin != -1:
                parsed = json.loads(texto_resp[inicio : fin + 1])
            else:
                parsed = {"destinos_sugeridos": [], "justificacion": texto_resp}
            return {
                "origen_id": referencia.origen_id,
                "texto_referencia": referencia.texto_referencia,
                "resuelta_por_llm": True,
                "metodo": "llm_groq",
                "resultado": parsed,
            }
        except Exception as exc:
            return {
                "origen_id": referencia.origen_id,
                "texto_referencia": referencia.texto_referencia,
                "resuelta_por_llm": False,
                "error": str(exc),
                "destinos_sugeridos": [],
            }
