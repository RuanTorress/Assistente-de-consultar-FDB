import os
import re
import unicodedata
from typing import List, Dict, Optional, Tuple
import fdb
from openai import OpenAI
import google.generativeai as genai
import json

# =========================
# 1. CONFIGURAÇÃO DE CHAVES (🔧 CORRIGIDO - IGUAIS AO main_central.py)
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
try:
    openai_client = OpenAI()
    print("✅ OpenAI configurada")
except Exception as e:
    openai_client = None
    print(f"❌ Erro OpenAI: {e}")

try:
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Gemini configurada")
except Exception as e:
    gemini_model = None
    print(f"❌ Erro Gemini: {e}")

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
conectado = False

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

# Testar conexão se conseguiu conectar
if conn and cur and conectado:
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
# 4. DECLARAR VARIÁVEIS GLOBAIS
# =========================
schema_cache: Dict[str, List[str]] = {}
foreign_keys: List[Dict] = []
valores_cache: Dict[str, Dict[str, List[str]]] = {}
SUGESTOES_INICIAIS: List[str] = []


historico_perguntas = {}
respostas_aprovadas = {}

CONHECIMENTO_PATH = "conhecimento_local.json"

def salvar_conhecimento():
    """Salva o histórico de perguntas em arquivo local"""
    try:
        with open(CONHECIMENTO_PATH, "w", encoding="utf-8") as f:
            json.dump(historico_perguntas, f, ensure_ascii=False, indent=2)
        print("💾 Conhecimento salvo.")
    except Exception as e:
        print(f"⚠️ Erro ao salvar conhecimento: {e}")

def carregar_conhecimento():
    """Carrega o histórico de perguntas do arquivo local"""
    global historico_perguntas
    try:
        with open(CONHECIMENTO_PATH, "r", encoding="utf-8") as f:
            historico_perguntas.update(json.load(f))
        print("📚 Conhecimento carregado.")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"⚠️ Erro ao carregar conhecimento: {e}")

def aprender_resposta(pergunta, sql, aprovada_pelo_usuario):
    if aprovada_pelo_usuario:
        historico_perguntas[pergunta.lower()] = sql
        salvar_conhecimento()

def buscar_resposta_aprendida(pergunta):
    return historico_perguntas.get(pergunta.lower())

# Carregar conhecimento ao iniciar
carregar_conhecimento()



# =========================
# 5. CARREGAR METADADOS E RELACIONAMENTOS
# =========================
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

def carregar_foreign_keys():
    """🔗 Carrega relacionamentos entre tabelas"""
    global foreign_keys
    foreign_keys = []
    if not conectado or not cur:
        print("⚠️ Sem conexão para carregar foreign keys")
        return
    
    sql_fk = """
    SELECT 
        rc.RDB$CONSTRAINT_NAME AS constraint_name,
        rc.RDB$RELATION_NAME AS tabela_origem,
        seg.RDB$FIELD_NAME AS campo_origem,
        relc.RDB$RELATION_NAME AS tabela_destino,
        segf.RDB$FIELD_NAME AS campo_destino
    FROM RDB$RELATION_CONSTRAINTS rc
    JOIN RDB$INDEX_SEGMENTS seg ON rc.RDB$INDEX_NAME = seg.RDB$INDEX_NAME
    JOIN RDB$REF_CONSTRAINTS ref ON rc.RDB$CONSTRAINT_NAME = ref.RDB$CONSTRAINT_NAME
    JOIN RDB$RELATION_CONSTRAINTS relc ON ref.RDB$CONST_NAME_UQ = relc.RDB$CONSTRAINT_NAME
    JOIN RDB$INDEX_SEGMENTS segf ON relc.RDB$INDEX_NAME = segf.RDB$INDEX_NAME
    WHERE rc.RDB$CONSTRAINT_TYPE = 'FOREIGN KEY'
    """
    
    try:
        cur.execute(sql_fk)
        for row in cur.fetchall():
            fk = {
                "constraint": row[0].strip() if row[0] else "",
                "from_table": row[1].strip() if row[1] else "",
                "from_field": row[2].strip() if row[2] else "",
                "to_table": row[3].strip() if row[3] else "",
                "to_field": row[4].strip() if row[4] else ""
            }
            if all(fk.values()):
                foreign_keys.append(fk)
        
        print(f"🔗 {len(foreign_keys)} relacionamentos carregados")
        if foreign_keys:
            print("   Relacionamentos encontrados:")
            for fk in foreign_keys[:3]:
                print(f"     • {fk['from_table']}.{fk['from_field']} → {fk['to_table']}.{fk['to_field']}")
            if len(foreign_keys) > 3:
                print(f"     ... e mais {len(foreign_keys) - 3}")
                
    except Exception as e:
        print(f"⚠️ Erro ao carregar foreign keys: {e}")

def formatar_relacionamentos() -> str:
    """🗺️ Formata relacionamentos para o prompt da IA"""
    if not foreign_keys:
        return "Nenhum relacionamento detectado."
    
    linhas = []
    for fk in foreign_keys:
        linhas.append(f"{fk['from_table']}.{fk['from_field']} → {fk['to_table']}.{fk['to_field']}")
    
    return "\n".join(linhas)

def formatar_schema_detalhado() -> str:
    """📋 Formata schema completo para o prompt da IA"""
    if not schema_cache:
        return "Nenhuma tabela carregada."
    
    linhas = []
    for tabela, campos in schema_cache.items():
        linhas.append(f"{tabela}: {', '.join(campos)}")
    
    return "\n".join(linhas)

def carregar_valores_distintos(tabela: str, campo: str, limite=20):
    """⚡ Carrega valores distintos sob demanda"""
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

# =========================
# 6. GERAÇÃO DE SUGESTÕES INTELIGENTES
# =========================
def get_relacionamentos_tabela(tabela: str) -> List[str]:
    """Retorna tabelas relacionadas a uma tabela específica"""
    relacionadas = []
    for fk in foreign_keys:
        if fk["from_table"] == tabela and fk["to_table"] not in relacionadas:
            relacionadas.append(fk["to_table"])
        elif fk["to_table"] == tabela and fk["from_table"] not in relacionadas:
            relacionadas.append(fk["from_table"])
    return relacionadas

