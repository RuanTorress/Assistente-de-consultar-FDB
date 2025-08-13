import os
import re
import unicodedata
from typing import List, Dict, Optional, Tuple
import fdb
from openai import OpenAI
import google.generativeai as genai

# =========================
# 1. CONFIGURAÇÃO DE CHAVES (IGUAL AO main_central.py QUE FUNCIONA)
# =========================
API_KEYS = {
    "openai": "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",
    "gemini": "AIzaSyDeTIz34pWW760D14Quh9Z_E7YPC4lQdFo"
}

current_api = "openai"

# Configurar APIs (igual ao main_central.py)
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

# =========================
# 2. CONFIGURAÇÃO FIREBIRD (EXATAMENTE IGUAL AO main_central.py)
# =========================
host = "localhost"
port = 4050
database = r"C:\Users\RuanFabio\Desktop\Ruan\banco\treinamento\CENTRAL.FDB"
user = "SYSDBA"
password = "masterkey"

print("🔌 Tentando conectar ao banco CENTRAL.FDB...")

# =========================
# 3. CONEXÃO FIREBIRD (MESMA LÓGICA DO main_central.py)
# =========================
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
    conectado = True
    
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
        conectado = True
        
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
            conectado = True
            
        except Exception as e3:
            print(f"❌ Erro conexão direta: {e3}")
            print("💡 Possíveis soluções:")
            print("   1. Instalar Firebird Server: https://firebirdsql.org/en/downloads/")
            print("   2. Verificar se o arquivo CENTRAL.FDB existe")
            print("   3. Verificar se o Firebird está rodando como serviço")
            print("   4. Tentar executar como administrador")
            conectado = False

# Testar conexão se conseguiu conectar (igual ao main_central.py)
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

# =========================
# 4. CARREGAR METADADOS
# =========================
schema_cache: Dict[str, List[str]] = {}
valores_cache: Dict[str, Dict[str, List[str]]] = {}

def carregar_schema():
    global schema_cache
    if not conectado or not cur:
        print("⚠️ Sem conexão para carregar schema")
        return
    
    try:
        cur.execute("SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0")
        tabelas = cur.fetchall()
        
        for tabela_row in tabelas:
            tabela = tabela_row[0].strip() if tabela_row[0] else None
            if not tabela:
                continue
                
            try:
                cur.execute("""
                    SELECT RDB$FIELD_NAME
                    FROM RDB$RELATION_FIELDS
                    WHERE RDB$RELATION_NAME = ?
                    ORDER BY RDB$FIELD_POSITION
                """, (tabela,))
                campos = [c[0].strip() for c in cur.fetchall() if c[0]]
                schema_cache[tabela] = campos
                print(f"📋 Tabela carregada: {tabela} ({len(campos)} campos)")
            except Exception as e:
                print(f"⚠️ Erro ao carregar campos de {tabela}: {e}")
                
    except Exception as e:
        print(f"⚠️ Erro ao carregar schema: {e}")

def carregar_valores_distintos(tabela: str, campo: str, limite=20):
    if not conectado or not cur:
        return []
    
    if tabela not in valores_cache:
        valores_cache[tabela] = {}
    if campo in valores_cache.get(tabela, {}):
        return valores_cache[tabela][campo]
        
    sql = f"SELECT DISTINCT FIRST {limite} {campo} FROM {tabela} WHERE {campo} IS NOT NULL"
    try:
        cur.execute(sql)
        valores = []
        for row in cur.fetchall():
            v = row[0]
            if isinstance(v, str):
                v = v.strip()
            if v:
                valores.append(str(v))
        valores_cache[tabela][campo] = valores
        return valores
    except Exception as e:
        print(f"⚠️ Erro ao carregar valores de {tabela}.{campo}: {e}")
        return []

# Carregar schema na inicialização
if conectado:
    carregar_schema()

