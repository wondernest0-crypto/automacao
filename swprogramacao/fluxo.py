"""Parte SWProgramação, passo 1: abrir a VPS e parar quando o programa carregar.

Sequência combinada:
  1. Abre o SWPROGRAMACAO.rdp (igual a dar dois cliques nele).
  2. Enquanto espera, observa a tela:
       login.png      -> login do Windows: usuário, TAB, senha, ENTER
       login_edi.png  -> login do EDI: usuário, TAB, senha, ENTER
  3. Quando aparece informe_parceiro.png, dá duplo clique em uliana.png.
  4. Espera o programa carregar e PARA (checkpoint).

Cada login é digitado uma vez. Se a tela não avançar (por exemplo, senha
errada), o passo para com erro em vez de tentar de novo, para não bloquear
o usuário. Nenhuma senha é gravada nem aparece no log.
"""
import os
from dataclasses import dataclass, field

from core.caminhos import DIR_IMG

PASTA_IMAGENS = os.path.join(DIR_IMG, 'swprogramacao')
IMG_LOGIN = os.path.join(PASTA_IMAGENS, 'login.png')
IMG_LOGIN_EDI = os.path.join(PASTA_IMAGENS, 'login_edi.png')
IMG_INFORME = os.path.join(PASTA_IMAGENS, 'informe_parceiro.png')
IMG_ULIANA = os.path.join(PASTA_IMAGENS, 'uliana.png')
IMAGENS = (IMG_LOGIN, IMG_LOGIN_EDI, IMG_INFORME, IMG_ULIANA)

TIMEOUT_ACESSO = 300      # s: tempo máximo para chegar à tela de parceiros
TIMEOUT_ULIANA = 15       # s: tempo para a ULIANA aparecer na lista
INTERVALO = 1.0           # s: pausa entre as verificações da tela
ESPERA_APOS_ENTER = 3.0   # s: tempo para a tela trocar depois do ENTER
TEMPO_CARREGAMENTO = 30   # s: espera o programa carregar após o duplo clique

CARREGANDO = 'carregando'


class FalhaFluxo(Exception):
    """O passo parou. A mensagem diz em que etapa e nunca contém senhas."""


@dataclass(frozen=True)
class Acesso:
    windows_login: str
    windows_senha: str = field(repr=False)
    edi_login: str
    edi_senha: str = field(repr=False)


def _preencher(tela, login, senha):
    tela.colar(login)
    tela.tecla('tab')
    tela.colar(senha)
    tela.tecla('enter')
    tela.esperar(ESPERA_APOS_ENTER)


def executar_ate_carregar(tela, acesso, registrar, abrir_rdp):
    """Roda o passo 1. Devolve CARREGANDO ou levanta FalhaFluxo."""
    abrir_rdp()
    registrar('SWPROGRAMACAO.rdp aberto. Aguardando a tela de login da VPS...')
    preenchido = {'windows': False, 'edi': False}
    prazo = tela.agora() + TIMEOUT_ACESSO

    while tela.localizar(IMG_INFORME) is None:
        if not preenchido['windows'] and tela.localizar(IMG_LOGIN) is not None:
            registrar('Login do Windows encontrado: preenchendo usuário e senha.')
            _preencher(tela, acesso.windows_login, acesso.windows_senha)
            preenchido['windows'] = True
        elif not preenchido['edi'] and tela.localizar(IMG_LOGIN_EDI) is not None:
            registrar('Login do EDI encontrado: preenchendo usuário e senha.')
            _preencher(tela, acesso.edi_login, acesso.edi_senha)
            preenchido['edi'] = True
        else:
            if tela.agora() > prazo:
                raise FalhaFluxo(
                    f'tempo limite de {TIMEOUT_ACESSO} s esgotado sem chegar à tela de '
                    'parceiros. Confira a tela da VPS e o log.')
            tela.esperar(INTERVALO)
    registrar('Tela de parceiros encontrada.')

    prazo_uliana = tela.agora() + TIMEOUT_ULIANA
    while not tela.clicar_duplo(IMG_ULIANA):
        if tela.agora() > prazo_uliana:
            raise FalhaFluxo('a ULIANA (uliana.png) não apareceu na lista de parceiros.')
        tela.esperar(INTERVALO)
    registrar('Duplo clique em ULIANA. Aguardando o programa carregar...')

    tela.esperar(TEMPO_CARREGAMENTO)
    registrar('CHECKPOINT: programa carregando. Parei aqui, como combinado.')
    return CARREGANDO
