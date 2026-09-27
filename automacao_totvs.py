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
from janelas_windows import janela_disponivel, janela_em_primeiro_plano

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
TEM_CTYPES = False
try:
    import ctypes
    myappid = 'deivid.automacao.totvs.v2.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    # ctypes é usado também para forçar/conferir o foco das janelas
    TEM_CTYPES = True
except Exception:
    # "windll" não existe fora do Windows - segue sem o reforço de foco
    TEM_CTYPES = False

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
TOTVS_URL = "http://192.168.2.6:8080/totvs-menu"
TEMPO_ESPERA_ABRIR = 30
# Tempo de inicialização do cliente DATASUL após clicar em abrir_popup.png.
TEMPO_APOS_CLIQUE_POPUP = 49
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

# Atalho que abre o lançador de programas no TOTVS (CTRL+X).
ATALHO_ABRIR_PROGRAMA = ('ctrl', 'x')

# Atalho alternativo: se a janela do lançador não aparecer com o CTRL+X,
# a automação confirma o foco do DATASUL e tenta este.
# (a automação de inventário usa CTRL+ALT+X para o mesmo lançador)
ATALHO_ABRIR_PROGRAMA_ALT = ('ctrl', 'alt', 'x')
TENTAR_ATALHO_ALTERNATIVO = True

# Antes de digitar o programa, limpa o campo do lançador (CTRL+A + DELETE)
LIMPAR_CAMPO_LANCADOR = True

# Diretório de origem dos pedidos (GM)
DIRETORIO_IMPORTACAO_GM = "\\\\192.168.0.9\\s\\Sawluz\\swedi\\OUTPUT\\GM\\"

# Quantos TABs consecutivos enviar para chegar ao campo de endereço
QTD_TAB_ENDERECO = 5

# Espera por cada botão da etapa final (sem reduzir a confiança visual).
TEMPO_ESPERA_BOTAO_IMPORTACAO = 30

# Tempo máximo (segundos) aguardando a janela "DATASUL Interactive" aparecer
TEMPO_ESPERA_DATASUL = 47

# Tempo (segundos) aguardando a janela do lançador de programas (depois do CTRL+X)
TEMPO_ESPERA_LANCADOR = 6

# Títulos (parciais) da janela do lançador de programas do DATASUL.
# OBS: se o lançador tiver outro título ele AINDA é encontrado, porque a
# automação também aceita "qualquer janela nova" que apareça depois do
# CTRL+X (veja o método aguardar_janela_lancador).
TITULOS_LANCADOR = (
    "Seleção de programas",
    "Selecao de programas",
    "Seleção de Programa",
    "Selecao de Programa",
    "Lançador de programas",
    "Lancador de programas",
)

