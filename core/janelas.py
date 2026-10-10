"""Validação e ativação das janelas nativas, sem depender do Gerenciador de Tarefas."""
import ctypes
from ctypes import wintypes
import importlib
import os

NAVEGADORES_EXE = {"msedge.exe", "chrome.exe", "firefox.exe", "iexplore.exe", "chromium.exe"}

# Títulos (parciais) da janela da Conexão de Área de Trabalho Remota (mstsc), em
# português e em inglês. A parte TOTVS mantém a própria lista em
# totvs/automacao.py; esta é a lista compartilhada (core não importa as partes).
TITULOS_RDP = (
    "Conexão de Área de Trabalho Remota",
    "Conexão de Area de Trabalho Remota",
    "Conexao de Area de Trabalho Remota",
    "Remote Desktop Connection",
)


def _pygetwindow():
    """pygetwindow, ou None quando a biblioteca não está instalada."""
    try:
        return importlib.import_module("pygetwindow")
    except Exception:
        return None


def janelas_por_titulo(titulos=TITULOS_RDP):
    """Janelas abertas cujo título contém um dos trechos (maiúsculas ignoradas).

    Sem pygetwindow, sem janelas ou com falha de consulta devolve lista vazia:
    quem chama decide o que fazer, e o fluxo não quebra por causa disso.
    """
    gw = _pygetwindow()
    if gw is None:
        return []
    achadas = []
    vistos = set()
    for titulo in titulos:
        try:
            janelas = gw.getWindowsWithTitle(titulo)
        except Exception:
            continue
        for janela in janelas:
            chave = getattr(janela, "_hWnd", None) or id(janela)
            if chave in vistos:
                continue
            vistos.add(chave)
            achadas.append(janela)
    return achadas


def trazer_para_frente(janela, maximizar=False):
    """Restaura e ativa a janela. True somente se ela ficou em primeiro plano.

    A automação por imagem só enxerga o que está visível: com a janela
    minimizada, atrás de outra ou parcialmente escondida, nenhuma captura casa.

    `maximizar` vem desligado de propósito: mudar o tamanho da janela da VPS
    muda a escala do conteúdo remoto e quebra a comparação com a captura, que
    foi feita no tamanho em que a janela estava.
    """
    if not janela:
        return False
    try:
        if getattr(janela, "isMinimized", False):
            janela.restore()
        if maximizar and not getattr(janela, "isMaximized", False):
            janela.maximize()
        janela.activate()
    except Exception:
        pass
    return janela_em_primeiro_plano(getattr(janela, "_hWnd", None))


def _apis():
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    for nome in ("IsWindow", "IsWindowVisible", "IsHungAppWindow"):
        funcao = getattr(user32, nome)
        funcao.argtypes = [wintypes.HWND]
        funcao.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    return user32, kernel32


def janela_disponivel(hwnd):
    """Exige HWND visível (inclusive minimizado), responsivo e processo vivo.

    Rejeita navegadores mesmo se o título da aba for DATASUL Interactive.
    Sem permissão para consultar o processo, falha de forma conservadora.
    """
    if os.name != "nt" or not hwnd:
        return False
    try:
        user32, kernel32 = _apis()
        if not user32.IsWindow(hwnd) or not user32.IsWindowVisible(hwnd):
            return False
        if user32.IsHungAppWindow(hwnd):
            return False
        pid = wintypes.DWORD()
        if not user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid)) or not pid.value:
            return False
        # SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION
        processo = kernel32.OpenProcess(0x00100000 | 0x1000, False, pid.value)
        if not processo:
            return False
        try:
            if kernel32.WaitForSingleObject(processo, 0) != 258:  # WAIT_TIMEOUT = vivo
                return False
            caminho = ctypes.create_unicode_buffer(32768)
            tamanho = wintypes.DWORD(len(caminho))
            if not kernel32.QueryFullProcessImageNameW(processo, 0, caminho, ctypes.byref(tamanho)):
                return False
            executavel = caminho.value.replace("\\", "/").rsplit("/", 1)[-1].lower()
            return executavel not in NAVEGADORES_EXE
        finally:
            kernel32.CloseHandle(processo)
    except (OSError, AttributeError):
        return False


def janela_em_primeiro_plano(hwnd):
    """Não considera uma falha de consulta como confirmação de foco."""
    if os.name != "nt" or not hwnd:
        return False
    try:
        user32, _ = _apis()
        return user32.GetForegroundWindow() == hwnd
    except (OSError, AttributeError):
        return False
