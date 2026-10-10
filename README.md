# 🤖 Sistema de Automação de Inventário TOTVS

Sistema para ajuste de estoque no TOTVS. Possui interface gráfica, automação
do navegador (Selenium + PyAutoGUI), atualização automática de planilhas e
log detalhado de execução.

---

## 🧩 Como funciona (lógica)

O sistema é dividido em **partes que não se importam entre si**; quem as liga fica na raiz:

1. **`lancamento_inventario.py`** — Interface gráfica (Tkinter).
   É por aqui que tudo começa. Serve para lançar/consultar itens, cadastrar
   colaboradores e **iniciar a automação**.
2. **`automacao_totvs.py`** — Motor da automação (ponto de entrada; a lógica fica em `totvs/automacao.py`).
   Abre o TOTVS no navegador (Edge), lê a planilha `RELATORIO_INVENTARIO.xlsx`,
   ajusta o estoque de cada item (entrada/saída) e, ao terminar, reabre a
   interface gráfica.
3. **`orquestrador.py`** — Define a ordem entre as partes: **VPS (SWProgramação)
   primeiro, DATASUL (TOTVS) depois**. É quem o START chama hoje.

Fluxo resumido (ajuste de estoque):

```
lancamento_inventario.py  --(clicar "Iniciar Automação")-->  automacao_totvs.py
        ↑                                                            |
        └----------------------(ao concluir)-------------------------┘
```

Fluxo do START (aba Importar Pedido HONDA & GM), decidido pelo orquestrador:

```
lancamento_inventario.py --(START)--> automacao_totvs.py importar --> orquestrador.py
                                                                          |
                        1º SWProgramação: SWPROGRAMACAO.rdp -> logins -> ULIANA
                        2º DATASUL  (DESLIGADO hoje: volta quando o 1º estiver finalizado)
```

---

## 🧱 Partes do projeto

O código está separado em partes, para que cada uma evolua sem mexer nas outras:

| Pasta | Parte | O que faz |
|---|---|---|
| `totvs/` | **TOTVS** | Ajuste de estoque, importação ESPD0001 (aba Importar Pedido HONDA & GM, por enquanto) e acesso ao TOTVS pelo Edge. |
| `swprogramacao/` | **SWProgramação** | Acesso à VPS. **Passo 1 pronto para teste** (abre a VPS e para na ULIANA carregada). Configurações e pedidos HONDA e GM: *em construção.* |
| `core/` | Compartilhado | Caminhos do projeto (modo .py e .exe), ações de tela por imagem, validação de janelas do Windows e busca/abertura do `.rdp` da área de trabalho. |
| `orquestrador.py` | **Sequência (raiz)** | Único lugar que liga as duas partes: define que a **VPS (SWProgramação) vem primeiro e o DATASUL (TOTVS) só depois**. Hoje a sequência tem só a etapa da VPS. |

Fluxo previsto: primeiro a parte **SWProgramação** (VPS: pedido HONDA e depois GM); em seguida, a parte **TOTVS**. A ordem vive em `orquestrador.py`, na raiz — as partes não se importam umas às outras (`tests/test_limites_partes.py` garante isso).

**Regra da vez:** o DATASUL **não** é executado enquanto todo o procedimento do `SWPROGRAMACAO.rdp` (abrir a VPS, login do Windows, login do EDI, tela “Informe o parceiro” e ULIANA) não terminar. Essa etapa ainda está em construção, então o START da aba de importação roda **somente a VPS** e encerra — não envia nenhuma tecla ao DATASUL. Quando ela for dada como finalizada, a entrada no DATASUL volta ao orquestrador, que já garante a ordem.

`lancamento_inventario.py` e `automacao_totvs.py` continuam na raiz porque o `compilar.bat`, os `.spec` e o workflow usam esses nomes. O teste `tests/test_limites_partes.py` impede que as partes importem umas às outras.

---

## 🖥️ SWProgramação (VPS): passo 1

Este passo abre a VPS, faz os dois logins e **procura a ULIANA na lista de parceiros**. Quando a ULIANA é encontrada, a automação **clica nela 3 vezes**, pausa e encerra com sucesso — a VPS permanece aberta com a ULIANA carregada. Ainda não faz configurações nem importação de pedidos.