def gerar_sugestoes_inteligentes() -> List[str]:
    """🧠 Gera sugestões baseadas no schema E relacionamentos"""
    sugestoes = []
    
    # Sugestões gerais sempre úteis
    sugestoes.extend([
        "listar todas as tabelas",
        "quantas tabelas tem no banco",
        "procedures do banco",
        "triggers do banco",
    ])
    
    # Sugestões baseadas nas tabelas encontradas
    for tabela, campos in schema_cache.items():
        nome_lower = tabela.lower()
        
        if "CLIENTE" in tabela.upper():
            sugestoes.extend([
            "tem cliente de goiania?",
            "quantos clientes de sao paulo",
            "mostrar 10 clientes",
            "clientes sem email",
            "primeiro cliente cadastrado",
        ])
        
        # Sugestões básicas para cada tabela
        sugestoes.append(f"quantos registros tem na tabela {nome_lower}")
        sugestoes.append(f"mostrar 5 registros de {nome_lower}")
        sugestoes.append(f"quais campos da tabela {nome_lower}")
        
        # Sugestões baseadas em relacionamentos
        relacionadas = get_relacionamentos_tabela(tabela)
        for rel in relacionadas[:2]:  # Máximo 2 relacionamentos por tabela
            sugestoes.append(f"relacionar {nome_lower} com {rel.lower()}")
            sugestoes.append(f"listar {nome_lower} e seus dados de {rel.lower()}")
        
        # Detectar tipo de tabela e sugerir consultas específicas
        if "CLIENTE" in tabela.upper():
            sugestoes.extend([
                "tem cliente de goiania?",
                "quantos clientes de sao paulo",
                "mostrar 10 clientes",
                "clientes sem email",
                "primeiro cliente cadastrado",
            ])
            # Sugestões relacionais para clientes
            if relacionadas:
                sugestoes.append("listar clientes com seus pedidos")
                sugestoes.append("total de pedidos por cliente")
        
        elif "PRODUTO" in tabela.upper():
            sugestoes.extend([
                f"produtos mais caros",
                f"quantos produtos cadastrados",
                f"produtos em estoque",
            ])
            
        elif "VENDA" in tabela.upper() or "PEDIDO" in tabela.upper():
            sugestoes.extend([
                f"vendas do último mês",
                f"total de vendas por cliente",
                f"produtos mais vendidos",
            ])
        
        # Sugestões baseadas em campos específicos
        for campo in campos:
            campo_upper = campo.upper()
            
            # Campos de cidade/localização
            if campo_upper in ("CIDADE", "UF", "ESTADO"):
                sugestoes.append(f"listar {nome_lower} por {campo.lower()}")
                sugestoes.append(f"{nome_lower} de brasilia")
                break
            
            # Campos de nome
            elif campo_upper in ("NOME", "RAZAO_SOCIAL", "NOME_FANTASIA"):
                sugestoes.append(f"{nome_lower} com nome maria")
                break
                
            # Campos de data
            elif "DATA" in campo_upper:
                sugestoes.append(f"{nome_lower} cadastrados hoje")
                break
    
    # Sugestões de relacionamento avançadas se houver FKs
    if foreign_keys:
        sugestoes.extend([
            "mostrar relacionamentos entre tabelas",
            "consulta com join automático",
            "dados consolidados de múltiplas tabelas",
        ])
    
    # Remover duplicatas mantendo ordem
    vistos = set()
    final = []
    for s in sugestoes:
        if s not in vistos:
            vistos.add(s)
            final.append(s)
    
    return final[:50]

def atualizar_sugestoes():
    """🔄 Atualiza as sugestões globais"""
    global SUGESTOES_INICIAIS
    SUGESTOES_INICIAIS = gerar_sugestoes_inteligentes()

# Carregar schema, relacionamentos e gerar sugestões na inicialização
if conectado:
    print("📋 Carregando metadados do banco...")
    carregar_schema()
    carregar_foreign_keys()
    atualizar_sugestoes()
else:
    # Sugestões básicas mesmo sem conexão
    SUGESTOES_INICIAIS = [
        "listar todas as tabelas",
        "quantas tabelas tem no banco",
        "procedures do banco",
        "triggers do banco",
        "tem cliente de goiania?",
        "quantos clientes de sao paulo",
        "mostrar 10 clientes",
    ]

# =========================
# 7. PRÉ-PROCESSAMENTO (REGRAS INTELIGENTES)
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

