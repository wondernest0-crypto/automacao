# Capturas da VPS — SWProgramação (passo 1)

Esta pasta guarda as **capturas reais da tela da VPS**, usadas pelo PyAutoGUI
para reconhecer cada etapa. Os arquivos `.png` daqui **não vão para o Git**
(estão no `.gitignore`): cada computador que roda a automação precisa das
próprias capturas.

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

Mostra cada imagem como `visível em x,y` (achou na tela atual) ou
`não visível agora` (a captura não corresponde à tela), além de `FALTA` quando
o arquivo não existe.

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
