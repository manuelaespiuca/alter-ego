"""Testes da chave da API (salvar no .env). Rode com: python -m unittest discover tests"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import chave, config, personality  # noqa: E402
from core.erros import AlterEgoError  # noqa: E402

CHAVE_BOA = "chave_de_teste_1234567890abcdef"


class ChaveTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._app_dir = config.APP_DIR
        self._chave = config.GEMINI_API_KEY
        config.APP_DIR = Path(self._tmp.name)
        config.GEMINI_API_KEY = ""
        self.env = Path(self._tmp.name) / ".env"

    def tearDown(self):
        config.APP_DIR = self._app_dir
        config.GEMINI_API_KEY = self._chave
        personality.definir_idioma("pt")
        self._tmp.cleanup()

    def test_existe_segue_a_configuracao(self):
        self.assertFalse(chave.existe())
        config.GEMINI_API_KEY = CHAVE_BOA
        self.assertTrue(chave.existe())

    def test_salvar_cria_o_env_e_passa_a_usar_a_chave(self):
        chave.salvar(f"  {CHAVE_BOA}  ")
        self.assertEqual(self.env.read_text(encoding="utf-8"), f"GEMINI_API_KEY={CHAVE_BOA}\n")
        self.assertEqual(config.GEMINI_API_KEY, CHAVE_BOA)
        self.assertTrue(chave.existe())

    def test_salvar_troca_a_chave_antiga_e_mantem_o_resto(self):
        self.env.write_text(
            "# minha config\nGEMINI_API_KEY=antiga_antiga_antiga_1234\nGEMINI_MODEL=gemini-x\n",
            encoding="utf-8",
        )
        chave.salvar(CHAVE_BOA)
        linhas = self.env.read_text(encoding="utf-8").splitlines()
        self.assertEqual(linhas.count(f"GEMINI_API_KEY={CHAVE_BOA}"), 1)
        self.assertNotIn("GEMINI_API_KEY=antiga_antiga_antiga_1234", linhas)
        self.assertIn("# minha config", linhas)
        self.assertIn("GEMINI_MODEL=gemini-x", linhas)

    def test_formato_estranho_e_rejeitado_e_nao_grava(self):
        for ruim in ("", "   ", None, "curta", "com espaco no meio 1234567890",
                     CHAVE_BOA + "\nGEMINI_MODEL=outro", CHAVE_BOA + "!", "a" * 201):
            with self.assertRaises(AlterEgoError):
                chave.salvar(ruim)
        self.assertFalse(self.env.exists())
        self.assertEqual(config.GEMINI_API_KEY, "")

    def test_pasta_sem_permissao_vira_erro_amigavel(self):
        config.APP_DIR = Path(self._tmp.name) / "nao_existe"  # gravar aqui falha com OSError
        with self.assertLogs("core.chave", level="WARNING") as logs, self.assertRaises(AlterEgoError) as ctx:
            chave.salvar(CHAVE_BOA)
        self.assertNotIn(CHAVE_BOA, str(ctx.exception))
        self.assertNotIn(CHAVE_BOA, "\n".join(logs.output))  # a chave nunca vai para o log
        self.assertEqual(config.GEMINI_API_KEY, "")

    def test_mensagem_no_idioma_atual(self):
        personality.definir_idioma("en")
        with self.assertRaises(AlterEgoError) as ctx:
            chave.salvar("curta")
        self.assertIn("key", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
