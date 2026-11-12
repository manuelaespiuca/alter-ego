"""Testes do AlterEgoAI com um Gemini falso (sem internet e sem chave).
Rode com: python -m unittest discover tests"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import config, history, personality  # noqa: E402
from core.ai_client import AlterEgoAI  # noqa: E402
from core.erros import AlterEgoError  # noqa: E402


class ErroServidor(Exception):
    """Imita o google.genai.errors.ServerError (ex.: 503 UNAVAILABLE)."""

    def __init__(self, code=503):
        super().__init__(f"{code} UNAVAILABLE. This model is currently experiencing high demand.")
        self.code = code


class RespostaFalsa:
    def __init__(self, text):
        self.text = text


class ChatFalso:
    """Devolve as respostas combinadas, uma por mensagem. Se for uma exceção, ela é lançada."""

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.enviadas = []

    def send_message(self, texto):
        self.enviadas.append(texto)
        r = self.respostas.pop(0)
        if isinstance(r, Exception):
            raise r
        return RespostaFalsa(r)


class ClienteFalso:
    def __init__(self, respostas=()):
        self.chat = ChatFalso(respostas)
        self.criacoes = []  # argumentos de cada chats.create(...)
        self.chats = self

    def create(self, **kwargs):  # imita client.chats.create(...)
        self.criacoes.append(kwargs)
        return self.chat


class AlterEgoAITest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._db = config.DB_PATH
        self._chave = config.GEMINI_API_KEY
        config.DB_PATH = Path(self._tmp.name) / "teste.db"
        history.init_db()

    def tearDown(self):
        config.DB_PATH = self._db
        config.GEMINI_API_KEY = self._chave
        personality.definir_idioma("pt")
        self._tmp.cleanup()

    def test_sem_chave_avisa_em_vez_de_quebrar(self):
        config.GEMINI_API_KEY = ""
        with self.assertRaises(AlterEgoError):
            AlterEgoAI()

    def test_resposta_vem_sem_etiqueta_e_e_salva_com_ela(self):
        cliente = ClienteFalso(["[feliz] Oi, tudo bem?"])
        ai = AlterEgoAI(client=cliente)
        self.assertEqual(ai.send("  oi  "), ("Oi, tudo bem?", "feliz"))
        self.assertEqual(cliente.chat.enviadas, ["oi"])
        salvas = [(m["role"], m["text"]) for m in history.load_recent(10)]
        self.assertEqual(salvas, [("user", "oi"), ("model", "[feliz] Oi, tudo bem?")])

    def test_texto_vazio_nao_chama_a_api_nem_salva(self):
        cliente = ClienteFalso()
        ai = AlterEgoAI(client=cliente)
        for vazio in ("", "   ", None):
            with self.assertRaises(AlterEgoError):
                ai.send(vazio)
        self.assertEqual(cliente.chat.enviadas, [])
        self.assertEqual(history.load_recent(10), [])

    def test_resposta_so_com_etiqueta_da_erro_e_nao_salva(self):
        ai = AlterEgoAI(client=ClienteFalso(["[feliz]"]))
        with self.assertRaises(AlterEgoError):
            ai.send("oi")
        self.assertEqual(history.load_recent(10), [])

    def test_erro_da_api_vira_mensagem_amigavel_e_nao_salva(self):
        class ReadTimeout(Exception):
            pass

        ai = AlterEgoAI(client=ClienteFalso([ReadTimeout()]))
        with self.assertLogs("core.ai_client", level="ERROR"):  # a causa real vai para o log
            with self.assertRaises(AlterEgoError) as ctx:
                ai.send("oi")
        self.assertNotIn("Traceback", str(ctx.exception))
        self.assertIn("demorou", str(ctx.exception))
        self.assertEqual(history.load_recent(10), [])

    def test_servico_instavel_tenta_de_novo_e_funciona(self):
        cliente = ClienteFalso([ErroServidor(503), ErroServidor(503), "[feliz] Voltei!"])
        ai = AlterEgoAI(client=cliente)
        with mock.patch("core.ai_client.time.sleep") as espera, self.assertLogs("core.ai_client", level="WARNING"):
            self.assertEqual(ai.send("oi"), ("Voltei!", "feliz"))
        self.assertEqual(len(cliente.chat.enviadas), 3)
        self.assertEqual([c.args[0] for c in espera.call_args_list], [2, 4])  # espera cresce a cada tentativa

    def test_servico_instavel_desiste_depois_das_tentativas(self):
        cliente = ClienteFalso([ErroServidor(503)] * 3)
        ai = AlterEgoAI(client=cliente)
        with mock.patch("core.ai_client.time.sleep"), self.assertLogs("core.ai_client", level="WARNING"):
            with self.assertRaises(AlterEgoError) as ctx:
                ai.send("oi")
        self.assertEqual(len(cliente.chat.enviadas), 3)
        self.assertIn("instável", str(ctx.exception))
        self.assertEqual(history.load_recent(10), [])

    def test_erro_que_nao_e_de_servidor_nao_tenta_de_novo(self):
        cliente = ClienteFalso([ErroServidor(401), "[feliz] não devia chegar aqui"])
        ai = AlterEgoAI(client=cliente)
        with mock.patch("core.ai_client.time.sleep") as espera, self.assertLogs("core.ai_client", level="ERROR"):
            with self.assertRaises(AlterEgoError):
                ai.send("oi")
        self.assertEqual(len(cliente.chat.enviadas), 1)
        espera.assert_not_called()

    def test_erro_aparece_no_idioma_atual(self):
        personality.definir_idioma("en")
        ai = AlterEgoAI(client=ClienteFalso())
        with self.assertRaises(AlterEgoError) as ctx:
            ai.send("")
        self.assertEqual(str(ctx.exception), "Type something first.")

    def test_reset_apaga_o_historico_e_recria_a_sessao(self):
        cliente = ClienteFalso(["[neutro] ok"])
        ai = AlterEgoAI(client=cliente)
        ai.send("oi")
        ai.reset()
        self.assertEqual(history.load_recent(10), [])
        self.assertEqual(len(cliente.criacoes), 2)  # sessão inicial + sessão depois do reset

    def test_recriar_sessao_usa_a_instrucao_no_idioma_atual(self):
        cliente = ClienteFalso()
        ai = AlterEgoAI(client=cliente)
        personality.definir_idioma("en")
        ai.recriar_sessao()
        instrucao = str(cliente.criacoes[-1]["config"].system_instruction)
        self.assertIn("Always speak in English", instrucao)

    def test_contexto_comeca_sempre_com_user(self):
        history.add_message("model", "[feliz] sobrou do corte")
        history.add_message("user", "oi")
        history.add_message("model", "[neutro] olá")
        cliente = ClienteFalso()
        AlterEgoAI(client=cliente)
        papeis = [c.role for c in cliente.criacoes[0]["history"]]
        self.assertEqual(papeis, ["user", "model"])


if __name__ == "__main__":
    unittest.main()
