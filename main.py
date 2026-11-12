"""Alter Ego Terminal: ponto de entrada. Abre a janela (Eel) e liga o front-end ao Gemini."""
import logging
import sys
import threading
import webbrowser

import eel

from core import chave, config, emocao, erros, history, personality
from core.ai_client import AlterEgoAI
from core.erros import AlterEgoError

HISTORICO_NA_ABERTURA = 30
PORTA = 8765  # fixa de propósito: o idioma escolhido fica salvo no navegador por endereço (localhost:PORTA)

log = logging.getLogger("alter_ego")

_ai = None  # criado sob demanda, para a janela abrir mesmo sem chave configurada


def _configurar_log():
    """Erros inesperados vão para o arquivo alter_ego.log (e para o console, se houver um)."""
    handlers = []
    try:
        handlers.append(logging.FileHandler(config.LOG_PATH, encoding="utf-8"))
    except OSError:  # pasta sem permissão de escrita: segue sem arquivo de log
        pass
    if sys.stderr is not None:  # num .exe sem console, stderr não existe
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


def _obter_ai():
    global _ai
    if _ai is None:
        _ai = AlterEgoAI()  # pode lançar AlterEgoError (ex.: sem chave)
    return _ai


def _para_tela(m):
    """Mensagem do histórico do jeito que o front-end mostra (sem a etiqueta de emoção)."""
    texto = emocao.separar(m["text"])[1] if m["role"] == "model" else m["text"]
    return {"role": m["role"], "text": texto}


@eel.expose
def set_language(lang):
    """Chamado pelo botão PT | EN: guarda o idioma e refaz a instrução da IA nele."""
    novo = personality.definir_idioma(lang)
    if _ai is not None:
        try:
            # Recria a conversa com a instrução no idioma novo (o histórico é mantido no banco)
            _ai.recriar_sessao()
        except Exception:
            log.exception("Falha ao recriar a sessão depois de trocar o idioma")
    return {"ok": True, "idioma": novo}


@eel.expose
def boot():
    """Dados iniciais para o front-end."""
    return {
        "saudacoes": personality.saudacoes(),  # { "pt": ..., "en": ... }
        "historico": [_para_tela(m) for m in history.load_recent(HISTORICO_NA_ABERTURA)],
        "tem_chave": chave.existe(),  # sem chave, o front-end pede para o usuário colar a dele
    }


@eel.expose
def salvar_chave(texto):
    """Chamado quando o usuário cola a chave do Gemini (primeira abertura ou /chave)."""
    global _ai
    try:
        chave.salvar(texto)
    except AlterEgoError as exc:
        return {"ok": False, "error": str(exc)}
    except Exception:  # nada de traceback na tela do usuário (ele vai para o log)
        log.exception("Erro inesperado ao salvar a chave")
        return {"ok": False, "error": erros.msg("inesperado")}
    _ai = None  # o cliente do Gemini é recriado com a chave nova na próxima mensagem
    return {"ok": True}


@eel.expose
def send_message(texto):
    try:
        resposta, emocao_id = _obter_ai().send(texto)
    except AlterEgoError as exc:
        return {"ok": False, "error": str(exc)}
    except Exception:  # nada de traceback na tela do usuário (ele vai para o log)
        log.exception("Erro inesperado em send_message")
        return {"ok": False, "error": erros.msg("inesperado")}
    return {"ok": True, "text": resposta, "emocao": emocao_id}


@eel.expose
def clear_history():
    if _ai is not None:
        _ai.reset()
    else:
        history.clear()
    return {"ok": True}


def _abrir_no_navegador_padrao():
    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{PORTA}/index.html")).start()
    eel.start("index.html", mode=None, port=PORTA, block=True)


def main():
    _configurar_log()
    history.init_db()
    eel.init(str(config.WEB_DIR))
    modo = config.BROWSER_MODE
    if modo == "default":
        return _abrir_no_navegador_padrao()
    try:
        eel.start("index.html", mode=modo, size=config.WINDOW_SIZE, port=PORTA)
    except EnvironmentError:
        # Chrome/Edge não encontrado: cai para o navegador padrão
        _abrir_no_navegador_padrao()


if __name__ == "__main__":
    main()
