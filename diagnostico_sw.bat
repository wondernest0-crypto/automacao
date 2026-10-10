@echo off
REM ============================================================
REM Confere o SWPROGRAMACAO.rdp, a tela, as 4 capturas da VPS e
REM o acesso salvo. NAO abre o DATASUL e nao mexe em nada.
REM Use antes de reclamar que "a imagem nunca e encontrada".
REM ============================================================
cd /d "%~dp0"
python -m swprogramacao --diagnostico
echo.
pause
