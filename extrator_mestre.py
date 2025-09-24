# 3_extrator_mestre.py (Versão Final com Navegação e Extração de Detalhes por IA)
import pandas as pd
import json
import os
import time
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
from bs4 import BeautifulSoup
import google.generativeai as genai
import soupsieve
import os

# --- CONFIGURAÇÃO ---
CHAVE_API_GOOGLE = os.getenv("GOOGLE_API_KEY")
ARQUIVO_DE_CONFIG = 'configuracao_scrapers.json'
PASTA_SAIDA = 'dados_extraidos'
ARQUIVO_ERROS = 'relatorio_erros_extrator.txt'
PAGINAS_PARA_EXTRAIR = 3
# --------------------

if CHAVE_API_GOOGLE == "SUA_CHAVE_API_AQUI":
    print("⚠️ ATENÇÃO: Adicione sua chave de API do Google AI para extrair detalhes da descrição.")
    
genai.configure(api_key=CHAVE_API_GOOGLE)

if not os.path.exists(PASTA_SAIDA):
    os.makedirs(PASTA_SAIDA)

def extrair_detalhes_com_ia(texto_descricao):
    if not texto_descricao or texto_descricao == "N/I" or CHAVE_API_GOOGLE == "SUA_CHAVE_API_AQUI":
        return {}
        
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    prompt = f"""
    Analise o texto a seguir. Extraia APENAS as seguintes informações e retorne um JSON válido:
    - "codigo" (string, o código/referência do imóvel)
    - "tipo" (string, ex: "Apartamento", "Casa", "Terreno/Lote")
    - "quartos" (número inteiro)
    - "salas" (número inteiro)
    - "banheiros" (número inteiro)
    - "garagem" (número inteiro de vagas)
    - "area" (string, ex: "120m²")
    
    Se uma informação não for encontrada, retorne null para o campo.

    Texto: "{texto_descricao[:2000]}"
    JSON de saída:
    """
    try:
        response = model.generate_content(prompt)
        json_str = response.text.strip().split('{', 1)[1].rsplit('}', 1)[0]
        return json.loads('{' + json_str + '}')
    except (IndexError, json.JSONDecodeError, Exception):
        return {}

def extrair_dados_site(config, erros_extracao):
    url_base = config.get('url_busca')
    dominio = urlparse(url_base).netloc
    print(f"  - Iniciando navegador para {url_base}...")
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(30)
    
    todas_os_imoveis = []
    
    try:
        driver.get(url_base)
        time.sleep(5)
        
        for i in range(PAGINAS_PARA_EXTRAIR):
            print(f"    - Lendo página {i+1}...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            anuncios = soup.select(config['container_anuncio'])
            
            if not anuncios:
                print("    - Nenhum anúncio encontrado com o seletor fornecido.")
                break

            for anuncio in anuncios:
                descricao = anuncio.select_one(config.get('descricao', '')).text.strip() if anuncio.select_one(config.get('descricao', '')) else ""
                
                detalhes_ia = extrair_detalhes_com_ia(descricao)
                time.sleep(1.5)

                dados_imovel = {
                    'codigo': detalhes_ia.get('codigo', "N/I"),
                    'tipo': detalhes_ia.get('tipo', "Não Especificado"),
                    'endereco': anuncio.select_one(config.get('endereco', '')).text.strip() if anuncio.select_one(config.get('endereco', '')) else "N/I",
                    'preco': anuncio.select_one(config.get('preco', '')).text.strip() if anuncio.select_one(config.get('preco', '')) else "N/I",
                    'area': detalhes_ia.get('area', "N/I"),
                    'quartos': detalhes_ia.get('quartos', "N/I"),
                    'salas': detalhes_ia.get('salas', "N/I"),
                    'banheiros': detalhes_ia.get('banheiros', "N/I"),
                    'garagem': detalhes_ia.get('garagem', "N/I"),
                    'site': dominio
                }
                todas_os_imoveis.append(dados_imovel)
            
            seletor_proxima = config.get('proxima_pagina')
            if not seletor_proxima or i == PAGINAS_PARA_EXTRAIR - 1:
                if not seletor_proxima: erros_extracao.append(f"{dominio} - Lembrete: Paginação não configurada.")
                break
            
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, seletor_proxima)
                driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(1)
                next_button.click()
                time.sleep(5)
            except (NoSuchElementException, ElementClickInterceptedException):
                print("    - Fim da paginação ou botão não clicável.")
                break
                
    except TimeoutException:
        erro = f"Timeout ao carregar a página {url_base}."
        print(f"    ❌ {erro}")
        erros_extracao.append(f"{dominio} - {erro}")
    except soupsieve.util.SelectorSyntaxError as e:
        erro = f"Erro de sintaxe no seletor '{config['container_anuncio']}'."
        print(f"    ❌ {erro}")
        erros_extracao.append(f"{dominio} - {erro}")
    except Exception as e:
        erro = f"Erro inesperado durante a navegação: {e}"
        print(f"    ❌ {erro}")
        erros_extracao.append(f"{dominio} - {erro}")
    finally:
        driver.quit()

    return todas_os_imoveis

if __name__ == "__main__":
    if not os.path.exists(ARQUIVO_DE_CONFIG):
        print(f"Arquivo '{ARQUIVO_DE_CONFIG}' não encontrado.")
        exit()

    with open(ARQUIVO_DE_CONFIG, 'r', encoding='utf-8') as f:
        configuracoes = json.load(f)
    
    erros_extracao = []
    print(f"🤖 Iniciando extração para {len(configuracoes)} sites configurados...")

    for dominio, config in configuracoes.items():
        print(f"\nExtraindo dados de: {dominio}")
        if not isinstance(config, dict):
            erros_extracao.append(f"{dominio} - Configuração inválida no JSON.")
            continue
            
        dados = extrair_dados_site(config, erros_extracao)
        
        if dados:
            df = pd.DataFrame(dados)
            nome_arquivo = os.path.join(PASTA_SAIDA, f"dados_{dominio.replace('.', '_')}.csv")
            df.to_csv(nome_arquivo, index=False, encoding='utf-8-sig')
            print(f"    ✅ {len(dados)} registros salvos em '{nome_arquivo}'")

    if erros_extracao:
        with open(ARQUIVO_ERROS, 'w', encoding='utf-8') as f:
            f.write("Relatório de Erros - Robô Extrator Mestre\n" + "="*40 + "\n")
            for erro in erros_extracao:
                f.write(f"{erro}\n")
        print(f"\n📝 Um relatório com {len(erros_extracao)} erros foi salvo em '{ARQUIVO_ERROS}'")

    print("\n\n🎉 Processo de extração finalizado!")
