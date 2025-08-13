import os
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

# 📂 Verificar arquivo do banco
db_path = r"C:\Users\Dev Ruan\Desktop\ruan\treinamento\CENTRAL.FDB"

print("🔍 Verificando arquivo CENTRAL.FDB...")

if os.path.exists(db_path):
    size = os.path.getsize(db_path)
    print(f"✅ Arquivo encontrado: {db_path}")
    print(f"📏 Tamanho: {size:,} bytes ({size/1024/1024:.2f} MB)")
else:
    print(f"❌ Arquivo não encontrado: {db_path}")
    print("💡 Verifique se o caminho está correto")

print("\n🔌 Status da Conexão:")
print("❌ Firebird Server não está rodando")
print("💡 Para conectar ao banco você precisa:")
print("   1. Instalar o Firebird Server")
print("   2. Ou usar uma ferramenta como IBExpert/FlameRobin")
print("   3. Ou executar as consultas SQL manualmente")

print("\n💬 Gerador de SQL para CENTRAL.FDB - OpenAI + Gemini")
print(f"🔑 API atual: {current_api}")
print("💡 Digite 'trocar' para alternar entre OpenAI e Gemini")
print("📋 As consultas serão geradas para você executar manualmente")
print("-" * 60)

def gerar_sql_openai(pergunta):
    prompt = f"""
    Você é um assistente SQL especialista em Firebird. Converta a seguinte pergunta em uma consulta SQL otimizada para Firebird:
    
    Pergunta: {pergunta}
    
    Contexto: Banco CENTRAL.FDB com possíveis tabelas como CLI_CLIENTE, PRODUTOS, VENDAS, etc.
    
    Regras importantes:
    - Para listar tabelas: SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0 ORDER BY RDB$RELATION_NAME
    - Para contar registros: SELECT COUNT(*) FROM nome_tabela
    - Para buscar dados: SELECT * FROM nome_tabela WHERE campo LIKE '%valor%'
    - Para verificar estrutura: SELECT RDB$FIELD_NAME, RDB$FIELD_TYPE FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'TABELA'
    - Use FIRST X em vez de LIMIT X
    - Use sintaxe específica do Firebird
    - Retorne SQL pronta para executar
    - Responda apenas com a SQL, sem explicações
    """
    
    resp = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=250,
        temperature=0.1
    )
    return resp.choices[0].message.content.strip()

def gerar_sql_gemini(pergunta):
    prompt = f"""
    Você é um assistente SQL especialista em Firebird. Converta a seguinte pergunta em uma consulta SQL otimizada para Firebird:
    
    Pergunta: {pergunta}
    
    Contexto: Banco CENTRAL.FDB com possíveis tabelas como CLI_CLIENTE, PRODUTOS, VENDAS, etc.
    
    Regras importantes:
    - Para listar tabelas: SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0 ORDER BY RDB$RELATION_NAME
    - Para contar registros: SELECT COUNT(*) FROM nome_tabela
    - Para buscar dados: SELECT * FROM nome_tabela WHERE campo LIKE '%valor%'
    - Para verificar estrutura: SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'TABELA'
    - Use FIRST X em vez de LIMIT X
    - Use sintaxe específica do Firebird
    - Retorne SQL pronta para executar
    - Responda apenas com a SQL, sem formatação markdown
    """
    
    response = gemini_model.generate_content(prompt)
    # Remove formatação markdown se houver
    sql = response.text.strip()
    if sql.startswith("```sql"):
        sql = sql.replace("```sql", "").replace("```", "").strip()
    if sql.startswith("```"):
        sql = sql.replace("```", "").strip()
    return sql

