"""Chave da API do Gemini: confere se existe e salva no .env (para quem não quer editar o arquivo)."""
import logging
import re

from . import config
from .erros import erro

log = logging.getLogger(__name__)

# Só letras, números, _, - e . (formato das chaves do Google AI Studio). Isso também impede que
# uma quebra de linha cole outras variáveis dentro do .env.
_FORMATO = re.compile(r"[A-Za-z0-9_.\-]{20,200}")
_LINHA_DA_CHAVE = re.compile(r"\s*GEMINI_API_KEY\s*=")


def existe():
    """True se já há uma chave configurada (no .env, no ambiente ou salva agora)."""
    return bool(config.GEMINI_API_KEY)


def salvar(chave):
    """Guarda a chave no .env ao lado do programa e passa a usá-la na hora.

    Lança AlterEgoError (com mensagem pronta para a tela) se a chave tiver formato estranho
    ou se a pasta não permitir gravar.
    """
    chave = (chave or "").strip()
    if not _FORMATO.fullmatch(chave):
        raise erro("chave_formato")

    caminho = config.APP_DIR / ".env"
    try:
        linhas = caminho.read_text(encoding="utf-8").splitlines() if caminho.exists() else []
        linhas = [l for l in linhas if not _LINHA_DA_CHAVE.match(l)]  # tira a chave antiga
        linhas.append(f"GEMINI_API_KEY={chave}")
        caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    except OSError as exc:
        log.warning("Não consegui gravar o .env em %s: %s", caminho, exc)  # a chave nunca vai para o log
        raise erro("sem_permissao") from exc

    config.GEMINI_API_KEY = chave
