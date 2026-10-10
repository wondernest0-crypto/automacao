"""Execução do passo 1 com as dependências reais (tela, .rdp e acesso).

A linha de comando (`python -m swprogramacao`) e o orquestrador da raiz
(`orquestrador.py`, que é quem o START da interface chama) usam ESTA função:
o procedimento é exatamente o mesmo nos dois caminhos —

    1. confere se as 4 capturas existem em img/swprogramacao/;
    2. acha o SWPROGRAMACAO.rdp na área de trabalho;
    3. carrega o acesso da VPS (variáveis de ambiente ou DPAPI);
    4. abre o .rdp, aguarda 10 s e traz a janela da VPS para a frente;
    5. login do Windows (usuário, TAB, senha, ENTER);
    6. login do EDI (usuário, TAB, senha, ENTER) e espera 4 s para carregar;
    7. espera a tela "Informe o parceiro", procura a ULIANA, clica 3 vezes,
       pausa e encerra com sucesso (a VPS continua aberta).

O que muda entre os dois caminhos é somente quem recebe as mensagens
(`registrar`) e o que fazer quando não existe acesso salvo: a linha de comando
pode pedir no terminal (`pedir_acesso`), o orquestrador roda sem console
(chamado pela interface) e por isso recebe `pedir_acesso=None`.

Nenhuma senha é gravada nem aparece nas mensagens.
"""
from core import telas
from swprogramacao import acessos, fluxo, rdp


def _obter_acesso(registrar, pedir_acesso):
    """Acesso salvo (ou pedido). Se não houver e não houver prompt, devolve None
    (a conexão RDP já possui as credenciais salvas no Windows)."""
    try:
        acesso = acessos.carregar_acesso()
    except acessos.ErroAcesso as erro:
        # Arquivo corrompido / proteção indisponível: nunca mexe na VPS.
        raise fluxo.FalhaFluxo(str(erro)) from erro
    if acesso is not None:
        registrar('Acesso carregado (variáveis de ambiente ou DPAPI); '
                  'nenhum valor é exibido no log.')
        return acesso
    if pedir_acesso is not None:
        acesso = pedir_acesso()
        if not all([acesso.windows_login, acesso.windows_senha,
                    acesso.edi_login, acesso.edi_senha]):
            raise fluxo.FalhaFluxo('Preencha todos os campos de acesso. Nada foi feito.')
        return acesso
    registrar('Acesso da VPS: credenciais salvas na conexão RDP '
              '(não requer digitação de login ou senha).')
    return None


_acesso_ou_falha = _obter_acesso


def executar_passo_um(registrar, pedir_acesso=None, confianca_minima=None, tela=None):
    """Roda o procedimento do SWPROGRAMACAO.rdp. Devolve fluxo.ENCONTRADA.

    Levanta `fluxo.FalhaFluxo` (com a mensagem pronta para o usuário) quando
    algum preparo falha — imagem ausente ou .rdp não encontrado — e também
    quando o fluxo não chega à ULIANA. Nenhuma falha de preparo abre a VPS.
    """
    fluxo.validar_imagens()
    try:
        caminho = rdp.caminho_rdp()
    except rdp.RdpNaoEncontrado as erro:
        raise fluxo.FalhaFluxo(str(erro)) from erro
    acesso = _obter_acesso(registrar, pedir_acesso)

    if tela is None:
        tela = (telas.Tela() if confianca_minima is None
                else telas.Tela(confianca_minima=confianca_minima))
    registrar(f'{rdp.NOME_ARQUIVO} encontrado: {caminho}')
    return fluxo.executar_ate_uliana(
        tela, acesso, registrar,
        abrir_rdp=lambda: rdp.abrir_rdp(caminho),
        preparar_vps=lambda: fluxo.trazer_vps_para_frente(tela, registrar))
