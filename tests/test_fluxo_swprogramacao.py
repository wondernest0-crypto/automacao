"""Passo 1 da SWProgramação com uma tela falsa (sem Windows e sem VPS).

A tela falsa segue um roteiro: as imagens visíveis mudam a cada ENTER.
O relógio também é falso, então os testes não esperam de verdade.
Sequência testada: espera de 10 s após abrir o .rdp, login do Windows (3 s),
login do EDI (4 s), tela de parceiros, ULIANA clicada 3 vezes, pausa final
e sucesso (a VPS permanece aberta).
"""
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

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

NOMES_IMAGENS = ('login.png', 'login_edi.png', 'informe_parceiro.png', 'uliana.png')


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

    def clicar(self, posicao, vezes=1, intervalo=0.7):
        self.acoes.append(('clicar', vezes))

    def clicar_duplo(self, caminho):  # o passo 1 não deve usar isto
        self.acoes.append(('duplo', caminho))
        return caminho in self.visiveis

    def colar(self, texto):
        self.acoes.append(('colar', texto))

    def tecla(self, nome):
        self.acoes.append(('tecla', nome))
        if nome == 'enter' and self.roteiro:
            self.visiveis = set(self.roteiro.pop(0))


def executar(tela, acesso=ACESSO):
    mensagens = []
    abertura = []
    resultado = fluxo.executar_ate_uliana(
        tela, acesso, mensagens.append, lambda: abertura.append(1))
    return resultado, mensagens, abertura


