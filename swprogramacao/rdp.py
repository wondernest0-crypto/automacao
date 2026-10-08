"""Abre a VPS pelo arquivo SWPROGRAMACAO.rdp que fica na área de trabalho."""
import os

NOME_ARQUIVO = 'SWPROGRAMACAO.rdp'

# Pastas onde o arquivo pode estar. No Windows em português a área de trabalho
# pode aparecer como 'Área de Trabalho'; com OneDrive, ela fica dentro do OneDrive.
PASTAS = (
    ('Desktop',),
    ('OneDrive', 'Desktop'),
    ('Área de Trabalho',),
    ('OneDrive', 'Área de Trabalho'),
)


class RdpNaoEncontrado(Exception):
    pass


def caminhos_candidatos(home=None):
    home = home or os.path.expanduser('~')
    return [os.path.join(home, *partes, NOME_ARQUIVO) for partes in PASTAS]


def caminho_rdp(home=None):
    candidatos = caminhos_candidatos(home)
    for caminho in candidatos:
        if os.path.isfile(caminho):
            return caminho
    raise RdpNaoEncontrado(
        f'Não achei o {NOME_ARQUIVO} na área de trabalho. Procurei em:\n  '
        + '\n  '.join(candidatos))


def abrir_rdp(caminho):
    """Igual a dar dois cliques no arquivo: abre com a Conexão de Área de Trabalho Remota."""
    os.startfile(caminho)  # existe só no Windows
