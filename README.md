# Catálogo de TCCs — IFPB

Atividade 07 de Rapid Application Development — Sistemas para Internet.

**Autor: Felipe Oliveira Raimundo. Modalidade: individual.**

Entrega individual conforme opção do aluno. Os desafios opcionais A (segunda versão) e B (cliente de gestão) não foram implementados.

## Organização

- `backend/`: Django e DRF; devolve JSON, com exceção da documentação gerada pelo drf-spectacular.
- `frontend/`: cliente independente em **HTML, CSS e JavaScript puro**, servido na porta 5500. Não usa templates Django, dados estáticos de trabalhos, localStorage ou service worker.
- `backend/db.sqlite3`: banco com dados fictícios já carregados.

Requer Python 3.12 ou superior. Comandos abaixo executados na raiz do repositório no PowerShell, sem precisar ativar o ambiente virtual.

## Executar o back-end

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe backend/manage.py migrate
.\.venv\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8000
```

API: http://127.0.0.1:8000/api/publico/v1/trabalhos/

## Executar o front-end

Em outro terminal, na raiz:

```powershell
.\.venv\Scripts\python.exe -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

Abra **http://127.0.0.1:5500/**. Não abra o HTML por `file://`. CORS permite `localhost:5500` e `127.0.0.1:5500`; a API é consultada em `127.0.0.1:8000`.

Busca e filtros são enviados ao servidor ao clicar em Buscar ou pressionar Enter; não existe uma chamada a cada tecla. Cada página contém seis itens. Ao escolher um trabalho, o detalhe é buscado novamente na API. Em falhas, os cartões são removidos e a tela informa o erro; não há cópia local dos dados.

## Contas da coordenação

Credenciais **exclusivamente para demonstração local e avaliação**, já presentes no banco entregue:

| Usuário | Senha | Token |
| --- | --- | --- |
| coordenacao1 | CatalogoTCC@12026 | 7d3e8f931919fccc6971439ffd5435d6eeba69c7 |
| coordenacao2 | CatalogoTCC@22026 | a838ab8d56cb27139a4f0e4ccaf12f9a0114df82 |

As duas contas têm `is_staff=True`; usuários comuns não entram na gestão. Autores são registros acadêmicos, sem conta de acesso. O projeto não depende de cookies ou sessões.