# Navegadores: usados apenas para NÃO confundir a janela do navegador (tela
# de login do TOTVS) com a janela do DATASUL.
NAVEGADORES = (
    "Microsoft Edge",
    "Google Chrome",
    "Mozilla Firefox",
    "Internet Explorer",
    "Chromium",
)

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
        # Recebidas da interface, nunca pela linha de comando ou arquivo.
        self.totvs_login = os.environ.pop("AUTOMACAO_TOTVS_LOGIN", "").strip()
        self.totvs_senha = os.environ.pop("AUTOMACAO_TOTVS_SENHA", "")
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
        """Minimiza TODAS as janelas abertas.

        Usa WIN+M (e não WIN+D): o WIN+D é um "liga/desliga" - se a área de
        trabalho já estiver visível (ou o comando chegar duas vezes) ele
        RESTAURA as janelas em vez de minimizar. O WIN+M sempre minimiza.

        Depois do atalho, minimiza pelo pygetwindow o que tiver sobrado,
        porque alguns aplicativos (janelas "sempre no topo") ignoram o WIN+M.
        """
        self.log("🔽 Minimizando todas as janelas...")
        try:
            pyautogui.hotkey('win', 'm')
            self.esperar(1)
        except Exception as e:
            self.log_erro(f"Erro ao enviar WIN+M: {e}")

        sobrou = 0
        try:
            for j in gw.getAllWindows():
                if not (j.title or '').strip():
                    continue
                try:
                    if j.visible and not j.isMinimized:
                        j.minimize()
                        sobrou += 1
                except Exception:
                    continue
            self.esperar(0.5)
            if sobrou:
                self.log_debug(f"Minimizadas {sobrou} janela(s) que o WIN+M não pegou")
            self.log_sucesso("Todas as janelas minimizadas")
        except Exception as e:
            self.log_aviso(f"Não consegui conferir as janelas abertas: {e}")
    
    def encontrar_janela(self, titulo, ignorar=()):
        """Procura uma janela cujo título contenha 'titulo'.

        ignorar: trechos que, se aparecerem no título, descartam a janela
        (ex.: não confundir a janela do navegador com a do DATASUL).
        """
        try:
            todas = gw.getAllWindows()
            for j in todas:
                if not j.title:
                    continue
                titulo_janela = j.title.lower()
                if titulo.lower() not in titulo_janela:
                    continue
                if any(x.lower() in titulo_janela for x in ignorar):
                    continue
                return j
        except Exception:
            pass
        return None

    def lista_janelas(self):
        """Lista as janelas abertas (só as que têm título)."""
        try:
            return [j for j in gw.getAllWindows() if (j.title or '').strip()]
        except Exception as e:
            self.log_debug(f"Não consegui listar as janelas: {e}")
            return []

    def janela_por_hwnd(self, hwnd):
        """Encontra a janela aberta pelo identificador (hwnd) do Windows."""
        for j in self.lista_janelas():
            if getattr(j, '_hWnd', None) == hwnd:
                return j
        return None

    def snapshot_janelas(self):
        """Retorna {hwnd: titulo} das janelas abertas AGORA.

        Serve para descobrir, depois, qual janela é NOVA - a do lançador de
        programas que o CTRL+X abre.
        """
        instantaneo = {}
        for j in self.lista_janelas():
            hwnd = getattr(j, '_hWnd', None)
            if hwnd:
                instantaneo[hwnd] = (j.title or '').strip()
        return instantaneo

    def registrar_estado_janelas(self, motivo):
        """Registra título, HWND, visibilidade, minimização e janela em foco."""
        try:
            foreground = ctypes.windll.user32.GetForegroundWindow() if TEM_CTYPES else None
            janelas = self.lista_janelas()
            self.log_debug(f"JANELAS [{motivo}]: total={len(janelas)}; HWND em primeiro plano={foreground}")
            for janela in janelas:
                hwnd = getattr(janela, '_hWnd', None)
                try:
                    detalhes = f"visível={janela.visible}; minimizada={janela.isMinimized}; x={janela.left}; y={janela.top}; w={janela.width}; h={janela.height}"
                except Exception as e:
                    detalhes = f"estado indisponível: {type(e).__name__}: {e!r}"
                self.log_debug(f"Janela: título={janela.title!r}; hwnd={hwnd}; {detalhes}; em_foco={hwnd == foreground}")
            if not janelas:
                self.log_aviso(f"Nenhuma janela com título foi enumerada: {motivo}")
        except Exception:
            self.log_erro(f"Falha ao enumerar janelas ({motivo}):\\n{traceback.format_exc()}")

    def registrar_processos_windows(self):
        """Consulta a lista de processos (equivalente a evidência do Gerenciador)."""
        if os.name != "nt":
            self.log_debug("Consulta tasklist ignorada: sistema operacional não é Windows.")
            return False
        try:
            resultado = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"], capture_output=True,
                text=True, encoding="mbcs", errors="replace", timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
            self.log_debug(f"tasklist: returncode={resultado.returncode}; stderr={resultado.stderr.strip()!r}")
            encontrados = []
            for linha in resultado.stdout.splitlines():
                if any(chave in linha.lower() for chave in ("datasul", "totvs", "progress", "prowin", "webclient")):
                    encontrados.append(linha)
            self.log_debug(f"Processos relacionados encontrados={len(encontrados)}")
            for linha in encontrados:
                self.log_debug(f"Processo Windows: {linha}")
            if not encontrados:
                self.log_aviso("tasklist não encontrou processos com nomes contendo datasul/totvs/progress/prowin/webclient.")
            return bool(encontrados)
        except Exception as e:
            self.log_erro(f"Falha consultando processos via tasklist: {type(e).__name__}: {e!r}")
            return False

    # ========================================
    # JANELA DO DATASUL - BUSCA TOLERANTE
    # ========================================
    TITULOS_DATASUL = ("DATASUL Interactive", "DATASUL Interative")

    def encontrar_janela_datasul(self, silencioso=False):
        """Consulta janelas/processos do Windows, inclusive janelas minimizadas."""
        for janela in self.lista_janelas():
            titulo = (janela.title or '').strip()
            if not any(t.lower() in titulo.lower() for t in self.TITULOS_DATASUL):
                continue
            if any(n.lower() in titulo.lower() for n in NAVEGADORES):
                continue
            if not janela_disponivel(getattr(janela, '_hWnd', None)):
                continue
            if not silencioso:
                self.log_sucesso(f"Janela e processo DATASUL disponíveis: '{titulo}'")
            return janela
        if not silencioso:
            self.log_aviso("Nenhuma janela DATASUL Interactive disponível no Windows.")
            self.log_debug(f"Janelas abertas agora: {[j.title for j in self.lista_janelas()]}")
        return None

    def aguardar_janela_lancador(self, janelas_antes, timeout):
        """Espera abrir a janela do lançador de programas (aberta pelo CTRL+X).

        Estratégia:
        1. procura pelos títulos conhecidos (TITULOS_LANCADOR);
        2. se não achar, aceita qualquer janela NOVA - que não existia antes
           do CTRL+X. É exatamente isso que o atalho faz: abre a caixa para
           digitar o programa do TOTVS.

        Retorna a janela do lançador ou None (timeout).
        """
        self.log(f"   >> Aguardando a janela do lançador de programas (até {timeout}s)...")
        titulos_antes = set(janelas_antes.values())
        limite = time.time() + max(1, timeout)

        while time.time() < limite:
            for titulo in TITULOS_LANCADOR:
                janela = self.encontrar_janela(titulo)
                if janela:
                    self.log_sucesso(f"Lançador encontrado pelo título: '{(janela.title or '').strip()}'")
                    return janela

            for hwnd, titulo in self.snapshot_janelas().items():
                if hwnd in janelas_antes or titulo in titulos_antes:
                    continue
                janela = self.janela_por_hwnd(hwnd)
                if janela:
                    self.log_sucesso(f"Janela NOVA detectada (lançador de programas): '{titulo}'")
                    return janela

            time.sleep(0.5)

        self.log_aviso(f"A janela do lançador não apareceu em {timeout}s")
        return None

    def mostrar_erro_visivel(self, titulo, mensagem):
        """Mostra uma caixa de erro na tela.

        O .exe da automação é compilado sem console, então qualquer exceção
        desaparece sem deixar rastro visível. Isso garante que o usuário veja
        o que aconteceu em vez de achar que "não fez nada".
        """
        try:
            import tkinter as tk
            from tkinter import messagebox
            raiz = tk.Tk()
            raiz.withdraw()
            messagebox.showerror(titulo, mensagem)
            raiz.destroy()
        except Exception as e:
            self.log_aviso(f"Não consegui exibir a caixa de erro: {e}")

    # ========================================
    # FOCO DAS JANELAS (o pyautogui digita na janela ATIVA)
    # ========================================
    def janela_em_foco(self, janela):
        """Só confirma quando o HWND é realmente o primeiro plano do Windows."""
        return janela_em_primeiro_plano(getattr(janela, '_hWnd', None))

    def _forcar_primeiro_plano(self, janela):
        """Força a janela para o primeiro plano pela API do Windows.

        O activate() do pygetwindow é só um pedido: quando o Windows não
        libera a troca de janela ativa ele é ignorado (a janela apenas pisca
        na barra de tarefas) e as teclas seguintes iriam para outro programa.
        O "toque" de ALT abaixo é o truque conhecido para destravar o
        SetForegroundWindow do Windows.
        """
        if not TEM_CTYPES:
            return False
        try:
            hwnd = getattr(janela, '_hWnd', None)
            if not hwnd:
                return False
            u = ctypes.windll.user32
            SW_RESTORE = 9
            try:
                if janela.isMinimized:
                    u.ShowWindow(hwnd, SW_RESTORE)
            except Exception:
                pass
            u.keybd_event(0x12, 0, 0, 0)   # ALT pressionado
            u.keybd_event(0x12, 0, 2, 0)   # ALT solto
            u.SetForegroundWindow(hwnd)
            u.BringWindowToTop(hwnd)
            return True
        except Exception as e:
            self.log_debug(f"Primeiro plano via API do Windows falhou: {e}")
            return False

    def clicar_barra_titulo(self, janela):
        """Último recurso: clicar na barra de título (isso ativa a janela)."""
        try:
            if janela.isMinimized:
                janela.restore()
                self.esperar(0.6)
            x = int(janela.left + janela.width / 2)
            y = int(janela.top + 10)
            largura, altura = pyautogui.size()
            if x < 0 or y < 0 or x >= largura or y >= altura:
                self.log_aviso("Janela fora da área da tela; não vou clicar na barra de título")
                return False
            self.log_debug(f"Clicando na barra de título da janela em ({x}, {y})")
            pyautogui.click(x, y)
            self.esperar(0.4)
            return self.janela_em_foco(janela) is True
        except Exception as e:
            self.log_debug(f"Clique na barra de título falhou: {e}")
            return False

    def trazer_frente(self, janela, tentativas=3, silencioso=True):
        """Restaura, ativa e CONFERE se a janela ficou em primeiro plano.

        Retorna True somente quando a janela está comprovadamente ativa.
        Se o foco não puder ser confirmado, retorna False: nesse caso é
        arriscado digitar, porque as teclas podem cair em outro programa.
        """
        if not janela:
            return False

        titulo = (janela.title or '').strip()
        for tentativa in range(1, max(1, tentativas) + 1):
            try:
                if janela.isMinimized:
                    janela.restore()
                    self.esperar(0.5)
                janela.activate()
            except Exception as e:
                self.log_debug(f"activate() falhou (tentativa {tentativa}): {e}")

            self.esperar(0.4)
            if self.janela_em_foco(janela) is True:
                self.log_debug(f"Janela em primeiro plano: '{titulo}'")
                return True

            # Reforço pela API do Windows
            self._forcar_primeiro_plano(janela)
            self.esperar(0.4)
            if self.janela_em_foco(janela) is True:
                self.log_debug(f"Janela em primeiro plano (via API do Windows): '{titulo}'")
                return True

            if tentativa < tentativas:
                self.log_debug(
                    f"'{titulo}' ainda não está em primeiro plano "
                    f"(tentativa {tentativa}/{tentativas})"
                )

        if self.clicar_barra_titulo(janela):
            self.log_debug(f"Janela ativada pelo clique na barra de título: '{titulo}'")
            return True

        if silencioso:
            self.log_aviso(f"Não confirmei o primeiro plano da janela '{titulo}'")
        else:
            self.log_erro(f"Não consegui trazer a janela '{titulo}' para frente")
        return False

    def garantir_foco_datasul(self):
        """Restaura e confirma foco; nunca envia TAB para uma janela desconhecida."""
        janela = self.encontrar_janela_datasul(silencioso=True)
        if not janela:
            self.log_erro("A janela/processo DATASUL não está disponível!")
            return None
        if (self.trazer_frente(janela, tentativas=3, silencioso=True)
                and janela_disponivel(getattr(janela, '_hWnd', None))
                and self.janela_em_foco(janela) is True):
            self.log_sucesso(f"Foco confirmado no DATASUL: '{janela.title}'")
            return janela
        self.log_erro("Foco não confirmado no DATASUL; nenhuma tecla será enviada.")
        return None

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
        """Usa o mesmo fluxo de abertura da importação."""
        return self._abrir_datasul_com_navegador() is not None

    def _login_totvs_navegador(self):
        """Abre o Edge, acessa o TOTVS, preenche login/senha, clica em Entrar
        e trata o popup 'Abrir aplicativo'. NÃO aguarda a janela DATASUL.
        Guarda o driver em self._driver_login (feche com _fechar_driver_login)."""
        if not self.totvs_login or not self.totvs_senha:
            self.log_erro("Preencha login e senha na aba Acesso TOTVS antes de iniciar.")
            self.mostrar_erro_visivel(
                "Acesso TOTVS", "DATASUL não está disponível. Preencha login e senha "
                "na aba Acesso TOTVS e inicie novamente.")
            return False
        sucesso = False
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
            self.log("   >> Preenchendo login informado na interface...")
            campo_login = wait.until(
                EC.element_to_be_clickable((By.ID, "txtUsername"))
            )
            campo_login.clear()
            campo_login.send_keys(self.totvs_login)
            
            # PASSO 2: Preencher SENHA
            self.log("   >> Preenchendo senha...")
            campo_senha = wait.until(EC.element_to_be_clickable((By.ID, "txtPassword")))
            campo_senha.clear()
            campo_senha.send_keys(self.totvs_senha)
            
            # PASSO 3: Clicar em ENTRAR
            self.log("   >> Clicando em 'Entrar'...")
            btn_entrar = wait.until(EC.element_to_be_clickable((By.ID, "btnEntrar")))
            btn_entrar.click()
            
            # O popup nativo do Edge não é acessível pelo DOM do Selenium.
            sucesso = self.tratar_popup_abrir_aplicativo()
            return sucesso

        except TimeoutException:
            self.log_erro("Timeout ao carregar página de login!")
            return False
        except NoSuchElementException:
            self.log_erro("Campo de login, senha ou botão Entrar não encontrado.")
            return False
        except Exception as e:
            # Não registrar detalhes do WebDriver que possam conter credenciais.
            self.log_erro(f"Falha ao abrir TOTVS via navegador ({type(e).__name__}).")
            return False
        finally:
            if not sucesso:
                self._fechar_driver_login()

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
        """Espera abrir.png; sem atalhos cegos quando a imagem não aparece."""
        imagens = [os.path.join(DIR_IMG, "abrir.png"),
                   os.path.join(DIR_IMG, "abrir_popup.png")]
        imagens = [imagem for imagem in imagens if os.path.isfile(imagem)]
        if not imagens:
            self.log_erro("Coloque abrir.png na pasta img (abrir_popup.png também é aceito).")
            return False
        self.log(f"   >> Procurando popup Abrir após Entrar; timeout={TEMPO_ESPERA_ABRIR}s; imagens existentes={[os.path.basename(x) for x in imagens]}; resolução={pyautogui.size()}")
        for imagem in imagens:
            try:
                self.log_debug(f"Imagem popup: {imagem}; tamanho={os.path.getsize(imagem)} bytes")
            except OSError as e:
                self.log_aviso(f"Não consegui ler metadados da imagem {imagem}: {e!r}")
        limite = time.monotonic() + TEMPO_ESPERA_ABRIR
        tentativa = 0
        ultimo_status = None
        while time.monotonic() < limite:
            tentativa += 1
            # Instalações com permissão já salva podem abrir sem popup.
            janela = self.encontrar_janela_datasul(silencioso=True)
            if janela:
                self.log_sucesso(f"DATASUL já detectado durante espera do popup: {janela.title!r}; hwnd={getattr(janela, '_hWnd', None)}")
                return True
            for imagem in imagens:
                try:
                    pos = pyautogui.locateCenterOnScreen(imagem, confidence=0.9)
                    status = f"não encontrado (confidence=0.9, tentativa={tentativa})" if not pos else f"encontrado em {pos} (confidence=0.9, tentativa={tentativa})"
                    if status != ultimo_status:
                        self.log_debug(f"Busca visual de {os.path.basename(imagem)}: {status}")
                        ultimo_status = status
                except Exception as e:
                    pos = None
                    self.log_aviso(f"Erro ao procurar imagem {os.path.basename(imagem)} na tentativa {tentativa}: {type(e).__name__}: {e!r}")
                if pos:
                    self.log_debug(f"Clicando no centro do popup em {pos}; imagem={imagem}")
                    pyautogui.click(pos)
                    self.log_sucesso(f"Clique enviado para {os.path.basename(imagem)} em {pos}")
                    self.log(f"Aguardando {TEMPO_APOS_CLIQUE_POPUP}s após clicar no popup antes de procurar a janela DATASUL...")
                    for segundo in range(1, TEMPO_APOS_CLIQUE_POPUP + 1):
                        time.sleep(1)
                        if segundo % 10 == 0 or segundo == TEMPO_APOS_CLIQUE_POPUP:
                            self.log_debug(f"Espera pós-popup: {segundo}/{TEMPO_APOS_CLIQUE_POPUP}s")
                    self.log_sucesso("Espera pós-popup concluída; agora será feita a busca da janela DATASUL.")
                    return True
            if tentativa % 10 == 0:
                self.log_debug(f"Popup ainda não encontrado após {tentativa} tentativas; tempo restante={max(0, limite-time.monotonic()):.1f}s")
            time.sleep(0.5)
        self.log_erro(f"Timeout procurando popup Abrir: {TEMPO_ESPERA_ABRIR}s, {tentativa} tentativas, imagens={imagens!r}, última busca={ultimo_status!r}")
        self.registrar_estado_janelas("timeout esperando popup Abrir")
        try:
            if getattr(self, '_driver_login', None):
                self.log_debug(f"Estado final Edge/Selenium: URL={self._driver_login.current_url!r}; título={self._driver_login.title!r}; handles={self._driver_login.window_handles!r}")
        except Exception as e:
            self.log_aviso(f"Não consegui coletar estado final do Edge: {type(e).__name__}: {e!r}")
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
        
        # VERIFICAÇÃO 2: alguma janela do DATASUL está aberta?
        self.log("🔍 Procurando janela do DATASUL...")
        janela = self.encontrar_janela_datasul()

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
            
            janela = self.encontrar_janela_datasul(silencioso=True)
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
        
        if not self.garantir_foco_datasul():
            return False
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
    def _abrir_datasul_com_navegador(self):
        """Abre o TOTVS pelo navegador e espera a janela do DATASUL aparecer.

        Retorna a janela do DATASUL ou None (já loga o erro e mostra a caixa
        de aviso na tela, porque o .exe roda sem console).
        """
        self.log("🌐 Abrindo TOTVS (login -> senha -> Entrar -> popup)...")

        if not self._login_totvs_navegador():
            self.log_erro("❌ Falha ao abrir/logar no TOTVS!")
            self.log_erro(f"   Verifique: {EDGE_DRIVER_PATH} existe? A versão do driver bate com o Edge instalado?")
            self.mostrar_erro_visivel(
                "Importar Pedido - ERRO",
                "Não foi possível abrir/logar no TOTVS pelo navegador.\n\n"
                f"Driver esperado: {EDGE_DRIVER_PATH}\n"
                f"Log: {ARQUIVO_LOG}"
            )
            return None

        self.log(f"   >> Aguardando a janela do DATASUL (até {TEMPO_ESPERA_DATASUL}s)...")
        janela = None
        try:
            for i in range(TEMPO_ESPERA_DATASUL):
                time.sleep(1)
                janela = self.encontrar_janela_datasul(silencioso=True)
                if janela:
                    self.log_sucesso(f"Janela do DATASUL apareceu após {i + 1}s!")
                    break
        finally:
            self._fechar_driver_login()

        if not janela:
            self.log_erro("❌ A janela do DATASUL não apareceu no tempo esperado!")
            self.mostrar_erro_visivel(
                "Importar Pedido - ERRO",
                f"A janela do DATASUL não apareceu em {TEMPO_ESPERA_DATASUL}s.\n\n"
                "Abra o TOTVS manualmente e clique em START de novo.\n"
                f"Log (lista as janelas abertas): {ARQUIVO_LOG}"
            )
        return janela

    def abrir_programa_no_totvs(self, programa):
        """CTRL+X -> janela do lançador -> digita o programa -> ENTER.

        Retorna True se o programa foi digitado (mesmo quando a janela do
        lançador não é localizada) e False quando o DATASUL não pôde ser
        colocado em primeiro plano (aí é melhor parar do que digitar às
        cegas em outro programa).
        """
        self.log("=" * 60)
        self.log(f"⌨️ ABRINDO O PROGRAMA {programa} NO TOTVS")
        self.log("=" * 60)

        atalhos = [ATALHO_ABRIR_PROGRAMA]
        if TENTAR_ATALHO_ALTERNATIVO and ATALHO_ABRIR_PROGRAMA_ALT not in atalhos:
            atalhos.append(ATALHO_ABRIR_PROGRAMA_ALT)

        janelas_antes = self.snapshot_janelas()
        janela_lancador = None

        for indice, atalho in enumerate(atalhos):
            # O atalho só chega no TOTVS se o DATASUL for a janela ATIVA
            if not self.garantir_foco_datasul():
                return False

            nome = '+'.join(k.upper() for k in atalho)
            self.log(f"⌨️ {nome} (abrir o lançador de programas)...")
            try:
                pyautogui.hotkey(*atalho)
            except Exception as e:
                self.log_erro(f"Falha ao enviar {nome}: {e}")
                continue
            self.esperar(1)

            janela_lancador = self.aguardar_janela_lancador(janelas_antes, TEMPO_ESPERA_LANCADOR)
            if janela_lancador:
                break

            if indice < len(atalhos) - 1:
                proximo = '+'.join(k.upper() for k in atalhos[indice + 1])
                self.log_aviso(f"A janela do lançador não apareceu com {nome}. Tentando {proximo}...")
            else:
                self.log_aviso(
                    "Nenhuma janela nova apareceu depois do atalho. Vou digitar o "
                    "programa mesmo assim: o campo pode estar na própria janela do DATASUL."
                )

        # Se a janela do lançador apareceu, ela precisa estar ATIVA para
        # receber o código do programa
        if janela_lancador:
            self.log("🔺 Trazendo a janela do lançador para frente...")
            if not self.trazer_frente(janela_lancador, tentativas=3, silencioso=False):
                return False
        elif not self.garantir_foco_datasul():
            return False

        if LIMPAR_CAMPO_LANCADOR:
            try:
                pyautogui.hotkey('ctrl', 'a')
                self.esperar(0.2)
                pyautogui.press('delete')
                self.esperar(0.2)
            except Exception as e:
                self.log_debug(f"Não consegui limpar o campo do lançador: {e}")

        self.log(f"⌨️ Digitando {programa}...")
        pyautogui.typewrite(programa, interval=0.05)
        self.esperar(TEMPO_CURTO)

        self.log("⌨️ ENTER (abrir o programa)...")
        pyautogui.press('enter')
        self.log(f"   >> Aguardando {TEMPO_ESPERA_PROGRAMA}s o programa carregar...")
        self.esperar(TEMPO_ESPERA_PROGRAMA)

        janela_programa = self.encontrar_janela(programa)
        if janela_programa:
            self.log_sucesso(f"Programa aberto: '{(janela_programa.title or '').strip()}'")
        else:
            self.log_aviso(f"Não vi '{programa}' no título de nenhuma janela; seguindo o fluxo.")
        return True

    def clicar_imagem_importacao(self, nome):
        """Espera e clica uma vez no botão, sem ENTER ou confiança reduzida."""
        caminho = os.path.join(DIR_IMG, nome)
        if not os.path.isfile(caminho):
            self.log_erro(f"Imagem obrigatória ausente: {caminho}")
            return False
        self.log(f"🖼️ Procurando {nome} (até {TEMPO_ESPERA_BOTAO_IMPORTACAO}s, confiança 90%)...")
        limite = time.monotonic() + TEMPO_ESPERA_BOTAO_IMPORTACAO
        while time.monotonic() < limite:
            try:
                pos = pyautogui.locateCenterOnScreen(caminho, confidence=0.9)
            except pyautogui.ImageNotFoundException:
                pos = None
            except Exception as erro:
                self.log_erro(f"Falha ao procurar {nome}: {type(erro).__name__}")
                return False
            if pos:
                try:
                    pyautogui.click(pos)
                except Exception as erro:
                    self.log_erro(f"Falha ao clicar em {nome}: {type(erro).__name__}")
                    return False
                self.log_sucesso(f"Clique enviado para {nome} em {pos}")
                self.esperar(TEMPO_CURTO)
                return True
            time.sleep(0.5)
        self.log_erro(f"Imagem {nome} não encontrada na tela em {TEMPO_ESPERA_BOTAO_IMPORTACAO}s.")
        return False

    def importar_pedido(self):
        """Fluxo da aba "Importar Pedido HONDA & GM" (botão START vermelho).

        Ordem do processo:

        1. Procura uma janela disponível do "DATASUL Interactive";
        2. Se não existir, minimiza as janelas, abre o TOTVS pelo navegador
           e aguarda até TEMPO_ESPERA_DATASUL;
        3. Traz a janela do DATASUL para a FRENTE e confirma que ela é a
           janela ativa (senão o CTRL+X iria para o programa errado);
        4. CTRL+X -> abre a janela do lançador de programas;
        5. Digita ESPD0001 -> ENTER;
        6. 1x TAB -> ENTER para confirmar a tela inicial; depois
           QTD_TAB_ENDERECO x TAB -> ENTER -> cola o diretório GM
           -> ENTER -> 4x TAB -> seta ↓ -> seta ↑;
        7. Localiza/clica abrir_popup.png, depois executar.png;
        8. Encerra sem ENTER adicional e reabre a interface gráfica.
           O resultado da importação no TOTVS não é verificado nesta etapa.

        Retorna True se o fluxo rodou até o fim; False se parou em algum erro
        (a interface é reaberta nos dois casos).
        """
        self.log("\n" + "=" * 60)
        self.log("🚗 IMPORTAÇÃO DE PEDIDO - HONDA & GM")
        self.log("=" * 60)

        diretorio = DIRETORIO_IMPORTACAO_GM

        # --------------------------------------------------
        # PASSO 1: procurar DATASUL ANTES de minimizar/abrir o navegador.
        # A busca usa as janelas nativas do Windows; em caso negativo, registra
        # também a lista de processos para revelar clientes em outra sessão.
        # --------------------------------------------------
        self.log("🔍 Procurando primeiro uma janela DATASUL Interactive já aberta...")
        self.registrar_estado_janelas("antes de qualquer minimização ou abertura do Edge")
        janela = self.encontrar_janela_datasul()

        if janela:
            self.log_sucesso("Janela do DATASUL já estava aberta; não vou iniciar outra sessão.")
        else:
            self.log_aviso("DATASUL não localizado nas janelas. Consultando processos do Windows antes de iniciar do zero.")
            processo_relacionado = self.registrar_processos_windows()
            if processo_relacionado:
                self.log_aviso("Há processo TOTVS/Progress ativo, mas nenhuma janela DATASUL disponível. O processo isolado não impede iniciar pelo navegador; nenhum processo será encerrado.")
            # Uma janela pode ter aparecido durante a consulta de processos.
            janela = self.encontrar_janela_datasul(silencioso=True)
            if janela:
                self.log_sucesso("Janela DATASUL apareceu durante a consulta; reutilizando a sessão.")
            else:
                self.log("Nenhuma janela DATASUL disponível; iniciando o fluxo completo pelo Edge.")
                self.log("🔽 Minimizando janelas somente após confirmar que não achou o DATASUL...")
                self.minimizar_todas_janelas()
                janela = self._abrir_datasul_com_navegador()
                if not janela:
                    self.reabrir_interface()
                    return False

        # --------------------------------------------------
        # PASSO 3: trazer para frente e CONFIRMAR o foco
        # --------------------------------------------------
        self.log("🔺 Trazendo a janela do DATASUL para frente...")
        janela = self.garantir_foco_datasul()
        if not janela:
            self.log_erro("❌ Não consegui deixar o DATASUL em primeiro plano!")
            self.mostrar_erro_visivel(
                "Importar Pedido - ERRO",
                "Não consegui ativar a janela do DATASUL Interactive.\n\n"
                "Clique nela manualmente e clique em START de novo.\n"
                f"Log: {ARQUIVO_LOG}"
            )
            self.reabrir_interface()
            return False
        self.esperar(TEMPO_MEDIO)

        # --------------------------------------------------
        # PASSOS 4 e 5: CTRL+X -> lançador -> ESPD0001 -> ENTER
        # --------------------------------------------------
        if not self.abrir_programa_no_totvs(PROGRAMA_IMPORTACAO):
            self.mostrar_erro_visivel(
                "Importar Pedido - ERRO",
                "Não consegui deixar o DATASUL em primeiro plano para abrir o "
                f"programa {PROGRAMA_IMPORTACAO}.\n\n"
                "Clique na janela do DATASUL e clique em START de novo.\n"
                f"Log: {ARQUIVO_LOG}"
            )
            self.reabrir_interface()
            return False

        # --------------------------------------------------
        # PASSO 6.1: confirmar a tela inicial do ESPD0001 com 1x TAB + ENTER
        # --------------------------------------------------
        self.log("⌨️ 1x TAB (confirmar a tela inicial do ESPD0001)...")
        pyautogui.press('tab')
        self.esperar(TEMPO_CURTO)
        self.log("⌨️ ENTER (após 1x TAB)...")
        pyautogui.press('enter')
        self.esperar(TEMPO_CURTO)

        # --------------------------------------------------
        # PASSO 6.2: TABs consecutivos até o campo de endereço (sem ENTER entre eles)
        # --------------------------------------------------
        self.log(f"⌨️ {QTD_TAB_ENDERECO}x TAB (até o campo de endereço)...")
        for i in range(QTD_TAB_ENDERECO):
            pyautogui.press('tab')
            self.log(f"   >> TAB {i + 1}/{QTD_TAB_ENDERECO} enviado")
            self.esperar(TEMPO_CURTO)

        # --------------------------------------------------
        # PASSO 6.2: ENTER, colar o diretório e confirmar com ENTER
        # --------------------------------------------------
        self.log("⌨️ ENTER (antes de colar o diretório)...")
        pyautogui.press('enter')
        self.esperar(TEMPO_CURTO)
        self.log(f"📋 Colando diretório: {diretorio}")
        try:
            pyperclip.copy(diretorio)
        except Exception as e:
            self.log_erro(f"Falha ao copiar diretório: {type(e).__name__}; importação interrompida.")
            self.mostrar_erro_visivel("Importar Pedido - ERRO", "Não foi possível copiar o diretório GM. Nenhum conteúdo será colado.")
            self.reabrir_interface()
            return False
        self.esperar(0.3)
        pyautogui.hotkey('ctrl', 'v')
        self.esperar(TEMPO_CURTO)
        self.log("⌨️ ENTER (após colar o diretório)...")
        pyautogui.press('enter')
        self.esperar(TEMPO_CURTO)

        # --------------------------------------------------
        # PASSO 6.3: 4x TAB
        # --------------------------------------------------
        self.log("⌨️ 4x TAB...")
        for _ in range(4):
            pyautogui.press('tab')
            self.esperar(0.3)

        # --------------------------------------------------
        # PASSO 6.4: seta para baixo, depois seta para cima
        # --------------------------------------------------
        self.log("⌨️ Seta para BAIXO...")
        pyautogui.press('down')
        self.esperar(TEMPO_CURTO)
        self.log("⌨️ Seta para CIMA...")
        pyautogui.press('up')
        self.esperar(TEMPO_CURTO)

        # --------------------------------------------------
        # PASSO 6.5: Abrir e Executar por imagem, nesta ordem (sem ENTER final)
        # --------------------------------------------------
        for nome in ('abrir_popup.png', 'executar.png'):
            if not self.clicar_imagem_importacao(nome):
                self.mostrar_erro_visivel(
                    "Importar Pedido - ERRO",
                    f"Não foi possível localizar/clicar em {nome}.\n"
                    "Confira o arquivo na pasta img e se o botão está visível na tela.\n"
                    "A sequência foi interrompida, sem confirmação por ENTER.\n"
                    f"Log: {ARQUIVO_LOG}"
                )
                self.reabrir_interface()
                return False

        self.log_sucesso("Sequência de importação encerrada após o clique em Executar; resultado no TOTVS não verificado.")
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
    modo_importar = len(sys.argv) > 1 and sys.argv[1].lower() in ("importar", "importacao", "import")

    # O .exe roda sem console: sem este bloco qualquer exceção some no ar e
    # o usuário só vê a interface fechar "sem fazer nada".
    try:
        if modo_importar:
            bot.importar_pedido()
        else:
            bot.executar()
    except Exception:
        erro = traceback.format_exc()
        bot.log_erro("EXCEÇÃO NÃO TRATADA:\n" + erro)
        bot.mostrar_erro_visivel(
            "Automação TOTVS - ERRO",
            "A automação parou com um erro inesperado.\n\n"
            f"{erro}\n"
            f"Log completo: {ARQUIVO_LOG}"
        )
        bot.reabrir_interface()
        sys.exit(1)
