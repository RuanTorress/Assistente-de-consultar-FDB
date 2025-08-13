import os
import fdb
from openai import OpenAI

# 🔑 Configurar sua API key da OpenAI
os.environ["OPENAI_API_KEY"] = "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"
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
        print("💡 Instale o Firebird Client Library")
        exit(1)

print("💬 Chat com Firebird (digite 'sair' para encerrar)")

def gerar_sql(pergunta):
    prompt = f"""
    Você é um assistente SQL para banco Firebird. Converta a seguinte pergunta em uma consulta SQL válida:
    Pergunta: {pergunta}
    Responda apenas com a SQL, sem explicações.
    """
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.1
    )
    return resp.choices[0].message.content.strip()

while True:
    pergunta = input("Você: ").strip()
    if pergunta.lower() == "sair":
        break
    try:
        sql = gerar_sql(pergunta)
        print(f"🔍 SQL gerada: {sql}")
        
        cur.execute(sql)
        if cur.description:
            for linha in cur.fetchall():
                print("🤖", linha)
        else:
            conn.commit()
            print("🤖 OK")
    except Exception as e:
        print("⚠️ Erro:", e)

cur.close()
conn.close()
