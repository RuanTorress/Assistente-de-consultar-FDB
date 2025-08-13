import os
import fdb
from openai import OpenAI

# 🔑 Configurar múltiplas APIs
API_KEYS = {
    "openai_1": "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",
    "openai_2": "SUA_SEGUNDA_CHAVE_AQUI",  # Substitua pela segunda chave
}

current_api = "openai_1"

def trocar_api():
    global current_api
    if current_api == "openai_1":
        current_api = "openai_2"
        print("🔄 Trocando para API 2...")
    else:
        current_api = "openai_1"
        print("🔄 Trocando para API 1...")
    
    os.environ["OPENAI_API_KEY"] = API_KEYS[current_api]
    return OpenAI()

# Inicializar com primeira API
os.environ["OPENAI_API_KEY"] = API_KEYS[current_api]
client = OpenAI()

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

print("💬 Chat com Firebird (digite 'sair' para encerrar)")
print(f"🔑 API atual: {current_api}")
print("💡 Digite 'trocar' para mudar de API")

def gerar_sql(pergunta):
    global client
    
    for tentativa in range(2):  # Tenta com 2 APIs
        try:
            prompt = f"""
            Você é um assistente SQL para banco Firebird. Converta a seguinte pergunta em uma consulta SQL válida para Firebird:
            Pergunta: {pergunta}
            
            Regras:
            - Use sintaxe específica do Firebird
            - Use FIRST X em vez de LIMIT X
            - Responda apenas com a SQL, sem explicações
            """
            
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            return resp.choices[0].message.content.strip()
            
        except Exception as e:
            if "quota" in str(e) or "429" in str(e):
                print(f"⚠️ API {current_api} sem cota. Tentando próxima...")
                client = trocar_api()
            else:
                print(f"⚠️ Erro na API: {e}")
                break
    
    # Se todas as APIs falharam, usar comando offline
    return gerar_sql_offline(pergunta)

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

while True:
    pergunta = input("Você: ").strip()
    
    if pergunta.lower() == "sair":
        break
    elif pergunta.lower() == "trocar":
        client = trocar_api()
        print(f"🔑 API atual: {current_api}")
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
