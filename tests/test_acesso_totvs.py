"""Testes sem desktop: executam as classes reais isolando imports GUI/Windows.

A carga por AST evita importar PyAutoGUI (exige display) e executar efeitos
colaterais globais (diretórios, arquivos e identidade da aplicação Windows).
"""
import ast
import os
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import janelas_windows

RAIZ = Path(__file__).resolve().parents[1]


def carregar_classe(arquivo, nome, ambiente):
    arvore = ast.parse((RAIZ / arquivo).read_text(encoding='utf-8'))
    for node in arvore.body:
        if isinstance(node, ast.Assign):
            try:
                valor = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    ambiente[target.id] = valor
    classe = next(n for n in arvore.body if isinstance(n, ast.ClassDef) and n.name == nome)
    exec(compile(ast.Module(body=[classe], type_ignores=[]), arquivo, 'exec'), ambiente)
    return ambiente[nome]


class TestFluxo(unittest.TestCase):
    def setUp(self):
        self.gui = Mock()
        self.gui.ImageNotFoundException = type('ImageNotFoundException', (Exception,), {})
        self.relogio = Mock()
        self.relogio.monotonic.side_effect = range(10000)
        self.env = dict(os=os, time=self.relogio, sys=sys, pyautogui=self.gui,
                        pyperclip=Mock(), janela_disponivel=Mock(return_value=True),
                        janela_em_primeiro_plano=Mock(return_value=True),
                        DIR_IMG=str(RAIZ / 'img'), DIR_BASE=str(RAIZ),
                        EDGE_DRIVER_PATH=str(RAIZ / 'msedgedriver.exe'), ARQUIVO_LOG='teste.log',
                        webdriver=Mock(), EdgeOptions=Mock(), EdgeService=Mock(),
                        WebDriverWait=Mock(), EC=Mock(), By=SimpleNamespace(ID='id'),
                        TimeoutException=type('TimeoutException', (Exception,), {}),
                        NoSuchElementException=type('NoSuchElementException', (Exception,), {}))
        cls = carregar_classe('automacao_totvs.py', 'AutomacaoTOTVS', self.env)
        self.bot = cls.__new__(cls)
        for metodo in ('log', 'log_debug', 'log_aviso', 'log_erro', 'log_sucesso',
                       'esperar', 'mostrar_erro_visivel', 'reabrir_interface', 'minimizar_todas_janelas'):
            setattr(self.bot, metodo, Mock())
        self.bot.totvs_login = 'operador_teste'
        self.bot.totvs_senha = 'senha_ficticia'
        self.bot._driver_login = None
        self.janela = SimpleNamespace(title='DATASUL Interactive - CE0220', _hWnd=123, isMinimized=True)

    def test_motor_retira_credenciais_do_ambiente(self):
        self.env['USUARIO_WINDOWS'] = 'teste'
        self.bot.iniciar_log = Mock()
        with patch.dict(os.environ, AUTOMACAO_TOTVS_LOGIN=' operador ',
                        AUTOMACAO_TOTVS_SENHA='senha_ficticia'):
            self.bot.__init__()
            self.assertEqual(self.bot.totvs_login, 'operador')
            self.assertEqual(self.bot.totvs_senha, 'senha_ficticia')
            self.assertNotIn('AUTOMACAO_TOTVS_LOGIN', os.environ)
            self.assertNotIn('AUTOMACAO_TOTVS_SENHA', os.environ)

    def test_janela_minimizada_valida(self):
        self.bot.lista_janelas = Mock(return_value=[self.janela])
        self.assertIs(self.bot.encontrar_janela_datasul(), self.janela)
        self.env['janela_disponivel'].assert_called_once_with(123)

    def test_ignora_titulo_do_edge_e_continua_busca(self):
        navegador = SimpleNamespace(title='DATASUL Interactive - Microsoft Edge', _hWnd=10)
        self.bot.lista_janelas = Mock(return_value=[navegador, self.janela])
        self.assertIs(self.bot.encontrar_janela_datasul(), self.janela)
        self.env['janela_disponivel'].assert_called_once_with(123)

    def test_ignora_processo_indisponivel_e_busca_proximo(self):
        self.bot.lista_janelas = Mock(return_value=[self.janela, self.janela])
        self.env['janela_disponivel'].side_effect = [False, True]
        self.assertIs(self.bot.encontrar_janela_datasul(), self.janela)

    def test_foco_incerto_nao_envia_tab_ou_atalho(self):
        self.bot.encontrar_janela_datasul = Mock(return_value=self.janela)
        self.bot.trazer_frente = Mock(return_value=True)
        self.bot.janela_em_foco = Mock(return_value=None)
        self.assertIsNone(self.bot.garantir_foco_datasul())
        self.gui.press.assert_not_called()
        self.gui.hotkey.assert_not_called()

    def test_foco_confirmado(self):
        self.bot.encontrar_janela_datasul = Mock(return_value=self.janela)
        self.bot.trazer_frente = Mock(return_value=True)
        self.assertIs(self.bot.garantir_foco_datasul(), self.janela)

    def test_foco_negado_interrompe_antes_ctrl_x(self):
        self.bot.snapshot_janelas = Mock(return_value={})
        self.bot.garantir_foco_datasul = Mock(return_value=None)
        self.assertFalse(self.bot.abrir_programa_no_totvs('ESPD0001'))
        self.gui.hotkey.assert_not_called()
        self.gui.typewrite.assert_not_called()

    def test_ctrl_x_apos_foco_e_nao_digita_se_lancador_nao_ativar(self):
        eventos = []
        self.bot.snapshot_janelas = Mock(return_value={})
        self.bot.garantir_foco_datasul = Mock(side_effect=lambda: eventos.append('foco') or self.janela)
        self.gui.hotkey.side_effect = lambda *keys: eventos.append(keys)
        self.bot.aguardar_janela_lancador = Mock(return_value=self.janela)
        self.bot.trazer_frente = Mock(return_value=False)
        self.assertFalse(self.bot.abrir_programa_no_totvs('ESPD0001'))
        self.assertEqual(eventos, ['foco', ('ctrl', 'x')])
        self.gui.typewrite.assert_not_called()

    def test_sessao_existente_nao_abre_edge(self):
        self.bot.encontrar_janela_datasul = Mock(return_value=self.janela)
        self.bot._abrir_datasul_com_navegador = Mock()
        self.bot.garantir_foco_datasul = Mock(return_value=self.janela)
        self.bot.abrir_programa_no_totvs = Mock(return_value=True)
        self.assertTrue(self.bot.importar_pedido())
        self.bot._abrir_datasul_com_navegador.assert_not_called()
        self.bot.minimizar_todas_janelas.assert_called_once()
        self.bot.abrir_programa_no_totvs.assert_called_once_with('ESPD0001')

    def test_sem_janela_abre_edge_e_continua(self):
        self.bot.encontrar_janela_datasul = Mock(return_value=None)
        self.bot._abrir_datasul_com_navegador = Mock(return_value=self.janela)
        self.bot.garantir_foco_datasul = Mock(return_value=self.janela)
        self.bot.abrir_programa_no_totvs = Mock(return_value=True)
        self.assertTrue(self.bot.importar_pedido())
        self.bot._abrir_datasul_com_navegador.assert_called_once()

    def test_falha_abertura_nao_continua(self):
        self.bot.encontrar_janela_datasul = Mock(return_value=None)
        self.bot._abrir_datasul_com_navegador = Mock(return_value=None)
        self.assertFalse(self.bot.importar_pedido())
        self.gui.hotkey.assert_not_called()
        self.bot.reabrir_interface.assert_called_once()

    def test_login_usa_credenciais_da_interface_e_url_menu(self):
        campos = [Mock(), Mock(), Mock()]
        self.env['WebDriverWait'].return_value.until.side_effect = campos
        self.bot.tratar_popup_abrir_aplicativo = Mock(return_value=True)
        self.assertTrue(self.bot._login_totvs_navegador())
        driver = self.env['webdriver'].Edge.return_value
        driver.get.assert_called_once_with('http://192.168.2.6:8080/totvs-menu')
        campos[0].send_keys.assert_called_once_with('operador_teste')
        campos[1].send_keys.assert_called_once_with('senha_ficticia')
        campos[2].click.assert_called_once()
        self.bot.tratar_popup_abrir_aplicativo.assert_called_once()
        driver.quit.assert_not_called()
        self.assertNotIn('senha_ficticia', str(self.bot.log.call_args_list))

    def test_senha_vazia_nao_abre_navegador(self):
        self.bot.totvs_senha = ''
        self.assertFalse(self.bot._login_totvs_navegador())
        self.env['webdriver'].Edge.assert_not_called()
        self.bot.mostrar_erro_visivel.assert_called_once()

    def test_falha_popup_fecha_driver(self):
        self.bot.tratar_popup_abrir_aplicativo = Mock(return_value=False)
        self.assertFalse(self.bot._login_totvs_navegador())
        self.env['webdriver'].Edge.return_value.quit.assert_called_once()
        self.assertIsNone(self.bot._driver_login)

    def test_timeout_login_fecha_driver_sem_vazar_senha(self):
        self.env['WebDriverWait'].return_value.until.side_effect = self.env['TimeoutException']('senha_ficticia')
        self.assertFalse(self.bot._login_totvs_navegador())
        self.env['webdriver'].Edge.return_value.quit.assert_called_once()
        self.assertNotIn('senha_ficticia', str(self.bot.log_erro.call_args_list))

    def test_imagem_abrir_tem_prioridade(self):
        self.bot.encontrar_janela_datasul = Mock(return_value=None)
        self.gui.locateCenterOnScreen.return_value = (100, 200)
        with patch('os.path.isfile', return_value=True):
            self.assertTrue(self.bot.tratar_popup_abrir_aplicativo())
        self.gui.locateCenterOnScreen.assert_called_once_with(str(RAIZ / 'img' / 'abrir.png'), confidence=0.9)
        self.gui.click.assert_called_once_with((100, 200))

    def test_imagem_atual_funciona_como_alternativa(self):
        self.bot.encontrar_janela_datasul = Mock(return_value=None)
        self.gui.locateCenterOnScreen.return_value = (10, 20)
        self.assertTrue(self.bot.tratar_popup_abrir_aplicativo())
        self.assertEqual(Path(self.gui.locateCenterOnScreen.call_args.args[0]).name, 'abrir_popup.png')

    def test_popup_ausente_nao_envia_atalhos_cegos(self):
        self.bot.encontrar_janela_datasul = Mock(return_value=None)
        self.gui.locateCenterOnScreen.side_effect = self.gui.ImageNotFoundException()
        self.assertFalse(self.bot.tratar_popup_abrir_aplicativo())
        self.gui.click.assert_not_called()
        self.gui.press.assert_not_called()
        self.gui.hotkey.assert_not_called()

    def test_datasul_abre_sem_popup(self):
        self.bot.encontrar_janela_datasul = Mock(return_value=self.janela)
        self.assertTrue(self.bot.tratar_popup_abrir_aplicativo())
        self.gui.click.assert_not_called()

    def test_aguarda_datasul_e_fecha_driver(self):
        self.bot._login_totvs_navegador = Mock(return_value=True)
        self.bot.encontrar_janela_datasul = Mock(side_effect=[None, self.janela])
        driver = self.bot._driver_login = Mock()
        self.assertIs(self.bot._abrir_datasul_com_navegador(), self.janela)
        driver.quit.assert_called_once()

    def test_timeout_datasul_fecha_driver_e_avisa(self):
        self.bot._login_totvs_navegador = Mock(return_value=True)
        self.bot.encontrar_janela_datasul = Mock(return_value=None)
        driver = self.bot._driver_login = Mock()
        self.assertIsNone(self.bot._abrir_datasul_com_navegador())
        driver.quit.assert_called_once()
        self.bot.mostrar_erro_visivel.assert_called_once()