def gerar_sql_offline(pergunta):
    # SQL offline para casos comuns - otimizado para Firebird
    comandos_offline = {
        "tabelas": "SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0 ORDER BY RDB$RELATION_NAME",
        "lista tabelas": "SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0 ORDER BY RDB$RELATION_NAME",
        "clientes": "SELECT FIRST 20 * FROM CLI_CLIENTE",
        "cliente": "SELECT FIRST 20 * FROM CLI_CLIENTE",
        "cli_cliente": "SELECT FIRST 20 * FROM CLI_CLIENTE",
        "quantos clientes": "SELECT COUNT(*) AS TOTAL_CLIENTES FROM CLI_CLIENTE",
        "count": "SELECT COUNT(*) FROM CLI_CLIENTE",
        "campos cli_cliente": "SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'CLI_CLIENTE' ORDER BY RDB$FIELD_POSITION",
        "estrutura": "SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'CLI_CLIENTE' ORDER BY RDB$FIELD_POSITION",
        "procedures": "SELECT RDB$PROCEDURE_NAME FROM RDB$PROCEDURES ORDER BY RDB$PROCEDURE_NAME",
        "triggers": "SELECT RDB$TRIGGER_NAME FROM RDB$TRIGGERS WHERE RDB$SYSTEM_FLAG = 0 ORDER BY RDB$TRIGGER_NAME",
        "generators": "SELECT RDB$GENERATOR_NAME FROM RDB$GENERATORS WHERE RDB$SYSTEM_FLAG = 0 ORDER BY RDB$GENERATOR_NAME",
        "indices": "SELECT RDB$INDEX_NAME FROM RDB$INDICES WHERE RDB$SYSTEM_FLAG = 0 ORDER BY RDB$INDEX_NAME",
    }
    
    pergunta_lower = pergunta.lower()
    for palavra, sql in comandos_offline.items():
        if palavra in pergunta_lower:
            print("🔧 Usando modo offline")
            return sql
    
    # Busca mais inteligente
    if "maria" in pergunta_lower:
        return "SELECT * FROM CLI_CLIENTE WHERE UPPER(NOME) LIKE '%MARIA%'"
    elif "joão" in pergunta_lower or "joao" in pergunta_lower:
        return "SELECT * FROM CLI_CLIENTE WHERE UPPER(NOME) LIKE '%JOÃO%' OR UPPER(NOME) LIKE '%JOAO%'"
    elif "produto" in pergunta_lower:
        return "SELECT FIRST 20 * FROM PRODUTOS"
    elif "venda" in pergunta_lower:
        return "SELECT FIRST 20 * FROM VENDAS"
    
    return "SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0 ORDER BY RDB$RELATION_NAME"

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

# Mostrar comandos úteis
print("💡 Comandos úteis para testar:")
print("   • 'lista as tabelas'")
print("   • 'quantos clientes tem'")
print("   • 'mostra os clientes'")
print("   • 'campos da tabela CLI_CLIENTE'")
print("   • 'tem cliente Maria'")
print("   • 'procedures do banco'")

while True:
    pergunta = input("\nVocê: ").strip()
    
    if pergunta.lower() == "sair":
        break
    elif pergunta.lower() == "trocar":
        trocar_api()
        continue
    elif pergunta.lower() == "ajuda":
        print("💡 Comandos disponíveis:")
        print("   • lista as tabelas")
        print("   • quantos clientes tem")
        print("   • mostra os clientes") 
        print("   • campos da tabela CLI_CLIENTE")
        print("   • tem cliente Maria")
        print("   • procedures do banco")
        print("   • trocar (muda API)")
        print("   • sair")
        continue
    
    try:
        sql = gerar_sql(pergunta)
        print(f"\n🔍 SQL gerada para CENTRAL.FDB:")
        print(f"📋 {sql}")
        print("\n💡 Para executar:")
        print("   1. Abra IBExpert, FlameRobin ou similar")
        print("   2. Conecte ao CENTRAL.FDB")
        print("   3. Execute a SQL acima")
        print("-" * 60)
            
    except Exception as e:
        print(f"⚠️ Erro: {e}")

print("\n👋 Até logo!")
print("💡 Para conectar ao banco, instale o Firebird Server ou use um cliente SQL")
