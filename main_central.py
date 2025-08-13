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
database = r"C:\Users\RuanFabio\Desktop\Ruan\banco\treinamento\CENTRAL.FDB"
user = "SYSDBA"
password = "masterkey"

print("🔌 Tentando conectar ao banco CENTRAL.FDB...")

# 🔌 Conexão ao banco real
conn = None
cur = None

try:
    # Primeira tentativa: conexão TCP/IP
    print(f"📡 Tentando TCP/IP em {host}:{port}")
    conn = fdb.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        charset='UTF8'
    )
    cur = conn.cursor()
    print("✅ Conectado ao CENTRAL.FDB via TCP/IP!")
    print(f"📡 Host: {host}:{port}")
    print(f"🗄️ Banco: {database}")
    
except Exception as e1:
    print(f"❌ Erro TCP/IP: {e1}")
    
    try:
        # Segunda tentativa: conexão local usando DSN
        print("🔄 Tentando conexão local com DSN...")
        dsn = f"{host}/{port}:{database}"
        conn = fdb.connect(
            dsn=dsn,
            user=user,
            password=password,
            charset='UTF8'
        )
        cur = conn.cursor()
        print("✅ Conectado ao CENTRAL.FDB via DSN!")
        
    except Exception as e2:
        print(f"❌ Erro DSN: {e2}")
        
        try:
            # Terceira tentativa: conexão direta ao arquivo (embedded)
            print("🔄 Tentando conexão direta ao arquivo...")
            conn = fdb.connect(
                database=database,
                user=user,
                password=password,
                charset='UTF8'
            )
            cur = conn.cursor()
            print("✅ Conectado ao CENTRAL.FDB diretamente!")
            
        except Exception as e3:
            print(f"❌ Erro conexão direta: {e3}")
            print("💡 Possíveis soluções:")
            print("   1. Instalar Firebird Server: https://firebirdsql.org/en/downloads/")
            print("   2. Verificar se o arquivo CENTRAL.FDB existe")
            print("   3. Verificar se o Firebird está rodando como serviço")
            print("   4. Tentar executar como administrador")

# Testar conexão se conseguiu conectar
if conn and cur:
    try:
        # Teste básico
        cur.execute("SELECT 1 FROM RDB$DATABASE")
        resultado = cur.fetchone()
        print(f"🎯 Teste de conexão: {resultado}")
        
        # Listar tabelas disponíveis
        cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0")
        tabelas = cur.fetchall()
        print(f"📊 Tabelas encontradas: {len(tabelas)}")
        for tabela in tabelas[:5]:  # Mostrar primeiras 5
            nome_tabela = tabela[0].strip() if tabela[0] else "N/A"
            print(f"   • {nome_tabela}")
        
    except Exception as e:
        print(f"⚠️ Erro no teste: {e}")

print("💬 Chat com CENTRAL.FDB - OpenAI + Gemini (digite 'sair' para encerrar)")
print(f"🔑 API atual: {current_api}")
print("💡 Digite 'trocar' para alternar entre OpenAI e Gemini")

def gerar_sql_openai(pergunta):
    prompt = f"""
    Você é um assistente SQL para banco Firebird. Converta a seguinte pergunta em uma consulta SQL útil para Firebird:
    
    Pergunta: {pergunta}
    
    Regras importantes:
    - Para verificar tabelas use: SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0
    - Para contar registros use: SELECT COUNT(*) FROM nome_tabela
    - Para buscar dados use: SELECT * FROM nome_tabela WHERE campo LIKE '%valor%'
    - Use FIRST X em vez de LIMIT X
    - Use sintaxe específica do Firebird
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
    Você é um assistente SQL para banco Firebird. Converta a seguinte pergunta em uma consulta SQL útil para Firebird:
    
    Pergunta: {pergunta}
    
    Regras importantes:
    - Para verificar tabelas use: SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0
    - Para contar registros use: SELECT COUNT(*) FROM nome_tabela
    - Para buscar dados use: SELECT * FROM nome_tabela WHERE campo LIKE '%valor%'
    - Use FIRST X em vez de LIMIT X
    - Use sintaxe específica do Firebird
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
        "tabelas": "SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0",
        "clientes": "SELECT * FROM CLI_CLIENTE",
        "cliente": "SELECT * FROM CLI_CLIENTE",
        "count": "SELECT COUNT(*) FROM CLI_CLIENTE",
        "quantos": "SELECT COUNT(*) FROM CLI_CLIENTE",
        "campos": "SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'CLI_CLIENTE'",
        "procedures": "SELECT RDB$PROCEDURE_NAME FROM RDB$PROCEDURES",
        "triggers": "SELECT RDB$TRIGGER_NAME FROM RDB$TRIGGERS WHERE RDB$SYSTEM_FLAG = 0",
    }
    
    pergunta_lower = pergunta.lower()
    for palavra, sql in comandos_offline.items():
        if palavra in pergunta_lower:
            print("🔧 Usando modo offline")
            return sql
    
    return "SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0"

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
            try:
                cur.execute(sql)
                
                # Verificar se é uma consulta SELECT
                if sql.strip().upper().startswith('SELECT'):
                    resultados = cur.fetchall()
                    if resultados:
                        print("🤖 Resultados do CENTRAL.FDB:")
                        for i, linha in enumerate(resultados[:20], 1):  # Máximo 20 linhas
                            # Limpar strings do Firebird (remove espaços extras)
                            linha_limpa = []
                            for campo in linha:
                                if isinstance(campo, str):
                                    linha_limpa.append(campo.strip())
                                else:
                                    linha_limpa.append(campo)
                            print(f"   {i}. {tuple(linha_limpa)}")
                        
                        if len(resultados) > 20:
                            print(f"   ... e mais {len(resultados) - 20} registros")
                    else:
                        print("🤖 Consulta executada - nenhum resultado encontrado")
                else:
                    # Para comandos INSERT, UPDATE, DELETE
                    conn.commit()
                    print("🤖 Comando executado com sucesso no CENTRAL.FDB")
                    
            except Exception as e_sql:
                print(f"⚠️ Erro na consulta SQL: {e_sql}")
                
        else:
            print("❌ Sem conexão com o banco. Execute esta SQL manualmente:")
            print(f"📋 {sql}")
            
    except Exception as e:
        print(f"⚠️ Erro: {e}")

if conn:
    cur.close()
    conn.close()
    print("🔌 Conexão com CENTRAL.FDB encerrada")

print("👋 Até logo!")
