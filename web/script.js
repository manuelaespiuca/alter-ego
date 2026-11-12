/* Alter Ego: front-end. Monitor verde + log de terminal, typewriter, som de blip e expressões do avatar. */

const el = {
  monitor: document.getElementById("monitor"),
  avatar: document.getElementById("avatar"),
  terminal: document.getElementById("terminal"),
  form: document.getElementById("form"),
  campo: document.getElementById("campo"),
  enviar: document.getElementById("btn-enviar"),
  idioma: document.getElementById("btn-idioma"),
  prompt: document.querySelector(".prompt"),
};

const VELOCIDADE_MS = 35;       // intervalo entre letras
const BLIP_A_CADA = 2;          // toca o blip a cada N letras visíveis
const LINHAS_NO_HISTORICO = 30; // quantas mensagens antigas aparecem ao abrir (se o modo abaixo for false)

// true: o log mostra só a última troca de mensagens, como na referência (o histórico
// continua salvo no banco). false: o log acumula toda a conversa.
const MOSTRAR_SO_ULTIMA_TROCA = true;

let somLigado = true;
let audioCtx = null;
let jaConversou = false;        // já houve conversa (histórico salvo ou mensagem desta sessão)
let saudacoes = null;           // saudações vindas do Python: { pt, en }
let ocupado = false;            // aguardando resposta da IA ou executando comando
let esperandoChave = false;     // o próximo texto digitado é a chave da API (não vai para a IA)
let fala = { id: 0, falando: false, pular: false };

/* ---------- Idioma (PT / EN) ---------- */

const TEXTOS = {
  pt: {
    nomes: { user: "Você:", model: "", sistema: "Sistema:", erro: "Erro:" },
    prompt: ">> Entrada:",
    dica: "Digite sua mensagem ou /ajuda para ver os comandos",
    pensando: "Pensando",
    dicaTerminal: "Clique para pular a animação",
    ajuda: "Comandos: /som, /limpar, /tela, /idioma, /chave e /ajuda. F11 também ativa a tela cheia.",
    som: (on) => "Som " + (on ? "ligado." : "desligado."),
    confirmarLimpar: "Apagar todo o histórico de conversas?",
    limpo: "Memória apagada. Vamos começar do zero!",
    desconhecido: "Comando desconhecido. Digite /ajuda.",
    falhaComando: "Não consegui executar esse comando.",
    semConexao: "Perdi a conexão com o programa. Feche e abra de novo.",
    falhaInicio: "Não consegui iniciar a conexão com o programa.",
    bemVindoDeNovo: "Que bom te ver de novo! Podemos continuar de onde paramos.",
    pedirChave: "Falta a sua chave do Gemini. Cole abaixo (crie uma de graça em aistudio.google.com/apikey). Ela fica salva só neste computador.",
    dicaChave: "Cole a chave aqui e aperte Enter (ou digite / para cancelar)",
    chaveSalva: "Chave salva! Já podemos conversar.",
  },
  en: {
    nomes: { user: "You:", model: "", sistema: "System:", erro: "Error:" },
    prompt: ">> Input:",
    dica: "Type your message or /help to see the commands",
    pensando: "Thinking",
    dicaTerminal: "Click to skip the animation",
    ajuda: "Commands: /sound, /clear, /screen, /lang, /key and /help. F11 also toggles fullscreen.",
    som: (on) => "Sound " + (on ? "on." : "off."),
    confirmarLimpar: "Erase the whole conversation history?",
    limpo: "Memory erased. Let's start from scratch!",
    desconhecido: "Unknown command. Type /help.",
    falhaComando: "I couldn't run that command.",
    semConexao: "I lost the connection to the program. Close it and open it again.",
    falhaInicio: "I couldn't start the connection to the program.",
    bemVindoDeNovo: "Good to see you again! We can pick up where we left off.",
    pedirChave: "I need your Gemini key. Paste it below (get a free one at aistudio.google.com/apikey). It is saved only on this computer.",
    dicaChave: "Paste the key here and press Enter (or type / to cancel)",
    chaveSalva: "Key saved! We can talk now.",
  },
};

