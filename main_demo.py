import os
import sqlite3
from openai import OpenAI
import google.generativeai as genai

# 🔑 Configurar múltiplas APIs (OpenAI + Gemini)
API_KEYS = {
    "openai": "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",
    "gemini": "AIzaSyDeTIz34pWW760D14Quh9Z_E7YPC4lQdFo"
}

current_api = "openai"

# Configurar APIs
os.environ["OPENAI_API_KEY"] = API_KEYS["openai"]
genai.configure(api_key=API_KEYS["gemini"])

# Inicializar clientes
openai_client = OpenAI()
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

def trocar_api():
    global current_api
    if current_api == "openai":
        current_api = "gemini"
        print("🔄 Trocando para Google Gemini...")
    else:
        current_api = "openai"
        print("🔄 Trocando para OpenAI...")
    print(f"🔑 API atual: {current_api}")

# 🗄️ Criar banco SQLite simulando Firebird (para demonstração)
def criar_banco_demo():
    conn = sqlite3.connect(':memory:')  # Banco em memória
    cur = conn.cursor()
    
    # Criar tabela CLI_CLIENTE com dados demo
    cur.execute('''
        CREATE TABLE CLI_CLIENTE (
            ID INTEGER PRIMARY KEY,
            NOME TEXT,
            EMAIL TEXT,
            TELEFONE TEXT,
            CIDADE TEXT
        )
    ''')
    
    # Inserir dados de exemplo
    dados_demo = [
        (1, 'Maria Silva', 'maria@email.com', '(11) 9999-1111', 'São Paulo'),
        (2, 'João Santos', 'joao@email.com', '(11) 8888-2222', 'Rio de Janeiro'),
        (3, 'Ana Costa', 'ana@email.com', '(11) 7777-3333', 'Belo Horizonte'),
        (4, 'Carlos Oliveira', 'carlos@email.com', '(11) 6666-4444', 'Salvador'),
        (5, 'Fernanda Lima', 'fernanda@email.com', '(11) 5555-5555', 'Brasília'),
    ]
    
    cur.executemany('''
        INSERT INTO CLI_CLIENTE (ID, NOME, EMAIL, TELEFONE, CIDADE) 
        VALUES (?, ?, ?, ?, ?)
    ''', dados_demo)
    
    # Criar tabela simulando RDB$RELATIONS
    cur.execute('''
        CREATE TABLE RDB_RELATIONS (
            RDB_RELATION_NAME TEXT,
            RDB_SYSTEM_FLAG INTEGER
        )
    ''')
    
    cur.execute('''
        INSERT INTO RDB_RELATIONS VALUES ('CLI_CLIENTE', 0)
    ''')
    
    conn.commit()
    print("🗄️ Banco de demonstração criado com 5 clientes!")
    return conn, cur

# Criar banco demo
conn, cur = criar_banco_demo()

print("💬 Chat com Firebird DEMO - OpenAI + Gemini (digite 'sair' para encerrar)")
print(f"🔑 API atual: {current_api}")
print("💡 Digite 'trocar' para alternar entre OpenAI e Gemini")
print("🎯 Usando banco SQLite simulando Firebird")

def gerar_sql_openai(pergunta):
    prompt = f"""
    Você é um assistente SQL para banco Firebird. Converta a seguinte pergunta em uma consulta SQL para SQLite (que simula Firebird):
    
    Pergunta: {pergunta}
    
    Contexto: Temos uma tabela CLI_CLIENTE com campos: ID, NOME, EMAIL, TELEFONE, CIDADE
    
    Regras importantes:
    - Para verificar tabelas use: SELECT name FROM sqlite_master WHERE type='table' AND name='CLI_CLIENTE'
    - Para contar use: SELECT COUNT(*) FROM CLI_CLIENTE
    - Para buscar cliente use: SELECT * FROM CLI_CLIENTE WHERE NOME LIKE '%nome%'
    - Use LIMIT X em vez de FIRST X (SQLite)
    - Responda apenas com a SQL, sem explicações
    """
    
    resp = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.1
    )
    return resp.choices[0].message.content.strip()

