"""Linha de comando do passo 1 (tudo simulado: sem VPS, sem Windows, sem prompts reais)."""
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from swprogramacao import __main__ as cli
from swprogramacao import fluxo, rdp


class TestCli(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        pasta = tmp.name
        self.log = os.path.join(pasta, 'log_teste.txt')

        self.rdp_arquivo = os.path.join(pasta, rdp.NOME_ARQUIVO)
        open(self.rdp_arquivo, 'w', encoding='utf-8').close()

        self.imagens = [os.path.join(pasta, nome) for nome in
                        ('login.png', 'login_edi.png', 'informe_parceiro.png', 'uliana.png')]
        for caminho in self.imagens:
            open(caminho, 'w').close()

        self.input = self._iniciar(patch('builtins.input', side_effect=['usuario-win', 'usuario-edi']))
        self.getpass = self._iniciar(patch.object(
            cli.getpass, 'getpass', side_effect=['SENHA-WIN-FALSA', 'SENHA-EDI-FALSA']))
        self.log_patch = self._iniciar(patch.object(cli, 'ARQUIVO_LOG', self.log))
        self.caminho_rdp = self._iniciar(patch.object(
            rdp, 'caminho_rdp', return_value=self.rdp_arquivo))
        self.abrir_rdp = self._iniciar(patch.object(rdp, 'abrir_rdp'))
        self.imagens_patch = self._iniciar(patch.object(fluxo, 'IMAGENS', tuple(self.imagens)))
        self.executar = self._iniciar(patch.object(fluxo, 'executar_ate_uliana'))
        self.executar.return_value = fluxo.ENCONTRADA
        # Sem acesso salvo: a linha de comando cai no pedido no terminal.
        self.carregar = self._iniciar(patch.object(
            cli.acessos, 'carregar_acesso', return_value=None))

    def _iniciar(self, patcher):
        mock = patcher.start()
        self.addCleanup(patcher.stop)
        return mock

    def _rodar(self, argv):
        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = cli.main(argv)
        return codigo, saida.getvalue()

    def _ler_log(self):
        if not os.path.exists(self.log):
            return ''
        with open(self.log, encoding='utf-8') as arquivo:
            return arquivo.read()

    def test_sem_imagem_para_antes_de_pedir_acesso(self):
        os.remove(self.imagens[0])  # falta login.png
        codigo, _ = self._rodar([])
        self.assertEqual(codigo, 1)
        self.input.assert_not_called()
        self.getpass.assert_not_called()
        self.assertIn('login.png', self._ler_log())

    def test_sem_rdp_para_antes_de_pedir_acesso(self):
        self.caminho_rdp.side_effect = rdp.RdpNaoEncontrado('não achei')
        codigo, _ = self._rodar([])
        self.assertEqual(codigo, 1)
        self.input.assert_not_called()
        self.getpass.assert_not_called()

    def test_campo_vazio_nao_abre_a_vps(self):
        casos = {
            'login do Windows vazio': (['', 'usuario-edi'], ['SENHA-WIN-FALSA', 'SENHA-EDI-FALSA']),
            'senha do EDI vazia': (['usuario-win', 'usuario-edi'], ['SENHA-WIN-FALSA', '']),
        }
        for nome, (entradas, senhas) in casos.items():
            with self.subTest(nome):
                self.input.side_effect = list(entradas)
                self.getpass.side_effect = list(senhas)
                codigo, _ = self._rodar([])
                self.assertEqual(codigo, 1)
                self.abrir_rdp.assert_not_called()
                self.executar.assert_not_called()

    def test_fluxo_recebe_os_acessos_digitados_e_abre_pela_funcao_certa(self):
        codigo, _ = self._rodar([])
        self.assertEqual(codigo, 0)
        tela, acesso, registrar = self.executar.call_args.args
        abrir = self.executar.call_args.kwargs['abrir_rdp']
        self.assertEqual(acesso.windows_login, 'usuario-win')
        self.assertEqual(acesso.windows_senha, 'SENHA-WIN-FALSA')
        self.assertEqual(acesso.edi_login, 'usuario-edi')
        self.assertEqual(acesso.edi_senha, 'SENHA-EDI-FALSA')
        abrir()
        self.abrir_rdp.assert_called_once_with(self.rdp_arquivo)

    def test_acesso_salvo_e_usado_sem_pedir_nada(self):
        acesso_salvo = fluxo.Acesso('win-salvo', 'S1', 'edi-salvo', 'S2')
        self.carregar.return_value = acesso_salvo

        codigo, _ = self._rodar([])

        self.assertEqual(codigo, 0)
        self.input.assert_not_called()
        self.getpass.assert_not_called()
        _, acesso_usado, _ = self.executar.call_args.args
        self.assertIs(acesso_usado, acesso_salvo)
        self.assertNotIn('S1', self._ler_log())
        self.assertNotIn('S2', self._ler_log())

    def test_erro_ao_carregar_acesso_para_antes_de_abrir(self):
        self.carregar.side_effect = cli.acessos.ErroAcesso('acesso salvo corrompido')
        codigo, _ = self._rodar([])
        self.assertEqual(codigo, 1)
        self.input.assert_not_called()
        self.executar.assert_not_called()
        self.abrir_rdp.assert_not_called()
        self.assertIn('corrompido', self._ler_log())

    def test_senhas_nunca_vao_para_o_log(self):
        def fluxo_falso(tela, acesso, registrar, abrir_rdp, preparar_vps=None):
            registrar('passo ok')
            return fluxo.ENCONTRADA
        self.executar.side_effect = fluxo_falso
        self._rodar([])
        log = self._ler_log()
        self.assertIn('passo ok', log)
        self.assertNotIn('SENHA', log)

    def test_falha_do_fluxo_vira_codigo_1_e_vai_para_o_log(self):
        self.executar.side_effect = fluxo.FalhaFluxo('a ULIANA não apareceu')
        codigo, _ = self._rodar([])
        self.assertEqual(codigo, 1)
        self.assertIn('PARADO: a ULIANA não apareceu', self._ler_log())

    def test_salvar_acesso_pede_e_grava_sem_abrir_a_vps(self):
        with patch.object(cli.acessos, 'salvar_acesso') as salvar:
            codigo, _ = self._rodar(['--salvar-acesso'])
        self.assertEqual(codigo, 0)
        acesso = salvar.call_args.args[0]
        self.assertEqual(acesso.windows_login, 'usuario-win')
        self.assertEqual(acesso.windows_senha, 'SENHA-WIN-FALSA')
        self.assertEqual(acesso.edi_login, 'usuario-edi')
        self.assertEqual(acesso.edi_senha, 'SENHA-EDI-FALSA')
        self.assertNotIn('SENHA', self._ler_log())
        self.executar.assert_not_called()
        self.abrir_rdp.assert_not_called()

    def test_salvar_acesso_incompleto_nao_grava(self):
        self.input.side_effect = ['', 'usuario-edi']
        with patch.object(cli.acessos, 'salvar_acesso') as salvar:
            codigo, _ = self._rodar(['--salvar-acesso'])
        self.assertEqual(codigo, 1)
        salvar.assert_not_called()

    def test_salvar_acesso_falha_de_protecao_termina_com_erro(self):
        with patch.object(cli.acessos, 'salvar_acesso',
                          side_effect=cli.acessos.ErroAcesso('requer Windows')):
            codigo, _ = self._rodar(['--salvar-acesso'])
        self.assertEqual(codigo, 1)

    def test_esquecer_acesso_apaga_e_nao_roda_o_fluxo(self):
        with patch.object(cli.acessos, 'esquecer_acesso') as esquecer:
            codigo, _ = self._rodar(['--esquecer-acesso'])
        self.assertEqual(codigo, 0)
        esquecer.assert_called_once_with()
        self.executar.assert_not_called()
        self.abrir_rdp.assert_not_called()

    def test_diagnostico_nao_pede_acesso_nem_abre_a_vps(self):
        tela_falsa = MagicMock(name='Tela')
        tela_falsa.localizar.return_value = None
        self._iniciar(patch.object(cli.telas, 'Tela', return_value=tela_falsa))

        codigo, saida = self._rodar(['--diagnostico'])

        self.assertEqual(codigo, 0)
        self.input.assert_not_called()
        self.getpass.assert_not_called()
        self.executar.assert_not_called()
        self.abrir_rdp.assert_not_called()
        self.assertIn('login.png', saida)
        self.assertIn('não visível agora', saida)
        self.assertIn('Acesso (sem mostrar valores)', saida)
        self.assertIn('SW_*', saida)

    def _tela_de_diagnostico(self, **atributos):
        tela = MagicMock(name='Tela')
        tela.localizar.return_value = None
        tela.confianca = 0.9
        tela.confianca_minima = 0.6
        tela.ultima_confianca = None
        tela.tamanho_tela.return_value = (1920, 1080)
        tela.tamanho_imagem.return_value = (812, 344)
        tela.descricao_tela.return_value = 'resolução 1920x1080; escala 150%; DPI aware'
        for nome, valor in atributos.items():
            setattr(tela, nome, valor)
        self._iniciar(patch.object(cli.telas, 'Tela', return_value=tela))
        return tela

    def test_diagnostico_mostra_pasta_resolucao_e_tamanho_das_capturas(self):
        self._tela_de_diagnostico()
        self._iniciar(patch.object(cli.janelas, 'janelas_por_titulo', return_value=[]))

        codigo, saida = self._rodar(['--diagnostico'])

        self.assertEqual(codigo, 0)
        self.assertIn(fluxo.PASTA_IMAGENS, saida)
        self.assertIn('resolução 1920x1080', saida)
        self.assertIn('812x344 px', saida)
        self.assertIn('de 0.9 até 0.6 de confiança', saida)
        self.assertIn('janela da VPS: não está aberta', saida)

    def test_diagnostico_avisa_quando_a_captura_e_maior_que_a_tela(self):
        tela = self._tela_de_diagnostico()
        tela.tamanho_imagem.return_value = (2400, 1300)
        self._iniciar(patch.object(cli.janelas, 'janelas_por_titulo', return_value=[]))

        _, saida = self._rodar(['--diagnostico'])

        self.assertIn('MAIOR que a tela: nunca será encontrada', saida)

    def test_diagnostico_mostra_a_janela_da_vps_aberta(self):
        self._tela_de_diagnostico()
        janela = MagicMock(name='janela')
        janela.title = 'Conexão de Área de Trabalho Remota - VPS'
        self._iniciar(patch.object(cli.janelas, 'janelas_por_titulo', return_value=[janela]))

        _, saida = self._rodar(['--diagnostico'])

        self.assertIn('janela da VPS: Conexão de Área de Trabalho Remota - VPS', saida)

    def test_diagnostico_mostra_a_confianca_em_que_a_imagem_casou(self):
        self._tela_de_diagnostico(
            ultima_confianca=0.75, localizar=lambda caminho: SimpleNamespace(x=10, y=20))

        _, saida = self._rodar(['--diagnostico'])

        self.assertIn('visível em 10,20 (confiança 0.75)', saida)

    def test_fluxo_recebe_preparar_vps_para_trazer_a_vps_para_frente(self):
        codigo, _ = self._rodar([])
        self.assertEqual(codigo, 0)
        preparar = self.executar.call_args.kwargs['preparar_vps']
        self.assertTrue(callable(preparar))
        with patch.object(fluxo, 'trazer_vps_para_frente', return_value=True) as trazer:
            preparar()
        trazer.assert_called_once()


class TestConfiancaMinima(unittest.TestCase):
    """--confianca-minima é a alavanca para uma captura que só casa frouxa."""

    @staticmethod
    def _silencioso(argv):
        saida = io.StringIO()
        with redirect_stdout(saida):
            return cli.main(argv)

    def test_numero_valido_vai_para_a_tela(self):
        with patch.object(cli.telas, 'Tela') as criar:
            self._silencioso(['--confianca-minima', '0.7', '--diagnostico'])
        self.assertEqual(criar.call_args.kwargs, {'confianca_minima': 0.7})

    def test_padrao_e_a_minima_do_modulo(self):
        with patch.object(cli.telas, 'Tela') as criar:
            self._silencioso(['--diagnostico'])
        self.assertEqual(criar.call_args.kwargs,
                         {'confianca_minima': cli.telas.CONFIANCA_MINIMA})

    def casos_invalidos(self):
        return {
            'sem número': ['--confianca-minima'],
            'não é número': ['--confianca-minima', 'abc'],
            'acima de 1': ['--confianca-minima', '1.5'],
            'zero': ['--confianca-minima', '0'],
            'negativo': ['--confianca-minima', '-0.2'],
        }

    def test_valor_invalido_para_sem_abrir_a_vps(self):
        for nome, argv in self.casos_invalidos().items():
            with self.subTest(nome):
                saida = io.StringIO()
                with redirect_stdout(saida):
                    codigo = cli.main(argv)
                self.assertEqual(codigo, 1)
                self.assertIn('--confianca-minima', saida.getvalue())

    def test_valor_invalido_nem_cria_a_tela(self):
        with patch.object(cli.telas, 'Tela') as criar:
            self._silencioso(['--confianca-minima', 'abc'])
        criar.assert_not_called()

    def test_limite_um_e_aceito(self):
        with patch.object(cli.telas, 'Tela') as criar:
            codigo = self._silencioso(['--confianca-minima', '1', '--diagnostico'])
        self.assertEqual(codigo, 0)
        self.assertEqual(criar.call_args.kwargs, {'confianca_minima': 1.0})


if __name__ == '__main__':
    unittest.main()
