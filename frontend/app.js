const API = 'http://127.0.0.1:8000/api/publico/v1/';
const form = document.querySelector('#filtros');
const lista = document.querySelector('#trabalhos');
const status = document.querySelector('#status');
const contagem = document.querySelector('#contagem');
const anterior = document.querySelector('#anterior');
const proxima = document.querySelector('#proxima');
const dialog = document.querySelector('#detalhe');
let pagina = 1, totalPaginas = 1;
let controller;

function elemento(tag, texto, classe) {
  const node = document.createElement(tag);
  if (texto !== undefined) node.textContent = texto;
  if (classe) node.className = classe;
  return node;
}
async function consultar(url, signal) {
  const resposta = await fetch(url, {signal, cache: 'no-store'});
  if (!resposta.ok) {
    if (resposta.status === 429) throw new Error(`Limite de consultas atingido. Aguarde ${resposta.headers.get('Retry-After') || '60'} segundos e tente novamente.`);
    throw new Error(`Não foi possível consultar o acervo (erro ${resposta.status}). Tente novamente.`);
  }
  return resposta.json();
}
function mensagemErro(erro) {
  return erro instanceof TypeError ? 'Não foi possível conectar à API. Verifique se o Django está ligado em 127.0.0.1:8000 e tente buscar novamente.' : erro.message;
}
function cartao(t) {
  const card = elemento('article', undefined, 'card');
  const meta = elemento('div', undefined, 'metadados');
  meta.append(elemento('span', t.curso, 'curso'), elemento('span', t.ano));
  const botao = elemento('button', 'Conhecer pesquisa ↗');
  botao.type = 'button';
  botao.setAttribute('aria-label', `Conhecer pesquisa: ${t.titulo}`);
  botao.addEventListener('click', () => abrirDetalhe(t.id));
  card.append(meta, elemento('h3', t.titulo), elemento('p', t.autores.join(' e ')),
    elemento('p', `Orientação: ${t.orientador}`), botao);
  return card;
}
async function carregar() {
  controller?.abort(); controller = new AbortController();
  lista.replaceChildren(); status.textContent = 'Buscando trabalhos…';
  anterior.disabled = true; proxima.disabled = true;
  contagem.textContent = 'Consultando…'; document.querySelector('#pagina').textContent = '';
  const params = new URLSearchParams(new FormData(form));
  for (const [chave, valor] of [...params]) if (!valor.trim()) params.delete(chave);
  params.set('page', pagina);
  try {
    const dados = await consultar(`${API}trabalhos/?${params}`, controller.signal);
    totalPaginas = Math.max(1, Math.ceil(dados.count / 6));
    contagem.textContent = `${dados.count} trabalho${dados.count === 1 ? '' : 's'} no acervo`;
    status.textContent = dados.results.length ? '' : 'Nenhum trabalho encontrado. Experimente outro termo ou remova o filtro de ano.';
    lista.replaceChildren(...dados.results.map(cartao));
    anterior.disabled = !dados.previous; proxima.disabled = !dados.next;
    document.querySelector('#pagina').textContent = `Página ${pagina} de ${totalPaginas}`;
  } catch (erro) {
    if (erro.name === 'AbortError') return;
    lista.replaceChildren(); status.textContent = mensagemErro(erro);
    contagem.textContent = 'Acervo indisponível';
  }
}
async function abrirDetalhe(id) {
  const conteudo = document.querySelector('#conteudo-detalhe');
  conteudo.replaceChildren(elemento('p', 'Carregando pesquisa…'));
  dialog.showModal();
  try {
    const t = await consultar(`${API}trabalhos/${id}/`);
    const tags = elemento('div', undefined, 'tags');
    tags.append(...t.palavras_chave.map(p => elemento('span', p)));
    conteudo.replaceChildren(elemento('p', `${t.curso} • ${t.ano}`, 'eyebrow'),
      elemento('h2', t.titulo), elemento('p', `Autores: ${t.autores.join(' e ')}`),
      elemento('p', `Orientação: ${t.orientador}${t.coorientador ? ' • Coorientação: ' + t.coorientador : ''}`),
      elemento('h3', 'Resumo'), elemento('p', t.resumo), elemento('h3', 'Palavras-chave'), tags);
    // Só permite protocolos seguros no link recebido da API.
    const url = new URL(t.link_pdf);
    if (['https:', 'http:'].includes(url.protocol)) {
      const link = elemento('a', 'Abrir arquivo PDF ↗', 'pdf');
      link.href = url.href; link.target = '_blank'; link.rel = 'noopener noreferrer';
      conteudo.append(link);
    }
    conteudo.querySelector('h2').id = 'titulo-detalhe';
  } catch (erro) { conteudo.replaceChildren(elemento('p', mensagemErro(erro))); }
}
form.addEventListener('submit', e => { e.preventDefault(); pagina = 1; carregar(); });
anterior.addEventListener('click', () => { if (pagina > 1) { pagina--; carregar(); } });
proxima.addEventListener('click', () => { if (pagina < totalPaginas) { pagina++; carregar(); } });
document.querySelector('#fechar').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', e => { if (e.target === dialog) { const r = dialog.getBoundingClientRect(); if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dialog.close(); } });
carregar();
