"""Testes do histórico em SQLite. Rode com: python -m unittest discover tests"""
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import config, history  # noqa: E402


class HistoryTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original = config.DB_PATH
        config.DB_PATH = Path(self._tmp.name) / "teste.db"
        history.init_db()

    def tearDown(self):
        config.DB_PATH = self._original
        self._tmp.cleanup()

    def test_salva_e_carrega_em_ordem(self):
        history.add_message("user", "oi")
        history.add_message("model", "olá!")
        msgs = history.load_recent(10)
        self.assertEqual([m["text"] for m in msgs], ["oi", "olá!"])
        self.assertEqual([m["role"] for m in msgs], ["user", "model"])

    def test_limite_devolve_as_mais_recentes(self):
        for i in range(5):
            history.add_message("user", f"msg {i}")
        msgs = history.load_recent(2)
        self.assertEqual([m["text"] for m in msgs], ["msg 3", "msg 4"])

    def test_limpar(self):
        history.add_message("user", "oi")
        history.clear()
        self.assertEqual(history.load_recent(10), [])

    def test_papel_invalido_e_rejeitado(self):
        with self.assertRaises(sqlite3.IntegrityError):
            history.add_message("robo", "isso não deveria entrar")


if __name__ == "__main__":
    unittest.main()
