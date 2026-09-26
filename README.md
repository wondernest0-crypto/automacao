# 🤖 Sistema de Automação de Inventário TOTVS

Sistema para ajuste de estoque no TOTVS. Possui interface gráfica, automação
do navegador (Selenium + PyAutoGUI), atualização automática de planilhas e
log detalhado de execução.

---

## 🧩 Como funciona (lógica)

O sistema tem **duas partes** que se chamam uma à outra:

1. **`lancamento_inventario.py`** — Interface gráfica (Tkinter).
   É por aqui que tudo começa. Serve para lançar/consultar itens, cadastrar
   colaboradores e **iniciar a automação**.
2. **`automacao_totvs.py`** — Motor da automação.
   Abre o TOTVS no navegador (Edge), lê a planilha `RELATORIO_INVENTARIO.xlsx`,
   ajusta o estoque de cada item (entrada/saída) e, ao terminar, reabre a
   interface gráfica.

Fluxo resumido:

```
lancamento_inventario.py  --(clicar "Iniciar Automação")-->  automacao_totvs.py
        ↑                                                            |
        └----------------------(ao concluir)-------------------------┘
```

---

## 🚗 Importar Pedido HONDA & GM (aba dedicada)

A interface tem uma segunda aba, **"Importar Pedido HONDA & GM"**, com um botão
grande e vermelho **START**. Ao clicar, roda o fluxo de importação
(`automacao_totvs.py importar`):

1. **Minimiza TODAS as janelas** (`WIN+M` + pygetwindow como reforço para as
   janelas que ignoram o atalho). O `WIN+M` é usado de propósito no lugar do
   `WIN+D`: o `WIN+D` é um *liga/desliga* e, se a área de trabalho já estivesse
   visível, ele **restaurava** as janelas em vez de minimizar.
2. Procura a janela do TOTVS (**"DATASUL Interactive"**, **"DATASUL Interative"**
   ou só **"DATASUL"** — a busca tenta as variações, ignora as janelas de
   navegador e, se não achar nenhuma, grava no log a lista de janelas abertas
   para você conferir o título real).
3. Se **não** achar, abre o TOTVS do zero (login → senha → Entrar → popup) e
   aguarda até ~47s a janela aparecer.
4. Traz o **"DATASUL Interactive" para a frente** e **confirma que ele é a
   janela ativa** (a que recebe as teclas): sem essa confirmação o `CTRL+X`
   iria para outro programa. Como reforço são usados
   `SetForegroundWindow`/`BringWindowToTop` e, se ainda assim o foco não for
   confirmado, o *truque do TAB* (o Windows passa a considerar a janela ativa).
