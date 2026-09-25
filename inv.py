import os
import time
import pyautogui
import openpyxl
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pygetwindow as gw

# Configurações iniciais
pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True

# Diretório atual do script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# Caminho da planilha e pasta de imagens
PLANILHA_PATH = os.path.join(SCRIPT_DIR, 'Inventario Atual.xlsm')
IMG_DIR = os.path.join(SCRIPT_DIR, 'img')

def minimizar_excel():
    """Minimiza a janela do Excel"""
    try:
        # Tenta encontrar janelas do Excel
        janelas_excel = gw.getWindowsWithTitle('Excel')
        if janelas_excel:
            for janela in janelas_excel:
                if 'Inventario Atual' in janela.title:
                    janela.minimize()
                    print("Janela do Excel minimizada")
                    return True
        # Se não encontrar pelo título, tenta pelo nome do processo
        janelas_excel = gw.getWindowsWithTitle('Inventario Atual')
        if janelas_excel:
            janelas_excel[0].minimize()
            print("Janela do Excel minimizada")
            return True
    except Exception as e:
        print(f"Erro ao minimizar Excel: {str(e)}")
    return False

def encontrar_imagem_variando_confianca(imagem, confianca_inicial=0.9, confianca_final=0.5, passo=0.1, grayscale=True):
    """
    Tenta encontrar uma imagem variando a confiança de confianca_inicial até confianca_final
    """
    confianca_atual = confianca_inicial
    while confianca_atual >= confianca_final:
        print(f"Tentando encontrar imagem {imagem} com confiança: {confianca_atual}")
        try:
            caminho_imagem = os.path.join(IMG_DIR, imagem)
            if not os.path.exists(caminho_imagem):
                print(f"Arquivo de imagem não encontrado: {caminho_imagem}")
                return False
                
            localizacao = pyautogui.locateOnScreen(caminho_imagem, confidence=confianca_atual, grayscale=grayscale)
            if localizacao:
                centro = pyautogui.center(localizacao)
                print(f"Imagem {imagem} encontrada com confiança {confianca_atual}!")
                print(f"Posição: {centro}")
                # Clica no centro da imagem
                pyautogui.click(centro)
                return True
            else:
                print(f"Imagem {imagem} não encontrada com confiança {confianca_atual}")
        except pyautogui.ImageNotFoundException:
            print(f"Imagem {imagem} não encontrada com confiança {confianca_atual}")
        except Exception as e:
            print(f"Erro ao procurar imagem {imagem}: {str(e)}")
        
        # Reduz a confiança
        confianca_atual -= passo
        time.sleep(0.5)  # Espera um pouco entre tentativas
    
    print(f"Imagem {imagem} não encontrada em nenhum nível de confiança testado")
    return False

