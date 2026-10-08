"""Armazenamento de dados sensíveis protegido pela DPAPI do usuário Windows.

Mesmo padrão da parte TOTVS (ver totvs/credenciais.py, que guarda o acesso do
DATASUL no mesmo formato): o blob fica em %LOCALAPPDATA%\\AutomacaoTOTVS\\,
fora da pasta do projeto, vinculado à conta Windows atual. Não há senha em
texto puro no código, nos arquivos do projeto ou no log, nem fallback para
armazenamento sem proteção.

Este módulo é genérico (guarda bytes por nome de arquivo) para atender às
partes sem que elas dependam umas das outras: cada parte define o que guarda.
"""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import tempfile


class ErroCredenciais(Exception):
    """Falha de armazenamento; nunca inclui o conteúdo das credenciais."""


class _Blob(ctypes.Structure):
    _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_ubyte))]


def _dpapi(dados, proteger):
    if os.name != 'nt':
        raise ErroCredenciais('O armazenamento protegido requer Windows.')
    crypt32 = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    blob_ptr = ctypes.POINTER(_Blob)
    crypt32.CryptProtectData.argtypes = [blob_ptr, wintypes.LPCWSTR, blob_ptr,
                                        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, blob_ptr]
    crypt32.CryptUnprotectData.argtypes = [blob_ptr, ctypes.c_void_p, blob_ptr,
                                          ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, blob_ptr]
    crypt32.CryptProtectData.restype = crypt32.CryptUnprotectData.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    buffer = ctypes.create_string_buffer(dados)
    entrada = _Blob(len(dados), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    saida = _Blob()
    funcao = crypt32.CryptProtectData if proteger else crypt32.CryptUnprotectData
    # CRYPTPROTECT_UI_FORBIDDEN; sem LOCAL_MACHINE: vincula ao usuário atual.
    if not funcao(ctypes.byref(entrada), None, None, None, None, 1, ctypes.byref(saida)):
        raise ErroCredenciais('Não foi possível acessar a proteção do Windows.')
    try:
        return ctypes.string_at(saida.pbData, saida.cbData)
    finally:
        kernel32.LocalFree(saida.pbData)


def caminho_armazenamento(nome_arquivo):
    """Caminho do arquivo protegido, fora da pasta do projeto (só no Windows)."""
    local = os.environ.get('LOCALAPPDATA')
    if os.name != 'nt' or not local:
        raise ErroCredenciais('O armazenamento protegido requer um perfil Windows.')
    return Path(local) / 'AutomacaoTOTVS' / nome_arquivo


def salvar_dados(nome_arquivo, dados):
    """Grava o blob protegido de forma atômica; nunca grava texto puro."""
    temporario = None
    try:
        arquivo = caminho_armazenamento(nome_arquivo)
        protegido = _dpapi(dados, True)  # Nunca escreve texto puro, nem como fallback.
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=arquivo.parent, delete=False) as f:
            temporario = Path(f.name)
            f.write(protegido)
        os.replace(temporario, arquivo)
    except ErroCredenciais:
        raise
    except Exception:
        raise ErroCredenciais('Não foi possível salvar os dados com a proteção do Windows.') from None
    finally:
        if temporario is not None:
            try:
                temporario.unlink(missing_ok=True)
            except OSError:
                pass  # Contém somente o blob protegido; preserva o erro original.


def carregar_dados(nome_arquivo):
    """Devolve os bytes protegidos; None se ainda não existe nada salvo."""
    try:
        arquivo = caminho_armazenamento(nome_arquivo)
        if not arquivo.exists():
            return None
        return _dpapi(arquivo.read_bytes(), False)
    except ErroCredenciais:
        raise
    except Exception:
        raise ErroCredenciais('Não foi possível carregar os dados salvos. Informe e salve novamente.') from None


def apagar_dados(nome_arquivo):
    """Apaga o arquivo protegido, inclusive quando ele não existe."""
    try:
        caminho_armazenamento(nome_arquivo).unlink(missing_ok=True)
    except Exception:
        raise ErroCredenciais('Não foi possível apagar os dados salvos.') from None
