"""Passo 1 da SWProgramação com uma tela falsa (sem Windows e sem VPS).

A tela falsa segue um roteiro: as imagens visíveis mudam a cada ENTER.
O relógio também é falso, então os testes não esperam de verdade.
"""
import unittest

from swprogramacao import fluxo
from swprogramacao.fluxo import (
    IMG_INFORME, IMG_LOGIN, IMG_LOGIN_EDI, IMG_ULIANA, Acesso, FalhaFluxo)

SENHA_WIN = 'SENHA-WIN-FALSA'
SENHA_EDI = 'SENHA-EDI-FALSA'
ACESSO = Acesso(
    windows_login='usuario-win',
    windows_senha=SENHA_WIN,
    edi_login='usuario-edi',
    edi_senha=SENHA_EDI,
)


class TelaFalsa:
    """Imita core.telas.Tela. Cada ENTER troca para a próxima tela do roteiro."""

    def __init__(self, telas_iniciais, telas_apos_enter=()):
        self.visiveis = set(telas_iniciais)
        self.roteiro = list(telas_apos_enter)
        self.acoes = []
        self.relogio = 0.0

    def agora(self):
        return self.relogio

    def esperar(self, segundos):
        self.relogio += segundos
        self.acoes.append(('esperar', segundos))

    def localizar(self, caminho):
        return (10, 20) if caminho in self.visiveis else None

    def clicar_duplo(self, caminho):
        if caminho in self.visiveis:
            self.acoes.append(('duplo', caminho))
            return True
        return False

    def colar(self, texto):
        self.acoes.append(('colar', texto))

    def tecla(self, nome):
        self.acoes.append(('tecla', nome))
        if nome == 'enter' and self.roteiro:
            self.visiveis = set(self.roteiro.pop(0))


def executar(tela, acesso=ACESSO):
    mensagens = []
    abertura = []
    resultado = fluxo.executar_ate_carregar(
        tela, acesso, mensagens.append, lambda: abertura.append(1))
    return resultado, mensagens, abertura


class TestPassoUm(unittest.TestCase):
    def test_caminho_feliz_para_no_checkpoint(self):
        tela = TelaFalsa({IMG_LOGIN}, [{IMG_LOGIN_EDI}, {IMG_INFORME, IMG_ULIANA}])

        resultado, mensagens, abertura = executar(tela)

        self.assertEqual(resultado, fluxo.CARREGANDO)
        self.assertEqual(abertura, [1], 'o .rdp deve ser aberto uma vez')
        self.assertEqual(tela.acoes, [
            ('colar', 'usuario-win'), ('tecla', 'tab'),
            ('colar', SENHA_WIN), ('tecla', 'enter'), ('esperar', fluxo.ESPERA_APOS_ENTER),
            ('colar', 'usuario-edi'), ('tecla', 'tab'),
            ('colar', SENHA_EDI), ('tecla', 'enter'), ('esperar', fluxo.ESPERA_APOS_ENTER),
            ('duplo', IMG_ULIANA), ('esperar', fluxo.TEMPO_CARREGAMENTO),
        ])
        self.assertTrue(any('CHECKPOINT' in m for m in mensagens))

    def test_nada_e_digitado_depois_do_checkpoint(self):
        tela = TelaFalsa({IMG_LOGIN}, [{IMG_LOGIN_EDI}, {IMG_INFORME, IMG_ULIANA}])
        executar(tela)
        self.assertEqual(tela.acoes[-1], ('esperar', fluxo.TEMPO_CARREGAMENTO))
        indice_duplo = tela.acoes.index(('duplo', IMG_ULIANA))
        depois = tela.acoes[indice_duplo + 1:]
        self.assertFalse([a for a in depois if a[0] in ('colar', 'tecla', 'duplo')])

    def test_login_do_edi_direto_nao_digita_o_windows(self):
        tela = TelaFalsa({IMG_LOGIN_EDI}, [{IMG_INFORME, IMG_ULIANA}])

        resultado, _, _ = executar(tela)

        self.assertEqual(resultado, fluxo.CARREGANDO)
        self.assertNotIn(('colar', 'usuario-win'), tela.acoes)
        self.assertIn(('colar', 'usuario-edi'), tela.acoes)

    def test_senha_errada_nao_redigita_e_para_pelo_prazo(self):
        # O ENTER não muda a tela: como se a senha estivesse errada.
        tela = TelaFalsa({IMG_LOGIN}, [])

        with self.assertRaises(FalhaFluxo) as contexto:
            executar(tela)

        self.assertIn('tempo limite', str(contexto.exception))
        self.assertEqual(tela.acoes.count(('colar', SENHA_WIN)), 1)
        self.assertEqual(tela.acoes.count(('colar', 'usuario-win')), 1)
        self.assertEqual(tela.acoes.count(('tecla', 'enter')), 1)

    def test_uliana_ausente_para_com_mensagem_clara(self):
        # A tela de parceiros aparece, mas sem a ULIANA na lista.
        tela = TelaFalsa({IMG_LOGIN_EDI}, [{IMG_INFORME}])

        with self.assertRaises(FalhaFluxo) as contexto:
            executar(tela)

        self.assertIn('ULIANA', str(contexto.exception))
        self.assertFalse([a for a in tela.acoes if a[0] == 'duplo'])

    def test_nada_visivel_estoura_prazo_sem_digitar_nada(self):
        tela = TelaFalsa(set(), [])

        with self.assertRaises(FalhaFluxo) as contexto:
            executar(tela)

        self.assertIn('tempo limite', str(contexto.exception))
        self.assertEqual([a for a in tela.acoes if a[0] == 'colar'], [])

    def test_segredos_nao_aparecem_em_log_nem_em_erro_nem_em_repr(self):
        tela_ok = TelaFalsa({IMG_LOGIN}, [{IMG_LOGIN_EDI}, {IMG_INFORME, IMG_ULIANA}])
        _, mensagens_ok, _ = executar(tela_ok)

        tela_erro = TelaFalsa({IMG_LOGIN}, [])
        with self.assertRaises(FalhaFluxo) as contexto:
            executar(tela_erro)
        mensagens_erro = [str(contexto.exception)]

        texto = '\n'.join(mensagens_ok + mensagens_erro) + repr(ACESSO)
        for segredo in (SENHA_WIN, SENHA_EDI):
            self.assertNotIn(segredo, texto)
        self.assertIn('usuario-win', repr(ACESSO), 'o login pode aparecer, a senha não')


if __name__ == '__main__':
    unittest.main()
