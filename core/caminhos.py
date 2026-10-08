"""Caminhos do projeto, iguais no modo .py e no modo .exe (PyInstaller).

Compartilhado pelas partes (TOTVS, SWProgramação e interface).
Este módulo não cria pastas nem arquivos: quem usa decide o que criar.
"""
import os
import sys


def get_base_path():
    """Pasta do projeto (modo .py) ou pasta do .exe (modo PyInstaller)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    # Este arquivo fica em core/, então a raiz do projeto é a pasta acima.
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DIR_BASE = get_base_path()
DIR_IMG = os.path.join(DIR_BASE, "img")
DIR_DATA = os.path.join(DIR_BASE, "data")
DIR_ASSETS = os.path.join(DIR_BASE, "assets")
