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


if __name__ == "__main__":
    unittest.main()