def sql_listar_cliente_cidade(cidade: str, limite=20) -> str:
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

    # Comandos específicos rápidos
    comandos_diretos = {
        "listar todas as tabelas": "SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0 ORDER BY RDB$RELATION_NAME",
        "quantas tabelas tem no banco": "SELECT COUNT(*) FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0",
        "procedures do banco": "SELECT RDB$PROCEDURE_NAME FROM RDB$PROCEDURES ORDER BY RDB$PROCEDURE_NAME",
        "triggers do banco": "SELECT RDB$TRIGGER_NAME FROM RDB$TRIGGERS WHERE RDB$SYSTEM_FLAG = 0 ORDER BY RDB$TRIGGER_NAME",
        "mostrar relacionamentos entre tabelas": f"/* Relacionamentos carregados: {len(foreign_keys)} */\nSELECT 'FK: ' || RDB$CONSTRAINT_NAME FROM RDB$RELATION_CONSTRAINTS WHERE RDB$CONSTRAINT_TYPE = 'FOREIGN KEY'",
    }
    
    if p in comandos_diretos:
        return comandos_diretos[p]

    # Comandos específicos para CLI_CLIENTE (se existir)
    if "CLI_CLIENTE" in schema_cache:
        comandos_cliente = {
            "primeiro cliente": "SELECT FIRST 1 * FROM CLI_CLIENTE",
            "clientes sem email": "SELECT FIRST 20 * FROM CLI_CLIENTE WHERE (EMAIL IS NULL OR TRIM(EMAIL) = '')",
            "clientes sem telefone": "SELECT FIRST 20 * FROM CLI_CLIENTE WHERE (TELEFONE IS NULL OR TRIM(TELEFONE) = '')",
        }
        if p in comandos_cliente:
            return comandos_cliente[p]

    # Mostrar N registros
    m = re.match(r"^mostrar\s+(\d+)\s+(?:registros\s+(?:de|da)\s+)?([a-z0-9_]+)$", p)
    if m:
        n = int(m.group(1))
        tabela = m.group(2).upper()
        if tabela in schema_cache:
            return f"SELECT FIRST {n} * FROM {tabela}"
    
    # Mostrar clientes específico
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
# 8. GERAÇÃO SQL VIA IA (🚀 MELHORADA COM RELACIONAMENTOS)
# =========================
def gerar_sql_openai(pergunta: str) -> str:
    """🤖 MELHORADA: Inclui relacionamentos no prompt"""
    if not openai_client:
        raise RuntimeError("OpenAI não configurada")
    
    prompt = f"""
Você é um assistente SQL especialista em banco Firebird. Converta a seguinte pergunta em uma consulta SQL útil para Firebird.

Pergunta: {pergunta}

Tabelas e campos disponíveis:
{formatar_schema_detalhado()}

Relacionamentos (chaves estrangeiras):
{formatar_relacionamentos()}

Regras IMPORTANTES:
1. Use os nomes EXATOS dos campos listados acima
2. Quando a pergunta envolver múltiplas tabelas, use JOIN baseado nos relacionamentos fornecidos
3. Para clientes de cidade use: WHERE UPPER(CIDADE) LIKE '%CIDADE%'
4. Use FIRST X em vez de LIMIT X
5. Use sintaxe específica do Firebird
6. Se precisar de agregação (soma, contagem), use GROUP BY apropriado
7. Para consultas relacionais, sempre use alias nas tabelas (ex: c.NOME, p.VALOR)
8. Responda APENAS com a SQL, sem explicações

Exemplos de JOIN:
- SELECT c.NOME, p.VALOR FROM CLI_CLIENTE c JOIN CLI_PEDIDO p ON c.ID_CLIENTE = p.ID_CLIENTE
"""
    
    resp = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.1
    )
    return resp.choices[0].message.content.strip()

def gerar_sql_gemini(pergunta: str) -> str:
    """🧠 MELHORADA: Inclui relacionamentos no prompt"""
    if not gemini_model:
        raise RuntimeError("Gemini não configurada")
    
    prompt = f"""
Você é um assistente SQL especialista em banco Firebird. Converta a seguinte pergunta em uma consulta SQL útil para Firebird.

Pergunta: {pergunta}

Tabelas e campos disponíveis:
{formatar_schema_detalhado()}

Relacionamentos (chaves estrangeiras):
{formatar_relacionamentos()}

Regras IMPORTANTES:
1. Use os nomes EXATOS dos campos listados acima
2. Quando a pergunta envolver múltiplas tabelas, use JOIN baseado nos relacionamentos fornecidos
3. Para verificar tabelas use: SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0
4. Para contar registros use: SELECT COUNT(*) FROM nome_tabela
5. Para buscar dados use: SELECT * FROM nome_tabela WHERE campo LIKE '%valor%'
6. Para clientes de cidade use: WHERE UPPER(CIDADE) LIKE '%CIDADE%'
7. Use FIRST X em vez de LIMIT X
8. Use sintaxe específica do Firebird
9. Para consultas relacionais, sempre use alias nas tabelas
10. Responda apenas com a SQL, sem formatação markdown

Exemplos de consultas relacionais:
- Listar clientes e pedidos: SELECT c.NOME, p.VALOR FROM CLI_CLIENTE c JOIN CLI_PEDIDO p ON c.ID = p.ID_CLIENTE
- Total por cliente: SELECT c.NOME, SUM(p.VALOR) FROM CLI_CLIENTE c JOIN CLI_PEDIDO p ON c.ID = p.ID_CLIENTE GROUP BY c.NOME
"""
    
    response = gemini_model.generate_content(prompt)
    sql = response.text.strip()
    if sql.startswith("```sql"):
        sql = sql.replace("```sql", "").replace("```", "").strip()
    elif sql.startswith("```"):
        sql = sql.replace("```", "").strip()
    return sql

def gerar_sql_offline(pergunta: str) -> str:
    """🔧 SQL offline melhorada com relacionamentos"""
    comandos_offline = {
        "tabelas": "SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0",
        "clientes": "SELECT FIRST 20 * FROM CLI_CLIENTE",
        "cliente": "SELECT FIRST 20 * FROM CLI_CLIENTE",
        "count": "SELECT COUNT(*) FROM CLI_CLIENTE",
        "quantos": "SELECT COUNT(*) FROM CLI_CLIENTE",
        "campos": "SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'CLI_CLIENTE'",
        "procedures": "SELECT RDB$PROCEDURE_NAME FROM RDB$PROCEDURES",
        "triggers": "SELECT RDB$TRIGGER_NAME FROM RDB$TRIGGERS WHERE RDB$SYSTEM_FLAG = 0",
    }
    
    pergunta_lower = pergunta.lower()
    
    # Busca por palavras-chave
    for palavra, sql in comandos_offline.items():
        if palavra in pergunta_lower:
            print("🔧 Usando modo offline")
            return sql
    
    # Template JOIN simples se detectar relacionamento
    if any(palavra in pergunta_lower for palavra in ["relacionar", "join", "listar", "com"]):
        if foreign_keys:
            # Pega o primeiro FK para exemplo
            fk = foreign_keys[0]
            return f"SELECT * FROM {fk['from_table']} f JOIN {fk['to_table']} t ON f.{fk['from_field']} = t.{fk['to_field']} ROWS 10"
    
    return "SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0"

