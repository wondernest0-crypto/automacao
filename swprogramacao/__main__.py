"""Linha de comando da parte SWProgramação.

    python -m swprogramacao                 roda o passo 1 (abre a VPS, faz os logins e acha a ULIANA)
    python -m swprogramacao --diagnostico   confere o .rdp, as imagens na tela e o acesso salvo
    python -m swprogramacao --salvar-acesso guarda o acesso com DPAPI (uma vez só; pede no terminal)
    python -m swprogramacao --esquecer-acesso apaga o acesso salvo

O acesso vem das variáveis de ambiente SW_WINDOWS_LOGIN, SW_WINDOWS_SENHA,
SW_EDI_LOGIN e SW_EDI_SENHA ou do arquivo protegido por DPAPI; se não houver,
é pedido no terminal. Senhas não são salvas em texto puro nem aparecem no log.
"""
import getpass
import os
import sys
from datetime import datetime

from core import telas
from core.caminhos import DIR_BASE
from swprogramacao import acessos, fluxo, rdp

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


def _acesso_completo(acesso):
    return all([acesso.windows_login, acesso.windows_senha,
                acesso.edi_login, acesso.edi_senha])


def _salvar_acesso():
    acesso = coletar_acesso()
    if not _acesso_completo(acesso):
        print('Preencha todos os campos de acesso. Nada foi salvo.')
        return 1
    try:
        acessos.salvar_acesso(acesso)
    except acessos.ErroAcesso as erro:
        print(erro)
        print('Dica: fora do Windows não dá para salvar; use as variáveis de '
              'ambiente SW_WINDOWS_LOGIN, SW_WINDOWS_SENHA, SW_EDI_LOGIN e SW_EDI_SENHA.')
        return 1
    registrar('Acesso salvo com a proteção do Windows (nenhum valor é exibido).')
    return 0


def _esquecer_acesso():
    try:
        acessos.esquecer_acesso()
    except acessos.ErroAcesso as erro:
        print(erro)
        return 1
    registrar('Acesso salvo apagado.')
    return 0


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
    status = acessos.indicadores()
    print('Acesso (sem mostrar valores):')
    print('  variáveis de ambiente SW_*:', 'completas' if status['ambiente'] else 'não definidas')
    print('  arquivo DPAPI (acesso_sw.dpapi):', 'salvo' if status['arquivo'] else 'não salvo')


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    tela = telas.Tela()
    try:
        if '--diagnostico' in argv:
            diagnostico(tela)
            return 0
        if '--salvar-acesso' in argv:
            return _salvar_acesso()
        if '--esquecer-acesso' in argv:
            return _esquecer_acesso()
        try:
            caminho = rdp.caminho_rdp()
        except rdp.RdpNaoEncontrado as erro:
            registrar(str(erro))
            return 1
        try:
            fluxo.validar_imagens(fluxo.IMAGENS)
        except fluxo.FalhaFluxo as erro:
            registrar(str(erro))
            return 1
        try:
            acesso = acessos.carregar_acesso()
        except acessos.ErroAcesso as erro:
            registrar(str(erro))
            return 1
        if acesso is None:
            acesso = coletar_acesso()
            if not _acesso_completo(acesso):
                registrar('Preencha todos os campos de acesso. Nada foi feito.')
                return 1
        else:
            registrar('Acesso carregado (variáveis de ambiente ou DPAPI); '
                      'nenhum valor é exibido no log.')
        fluxo.executar_ate_uliana(
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
