"""Ações de tela por imagem (PyAutoGUI), compartilhadas pelas partes do projeto.

A lógica de cada parte recebe um objeto com estes métodos: agora, esperar,
localizar, clicar_duplo, colar e tecla. Em produção é a classe Tela; nos testes,
um objeto falso. Os imports de pyautogui e pyperclip ficam dentro dos métodos,
então importar este módulo não exige Windows nem tela.

Dois detalhes fazem diferença entre "a imagem existe" e "a imagem é achada":

1. DPI: sem o processo marcado como 'DPI aware', no Windows com escala de tela
   diferente de 100% (125%, 150%) a captura de tela que o PyAutoGUI recebe vem
   REDUZIDA, enquanto a captura feita pelo usuário (Ferramenta de Captura) está
   nos pixels reais. Os tamanhos não batem e a comparação por pixels nunca
   fecha. `garantir_dpi_aware()` cuida disso uma vez, antes da primeira busca.

2. Confiança: uma captura feita em outro momento (tema, anti-alias, fonte) pode
   casar só com confiança menor. A busca desce da confiança padrão até o mínimo
   e guarda em `ultima_confianca` o valor em que casou, o que vai para o log e
   para o `--diagnostico`: se casar em 0.6, a captura precisa ser refeita.
"""
import importlib
import os
import time

# Tempo (s) que a colagem tem para chegar à VPS antes de limpar a área de
# transferência. Se um campo chegar vazio na VPS, aumente este valor.
ESPERA_COLAGEM = 1.0

CONFIANCA_PADRAO = 0.9
CONFIANCA_MINIMA = 0.6
PASSO_CONFIANCA = 0.15

# None = ainda não tentou marcar o processo como DPI aware.
_ESTADO_DPI = None


def _importar(nome):
    """Importa uma dependência de tela. Fora do Windows o import pode falhar de vários jeitos."""
    try:
        return importlib.import_module(nome)
    except Exception as erro:
        raise RuntimeError(f'Automação de tela indisponível: {nome} não carrega ({erro}).') from erro


def garantir_dpi_aware():
    """Marca o processo como 'DPI aware' e devolve uma descrição do resultado.

    Idempotente (o resultado fica em cache) e nunca levanta erro: se não der
    para marcar, a busca continua e a descrição diz o que aconteceu. Fora do
    Windows não faz nada.
    """
    global _ESTADO_DPI
    if _ESTADO_DPI is not None:
        return _ESTADO_DPI
    if os.name != 'nt':
        _ESTADO_DPI = 'DPI awareness não se aplica (fora do Windows)'
        return _ESTADO_DPI
    try:
        import ctypes
        try:
            # PROCESS_PER_MONITOR_DPI_AWARE = 2 (Windows 8.1+).
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            _ESTADO_DPI = 'DPI aware (per-monitor, shcore)'
        except Exception:
            # Fallback para o Windows 7 / sem shcore.
            ctypes.windll.user32.SetProcessDPIAware()
            _ESTADO_DPI = 'DPI aware (SetProcessDPIAware)'
    except Exception as erro:
        _ESTADO_DPI = f'NÃO consegui marcar como DPI aware: {erro}'
    return _ESTADO_DPI


def escala_dpi():
    """Escala de exibição do Windows (1.0 = 100%, 1.5 = 150%); None se não der."""
    if os.name != 'nt':
        return None
    try:
        import ctypes
        try:
            return round(ctypes.windll.user32.GetDpiForSystem() / 96.0, 2)
        except (AttributeError, OSError):
            # Windows antigo: pergunta ao DC da tela (LOGPIXELSY = 90).
            hdc = ctypes.windll.user32.GetDC(None)
            try:
                return round(ctypes.windll.gdi32.GetDeviceCaps(hdc, 90) / 96.0, 2)
            finally:
                ctypes.windll.user32.ReleaseDC(None, hdc)
    except Exception:
        return None


class Tela:
    def __init__(self, confianca=CONFIANCA_PADRAO, confianca_minima=CONFIANCA_MINIMA):
        garantir_dpi_aware()
        self.confianca = confianca
        self.confianca_minima = confianca_minima
        self.ultima_confianca = None

    @staticmethod
    def _pyautogui():
        return _importar('pyautogui')

    def agora(self):
        return time.monotonic()

    def esperar(self, segundos):
        time.sleep(segundos)

    def _faixas_de_confianca(self):
        """Confianças testadas na busca, da mais exigente para a mais frouxa."""
        valores = []
        confianca = self.confianca
        while confianca >= self.confianca_minima - 1e-9:
            valores.append(round(confianca, 2))
            confianca -= PASSO_CONFIANCA
        return valores or [round(self.confianca, 2)]

    def localizar(self, caminho_imagem):
        """Centro (x, y) da imagem na tela, ou None se ela não estiver visível.

        Testa da confiança padrão até a mínima; `ultima_confianca` fica com o
        valor em que a imagem casou (None quando não casou em nenhum).
        """
        pag = self._pyautogui()
        for confianca in self._faixas_de_confianca():
            try:
                pos = pag.locateCenterOnScreen(caminho_imagem, confidence=confianca)
            except Exception as erro:
                # Algumas versões do PyAutoGUI levantam ImageNotFoundException em vez de devolver None.
                if type(erro).__name__ == 'ImageNotFoundException':
                    continue
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
            if pos is not None:
                self.ultima_confianca = confianca
                return pos
        self.ultima_confianca = None
        return None

    def tamanho_tela(self):
        """(largura, altura) em pixels da tela; None se não der para medir."""
        try:
            largura, altura = self._pyautogui().size()
            return int(largura), int(altura)
        except Exception:
            return None

    def tamanho_imagem(self, caminho_imagem):
        """(largura, altura) em pixels da captura; None se o arquivo não abrir."""
        try:
            imagem = _importar('PIL.Image')
            with imagem.open(caminho_imagem) as arquivo:
                return arquivo.size
        except Exception:
            return None

    def descricao_tela(self):
        """Uma linha com resolução, escala e estado do DPI awareness."""
        tamanho = self.tamanho_tela()
        escala = escala_dpi()
        partes = [f'resolução {tamanho[0]}x{tamanho[1]}' if tamanho
                  else 'resolução: não consegui medir']
        partes.append(f'escala {int(escala * 100)}%' if escala
                      else 'escala: não consegui medir')
        partes.append(garantir_dpi_aware())
        return '; '.join(partes)

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
