"""Parte SWProgramação, passo 1: abrir a VPS, fazer os logins e procurar a ULIANA.

Procedimento do SWPROGRAMACAO.rdp, na ordem em que ele acontece na tela da
VPS (o campo de usuário já vem com o foco, por isso não se clica em nada):

    login.png (tela de login do Windows)
        -> cola o usuário do Windows, TAB, cola a senha, ENTER
        -> espera ESPERA_APOS_ENTER_WINDOWS (3 s)
    login_edi.png (tela de login do EDI)
        -> cola o usuário do EDI, TAB, cola a senha, ENTER
        -> espera ESPERA_APOS_ENTER_EDI (4 s) para a tela carregar
    informe_parceiro.png ("Informe o parceiro")
        -> sinal de que os dois logins terminaram
    uliana.png
        -> procura a ULIANA na lista e encerra (não clica nela)

Este passo é a PRIMEIRA etapa da sequência: o DATASUL só é executado depois
que ele termina (a ordem fica em orquestrador.py, na raiz). Enquanto o
procedimento do RDP estiver em construção, a sequência para aqui e o DATASUL
não é chamado.

Detalhes da execução:
  1. Confere se as 4 capturas existem em img/swprogramacao/ (falha antes de
     abrir a VPS se faltar alguma — imagem ausente não é "não achou na tela").
  2. Abre o SWPROGRAMACAO.rdp (igual a dar dois cliques nele).
  3. Espera a janela da Conexão de Área de Trabalho Remota aparecer e a põe em
     PRIMEIRO PLANO (sem redimensionar). A busca por imagem só enxerga o que
     está visível na tela: VPS minimizada ou atrás de outra janela nunca casa.
  4. Registra resolução, escala de exibição e o tamanho em pixels de cada
     captura: são os números que explicam "a imagem existe mas nunca é achada".
  5. A cada ciclo, PROCURA TODAS AS IMAGENS na tela antes de decidir o próximo
     passo:
       login.png            -> login do Windows: usuário, TAB, senha, ENTER,
                               espera ESPERA_APOS_ENTER_WINDOWS
       login_edi.png        -> login do EDI: usuário, TAB, senha, ENTER,
                               espera ESPERA_APOS_ENTER_EDI (4 s)
       informe_parceiro.png -> chegou na tela de parceiros: sai do loop
  6. Com informe_parceiro.png na tela, PROCURA uliana.png. Achou: registra e
     termina (não clica em nada). Não achou no prazo: para com erro.

Cada login é digitado uma vez. Se a tela não avançar (por exemplo, senha
errada), o passo para com erro em vez de tentar de novo, para não bloquear
o usuário. Nenhuma senha é gravada nem aparece no log.
"""
import os
from dataclasses import dataclass, field

from core import janelas
from core.caminhos import DIR_BASE, DIR_IMG

PASTA_IMAGENS = os.path.join(DIR_IMG, 'swprogramacao')
IMG_LOGIN = os.path.join(PASTA_IMAGENS, 'login.png')
IMG_LOGIN_EDI = os.path.join(PASTA_IMAGENS, 'login_edi.png')
IMG_INFORME = os.path.join(PASTA_IMAGENS, 'informe_parceiro.png')
IMG_ULIANA = os.path.join(PASTA_IMAGENS, 'uliana.png')
IMAGENS = (IMG_LOGIN, IMG_LOGIN_EDI, IMG_INFORME, IMG_ULIANA)

TIMEOUT_ACESSO = 300      # s: tempo máximo para chegar à tela de parceiros
TIMEOUT_ULIANA = 15       # s: tempo para a ULIANA aparecer na lista
INTERVALO = 1.0           # s: pausa entre as verificações da tela
INTERVALO_LOG = 30        # s: de quanto em quanto tempo registra que segue procurando
ESPERA_APOS_ENTER_WINDOWS = 3.0  # s: tempo para a tela trocar depois do ENTER do Windows
ESPERA_APOS_ENTER_EDI = 4.0      # s: tempo para carregar depois do ENTER do EDI
ESPERA_JANELA_RDP = 30    # s: tempo para a janela da VPS aparecer depois de abrir o .rdp
INTERVALO_JANELA = 1.0    # s: pausa entre as procuras pela janela da VPS

