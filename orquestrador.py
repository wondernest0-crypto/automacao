"""Liga as duas partes: SWProgramação (VPS) primeiro, DATASUL depois.

Este é o único lugar do projeto que fala com as duas partes: `totvs/` e
`swprogramacao/` não se importam uma da outra (ver tests/test_limites_partes.py),
então a ordem da sequência mora aqui, na raiz.

SEQUÊNCIA DO START (aba "Importar Pedido HONDA & GM")

    1. SWProgramação — abre o SWPROGRAMACAO.rdp da área de trabalho e faz o
       procedimento completo da VPS (swprogramacao/execucao.py):
         login do Windows  -> usuário, TAB, senha, ENTER;
         login do EDI      -> usuário, TAB, senha, ENTER e 4 s para carregar;
         tela "Informe o parceiro" -> procura a ULIANA, clica 3 vezes, pausa
         e encerra com sucesso (a VPS permanece aberta).
    2. DATASUL — só entra depois que o passo 1 termina.

HOJE SÓ O PASSO 1 EXISTE NA SEQUÊNCIA. A parte do SWPROGRAMACAO.rdp ainda está
em construção, e foi decidido que o DATASUL não é executado enquanto esse
procedimento não estiver finalizado: o START roda a VPS, encerra após clicar
3 vezes na ULIANA e NÃO abre o DATASUL nem envia nenhuma tecla para ele. Quando essa etapa for
dada como finalizada, a entrada no DATASUL volta aqui — o motor continua
pronto em `totvs/automacao.py` (AutomacaoTOTVS.importar_pedido), basta passá-lo
em `entrar_no_datasul`. Nada mais precisa mudar: a ordem (VPS primeiro,
DATASUL depois) já é garantida por este módulo.
"""
import traceback
from dataclasses import dataclass

from swprogramacao import acessos, execucao, fluxo

# Mensagens do log (o .exe roda sem console: o log e a caixa de aviso são o
# que o usuário vê).
MENSAGEM_ORDEM = ('ORDEM DA SEQUÊNCIA: primeiro todo o procedimento do '
                  'SWPROGRAMACAO.rdp; só depois o DATASUL.')
MENSAGEM_SEM_DATASUL = (
    '⏹️ FIM DA SEQUÊNCIA: procedimento do SWPROGRAMACAO.rdp concluído. '
    'A entrada no DATASUL está DESLIGADA nesta versão — ela volta quando o '
    'procedimento do RDP (logins, tela de parceiro e ULIANA) estiver '
    'finalizado. Nenhuma tecla foi enviada ao DATASUL.')
MENSAGEM_SW_OBRIGATORIA = ('O DATASUL não é executado enquanto o procedimento do '
                           'SWPROGRAMACAO.rdp não terminar: a VPS vem primeiro e '
                           'só depois o DATASUL.')


@dataclass
class Resultado:
    """O que a sequência fez. `motivo` explica por que parou (vazio = ok)."""

    concluiu: bool
    entrou_no_datasul: bool = False
    motivo: str = ''


def executar_etapa_swprogramacao(registrar, pedir_acesso=None, confianca_minima=None,
                                 tela=None):
    """Roda o procedimento do SWPROGRAMACAO.rdp. Devolve (ok, motivo).

    Não levanta erro: quem chama decide o que fazer. `pedir_acesso` é o
    retorno para pedir o acesso no terminal (a linha de comando usa; a
    interface não tem terminal e passa None).
    """
    try:
        execucao.executar_passo_um(registrar, pedir_acesso=pedir_acesso,
                                   confianca_minima=confianca_minima, tela=tela)
    except fluxo.FalhaFluxo as erro:
        # Preparo (imagem/.rdp/acesso) ou fluxo: a VPS não chegou ao fim.
        return False, str(erro)
    except (acessos.ErroAcesso, RuntimeError) as erro:
        # RuntimeError: automação de tela indisponível (sem pyautogui/tela).
        return False, str(erro)
    return True, ''