def gerar_sql(pergunta: str) -> str:
    """🎯 Pipeline completo de geração SQL"""
    # 0. Verifica se já aprendeu essa pergunta
    resposta_aprendida = buscar_resposta_aprendida(pergunta)
    if resposta_aprendida:
        print("💡 (Resposta aprendida)")
        return resposta_aprendida
    
    # 1. Primeiro tenta regras pré-processadas (RÁPIDO)
    regra = preprocessar_pergunta(pergunta)
    if regra:
        print("🔧 (Regra aplicada)")
        return regra
    
    # 2. Depois tenta IA
    try:
        if current_api == "openai" and openai_client:
            print("🤖 Usando OpenAI com relacionamentos...")
            return gerar_sql_openai(pergunta)
        elif current_api == "gemini" and gemini_model:
            print("🧠 Usando Gemini com relacionamentos...")
            return gerar_sql_gemini(pergunta)
        else:
            print(f"⚠️ {current_api} não configurada. Tentando alternativa...")
            trocar_api()
            if current_api == "openai" and openai_client:
                return gerar_sql_openai(pergunta)
            elif current_api == "gemini" and gemini_model:
                return gerar_sql_gemini(pergunta)
            else:
                print("⚠️ Nenhuma IA disponível. Usando modo offline...")
                return gerar_sql_offline(pergunta)
    except Exception as e:
        if "quota" in str(e) or "429" in str(e) or "limit" in str(e).lower():
            print(f"⚠️ {current_api} sem cota. Tentando API alternativa...")
            trocar_api()
            try:
                if current_api == "openai" and openai_client:
                    return gerar_sql_openai(pergunta)
                elif current_api == "gemini" and gemini_model:
                    return gerar_sql_gemini(pergunta)
                else:
                    return gerar_sql_offline(pergunta)
            except Exception as e2:
                print(f"⚠️ Ambas APIs falharam. Usando modo offline...")
                return gerar_sql_offline(pergunta)
        else:
            print(f"⚠️ Erro na API: {e}")
            return gerar_sql_offline(pergunta)

# =========================
# 9. EXECUÇÃO DE SQL (MELHORADA)
# =========================
def analisar_sql(sql: str):
    """🔍 Analisa SQL antes da execução para dar dicas"""
    # Alerta para SELECT * em tabelas grandes
    match = re.match(r"SELECT\s+\*.*FROM\s+([A-Z0-9_]+)", sql, re.IGNORECASE)
    if match:
        tabela = match.group(1).upper()
        if tabela in schema_cache and conectado:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {tabela}")
                total = cur.fetchone()[0]
                if total > 10000:
                    print(f"⚠️ Atenção: {tabela} tem {total:,} registros. A consulta pode ser lenta.")
                    print("💡 Considere usar FIRST N para limitar resultados.")
            except Exception:
                pass

def executar_sql(sql: str):
    """⚡ Executa SQL com análise prévia"""
    if not (conn and cur):
        return False, []
    
    analisar_sql(sql)
    
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

def print_tabela_bonita(rows, max_rows=20):
    """📊 Exibe resultados em formato tabela"""
    if not rows:
        print("⚠️ Nenhum resultado.")
        return
    
    # Descobrir nomes dos campos se possível
    campos = []
    if cur and cur.description:
        campos = [desc[0].strip() for desc in cur.description]
    
    if campos:
        # Ajustar largura das colunas
        col_widths = []
        for i, campo in enumerate(campos):
            max_width = len(str(campo))
            for row in rows[:max_rows]:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            col_widths.append(min(max_width, 25))  # Máximo 25 caracteres por coluna
        
        # Cabeçalho
        header = " | ".join(str(c)[:col_widths[i]].ljust(col_widths[i]) for i, c in enumerate(campos))
        print(header)
        print("-" * len(header))
        
        # Linhas
        for i, row in enumerate(rows[:max_rows]):
            linha = " | ".join(str(row[j])[:col_widths[j]].ljust(col_widths[j]) for j in range(len(campos)))
            print(linha)
    else:
        # Fallback sem campos
        for i, linha in enumerate(rows[:max_rows], 1):
            print(f"   {i:2d}. {linha}")
    
    if len(rows) > max_rows:
        print(f"\n   ➕ ... e mais {len(rows) - max_rows} registros")

