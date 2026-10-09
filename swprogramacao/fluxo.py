"""Parte SWProgramação, passo 1: abrir a VPS, fazer os logins e procurar a ULIANA.

Sequência combinada:
  1. Confere se as 4 capturas existem em img/swprogramacao/ (falha antes de
     abrir a VPS se faltar alguma — imagem ausente não é "não achou na tela").
  2. Abre o SWPROGRAMACAO.rdp (igual a dar dois cliques nele).
  3. A cada ciclo, PROCURA TODAS AS IMAGENS na tela antes de decidir o próximo
     passo:
       login.png            -> login do Windows: usuário, TAB, senha, ENTER,
                               espera ESPERA_APOS_ENTER_WINDOWS
       login_edi.png        -> login do EDI: usuário, TAB, senha, ENTER,
                               espera ESPERA_APOS_ENTER_EDI (4 s)
       informe_parceiro.png -> chegou na tela de parceiros: sai do loop
  4. Com informe_parceiro.png na tela, PROCURA uliana.png. Achou: registra e
     termina (não clica em nada). Não achou no prazo: para com erro.

Cada login é digitado uma vez. Se a tela não avançar (por exemplo, senha
errada), o passo para com erro em vez de tentar de novo, para não bloquear
o usuário. Nenhuma senha é gravada nem aparece no log.
"""
import os
from dataclasses import dataclass, field

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


def _preencher(tela, login, senha, espera):
    """Campo de usuário já está com o foco: digita usuário, TAB, senha, ENTER e espera."""
    tela.colar(login)
    tela.tecla('tab')
    tela.colar(senha)
    tela.tecla('enter')
    tela.esperar(espera)


def executar_ate_uliana(tela, acesso, registrar, abrir_rdp):
    """Roda o passo 1. Devolve ENCONTRADA ou levanta FalhaFluxo."""
    validar_imagens()
    abrir_rdp()
    registrar('SWPROGRAMACAO.rdp aberto. Aguardando a tela de login da VPS...')
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
                'parceiros. Confira a tela da VPS e o log.')
        if tela.agora() - ultimo_log >= INTERVALO_LOG:
            registrar('Procurando na tela por login.png, login_edi.png e '
                      'informe_parceiro.png... nada visível ainda.')
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
