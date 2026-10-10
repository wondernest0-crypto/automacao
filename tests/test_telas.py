"""core/telas.py com pyautogui e pyperclip falsos (funciona sem tela e sem Windows)."""
import sys
import unittest
from collections import namedtuple
from unittest.mock import MagicMock, call, patch

from core import telas

Ponto = namedtuple('Ponto', 'x y')


class ImageNotFoundException(Exception):
    """Mesmo nome que o PyAutoGUI usa; Tela.localizar identifica pelo nome."""


def _pyautogui_falso():
    pag = MagicMock(name='pyautogui')
    return pag


class TestTela(unittest.TestCase):
    def setUp(self):
        self.pag = _pyautogui_falso()
        patcher = patch.dict(sys.modules, {'pyautogui': self.pag})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_localizar_devolve_none_quando_levanta_image_not_found(self):
        self.pag.locateCenterOnScreen.side_effect = ImageNotFoundException('x')
        self.assertIsNone(telas.Tela().localizar('img.png'))

    def test_localizar_devolve_none_quando_retorna_none(self):
        self.pag.locateCenterOnScreen.return_value = None
        self.assertIsNone(telas.Tela().localizar('img.png'))

    def test_localizar_repassa_outros_erros(self):
        self.pag.locateCenterOnScreen.side_effect = OSError('tela indisponível')
        with self.assertRaises(OSError):
            telas.Tela().localizar('img.png')

    def test_arquivo_de_imagem_inexistente_levanta_mensagem_clara(self):
        self.pag.locateCenterOnScreen.side_effect = FileNotFoundError('x')
        with self.assertRaises(RuntimeError) as contexto:
            telas.Tela().localizar('img/swprogramacao/login.png')
        self.assertIn('img/swprogramacao/login.png', str(contexto.exception))

    def test_arquivo_que_nao_e_imagem_levanta_mensagem_clara(self):
        class UnidentifiedImageError(Exception):
            """Mesmo nome que o Pillow usa; Tela.localizar identifica pelo nome."""

        self.pag.locateCenterOnScreen.side_effect = UnidentifiedImageError('x')
        with self.assertRaises(RuntimeError) as contexto:
            telas.Tela().localizar('img/corrompido.png')
        self.assertIn('img/corrompido.png', str(contexto.exception))

    def test_localizar_usa_a_confianca_configurada(self):
        self.pag.locateCenterOnScreen.return_value = Ponto(1, 2)
        telas.Tela(confianca=0.85).localizar('a.png')
        self.pag.locateCenterOnScreen.assert_called_once_with('a.png', confidence=0.85)

    def test_clicar_duplo_no_centro_da_imagem(self):
        self.pag.locateCenterOnScreen.return_value = Ponto(100, 200)
        self.assertTrue(telas.Tela().clicar_duplo('a.png'))
        self.pag.doubleClick.assert_called_once_with(100, 200)

    def test_clicar_duplo_sem_imagem_nao_clica(self):
        self.pag.locateCenterOnScreen.return_value = None
        self.assertFalse(telas.Tela().clicar_duplo('a.png'))
        self.pag.doubleClick.assert_not_called()

    def test_colar_copia_cola_e_limpa_a_area_de_transferencia(self):
        clipboard = MagicMock(name='pyperclip')
        with patch.dict(sys.modules, {'pyperclip': clipboard}), \
                patch.object(telas.time, 'sleep') as sleep:
            telas.Tela().colar('segredo')
        clipboard.copy.assert_has_calls([call('segredo'), call('')])
        self.pag.hotkey.assert_called_once_with('ctrl', 'v')
        sleep.assert_called_once_with(telas.ESPERA_COLAGEM)

    def test_colar_limpa_a_area_mesmo_se_a_colagem_falhar(self):
        clipboard = MagicMock(name='pyperclip')
        self.pag.hotkey.side_effect = RuntimeError('falhou')
        with patch.dict(sys.modules, {'pyperclip': clipboard}), \
                patch.object(telas.time, 'sleep'):
            with self.assertRaises(RuntimeError):
                telas.Tela().colar('segredo')
        self.assertEqual(clipboard.copy.call_args_list[-1], call(''))

    def test_tecla_repassa_o_nome(self):
        telas.Tela().tecla('tab')
        self.pag.press.assert_called_once_with('tab')

    def test_sem_pyperclip_levanta_mensagem_clara(self):
        with patch.dict(sys.modules, {'pyperclip': None}):
            with self.assertRaises(RuntimeError) as contexto:
                telas.Tela().colar('segredo')
        self.assertIn('pyperclip', str(contexto.exception))
        self.pag.hotkey.assert_not_called()

    def test_sem_pyautogui_levanta_mensagem_clara(self):
        with patch.dict(sys.modules, {'pyautogui': None}):
            with self.assertRaises(RuntimeError) as contexto:
                telas.Tela().localizar('a.png')
        self.assertIn('indisponível', str(contexto.exception))


