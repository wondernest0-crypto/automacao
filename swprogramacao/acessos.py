"""Acesso da VPS (login do Windows e login do EDI) para o passo 1.

Ordem de leitura:
  1. Variáveis de ambiente SW_WINDOWS_LOGIN, SW_WINDOWS_SENHA, SW_EDI_LOGIN
     e SW_EDI_SENHA (útil para rodar sem prompt, inclusive em .bat/.exe);
  2. Arquivo protegido pela DPAPI do usuário Windows
     (%LOCALAPPDATA%\\AutomacaoTOTVS\\acesso_sw.dpapi), salvo com
     `python -m swprogramacao --salvar-acesso`;
  3. Nada salvo: a linha de comando pede no terminal, como antes.

Segurança (mesmo padrão da parte TOTVS): nenhuma senha em texto puro no
código, nos arquivos do projeto ou no log; o arquivo fica fora da pasta do
projeto e vinculado à conta Windows de quem roda. Fora do Windows não existe
DPAPI, então o acesso é sempre pedido no terminal.
"""
import json
import os

from core import credenciais as core_cred
from swprogramacao import fluxo

NOME_ARQUIVO = 'acesso_sw.dpapi'

VAR_WINDOWS_LOGIN = 'SW_WINDOWS_LOGIN'
VAR_WINDOWS_SENHA = 'SW_WINDOWS_SENHA'
VAR_EDI_LOGIN = 'SW_EDI_LOGIN'
VAR_EDI_SENHA = 'SW_EDI_SENHA'
VARIAVEIS = (VAR_WINDOWS_LOGIN, VAR_WINDOWS_SENHA, VAR_EDI_LOGIN, VAR_EDI_SENHA)

ErroAcesso = core_cred.ErroCredenciais


def _completo(acesso):
    return all([acesso.windows_login, acesso.windows_senha,
                acesso.edi_login, acesso.edi_senha])


def _do_ambiente():
    valores = [os.environ.get(nome, '') for nome in VARIAVEIS]
    if not all(valores):
        return None
    return fluxo.Acesso(
        windows_login=valores[0], windows_senha=valores[1],
        edi_login=valores[2], edi_senha=valores[3])


def _do_arquivo():
    dados = core_cred.carregar_dados(NOME_ARQUIVO)
    if dados is None:
        return None
    try:
        salvo = json.loads(dados.decode('utf-8'))
        acesso = fluxo.Acesso(
            windows_login=salvo['windows_login'],
            windows_senha=salvo['windows_senha'],
            edi_login=salvo['edi_login'],
            edi_senha=salvo['edi_senha'],
        )
    except (ValueError, KeyError, TypeError, UnicodeDecodeError):
        raise ErroAcesso('O acesso salvo está corrompido. Salve novamente com --salvar-acesso.') from None
    if not _completo(acesso):
        raise ErroAcesso('O acesso salvo está incompleto. Salve novamente com --salvar-acesso.')
    return acesso


def carregar_acesso():
    """Devolve o Acesso completo (ambiente ou DPAPI); None se não houver.

    Fora do Windows devolve None (não há DPAPI): cai no pedido no terminal.
    No Windows, arquivo corrompido ou ilegível levanta ErroAcesso com mensagem
    clara, sem conteúdo de senha.
    """
    acesso = _do_ambiente()
    if acesso is not None:
        return acesso
    try:
        return _do_arquivo()
    except ErroAcesso:
        if os.name == 'nt':
            raise
        return None


def salvar_acesso(acesso):
    """Guarda o acesso com DPAPI (somente Windows). Nunca grava texto puro."""
    if not _completo(acesso):
        raise ErroAcesso('Preencha todos os campos de acesso antes de salvar.')
    dados = json.dumps({
        'windows_login': acesso.windows_login,
        'windows_senha': acesso.windows_senha,
        'edi_login': acesso.edi_login,
        'edi_senha': acesso.edi_senha,
    }, ensure_ascii=False).encode('utf-8')
    core_cred.salvar_dados(NOME_ARQUIVO, dados)


def esquecer_acesso():
    """Apaga o acesso salvo (inclusive quando não existe)."""
    core_cred.apagar_dados(NOME_ARQUIVO)


def indicadores():
    """Status do acesso, sem nenhum valor: serve para o --diagnostico."""
    try:
        arquivo = core_cred.caminho_armazenamento(NOME_ARQUIVO).exists()
    except ErroAcesso:
        arquivo = False
    return {'ambiente': _do_ambiente() is not None, 'arquivo': arquivo}
