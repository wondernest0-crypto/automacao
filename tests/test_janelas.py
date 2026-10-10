"""core/janelas.py: busca por título e ativação da janela da VPS."""
import sys
import unittest
from unittest.mock import MagicMock, patch

from core import janelas


def janela_falsa(titulo, hwnd, minimizada=False, maximizada=False):
    janela = MagicMock(name='janela')
    janela.title = titulo
    janela._hWnd = hwnd
    janela.isMinimized = minimizada
    janela.isMaximized = maximizada
    return janela


class TestJanelasPorTitulo(unittest.TestCase):
    def test_acha_pelo_titulo_parcial_e_nao_repete(self):
        # Vários trechos de TITULOS_RDP casam com o mesmo título: vem uma vez só.
        janela = janela_falsa('Conexão de Área de Trabalho Remota - VPS', 42)
        gw = MagicMock(name='pygetwindow')
        gw.getWindowsWithTitle.side_effect = lambda trecho: (
            [janela] if 'Remota' in trecho else [])

        with patch.dict(sys.modules, {'pygetwindow': gw}):
            achadas = janelas.janelas_por_titulo()

        self.assertEqual(achadas, [janela])

    def test_titulos_cobrem_portugues_e_ingles(self):
        for esperado in ('Conexão de Área de Trabalho Remota',
                         'Remote Desktop Connection'):
            with self.subTest(titulo=esperado):
                self.assertIn(esperado, janelas.TITULOS_RDP)

    def test_sem_pygetwindow_devolve_lista_vazia(self):
        with patch.dict(sys.modules, {'pygetwindow': None}):
            self.assertEqual(janelas.janelas_por_titulo(), [])

    def test_falha_de_consulta_nao_quebra_a_busca(self):
        gw = MagicMock(name='pygetwindow')
        gw.getWindowsWithTitle.side_effect = OSError('sem acesso à sessão')
        with patch.dict(sys.modules, {'pygetwindow': gw}):
            self.assertEqual(janelas.janelas_por_titulo(), [])


class TestTrazerParaFrente(unittest.TestCase):
    def test_restaura_e_ativa_a_janela_minimizada(self):
        janela = janela_falsa('VPS', 7, minimizada=True)
        with patch.object(janelas, 'janela_em_primeiro_plano', return_value=True) as foco:
            self.assertTrue(janelas.trazer_para_frente(janela))
        janela.restore.assert_called_once_with()
        janela.activate.assert_called_once_with()
        foco.assert_called_once_with(7)

    def test_por_padrao_nao_redimensiona(self):
        # Redimensionar muda a escala do conteúdo remoto e quebra a comparação
        # com a captura: maximizar só acontece quando quem chama pede.
        janela = janela_falsa('VPS', 7)
        with patch.object(janelas, 'janela_em_primeiro_plano', return_value=True):
            janelas.trazer_para_frente(janela)
        janela.maximize.assert_not_called()
        janela.restore.assert_not_called()

    def test_maximizar_explicito_maximiza_uma_vez(self):
        janela = janela_falsa('VPS', 7)
        with patch.object(janelas, 'janela_em_primeiro_plano', return_value=True):
            janelas.trazer_para_frente(janela, maximizar=True)
        janela.maximize.assert_called_once_with()

    def test_janela_ja_maximizada_nao_maximiza_de_novo(self):
        janela = janela_falsa('VPS', 7, maximizada=True)
        with patch.object(janelas, 'janela_em_primeiro_plano', return_value=True):
            janelas.trazer_para_frente(janela, maximizar=True)
        janela.maximize.assert_not_called()

    def test_sem_janela_devolve_false(self):
        self.assertFalse(janelas.trazer_para_frente(None))

    def test_so_confirma_com_a_janela_em_primeiro_plano(self):
        # activate() é só um pedido: sem confirmação, retorna False.
        janela = janela_falsa('VPS', 7)
        with patch.object(janelas, 'janela_em_primeiro_plano', return_value=False):
            self.assertFalse(janelas.trazer_para_frente(janela))

    def test_falha_no_activate_ainda_confere_o_primeiro_plano(self):
        janela = janela_falsa('VPS', 7)
        janela.activate.side_effect = OSError('Windows recusou a troca de foco')
        with patch.object(janelas, 'janela_em_primeiro_plano', return_value=True):
            self.assertTrue(janelas.trazer_para_frente(janela))


if __name__ == '__main__':
    unittest.main()
