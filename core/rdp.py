"""Localiza e abre arquivos .rdp que ficam na área de trabalho.

Compartilhado pelas partes (TOTVS e SWProgramação). A área de trabalho pode
aparecer como 'Desktop' ou 'Área de Trabalho' (Windows em português), e com
OneDrive ela fica dentro da pasta OneDrive. No Windows, a pasta real da área
de trabalho é consultada primeiro pela API de pastas conhecidas (SHGetKnownFolderPath),
o que cobre redirecionamentos do OneDrive e perfis fora do caminho padrão.
"""
import os

PASTAS_DESKTOP = (
    ('Desktop',),
    ('OneDrive', 'Desktop'),
    ('Área de Trabalho',),
    ('OneDrive', 'Área de Trabalho'),
)


class RdpNaoEncontrado(Exception):
    """O .rdp não estava em nenhum dos locais possíveis da área de trabalho."""


def _desktop_conhecido():
    """Pasta real da área de trabalho no Windows; None fora do Windows ou em falha.

    Usa SHGetKnownFolderPath (FOLDERID_Desktop), então funciona mesmo quando a
    área de trabalho foi redirecionada (OneDrive) ou está em outro caminho.
    Qualquer erro devolve None: a busca pelos caminhos padrão continua valendo.
    """
    if os.name != 'nt':
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class GUID(ctypes.Structure):
            _fields_ = [('Data1', wintypes.DWORD),
                        ('Data2', wintypes.WORD),
                        ('Data3', wintypes.WORD),
                        ('Data4', ctypes.c_ubyte * 8)]

        # FOLDERID_Desktop = {754AC886-DF64-4CBA-86B5-F7FBF4FBCEF5}
        desktop = GUID(0x754AC886, 0xDF64, 0x4CBA,
                       (ctypes.c_ubyte * 8)(0x86, 0xB5, 0xF7, 0xFB, 0xF4, 0xFB, 0xCE, 0xF5))
        shell32 = ctypes.WinDLL('shell32', use_last_error=True)
        ole32 = ctypes.WinDLL('ole32', use_last_error=True)
        ponteiro = wintypes.LPWSTR()
        shell32.SHGetKnownFolderPath.argtypes = [
            ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE,
            ctypes.POINTER(wintypes.LPWSTR)]
        shell32.SHGetKnownFolderPath.restype = wintypes.HRESULT
        ole32.CoTaskMemFree.argtypes = [wintypes.LPWSTR]
        hr = shell32.SHGetKnownFolderPath(ctypes.byref(desktop), 0, None, ctypes.byref(ponteiro))
        if hr != 0 or not ponteiro.value:
            return None
        caminho = ponteiro.value
        ole32.CoTaskMemFree(ponteiro)
        return caminho
    except Exception:
        return None


def caminhos_candidatos(nome_arquivo, home=None):
    home = home or os.path.expanduser('~')
    candidatos = []
    conhecido = _desktop_conhecido()
    if conhecido:
        candidatos.append(os.path.join(conhecido, nome_arquivo))
    candidatos.extend(os.path.join(home, *partes, nome_arquivo) for partes in PASTAS_DESKTOP)
    return list(dict.fromkeys(candidatos))  # sem repetidos, mantendo a ordem


def caminho_rdp(nome_arquivo, home=None):
    """Devolve o primeiro caminho existente; senão levanta RdpNaoEncontrado."""
    candidatos = caminhos_candidatos(nome_arquivo, home)
    for caminho in candidatos:
        if os.path.isfile(caminho):
            return caminho
    raise RdpNaoEncontrado(
        f'Não achei o {nome_arquivo} na área de trabalho. Procurei em:\n  '
        + '\n  '.join(candidatos))


def abrir_rdp(caminho):
    """Igual a dar dois cliques no arquivo: abre com a Conexão de Área de Trabalho Remota."""
    if not hasattr(os, 'startfile'):
        raise RuntimeError('Abrir o .rdp requer Windows (Conexão de Área de Trabalho Remota).')
    os.startfile(caminho)  # existe só no Windows