ENCONTRADA = 'uliana_encontrada'


class FalhaFluxo(Exception):
    """O passo parou. A mensagem diz em que etapa e nunca contém senhas."""


@dataclass(frozen=True)
class Acesso:
    windows_login: str
    windows_senha: str = field(repr=False)
    edi_login: str
    edi_senha: str = field(repr=False)


def validar_imagens(imagens=None):
    """Confere se todas as capturas existem em disco antes de abrir a VPS.

    Imagem ausente é arquivo ausente: o passo para com a lista do que falta,
    em vez de parecer que a imagem "não foi encontrada na tela".
    """
    if imagens is None:
        imagens = IMAGENS
    faltando = [os.path.basename(i) for i in imagens if not os.path.isfile(i)]
    if faltando:
        pasta = os.path.relpath(PASTA_IMAGENS, DIR_BASE)
        raise FalhaFluxo(
            f'Faltam imagens em {pasta}/: '
            + ', '.join(faltando)
            + '. Coloque as capturas reais da tela da VPS nesse caminho '
            '(veja img/swprogramacao/README.md).')


def _varrer(tela):
    """Procura TODAS as imagens da fase de acesso de uma só vez na tela."""
    return {imagem: tela.localizar(imagem)
            for imagem in (IMG_LOGIN, IMG_LOGIN_EDI, IMG_INFORME)}


def trazer_vps_para_frente(tela, registrar, prazo=ESPERA_JANELA_RDP):
    """Espera a janela da VPS aparecer e a coloca em primeiro plano.

    Abre-se o .rdp e a janela pode demorar, vir minimizada ou ficar atrás do
    terminal — e a busca por imagem só enxerga o que está visível na tela. Aqui
    a janela é ativada SEM redimensionar: mudar o tamanho da janela muda a
    escala do conteúdo remoto e quebra a comparação com a captura.

    Devolve True quando a janela ficou comprovadamente em primeiro plano. Não
    levanta erro: sem a confirmação o fluxo segue e o log diz o que aconteceu.
    """
    limite = tela.agora() + prazo
    while True:
        achadas = janelas.janelas_por_titulo()
        if achadas:
            janela = achadas[0]
            titulo = (getattr(janela, 'title', '') or '').strip()
            if janelas.trazer_para_frente(janela):
                registrar(f'Janela da VPS em primeiro plano: "{titulo}".')
                return True
            registrar(f'Achei a janela da VPS ("{titulo}"), mas não consegui colocá-la '
                      'em primeiro plano. Traga a janela da VPS para a frente '
                      'manualmente: a automação só enxerga o que está visível.')
            return False
        if tela.agora() > limite:
            registrar(f'Não achei a janela da Conexão de Área de Trabalho Remota em '
                      f'{prazo} s. Se a VPS abriu com outro título, avise para ajustar '
                      'a busca; enquanto isso, mantenha a janela da VPS visível.')
            return False
        tela.esperar(INTERVALO_JANELA)


def _par_de_pixeis(valor):
    """(largura, altura) quando valor é um par de números; senão None."""
    try:
        largura, altura = valor
        return int(largura), int(altura)
    except (TypeError, ValueError):
        return None


def _registrar_contexto_de_tela(tela, registrar):
    """Registra resolução, escala e o tamanho em pixels de cada captura.

    É o diagnóstico de "o arquivo existe mas nunca é achado": se a captura foi
    feita em outra resolução ou com outra escala de exibição, os tamanhos não
    batem e a comparação por pixels nunca fecha. Uma captura maior que a tela
    atual é impossível de achar, e o log diz isso na hora.
    """
    descricao = getattr(tela, 'descricao_tela', None)
    if descricao is not None:
        registrar(f'Tela: {descricao()}')
    medir_tela = getattr(tela, 'tamanho_tela', None)
    medir_imagem = getattr(tela, 'tamanho_imagem', None)
    if medir_tela is None or medir_imagem is None:
        return
    tamanho_tela = _par_de_pixeis(medir_tela())
    for caminho in IMAGENS:
        tamanho = _par_de_pixeis(medir_imagem(caminho))
        if not tamanho:
            continue
        aviso = ''
        if tamanho_tela and (tamanho[0] > tamanho_tela[0] or tamanho[1] > tamanho_tela[1]):
            aviso = (f' — MAIOR que a tela atual ({tamanho_tela[0]}x{tamanho_tela[1]}): '
                     'nunca será encontrada, recapture nesta resolução')
        registrar(f'  {os.path.basename(caminho)}: {tamanho[0]}x{tamanho[1]} px{aviso}')


