"""Ações de tela por imagem (PyAutoGUI), compartilhadas pelas partes do projeto.

A lógica de cada parte recebe um objeto com estes métodos: agora, esperar,
localizar, clicar_duplo, colar e tecla. Em produção é a classe Tela; nos testes,
um objeto falso. Os imports de pyautogui e pyperclip ficam dentro dos métodos,
então importar este módulo não exige Windows nem tela.
"""
import importlib
import time

# Tempo (s) que a colagem tem para chegar à VPS antes de limpar a área de
# transferência. Se um campo chegar vazio na VPS, aumente este valor.
ESPERA_COLAGEM = 1.0


def _importar(nome):
    """Importa uma dependência de tela. Fora do Windows o import pode falhar de vários jeitos."""
    try:
        return importlib.import_module(nome)
    except Exception as erro:
        raise RuntimeError(f'Automação de tela indisponível: {nome} não carrega ({erro}).') from erro


class Tela:
    def __init__(self, confianca=0.9):
        self.confianca = confianca

    @staticmethod
    def _pyautogui():
        return _importar('pyautogui')

    def agora(self):
        return time.monotonic()

    def esperar(self, segundos):
        time.sleep(segundos)

    def localizar(self, caminho_imagem):
        """Centro (x, y) da imagem na tela, ou None se ela não estiver visível."""
        pag = self._pyautogui()
        try:
            return pag.locateCenterOnScreen(caminho_imagem, confidence=self.confianca)
        except Exception as erro:
            # Algumas versões do PyAutoGUI levantam ImageNotFoundException em vez de devolver None.
            if type(erro).__name__ == 'ImageNotFoundException':
                return None
            # Arquivo de imagem ausente ou ilegível: avisa o caminho, em vez de
            # estourar com erro de biblioteca (que parece "não achou na tela").
            if isinstance(erro, FileNotFoundError):
                raise RuntimeError(
                    f'Arquivo de imagem não existe: {caminho_imagem}. '
                    'Coloque a captura no caminho indicado.') from erro
            if type(erro).__name__ == 'UnidentifiedImageError':
                raise RuntimeError(
                    f'O arquivo não é uma imagem válida: {caminho_imagem}. '
                    'Salve novamente a captura como .png.') from erro
            raise

    def clicar_duplo(self, caminho_imagem):
        """Duplo clique no centro da imagem. Devolve False se ela não estiver visível."""
        pos = self.localizar(caminho_imagem)
        if pos is None:
            return False
        self._pyautogui().doubleClick(pos.x, pos.y)
        return True

    def colar(self, texto):
        """Cola o texto pela área de transferência e a limpa logo depois.

        Colar evita problemas de layout de teclado com símbolos como '@'.
        """
        pyperclip = _importar('pyperclip')
        pag = self._pyautogui()
        pyperclip.copy(texto)
        try:
            pag.hotkey('ctrl', 'v')
            time.sleep(ESPERA_COLAGEM)
        finally:
            pyperclip.copy('')

    def tecla(self, nome):
        self._pyautogui().press(nome)