// Comandos aceitos nos dois idiomas (nome digitado -> comando interno).
const ALIAS = {
  ajuda: "ajuda", help: "ajuda",
  som: "som", sound: "som",
  limpar: "limpar", clear: "limpar",
  tela: "tela", screen: "tela",
  idioma: "idioma", lang: "idioma", language: "idioma",
  chave: "chave", key: "chave",
};

function idiomaInicial() {
  try {
    const salvo = localStorage.getItem("alterego_idioma");
    if (salvo === "pt" || salvo === "en") return salvo;
  } catch (e) {}
  return (navigator.language || "pt").toLowerCase().startsWith("en") ? "en" : "pt";
}

let idioma = idiomaInicial();
const t = () => TEXTOS[idioma];

function aplicarIdioma() {
  document.documentElement.lang = idioma === "pt" ? "pt-BR" : "en";
  el.prompt.textContent = t().prompt;
  el.campo.placeholder = esperandoChave ? t().dicaChave : t().dica;
  el.terminal.title = t().dicaTerminal;
  el.idioma.innerHTML = idioma === "pt" ? "<b>PT</b> <span>|</span> EN" : "PT <span>|</span> <b>EN</b>";
  // Atualiza os rótulos das linhas que já estão no log
  el.terminal.querySelectorAll(".linha").forEach((linha) => {
    const tipo = linha.className.replace("linha", "").trim().split(/\s+/)[0];
    const quem = linha.querySelector(".quem");
    if (quem && tipo in t().nomes) quem.textContent = t().nomes[tipo];
  });
  const pensando = el.terminal.querySelector(".corpo.pensando");
  if (pensando) pensando.textContent = t().pensando;
}

// Avisa o Python (para a IA responder no idioma certo). Se o backend ainda não tiver
// essa função, o front-end segue funcionando só com a interface traduzida.
async function avisarBackendIdioma() {
  try { await eel.set_language(idioma)(); } catch (e) {}
}

/* ---------- Avatar (expressões; se faltar a imagem, aparece o fundo.png; sem ele, o monitor fica vazio com borda) ---------- */

// GIF transparente de 1 pixel: deixa o <img> vazio sem mostrar o ícone de imagem quebrada
// (só é usado se faltar a expressão E o fundo.png).
const PIXEL_VAZIO = "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==";

// Cada expressão é uma imagem em web/expressoes/<nome>.<extensão>. Os nomes são os mesmos
// que o Gemini usa nas etiquetas (ver core/emocao.py). Etiqueta desconhecida cai em "neutro".
// O programa aceita .jpg, .jpeg, .png e .webp: ele descobre sozinho qual existe para cada uma.
const PASTA_EXPRESSOES = "expressoes";
const EXTENSOES = ["jpg", "jpeg", "png", "webp"];
const NOMES_EXPRESSOES = ["neutro", "feliz", "timido", "preocupado", "pensativo", "triste", "surpreso"];

const FONTES = {};              // nome -> caminho da imagem que existe
let descobertaConcluida = false;
let expressaoAtual = "neutro";

function descobrirImagem(nome) {
  return new Promise((resolve) => {
    let i = 0;
    const tentar = () => {
      if (i >= EXTENSOES.length) return resolve(null);
      const src = `${PASTA_EXPRESSOES}/${nome}.${EXTENSOES[i++]}`;
      const img = new Image();
      img.onload = () => { FONTES[nome] = src; resolve(src); };
      img.onerror = tentar;
      img.src = src;
    };
    tentar();
  });
}

