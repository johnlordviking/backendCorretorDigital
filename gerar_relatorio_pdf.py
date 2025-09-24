# 5_gerar_relatorio_pdf.py (Versão modificada para Dashboard)
import pandas as pd
import os
import sys
import re
import time
from fpdf import FPDF
import matplotlib.pyplot as plt

# --- CONFIGURAÇÃO ---
ARQUIVO_EXCEL = 'OFERTAS_CONSOLIDADAS.xlsx'
PASTA_RELATORIOS = 'relatorios' # Nome da pasta onde os PDFs serão salvos
# --------------------

def limpar_valor(valor):
    """Limpa e converte um valor monetário em string para float."""
    if pd.isna(valor): return None
    try:
        valor_str = str(valor)
        # Remove caracteres não numéricos, exceto vírgula e ponto
        valor_limpo = re.sub(r'[^\d,.]', '', valor_str)
        # Lida com o formato brasileiro (ex: 1.000,00)
        if ',' in valor_limpo and '.' in valor_limpo:
            valor_limpo = valor_limpo.replace('.', '')
        valor_limpo = valor_limpo.replace(',', '.')
        return float(valor_limpo)
    except (ValueError, TypeError):
        return None

def formatar_brl(valor):
    """Formata um número para o padrão de moeda brasileiro (R$)."""
    if pd.isna(valor): return "N/A"
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

class PDF(FPDF):
    """Classe customizada para o PDF, com cabeçalho e rodapé personalizados."""
    def __init__(self, cidade):
        super().__init__()
        self.cidade = cidade
        
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, f'Relatório de Potencial Imobiliário - {self.cidade}', 0, 1, 'C')
        self.set_font('Arial', 'I', 8)
        self.cell(0, 5, f'Gerado em: {time.strftime("%d/%m/%Y %H:%M:%S")}', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)

    def draw_table(self, header, data, col_widths):
        # ... (código da tabela, sem alterações)
        self.set_font('Arial', 'B', 9)
        self.set_fill_color(230, 230, 230)
        for i, col_name in enumerate(header):
            self.cell(col_widths[i], 7, col_name, 1, 0, 'C', 1)
        self.ln()
        self.set_font('Arial', '', 9)
        for row in data:
            for i, item in enumerate(row):
                self.cell(col_widths[i], 6, str(item), 1, 0, 'L' if i == 0 else 'R')
            self.ln()


