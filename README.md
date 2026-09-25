# 🤖 Sistema de Automação de Inventário TOTVS

## 📌 Versão 2.1 - Atualizado em 20/02/2026

Sistema automatizado para ajuste de estoque no TOTVS, com interface gráfica, logs detalhados e suporte para uso em rede.

---

## ✨ NOVIDADES DA VERSÃO 2.1

### 🖼️ Logs Detalhados de Imagens
- Caminho completo de cada imagem registrado no log
- Facilita diagnóstico quando projeto está em rede
- Identifica rapidamente problemas de caminho

### 📊 Dashboard Melhorado
- Colunas mais largas (40 e 25 caracteres)
- Gráficos 50% maiores
- Novo gráfico de Volume (Excesso vs Falta)
- Labels em negrito com fontes maiores

### 🌐 Modo Compartilhamento
- Suporte para múltiplos usuários visualizando
- Automação funciona com outros usuários na planilha
- Tratamento de erro de permissão
- Script de configuração automática

### 🔄 Sincronização Automática
- Dados da aba CONTAGEM replicados para HISTORICO_AJUSTES
- Histórico sempre atualizado
- Rastreabilidade completa

---

## 🚀 INÍCIO RÁPIDO

### 1. Testar o Sistema
```bash
# Windows
executar_testes.bat

# Ou
python testar_ajustes.py
```

### 2. Criar Planilha (se não existir)
```bash
# Windows
criar_planilha.bat

# Ou
python criar_planilha_exemplo.py
```

### 3. Configurar para Rede
```bash
# Windows
configurar_rede.bat

# Ou
python configurar_compartilhamento.py
```

### 4. Executar Automação
```bash
python lancamento_inventario.py
```

---

## 📁 ESTRUTURA DO PROJETO

```
inventario/
├── 📄 Automação
│   ├── automacao_totvs.py          ⭐ Principal (MODIFICADO)
│   ├── lancamento_inventario.py    Interface gráfica
│   └── inv.py                       Funções auxiliares
│
├── 🆕 Novos Scripts
│   ├── configurar_compartilhamento.py  Preparar para rede
│   ├── testar_ajustes.py               Testes completos
│   └── criar_planilha_exemplo.py       Criar planilha
│
├── 📊 Planilhas
│   └── gerar_planilha.py           ⭐ Gerador (MODIFICADO)
│
├── 📚 Documentação
│   ├── GUIA_RAPIDO.md              👈 Comece aqui!
│   ├── AJUSTES_REALIZADOS.md       Detalhes técnicos
│   ├── RESUMO_AJUSTES.txt          Resumo executivo
│   └── INDICE_ARQUIVOS.md          Lista completa
│
├── 🖥️ Atalhos Windows
│   ├── executar_testes.bat
│   ├── configurar_rede.bat
│   └── criar_planilha.bat
│
├── 📂 data/
│   └── RELATORIO_INVENTARIO.xlsx   Planilha principal
│
└── 🖼️ img/
    └── *.png                        Imagens para automação
```

---

## 📚 DOCUMENTAÇÃO

### Para Usuários
- **[GUIA_RAPIDO.md](GUIA_RAPIDO.md)** - Guia prático passo a passo
- **[RESUMO_AJUSTES.txt](RESUMO_AJUSTES.txt)** - Resumo das mudanças

### Para Desenvolvedores
- **[AJUSTES_REALIZADOS.md](AJUSTES_REALIZADOS.md)** - Documentação técnica completa
- **[INDICE_ARQUIVOS.md](INDICE_ARQUIVOS.md)** - Lista de todos os arquivos

---

## 🔧 REQUISITOS

### Software
- Python 3.x
- Microsoft Edge (para abrir TOTVS)
- Microsoft Excel (para visualizar planilhas)

### Bibliotecas Python
```bash
pip install pandas openpyxl pyautogui pygetwindow selenium xlsxwriter
```

### Arquivos Necessários
- `msedgedriver.exe` (driver do Edge)
- Imagens na pasta `img/` (8 arquivos .png)
- Planilha `RELATORIO_INVENTARIO.xlsx` na pasta `data/`

---

## 💡 FUNCIONALIDADES

### ✅ Automação Completa
- Abre TOTVS automaticamente via navegador
- Processa itens pendentes da planilha
- Ajusta estoque (entrada/saída)
- Atualiza planilha automaticamente
- Gera log detalhado

### ✅ Interface Gráfica
- Lançamento manual de itens
- Visualização de pendentes
- Cadastro de colaboradores
- Resumo de acuracidade

### ✅ Relatórios
- Dashboard com gráficos
- Histórico de ajustes
- Indicadores de acuracidade
- Análise de divergências

