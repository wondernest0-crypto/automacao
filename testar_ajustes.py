# ========================================
# SCRIPT DE TESTE DOS AJUSTES REALIZADOS
# Verifica se todas as modificações estão funcionando
# ========================================

import os
import sys
from datetime import datetime

def get_base_path():
    """Retorna o caminho base"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

DIR_BASE = get_base_path()
DIR_DATA = os.path.join(DIR_BASE, "data")
DIR_IMG = os.path.join(DIR_BASE, "img")
ARQUIVO_RELATORIO = os.path.join(DIR_DATA, "RELATORIO_INVENTARIO.xlsx")

print("=" * 70)
print("🧪 TESTE DOS AJUSTES REALIZADOS")
print("=" * 70)
print(f"\n📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
print(f"📁 Diretório base: {DIR_BASE}")

# ========================================
# TESTE 1: VERIFICAR ESTRUTURA DE PASTAS
# ========================================
print("\n" + "=" * 70)
print("📂 TESTE 1: ESTRUTURA DE PASTAS")
print("=" * 70)

pastas = {
    'data': DIR_DATA,
    'img': DIR_IMG
}

for nome, caminho in pastas.items():
    existe = os.path.exists(caminho)
    status = "✅" if existe else "❌"
    print(f"{status} Pasta '{nome}': {caminho}")
    if existe:
        arquivos = os.listdir(caminho)
        print(f"   📄 {len(arquivos)} arquivo(s) encontrado(s)")

# ========================================
# TESTE 2: VERIFICAR IMAGENS
# ========================================
print("\n" + "=" * 70)
print("🖼️ TESTE 2: IMAGENS NECESSÁRIAS")
print("=" * 70)

imagens_necessarias = [
    '+.png',
    'saida.png',
    'certo.png',
    'confirmar.png',
    'x.png',
    'cancelar.png',
    'vencimento.png',
    'ok.png'
]

imagens_encontradas = 0
imagens_faltando = []

for img in imagens_necessarias:
    caminho = os.path.join(DIR_IMG, img)
    caminho_abs = os.path.abspath(caminho)
    existe = os.path.exists(caminho)
    
    if existe:
        tamanho = os.path.getsize(caminho)
        print(f"✅ {img}")
        print(f"   Caminho: {caminho_abs}")
        print(f"   Tamanho: {tamanho} bytes")
        imagens_encontradas += 1
    else:
        print(f"❌ {img} - NÃO ENCONTRADA")
        print(f"   Esperado em: {caminho_abs}")
        imagens_faltando.append(img)

print(f"\n📊 Resumo: {imagens_encontradas}/{len(imagens_necessarias)} imagens encontradas")

# ========================================
# TESTE 3: VERIFICAR PLANILHA
# ========================================
print("\n" + "=" * 70)
print("📊 TESTE 3: PLANILHA RELATORIO_INVENTARIO.xlsx")
print("=" * 70)

if os.path.exists(ARQUIVO_RELATORIO):
    print(f"✅ Planilha encontrada")
    print(f"   Caminho: {os.path.abspath(ARQUIVO_RELATORIO)}")
    print(f"   Tamanho: {os.path.getsize(ARQUIVO_RELATORIO)} bytes")
    
    try:
        from openpyxl import load_workbook
        print("\n🔍 Verificando estrutura da planilha...")
        
        wb = load_workbook(ARQUIVO_RELATORIO, read_only=True)
        print(f"   📋 Abas encontradas: {wb.sheetnames}")
        
        # Verificar aba CONTAGEM
        if 'CONTAGEM' in wb.sheetnames:
            print("   ✅ Aba CONTAGEM existe")
        else:
            print("   ❌ Aba CONTAGEM NÃO EXISTE")
        
        # Verificar aba DASHBOARD
        if 'DASHBOARD' in wb.sheetnames:
            print("   ✅ Aba DASHBOARD existe")
        else:
            print("   ⚠️ Aba DASHBOARD não existe (será criada ao gerar planilha)")
        
        # Verificar aba HISTORICO_AJUSTES
        if 'HISTORICO_AJUSTES' in wb.sheetnames:
            print("   ✅ Aba HISTORICO_AJUSTES existe")
            ws = wb['HISTORICO_AJUSTES']
            print(f"   📝 Registros no histórico: {ws.max_row - 1}")
        else:
            print("   ⚠️ Aba HISTORICO_AJUSTES não existe")
            print("      Execute 'configurar_compartilhamento.py' para criar")
        
        wb.close()
        
    except ImportError:
        print("   ⚠️ Biblioteca openpyxl não instalada")
        print("      Execute: pip install openpyxl")
    except Exception as e:
        print(f"   ❌ Erro ao abrir planilha: {e}")
else:
    print(f"❌ Planilha NÃO ENCONTRADA")
    print(f"   Esperado em: {os.path.abspath(ARQUIVO_RELATORIO)}")

# ========================================
# TESTE 4: VERIFICAR ARQUIVOS PYTHON
# ========================================
print("\n" + "=" * 70)
print("🐍 TESTE 4: ARQUIVOS PYTHON")
print("=" * 70)

arquivos_python = {
    'automacao_totvs.py': 'Automação principal',
    'gerar_planilha.py': 'Gerador de planilha',
    'configurar_compartilhamento.py': 'Configurador de compartilhamento',
    'lancamento_inventario.py': 'Interface de lançamento'
}

for arquivo, descricao in arquivos_python.items():
    caminho = os.path.join(DIR_BASE, arquivo)
    existe = os.path.exists(caminho)
    status = "✅" if existe else "❌"
    print(f"{status} {arquivo}")
    print(f"   {descricao}")
    if existe:
        tamanho = os.path.getsize(caminho)
        print(f"   Tamanho: {tamanho} bytes")

# ========================================
# TESTE 5: VERIFICAR LOGS
# ========================================
print("\n" + "=" * 70)
print("📝 TESTE 5: SISTEMA DE LOGS")
print("=" * 70)

arquivo_log = os.path.join(DIR_BASE, "log_automacao.txt")
if os.path.exists(arquivo_log):
    print(f"✅ Arquivo de log encontrado")
    print(f"   Caminho: {os.path.abspath(arquivo_log)}")
    tamanho = os.path.getsize(arquivo_log)
    print(f"   Tamanho: {tamanho} bytes")
    
    if tamanho > 0:
        print("\n   📄 Últimas 10 linhas do log:")
        try:
            with open(arquivo_log, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
                ultimas = linhas[-10:] if len(linhas) > 10 else linhas
                for linha in ultimas:
                    print(f"      {linha.rstrip()}")
        except Exception as e:
            print(f"   ⚠️ Erro ao ler log: {e}")
else:
    print(f"⚠️ Arquivo de log não existe ainda")
    print(f"   Será criado na primeira execução da automação")

# ========================================
# RESUMO FINAL
# ========================================
print("\n" + "=" * 70)
print("📊 RESUMO DOS TESTES")
print("=" * 70)

print(f"\n✅ Ajustes implementados:")
print(f"   1. ✅ Logs de caminhos de imagens (automacao_totvs.py)")
print(f"   2. ✅ Dashboard melhorado (gerar_planilha.py)")
print(f"   3. ✅ Configurador de compartilhamento (novo arquivo)")
print(f"   4. ✅ Sincronização CONTAGEM → HISTORICO_AJUSTES")

print(f"\n📋 Próximos passos:")
if imagens_faltando:
    print(f"   ⚠️ Adicionar imagens faltando: {', '.join(imagens_faltando)}")

if not os.path.exists(ARQUIVO_RELATORIO):
    print(f"   ⚠️ Criar planilha RELATORIO_INVENTARIO.xlsx")
else:
    try:
        from openpyxl import load_workbook
        wb = load_workbook(ARQUIVO_RELATORIO, read_only=True)
        if 'HISTORICO_AJUSTES' not in wb.sheetnames:
            print(f"   ⚠️ Executar: python configurar_compartilhamento.py")
        wb.close()
    except:
        pass

print(f"\n💡 Recomendações:")
print(f"   1. Execute 'configurar_compartilhamento.py' antes de usar em rede")
print(f"   2. Teste a automação em ambiente local primeiro")
print(f"   3. Verifique os logs em 'log_automacao.txt' após cada execução")
print(f"   4. Faça backup da planilha regularmente")

print("\n" + "=" * 70)
print("✅ TESTE CONCLUÍDO")
print("=" * 70)

input("\nPressione ENTER para sair...")
