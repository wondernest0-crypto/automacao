# ========================================
# GERADOR DE PLANILHA DE ACURACIDADE
# Desenvolvido para controle de estoque
# ========================================

import pandas as pd
from datetime import datetime
import os

print("=" * 50)
print("🔥 GERADOR DE PLANILHA DE ACURACIDADE DE ESTOQUE")
print("=" * 50)

# ========================================
# DADOS DE EXEMPLO (EDITE AQUI!)
# ========================================
dados = {
    'Item': [
        'VK22020',
        'VK22021', 
        'VK22022',
        'VK22023',
        'VK22024',
        'VK22025',
        'VK22026',
        'VK22027',
        'VK22028',
        'VK22029'
    ],
    'Qtd_Fiscal_TOTVS': [
        500,
        300,
        450,
        1000,
        200,
        750,
        600,
        320,
        890,
        150
    ],
    'Qtd_Fisica_Contada': [
        510,    # Excesso de 10
        300,    # Exato
        430,    # Falta de 20
        1150,   # Excesso de 150
        185,    # Falta de 15
        750,    # Exato
        680,    # Excesso de 80
        290,    # Falta de 30
        890,    # Exato
        175     # Excesso de 25
    ]
}

# ========================================
# CRIANDO DATAFRAME E CALCULANDO
# ========================================
df = pd.DataFrame(dados)

# Diferença (Física - Fiscal)
df['Diferenca'] = df['Qtd_Fisica_Contada'] - df['Qtd_Fiscal_TOTVS']

# Acuracidade % (NUNCA PASSA DE 100%)
df['Acuracidade_%'] = (
    df[['Qtd_Fisica_Contada', 'Qtd_Fiscal_TOTVS']].min(axis=1) / 
    df['Qtd_Fiscal_TOTVS'] * 100
).round(2)

# Excesso % (só quando tem mais no físico)
df['Excesso_%'] = df.apply(
    lambda x: round((x['Qtd_Fisica_Contada'] - x['Qtd_Fiscal_TOTVS']) / x['Qtd_Fiscal_TOTVS'] * 100, 2) 
    if x['Qtd_Fisica_Contada'] > x['Qtd_Fiscal_TOTVS'] else None, 
    axis=1
)

# Falta % (só quando tem menos no físico)
df['Falta_%'] = df.apply(
    lambda x: round((x['Qtd_Fiscal_TOTVS'] - x['Qtd_Fisica_Contada']) / x['Qtd_Fiscal_TOTVS'] * 100, 2) 
    if x['Qtd_Fisica_Contada'] < x['Qtd_Fiscal_TOTVS'] else None, 
    axis=1
)

# Status
df['Status'] = df['Diferenca'].apply(
    lambda x: '✅ EXATO' if x == 0 else ('🔴 EXCESSO' if x > 0 else '⚠️ FALTA')
)

# ========================================
# CALCULANDO INDICADORES DO DASHBOARD
# ========================================
total_itens = len(df)
acuracidade_geral = df['Acuracidade_%'].mean().round(2)
qtd_excesso = len(df[df['Diferenca'] > 0])
qtd_falta = len(df[df['Diferenca'] < 0])
qtd_exato = len(df[df['Diferenca'] == 0])
vol_excesso = int(df[df['Diferenca'] > 0]['Diferenca'].sum())
vol_falta = int(abs(df[df['Diferenca'] < 0]['Diferenca'].sum()))
perc_excesso = round(qtd_excesso / total_itens * 100, 2)
perc_falta = round(qtd_falta / total_itens * 100, 2)
perc_exato = round(qtd_exato / total_itens * 100, 2)

# DataFrame do Dashboard
dashboard = pd.DataFrame({
    'Indicador': [
        '📊 Total de Itens Contados',
        '🎯 Acuracidade Geral (%)',
        '🔴 Qtd Itens com Excesso',
        '⚠️ Qtd Itens com Falta',
        '✅ Qtd Itens Exatos',
        '📈 % Itens com Excesso',
        '📉 % Itens com Falta',
        '✔️ % Itens Exatos',
        '📦 Volume Total de Excesso (peças)',
        '📦 Volume Total de Falta (peças)'
    ],
    'Valor': [
        total_itens,
        f"{acuracidade_geral}%",
        qtd_excesso,
        qtd_falta,
        qtd_exato,
        f"{perc_excesso}%",
        f"{perc_falta}%",
        f"{perc_exato}%",
        vol_excesso,
        vol_falta
    ]
})

# Dados para gráfico de pizza
grafico_dados = pd.DataFrame({
    'Status': ['EXATO', 'EXCESSO', 'FALTA'],
    'Quantidade': [qtd_exato, qtd_excesso, qtd_falta]
})

# ========================================
# GERANDO ARQUIVO EXCEL
# ========================================
nome_arquivo = f'Acuracidade_Estoque_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