def executar_sequencia(registrar, entrar_no_datasul=None, pedir_acesso=None,
                       confianca_minima=None, tela=None):
    """Roda a sequência do START: a VPS primeiro, o DATASUL depois.

    `entrar_no_datasul` é o chamável que abre o DATASUL (hoje ninguém passa
    nada, então a sequência termina na VPS). `registrar` recebe cada mensagem
    (na prática, o log da automação). Devolve um Resultado; não levanta erro.
    """
    registrar('=' * 60)
    registrar('🚗 IMPORTAÇÃO DE PEDIDO - HONDA & GM')
    registrar('=' * 60)
    registrar(MENSAGEM_ORDEM)

    ok, motivo = executar_etapa_swprogramacao(
        registrar, pedir_acesso=pedir_acesso,
        confianca_minima=confianca_minima, tela=tela)
    if not ok:
        registrar(f'❌ ERRO: o procedimento do SWPROGRAMACAO.rdp não terminou: {motivo}')
        registrar(MENSAGEM_SW_OBRIGATORIA)
        return Resultado(concluiu=False, entrou_no_datasul=False, motivo=motivo)

    registrar('✅ SUCESSO: procedimento do SWPROGRAMACAO.rdp concluído '
              '(login do Windows, login do EDI, tela de parceiro e ULIANA).')

    if entrar_no_datasul is None:
        # Etapa do DATASUL desligada até o procedimento do RDP ser finalizado.
        registrar(MENSAGEM_SEM_DATASUL)
        return Resultado(concluiu=True, entrou_no_datasul=False)

    registrar('➡️ Etapa da VPS concluída. Iniciando o DATASUL...')
    try:
        entrou = bool(entrar_no_datasul())
    except Exception as erro:
        motivo = f'o DATASUL parou com erro: {type(erro).__name__}: {erro}'
        registrar(f'❌ ERRO: {motivo}')
        return Resultado(concluiu=False, entrou_no_datasul=True, motivo=motivo)
    if not entrou:
        motivo = 'o DATASUL não foi executado até o fim (veja o log).'
        registrar(f'❌ ERRO: {motivo}')
        return Resultado(concluiu=False, entrou_no_datasul=True, motivo=motivo)
    registrar('✅ SUCESSO: sequência concluída (VPS e DATASUL).')
    return Resultado(concluiu=True, entrou_no_datasul=True)


def rodar_importacao(bot, entrar_no_datasul=None, pedir_acesso=None,
                     confianca_minima=None, tela=None):
    """Roda a sequência do START usando o motor TOTVS para log/avisos.

    `bot` é o AutomacaoTOTVS (ou qualquer objeto com log, log_erro,
    mostrar_erro_visivel e reabrir_interface): é ele que escreve no
    log_automacao.txt, mostra o aviso na tela e reabre a interface no fim —
    inclusive quando tudo dá errado, para a interface não desaparecer.
    """
    try:
        resultado = executar_sequencia(
            bot.log, entrar_no_datasul=entrar_no_datasul,
            pedir_acesso=pedir_acesso, confianca_minima=confianca_minima, tela=tela)
    except Exception:
        erro = traceback.format_exc()
        bot.log_erro('EXCEÇÃO NÃO TRATADA NA SEQUÊNCIA:\n' + erro)
        bot.mostrar_erro_visivel(
            'Importar Pedido - ERRO',
            'A sequência parou com um erro inesperado.\n\n'
            f'{erro}\nLog completo: veja log_automacao.txt')
        bot.reabrir_interface()
        return Resultado(concluiu=False, entrou_no_datasul=False,
                         motivo='erro inesperado na sequência')

    if not resultado.concluiu:
        bot.mostrar_erro_visivel(
            'Importar Pedido - VPS',
            'A etapa da VPS não terminou, então o DATASUL não foi executado.\n\n'
            f'{resultado.motivo}\n\n'
            'Dica: rode "python -m swprogramacao --diagnostico" para conferir '
            'as capturas, a janela da VPS e o acesso salvo.\n'
            'Log completo: veja log_automacao.txt')
    bot.reabrir_interface()
    return resultado
