import os
import fdb
import time
from openai import OpenAI
import google.generativeai as genai

# 🔑 APIs configuradas
API_KEYS = {
    "openai": "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",
    "gemini": "AIzaSyDeTIz34pWW760D14Quh9Z_E7YPC4lQdFo"
}

os.environ["OPENAI_API_KEY"] = API_KEYS["openai"]
genai.configure(api_key=API_KEYS["gemini"])

openai_client = OpenAI()
gemini_model = genai.GenerativeModel('gemini-1.5-flash')
current_api = "openai"

def testar_conexao():
    """Testa conexão com várias configurações"""
    db_path = r"C:\Users\Dev Ruan\Desktop\ruan\treinamento\CENTRAL.FDB"
    
    configs = [
        # TCP/IP porta 4050
        {"host": "localhost", "port": 4050, "database": db_path},
        # TCP/IP porta 3050 (padrão)
        {"host": "localhost", "port": 3050, "database": db_path},
        # Embedded (direto no arquivo)
        {"database": db_path},
        # DSN formato
        {"dsn": f"localhost/4050:{db_path}"},
        {"dsn": f"localhost/3050:{db_path}"},
    ]
    
    for i, config in enumerate(configs, 1):
        try:
            print(f"🔄 Teste {i}: {config}")
            conn = fdb.connect(
                user="SYSDBA",
                password="masterkey",
                charset="UTF8",
                **config
            )
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM RDB$DATABASE")
            resultado = cur.fetchone()
            
            print(f"✅ SUCESSO! Configuração {i} funcionou!")
            print(f"📊 Teste: {resultado}")
            
            # Testar listagem de tabelas
            cur.execute("SELECT COUNT(*) FROM RDB$RELATIONS WHERE RDB$SYSTEM_FLAG = 0")
            qtd_tabelas = cur.fetchone()[0]
            print(f"📋 Tabelas encontradas: {qtd_tabelas}")
            
            cur.close()
            conn.close()
            return config
            
        except Exception as e:
            print(f"❌ Teste {i} falhou: {e}")
    
    return None

def main():
    print("🔍 DIAGNÓSTICO DE CONEXÃO FIREBIRD")
    print("=" * 50)
    
    # Verificar arquivo
    db_path = r"C:\Users\Dev Ruan\Desktop\ruan\treinamento\CENTRAL.FDB"
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"✅ Arquivo CENTRAL.FDB encontrado ({size:,} bytes)")
    else:
        print(f"❌ Arquivo não encontrado: {db_path}")
        return
    
    # Testar conexões
    config_funcionou = testar_conexao()
    
    if config_funcionou:
        print("\n🎉 CONEXÃO ESTABELECIDA!")
        print(f"🔧 Use esta configuração: {config_funcionou}")
        print("\n💬 Iniciando chat...")
        
        # Aqui você poderia iniciar o chat normal
        
    else:
        print("\n❌ NENHUMA CONEXÃO FUNCIONOU")
        print("\n💡 SOLUÇÕES:")
        print("1. Instalar Firebird Server:")
        print("   • Download: https://firebirdsql.org/en/downloads/")
        print("   • Instalar Firebird 5.0 para Windows")
        print("   • O serviço iniciará automaticamente")
        print("\n2. Verificar se há Firebird já instalado:")
        print("   • Procurar por 'Firebird' no menu Iniciar")
        print("   • Verificar pasta C:\\Program Files\\Firebird*")
        print("\n3. Usar ferramentas externas:")
        print("   • IBExpert (gratuito)")
        print("   • FlameRobin (open source)")
        print("   • DBeaver (universal)")
        
        print(f"\n🤖 Enquanto isso, use o main_sql_generator.py que está funcionando!")

if __name__ == "__main__":
    main()