class TestWindows(unittest.TestCase):
    def setUp(self):
        self.user = Mock()
        self.kernel = Mock()
        self.user.IsHungAppWindow.return_value = False
        self.user.GetWindowThreadProcessId.side_effect = self.pid
        self.kernel.WaitForSingleObject.return_value = 258
        self.kernel.QueryFullProcessImageNameW.side_effect = self.nome
        self.executavel = r'C:\TOTVS\prowin32.exe'
        self.addCleanup(patch.stopall)
        patch.object(janelas_windows.os, 'name', 'nt').start()
        patch.object(janelas_windows, '_apis', return_value=(self.user, self.kernel)).start()

    def pid(self, hwnd, ponteiro):
        ponteiro._obj.value = 321
        return 1

    def nome(self, processo, flags, buffer, tamanho):
        buffer.value = self.executavel
        return True

    def test_processo_vivo_e_fecha_handle(self):
        self.assertTrue(janelas_windows.janela_disponivel(123))
        self.kernel.CloseHandle.assert_called_once_with(self.kernel.OpenProcess.return_value)

    def test_edge_rejeitado_independente_do_titulo(self):
        self.executavel = r'C:\Edge\msedge.exe'
        self.assertFalse(janelas_windows.janela_disponivel(123))
        self.kernel.CloseHandle.assert_called_once()

    def test_processo_encerrado_rejeitado(self):
        self.kernel.WaitForSingleObject.return_value = 0
        self.assertFalse(janelas_windows.janela_disponivel(123))
        self.kernel.CloseHandle.assert_called_once()

    def test_janela_travada_rejeitada(self):
        self.user.IsHungAppWindow.return_value = True
        self.assertFalse(janelas_windows.janela_disponivel(123))
        self.kernel.OpenProcess.assert_not_called()

    def test_sem_permissao_rejeitado(self):
        self.kernel.OpenProcess.return_value = 0
        self.assertFalse(janelas_windows.janela_disponivel(123))
        self.kernel.CloseHandle.assert_not_called()

    def test_foco_exige_hwnd_correto(self):
        self.user.GetForegroundWindow.return_value = 123
        self.assertTrue(janelas_windows.janela_em_primeiro_plano(123))
        self.assertFalse(janelas_windows.janela_em_primeiro_plano(999))