function setExpressao(nome) {
  expressaoAtual = NOMES_EXPRESSOES.includes(nome) ? nome : "neutro";
  const src = FONTES[expressaoAtual];
  if (src) {
    el.monitor.classList.remove("vazio");
    el.avatar.src = src;
  } else if (descobertaConcluida) {
    // A imagem da expressão não existe: o aviso vai para o console (F12).
    console.warn(`Faltou a imagem da expressão "${expressaoAtual}" em ${PASTA_EXPRESSOES}/ (.jpg, .jpeg, .png ou .webp)`);
    if (FONTES.fundo) {
      // Mostra só o fundo do monitor, sem a personagem.
      el.monitor.classList.remove("vazio");
      el.avatar.src = FONTES.fundo;
    } else {
      // Nem o fundo existe: monitor vazio, só com a borda.
      el.monitor.classList.add("vazio");
      el.avatar.src = PIXEL_VAZIO;
    }
  }
}

// Procura todas as imagens de antemão (a troca fica instantânea) e mostra a atual quando achar.
// O "fundo" (monitor sem a personagem) é o que aparece quando falta a imagem de uma expressão.
Promise.all([...NOMES_EXPRESSOES, "fundo"].map(descobrirImagem)).then(() => {
  descobertaConcluida = true;
  setExpressao(expressaoAtual);
});

/* ---------- Som de visual novel ---------- */

function obterAudio() {
  if (!audioCtx) {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return null;
    audioCtx = new Ctx();
  }
  if (audioCtx.state === "suspended") audioCtx.resume();
  return audioCtx;
}

function tocarBlip() {
  if (!somLigado) return;
  const ctx = obterAudio();
  if (!ctx) return;

  const agora = ctx.currentTime;
  const osc = ctx.createOscillator();
  const ganho = ctx.createGain();

  osc.type = "triangle";
  osc.frequency.value = 500 + Math.random() * 250; // 500 a 750 Hz

  // Envelope curtinho para não estalar
  ganho.gain.setValueAtTime(0.0001, agora);
  ganho.gain.exponentialRampToValueAtTime(0.12, agora + 0.005);
  ganho.gain.exponentialRampToValueAtTime(0.0001, agora + 0.03);

  osc.connect(ganho).connect(ctx.destination);
  osc.start(agora);
  osc.stop(agora + 0.04);
}

/* ---------- Log de terminal ---------- */


// Cria uma linha no terminal e devolve o elemento onde o texto é escrito.
function novaLinha(tipo, texto = "") {
  const linha = document.createElement("div");
  linha.className = "linha " + tipo;

  const quem = document.createElement("span");
  quem.className = "quem";
  quem.textContent = t().nomes[tipo] || "";

  const corpo = document.createElement("span");
  corpo.className = "corpo";
  corpo.textContent = texto;

  linha.append(quem, corpo);
  el.terminal.appendChild(linha);
  el.terminal.scrollTop = el.terminal.scrollHeight;
  return corpo;
}

// Muda o tipo (cor e rótulo) de uma linha que já existe.
function definirTipo(corpo, tipo) {
  corpo.parentElement.className = "linha " + tipo;
  corpo.previousElementSibling.textContent = t().nomes[tipo] || "";
}

/* ---------- Efeito typewriter ---------- */

