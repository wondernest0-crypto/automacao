"""Persistência isolada da rede e da conta Windows real."""
import ctypes
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import credenciais_totvs as cred


class TestArmazenamento(unittest.TestCase):
    def setUp(self):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.arquivo = Path(pasta.name) / 'perfil' / 'acesso.dpapi'
        self.patch = patch.object(cred, '_arquivo', return_value=self.arquivo)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_primeiro_uso(self):
        self.assertEqual(cred.carregar_credenciais(), ('deivid', ''))

    def test_salva_somente_blob_protegido_e_reabre(self):
        senha = ' senha fictícia com espaços '
        dados = json.dumps({'login': 'operador', 'senha': senha}, ensure_ascii=False).encode('utf-8')
        with patch.object(cred, '_dpapi', return_value=b'blob-protegido') as api:
            cred.salvar_credenciais(' operador ', senha)
            api.assert_called_once_with(dados, True)
        self.assertEqual(self.arquivo.read_bytes(), b'blob-protegido')
        self.assertEqual(list(self.arquivo.parent.iterdir()), [self.arquivo])
        with patch.object(cred, '_dpapi', return_value=dados) as api:
            self.assertEqual(cred.carregar_credenciais(), ('operador', senha))
            api.assert_called_once_with(b'blob-protegido', False)

    def test_falha_protecao_nao_grava_texto_puro(self):
        with patch.object(cred, '_dpapi', side_effect=OSError('senha secreta')):
            with self.assertRaises(cred.ErroCredenciais) as erro:
                cred.salvar_credenciais('usuario', 'senha secreta')
        self.assertNotIn('senha secreta', str(erro.exception))
        self.assertFalse(self.arquivo.exists())

    def test_falha_substituicao_preserva_acesso_anterior_e_limpa_temporario(self):
        self.arquivo.parent.mkdir()
        self.arquivo.write_bytes(b'anterior')
        with patch.object(cred, '_dpapi', return_value=b'novo'), patch.object(cred.os, 'replace', side_effect=OSError()):
            with self.assertRaises(cred.ErroCredenciais):
                cred.salvar_credenciais('novo', 'nova senha')
        self.assertEqual(self.arquivo.read_bytes(), b'anterior')
        self.assertEqual(list(self.arquivo.parent.iterdir()), [self.arquivo])

    def test_conteudo_invalido_nao_e_carregado(self):
        self.arquivo.parent.mkdir()
        self.arquivo.write_bytes(b'corrompido')
        for dados in (b'invalido', b'[]', b'{}', b'{"login": 1, "senha": "s"}'):
            with self.subTest(dados=dados), patch.object(cred, '_dpapi', return_value=dados):
                with self.assertRaises(cred.ErroCredenciais):
                    cred.carregar_credenciais()

    def test_outro_usuario_ou_arquivo_corrompido(self):
        self.arquivo.parent.mkdir()
        self.arquivo.write_bytes(b'blob')
        with patch.object(cred, '_dpapi', side_effect=cred.ErroCredenciais('Falha DPAPI')):
            with self.assertRaises(cred.ErroCredenciais):
                cred.carregar_credenciais()

    def test_esquecer_inclusive_quando_nao_existe(self):
        self.arquivo.parent.mkdir()
        self.arquivo.write_bytes(b'blob')
        cred.esquecer_credenciais()
        cred.esquecer_credenciais()
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
        with patch.object(cred.os, 'name', 'nt'), patch.object(cred.ctypes, 'WinDLL', create=True, side_effect=[crypt, kernel] * 2):
            self.assertEqual(cred._dpapi(b'teste', True), b'retorno')
            self.assertEqual(cred._dpapi(b'teste', False), b'retorno')
        self.assertEqual(kernel.LocalFree.call_count, 2)

    @unittest.skipUnless(os.name == 'nt', 'DPAPI real exige Windows')
    def test_roundtrip_windows(self):
        dados = 'senha fictícia'.encode('utf-8')
        protegido = cred._dpapi(dados, True)
        self.assertNotEqual(protegido, dados)
        self.assertEqual(cred._dpapi(protegido, False), dados)


if __name__ == '__main__':
    unittest.main()