# =========================
# 10. BOT (MODO SUGESTÕES MELHORADO)
# =========================
def modo_bot():
    """🤖 Bot inteligente com navegação hierárquica, busca e JOIN automático"""
    print("\n🤖 MODO BOT (Navegação e Busca Inteligente)")
    print("Explore suas tabelas passo a passo, busque termos e relacione dados sem voltar ao início.")
    
    # Estado com memória simples
    historico = []
    tabelas_visitadas = []
    ultima_tabela = None

    # ---------- Helpers locais ----------
    def pause(msg="Pressione Enter para continuar..."):
        try:
            input(msg)
        except EOFError:
            pass

    def listar_categorias():
        # Categoriza por prefixos/padrões comuns
        cats = {
            "👥 CLIENTES": [],
            "📦 PRODUTOS": [],
            "💰 VENDAS/PEDIDOS": [],
            "🌍 LOCALIZAÇÃO": [],
            "🔐 ACESSO": [],
            "📊 MOVIMENTO": [],
            "🏢 COMERCIAL": [],
            "⚙️ SISTEMA": [],
            "📋 OUTRAS": [],
        }
        for t in sorted(schema_cache.keys()):
            up = t.upper()
            if any(x in up for x in ("CLI_", "CLIENTE")):
                cats["👥 CLIENTES"].append(t)
            elif any(x in up for x in ("PRO_", "PRODUTO")):
                cats["📦 PRODUTOS"].append(t)
            elif any(x in up for x in ("VND_", "VENDA", "PEDIDO")):
                cats["💰 VENDAS/PEDIDOS"].append(t)
            elif any(x in up for x in ("LOC_", "CIDADE", "UF", "REGIAO", "BAIRRO")):
                cats["🌍 LOCALIZAÇÃO"].append(t)
            elif any(x in up for x in ("ACE_", "USUARIO", "PERFIL")):
                cats["🔐 ACESSO"].append(t)
            elif any(x in up for x in ("MOV_", "GIRO", "ESTOQUE")):
                cats["📊 MOVIMENTO"].append(t)
            elif any(x in up for x in ("COM_", "OC_", "SC_")):
                cats["🏢 COMERCIAL"].append(t)
            elif any(x in up for x in ("SYS_", "SISTEMA", "CONFIG", "PARAM")):
                cats["⚙️ SISTEMA"].append(t)
            else:
                cats["📋 OUTRAS"].append(t)
        return cats

    def escolher_tabela():
        print("\n" + "="*80)
        print("📋 Selecione uma tabela para explorar, ou pesquise por nome.")
        print("="*80)

        if not schema_cache:
            print("❌ Nenhuma tabela carregada. Use 'Recarregar schema' no menu principal.")
            pause()
            return None

        # Tabelas recentes
        if tabelas_visitadas:
            print("🕒 Recentes:")
            for i, t in enumerate(tabelas_visitadas[-5:], 1):
                print(f"  R{i}. {t} ({len(schema_cache[t])} campos)")
            print("-"*80)

        # Mostrar por categorias com numeração contínua
        opcoes = []
        idx = 1
        for titulo, lista in listar_categorias().items():
            if not lista:
                continue
            print(f"{titulo} ({len(lista)}):")
            for t in lista:
                rels = [fk for fk in foreign_keys if fk['from_table'] == t or fk['to_table'] == t]
                mark = " 🔗" if len(rels) >= 5 else ""
                print(f"  {idx:2d}. {t} ({len(schema_cache[t])} campos, {len(rels)} rels){mark}")
                opcoes.append(t)
                idx += 1
            print()

        print("Comandos:")
        print("  • Número da tabela (ex: 12)")
        print("  • Nome parcial/total (ex: CLI_CLIENTE ou CLIENTE)")
        print("  • 'R1', 'R2'... para recentes")
        print("  • 'buscar termo' para filtrar por nome (ex: buscar cidade)")
        print("  • 'trocar' (IA), 'voltar' (menu principal), 'sair'")
        ent = input("\nEscolha: ").strip()

        if ent.lower() in ("voltar", "menu"):
            return "voltar"
        if ent.lower() == "sair":
            print("👋 Encerrando...")
            exit(0)
        if ent.lower() == "trocar":
            trocar_api()
            return None

        if ent.upper().startswith("R") and ent[1:].isdigit():
            ridx = int(ent[1:]) - 1
            recentes = tabelas_visitadas[-5:]
            if 0 <= ridx < len(recentes):
                return recentes[ridx]

        if ent.lower().startswith("buscar "):
            termo = ent[7:].strip().upper()
            matches = [t for t in schema_cache.keys() if termo in t.upper()]
            if not matches:
                print("⚠️ Nenhuma tabela encontrada.")
                pause()
                return None
            print("\n🔎 Resultado da busca:")
            for i, t in enumerate(matches, 1):
                print(f"  {i:2d}. {t} ({len(schema_cache[t])} campos)")
            s = input("Número para selecionar ou Enter para cancelar: ").strip()
            if s.isdigit():
                i = int(s) - 1
                if 0 <= i < len(matches):
                    return matches[i]
            return None

        if ent.isdigit():
            i = int(ent) - 1
            if 0 <= i < len(opcoes):
                return opcoes[i]

        # Nome parcial
        up = ent.upper()
        candidatos = [t for t in schema_cache.keys() if up in t.upper()]
        if len(candidatos) == 1:
            return candidatos[0]
        elif len(candidatos) > 1:
            print("\nVárias tabelas encontradas:")
            for i, t in enumerate(candidatos, 1):
                print(f"  {i}. {t}")
            s = input("Escolha uma (número): ").strip()
            if s.isdigit():
                i = int(s) - 1
                if 0 <= i < len(candidatos):
                    return candidatos[i]
        else:
            print("⚠️ Tabela não encontrada.")
            pause()

        return None

    def ver_estrutura(tabela):
        campos = schema_cache.get(tabela, [])
        print("\n📋 Estrutura da tabela:", tabela)
        print(f"Total de campos: {len(campos)}")
        for i, c in enumerate(campos, 1):
            print(f"  {i:2d}. {c}")
        # Relacionamentos
        rels = [fk for fk in foreign_keys if fk['from_table'] == tabela or fk['to_table'] == tabela]
        print(f"\n🔗 Relacionamentos ({len(rels)}):")
        if rels:
            for fk in rels:
                print(f"  • {fk['from_table']}.{fk['from_field']} → {fk['to_table']}.{fk['to_field']}")
        else:
            print("  (nenhum)")
        pause()

    def contar_registros(tabela):
        if not conectado:
            print("❌ Sem conexão.")
            pause()
            return
        try:
            cur.execute(f"SELECT COUNT(*) FROM {tabela}")
            total = cur.fetchone()[0]
            print(f"📊 Total de registros em {tabela}: {total:,}")
        except Exception as e:
            print(f"❌ Erro ao contar: {e}")
        pause()

    def mostrar_dados(tabela):
        print("\n👀 Quantos registros mostrar?")
        print("  1. 5  |  2. 10  |  3. 20  |  4. Personalizado")
        ent = input("Escolha (1-4): ").strip()
        limite = 10
        if ent == "1":
            limite = 5
        elif ent == "2":
            limite = 10
        elif ent == "3":
            limite = 20
        elif ent == "4":
            try:
                limite = max(1, int(input("Quantidade: ").strip()))
            except:
                limite = 10
        sql = f"SELECT FIRST {limite} * FROM {tabela}"
        if not conectado:
            print("📋 SQL:", sql)
            pause()
            return
        ok, rows = executar_sql(sql)
        if ok and rows:
            print_tabela_bonita(rows, limite)
        elif ok:
            print("✅ Executado, sem registros.")
        else:
            print("❌ Erro ao executar.")
        pause()

    def parse_campos(tabela, entrada):
        # retorna lista de campos válidos com base em números, listas, nomes parciais ou 'todos'
        campos = schema_cache.get(tabela, [])
        if not campos:
            return []
        e = entrada.strip()
        if e.lower() == "todos":
            return campos[:15]
        selec = []
        # range  ex: 3-7
        if "-" in e and all(x.strip().isdigit() for x in e.split("-")):
            a, b = e.split("-")
            a, b = int(a) - 1, int(b) - 1
            for i in range(min(a, b), max(a, b) + 1):
                if 0 <= i < len(campos):
                    selec.append(campos[i])
        # números separados por vírgula
        elif "," in e and all(x.strip().isdigit() for x in e.split(",")):
            idxs = [int(x.strip()) - 1 for x in e.split(",")]
            for i in idxs:
                if 0 <= i < len(campos):
                    selec.append(campos[i])
        # número único
        elif e.isdigit():
            i = int(e) - 1
            if 0 <= i < len(campos):
                selec.append(campos[i])
        else:
            # nomes (podem ser múltiplos separados por vírgula/espaço)
            nomes = [x.strip().upper() for x in e.replace(",", " ").split() if x.strip()]
            for c in campos:
                up = c.upper()
                if any(n in up for n in nomes):
                    selec.append(c)
        # remover duplicatas preservando ordem
        uniq = []
        for c in selec:
            if c not in uniq:
                uniq.append(c)
        return uniq[:10]  # limitar para não estourar largura

    def campos_especificos(tabela):
        campos = schema_cache.get(tabela, [])
        if not campos:
            print("❌ Tabela sem campos.")
            pause()
            return
        print(f"\n🎯 Campos em {tabela}:")
        for i, c in enumerate(campos, 1):
            print(f"  {i:2d}. {c}")
        print("\nDicas:")
        print("  • números: 1,3,5  |  faixa: 2-6  |  nomes/parte: NOME, CNPJ")
        print("  • 'todos' para primeiros 15 campos")
        e = input("Quais campos explorar? ").strip()
        sel = parse_campos(tabela, e)
        if not sel:
            print("⚠️ Nenhum campo válido selecionado.")
            pause()
            return
        sql = f"SELECT FIRST 15 {', '.join(sel)} FROM {tabela}"
        if not conectado:
            print("📋 SQL:", sql)
            pause()
            return
        ok, rows = executar_sql(sql)
        if ok and rows:
            print_tabela_bonita(rows, 15)
        elif ok:
            print("✅ Executado, sem registros.")
        else:
            print("❌ Erro ao executar.")
        pause()

    def valores_unicos(tabela):
        campos = schema_cache.get(tabela, [])
        if not campos:
            print("❌ Tabela sem campos.")
            pause()
            return
        print(f"\n🏷️ Escolha um campo para ver valores únicos de {tabela}:")
        for i, c in enumerate(campos, 1):
            print(f"  {i:2d}. {c}")
        e = input("Campo (número ou nome): ").strip()
        sel = parse_campos(tabela, e)
        if not sel:
            print("⚠️ Campo inválido.")
            pause()
            return
        campo = sel[0]
        # Tentar usar cache de distintos (já existe no seu código)
        valores = carregar_valores_distintos(tabela, campo, limite=20) or []
        if valores:
            print(f"\n🏷️ {len(valores)} valores (mostrando até 20) de {campo}:")
            for i, v in enumerate(valores, 1):
                print(f"  {i:2d}. {v}")
            ch = input("\nFiltrar por um destes valores? (número/valor/Enter): ").strip()
            if not ch:
                pause()
                return
            # montar filtro
            if ch.isdigit():
                i = int(ch) - 1
                if 0 <= i < len(valores):
                    val = valores[i]
                else:
                    val = None
            else:
                val = ch
            if val is None:
                pause()
                return
            # heurística: tratar como numérico se só dígitos e campo parece ID/NR
            is_num = val.isdigit() and (campo.upper().startswith("ID") or campo.upper().startswith("NR") or campo.upper().endswith("_ID"))
            if is_num:
                sql = f"SELECT FIRST 15 * FROM {tabela} WHERE {campo} = {val}"
            else:
                sql = f"SELECT FIRST 15 * FROM {tabela} WHERE UPPER({campo}) LIKE '%{str(val).upper()}%'"
            if not conectado:
                print("📋 SQL:", sql)
                pause()
                return
            ok, rows = executar_sql(sql)
            if ok and rows:
                print_tabela_bonita(rows, 15)
            elif ok:
                print("✅ Executado, sem registros.")
            else:
                print("❌ Erro ao executar.")
            pause()
        else:
            # fallback direto no banco
            sql = f"SELECT DISTINCT FIRST 20 {campo} FROM {tabela} WHERE {campo} IS NOT NULL ORDER BY {campo}"
            if not conectado:
                print("📋 SQL:", sql)
                pause()
                return
            ok, rows = executar_sql(sql)
            if ok and rows:
                for i, r in enumerate(rows, 1):
                    print(f"  {i:2d}. {r[0]}")
            elif ok:
                print("✅ Sem valores distintos.")
            else:
                print("❌ Erro ao executar.")
            pause()

    def filtros_personalizados(tabela):
        campos = schema_cache.get(tabela, [])
        if not campos:
            print("❌ Tabela sem campos.")
            pause()
            return
        # gerar exemplos a partir de campos reais
        exemplos = []
        for c in campos[:10]:
            u = c.upper()
            if u.startswith("ID") or u.endswith("_ID"):
                exemplos += [f"{c} = 1", f"{c} > 0"]
            elif any(x in u for x in ("NM_", "NOME", "RAZAO", "FANTASIA", "DESCR")):
                exemplos += [f"{c} LIKE '%FARMACIA%'", f"UPPER({c}) LIKE '%SILVA%'"]
            elif u.startswith("NR") or "FONE" in u or "CNPJ" in u or "CEP" in u:
                exemplos += [f"{c} IS NOT NULL", f"LENGTH({c}) >= 8"]
            elif u.startswith("DT") or "DATA" in u:
                exemplos += [f"{c} >= '2024-01-01'", f"{c} IS NOT NULL"]
            elif u.startswith("FG") or "FLAG" in u or "STATUS" in u:
                exemplos += [f"{c} = 'S'", f"{c} = 'N'"]
        print("\n🔍 Exemplos de filtros (sem WHERE):")
        for i, ex in enumerate(exemplos[:8], 1):
            print(f"  {i}. {ex}")
        filtro = input("\nDigite o filtro WHERE (sem 'WHERE'): ").strip()
        if not filtro:
            return
        sql = f"SELECT FIRST 15 * FROM {tabela} WHERE {filtro}"
        if not conectado:
            print("📋 SQL:", sql)
            pause()
            return
        ok, rows = executar_sql(sql)
        if ok and rows:
            print_tabela_bonita(rows, 15)
        elif ok:
            print("✅ Nenhum registro encontrado.")
        else:
            print("❌ Erro no filtro. Verifique nomes de campos reais (veja 'Ver estrutura').")
        pause()

    def explorar_relacionamentos(tabela):
        rels = [fk for fk in foreign_keys if fk['from_table'] == tabela or fk['to_table'] == tabela]
        if not rels:
            print("❌ Nenhum relacionamento para esta tabela.")
            pause()
            return
        print(f"\n🔗 Relacionamentos de {tabela}:")
        for i, fk in enumerate(rels, 1):
            if fk['from_table'] == tabela:
                print(f"  {i:2d}. {tabela}.{fk['from_field']} → {fk['to_table']}.{fk['to_field']}")
            else:
                print(f"  {i:2d}. {fk['from_table']}.{fk['from_field']} → {tabela}.{fk['to_field']}")
        s = input("Escolha um relacionamento (número) ou Enter para cancelar: ").strip()
        if not s.isdigit():
            return
        i = int(s) - 1
        if not (0 <= i < len(rels)):
            return
        fk = rels[i]
        if fk['from_table'] == tabela:
            sql = (
                f"SELECT FIRST 15 a.{fk['from_field']}, b.* "
                f"FROM {fk['from_table']} a JOIN {fk['to_table']} b "
                f"ON a.{fk['from_field']} = b.{fk['to_field']}"
            )
        else:
            sql = (
                f"SELECT FIRST 15 b.{fk['to_field']}, a.* "
                f"FROM {fk['from_table']} a JOIN {fk['to_table']} b "
                f"ON a.{fk['from_field']} = b.{fk['to_field']}"
            )
        if not conectado:
            print("📋 SQL:", sql)
            pause()
            return
        ok, rows = executar_sql(sql)
        if ok and rows:
            print_tabela_bonita(rows, 15)
        elif ok:
            print("✅ Sem registros relacionados.")
        else:
            print("❌ Erro no JOIN.")
        pause()

    def buscar_nesta_tabela(tabela):
        termo = input("🔎 Termo de busca (em campos de texto): ").strip()
        if not termo:
            return
        # focar em prováveis campos de texto
        campos = schema_cache.get(tabela, [])
        text_fields = [c for c in campos if any(k in c.upper() for k in ("NM_", "NOME", "RAZAO", "FANTASIA", "DESCR"))]
        if not text_fields:
            text_fields = campos[:5]
        conds = [f"UPPER({c}) LIKE '%{termo.upper()}%'" for c in text_fields]
        where = " OR ".join(conds) if conds else "1=1"
        sql = f"SELECT FIRST 15 * FROM {tabela} WHERE {where}"
        if not conectado:
            print("📋 SQL:", sql)
            pause()
            return
        ok, rows = executar_sql(sql)
        if ok and rows:
            print_tabela_bonita(rows, 15)
        elif ok:
            print("✅ Nenhum registro encontrado.")
        else:
            print("❌ Erro ao buscar.")
        pause()

    def pergunta_livre_sql():
        q = input("\n💬 Pergunte em linguagem natural (IA gera SQL). 'voltar' para sair: ").strip()
        if not q or q.lower() in ("voltar", "sair"):
            return
        sql = gerar_sql(q)
        print("🔍 SQL gerada:", sql)
        if not conectado:
            print("📋 Sem conexão. Execute manualmente no seu cliente.")
            pause()
            return
        ok, rows = executar_sql(sql)
        if ok and rows:
            print_tabela_bonita(rows, 25)
        elif ok:
            print("✅ Executado, sem registros.")
        else:
            print("❌ Erro na execução.")
        pause()

    def explorar_tabela(tabela):
        nonlocal ultima_tabela
        ultima_tabela = tabela
        if tabela not in tabelas_visitadas:
            tabelas_visitadas.append(tabela)
        while True:
            print("\n" + "="*80)
            print(f"🔍 Explorando {tabela}")
            print("="*80)
            print("Opções:")
            print("  1. 📋 Ver estrutura")
            print("  2. 🔢 Contar registros")
            print("  3. 👀 Mostrar dados")
            print("  4. 🎯 Campos específicos")
            print("  5. 🏷️ Valores únicos por campo")
            print("  6. 🔍 Filtros personalizados")
            print("  7. 🔗 Relacionamentos (JOIN)")
            print("  8. 🔎 Buscar nesta tabela (texto)")
            print("  9. 🤖 Pergunta livre (IA → SQL)")
            print("  0. 🔙 Trocar de tabela")
            print("Comandos: número, 'voltar' (menu), 'trocar' (IA), 'sair'")
            ent = input("Sua escolha: ").strip().lower()
            if ent in ("voltar", "menu"):
                return "voltar"
            if ent == "sair":
                print("👋 Encerrando...")
                exit(0)
            if ent == "trocar":
                trocar_api()
                continue
            if ent == "0":
                return None
            if ent == "1":
                ver_estrutura(tabela)
            elif ent == "2":
                contar_registros(tabela)
            elif ent == "3":
                mostrar_dados(tabela)
            elif ent == "4":
                campos_especificos(tabela)
            elif ent == "5":
                valores_unicos(tabela)
            elif ent == "6":
                filtros_personalizados(tabela)
            elif ent == "7":
                explorar_relacionamentos(tabela)
            elif ent == "8":
                buscar_nesta_tabela(tabela)
            elif ent == "9":
                pergunta_livre_sql()
            else:
                print("⚠️ Opção inválida.")

    # ---------- Loop principal ----------
    while True:
        # 1) Escolher tabela
        t = escolher_tabela()
        if t == "voltar":
            return
        if not t:
            continue

        historico.append(f"Tabela: {t}")
        res = explorar_tabela(t)
        if res == "voltar":
            return
        # senão, volta para escolher outra tabela e continuar a navegação

