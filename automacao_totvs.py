# ========================================
# AUTOMAÇÃO TOTVS - PONTO DE ENTRADA
# ========================================
# Fica na raiz porque é o script que a interface (lancamento_inventario.py),
# o compilar.bat e o Automacao_TOTVS.spec usam. A lógica está em totvs/automacao.py.
from totvs.automacao import main

if __name__ == "__main__":
    main()
