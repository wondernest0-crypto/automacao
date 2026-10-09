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
2. **`automacao_totvs.py`** — Motor da automação (ponto de entrada; a lógica fica em `totvs/automacao.py`).
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

## 🧱 Partes do projeto

O código está separado em partes, para que cada uma evolua sem mexer nas outras:

| Pasta | Parte | O que faz |
|---|---|---|
| `totvs/` | **TOTVS** | Ajuste de estoque, importação ESPD0001 (aba Importar Pedido HONDA & GM, por enquanto) e acesso ao TOTVS pelo Edge. |
| `swprogramacao/` | **SWProgramação** | Acesso à VPS. **Passo 1 pronto para teste** (abre a VPS e para na ULIANA carregada). Configurações e pedidos HONDA e GM: *em construção.* |
| `core/` | Compartilhado | Caminhos do projeto (modo .py e .exe), ações de tela por imagem, validação de janelas do Windows e busca/abertura do `.rdp` da área de trabalho. |

Fluxo previsto: primeiro a parte **SWProgramação** (VPS: pedido HONDA e depois GM); em seguida, a parte **TOTVS**. A interface (`lancamento_inventario.py`) fica na raiz e será o ponto que liga as partes.

No fluxo de importação, o START já respeita essa ordem: **abre o `SWPROGRAMACAO.rdp` da área de trabalho antes de executar o DATASUL** (sessão RDP já aberta é reutilizada; sem o `.rdp` e sem sessão aberta, o DATASUL não é executado).

`lancamento_inventario.py` e `automacao_totvs.py` continuam na raiz porque o `compilar.bat`, os `.spec` e o workflow usam esses nomes. O teste `tests/test_limites_partes.py` impede que as partes importem umas às outras.

---

## 🖥️ SWProgramação (VPS): passo 1

Este passo abre a VPS, faz os dois logins e **procura a ULIANA na lista de parceiros**. Quando a ULIANA é encontrada, o passo termina (não clica nela). Ainda não faz configurações nem importação de pedidos.

**O que ele faz, em ordem:**

1. Confere se as 4 capturas existem em `img/swprogramacao/`. Se faltar alguma, **para antes de abrir a VPS** e diz quais faltam (imagem ausente é arquivo ausente, não "não achei na tela").
2. Abre o `SWPROGRAMACAO.rdp` da área de trabalho (igual a dar dois cliques). A busca cobre a pasta real da área de trabalho do Windows (API de pastas conhecidas), `Desktop`, `Área de Trabalho` e as versões dentro do OneDrive.
3. A cada ciclo, **procura TODAS as imagens na tela antes de decidir o próximo passo**:
   - `login.png` (login do Windows, com o campo de usuário já em foco): usuário, TAB, senha, ENTER, e espera 3 s;
   - `login_edi.png` (login do EDI, "Usuário:"): usuário, TAB, senha, ENTER, e espera **4 s** (`ESPERA_APOS_ENTER_EDI`);
   - `informe_parceiro.png`: é o sinal de que os logins terminaram.
   Cada login é digitado **uma vez**. Se a senha estiver errada, o passo para com erro e não tenta de novo.
4. Com `informe_parceiro.png` na tela, **procura `uliana.png`**. Achou: registra "ULIANA encontrada" e **termina** (não clica). Se não achar em 15 s, para com erro.

**Antes de rodar:**

- Coloque as 4 capturas em `img/swprogramacao/`: `login.png`, `login_edi.png`, `informe_parceiro.png` e `uliana.png`. Use capturas reais da tela da VPS, na mesma resolução e zoom do computador que vai rodar. Não use imagens ilustrativas. As instruções de captura de cada imagem estão em `img/swprogramacao/README.md`.
- As capturas **não vão para o Git** (ficam só no PC de quem roda, pelo `.gitignore`).
- Mantenha a área de transferência ativa no RDP (é o padrão do Windows). Os dados são colados, não digitados, para evitar problemas com `@` e outros símbolos.
- Deixe a janela da VPS visível e não minimizada: a automação enxerga só o que está na tela.
- Ainda não existe `.exe` para esta parte. Rode pelo Python, como abaixo.