class TestPassoUm(unittest.TestCase):
    def setUp(self):
        # As capturas reais ficam só no PC local (gitignore): o teste não pode
        # depender delas existirem no repositório.
        patcher = patch.object(fluxo, 'validar_imagens', lambda imagens=None: None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_caminho_feliz_procura_uliana_e_termina(self):
        tela = TelaFalsa({IMG_LOGIN}, [{IMG_LOGIN_EDI}, {IMG_INFORME, IMG_ULIANA}])

        resultado, mensagens, abertura = executar(tela)

        self.assertEqual(resultado, fluxo.ENCONTRADA)
        self.assertEqual(abertura, [1], 'o .rdp deve ser aberto uma vez')
        self.assertEqual(tela.acoes, [
            ('esperar', fluxo.ESPERA_APOS_ABRIR_RDP),
            ('colar', 'usuario-win'), ('tecla', 'tab'),
            ('colar', SENHA_WIN), ('tecla', 'enter'), ('esperar', fluxo.ESPERA_APOS_ENTER_WINDOWS),
            ('colar', 'usuario-edi'), ('tecla', 'tab'),
            ('colar', SENHA_EDI), ('tecla', 'enter'), ('esperar', fluxo.ESPERA_APOS_ENTER_EDI),
            ('clicar', fluxo.CLIQUES_ULIANA), ('esperar', fluxo.PAUSA_APOS_ULIANA),
        ])
        self.assertTrue(any('ULIANA encontrada' in m for m in mensagens))

    def test_espera_dez_segundos_apos_abrir_o_rdp_antes_de_procurar(self):
        self.assertEqual(fluxo.ESPERA_APOS_ABRIR_RDP, 10.0)
        tela = TelaFalsa({IMG_LOGIN}, [{IMG_LOGIN_EDI}, {IMG_INFORME, IMG_ULIANA}])
        executar(tela)
        self.assertEqual(tela.acoes[0], ('esperar', 10.0))
        self.assertLess(tela.acoes.index(('esperar', 10.0)),
                        tela.acoes.index(('colar', 'usuario-win')))

    def test_espera_do_edi_e_de_4_segundos(self):
        self.assertEqual(fluxo.ESPERA_APOS_ENTER_EDI, 4.0)
        tela = TelaFalsa({IMG_LOGIN_EDI}, [{IMG_INFORME, IMG_ULIANA}])
        executar(tela)
        indice_enter = tela.acoes.index(('tecla', 'enter'))
        self.assertEqual(tela.acoes[indice_enter + 1], ('esperar', 4.0))

    def test_uliana_recebe_tres_cliques_e_pausa_final(self):
        # A ULIANA é clicada 3 vezes; o passo pausa e termina com sucesso.
        tela = TelaFalsa({IMG_LOGIN}, [{IMG_LOGIN_EDI}, {IMG_INFORME, IMG_ULIANA}])
        resultado, mensagens, _ = executar(tela)
        self.assertEqual(resultado, fluxo.ENCONTRADA)
        self.assertEqual(fluxo.CLIQUES_ULIANA, 3)
        self.assertEqual(tela.acoes[-2:],
                         [('clicar', 3), ('esperar', fluxo.PAUSA_APOS_ULIANA)])
        # Nada é digitado depois dos cliques na ULIANA.
        ultimo_colar = max(i for i, acao in enumerate(tela.acoes) if acao[0] == 'colar')
        self.assertLess(ultimo_colar, tela.acoes.index(('clicar', 3)))
        self.assertFalse([a for a in tela.acoes if a[0] == 'duplo'])
        self.assertTrue(any('clicando 3 vezes' in m for m in mensagens))

    def test_login_do_edi_direto_nao_digita_o_windows(self):
        tela = TelaFalsa({IMG_LOGIN_EDI}, [{IMG_INFORME, IMG_ULIANA}])

        resultado, _, _ = executar(tela)

        self.assertEqual(resultado, fluxo.ENCONTRADA)
        self.assertNotIn(('colar', 'usuario-win'), tela.acoes)
        self.assertIn(('colar', 'usuario-edi'), tela.acoes)

    def test_ambos_logins_visiveis_preenche_windows_primeiro(self):
        # As duas telas de login visíveis no mesmo ciclo: o Windows vem primeiro.
        tela = TelaFalsa({IMG_LOGIN, IMG_LOGIN_EDI}, [])

        with self.assertRaises(FalhaFluxo):
            executar(tela)

        primeiro_win = tela.acoes.index(('colar', 'usuario-win'))
        primeiro_edi = tela.acoes.index(('colar', 'usuario-edi'))
        self.assertLess(primeiro_win, primeiro_edi)

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
        self.assertFalse([a for a in tela.acoes if a[0] in ('duplo', 'clicar')],
                         'sem ULIANA na tela, nada deve ser clicado')

    def test_uliana_que_aparece_depois_ainda_e_encontrada(self):
        # A ULIANA demora um pouco: o passo espera e termina quando ela aparece.
        class TelaUlianaTardia(TelaFalsa):
            def localizar(self, caminho):
                if caminho == IMG_ULIANA:
                    self.procuras = getattr(self, 'procuras', 0) + 1
                    return (10, 20) if self.procuras >= 3 else None
                return super().localizar(caminho)

        tela = TelaUlianaTardia({IMG_LOGIN_EDI, IMG_INFORME}, [])
        resultado, _, _ = executar(tela)
        self.assertEqual(resultado, fluxo.ENCONTRADA)
        self.assertEqual(tela.procuras, 3)
        self.assertIn(('clicar', 3), tela.acoes, 'achou a ULIANA: clica 3 vezes')

    def test_login_edi_e_preenchido_mesmo_com_informe_visivel(self):
        # Procura em cascata: login_edi.png visível junto com informe_parceiro.png
        # ainda preenche o EDI antes de sair do loop pela tela de parceiros.
        tela = TelaFalsa({IMG_LOGIN_EDI, IMG_INFORME}, [{IMG_INFORME, IMG_ULIANA}])

        resultado, _, _ = executar(tela)

        self.assertEqual(resultado, fluxo.ENCONTRADA)
        self.assertIn(('colar', 'usuario-edi'), tela.acoes)
        self.assertIn(('clicar', 3), tela.acoes)

    def test_nada_visivel_estoura_prazo_sem_digitar_nada(self):
        tela = TelaFalsa(set(), [])

        with self.assertRaises(FalhaFluxo) as contexto:
            executar(tela)

        self.assertIn('tempo limite', str(contexto.exception))
        self.assertEqual([a for a in tela.acoes if a[0] == 'colar'], [])

    def test_enquanto_espera_registra_que_procura_todas_as_imagens(self):
        tela = TelaFalsa(set(), [])
        mensagens = []

        with self.assertRaises(FalhaFluxo):
            fluxo.executar_ate_uliana(tela, ACESSO, mensagens.append, lambda: None)

        varreduras = [m for m in mensagens if 'Procurando na tela' in m]
        self.assertTrue(varreduras, 'deve registrar que segue procurando')
        for nome in ('login.png', 'login_edi.png', 'informe_parceiro.png'):
            self.assertIn(nome, varreduras[0])

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


class TestValidarImagens(unittest.TestCase):
    def test_todas_presentes_nao_levanta(self):
        with tempfile.TemporaryDirectory() as pasta:
            imagens = tuple(os.path.join(pasta, nome) for nome in NOMES_IMAGENS)
            for caminho in imagens:
                open(caminho, 'w').close()
            self.assertIsNone(fluxo.validar_imagens(imagens))

    def test_lista_somente_o_que_falta(self):
        with tempfile.TemporaryDirectory() as pasta:
            imagens = tuple(os.path.join(pasta, nome) for nome in NOMES_IMAGENS)
            for caminho in imagens[1:]:
                open(caminho, 'w').close()
            with self.assertRaises(FalhaFluxo) as contexto:
                fluxo.validar_imagens(imagens)
        mensagem = str(contexto.exception)
        self.assertIn('login.png', mensagem)
        self.assertTrue(mensagem.startswith('Faltam imagens em img/swprogramacao/:'),
                        f'a mensagem deve mostrar a pasta correta: {mensagem}')
        self.assertNotIn('uliana.png', mensagem)

    def test_imagem_faltando_para_antes_de_abrir_a_vps(self):
        with tempfile.TemporaryDirectory() as pasta:
            imagens = tuple(os.path.join(pasta, nome) for nome in NOMES_IMAGENS)
            for caminho in imagens[1:]:
                open(caminho, 'w').close()
            with patch.object(fluxo, 'IMAGENS', imagens):
                tela = TelaFalsa(set(), [])
                abertura = []
                with self.assertRaises(FalhaFluxo) as contexto:
                    fluxo.executar_ate_uliana(
                        tela, ACESSO, lambda m: None, lambda: abertura.append(1))
        self.assertIn('login.png', str(contexto.exception))
        self.assertEqual(abertura, [], 'não deve abrir a VPS com imagem faltando')
        self.assertEqual([a for a in tela.acoes if a[0] == 'colar'], [])


class TestTrazerVpsParaFrente(unittest.TestCase):
    """A busca por imagem só enxerga o que está visível na tela."""

    def test_acha_a_janela_e_traz_para_o_primeiro_plano(self):
        tela = TelaFalsa(set(), [])
        janela = MagicMock(name='janela', title='Conexão de Área de Trabalho Remota - VPS')
        mensagens = []

        with patch.object(fluxo.janelas, 'janelas_por_titulo', return_value=[janela]), \
                patch.object(fluxo.janelas, 'trazer_para_frente', return_value=True) as trazer:
            resultado = fluxo.trazer_vps_para_frente(tela, mensagens.append)

        self.assertTrue(resultado)
        trazer.assert_called_once_with(janela)
        self.assertTrue(any('primeiro plano' in m for m in mensagens), mensagens)

    def test_janela_achada_mas_sem_foco_avisa_sem_estourar(self):
        tela = TelaFalsa(set(), [])
        janela = MagicMock(name='janela', title='VPS')
        mensagens = []

        with patch.object(fluxo.janelas, 'janelas_por_titulo', return_value=[janela]), \
                patch.object(fluxo.janelas, 'trazer_para_frente', return_value=False):
            resultado = fluxo.trazer_vps_para_frente(tela, mensagens.append)

        self.assertFalse(resultado)
        self.assertTrue(any('manualmente' in m for m in mensagens), mensagens)

    def test_sem_janela_espera_ate_o_prazo_e_avisa(self):
        tela = TelaFalsa(set(), [])
        mensagens = []

        with patch.object(fluxo.janelas, 'janelas_por_titulo', return_value=[]):
            resultado = fluxo.trazer_vps_para_frente(tela, mensagens.append, prazo=3)

        self.assertFalse(resultado)
        self.assertIn(('esperar', fluxo.INTERVALO_JANELA), tela.acoes)
        self.assertTrue(any('Não achei a janela' in m for m in mensagens), mensagens)


class TestContextoDeTela(unittest.TestCase):
    """Os números que explicam 'o arquivo existe mas nunca é achado'."""

    def setUp(self):
        # As capturas reais ficam só no PC local: o teste não depende delas.
        patcher = patch.object(fluxo, 'validar_imagens', lambda imagens=None: None)
        patcher.start()
        self.addCleanup(patcher.stop)

    class TelaMedida(TelaFalsa):
        def __init__(self, tamanho_tela, tamanho_imagem, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._tela = tamanho_tela
            self._imagem = tamanho_imagem

        def tamanho_tela(self):
            return self._tela

        def tamanho_imagem(self, caminho):
            return self._imagem

        def descricao_tela(self):
            return 'resolução 1920x1080; escala 150%; DPI aware'

    def test_registra_resolucao_e_tamanho_das_capturas(self):
        tela = self.TelaMedida((1920, 1080), (812, 344),
                               {IMG_LOGIN}, [{IMG_LOGIN_EDI}, {IMG_INFORME, IMG_ULIANA}])
        mensagens = []

        fluxo.executar_ate_uliana(tela, ACESSO, mensagens.append, lambda: None)

        texto = '\n'.join(mensagens)
        self.assertIn('resolução 1920x1080; escala 150%', texto)
        self.assertIn('login.png: 812x344 px', texto)
        self.assertIn('uliana.png: 812x344 px', texto)
        self.assertNotIn('MAIOR que a tela', texto)

    def test_avisa_quando_a_captura_e_maior_que_a_tela(self):
        # Captura feita em outra resolução: nunca vai casar, e o log diz na hora.
        tela = self.TelaMedida((1920, 1080), (2400, 1300),
                               {IMG_LOGIN}, [{IMG_LOGIN_EDI}, {IMG_INFORME, IMG_ULIANA}])
        mensagens = []

        fluxo.executar_ate_uliana(tela, ACESSO, mensagens.append, lambda: None)

        self.assertTrue(any('MAIOR que a tela atual' in m for m in mensagens), mensagens)

    def test_tela_sem_medidas_nao_quebra_o_fluxo(self):
        # A tela falsa antiga não mede nada: o passo segue, só sem o diagnóstico.
        tela = TelaFalsa({IMG_LOGIN}, [{IMG_LOGIN_EDI}, {IMG_INFORME, IMG_ULIANA}])
        resultado, _, _ = executar(tela)
        self.assertEqual(resultado, fluxo.ENCONTRADA)


class TestPrepararVpsNoFluxo(unittest.TestCase):
    def setUp(self):
        patcher = patch.object(fluxo, 'validar_imagens', lambda imagens=None: None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_rodou_depois_de_abrir_o_rdp_e_antes_de_procurar(self):
        tela = TelaFalsa({IMG_LOGIN}, [{IMG_LOGIN_EDI}, {IMG_INFORME, IMG_ULIANA}])
        ordem = []

        fluxo.executar_ate_uliana(
            tela, ACESSO, ordem.append, lambda: ordem.append('abrir_rdp'),
            preparar_vps=lambda: ordem.append('preparar_vps'))

        self.assertLess(ordem.index('abrir_rdp'), ordem.index('preparar_vps'))

    def test_contexto_vem_depois_de_preparar_a_vps(self):
        tela = TelaFalsa({IMG_LOGIN}, [{IMG_LOGIN_EDI}, {IMG_INFORME, IMG_ULIANA}])
        tela.tamanho_tela = lambda: (1920, 1080)
        tela.tamanho_imagem = lambda caminho: (100, 40)
        tela.descricao_tela = lambda: 'resolução 1920x1080'
        ordem = []

        fluxo.executar_ate_uliana(
            tela, ACESSO, ordem.append, lambda: ordem.append('abrir_rdp'),
            preparar_vps=lambda: ordem.append('preparar_vps'))

        indice_contexto = next(i for i, m in enumerate(ordem) if m.startswith('Tela:'))
        self.assertLess(ordem.index('preparar_vps'), indice_contexto)

    def test_sem_preparar_vps_o_fluxo_funciona_igual(self):
        tela = TelaFalsa({IMG_LOGIN}, [{IMG_LOGIN_EDI}, {IMG_INFORME, IMG_ULIANA}])
        resultado, _, abertura = executar(tela)
        self.assertEqual(resultado, fluxo.ENCONTRADA)
        self.assertEqual(abertura, [1])


if __name__ == '__main__':
    unittest.main()
