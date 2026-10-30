"""Pruebas automatizadas para la Fase 3: Referencias directas dentro de la misma ley."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from grafo_lexis.cargador import cargar_corpus_completo
from grafo_lexis.detector_referencias import DetectorReferencias


class TestReferenciasDirectas(unittest.TestCase):
    """Pruebas unitarias e integrales para citas directas y listas dentro de la misma ley."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.leyes, cls.articulos = cargar_corpus_completo()
        cls.detector = DetectorReferencias(cls.leyes, cls.articulos)
        cls.resultado = cls.detector.detectar_en_corpus(incluir_transitorios=False)
        cls.aristas = cls.resultado["aristas_refiere_a"]

    def test_cita_directa_simple_misma_ley(self) -> None:
        """Verifica cita directa simple como 'artículo 47' o 'artículo 123' dentro de la misma ley."""
        citas_misma_ley = [
            a for a in self.aristas if a.relacion == "misma_ley" and a.clase == "directa"
        ]
        self.assertGreater(len(citas_misma_ley), 800)
        for a in citas_misma_ley[:50]:
            self.assertEqual(a.origen_ley_id, a.destino_ley_id)
            self.assertTrue(a.texto_referencia)
            self.assertGreaterEqual(a.span_fin, a.span_inicio)

    def test_cita_con_sufijo_bis_y_letra(self) -> None:
        """Verifica detección de artículos con sufijos latinos (Bis, Ter) o literales (153-A, 240 C)."""
        destinos = {a.destino_id for a in self.aristas}
        # Verificar que artículos con sufijos son referenciados y resueltos correctamente
        con_sufijo = [d for d in destinos if "-" in d.split(":")[-1]]
        self.assertGreater(len(con_sufijo), 15)
        self.assertIn("articulo:cc_tlax:240-C", destinos)
        self.assertIn("articulo:cc_tlax:240-D", destinos)

    def test_cita_con_componente_previo_y_posterior(self) -> None:
        """Verifica que componentes internos ('fracción X', 'párrafo segundo') se guarden en la arista."""
        con_componente = [a for a in self.aristas if a.componente is not None]
        self.assertGreater(len(con_componente), 200)
        # Verificar un caso concreto con componente
        ejemplos_fraccion = [
            a for a in con_componente if "fracci" in a.componente.lower()
        ]
        self.assertGreater(len(ejemplos_fraccion), 100)

    def test_cita_multiple_en_lista_con_grupo_id(self) -> None:
        """Verifica que listas ('artículos 10, 12 y 14') generen múltiples aristas con el mismo grupo_id."""
        listas = [a for a in self.aristas if a.clase == "lista"]
        self.assertGreater(len(listas), 250)
        grupos = {}
        for a in listas:
            self.assertIsNotNone(a.grupo_id)
            grupos.setdefault(a.grupo_id, []).append(a)
        # Todo grupo de lista debe tener al menos 2 aristas (salvo auto-referencia filtrada)
        grupos_multiples = [g for g in grupos.values() if len(g) >= 2]
        self.assertGreater(len(grupos_multiples), 90)


if __name__ == "__main__":
    unittest.main()