**Como rodar** (na pasta do projeto):

```
python -m swprogramacao --salvar-acesso     # guarda o acesso uma vez (DPAPI, no Windows)
python -m swprogramacao --diagnostico       # confere o .rdp, as 4 imagens e o acesso salvo
python -m swprogramacao                     # roda o passo 1 até achar a ULIANA
python -m swprogramacao --esquecer-acesso   # apaga o acesso salvo
```

Com a VPS aberta, o `--diagnostico` mostra onde cada imagem foi encontrada. Se alguma aparecer como "não visível", a captura não corresponde à tela atual.

**Segurança:** o acesso (login do Windows e do EDI) pode ser guardado **uma vez** com `--salvar-acesso`, protegido pela DPAPI do Windows em `%LOCALAPPDATA%\AutomacaoTOTVS\acesso_sw.dpapi`, fora da pasta do projeto. Também pode ser passado por variáveis de ambiente (`SW_WINDOWS_LOGIN`, `SW_WINDOWS_SENHA`, `SW_EDI_LOGIN`, `SW_EDI_SENHA`), com prioridade sobre o arquivo salvo. Se não houver acesso salvo, ele é pedido no terminal. Não há senha em texto puro no código, nos arquivos do projeto ou no log, e nenhuma senha aparece no log. O registro fica em `log_swprogramacao.txt`, que é ignorado pelo Git.

**Se parar:** o terminal e o log dizem em qual etapa parou (imagem faltando, login do Windows, login do EDI, ULIANA não encontrada ou tempo esgotado).

---

## 🚗 Importar Pedido HONDA & GM (aba dedicada)

A interface tem uma segunda aba, **"Importar Pedido HONDA & GM"**, com um botão
grande e vermelho **START**. Ao clicar, roda o fluxo de importação
(`automacao_totvs.py importar`):

1. **Abre a VPS antes de executar o DATASUL:** procura
   `SWPROGRAMACAO.rdp` na área de trabalho (Desktop, OneDrive/Desktop,
   Área de Trabalho e OneDrive/Área de Trabalho) e o abre igual a dar dois
   cliques. Se já houver uma Conexão de Área de Trabalho Remota aberta, a
   sessão é reutilizada (nada é reaberto). Depois, aguarda
   `TEMPO_ESPERA_RDP` para a VPS carregar. **Sem o `.rdp` e sem sessão
   aberta, o fluxo para com aviso e o DATASUL não é executado.**
2. Procura primeiro uma janela DATASUL disponível, **antes de minimizar ou
   abrir o navegador**. Uma sessão já aberta é reutilizada.
3. Consulta as janelas nativas do Windows (sem abrir visualmente o Gerenciador
   de Tarefas). Aceita **"DATASUL Interactive"** ou **"DATASUL Interative"**,
   inclusive minimizadas e com sufixos no título. Exige janela visível/responsiva
   e processo vivo; descarta navegadores pelo título **e pelo executável**.
   Se não encontrar janela, registra os processos como diagnóstico: um
   `prowin32.exe` isolado **não bloqueia** a abertura e não é encerrado.
   Confere as janelas novamente antes de iniciar outra sessão. Sem janela,
   minimiza as demais com `WIN+M` (não usa `WIN+D`, que alterna a área de trabalho).
4. Se não encontrar uma janela disponível, abre o Edge em
   `http://192.168.2.6:8080/totvs-menu`, preenche o acesso informado na interface
   e clica em **Entrar**. Procura `img/abrir.png` (ou `img/abrir_popup.png`,
   nome existente nesta versão) por até 30s e clica no botão encontrado.
   Se o DATASUL abrir sem popup, segue normalmente. Sem imagem correspondente,
   interrompe com aviso em vez de enviar atalhos às cegas.
   Depois do clique, aguarda até 47s pela janela/processo DATASUL.
5. Restaura e ativa a janela, usando também `SetForegroundWindow`,
   `BringWindowToTop` e clique na barra de título. **Exige confirmação real do
   foco antes do CTRL+X**; se a consulta falhar ou outra janela estiver ativa,
   interrompe. Não envia TAB para tentar ativar uma janela desconhecida.
