# ========================================
# AUTOMAÇÃO TOTVS - AJUSTE DE ESTOQUE
# Desenvolvido por: Deivid - Faturamento
# ========================================

import pyautogui
import pygetwindow as gw
import pyperclip
import pandas as pd
import time
import os
import glob
import subprocess
import sys
from datetime import datetime
import getpass
import traceback

# ========================================
# SELENIUM - PARA ABRIR TOTVS VIA NAVEGADOR
# ========================================
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ========================================
# ⭐ ADICIONE AQUI ⭐
# CORRIGIR ÍCONE NA BARRA DE TAREFAS (WINDOWS)
# ========================================
try:
    import ctypes
    myappid = 'deivid.automacao.totvs.v2.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# ========================================
# DETECTAR SE ESTÁ RODANDO COMO .EXE OU .PY
# ========================================
def get_base_path():
    """Retorna o caminho base, seja rodando como .py ou .exe"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

DIR_BASE = get_base_path()
DIR_IMG = os.path.join(DIR_BASE, "img")
DIR_DATA = os.path.join(DIR_BASE, "data")
DIR_ASSETS = os.path.join(DIR_BASE, "assets")

os.makedirs(DIR_IMG, exist_ok=True)
os.makedirs(DIR_DATA, exist_ok=True)
os.makedirs(DIR_ASSETS, exist_ok=True)

ARQUIVO_RELATORIO = os.path.join(DIR_DATA, "RELATORIO_INVENTARIO.xlsx")
ARQUIVO_BASE_FISCAL = os.path.join(DIR_DATA, "BASE_FISCAL_TOTVS.xlsx")
ARQUIVO_HISTORICO = os.path.join(DIR_DATA, "historico_ajustes.xlsx")
ARQUIVO_LOG = os.path.join(DIR_BASE, "log_automacao.txt")

IMG_MAIS = os.path.join(DIR_IMG, "+.png")
IMG_SAIDA = os.path.join(DIR_IMG, "saida.png")
IMG_CERTO = os.path.join(DIR_IMG, "certo.png")
IMG_CONFIRMAR = os.path.join(DIR_IMG, "confirmar.png")
IMG_FECHAR = os.path.join(DIR_IMG, "x.png")
IMG_CANCELAR = os.path.join(DIR_IMG, "cancelar.png")
IMG_VENCIMENTO = os.path.join(DIR_IMG, "vencimento.png")
IMG_OK = os.path.join(DIR_IMG, "ok.png")

COD_ENTRADA = "91110017"
COD_SAIDA = "91110018"

# ========================================
# CONFIGURAÇÕES TOTVS WEB
# ========================================
TOTVS_URL = "http://192.168.2.6:8080/totvs-login/loginForm"
TOTVS_LOGIN = "expedicao"
TOTVS_SENHA = "123mudar@"
# Driver do Edge - coloque msedgedriver.exe na mesma pasta do script
EDGE_DRIVER_PATH = os.path.join(DIR_BASE, "msedgedriver.exe")

TEMPO_CURTO = 2
TEMPO_MEDIO = 3
TEMPO_LONGO = 6

# ========================================
# CONFIGURAÇÕES - IMPORTAÇÃO DE PEDIDO (HONDA & GM)
# ========================================
# Programa TOTVS aberto pelo atalho do lançador
PROGRAMA_IMPORTACAO = "ESPD0001"

# Atalho que abre o lançador de programas no TOTVS.
# OBS: você pediu CTRL+X. A automação de inventário existente usa
#      CTRL+ALT+X para o mesmo lançador. Se o lançador não abrir,
#      troque para ('ctrl', 'alt', 'x').
ATALHO_ABRIR_PROGRAMA = ('ctrl', 'x')

# Diretório de origem dos pedidos (GM)
DIRETORIO_IMPORTACAO_GM = "\\\\192.168.0.9\\s\\Sawluz\\swedi\\OUTPUT\\GM\\"

# Quantas vezes repetir a sequência (TAB, ENTER) após abrir o programa
QTD_TAB_ENTER = 5

# Tempo máximo (segundos) aguardando a janela "DATASUL Interative" aparecer
TEMPO_ESPERA_DATASUL = 47

# Tempo (segundos) aguardando o programa ESPD0001 carregar
TEMPO_ESPERA_PROGRAMA = 6

USUARIO_WINDOWS = getpass.getuser()

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3


class AutomacaoTOTVS:
    def __init__(self):
        self.arquivo_log = ARQUIVO_LOG
        self.iniciar_log()
        
        self.log("=" * 60)
        self.log("🤖 AUTOMAÇÃO TOTVS - AJUSTE DE ESTOQUE")
        self.log("=" * 60)
        self.log(f"📁 Diretório: {DIR_BASE}")
        self.log(f"👤 Usuário: {USUARIO_WINDOWS}")
        
        self.itens_pendentes = []
        self.itens_processados = []
        self.item_atual = None
        self.qtd_fisica_atual = 0
        self.colaborador_atual = ''
        self.linha_excel_atual = None
        self.lotes_encontrados = []
        self.qtd_mv_retirada = 0
        self.primeiro_item = True
        self.total_itens_processar = 0
        self._driver_login = None  # driver do Edge usado no login (fechar ao terminar)
    
    # ========================================
    # SISTEMA DE LOG EM ARQUIVO
    # ========================================
    
    def iniciar_log(self):
        try:
            with open(self.arquivo_log, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("🤖 AUTOMAÇÃO TOTVS - LOG DETALHADO\n")
                f.write(f"Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Diretório: {DIR_BASE}\n")
                f.write(f"Usuário: {USUARIO_WINDOWS}\n")
                f.write("=" * 60 + "\n\n")
        except Exception as e:
            print(f"Erro ao criar log: {e}")
    
    def log(self, msg):
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        linha = f"[{timestamp}] {msg}"
        print(linha)
        try:
            with open(self.arquivo_log, 'a', encoding='utf-8') as f:
                f.write(linha + '\n')
        except:
            pass
    
    def log_debug(self, msg):
        self.log(f"🔍 DEBUG: {msg}")
    
    def log_sucesso(self, msg):
        self.log(f"✅ SUCESSO: {msg}")
    
    def log_erro(self, msg):
        self.log(f"❌ ERRO: {msg}")
    
    def log_aviso(self, msg):
        self.log(f"⚠️ AVISO: {msg}")
    
    # ========================================
    # FUNÇÕES AUXILIARES
    # ========================================
    
    def esperar(self, seg):
        time.sleep(seg)
    
    def minimizar_todas_janelas(self):
        self.log("🔽 Minimizando todas as janelas...")
        try:
            pyautogui.hotkey('win', 'd')
            self.esperar(1)
            self.log_sucesso("Todas as janelas minimizadas")
        except Exception as e:
            self.log_erro(f"Erro ao minimizar: {e}")
    
    def encontrar_janela(self, titulo):
        try:
            todas = gw.getAllWindows()
            for j in todas:
                if titulo.lower() in j.title.lower():
                    return j
        except:
            pass
        return None
    
    def trazer_frente(self, janela):
        try:
            if janela.isMinimized:
                janela.restore()
            janela.activate()
            self.esperar(0.5)
            return True
        except Exception as e:
            self.log_erro(f"Erro ao trazer janela: {e}")
            return False
    
    def fechar_janela(self, titulo):
        try:
            janela = self.encontrar_janela(titulo)
            if janela:
                self.trazer_frente(janela)
                self.esperar(0.3)
                pyautogui.hotkey('alt', 'F4')
                self.esperar(0.5)
                pyautogui.press('n')
                self.esperar(0.3)
                self.log_sucesso(f"Janela {titulo} fechada")
                return True
        except Exception as e:
            self.log_erro(f"Erro ao fechar janela: {e}")
        return False
        
    # ========================================
    # ABRIR TOTVS VIA NAVEGADOR
    # ========================================
    def abrir_totvs_navegador(self):
        """Abre TOTVS pelo navegador Edge, faz login e aguarda a janela DATASUL."""
        self.log("\n🌐 ABRINDO TOTVS VIA NAVEGADOR...")

        if not self._login_totvs_navegador():
            return False

        # Aguardar TOTVS Desktop abrir
        self.log("   >> Aguardando TOTVS Desktop iniciar (30 seg max)...")
        for i in range(30):
            time.sleep(1)
            janela_datasul = self.encontrar_janela("DATASUL")
            if janela_datasul:
                self.log_sucesso("DATASUL aberto com sucesso!")
                self._fechar_driver_login()
                return True

        self.log_aviso("TOTVS não abriu no tempo esperado")
        self._fechar_driver_login()
        return False

    def _login_totvs_navegador(self):
        """Abre o Edge, acessa o TOTVS, preenche login/senha, clica em Entrar
        e trata o popup 'Abrir aplicativo'. NÃO aguarda a janela DATASUL.
        Guarda o driver em self._driver_login (feche com _fechar_driver_login)."""
        try:
            # Configurar Edge
            edge_options = EdgeOptions()
            edge_options.add_argument("--start-maximized")
            edge_options.add_argument("--disable-notifications")
            
            # ========================================
            # USAR DRIVER LOCAL
            # ========================================
            driver_local = os.path.join(DIR_BASE, "msedgedriver.exe")
            
            self.log(f"   >> Driver: {driver_local}")
            
            if not os.path.exists(driver_local):
                self.log_erro(f"Driver não encontrado: {driver_local}")
                return False
            
            self.log("   >> Iniciando Edge...")
            service = EdgeService(executable_path=driver_local)
            driver = webdriver.Edge(service=service, options=edge_options)
            self._driver_login = driver
            self.log_sucesso("Edge iniciado!")
            
            self.log(f"   >> Acessando: {TOTVS_URL}")
            driver.get(TOTVS_URL)
            
            # Aguardar página carregar
            self.log("   >> Aguardando página carregar...")
            wait = WebDriverWait(driver, 15)
            
            # PASSO 1: Preencher LOGIN
            self.log(f"   >> Preenchendo login: {TOTVS_LOGIN}")
            campo_login = wait.until(
                EC.presence_of_element_located((By.ID, "txtUsername"))
            )
            campo_login.clear()
            campo_login.send_keys(TOTVS_LOGIN)
            
            # PASSO 2: Preencher SENHA
            self.log("   >> Preenchendo senha...")
            campo_senha = driver.find_element(By.ID, "txtPassword")
            campo_senha.clear()
            campo_senha.send_keys(TOTVS_SENHA)
            
            # PASSO 3: Clicar em ENTRAR
            self.log("   >> Clicando em 'Entrar'...")
            btn_entrar = driver.find_element(By.ID, "btnEntrar")
            btn_entrar.click()
            
            # PASSO 4: Aguardar carregamento
            self.log("   >> Aguardando 10 segundos para carregar...")
            time.sleep(10)
            
            # PASSO 5: Lidar com popup do Windows
            self.log("   >> Verificando popup 'Abrir aplicativo'...")
            popup_tratado = self.tratar_popup_abrir_aplicativo()
            
            if popup_tratado:
                self.log_sucesso("Popup tratado! Aguardando TOTVS abrir...")
            else:
                self.log_aviso("Popup não detectado, continuando...")

            return True

        except TimeoutException:
            self.log_erro("Timeout ao carregar página de login!")
            return False
        except NoSuchElementException as e:
            self.log_erro(f"Elemento não encontrado: {e}")
            return False
        except Exception as e:
            self.log_erro(f"Erro ao abrir TOTVS via navegador: {e}")
            traceback.print_exc()
            return False

    def _fechar_driver_login(self):
        """Fecha o driver do Edge usado no login (se existir)."""
        try:
            driver = getattr(self, '_driver_login', None)
            if driver:
                driver.quit()
        except Exception:
            pass
        self._driver_login = None

    def tratar_popup_abrir_aplicativo(self):
        """
        Trata o popup do Windows 'deseja abrir este aplicativo'
        """
        self.log("   >> Tentando tratar popup 'Abrir aplicativo'...")
        
        # MÉTODO 1: Tentar clicar em imagem do botão "Abrir"
        img_abrir = os.path.join(DIR_IMG, "abrir_popup.png")
        if os.path.exists(img_abrir):
            self.log("   >> Procurando imagem do botão 'Abrir'...")
            for tentativa in range(5):
                pos = self.encontrar_imagem(img_abrir, conf_inicial=0.8)
                if pos:
                    pyautogui.click(pos)
                    self.log_sucesso("Clicou no botão 'Abrir' via imagem!")
                    return True
                time.sleep(1)
        
        # MÉTODO 2: Tentar atalhos de teclado
        self.log("   >> Tentando atalhos de teclado...")
        
        # Aguardar popup aparecer
        time.sleep(2)
        
        # Tentar Alt+A (atalho comum para "Abrir")
        self.log("   >> Tentando Alt+A...")
        pyautogui.hotkey('alt', 'a')
        time.sleep(1)
        
        # Verificar se funcionou
        janela_datasul = self.encontrar_janela("DATASUL")
        if janela_datasul:
            return True
        
        # Tentar Enter (se o botão Abrir já estiver focado)
        self.log("   >> Tentando Enter...")
        pyautogui.press('enter')
        time.sleep(1)
        
        # MÉTODO 3: Tentar Tab + Enter para navegar até o botão
        self.log("   >> Tentando Tab + Enter...")
        pyautogui.press('tab')
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(1)
        
        return False
        
    # ========================================
    # PREPARAR TOTVS
    # ========================================
    
    def preparar_totvs(self):
        self.log("\n📋 PREPARANDO TOTVS...")
        
        self.minimizar_todas_janelas()
        
        # VERIFICAÇÃO 1: CE0220 já está aberto?
        self.log("🔍 Procurando CE0220...")
        janela = self.encontrar_janela("CE0220")
        
        if janela:
            self.log_sucesso("CE0220 encontrado!")
            self.trazer_frente(janela)
            self.esperar(TEMPO_LONGO)
            
            self.log("   >> Clicando em x.png para limpar...")
            if self.clicar_imagem(IMG_FECHAR):
                self.esperar(TEMPO_MEDIO)
                self.log_sucesso("Tela limpa!")
            else:
                self.log_aviso("x.png não encontrado, continuando...")
            
            return True
        
        self.log_aviso("CE0220 não está aberto")
        
        # VERIFICAÇÃO 2: DATASUL interactive está aberto?
        self.log("🔍 Procurando 'DATASUL interactive'...")
        janela = self.encontrar_janela("DATASUL interactive")
        
        if not janela:
            self.log("🔍 Procurando 'DATASUL'...")
            janela = self.encontrar_janela("DATASUL")
        
        # ========================================
        # 🌐 SE NÃO ENCONTRAR DATASUL, ABRIR VIA NAVEGADOR
        # ========================================
        if not janela:
            self.log_aviso("⚠️ DATASUL não encontrado!")
            self.log("🌐 Iniciando abertura via navegador Edge...")
            
            if not self.abrir_totvs_navegador():
                self.log_erro("❌ Falha ao abrir TOTVS via navegador!")
                return False
            
            # ========================================
            # ⏳ AGUARDAR 10 SEGUNDOS APÓS TOTVS ABRIR
            # ========================================
            self.log("   >> Aguardando 10 segundos para TOTVS estabilizar...")
            self.esperar(45)
            
            janela = self.encontrar_janela("DATASUL")
            if not janela:
                self.log_erro("DATASUL ainda não disponível após login!")
                return False
        
        self.log_sucesso("DATASUL encontrado!")
        self.trazer_frente(janela)
        
        # ========================================
        # ⏳ AGUARDAR MAIS 5 SEGUNDOS ANTES DE DIGITAR
        # ========================================
        self.log("   >> Aguardando 5 segundos antes de abrir CE0220...")
        self.esperar(5)
        
        self.log("⌨️ CTRL+ALT+X...")
        pyautogui.hotkey('ctrl', 'alt', 'x')
        self.esperar(TEMPO_MEDIO)
        
        self.log("⌨️ CE0220 + Enter...")
        pyautogui.typewrite('CE0220', interval=0.05)
        pyautogui.press('enter')
        self.esperar(TEMPO_LONGO)
        
        self.log("   >> Aguardando CE0220 carregar...")
        self.esperar(3)
        
        self.log("   >> Clicando em x.png para limpar...")
        if self.clicar_imagem(IMG_FECHAR):
            self.esperar(TEMPO_MEDIO)
            self.log_sucesso("Tela limpa!")
        else:
            self.log_aviso("x.png não encontrado, continuando...")
        
        self.log_sucesso("CE0220 aberto e pronto!")
        return True
    
    # ========================================
    # FUNÇÕES DE IMAGEM
    # ========================================
    
    def encontrar_imagem(self, caminho, conf_inicial=0.9, conf_min=0.3):
        # LOG DO CAMINHO DA IMAGEM
        caminho_absoluto = os.path.abspath(caminho)
        self.log_debug(f"🖼️ Procurando imagem: {os.path.basename(caminho)}")
        self.log_debug(f"   Caminho completo: {caminho_absoluto}")
        self.log_debug(f"   Existe: {os.path.exists(caminho)}")
        
        if not os.path.exists(caminho):
            self.log_aviso(f"Imagem não existe: {caminho}")
            self.log_aviso(f"Caminho absoluto: {caminho_absoluto}")
            return None
        
        conf = conf_inicial
        while conf >= conf_min:
            try:
                loc = pyautogui.locateOnScreen(caminho, confidence=conf)
                if loc:
                    self.log_debug(f"   ✅ Encontrada com confiança: {conf:.1f}")
                    return pyautogui.center(loc)
            except:
                pass
            conf -= 0.1
        
        self.log_debug(f"   ❌ Não encontrada (testado de {conf_inicial} até {conf_min})")
        return None
    
    def encontrar_imagem_exata(self, caminho, confianca=0.95):
        # LOG DO CAMINHO DA IMAGEM
        caminho_absoluto = os.path.abspath(caminho)
        self.log_debug(f"🖼️ Procurando imagem EXATA: {os.path.basename(caminho)}")
        self.log_debug(f"   Caminho completo: {caminho_absoluto}")
        self.log_debug(f"   Existe: {os.path.exists(caminho)}")
        
        if not os.path.exists(caminho):
            self.log_aviso(f"Imagem não existe: {caminho}")
            self.log_aviso(f"Caminho absoluto: {caminho_absoluto}")
            return None
        
        try:
            loc = pyautogui.locateOnScreen(
                caminho, 
                confidence=confianca,
                grayscale=False
            )
            if loc:
                self.log_debug(f"✅ Imagem EXATA encontrada ({confianca*100:.0f}%): {os.path.basename(caminho)}")
                return pyautogui.center(loc)
        except Exception as e:
            self.log_debug(f"Detecção exata - não encontrado ou erro: {e}")
        
        self.log_debug(f"   ❌ Não encontrada")
        return None
    
    def clicar_imagem(self, caminho, esperar_depois=True):
        pos = self.encontrar_imagem(caminho)
        if pos:
            pyautogui.click(pos)
            if esperar_depois:
                self.esperar(TEMPO_CURTO)
            return True
        self.log_aviso(f"Imagem não encontrada: {os.path.basename(caminho)}")
        return False
    
    # ========================================
    # VERIFICAR POPUP DE VENCIMENTO
    # ========================================
    
    def verificar_popup_vencimento(self, tipo_operacao='entrada', quantidade=None):
        """Verifica e trata popup de vencimento APÓS confirmar.png ter sido clicado"""
        self.log("   >> Aguardando 5 segundos para verificar popup de vencimento...")
        self.esperar(5)
        
        self.log("   >> Verificando popup de vencimento (DETECÇÃO PRECISA)...")
        
        pos_vencimento = self.encontrar_imagem_exata(IMG_VENCIMENTO, confianca=0.95)
        
        if not pos_vencimento:
            self.esperar(0.3)
            pos_vencimento = self.encontrar_imagem_exata(IMG_VENCIMENTO, confianca=0.92)
        
        if pos_vencimento:
            self.log_aviso("⚠️ POPUP DE VENCIMENTO DETECTADO!")
            
            # ✅ Vai direto para ok.png (sem confirmar.png antes)
            self.log("   >> Clicando em ok.png...")
            if self.clicar_imagem(IMG_OK):
                self.esperar(TEMPO_MEDIO)
            else:
                self.log_aviso("ok.png não encontrado, tentando Enter...")
                self.enter()
                self.esperar(TEMPO_MEDIO)
            
            data_atual = datetime.now().strftime("%d%m%Y")
            self.log(f"   >> Digitando data atual: {data_atual}")
            self.digitar(data_atual)
            self.esperar(0.3)
            
            self.log("   >> 4x TAB")
            self.tab(4)
            
            self.log("   >> Retomando lógica normal...")
            
            if tipo_operacao == 'entrada':
                self.log(f"   >> Código: {COD_ENTRADA}")
                self.digitar(COD_ENTRADA)
            else:
                self.log(f"   >> Código: {COD_SAIDA}")
                self.digitar(COD_SAIDA)
            
            self.log("   >> CTRL+TAB")
            self.ctrl_tab()
            
            qtd = quantidade if quantidade is not None else self.qtd_fisica_atual
            self.log(f"   >> Quantidade: {qtd}")
            self.digitar(str(qtd))
            
            self.log("   >> certo.png")
            self.clicar_imagem(IMG_CERTO)
            self.esperar(TEMPO_MEDIO)
            
            self.log("   >> confirmar.png (finalizando)")
            self.clicar_imagem(IMG_CONFIRMAR)
            self.esperar(TEMPO_MEDIO)
            
            self.log_sucesso("Popup de vencimento tratado!")
            return True
        else:
            self.log("   >> Nenhum popup de vencimento detectado ✓")
            return False
    
    # ========================================
    # FUNÇÕES DE TECLADO
    # ========================================
    
    def digitar_item(self, texto):
        texto_upper = str(texto).upper().strip()
        self.log(f"   >> Colando via clipboard: '{texto_upper}'")
        
        try:
            clipboard_backup = pyperclip.paste()
        except:
            clipboard_backup = ''
        
        pyperclip.copy(texto_upper)
        self.esperar(0.2)
        
        pyautogui.hotkey('ctrl', 'v')
        self.esperar(0.3)
        
        try:
            pyperclip.copy(clipboard_backup)
        except:
            pass
    
    def digitar(self, texto, maiusculo=False):
        texto_final = str(texto).upper() if maiusculo else str(texto)
        pyautogui.typewrite(texto_final, interval=0.03)
    
    def tab(self, vezes=1):
        for _ in range(vezes):
            pyautogui.press('tab')
            self.esperar(0.1)
    
    def enter(self):
        pyautogui.press('enter')
        self.esperar(0.2)
    
    def seta_baixo(self, vezes=1):
        for _ in range(vezes):
            pyautogui.press('down')
            self.esperar(0.1)
    
    def f5(self):
        pyautogui.press('f5')
        self.esperar(TEMPO_LONGO)
    
    def ctrl_alt_e(self):
        pyautogui.hotkey('ctrl', 'alt', 'e')
        self.esperar(5)
    
    def ctrl_tab(self):
        pyautogui.hotkey('ctrl', 'tab')
        self.esperar(0.3)
    
    # ========================================
    # GERAR LOTE ROT
    # ========================================
    
    def gerar_lote_rot(self):
        hoje = datetime.now()
        lote = f"ROT{hoje.day:02d}{hoje.month:02d}{hoje.year}"
        self.log(f"   >> Lote ROT gerado: {lote}")
        return lote
    
    def gerar_validade_rot(self):
        hoje = datetime.now()
        mes = hoje.month + 6
        ano = hoje.year
        if mes > 12:
            mes -= 12
            ano += 1
        validade = f"{hoje.day:02d}{mes:02d}{ano}"
        self.log(f"   >> Validade: {validade}")
        return validade
    
    # ========================================
    # FUNÇÕES DE ARQUIVO
    # ========================================
    
    def carregar_relatorio(self):
        self.log("\n📂 CARREGANDO RELATÓRIO...")
        self.log_debug(f"Arquivo: {ARQUIVO_RELATORIO}")
        
        if not os.path.exists(ARQUIVO_RELATORIO):
            self.log_erro("RELATORIO_INVENTARIO.xlsx não encontrado!")
            return False
        
        try:
            tamanho = os.path.getsize(ARQUIVO_RELATORIO)
            self.log_debug(f"Tamanho do arquivo: {tamanho} bytes")
            
            df = pd.read_excel(ARQUIVO_RELATORIO, sheet_name='CONTAGEM', skiprows=3)
            
            self.log_debug(f"Colunas encontradas: {list(df.columns)}")
            self.log_debug(f"Total de linhas: {len(df)}")
            
            col_item = None
            col_qtd = None
            col_ajustado = None
            col_colaborador = None
            
            for col in df.columns:
                col_upper = str(col).upper().strip()
                if col_upper == 'ITEM':
                    col_item = col
                elif col_upper in ['QTD_FISICA', 'QTD FÍSICA', 'QTD FISICA']:
                    col_qtd = col
                elif col_upper == 'AJUSTADO':
                    col_ajustado = col
                elif col_upper == 'COLABORADOR':
                    col_colaborador = col
            
            if not col_item or not col_qtd:
                self.log_erro(f"Colunas não encontradas! Item={col_item}, Qtd={col_qtd}")
                return False
            
            self.log_sucesso(f"Colunas mapeadas:")
            self.log_debug(f"  Item={col_item}")
            self.log_debug(f"  Qtd={col_qtd}")
            self.log_debug(f"  Ajustado={col_ajustado}")
            self.log_debug(f"  Colaborador={col_colaborador}")
            
            self.log("\n📋 FILTRANDO ITENS PENDENTES:")
            for idx, row in df.iterrows():
                item_val = row.get(col_item)
                if pd.notna(item_val) and str(item_val).strip():
                    ajustado = str(row.get(col_ajustado, '')).upper().strip()
                    colaborador = row.get(col_colaborador, '') if col_colaborador else ''
                    
                    is_ajustado = 'SIM' in ajustado
                    
                    if not is_ajustado:
                        self.itens_pendentes.append({
                            'Item': str(item_val).strip().upper(),
                            'Qtd_Fisica': int(row.get(col_qtd, 0)) if pd.notna(row.get(col_qtd)) else 0,
                            'Colaborador': str(colaborador).strip() if pd.notna(colaborador) else '',
                            'Linha_Excel': idx + 5
                        })
                        self.log_sucesso(f"  PENDENTE: '{item_val}' (linha {idx + 5})")
            
            self.log(f"\n📊 RESUMO:")
            self.log_sucesso(f"  {len(self.itens_pendentes)} itens PENDENTES para processar")
            
            for item in self.itens_pendentes:
                self.log(f"     📦 {item['Item']} = {item['Qtd_Fisica']} pcs | Colab: {item['Colaborador']} | Linha: {item['Linha_Excel']}")
            
            return True
            
        except Exception as e:
            self.log_erro(f"Erro ao carregar: {e}")
            traceback.print_exc()
            return False
    
    def encontrar_gotoexcel(self):
        self.log("🔍 Procurando Gotoexcel...")
        
        user_profile = os.environ.get('USERPROFILE', '')
        
        locais = [
            'C:\\Temp',
            user_profile,
            os.path.join(user_profile, 'Documents'),
            os.path.join(user_profile, 'Downloads'),
            os.path.join(user_profile, 'Desktop'),
        ]
        
        for local in locais:
            padrao = os.path.join(local, 'Gotoexcel*.xlsx')
            arquivos = glob.glob(padrao)
            if arquivos:
                arquivo = max(arquivos, key=os.path.getmtime)
                self.log_sucesso(f"Encontrado: {arquivo}")
                return arquivo
            
            padrao2 = os.path.join(local, 'gotoexcel*.xlsx')
            arquivos2 = glob.glob(padrao2)
            if arquivos2:
                arquivo = max(arquivos2, key=os.path.getmtime)
                self.log_sucesso(f"Encontrado: {arquivo}")
                return arquivo
        
        self.log_aviso("Gotoexcel não encontrado nos locais padrão")
        return None
    
    def ler_gotoexcel(self, caminho):
        self.log("📖 Lendo Gotoexcel...")
        
        try:
            self.esperar(1)
            df = pd.read_excel(caminho, header=None)
            
            lotes = []
            
            if len(df) < 4:
                self.log_aviso("Arquivo Gotoexcel vazio ou sem dados de lotes")
                self.fechar_janela("otoexcel")
                return []
            
            num_colunas = len(df.columns)
            self.log_debug(f"Gotoexcel tem {num_colunas} colunas e {len(df)} linhas")
            
            for i in range(3, len(df)):
                try:
                    if num_colunas < 8:
                        self.log_aviso(f"Linha {i} não tem colunas suficientes")
                        continue
                    
                    item = df.iloc[i, 0] if pd.notna(df.iloc[i, 0]) else None
                    lote = df.iloc[i, 4] if num_colunas > 4 and pd.notna(df.iloc[i, 4]) else None
                    qtd = df.iloc[i, 7] if num_colunas > 7 and pd.notna(df.iloc[i, 7]) else 0
                    
                    if item and lote:
                        tipo = self.classificar_lote(str(lote))
                        lotes.append({
                            'item': str(item),
                            'lote': str(lote),
                            'quantidade': int(qtd) if qtd else 0,
                            'posicao': i - 3,
                            'tipo': tipo
                        })
                except Exception as e:
                    self.log_debug(f"Erro ao ler linha {i}: {e}")
                    continue
            
            self.lotes_encontrados = lotes
            self.log_sucesso(f"{len(lotes)} lotes encontrados:")
            for l in lotes:
                tipo_icon = "✅" if l['tipo'] in ['AC', 'INV', 'ROT'] else "⚠️"
                self.log(f"   {tipo_icon} [{l['posicao']}] {l['lote']} ({l['tipo']}) = {l['quantidade']} pcs")
            
            self.log("📕 Fechando Gotoexcel sem salvar...")
            self.fechar_janela("otoexcel")
            
            return lotes
        except Exception as e:
            self.log_erro(f"Erro ao ler Gotoexcel: {e}")
            self.fechar_janela("otoexcel")
            return []
    
    def classificar_lote(self, lote):
        lote_upper = lote.upper().strip()
        
        if lote_upper.startswith('INV'):
            return 'INV'
        elif lote_upper.startswith('ROT'):
            return 'ROT'
        elif lote_upper.startswith('MV'):
            return 'IRREGULAR'
        elif lote_upper.startswith('AC'):
            resto = lote_upper[2:]
            if resto and resto[0].isalpha():
                return 'IRREGULAR'
            else:
                return 'AC'
        else:
            return 'IRREGULAR'
    
    def atualizar_base_fiscal(self, item, quantidade, lote=None):
        try:
            if os.path.exists(ARQUIVO_BASE_FISCAL):
                df = pd.read_excel(ARQUIVO_BASE_FISCAL)
            else:
                df = pd.DataFrame(columns=['Item', 'Qtd_Fiscal_TOTVS', 'Lote'])
            
            nova_linha = pd.DataFrame({
                'Item': [item],
                'Qtd_Fiscal_TOTVS': [quantidade],
                'Lote': [lote if lote else '']
            })
            df = pd.concat([df, nova_linha], ignore_index=True)
            df.to_excel(ARQUIVO_BASE_FISCAL, index=False)
            return True
        except:
            return False
    
    # ========================================
    # ATUALIZAR RELATÓRIO
    # ========================================
    
    def atualizar_relatorio_item(self, item, qtd_fiscal, diferenca, ajustado='SIM', status_texto='AJUSTADO'):
        self.log(f"\n📝 ATUALIZANDO RELATÓRIO: {item}")
        self.log_debug(f"  Qtd Física: {self.qtd_fisica_atual}")
        self.log_debug(f"  Qtd Fiscal recebida: {qtd_fiscal}")
        self.log_debug(f"  Diferença: {diferenca}")
        
        try:
            from openpyxl import load_workbook
            from openpyxl.styles import PatternFill, Font
            
            # ABRIR EM MODO COMPARTILHADO
            wb = load_workbook(ARQUIVO_RELATORIO, read_only=False, keep_vba=False)
            
            # Verificar se tem permissão de escrita
            if wb.read_only:
                self.log_erro("Arquivo está em modo somente leitura!")
                return False
            
            ws = wb['CONTAGEM']
            
            verde_fill = PatternFill(start_color='27AE60', end_color='27AE60', fill_type='solid')
            verde_claro_fill = PatternFill(start_color='D5F5E3', end_color='D5F5E3', fill_type='solid')
            vermelho_fill = PatternFill(start_color='E74C3C', end_color='E74C3C', fill_type='solid')
            azul_fill = PatternFill(start_color='3498DB', end_color='3498DB', fill_type='solid')
            branco_font = Font(color='FFFFFF', bold=True)
            
            item_upper = item.upper().strip()
            linha_alvo = None
            
            if self.linha_excel_atual:
                self.log_debug(f"  Tentando linha específica: {self.linha_excel_atual}")
                cell_item = ws.cell(row=self.linha_excel_atual, column=1).value
                if cell_item and str(cell_item).strip().upper() == item_upper:
                    ajustado_cell = ws.cell(row=self.linha_excel_atual, column=9).value
                    ajustado_val = str(ajustado_cell).upper().strip() if ajustado_cell else ''
                    
                    if 'SIM' not in ajustado_val:
                        linha_alvo = self.linha_excel_atual
                        self.log_sucesso(f"  Linha específica confirmada: {linha_alvo}")
            
            if not linha_alvo:
                self.log_debug(f"  Buscando linha PENDENTE do item '{item_upper}'...")
                
                for row in range(5, ws.max_row + 1):
                    cell_item = ws.cell(row=row, column=1).value
                    
                    if cell_item and str(cell_item).strip().upper() == item_upper:
                        ajustado_cell = ws.cell(row=row, column=9).value
                        ajustado_val = str(ajustado_cell).upper().strip() if ajustado_cell else ''
                        
                        if 'SIM' not in ajustado_val:
                            linha_alvo = row
                            self.log_sucesso(f"  Linha PENDENTE encontrada: {row}")
                            break
            
            if not linha_alvo:
                for row in range(5, ws.max_row + 1):
                    cell_item = ws.cell(row=row, column=1).value
                    if cell_item and str(cell_item).strip().upper() == item_upper:
                        linha_alvo = row
                
                if linha_alvo:
                    self.log_aviso(f"  Usando última ocorrência: linha {linha_alvo}")
            
            if not linha_alvo:
                self.log_erro(f"  Item '{item_upper}' NÃO ENCONTRADO no relatório!")
                return False
            
            row = linha_alvo
            self.log_sucesso(f"  Atualizando linha {row}...")
            
            qtd_fiscal_final = qtd_fiscal
            
            self.log_debug(f"  Qtd Fiscal FINAL: {qtd_fiscal_final}")
            
            ws.cell(row=row, column=3, value=qtd_fiscal_final)
            ws.cell(row=row, column=4, value=diferenca)
            
            status_cell = ws.cell(row=row, column=5)
            if diferenca == 0:
                status_cell.value = 'OK - CORRETO'
                status_cell.fill = verde_fill
                status_cell.font = branco_font
            elif diferenca > 0:
                status_cell.value = f'EXCESSO +{diferenca}'
                status_cell.fill = vermelho_fill
                status_cell.font = branco_font
            else:
                status_cell.value = f'FALTA {diferenca}'
                status_cell.fill = azul_fill
                status_cell.font = branco_font
            
            if qtd_fiscal_final > 0:
                menor = min(self.qtd_fisica_atual, qtd_fiscal_final)
                maior = max(self.qtd_fisica_atual, qtd_fiscal_final)
                acur = round((menor / maior) * 100, 1)
                acur_cell = ws.cell(row=row, column=6)
                acur_cell.value = f'{acur}%'
                
                if acur >= 100:
                    acur_cell.fill = verde_fill
                    acur_cell.font = branco_font
                elif acur >= 95:
                    acur_cell.fill = verde_claro_fill
            
            if diferenca > 0 and qtd_fiscal_final > 0:
                ws.cell(row=row, column=7, value=f'{round(diferenca / qtd_fiscal_final * 100, 1)}%')
            else:
                ws.cell(row=row, column=7, value='-')
            
            if diferenca < 0 and qtd_fiscal_final > 0:
                ws.cell(row=row, column=8, value=f'{round(abs(diferenca) / qtd_fiscal_final * 100, 1)}%')
            else:
                ws.cell(row=row, column=8, value='-')
            
            ajust_cell = ws.cell(row=row, column=9)
            ajust_cell.value = 'SIM'
            ajust_cell.fill = verde_fill
            ajust_cell.font = branco_font
            
            data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            ws.cell(row=row, column=11, value=data_hora)
            
            for col in range(1, 12):
                if col not in [5, 6, 9]:
                    ws.cell(row=row, column=col).fill = verde_claro_fill
            
            # ========================================
            # ATUALIZAR ABA HISTORICO_AJUSTES
            # ========================================
            self.log_debug(f"  Atualizando aba HISTORICO_AJUSTES...")
            
            if 'HISTORICO_AJUSTES' not in wb.sheetnames:
                self.log_debug(f"  Criando aba HISTORICO_AJUSTES...")
                ws_hist = wb.create_sheet('HISTORICO_AJUSTES')
                # Cabeçalhos
                headers = ['ITEM', 'QTD FÍSICA', 'QTD FISCAL', 'DIFERENÇA', 'STATUS', 
                          'ACURACIDADE %', 'EXCESSO %', 'FALTA %', 'COLABORADOR', 'DATA/HORA']
                for col_idx, header in enumerate(headers, start=1):
                    cell = ws_hist.cell(row=1, column=col_idx, value=header)
                    cell.fill = PatternFill(start_color='2E75B6', end_color='2E75B6', fill_type='solid')
                    cell.font = Font(color='FFFFFF', bold=True)
            else:
                ws_hist = wb['HISTORICO_AJUSTES']
            
            # Adicionar nova linha no histórico
            nova_linha = ws_hist.max_row + 1
            ws_hist.cell(row=nova_linha, column=1, value=item_upper)
            ws_hist.cell(row=nova_linha, column=2, value=self.qtd_fisica_atual)
            ws_hist.cell(row=nova_linha, column=3, value=qtd_fiscal_final)
            ws_hist.cell(row=nova_linha, column=4, value=diferenca)
            ws_hist.cell(row=nova_linha, column=5, value=status_cell.value)
            
            # Acuracidade
            if qtd_fiscal_final > 0:
                menor = min(self.qtd_fisica_atual, qtd_fiscal_final)
                maior = max(self.qtd_fisica_atual, qtd_fiscal_final)
                acur = round((menor / maior) * 100, 1)
                ws_hist.cell(row=nova_linha, column=6, value=f'{acur}%')
            else:
                ws_hist.cell(row=nova_linha, column=6, value='0%')
            
            # Excesso %
            if diferenca > 0 and qtd_fiscal_final > 0:
                ws_hist.cell(row=nova_linha, column=7, value=f'{round(diferenca / qtd_fiscal_final * 100, 1)}%')
            else:
                ws_hist.cell(row=nova_linha, column=7, value='-')
            
            # Falta %
            if diferenca < 0 and qtd_fiscal_final > 0:
                ws_hist.cell(row=nova_linha, column=8, value=f'{round(abs(diferenca) / qtd_fiscal_final * 100, 1)}%')
            else:
                ws_hist.cell(row=nova_linha, column=8, value='-')
            
            ws_hist.cell(row=nova_linha, column=9, value=self.colaborador_atual)
            ws_hist.cell(row=nova_linha, column=10, value=data_hora)
            
            self.log_debug(f"  Salvando arquivo...")
            wb.save(ARQUIVO_RELATORIO)
            wb.close()
            self.log_sucesso(f"  Relatório salvo! Linha {row} marcada como AJUSTADO")
            self.log_sucesso(f"  Histórico atualizado na linha {nova_linha}")
            
            self.adicionar_historico(item, self.qtd_fisica_atual, qtd_fiscal_final, diferenca, self.colaborador_atual)
            
            self.itens_processados.append({
                'Item': item,
                'Qtd_Fisica': self.qtd_fisica_atual,
                'Qtd_Fiscal': qtd_fiscal_final,
                'Diferenca': diferenca,
                'Colaborador': self.colaborador_atual,
                'Data_Hora': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                'Linha_Excel': row
            })
            
            return True
            
        except PermissionError as e:
            self.log_erro(f"  Erro de permissão: Arquivo pode estar aberto por outro usuário!")
            self.log_erro(f"  Detalhes: {e}")
            return False
        except Exception as e:
            self.log_erro(f"  Erro ao atualizar relatório: {e}")
            traceback.print_exc()
            return False
    
    def adicionar_historico(self, item, qtd_fisica, qtd_fiscal, diferenca, colaborador):
        try:
            self.log_debug(f"  Adicionando ao histórico...")
            
            if os.path.exists(ARQUIVO_HISTORICO):
                df = pd.read_excel(ARQUIVO_HISTORICO)
            else:
                df = pd.DataFrame(columns=['Item', 'Qtd_Fisica', 'Qtd_Fiscal', 'Diferenca', 'Colaborador', 'Data_Hora', 'Data'])
            
            nova_linha = pd.DataFrame({
                'Item': [item],
                'Qtd_Fisica': [qtd_fisica],
                'Qtd_Fiscal': [qtd_fiscal],
                'Diferenca': [diferenca],
                'Colaborador': [colaborador],
                'Data_Hora': [datetime.now().strftime("%d/%m/%Y %H:%M:%S")],
                'Data': [datetime.now().strftime("%d/%m/%Y")]
            })
            
            df = pd.concat([df, nova_linha], ignore_index=True)
            df.to_excel(ARQUIVO_HISTORICO, index=False)
            
            self.log_debug(f"  Histórico atualizado: {len(df)} registros")
            
        except Exception as e:
            self.log_aviso(f"  Erro ao adicionar histórico: {e}")
    
    # ========================================
    # FECHAR Z02IN403
    # ========================================
    
    def fechar_pesquisa_saldo(self):
        self.log("📕 Fechando Z02IN403 (Pesquisa Saldo)...")
        
        janela = self.encontrar_janela("Z02IN403")
        if janela:
            self.trazer_frente(janela)
            self.esperar(0.5)
        
        self.log("   >> Clicando em cancelar.png...")
        if self.clicar_imagem(IMG_CANCELAR):
            self.esperar(TEMPO_MEDIO)
        else:
            self.log("   >> cancelar.png não encontrado, tentando ESC...")
            pyautogui.press('escape')
            self.esperar(0.5)
        
        self.log("   >> Clicando em x.png...")
        if self.clicar_imagem(IMG_FECHAR):
            self.esperar(TEMPO_MEDIO)
            self.log_sucesso("Z02IN403 fechada!")
        else:
            self.log("   >> x.png não encontrado, tentando ALT+F4...")
            pyautogui.hotkey('alt', 'F4')
            self.esperar(0.5)
        
        return True
    
    # ========================================
    # BUSCAR ITEM
    # ========================================
    
    def buscar_item(self, item):
        self.log(f"🔍 Buscando: {item}")
        
        if self.primeiro_item:
            self.log("   >> +.png (primeiro item)")
            if not self.clicar_imagem(IMG_MAIS):
                self.log_erro("Não foi possível clicar em +.png")
                return False
            
            self.log("   >> Aguardando 3 segundos...")
            self.esperar(3)
            
            self.primeiro_item = False
        else:
            self.log("   >> (digitando direto, sem +.png)")
        
        self.digitar_item(item)
        
        self.log("   >> 2x TAB")
        self.tab(2)
        
        self.log("   >> F5")
        self.f5()
        
        self.log("   >> 3x TAB")
        self.tab(3)
        
        self.log("   >> CTRL+ALT+E")
        self.ctrl_alt_e()
        
        self.log_sucesso("Exportado")
        return True
    
    # ========================================
    # LÓGICA AC/INV
    # ========================================
    
    def executar_logica_ac_inv(self, lotes):
        self.log("🔵 LÓGICA AC/INV")
        
        qtd_fiscal = sum(l['quantidade'] for l in lotes)
        diferenca = self.qtd_fisica_atual - qtd_fiscal
        
        self.log(f"   📊 Físico: {self.qtd_fisica_atual}")
        self.log(f"   📊 Fiscal: {qtd_fiscal}")
        self.log(f"   📊 Diferença: {diferenca}")
        
        for l in lotes:
            self.atualizar_base_fiscal(l['item'], l['quantidade'], l['lote'])
        
        if diferenca == 0:
            self.log_sucesso("Estoque CORRETO! Não precisa ajustar.")
            
            self.fechar_pesquisa_saldo()
            
            self.primeiro_item = True
            self.log("   >> Flag resetada: próximo item usará +.png")
            
            resultado = self.atualizar_relatorio_item(self.item_atual, qtd_fiscal, 0, 'SIM', 'OK - CORRETO')
            
            if resultado:
                self.log_sucesso(f"Item {self.item_atual} marcado como OK no relatório!")
            else:
                self.log_erro(f"Falha ao atualizar item {self.item_atual} no relatório!")
            
            return resultado
        
        if diferenca > 0:
            return self.adicionar_estoque(lotes, diferenca, qtd_fiscal)
        else:
            return self.retirar_estoque_multiplos_lotes(lotes, abs(diferenca), qtd_fiscal)
    
    def adicionar_estoque(self, lotes, qtd_adicionar, qtd_fiscal):
        self.log(f"\n📥 ADICIONANDO {qtd_adicionar} unidades...")
        
        lotes_ac = [l for l in lotes if l['tipo'] == 'AC']
        
        if not lotes_ac:
            self.log_aviso("Nenhum lote AC, usando primeiro lote disponível")
            lote_destino = lotes[0]
        else:
            lote_destino = lotes_ac[0]
        
        self.log(f"   >> Destino: {lote_destino['lote']} (posição [{lote_destino['posicao']}])")
        
        janela = self.encontrar_janela("Z02IN403")
        if janela:
            self.trazer_frente(janela)
        self.esperar(TEMPO_MEDIO)
        
        self.log("   >> Clicando em cancelar.png...")
        if self.clicar_imagem(IMG_CANCELAR):
            self.esperar(TEMPO_MEDIO)
        else:
            pyautogui.press('escape')
            self.esperar(0.5)
        
        self.log("   >> F5")
        self.f5()
        
        self.log("   >> 3x TAB")
        self.tab(3)
        
        posicao = lote_destino['posicao']
        if posicao > 0:
            self.log(f"   >> {posicao}x SETA BAIXO")
            self.seta_baixo(posicao)
        
        self.log("   >> Enter")
        self.enter()
        
        self.log("   >> 5x TAB")
        self.tab(5)
        
        self.log(f"   >> Código: {COD_ENTRADA}")
        self.digitar(COD_ENTRADA)
        
        self.log("   >> CTRL+TAB")
        self.ctrl_tab()
        
        self.log(f"   >> Quantidade: {qtd_adicionar}")
        self.digitar(str(qtd_adicionar))
        
        self.log("   >> certo.png")
        self.clicar_imagem(IMG_CERTO)
        self.esperar(TEMPO_MEDIO)
        
        # ✅ PRIMEIRO clicar em confirmar.png
        self.log("   >> confirmar.png")
        self.clicar_imagem(IMG_CONFIRMAR)
        self.esperar(TEMPO_MEDIO)
        
        # ✅ DEPOIS verificar popup (aguarda 5 seg internamente)
        self.verificar_popup_vencimento('entrada', qtd_adicionar)
        
        self.log_sucesso(f"Adicionado {qtd_adicionar} pcs em {lote_destino['lote']}!")
        
        diferenca = self.qtd_fisica_atual - qtd_fiscal
        resultado = self.atualizar_relatorio_item(self.item_atual, qtd_fiscal, diferenca, 'SIM')
        
        return resultado
    
    # ========================================
    # RETIRAR ESTOQUE - CORRIGIDO ✅
    # ========================================
    
    def retirar_estoque_multiplos_lotes(self, lotes, qtd_retirar_total, qtd_fiscal):
        """Retira estoque de múltiplos lotes na ordem: INV > ROT > AC"""
        self.log(f"\n📤 RETIRANDO {qtd_retirar_total} unidades de múltiplos lotes...")
        
        lotes_inv = [l for l in lotes if l['tipo'] == 'INV']
        lotes_rot = [l for l in lotes if l['tipo'] == 'ROT']
        lotes_ac = [l for l in lotes if l['tipo'] == 'AC']
        
        self.log(f"   Lotes INV: {len(lotes_inv)} | ROT: {len(lotes_rot)} | AC: {len(lotes_ac)}")
        
        lotes_ordenados = lotes_inv + lotes_rot + lotes_ac
        
        self.log("   📋 Ordem de retirada:")
        for i, l in enumerate(lotes_ordenados):
            self.log(f"      {i+1}. [{l['posicao']}] {l['lote']} ({l['tipo']}) = {l['quantidade']} pcs")
        
        qtd_restante = qtd_retirar_total
        retiradas_feitas = []
        
        for lote in lotes_ordenados:
            if qtd_restante <= 0:
                break
            
            qtd_retirar_lote = min(lote['quantidade'], qtd_restante)
            
            if qtd_retirar_lote > 0:
                retiradas_feitas.append({
                    'lote': lote['lote'],
                    'tipo': lote['tipo'],
                    'posicao': lote['posicao'],
                    'quantidade': qtd_retirar_lote,
                    'saldo_lote': lote['quantidade']
                })
                qtd_restante -= qtd_retirar_lote
                self.log(f"   ➡️ Retirar {qtd_retirar_lote} de {lote['lote']} (restante: {qtd_restante})")
        
        if qtd_restante > 0:
            self.log_aviso(f"⚠️ Não há saldo suficiente! Faltam {qtd_restante} pcs")
        
        for idx, retirada in enumerate(retiradas_feitas):
            self.log(f"\n🔄 Retirada {idx+1}/{len(retiradas_feitas)}: {retirada['quantidade']} pcs de {retirada['lote']}")
            
            janela = self.encontrar_janela("Z02IN403")
            if janela:
                self.trazer_frente(janela)
            self.esperar(TEMPO_MEDIO)
            
            if idx == 0:
                self.log("   >> Clicando em cancelar.png...")
                if self.clicar_imagem(IMG_CANCELAR):
                    self.esperar(TEMPO_MEDIO)
                else:
                    pyautogui.press('escape')
                    self.esperar(0.5)
                
                self.log("   >> F5")
                self.f5()
            else:
                self.log("   >> Aguardando 4 segundos...")
                self.esperar(4)
                
                self.log(f"   >> Digitando item: {self.item_atual}")
                self.digitar_item(self.item_atual)
                
                self.log("   >> 2x TAB")
                self.tab(2)
                
                self.log("   >> F5")
                self.f5()
            
            self.log("   >> 3x TAB")
            self.tab(3)
            
            if idx == 0:
                posicao = retirada['posicao']
            else:
                posicao = 0
            
            if posicao > 0:
                self.log(f"   >> {posicao}x SETA BAIXO (posição [{posicao}])")
                self.seta_baixo(posicao)
            else:
                self.log(f"   >> Posição [0], sem setas")
            
            self.log("   >> Enter")
            self.enter()
            
            self.log("   >> 5x TAB")
            self.tab(5)
            
            self.log(f"   >> Código: {COD_SAIDA}")
            self.digitar(COD_SAIDA)
            
            self.log("   >> CTRL+TAB")
            self.ctrl_tab()
            
            self.log(f"   >> Quantidade: {retirada['quantidade']}")
            self.digitar(str(retirada['quantidade']))
            
            # ✅ SEQUÊNCIA CORRIGIDA
            self.log("   >> saida.png")
            if not self.clicar_imagem(IMG_SAIDA):
                self.log_erro("saida.png não encontrado!")
            self.esperar(TEMPO_MEDIO)
            
            # ✅ VERIFICAR confirmar.png APÓS saida.png
            self.log("   >> Verificando confirmar.png após saída...")
            if self.clicar_imagem(IMG_CONFIRMAR):
                self.log_sucesso("confirmar.png clicado após saída!")
                self.esperar(TEMPO_MEDIO)
            
            self.log("   >> certo.png")
            if not self.clicar_imagem(IMG_CERTO):
                self.log_erro("certo.png não encontrado!")
            self.esperar(TEMPO_MEDIO)
            
            # VERIFICAR POPUP DE VENCIMENTO
            self.verificar_popup_vencimento('saida', retirada['quantidade'])
            
            self.log_sucesso(f"Retirado {retirada['quantidade']} pcs de {retirada['lote']}!")
        
        diferenca = self.qtd_fisica_atual - qtd_fiscal
        resultado = self.atualizar_relatorio_item(self.item_atual, qtd_fiscal, diferenca, 'SIM')
        
        return resultado
    
    # ========================================
    # LÓGICA LOTES IRREGULARES - CORRIGIDO ✅
    # ========================================
    
    def executar_logica_irregular(self, lotes):
        """Executa lógica quando existem lotes IRREGULARES junto com válidos"""
        self.log("🔴 LÓGICA LOTES IRREGULARES (MV, ACERTO, etc.)")
        
        lotes_irregulares = [l for l in lotes if l['tipo'] == 'IRREGULAR']
        lotes_validos = [l for l in lotes if l['tipo'] in ['AC', 'INV', 'ROT']]
        
        self.log(f"   Lotes IRREGULARES: {len(lotes_irregulares)}")
        self.log(f"   Lotes VÁLIDOS (AC/INV/ROT): {len(lotes_validos)}")
        
        if not lotes_irregulares:
            self.log_aviso("Nenhum lote irregular encontrado, usando lógica AC/INV")
            return self.executar_logica_ac_inv(lotes)
        
        for idx_irreg, lote_irreg in enumerate(lotes_irregulares):
            self.log(f"\n🔄 Processando IRREGULAR [{idx_irreg + 1}/{len(lotes_irregulares)}]: {lote_irreg['lote']} = {lote_irreg['quantidade']} pcs")
            
            # PASSO 1: Retirando do lote IRREGULAR
            self.log("\n📤 PASSO 1: Retirando do lote IRREGULAR...")
            
            if idx_irreg == 0:
                self.log("   >> Voltando para Z02IN403...")
                janela = self.encontrar_janela("Z02IN403")
                if janela:
                    self.trazer_frente(janela)
                self.esperar(TEMPO_MEDIO)
                
                self.log("   >> Clicando em cancelar.png...")
                if self.clicar_imagem(IMG_CANCELAR):
                    self.esperar(TEMPO_MEDIO)
                else:
                    pyautogui.press('escape')
                    self.esperar(0.5)
                
                self.log("   >> F5")
                self.f5()
            else:
                self.log("   >> Aguardando 4 segundos...")
                self.esperar(4)
                
                self.log(f"   >> Digitando item: {self.item_atual}")
                self.digitar_item(self.item_atual)
                
                self.log("   >> 2x TAB")
                self.tab(2)
                
                self.log("   >> F5")
                self.f5()
            
            self.log(f"   >> 3x TAB")
            self.tab(3)
            
            if idx_irreg == 0:
                posicao_irreg = lote_irreg['posicao']
            else:
                posicao_irreg = 0
            
            if posicao_irreg > 0:
                self.log(f"   >> {posicao_irreg}x SETA BAIXO")
                self.seta_baixo(posicao_irreg)
            
            self.log("   >> Enter")
            self.enter()
            
            self.log("   >> 5x TAB")
            self.tab(5)
            
            self.log(f"   >> Código: {COD_SAIDA}")
            self.digitar(COD_SAIDA)
            
            self.log("   >> CTRL+TAB")
            self.ctrl_tab()
            
            qtd_irreg = lote_irreg['quantidade']
            self.log(f"   >> Quantidade: {qtd_irreg}")
            self.digitar(str(qtd_irreg))
            
            # ✅ SEQUÊNCIA CORRIGIDA
            self.log("   >> saida.png")
            if not self.clicar_imagem(IMG_SAIDA):
                self.log_erro("saida.png não encontrado!")
            self.esperar(TEMPO_MEDIO)
            
            # ✅ VERIFICAR confirmar.png APÓS saida.png
            self.log("   >> Verificando confirmar.png após saída...")
            if self.clicar_imagem(IMG_CONFIRMAR):
                self.log_sucesso("confirmar.png clicado após saída!")
                self.esperar(TEMPO_MEDIO)
            
            self.log("   >> certo.png")
            if not self.clicar_imagem(IMG_CERTO):
                self.log_erro("certo.png não encontrado!")
            self.esperar(TEMPO_MEDIO)
            
            self.verificar_popup_vencimento('saida', qtd_irreg)
            
            self.qtd_mv_retirada = qtd_irreg
            self.log_sucesso(f"Retirado {qtd_irreg} pcs do lote IRREGULAR!")
            
            # PASSO 2: Adicionando em lote válido ou criando ROT
            self.log("   >> Aguardando 4 segundos...")
            self.esperar(4)
            
            if lotes_validos:
                lote_destino = lotes_validos[0]
                self.log(f"\n📥 PASSO 2: Adicionando {qtd_irreg} pcs em {lote_destino['lote']}...")
                
                self.log(f"   >> Digitando item: {self.item_atual}")
                self.digitar_item(self.item_atual)
                
                self.log("   >> 2x TAB")
                self.tab(2)
                
                self.log("   >> F5")
                self.f5()
                
                self.log(f"   >> 3x TAB")
                self.tab(3)
                
                self.log("   >> Enter (primeiro lote disponível)")
                self.enter()
                
                self.log("   >> 5x TAB")
                self.tab(5)
                
                self.log(f"   >> Código: {COD_ENTRADA}")
                self.digitar(COD_ENTRADA)
                
                self.log("   >> CTRL+TAB")
                self.ctrl_tab()
                
                self.log(f"   >> Quantidade: {qtd_irreg}")
                self.digitar(str(qtd_irreg))
                
                self.log("   >> certo.png")
                if not self.clicar_imagem(IMG_CERTO):
                    self.log_erro("certo.png não encontrado!")
                self.esperar(TEMPO_MEDIO)
                
                # ✅ PRIMEIRO clicar em confirmar.png
                self.log("   >> confirmar.png")
                if not self.clicar_imagem(IMG_CONFIRMAR):
                    self.log_erro("confirmar.png não encontrado!")
                self.esperar(TEMPO_MEDIO)
                
                # ✅ DEPOIS verificar popup (aguarda 5 seg internamente)
                self.verificar_popup_vencimento('entrada', qtd_irreg)
                
                self.log_sucesso(f"Adicionado {qtd_irreg} pcs em {lote_destino['lote']}!")
                
            else:
                self.log_aviso("Nenhum lote válido encontrado, criando ROT...")
                self.criar_lote_rot_irregular(qtd_irreg)
        
        # PASSO 3: Ajuste final
        self.log("\n⚖️ PASSO 3: Ajuste final do estoque...")
        
        self.log("   >> Aguardando 4 segundos...")
        self.esperar(4)
        
        self.log(f"   >> Digitando item: {self.item_atual}")
        self.digitar_item(self.item_atual)
        
        self.log("   >> 2x TAB")
        self.tab(2)
        
        self.log("   >> F5")
        self.f5()
        
        self.log("   >> 3x TAB")
        self.tab(3)
        
        self.log("   >> CTRL+ALT+E")
        self.ctrl_alt_e()
        
        self.log("   >> Aguardando 6 segundos para Gotoexcel...")
        self.esperar(6)
        
        janela_goto = self.encontrar_janela("otoexcel")
        if janela_goto:
            self.trazer_frente(janela_goto)
        
        caminho = self.encontrar_gotoexcel()
        if caminho:
            novos_lotes = self.ler_gotoexcel(caminho)
            if novos_lotes:
                novos_irregulares = [l for l in novos_lotes if l['tipo'] == 'IRREGULAR']
                if novos_irregulares:
                    self.log_aviso(f"Ainda há {len(novos_irregulares)} lotes irregulares! Processando...")
                    return self.executar_logica_irregular(novos_lotes)
                else:
                    return self.executar_logica_ac_inv(novos_lotes)
        
        self.log_aviso("Não foi possível obter saldo atualizado")
        return False
    
    def criar_lote_rot_irregular(self, quantidade):
        novo_lote = self.gerar_lote_rot()
        validade = self.gerar_validade_rot()
        
        self.log(f"📦 Criando lote ROT: {novo_lote} | Validade: {validade}")
        
        self.log(f"   >> Digitando item: {self.item_atual}")
        self.digitar_item(self.item_atual)
        
        self.log("   >> 2x TAB")
        self.tab(2)
        
        self.log(f"   >> Digitando lote: {novo_lote}")
        self.digitar_item(novo_lote)
        
        self.log("   >> 1x TAB")
        self.tab(1)
        
        self.log(f"   >> Digitando validade: {validade}")
        self.digitar(validade)
        
        self.log("   >> 5x TAB")
        self.tab(5)
        
        self.log(f"   >> Código: {COD_ENTRADA}")
        self.digitar(COD_ENTRADA)
        
        self.log("   >> CTRL+TAB")
        self.ctrl_tab()
        
        self.log(f"   >> Quantidade: {quantidade}")
        self.digitar(str(quantidade))
        
        self.log("   >> certo.png")
        if not self.clicar_imagem(IMG_CERTO):
            self.log_erro("certo.png não encontrado!")
        self.esperar(TEMPO_MEDIO)
        
        # ✅ PRIMEIRO clicar em confirmar.png
        self.log("   >> confirmar.png")
        if not self.clicar_imagem(IMG_CONFIRMAR):
            self.log_erro("confirmar.png não encontrado!")
        self.esperar(TEMPO_MEDIO)
        
        # ✅ DEPOIS verificar popup (aguarda 5 seg internamente)
        self.verificar_popup_vencimento('entrada', quantidade)
        
        self.log_sucesso(f"Lote ROT criado: {novo_lote} com {quantidade} pcs")
    
    # ========================================
    # CRIAR LOTE ROT NOVO
    # ========================================
    
    def criar_lote_rot_novo(self):
        self.log("\n📦 CRIANDO LOTE ROT NOVO (item sem lote)...")
        
        novo_lote = self.gerar_lote_rot()
        validade = self.gerar_validade_rot()
        
        self.log(f"   Lote: {novo_lote}")
        self.log(f"   Validade: {validade}")
        self.log(f"   Quantidade: {self.qtd_fisica_atual}")
        
        self.log("   >> Voltando para Z02IN403...")
        janela = self.encontrar_janela("Z02IN403")
        if janela:
            self.trazer_frente(janela)
        self.esperar(TEMPO_MEDIO)
        
        self.log("   >> Clicando em cancelar.png...")
        if self.clicar_imagem(IMG_CANCELAR):
            self.esperar(TEMPO_MEDIO)
        else:
            pyautogui.press('escape')
            self.esperar(0.5)
        
        self.log(f"   >> Digitando lote: {novo_lote}")
        self.digitar_item(novo_lote)
        
        self.log("   >> 1x TAB")
        self.tab(1)
        
        self.log(f"   >> Digitando validade: {validade}")
        self.digitar(validade)
        
        self.log("   >> 5x TAB")
        self.tab(5)
        
        self.log(f"   >> Código: {COD_ENTRADA}")
        self.digitar(COD_ENTRADA)
        
        self.log("   >> CTRL+TAB")
        self.ctrl_tab()
        
        self.log(f"   >> Quantidade: {self.qtd_fisica_atual}")
        self.digitar(str(self.qtd_fisica_atual))
        
        self.log("   >> certo.png")
        if not self.clicar_imagem(IMG_CERTO):
            self.log_erro("certo.png não encontrado!")
        self.esperar(TEMPO_MEDIO)
        
        # ✅ PRIMEIRO clicar em confirmar.png
        self.log("   >> confirmar.png")
        if not self.clicar_imagem(IMG_CONFIRMAR):
            self.log_erro("confirmar.png não encontrado!")
        self.esperar(TEMPO_MEDIO)
        
        # ✅ DEPOIS verificar popup (aguarda 5 seg internamente)
        self.verificar_popup_vencimento('entrada', self.qtd_fisica_atual)
        
        self.log_sucesso(f"Lote ROT criado: {novo_lote} com {self.qtd_fisica_atual} pcs!")
        
        resultado = self.atualizar_relatorio_item(
            self.item_atual, 
            self.qtd_fisica_atual,
            0,
            'SIM', 
            'LOTE CRIADO'
        )
        
        return resultado
    
    # ========================================
    # LÓGICA APENAS IRREGULAR - CORRIGIDO ✅
    # ========================================
    
    def executar_logica_apenas_irregular(self, lotes_irregulares):
        """Executa lógica quando só existem lotes IRREGULARES"""
        self.log("🔴 LÓGICA APENAS LOTES IRREGULARES (sem AC/INV/ROT)")
        
        total_irreg = sum(l['quantidade'] for l in lotes_irregulares)
        self.log(f"   Total em lotes IRREGULARES: {total_irreg} pcs")
        self.log(f"   Físico: {self.qtd_fisica_atual} pcs")
        
        for idx_irreg, lote_irreg in enumerate(lotes_irregulares):
            self.log(f"\n🔄 Processando IRREGULAR [{idx_irreg + 1}/{len(lotes_irregulares)}]: {lote_irreg['lote']} = {lote_irreg['quantidade']} pcs")
            
            # PASSO 1: Retirando do lote IRREGULAR
            self.log("\n📤 PASSO 1: Retirando do lote IRREGULAR...")
            
            if idx_irreg == 0:
                self.log("   >> Voltando para Z02IN403...")
                janela = self.encontrar_janela("Z02IN403")
                if janela:
                    self.trazer_frente(janela)
                self.esperar(TEMPO_MEDIO)
                
                self.log("   >> Clicando em cancelar.png...")
                if self.clicar_imagem(IMG_CANCELAR):
                    self.esperar(TEMPO_MEDIO)
                else:
                    pyautogui.press('escape')
                    self.esperar(0.5)
                
                self.log("   >> F5")
                self.f5()
            else:
                self.log("   >> Aguardando 4 segundos...")
                self.esperar(4)
                
                self.log(f"   >> Digitando item: {self.item_atual}")
                self.digitar_item(self.item_atual)
                
                self.log("   >> 2x TAB")
                self.tab(2)
                
                self.log("   >> F5")
                self.f5()
            
            self.log("   >> 3x TAB")
            self.tab(3)
            
            if idx_irreg == 0:
                posicao_irreg = lote_irreg['posicao']
            else:
                posicao_irreg = 0
            
            if posicao_irreg > 0:
                self.log(f"   >> {posicao_irreg}x SETA BAIXO")
                self.seta_baixo(posicao_irreg)
            
            self.log("   >> Enter")
            self.enter()
            
            self.log("   >> 5x TAB")
            self.tab(5)
            
            self.log(f"   >> Código: {COD_SAIDA}")
            self.digitar(COD_SAIDA)
            
            self.log("   >> CTRL+TAB")
            self.ctrl_tab()
            
            qtd_irreg = lote_irreg['quantidade']
            self.log(f"   >> Quantidade: {qtd_irreg}")
            self.digitar(str(qtd_irreg))
            
            # ✅ SEQUÊNCIA CORRIGIDA
            self.log("   >> saida.png")
            if not self.clicar_imagem(IMG_SAIDA):
                self.log_erro("saida.png não encontrado!")
            self.esperar(TEMPO_MEDIO)
            
            # ✅ VERIFICAR confirmar.png APÓS saida.png
            self.log("   >> Verificando confirmar.png após saída...")
            if self.clicar_imagem(IMG_CONFIRMAR):
                self.log_sucesso("confirmar.png clicado após saída!")
                self.esperar(TEMPO_MEDIO)
            
            self.log("   >> certo.png")
            if not self.clicar_imagem(IMG_CERTO):
                self.log_erro("certo.png não encontrado!")
            self.esperar(TEMPO_MEDIO)
            
            self.verificar_popup_vencimento('saida', qtd_irreg)
            
            self.qtd_mv_retirada = qtd_irreg
            self.log_sucesso(f"Retirado {qtd_irreg} pcs do lote IRREGULAR!")
            
            # PASSO 2: Criar lote ROT
            self.log("   >> Aguardando 4 segundos...")
            self.esperar(4)
            
            self.log(f"\n📥 PASSO 2: Criando lote ROT com {qtd_irreg} pcs...")
            
            novo_lote = self.gerar_lote_rot()
            validade = self.gerar_validade_rot()
            
            self.log(f"   >> Digitando item: {self.item_atual}")
            self.digitar_item(self.item_atual)
            
            self.log("   >> 2x TAB")
            self.tab(2)
            
            self.log(f"   >> Digitando lote: {novo_lote}")
            self.digitar_item(novo_lote)
            
            self.log("   >> 1x TAB")
            self.tab(1)
            
            self.log(f"   >> Digitando validade: {validade}")
            self.digitar(validade)
            
            self.log("   >> 5x TAB")
            self.tab(5)
            
            self.log(f"   >> Código: {COD_ENTRADA}")
            self.digitar(COD_ENTRADA)
            
            self.log("   >> CTRL+TAB")
            self.ctrl_tab()
            
            self.log(f"   >> Quantidade: {qtd_irreg}")
            self.digitar(str(qtd_irreg))
            
            self.log("   >> certo.png")
            if not self.clicar_imagem(IMG_CERTO):
                self.log_erro("certo.png não encontrado!")
            self.esperar(TEMPO_MEDIO)
            
            # ✅ PRIMEIRO clicar em confirmar.png
            self.log("   >> confirmar.png")
            if not self.clicar_imagem(IMG_CONFIRMAR):
                self.log_erro("confirmar.png não encontrado!")
            self.esperar(TEMPO_MEDIO)
            
            # ✅ DEPOIS verificar popup (aguarda 5 seg internamente)
            self.verificar_popup_vencimento('entrada', qtd_irreg)
            
            self.log_sucesso(f"Lote ROT criado: {novo_lote} com {qtd_irreg} pcs!")
        
        # PASSO 3: Ajuste final
        self.log("\n⚖️ PASSO 3: Ajuste final do estoque...")
        
        self.log("   >> Aguardando 4 segundos...")
        self.esperar(4)
        
        self.log(f"   >> Digitando item: {self.item_atual}")
        self.digitar_item(self.item_atual)
        
        self.log("   >> 2x TAB")
        self.tab(2)
        
        self.log("   >> F5")
        self.f5()
        
        self.log("   >> 3x TAB")
        self.tab(3)
        
        self.log("   >> CTRL+ALT+E")
        self.ctrl_alt_e()
        
        self.log("   >> Aguardando 6 segundos para Gotoexcel...")
        self.esperar(6)
        
        janela_goto = self.encontrar_janela("otoexcel")
        if janela_goto:
            self.trazer_frente(janela_goto)
        
        caminho = self.encontrar_gotoexcel()
        if caminho:
            novos_lotes = self.ler_gotoexcel(caminho)
            if novos_lotes:
                return self.executar_logica_ac_inv(novos_lotes)
        
        self.log_aviso("Não foi possível obter saldo atualizado")
        return False
    
    # ========================================
    # PROCESSAR ITEM
    # ========================================
    
    def processar_item(self, item_data):
        self.item_atual = item_data['Item'].upper()
        self.qtd_fisica_atual = item_data['Qtd_Fisica']
        self.colaborador_atual = item_data.get('Colaborador', '')
        self.linha_excel_atual = item_data.get('Linha_Excel', None)
        
        self.log("\n" + "=" * 60)
        self.log(f"📦 PROCESSANDO ITEM: {self.item_atual}")
        self.log(f"   Quantidade Física: {self.qtd_fisica_atual}")
        self.log(f"   Colaborador: {self.colaborador_atual}")
        self.log(f"   Linha Excel: {self.linha_excel_atual}")
        self.log("=" * 60)
        
        if not self.buscar_item(self.item_atual):
            self.log_erro(f"Falha ao buscar item {self.item_atual}")
            return False
        
        self.log("⏳ Aguardando Gotoexcel...")
        self.esperar(TEMPO_LONGO)
        
        janela_goto = self.encontrar_janela("otoexcel")
        if janela_goto:
            self.trazer_frente(janela_goto)
        
        caminho = self.encontrar_gotoexcel()
        if not caminho:
            self.log_erro("Gotoexcel não encontrado!")
            return False
        
        lotes = self.ler_gotoexcel(caminho)
        
        # CASO 1: SEM LOTES E FÍSICO = 0
        if not lotes and self.qtd_fisica_atual == 0:
            self.log_sucesso("Físico = 0 e Fiscal = 0. Estoque CORRETO!")
            
            self.fechar_pesquisa_saldo()
            
            self.primeiro_item = True
            self.log("   >> Flag resetada: próximo item usará +.png")
            
            resultado = self.atualizar_relatorio_item(
                self.item_atual, 
                0,
                0,
                'SIM', 
                'OK - CORRETO'
            )
            
            if resultado:
                self.log_sucesso(f"Item {self.item_atual} marcado como OK no relatório!")
            
            return resultado
        
        # CASO 2: SEM LOTES MAS FÍSICO > 0
        if not lotes:
            self.log_aviso("⚠️ SEM LOTES encontrados mas tem estoque físico! Criando lote ROT novo...")
            return self.criar_lote_rot_novo()
        
        # CASO 3: APENAS LOTES IRREGULARES
        tipos = set(l['tipo'] for l in lotes)
        lotes_irregulares = [l for l in lotes if l['tipo'] == 'IRREGULAR']
        lotes_validos = [l for l in lotes if l['tipo'] in ['AC', 'INV', 'ROT']]
        
        if lotes_irregulares and not lotes_validos:
            self.log_aviso("⚠️ Apenas lote(s) IRREGULARES encontrado(s)!")
            return self.executar_logica_apenas_irregular(lotes_irregulares)
        
        # CASO 4: TEM IRREGULARES E LOTES VÁLIDOS
        if 'IRREGULAR' in tipos:
            return self.executar_logica_irregular(lotes)
        
        # CASO 5: APENAS AC/INV/ROT
        return self.executar_logica_ac_inv(lotes)
    
    # ========================================
    # FECHAR CE0220
    # ========================================
    
    def fechar_ce0220(self):
        self.log("\n📕 Fechando CE0220...")
        
        janela = self.encontrar_janela("CE0220")
        if janela:
            self.trazer_frente(janela)
            self.esperar(1)
        
        self.log("   >> Clicando em x.png...")
        if self.clicar_imagem(IMG_FECHAR):
            self.log_sucesso("CE0220 fechado!")
            self.esperar(2)
        else:
            pyautogui.hotkey('alt', 'F4')
            self.esperar(1)
    
    # ========================================
    # FINALIZAR
    # ========================================
    
    def finalizar(self):
        self.log("\n" + "=" * 60)
        self.log("🏁 FINALIZANDO AUTOMAÇÃO")
        self.log("=" * 60)
        
        self.log(f"\n📊 RESUMO: {len(self.itens_processados)} itens processados")
        
        for item in self.itens_processados:
            dif = item['Diferenca']
            status = "CORRETO" if dif == 0 else f"AJUSTADO (dif: {dif})"
            self.log_sucesso(f"   {item['Item']} - {status}")
        
        self.log("\n📕 Fechando CE0220...")
        if self.clicar_imagem(IMG_FECHAR):
            self.esperar(0.5)
        
        self.minimizar_todas_janelas()
        self.reabrir_interface()
    
    # ========================================
    # REABRIR INTERFACE
    # ========================================
    
    def reabrir_interface(self):
        self.log("\n🔄 Reabrindo interface...")
        
        if getattr(sys, 'frozen', False):
            script = os.path.join(DIR_BASE, "Sistema_Inventario.exe")
        else:
            script = os.path.join(DIR_BASE, "lancamento_inventario.py")
        
        self.log_debug(f"Script: {script}")
        self.log_debug(f"Existe: {os.path.exists(script)}")
        
        if not os.path.exists(script):
            self.log_erro(f"Arquivo não encontrado: {script}")
            return
        
        try:
            if getattr(sys, 'frozen', False):
                subprocess.Popen([script], cwd=DIR_BASE)
            else:
                subprocess.Popen([sys.executable, script], cwd=DIR_BASE)
            
            self.log_sucesso("Interface reaberta!")
        except Exception as e:
            self.log_erro(f"Erro ao reabrir: {e}")
    
    # ========================================
    # IMPORTAR PEDIDO - HONDA & GM (ESPD0001)
    # ========================================
    def importar_pedido(self):
        """Abre o programa ESPD0001 no TOTVS e importa pedidos do diretório GM."""
        self.log("\n" + "=" * 60)
        self.log("🚗 IMPORTAÇÃO DE PEDIDO - HONDA & GM")
        self.log("=" * 60)

        diretorio = DIRETORIO_IMPORTACAO_GM

        # --------------------------------------------------
        # PASSO 1: Procurar a janela "DATASUL Interative"
        # --------------------------------------------------
        self.log("🔍 Procurando janela 'DATASUL Interative'...")
        janela = self.encontrar_janela("DATASUL Interative")

        # --------------------------------------------------
        # PASSO 2: Se não achar, abre o TOTVS do zero e
        #          aguarda até TEMPO_ESPERA_DATASUL a janela aparecer
        # --------------------------------------------------
        if not janela:
            self.log_aviso("⚠️ 'DATASUL Interative' não encontrado!")
            self.log("🌐 Abrindo TOTVS (login -> senha -> Entrar -> popup)...")

            if not self._login_totvs_navegador():
                self.log_erro("❌ Falha ao abrir/logar no TOTVS!")
                self.reabrir_interface()
                return False

            self.log(f"   >> Aguardando 'DATASUL Interative' (até {TEMPO_ESPERA_DATASUL}s)...")
            for i in range(TEMPO_ESPERA_DATASUL):
                time.sleep(1)
                janela = self.encontrar_janela("DATASUL Interative")
                if janela:
                    self.log_sucesso(f"'DATASUL Interative' apareceu após {i + 1}s!")
                    break

            self._fechar_driver_login()

            if not janela:
                self.log_erro("❌ 'DATASUL Interative' não apareceu no tempo esperado!")
                self.reabrir_interface()
                return False
        else:
            self.log_sucesso("'DATASUL Interative' já estava aberto!")

        # --------------------------------------------------
        # PASSO 3: Trazer para frente e abrir o ESPD0001
        # --------------------------------------------------
        self.log("🔺 Trazendo 'DATASUL Interative' para frente...")
        self.trazer_frente(janela)
        self.esperar(TEMPO_MEDIO)

        atalho = '+'.join(k.upper() for k in ATALHO_ABRIR_PROGRAMA)
        self.log(f"⌨️ {atalho} (abrir lançador)...")
        pyautogui.hotkey(*ATALHO_ABRIR_PROGRAMA)
        self.esperar(TEMPO_CURTO)

        self.log(f"⌨️ Digitando {PROGRAMA_IMPORTACAO}...")
        pyautogui.typewrite(PROGRAMA_IMPORTACAO, interval=0.05)
        self.esperar(TEMPO_CURTO)

        self.log("⌨️ ENTER (abrir programa)...")
        pyautogui.press('enter')
        self.log(f"   >> Aguardando {TEMPO_ESPERA_PROGRAMA}s o programa carregar...")
        self.esperar(TEMPO_ESPERA_PROGRAMA)

        # --------------------------------------------------
        # PASSO 4: TAB e ENTER (QTD_TAB_ENTER x)
        # --------------------------------------------------
        self.log(f"⌨️ {QTD_TAB_ENTER}x (TAB, ENTER)...")
        for i in range(QTD_TAB_ENTER):
            pyautogui.press('tab')
            self.esperar(0.3)
            pyautogui.press('enter')
            self.log(f"   >> Sequência {i + 1}/{QTD_TAB_ENTER}")
            self.esperar(TEMPO_CURTO)

        # --------------------------------------------------
        # PASSO 5: Colar o diretório
        # --------------------------------------------------
        self.log(f"📋 Colando diretório: {diretorio}")
        try:
            pyperclip.copy(diretorio)
        except Exception as e:
            self.log_aviso(f"Falha ao copiar diretório: {e}")
        self.esperar(0.3)
        pyautogui.hotkey('ctrl', 'v')
        self.esperar(TEMPO_CURTO)

        # --------------------------------------------------
        # PASSO 6: 4x TAB
        # --------------------------------------------------
        self.log("⌨️ 4x TAB...")
        for _ in range(4):
            pyautogui.press('tab')
            self.esperar(0.3)

        # --------------------------------------------------
        # PASSO 7: Seta para baixo, depois seta para cima
        # --------------------------------------------------
        self.log("⌨️ Seta para BAIXO...")
        pyautogui.press('down')
        self.esperar(TEMPO_CURTO)
        self.log("⌨️ Seta para CIMA...")
        pyautogui.press('up')
        self.esperar(TEMPO_CURTO)

        # --------------------------------------------------
        # PASSO 8: ENTER final
        # --------------------------------------------------
        self.log("⌨️ ENTER (confirmar)...")
        pyautogui.press('enter')
        self.esperar(TEMPO_MEDIO)

        self.log_sucesso("✅ Fluxo de importação de pedido concluído!")
        self.reabrir_interface()
        return True

    # ========================================
    # EXECUTAR
    # ========================================
    
    def executar(self):
        self.log("\n🚀 INICIANDO AUTOMAÇÃO...\n")
        
        if not self.carregar_relatorio():
            self.log_erro("Erro ao carregar relatório!")
            self.reabrir_interface()
            return
        
        if not self.itens_pendentes:
            self.log_sucesso("Nenhum item pendente para processar!")
            self.reabrir_interface()
            return
        
        if not self.preparar_totvs():
            self.log_erro("TOTVS não disponível!")
            self.reabrir_interface()
            return
        
        total = len(self.itens_pendentes)
        self.total_itens_processar = total
        self.log(f"\n📦 TOTAL DE ITENS A PROCESSAR: {total}")
        
        for idx, item in enumerate(self.itens_pendentes):
            self.log(f"\n{'='*60}")
            self.log(f"📦 ITEM [{idx+1}/{total}]")
            self.log(f"{'='*60}")
            
            try:
                sucesso = self.processar_item(item)
                if sucesso:
                    self.log_sucesso(f"Item {item['Item']} processado com sucesso!")
                else:
                    self.log_erro(f"Falha ao processar item {item['Item']}")
            except Exception as e:
                self.log_erro(f"Exceção ao processar: {e}")
                traceback.print_exc()
                try:
                    with open(self.arquivo_log, 'a', encoding='utf-8') as f:
                        f.write(f"\n{'='*60}\n")
                        f.write(f"EXCEÇÃO DETALHADA:\n")
                        f.write(traceback.format_exc())
                        f.write(f"{'='*60}\n")
                except:
                    pass
            
            if idx < total - 1:
                self.log("\n⏳ Aguardando 7 segundos antes do próximo item...")
                self.esperar(7)
        
        self.finalizar()


# ========================================
# EXECUTAR
# ========================================
if __name__ == "__main__":
    bot = AutomacaoTOTVS()
    # Modo "importar" roda o fluxo de Importar Pedido HONDA & GM (ESPD0001).
    # Sem argumento, roda a automação de ajuste de inventário (padrão).
    if len(sys.argv) > 1 and sys.argv[1].lower() in ("importar", "importacao", "import"):
        bot.importar_pedido()
    else:
        bot.executar()