Obter o token novamente:

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/gestao/token/ -d "username=coordenacao1" -d "password=CatalogoTCC@12026"
curl.exe http://127.0.0.1:8000/api/gestao/trabalhos/ -H "Authorization: Token 7d3e8f931919fccc6971439ffd5435d6eeba69c7"
```

O cadastro do trabalho usa o usuário do token em `cadastrado_por`. Se o cliente enviar esse campo no JSON, o valor será ignorado. A ausência de token retorna 401; token de usuário sem acesso à coordenação retorna 403.

## Endpoints e documentação

**Swagger UI:** http://127.0.0.1:8000/api/docs/

**OpenAPI:** http://127.0.0.1:8000/api/schema/

| Método | Endereço | Acesso / finalidade |
| --- | --- | --- |
| GET | `/api/publico/v1/trabalhos/` | Aberto, lista paginada de publicados |
| GET | `/api/publico/v1/trabalhos/{id}/` | Aberto, detalhe de publicado |
| GET | `/api/publico/v1/estatisticas/` | Aberto, contagens e ranking |
| POST | `/api/gestao/token/` | Usuário/senha → token |
| GET, POST | `/api/gestao/trabalhos/` | Coordenação: listar/criar |
| GET, PUT, PATCH, DELETE | `/api/gestao/trabalhos/{id}/` | Coordenação: consultar/alterar/excluir |
| GET, POST | `/api/gestao/cursos/` | Coordenação: listar/criar curso |
| GET, POST | `/api/gestao/orientadores/` | Coordenação: listar/criar orientador |
| GET, POST | `/api/gestao/autores/` | Coordenação: listar/criar autor |
| GET, POST | `/api/gestao/palavras-chave/` | Coordenação: listar/criar palavra-chave |
| GET, PUT, PATCH, DELETE | `/api/gestao/{recurso}/{id}/` | Detalhe/edição/exclusão de cada cadastro de apoio |

Na escrita, relacionamentos recebem IDs. Use a gestão autenticada para consultar os IDs dos cadastros. Exemplo de JSON para criar um trabalho:

```json
{
  "titulo": "Avaliação de acessibilidade em portais acadêmicos",
  "resumo": "Pesquisa aplicada sobre acessibilidade digital no ensino superior.",
  "ano": 2026,
  "situacao": "em_andamento",
  "link_pdf": "https://example.org/pesquisa.pdf",
  "curso": 1,
  "orientador": 1,
  "coorientador": null,
  "autores": [1],
  "palavras_chave": [1, 2]
}
```

Para publicar, faça PATCH no trabalho com `situacao: "publicado"`, `nota: "9.00"` e `data_defesa: "2026-03-15"`. A API valida o estado final, inclusive em PATCH: não permite remover nota ou data de um trabalho publicado. Trabalhos defendidos também precisam de nota.

### Busca, filtros e ordenação

```text
/api/publico/v1/trabalhos/?search=energia
/api/publico/v1/trabalhos/?search=Ana%20Beatriz
/api/publico/v1/trabalhos/?ano=2026&curso=1
/api/publico/v1/trabalhos/?palavra_chave=Django&ano=2026&curso=1&search=bibliotecas
/api/publico/v1/trabalhos/?ordering=titulo&page=2
/api/publico/v1/trabalhos/?ordering=-ano
```

`search` consulta título, resumo, nome dos autores e nome do orientador. `curso` é o ID; `palavra_chave` é o termo completo, sem diferenciar maiúsculas/minúsculas. Todos os filtros podem ser combinados. `ordering` aceita `ano`, `-ano`, `titulo` e `-titulo`. A paginação devolve `count`, `next`, `previous` e `results`.

## As três decisões do contrato público

### 1. Quais registros e campos são públicos

**Recorte de registros:** somente `situacao=publicado`. Em andamento e defendido ficam restritos à gestão. O filtro acontece no queryset, antes de serializar: tentar acessar diretamente o ID de um trabalho não publicado retorna **404**.

**Recorte de campos:** `id`, `titulo`, `resumo` integral, `ano`, `data_defesa`, `link_pdf`, `curso`, `orientador`, `coorientador`, `autores` e `palavras_chave`. Curso, orientadores e autores são nomes legíveis; curso inclui a sigla. Palavras-chave são termos.

Ficam de fora **nota, todos os e-mails, usuário cadastrador e situação interna**. A nota pertence ao processo avaliativo; os contatos não são necessários para pesquisar o acervo; o cadastrador é informação operacional. A publicação já é garantida pelo recorte de registros. Os serializers público e de gestão são classes diferentes, com listas explícitas de campos.

As estatísticas também usam somente publicados. `Count` e agrupamentos são executados pelo banco: números por ano, por curso e ranking decrescente dos orientadores por quantidade de orientações. Coorientações não entram nesse ranking. Não existem campos de estatística persistidos.

### 2. Versionamento e duração da promessa

**Porta pública:** versão no endereço, `/api/publico/v1/`. A promessa é manter nomes, tipos, significado dos campos, formato da paginação e URLs da v1 durante sua vida útil. Um campo não será renomeado/removido silenciosamente. Mudanças incompatíveis exigem uma nova versão e convivência de no mínimo **seis meses** com a versão anterior, contados do anúncio de descontinuação em documentação pública. Não há data programada de retirada da v1. Campos opcionais novos podem ser adicionados; clientes devem tolerar campos desconhecidos.

**Porta de gestão:** `/api/gestao/`, sem versão no endereço. É um contrato interno da coordenação e pode ser atualizado junto dos clientes internos, com aviso prévio aos responsáveis. Evita manter versões paralelas de um fluxo controlado. Isso não altera a estabilidade prometida à porta pública. Nesta entrega existe somente a v1: o desafio opcional de segunda versão não foi feito.

### 3. Limite de uso e resposta

**20 requisições por minuto por IP**, em janela móvel, compartilhadas entre lista, detalhe e estatísticas públicas, usando `AnonRateThrottle` do DRF. Os endpoints públicos não processam token: sempre são abertos e o limite por IP continua igual, inclusive se alguém enviar um cabeçalho de autenticação. Não é possível escapar do limite simplesmente anexando um token.

Ao exceder, o cliente recebe **429 Too Many Requests**, corpo JSON com `detail` e cabeçalho **Retry-After** indicando quantos segundos esperar. O cliente deve aguardar, em vez de insistir. Demonstração no PowerShell:

```powershell
1..21 | ForEach-Object { curl.exe -s -o NUL -w "%{http_code}\n" http://127.0.0.1:8000/api/publico/v1/trabalhos/ }
```

Espere um minuto sem consultas antes de demonstrar para começar com a janela limpa. O limite usa o cache local em memória, adequado ao servidor único da atividade; reiniciar o Django limpa a janela. O throttling padrão do DRF é um controle de uso com contagem aproximada sob concorrência, não uma defesa contra DDoS. Em vários processos, seria necessário um cache compartilhado.

## ViewSets e APIView

- `TrabalhoPublicoViewSet` é somente leitura. `TrabalhoGestaoViewSet` e os quatro cadastros de apoio usam `ModelViewSet` com routers: são recursos CRUD convencionais e reaproveitam o fluxo padrão.
- `EstatisticasView` usa **APIView** com `get()`: devolve agregações de diferentes agrupamentos, não o CRUD de uma entidade. A implementação explícita deixa o contrato dessa resposta visível.
- `TokenView` especializa a view de token do DRF para limitar tentativas e documentar a entrada.

## Validações e integridade

- Ano futuro: validator do campo do model.
- Publicação com nota e data: `Trabalho.clean()`, chamado pelo serializer após mesclar os dados enviados com os dados atuais.
- Um ou dois autores distintos: serializer, pois a relação ManyToMany ainda não existe antes de salvar o trabalho. Não é suficiente tentar contar autores em um model ainda sem PK.
- Título + curso + ano: checagem no serializer e `UniqueConstraint` no banco.
- Notas entre 0 e 10; e-mails e URLs com validação de formato.
- Exclusões de cursos/orientadores em uso são bloqueadas; excluir o único autor de um trabalho também é bloqueado.

Erros de validação e exclusão protegida retornam **400 com JSON**; nenhum dado inválido precisa passar por uma view para ser validado. As views apenas consultam, agregam e atribuem o usuário autenticado. A API usa `select_related`, `prefetch_related` e busca sem repetição de trabalhos para evitar consultas por item e duplicatas nos relacionamentos.

## Dados de demonstração

O banco entregue contém **4 cursos, 8 orientadores, 36 trabalhos em seis anos, 15 palavras-chave reaproveitadas, 30 publicados, 3 defendidos, 3 em andamento, 6 trabalhos com dois autores e 2 contas da coordenação com token**. Os nomes e dados são fictícios; os links `example.org` são ilustrativos, não arquivos reais.

Para recarregar os mesmos dados (idempotente, sem apagar outros registros):

```powershell
.\.venv\Scripts\python.exe backend/manage.py seed
```

O comando preserva tokens existentes e imprime os tokens gerados caso o banco tenha sido recriado. Nesse caso, use os novos valores impressos. Reaplica as senhas de demonstração às duas contas.

## Verificação

```powershell
.\.venv\Scripts\python.exe backend/manage.py check
.\.venv\Scripts\python.exe backend/manage.py test catalogo
.\.venv\Scripts\python.exe backend/manage.py spectacular --file backend/schema.yaml --validate
```

Dez testes automatizados exercitam: recorte de registros e campos; nomes e detalhe; busca nos quatro campos; filtros combinados; ordenação; paginação; estatísticas; token sem sessão; usuário sem permissão; CRUD dos trabalhos e cadastros de apoio; publicação e PATCH; ano/autores/duplicidade; atribuição do cadastrador; CORS; 429 e Retry-After; schema e documentação.

Verificado no navegador: listagem, detalhe com resumo e palavras-chave, busca por energia, combinação com filtro por ano, estado vazio e API desligada. Para repetir o último teste, pare apenas o terminal do Django com Ctrl+C e recarregue a página do front-end: nenhum trabalho deve aparecer, e a mensagem de conexão deve orientar a tentar novamente. Depois reinicie o Django.

## Referências

- [DRF: autenticação por token](https://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication)
- [DRF: permissões](https://www.django-rest-framework.org/api-guide/permissions/)
- [DRF: throttling](https://www.django-rest-framework.org/api-guide/throttling/)
- [drf-spectacular: personalização do schema](https://drf-spectacular.readthedocs.io/en/latest/customization.html)

Configurações e credenciais são destinadas à avaliação local. Para uma publicação real, usar uma chave secreta própria, DEBUG desativado, credenciais novas e HTTPS; os dados entregues não devem ser confundidos com um acervo institucional real.
