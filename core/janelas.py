"""Validação das janelas nativas, sem depender da tela do Gerenciador de Tarefas."""
import ctypes
from ctypes import wintypes
import os

NAVEGADORES_EXE = {"msedge.exe", "chrome.exe", "firefox.exe", "iexplore.exe", "chromium.exe"}


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