with pd.ExcelWriter(nome_arquivo, engine='xlsxwriter') as writer:
    
    # Escrevendo as abas
    df.to_excel(writer, sheet_name='CONTAGEM', index=False, startrow=2)
    dashboard.to_excel(writer, sheet_name='DASHBOARD', index=False, startrow=2)
    grafico_dados.to_excel(writer, sheet_name='DASHBOARD', index=False, startrow=2, startcol=4)
    
    workbook = writer.book
    
    # ========================================
    # FORMATOS
    # ========================================
    
    # Título
    titulo_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'font_color': 'white',
        'bg_color': '#1F4E79',
        'align': 'center',
        'valign': 'vcenter',
        'border': 2
    })
    
    # Cabeçalho
    header_format = workbook.add_format({
        'bold': True,
        'font_size': 11,
        'font_color': 'white',
        'bg_color': '#2E75B6',
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })
    
    # Células normais
    cell_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    # Verde (Exato)
    green_format = workbook.add_format({
        'bg_color': '#C6EFCE',
        'font_color': '#006100',
        'border': 1,
        'align': 'center',
        'bold': True
    })
    
    # Vermelho (Excesso)
    red_format = workbook.add_format({
        'bg_color': '#FFC7CE',
        'font_color': '#9C0006',
        'border': 1,
        'align': 'center',
        'bold': True
    })
    
    # Amarelo (Falta)
    yellow_format = workbook.add_format({
        'bg_color': '#FFEB9C',
        'font_color': '#9C5700',
        'border': 1,
        'align': 'center',
        'bold': True
    })
    
    # Número
    number_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'num_format': '#,##0'
    })
    
    # Percentual
    percent_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'num_format': '0.00"%"'
    })
    
    # ========================================
    # ABA CONTAGEM
    # ========================================
    ws1 = writer.sheets['CONTAGEM']
    
    # Título
    ws1.merge_range('A1:H1', '📊 CONTROLE DE ACURACIDADE DE ESTOQUE', titulo_format)
    
    # Largura das colunas
    ws1.set_column('A:A', 15)  # Item
    ws1.set_column('B:B', 20)  # Qtd Fiscal
    ws1.set_column('C:C', 20)  # Qtd Física
    ws1.set_column('D:D', 12)  # Diferença
    ws1.set_column('E:E', 15)  # Acuracidade
    ws1.set_column('F:F', 12)  # Excesso %
    ws1.set_column('G:G', 12)  # Falta %
    ws1.set_column('H:H', 15)  # Status
    
    # Cabeçalhos formatados
    headers = ['Item', 'Qtd Fiscal (TOTVS)', 'Qtd Física (Contada)', 'Diferença', 
               'Acuracidade %', 'Excesso %', 'Falta %', 'Status']
    for col, header in enumerate(headers):
        ws1.write(2, col, header, header_format)
    
    # Formatação condicional no Status
    ws1.conditional_format('H4:H1000', {
        'type': 'text',
        'criteria': 'containing',
        'value': 'EXATO',
        'format': green_format
    })
    ws1.conditional_format('H4:H1000', {
        'type': 'text',
        'criteria': 'containing',
        'value': 'EXCESSO',
        'format': red_format
    })
    ws1.conditional_format('H4:H1000', {
        'type': 'text',
        'criteria': 'containing',
        'value': 'FALTA',
        'format': yellow_format
    })
    
    # Formatação condicional na Acuracidade
    ws1.conditional_format('E4:E1000', {
        'type': 'cell',
        'criteria': '==',
        'value': 100,
        'format': green_format
    })
    ws1.conditional_format('E4:E1000', {
        'type': 'cell',
        'criteria': '<',
        'value': 95,
        'format': red_format
    })
    ws1.conditional_format('E4:E1000', {
        'type': 'cell',
        'criteria': 'between',
        'minimum': 95,
        'maximum': 99.99,
        'format': yellow_format
    })
    
    # Congelar painel
    ws1.freeze_panes(3, 0)
    
    # ========================================
    # ABA DASHBOARD
    # ========================================
    ws2 = writer.sheets['DASHBOARD']
    
    # Título
    ws2.merge_range('A1:B1', '📊 DASHBOARD DE INDICADORES', titulo_format)
    
    # Largura das colunas - AJUSTADO PARA MELHOR VISUALIZAÇÃO
    ws2.set_column('A:A', 40)  # Indicador - mais largo
    ws2.set_column('B:B', 25)  # Valor - mais largo
    ws2.set_column('E:E', 18)  # Status
    ws2.set_column('F:F', 18)  # Quantidade
    
    # Cabeçalhos
    ws2.write(2, 0, 'Indicador', header_format)
    ws2.write(2, 1, 'Valor', header_format)
    ws2.write(2, 4, 'Status', header_format)
    ws2.write(2, 5, 'Quantidade', header_format)
    
    # ========================================
    # GRÁFICO DE PIZZA - MELHORADO
    # ========================================
    pie_chart = workbook.add_chart({'type': 'pie'})
    pie_chart.add_series({
        'name': 'Distribuição por Status',
        'categories': '=DASHBOARD!$E$4:$E$6',
        'values': '=DASHBOARD!$F$4:$F$6',
        'points': [
            {'fill': {'color': '#00B050'}},  # Verde - Exato
            {'fill': {'color': '#FF0000'}},  # Vermelho - Excesso
            {'fill': {'color': '#FFC000'}},  # Amarelo - Falta
        ],
        'data_labels': {
            'percentage': True, 
            'category': True,
            'position': 'best_fit',
            'font': {'size': 11, 'bold': True}
        }
    })
    pie_chart.set_title({
        'name': '📊 Distribuição por Status',
        'name_font': {'size': 14, 'bold': True}
    })
    pie_chart.set_legend({'position': 'bottom', 'font': {'size': 10}})
    pie_chart.set_style(10)
    ws2.insert_chart('H2', pie_chart, {'x_scale': 1.5, 'y_scale': 1.5})
    
    # ========================================
    # GRÁFICO DE BARRAS - ACURACIDADE POR ITEM - MELHORADO
    # ========================================
    bar_chart = workbook.add_chart({'type': 'bar'})
    bar_chart.add_series({
        'name': 'Acuracidade %',
        'categories': '=CONTAGEM!$A$4:$A$13',
        'values': '=CONTAGEM!$E$4:$E$13',
        'fill': {'color': '#2E75B6'},
        'data_labels': {
            'value': True,
            'font': {'size': 9, 'bold': True}
        }
    })
    bar_chart.set_title({
        'name': '🎯 Acuracidade por Item (%)',
        'name_font': {'size': 14, 'bold': True}
    })
    bar_chart.set_x_axis({
        'name': 'Acuracidade %', 
        'max': 100,
        'name_font': {'size': 11, 'bold': True},
        'num_font': {'size': 10}
    })
    bar_chart.set_y_axis({
        'name': 'Item',
        'name_font': {'size': 11, 'bold': True},
        'num_font': {'size': 10}
    })
    bar_chart.set_legend({'position': 'none'})
    bar_chart.set_style(10)
    ws2.insert_chart('H20', bar_chart, {'x_scale': 1.5, 'y_scale': 1.8})
    
    # ========================================
    # GRÁFICO DE COLUNAS - VOLUME EXCESSO vs FALTA - MELHORADO
    # ========================================
    col_chart = workbook.add_chart({'type': 'column'})
    col_chart.add_series({
        'name': 'Volume Excesso',
        'categories': ['DASHBOARD', 8, 0, 8, 0],
        'values': [[vol_excesso]],
        'fill': {'color': '#FF0000'},
        'data_labels': {
            'value': True,
            'font': {'size': 11, 'bold': True}
        }
    })
    col_chart.add_series({
        'name': 'Volume Falta',
        'categories': ['DASHBOARD', 9, 0, 9, 0],
        'values': [[vol_falta]],
        'fill': {'color': '#FFC000'},
        'data_labels': {
            'value': True,
            'font': {'size': 11, 'bold': True}
        }
    })
    col_chart.set_title({
        'name': '📦 Volume Total: Excesso vs Falta (peças)',
        'name_font': {'size': 14, 'bold': True}
    })
    col_chart.set_x_axis({
        'name': 'Tipo',
        'name_font': {'size': 11, 'bold': True}
    })
    col_chart.set_y_axis({
        'name': 'Quantidade (peças)',
        'name_font': {'size': 11, 'bold': True},
        'num_font': {'size': 10}
    })
    col_chart.set_legend({'position': 'top', 'font': {'size': 10}})
    col_chart.set_style(10)
    ws2.insert_chart('H45', col_chart, {'x_scale': 1.5, 'y_scale': 1.3})
    
print(f"\n✅ ARQUIVO GERADO COM SUCESSO!")
print(f"📁 Nome: {nome_arquivo}")
print(f"📂 Local: {os.getcwd()}")
print("=" * 50)
print("\n📊 RESUMO DOS INDICADORES:")
print(f"   Total de Itens: {total_itens}")
print(f"   Acuracidade Geral: {acuracidade_geral}%")
print(f"   Itens Exatos: {qtd_exato} ({perc_exato}%)")
print(f"   Itens com Excesso: {qtd_excesso} ({perc_excesso}%)")
print(f"   Itens com Falta: {qtd_falta} ({perc_falta}%)")
print(f"   Volume Excesso: {vol_excesso} peças")
print(f"   Volume Falta: {vol_falta} peças")
print("=" * 50)
print("\n🔥 Abre o arquivo e confere! Tá PROFISSIONAL!")