5. **CTRL+X** → abre a **janela do lançador de programas**. A automação espera
   essa janela aparecer (pelos títulos conhecidos **ou** por "qualquer janela
   nova" que surja depois do atalho), traz ela para a frente e só então digita.
6. Digita **ESPD0001** → **ENTER** (o campo é limpo com `CTRL+A` + `DELETE`
   antes de digitar, para não juntar com um código que já estivesse lá).
7. **5x** (TAB, ENTER).
8. Cola o diretório `\\192.168.0.9\s\Sawluz\swedi\OUTPUT\GM\`.
9. **4x** TAB → seta **↓** → seta **↑** → **ENTER** (importa) e reabre a
   interface gráfica.

Tudo é registrado em `log_automacao.txt` (o `.exe` roda sem console), com um
passo a passo numerado igual a este.

Ajustes ficam no topo de `automacao_totvs.py`:

- `ATALHO_ABRIR_PROGRAMA` — atalho do lançador (padrão `CTRL+X`).
- `ATALHO_ABRIR_PROGRAMA_ALT` / `TENTAR_ATALHO_ALTERNATIVO` — atalho alternativo
  (`CTRL+ALT+X`, o mesmo usado na automação de inventário) tentado
  automaticamente quando a janela do lançador não aparece com o `CTRL+X`.
- `LIMPAR_CAMPO_LANCADOR` — limpar o campo (`CTRL+A` + `DELETE`) antes de digitar.
- `DIRETORIO_IMPORTACAO_GM` — diretório de origem dos pedidos.
- `QTD_TAB_ENTER` — quantas vezes repetir (TAB, ENTER).
- `TEMPO_ESPERA_DATASUL` — tempo máximo (s) esperando a janela do DATASUL (padrão 47).
- `TEMPO_ESPERA_LANCADOR` — tempo (s) esperando a janela do lançador (padrão 6).
- `TEMPO_ESPERA_FOCO` — tempo (s) esperando o DATASUL virar a janela ativa (padrão 2.5).
- `TEMPO_ESPERA_PROGRAMA` — tempo (s) esperando o ESPD0001 carregar.
- `TITULOS_LANCADOR` — títulos do lançador de programas (opcional: a janela nova
  já é detectada mesmo que o título mude).
- `NAVEGADORES` — usados apenas para não confundir o navegador com o DATASUL.

---

## 🚀 Como executar

```bash
# 1. (recomendado) criar e ativar um ambiente virtual
python -m venv .venv && .venv\Scripts\activate

# 2. instalar dependências
pip install pandas openpyxl pyautogui pygetwindow pyperclip selenium

# 3. abrir a interface gráfica
python lancamento_inventario.py
```

Na interface, clique em **"Iniciar Automação"**. Acompanhe o progresso em
`log_automacao.txt`.

---

## 📁 Estrutura do projeto

```
automacao/
├── lancamento_inventario.py    ⭐ Interface gráfica (ponto de entrada)
├── automacao_totvs.py          ⭐ Motor de automação TOTVS
├── msedgedriver.exe            Driver do Edge (Selenium)
│
├── compilar.bat                Gera os .exe (PyInstaller)
├── Sistema_Inventario.spec     Config de build da interface
├── Automacao_TOTVS.spec        Config de build da automação
├── log_automacao.txt           Log de execução (gerado automaticamente)
├── README.md                   Este arquivo
│
├── data/
│   ├── RELATORIO_INVENTARIO.xlsx   Planilha principal (aba CONTAGEM)
│   ├── BASE_FISCAL_TOTVS.xlsx      Saldo fiscal do TOTVS por item
│   ├── itens_cadastrados.xlsx      Cadastro de itens
│   ├── colaboradores.xlsx          Cadastro de colaboradores
│   └── historico_ajustes.xlsx      Histórico de ajustes
│
└── img/                        Imagens usadas pelo PyAutoGUI
```

### Imagens em `img/` (usadas pela automação)
`+.png`, `saida.png`, `certo.png`, `confirmar.png`, `x.png`, `cancelar.png`,
`vencimento.png`, `ok.png`, `abrir_popup.png`

---

## ✅ Requisitos

- **Python 3.x**
- **Microsoft Edge** instalado
- **msedgedriver.exe** compatível com a versão do Edge.
  Baixe em: <https://developer.microsoft.com/pt-br/microsoft-edge/tools/webdriver/>
  e coloque o `.exe` na pasta do projeto.

Bibliotecas Python:

```bash
pip install pandas openpyxl pyautogui pygetwindow pyperclip selenium
```

---

## 📊 Planilha principal (`data/RELATORIO_INVENTARIO.xlsx`)

- **Aba `CONTAGEM`** — onde você informa os itens:
  `ITEM`, `QTD FÍSICA`, `COLABORADOR`. A automação preenche `QTD FISCAL`,
  `DIFERENÇA`, `STATUS` (OK / EXCESSO / FALTA), `ACURACIDADE %`, `AJUSTADO` e
  `DATA/HORA`.
- **Aba `HISTORICO_AJUSTES`** — registro de todos os ajustes (sincronizado).
- **Aba `DASHBOARD`** — indicadores e gráficos.

---

## 📝 Logs

Cada execução grava em `log_automacao.txt`: caminhos das imagens, item
processado, sucessos, erros e timestamp de cada operação. É o primeiro lugar
para olhar em caso de problema.

---

## 🛠️ Solução de problemas

| Problema | O que fazer |
|---|---|
| Imagem não encontrada | Confira se os `.png` estão em `img/` e se a resolução/tema do TOTVS não mudou. Veja o caminho registrado no log. |
| TOTVS não abre | Confira `msedgedriver.exe` (versão compatível com o Edge) e as credenciais/URL em `automacao_totvs.py`. |
| Planilha não existe | Verifique `data/RELATORIO_INVENTARIO.xlsx`. |
| Erro de permissão na planilha | Feche o arquivo no Excel antes de rodar a automação. |
| START da aba "Importar Pedido" não faz nada | Abra `log_automacao.txt`: se o timestamp **não** mudou, o `Automacao_TOTVS.exe` nem iniciou (confira se ele está na mesma pasta da interface). Se mudou, o log mostra em qual passo parou e lista as janelas abertas — confira ali o título real da janela do DATASUL. |
| O `CTRL+X` não abre a janela do lançador | O log mostra `A janela do lançador não apareceu com CTRL+X. Tentando CTRL+ALT+X...` — a automação já tenta o atalho alternativo sozinha. Se nenhum dos dois abrir, confira o atalho direto no TOTVS e ajuste `ATALHO_ABRIR_PROGRAMA` no topo de `automacao_totvs.py`. |
| O texto digitou no lugar errado (não no TOTVS) | Significa que o DATASUL não era a janela ativa. O log traz `Não confirmei o primeiro plano do DATASUL; aplicando o truque do TAB...`; se o foco não for confirmado, a automação **para** e avisa na tela em vez de digitar às cegas. Clique na janela do DATASUL e clique em START de novo. |

---

## 📦 Gerar os executáveis (.exe)

```bat
compilar.bat
```

Gera `dist\Sistema_Inventario.exe` (interface) e `dist\Automacao_TOTVS.exe`
(automação), já com `img\`, `data\` e `msedgedriver.exe`.

---

**Desenvolvedor:** Deived - Faturamento
**Versão:** 2.1
