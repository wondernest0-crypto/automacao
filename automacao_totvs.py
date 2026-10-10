# ========================================
# AUTOMAÇÃO TOTVS - PONTO DE ENTRADA
# ========================================
# Fica na raiz porque é o script que a interface (lancamento_inventario.py),
# o compilar.bat e o Automacao_TOTVS.spec usam. A lógica está em totvs/automacao.py.
import sys

from totvs.automacao import AutomacaoTOTVS, main as main_totvs

# A sequência do modo "importar" (START da aba Importar Pedido HONDA & GM) é
# decidida pelo orquestrador, na raiz: ele é o único lugar que pode ligar as
# duas partes (totvs/ e swprogramacao/ não se importam entre si).
#
# Hoje essa sequência roda SOMENTE o procedimento do SWPROGRAMACAO.rdp (abrir
# a VPS, login do Windows, login do EDI, tela de parceiro e ULIANA) e para aí:
# o DATASUL não é executado enquanto essa etapa não estiver finalizada.
from orquestrador import rodar_importacao

MODO_IMPORTAR = ("importar", "importacao", "import")


def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() in MODO_IMPORTAR:
        # O bot é usado pelo orquestrador para o log (log_automacao.txt), para
        # o aviso na tela e para reabrir a interface no fim — inclusive quando
        # a sequência para, para a interface não desaparecer.
        rodar_importacao(AutomacaoTOTVS())
        return
    main_totvs()


if __name__ == "__main__":
    main()