class TestDpiAware(unittest.TestCase):
    """A causa clássica de 'a imagem existe mas nunca é achada'."""

    def setUp(self):
        telas._ESTADO_DPI = None
        self.addCleanup(setattr, telas, '_ESTADO_DPI', None)

    def test_fora_do_windows_nao_faz_nada(self):
        with patch.object(telas.os, 'name', 'posix'):
            resultado = telas.garantir_dpi_aware()
        self.assertIn('não se aplica', resultado)

    def test_no_windows_usa_shcore_per_monitor(self):
        ctypes_falso = MagicMock(name='ctypes')
        with patch.dict(sys.modules, {'ctypes': ctypes_falso}), \
                patch.object(telas.os, 'name', 'nt'):
            resultado = telas.garantir_dpi_aware()
        ctypes_falso.windll.shcore.SetProcessDpiAwareness.assert_called_once_with(2)
        self.assertIn('DPI aware', resultado)

    def test_sem_shcore_cai_para_set_process_dpi_aware(self):
        ctypes_falso = MagicMock(name='ctypes')
        ctypes_falso.windll.shcore.SetProcessDpiAwareness.side_effect = OSError('sem shcore')
        with patch.dict(sys.modules, {'ctypes': ctypes_falso}), \
                patch.object(telas.os, 'name', 'nt'):
            resultado = telas.garantir_dpi_aware()
        ctypes_falso.windll.user32.SetProcessDPIAware.assert_called_once_with()
        self.assertIn('SetProcessDPIAware', resultado)

    def test_falha_nunca_estoura_e_fica_registrada(self):
        with patch.object(telas, '_ESTADO_DPI', None), \
                patch.object(telas.os, 'name', 'nt'), \
                patch.dict(sys.modules, {'ctypes': None}):
            resultado = telas.garantir_dpi_aware()
        self.assertIn('NÃO consegui marcar como DPI aware', resultado)

    def test_resultado_fica_em_cache(self):
        ctypes_falso = MagicMock(name='ctypes')
        with patch.dict(sys.modules, {'ctypes': ctypes_falso}), \
                patch.object(telas.os, 'name', 'nt'):
            telas.garantir_dpi_aware()
            telas.garantir_dpi_aware()
        self.assertEqual(ctypes_falso.windll.shcore.SetProcessDpiAwareness.call_count, 1)

    def test_criar_tela_marca_o_processo_antes_da_primeira_busca(self):
        with patch.object(telas, 'garantir_dpi_aware', return_value='ok') as marcar:
            telas.Tela()
        marcar.assert_called_once_with()

    def test_escala_dpi_fora_do_windows_devolve_none(self):
        with patch.object(telas.os, 'name', 'posix'):
            self.assertIsNone(telas.escala_dpi())

    def test_escala_dpi_no_windows_vem_de_get_dpi_for_system(self):
        ctypes_falso = MagicMock(name='ctypes')
        ctypes_falso.windll.user32.GetDpiForSystem.return_value = 144  # 150%
        with patch.dict(sys.modules, {'ctypes': ctypes_falso}), \
                patch.object(telas.os, 'name', 'nt'):
            self.assertEqual(telas.escala_dpi(), 1.5)


