"""Sequência do START (orquestrador.py, na raiz): a VPS primeiro, o DATASUL depois.

Hoje a entrada no DATASUL não existe na sequência: o START roda SOMENTE o
procedimento do SWPROGRAMACAO.rdp e encerra na ULIANA. Os testes usam um bot
falso (o mesmo "contrato" do AutomacaoTOTVS: log, log_erro,
mostrar_erro_visivel e reabrir_interface) e um passo 1 simulado — sem Windows,
sem VPS e sem tela.
"""
import importlib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import orquestrador
from swprogramacao import fluxo


class BotFalso:
    """Imita o que o orquestrador usa do AutomacaoTOTVS."""

    def __init__(self):
        self.mensagens = []
        self.avisos = []
        self.reabertas = 0

    def log(self, msg):
        self.mensagens.append(str(msg))

    def log_erro(self, msg):
        self.log(msg)

    def log_sucesso(self, msg):
        self.log(msg)

    def log_aviso(self, msg):
        self.log(msg)

    def mostrar_erro_visivel(self, titulo, mensagem):
        self.avisos.append((titulo, mensagem))

    def reabrir_interface(self):
        self.reabertas += 1

    @property
    def texto(self):
        return '\n'.join(self.mensagens)


class TestSequenciaDoStart(unittest.TestCase):
    def setUp(self):
        self.passo = MagicMock(name='executar_passo_um', return_value=fluxo.ENCONTRADA)
        patcher = patch.object(orquestrador.execucao, 'executar_passo_um', self.passo)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _rodar(self, entrar_no_datasul=None, bot=None):
        bot = bot or BotFalso()
        return bot, orquestrador.rodar_importacao(bot, entrar_no_datasul=entrar_no_datasul)

    def test_start_roda_a_vps_e_nao_abre_o_datasul(self):
        datasul = MagicMock(name='entrar_no_datasul')

        bot, resultado = self._rodar()

        self.assertEqual(self.passo.call_count, 1, 'o passo 1 da VPS deve rodar uma vez')
        datasul.assert_not_called()
        self.assertTrue(resultado.concluiu)
        self.assertFalse(resultado.entrou_no_datasul)
        self.assertEqual(resultado.motivo, '')
        self.assertEqual(bot.reabertas, 1, 'a interface precisa voltar no fim')
        self.assertEqual(bot.avisos, [], 'sem erro não há caixa de aviso')

    def test_log_diz_que_o_datasul_esta_desligado_e_que_a_vps_terminou(self):
        bot, _ = self._rodar()

        self.assertIn('DATASUL', bot.texto)
        self.assertIn('DESLIGADA', bot.texto)
        self.assertIn('SWPROGRAMACAO.rdp', bot.texto)

    def test_passo_um_recebe_quem_registra_as_mensagens(self):
        bot = BotFalso()

        self._rodar(bot=bot)

        registrar = self.passo.call_args.args[0]
        registrar('mensagem de teste')
        self.assertIn('mensagem de teste', bot.texto)

    def test_a_vps_vem_antes_do_datasul_quando_ele_existe_na_sequencia(self):
        ordem = []
        self.passo.side_effect = lambda *args, **kwargs: ordem.append('vps') or fluxo.ENCONTRADA
        entrar = lambda: ordem.append('datasul') or True  # noqa: E731

        _, resultado = self._rodar(entrar_no_datasul=entrar)

        self.assertEqual(ordem, ['vps', 'datasul'])
        self.assertTrue(resultado.concluiu)
        self.assertTrue(resultado.entrou_no_datasul)

    def test_falha_na_vps_nao_entra_no_datasul(self):
        self.passo.side_effect = fluxo.FalhaFluxo('a ULIANA não apareceu')
        datasul = MagicMock(name='entrar_no_datasul')

        bot, resultado = self._rodar(entrar_no_datasul=datasul)

        datasul.assert_not_called()
        self.assertFalse(resultado.concluiu)
        self.assertFalse(resultado.entrou_no_datasul)
        self.assertIn('ULIANA', resultado.motivo)
        self.assertIn('ULIANA', bot.texto)
        self.assertEqual(len(bot.avisos), 1, 'o usuário precisa ver o aviso na tela')
        self.assertEqual(bot.reabertas, 1)

    def test_sem_acesso_salvo_avisa_como_salvar_e_nao_abre_o_datasul(self):
        self.passo.side_effect = fluxo.FalhaFluxo(
            'não há acesso da VPS salvo. Salve uma vez com '
            '"python -m swprogramacao --salvar-acesso"')
        datasul = MagicMock(name='entrar_no_datasul')

        bot, resultado = self._rodar(entrar_no_datasul=datasul)

        datasul.assert_not_called()
        self.assertFalse(resultado.concluiu)
        self.assertIn('--salvar-acesso', bot.texto)
        self.assertIn('--salvar-acesso', bot.avisos[0][1])

    def test_imagem_faltando_para_antes_de_qualquer_tecla(self):
        self.passo.side_effect = fluxo.FalhaFluxo(
            'Faltam imagens em img/swprogramacao/: login.png')
        datasul = MagicMock(name='entrar_no_datasul')

        _, resultado = self._rodar(entrar_no_datasul=datasul)

        datasul.assert_not_called()
        self.assertFalse(resultado.concluiu)
        self.assertIn('login.png', resultado.motivo)

    def test_datasul_que_falha_devolve_o_motivo(self):
        bot, resultado = self._rodar(entrar_no_datasul=lambda: False)

        self.assertFalse(resultado.concluiu)
        self.assertTrue(resultado.entrou_no_datasul)
        self.assertTrue(resultado.motivo)
        self.assertEqual(len(bot.avisos), 1)

    def test_datasul_que_levanta_erro_nao_deixa_o_motivo_vazio(self):
        def entrar():
            raise RuntimeError('DATASUL não abriu')

        bot, resultado = self._rodar(entrar_no_datasul=entrar)

        self.assertFalse(resultado.concluiu)
        self.assertIn('DATASUL não abriu', resultado.motivo)
        self.assertEqual(len(bot.avisos), 1)

    def test_erro_inesperado_reabre_a_interface_e_mostra_o_erro(self):
        self.passo.side_effect = RuntimeError('pyautogui não carrega')

        bot, resultado = self._rodar()

        self.assertFalse(resultado.concluiu)
        self.assertIn('pyautogui não carrega', bot.texto)
        self.assertEqual(bot.reabertas, 1)
        self.assertEqual(len(bot.avisos), 1)

    def test_mensagens_de_ordem_ficam_no_log(self):
        bot, _ = self._rodar()

        self.assertIn(orquestrador.MENSAGEM_ORDEM, bot.texto)