def _preencher(tela, login, senha, espera):
    """Campo de usuário já está com o foco: digita usuário, TAB, senha, ENTER e espera."""
    tela.colar(login)
    tela.tecla('tab')
    tela.colar(senha)
    tela.tecla('enter')
    tela.esperar(espera)


def executar_ate_uliana(tela, acesso, registrar, abrir_rdp, preparar_vps=None):
    """Roda o passo 1. Devolve ENCONTRADA ou levanta FalhaFluxo.

    `abrir_rdp` e `preparar_vps` vêm de fora (a linha de comando passa os reais;
    os testes passam objetos falsos). `preparar_vps` é chamado depois de abrir o
    .rdp e deve trazer a janela da VPS para o primeiro plano; None pula a etapa.
    """
    validar_imagens()
    abrir_rdp()
    registrar('SWPROGRAMACAO.rdp aberto. Aguardando a tela de login da VPS...')
    if preparar_vps is not None:
        preparar_vps()
    _registrar_contexto_de_tela(tela, registrar)
    preenchido = {'windows': False, 'edi': False}
    prazo = tela.agora() + TIMEOUT_ACESSO
    ultimo_log = tela.agora()

    while True:
        # Antes de qualquer próximo passo, confere TODAS as imagens na tela.
        visiveis = _varrer(tela)
        if visiveis[IMG_INFORME] is not None:
            break
        if not preenchido['windows'] and visiveis[IMG_LOGIN] is not None:
            registrar('Login do Windows encontrado (login.png): preenchendo usuário e senha.')
            _preencher(tela, acesso.windows_login, acesso.windows_senha,
                       ESPERA_APOS_ENTER_WINDOWS)
            preenchido['windows'] = True
            continue
        if not preenchido['edi'] and visiveis[IMG_LOGIN_EDI] is not None:
            registrar('Login do EDI encontrado (login_edi.png): preenchendo usuário e senha.')
            _preencher(tela, acesso.edi_login, acesso.edi_senha, ESPERA_APOS_ENTER_EDI)
            preenchido['edi'] = True
            continue
        if tela.agora() > prazo:
            raise FalhaFluxo(
                f'tempo limite de {TIMEOUT_ACESSO} s esgotado sem chegar à tela de '
                'parceiros. Confira a tela da VPS e o log: a janela da VPS precisa '
                'estar visível (não minimizada) e as capturas precisam ter sido '
                'feitas nesta mesma resolução e escala de exibição '
                '(python -m swprogramacao --diagnostico mostra os tamanhos).')
        if tela.agora() - ultimo_log >= INTERVALO_LOG:
            registrar('Procurando na tela por login.png, login_edi.png e '
                      'informe_parceiro.png... nada visível ainda. A janela da VPS '
                      'tem de estar visível (não minimizada nem coberta) e a captura '
                      'feita nesta mesma resolução e escala.')
            ultimo_log = tela.agora()
        tela.esperar(INTERVALO)
    registrar('Tela de parceiros encontrada (informe_parceiro.png).')

    # Só procura a ULIANA: não clica nela. Achou, o passo termina.
    prazo_uliana = tela.agora() + TIMEOUT_ULIANA
    while tela.localizar(IMG_ULIANA) is None:
        if tela.agora() > prazo_uliana:
            raise FalhaFluxo('a ULIANA (uliana.png) não apareceu na lista de parceiros.')
        tela.esperar(INTERVALO)
    registrar('ULIANA encontrada (uliana.png). Fim do passo.')
    return ENCONTRADA