# =========================
# 11. CHAT (MODO LIVRE MELHORADO)
# =========================
chat_history = []

def modo_chat():
    print("\n💬 MODO CHAT (Conversa Livre com JOIN Inteligente)")
    print("Pergunte qualquer coisa sobre o banco. A IA agora conhece os relacionamentos!")
    print("Comandos: 'trocar', 'voltar', 'rels' (ver relacionamentos), 'sair'")
    
    while True:
        pergunta = input("\nVocê: ").strip()
        
        if pergunta.lower() in ("voltar", "menu"):
            return
        if pergunta.lower() == "sair":
            print("👋 Encerrando chat.")
            exit(0)
        if pergunta.lower() == "trocar":
            trocar_api()
            continue
        if pergunta.lower() == "rels":
            print(f"\n🔗 Relacionamentos disponíveis ({len(foreign_keys)}):")
            for fk in foreign_keys:
                print(f"   • {fk['from_table']}.{fk['from_field']} → {fk['to_table']}.{fk['to_field']}")
            continue
            
        # 🔧 AQUI TAMBÉM: chat em linguagem natural agora funciona
        sql = gerar_sql(pergunta)
        print(f"🔍 SQL gerada: {sql}")
        
        if conectado:
            sucesso, rows = executar_sql(sql)
            if sucesso and rows:
                print("🤖 Resultados do CENTRAL.FDB:")
                print_tabela_bonita(rows, 25)
            elif sucesso:
                print("🤖 Comando executado com sucesso")
            else:
                print("❌ Erro na execução")
        else:
            print("❌ Sem conexão com o banco. Execute esta SQL manualmente:")
            print(f"📋 {sql}")

            
