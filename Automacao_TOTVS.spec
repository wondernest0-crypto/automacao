# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['automacao_totvs.py'],
    pathex=[],
    binaries=[('msedgedriver.exe', '.')],
    datas=[('img', 'img'), ('data', 'data'), ('assets', 'assets')],
    hiddenimports=['pandas', 'openpyxl', 'pyautogui', 'pygetwindow', 'pyperclip', 'PIL', 'PIL.Image', 'pyscreeze', 'ctypes', 'selenium', 'selenium.webdriver', 'selenium.webdriver.edge', 'selenium.webdriver.edge.service', 'selenium.webdriver.edge.options', 'selenium.webdriver.common.by', 'selenium.webdriver.support', 'selenium.webdriver.support.ui', 'selenium.webdriver.support.expected_conditions', 'selenium.common.exceptions'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Automacao_TOTVS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icone.ico'],
)