**Ele é a primeira etapa da sequência do START**, e é o mesmo procedimento nos dois caminhos: `python -m swprogramacao` (com terminal) e o botão START da interface (sem terminal), que passa por `orquestrador.py`. Enquanto este procedimento não estiver finalizado, o DATASUL não é executado (veja “Partes do projeto” acima).

O procedimento na tela da VPS, na ordem (o campo de usuário já vem com o foco, por isso nada é clicado):

```
(abre o .rdp, aguarda 10 s e traz a janela da VPS para a frente)
login.png             -> usuário do Windows, TAB, senha, ENTER  (espera 3 s)
login_edi.png         -> usuário do EDI, TAB, senha, ENTER      (espera 4 s para carregar)
informe_parceiro.png  -> tela “Informe o parceiro”: os logins terminaram
uliana.png            -> clica 3 vezes na ULIANA, pausa e encerra com sucesso
```

**O que ele faz, em ordem:**

1. Confere se as 4 capturas existem em `img/swprogramacao/`. Se faltar alguma, **para antes de abrir a VPS** e diz quais faltam (imagem ausente é arquivo ausente, não "não achei na tela").
2. Abre o `SWPROGRAMACAO.rdp` da área de trabalho (igual a dar dois cliques). A busca cobre a pasta real da área de trabalho do Windows (API de pastas conhecidas), `Desktop`, `Área de Trabalho` e as versões dentro do OneDrive.
3. **Aguarda 10 s** após abrir o `.rdp` e então espera a janela da **Conexão de Área de Trabalho Remota** aparecer e a coloca em **primeiro plano**, sem redimensionar (redimensionar muda a escala do conteúdo remoto e quebra a comparação com a captura). A busca por imagem só enxerga o que está visível na tela: VPS minimizada ou atrás de outra janela nunca casa.
4. Registra no log a **resolução, a escala de exibição e o tamanho em pixels de cada captura** — são os números que explicam "o arquivo existe mas nunca é achado". Captura maior que a tela atual é impossível de achar, e o log avisa.
5. A cada ciclo, **procura as imagens na ordem** `login.png`, depois `login_edi.png`, depois `informe_parceiro.png`, e age na primeira que achar, testando a confiança de 0.9 até 0.6 (o valor em que a imagem casou vai para o `--diagnostico`):
   - `login.png` (login do Windows, com o campo de usuário já em foco): usuário, TAB, senha, ENTER, e espera 3 s;
   - `login_edi.png` (login do EDI, "Usuário:"): usuário, TAB, senha, ENTER, e espera **4 s** (`ESPERA_APOS_ENTER_EDI`);
   - `informe_parceiro.png`: é o sinal de que os logins terminaram.
   Cada login é digitado **uma vez**. Se a senha estiver errada, o passo para com erro e não tenta de novo.
6. Com `informe_parceiro.png` na tela, **procura `uliana.png`**. Achou: **clica nela 3 vezes**, pausa 5 s e **termina com sucesso** (a VPS continua aberta). Se não achar em 15 s, para com erro.

**Antes de rodar:**

- Coloque as 4 capturas em `img/swprogramacao/`: `login.png`, `login_edi.png`, `informe_parceiro.png` e `uliana.png`. Use capturas reais da tela da VPS, na mesma resolução e zoom do computador que vai rodar. Não use imagens ilustrativas. As instruções de captura de cada imagem estão em `img/swprogramacao/README.md`.
- As capturas **vão para o Git** (a tela da VPS é a mesma para todos). Recapture só se a resolução ou a escala de exibição do PC mudar.
- Mantenha a área de transferência ativa no RDP (é o padrão do Windows). Os dados são colados, não digitados, para evitar problemas com `@` e outros símbolos.
- Deixe a janela da VPS visível e não minimizada: a automação enxerga só o que está na tela. O fluxo já traz a janela para o primeiro plano depois de abrir o `.rdp`; se o log disser que não conseguiu, traga manualmente.
- Deixe a **escala de exibição** do Windows igual à do PC onde as capturas foram feitas. O processo é marcado como *DPI aware* automaticamente; sem isso, com escala de 125%/150%, a tela é lida reduzida e nenhuma captura casa.
- Ainda não existe `.exe` para esta parte. Rode pelo Python, como abaixo.

