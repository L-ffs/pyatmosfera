# Atmosfera

Aplicação web que mostra o clima atual e a previsão dos próximos dias das cidades favoritas do usuário.
Refatoração em Python do projeto original em C++ (trabalho de DCC117).

**Tecnologias:** Python 3.13, FastAPI, Cloudflare Workers, Firestore (somente banco de dados),
Open-Meteo (busca de cidades e previsão), HTML/CSS/JavaScript, pytest.

## Funcionalidades (requisitos funcionais)

| RF | Funcionalidade | Rota |
|----|----------------|------|
| RF1 | Criar conta | `POST /api/auth/signup` |
| RF2 | Fazer login | `POST /api/auth/login` (cria o cookie de sessão) |
| RF3 | Pesquisar cidades | `GET /api/cities/search?q=` |
| RF4 | Favoritar cidade | `POST /api/favorites` |
| RF5 | Ver clima das cidades favoritas | `GET /api/weather/favorites` |
| RF6 | Remover cidade favorita | `DELETE /api/favorites/{chave}` |
| RF7 | Alterar senha | `POST /api/auth/password` |

Também existem `POST /api/auth/logout` e `GET /api/me`.

## Como o código está organizado

O servidor valida os dados, guarda a senha com hash PBKDF2 e controla a sessão (JWT em cookie
`HttpOnly`). O Firestore só armazena os dados. A organização segue o padrão Fronteira–Controle–Entidade:

```
src/atmosfera/
  boundary/   routers (auth, cidades, clima), modelos de requisição, dependências, tratamento de erros
  control/    AuthService, SessionService, CityService, WeatherService  (regras dos casos de uso)
  entity/     User, City, WeatherSnapshot e afins
  external/   FirestoreClient, UserRepository, GeocodingClient, ForecastClient  (conversa com os sistemas externos)
  support/    Settings, PasswordHasher, TtlCache, HttpClient, erros
  main.py     cria o app FastAPI
src/entry.py  ponto de entrada do Cloudflare Workers
src/dev.py    servidor para desenvolvimento local
public/       páginas estáticas: login (index.html), cadastro e home
tests/        testes pytest
```

## Rodar localmente

Requisitos: [uv](https://docs.astral.sh/uv/) e Python 3.13.

```bash
uv sync
cp .dev.vars.example .env        # preencha SESSION_SECRET e FIRESTORE_PROJECT_ID
export $(grep -v '^#' .env | xargs)
uv run uvicorn dev:app --app-dir src --reload
# abra http://localhost:8000
```

Testes:

```bash
uv run pytest
```

## Publicar no Cloudflare (pelo GitHub)

1. Em `wrangler.jsonc`, troque `FIRESTORE_PROJECT_ID` pelo ID do seu projeto Firebase e envie o código ao GitHub.
2. No painel da Cloudflare: **Workers & Pages → Create → Import a repository** e escolha o repositório.
3. Comando de deploy: `uv run pywrangler deploy` (confira na documentação da Cloudflare, pois o
   suporte a Python Workers ainda é novo).
4. Em **Settings → Variables and Secrets**, cadastre o segredo `SESSION_SECRET` (texto aleatório com 32 ou mais caracteres).

## Firestore

O sistema usa a API REST do Firestore **sem credenciais** (como no projeto original). Isso exige regras
que permitam leitura e escrita na coleção `users`. É aceitável para este trabalho, mas **qualquer pessoa
que conheça o ID do projeto consegue ler os dados da coleção** (os hashes das senhas, não as senhas).
Em produção o correto seria usar uma conta de serviço e fechar as regras.

## Limitações conhecidas

- O logout apaga o cookie, mas o token não é revogado no servidor (sessão sem estado). Ele expira em 8 horas.
- O custo de CPU do PBKDF2 (100 mil iterações) pode passar do limite do plano gratuito do Workers.
  O número é configurável em `PBKDF2_ITERATIONS`.
- O cache de clima e de buscas vive na memória de cada instância e se perde quando ela reinicia.
