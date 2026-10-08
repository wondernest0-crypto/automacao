"""Garante que as partes continuam separadas (ver README, seção "Partes do projeto").

- core/ não depende de totvs/ nem de swprogramacao/;
- totvs/ e swprogramacao/ não dependem uma da outra.

A ligação entre as partes fica na raiz (interface ou orquestrador),
nunca dentro de uma parte.
"""
import ast
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

PROIBIDOS = {
    'core': ('totvs', 'swprogramacao'),
    'totvs': ('swprogramacao',),
    'swprogramacao': ('totvs',),
}


def modulos_importados(arquivo):
    """Nomes absolutos importados pelo arquivo (imports relativos são locais à parte)."""
    arvore = ast.parse(arquivo.read_text(encoding='utf-8'))
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            for alias in no.names:
                yield alias.name
        elif isinstance(no, ast.ImportFrom) and no.level == 0 and no.module:
            yield no.module


class TestLimitesEntrePartes(unittest.TestCase):
    def test_partes_nao_importam_umas_as_outras(self):
        for parte, proibidos in PROIBIDOS.items():
            for arquivo in sorted((RAIZ / parte).rglob('*.py')):
                for modulo in modulos_importados(arquivo):
                    with self.subTest(arquivo=str(arquivo.relative_to(RAIZ)), importa=modulo):
                        self.assertNotIn(modulo.split('.')[0], proibidos)


if __name__ == '__main__':
    unittest.main()