class TestInterface(unittest.TestCase):
    def setUp(self):
        self.subprocess = Mock(DETACHED_PROCESS=8, CREATE_NEW_PROCESS_GROUP=512, CREATE_NO_WINDOW=134217728)
        self.env = dict(os=os, sys=SimpleNamespace(executable=sys.executable, frozen=False),
                        subprocess=self.subprocess, DIR_BASE=str(RAIZ), messagebox=Mock())
        cls = carregar_classe('lancamento_inventario.py', 'LancamentoInventario', self.env)
        self.ui = cls.__new__(cls)
        self.ui.totvs_login = Mock(get=Mock(return_value=' operador '))
        self.ui.totvs_senha = Mock(get=Mock(return_value=' senha ficticia '))
        self.ui.root = Mock()
        self.ui.salvar_relatorio = Mock()
        self.ui.lancamentos = [{'Item': 'teste', 'Ajustado': 'NÃO'}]

    def test_ambiente_nao_muda_processo_pai(self):
        antes = os.environ.copy()
        ambiente = self.ui.ambiente_automacao()
        self.assertEqual(ambiente['AUTOMACAO_TOTVS_LOGIN'], 'operador')
        self.assertEqual(ambiente['AUTOMACAO_TOTVS_SENHA'], ' senha ficticia ')
        self.assertEqual(dict(os.environ), antes)

    def test_credenciais_passadas_em_ambos_modos_py_e_exe(self):
        for frozen in (False, True):
            for metodo in ('iniciar_importacao', 'iniciar_automacao'):
                with self.subTest(frozen=frozen, metodo=metodo), patch('os.path.exists', return_value=True):
                    self.env['sys'].frozen = frozen
                    self.subprocess.Popen.reset_mock()
                    getattr(self.ui, metodo)()
                    args, kwargs = self.subprocess.Popen.call_args
                    self.assertEqual(kwargs['env']['AUTOMACAO_TOTVS_LOGIN'], 'operador')
                    self.assertEqual(kwargs['env']['AUTOMACAO_TOTVS_SENHA'], ' senha ficticia ')
                    self.assertNotIn('senha ficticia', str(args))


if __name__ == '__main__':
    unittest.main()
