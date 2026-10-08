"""Localiza e abre arquivos .rdp que ficam na área de trabalho.

Compartilhado pelas partes (TOTVS e SWProgramação). A área de trabalho pode
aparecer como 'Desktop' ou 'Área de Trabalho' (Windows em português), e com
OneDrive ela fica dentro da pasta OneDrive.
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


def caminhos_candidatos(nome_arquivo, home=None):
    home = home or os.path.expanduser('~')
    return [os.path.join(home, *partes, nome_arquivo) for partes in PASTAS_DESKTOP]


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
    os.startfile(caminho)  # existe só no Windows
