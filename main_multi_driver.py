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

# 📂 Configuração do Firebird
database = r"C:\Users\Dev Ruan\Desktop\ruan\treinamento\CENTRAL.FDB"
user = "SYSDBA"
password = "masterkey"

print("🔌 Testando drivers Firebird disponíveis...")

# Testar múltiplos drivers
drivers_testados = []
conn = None
cur = None
driver_usado = None

# 1. Tentar fdb
try:
    import fdb
    print("✅ Driver fdb encontrado")
    
    # Testar conexões com fdb
    configs_fdb = [
        {"host": "localhost", "port": 4050, "database": database},
        {"host": "localhost", "port": 3050, "database": database},
        {"database": database},  # Embedded
        {"dsn": f"localhost/4050:{database}"},
        {"dsn": f"localhost/3050:{database}"},
    ]
    
    for i, config in enumerate(configs_fdb, 1):
        try:
            print(f"🔄 Testando fdb config {i}: {config}")
            conn = fdb.connect(
                user=user,
                password=password,
                charset='UTF8',
                **config
            )
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM RDB$DATABASE")
            resultado = cur.fetchone()
            print(f"✅ SUCESSO com fdb! Config: {config}")
            driver_usado = "fdb"
            drivers_testados.append(("fdb", config, "SUCESSO"))
            break
        except Exception as e:
            print(f"❌ fdb config {i} falhou: {e}")
            drivers_testados.append(("fdb", config, f"ERRO: {e}"))
            if conn:
                try:
                    conn.close()
                except:
                    pass
                conn = None
                cur = None
                
except ImportError:
    print("❌ Driver fdb não encontrado")
    drivers_testados.append(("fdb", None, "Não instalado"))

# 2. Se fdb não funcionou, tentar firebirdsql
if not conn:
    try:
        import firebirdsql
        print("✅ Driver firebirdsql encontrado")
        
        configs_firebirdsql = [
            {"host": "localhost", "port": 4050, "database": database},
            {"host": "localhost", "port": 3050, "database": database},
            {"database": database},  # Local
        ]
        
        for i, config in enumerate(configs_firebirdsql, 1):
            try:
                print(f"🔄 Testando firebirdsql config {i}: {config}")
                conn = firebirdsql.connect(
                    user=user,
                    password=password,
                    charset='UTF8',
                    **config
                )
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM RDB$DATABASE")
                resultado = cur.fetchone()
                print(f"✅ SUCESSO com firebirdsql! Config: {config}")
                driver_usado = "firebirdsql"
                drivers_testados.append(("firebirdsql", config, "SUCESSO"))
                break
            except Exception as e:
                print(f"❌ firebirdsql config {i} falhou: {e}")
                drivers_testados.append(("firebirdsql", config, f"ERRO: {e}"))
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
                    conn = None
                    cur = None
                    
    except ImportError:
        print("❌ Driver firebirdsql não encontrado")
        drivers_testados.append(("firebirdsql", None, "Não instalado"))

# 3. Se ainda não funcionou, tentar firebird.driver
if not conn:
    try:
        import firebird.driver as fb_driver
        print("✅ Driver firebird.driver encontrado")
        
        configs_fb_driver = [
            {"database": database},  # Só teste local
        ]
        
        for i, config in enumerate(configs_fb_driver, 1):
            try:
                print(f"🔄 Testando firebird.driver config {i}: {config}")
                conn = fb_driver.connect(
                    user=user,
                    password=password,
                    charset='UTF8',
                    **config
                )
                cur = conn.cursor()
                cur.execute("SELECT 1 FROM RDB$DATABASE")
                resultado = cur.fetchone()
                print(f"✅ SUCESSO com firebird.driver! Config: {config}")
                driver_usado = "firebird.driver"
                drivers_testados.append(("firebird.driver", config, "SUCESSO"))
                break
            except Exception as e:
                print(f"❌ firebird.driver config {i} falhou: {e}")
                drivers_testados.append(("firebird.driver", config, f"ERRO: {e}"))
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
                    conn = None
                    cur = None
                    
    except ImportError:
        print("❌ Driver firebird.driver não encontrado")
        drivers_testados.append(("firebird.driver", None, "Não instalado"))