# =========================
# 5. GERAÇÃO DE SUGESTÕES
# =========================
def gerar_sugestoes_basicas() -> List[str]:
    sugestoes = []
    
    # Templates simples por tabela
    for tabela, campos in schema_cache.items():
        nome_tabela_lower = tabela.lower()
        sugestoes.append(f"listar registros da tabela {nome_tabela_lower}")
        sugestoes.append(f"quantos registros tem na tabela {nome_tabela_lower}")
        
        if len(campos) <= 10:
            sugestoes.append(f"quais campos da tabela {nome_tabela_lower}")
        
        # Campos candidatos para busca por nome
        for campo in campos:
            if campo.upper() in ("NOME", "NOME_CLIENTE", "RAZAO_SOCIAL"):
                sugestoes.append(f"registros com nome contendo maria")
                break
        
        # Campos tipo localização
        for campo in campos:
            if campo.upper() in ("CIDADE", "UF", "ESTADO"):
                valores = carregar_valores_distintos(tabela, campo, 5)
                for v in valores[:3]:  # Máximo 3 cidades por tabela
                    v_limpo = v.strip()
                    if v_limpo:
                        sugestoes.append(f"tem {nome_tabela_lower} de {v_limpo.lower()}?")
                        sugestoes.append(f"quantos {nome_tabela_lower} de {v_limpo.lower()}")
                break
    
    # Específicos se existir CLI_CLIENTE
    if "CLI_CLIENTE" in schema_cache:
        sugestoes.extend([
            "tem cliente de goiania?",
            "quantos clientes de sao paulo",
            "listar clientes da cidade rio de janeiro",
            "quais campos da tabela cli_cliente",
            "mostrar 10 clientes",
            "clientes sem email",
            "primeiro cliente",
        ])
    
    # Comandos gerais úteis
    sugestoes.extend([
        "listar todas as tabelas",
        "quantas tabelas tem no banco",
        "procedures do banco",
        "triggers do banco",
    ])
    
    # Remover duplicatas mantendo ordem
    vistos = set()
    final = []
    for s in sugestoes:
        if s not in vistos:
            vistos.add(s)
            final.append(s)
    
    return final[:50]  # Máximo 50 sugestões

SUGESTOES_INICIAIS = gerar_sugestoes_basicas()

