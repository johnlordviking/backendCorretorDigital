# 4_consolidar_dados.py (Versão Final)
import pandas as pd
import os
import glob

# --- CONFIGURAÇÃO ---
PASTA_DOS_CSV = 'dados_extraidos'
NOME_ARQUIVO_FINAL = 'OFERTAS_CONSOLIDADAS.xlsx'
# --------------------

arquivos_csv = glob.glob(os.path.join(PASTA_DOS_CSV, '*.csv'))

if not arquivos_csv:
    print(f"Nenhum arquivo CSV encontrado na pasta '{PASTA_DOS_CSV}'. Execute o '3_extrator_mestre.py' primeiro.")
    exit()

print(f"Consolidando {len(arquivos_csv)} arquivos CSV...")

lista_de_dfs = []
for arquivo in arquivos_csv:
    try:
        df = pd.read_csv(arquivo)
        lista_de_dfs.append(df)
    except Exception as e:
        print(f"Não foi possível ler o arquivo {arquivo}. Erro: {e}")

if lista_de_dfs:
    df_final = pd.concat(lista_de_dfs, ignore_index=True)
    
    # Remove duplicatas baseadas em colunas chave para evitar imóveis repetidos
    colunas_chave = ['endereco', 'preco', 'site']
    df_final.drop_duplicates(subset=colunas_chave, inplace=True, keep='first')
    
    # Reordena as colunas para o padrão final e garante que todas existam
    colunas_finais = ['codigo', 'tipo', 'endereco', 'preco', 'area', 'quartos', 'salas', 'banheiros', 'garagem', 'site']
    for col in colunas_finais:
        if col not in df_final.columns:
            df_final[col] = "N/I"
    df_final = df_final[colunas_finais]

    df_final.to_excel(NOME_ARQUIVO_FINAL, index=False)
    
    print(f"\n✅ Consolidação concluída! {len(df_final)} ofertas únicas salvas em '{NOME_ARQUIVO_FINAL}'")
else:
    print("\n❌ Nenhum dado para consolidar.")
