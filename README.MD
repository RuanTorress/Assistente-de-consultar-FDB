# (Substitua por Nome do Projeto) – Assistente Inteligente para Consultas em Firebird (.FDB)

> Gere SQL a partir de linguagem natural, diagnostique conexões Firebird, teste múltiplos drivers, use fallback entre modelos (OpenAI / Gemini / Offline) e explore seu banco de forma interativa.

---

## 📌 Visão Geral

Este projeto reúne vários scripts Python que:
- Conectam (ou tentam conectar) a bancos Firebird (`.FDB`)
- Geram consultas SQL a partir de perguntas em linguagem natural (PT-BR)
- Alternam dinamicamente entre modelos (OpenAI / Gemini) com fallback offline
- Fazem diagnóstico de ambiente e drivers
- Oferecem modos simplificado, híbrido, multi-driver, demo (SQLite) e offline

Você pode usá-lo como:
- Ferramenta de exploração interativa
- Base para um pacote Python
- Assistente interno (“copilot”) para Firebird
- Ferramenta de treinamento e demonstração

---

## ✨ Principais Recursos

| Recurso | Script Principal | Descrição |
|---------|------------------|-----------|
| Chat + Geração de SQL (Firebird real) | `main_central.py`, `main_hibrido.py` | Conversa e executa SQL diretamente no banco |
| Multi-driver (fdb / firebirdsql / firebird.driver) | `main_multi_driver.py` | Tenta diferentes drivers automaticamente |
| Diagnóstico de conexão | `diagnostico_firebird.py` | Testa várias configurações e relata falhas |
| Geração sem conexão | `main_sql_generator.py`, `main_simples.py` | Produz apenas SQL para execução manual |
| Modo híbrido OpenAI ↔ Gemini | `main_hibrido.py`, `main_central.py` | Troca de provedor e fallback |
| Duas chaves OpenAI | `main_dupla_api.py` | Rotação entre duas contas/chaves |
| Demo com SQLite (simulação) | `main_demo.py` | Simula um ambiente para demonstração |
| Modo totalmente offline | `main_offline.py` | Responde com SQL pré-mapeada sem IA |
| Dicionário offline inteligente | Vários scripts | Palavras‑chave → consultas úteis |

---

## 🧱 Estrutura Atual (Sugestão de Organização Futuras)

```
.
├── diagnostico_firebird.py
├── main.py
├── main_central.py
├── main_demo.py
├── main_dupla_api.py
├── main_hibrido.py
├── main_multi_driver.py
├── main_offline.py
├── main_simples.py
├── main_sql_generator.py
├── Redmir.md          (arquivo antigo - pode remover ou substituir)
└── README.md          (este arquivo)
```

Sugerido para evolução (pacote):
```
seu_projeto/
  core/
    connection.py
    drivers.py
    diagnostics.py
  ai/
    openai_provider.py
    gemini_provider.py
    offline_fallback.py
  cli/
    chat.py
    generate.py
    offline.py
    demo.py
  prompts/
    firebird_rules.txt
  utils/
    normalize.py
    env.py
```

---

## ✅ Pré-Requisitos

- Python 3.10+ (recomendado)
- Firebird instalado (para uso real): https://firebirdsql.org/en/downloads/
- Cliente ou biblioteca (`fbclient.dll` no Windows) acessível no PATH
- Drivers Python:
  - `fdb`
  - (Opcional) `firebirdsql`, `firebird-driver`
- Contas válidas (se usar IA) para:
  - OpenAI
  - Google Gemini

---

## 📦 Instalação das Dependências

```bash
python -m venv .venv
# Ativar ambiente:
# Windows PowerShell:
. .venv/Scripts/Activate.ps1
# Linux/Mac:
source .venv/bin/activate

pip install --upgrade pip
pip install fdb
pip install firebirdsql firebird-driver     # (opcionais)
pip install openai
pip install google-generativeai
python -m pip install python-dotenv         # (recomendado para .env)
```

---

## 🔐 Configuração de Variáveis de Ambiente

NUNCA armazene chaves reais dentro dos arquivos Python em produção.

Crie um arquivo `.env`:

```
OPENAI_API_KEY=coloque_sua_chave_aqui
GEMINI_API_KEY=coloque_sua_chave_aqui
FIREBIRD_DB_PATH=C:\caminho\para\CENTRAL.FDB
FIREBIRD_HOST=localhost
FIREBIRD_PORT=3050
FIREBIRD_USER=SYSDBA
FIREBIRD_PASSWORD=masterkey
```

Use no código:

```python
from dotenv import load_dotenv
import os
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
```

---

## ⚠️ Segurança

- Remova todas as chaves hardcoded antes de comitar (estão expostas nos scripts).
- Faça um commit substituindo-as por leitura via `os.getenv`.
- Se as chaves já estiverem públicas, revogue-as nos painéis OpenAI / Google.

---

## 🚀 Modos de Uso (Scripts)

### 1. Diagnóstico de Conexão

```bash
python diagnostico_firebird.py
```
Testa múltiplas formas de conexão (porta 4050/3050, DSN, embedded) e retorna a primeira válida.

### 2. Chat com Execução Real (multi API)

```bash
python main_menu.py
```
Comandos úteis no chat:

- `trocar` → alterna OpenAI/Gemini
- `sair` → finaliza

### 3. Modo Híbrido Inteligente

