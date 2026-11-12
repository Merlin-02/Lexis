"""
Pruebas unitarias para el módulo de entorno (.env), persistencia de sesiones
por dispositivo y evaluación de respuestas (Like/Dislike, 0 a 5 estrellas y
comentarios finales de experiencia).
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gestor_evaluacion import (
    GestorSesionesEvaluacion,
    es_entorno_pruebas,
    generar_dispositivo_id,
    generar_mensaje_id,
    generar_sesion_id,
    obtener_entorno_despliegue,
)
from gestor_usuarios import GestorUsuarios


class TestEvaluacionYSesiones(unittest.TestCase):
    def test_1_deteccion_entorno_env(self) -> None:
        """Verifica que LEXIS_ENV en .env distinga produccion, pruebas y desarrollo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / ".env"

            env_path.write_text("LEXIS_ENV=pruebas\n", encoding="utf-8")
            self.assertEqual(obtener_entorno_despliegue(env_path), "pruebas")
            self.assertTrue(es_entorno_pruebas(env_path))

            env_path.write_text("LEXIS_ENV=producción\n", encoding="utf-8")
            self.assertEqual(obtener_entorno_despliegue(env_path), "produccion")
            self.assertFalse(es_entorno_pruebas(env_path))

            env_path.write_text("LEXIS_ENV=desarrollo\n", encoding="utf-8")
            self.assertEqual(obtener_entorno_despliegue(env_path), "desarrollo")
            self.assertFalse(es_entorno_pruebas(env_path))

    def test_2_guardado_y_reanudacion_por_dispositivo(self) -> None:
        """Verifica que las conversaciones se guarden por dispositivo y puedan retomarse después."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gestor = GestorSesionesEvaluacion(base_dir=Path(tmpdir))
            disp_1 = generar_dispositivo_id("Mozilla/5.0|es-MX|localhost")
            disp_2 = generar_dispositivo_id("OtroNavegador|en-US|localhost")

            ses_1 = generar_sesion_id()
            datos_1 = gestor.crear_estructura_sesion(
                sesion_id=ses_1,
                dispositivo_id=disp_1,
                entorno="pruebas",
                nombre_evaluador="Lic. María Hernández",
            )
            datos_1["messages"] = [
                {"role": "user", "content": "¿Cómo se tramita la revocación de la adopción?"},
                {
                    "id_mensaje": generar_mensaje_id(1),
                    "role": "assistant",
                    "content": "Se tramita conforme al artículo 1470 del CPC de Tlaxcala...",
                    "consulta_origen": "¿Cómo se tramita la revocación de la adopción?",
                    "evaluacion": {
                        "voto": None,
                        "estrellas": None,
                        "correccion_juridica": "",
                        "evaluado_en": None,
                    },
                },
            ]
            gestor.guardar_sesion(datos_1)

            ses_2 = generar_sesion_id()
            datos_2 = gestor.crear_estructura_sesion(
                sesion_id=ses_2,
                dispositivo_id=disp_2,
                entorno="pruebas",
                nombre_evaluador="Lic. Carlos Ruiz",
            )
            datos_2["messages"] = [
                {"role": "user", "content": "¿Cuál es la indemnización por despido?"}
            ]
            gestor.guardar_sesion(datos_2)

            lista_disp_1 = gestor.listar_sesiones(dispositivo_id=disp_1)
            self.assertEqual(len(lista_disp_1), 1)
            self.assertEqual(lista_disp_1[0]["sesion_id"], ses_1)
            self.assertIn("revocación de la adopción", lista_disp_1[0]["titulo"])

            recuperada = gestor.cargar_sesion(ses_1)
            self.assertIsNotNone(recuperada)
            self.assertEqual(recuperada["nombre_evaluador"], "Lic. María Hernández")
            self.assertEqual(len(recuperada["messages"]), 2)

    def test_3_voto_like_dislike_y_estrellas_0_a_5(self) -> None:
        """Verifica calificación con Like/Dislike, estrellas de 0 a 5 y observación jurídica."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gestor = GestorSesionesEvaluacion(base_dir=Path(tmpdir))
            ses_id = generar_sesion_id()
            msg_id = "msg_0001_test"

            datos = gestor.crear_estructura_sesion(
                sesion_id=ses_id,
                dispositivo_id="disp_test",
                entorno="pruebas",
                nombre_evaluador="Lic. Roberto Gómez",
            )
            datos["messages"] = [
                {"role": "user", "content": "Consulta sobre adopción"},
                {
                    "id_mensaje": msg_id,
                    "role": "assistant",
                    "content": "Respuesta del modelo sobre adopción.",
                    "consulta_origen": "Consulta sobre adopción",
                    "articulos_recuperados": [
                        {"documento": "Procedimiento Civiles Tlaxcala", "articulo": "Artículo 1470.-"}
                    ],
                    "nodos_grafo": ["articulo:cpc_tlax:1470", "articulo:cc_tlax:240-C"],
                },
            ]
            gestor.guardar_sesion(datos)

            # 1. Registrar Like
            ok_voto = gestor.registrar_voto_mensaje(datos, msg_id, "like")
            self.assertTrue(ok_voto)

            # 2. Registrar 0 estrellas y luego actualizar a 5 estrellas
            ok_est_0 = gestor.registrar_estrellas_mensaje(datos, msg_id, 0)
            self.assertTrue(ok_est_0)
            self.assertEqual(datos["messages"][1]["evaluacion"]["estrellas"], 0)

            ok_est_5 = gestor.registrar_estrellas_mensaje(
                datos,
                msg_id,
                5,
                correccion_juridica="Respuesta correcta; cita adecuadamente el art. 1470 CPC y 240-C CC.",
            )
            self.assertTrue(ok_est_5)

            # Validar rango inválido
            with self.assertRaises(ValueError):
                gestor.registrar_estrellas_mensaje(datos, msg_id, 6)

            # 3. Guardar experiencia final antes de terminar la conversación
            gestor.guardar_experiencia_final(
                datos,
                comentarios_experiencia="Excelente precisión al concatenar el Código Civil con el Procesal.",
                calificacion_global_estrellas=5,
                sugerencias_correccion_futura="Incluir plazos de notificación al Ministerio Público.",
                finalizar_conversacion=True,
            )

            recargada = gestor.cargar_sesion(ses_id)
            self.assertEqual(recargada["estado"], "finalizada")
            self.assertEqual(
                recargada["experiencia_final"]["calificacion_global_estrellas"], 5
            )
            self.assertIn(
                "Excelente precisión",
                recargada["experiencia_final"]["comentarios_experiencia"],
            )

            # Verificar consolidado para trabajo futuro
            self.assertTrue(gestor.archivo_consolidado.exists())
            consolidado = json.loads(
                gestor.archivo_consolidado.read_text(encoding="utf-8")
            )
            self.assertIn(ses_id, consolidado["sesiones"])
            evals = consolidado["sesiones"][ses_id]["respuestas_evaluadas"]
            self.assertEqual(len(evals), 1)
            self.assertEqual(evals[0]["voto"], "like")
            self.assertEqual(evals[0]["estrellas_0_a_5"], 5)

    def test_4_registro_login_y_evaluacion_usuario_general(self) -> None:
        """Verifica creación de cuenta, exigencia de disclaimer, inicio de sesión y evaluación por usuario general."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            gestor_usr = GestorUsuarios(base_dir=base)
            gestor_ses = GestorSesionesEvaluacion(base_dir=base)

            # 1. Rechazar registro si no acepta el disclaimer de seguridad y fase de pruebas
            ok_no_disc, msg_no_disc, _ = gestor_usr.registrar_usuario(
                username="ciudadano_1",
                password="mipassword123",
                nombre_completo="Juan Ciudadano",
                rol="Usuario General",
                acepta_disclaimer=False,
            )
            self.assertFalse(ok_no_disc)
            self.assertIn("aviso de seguridad", msg_no_disc)

            # 2. Registro válido aceptando el disclaimer (usuario general y especialista de Tlaxcala)
            ok_reg, _, perfil = gestor_usr.registrar_usuario(
                username="ciudadano_1",
                password="mipassword123",
                nombre_completo="Juan Ciudadano",
                correo="juan@ejemplo.com",
                acepta_disclaimer=True,
                es_area_juridica_tlaxcala=False,
            )
            self.assertTrue(ok_reg)
            self.assertIsNotNone(perfil)
            self.assertEqual(perfil["username"], "ciudadano_1")
            self.assertFalse(perfil["es_area_juridica_tlaxcala"])
            self.assertEqual(perfil["rol"], "Usuario General")
            self.assertNotIn("password_hash", perfil)

            ok_tlax, _, perfil_tlax = gestor_usr.registrar_usuario(
                username="abogado_tlax",
                password="mipassword123",
                nombre_completo="Lic. Elena Morales",
                acepta_disclaimer=True,
                es_area_juridica_tlaxcala=True,
            )
            self.assertTrue(ok_tlax)
            self.assertTrue(perfil_tlax["es_area_juridica_tlaxcala"])
            self.assertIn("Tlaxcala", perfil_tlax["rol"])

            # 3. Autenticación con nombre de usuario y con correo
            ok_login, _, perfil_login = gestor_usr.autenticar_usuario(
                "ciudadano_1", "mipassword123"
            )
            self.assertTrue(ok_login)
            self.assertEqual(perfil_login["usuario_id"], perfil["usuario_id"])

            ok_correo, _, _ = gestor_usr.autenticar_usuario(
                "juan@ejemplo.com", "mipassword123"
            )
            self.assertTrue(ok_correo)

            ok_bad, _, _ = gestor_usr.autenticar_usuario("ciudadano_1", "clave_erronea")
            self.assertFalse(ok_bad)

            # 4. Token de sesión y cierre de sesión
            token = gestor_usr.crear_token_sesion("ciudadano_1", "disp_123")
            self.assertIsNotNone(gestor_usr.validar_token_sesion(token))
            gestor_usr.cerrar_token_sesion(token)
            self.assertIsNone(gestor_usr.validar_token_sesion(token))

            # 5. Guardar sesión y puntuación de chat para usuario general
            ses_id = generar_sesion_id()
            datos_ses = gestor_ses.crear_estructura_sesion(
                sesion_id=ses_id,
                dispositivo_id="disp_123",
                entorno="pruebas",
                nombre_evaluador=perfil["nombre_completo"],
                usuario_id=perfil["usuario_id"],
                username=perfil["username"],
                rol_usuario=perfil["rol"],
            )
            datos_ses["messages"] = [
                {"role": "user", "content": "¿Qué hago si me despidieron hoy?"},
                {
                    "id_mensaje": "msg_usr_1",
                    "role": "assistant",
                    "content": "Orientación sobre despido conforme a la LFT...",
                    "consulta_origen": "¿Qué hago si me despidieron hoy?",
                },
            ]
            gestor_ses.guardar_sesion(datos_ses)
            gestor_ses.registrar_voto_mensaje(datos_ses, "msg_usr_1", "like")
            gestor_ses.registrar_estrellas_mensaje(
                datos_ses,
                "msg_usr_1",
                4,
                correccion_juridica="Muy clara la explicación para un usuario general.",
            )

            sesiones_usuario = gestor_ses.listar_sesiones(
                usuario_id=perfil["usuario_id"]
            )
            self.assertEqual(len(sesiones_usuario), 1)
            self.assertEqual(sesiones_usuario[0]["rol_usuario"], "Usuario General")
            self.assertEqual(sesiones_usuario[0]["num_respuestas_evaluadas"], 1)

    def test_5_modo_ligero_railway_sin_chromadb(self) -> None:
        """Verifica que en Railway (sin lexis_vectordb ni GPU) el motor híbrido y GraphRAG funcionen eficientemente."""
        import os
        from buscador import inicializar_motores, busqueda_hibrida, MODELO_NOMBRE
        from grafo_lexis.integracion_rag import construir_contexto_graphrag, obtener_recuperador_grafo

        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["LEXIS_MODO_LIGERO"] = "1"
            try:
                (
                    coleccion,
                    motor_bm25,
                    modelo_semantico,
                    diccionario_textos,
                    diccionario_metadatos,
                    documentos_disponibles,
                    _,
                ) = inicializar_motores(str(Path(tmpdir) / "no_existe_db"), MODELO_NOMBRE)

                self.assertEqual(len(documentos_disponibles), 6)
                self.assertGreater(len(diccionario_textos), 7000)

                q = "¿Cómo se tramita la revocación de la adopción cuando el adoptado es mayor de edad?"
                hits = busqueda_hibrida(
                    consulta=q,
                    coleccion=coleccion,
                    motor_bm25=motor_bm25,
                    modelo=modelo_semantico,
                    diccionario_textos=diccionario_textos,
                    diccionario_metadatos=diccionario_metadatos,
                    top_k=10,
                    filtro_documento=None,
                )
                self.assertGreater(len(hits), 0)
                articulos_top = [h.get("articulo", "") for h in hits[:5]]
                self.assertTrue(any("1470" in a or "1466" in a for a in articulos_top))

                ctx = construir_contexto_graphrag(
                    hits,
                    max_fragmentos_base=4,
                    max_vecinos_grafo=4,
                    recuperador=obtener_recuperador_grafo(),
                )
                self.assertIn("240-C", ctx["bloque_prompt"])
            finally:
                os.environ.pop("LEXIS_MODO_LIGERO", None)


if __name__ == "__main__":
    unittest.main()
