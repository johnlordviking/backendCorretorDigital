# 1_buscar_sites.py (Versão ajustada para n8n)
from googlesearch import search
import time
from urllib.parse import urlparse
import sys
import json # MUDANÇA 1: Importar a biblioteca JSON

# --- FUNÇÃO PARA LOGS ---
def log(message):
    """Imprime mensagens de log no standard error para não poluir a saída de dados."""
    print(message, file=sys.stderr)

# --- CONFIGURAÇÃO ---
num_resultados_por_busca = 50

# Palavras-chave positivas
PALAVRAS_CHAVE_INCLUIR = ["imoveis", "imobiliaria", "corretor", "creci", "aluguel", "venda", "lançamentos"]
# Palavras-chave negativas para a query
PALAVRAS_CHAVE_EXCLUIR_QUERY = "-vagas -emprego -classificados -cartorio -registro -noticias"
# Domínios para ignorar
DOMINIOS_PARA_IGNORAR = [
    "zapimoveis", "vivareal", "olx", "imovelweb", "mercadolivre", 
    "facebook", "instagram", "linkedin", "youtube", "twitter",
    "infojobs", "catho", "vagas.com.br", "indeed", "glassdoor",
    "guiamais", "jusbrasil", "gov.br", "prefeitura", "econodata"
]

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cidade = sys.argv[1]
    else:
        log("Erro: Forneça o nome da cidade como argumento.")
        exit(1)

    queries = [
        f'site imobiliária "{cidade}" MG {PALAVRAS_CHAVE_EXCLUIR_QUERY}',
        f'imóveis à venda em "{cidade}" {PALAVRAS_CHAVE_EXCLUIR_QUERY}',
        f'corretor de imóveis site "{cidade}" {PALAVRAS_CHAVE_EXCLUIR_QUERY}'
    ]

    log(f"🔎 Iniciando a busca refinada por sites de imobiliárias em {cidade}...")
    urls_encontradas = set()

    for query in queries:
        log(f"Buscando por: '{query}'...")
        try:
            for url in search(query, num_results=num_resultados_por_busca, lang='pt-br'):
                dominio_principal = urlparse(url).netloc
                
                if not dominio_principal:
                    continue

                if any(portal_ignorado in dominio_principal for portal_ignorado in DOMINIOS_PARA_IGNORAR):
                    continue

                if any(keyword in url.lower() for keyword in PALAVRAS_CHAVE_INCLUIR):
                    urls_encontradas.add(f"https://{dominio_principal}") # Adiciona URL completa
                
                time.sleep(1.5)
                
        except Exception as e:
            log(f"Ocorreu um erro na busca: {e}. Continuando...")
        
        log("Aguardando para a próxima busca...")
        time.sleep(5)

    log(f"\n✅ Busca finalizada! Foram encontrados {len(urls_encontradas)} domínios potenciais.")

    # MUDANÇA 2: Em vez de salvar em arquivo, imprimir um JSON para o n8n capturar
    resultado_json = {
        "cidade_analisada": cidade,
        "total_sites": len(urls_encontradas),
        "sites": sorted(list(urls_encontradas))
    }
    
    # Imprime o JSON no standard output. Esta será a saída de dados para o n8n.
    print(json.dumps(resultado_json, indent=4))