```bash
python main_hibrido.py
```
Similar ao central, mas com regras mais contextuais (ex: “TEM TABELA X”).

### 4. Multi-Driver Auto-Teste

```bash
python main_multi_driver.py
```
Percorre `fdb`, `firebirdsql`, `firebird.driver` e tenta diferentes configs.

### 5. Gerador de SQL (sem conexão)

```bash
python main_sql_generator.py
```
Ideal quando o Firebird não está disponível.

### 6. Duas Chaves OpenAI

```bash
python main_dupla_api.py
```
Rotaciona entre `openai_1` e `openai_2` quando há erro de cota.

### 7. Demo com SQLite (para demonstrar sem Firebird)

```bash
python main_demo.py
```
Simula tabela `CLI_CLIENTE` em memória.

### 8. Modo Simples

```bash
python main_simples.py
```
Entrada → Geração de SQL → Saída (somente).

### 9. Modo Offline Total

```bash
python main_offline.py
```
Mapeia termos para SQL pré-definida sem IA.

---

## 🔄 Fluxo de Fallback (IA)

Ordem típica implementada:
1. Tenta gerar SQL com OpenAI
2. Se quota/erro: muda para Gemini
3. Se falhar novamente: usa dicionário offline
4. Caso o script suporte multi-driver: retorna SQL mesmo sem conexão

---

## 🧠 Regras de Geração de SQL (Resumo)

- Usa `FIRST X` em vez de `LIMIT X` (Firebird)
- Para listar tabelas:  
  `SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0`
- Para campos:  
  `SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'NOME'`
- Para buscar:  
  `SELECT * FROM TABELA WHERE CAMPO LIKE '%valor%'`
- Normaliza strings retirando espaços de padding
- Oferece consultas contextuais (clientes, procedures, triggers, generators)

---

## 🧪 Exemplos de Perguntas

Pergunta:
```
lista as tabelas
```
Resposta (esperada):
```
SELECT RDB$RELATION_NAME
FROM RDB$RELATIONS
WHERE RDB$SYSTEM_FLAG = 0
ORDER BY RDB$RELATION_NAME
```

Pergunta:
```
tem cliente Maria?
```
Resposta:
```
SELECT * FROM CLI_CLIENTE WHERE UPPER(NOME) LIKE '%MARIA%'
```

Pergunta:
```
quantos clientes tem
```
Resposta:
```
SELECT COUNT(*) FROM CLI_CLIENTE
```

---

## 🔧 Próximos Passos (Roadmap Sugerido)

- [ ] Criar pacote instalável (`pyproject.toml`)
- [ ] Unificar prompts em arquivos externos (ex: `prompts/`)
- [ ] Implementar logging estruturado (`logging` + níveis)
- [ ] Adicionar testes unitários (pytest) para dicionário offline
- [ ] Adicionar modo REST (FastAPI)
- [ ] Adicionar cache de respostas (functools.lru_cache ou Redis)
- [ ] Sanitização de perguntas antes de virar SQL (reduzir risco de injection)
- [ ] Suporte a múltiplos bancos (Firebird → PostgreSQL adaptável)
- [ ] Dockerfile (com fbclient pré-instalado)
- [ ] Integração com interface web (Streamlit ou FastAPI + HTMX)

---

## 🤝 Contribuindo

1. Faça um fork
2. Crie uma branch: `feature/melhorias`
3. Commits descritivos (PT ou EN)  
4. Abra PR explicando o contexto

Sugestão de padrão de commit:
```
feat(sql): adiciona regra para buscar por email
fix(conn): corrige fallback ao driver firebirdsql
docs(readme): melhora seção de instalação
```

---

## 📝 Licença

(Escolha uma: MIT / Apache-2.0 / BSD-3 / Proprietária interna).  
Exemplo MIT:

```
MIT License (coloque aqui o texto completo da MIT)
```

---

## ❓ FAQ

| Pergunta | Resposta |
|----------|----------|
| Falhou na porta 4050 | Tente 3050 ou verifique serviço do Firebird |
| Não lista tabelas | Usuário sem permissão ou banco vazio |
| Acentos estranhos | Defina `charset='UTF8'` na conexão |
| Retorna espaços em strings | Campos CHAR fixos – use `.strip()` (já tratado em alguns scripts) |
| Chave OpenAI inválida | Revogue e gere nova no painel da OpenAI |
| Quero rodar no Linux | Instale o pacote `firebird` e a client library (`libfbclient.so`) |

---

## 🧹 Limpeza e Boas Práticas

- Remova `Redmir.md` (grafia incorreta) e mantenha apenas `README.md`.
- Use `.gitignore` para:  
  ```
  .venv/
  .env
  __pycache__/
  *.log
  ```
- Caso publique, remova caminhos absolutos (ex: `C:\Users\Dev Ruan\...`).

---

## 🛟 Suporte / Dúvidas

Abra uma issue ou envie uma pergunta descrevendo:
- Sistema Operacional
- Versão Python
- Script usado
- Stack trace (se houver)

---

## 🔄 Personalização do Nome

Edite o topo substituindo “(Substitua por Nome do Projeto)”. Exemplos prontos:
- FirebirdLens
- fdbchat
- FireSQL Forge
- QueryBird

Escolha um, substitua e ajuste o slogan.

---

Feito com foco em produtividade e exploração inteligente de bancos Firebird.  
Contribua, adapte e evolua!
