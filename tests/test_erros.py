"""Testes das mensagens de erro (pt/en). Rode com: python -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import config, erros, personality  # noqa: E402


class ErroFalso(Exception):
    """Imita as exceções da API: tem um `.code` (status HTTP) e um texto."""

    def __init__(self, code=None, texto=""):
        super().__init__(texto)
        self.code = code


class ReadTimeout(Exception):
    """Imita o httpx.ReadTimeout: o texto vem vazio, só o nome da classe diz o que houve."""


class ConnectError(Exception):
    pass


class ClassificarErroTest(unittest.TestCase):
    def test_limite_de_uso(self):
        self.assertEqual(erros.classificar_erro(ErroFalso(429, "RESOURCE_EXHAUSTED")), "limite")
        self.assertEqual(erros.classificar_erro(ErroFalso(None, "You exceeded your quota")), "limite")

    def test_chave_invalida(self):
        self.assertEqual(erros.classificar_erro(ErroFalso(400, "API key not valid.")), "chave_invalida")
        self.assertEqual(erros.classificar_erro(ErroFalso(401, "bad api_key")), "chave_invalida")
        self.assertEqual(erros.classificar_erro(ErroFalso(403, "permission denied")), "chave_invalida")
        self.assertEqual(erros.classificar_erro(ErroFalso(None, "API_KEY_INVALID")), "chave_invalida")

    def test_400_sem_relacao_com_chave_e_generico(self):
        self.assertEqual(erros.classificar_erro(ErroFalso(400, "invalid argument")), "generico")

    def test_modelo_nao_encontrado(self):
        self.assertEqual(erros.classificar_erro(ErroFalso(404, "")), "modelo")
        self.assertEqual(erros.classificar_erro(ErroFalso(None, "model not found")), "modelo")

    def test_timeout_pelo_nome_da_classe(self):
        self.assertEqual(erros.classificar_erro(ReadTimeout()), "timeout")
        self.assertEqual(erros.classificar_erro(ErroFalso(None, "request timed out")), "timeout")

    def test_sem_conexao(self):
        self.assertEqual(erros.classificar_erro(ConnectError()), "conexao")
        self.assertEqual(erros.classificar_erro(ErroFalso(None, "name resolution failed")), "conexao")

    def test_servico_instavel(self):
        self.assertEqual(erros.classificar_erro(ErroFalso(503, "unavailable")), "instavel")

    def test_desconhecido_e_codigo_estranho_nao_quebram(self):
        self.assertEqual(erros.classificar_erro(ValueError("???")), "generico")
        self.assertEqual(erros.classificar_erro(ErroFalso("500", "texto")), "generico")


class MensagensTest(unittest.TestCase):
    def tearDown(self):
        personality.definir_idioma("pt")

    def test_pt_e_en_tem_as_mesmas_chaves(self):
        self.assertEqual(set(erros.MENSAGENS["pt"]), set(erros.MENSAGENS["en"]))

    def test_toda_chave_classificada_tem_mensagem(self):
        for chave in ("limite", "chave_invalida", "modelo", "timeout", "conexao", "instavel", "generico"):
            self.assertIn(chave, erros.MENSAGENS["pt"])

    def test_segue_o_idioma_atual(self):
        personality.definir_idioma("pt")
        pt = erros.msg("digite_algo")
        personality.definir_idioma("en")
        en = erros.msg("digite_algo")
        self.assertNotEqual(pt, en)
        self.assertEqual(en, erros.MENSAGENS["en"]["digite_algo"])

    def test_nome_do_modelo_entra_na_mensagem(self):
        for idioma in ("pt", "en"):
            personality.definir_idioma(idioma)
            self.assertIn(config.MODEL_NAME, erros.traduzir_erro(ErroFalso(404, "")))

    def test_erro_vira_alter_ego_error_com_a_mensagem(self):
        e = erros.erro("sem_palavras")
        self.assertIsInstance(e, erros.AlterEgoError)
        self.assertEqual(str(e), erros.MENSAGENS["pt"]["sem_palavras"])


if __name__ == "__main__":
    unittest.main()