# --- FLUXO PRINCIPAL DE EXECUÇÃO ---
if __name__ == "__main__":
    # Validação dos argumentos de linha de comando
    if len(sys.argv) < 3:
        print("Erro: Forneça o nome da cidade e o ID da consulta como argumentos.")
        print("Exemplo: python gerar_relatorio_pdf.py \"São João del-Rei\" \"consulta_123xyz\"")
        sys.exit(1)

    CIDADE_ANALISADA = sys.argv[1]
    CONSULTA_ID = sys.argv[2]
    
    # Define o nome do arquivo final e o caminho completo
    NOME_RELATORIO_PDF = f"Relatorio_{CONSULTA_ID}.pdf"
    CAMINHO_COMPLETO_PDF = os.path.join(PASTA_RELATORIOS, NOME_RELATORIO_PDF)
    
    # Cria a pasta de relatórios, se não existir
    os.makedirs(PASTA_RELATORIOS, exist_ok=True)
    
    if not os.path.exists(ARQUIVO_EXCEL):
        print(f"Arquivo de dados '{ARQUIVO_EXCEL}' não encontrado.")
        sys.exit(1)

    print(f"📊 Iniciando geração do relatório para a cidade: {CIDADE_ANALISADA}...")
    df = pd.read_excel(ARQUIVO_EXCEL)

    # Limpeza e processamento dos dados
    df['preco_num'] = df['preco'].apply(limpar_valor)
    df.dropna(subset=['preco_num'], inplace=True)
    df = df[df['preco_num'] > 1000]

    if df.empty:
        print("❌ Não foram encontrados dados válidos para gerar o relatório.")
        sys.exit(1)

    df['bairro'] = df['endereco'].str.split(',').str[-1].str.strip().str.title()
    df['tipo'].fillna('Não Especificado', inplace=True)
    df.loc[df['tipo'].str.contains('Terreno|Lote', case=False, na=False), 'tipo'] = 'Terreno/Lote'
    df.loc[df['tipo'].str.contains('Casa', case=False, na=False), 'tipo'] = 'Casa'
    df.loc[df['tipo'].str.contains('Apartamento', case=False, na=False), 'tipo'] = 'Apartamento'

    # Análises estatísticas
    analise_categoria = df.groupby('tipo')['preco_num'].agg(['mean', 'max', 'min', 'count']).reset_index()
    analise_bairro = df.groupby('bairro')['preco_num'].agg(['mean', 'count']).reset_index().sort_values(by='count', ascending=False).head(10)

    # Geração do Gráfico (com nome de arquivo temporário e único)
    grafico_path_temp = os.path.join(PASTA_RELATORIOS, f'grafico_{CONSULTA_ID}.png')
    plt.figure(figsize=(10, 6))
    analise_categoria.set_index('tipo')['mean'].sort_values().plot(kind='barh', color='skyblue')
    plt.title('Preço Médio de Oferta por Categoria de Imóvel')
    plt.xlabel('Preço Médio (R$)')
    plt.ylabel('Categoria')
    plt.grid(axis='x', linestyle='--')
    plt.savefig(grafico_path_temp, bbox_inches='tight')
    plt.close()
    print("  - Gráfico de médias gerado.")

    # --- Montagem do PDF ---
    pdf = PDF(CIDADE_ANALISADA)
    pdf.add_page()
    
    # Sumário Executivo
    pdf.chapter_title('Sumário Executivo')
    pdf.set_font('Arial', '', 11)
    media_geral = df['preco_num'].mean()
    pdf.multi_cell(0, 8, f"- Total de ofertas válidas analisadas: {len(df)}\n"
                       f"- Preço médio geral de oferta: {formatar_brl(media_geral)}")
    pdf.ln(5)

    # Tabelas de Análise
    pdf.chapter_title('Análise de Preços por Categoria')
    header_cat = ['Categoria', 'Média (R$)', 'Máximo (R$)', 'Mínimo (R$)', 'Nº Ofertas']
    data_cat = [[row['tipo'], formatar_brl(row['mean']), formatar_brl(row['max']), formatar_brl(row['min']), int(row['count'])] for _, row in analise_categoria.iterrows()]
    pdf.draw_table(header_cat, data_cat, [50, 40, 40, 30, 30])
    pdf.ln(10)
    
    pdf.chapter_title('Top 10 Bairros por Volume de Ofertas')
    # ... (código da tabela de bairros, sem alterações)
    header_bairro = ['Bairro', 'Média (R$)', 'Nº Ofertas']
    data_bairro = [[row['bairro'], formatar_brl(row['mean']), int(row['count'])] for _, row in analise_bairro.iterrows()]
    pdf.set_font('Arial', 'B', 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(120, 7, 'Bairro', 1, 0, 'C', 1)
    pdf.cell(40, 7, 'Média (R$)', 1, 0, 'C', 1)
    pdf.cell(30, 7, 'Nº Ofertas', 1, 1, 'C', 1)
    pdf.set_font('Arial', '', 9)
    for row in data_bairro:
        pdf.cell(120, 6, str(row[0]), 1, 0, 'L')
        pdf.cell(40, 6, str(row[1]), 1, 0, 'R')
        pdf.cell(30, 6, str(row[2]), 1, 1, 'R')
    
    # Adiciona a imagem do gráfico
    if os.path.exists(grafico_path_temp):
        pdf.add_page(orientation='L')
        pdf.chapter_title('Gráfico: Preço Médio por Categoria')
        pdf.image(grafico_path_temp, x=10, y=None, w=277)
    
    # Salva o arquivo PDF final
    pdf.output(CAMINHO_COMPLETO_PDF)
    print(f"✅ Relatório '{NOME_RELATORIO_PDF}' gerado com sucesso em '{PASTA_RELATORIOS}/'")
    
    # Remove o arquivo de imagem temporário
    if os.path.exists(grafico_path_temp):
        os.remove(grafico_path_temp)
        print("  - Gráfico temporário removido.")