**Como rodar** (na pasta do projeto):

```
python -m swprogramacao --salvar-acesso     # guarda o acesso uma vez (DPAPI, no Windows)
python -m swprogramacao --diagnostico       # confere o .rdp, a tela, as 4 imagens e o acesso salvo
python -m swprogramacao                     # roda o passo 1 até achar a ULIANA
python -m swprogramacao --confianca-minima 0.4   # diagnóstico: aceita casamento mais frouxo
python -m swprogramacao --esquecer-acesso   # apaga o acesso salvo
```

Prefere não digitar comando? Há dois atalhos na raiz: **`salvar_acesso_sw.bat`**
(guarda o acesso; rode uma vez em cada conta Windows) e **`diagnostico_sw.bat`**
(conferência completa), que abrem, fazem o serviço e esperam você ler o resultado.

> O START da interface (e o `.exe`) **não tem terminal para pedir senha**. Por
> isso, se não houver acesso salvo, a sequência para antes de abrir a VPS e
> diz para rodar `--salvar-acesso` — é o `salvar_acesso_sw.bat` que resolve.

Com a VPS aberta, o `--diagnostico` mostra a **pasta usada** (em `.exe` ela é a pasta do executável, não a do projeto), a **resolução e a escala da tela**, se a **janela da VPS está aberta**, o **tamanho em pixels de cada captura** e onde cada imagem foi encontrada (`visível em x,y (confiança 0.9)`). Se alguma aparecer como "não visível", a captura não corresponde à tela atual — veja "Imagem existe mas nunca é encontrada" na tabela de problemas.

**Segurança:** o acesso (login do Windows e do EDI) pode ser guardado **uma vez** com `--salvar-acesso`, protegido pela DPAPI do Windows em `%LOCALAPPDATA%\AutomacaoTOTVS\acesso_sw.dpapi`, fora da pasta do projeto. Também pode ser passado por variáveis de ambiente (`SW_WINDOWS_LOGIN`, `SW_WINDOWS_SENHA`, `SW_EDI_LOGIN`, `SW_EDI_SENHA`), com prioridade sobre o arquivo salvo. Se não houver acesso salvo, ele é pedido no terminal. Não há senha em texto puro no código, nos arquivos do projeto ou no log, e nenhuma senha aparece no log. O registro fica em `log_swprogramacao.txt`, que é ignorado pelo Git.

**Se parar:** o terminal e o log dizem em qual etapa parou (imagem faltando, login do Windows, login do EDI, ULIANA não encontrada ou tempo esgotado).

---

## 🚗 Importar Pedido HONDA & GM (aba dedicada)

A interface tem uma segunda aba, **"Importar Pedido HONDA & GM"**, com um botão
grande e vermelho **START**. Ao clicar, a interface chama
`automacao_totvs.py importar`, que entrega a sequência ao `orquestrador.py`.

> ### ⚠️ O DATASUL não é executado nesta versão
>
> A parte do `SWPROGRAMACAO.rdp` ainda está em construção, e ficou combinado
> que o DATASUL só entra **depois que todo o procedimento do RDP terminar**.
> Hoje o START roda somente os passos 1 e 2 abaixo (a VPS), encerra após
> clicar 3 vezes na ULIANA e reabre a interface — nenhuma tecla é enviada ao DATASUL. Os passos do
> DATASUL continuam prontos no motor (`totvs/automacao.py`,
> `AutomacaoTOTVS.importar_pedido`) e voltam à sequência quando essa etapa for
> dada como finalizada; nada mais precisa mudar, porque a ordem “VPS primeiro,
> DATASUL depois” já é garantida pelo orquestrador.

**O que o START faz hoje, em ordem:**

1. **Abre a VPS:** procura `SWPROGRAMACAO.rdp` na área de trabalho (Desktop,
   OneDrive/Desktop, Área de Trabalho e OneDrive/Área de Trabalho) e o abre
   igual a dar dois cliques; depois traz a janela da VPS para o primeiro plano.
