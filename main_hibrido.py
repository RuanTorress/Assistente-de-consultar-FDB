import os
import fdb
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

# 📂 Configuração do Firebird
host = "localhost"
port = 4050
db_path = r"C:\Users\Dev Ruan\Desktop\ruan\treinamento\CENTRAL.FDB"
user = "SYSDBA"
password = "masterkey"

# 🔌 Conexão
try:
    # Conecta via TCP/IP na porta 4050
    dsn = f"{host}/{port}:{db_path}"
    conn = fdb.connect(
        dsn=dsn,
        user=user,
        password=password,
        charset="UTF8"
    )
    cur = conn.cursor()
    print("✅ Conectado ao banco Firebird com sucesso!")
    print(f"📡 Host: {host}:{port}")
    print(f"🗄️ Banco: {db_path}")
except Exception as e:
    print(f"❌ Erro ao conectar ao banco: {e}")
    print("💡 Verifique se o Firebird está rodando na porta 4050")
    # Tentativa alternativa com conexão local
    try:
        print("🔄 Tentando conexão local...")
        conn = fdb.connect(
            database=db_path,
            user=user,
            password=password,
            charset="UTF8"
        )
        cur = conn.cursor()
        print("✅ Conectado ao banco Firebird localmente!")
    except Exception as e2:
        print(f"❌ Erro na conexão local também: {e2}")
        print("💡 Usando modo offline...")
        conn = None
        cur = None

print("💬 Chat com Firebird - OpenAI + Gemini (digite 'sair' para encerrar)")
print(f"🔑 API atual: {current_api}")
print("💡 Digite 'trocar' para alternar entre OpenAI e Gemini")

def gerar_sql_openai(pergunta):
    prompt = f"""
    Você é um assistente SQL para banco Firebird. Converta a seguinte pergunta em uma consulta SQL útil e completa para Firebird:
    
    Pergunta: {pergunta}
    
    Regras importantes:
    - Se perguntar sobre "TEM TABELA X", responda: SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$RELATION_NAME = 'X' AND RDB$SYSTEM_FLAG = 0
    - Se perguntar sobre "TEM CLIENTE X", responda: SELECT * FROM CLI_CLIENTE WHERE NOME LIKE '%X%'
    - Use FIRST X em vez de LIMIT X
    - Use sintaxe específica do Firebird
    - Retorne consultas que mostrem dados úteis, não apenas 1 ou 0
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
    Você é um assistente SQL para banco Firebird. Converta a seguinte pergunta em uma consulta SQL útil e completa para Firebird:
    
    Pergunta: {pergunta}
    
    Regras importantes:
    - Se perguntar sobre "TEM TABELA X", responda: SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$RELATION_NAME = 'X' AND RDB$SYSTEM_FLAG = 0
    - Se perguntar sobre "TEM CLIENTE X", responda: SELECT * FROM CLI_CLIENTE WHERE NOME LIKE '%X%'
    - Use FIRST X em vez de LIMIT X
    - Use sintaxe específica do Firebird
    - Retorne consultas que mostrem dados úteis, não apenas 1 ou 0
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
        "tabelas": "SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0;",
        "campos": "SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'CLI_CLIENTE';",
        "count": "SELECT COUNT(*) FROM CLI_CLIENTE;",
        "primeiro": "SELECT FIRST 1 * FROM CLI_CLIENTE;",
        "10": "SELECT FIRST 10 * FROM CLI_CLIENTE;",
    }
    
    pergunta_lower = pergunta.lower()
    for palavra, sql in comandos_offline.items():
        if palavra in pergunta_lower:
            print("🔧 Usando modo offline")
            return sql
    
    return "SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0; -- Listando tabelas"

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
        
        if conn and cur:
            cur.execute(sql)
            if cur.description:
                for linha in cur.fetchall():
                    print("🤖", linha)
            else:
                conn.commit()
                print("🤖 OK")
        else:
            print("📋 Execute esta SQL no seu cliente Firebird")
            
    except Exception as e:
        print("⚠️ Erro:", e)

if conn:
    cur.close()
    conn.close()

print("👋 Até logo!")