6. **CTRL+X** → abre a **janela do lançador de programas**. A automação espera
   essa janela aparecer (pelos títulos conhecidos **ou** por "qualquer janela
   nova" que surja depois do atalho), traz ela para a frente e só então digita.
7. Digita **ESPD0001** → **ENTER** (o campo é limpo com `CTRL+A` + `DELETE`
   antes de digitar, para não juntar com um código que já estivesse lá).
8. Após o carregamento do programa, envia **1x TAB** → **ENTER** para confirmar
   a tela inicial do ESPD0001.
9. Envia **5x TAB consecutivos**, sem ENTER entre eles, para chegar ao campo de
   endereço. Depois pressiona **ENTER**, antes de colar.
10. Cola o diretório `\\192.168.0.9\s\Sawluz\swedi\OUTPUT\GM\` e pressiona **ENTER**.
11. Envia **4x** TAB → seta **↓** → seta **↑**.
12. Procura **`img/abrir_popup.png`** e clica; em seguida procura
    **`img/executar.png`** e clica. Aguarda até 30s por cada botão, com confiança
    fixa de 90%. Arquivo ausente, erro ou botão não encontrado interrompe o
    fluxo com aviso; não tenta confirmar por ENTER.
13. Encerra após o clique em Executar e reabre a interface, **sem ENTER final**
    nem outras confirmações. Esta etapa não verifica o resultado da importação
    dentro do TOTVS.

Tudo é registrado em `log_automacao.txt` (o `.exe` roda sem console), com um
passo a passo numerado igual a este.

Ajustes ficam no topo de `totvs/automacao.py`:

- `ARQUIVO_RDP_VPS` — nome do arquivo da VPS na área de trabalho (padrão `SWPROGRAMACAO.rdp`).
- `TITULOS_RDP` — títulos da janela da Conexão de Área de Trabalho Remota, para reutilizar a sessão já aberta.
- `TEMPO_ESPERA_RDP` — tempo (s) aguardando a VPS abrir antes de executar o DATASUL (padrão 15).
- `ATALHO_ABRIR_PROGRAMA` — atalho do lançador (padrão `CTRL+X`).
- `ATALHO_ABRIR_PROGRAMA_ALT` / `TENTAR_ATALHO_ALTERNATIVO` — atalho alternativo
  (`CTRL+ALT+X`, o mesmo usado na automação de inventário) tentado
  automaticamente quando a janela do lançador não aparece com o `CTRL+X`.
- `LIMPAR_CAMPO_LANCADOR` — limpar o campo (`CTRL+A` + `DELETE`) antes de digitar.
- `DIRETORIO_IMPORTACAO_GM` — diretório de origem dos pedidos.
- `QTD_TAB_ENTER` — quantas vezes repetir (TAB, ENTER).
- `TEMPO_ESPERA_BOTAO_IMPORTACAO` — espera máxima por cada botão Abrir/Executar (30s).
- `TEMPO_ESPERA_DATASUL` — tempo máximo (s) esperando a janela do DATASUL (padrão 47).
- `TEMPO_ESPERA_LANCADOR` — tempo (s) esperando a janela do lançador (padrão 6).
- `TEMPO_ESPERA_ABRIR` — tempo (s) procurando o botão Abrir após o login (padrão 30).
- `TEMPO_ESPERA_PROGRAMA` — tempo (s) esperando o ESPD0001 carregar.
- `TITULOS_LANCADOR` — títulos do lançador de programas (opcional: a janela nova
  já é detectada mesmo que o título mude).
- `NAVEGADORES` — títulos de navegadores descartados na busca pelo DATASUL.

---

## 🔑 Login e senha por operador

Na aba **Acesso TOTVS**, edite o login (inicialmente `deivid`) e preencha a
senha antes de clicar em START. Os mesmos campos atendem ao inventário e à
importação HONDA & GM; qualquer um dos três operadores pode informar seu acesso.
A senha fica mascarada, com a opção **Mostrar senha**.

No primeiro uso, informe a senha e clique em **Salvar acesso** ou inicie um
fluxo com **START** (também salva automaticamente). Ao reabrir a interface,
**login e senha já vêm preenchidos**, inclusive após a automação. Alterações
são salvas nesses botões; fechar a janela sem salvar não guarda as edições.
Use **Esquecer acesso** para apagar o acesso salvo e limpar os campos.

O acesso é criptografado pela **DPAPI do Windows**, vinculado ao usuário Windows
atual, em `%LOCALAPPDATA%\AutomacaoTOTVS\acesso.dpapi`, fora da pasta do projeto.
Não há senha em texto puro no código, nos arquivos do projeto ou no log, nem
fallback para armazenamento sem proteção. Se não for possível salvar, a
interface avisa e permite usar o acesso somente naquela execução. Se o arquivo
não puder ser lido, informe e salve o acesso novamente.
Cada conta Windows mantém seu próprio acesso; pessoas que usam a mesma conta
Windows compartilham o acesso salvo. A proteção não impede programas executados
nessa conta de lerem os dados. Não copie esse arquivo para outro computador.

Os dados são passados somente ao processo filho por seu ambiente, não por
argumentos de linha de comando; o motor os retira do ambiente antes de abrir
Edge ou reabrir a interface. Isso evita repassá-los aos processos seguintes,
mas não substitui a proteção da sessão Windows contra outros usuários locais.
Se executar o motor diretamente, use a interface para fornecer o acesso.

**Uma sessão DATASUL já aberta é reutilizada**, sem trocar o usuário conectado.
As credenciais só são necessárias quando for preciso abrir pelo navegador.
A URL solicitada usa HTTP: mantenha o uso restrito à rede interna autorizada.

---

## 🚀 Como executar

```bash
# 1. (recomendado) criar e ativar um ambiente virtual
python -m venv .venv && .venv\Scripts\activate

# 2. instalar dependências
pip install -r requirements.txt

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
├── automacao_totvs.py          ⭐ Ponto de entrada do motor TOTVS
├── msedgedriver.exe            Driver do Edge (Selenium)
│
├── totvs/                      PARTE TOTVS
│   ├── automacao.py            Motor: ajuste de estoque, importação ESPD0001 e login
│   └── credenciais.py          Acesso TOTVS salvo com DPAPI (somente Windows)
│
├── swprogramacao/              PARTE SWPROGRAMAÇÃO (VPS)
│   ├── __main__.py             Linha de comando: python -m swprogramacao
│   ├── fluxo.py                Passo 1: valida as imagens, logins, ULIANA e checkpoint
│   ├── acessos.py              Acesso da VPS (ambiente/DPAPI), sem senha em texto puro
│   └── rdp.py                  Acha e abre o SWPROGRAMACAO.rdp
│
├── core/                       Código compartilhado pelas partes
│   ├── caminhos.py             Pastas do projeto (modo .py e .exe)
│   ├── telas.py                Ações de tela por imagem (PyAutoGUI)
│   ├── janelas.py              Validação de janelas do Windows
│   ├── credenciais.py          Armazenamento DPAPI fora do projeto (acessos)
│   └── rdp.py                  Procura e abre o SWPROGRAMACAO.rdp da área de trabalho
│
├── tests/                      Testes automatizados
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
`vencimento.png`, `ok.png`, `abrir_popup.png` (alternativa para `abrir.png`).

**Pendente de captura:** `img/executar.png` ainda não está incluída no repositório.
Coloque nesse caminho uma captura recortada do botão Executar do ESPD0001
antes de usar a sequência nova (e antes de compilar os executáveis).
`abrir_popup.png` já existe; confira se corresponde ao botão Abrir dessa etapa.
Não use uma imagem ilustrativa: a busca precisa da aparência real do botão.

Os botões Abrir e Executar usam confiança fixa de 90% (OpenCV), sem reduzir para limiares
que possam clicar em imagens não relacionadas. Use uma captura compatível com
a escala de tela/zoom do computador Windows.

As imagens da VPS (passo 1 da SWProgramação) ficam em `img/swprogramacao/`; veja a seção
própria acima.

---

## ✅ Requisitos

- **Python 3.x**
- **Microsoft Edge** instalado
- **msedgedriver.exe** compatível com a versão do Edge.
  Baixe em: <https://developer.microsoft.com/pt-br/microsoft-edge/tools/webdriver/>
  e coloque o `.exe` na pasta do projeto.

Bibliotecas Python:

```bash
pip install -r requirements.txt
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
| TOTVS não abre | Confira `msedgedriver.exe` (versão compatível com o Edge) e as credenciais/URL em `totvs/automacao.py`. |
| Planilha não existe | Verifique `data/RELATORIO_INVENTARIO.xlsx`. |
| Erro de permissão na planilha | Feche o arquivo no Excel antes de rodar a automação. |
| START da aba "Importar Pedido" não faz nada | Abra `log_automacao.txt`: se o timestamp **não** mudou, o `Automacao_TOTVS.exe` nem iniciou (confira se ele está na mesma pasta da interface). Se mudou, o log mostra em qual passo parou e lista as janelas abertas — confira ali o título real da janela do DATASUL. |
| O `CTRL+X` não abre a janela do lançador | O log mostra `A janela do lançador não apareceu com CTRL+X. Tentando CTRL+ALT+X...` — a automação já tenta o atalho alternativo sozinha. Se nenhum dos dois abrir, confira o atalho direto no TOTVS e ajuste `ATALHO_ABRIR_PROGRAMA` no topo de `totvs/automacao.py`. |
| O texto digitou no lugar errado (não no TOTVS) | Significa que o DATASUL não era a janela ativa. O log traz `Foco não confirmado no DATASUL; nenhuma tecla será enviada.`; se o foco não for confirmado, a automação **para** e avisa na tela em vez de digitar às cegas. Clique na janela do DATASUL e clique em START de novo. |
| Importação para com "SWPROGRAMACAO.rdp não encontrado" | Coloque o arquivo na área de trabalho (valem Desktop, OneDrive/Desktop, Área de Trabalho e OneDrive/Área de Trabalho). Enquanto a VPS não abre, o DATASUL não é executado de propósito; se a sessão RDP já estiver aberta, o arquivo nem é procurado. |

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

## Testes deste fluxo

```bash
python -m unittest discover -s tests -v
```

Os testes simulam as APIs Windows, Selenium e teclado/mouse sem acessar o
servidor interno. Validação final precisa ser feita no Windows com Edge e TOTVS:

- DATASUL minimizado: deve reutilizar a sessão e confirmar foco antes de CTRL+X.
- Apenas uma aba Edge chamada DATASUL Interactive: não pode ser confundida com o aplicativo.
- DATASUL fechado, inclusive com `prowin32.exe` restante: deve iniciar pelo Edge.
- Salvar acesso e fechar/reabrir a interface: login e senha devem estar preenchidos.
- Conferir os dois ENTERs ao redor da colagem, depois Abrir → Executar, sem ENTER final.
- Remover/ocultar cada imagem: deve interromper, sem clicar no próximo botão.
- Testar **Esquecer acesso** e confirmar que a senha não volta ao reabrir.
- Senha inválida, imagem ausente ou janela sem foco: deve parar sem continuar o pedido.
- Alterar o acesso para cada operador e testar tanto `.py` quanto os `.exe` recompilados.
- SWProgramação, passo 1: com a VPS aberta, `python -m swprogramacao --diagnostico` deve achar o `.rdp` e as 4 imagens; depois, rodar até achar a ULIANA (`ULIANA encontrada` no log).
- SWProgramação: sem as 4 capturas em `img/swprogramacao/`, o passo para **antes** de abrir a VPS e diz quais faltam; com `--salvar-acesso` (ou variáveis de ambiente), rodar de novo não deve pedir senha.
- Importação: ao clicar em START, o log deve mostrar a abertura do `SWPROGRAMACAO.rdp` ANTES da busca pelo DATASUL. Com uma sessão RDP já aberta, nada deve ser reaberto; sem o `.rdp` (e sem sessão aberta), o DATASUL não deve ser executado.

Instale as dependências atualizadas e execute `compilar.bat` novamente para
usar as alterações nos executáveis. O ambiente Linux de desenvolvimento não
valida a interface gráfica Windows nem a conectividade com a rede interna.
