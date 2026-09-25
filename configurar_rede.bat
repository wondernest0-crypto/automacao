@echo off
chcp 65001 >nul
title Configurar Compartilhamento - Sistema de Inventário

echo.
echo ========================================
echo 🔧 CONFIGURANDO MODO COMPARTILHAMENTO
echo ========================================
echo.
echo ⚠️ IMPORTANTE: Feche o Excel antes de continuar!
echo.
pause

python configurar_compartilhamento.py

pause
