"""Localização do SWPROGRAMACAO.rdp e abertura pelo Windows (simulados em pasta temporária)."""
import os
import tempfile
import unittest
from unittest.mock import patch

from core import rdp as rdp_core
from swprogramacao import rdp


class TestCaminhoRdp(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = tmp.name

    def _criar(self, *partes):
        caminho = os.path.join(self.home, *partes, rdp.NOME_ARQUIVO)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, 'w', encoding='utf-8') as arquivo:
            arquivo.write('')
        return caminho

    def test_acha_na_pasta_desktop(self):
        esperado = self._criar('Desktop')
        self.assertEqual(rdp.caminho_rdp(self.home), esperado)

    def test_acha_na_area_de_trabalho_em_portugues(self):
        esperado = self._criar('Área de Trabalho')
        self.assertEqual(rdp.caminho_rdp(self.home), esperado)

    def test_acha_dentro_do_onedrive(self):
        esperado = self._criar('OneDrive', 'Área de Trabalho')
        self.assertEqual(rdp.caminho_rdp(self.home), esperado)

    def test_sem_arquivo_lista_os_lugares_onde_procurou(self):
        with self.assertRaises(rdp.RdpNaoEncontrado) as contexto:
            rdp.caminho_rdp(self.home)
        for candidato in rdp.caminhos_candidatos(self.home):
            self.assertIn(candidato, str(contexto.exception))

    def test_abrir_rdp_chama_startfile(self):
        with patch.object(rdp_core.os, 'startfile', create=True) as startfile:
            rdp.abrir_rdp('C:/Users/x/Desktop/SWPROGRAMACAO.rdp')
        startfile.assert_called_once_with('C:/Users/x/Desktop/SWPROGRAMACAO.rdp')


class TestRdpCompartilhado(unittest.TestCase):
    """core/rdp.py: a mesma busca na área de trabalho, paramétrica pelo nome."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = tmp.name

    def _criar(self, nome, *partes):
        caminho = os.path.join(self.home, *partes, nome)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, 'w', encoding='utf-8') as arquivo:
            arquivo.write('')
        return caminho

    def test_acha_com_nome_explícito(self):
        esperado = self._criar('OUTRA.rdp', 'OneDrive', 'Desktop')
        self.assertEqual(rdp_core.caminho_rdp('OUTRA.rdp', self.home), esperado)

    def test_nao_encontrado_levanta_com_o_nome_do_arquivo(self):
        with self.assertRaises(rdp_core.RdpNaoEncontrado) as contexto:
            rdp_core.caminho_rdp('NADA.rdp', self.home)
        self.assertIn('NADA.rdp', str(contexto.exception))
        for candidato in rdp_core.caminhos_candidatos('NADA.rdp', self.home):
            self.assertIn(candidato, str(contexto.exception))

    def test_abrir_chama_startfile(self):
        with patch.object(rdp_core.os, 'startfile', create=True) as startfile:
            rdp_core.abrir_rdp('C:/Users/x/Desktop/SWPROGRAMACAO.rdp')
        startfile.assert_called_once_with('C:/Users/x/Desktop/SWPROGRAMACAO.rdp')


if __name__ == '__main__':
    unittest.main()
