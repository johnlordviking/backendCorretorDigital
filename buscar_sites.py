# 1_buscar_sites.py (Versão Final Refinada)
from googlesearch import search
import time
from urllib.parse import urlparse
import sys

# --- CONFIGURAÇÃO ---
num_resultados_por_busca = 50
# --------------------


# Palavras-chave positivas que indicam um site de imobiliária
PALAVRAS_CHAVE_INCLUIR = ["imoveis", "imobiliaria", "corretor", "creci", "aluguel", "venda", "lançamentos"]

# Palavras-chave negativas para excluir sites indesejados da busca do Google
PALAVRAS_CHAVE_EXCLUIR_QUERY = "-vagas -emprego -classificados -cartorio -registro -noticias"

# Domínios de grandes portais, classificados e outros a serem sempre ignorados
DOMINIOS_PARA_IGNORAR = [
    "zapimoveis", "vivareal", "olx", "imovelweb", "mercadolivre", 
    "facebook", "instagram", "linkedin", "youtube", "twitter",
    "infojobs", "catho", "vagas.com.br", "indeed", "glassdoor",
    "guiamais", "jusbrasil", "gov.br", "prefeitura", "econodata"
]

if __name__ == "__main__": # Adicione essa verificação
    # 2. SUBSTITUA A LINHA 'cidade = ...' POR ESTE BLOCO
    if len(sys.argv) > 1:
        cidade = sys.argv[1]
    else:
        print("Erro: Forneça o nome da cidade como argumento.")
        print("Exemplo: python 1_buscar_sites.py \"São João del-Rei\"")
        exit()

    queries = [
        f'site imobiliária "{cidade}" MG {PALAVRAS_CHAVE_EXCLUIR_QUERY}',
        f'imóveis à venda em "{cidade}" {PALAVRAS_CHAVE_EXCLUIR_QUERY}',
        f'corretor de imóveis site "{cidade}" {PALAVRAS_CHAVE_EXCLUIR_QUERY}'
    ]

print(f"🔎 Iniciando a busca refinada por sites de imobiliárias em {cidade}...")
urls_encontradas = set()

for query in queries:
    print(f"Buscando por: '{query}'...")
    try:
        for url in search(query, num_results=num_resultados_por_busca, lang='pt-br'):
            dominio_principal = urlparse(url).netloc
            
            if not dominio_principal:
                continue

            if any(portal_ignorado in dominio_principal for portal_ignorado in DOMINIOS_PARA_IGNORAR):
                continue

            if any(keyword in url.lower() for keyword in PALAVRAS_CHAVE_INCLUIR):
                urls_encontradas.add(dominio_principal)
            
            time.sleep(1.5)
            
    except Exception as e:
        print(f"Ocorreu um erro na busca: {e}. Continuando...")
    
    print("Aguardando para a próxima busca...")
    time.sleep(5)

print(f"\n✅ Busca finalizada! Foram encontrados {len(urls_encontradas)} domínios potenciais.")

with open('sites_para_analisar.txt', 'w', encoding='utf-8') as f:
    for url in sorted(urls_encontradas):
        f.write(f"https://{url}\n")

print("\n📝 Lista de sites salva em 'sites_para_analisar.txt'")
print("A lista agora está mais limpa, mas uma validação manual final ainda é recomendada.")