2. **Faz o procedimento da VPS:** aguarda 10 s após abrir o `.rdp`, login do
   Windows (usuário, TAB, senha, ENTER), login do EDI (usuário, TAB, senha,
   ENTER), 4 s para carregar, espera a tela “Informe o parceiro”, procura a
   ULIANA e clica nela 3 vezes. É exatamente o mesmo procedimento
   de `python -m swprogramacao` (seção acima). Sem o `.rdp`, sem acesso salvo
   ou com alguma captura faltando, ele para **antes** de abrir a VPS.
3. **Encerra e reabre a interface**, registrando no log que o DATASUL está
   desligado. Se qualquer etapa falhar, o aviso aparece na tela e o motivo
   exato fica em `log_automacao.txt`.

**Passos do DATASUL — desligados hoje, na ordem em que voltam:**

1. Procura uma janela DATASUL disponível **antes de minimizar ou
   abrir o navegador**. Uma sessão já aberta é reutilizada.
2. Consulta as janelas nativas do Windows (sem abrir visualmente o Gerenciador
   de Tarefas). Aceita **"DATASUL Interactive"** ou **"DATASUL Interative"**,
   inclusive minimizadas e com sufixos no título. Exige janela visível/responsiva
   e processo vivo; descarta navegadores pelo título **e pelo executável**.
   Se não encontrar janela, registra os processos como diagnóstico: um
   `prowin32.exe` isolado **não bloqueia** a abertura e não é encerrado.
   Confere as janelas novamente antes de iniciar outra sessão. Sem janela,
   minimiza as demais com `WIN+M` (não usa `WIN+D`, que alterna a área de trabalho).
3. Se não encontrar uma janela disponível, abre o Edge em
   `http://192.168.2.6:8080/totvs-menu`, preenche o acesso informado na interface
   e clica em **Entrar**. Procura `img/abrir.png` (ou `img/abrir_popup.png`,
   nome existente nesta versão) por até 30s e clica no botão encontrado.
   Se o DATASUL abrir sem popup, segue normalmente. Sem imagem correspondente,
   interrompe com aviso em vez de enviar atalhos às cegas.
   Depois do clique, aguarda até 47s pela janela/processo DATASUL.
4. Restaura e ativa a janela, usando também `SetForegroundWindow`,
   `BringWindowToTop` e clique na barra de título. **Exige confirmação real do
   foco antes do CTRL+X**; se a consulta falhar ou outra janela estiver ativa,
   interrompe. Não envia TAB para tentar ativar uma janela desconhecida.
