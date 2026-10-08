"""Abre a VPS pelo arquivo SWPROGRAMACAO.rdp que fica na área de trabalho.

A busca na área de trabalho e a abertura ficam em core/rdp.py (código
compartilhado, também usado pela parte TOTVS para abrir a VPS antes de
executar o DATASUL). Este módulo mantém a API da parte SWProgramação.
"""
from core import rdp as rdp_compartilhado

NOME_ARQUIVO = 'SWPROGRAMACAO.rdp'
RdpNaoEncontrado = rdp_compartilhado.RdpNaoEncontrado


def caminhos_candidatos(home=None):
    return rdp_compartilhado.caminhos_candidatos(NOME_ARQUIVO, home)


def caminho_rdp(home=None):
    return rdp_compartilhado.caminho_rdp(NOME_ARQUIVO, home)


def abrir_rdp(caminho):
    return rdp_compartilhado.abrir_rdp(caminho)
