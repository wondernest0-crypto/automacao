"""Acesso local protegido pela DPAPI do usuário Windows, fora do projeto."""
import ctypes
from ctypes import wintypes
import json
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


def _arquivo():
    local = os.environ.get('LOCALAPPDATA')
    if os.name != 'nt' or not local:
        raise ErroCredenciais('O armazenamento protegido requer um perfil Windows.')
    return Path(local) / 'AutomacaoTOTVS' / 'acesso.dpapi'


def carregar_credenciais():
    try:
        arquivo = _arquivo()
        if not arquivo.exists():
            return 'deivid', ''
        dados = json.loads(_dpapi(arquivo.read_bytes(), False).decode('utf-8'))
        if not isinstance(dados, dict) or not all(isinstance(dados.get(k), str) for k in ('login', 'senha')):
            raise ValueError()
        return dados['login'], dados['senha']
    except Exception:
        raise ErroCredenciais('Não foi possível carregar o acesso salvo. Informe e salve novamente.') from None


def salvar_credenciais(login, senha):
    temporario = None
    try:
        arquivo = _arquivo()
        dados = json.dumps({'login': login.strip(), 'senha': senha}, ensure_ascii=False).encode('utf-8')
        protegido = _dpapi(dados, True)  # Nunca escreve texto puro, nem como fallback.
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=arquivo.parent, delete=False) as f:
            temporario = Path(f.name)
            f.write(protegido)
        os.replace(temporario, arquivo)
    except Exception:
        raise ErroCredenciais('Não foi possível salvar o acesso com a proteção do Windows.') from None
    finally:
        if temporario is not None:
            try:
                temporario.unlink(missing_ok=True)
            except OSError:
                pass  # Contém somente o blob protegido; preserva o erro original.


def esquecer_credenciais():
    try:
        _arquivo().unlink(missing_ok=True)
    except Exception:
        raise ErroCredenciais('Não foi possível apagar o acesso salvo.') from None