def gerar_sql_gemini(pergunta):
    prompt = f"""
    Você é um assistente SQL para banco Firebird. Converta a seguinte pergunta em uma consulta SQL para SQLite (que simula Firebird):
    
    Pergunta: {pergunta}
    
    Contexto: Temos uma tabela CLI_CLIENTE com campos: ID, NOME, EMAIL, TELEFONE, CIDADE
    
    Regras importantes:
    - Para verificar tabelas use: SELECT name FROM sqlite_master WHERE type='table' AND name='CLI_CLIENTE'
    - Para contar use: SELECT COUNT(*) FROM CLI_CLIENTE
    - Para buscar cliente use: SELECT * FROM CLI_CLIENTE WHERE NOME LIKE '%nome%'
    - Use LIMIT X em vez de FIRST X (SQLite)
    - Responda apenas com a SQL, sem formatação markdown
    """
    
    response = gemini_model.generate_content(prompt)
    # Remove formatação markdown se houver
    sql = response.text.strip()
    if sql.startswith("```sql"):
        sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql

def gerar_sql_offline(pergunta):
    # SQL offline para casos comuns
    comandos_offline = {
        "clientes": "SELECT * FROM CLI_CLIENTE;",
        "cliente": "SELECT * FROM CLI_CLIENTE;",
        "quantos": "SELECT COUNT(*) FROM CLI_CLIENTE;",
        "count": "SELECT COUNT(*) FROM CLI_CLIENTE;",
        "tabela": "SELECT name FROM sqlite_master WHERE type='table';",
        "maria": "SELECT * FROM CLI_CLIENTE WHERE NOME LIKE '%MARIA%';",
        "todos": "SELECT * FROM CLI_CLIENTE;",
    }
    
    pergunta_lower = pergunta.lower()
    for palavra, sql in comandos_offline.items():
        if palavra in pergunta_lower:
            print("🔧 Usando modo offline")
            return sql
    
    return "SELECT * FROM CLI_CLIENTE LIMIT 5; -- Mostrando primeiros 5 clientes"

def gerar_sql(pergunta):
    global current_api
    
    try:
        if current_api == "openai":
            print("🤖 Usando OpenAI...")
            return gerar_sql_openai(pergunta)
        else:
            print("🧠 Usando Google Gemini...")
            return gerar_sql_gemini(pergunta)
            
    except Exception as e:
        if "quota" in str(e) or "429" in str(e) or "limit" in str(e).lower():
            print(f"⚠️ {current_api} sem cota. Tentando API alternativa...")
            trocar_api()
            try:
                if current_api == "openai":
                    return gerar_sql_openai(pergunta)
                else:
                    return gerar_sql_gemini(pergunta)
            except Exception as e2:
                print(f"⚠️ Ambas APIs falharam. Usando modo offline...")
                return gerar_sql_offline(pergunta)
        else:
            print(f"⚠️ Erro na API: {e}")
            return gerar_sql_offline(pergunta)

while True:
    pergunta = input("Você: ").strip()
    
    if pergunta.lower() == "sair":
        break
    elif pergunta.lower() == "trocar":
        trocar_api()
        continue
    
    try:
        sql = gerar_sql(pergunta)
        print(f"🔍 SQL gerada: {sql}")
        
        # Executar no banco demo
        cur.execute(sql)
        resultados = cur.fetchall()
        
        if resultados:
            print("🤖 Resultados:")
            for i, linha in enumerate(resultados, 1):
                print(f"   {i}. {linha}")
        else:
            print("🤖 Consulta executada com sucesso (sem resultados)")
            
    except Exception as e:
        print(f"⚠️ Erro na consulta: {e}")
        print("💡 Tentando consulta alternativa...")
        try:
            sql_alternativa = gerar_sql_offline(pergunta)
            print(f"🔧 SQL alternativa: {sql_alternativa}")
            cur.execute(sql_alternativa)
            resultados = cur.fetchall()
            if resultados:
                print("🤖 Resultados:")
                for i, linha in enumerate(resultados, 1):
                    print(f"   {i}. {linha}")
        except Exception as e2:
            print(f"⚠️ Erro: {e2}")

conn.close()
print("👋 Até logo!")
