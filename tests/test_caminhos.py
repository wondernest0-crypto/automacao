"""Caminhos do projeto no modo .py e no modo .exe (PyInstaller).

Regressão: ao mover o motor para totvs/, a raiz do projeto não pode mudar.
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from core import caminhos

RAIZ = Path(__file__).resolve().parents[1]


class TestCaminhos(unittest.TestCase):
    def test_modo_py_aponta_para_raiz_do_projeto(self):
        self.assertEqual(Path(caminhos.get_base_path()), RAIZ)
        self.assertEqual(Path(caminhos.DIR_BASE), RAIZ)
        self.assertEqual(Path(caminhos.DIR_IMG), RAIZ / 'img')
        self.assertEqual(Path(caminhos.DIR_DATA), RAIZ / 'data')
        self.assertEqual(Path(caminhos.DIR_ASSETS), RAIZ / 'assets')

    def test_modo_exe_usa_pasta_do_executavel(self):
        executavel = os.path.join('pasta', 'do', 'programa', 'Automacao_TOTVS.exe')
        with patch.object(sys, 'frozen', True, create=True), \
                patch.object(sys, 'executable', executavel):
            self.assertEqual(caminhos.get_base_path(), os.path.dirname(executavel))


if __name__ == '__main__':
    unittest.main()
