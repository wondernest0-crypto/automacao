"""core/credenciais.py: blob DPAPI fora do projeto (persistência isolada).

Espelha os testes de totvs/credenciais.py: o armazenamento protegido fica em
%LOCALAPPDATA%\\AutomacaoTOTVS\\, vinculado à conta Windows atual.
"""
import ctypes
import json
import os
from pathlib import Path, PureWindowsPath
import tempfile
import unittest
from unittest.mock import Mock, patch

from core import credenciais as cred


class TestCaminhoArmazenamento(unittest.TestCase):
    def test_dentro_do_perfil_windows(self):
        # os.name='nt' faz o pathlib escolher WindowsPath; no teste Linux,
        # PureWindowsPath produz o mesmo caminho sem instanciar WindowsPath.
        with patch.object(cred.os, 'name', 'nt'), \
                patch.dict(os.environ, {'LOCALAPPDATA': 'C:/Users/x/AppData/Local'}), \
                patch.object(cred, 'Path', PureWindowsPath):
            caminho = cred.caminho_armazenamento('acesso_sw.dpapi')
        esperado = PureWindowsPath('C:/Users/x/AppData/Local') / 'AutomacaoTOTVS' / 'acesso_sw.dpapi'
        self.assertEqual(caminho, esperado)

    def test_fora_do_windows_levanta(self):
        with self.assertRaises(cred.ErroCredenciais):
            cred.caminho_armazenamento('acesso_sw.dpapi')


class TestArmazenamento(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.arquivo = Path(pasta.name) / 'perfil' / 'acesso_sw.dpapi'
        self.caminho = self._iniciar(patch.object(
            cred, 'caminho_armazenamento', return_value=self.arquivo))

    def _iniciar(self, patcher):
        mock = patcher.start()
        self.addCleanup(patcher.stop)
        return mock

    def test_sem_arquivo_devolve_none(self):
        self.assertIsNone(cred.carregar_dados('acesso_sw.dpapi'))

    def test_salva_somente_blob_protegido_e_reabre(self):
        senha = ' senha fictícia com espaços '
        dados = json.dumps({'windows_senha': senha}, ensure_ascii=False).encode('utf-8')
        with patch.object(cred, '_dpapi', return_value=b'blob-protegido') as api:
            cred.salvar_dados('acesso_sw.dpapi', dados)
            api.assert_called_once_with(dados, True)
        self.assertEqual(self.arquivo.read_bytes(), b'blob-protegido')
        self.assertEqual(list(self.arquivo.parent.iterdir()), [self.arquivo])
        with patch.object(cred, '_dpapi', return_value=dados) as api:
            self.assertEqual(cred.carregar_dados('acesso_sw.dpapi'), dados)
            api.assert_called_once_with(b'blob-protegido', False)

    def test_falha_protecao_nao_grava_texto_puro(self):
        with patch.object(cred, '_dpapi', side_effect=OSError('senha secreta')):
            with self.assertRaises(cred.ErroCredenciais) as erro:
                cred.salvar_dados('acesso_sw.dpapi', b'{"senha": "senha secreta"}')
        self.assertNotIn('senha secreta', str(erro.exception))
        self.assertFalse(self.arquivo.exists())

    def test_falha_substituicao_preserva_anterior_e_limpa_temporario(self):
        self.arquivo.parent.mkdir()
        self.arquivo.write_bytes(b'anterior')
        with patch.object(cred, '_dpapi', return_value=b'novo'), \
                patch.object(cred.os, 'replace', side_effect=OSError()):
            with self.assertRaises(cred.ErroCredenciais):
                cred.salvar_dados('acesso_sw.dpapi', b'novos dados')
        self.assertEqual(self.arquivo.read_bytes(), b'anterior')
        self.assertEqual(list(self.arquivo.parent.iterdir()), [self.arquivo])

    def test_arquivo_corrompido_levanta_sem_conteudo(self):
        self.arquivo.parent.mkdir()
        self.arquivo.write_bytes(b'blob')
        with patch.object(cred, '_dpapi', side_effect=cred.ErroCredenciais('Falha DPAPI')):
            with self.assertRaises(cred.ErroCredenciais):
                cred.carregar_dados('acesso_sw.dpapi')

    def test_apagar_inclusive_quando_nao_existe(self):
        self.arquivo.parent.mkdir()
        self.arquivo.write_bytes(b'blob')
        cred.apagar_dados('acesso_sw.dpapi')
        cred.apagar_dados('acesso_sw.dpapi')
        self.assertFalse(self.arquivo.exists())


class TestDPAPI(unittest.TestCase):
    def test_api_vinculada_ao_usuario_e_libera_memoria(self):
        crypt, kernel = Mock(), Mock()
        buffer = ctypes.create_string_buffer(b'retorno')

        def executar(entrada, descricao, entropia, reservado, prompt, flags, saida):
            self.assertEqual(ctypes.string_at(entrada._obj.pbData, entrada._obj.cbData), b'teste')
            self.assertEqual(flags, 1)  # Não inclui CRYPTPROTECT_LOCAL_MACHINE.
            saida._obj.cbData = 7
            saida._obj.pbData = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))
            return True

        crypt.CryptProtectData.side_effect = executar
        crypt.CryptUnprotectData.side_effect = executar
        with patch.object(cred.os, 'name', 'nt'), \
                patch.object(cred.ctypes, 'WinDLL', create=True, side_effect=[crypt, kernel] * 2):
            self.assertEqual(cred._dpapi(b'teste', True), b'retorno')
            self.assertEqual(cred._dpapi(b'teste', False), b'retorno')
        self.assertEqual(kernel.LocalFree.call_count, 2)

    def test_fora_do_windows_levanta_erro_claro(self):
        with self.assertRaises(cred.ErroCredenciais) as erro:
            cred._dpapi(b'teste', True)
        self.assertIn('Windows', str(erro.exception))

    @unittest.skipUnless(os.name == 'nt', 'DPAPI real exige Windows')
    def test_roundtrip_windows(self):
        dados = 'senha fictícia'.encode('utf-8')
        protegido = cred._dpapi(dados, True)
        self.assertNotEqual(protegido, dados)
        self.assertEqual(cred._dpapi(protegido, False), dados)


if __name__ == '__main__':
    unittest.main()