5. **CTRL+X** → abre a **janela do lançador de programas**. A automação espera
   essa janela aparecer (pelos títulos conhecidos **ou** por "qualquer janela
   nova" que surja depois do atalho), traz ela para a frente e só então digita.
6. Digita **ESPD0001** → **ENTER** (o campo é limpo com `CTRL+A` + `DELETE`
   antes de digitar, para não juntar com um código que já estivesse lá).
7. Após o carregamento do programa, envia **1x TAB** → **ENTER** para confirmar
   a tela inicial do ESPD0001.
8. Envia **5x TAB consecutivos**, sem ENTER entre eles, para chegar ao campo de
   endereço. Depois pressiona **ENTER**, antes de colar.
9. Cola o diretório `\\192.168.0.9\s\Sawluz\swedi\OUTPUT\GM\` e pressiona **ENTER**.
10. Envia **4x** TAB → seta **↓** → seta **↑**.
11. Procura **`img/abrir_popup.png`** e clica; em seguida procura
    **`img/executar.png`** e clica. Aguarda até 30s por cada botão, com confiança
    fixa de 90%. Arquivo ausente, erro ou botão não encontrado interrompe o
    fluxo com aviso; não tenta confirmar por ENTER.
12. Encerra após o clique em Executar e reabre a interface, **sem ENTER final**
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
├── orquestrador.py             ⭐ Sequência: VPS (SWProgramação) primeiro, DATASUL depois
├── msedgedriver.exe            Driver do Edge (Selenium)
│
├── totvs/                      PARTE TOTVS
│   ├── automacao.py            Motor: ajuste de estoque, importação ESPD0001 e login
│   └── credenciais.py          Acesso TOTVS salvo com DPAPI (somente Windows)
│
├── swprogramacao/              PARTE SWPROGRAMAÇÃO (VPS)
│   ├── __main__.py             Linha de comando: python -m swprogramacao
│   ├── execucao.py             Passo 1 com as dependências reais (usado pela CLI e pelo START)
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
├── salvar_acesso_sw.bat        Atalho: salva o acesso da VPS (DPAPI, uma vez)
├── diagnostico_sw.bat          Atalho: confere .rdp, tela, imagens e acesso
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
| SWProgramação: a imagem existe mas nunca é encontrada | Rode `python -m swprogramacao --diagnostico` e confira, nesta ordem: (1) a **janela da VPS está visível** — minimizada, atrás de outra ou em outro monitor nunca casa; (2) a **escala de exibição** do Windows é a mesma do PC que capturou (com 125%/150% a tela é lida reduzida; o projeto já marca o processo como *DPI aware*); (3) o **tamanho da captura** não é maior que a resolução listada; (4) teste `--confianca-minima 0.4` — se só casar frouxo, refaça a captura. |
| SWProgramação: "Faltam imagens em img\swprogramacao/" | O arquivo não existe no caminho indicado. O `--diagnostico` mostra a pasta absoluta em uso: em `.exe` ela é a pasta do executável, não a do projeto. |
| START não entra no DATASUL (comportamento esperado hoje) | Enquanto o procedimento do `SWPROGRAMACAO.rdp` não estiver finalizado, a sequência para na VPS de propósito: o log traz `A entrada no DATASUL está DESLIGADA nesta versão`. O DATASUL volta quando essa etapa for dada como finalizada. |
| START para dizendo que não há acesso da VPS salvo | Salve uma vez com `python -m swprogramacao --salvar-acesso` (a interface/.exe não tem terminal para pedir a senha) ou defina `SW_WINDOWS_LOGIN`, `SW_WINDOWS_SENHA`, `SW_EDI_LOGIN` e `SW_EDI_SENHA`. Nenhuma senha é gravada no projeto nem no log. |
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
- SWProgramação, passo 1: com a VPS aberta, `python -m swprogramacao --diagnostico` deve achar o `.rdp`, mostrar resolução/escala/janela da VPS e achar as 4 imagens; depois, rodar até achar a ULIANA, clicar nela 3 vezes e terminar com sucesso (`ULIANA encontrada ... clicando 3 vezes` no log).
- Sequência (orquestrador): com o passo 1 simulado como concluído, o START termina sem chamar o DATASUL e sem enviar nenhuma tecla; com o passo 1 falhando, o DATASUL não é chamado, o aviso aparece na tela e a interface é reaberta.
- SWProgramação: sem as 4 capturas em `img/swprogramacao/`, o passo para **antes** de abrir a VPS e diz quais faltam; com `--salvar-acesso` (ou variáveis de ambiente), rodar de novo não deve pedir senha.
- SWProgramação: ao rodar, o log deve trazer `Janela da VPS em primeiro plano` e a linha `Tela: resolução ...; escala ...` com o tamanho em pixels de cada captura.
- Importação: ao clicar em START, o log (`log_automacao.txt`) deve mostrar o procedimento do `SWPROGRAMACAO.rdp` (login do Windows, login do EDI, tela de parceiro e ULIANA) e, no fim, `A entrada no DATASUL está DESLIGADA nesta versão`. Nenhuma tecla deve ser enviada ao DATASUL.
- Importação: com uma captura faltando, com o `.rdp` ausente ou sem acesso salvo, o START deve parar antes mesmo de abrir a VPS, mostrar o aviso na tela e reabrir a interface.

Instale as dependências atualizadas e execute `compilar.bat` novamente para
usar as alterações nos executáveis. O ambiente Linux de desenvolvimento não
valida a interface gráfica Windows nem a conectividade com a rede interna.
