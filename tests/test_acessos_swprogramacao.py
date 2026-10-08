"""Acesso da VPS: variáveis de ambiente e arquivo DPAPI (tudo simulado)."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from swprogramacao import acessos, fluxo

SENHA_WIN = 'senha-win-falsa'
SENHA_EDI = 'senha-edi-falsa'


def _acesso():
    return fluxo.Acesso('win-login', SENHA_WIN, 'edi-login', SENHA_EDI)


class TestCarregarAcesso(unittest.TestCase):
    def setUp(self):
        ambiente = patch.dict(os.environ, {}, clear=False)
        ambiente.start()
        self.addCleanup(ambiente.stop)
        for nome in acessos.VARIAVEIS:
            os.environ.pop(nome, None)
        self.arquivo = self._iniciar(patch.object(
            acessos.core_cred, 'carregar_dados', return_value=None))

    def _iniciar(self, patcher):
        mock = patcher.start()
        self.addCleanup(patcher.stop)
        return mock

    def _definir_ambiente(self, **valores):
        padrao = {
            acessos.VAR_WINDOWS_LOGIN: 'win-login',
            acessos.VAR_WINDOWS_SENHA: SENHA_WIN,
            acessos.VAR_EDI_LOGIN: 'edi-login',
            acessos.VAR_EDI_SENHA: SENHA_EDI,
        }
        padrao.update(valores)
        for nome, valor in padrao.items():
            if valor is None:
                os.environ.pop(nome, None)
            else:
                os.environ[nome] = valor

    def test_sem_ambiente_e_sem_arquivo_devolve_none(self):
        self.assertIsNone(acessos.carregar_acesso())

    def test_variaveis_de_ambiente_completas(self):
        self._definir_ambiente()
        acesso = acessos.carregar_acesso()
        self.assertEqual(acesso.windows_login, 'win-login')
        self.assertEqual(acesso.windows_senha, SENHA_WIN)
        self.assertEqual(acesso.edi_login, 'edi-login')
        self.assertEqual(acesso.edi_senha, SENHA_EDI)
        self.arquivo.assert_not_called()

    def test_variaveis_incompletas_caem_no_arquivo(self):
        self._definir_ambiente(**{acessos.VAR_EDI_SENHA: None})
        self.arquivo.return_value = json.dumps({
            'windows_login': 'win-login', 'windows_senha': SENHA_WIN,
            'edi_login': 'edi-login', 'edi_senha': SENHA_EDI,
        }).encode('utf-8')
        acesso = acessos.carregar_acesso()
        self.assertEqual(acesso.edi_login, 'edi-login')
        self.arquivo.assert_called_once_with(acessos.NOME_ARQUIVO)

    def test_arquivo_salvo_devolve_acesso(self):
        self.arquivo.return_value = json.dumps({
            'windows_login': 'win-login', 'windows_senha': SENHA_WIN,
            'edi_login': 'edi-login', 'edi_senha': SENHA_EDI,
        }, ensure_ascii=False).encode('utf-8')
        acesso = acessos.carregar_acesso()
        self.assertEqual((acesso.windows_login, acesso.windows_senha,
                          acesso.edi_login, acesso.edi_senha),
                         ('win-login', SENHA_WIN, 'edi-login', SENHA_EDI))

    def test_arquivo_corrompido_levanta_no_windows(self):
        self.arquivo.return_value = b'corrompido'
        with patch.object(acessos.os, 'name', 'nt'):
            with self.assertRaises(acessos.ErroAcesso) as contexto:
                acessos.carregar_acesso()
        self.assertIn('corrompido', str(contexto.exception))

    def test_arquivo_corrompido_fora_do_windows_cai_no_prompt(self):
        self.arquivo.return_value = b'corrompido'
        self.assertIsNone(acessos.carregar_acesso())

    def test_arquivo_incompleto_levanta(self):
        self.arquivo.return_value = json.dumps({
            'windows_login': 'win-login', 'windows_senha': '',
            'edi_login': 'edi-login', 'edi_senha': SENHA_EDI,
        }).encode('utf-8')
        with patch.object(acessos.os, 'name', 'nt'):
            with self.assertRaises(acessos.ErroAcesso) as contexto:
                acessos.carregar_acesso()
        self.assertIn('incompleto', str(contexto.exception))

    def test_sem_dpapi_fora_do_windows_devolve_none(self):
        self.arquivo.side_effect = acessos.ErroAcesso('O armazenamento protegido requer Windows.')
        self.assertIsNone(acessos.carregar_acesso())

    def test_erro_de_leitura_no_windows_levanta(self):
        self.arquivo.side_effect = acessos.ErroAcesso('Não foi possível carregar')
        with patch.object(acessos.os, 'name', 'nt'):
            with self.assertRaises(acessos.ErroAcesso):
                acessos.carregar_acesso()

    def test_senhas_nunca_aparecem_em_erro_nem_em_repr(self):
        self.arquivo.return_value = b'corrompido'
        with patch.object(acessos.os, 'name', 'nt'):
            with self.assertRaises(acessos.ErroAcesso) as contexto:
                acessos.carregar_acesso()
        acesso = _acesso()
        texto = str(contexto.exception) + repr(acesso)
        self.assertNotIn(SENHA_WIN, texto)
        self.assertNotIn(SENHA_EDI, texto)
        self.assertIn('win-login', repr(acesso), 'o login pode aparecer, a senha não')


class TestSalvarEEsquecer(unittest.TestCase):
    def test_salvar_grava_json_no_arquivo_dpapi(self):
        with patch.object(acessos.core_cred, 'salvar_dados') as salvar:
            acessos.salvar_acesso(_acesso())
        nome, dados = salvar.call_args.args
        self.assertEqual(nome, acessos.NOME_ARQUIVO)
        salvo = json.loads(dados.decode('utf-8'))
        self.assertEqual(salvo, {
            'windows_login': 'win-login', 'windows_senha': SENHA_WIN,
            'edi_login': 'edi-login', 'edi_senha': SENHA_EDI,
        })

    def test_salvar_incompleto_levanta_sem_gravar(self):
        with patch.object(acessos.core_cred, 'salvar_dados') as salvar:
            with self.assertRaises(acessos.ErroAcesso) as contexto:
                acessos.salvar_acesso(fluxo.Acesso('win-login', '', 'edi-login', SENHA_EDI))
        self.assertIn('Preencha todos os campos', str(contexto.exception))
        salvar.assert_not_called()

    def test_esquecer_apaga_o_arquivo(self):
        with patch.object(acessos.core_cred, 'apagar_dados') as apagar:
            acessos.esquecer_acesso()
        apagar.assert_called_once_with(acessos.NOME_ARQUIVO)


class TestIndicadores(unittest.TestCase):
    def setUp(self):
        ambiente = patch.dict(os.environ, {}, clear=False)
        ambiente.start()
        self.addCleanup(ambiente.stop)
        for nome in acessos.VARIAVEIS:
            os.environ.pop(nome, None)

    def test_sem_acesso_nada_marcado(self):
        with patch.object(acessos.core_cred, 'caminho_armazenamento',
                          side_effect=acessos.ErroAcesso('requer Windows')):
            status = acessos.indicadores()
        self.assertEqual(status, {'ambiente': False, 'arquivo': False})

    def test_ambiente_completo_e_arquivo_existente(self):
        for nome, valor in zip(acessos.VARIAVEIS, ('a', 'b', 'c', 'd')):
            os.environ[nome] = valor
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / acessos.NOME_ARQUIVO
            caminho.write_bytes(b'blob')
            with patch.object(acessos.core_cred, 'caminho_armazenamento', return_value=caminho):
                status = acessos.indicadores()
        self.assertEqual(status, {'ambiente': True, 'arquivo': True})

    def test_indicadores_nunca_mostram_valores(self):
        for nome, valor in zip(acessos.VARIAVEIS, ('a', 'b', 'c', 'd')):
            os.environ[nome] = valor
        with patch.object(acessos.core_cred, 'caminho_armazenamento',
                          side_effect=acessos.ErroAcesso('requer Windows')):
            texto = repr(acessos.indicadores())
        self.assertNotIn("'a'", texto)


if __name__ == '__main__':
    unittest.main()
