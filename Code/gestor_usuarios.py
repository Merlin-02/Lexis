"""
Módulo de autenticación, registro de cuentas de usuario y gestión de sesiones
autenticadas para el sistema LEXIS.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

DIR_CODE = Path(__file__).resolve().parent
ROOT_DIR = DIR_CODE.parent
DIR_EVALUACION_DEFAULT = ROOT_DIR / "sesiones_evaluacion"

ROLES_USUARIO = (
    "Usuario General",
    "Estudiante de Derecho",
    "Licenciado en Derecho / Abogado",
    "Investigador / Académico",
)


def _hash_password(password: str, salt_hex: str) -> str:
    """Deriva un hash PBKDF2-HMAC-SHA256 seguro para la contraseña."""
    salt_bytes = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        120_000,
    )
    return dk.hex()


class GestorUsuarios:
    """
    Administra la creación de cuentas, inicio de sesión con contraseñas cifradas
    mediante PBKDF2-HMAC-SHA256 y tokens de sesión persistentes.
    """

    def __init__(self, base_dir: Path = DIR_EVALUACION_DEFAULT) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.archivo_usuarios = self.base_dir / "usuarios.json"
        self.archivo_tokens = self.base_dir / "tokens_sesion.json"

    def _cargar_usuarios(self) -> Dict[str, Dict[str, Any]]:
        if not self.archivo_usuarios.exists():
            return {}
        try:
            with open(self.archivo_usuarios, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _guardar_usuarios(self, usuarios: Dict[str, Dict[str, Any]]) -> None:
        with open(self.archivo_usuarios, "w", encoding="utf-8") as f:
            json.dump(usuarios, f, ensure_ascii=False, indent=2)

    def _cargar_tokens(self) -> Dict[str, Dict[str, Any]]:
        if not self.archivo_tokens.exists():
            return {}
        try:
            with open(self.archivo_tokens, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _guardar_tokens(self, tokens: Dict[str, Dict[str, Any]]) -> None:
        with open(self.archivo_tokens, "w", encoding="utf-8") as f:
            json.dump(tokens, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _sanitizar_perfil(datos_usuario: Dict[str, Any]) -> Dict[str, Any]:
        """Devuelve los datos públicos de la cuenta sin exponer hash ni salt."""
        es_tlax = bool(datos_usuario.get("es_area_juridica_tlaxcala", False))
        rol_default = (
            "Abogado / Estudiante de Derecho o afín (Tlaxcala)"
            if es_tlax
            else "Usuario General"
        )
        return {
            "usuario_id": datos_usuario.get("usuario_id", ""),
            "username": datos_usuario.get("username", ""),
            "nombre_completo": datos_usuario.get("nombre_completo", ""),
            "correo": datos_usuario.get("correo", ""),
            "es_area_juridica_tlaxcala": es_tlax,
            "rol": datos_usuario.get("rol", rol_default),
            "cedula_profesional": datos_usuario.get("cedula_profesional", ""),
            "acepta_disclaimer": datos_usuario.get("acepta_disclaimer", True),
            "creado_en": datos_usuario.get("creado_en", ""),
            "ultimo_acceso": datos_usuario.get("ultimo_acceso", ""),
        }

    def registrar_usuario(
        self,
        username: str,
        password: str,
        nombre_completo: str,
        rol: str = "",
        correo: str = "",
        cedula_profesional: str = "",
        acepta_disclaimer: bool = False,
        es_area_juridica_tlaxcala: bool = False,
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Registra una nueva cuenta de usuario validando unicidad, longitud de
        contraseña y aceptación expresa de los avisos de seguridad y fase de pruebas.
        """
        username_clean = username.strip().lower()
        nombre_clean = nombre_completo.strip()
        correo_clean = correo.strip().lower()
        if rol and rol.strip():
            rol_clean = rol.strip()
        else:
            rol_clean = (
                "Abogado / Estudiante de Derecho o afín (Tlaxcala)"
                if es_area_juridica_tlaxcala
                else "Usuario General"
            )

        if not username_clean or len(username_clean) < 3:
            return (
                False,
                "El nombre de usuario debe tener al menos 3 caracteres.",
                None,
            )

        if not re.match(r"^[a-z0-9_.@-]+$", username_clean):
            return (
                False,
                "El nombre de usuario solo puede contener letras, números, puntos, guiones o arroba.",
                None,
            )

        if not nombre_clean or len(nombre_clean) < 3:
            return (
                False,
                "Por favor ingresa tu nombre completo (mínimo 3 caracteres).",
                None,
            )

        if not password or len(password) < 6:
            return (
                False,
                "La contraseña debe tener al menos 6 caracteres.",
                None,
            )

        if not acepta_disclaimer:
            return (
                False,
                "Debes aceptar el aviso de seguridad y fase de pruebas para crear una cuenta.",
                None,
            )

        usuarios = self._cargar_usuarios()
        if username_clean in usuarios:
            return (
                False,
                "El nombre de usuario ya está registrado. Elige otro o inicia sesión.",
                None,
            )

        if correo_clean:
            for u_data in usuarios.values():
                if u_data.get("correo") and u_data.get("correo") == correo_clean:
                    return (
                        False,
                        "El correo electrónico ya está asociado a otra cuenta.",
                        None,
                    )

        salt_hex = secrets.token_hex(16)
        password_hash = _hash_password(password, salt_hex)
        ahora = datetime.now().isoformat(timespec="seconds")
        usuario_id = f"usr_{secrets.token_hex(6)}"

        registro = {
            "usuario_id": usuario_id,
            "username": username_clean,
            "nombre_completo": nombre_clean,
            "correo": correo_clean,
            "es_area_juridica_tlaxcala": bool(es_area_juridica_tlaxcala),
            "rol": rol_clean,
            "cedula_profesional": cedula_profesional.strip(),
            "acepta_disclaimer": True,
            "salt": salt_hex,
            "password_hash": password_hash,
            "creado_en": ahora,
            "ultimo_acceso": ahora,
        }

        usuarios[username_clean] = registro
        self._guardar_usuarios(usuarios)
        return (
            True,
            "Cuenta creada exitosamente.",
            self._sanitizar_perfil(registro),
        )

    def autenticar_usuario(
        self,
        identificador: str,
        password: str,
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Verifica credenciales por nombre de usuario o correo electrónico.
        """
        id_clean = identificador.strip().lower()
        if not id_clean or not password:
            return (
                False,
                "Ingresa tu usuario (o correo) y tu contraseña.",
                None,
            )

        usuarios = self._cargar_usuarios()
        datos_usuario = usuarios.get(id_clean)

        if not datos_usuario:
            for u_data in usuarios.values():
                if u_data.get("correo") and u_data.get("correo") == id_clean:
                    datos_usuario = u_data
                    break

        if not datos_usuario:
            return (
                False,
                "Usuario o contraseña incorrectos.",
                None,
            )

        salt_hex = datos_usuario.get("salt", "")
        esperado_hash = datos_usuario.get("password_hash", "")
        if not salt_hex or not esperado_hash:
            return (
                False,
                "Error en el registro de credenciales del usuario.",
                None,
            )

        calculado_hash = _hash_password(password, salt_hex)
        if not hmac.compare_digest(calculado_hash, esperado_hash):
            return (
                False,
                "Usuario o contraseña incorrectos.",
                None,
            )

        datos_usuario["ultimo_acceso"] = datetime.now().isoformat(timespec="seconds")
        usuarios[datos_usuario["username"]] = datos_usuario
        self._guardar_usuarios(usuarios)

        return (
            True,
            "Inicio de sesión exitoso.",
            self._sanitizar_perfil(datos_usuario),
        )

    def obtener_usuario_por_username(self, username: str) -> Optional[Dict[str, Any]]:
        usuarios = self._cargar_usuarios()
        u = usuarios.get(username.strip().lower())
        return self._sanitizar_perfil(u) if u else None

    def crear_token_sesion(self, username: str, dispositivo_id: str = "") -> str:
        """Crea un token de sesión persistente para mantener la sesión tras recargas."""
        token = f"tok_{secrets.token_hex(16)}"
        tokens = self._cargar_tokens()
        tokens[token] = {
            "username": username.strip().lower(),
            "dispositivo_id": dispositivo_id,
            "creado_en": datetime.now().isoformat(timespec="seconds"),
        }
        self._guardar_tokens(tokens)
        return token

    def validar_token_sesion(self, token: str) -> Optional[Dict[str, Any]]:
        """Valida un token activo y devuelve el perfil del usuario correspondiente."""
        if not token:
            return None
        tokens = self._cargar_tokens()
        info = tokens.get(token)
        if not info:
            return None
        return self.obtener_usuario_por_username(info.get("username", ""))

    def cerrar_token_sesion(self, token: str) -> None:
        """Revoca un token de sesión al cerrar sesión."""
        if not token:
            return
        tokens = self._cargar_tokens()
        if token in tokens:
            del tokens[token]
            self._guardar_tokens(tokens)
