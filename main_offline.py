import os

print("💬 Gerador de SQL para Firebird - Versão Offline")
print("🔧 Comandos SQL comuns para Firebird")
print("-" * 50)

# Comandos SQL pré-definidos para Firebird
comandos_sql = {
    "tabelas": "SELECT RDB$RELATION_NAME FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0;",
    "campos": "SELECT RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME = 'NOME_TABELA';",
    "clientes": "SELECT * FROM CLI_CLIENTE;",
    "todos clientes": "SELECT * FROM CLI_CLIENTE;",
    "primeiro cliente": "SELECT FIRST 1 * FROM CLI_CLIENTE;",
    "10 clientes": "SELECT FIRST 10 * FROM CLI_CLIENTE;",
    "count clientes": "SELECT COUNT(*) FROM CLI_CLIENTE;",
    "criar tabela": "CREATE TABLE EXEMPLO (ID INTEGER PRIMARY KEY, NOME VARCHAR(50));",
    "inserir": "INSERT INTO CLI_CLIENTE (NOME, EMAIL) VALUES ('João', 'joao@email.com');",
    "atualizar": "UPDATE CLI_CLIENTE SET NOME = 'Novo Nome' WHERE ID = 1;",
    "deletar": "DELETE FROM CLI_CLIENTE WHERE ID = 1;",
    "procedure": "SELECT * FROM RDB$PROCEDURES;",
    "triggers": "SELECT * FROM RDB$TRIGGERS;",
    "geradores": "SELECT * FROM RDB$GENERATORS;",
}

def mostrar_ajuda():
    print("\n📋 Comandos disponíveis:")
    for cmd in comandos_sql.keys():
        print(f"  • {cmd}")
    print("\n💡 Digite parte do comando para buscar SQL relacionado")

def buscar_sql(termo):
    termo = termo.lower().strip()
    encontrados = []
    
    for cmd, sql in comandos_sql.items():
        if termo in cmd.lower():
            encontrados.append((cmd, sql))
    
    return encontrados

# Mostrar ajuda inicial
mostrar_ajuda()

while True:
    pergunta = input("\nVocê: ").strip()
    
    if pergunta.lower() in ["sair", "exit", "quit"]:
        break
    elif pergunta.lower() in ["ajuda", "help", "?"]:
        mostrar_ajuda()
        continue
    
    # Buscar comandos relacionados
    resultados = buscar_sql(pergunta)
    
    if resultados:
        print(f"\n🔍 Encontrei {len(resultados)} comando(s) relacionado(s):")
        for i, (cmd, sql) in enumerate(resultados, 1):
            print(f"\n{i}. {cmd.upper()}:")
            print(f"📋 {sql}")
    else:
        print("\n❓ Comando não encontrado. Digite 'ajuda' para ver os disponíveis.")
        
        # Sugestões baseadas em palavras-chave
        if "client" in pergunta.lower() or "cli" in pergunta.lower():
            print("💡 Talvez você queira: 'clientes', 'count clientes', 'primeiro cliente'")
        elif "tabela" in pergunta.lower():
            print("💡 Talvez você queira: 'tabelas', 'campos', 'criar tabela'")

print("\n👋 Até logo!")