# =========================
# 12. MENU PRINCIPAL MELHORADO
# =========================
def menu_principal():
    print("\n" + "="*80)
    print("🚀 ASSISTENTE FIREBIRD INTELIGENTE - VERSÃO COM RELACIONAMENTOS")
    print(f"🔌 Conexão: {'✅ CONECTADO' if conectado else '❌ SEM CONEXÃO'}")
    print(f"🧠 IA atual: {current_api.upper()} ({'✅' if (current_api == 'openai' and openai_client) or (current_api == 'gemini' and gemini_model) else '❌'})")
    print(f"📊 Tabelas: {len(schema_cache)} | 🔗 Relacionamentos: {len(foreign_keys)} | 💡 Sugestões: {len(SUGESTOES_INICIAIS)}")
    print("="*80)
    print("1. 🤖 Bot (Sugeridor inteligente com JOIN automático)")
    print("2. 💬 Chat (Conversa livre com relacionamentos)")
    print("3. 🔄 Trocar IA (OpenAI ↔ Gemini)")
    print("4. 📋 Recarregar schema e relacionamentos")
    print("5. 🔍 Ver tabelas e relacionamentos")
    print("6. 🧪 Testar SQL customizada")
    print("7. 👋 Sair")
    print("="*80)

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
                print("🔄 Recarregando metadados completos...")
                carregar_schema()
                carregar_foreign_keys()
                atualizar_sugestoes()
                print("✅ Schema, relacionamentos e sugestões atualizadas.")
                # Mostra tabelas e relacionamentos após recarregar
                if schema_cache:
                    print(f"\n📋 Tabelas carregadas ({len(schema_cache)}):")
                    for i, (tabela, campos) in enumerate(schema_cache.items(), 1):
                        print(f"   {i:2d}. {tabela} ({len(campos)} campos)")
                    print(f"\n🔗 Relacionamentos ({len(foreign_keys)}):")
                    for i, fk in enumerate(foreign_keys, 1):
                        print(f"   {i:2d}. {fk['from_table']}.{fk['from_field']} → {fk['to_table']}.{fk['to_field']}")
                else:
                    print("❌ Nenhuma tabela carregada.")
            else:
                print("❌ Sem conexão para recarregar.")
            continue  # <-- Adicione esta linha    
        elif op == "5":
            if schema_cache:
                print(f"\n📋 Tabelas carregadas ({len(schema_cache)}):")
                for i, (tabela, campos) in enumerate(schema_cache.items(), 1):
                    print(f"   {i:2d}. {tabela} ({len(campos)} campos)")
                    
                print(f"\n🔗 Relacionamentos ({len(foreign_keys)}):")
                for i, fk in enumerate(foreign_keys, 1):
                    print(f"   {i:2d}. {fk['from_table']}.{fk['from_field']} → {fk['to_table']}.{fk['to_field']}")
            else:
                print("❌ Nenhuma tabela carregada.")
        elif op == "6":
            if not conectado:
                print("❌ Sem conexão.")
                continue
            sql_custom = input("Digite a SQL para testar: ").strip()
            if sql_custom:
                sucesso, rows = executar_sql(sql_custom)
                if sucesso and rows:
                    print_tabela_bonita(rows)
                elif sucesso:
                    print("✅ Executado com sucesso")
        elif op == "7":
            print("👋 Até logo!")
            if conn:
                cur.close()
                conn.close()
                print("🔌 Conexão encerrada")
            exit(0)
        else:
            print("⚠️ Opção inválida. Escolha 1-7.")

