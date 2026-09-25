# ========================================
# CONFIGURAÇÕES DO SISTEMA
# ========================================

import os
import getpass

# Diretórios
DIR_BASE = os.path.dirname(os.path.abspath(__file__))
DIR_IMG = os.path.join(DIR_BASE, "img")
DIR_DATA = os.path.join(DIR_BASE, "data")

# Criar diretórios
os.makedirs(DIR_IMG, exist_ok=True)
os.makedirs(DIR_DATA, exist_ok=True)

# Arquivos
ARQUIVO_RELATORIO = os.path.join(DIR_DATA, "RELATORIO_INVENTARIO.xlsx")
ARQUIVO_BASE_FISCAL = os.path.join(DIR_DATA, "BASE_FISCAL_TOTVS.xlsx")
ARQUIVO_ITENS = os.path.join(DIR_DATA, "itens_cadastrados.xlsx")
ARQUIVO_COLABORADORES = os.path.join(DIR_DATA, "colaboradores.xlsx")
ARQUIVO_HISTORICO = os.path.join(DIR_DATA, "historico_ajustes.xlsx")

# Imagens
IMG_MAIS = os.path.join(DIR_IMG, "+.png")
IMG_SAIDA = os.path.join(DIR_IMG, "saida.png")
IMG_CERTO = os.path.join(DIR_IMG, "certo.png")
IMG_CONFIRMAR = os.path.join(DIR_IMG, "confirmar.png")

# Códigos TOTVS
COD_ENTRADA = "91110017"
COD_SAIDA = "91110018"

# Senhas
SENHA_PROTECAO = "719328fa"
SENHA_ADMIN = "admin123"

# Usuário Windows
USUARIO_WINDOWS = getpass.getuser()

# Tempos de espera (segundos)
TEMPO_CURTO = 0.5
TEMPO_MEDIO = 1
TEMPO_LONGO = 3

print("✅ Configurações carregadas")
print(f"📁 Diretório: {DIR_BASE}")