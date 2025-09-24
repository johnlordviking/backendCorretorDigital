# 5_gerar_relatorio_pdf.py (Versão Final com Análise Avançada)
import pandas as pd
import os
from fpdf import FPDF
import matplotlib.pyplot as plt
import time
import re
import sys

# --- CONFIGURAÇÃO ---
ARQUIVO_EXCEL = 'OFERTAS_CONSOLIDADAS.xlsx'
NOME_RELATORIO_PDF = 'Relatorio_Mercado_Imobiliario.pdf'

# --------------------

def limpar_valor(valor):
    if pd.isna(valor): return None
    try:
        valor_str = str(valor)
        # Remove R$, pontos de milhar, e converte vírgula para ponto decimal
        valor_limpo = re.sub(r'[^\d,.]', '', valor_str)
        if ',' in valor_limpo and '.' in valor_limpo:
            valor_limpo = valor_limpo.replace('.', '')
        valor_limpo = valor_limpo.replace(',', '.')
        return float(valor_limpo)
    except (ValueError, TypeError):
        return None

class PDF(FPDF):
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

def formatar_brl(valor):
    if pd.isna(valor): return "N/A"
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

if __name__ == "__main__":
    if len(sys.argv) > 1:
        CIDADE_ANALISADA = sys.argv[1]
    else:
        print("Erro: Forneça o nome da cidade como argumento.")
        print("Exemplo: python 5_gerar_relatorio_pdf.py \"São João del-Rei\"")
        exit()

    if not os.path.exists(ARQUIVO_EXCEL):
        print(f"Arquivo '{ARQUIVO_EXCEL}' não encontrado.")
        exit()

    print("📊 Iniciando geração do relatório em PDF...")
    df = pd.read_excel(ARQUIVO_EXCEL)

    df['preco_num'] = df['preco'].apply(limpar_valor)
    df.dropna(subset=['preco_num'], inplace=True)
    df = df[df['preco_num'] > 1000] # Filtra preços muito baixos

    # Extrai o bairro do endereço (lógica simplificada)
    df['bairro'] = df['endereco'].str.split(',').str[-1].str.strip().str.title()
    
    # Padroniza a coluna 'tipo'
    df['tipo'].fillna('Não Especificado', inplace=True)
    df.loc[df['tipo'].str.contains('Terreno|Lote', case=False, na=False), 'tipo'] = 'Terreno/Lote'
    df.loc[df['tipo'].str.contains('Casa', case=False, na=False), 'tipo'] = 'Casa'
    df.loc[df['tipo'].str.contains('Apartamento', case=False, na=False), 'tipo'] = 'Apartamento'


    analise_categoria = df.groupby('tipo')['preco_num'].agg(['mean', 'max', 'min', 'count']).reset_index()
    analise_bairro = df.groupby('bairro')['preco_num'].agg(['mean', 'count']).reset_index().sort_values(by='count', ascending=False).head(10)

    if not analise_categoria.empty:
        plt.figure(figsize=(10, 6))
        analise_categoria.set_index('tipo')['mean'].sort_values().plot(kind='barh', color='skyblue')
        plt.title('Preço Médio de Oferta por Categoria de Imóvel')
        plt.xlabel('Preço Médio (R$)')
        plt.ylabel('Categoria')
        plt.grid(axis='x', linestyle='--')
        grafico_path = 'grafico_media_precos.png'
        plt.savefig(grafico_path, bbox_inches='tight')
        plt.close()
        print("  - Gráfico de médias gerado.")
    else:
        grafico_path = None

    pdf = PDF(CIDADE_ANALISADA)
    pdf.add_page()
    
    pdf.chapter_title('Sumário Executivo')
    pdf.set_font('Arial', '', 11)
    media_geral = df['preco_num'].mean()
    pdf.multi_cell(0, 8, f"- Total de ofertas válidas analisadas: {len(df)}\n"
                       f"- Preço médio geral de oferta: {formatar_brl(media_geral)}")
    pdf.ln(5)

    pdf.chapter_title('Análise de Preços por Categoria')
    header_cat = ['Categoria', 'Média (R$)', 'Máximo (R$)', 'Mínimo (R$)', 'Nº Ofertas']
    data_cat = []
    for _, row in analise_categoria.iterrows():
        data_cat.append([row['tipo'], formatar_brl(row['mean']), formatar_brl(row['max']), formatar_brl(row['min']), int(row['count'])])
    pdf.draw_table(header_cat, data_cat, [50, 40, 40, 30, 30])
    pdf.ln(10)
    
    pdf.chapter_title('Top 10 Bairros por Volume de Ofertas')
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
    
    if grafico_path and os.path.exists(grafico_path):
        pdf.add_page(orientation='L')
        pdf.chapter_title('Gráfico: Preço Médio por Categoria')
        pdf.image(grafico_path, x=10, y=None, w=277)
    
    pdf.output(NOME_RELATORIO_PDF)
    print(f"✅ Relatório '{NOME_RELATORIO_PDF}' gerado com sucesso!")
