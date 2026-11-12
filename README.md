<a id="topo"></a>

<p align="center">
  <img src="https://i.imgur.com/AgeHTlC.png" alt="KAngel Bot" width="600">
</p>

# Alter Ego

🇺🇸 [Read in English](README-en.md)

Programa de conversa escrito em Python com [Eel](https://github.com/python-eel/Eel) que abre uma janela estilo visual novel para você conversar com a Alter Ego. Ela conversa por IA (Gemini), tem um avatar que muda de expressão conforme a emoção da resposta, efeito de digitação com som, histórico salvo em SQLite, comandos no chat e erros em linguagem simples, e suporta dois idiomas (português e inglês), trocados pelo botão `PT | EN`.

```
while friend.exists():
    listen()
```

| Informações | Detalhes |
|---|---|
| **Interface** | janela desktop (Chrome, Edge ou navegador padrão) em `localhost:8765` |
| **IA** | Gemini (`gemini-3.6-flash` por padrão, via `google-genai`) |
| **Idiomas** | português e inglês, trocados pelo botão `PT \| EN` |
| **Avatar** | 7 expressões que mudam conforme a emoção da resposta |
| **Histórico** | SQLite, mantido entre as execuções |
| **Destaques** | efeito de digitação com som, memória de conversa, tentativas automáticas, erros em linguagem simples |

## Funcionalidades

### Conversa com IA (Gemini)
- Você escreve no campo de entrada e a Alter Ego responde, no idioma escolhido no botão `PT | EN`
- A conversa tem memória: as últimas 40 mensagens salvas voltam ao modelo como contexto (o valor está em `MAX_CONTEXT_MESSAGES`, no `core/config.py`)
- O contexto sempre começa por uma mensagem sua, que é o formato que o Gemini exige
- A personalidade é uma instrução de sistema (editável em `core/personality.py`): gentil, prestativa, um pouco tímida, mas corajosa, leal e amigável, com um leve tom de computador curioso
- A Alter Ego fala sempre no feminino sobre si mesma e responde em até três frases curtas, a menos que você peça mais detalhes
- A resposta vem sempre em texto corrido, sem markdown, listas, emojis ou blocos de código, porque aparece numa caixa de diálogo de visual novel
- Ajuda com qualquer assunto, como estudos e programação, sem sair do personagem
- Se o Gemini estiver sobrecarregado (erro 5xx, como o 503), o programa tenta de novo até 3 vezes, esperando 2 s e depois 4 s
- Se o Gemini não responder em 30 segundos, o programa avisa em vez de ficar em "Pensando..." para sempre
- Só salva no histórico o par pergunta/resposta que deu certo: respostas com erro não entram no banco

### Chave da API
- Na primeira abertura, se não houver chave, o programa pede para você colar a sua (o que você digita aparece como bolinhas e não vai para o log)
- A chave é salva no `.env` ao lado do programa, só neste computador
- O comando `/chave` troca a chave depois, e um `.env` editado à mão continua funcionando

### Emoções e avatar
O Gemini abre cada resposta com uma etiqueta entre colchetes, e o programa usa essa etiqueta para trocar a imagem do avatar. A etiqueta não aparece na tela.

| Emoção | Quando aparece |
|---|---|
| `[neutro]` | tom neutro e padrão |
| `[feliz]` | alegria, saudação |
| `[timido]` | timidez |
| `[preocupado]` | preocupação (também usada nas mensagens de erro) |
| `[pensativo]` | reflexão |
| `[triste]` | tristeza |
| `[surpreso]` | surpresa |

- A etiqueta aceita maiúsculas e acentos (`[Tímido]` vira `timido`)
- Etiqueta desconhecida ou ausente cai em `neutro`, e o texto continua aparecendo normalmente
- Colchetes no meio do texto (como `[1, 2, 3]`) não são tratados como etiqueta
- As imagens ficam em `web/expressoes/<nome>` e o programa aceita `.jpg`, `.jpeg`, `.png` e `.webp`
- Se a imagem de uma expressão não existir, aparece o `web/expressoes/fundo.png` (o monitor sem a personagem) em vez de quebrar a tela. Se nem ele existir, o monitor fica vazio, só com a borda clara. Nos dois casos, o nome da expressão que faltou aparece no console do navegador (`F12`)

### Terminal e efeitos
- O texto aparece letra por letra (efeito de digitação), com pausas maiores em pontuação
- Um som curto de "blip" toca a cada duas letras visíveis (gerado pelo navegador, sem arquivos de áudio)
- Clicar no terminal pula a animação
- O log mostra só a última troca de mensagens, como numa visual novel; o histórico completo continua salvo no banco
- Enquanto espera a resposta, aparece "Pensando..." com pontinhos animados
- Ao abrir, o programa cumprimenta com uma saudação inicial, ou com "Que bom te ver de novo!" se já houve conversa antes
- `F11` ativa e desativa a tela cheia

### Comandos no chat
| Comando | Descrição |
|---|---|
| `/ajuda` / `/help` | mostra a lista de comandos |
| `/som` / `/sound` | liga ou desliga o som de digitação |
| `/idioma pt` / `/lang en` (ou `/language`) | troca o idioma; sem argumento, alterna entre PT e EN |
| `/limpar` / `/clear` | apaga todo o histórico de conversas (pede confirmação) |
| `/tela` / `/screen` | liga ou desliga a tela cheia |
| `/chave` / `/key` | pede a chave do Gemini e salva (troca a atual) |

Os nomes dos comandos existem nos dois idiomas ao mesmo tempo, independente do idioma escolhido.

### Histórico
- Cada mensagem é salva em SQLite (`data/historico.db`), com o papel (`user` ou `model`), o texto e a data
- A resposta do modelo é guardada com a etiqueta de emoção, para ele continuar vendo o padrão nas mensagens seguintes
- O banco só aceita os papéis `user` e `model`
- `/limpar` apaga o banco e reinicia a conversa com o Gemini

## Idiomas (pt/en)
- O botão `PT | EN` (canto superior direito) ou o comando `/idioma` troca o idioma da interface e da IA
- Ao trocar, a tela é limpa (o histórico salvo continua intacto), a instrução da IA é refeita no idioma novo e a Alter Ego se apresenta de novo
- A escolha fica salva no navegador, por endereço. Por isso a porta é fixa (`8765`): se ela mudasse, o idioma escolhido seria esquecido
- Na primeira vez, o idioma é escolhido pelo idioma do navegador (inglês se começar com `en`, senão português)
- Os erros também aparecem no idioma escolhido
- As etiquetas de emoção ficam sempre iguais (`feliz`, `timido`...) nos dois idiomas, porque o programa usa esses nomes para escolher a imagem

## Quando algo dá errado
Os erros aparecem na tela em linguagem simples, e a causa técnica de cada um é gravada em `alter_ego.log`.

| Situação | O que o programa faz |
|---|---|
| Sem chave da API | pede a chave ao abrir; se faltar depois, manda usar `/chave` |
| Chave inválida | pede para usar `/chave` e colocar outra |
| Limite de uso da API | pede para esperar um pouco |
| Modelo não encontrado | mostra o nome do modelo e pede para conferir o `GEMINI_MODEL` |
| Demora demais | sugere verificar a conexão com a internet |
| Sem internet | avisa que não conseguiu se conectar |
| Serviço do Gemini instável | tenta 3 vezes antes de avisar |
| Resposta vazia (só a etiqueta) | pede para reformular a pergunta |
| Qualquer outro erro | mostra uma mensagem genérica e grava os detalhes no log |

Se aparecer "Algo deu errado" ou "Algo inesperado aconteceu", abra o `alter_ego.log` para ver o motivo.

## Baixar o app pronto (Windows)

1. Na aba [Releases](../../releases) do repositório, baixe o `AlterEgo-windows.zip` e extraia a pasta (não abra de dentro do zip)
2. Abra o `AlterEgo.exe`
3. Na primeira vez, o programa pede a sua chave do Gemini: crie uma de graça no [Google AI Studio](https://aistudio.google.com/apikey) e cole no campo de entrada

Precisa do Google Chrome ou do Microsoft Edge instalado. O app não é assinado digitalmente, então o Windows pode mostrar "O Windows protegeu o computador": clique em **Mais informações** e depois em **Executar assim mesmo**.

## Como rodar pelo código

1. Instale o Python 3.10+ e as dependências:
   ```
   pip install -r requirements.txt
   ```
2. Copie `.env.example` para `.env` e coloque a sua chave do [Google AI Studio](https://aistudio.google.com/apikey) em `GEMINI_API_KEY`. Se preferir, pule este passo: ao abrir sem chave, o programa pede para você colar a sua. Nunca suba o `.env` para o GitHub (ele já está no `.gitignore`)
3. Rode:
   ```
   python main.py
   ```

O programa abre uma janela no Chrome ou no Edge. Se nenhum dos dois for encontrado, ele cai para o navegador padrão.

### Configuração (`.env`)

| Variável | Para que serve | Padrão |
|---|---|---|
| `GEMINI_API_KEY` | chave da API do Gemini (obrigatória; se faltar, o programa pede ao abrir) | vazio |
| `GEMINI_MODEL` | modelo do Gemini | `gemini-3.6-flash` |
| `ALTER_EGO_BROWSER` | navegador usado: `chrome`, `edge` ou `default` | `chrome` |
| `ALTER_EGO_DB` | caminho do banco de histórico | `data/historico.db` |

Os nomes de modelos mudam com o tempo. Se aparecer "O modelo não foi encontrado", confira o nome atual na documentação do Google AI Studio e troque em `GEMINI_MODEL`.

Outras opções ficam no `core/config.py`: tempo limite da API (`TIMEOUT_API_SEGUNDOS`, 30 s), mensagens de contexto (`MAX_CONTEXT_MESSAGES`, 40) e tamanho da janela (`WINDOW_SIZE`, 1000 × 580).

## Como criar uma emoção nova
1. Adicione o nome em `EMOCOES` (`core/emocao.py`)
2. Coloque a imagem em `web/expressoes/<nome>.jpg` (ou `.jpeg`, `.png`, `.webp`)
3. Adicione o nome em `NOMES_EXPRESSOES` no `web/script.js` (e no `web/teste_zoom.html`, se for usá-lo)

A instrução da IA é montada a partir de `EMOCOES`, então a nova etiqueta já entra no prompt sozinha.

## Estrutura do projeto

```
.
├── main.py                      # abre a janela (Eel) e expõe as funções para o front-end
├── requirements.txt
├── build.bat                    # gera o app do Windows em dist/AlterEgo/
├── LICENSE                      # licença MIT
├── .gitignore                   # deixa de fora .env, data/, alter_ego.log, build/, dist/ e caches
├── .github/
│   └── workflows/
│       └── release.yml          # gera o app no GitHub e publica na aba Releases
├── .env                         # sua chave do Gemini (criado por você ou pelo programa; não vai para o GitHub)
├── .env.example                 # modelo do .env
├── alter_ego.log                # gerado automaticamente: erros inesperados
├── core/                        # o "cérebro" do programa
│   ├── config.py                # chave, modelo, timeout, caminhos do .env, do banco e do log
│   ├── chave.py                 # confere e salva a chave da API no .env
│   ├── ai_client.py             # conversa com o Gemini, com memória e novas tentativas
│   ├── history.py               # histórico em SQLite
│   ├── personality.py           # personalidade e saudações, em português e inglês
│   ├── emocao.py                # etiquetas de emoção ([feliz], [timido]...)
│   └── erros.py                 # todas as mensagens de erro, nos dois idiomas
├── data/
│   └── historico.db             # gerado automaticamente (não vai para o GitHub)
├── web/                         # interface
│   ├── index.html
│   ├── style.css
│   ├── script.js                # terminal, digitação, som, avatar, comandos e idioma
│   ├── teste_zoom.html          # compara web/expressoes com web/expressoes_normalizadas
│   ├── expressoes/              # uma imagem por emoção, mais o fundo.png (usado quando falta uma)
│   └── expressoes_normalizadas/ # versão com zoom igualado (opcional)
└── tests/                       # testes de unidade
    ├── test_ai_client.py
    ├── test_chave.py
    ├── test_emocao.py
    ├── test_erros.py
    ├── test_history.py
    └── test_personality.py
```

`web/teste_zoom.html` é uma página de apoio para comparar `web/expressoes/` com `web/expressoes_normalizadas/` (versão com zoom igualado). Para o programa usar a versão normalizada, troque `PASTA_EXPRESSOES` no `script.js`.

## Testes

```
python -m unittest discover tests
```

Instale as dependências antes (`pip install -r requirements.txt`). Os testes não usam internet nem a chave da API: o `ai_client` é testado com um Gemini falso. Eles cobrem as etiquetas de emoção, a classificação e as mensagens de erro (nos dois idiomas), o histórico, a personalidade, a chave da API e o cliente da IA (novas tentativas, erros e reinício de sessão).

## Gerando um executável (.exe)

Dentro do app, o `.env`, a pasta `data/` (histórico) e o `alter_ego.log` ficam **ao lado do `AlterEgo.exe`**, e a pasta `web/` vai empacotada junto. Há duas formas de gerar:

**Pelo GitHub (recomendado: publica sozinho na aba Releases):**

```
git tag v1.0.0
git push origin v1.0.0
```

O fluxo `.github/workflows/release.yml` roda os testes, gera o app e anexa o `AlterEgo-windows.zip` à release. Também dá para rodá-lo na mão, na aba **Actions**.

**No seu computador (Windows):** dê dois cliques no `build.bat`. O app fica em `dist/AlterEgo/`; compacte a pasta em `.zip` para mandar a alguém. O comando equivalente, com o PyInstaller instalado, é `python -m eel main.py web --onedir --noconsole --name AlterEgo`.

Nunca coloque a sua chave dentro do app: quem receber o programa cola a própria chave na primeira abertura.

## Bibliotecas usadas

- [`eel`](https://pypi.org/project/Eel/): liga o Python ao front-end em HTML/JS
- [`google-genai`](https://pypi.org/project/google-genai/): integração com o Gemini
- [`python-dotenv`](https://pypi.org/project/python-dotenv/): leitura das variáveis de ambiente
- `sqlite3` (já vem com o Python): histórico das conversas

## Aviso

Este é um projeto de fã. O Alter Ego é um programa de inteligência artificial de *Danganronpa: Trigger Happy Havoc*, e este projeto não tem relação com os criadores nem com a publicadora do jogo. A versão daqui é original e feminina, inspirada no programa, mas criada como o alter ego da autora. A licença MIT cobre apenas o código: o Alter Ego original e qualquer material de terceiros não fazem parte dela.

## Licença

O código deste projeto é distribuído sob a licença [MIT](LICENSE): você pode usar, copiar, modificar e distribuir, desde que mantenha o aviso de copyright e a licença.

Copyright (c) 2026 Alter Ego.

---

<p align="center">
  <a href="#topo">↑ voltar ao topo</a>
</p>
