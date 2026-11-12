"""Emoções do Alter Ego: o Gemini abre cada resposta com uma etiqueta, como [feliz]."""
import re
import unicodedata

# Cada nome precisa ter uma imagem em web/expressoes/<nome>.jpg, .jpeg, .png ou .webp
# e uma entrada em NOMES_EXPRESSOES no web/script.js (e no web/teste_zoom.html, se for usá-lo).
EMOCOES = ("neutro", "feliz", "timido", "preocupado", "pensativo", "triste", "surpreso")
EMOCAO_PADRAO = "neutro"

_ETIQUETA = re.compile(r"^\s*\[([^\]\n]{1,30})\]\s*")


def _normalizar(nome):
    """'Tímido ' -> 'timido' (sem acento, minúsculo)."""
    sem_acento = unicodedata.normalize("NFD", nome)
    sem_acento = "".join(c for c in sem_acento if unicodedata.category(c) != "Mn")
    return sem_acento.strip().lower()


def separar(texto):
    """Devolve (emocao, texto_sem_etiqueta). Sem etiqueta ou etiqueta desconhecida = neutro."""
    texto = texto or ""
    achou = _ETIQUETA.match(texto)
    if not achou:
        return EMOCAO_PADRAO, texto.strip()
    nome = _normalizar(achou.group(1))
    return (nome if nome in EMOCOES else EMOCAO_PADRAO), texto[achou.end():].strip()
