import os
from openai import OpenAI

# 🔑 Configurar sua API key da OpenAI
os.environ["OPENAI_API_KEY"] = "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"
client = OpenAI()

print("💬 Gerador de SQL para Firebird (digite 'sair' para encerrar)")
print("🔧 Versão sem conexão direta ao banco")

def gerar_sql(pergunta):
    prompt = f"""
    Você é um assistente SQL para banco Firebird. Converta a seguinte pergunta em uma consulta SQL válida para Firebird:
    
    Pergunta: {pergunta}
    
    Regras:
    - Use sintaxe específica do Firebird
    - Responda apenas com a SQL, sem explicações
    - Use FIRST X em vez de LIMIT X
    - Use RDB$ tabelas do sistema quando apropriado
    """
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.1
    )
    return resp.choices[0].message.content.strip()

while True:
    pergunta = input("Você: ").strip()
    if pergunta.lower() == "sair":
        break
    
    try:
        sql = gerar_sql(pergunta)
        print(f"🔍 SQL gerada para Firebird:")
        print(f"📋 {sql}")
        print("-" * 50)
    except Exception as e:
        print(f"⚠️ Erro: {e}")

print("👋 Até logo!")