// Escreve `texto` letra por letra numa linha do terminal.
// Se `corpo` for informado, reaproveita essa linha (usado após o "Pensando...").
function falar(texto, { tipo = "model", som = true, corpo = null, expressao = null } = {}) {
  return new Promise((resolve) => {
    const meuId = ++fala.id;
    texto = String(texto ?? ""); // texto vazio ou indefinido não pode virar "undefined" na tela
    const letras = Array.from(texto);
    let i = 0;
    let visiveis = 0;

    if (expressao) setExpressao(expressao);
    if (corpo) definirTipo(corpo, tipo);
    else corpo = novaLinha(tipo);
    corpo.classList.remove("pensando");
    corpo.textContent = "";

    fala.falando = true;
    fala.pular = false;

    function terminar() {
      if (meuId === fala.id) {
        fala.falando = false;
        fala.pular = false;
      }
      resolve();
    }

    function passo() {
      if (meuId !== fala.id) return resolve(); // outra fala começou
      if (fala.pular) {
        corpo.textContent = texto;
        el.terminal.scrollTop = el.terminal.scrollHeight;
        return terminar();
      }

      const ch = letras[i++];
      corpo.textContent += ch;

      if (/\S/.test(ch)) {
        visiveis++;
        if (som && visiveis % BLIP_A_CADA === 0) tocarBlip();
      }
      el.terminal.scrollTop = el.terminal.scrollHeight;

      if (i >= letras.length) return terminar();

      let atraso = VELOCIDADE_MS;
      if (/[.!?…]/.test(ch)) atraso = 220;
      else if (/[,;:]/.test(ch)) atraso = 110;
      setTimeout(passo, atraso);
    }

    if (letras.length) passo();
    else terminar(); // nada para escrever
  });
}

// Clicar no terminal pula a animação.
el.terminal.addEventListener("click", () => {
  if (fala.falando) fala.pular = true;
});

function mostrarPensando() {
  fala.id++; // cancela qualquer fala em andamento
  fala.falando = false;
  // A imagem não muda enquanto espera a resposta; "pensativo" só entra quando o Gemini escolhe.
  const corpo = novaLinha("model", t().pensando);
  corpo.classList.add("pensando");
  return corpo;
}

const sistema = (texto) => falar(texto, { tipo: "sistema", som: false });
const erro = (texto) => falar(texto, { tipo: "erro", som: false, expressao: "preocupado" });

/* ---------- Tela cheia ---------- */

function alternarTelaCheia() {
  if (document.fullscreenElement) document.exitFullscreen();
  else document.documentElement.requestFullscreen().catch(() => {});
}

document.addEventListener("keydown", (ev) => {
  if (ev.key === "F11") {
    ev.preventDefault();
    alternarTelaCheia();
  }
});

/* ---------- Comandos (/ajuda, /som, /limpar, /tela, /idioma) ---------- */

async function executarComando(entrada) {
  const [cmdBruto, ...resto] = entrada.slice(1).trim().split(/\s+/);
  const arg = resto.join(" ").toLowerCase();
  const cmd = ALIAS[(cmdBruto || "").toLowerCase()];

  switch (cmd) {
    case "ajuda":
      return sistema(t().ajuda);

    case "som":
      somLigado = !somLigado;
      if (somLigado) tocarBlip();
      return sistema(t().som(somLigado));

    case "tela":
      alternarTelaCheia();
      return;

    case "idioma":
      await trocarIdioma(arg === "pt" || arg === "en" ? arg : null);
      return;

    case "chave":
      return pedirChave();

    case "limpar":
      if (!confirm(t().confirmarLimpar)) return;
      await eel.clear_history()();
      el.terminal.innerHTML = "";
      return falar(t().limpo, { som: false, expressao: "neutro" });

    default:
      return erro(t().desconhecido);
  }
}

// Texto de abertura no idioma atual (saudação inicial, ou "bem-vindo de volta" se já houve conversa).
function textoAbertura() {
  if (jaConversou) return t().bemVindoDeNovo;
  if (saudacoes) return saudacoes[idioma] || saudacoes.pt || t().bemVindoDeNovo;
  return t().bemVindoDeNovo;
}

// Alterna PT <-> EN (ou define um idioma específico): limpa o log na tela
// (o histórico salvo continua intacto) e fala a abertura no idioma novo.
async function trocarIdioma(novo = null) {
  idioma = novo || (idioma === "pt" ? "en" : "pt");
  try { localStorage.setItem("alterego_idioma", idioma); } catch (e) {}
  aplicarIdioma();
  await avisarBackendIdioma();
  el.terminal.innerHTML = "";
  return falar(textoAbertura(), { som: false, expressao: "feliz" });
}

