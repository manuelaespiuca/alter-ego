"""Testes das etiquetas de emoção. Rode com: python -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import emocao  # noqa: E402


class EmocaoTest(unittest.TestCase):
    def test_separa_etiqueta_do_texto(self):
        self.assertEqual(emocao.separar("[feliz] Que bom te ver!"), ("feliz", "Que bom te ver!"))

    def test_aceita_maiuscula_e_acento(self):
        self.assertEqual(emocao.separar("[Tímido] Oi..."), ("timido", "Oi..."))

    def test_etiqueta_desconhecida_vira_neutro_e_some(self):
        self.assertEqual(emocao.separar("[bravo] Cuidado!"), ("neutro", "Cuidado!"))

    def test_sem_etiqueta_fica_neutro(self):
        self.assertEqual(emocao.separar("Olá!"), ("neutro", "Olá!"))

    def test_colchetes_no_meio_do_texto_nao_sao_etiqueta(self):
        self.assertEqual(emocao.separar("Use a lista [1, 2, 3]."), ("neutro", "Use a lista [1, 2, 3]."))

    def test_so_etiqueta_deixa_texto_vazio(self):
        self.assertEqual(emocao.separar("[feliz]"), ("feliz", ""))

    def test_vazio(self):
        self.assertEqual(emocao.separar(""), ("neutro", ""))


if __name__ == "__main__":
    unittest.main()
