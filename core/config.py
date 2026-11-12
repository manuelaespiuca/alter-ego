"""Configurações do projeto, lidas de variáveis de ambiente (.env)."""
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # permite rodar os testes sem o python-dotenv instalado
    def load_dotenv(*args, **kwargs):
        return False

# Onde ficam as coisas do usuário (.env, data/, log) e onde ficam os recursos do programa (web/).
# Rodando com `python main.py`, as duas são a pasta do projeto. Dentro de um .exe (PyInstaller),
# o .env, o data/ e o log ficam AO LADO do executável, e a pasta web/ vai empacotada dentro dele.
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
    RECURSOS_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
else:
    APP_DIR = RECURSOS_DIR = Path(__file__).resolve().parent.parent

load_dotenv(APP_DIR / ".env")

# Chave da API do Gemini (Google AI Studio). Nunca escreva a chave no código.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Os nomes de modelos mudam com o tempo: confira a documentação do Google AI Studio
# e troque aqui ou no .env se necessário.
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()

# Quanto tempo esperar pela resposta do Gemini antes de desistir (evita ficar em "Pensando..." para sempre).
TIMEOUT_API_SEGUNDOS = 30

# Banco SQLite com o histórico das conversas.
DB_PATH = Path(os.getenv("ALTER_EGO_DB", APP_DIR / "data" / "historico.db"))

# Arquivo onde os erros inesperados são registrados (para você descobrir o que deu errado).
LOG_PATH = APP_DIR / "alter_ego.log"

# Pasta do front-end.
WEB_DIR = RECURSOS_DIR / "web"

# Quantas mensagens recentes são devolvidas ao modelo como contexto.
MAX_CONTEXT_MESSAGES = 40

# Tamanho da janela (largura, altura).
WINDOW_SIZE = (1000, 580)

# Navegador usado pelo Eel: "chrome", "edge" ou "default".
BROWSER_MODE = os.getenv("ALTER_EGO_BROWSER", "chrome").strip().lower()
