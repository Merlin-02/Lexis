"""Pruebas automatizadas para la Fase 4: Referencias relativas (artículo anterior/siguiente y propia ley)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from grafo_lexis.constructor_grafo import ConstructorGrafoLexis


class TestReferenciasRelativasFase4(unittest.TestCase):
    """Pruebas unitarias e integrales para referencias relativas dentro de la misma ley."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.constructor = ConstructorGrafoLexis()
        cls.constructor.cargar_y_construir_estructura_base()
        cls.resumen = cls.constructor.detectar_y_agregar_referencias_fase4()
        cls.aristas_rel = [
            a for a in cls.constructor.aristas_refiere_a if a.clase == "relativa"
        ]

    def test_articulo_anterior_y_que_precede(self) -> None:
        """Verifica resolución de 'el artículo anterior' y 'el artículo que precede'."""
        # cc_tlax:13 cita 'el artículo anterior' -> cc_tlax:12
        aristas_13 = [
            a for a in self.aristas_rel if a.origen_id == "articulo:cc_tlax:13"
        ]
        self.assertTrue(any(a.destino_id == "articulo:cc_tlax:12" for a in aristas_13))

        # cc_tlax:62 cita 'del artículo que precede' -> cc_tlax:61
        aristas_62 = [
            a for a in self.aristas_rel if a.origen_id == "articulo:cc_tlax:62"
        ]
        self.assertTrue(any(a.destino_id == "articulo:cc_tlax:61" for a in aristas_62))

    def test_articulo_siguiente_y_subarticulos_bis(self) -> None:
        """Verifica 'el artículo siguiente' y navegación relativa sobre subartículos Bis/Ter."""
        # cc_tlax:5 cita 'el artículo siguiente' -> cc_tlax:6
        aristas_5 = [
            a for a in self.aristas_rel if a.origen_id == "articulo:cc_tlax:5"
        ]
        self.assertTrue(any(a.destino_id == "articulo:cc_tlax:6" for a in aristas_5))

        # cc_tlax:346-TER cita 'el artículo anterior' -> cc_tlax:346-BIS
        aristas_346ter = [
            a for a in self.aristas_rel if a.origen_id == "articulo:cc_tlax:346-TER"
        ]
        self.assertTrue(
            any(a.destino_id == "articulo:cc_tlax:346-BIS" for a in aristas_346ter)
        )

    def test_dos_o_mas_articulos_anteriores(self) -> None:
        """Verifica cuantificadores ('los dos artículos anteriores') respetando el orden secuencial real."""
        # cc_tlax:194 cita 'en los dos artículos anteriores' -> en la secuencia real son cc_tlax:193 y cc_tlax:192-BIS
        aristas_194 = [
            a
            for a in self.aristas_rel
            if a.origen_id == "articulo:cc_tlax:194"
            and a.destino_id.startswith("articulo:")
        ]
        destinos_194 = {a.destino_id for a in aristas_194}
        self.assertEqual(destinos_194, {"articulo:cc_tlax:192-BIS", "articulo:cc_tlax:193"})

    def test_relativas_a_la_propia_ley(self) -> None:
        """Verifica que 'la presente Ley', 'este Código', 'esta Constitución' apunten al nodo Ley."""
        rel_a_ley = [
            a for a in self.aristas_rel if a.destino_id.startswith("ley:")
        ]
        self.assertGreaterEqual(len(rel_a_ley), 340)
        for a in rel_a_ley[:30]:
            self.assertEqual(a.destino_id, a.origen_ley_id)
            self.assertEqual(a.metodo, "contexto")

    def test_plural_indeterminado_reportado_como_relativa_ambigua(self) -> None:
        """Verifica que 'los artículos anteriores' (sin número) se reporte como relativa_ambigua y no invente aristas."""
        ambiguas = [
            r
            for r in self.constructor.referencias_rotas
            if r.motivo == "relativa_ambigua"
        ]
        self.assertGreaterEqual(len(ambiguas), 60)


if __name__ == "__main__":
    unittest.main()
