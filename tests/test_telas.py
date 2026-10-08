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


if __name__ == '__main__':
    unittest.main()
