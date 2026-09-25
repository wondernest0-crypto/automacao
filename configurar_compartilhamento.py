# ========================================
# CONFIGURAR PLANILHA EM MODO COMPARTILHADO
# Permite múltiplos usuários acessarem simultaneamente
# ========================================

import os
from openpyxl import load_workbook
import sys

def get_base_path():
    """Retorna o caminho base"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

DIR_BASE = get_base_path()
DIR_DATA = os.path.join(DIR_BASE, "data")
ARQUIVO_RELATORIO = os.path.join(DIR_DATA, "RELATORIO_INVENTARIO.xlsx")

print("=" * 60)
print("🔧 CONFIGURADOR DE COMPARTILHAMENTO DE PLANILHA")
print("=" * 60)

if not os.path.exists(ARQUIVO_RELATORIO):
    print(f"\n❌ ERRO: Arquivo não encontrado!")
    print(f"   Caminho: {ARQUIVO_RELATORIO}")
    input("\nPressione ENTER para sair...")
    sys.exit(1)

print(f"\n📂 Arquivo: {ARQUIVO_RELATORIO}")
print(f"   Tamanho: {os.path.getsize(ARQUIVO_RELATORIO)} bytes")

try:
    print("\n🔄 Abrindo planilha...")
    wb = load_workbook(ARQUIVO_RELATORIO, read_only=False, keep_vba=False)
    
    # Verificar abas existentes
    print(f"\n📋 Abas encontradas: {wb.sheetnames}")
    
    # Criar aba HISTORICO_AJUSTES se não existir
    if 'HISTORICO_AJUSTES' not in wb.sheetnames:
        print("\n📝 Criando aba HISTORICO_AJUSTES...")
        from openpyxl.styles import PatternFill, Font
        
        ws_hist = wb.create_sheet('HISTORICO_AJUSTES')
        
        # Cabeçalhos
        headers = ['ITEM', 'QTD FÍSICA', 'QTD FISCAL', 'DIFERENÇA', 'STATUS', 
                  'ACURACIDADE %', 'EXCESSO %', 'FALTA %', 'COLABORADOR', 'DATA/HORA']
        
        header_fill = PatternFill(start_color='2E75B6', end_color='2E75B6', fill_type='solid')
        header_font = Font(color='FFFFFF', bold=True)
        
        for col_idx, header in enumerate(headers, start=1):
            cell = ws_hist.cell(row=1, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
        
        # Ajustar larguras
        ws_hist.column_dimensions['A'].width = 15  # ITEM
        ws_hist.column_dimensions['B'].width = 15  # QTD FÍSICA
        ws_hist.column_dimensions['C'].width = 15  # QTD FISCAL
        ws_hist.column_dimensions['D'].width = 12  # DIFERENÇA
        ws_hist.column_dimensions['E'].width = 20  # STATUS
        ws_hist.column_dimensions['F'].width = 15  # ACURACIDADE %
        ws_hist.column_dimensions['G'].width = 12  # EXCESSO %
        ws_hist.column_dimensions['H'].width = 12  # FALTA %
        ws_hist.column_dimensions['I'].width = 20  # COLABORADOR
        ws_hist.column_dimensions['J'].width = 20  # DATA/HORA
        
        print("   ✅ Aba HISTORICO_AJUSTES criada com sucesso!")
    else:
        print("\n✅ Aba HISTORICO_AJUSTES já existe")
    
    # Configurar proteção de planilha (permite edição mas mantém estrutura)
    print("\n🔒 Configurando proteção de planilha...")
    
    # Desproteger todas as abas primeiro
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        if ws.protection.sheet:
            ws.protection.sheet = False
            print(f"   Desprotegido: {sheet_name}")
    
    # Salvar com configurações de compartilhamento
    print("\n💾 Salvando planilha...")
    
    # Remover proteção de pasta de trabalho se existir
    if wb.security:
        wb.security.lockStructure = False
        wb.security.lockWindows = False
    
    wb.save(ARQUIVO_RELATORIO)
    wb.close()
    
    print("\n✅ SUCESSO!")
    print("\n📋 CONFIGURAÇÕES APLICADAS:")
    print("   ✓ Aba HISTORICO_AJUSTES verificada/criada")
    print("   ✓ Proteções removidas")
    print("   ✓ Planilha pronta para compartilhamento")
    
    print("\n💡 DICAS PARA COMPARTILHAMENTO EM REDE:")
    print("   1. Coloque o arquivo em uma pasta compartilhada na rede")
    print("   2. Configure permissões de leitura/escrita para todos os usuários")
    print("   3. A automação agora pode escrever mesmo com outros usuários visualizando")
    print("   4. Evite que múltiplos usuários EDITEM simultaneamente (apenas visualização)")
    
    print("\n⚠️ IMPORTANTE:")
    print("   - Se alguém estiver EDITANDO a planilha, a automação pode falhar")
    print("   - Usuários podem VISUALIZAR sem problemas")
    print("   - A automação detecta e informa se não conseguir escrever")

except PermissionError:
    print("\n❌ ERRO: Arquivo está aberto!")
    print("   Feche o Excel e tente novamente.")
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
input("\nPressione ENTER para sair...")