def encontrar_janela_totvs():
    """
    Estratégia simples para encontrar a janela do TOTVS CE0220
    """
    print("Procurando janela do TOTVS CE0220...")
    
    # Estratégia principal: Procurar pela imagem ce0220.png na tela atual
    print("Procurando pela imagem ce0220.png na tela atual...")
    if encontrar_imagem_variando_confianca('ce0220.png'):
        print("Janela CE0220 encontrada!")
        return True
    
    # Estratégia alternativa: Tentar com pygetwindow
    try:
        janelas = gw.getWindowsWithTitle("CE0220")
        if janelas:
            janela = janelas[0]
            print(f"Janela encontrada pelo título: {janela.title}")
            if janela.isMinimized:
                janela.restore()
            janela.activate()
            time.sleep(1)
            
            # Clicar no centro da janela
            rect = janela.rect
            centro_x = rect.left + (rect.width // 2)
            centro_y = rect.top + (rect.height // 2)
            pyautogui.click(centro_x, centro_y)
            print(f"Clicando no centro da janela: ({centro_x}, {centro_y})")
            return True
    except Exception as e:
        print(f"Erro com pygetwindow: {str(e)}")
    
    print("Não foi possível encontrar a janela do TOTVS")
    return False

def preencher_lote(lote_base):
    """Formata o lote com a data atual no formato DDMMYYYY"""
    data_atual = datetime.now()
    data_formatada = data_atual.strftime('%d%m%Y')
    return f"{lote_base.upper()}{data_formatada}"  # Garantir que o lote base seja maiúsculo

def calcular_vencimento(data_lote_str):
    """Calcula a data de vencimento (6 meses após)"""
    try:
        data_lote = datetime.strptime(data_lote_str, '%d%m%Y')
        vencimento = data_lote + relativedelta(months=+6)
        return vencimento.strftime('%d%m%Y')
    except Exception as e:
        print(f"Erro ao calcular vencimento: {str(e)}")
        return None

def tratar_erro_vencimento():
    """
    Trata o erro de vencimento já existente
    """
    print("Detectado erro de vencimento já existente. Tratando...")
    
    # Clicar no botão OK
    if not encontrar_imagem_variando_confianca('ok.png'):
        print("Não foi possível encontrar o botão OK")
        return False
    
    # Digitar data atual
    data_atual = datetime.now().strftime('%d%m%Y')
    print(f"Digitando data atual: {data_atual}")
    pyautogui.write(data_atual)
    
    # Pressionar TAB 4 vezes
    print("Pressionar TAB 4 vezes...")
    for i in range(4):
        pyautogui.press('tab')
        print(f"TAB {i+1}/4")
        time.sleep(0.2)
    
    # Digitar código contábil
    print("Digitando código contábil...")
    pyautogui.write('91110017')
    
    # APERTAR TAB 1 VEZ
    print("Apertando TAB 1 vez...")
    pyautogui.press('tab')
    
    return True

def verificar_conclusao_operacao():
    """
    Verifica se a operação foi concluída com sucesso
    """
    print("Verificando se a operação foi concluída com sucesso...")
    
    # Estratégia 1: Verificar se o popup de confirmação fechou
    tempo_maximo = 15  # segundos
    tempo_inicial = time.time()
    
    while time.time() - tempo_inicial < tempo_maximo:
        try:
            # Tenta encontrar a imagem SIM.png - se não encontrar, o popup fechou
            localizacao = pyautogui.locateOnScreen(os.path.join(IMG_DIR, 'SIM.png'), confidence=0.7)
            if not localizacao:
                print("Popup de confirmação fechado! Operação concluída.")
                return True
        except:
            # Se não encontrar, significa que o popup fechou
            print("Popup de confirmação fechado! Operação concluída.")
            return True
        
        time.sleep(0.5)
    
    print("Timeout ao verificar conclusão da operação")
    return False

def main():
    try:
        print("Iniciando automação...")
        
        # 1. Abrir planilha
        if not os.path.exists(PLANILHA_PATH):
            pyautogui.alert(f"Planilha não encontrada: {PLANILHA_PATH}")
            return
            
        print("Abrindo planilha...")
        os.startfile(PLANILHA_PATH)
        time.sleep(5)
        
        # Clicar em "Habilitar Conteúdo"
        print("Procurando botão 'Habilitar Conteúdo'...")
        encontrar_imagem_variando_confianca('habilitar_conteudo.png')
        
        # Carregar planilha
        print("Carregando dados da planilha...")
        time.sleep(3)
        workbook = openpyxl.load_workbook(PLANILHA_PATH, read_only=True, data_only=True)
        sheet = workbook.active
        
        # Minimizar a janela do Excel
        print("Minimizando janela do Excel...")
        minimizar_excel()
        time.sleep(1)
        
        # 2. Processar cada linha da planilha
        print("Iniciando processamento dos dados...")
        total_registros = 0
        
        for row in range(2, sheet.max_row + 1):
            # Obter valores da planilha e converter para maiúsculas
            item = str(sheet[f'A{row}'].value).upper() if sheet[f'A{row}'].value else None
            quantidade = str(sheet[f'B{row}'].value).upper() if sheet[f'B{row}'].value else None
            lote_base = str(sheet[f'C{row}'].value).upper() if sheet[f'C{row}'].value else None
            
            if not item or not quantidade or not lote_base:
                print(f"Linha {row} sem dados. Encerrando processamento.")
                break
                
            total_registros += 1
            print(f"\nProcessando linha {row}: Item={item}, Qtd={quantidade}, Lote={lote_base}")
            
            # ENCONTRAR JANELA DO TOTVS
            print("Procurando janela do TOTVS...")
            if not encontrar_janela_totvs():
                pyautogui.alert("Não foi possível encontrar a janela do TOTVS CE0220")
                return
                
            # Clicar no botão +
            print("Procurando botão +...")
            if not encontrar_imagem_variando_confianca('+.png'):
                pyautogui.alert("Não foi possível encontrar o botão +")
                return
                
            # Preencher campo do item (em maiúsculas)
            print("Procurando campo item...")
            if not encontrar_imagem_variando_confianca('item.png'):
                pyautogui.alert("Não foi possível encontrar o campo item")
                return
            pyautogui.write(item.upper())  # GARANTIR LETRAS MAIÚSCULAS
            pyautogui.press('tab')
            
            # Preencher APA (em maiúsculas)
            pyautogui.write('APA'.upper())
            pyautogui.press('tab')
            
            # Preencher lote (em maiúsculas)
            lote_completo = preencher_lote(lote_base.upper())  # GARANTIR LETRAS MAIÚSCULAS
            print(f"Lote completo: {lote_completo}")
            pyautogui.write(lote_completo.upper())  # GARANTIR LETRAS MAIÚSCULAS
            pyautogui.press('tab')
            
            # Calcular e preencher vencimento
            data_lote = lote_completo[-8:]
            vencimento = calcular_vencimento(data_lote)
            if vencimento:
                print(f"Vencimento calculado: {vencimento}")
                pyautogui.write(vencimento)
            else:
                pyautogui.alert("Erro ao calcular vencimento")
                return
            
            # Pressionar TAB 5 vezes após digitar a validade
            print("Pressionar TAB 5 vezes após a validade...")
            for i in range(5):
                pyautogui.press('tab')
                print(f"TAB {i+1}/5")
                time.sleep(0.2)
            
            # Preencher conta contábil
            pyautogui.write('91110017')
            pyautogui.press('tab')
            
            # Preencher quantidade (em maiúsculas)
            print("Procurando campo valores...")
            if not encontrar_imagem_variando_confianca('valores.png'):
                pyautogui.alert("Não foi possível encontrar o campo valores")
                return
            pyautogui.write(quantidade.upper())  # GARANTIR LETRAS MAIÚSCULAS
            
            # Confirmar operação
            print("Procurando botão certo...")
            if not encontrar_imagem_variando_confianca('certo.png'):
                pyautogui.alert("Não foi possível confirmar a operação")
                return
            
            # Aguardar um pouco antes de procurar o SIM
            time.sleep(1)
            
            print("Procurando botão SIM...")
            if not encontrar_imagem_variando_confianca('SIM.png'):
                pyautogui.alert("Não foi possível confirmar no popup final")
                return
                
            # Verificar se apareceu o erro de vencimento
            time.sleep(1)  # Esperar um pouco para o erro aparecer
            print("Verificando se apareceu erro de vencimento...")
            if encontrar_imagem_variando_confianca('vencimento.png', confianca_inicial=0.9, confianca_final=0.7):
                print("Erro de vencimento detectado! Tratando...")
                if not tratar_erro_vencimento():
                    pyautogui.alert("Erro ao tratar o vencimento")
                    return
                
                # Confirmar operação novamente após tratar o erro
                print("Procurando botão certo novamente...")
                if not encontrar_imagem_variando_confianca('certo.png'):
                    pyautogui.alert("Não foi possível confirmar a operação após tratar o erro")
                    return
                
                # Aguardar um pouco antes de procurar o SIM
                time.sleep(1)
                
                print("Procurando botão SIM novamente...")
                if not encontrar_imagem_variando_confianca('SIM.png'):
                    pyautogui.alert("Não foi possível confirmar no popup final após tratar o erro")
                    return
                
            # VERIFICAR SE A OPERAÇÃO FOI CONCLUÍDA COM SUCESSO
            print("Verificando conclusão da operação...")
            time.sleep(1)  # Espera inicial
            
            if verificar_conclusao_operacao():
                print("Operação concluída com sucesso!")
            else:
                print("Não foi possível confirmar a conclusão da operação, mas continuando...")
            
            # Espera adicional para garantir que a janela esteja pronta para o próximo item
            print("Preparando para o próximo item...")
            time.sleep(3)  # Aumentei o tempo de espera
                
            print(f"Linha {row} processada com sucesso!")
            
        # 3. Mensagem final
        if total_registros > 0:
            pyautogui.alert(f"Processamento concluído! {total_registros} registros inseridos.")
        else:
            pyautogui.alert("Nenhum registro processado. Verifique a planilha.")
        
    except Exception as e:
        print(f"Ocorreu um erro: {str(e)}")
        pyautogui.alert(f"Erro na automação: {str(e)}")
    finally:
        if 'workbook' in locals():
            workbook.close()
        print("Automação finalizada.")

if __name__ == "__main__":
    main()