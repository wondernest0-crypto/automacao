@echo off
REM ============================================================
REM Salva o acesso da VPS (login do Windows e login do EDI).
REM Rode UMA vez em cada conta Windows (ou quando a senha mudar).
REM A senha fica protegida pela DPAPI, fora da pasta do projeto:
REM   %LOCALAPPDATA%\AutomacaoTOTVS\acesso_sw.dpapi
REM Nenhuma senha fica gravada no projeto nem no log.
REM ============================================================
cd /d "%~dp0"
python -m swprogramacao --salvar-acesso
echo.
pause