# =========================
# 13. MAIN
# =========================
def main():
    print("🔥 ASSISTENTE FIREBIRD INTELIGENTE - VERSÃO RELACIONAMENTOS")
    print("🧠 IA híbrida (OpenAI/Gemini) + 🔗 JOIN automático + 📋 Sugestões contextuais")
    
    if not conectado:
        print("\n⚠️ OPERANDO SEM EXECUÇÃO REAL (somente geração de SQL)")
        print("💡 Verifique se o Firebird está rodando e o caminho do banco está correto")
        print("📋 Você ainda pode usar o bot e chat para gerar SQL com relacionamentos")
    
    print(f"\n🎯 Status: Schema {'✅' if schema_cache else '❌'} | FKs {'✅' if foreign_keys else '❌'} | Sugestões {'✅' if SUGESTOES_INICIAIS else '❌'}")
    
    if not openai_client and not gemini_model:
        print("⚠️ NENHUMA IA CONFIGURADA - Configure OPENAI_API_KEY ou GEMINI_API_KEY")
    else:
        apis_ok = []
        if openai_client:
            apis_ok.append("OpenAI")
        if gemini_model:
            apis_ok.append("Gemini")
        print(f"✅ APIs funcionando: {', '.join(apis_ok)}")
    
    while True:
        menu_principal()

if __name__ == "__main__":
    main()