el.idioma.addEventListener("click", () => {
  if (ocupado) return; // não troca no meio de uma resposta
  obterAudio();
  ocupado = true;
  trocarIdioma().finally(() => { ocupado = false; el.campo.focus(); });
});

/* ---------- Chave da API (primeira abertura e /chave) ---------- */

// Põe o campo de entrada em "modo chave": o próximo texto enviado é a chave, mostrada como bolinhas.
async function pedirChave() {
  esperandoChave = true;
  el.campo.classList.add("secreto");
  el.campo.placeholder = t().dicaChave;
  await sistema(t().pedirChave);
}

function sairDoModoChave() {
  esperandoChave = false;
  el.campo.classList.remove("secreto");
  el.campo.placeholder = t().dica;
}

async function salvarChave(chave) {
  if (MOSTRAR_SO_ULTIMA_TROCA) el.terminal.innerHTML = "";
  novaLinha("user", "••••••••"); // a chave nunca aparece no log
  let resp;
  try {
    resp = await eel.salvar_chave(chave)();
  } catch (e) {
    resp = { ok: false, error: t().semConexao };
  }
  if (resp.ok) {
    sairDoModoChave();
    await sistema(t().chaveSalva);
  } else {
    // continua em modo chave, para o usuário colar de novo
    await falar(resp.error, { tipo: "erro", som: false, expressao: "preocupado" });
  }
}

/* ---------- Envio de mensagens ---------- */

function travar(sim) {
  ocupado = sim;
  el.campo.disabled = sim;
  el.enviar.disabled = sim;
  if (!sim) el.campo.focus();
}

el.form.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const msg = el.campo.value.trim();
  if (!msg || ocupado) return;

  obterAudio(); // o navegador só libera o áudio após um gesto do usuário
  el.campo.value = "";

  // Pedido da chave: o texto digitado é a chave (não vai para a IA nem aparece no log).
  // Começar com "/" cancela o pedido e roda o comando normalmente.
  if (esperandoChave) {
    if (!msg.startsWith("/")) {
      travar(true);
      await salvarChave(msg);
      travar(false);
      return;
    }
    sairDoModoChave();
  }

  if (MOSTRAR_SO_ULTIMA_TROCA) el.terminal.innerHTML = "";
  novaLinha("user", msg);
  travar(true);

  if (msg.startsWith("/")) {
    try {
      await executarComando(msg);
    } catch (e) {
      await erro(t().falhaComando);
    }
    travar(false);
    return;
  }

  const linhaPensando = mostrarPensando();
  let resp;
  try {
    resp = await eel.send_message(msg)();
  } catch (e) {
    resp = { ok: false, error: t().semConexao };
  }

  travar(false);
  if (resp.ok) {
    jaConversou = true;
    await falar(resp.text, { corpo: linhaPensando, expressao: resp.emocao });
  } else {
    await falar(resp.error, { tipo: "erro", som: false, corpo: linhaPensando, expressao: "preocupado" });
  }
});

/* ---------- Inicialização ---------- */

async function iniciar() {
  setExpressao("feliz");
  aplicarIdioma();
  await avisarBackendIdioma();
  let dados;
  try {
    dados = await eel.boot()();
  } catch (e) {
    await erro(t().falhaInicio);
    return;
  }

  // Mostra o final da conversa anterior, sem animação.
  if (!MOSTRAR_SO_ULTIMA_TROCA) {
    dados.historico.slice(-LINHAS_NO_HISTORICO).forEach((m) => novaLinha(m.role, m.text));
  }

  // Se já houve conversa, cumprimenta de volta em vez de repetir a saudação inicial.
  saudacoes = dados.saudacoes;
  jaConversou = dados.historico.some((m) => m.role === "model");
  await falar(textoAbertura(), { som: false, expressao: "feliz" });
  if (!dados.tem_chave) await pedirChave(); // primeira abertura: pede a chave em vez de dar erro
}

window.addEventListener("load", iniciar);