class TestPontoDeEntrada(unittest.TestCase):
    """automacao_totvs.py: só o modo 'importar' passa pelo orquestrador."""

    def _carregar(self):
        """Importa o ponto de entrada com a parte TOTVS substituída por um falso.

        O motor real exige pandas/selenium (que não existem neste ambiente de
        teste), e o que este teste confere é só para quem o ponto de entrada
        delega.
        """
        totvs_falso = SimpleNamespace(
            main=MagicMock(name='main_totvs'),
            AutomacaoTOTVS=MagicMock(name='AutomacaoTOTVS'))
        with patch.dict(sys.modules, {'totvs.automacao': totvs_falso}):
            return importlib.import_module('automacao_totvs'), totvs_falso

    def _rodar(self, argv, modulo):
        with patch.object(modulo, 'rodar_importacao') as rodar, \
                patch.object(sys, 'argv', argv):
            modulo.main()
        return rodar

    def test_modo_importar_vai_para_o_orquestrador(self):
        modulo, totvs_falso = self._carregar()

        rodar = self._rodar(['automacao_totvs.py', 'importar'], modulo)

        rodar.assert_called_once()
        totvs_falso.main.assert_not_called()

    def test_sem_argumento_continua_rodando_a_automacao_de_inventario(self):
        modulo, totvs_falso = self._carregar()

        rodar = self._rodar(['automacao_totvs.py'], modulo)

        rodar.assert_not_called()
        totvs_falso.main.assert_called_once_with()

    def test_modo_importar_entrega_um_bot_ao_orquestrador(self):
        modulo, totvs_falso = self._carregar()

        rodar = self._rodar(['automacao_totvs.py', 'importar'], modulo)

        bot = rodar.call_args.args[0]
        self.assertIs(bot, totvs_falso.AutomacaoTOTVS.return_value)


if __name__ == '__main__':
    unittest.main()
