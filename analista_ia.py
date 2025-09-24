# 2_analista_ia.py (Versão Final com Validação)AIzaSyAjA_YoXVBXJ3e5QVeyA1zPv5ivzWfnrg4
# 2_analista_ia.py (Versão Final com Validação e Processamento em Lotes)
import requests
from bs4 import BeautifulSoup
import json
import os
import google.generativeai as genai
import time
from urllib.parse import urlparse
import os

# --- CONFIGURAÇÃO ---
# Cole sua chave de API do Google AI aqui.
# Você pode obter uma em https://aistudio.google.com/
CHAVE_API_GOOGLE = os.getenv("GOOGLE_API_KEY")
ARQUIVO_DE_SITES = 'sites_para_analisar.txt'
ARQUIVO_DE_SAIDA = 'configuracao_scrapers.json'
ARQUIVO_ERROS = 'relatorio_erros_analista.txt'
# --------------------

if CHAVE_API_GOOGLE == "SUA_CHAVE_API_AQUI":
    print("⚠️ ATENÇÃO: Você precisa adicionar sua chave de API do Google AI na variável CHAVE_API_GOOGLE.")
    exit()

genai.configure(api_key=CHAVE_API_GOOGLE)

def carregar_configuracoes_existentes(arquivo):
    """Carrega as configurações já salvas, se o arquivo existir."""
    if os.path.exists(arquivo):
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Aviso: O arquivo '{arquivo}' está corrompido ou vazio. Começando um novo.")
            return {}
    return {}

def buscar_html_da_pagina(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        return response.text, None
    except requests.RequestException as e:
        return None, f"Erro ao buscar a URL: {e}"

def criar_prompt_para_llm(html_pagina):
    soup = BeautifulSoup(html_pagina, 'html.parser')
    for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'svg']):
        tag.decompose()
    html_limpo = soup.prettify()[:15000] # Limita o tamanho para a API

    return f"""
    Analise o código HTML a seguir de uma página de listagem de imóveis e gere um JSON com os seletores CSS para os seguintes campos:
    1. 'container_anuncio': O seletor principal que engloba um único anúncio de imóvel na lista.
    2. 'preco': Seletor para o preço do imóvel.
    3. 'endereco': Seletor para o endereço ou bairro.
    4. 'descricao': Seletor para o bloco de texto com a descrição do imóvel (onde podem estar quartos, banheiros, etc.).
    5. 'proxima_pagina': Seletor para o link ou botão de "próxima página" ou "next". Se não encontrar, retorne null.

    Instruções:
    - Forneça os seletores DENTRO do 'container_anuncio', exceto para 'proxima_pagina'.
    - O formato da saída deve ser um JSON válido, e nada mais.

    HTML:
    ```html
    {html_limpo}
    ```
    JSON de saída:
    """

def gerar_configuracao_com_ia(html_pagina):
    prompt = criar_prompt_para_llm(html_pagina)
    try:
        print("  🧠 Enviando HTML para o Google AI (Gemini) analisar...")
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content(prompt)
        # Extrai e limpa a resposta para garantir que seja apenas o JSON
        resposta_json = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(resposta_json), None
    except Exception as e:
        if 'quota' in str(e).lower():
            return None, "Cota da API excedida"
        else:
            return None, f"Erro ao comunicar com a API: {e}"

# --- FLUXO PRINCIPAL ---
if __name__ == "__main__":
    if not os.path.exists(ARQUIVO_DE_SITES):
        print(f"Arquivo '{ARQUIVO_DE_SITES}' não encontrado. Execute o '1_buscar_sites.py' primeiro.")
        exit()

    configuracoes_finais = carregar_configuracoes_existentes(ARQUIVO_DE_SAIDA)
    erros_analise = []
    print(f"Carregadas {len(configuracoes_finais)} configurações já existentes.")

    with open(ARQUIVO_DE_SITES, 'r', encoding='utf-8') as f:
        sites_para_processar = [line.strip() for line in f if line.strip()]

    sites_novos = [site for site in sites_para_processar if urlparse(site).netloc not in configuracoes_finais]
    
    if not sites_novos:
        print("✅ Nenhum site novo para processar.")
        exit()

    print(f"🤖 Iniciando análise com IA para {len(sites_novos)} novos sites...")

    for site_url in sites_novos:
        dominio = urlparse(site_url).netloc
        print(f"\nProcessando: {site_url}")
        html_result, erro_busca = buscar_html_da_pagina(site_url)
        
        if erro_busca:
            erros_analise.append(f"{site_url} - {erro_busca}")
            continue

        time.sleep(2)
        config, erro_ia = gerar_configuracao_com_ia(html_result)
        
        if erro_ia:
            erros_analise.append(f"{site_url} - {erro_ia}")
            if "Cota da API excedida" in erro_ia:
                print("  🛑 Parando a execução. Rode novamente mais tarde para continuar.")
                break
            continue

        if isinstance(config, dict) and config.get('container_anuncio'):
            print(f"  ✅ Configuração gerada e validada!")
            config['url_busca'] = site_url
            configuracoes_finais[dominio] = config
        else:
            motivo = f"A IA não retornou uma configuração válida. Resposta: {config}"
            print(f"  ⚠️ AVISO: {motivo}")
            erros_analise.append(f"{site_url} - {motivo}")

    with open(ARQUIVO_DE_SAIDA, 'w', encoding='utf-8') as f:
        json.dump(configuracoes_finais, f, indent=2, ensure_ascii=False)
    print(f"\n\n🎉 Processo finalizado! {len(configuracoes_finais)} configs salvas em '{ARQUIVO_DE_SAIDA}'")

    if erros_analise:
        with open(ARQUIVO_ERROS, 'w', encoding='utf-8') as f:
            f.write("Relatório de Erros - Robô Analista com IA\n" + "="*40 + "\n")
            for erro in erros_analise:
                f.write(f"{erro}\n")
        print(f"\n📝 Um relatório com {len(erros_analise)} erros foi salvo em '{ARQUIVO_ERROS}'")

