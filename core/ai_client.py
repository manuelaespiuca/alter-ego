"""Comunicação com o Gemini, com memória de conversa e erros em linguagem amigável."""
import logging
import time

from google import genai
from google.genai import types

from . import config, emocao, history, personality
from .erros import AlterEgoError, classificar_erro, erro, traduzir_erro

log = logging.getLogger(__name__)

# Quando o Gemini está sobrecarregado (erro 5xx, como o 503 "high demand"), tentamos de novo
# algumas vezes antes de avisar o usuário. A espera aumenta a cada tentativa (2 s, 4 s...).
TENTATIVAS = 3
ESPERA_ENTRE_TENTATIVAS_S = 2


class AlterEgoAI:
    def __init__(self, client=None):
        """`client` só existe para os testes (um cliente falso). No uso normal, deixe vazio."""
        if client is None:
            if not config.GEMINI_API_KEY:
                raise erro("sem_chave")
            client = genai.Client(
                api_key=config.GEMINI_API_KEY,
                # O timeout do google-genai é em milissegundos.
                http_options=types.HttpOptions(timeout=int(config.TIMEOUT_API_SEGUNDOS * 1000)),
            )
        self._client = client
        self._chat = None
        self.recriar_sessao()

    # --- sessão de chat ---------------------------------------------------
    def _contexto_salvo(self):
        """Reconstrói o histórico no formato do Gemini (começa sempre com 'user')."""
        msgs = history.load_recent(config.MAX_CONTEXT_MESSAGES)
        while msgs and msgs[0]["role"] != "user":
            msgs.pop(0)
        return [
            types.Content(role=m["role"], parts=[types.Part(text=m["text"])])
            for m in msgs
        ]

    def recriar_sessao(self):
        """Começa uma conversa nova com o Gemini, com a instrução no idioma atual.

        O histórico salvo no banco é reaproveitado como contexto.
        """
        self._chat = self._client.chats.create(
            model=config.MODEL_NAME,
            config=types.GenerateContentConfig(
                system_instruction=personality.instrucao(),
                temperature=0.9,
            ),
            history=self._contexto_salvo(),
        )

    def _pedir_resposta(self, texto):
        """Envia a mensagem ao Gemini e devolve a resposta bruta (com a etiqueta de emoção).

        Se o serviço estiver instável (5xx), tenta de novo algumas vezes. Qualquer outro erro
        (chave inválida, limite de uso, sem internet...) é traduzido e lançado na hora.
        """
        for tentativa in range(1, TENTATIVAS + 1):
            try:
                resposta = self._chat.send_message(texto)
                return (resposta.text or "").strip()
            except Exception as exc:  # a API pode lançar vários tipos de erro
                if classificar_erro(exc) == "instavel" and tentativa < TENTATIVAS:
                    log.warning("Gemini instável (tentativa %d de %d); tentando de novo", tentativa, TENTATIVAS)
                    time.sleep(ESPERA_ENTRE_TENTATIVAS_S * tentativa)
                    continue
                log.exception("Falha ao chamar o Gemini")  # a causa real fica no log
                raise AlterEgoError(traduzir_erro(exc)) from exc

    # --- API pública ------------------------------------------------------
    def reset(self):
        """Apaga o histórico salvo e reinicia a sessão."""
        history.clear()
        self.recriar_sessao()

    def send(self, texto):
        texto = (texto or "").strip()
        if not texto:
            raise erro("digite_algo")
        bruta = self._pedir_resposta(texto)

        emocao_id, reply = emocao.separar(bruta)
        if not reply:
            # O chat em memória já guardou essa troca, mas o banco não: recriar a sessão
            # faz a memória voltar a refletir o que está salvo.
            self.recriar_sessao()
            raise erro("sem_palavras")

        # Só salva o par pergunta/resposta quando deu tudo certo. A resposta é salva com a
        # etiqueta, para o modelo continuar vendo o padrão nas próximas mensagens.
        history.add_message("user", texto)
        history.add_message("model", bruta)
        return reply, emocao_id