### ✅ Logs Detalhados
- Caminho completo das imagens
- Cada passo da automação
- Erros e avisos
- Timestamp preciso

---

## 🌐 USO EM REDE

### Configuração
1. Execute `configurar_rede.bat`
2. Coloque pasta em local compartilhado
3. Configure permissões de leitura/escrita
4. Teste com um usuário primeiro

### Importante
- ✅ Múltiplos usuários podem VISUALIZAR
- ✅ Automação funciona com outros visualizando
- ⚠️ Apenas um usuário pode EDITAR por vez

---

## 📝 LOGS

### Localização
```
log_automacao.txt
```

### Informações Registradas
- 🖼️ Caminhos completos das imagens
- 📦 Processamento de cada item
- ✅ Sucessos e conclusões
- ❌ Erros e avisos
- ⏱️ Timestamp de cada operação

### Exemplo de Log
```
🔍 DEBUG: 🖼️ Procurando imagem: +.png
🔍 DEBUG:    Caminho completo: C:\...\img\+.png
🔍 DEBUG:    Existe: True
🔍 DEBUG:    ✅ Encontrada com confiança: 0.9

📦 PROCESSANDO ITEM: VK22020
   Quantidade Física: 100
   Colaborador: João Silva

✅ SUCESSO: Relatório salvo! Linha 5 marcada como AJUSTADO
✅ SUCESSO: Histórico atualizado na linha 10
```

---

## 🔍 SOLUÇÃO DE PROBLEMAS

### Imagens não encontradas
```bash
# Verifique os caminhos no log
python testar_ajustes.py
```

### Erro de permissão
```bash
# Configure para rede
python configurar_compartilhamento.py
```

### Planilha não existe
```bash
# Crie a planilha
python criar_planilha_exemplo.py
```

### TOTVS não abre
- Verifique `msedgedriver.exe`
- Confirme credenciais em `automacao_totvs.py`
- Teste abrir TOTVS manualmente

---

## 📊 PLANILHA RELATORIO_INVENTARIO.xlsx

### Aba CONTAGEM
- ITEM - Código do item
- QTD FÍSICA - Quantidade contada
- QTD FISCAL - Preenchido pela automação
- DIFERENÇA - Calculado automaticamente
- STATUS - OK, EXCESSO ou FALTA
- ACURACIDADE % - Percentual de acerto
- AJUSTADO - SIM após processamento
- COLABORADOR - Quem contou
- DATA/HORA - Quando foi processado

### Aba HISTORICO_AJUSTES
- Registro de todos os ajustes
- Sincronizado automaticamente
- Mantém histórico completo

### Aba DASHBOARD
- Gráficos melhorados
- Indicadores de acuracidade
- Análise de divergências

---

## 🎯 FLUXO DE TRABALHO

### 1. Preparação
```
1. Abrir planilha RELATORIO_INVENTARIO.xlsx
2. Adicionar itens na aba CONTAGEM
3. Preencher: ITEM, QTD FÍSICA, COLABORADOR
4. Salvar e fechar
```

### 2. Execução
```
1. Executar: python lancamento_inventario.py
2. Clicar em "Iniciar Automação"
3. Aguardar processamento
4. Verificar log
```

### 3. Verificação
```
1. Abrir planilha
2. Verificar aba CONTAGEM (coluna AJUSTADO = SIM)
3. Verificar aba HISTORICO_AJUSTES
4. Conferir log_automacao.txt
```

---

## 🛠️ SCRIPTS UTILITÁRIOS

### `testar_ajustes.py`
Testa toda a estrutura do sistema
```bash
python testar_ajustes.py
```

### `configurar_compartilhamento.py`
Prepara planilha para uso em rede
```bash
python configurar_compartilhamento.py
```

### `criar_planilha_exemplo.py`
Cria planilha do zero
```bash
python criar_planilha_exemplo.py
```

### `gerar_planilha.py`
Gera planilha com dashboard completo
```bash
python gerar_planilha.py
```

---

## 📞 SUPORTE

### Desenvolvedor
**Deivid - Faturamento**

### Versão
2.1 (20/02/2026)

### Documentação
- [GUIA_RAPIDO.md](GUIA_RAPIDO.md) - Guia prático
- [AJUSTES_REALIZADOS.md](AJUSTES_REALIZADOS.md) - Detalhes técnicos

### Logs
- `log_automacao.txt` - Log completo da automação

---

## 📜 LICENÇA

Sistema desenvolvido para uso interno.  
Todos os direitos reservados.

---

## 🎉 AGRADECIMENTOS

Obrigado por usar o Sistema de Automação de Inventário TOTVS!

Para começar, leia o **[GUIA_RAPIDO.md](GUIA_RAPIDO.md)** 👈

---

**Última atualização:** 20/02/2026  
**Versão:** 2.1