# Mostrar resumo dos testes
print("\n📊 RESUMO DOS TESTES:")
print("=" * 60)
for driver, config, status in drivers_testados:
    print(f"• {driver}: {status}")
    if config:
        print(f"  Config: {config}")

# Testar conexão se conseguiu conectar
if conn and cur:
    try:
        print(f"\n🎉 CONECTADO COM SUCESSO usando: {driver_usado}")
        
        # Teste básico
        cur.execute("SELECT 1 FROM RDB$DATABASE")
        resultado = cur.fetchone()
        print(f"🎯 Teste de conexão: {resultado}")
        
        # Listar tabelas disponíveis
        cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0")
        tabelas = cur.fetchall()
        print(f"📊 Tabelas encontradas: {len(tabelas)}")
        for tabela in tabelas[:10]:  # Mostrar primeiras 10
            nome_tabela = tabela[0].strip() if tabela[0] else "N/A"
            print(f"   • {nome_tabela}")
        
        if len(tabelas) > 10:
            print(f"   ... e mais {len(tabelas) - 10} tabelas")
        
    except Exception as e:
        print(f"⚠️ Erro no teste: {e}")
else:
    print("\n❌ NENHUMA CONEXÃO FUNCIONOU")
    print("\n💡 POSSÍVEIS SOLUÇÕES:")
    print("1. Instalar Firebird Server:")
    print("   • Download: https://firebirdsql.org/en/downloads/")
    print("   • Instalar Firebird 5.0 para Windows")
    print("   • Iniciar como serviço")
    print("\n2. Verificar se o arquivo existe:")
    if os.path.exists(database):
        size = os.path.getsize(database)
        print(f"   ✅ Arquivo existe: {size:,} bytes")
    else:
        print(f"   ❌ Arquivo não encontrado: {database}")
    print("\n3. Executar como Administrador")
    print("4. Verificar se há Firebird já instalado em C:\\Program Files\\")

print(f"\n💬 Chat com CENTRAL.FDB - OpenAI + Gemini")
if conn:
    print("🔌 MODO: Conectado ao banco real")
else:
    print("📋 MODO: Gerador de SQL (sem conexão)")
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
        "tabelas": "SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0 ORDER BY RDB$RELATION_NAME",
        "clientes": "SELECT FIRST 20 * FROM CLI_CLIENTE",
        "cliente": "SELECT FIRST 20 * FROM CLI_CLIENTE",
        "count": "SELECT COUNT(*) FROM CLI_CLIENTE",
        "quantos": "SELECT COUNT(*) FROM CLI_CLIENTE",
        "campos": "SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'CLI_CLIENTE' ORDER BY RDB$FIELD_POSITION",
        "procedures": "SELECT RDB$PROCEDURE_NAME FROM RDB$PROCEDURES ORDER BY RDB$PROCEDURE_NAME",
        "triggers": "SELECT RDB$TRIGGER_NAME FROM RDB$TRIGGERS WHERE RDB$SYSTEM_FLAG = 0 ORDER BY RDB$TRIGGER_NAME",
    }
    
    pergunta_lower = pergunta.lower()
    for palavra, sql in comandos_offline.items():
        if palavra in pergunta_lower:
            print("🔧 Usando modo offline")
            return sql
    
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

while True:
    pergunta = input("\nVocê: ").strip()
    
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
            print("📋 Execute esta SQL em seu cliente Firebird:")
            print(f"   {sql}")
            
    except Exception as e:
        print(f"⚠️ Erro: {e}")

if conn:
    cur.close()
    conn.close()
    print("🔌 Conexão com CENTRAL.FDB encerrada")

print("👋 Até logo!")
