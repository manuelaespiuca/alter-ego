"""Testes da personalidade e do idioma. Rode com: python -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import emocao, personality  # noqa: E402


class PersonalityTest(unittest.TestCase):
    def tearDown(self):
        personality.definir_idioma("pt")

    def test_idioma_invalido_vira_o_padrao(self):
        self.assertEqual(personality.definir_idioma("fr"), "pt")
        self.assertEqual(personality.definir_idioma(None), "pt")

    def test_definir_idioma_guarda_o_valor(self):
        self.assertEqual(personality.definir_idioma("en"), "en")
        self.assertEqual(personality.idioma_atual(), "en")

    def test_instrucao_sem_argumento_usa_o_idioma_atual(self):
        personality.definir_idioma("en")
        self.assertEqual(personality.instrucao(), personality.instrucao("en"))
        self.assertIn("Always speak in English", personality.instrucao())

    def test_instrucao_em_portugues(self):
        self.assertIn("português do Brasil", personality.instrucao("pt"))

    def test_instrucao_cita_todas_as_etiquetas_nos_dois_idiomas(self):
        for idioma in personality.IDIOMAS:
            texto = personality.instrucao(idioma)
            for e in emocao.EMOCOES:
                self.assertIn(f"[{e}]", texto, f"{idioma}: falta [{e}]")

    def test_instrucao_cita_o_criador(self):
        for idioma in personality.IDIOMAS:
            self.assertIn(personality.CRIADOR, personality.instrucao(idioma))

    def test_saudacoes_tem_pt_e_en(self):
        s = personality.saudacoes()
        self.assertEqual(set(s), {"pt", "en"})
        self.assertTrue(all(s.values()))

    def test_saudacoes_devolve_uma_copia(self):
        personality.saudacoes()["pt"] = "alterado"
        self.assertNotEqual(personality.saudacoes()["pt"], "alterado")


if __name__ == "__main__":
    unittest.main()