# =========================
# 6. PRÉ-PROCESSAMENTO (REGRAS INTELIGENTES)
# =========================
def remover_acentos(txt: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')

def montar_condicao_cidade(nome_cidade: str, campo_cidade="CIDADE") -> str:
    base = remover_acentos(nome_cidade).upper()
    variantes = {base}
    
    # Casos especiais de cidades
    mapeamentos = {
        "GOIANIA": "GOIÂNIA",
        "SAO PAULO": "SÃO PAULO", 
        "BRASILIA": "BRASÍLIA",
        "RIBEIRAO PRETO": "RIBEIRÃO PRETO"
    }
    
    if base in mapeamentos:
        variantes.add(mapeamentos[base])
    
    condicoes = " OR ".join([f"UPPER({campo_cidade}) LIKE '%{v}%'" for v in variantes])
    return f"({condicoes})"

def sql_existe_cliente_cidade(cidade: str) -> str:
    return f"SELECT FIRST 1 * FROM CLI_CLIENTE WHERE {montar_condicao_cidade(cidade)}"

def sql_count_cliente_cidade(cidade: str) -> str:
    return f"SELECT COUNT(*) AS TOTAL FROM CLI_CLIENTE WHERE {montar_condicao_cidade(cidade)}"

def sql_listar_cliente_cidade(cidade: str, limite=50) -> str:
    return f"SELECT FIRST {limite} * FROM CLI_CLIENTE WHERE {montar_condicao_cidade(cidade)}"

REGEX_CIDADE = r"([a-zA-ZãâáêéíóôõúçÀ-Ú\s]+)"

def preprocessar_pergunta(pergunta: str) -> Optional[str]:
    p = pergunta.lower().strip()

    # Clientes por cidade
    padroes_cidade = [
        (rf"^tem\s+cliente(?:s)?\s+de\s+{REGEX_CIDADE}\??$", sql_existe_cliente_cidade),
        (rf"^quantos\s+clientes\s+(?:de|em)\s+{REGEX_CIDADE}\??$", sql_count_cliente_cidade),
        (rf"^listar\s+clientes\s+(?:de|da|do|em)\s+(?:cidade\s+)?{REGEX_CIDADE}\??$", sql_listar_cliente_cidade),
        (rf"^clientes\s+de\s+{REGEX_CIDADE}\??$", sql_listar_cliente_cidade),
    ]
    
    for rgx, func in padroes_cidade:
        m = re.match(rgx, p)
        if m:
            cidade = m.group(1).strip()
            if "CLI_CLIENTE" in schema_cache:
                return func(cidade)

    # Comandos específicos
    comandos_diretos = {
        "listar todas as tabelas": "SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0 ORDER BY RDB$RELATION_NAME",
        "quantas tabelas tem no banco": "SELECT COUNT(*) FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0",
        "procedures do banco": "SELECT RDB$PROCEDURE_NAME FROM RDB$PROCEDURES ORDER BY RDB$PROCEDURE_NAME",
        "triggers do banco": "SELECT RDB$TRIGGER_NAME FROM RDB$TRIGGERS WHERE RDB$SYSTEM_FLAG = 0 ORDER BY RDB$TRIGGER_NAME",
        "primeiro cliente": "SELECT FIRST 1 * FROM CLI_CLIENTE" if "CLI_CLIENTE" in schema_cache else None,
        "clientes sem email": "SELECT FIRST 50 * FROM CLI_CLIENTE WHERE (EMAIL IS NULL OR TRIM(EMAIL) = '')" if "CLI_CLIENTE" in schema_cache else None,
    }
    
    if p in comandos_diretos and comandos_diretos[p]:
        return comandos_diretos[p]

    # Mostrar N registros
    m = re.match(r"^mostrar\s+(\d+)\s+clientes$", p)
    if m and "CLI_CLIENTE" in schema_cache:
        n = int(m.group(1))
        return f"SELECT FIRST {n} * FROM CLI_CLIENTE"

    # Quais campos da tabela
    m = re.match(r"^quais\s+campos\s+da\s+tabela\s+([a-z0-9_]+)$", p)
    if m:
        tabela = m.group(1).upper()
        if tabela in schema_cache:
            return f"SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = '{tabela}' ORDER BY RDB$FIELD_POSITION"

    return None

# =========================
# 7. GERAÇÃO SQL VIA IA (USANDO MESMOS PROMPTS DO main_central.py)
# =========================
def gerar_sql_openai(pergunta: str) -> str:
    prompt = f"""
    Você é um assistente SQL para banco Firebird. Converta a seguinte pergunta em uma consulta SQL útil para Firebird:

    Pergunta: {pergunta}

    Tabelas e campos disponíveis:
    {chr(10).join([f"{t}: {', '.join(campos)}" for t, campos in schema_cache.items()])}

    Regras importantes:
    - Use os nomes reais dos campos conforme listado acima.
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

def gerar_sql_gemini(pergunta: str) -> str:
    prompt = f"""
    Você é um assistente SQL para banco Firebird. Converta a seguinte pergunta em uma consulta SQL útil para Firebird:
    
    Pergunta: {pergunta}
    
    Tabelas disponíveis: {', '.join(schema_cache.keys()) if schema_cache else 'CLI_CLIENTE'}
    
    Regras importantes:
    - Para verificar tabelas use: SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0
    - Para contar registros use: SELECT COUNT(*) FROM nome_tabela
    - Para buscar dados use: SELECT * FROM nome_tabela WHERE campo LIKE '%valor%'
    - Para clientes de cidade use: SELECT * FROM CLI_CLIENTE WHERE UPPER(CIDADE) LIKE '%CIDADE%'
    - Use FIRST X em vez de LIMIT X
    - Use sintaxe específica do Firebird
    - Responda apenas com a SQL, sem formatação markdown
    """
    
    response = gemini_model.generate_content(prompt)
    sql = response.text.strip()
    if sql.startswith("```sql"):
        sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql

def gerar_sql_offline(pergunta: str) -> str:
    # SQL offline para casos comuns (igual ao main_central.py)
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

def gerar_sql(pergunta: str) -> str:
    # 1. Primeiro tenta regras pré-processadas
    regra = preprocessar_pergunta(pergunta)
    if regra:
        print("🔧 (Regra aplicada)")
        return regra
    
    # 2. Depois tenta IA
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

# =========================
# 8. EXECUÇÃO DE SQL (IGUAL AO main_central.py)
# =========================
def executar_sql(sql: str):
    if not (conn and cur):
        return False, []
    
    try:
        cur.execute(sql)
        
        # Verificar se é uma consulta SELECT
        if sql.strip().upper().startswith('SELECT'):
            resultados = cur.fetchall()
            if resultados:
                # Limpar strings do Firebird (remove espaços extras)
                resultados_limpos = []
                for linha in resultados:
                    linha_limpa = []
                    for campo in linha:
                        if isinstance(campo, str):
                            linha_limpa.append(campo.strip())
                        else:
                            linha_limpa.append(campo)
                    resultados_limpos.append(tuple(linha_limpa))
                return True, resultados_limpos
            else:
                return True, []
        else:
            # Para comandos INSERT, UPDATE, DELETE
            conn.commit()
            return True, []
            
    except Exception as e:
        print(f"⚠️ Erro na consulta SQL: {e}")
        return False, []

# =========================
# 9. BOT (MODO SUGESTÕES)
# =========================
def modo_bot():
    print("\n🤖 MODO BOT (Sugeridor)")
    print("Digite número da sugestão, texto livre, 'voltar' para menu ou 'trocar' para alternar IA.")
    
    while True:
        print("\n" + "="*50)
        print("📋 Sugestões de perguntas:")
        for i, sug in enumerate(SUGESTOES_INICIAIS[:15], 1):
            print(f"  {i:2d}. {sug}")
        
        if len(SUGESTOES_INICIAIS) > 15:
            print(f"     ... e mais {len(SUGESTOES_INICIAIS) - 15} sugestões")
        
        print("="*50)
        entrada = input("Sua escolha (número ou texto): ").strip()
        
        if entrada.lower() in ("voltar", "menu"):
            return
        if entrada.lower() == "trocar":
            trocar_api()
            continue
        if entrada.lower() == "sair":
            print("👋 Encerrando...")
            exit(0)
            
        # Verificar se é um número
        if entrada.isdigit():
            idx = int(entrada) - 1
            if 0 <= idx < len(SUGESTOES_INICIAIS):
                pergunta = SUGESTOES_INICIAIS[idx]
                print(f"📝 Pergunta selecionada: {pergunta}")
            else:
                print("⚠️ Número inválido")
                continue
        else:
            pergunta = entrada

        # Gerar e executar SQL
        sql = gerar_sql(pergunta)
        print(f"🔍 SQL gerada: {sql}")
        
        if conectado:
            sucesso, rows = executar_sql(sql)
            if sucesso and rows:
                print(f"📊 {len(rows)} linha(s) encontrada(s) (mostrando até 20):")
                for i, linha in enumerate(rows[:20], 1):
                    print(f"   {i:2d}. {linha}")
                
                if len(rows) > 20:
                    print(f"   ... e mais {len(rows) - 20} registros")
            elif sucesso:
                print("✅ Comando executado com sucesso (sem resultados)")
        else:
            print("📋 Sem conexão. Execute esta SQL manualmente se desejar.")

# =========================
# 10. CHAT (MODO LIVRE) - IGUAL AO main_central.py
# =========================
def modo_chat():
    print("\n💬 MODO CHAT (Livre)")
    print("Pergunte algo sobre o banco. Comandos especiais: 'trocar', 'voltar', 'sair'")
    
    while True:
        pergunta = input("Você: ").strip()
        
        if pergunta.lower() in ("voltar", "menu"):
            return
        if pergunta.lower() == "sair":
            print("👋 Encerrando chat.")
            exit(0)
        if pergunta.lower() == "trocar":
            trocar_api()
            continue
            
        sql = gerar_sql(pergunta)
        print(f"🔍 SQL gerada: {sql}")
        
        if conectado:
            sucesso, rows = executar_sql(sql)
            if sucesso and rows:
                print(f"🤖 Resultados do CENTRAL.FDB:")
                for i, linha in enumerate(rows[:20], 1):
                    print(f"   {i:2d}. {linha}")
                
                if len(rows) > 20:
                    print(f"   ... e mais {len(rows) - 20} registros")
            elif sucesso:
                print("🤖 Comando executado com sucesso")
        else:
            print("❌ Sem conexão com o banco. Execute esta SQL manualmente:")
            print(f"📋 {sql}")

# ...existing code...

def gerar_sinonimos_automaticos(schema_cache):
    sinonimos = {}
    for tabela, campos in schema_cache.items():
        sinonimos[tabela] = {}
        for campo in campos:
            campo_lower = campo.lower()
            # Adiciona o próprio nome do campo como sinônimo
            sinonimos[tabela][campo_lower] = campo
            # Adiciona variações comuns
            if "nome" in campo_lower:
                sinonimos[tabela]["nome"] = campo
                sinonimos[tabela]["nome do cliente"] = campo
            if "email" in campo_lower:
                sinonimos[tabela]["email"] = campo
            if "cidade" in campo_lower:
                sinonimos[tabela]["cidade"] = campo
            # Adicione outras regras conforme necessário
    return sinonimos

SINONIMOS_CAMPOS = gerar_sinonimos_automaticos(schema_cache)
# ...existing code...
def campo_real(tabela: str, termo_usuario: str) -> Optional[str]:
    tabela = tabela.upper()
    termo = termo_usuario.lower()
    if tabela in SINONIMOS_CAMPOS:
        for sinonimo, campo in SINONIMOS_CAMPOS[tabela].items():
            if termo in sinonimo:
                return campo
    return None            

# =========================
# 11. MENU PRINCIPAL
# =========================
def menu_principal():
    print("\n" + "="*60)
    print("🚀 ASSISTENTE FIREBIRD INTELIGENTE")
    print(f"🔌 Conexão: {'✅ CONECTADO' if conectado else '❌ SEM CONEXÃO'}")
    print(f"🧠 IA atual: {current_api.upper()}")
    print(f"📊 Tabelas carregadas: {len(schema_cache)}")
    print("="*60)
    print("1. 🤖 Bot (Sugeridor de perguntas)")
    print("2. 💬 Chat (Conversa livre)")
    print("3. 🔄 Trocar IA (OpenAI ↔ Gemini)")
    print("4. 📋 Recarregar schema do banco")
    print("5. 🔍 Mostrar tabelas carregadas")
    print("6. 👋 Sair")
    print("="*60)

    while True:
        op = input("Escolha uma opção: ").strip()
        
        if op == "1":
            modo_bot()
            break
        elif op == "2":
            modo_chat()
            break
        elif op == "3":
            trocar_api()
        elif op == "4":
            if conectado:
                carregar_schema()
                global SUGESTOES_INICIAIS
                SUGESTOES_INICIAIS = gerar_sugestoes_basicas()
                print("✅ Schema recarregado e sugestões atualizadas.")
            else:
                print("❌ Sem conexão para recarregar schema.")
        elif op == "5":
            if schema_cache:
                print(f"\n📋 Tabelas carregadas ({len(schema_cache)}):")
                for tabela, campos in schema_cache.items():
                    print(f"   • {tabela} ({len(campos)} campos)")
            else:
                print("❌ Nenhuma tabela carregada.")
        elif op == "6":
            print("👋 Até logo!")
            if conn:
                cur.close()
                conn.close()
                print("🔌 Conexão encerrada")
            exit(0)
        else:
            print("⚠️ Opção inválida. Escolha 1-6.")

# =========================
# 12. MAIN
# =========================
def main():
    print("🔥 ASSISTENTE FIREBIRD INTELIGENTE")
    print("Bot + Chat com IA híbrida (OpenAI/Gemini) + Regras inteligentes")
    
    if not conectado:
        print("⚠️ Operando sem execução real (somente geração de SQL)")
        print("💡 Verifique se o Firebird está rodando e o caminho do banco está correto")
    
    while True:
        menu_principal()

if __name__ == "__main__":
    main()