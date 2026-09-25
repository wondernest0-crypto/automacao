@echo off
chcp 65001 >nul
echo ============================================
echo    COMPILANDO SISTEMA DE INVENTARIO
echo ============================================
echo.

cd /d "C:\Users\faturamento3\Desktop\inventario"

echo [0/5] Limpando builds anteriores...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del *.spec 2>nul
echo.

echo ============================================
echo [1/5] Verificando arquivos necessarios...
echo ============================================

if not exist "msedgedriver.exe" (
    echo ❌ ERRO: msedgedriver.exe NAO encontrado!
    echo.
    echo Baixe em: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
    echo Coloque na pasta: C:\Users\faturamento3\Desktop\inventario
    echo.
    pause
    exit /b 1
)
echo ✅ msedgedriver.exe encontrado!

if not exist "assets\icone.ico" (
    echo ⚠️ AVISO: icone.ico nao encontrado em assets\
)
echo.

echo ============================================
echo [2/5] Compilando Interface Principal...
echo ============================================
python -m PyInstaller --noconfirm --onefile --windowed ^
    --name "Sistema_Inventario" ^
    --icon="assets\icone.ico" ^
    --add-data "img;img" ^
    --add-data "data;data" ^
    --add-data "assets;assets" ^
    --hidden-import pandas ^
    --hidden-import openpyxl ^
    --hidden-import xlsxwriter ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageTk ^
    --hidden-import PIL._tkinter_finder ^
    --hidden-import ctypes ^
    --hidden-import threading ^
    --noupx ^
    lancamento_inventario.py

if not exist "dist\Sistema_Inventario.exe" (
    echo.
    echo ❌ ERRO: Sistema_Inventario.exe NAO foi criado!
    echo Verifique os erros acima.
    pause
    exit /b 1
)

echo.
echo ✅ Sistema_Inventario.exe criado com sucesso!
echo.

echo ============================================
echo [3/5] Movendo primeiro EXE para backup...
echo ============================================
mkdir "dist\temp_backup" 2>nul
move "dist\Sistema_Inventario.exe" "dist\temp_backup\" >nul
echo ✅ Backup feito!
echo.

echo ============================================
echo [4/5] Compilando Automacao TOTVS...
echo ============================================
REM NOTA: Usando --console para ver logs em tempo real
REM       Troque para --windowed se quiser esconder o console

python -m PyInstaller --noconfirm --onefile --windowed ^
    --name "Automacao_TOTVS" ^
    --icon="assets\icone.ico" ^
    --add-data "img;img" ^
    --add-data "data;data" ^
    --add-data "assets;assets" ^
    --add-binary "msedgedriver.exe;." ^
    --hidden-import pandas ^
    --hidden-import openpyxl ^
    --hidden-import pyautogui ^
    --hidden-import pygetwindow ^
    --hidden-import pyperclip ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import pyscreeze ^
    --hidden-import ctypes ^
    --hidden-import selenium ^
    --hidden-import selenium.webdriver ^
    --hidden-import selenium.webdriver.edge ^
    --hidden-import selenium.webdriver.edge.service ^
    --hidden-import selenium.webdriver.edge.options ^
    --hidden-import selenium.webdriver.common.by ^
    --hidden-import selenium.webdriver.support ^
    --hidden-import selenium.webdriver.support.ui ^
    --hidden-import selenium.webdriver.support.expected_conditions ^
    --hidden-import selenium.common.exceptions ^
    --noupx ^
    automacao_totvs.py

if not exist "dist\Automacao_TOTVS.exe" (
    echo.
    echo ❌ ERRO: Automacao_TOTVS.exe NAO foi criado!
    pause
    exit /b 1
)

echo.
echo ✅ Automacao_TOTVS.exe criado com sucesso!
echo.

echo ============================================
echo [5/5] Organizando arquivos finais...
echo ============================================

REM Mover o primeiro EXE de volta
move "dist\temp_backup\Sistema_Inventario.exe" "dist\" >nul
rmdir "dist\temp_backup" 2>nul

REM Copiar pastas necessarias
echo Copiando pasta img...
xcopy /E /I /Y "img" "dist\img" >nul

echo Copiando pasta data...
xcopy /E /I /Y "data" "dist\data" >nul

echo Copiando pasta assets...
xcopy /E /I /Y "assets" "dist\assets" >nul

REM ⭐ IMPORTANTE: Copiar msedgedriver.exe para dist
echo Copiando msedgedriver.exe...
copy /Y "msedgedriver.exe" "dist\" >nul

echo.
echo ============================================
echo    ✅ COMPILACAO CONCLUIDA COM SUCESSO!
echo ============================================
echo.
echo 📁 Arquivos criados em: dist\
echo.
echo    📦 Sistema_Inventario.exe
echo    🤖 Automacao_TOTVS.exe
echo    🌐 msedgedriver.exe
echo    📂 img\
echo    📂 data\
echo    📂 assets\
echo.

REM Verificar se todos existem
set "TODOS_OK=1"

if not exist "dist\Sistema_Inventario.exe" (
    echo ⚠️ AVISO: Sistema_Inventario.exe nao encontrado!
    set "TODOS_OK=0"
)

if not exist "dist\Automacao_TOTVS.exe" (
    echo ⚠️ AVISO: Automacao_TOTVS.exe nao encontrado!
    set "TODOS_OK=0"
)

if not exist "dist\msedgedriver.exe" (
    echo ⚠️ AVISO: msedgedriver.exe nao encontrado na dist!
    set "TODOS_OK=0"
)

if "%TODOS_OK%"=="1" (
    echo ✅ Todos os arquivos foram criados com sucesso!
)

echo.
echo ============================================
echo    ESTRUTURA FINAL:
echo ============================================
echo.
dir /b "dist"
echo.

echo Pressione qualquer tecla para abrir a pasta dist...
pause >nul
explorer "dist"