class TestFaixasDeConfianca(unittest.TestCase):
    def test_desce_da_padrao_ate_a_minima(self):
        self.assertEqual(telas.Tela()._faixas_de_confianca(), [0.9, 0.75, 0.6])

    def test_minima_igual_a_padrao_testa_so_uma(self):
        self.assertEqual(telas.Tela(confianca=0.8, confianca_minima=0.8)._faixas_de_confianca(),
                         [0.8])

    def test_minima_acima_da_padrao_ainda_testa_a_padrao(self):
        self.assertEqual(telas.Tela(confianca=0.5, confianca_minima=0.9)._faixas_de_confianca(),
                         [0.5])


class TestLocalizarComQuedaDeConfianca(unittest.TestCase):
    def setUp(self):
        self.pag = MagicMock(name='pyautogui')
        patcher = patch.dict(sys.modules, {'pyautogui': self.pag})
        patcher.start()
        self.addCleanup(patcher.stop)

    def confiancas_usadas(self):
        return [c.kwargs['confidence'] for c in self.pag.locateCenterOnScreen.call_args_list]

    def test_para_na_primeira_confianca_que_casar(self):
        self.pag.locateCenterOnScreen.side_effect = [None, Ponto(5, 6)]
        tela = telas.Tela()
        self.assertEqual(tela.localizar('a.png'), Ponto(5, 6))
        self.assertEqual(tela.ultima_confianca, 0.75)
        self.assertEqual(self.confiancas_usadas(), [0.9, 0.75])

    def test_sem_casar_em_nenhuma_devolve_none_e_limpa_a_confianca(self):
        self.pag.locateCenterOnScreen.return_value = None
        tela = telas.Tela()
        tela.ultima_confianca = 0.9
        self.assertIsNone(tela.localizar('a.png'))
        self.assertIsNone(tela.ultima_confianca)
        self.assertEqual(self.confiancas_usadas(), [0.9, 0.75, 0.6])

    def test_imagem_nao_encontrada_nas_tres_tenta_devolve_none(self):
        self.pag.locateCenterOnScreen.side_effect = ImageNotFoundException('x')
        self.assertIsNone(telas.Tela().localizar('a.png'))
        self.assertEqual(self.confiancas_usadas(), [0.9, 0.75, 0.6])


class TestMedidasParaDiagnostico(unittest.TestCase):
    def setUp(self):
        self.pag = MagicMock(name='pyautogui')
        patcher = patch.dict(sys.modules, {'pyautogui': self.pag})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_tamanho_tela_vem_do_pyautogui(self):
        self.pag.size.return_value = (1920, 1080)
        self.assertEqual(telas.Tela().tamanho_tela(), (1920, 1080))

    def test_tamanho_tela_que_falha_devolve_none(self):
        self.pag.size.side_effect = OSError('sem tela')
        self.assertIsNone(telas.Tela().tamanho_tela())

    def test_tamanho_imagem_vem_do_pillow(self):
        pillow = MagicMock(name='PIL.Image')
        pillow.open.return_value.__enter__.return_value.size = (812, 344)
        with patch.dict(sys.modules, {'PIL.Image': pillow}):
            self.assertEqual(telas.Tela().tamanho_imagem('a.png'), (812, 344))
        pillow.open.assert_called_once_with('a.png')

    def test_tamanho_imagem_ilegivel_devolve_none(self):
        with patch.dict(sys.modules, {'PIL.Image': None}):
            self.assertIsNone(telas.Tela().tamanho_imagem('a.png'))

    def test_descricao_junta_resolucao_escala_e_dpi(self):
        self.pag.size.return_value = (1920, 1080)
        with patch.object(telas, 'escala_dpi', return_value=1.5), \
                patch.object(telas, 'garantir_dpi_aware', return_value='DPI aware (shcore)'):
            descricao = telas.Tela().descricao_tela()
        self.assertIn('resolução 1920x1080', descricao)
        self.assertIn('escala 150%', descricao)
        self.assertIn('DPI aware (shcore)', descricao)

    def test_descricao_diz_quando_nao_deu_para_medir(self):
        self.pag.size.side_effect = OSError('sem tela')
        with patch.object(telas, 'escala_dpi', return_value=None), \
                patch.object(telas, 'garantir_dpi_aware', return_value='sem DPI'):
            descricao = telas.Tela().descricao_tela()
        self.assertIn('resolução: não consegui medir', descricao)
        self.assertIn('escala: não consegui medir', descricao)


if __name__ == '__main__':
    unittest.main()
