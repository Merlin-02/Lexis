"""
Módulo de gestión de entorno (.env), persistencia de sesiones por dispositivo
y evaluación de respuestas (Like/Dislike, 0 a 5 estrellas, corrección jurídica
y comentarios finales de experiencia) para validación por Licenciados en Derecho.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
import unicodedata
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

try:
    import fcntl
except ImportError:
    fcntl = None  # type: ignore

_LOCK_EVALUACION = threading.RLock()


@contextmanager
def _bloqueo_archivo_eval(ruta_lock: Path):
    """Bloqueo concurrente a nivel de hilo y proceso para archivos de sesiones y evaluaciones."""
    with _LOCK_EVALUACION:
        ruta_lock.parent.mkdir(parents=True, exist_ok=True)
        with open(ruta_lock, "a+", encoding="utf-8") as lf:
            if fcntl is not None:
                fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                if fcntl is not None:
                    fcntl.flock(lf.fileno(), fcntl.LOCK_UN)


def _escribir_json_atomico_eval(ruta_destino: Path, datos: Any) -> None:
    """Escritura atómica de JSON mediante archivo temporal y reemplazo POSIX (os.replace)."""
    ruta_destino.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=str(ruta_destino.parent),
        prefix=f".{ruta_destino.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, ruta_destino)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        raise

DIR_CODE = Path(__file__).resolve().parent
ROOT_DIR = DIR_CODE.parent


def obtener_directorio_datos_persistentes() -> Path:
    """
    Obtiene el directorio de persistencia para sesiones y usuarios.
    Soporta volúmenes persistentes de Railway (`LEXIS_DATA_DIR` o `RAILWAY_VOLUME_MOUNT_PATH`).
    """
    vol_custom = os.getenv("LEXIS_DATA_DIR") or os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
    if vol_custom and vol_custom.strip():
        return Path(vol_custom.strip()) / "sesiones_evaluacion"
    return ROOT_DIR / "sesiones_evaluacion"


DIR_EVALUACION_DEFAULT = obtener_directorio_datos_persistentes()

ENTORNOS_VALIDOS = ("produccion", "pruebas", "desarrollo")


def _normalizar_token(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", valor.strip().lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def obtener_entorno_despliegue(ruta_env: Optional[Path] = None) -> str:
    """
    Lee el archivo .env (en Code/.env o en la raíz del proyecto) y determina
    el entorno de despliegue: 'produccion', 'pruebas' o 'desarrollo'.
    Por defecto retorna 'desarrollo' si no está definido.
    """
    if ruta_env and Path(ruta_env).exists():
        load_dotenv(dotenv_path=Path(ruta_env), override=True)
    else:
        env_code = DIR_CODE / ".env"
        env_root = ROOT_DIR / ".env"
        if env_root.exists():
            load_dotenv(dotenv_path=env_root, override=True)
        if env_code.exists():
            load_dotenv(dotenv_path=env_code, override=True)

    raw_val = (
        os.getenv("LEXIS_ENV")
        or os.getenv("ENTORNO")
        or os.getenv("APP_ENV")
        or "desarrollo"
    )
    norm = _normalizar_token(raw_val)

    mapeo = {
        "pruebas": "pruebas",
        "prueba": "pruebas",
        "test": "pruebas",
        "testing": "pruebas",
        "qa": "pruebas",
        "produccion": "produccion",
        "prod": "produccion",
        "production": "produccion",
        "desarrollo": "desarrollo",
        "dev": "desarrollo",
        "development": "desarrollo",
    }
    return mapeo.get(norm, "desarrollo")


def es_entorno_pruebas(ruta_env: Optional[Path] = None) -> bool:
    """Retorna True únicamente cuando el entorno configurado en .env es 'pruebas'."""
    return obtener_entorno_despliegue(ruta_env=ruta_env) == "pruebas"


def generar_dispositivo_id(semilla_headers: Optional[str] = None) -> str:
    """
    Genera un identificador corto y estable para el dispositivo o sesión del navegador.
    Si se proporciona información de cabeceras (ej. User-Agent + Host), genera un hash
    determinista; de lo contrario crea un token aleatorio corto.
    """
    if semilla_headers and semilla_headers.strip():
        digest = hashlib.sha256(semilla_headers.strip().encode("utf-8")).hexdigest()[:10]
        return f"disp_{digest}"
    return f"disp_{uuid.uuid4().hex[:8]}"


def generar_sesion_id() -> str:
    """Genera un identificador único ordenable cronológicamente para una conversación."""
    ahora = datetime.now().strftime("%Y%m%d_%H%M%S")
    sufijo = uuid.uuid4().hex[:6]
    return f"ses_{ahora}_{sufijo}"


def generar_mensaje_id(indice: int) -> str:
    """Genera un identificador único para un mensaje dentro de la conversación."""
    return f"msg_{indice:04d}_{uuid.uuid4().hex[:6]}"


class GestorSesionesEvaluacion:
    """
    Administra el guardado y recuperación de conversaciones por dispositivo,
    así como las calificaciones por respuesta (Like/Dislike + 0 a 5 estrellas)
    y los comentarios finales de experiencia.
    """

    def __init__(self, base_dir: Path = DIR_EVALUACION_DEFAULT) -> None:
        self.base_dir = Path(base_dir)
        self.sesiones_dir = self.base_dir / "sesiones"
        self.sesiones_dir.mkdir(parents=True, exist_ok=True)
        self.archivo_consolidado = self.base_dir / "evaluaciones_consolidado.json"

    def ruta_sesion(self, sesion_id: str) -> Path:
        limpio = "".join(c for c in sesion_id if c.isalnum() or c in ("_", "-"))
        return self.sesiones_dir / f"{limpio}.json"

    def crear_estructura_sesion(
        self,
        sesion_id: str,
        dispositivo_id: str,
        entorno: str,
        nombre_evaluador: str = "",
        usuario_id: str = "",
        username: str = "",
        rol_usuario: str = "Usuario General",
        es_area_juridica_tlaxcala: bool = False,
    ) -> Dict[str, Any]:
        ahora = datetime.now().isoformat(timespec="seconds")
        return {
            "sesion_id": sesion_id,
            "dispositivo_id": dispositivo_id,
            "usuario_id": usuario_id.strip(),
            "username": username.strip().lower(),
            "rol_usuario": rol_usuario.strip() if rol_usuario else "Usuario General",
            "es_area_juridica_tlaxcala": bool(es_area_juridica_tlaxcala),
            "nombre_evaluador": nombre_evaluador.strip(),
            "entorno": entorno,
            "estado": "activa",
            "titulo": "Nueva conversación",
            "creada_en": ahora,
            "actualizada_en": ahora,
            "messages": [],
            "historial_rag": [],
            "experiencia_final": {
                "calificacion_global_estrellas": None,
                "comentarios_experiencia": "",
                "sugerencias_correccion_futura": "",
                "guardado_en": None,
            },
        }

    def guardar_sesion(self, datos_sesion: Dict[str, Any]) -> Path:
        """
        Persiste el estado completo de una conversación en disco y actualiza el
        título automáticamente a partir de la primera consulta del usuario.
        """
        sesion_id = datos_sesion["sesion_id"]
        datos_sesion["actualizada_en"] = datetime.now().isoformat(timespec="seconds")

        # Determinar título descriptivo con la primera consulta del usuario
        for msg in datos_sesion.get("messages", []):
            if msg.get("role") == "user" and msg.get("content", "").strip():
                texto = msg["content"].strip().replace("\n", " ")
                datos_sesion["titulo"] = texto[:65] + ("..." if len(texto) > 65 else "")
                break

        ruta = self.ruta_sesion(sesion_id)
        with _bloqueo_archivo_eval(self.base_dir / ".sesiones.lock"):
            _escribir_json_atomico_eval(ruta, datos_sesion)
            self._actualizar_consolidado(datos_sesion)
        return ruta

    def cargar_sesion(self, sesion_id: str) -> Optional[Dict[str, Any]]:
        """Carga una sesión previamente guardada desde disco."""
        ruta = self.ruta_sesion(sesion_id)
        if not ruta.exists():
            return None
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def listar_sesiones(
        self,
        dispositivo_id: Optional[str] = None,
        usuario_id: Optional[str] = None,
        username: Optional[str] = None,
        incluir_vacias: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Lista las sesiones guardadas ordenadas de la más reciente a la más antigua.
        Si se especifica usuario_id/username o dispositivo_id, filtra las sesiones
        correspondientes al usuario autenticado o dispositivo.
        """
        sesiones: List[Dict[str, Any]] = []
        for archivo in self.sesiones_dir.glob("*.json"):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    data = json.load(f)
                mensajes = data.get("messages", [])
                if not incluir_vacias and not mensajes and not (
                    data.get("experiencia_final", {}).get("comentarios_experiencia")
                ):
                    continue
                if usuario_id or username:
                    coincide_usr = (
                        (usuario_id and data.get("usuario_id") == usuario_id)
                        or (username and data.get("username") == username.strip().lower())
                        or (
                            not data.get("usuario_id")
                            and not data.get("username")
                            and dispositivo_id
                            and data.get("dispositivo_id") == dispositivo_id
                        )
                    )
                    if not coincide_usr:
                        continue
                elif dispositivo_id and data.get("dispositivo_id") != dispositivo_id:
                    continue
                sesiones.append(
                    {
                        "sesion_id": data.get("sesion_id", archivo.stem),
                        "dispositivo_id": data.get("dispositivo_id", ""),
                        "usuario_id": data.get("usuario_id", ""),
                        "username": data.get("username", ""),
                        "rol_usuario": data.get("rol_usuario", "Usuario General"),
                        "nombre_evaluador": data.get("nombre_evaluador", ""),
                        "titulo": data.get("titulo", "Conversación sin título"),
                        "estado": data.get("estado", "activa"),
                        "creada_en": data.get("creada_en", ""),
                        "actualizada_en": data.get("actualizada_en", ""),
                        "num_mensajes": len(mensajes),
                        "num_respuestas_evaluadas": sum(
                            1
                            for m in mensajes
                            if m.get("role") == "assistant"
                            and m.get("evaluacion", {}).get("voto") in ("like", "dislike")
                        ),
                    }
                )
            except Exception:
                continue

        sesiones.sort(key=lambda x: x.get("actualizada_en", ""), reverse=True)
        return sesiones

    def registrar_voto_mensaje(
        self,
        datos_sesion: Dict[str, Any],
        id_mensaje: str,
        voto: str,
    ) -> bool:
        """
        Registra 'like' o 'dislike' en un mensaje del asistente y guarda la sesión.
        """
        if voto not in ("like", "dislike"):
            raise ValueError("El voto debe ser 'like' o 'dislike'.")

        for msg in datos_sesion.get("messages", []):
            if msg.get("id_mensaje") == id_mensaje:
                eval_actual = msg.setdefault(
                    "evaluacion",
                    {
                        "voto": None,
                        "estrellas": None,
                        "correccion_juridica": "",
                        "evaluado_en": None,
                    },
                )
                eval_actual["voto"] = voto
                eval_actual["evaluado_en"] = datetime.now().isoformat(timespec="seconds")
                self.guardar_sesion(datos_sesion)
                return True
        return False

    def registrar_estrellas_mensaje(
        self,
        datos_sesion: Dict[str, Any],
        id_mensaje: str,
        estrellas: int,
        correccion_juridica: Optional[str] = None,
    ) -> bool:
        """
        Registra la calificación de 0 a 5 estrellas (y opcionalmente una nota o
        corrección jurídica del licenciado en derecho) en un mensaje ya votado.
        """
        if not isinstance(estrellas, int) or estrellas < 0 or estrellas > 5:
            raise ValueError("La puntuación de estrellas debe ser un entero entre 0 y 5.")

        for msg in datos_sesion.get("messages", []):
            if msg.get("id_mensaje") == id_mensaje:
                eval_actual = msg.setdefault(
                    "evaluacion",
                    {
                        "voto": None,
                        "estrellas": None,
                        "correccion_juridica": "",
                        "evaluado_en": None,
                    },
                )
                eval_actual["estrellas"] = estrellas
                if correccion_juridica is not None:
                    eval_actual["correccion_juridica"] = correccion_juridica.strip()
                eval_actual["evaluado_en"] = datetime.now().isoformat(timespec="seconds")
                self.guardar_sesion(datos_sesion)
                return True
        return False

    def guardar_experiencia_final(
        self,
        datos_sesion: Dict[str, Any],
        comentarios_experiencia: str,
        calificacion_global_estrellas: Optional[int] = None,
        sugerencias_correccion_futura: str = "",
        finalizar_conversacion: bool = False,
    ) -> Path:
        """
        Guarda los comentarios con respecto a la experiencia antes de terminar la
        conversación y opcionalmente marca la sesión como 'finalizada'.
        """
        if calificacion_global_estrellas is not None:
            if (
                not isinstance(calificacion_global_estrellas, int)
                or calificacion_global_estrellas < 0
                or calificacion_global_estrellas > 5
            ):
                raise ValueError("La calificación global debe estar entre 0 y 5 estrellas.")

        datos_sesion["experiencia_final"] = {
            "calificacion_global_estrellas": calificacion_global_estrellas,
            "comentarios_experiencia": comentarios_experiencia.strip(),
            "sugerencias_correccion_futura": sugerencias_correccion_futura.strip(),
            "guardado_en": datetime.now().isoformat(timespec="seconds"),
        }
        if finalizar_conversacion:
            datos_sesion["estado"] = "finalizada"

        return self.guardar_sesion(datos_sesion)

    def _actualizar_consolidado(self, datos_sesion: Dict[str, Any]) -> None:
        """
        Actualiza el archivo consolidado de evaluaciones para facilitar el trabajo
        futuro de análisis y corrección de respuestas jurídicas.
        """
        consolidado: Dict[str, Any] = {"sesiones": {}}
        if self.archivo_consolidado.exists():
            try:
                with open(self.archivo_consolidado, "r", encoding="utf-8") as f:
                    consolidado = json.load(f)
            except Exception:
                consolidado = {"sesiones": {}}

        respuestas_evaluadas = []
        for msg in datos_sesion.get("messages", []):
            if msg.get("role") != "assistant":
                continue
            ev = msg.get("evaluacion", {})
            if ev.get("voto") is not None or ev.get("estrellas") is not None or ev.get("correccion_juridica"):
                respuestas_evaluadas.append(
                    {
                        "id_mensaje": msg.get("id_mensaje"),
                        "consulta_origen": msg.get("consulta_origen", ""),
                        "respuesta_modelo": msg.get("content", ""),
                        "ley_filtrada": msg.get("ley_filtrada", "Automático"),
                        "articulos_recuperados": msg.get("articulos_recuperados", []),
                        "nodos_grafo": msg.get("nodos_grafo", []),
                        "tiempo_respuesta_seg": msg.get("tiempo_respuesta_seg"),
                        "voto": ev.get("voto"),
                        "estrellas_0_a_5": ev.get("estrellas"),
                        "correccion_juridica": ev.get("correccion_juridica", ""),
                        "evaluado_en": ev.get("evaluado_en"),
                    }
                )

        consolidado.setdefault("sesiones", {})[datos_sesion["sesion_id"]] = {
            "sesion_id": datos_sesion["sesion_id"],
            "dispositivo_id": datos_sesion.get("dispositivo_id", ""),
            "usuario_id": datos_sesion.get("usuario_id", ""),
            "username": datos_sesion.get("username", ""),
            "rol_usuario": datos_sesion.get("rol_usuario", "Usuario General"),
            "es_area_juridica_tlaxcala": bool(
                datos_sesion.get("es_area_juridica_tlaxcala", False)
            ),
            "nombre_evaluador": datos_sesion.get("nombre_evaluador", ""),
            "entorno": datos_sesion.get("entorno", ""),
            "estado": datos_sesion.get("estado", "activa"),
            "titulo": datos_sesion.get("titulo", ""),
            "actualizada_en": datos_sesion.get("actualizada_en", ""),
            "experiencia_final": datos_sesion.get("experiencia_final", {}),
            "respuestas_evaluadas": respuestas_evaluadas,
        }

        _escribir_json_atomico_eval(self.archivo_consolidado, consolidado)
