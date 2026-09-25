# ========================================
# CRIAR BASE FISCAL (ITENS DO TOTVS)
# Roda só uma vez para criar o arquivo base
# ========================================

import pandas as pd

# ========================================
# COLOQUE AQUI OS ITENS DO TOTVS
# ========================================
dados_totvs = {
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
    'Descricao': [
        'Produto A',
        'Produto B',
        'Produto C',
        'Produto D',
        'Produto E',
        'Produto F',
        'Produto G',
        'Produto H',
        'Produto I',
        'Produto J'
    ]
}

df = pd.DataFrame(dados_totvs)
df.to_excel('BASE_FISCAL_TOTVS.xlsx', index=False)

print("✅ BASE FISCAL CRIADA: BASE_FISCAL_TOTVS.xlsx")
print("📝 Edite esse arquivo para adicionar/alterar itens do TOTVS")