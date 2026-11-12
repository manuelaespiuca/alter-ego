"""Erros e mensagens para o usuário, nos dois idiomas (pt/en).

Todo texto que aparece na tela quando algo dá errado fica aqui, num lugar só. O idioma vem do
botão PT | EN (personality.idioma_atual()). Este módulo não depende do google-genai, então dá
para testá-lo sem a biblioteca instalada.
"""
from . import config, personality


class AlterEgoError(Exception):
    """Erro com mensagem já pronta para mostrar ao usuário."""


MENSAGENS = {
    "pt": {
        "sem_chave": "Ainda não tenho a sua chave da API. Digite /chave para colocá-la.",
        "digite_algo": "Digite alguma coisa primeiro.",
        "sem_palavras": "Fiquei sem palavras desta vez. Pode reformular a pergunta?",
        "limite": "Cheguei no limite de uso da API por agora. Espere um pouco e tente de novo.",
        "chave_invalida": "A chave da API parece inválida. Digite /chave para colocar outra.",
        "chave_formato": (
            "Essa chave não parece certa: ela tem só letras, números, _ e -, sem espaços. "
            "Cole de novo."
        ),
        "sem_permissao": (
            "Não consegui salvar a chave nesta pasta. Mova o programa para outra pasta "
            "(como Documentos) e tente de novo."
        ),
        "modelo": (
            "O modelo '{modelo}' não foi encontrado. "
            "Confira o nome em GEMINI_MODEL no arquivo .env."
        ),
        "timeout": "A resposta demorou demais. Verifique sua conexão com a internet e tente de novo.",
        "conexao": "Não consegui me conectar à internet. Verifique sua conexão e tente de novo.",
        "instavel": "O serviço do Gemini está instável agora. Tente novamente em instantes.",
        "generico": "Algo deu errado ao falar com a IA. Tente novamente.",
        "inesperado": "Algo inesperado aconteceu. Tente novamente.",
    },
    "en": {
        "sem_chave": "I don't have your API key yet. Type /key to enter it.",
        "digite_algo": "Type something first.",
        "sem_palavras": "I was lost for words this time. Could you rephrase your question?",
        "limite": "I've reached the API usage limit for now. Please wait a moment and try again.",
        "chave_invalida": "The API key looks invalid. Type /key to enter another one.",
        "chave_formato": (
            "That key doesn't look right: it only has letters, numbers, _ and -, with no spaces. "
            "Paste it again."
        ),
        "sem_permissao": (
            "I couldn't save the key in this folder. Move the program to another folder "
            "(like Documents) and try again."
        ),
        "modelo": (
            "The model '{modelo}' was not found. "
            "Check the name in GEMINI_MODEL in the .env file."
        ),
        "timeout": "The reply took too long. Check your internet connection and try again.",
        "conexao": "I couldn't connect to the internet. Check your connection and try again.",
        "instavel": "The Gemini service is unstable right now. Please try again in a moment.",
        "generico": "Something went wrong while talking to the AI. Please try again.",
        "inesperado": "Something unexpected happened. Please try again.",
    },
}


def msg(chave, **dados):
    """Texto da mensagem `chave` no idioma atual. Ex.: msg("modelo", modelo="gemini-x")."""
    texto = MENSAGENS[personality.idioma_atual()][chave]
    return texto.format(**dados) if dados else texto


def erro(chave, **dados):
    """Atalho: cria um AlterEgoError com a mensagem `chave` no idioma atual."""
    return AlterEgoError(msg(chave, **dados))


def classificar_erro(exc):
    """Descobre que tipo de problema é uma exceção da API/rede. Devolve a chave da mensagem."""
    # O nome da classe entra na busca porque erros de rede (httpx.ReadTimeout, ConnectError...)
    # costumam ter texto vazio: só o nome diz o que aconteceu.
    texto = f"{type(exc).__name__} {exc}".lower()
    codigo = getattr(exc, "code", None)
    if not isinstance(codigo, int):
        codigo = None

    if codigo == 429 or "resource_exhausted" in texto or "quota" in texto:
        return "limite"
    if (
        codigo in (400, 401, 403)
        and ("api key" in texto or "api_key" in texto or "permission" in texto)
    ) or "api_key_invalid" in texto:
        return "chave_invalida"
    if codigo == 404 or "not found" in texto:
        return "modelo"
    if "timeout" in texto or "timed out" in texto:
        return "timeout"
    if any(p in texto for p in ("connect", "network", "name resolution")):
        return "conexao"
    if codigo is not None and codigo >= 500:
        return "instavel"
    return "generico"


def traduzir_erro(exc):
    """Converte exceções da API/rede em mensagens amigáveis, no idioma atual."""
    return msg(classificar_erro(exc), modelo=config.MODEL_NAME)
