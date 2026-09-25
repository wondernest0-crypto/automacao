# 🚀 GUIA RÁPIDO - SISTEMA DE INVENTÁRIO

## 📋 ÍNDICE
1. [Primeiros Passos](#primeiros-passos)
2. [Configurar para Rede](#configurar-para-rede)
3. [Executar Automação](#executar-automação)
4. [Verificar Logs](#verificar-logs)
5. [Solução de Problemas](#solução-de-problemas)

---

## 🎯 PRIMEIROS PASSOS

### 1. Testar o Sistema
```bash
# Clique duas vezes em:
executar_testes.bat

# Ou execute:
python testar_ajustes.py
```

Isso vai verificar:
- ✅ Estrutura de pastas
- ✅ Imagens necessárias
- ✅ Planilha RELATORIO_INVENTARIO.xlsx
- ✅ Arquivos Python
- ✅ Sistema de logs

---

## 🌐 CONFIGURAR PARA REDE

### Passo 1: Fechar o Excel
⚠️ **IMPORTANTE**: Feche completamente o Excel antes de continuar!

### Passo 2: Executar Configurador
```bash
# Clique duas vezes em:
configurar_rede.bat

# Ou execute:
python configurar_compartilhamento.py
```

### Passo 3: O que o configurador faz?
- ✅ Cria aba HISTORICO_AJUSTES (se não existir)
- ✅ Remove proteções da planilha
- ✅ Configura para acesso simultâneo
- ✅ Prepara para uso em rede

### Passo 4: Colocar em Rede
1. Copie a pasta completa para uma pasta compartilhada na rede
2. Configure permissões de leitura/escrita para todos os usuários
3. Teste primeiro com um usuário

---

## ▶️ EXECUTAR AUTOMAÇÃO

### Método 1: Interface Gráfica
```bash
# Execute:
python lancamento_inventario.py

# Ou clique duas vezes em:
Sistema_Inventario.exe
```

### Método 2: Direto (sem interface)
```bash
python automacao_totvs.py
```

### O que acontece durante a execução?
1. 📂 Carrega RELATORIO_INVENTARIO.xlsx
2. 🔍 Identifica itens pendentes (AJUSTADO ≠ SIM)
3. 🌐 Abre TOTVS via navegador (se necessário)
4. 📦 Processa cada item automaticamente
5. 💾 Atualiza planilha (CONTAGEM + HISTORICO_AJUSTES)
6. 📝 Gera log detalhado

---

## 📝 VERIFICAR LOGS

### Onde encontrar?
```
log_automacao.txt
```

### O que procurar?

#### ✅ Logs de Imagens (NOVO!)
```
🔍 DEBUG: 🖼️ Procurando imagem: +.png
🔍 DEBUG:    Caminho completo: C:\...\img\+.png
🔍 DEBUG:    Existe: True
🔍 DEBUG:    ✅ Encontrada com confiança: 0.9
```

#### ✅ Logs de Processamento
```
📦 PROCESSANDO ITEM: VK22020
   Quantidade Física: 100
   Colaborador: João Silva
   Linha Excel: 5
```

#### ✅ Logs de Atualização
```
📝 ATUALIZANDO RELATÓRIO: VK22020
✅ SUCESSO: Relatório salvo! Linha 5 marcada como AJUSTADO
✅ SUCESSO: Histórico atualizado na linha 10
```

#### ❌ Erros Comuns
```
❌ ERRO: Imagem não existe: C:\...\img\+.png
❌ ERRO: Erro de permissão: Arquivo pode estar aberto por outro usuário!
```

---

## 🔧 SOLUÇÃO DE PROBLEMAS

### Problema 1: Imagens não encontradas

**Sintoma:**
```
❌ ERRO: Imagem não existe: +.png
```

**Solução:**
1. Abra `log_automacao.txt`
2. Procure por "Caminho completo:"
3. Verifique se o caminho está correto
4. Confirme que as imagens estão na pasta `img/`

**Exemplo de verificação:**
```bash
python testar_ajustes.py
```

---

### Problema 2: Erro de permissão ao salvar

**Sintoma:**
```
❌ ERRO: Erro de permissão: Arquivo pode estar aberto por outro usuário!
```

**Solução:**
1. Verifique se alguém está EDITANDO a planilha
2. Peça para fechar ou mudar para modo visualização
3. Execute novamente a automação

**Nota:** Múltiplos usuários podem VISUALIZAR, mas apenas um pode EDITAR por vez.

---

### Problema 3: Aba HISTORICO_AJUSTES não existe

**Sintoma:**
```
⚠️ Aba HISTORICO_AJUSTES não existe
```

**Solução:**
```bash
# Execute:
python configurar_compartilhamento.py
```

Ou deixe a automação criar automaticamente na primeira execução.

---

### Problema 4: TOTVS não abre

**Sintoma:**
```
❌ ERRO: TOTVS não disponível!
```

**Solução:**
1. Verifique se o driver `msedgedriver.exe` está na pasta
2. Confirme as credenciais em `automacao_totvs.py`:
   - TOTVS_URL
   - TOTVS_LOGIN
   - TOTVS_SENHA
3. Teste abrir o TOTVS manualmente no navegador

---

### Problema 5: Dashboard não aparece

**Sintoma:**
Planilha não tem aba DASHBOARD ou gráficos

**Solução:**
```bash
# Gere uma nova planilha:
python gerar_planilha.py
```

Isso cria uma planilha de exemplo com:
- ✅ Aba CONTAGEM
- ✅ Aba DASHBOARD com gráficos melhorados
- ✅ Larguras de colunas ajustadas

---

## 📊 VERIFICAR RESULTADOS

### 1. Abrir Planilha
```
data/RELATORIO_INVENTARIO.xlsx
```

### 2. Verificar Aba CONTAGEM
- Coluna "AJUSTADO" deve estar "SIM" para itens processados
- Coluna "DATA/HORA" mostra quando foi processado
- Células em verde claro = processado com sucesso

### 3. Verificar Aba HISTORICO_AJUSTES
- Cada linha = um ajuste realizado
- Ordenado por data/hora
- Mantém histórico completo

### 4. Verificar Aba DASHBOARD (se existir)
- Gráficos maiores e mais legíveis
- Colunas mais largas
- Indicadores atualizados

---

## 💡 DICAS IMPORTANTES

### ✅ Antes de Executar
1. Feche o Excel
2. Faça backup da planilha
3. Verifique se as imagens estão na pasta `img/`
4. Confirme que o TOTVS está acessível

### ✅ Durante a Execução
1. Não mexa no mouse/teclado
2. Deixe a automação trabalhar
3. Acompanhe pelo log em tempo real

### ✅ Após a Execução
1. Verifique o log em `log_automacao.txt`
2. Confira a planilha
3. Valide alguns itens manualmente

### ✅ Em Rede
1. Configure permissões corretas
2. Teste com um usuário primeiro
3. Oriente usuários a apenas VISUALIZAR durante automação
4. Mantenha backup atualizado

---

## 📞 SUPORTE

### Arquivos de Diagnóstico
Ao reportar problemas, envie:
1. `log_automacao.txt` (log completo)
2. Print da tela de erro
3. Versão do Windows
4. Localização da pasta (local ou rede)

### Desenvolvedor
**Deivid - Faturamento**  
Versão: 2.1  
Data: 20/02/2026

---

## 🎓 RECURSOS ADICIONAIS

### Documentação Completa
- `AJUSTES_REALIZADOS.md` - Detalhes técnicos dos ajustes
- `README.md` - Documentação geral (se existir)

### Scripts Úteis
- `testar_ajustes.py` - Testa toda a estrutura
- `configurar_compartilhamento.py` - Prepara para rede
- `gerar_planilha.py` - Cria planilha de exemplo

### Arquivos Batch
- `executar_testes.bat` - Executa testes
- `configurar_rede.bat` - Configura compartilhamento

---

**🎉 Pronto! Sistema configurado e funcionando!**
