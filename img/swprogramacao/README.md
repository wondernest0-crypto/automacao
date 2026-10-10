# Capturas da VPS — SWProgramação (passo 1)

Esta pasta guarda as **capturas reais da tela da VPS**, usadas pelo PyAutoGUI
para reconhecer cada etapa. Os `.png` daqui **vão para o Git**: a tela da VPS é
a mesma para todos, então as capturas viajam junto com o projeto. Só é preciso
recapturar quando a **resolução** ou a **escala de exibição** do computador que
roda a automação mudar.

> As 4 capturas ainda não estão no repositório. Quem já tem os arquivos no PC
> precisa adicioná-los uma vez: `git add img/swprogramacao/*.png`.

## O que capturar (4 arquivos, nomes exatos)

| Arquivo | O que é | Dica de captura |
|---|---|---|
| `login.png` | Tela de **login do Windows** da VPS (onde pede usuário e senha do Windows). | Recorte com a área do formulário de login. A automação cola o usuário, dá TAB, cola a senha e dá ENTER — o campo precisa ser o foco da tela. |
| `login_edi.png` | Tela de **login do EDI** (onde aparece `Usuário:`). | Recorte com o rótulo `Usuário:` e o campo ao lado. Só aparece depois do login do Windows. |
| `informe_parceiro.png` | Tela **"Informe o parceiro"**. | Recorte com o rótulo `Informe o parceiro:` — é o sinal de que os logins terminaram. |
| `uliana.png` | A linha **ULIANA** na lista de parceiros. | Recorte pequeno, só a linha da ULIANA (nome + código, se houver). A automação só procura essa linha e termina; não clica nela. |

## Regras importantes

- **Use capturas reais, não imagens ilustrativas.** A busca compara os pixels
  da tela; uma imagem "parecida" não é encontrada.
- Capture na **mesma resolução, escala e zoom** do computador que vai rodar a
  automação (o RDP precisa abrir em tela cheia ou no mesmo tamanho da captura).
- Salve como **`.png`**, com exatamente os nomes da tabela.
- Se a tela da VPS mudar (tema, idioma, resolução), **recapture** a imagem
  correspondente.

## Como conferir

```
python -m swprogramacao --diagnostico
```

Mostra a pasta usada, a resolução e a escala da tela, se a janela da VPS está
aberta e, para cada imagem, `visível em x,y (confiança 0.9)` (achou na tela
atual), `não visível agora` (a captura não corresponde à tela) ou `FALTA`
(quando o arquivo não existe). Ao lado de cada imagem vem o tamanho em pixels
da captura: se ele for maior que a resolução listada, a imagem nunca será
encontrada.

## "O arquivo existe, mas a imagem nunca é encontrada"

Nessa ordem:

1. **Janela da VPS visível.** A automação só enxerga o que está na tela. Janela
   minimizada, atrás de outra ou em um segundo monitor não casa com nada. O
   fluxo já traz a janela da Conexão de Área de Trabalho Remota para o primeiro
   plano depois de abrir o `.rdp`; se o log disser que não conseguiu, traga a
   janela para a frente manualmente.
2. **Escala de exibição.** No Windows com escala diferente de 100% (125%, 150%),
   uma captura feita na escala real não casa com uma tela lida em escala
   reduzida. O projeto marca o processo como *DPI aware* ao criar a tela, e o
   `--diagnostico` mostra a escala em uso. Se a escala do PC de quem capturou
   for diferente da sua, **recapture no seu PC**.
3. **Resolução e tamanho da janela.** A captura precisa ter sido feita com a
   janela da VPS no mesmo tamanho em que ela abre. Não maximize nem redimensione
   a janela depois de capturar.
4. **Confiança.** A busca testa de 0.9 até 0.6. Para aceitar um casamento mais
   frouxo (útil para diagnosticar), rode com `--confianca-minima 0.4`:
   `python -m swprogramacao --confianca-minima 0.4`. Se a imagem só casar com
   confiança baixa, refaça a captura — ela está diferente da tela atual.

## Acesso (login e senha)

As credenciais não ficam nesta pasta. Guarde uma vez com:

```
python -m swprogramacao --salvar-acesso
```

O acesso fica protegido pela DPAPI do Windows em
`%LOCALAPPDATA%\AutomacaoTOTVS\acesso_sw.dpapi`, fora do projeto. Para apagar:
`python -m swprogramacao --esquecer-acesso`. Também é possível passar o acesso
por variáveis de ambiente (`SW_WINDOWS_LOGIN`, `SW_WINDOWS_SENHA`,
`SW_EDI_LOGIN`, `SW_EDI_SENHA`).
