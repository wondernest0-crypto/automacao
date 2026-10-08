"""Linha de comando da parte SWProgramação.

    python -m swprogramacao                 roda o passo 1 (abre a VPS até o programa carregar)
    python -m swprogramacao --diagnostico   confere o .rdp e as imagens na tela atual

Os logins e senhas são pedidos no terminal. Não são salvos nem gravados no log.
"""
import getpass
import os
import sys
from datetime import datetime

from core import telas
from core.caminhos import DIR_BASE
from swprogramacao import fluxo, rdp

ARQUIVO_LOG = os.path.join(DIR_BASE, 'log_swprogramacao.txt')


def registrar(mensagem):
    linha = f'[{datetime.now():%H:%M:%S}] {mensagem}'
    print(linha, flush=True)
    with open(ARQUIVO_LOG, 'a', encoding='utf-8') as arquivo:
        arquivo.write(linha + '\n')


def coletar_acesso():
    print('Digite os acessos. Eles não ficam salvos.')
    return fluxo.Acesso(
        windows_login=input('  Login do Windows da VPS: ').strip(),
        windows_senha=getpass.getpass('  Senha do Windows da VPS: '),
        edi_login=input('  Usuário do EDI: ').strip(),
        edi_senha=getpass.getpass('  Senha do EDI: '),
    )


def diagnostico(tela):
    print('Arquivo SWPROGRAMACAO.rdp:')
    try:
        print('  encontrado em', rdp.caminho_rdp())
    except rdp.RdpNaoEncontrado as erro:
        print(' ', erro)
    print('Imagens (confiança 90%):')
    for caminho in fluxo.IMAGENS:
        nome = os.path.basename(caminho)
        if not os.path.isfile(caminho):
            print(f'  {nome:20s} FALTA: coloque o arquivo em img/swprogramacao/')
            continue
        pos = tela.localizar(caminho)
        situacao = f'visível em {pos.x},{pos.y}' if pos else 'não visível agora'
        print(f'  {nome:20s} {situacao}')


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    tela = telas.Tela()
    try:
        if '--diagnostico' in argv:
            diagnostico(tela)
            return 0
        try:
            caminho = rdp.caminho_rdp()
        except rdp.RdpNaoEncontrado as erro:
            registrar(str(erro))
            return 1
        faltando = [os.path.basename(i) for i in fluxo.IMAGENS if not os.path.isfile(i)]
        if faltando:
            registrar('Faltam imagens em img/swprogramacao/: ' + ', '.join(faltando))
            return 1
        acesso = coletar_acesso()
        if not all([acesso.windows_login, acesso.windows_senha,
                    acesso.edi_login, acesso.edi_senha]):
            registrar('Preencha todos os campos de acesso. Nada foi feito.')
            return 1
        fluxo.executar_ate_carregar(
            tela, acesso, registrar, abrir_rdp=lambda: rdp.abrir_rdp(caminho))
        return 0
    except fluxo.FalhaFluxo as erro:
        registrar(f'PARADO: {erro}')
        return 1
    except RuntimeError as erro:
        print(erro)
        return 1


if __name__ == '__main__':
    sys.exit(main())
