# ========================================
# SISTEMA DE INVENTÁRIO - EXPEDIÇÃO E LOGÍSTICA
# Desenvolvido por: Deivid - Faturamento
# ========================================

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
from datetime import datetime, timedelta
import os
import subprocess
import sys
import threading

# ========================================
# CORRIGIR ÍCONE NA BARRA DE TAREFAS (WINDOWS)
# ========================================
try:
    import ctypes
    # Define um ID único para o aplicativo
    # Isso faz o Windows tratar como app independente (não como Python)
    myappid = ''
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# ========================================
# DETECTAR SE ESTÁ RODANDO COMO .EXE OU .PY
# ========================================
def get_base_path():
    """Retorna o caminho base, seja rodando como .py ou .exe"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

DIR_BASE = get_base_path()
DIR_DATA = os.path.join(DIR_BASE, "data")
DIR_IMG = os.path.join(DIR_BASE, "img")
DIR_ASSETS = os.path.join(DIR_BASE, "assets")

# Criar pastas se não existirem
os.makedirs(DIR_DATA, exist_ok=True)
os.makedirs(DIR_IMG, exist_ok=True)
os.makedirs(DIR_ASSETS, exist_ok=True)

# Arquivos
ARQUIVO_RELATORIO = os.path.join(DIR_DATA, "RELATORIO_INVENTARIO.xlsx")
ARQUIVO_ITENS = os.path.join(DIR_DATA, "itens_cadastrados.xlsx")
ARQUIVO_COLABORADORES = os.path.join(DIR_DATA, "colaboradores.xlsx")
ARQUIVO_HISTORICO = os.path.join(DIR_DATA, "historico_ajustes.xlsx")

# Senhas
SENHA_PROTECAO = "719328fa"
SENHA_ADMIN = "admin123"
SENHA_PLANILHA = "719328@Fa"


class LancamentoInventario:
    def __init__(self, root):
        self.root = root
        self.root.title("SISTEMA DE INVENTÁRIO - EXPEDIÇÃO E LOGÍSTICA")
        self.root.geometry("1000x700")
        self.root.resizable(False, False)
        self.root.configure(bg='#1a1a2e')
        
        # ========================================
        # ⭐ ÍCONE CORRIGIDO - BARRA DE TAREFAS ⭐
        # ========================================
        try:
            icone_path = os.path.join(DIR_ASSETS, "icone.ico")
            if os.path.exists(icone_path):
                # Carrega o ícone na janela E na barra de tarefas
                self.root.iconbitmap(default=icone_path)
                print(f"✅ Ícone carregado: {icone_path}")
            else:
                print(f"⚠️ Arquivo de ícone não encontrado: {icone_path}")
        except Exception as e:
            print(f"⚠️ Não foi possível carregar ícone: {e}")
        # ========================================
        # ⭐ FIM DA CORREÇÃO DO ÍCONE ⭐
        # ========================================
        
        self.centralizar()
        
        self.lancamentos = []
        self.itens_cadastrados = []
        self.colaboradores = []
        
        self.carregar_itens()
        self.carregar_colaboradores()
        self.limpar_historico_mes_anterior()  # Limpa histórico do mês anterior
        self.carregar_lancamentos_existentes()
        self.criar_interface()
    
    def centralizar(self):
        self.root.update_idletasks()
        w, h = 1000, 700
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')
    
    # ========================================
    # LIMPAR HISTÓRICO DO MÊS ANTERIOR
    # ========================================
    
    def limpar_historico_mes_anterior(self):
        """Remove registros do mês anterior, mantendo apenas o mês atual"""
        if not os.path.exists(ARQUIVO_HISTORICO):
            return
        
        try:
            df = pd.read_excel(ARQUIVO_HISTORICO)
            if df.empty:
                return
            
            mes_atual = datetime.now().month
            ano_atual = datetime.now().year
            
            registros_mantidos = []
            for _, row in df.iterrows():
                data_str = str(row.get('Data', ''))
                if data_str and len(data_str) >= 10:
                    try:
                        # Tenta parsear a data (formato DD/MM/YYYY)
                        if '/' in data_str:
                            partes = data_str.split('/')
                            if len(partes) >= 3:
                                dia = int(partes[0])
                                mes = int(partes[1])
                                ano = int(partes[2][:4])
                                
                                # Mantém apenas se for do mês atual
                                if mes == mes_atual and ano == ano_atual:
                                    registros_mantidos.append(row.to_dict())
                    except:
                        pass
            
            if len(registros_mantidos) < len(df):
                df_novo = pd.DataFrame(registros_mantidos)
                df_novo.to_excel(ARQUIVO_HISTORICO, index=False)
                print(f"🗑️ Histórico limpo: {len(df) - len(registros_mantidos)} registros do mês anterior removidos")
            
        except Exception as e:
            print(f"⚠️ Erro ao limpar histórico: {e}")
    
    # ========================================
    # CARREGAR DADOS
    # ========================================
    
    def carregar_itens(self):
        if os.path.exists(ARQUIVO_ITENS):
            try:
                df = pd.read_excel(ARQUIVO_ITENS)
                self.itens_cadastrados = df['Item'].tolist()
            except:
                self.itens_cadastrados = []
        else:
            df = pd.DataFrame({'Item': [], 'Descricao': [], 'Categoria': []})
            df.to_excel(ARQUIVO_ITENS, index=False)
            self.itens_cadastrados = []
    
    def carregar_colaboradores(self):
        if os.path.exists(ARQUIVO_COLABORADORES):
            try:
                df = pd.read_excel(ARQUIVO_COLABORADORES)
                self.colaboradores = df['Nome'].tolist()
            except:
                self.colaboradores = []
        else:
            df = pd.DataFrame({'Nome': [], 'Data_Cadastro': []})
            df.to_excel(ARQUIVO_COLABORADORES, index=False)
            self.colaboradores = []
    
    def carregar_lancamentos_existentes(self):
        if os.path.exists(ARQUIVO_RELATORIO):
            try:
                df = pd.read_excel(ARQUIVO_RELATORIO, sheet_name='CONTAGEM', skiprows=3)
                print(f"📋 Colunas encontradas: {list(df.columns)}")
                
                col_map = {}
                for col in df.columns:
                    col_upper = str(col).upper().strip()
                    if col_upper == 'ITEM':
                        col_map['Item'] = col
                    elif col_upper in ['QTD_FISICA', 'QTD FÍSICA', 'QTD FISICA']:
                        col_map['Qtd_Fisica'] = col
                    elif col_upper in ['QTD_FISCAL', 'QTD FISCAL']:
                        col_map['Qtd_Fiscal'] = col
                    elif col_upper in ['DIFERENCA', 'DIFERENÇA']:
                        col_map['Diferenca'] = col
                    elif col_upper == 'STATUS':
                        col_map['Status'] = col
                    elif col_upper in ['ACURACIDADE_%', 'ACURACIDADE %', 'ACURACIDADE']:
                        col_map['Acuracidade'] = col
                    elif col_upper in ['EXCESSO_%', 'EXCESSO %', 'EXCESSO']:
                        col_map['Excesso'] = col
                    elif col_upper in ['FALTA_%', 'FALTA %', 'FALTA']:
                        col_map['Falta'] = col
                    elif col_upper == 'AJUSTADO':
                        col_map['Ajustado'] = col
                    elif col_upper == 'COLABORADOR':
                        col_map['Colaborador'] = col
                    elif col_upper in ['DATA_HORA', 'DATA/HORA']:
                        col_map['Data_Hora'] = col
                
                for _, row in df.iterrows():
                    item_col = col_map.get('Item')
                    if item_col and pd.notna(row.get(item_col)):
                        self.lancamentos.append({
                            'Item': str(row.get(item_col, '')),
                            'Qtd_Fisica': int(row.get(col_map.get('Qtd_Fisica', 'Qtd_Fisica'), 0)) if pd.notna(row.get(col_map.get('Qtd_Fisica', 'Qtd_Fisica'))) else 0,
                            'Qtd_Fiscal': int(row.get(col_map.get('Qtd_Fiscal', 'Qtd_Fiscal'), 0)) if pd.notna(row.get(col_map.get('Qtd_Fiscal', 'Qtd_Fiscal'))) else None,
                            'Diferenca': int(row.get(col_map.get('Diferenca', 'Diferenca'), 0)) if pd.notna(row.get(col_map.get('Diferenca', 'Diferenca'))) else None,
                            'Status': row.get(col_map.get('Status', 'Status'), '⏳ PENDENTE'),
                            'Acuracidade': row.get(col_map.get('Acuracidade', 'Acuracidade'), None),
                            'Excesso': row.get(col_map.get('Excesso', 'Excesso'), None),
                            'Falta': row.get(col_map.get('Falta', 'Falta'), None),
                            'Ajustado': row.get(col_map.get('Ajustado', 'Ajustado'), 'NÃO'),
                            'Colaborador': row.get(col_map.get('Colaborador', 'Colaborador'), ''),
                            'Data_Hora': row.get(col_map.get('Data_Hora', 'Data_Hora'), '')
                        })
                
                print(f"✅ {len(self.lancamentos)} lançamentos carregados")
                
            except Exception as e:
                print(f"⚠️ Erro ao carregar: {e}")
                import traceback
                traceback.print_exc()
    
    # ========================================
    # INTERFACE
    # ========================================
    
    def criar_interface(self):
        # CABEÇALHO
        header = tk.Frame(self.root, bg='#16213e', height=60)
        header.pack(fill='x', padx=5, pady=5)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="📦 SISTEMA DE INVENTÁRIO - EXPEDIÇÃO E LOGÍSTICA",
            font=('Arial', 16, 'bold'),
            fg='#00d4ff',
            bg='#16213e'
        ).pack(pady=8)
        
        tk.Label(
            header,
            text="",
            font=('Arial', 9, 'italic'),
            fg='#95a5a6',
            bg='#16213e'
        ).pack()
        
        # FRAME DE LANÇAMENTO
        frame_lanc = tk.LabelFrame(
            self.root,
            text=" LANÇAR CONTAGEM ",
            font=('Arial', 10, 'bold'),
            fg='#00d4ff',
            bg='#1a1a2e',
            padx=10,
            pady=10
        )
        frame_lanc.pack(fill='x', padx=10, pady=5)
        
        # LINHA 1
        frame_linha1 = tk.Frame(frame_lanc, bg='#1a1a2e')
        frame_linha1.pack(fill='x', pady=8)
        
        tk.Label(
            frame_linha1, 
            text="ITEM:", 
            font=('Arial', 12, 'bold'), 
            fg='white', 
            bg='#1a1a2e'
        ).pack(side='left', padx=(5, 5))
        
        self.combo_item = ttk.Combobox(frame_linha1, width=20, font=('Arial', 12))
        self.combo_item['values'] = self.itens_cadastrados
        self.combo_item.pack(side='left', padx=5)
        self.combo_item.bind('<Return>', lambda e: self.entry_qtd.focus())
        self.combo_item.bind('<KeyRelease>', self.filtrar_itens)
        
        tk.Label(
            frame_linha1, 
            text="QTD:", 
            font=('Arial', 12, 'bold'), 
            fg='white', 
            bg='#1a1a2e'
        ).pack(side='left', padx=(15, 5))
        
        self.entry_qtd = tk.Entry(
            frame_linha1, 
            width=8, 
            font=('Arial', 14, 'bold'), 
            justify='center', 
            bg='#0f3460', 
            fg='#00ff00', 
            insertbackground='white'
        )
        self.entry_qtd.pack(side='left', padx=5)
        self.entry_qtd.bind('<Return>', lambda e: self.lancar())
        
        tk.Button(
            frame_linha1, 
            text="LANÇAR", 
            font=('Arial', 11, 'bold'), 
            bg='#00b894', 
            fg='white', 
            width=10, 
            cursor='hand2', 
            command=self.lancar
        ).pack(side='left', padx=15)
        
        # COLABORADOR
        frame_colab = tk.Frame(frame_linha1, bg='#1a1a2e')
        frame_colab.pack(side='right', padx=5)
        
        tk.Label(
            frame_colab, 
            text="Colaborador:", 
            font=('Arial', 9), 
            fg='white', 
            bg='#1a1a2e'
        ).pack(side='left', padx=2)
        
        self.combo_colaborador = ttk.Combobox(frame_colab, width=15, font=('Arial', 9), state='readonly')
        self.combo_colaborador['values'] = self.colaboradores
        self.combo_colaborador.pack(side='left', padx=2)
        
        tk.Button(
            frame_colab, 
            text="Novo", 
            font=('Arial', 8), 
            bg='#3498db', 
            fg='white', 
            cursor='hand2', 
            command=self.cadastrar_colaborador
        ).pack(side='left', padx=5)
        
        # LINHA 2
        frame_linha2 = tk.Frame(frame_lanc, bg='#1a1a2e')
        frame_linha2.pack(fill='x', pady=2)
        
        tk.Label(frame_linha2, text="", width=6, bg='#1a1a2e').pack(side='left')
        
        tk.Button(
            frame_linha2, 
            text="Add Itens", 
            font=('Arial', 9), 
            bg='#9b59b6', 
            fg='white', 
            cursor='hand2', 
            command=self.cadastrar_item
        ).pack(side='left', padx=5)
        
        # TABELA
        frame_tabela = tk.Frame(self.root, bg='#1a1a2e')
        frame_tabela.pack(fill='both', expand=True, padx=10, pady=5)
        
        colunas = ('Item', 'Qtd Fís', 'Qtd Fisc', 'Dif', 'Status', 'Acur%', 'Exc%', 'Falt%', 'Colab')
        self.tree = ttk.Treeview(frame_tabela, columns=colunas, show='headings', height=12)
        
        for col in colunas:
            self.tree.heading(col, text=col.upper())
        
        self.tree.column('Item', width=110, anchor='center')
        self.tree.column('Qtd Fís', width=70, anchor='center')
        self.tree.column('Qtd Fisc', width=70, anchor='center')
        self.tree.column('Dif', width=60, anchor='center')
        self.tree.column('Status', width=110, anchor='center')
        self.tree.column('Acur%', width=70, anchor='center')
        self.tree.column('Exc%', width=65, anchor='center')
        self.tree.column('Falt%', width=65, anchor='center')
        self.tree.column('Colab', width=100, anchor='center')
        
        scrollbar = ttk.Scrollbar(frame_tabela, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Treeview', background='#0f3460', foreground='white', fieldbackground='#0f3460', font=('Arial', 9), rowheight=24)
        style.configure('Treeview.Heading', background='#16213e', foreground='white', font=('Arial', 9, 'bold'))
        
        self.tree.tag_configure('pendente', background='#f39c12', foreground='black')
        self.tree.tag_configure('ajustado', background='#27ae60', foreground='white')
        self.tree.tag_configure('excesso', background='#e74c3c', foreground='white')
        self.tree.tag_configure('falta', background='#3498db', foreground='white')
        self.tree.tag_configure('exato', background='#00b894', foreground='white')
        
        self.atualizar_tabela()
        
        # RESUMO
        frame_resumo = tk.Frame(self.root, bg='#16213e', height=35)
        frame_resumo.pack(fill='x', padx=10, pady=2)
        
        self.lbl_resumo = tk.Label(frame_resumo, text="", font=('Arial', 10, 'bold'), fg='#00d4ff', bg='#16213e')
        self.lbl_resumo.pack(pady=8)
        self.atualizar_resumo()
        
        # BOTÕES
        frame_btn = tk.Frame(self.root, bg='#1a1a2e')
        frame_btn.pack(fill='x', padx=10, pady=10)
        
        frame_btn_esquerda = tk.Frame(frame_btn, bg='#1a1a2e')
        frame_btn_esquerda.pack(side='left', expand=True)
        
        tk.Button(
            frame_btn_esquerda, 
            text="Limpar Pendentes", 
            font=('Arial', 10, 'bold'), 
            bg='#e67e22', 
            fg='white', 
            width=14, 
            cursor='hand2', 
            command=self.limpar_pendentes
        ).pack(side='left', padx=10)
        
        tk.Button(
            frame_btn_esquerda, 
            text="Limpar Concluídos", 
            font=('Arial', 10, 'bold'), 
            bg='#9b59b6', 
            fg='white', 
            width=14, 
            cursor='hand2', 
            command=self.limpar_concluidos
        ).pack(side='left', padx=10)
        
        tk.Button(
            frame_btn_esquerda, 
            text="Dashboard", 
            font=('Arial', 10, 'bold'), 
            bg='#3498db', 
            fg='white', 
            width=12, 
            cursor='hand2', 
            command=self.abrir_relatorio
        ).pack(side='left', padx=10)
        
        # START
        tk.Button(
            frame_btn, 
            text="START", 
            font=('Arial', 20, 'bold'), 
            bg='#9b59b6', 
            fg='white', 
            width=12, 
            height=2, 
            cursor='hand2', 
            command=self.iniciar_automacao
        ).pack(side='right', padx=20)
        
        # CRÉDITOS NO RODAPÉ
        frame_creditos = tk.Frame(self.root, bg='#1a1a2e')
        frame_creditos.pack(fill='x', pady=5)
        
        tk.Label(
            frame_creditos,
            text="© 2026 - Desenvolvido por Deivid - Faturamento",
            font=('Arial', 8),
            fg='#7f8c8d',
            bg='#1a1a2e'
        ).pack()
    
    def filtrar_itens(self, event):
        valor = self.combo_item.get().upper()
        if valor == '':
            self.combo_item['values'] = self.itens_cadastrados
        else:
            filtrados = [i for i in self.itens_cadastrados if valor in i.upper()]
            self.combo_item['values'] = filtrados
    
    def cadastrar_colaborador(self):
        nome = simpledialog.askstring("Novo Colaborador", "Nome do colaborador:", parent=self.root)
        if nome and nome.strip():
            nome = nome.strip().upper()
            if nome in self.colaboradores:
                messagebox.showwarning("Aviso", f"'{nome}' já existe!")
                return
            self.colaboradores.append(nome)
            df = pd.DataFrame({'Nome': self.colaboradores, 'Data_Cadastro': [datetime.now().strftime("%d/%m/%Y")] * len(self.colaboradores)})
            df.to_excel(ARQUIVO_COLABORADORES, index=False)
            self.combo_colaborador['values'] = self.colaboradores
            self.combo_colaborador.set(nome)
            messagebox.showinfo("Sucesso", f"'{nome}' cadastrado!")
    
    def cadastrar_item(self):
        senha = simpledialog.askstring("Senha Admin", "Senha:", parent=self.root, show='*')
        if senha != SENHA_ADMIN:
            messagebox.showerror("Erro", "Senha incorreta!")
            return
        
        item = simpledialog.askstring("Novo Item", "Código do item:", parent=self.root)
        if not item or not item.strip():
            return
        
        item = item.strip().upper()
        if item in self.itens_cadastrados:
            messagebox.showwarning("Aviso", f"'{item}' já existe!")
            return
        
        descricao = simpledialog.askstring("Descrição", "Descrição (opcional):", parent=self.root)
        
        self.itens_cadastrados.append(item)
        
        if os.path.exists(ARQUIVO_ITENS):
            df = pd.read_excel(ARQUIVO_ITENS)
        else:
            df = pd.DataFrame(columns=['Item', 'Descricao', 'Categoria'])
        
        nova = pd.DataFrame({'Item': [item], 'Descricao': [descricao if descricao else ''], 'Categoria': ['']})
        df = pd.concat([df, nova], ignore_index=True)
        df.to_excel(ARQUIVO_ITENS, index=False)
        
        self.combo_item['values'] = self.itens_cadastrados
        self.combo_item.set(item)
        messagebox.showinfo("Sucesso", f"'{item}' cadastrado!")
    
    def lancar(self):
        colaborador = self.combo_colaborador.get()
        item = self.combo_item.get().strip().upper()
        qtd_str = self.entry_qtd.get().strip()
        
        if not colaborador:
            messagebox.showwarning("Aviso", "Selecione colaborador!")
            return
        if not item:
            messagebox.showwarning("Aviso", "Digite o item!")
            return
        if item not in self.itens_cadastrados:
            if messagebox.askyesno("Item não existe", f"'{item}' não cadastrado. Cadastrar?"):
                self.combo_item.set(item)
                self.cadastrar_item()
            return
        if not qtd_str:
            messagebox.showwarning("Aviso", "Digite quantidade!")
            return
        
        try:
            qtd_fisica = int(qtd_str)
        except:
            messagebox.showerror("Erro", "Apenas números!")
            return
        
        if qtd_fisica < 0:
            messagebox.showerror("Erro", "Quantidade inválida!")
            return
        
        # Remover duplicado pendente
        self.lancamentos = [l for l in self.lancamentos if not (l['Item'] == item and str(l.get('Ajustado', 'NÃO')).upper().replace('✅', '').replace('❌', '').strip() != 'SIM')]
        
        self.lancamentos.append({
            'Item': item,
            'Qtd_Fisica': qtd_fisica,
            'Qtd_Fiscal': None,
            'Diferenca': None,
            'Status': '⏳ PENDENTE',
            'Acuracidade': None,
            'Excesso': None,
            'Falta': None,
            'Ajustado': 'NÃO',
            'Colaborador': colaborador,
            'Data_Hora': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        })
        
        self.atualizar_tabela()
        self.atualizar_resumo()
        self.combo_item.set('')
        self.entry_qtd.delete(0, tk.END)
        self.combo_item.focus()
    
    # ========================================
    # CÁLCULOS
    # ========================================
    
    def calcular_acuracidade(self, qtd_fisica, qtd_fiscal):
        if qtd_fiscal is None or qtd_fiscal == 0:
            return None
        if qtd_fisica == 0:
            return 0.0
        
        menor = min(qtd_fisica, qtd_fiscal)
        maior = max(qtd_fisica, qtd_fiscal)
        
        return round((menor / maior) * 100, 1)
    
    def calcular_excesso_percentual(self, diferenca, qtd_fiscal):
        if diferenca is None or qtd_fiscal is None or qtd_fiscal == 0:
            return None
        if diferenca <= 0:
            return None
        
        return round((diferenca / qtd_fiscal) * 100, 1)
    
    def calcular_falta_percentual(self, diferenca, qtd_fiscal):
        if diferenca is None or qtd_fiscal is None or qtd_fiscal == 0:
            return None
        if diferenca >= 0:
            return None
        
        return round((abs(diferenca) / qtd_fiscal) * 100, 1)
    
    def atualizar_tabela(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        for lanc in self.lancamentos:
            ajustado_raw = str(lanc.get('Ajustado', 'NÃO')).upper().replace('✅', '').replace('❌', '').strip()
            ajustado = 'SIM' if 'SIM' in ajustado_raw else 'NÃO'
            diferenca = lanc.get('Diferenca')
            qtd_fisica = lanc.get('Qtd_Fisica', 0)
            qtd_fiscal = lanc.get('Qtd_Fiscal')
            
            acuracidade = self.calcular_acuracidade(qtd_fisica, qtd_fiscal)
            excesso_perc = self.calcular_excesso_percentual(diferenca, qtd_fiscal)
            falta_perc = self.calcular_falta_percentual(diferenca, qtd_fiscal)
            
            if ajustado == 'SIM':
                status = '✅ AJUSTADO'
                tag = 'ajustado'
            elif diferenca is None:
                status = '⏳ PENDENTE'
                tag = 'pendente'
            elif diferenca == 0:
                status = '✅ EXATO'
                tag = 'exato'
            elif diferenca > 0:
                status = f'🔴 EXCESSO +{diferenca}'
                tag = 'excesso'
            else:
                status = f'🔵 FALTA {diferenca}'
                tag = 'falta'
            
            acur_str = f"{acuracidade}%" if acuracidade is not None else '-'
            exc_str = f"{excesso_perc}%" if excesso_perc is not None else '-'
            falt_str = f"{falta_perc}%" if falta_perc is not None else '-'
            
            self.tree.insert('', 'end', values=(
                lanc['Item'],
                lanc['Qtd_Fisica'],
                qtd_fiscal if qtd_fiscal is not None else '-',
                diferenca if diferenca is not None else '-',
                status,
                acur_str,
                exc_str,
                falt_str,
                lanc.get('Colaborador', '')
            ), tags=(tag,))
    
    def atualizar_resumo(self):
        total = len(self.lancamentos)
        pendentes = 0
        ajustados = 0
        
        for l in self.lancamentos:
            ajustado_raw = str(l.get('Ajustado', 'NÃO')).upper().replace('✅', '').replace('❌', '').strip()
            if 'SIM' in ajustado_raw:
                ajustados += 1
            else:
                pendentes += 1
        
        self.lbl_resumo.config(text=f"📊 Total: {total} | ⏳ Pendentes: {pendentes} | ✅ Ajustados: {ajustados}")
    
    def excluir(self):
        sel = self.tree.selection()
        if not sel:
            return
        item = self.tree.item(sel[0])['values'][0]
        self.lancamentos = [l for l in self.lancamentos if l['Item'] != item]
        self.atualizar_tabela()
        self.atualizar_resumo()
    
    def limpar_pendentes(self):
        """Remove todos os itens PENDENTES (não ajustados) - APENAS DA INTERFACE"""
        if messagebox.askyesno("Confirmar", "Limpar todos os itens PENDENTES da interface?\n\n(A planilha NÃO será alterada)"):
            novos = []
            for l in self.lancamentos:
                ajustado_raw = str(l.get('Ajustado', 'NÃO')).upper().replace('✅', '').replace('❌', '').strip()
                if 'SIM' in ajustado_raw:
                    novos.append(l)
            self.lancamentos = novos
            self.atualizar_tabela()
            self.atualizar_resumo()
            messagebox.showinfo("Sucesso", "Itens pendentes removidos da interface!")
    
    def limpar_concluidos(self):
        """Remove todos os itens CONCLUÍDOS/AJUSTADOS - APENAS DA INTERFACE"""
        if messagebox.askyesno("Confirmar", "Limpar todos os itens CONCLUÍDOS da interface?\n\n(A planilha NÃO será alterada)"):
            novos = []
            for l in self.lancamentos:
                ajustado_raw = str(l.get('Ajustado', 'NÃO')).upper().replace('✅', '').replace('❌', '').strip()
                if 'SIM' not in ajustado_raw:
                    novos.append(l)
            self.lancamentos = novos
            self.atualizar_tabela()
            self.atualizar_resumo()
            messagebox.showinfo("Sucesso", "Itens concluídos removidos da interface!")
    
    def abrir_relatorio(self):
        if os.path.exists(ARQUIVO_RELATORIO):
            os.startfile(ARQUIVO_RELATORIO)
        else:
            messagebox.showinfo("Info", "Relatório não gerado ainda!")
    
    # ========================================
    # INICIAR AUTOMAÇÃO - OTIMIZADO PARA VELOCIDADE
    # ========================================
    
    def iniciar_automacao(self):
        pendentes = []
        for l in self.lancamentos:
            ajustado_raw = str(l.get('Ajustado', 'NÃO')).upper().replace('✅', '').replace('❌', '').strip()
            if 'SIM' not in ajustado_raw:
                pendentes.append(l)
        
        print(f"\n🔍 DEBUG - Total lançamentos: {len(self.lancamentos)}")
        print(f"🔍 DEBUG - Pendentes encontrados: {len(pendentes)}")
        for p in pendentes:
            print(f"   Item: {p['Item']} | Ajustado: '{p.get('Ajustado', 'NÃO')}'")
        
        if not pendentes:
            messagebox.showinfo("Info", "Nenhum pendente!")
            return
        
        try:
            # Salva relatório em thread separada para não bloquear
            self.salvar_relatorio()
            
            # DETECTAR SE É .EXE OU .PY
            if getattr(sys, 'frozen', False):
                script = os.path.join(DIR_BASE, "Automacao_TOTVS.exe")
                if os.path.exists(script):
                    print(f"🚀 Executando: {script}")
                    # Usar START /B para execução mais rápida no Windows
                    subprocess.Popen(
                        script,
                        shell=False,
                        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
                    )
                else:
                    messagebox.showerror("Erro", f"Arquivo não encontrado:\n{script}")
                    return
            else:
                script = os.path.join(DIR_BASE, "automacao_totvs.py")
                if os.path.exists(script):
                    print(f"🚀 Executando: {script}")
                    # Execução rápida sem esperar
                    subprocess.Popen(
                        [sys.executable, script],
                        shell=False,
                        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                    )
                else:
                    messagebox.showerror("Erro", f"Arquivo não encontrado:\n{script}")
                    return
            
            # Fechar janela atual imediatamente
            self.root.destroy()
                    
        except Exception as e:
            messagebox.showerror("Erro", str(e))
    
    # ========================================
    # FUNÇÕES AUXILIARES PARA HISTÓRICO
    # ========================================
    
    def obter_semana_do_ano(self, data_str):
        """Retorna o número da semana do ano para uma data"""
        try:
            if '/' in data_str:
                partes = data_str.split('/')
                if len(partes) >= 3:
                    dia = int(partes[0])
                    mes = int(partes[1])
                    ano = int(partes[2][:4])
                    data = datetime(ano, mes, dia)
                    return data.isocalendar()[1]
        except:
            pass
        return datetime.now().isocalendar()[1]
    
    def filtrar_historico_por_periodo(self, historico, periodo='dia'):
        """Filtra histórico por período: 'dia', 'semana', 'mes'"""
        hoje = datetime.now()
        semana_atual = hoje.isocalendar()[1]
        mes_atual = hoje.month
        ano_atual = hoje.year
        dia_atual = hoje.strftime("%d/%m/%Y")
        
        filtrados = []
        
        for h in historico:
            data_str = str(h.get('Data', ''))
            if not data_str or len(data_str) < 10:
                continue
            
            try:
                if '/' in data_str:
                    partes = data_str.split('/')
                    if len(partes) >= 3:
                        dia = int(partes[0])
                        mes = int(partes[1])
                        ano = int(partes[2][:4])
                        
                        if periodo == 'dia':
                            if data_str[:10] == dia_atual:
                                filtrados.append(h)
                        elif periodo == 'semana':
                            data = datetime(ano, mes, dia)
                            if data.isocalendar()[1] == semana_atual and ano == ano_atual:
                                filtrados.append(h)
                        elif periodo == 'mes':
                            if mes == mes_atual and ano == ano_atual:
                                filtrados.append(h)
            except:
                pass
        
        return filtrados
    
    # ========================================
    # SALVAR RELATÓRIO COM DASHBOARD COMPLETO
    # ========================================
    
    def salvar_relatorio(self):
        print("💾 Salvando relatório com DASHBOARD COMPLETO...")
        
        df = pd.DataFrame(self.lancamentos)
        
        colunas = ['Item', 'Qtd_Fisica', 'Qtd_Fiscal', 'Diferenca', 'Status', 
                   'Acuracidade', 'Excesso', 'Falta', 'Ajustado', 'Colaborador', 'Data_Hora']
        for col in colunas:
            if col not in df.columns:
                df[col] = None
        df = df[colunas]
        
        # CARREGAR HISTÓRICO
        historico = []
        if os.path.exists(ARQUIVO_HISTORICO):
            try:
                df_hist = pd.read_excel(ARQUIVO_HISTORICO)
                historico = df_hist.to_dict('records')
            except:
                historico = []
        
        # Adicionar novos ajustes ao histórico
        for lanc in self.lancamentos:
            ajustado_raw = str(lanc.get('Ajustado', 'NÃO')).upper().replace('✅', '').replace('❌', '').strip()
            if 'SIM' in ajustado_raw:
                # Verificar se já existe no histórico
                item = lanc['Item']
                data_hora = lanc.get('Data_Hora', '')
                existe = False
                for h in historico:
                    if h.get('Item') == item and h.get('Data_Hora') == data_hora:
                        existe = True
                        break
                
                if not existe:
                    historico.append({
                        'Item': lanc['Item'],
                        'Qtd_Fisica': lanc['Qtd_Fisica'],
                        'Qtd_Fiscal': lanc.get('Qtd_Fiscal'),
                        'Diferenca': lanc.get('Diferenca'),
                        'Colaborador': lanc.get('Colaborador', ''),
                        'Data_Hora': lanc.get('Data_Hora', datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
                        'Data': lanc.get('Data_Hora', '')[:10] if lanc.get('Data_Hora') else datetime.now().strftime("%d/%m/%Y"),
                        'Semana': self.obter_semana_do_ano(lanc.get('Data_Hora', '')[:10] if lanc.get('Data_Hora') else datetime.now().strftime("%d/%m/%Y")),
                        'Mes': datetime.now().month,
                        'Ano': datetime.now().year
                    })
        
        if historico:
            df_historico = pd.DataFrame(historico)
            df_historico.to_excel(ARQUIVO_HISTORICO, index=False)
        
        # Filtrar históricos por período
        historico_dia = self.filtrar_historico_por_periodo(historico, 'dia')
        historico_semana = self.filtrar_historico_por_periodo(historico, 'semana')
        historico_mes = self.filtrar_historico_por_periodo(historico, 'mes')
        
        # CALCULAR INDICADORES
        total_itens = len(df)
        df_fiscal = df[df['Qtd_Fiscal'].notna()].copy()
        itens_fiscal = len(df_fiscal)
        
        total_pecas_fisicas = 0
        total_pecas_fiscais = 0
        vol_excesso = 0
        vol_falta = 0
        soma_acuracidade = 0
        qtd_com_acuracidade = 0
        
        qtd_exato = 0
        qtd_excesso = 0
        qtd_falta = 0
        
        for _, row in df.iterrows():
            qtd_fisica = row.get('Qtd_Fisica', 0) or 0
            qtd_fiscal = row.get('Qtd_Fiscal')
            
            total_pecas_fisicas += qtd_fisica
            
            if pd.notna(qtd_fiscal) and qtd_fiscal is not None:
                total_pecas_fiscais += qtd_fiscal
                diferenca = qtd_fisica - qtd_fiscal
                
                acur = self.calcular_acuracidade(qtd_fisica, qtd_fiscal)
                if acur is not None:
                    soma_acuracidade += acur
                    qtd_com_acuracidade += 1
                
                if diferenca == 0:
                    qtd_exato += 1
                elif diferenca > 0:
                    qtd_excesso += 1
                    vol_excesso += diferenca
                else:
                    qtd_falta += 1
                    vol_falta += abs(diferenca)
        
        if itens_fiscal > 0:
            perc_exato = round(qtd_exato / itens_fiscal * 100, 1)
            perc_excesso = round(qtd_excesso / itens_fiscal * 100, 1)
            perc_falta = round(qtd_falta / itens_fiscal * 100, 1)
        else:
            perc_exato = perc_excesso = perc_falta = 0
        
        if qtd_com_acuracidade > 0:
            acuracidade_media = round(soma_acuracidade / qtd_com_acuracidade, 1)
        else:
            acuracidade_media = 0
        
        divergencia_total = vol_excesso + vol_falta
        if total_pecas_fiscais > 0:
            perc_divergencia = round(divergencia_total / total_pecas_fiscais * 100, 1)
        else:
            perc_divergencia = 0
        
        qtd_ajustados = 0
        qtd_pendentes = 0
        for _, row in df.iterrows():
            ajustado_raw = str(row.get('Ajustado', 'NÃO')).upper().replace('✅', '').replace('❌', '').strip()
            if 'SIM' in ajustado_raw:
                qtd_ajustados += 1
            else:
                qtd_pendentes += 1
        
        colab_count = {}
        for lanc in self.lancamentos:
            ajustado_raw = str(lanc.get('Ajustado', 'NÃO')).upper().replace('✅', '').replace('❌', '').strip()
            if 'SIM' in ajustado_raw:
                colab = lanc.get('Colaborador', 'N/A')
                colab_count[colab] = colab_count.get(colab, 0) + 1
        
        if colab_count:
            top_colab = max(colab_count, key=colab_count.get)
            top_colab_qtd = colab_count[top_colab]
        else:
            top_colab = 'N/A'
            top_colab_qtd = 0
        
        evolucao_por_data = {}
        for h in historico:
            data = h.get('Data', '')
            if data:
                if data not in evolucao_por_data:
                    evolucao_por_data[data] = {'ajustes': 0, 'exato': 0, 'excesso': 0, 'falta': 0, 'pecas': 0}
                evolucao_por_data[data]['ajustes'] += 1
                dif = h.get('Diferenca', 0) or 0
                evolucao_por_data[data]['pecas'] += abs(dif)
                if dif == 0:
                    evolucao_por_data[data]['exato'] += 1
                elif dif > 0:
                    evolucao_por_data[data]['excesso'] += 1
                else:
                    evolucao_por_data[data]['falta'] += 1
        
        # GERAR EXCEL
        with pd.ExcelWriter(ARQUIVO_RELATORIO, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # FORMATOS
            titulo_fmt = workbook.add_format({
                'bold': True, 'font_size': 20, 'font_color': 'white',
                'bg_color': '#1a1a2e', 'align': 'center', 'valign': 'vcenter', 'border': 3
            })
            subtitulo_fmt = workbook.add_format({
                'bold': True, 'font_size': 11, 'font_color': '#00d4ff',
                'bg_color': '#16213e', 'align': 'center', 'valign': 'vcenter', 'border': 1
            })
            header_fmt = workbook.add_format({
                'bold': True, 'font_size': 10, 'font_color': 'white',
                'bg_color': '#2c3e50', 'align': 'center', 'valign': 'vcenter', 'border': 2,
                'text_wrap': True
            })
            cell_fmt = workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 10
            })
            cell_num_fmt = workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 10,
                'num_format': '#,##0'
            })
            
            green_fmt = workbook.add_format({
                'bold': True, 'font_size': 10, 'font_color': 'white',
                'bg_color': '#27ae60', 'align': 'center', 'valign': 'vcenter', 'border': 1
            })
            green_light_fmt = workbook.add_format({
                'font_size': 10, 'bg_color': '#d5f5e3', 'align': 'center', 'valign': 'vcenter', 'border': 1
            })
            red_fmt = workbook.add_format({
                'bold': True, 'font_size': 10, 'font_color': 'white',
                'bg_color': '#e74c3c', 'align': 'center', 'valign': 'vcenter', 'border': 1
            })
            red_light_fmt = workbook.add_format({
                'font_size': 10, 'bg_color': '#fadbd8', 'align': 'center', 'valign': 'vcenter', 'border': 1
            })
            blue_fmt = workbook.add_format({
                'bold': True, 'font_size': 10, 'font_color': 'white',
                'bg_color': '#3498db', 'align': 'center', 'valign': 'vcenter', 'border': 1
            })
            blue_light_fmt = workbook.add_format({
                'font_size': 10, 'bg_color': '#d6eaf8', 'align': 'center', 'valign': 'vcenter', 'border': 1
            })
            yellow_fmt = workbook.add_format({
                'bold': True, 'font_size': 10, 'font_color': 'black',
                'bg_color': '#f39c12', 'align': 'center', 'valign': 'vcenter', 'border': 1
            })
            yellow_light_fmt = workbook.add_format({
                'font_size': 10, 'bg_color': '#fdebd0', 'align': 'center', 'valign': 'vcenter', 'border': 1
            })
            purple_fmt = workbook.add_format({
                'bold': True, 'font_size': 10, 'font_color': 'white',
                'bg_color': '#9b59b6', 'align': 'center', 'valign': 'vcenter', 'border': 1
            })
            
            ind_label_fmt = workbook.add_format({
                'bold': True, 'font_size': 12, 'font_color': 'white',
                'bg_color': '#34495e', 'align': 'left', 'valign': 'vcenter', 'border': 2, 'indent': 1
            })
            ind_value_fmt = workbook.add_format({
                'bold': True, 'font_size': 16, 'font_color': '#00d4ff',
                'bg_color': '#2c3e50', 'align': 'center', 'valign': 'vcenter', 'border': 2
            })
            ind_value_green_fmt = workbook.add_format({
                'bold': True, 'font_size': 16, 'font_color': 'white',
                'bg_color': '#27ae60', 'align': 'center', 'valign': 'vcenter', 'border': 2
            })
            ind_value_red_fmt = workbook.add_format({
                'bold': True, 'font_size': 16, 'font_color': 'white',
                'bg_color': '#e74c3c', 'align': 'center', 'valign': 'vcenter', 'border': 2
            })
            ind_value_blue_fmt = workbook.add_format({
                'bold': True, 'font_size': 16, 'font_color': 'white',
                'bg_color': '#3498db', 'align': 'center', 'valign': 'vcenter', 'border': 2
            })
            ind_value_yellow_fmt = workbook.add_format({
                'bold': True, 'font_size': 16, 'font_color': 'black',
                'bg_color': '#f39c12', 'align': 'center', 'valign': 'vcenter', 'border': 2
            })
            ind_value_purple_fmt = workbook.add_format({
                'bold': True, 'font_size': 16, 'font_color': 'white',
                'bg_color': '#9b59b6', 'align': 'center', 'valign': 'vcenter', 'border': 2
            })
            
            secao_fmt = workbook.add_format({
                'bold': True, 'font_size': 13, 'font_color': 'white',
                'bg_color': '#1a1a2e', 'align': 'center', 'valign': 'vcenter', 'border': 2
            })
            
            dev_fmt = workbook.add_format({
                'italic': True, 'font_size': 9, 'font_color': '#95a5a6',
                'bg_color': '#16213e', 'align': 'center', 'valign': 'vcenter', 'border': 1
            })
            
            # ========================================
            # ABA CONTAGEM
            # ========================================
            ws1 = workbook.add_worksheet('CONTAGEM')
            
            ws1.merge_range('A1:K1', '📦 RELATÓRIO DE INVENTÁRIO - EXPEDIÇÃO E LOGÍSTICA', titulo_fmt)
            ws1.merge_range('A2:K2', f'Gerado em: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")} | Desenvolvido por: Deivid - Faturamento', subtitulo_fmt)
            ws1.merge_range('A3:K3', f'Total: {total_itens} itens | Ajustados: {qtd_ajustados} | Pendentes: {qtd_pendentes} | Acuracidade Média: {acuracidade_media}%', subtitulo_fmt)
            
            ws1.set_row(0, 40)
            ws1.set_row(1, 22)
            ws1.set_row(2, 22)
            ws1.set_row(3, 28)
            
            header_names = ['ITEM', 'QTD FÍSICA', 'QTD FISCAL', 'DIFERENÇA', 'STATUS', 
                           'ACURACIDADE %', 'EXCESSO %', 'FALTA %', 'AJUSTADO', 'COLABORADOR', 'DATA/HORA']
            
            for col, h in enumerate(header_names):
                ws1.write(3, col, h, header_fmt)
            
            ws1.set_column('A:A', 14)
            ws1.set_column('B:D', 12)
            ws1.set_column('E:E', 16)
            ws1.set_column('F:H', 12)
            ws1.set_column('I:I', 11)
            ws1.set_column('J:J', 14)
            ws1.set_column('K:K', 18)
            
            for row_idx, lanc in enumerate(self.lancamentos):
                row = row_idx + 4
                ws1.set_row(row, 22)
                
                ajustado_raw = str(lanc.get('Ajustado', 'NÃO')).upper().replace('✅', '').replace('❌', '').strip()
                ajustado = 'SIM' if 'SIM' in ajustado_raw else 'NÃO'
                
                qtd_fisica = lanc.get('Qtd_Fisica', 0) or 0
                qtd_fiscal = lanc.get('Qtd_Fiscal')
                
                if qtd_fiscal is not None:
                    diferenca = qtd_fisica - qtd_fiscal
                    acuracidade = self.calcular_acuracidade(qtd_fisica, qtd_fiscal)
                    excesso_perc = self.calcular_excesso_percentual(diferenca, qtd_fiscal)
                    falta_perc = self.calcular_falta_percentual(diferenca, qtd_fiscal)
                else:
                    diferenca = None
                    acuracidade = None
                    excesso_perc = None
                    falta_perc = None
                
                if ajustado == 'SIM':
                    row_fmt = green_light_fmt
                elif diferenca is None:
                    row_fmt = yellow_light_fmt
                elif diferenca == 0:
                    row_fmt = green_light_fmt
                elif diferenca > 0:
                    row_fmt = red_light_fmt
                else:
                    row_fmt = blue_light_fmt
                
                ws1.write(row, 0, lanc.get('Item', ''), row_fmt)
                ws1.write(row, 1, qtd_fisica, row_fmt)
                ws1.write(row, 2, qtd_fiscal if qtd_fiscal is not None else '', row_fmt)
                ws1.write(row, 3, diferenca if diferenca is not None else '', row_fmt)
                
                if ajustado == 'SIM':
                    ws1.write(row, 4, 'AJUSTADO', green_fmt)
                elif diferenca is None:
                    ws1.write(row, 4, 'PENDENTE', yellow_fmt)
                elif diferenca == 0:
                    ws1.write(row, 4, 'EXATO', green_fmt)
                elif diferenca > 0:
                    ws1.write(row, 4, f'EXCESSO +{diferenca}', red_fmt)
                else:
                    ws1.write(row, 4, f'FALTA {diferenca}', blue_fmt)
                
                if acuracidade is not None:
                    if acuracidade >= 95:
                        ws1.write(row, 5, f'{acuracidade}%', green_fmt)
                    elif acuracidade >= 80:
                        ws1.write(row, 5, f'{acuracidade}%', yellow_fmt)
                    else:
                        ws1.write(row, 5, f'{acuracidade}%', red_fmt)
                else:
                    ws1.write(row, 5, '', row_fmt)
                
                if excesso_perc is not None:
                    ws1.write(row, 6, f'{excesso_perc}%', red_fmt)
                else:
                    ws1.write(row, 6, '-', row_fmt)
                
                if falta_perc is not None:
                    ws1.write(row, 7, f'{falta_perc}%', blue_fmt)
                else:
                    ws1.write(row, 7, '-', row_fmt)
                
                if ajustado == 'SIM':
                    ws1.write(row, 8, 'SIM', green_fmt)
                else:
                    ws1.write(row, 8, 'NÃO', yellow_fmt)
                
                ws1.write(row, 9, lanc.get('Colaborador', ''), row_fmt)
                ws1.write(row, 10, lanc.get('Data_Hora', ''), row_fmt)
            
            ws1.freeze_panes(4, 0)
            
            # ⭐ PROTEGER ABA CONTAGEM COM SENHA
            ws1.protect(SENHA_PLANILHA)
            
            # ========================================
            # ABA DASHBOARD
            # ========================================
            ws2 = workbook.add_worksheet('DASHBOARD')
            
            ws2.merge_range('A1:P1', '📊 DASHBOARD - EXPEDIÇÃO E LOGÍSTICA', titulo_fmt)
            ws2.merge_range('A2:P2', f'Última atualização: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")} | Desenvolvido por: Deivid - Faturamento', subtitulo_fmt)
            
            ws2.set_row(0, 50)
            ws2.set_row(1, 25)
            
            ws2.set_column('A:A', 3)
            ws2.set_column('B:B', 26)
            ws2.set_column('C:C', 16)
            ws2.set_column('D:D', 3)
            ws2.set_column('E:E', 26)
            ws2.set_column('F:F', 16)
            ws2.set_column('G:G', 3)
            ws2.set_column('H:H', 18)
            ws2.set_column('I:P', 12)
            
            # INDICADORES
            ws2.merge_range('B4:F4', '📈 INDICADORES PRINCIPAIS DE ESTOQUE', secao_fmt)
            ws2.set_row(3, 30)
            
            row = 5
            ws2.write(row, 1, 'TOTAL DE ITENS', ind_label_fmt)
            ws2.write(row, 2, total_itens, ind_value_fmt)
            ws2.set_row(row, 32)
            
            row += 1
            ws2.write(row, 1, 'ACURACIDADE MÉDIA', ind_label_fmt)
            fmt = ind_value_green_fmt if acuracidade_media >= 95 else (ind_value_yellow_fmt if acuracidade_media >= 80 else ind_value_red_fmt)
            ws2.write(row, 2, f'{acuracidade_media}%', fmt)
            ws2.set_row(row, 32)
            
            row += 1
            ws2.write(row, 1, 'ITENS EXATOS (100%)', ind_label_fmt)
            ws2.write(row, 2, f'{qtd_exato} ({perc_exato}%)', ind_value_green_fmt)
            ws2.set_row(row, 32)
            
            row += 1
            ws2.write(row, 1, 'ITENS COM EXCESSO', ind_label_fmt)
            ws2.write(row, 2, f'{qtd_excesso} ({perc_excesso}%)', ind_value_red_fmt)
            ws2.set_row(row, 32)
            
            row += 1
            ws2.write(row, 1, 'ITENS COM FALTA', ind_label_fmt)
            ws2.write(row, 2, f'{qtd_falta} ({perc_falta}%)', ind_value_blue_fmt)
            ws2.set_row(row, 32)
            
            row = 5
            ws2.write(row, 4, 'ITENS AJUSTADOS', ind_label_fmt)
            ws2.write(row, 5, qtd_ajustados, ind_value_green_fmt)
            
            row += 1
            ws2.write(row, 4, 'ITENS PENDENTES', ind_label_fmt)
            ws2.write(row, 5, qtd_pendentes, ind_value_yellow_fmt)
            
            row += 1
            ws2.write(row, 4, 'VOLUME EXCESSO (pcs)', ind_label_fmt)
            ws2.write(row, 5, f'{vol_excesso:,}'.replace(',', '.'), ind_value_red_fmt)
            
            row += 1
            ws2.write(row, 4, 'VOLUME FALTA (pcs)', ind_label_fmt)
            ws2.write(row, 5, f'{vol_falta:,}'.replace(',', '.'), ind_value_blue_fmt)
            
            row += 1
            ws2.write(row, 4, 'TOP COLABORADOR', ind_label_fmt)
            ws2.write(row, 5, f'{top_colab} ({top_colab_qtd})', ind_value_purple_fmt)
            
            # MÉTRICAS LOGÍSTICA
            ws2.merge_range('B12:F12', '🚚 MÉTRICAS DE EXPEDIÇÃO E LOGÍSTICA', secao_fmt)
            ws2.set_row(11, 30)
            
            row = 13
            ws2.write(row, 1, 'TOTAL PEÇAS FÍSICAS', ind_label_fmt)
            ws2.write(row, 2, f'{total_pecas_fisicas:,}'.replace(',', '.'), ind_value_fmt)
            ws2.set_row(row, 32)
            
            row += 1
            ws2.write(row, 1, 'TOTAL PEÇAS FISCAIS', ind_label_fmt)
            ws2.write(row, 2, f'{total_pecas_fiscais:,}'.replace(',', '.'), ind_value_fmt)
            ws2.set_row(row, 32)
            
            row += 1
            ws2.write(row, 1, 'DIVERGÊNCIA TOTAL (pcs)', ind_label_fmt)
            fmt = ind_value_green_fmt if divergencia_total == 0 else ind_value_red_fmt
            ws2.write(row, 2, f'{divergencia_total:,}'.replace(',', '.'), fmt)
            ws2.set_row(row, 32)
            
            row += 1
            ws2.write(row, 1, 'DIVERGÊNCIA %', ind_label_fmt)
            fmt = ind_value_green_fmt if perc_divergencia < 5 else (ind_value_yellow_fmt if perc_divergencia < 10 else ind_value_red_fmt)
            ws2.write(row, 2, f'{perc_divergencia}%', fmt)
            ws2.set_row(row, 32)
            
            row = 13
            ws2.write(row, 4, 'TAXA DE AJUSTE', ind_label_fmt)
            taxa_ajuste = round(qtd_ajustados / total_itens * 100, 1) if total_itens > 0 else 0
            ws2.write(row, 5, f'{taxa_ajuste}%', ind_value_green_fmt if taxa_ajuste >= 80 else ind_value_yellow_fmt)
            
            row += 1
            ws2.write(row, 4, 'EFICIÊNCIA CONTAGEM', ind_label_fmt)
            eficiencia = round((qtd_exato + qtd_ajustados) / total_itens * 100, 1) if total_itens > 0 else 0
            ws2.write(row, 5, f'{eficiencia}%', ind_value_green_fmt if eficiencia >= 90 else ind_value_yellow_fmt)
            
            row += 1
            ws2.write(row, 4, 'ITENS POR HORA (EST)', ind_label_fmt)
            itens_hora = round(qtd_ajustados / 8, 1) if qtd_ajustados > 0 else 0
            ws2.write(row, 5, f'{itens_hora}', ind_value_fmt)
            
            row += 1
            ws2.write(row, 4, 'PEÇAS POR ITEM (MÉD)', ind_label_fmt)
            pecas_item = round(total_pecas_fisicas / total_itens, 1) if total_itens > 0 else 0
            ws2.write(row, 5, f'{pecas_item}', ind_value_fmt)
            
            # GRÁFICOS
            vol_data_row = 5
            ws2.write(vol_data_row, 7, 'TIPO', header_fmt)
            ws2.write(vol_data_row, 8, 'PEÇAS', header_fmt)
            ws2.write(vol_data_row + 1, 7, 'EXCESSO', red_fmt)
            ws2.write(vol_data_row + 1, 8, vol_excesso, cell_num_fmt)
            ws2.write(vol_data_row + 2, 7, 'FALTA', blue_fmt)
            ws2.write(vol_data_row + 2, 8, vol_falta, cell_num_fmt)
            
            vol_chart = workbook.add_chart({'type': 'line'})
            vol_chart.add_series({
                'name': 'Excesso',
                'categories': '=DASHBOARD!$H$6',
                'values': '=DASHBOARD!$I$6',
                'line': {'color': '#e74c3c', 'width': 3},
                'marker': {'type': 'circle', 'size': 10, 'fill': {'color': '#e74c3c'}},
                'data_labels': {'value': True, 'font': {'bold': True, 'size': 11, 'color': '#e74c3c'}}
            })
            vol_chart.add_series({
                'name': 'Falta',
                'categories': '=DASHBOARD!$H$7',
                'values': '=DASHBOARD!$I$7',
                'line': {'color': '#3498db', 'width': 3},
                'marker': {'type': 'circle', 'size': 10, 'fill': {'color': '#3498db'}},
                'data_labels': {'value': True, 'font': {'bold': True, 'size': 11, 'color': '#3498db'}}
            })
            vol_chart.set_title({'name': 'VOLUME DE DIVERGÊNCIAS', 'name_font': {'bold': True, 'size': 11}})
            vol_chart.set_style(10)
            vol_chart.set_legend({'position': 'bottom'})
            vol_chart.set_size({'width': 320, 'height': 180})
            ws2.insert_chart('L6', vol_chart)
            
            status_data_row = 10
            ws2.write(status_data_row, 7, 'STATUS', header_fmt)
            ws2.write(status_data_row, 8, 'QTD', header_fmt)
            ws2.write(status_data_row + 1, 7, 'EXATO', green_fmt)
            ws2.write(status_data_row + 1, 8, qtd_exato, cell_fmt)
            ws2.write(status_data_row + 2, 7, 'EXCESSO', red_fmt)
            ws2.write(status_data_row + 2, 8, qtd_excesso, cell_fmt)
            ws2.write(status_data_row + 3, 7, 'FALTA', blue_fmt)
            ws2.write(status_data_row + 3, 8, qtd_falta, cell_fmt)
            
            status_chart = workbook.add_chart({'type': 'line'})
            status_chart.add_series({
                'name': 'Exato',
                'categories': '=DASHBOARD!$H$11',
                'values': '=DASHBOARD!$I$11',
                'line': {'color': '#27ae60', 'width': 3},
                'marker': {'type': 'diamond', 'size': 10, 'fill': {'color': '#27ae60'}},
                'data_labels': {'value': True, 'font': {'bold': True, 'size': 10, 'color': '#27ae60'}}
            })
            status_chart.add_series({
                'name': 'Excesso',
                'categories': '=DASHBOARD!$H$12',
                'values': '=DASHBOARD!$I$12',
                'line': {'color': '#e74c3c', 'width': 3},
                'marker': {'type': 'square', 'size': 10, 'fill': {'color': '#e74c3c'}},
                'data_labels': {'value': True, 'font': {'bold': True, 'size': 10, 'color': '#e74c3c'}}
            })
            status_chart.add_series({
                'name': 'Falta',
                'categories': '=DASHBOARD!$H$13',
                'values': '=DASHBOARD!$I$13',
                'line': {'color': '#3498db', 'width': 3},
                'marker': {'type': 'triangle', 'size': 10, 'fill': {'color': '#3498db'}},
                'data_labels': {'value': True, 'font': {'bold': True, 'size': 10, 'color': '#3498db'}}
            })
            status_chart.set_title({'name': 'DISTRIBUIÇÃO POR STATUS', 'name_font': {'bold': True, 'size': 11}})
            status_chart.set_style(10)
            status_chart.set_legend({'position': 'bottom'})
            status_chart.set_size({'width': 320, 'height': 200})
            ws2.insert_chart('L14', status_chart)
            
            # EVOLUÇÃO DIÁRIA
            evol_row = 20
            ws2.merge_range(evol_row, 1, evol_row, 6, '📅 EVOLUÇÃO DIÁRIA DE AJUSTES', secao_fmt)
            ws2.set_row(evol_row, 28)
            
            evol_row += 2
            ws2.write(evol_row, 1, 'DATA', header_fmt)
            ws2.write(evol_row, 2, 'AJUSTES', header_fmt)
            ws2.write(evol_row, 3, 'EXATOS', header_fmt)
            ws2.write(evol_row, 4, 'EXCESSO', header_fmt)
            ws2.write(evol_row, 5, 'FALTA', header_fmt)
            ws2.write(evol_row, 6, 'PEÇAS', header_fmt)
            
            datas_ordenadas = sorted(evolucao_por_data.keys())
            for i, data in enumerate(datas_ordenadas[-10:]):
                dados = evolucao_por_data[data]
                ws2.write(evol_row + 1 + i, 1, data, cell_fmt)
                ws2.write(evol_row + 1 + i, 2, dados['ajustes'], purple_fmt)
                ws2.write(evol_row + 1 + i, 3, dados['exato'], green_fmt)
                ws2.write(evol_row + 1 + i, 4, dados['excesso'], red_fmt)
                ws2.write(evol_row + 1 + i, 5, dados['falta'], blue_fmt)
                ws2.write(evol_row + 1 + i, 6, dados['pecas'], cell_num_fmt)
            
            if len(datas_ordenadas) > 0:
                num_datas = min(len(datas_ordenadas), 10)
                evol_chart = workbook.add_chart({'type': 'line'})
                evol_chart.add_series({
                    'name': 'Ajustes',
                    'categories': f'=DASHBOARD!$B${evol_row + 2}:$B${evol_row + 1 + num_datas}',
                    'values': f'=DASHBOARD!$C${evol_row + 2}:$C${evol_row + 1 + num_datas}',
                    'line': {'color': '#9b59b6', 'width': 2.5},
                    'marker': {'type': 'circle', 'size': 7, 'fill': {'color': '#9b59b6'}}
                })
                evol_chart.add_series({
                    'name': 'Exatos',
                    'categories': f'=DASHBOARD!$B${evol_row + 2}:$B${evol_row + 1 + num_datas}',
                    'values': f'=DASHBOARD!$D${evol_row + 2}:$D${evol_row + 1 + num_datas}',
                    'line': {'color': '#27ae60', 'width': 2},
                    'marker': {'type': 'diamond', 'size': 6, 'fill': {'color': '#27ae60'}}
                })
                evol_chart.add_series({
                    'name': 'Excesso',
                    'categories': f'=DASHBOARD!$B${evol_row + 2}:$B${evol_row + 1 + num_datas}',
                    'values': f'=DASHBOARD!$E${evol_row + 2}:$E${evol_row + 1 + num_datas}',
                    'line': {'color': '#e74c3c', 'width': 2},
                    'marker': {'type': 'square', 'size': 6, 'fill': {'color': '#e74c3c'}}
                })
                evol_chart.add_series({
                    'name': 'Falta',
                    'categories': f'=DASHBOARD!$B${evol_row + 2}:$B${evol_row + 1 + num_datas}',
                    'values': f'=DASHBOARD!$F${evol_row + 2}:$F${evol_row + 1 + num_datas}',
                    'line': {'color': '#3498db', 'width': 2},
                    'marker': {'type': 'triangle', 'size': 6, 'fill': {'color': '#3498db'}}
                })
                evol_chart.set_title({'name': 'EVOLUÇÃO DIÁRIA', 'name_font': {'bold': True, 'size': 10}})
                evol_chart.set_style(10)
                evol_chart.set_legend({'position': 'bottom'})
                evol_chart.set_size({'width': 320, 'height': 280})
                ws2.insert_chart('L21', evol_chart)
            
            # RANKING
            rank_row = 38
            ws2.merge_range(rank_row, 1, rank_row, 5, '🏆 RANKING DE COLABORADORES', secao_fmt)
            ws2.set_row(rank_row, 28)
            
            rank_row += 2
            ws2.write(rank_row, 1, 'POS', header_fmt)
            ws2.write(rank_row, 2, 'COLABORADOR', header_fmt)
            ws2.write(rank_row, 3, 'AJUSTES', header_fmt)
            ws2.write(rank_row, 4, '%', header_fmt)
            ws2.write(rank_row, 5, 'MÉDIA/DIA', header_fmt)
            
            if colab_count:
                ranking = sorted(colab_count.items(), key=lambda x: x[1], reverse=True)
                for i, (colab, qtd) in enumerate(ranking[:10]):
                    perc = round(qtd / qtd_ajustados * 100, 1) if qtd_ajustados > 0 else 0
                    media_dia = round(qtd / max(len(evolucao_por_data), 1), 1)
                    
                    if i == 0:
                        pos_fmt = green_fmt
                        medalha = '🥇'
                    elif i == 1:
                        pos_fmt = blue_fmt
                        medalha = '🥈'
                    elif i == 2:
                        pos_fmt = yellow_fmt
                        medalha = '🥉'
                    else:
                        pos_fmt = cell_fmt
                        medalha = f'{i+1}º'
                    
                    ws2.write(rank_row + 1 + i, 1, medalha, pos_fmt)
                    ws2.write(rank_row + 1 + i, 2, colab, cell_fmt)
                    ws2.write(rank_row + 1 + i, 3, qtd, purple_fmt)
                    ws2.write(rank_row + 1 + i, 4, f'{perc}%', cell_fmt)
                    ws2.write(rank_row + 1 + i, 5, media_dia, cell_fmt)
            
            # ========================================
            # 📋 ÚLTIMOS AJUSTES REALIZADOS (HOJE)
            # ========================================
            hist_row = 52
            hist_col = 1
            ws2.merge_range(hist_row, hist_col, hist_row, hist_col + 6, '📋 ÚLTIMOS AJUSTES REALIZADOS (HOJE)', secao_fmt)
            ws2.set_row(hist_row, 28)
            
            hist_row += 2
            ws2.write(hist_row, hist_col, 'DATA/HORA', header_fmt)
            ws2.write(hist_row, hist_col + 1, 'ITEM', header_fmt)
            ws2.write(hist_row, hist_col + 2, 'FÍSICA', header_fmt)
            ws2.write(hist_row, hist_col + 3, 'FISCAL', header_fmt)
            ws2.write(hist_row, hist_col + 4, 'DIF', header_fmt)
            ws2.write(hist_row, hist_col + 5, 'ACUR%', header_fmt)
            ws2.write(hist_row, hist_col + 6, 'COLAB', header_fmt)
            
            ultimos_dia = historico_dia[-10:] if len(historico_dia) > 10 else historico_dia
            ultimos_dia_rev = list(reversed(ultimos_dia))
            
            for i, h in enumerate(ultimos_dia_rev):
                qtd_f = h.get('Qtd_Fisica', 0) or 0
                qtd_c = h.get('Qtd_Fiscal', 0) or 0
                dif = h.get('Diferenca', 0) or 0
                acur = self.calcular_acuracidade(qtd_f, qtd_c)
                
                if dif == 0:
                    fmt = green_light_fmt
                elif dif > 0:
                    fmt = red_light_fmt
                else:
                    fmt = blue_light_fmt
                
                ws2.write(hist_row + 1 + i, hist_col, h.get('Data_Hora', ''), fmt)
                ws2.write(hist_row + 1 + i, hist_col + 1, h.get('Item', ''), fmt)
                ws2.write(hist_row + 1 + i, hist_col + 2, qtd_f, fmt)
                ws2.write(hist_row + 1 + i, hist_col + 3, qtd_c, fmt)
                ws2.write(hist_row + 1 + i, hist_col + 4, dif, fmt)
                
                if acur is not None:
                    if acur >= 95:
                        ws2.write(hist_row + 1 + i, hist_col + 5, f'{acur}%', green_fmt)
                    elif acur >= 80:
                        ws2.write(hist_row + 1 + i, hist_col + 5, f'{acur}%', yellow_fmt)
                    else:
                        ws2.write(hist_row + 1 + i, hist_col + 5, f'{acur}%', red_fmt)
                else:
                    ws2.write(hist_row + 1 + i, hist_col + 5, '-', fmt)
                
                ws2.write(hist_row + 1 + i, hist_col + 6, h.get('Colaborador', ''), fmt)
            
            # ========================================
            # 📋 ÚLTIMOS AJUSTES SEMANAL
            # ========================================
            sem_row = 52
            sem_col = 9
            ws2.merge_range(sem_row, sem_col, sem_row, sem_col + 6, '📋 AJUSTES DA SEMANA', secao_fmt)
            ws2.set_row(sem_row, 28)
            
            sem_row += 2
            ws2.write(sem_row, sem_col, 'DATA/HORA', header_fmt)
            ws2.write(sem_row, sem_col + 1, 'ITEM', header_fmt)
            ws2.write(sem_row, sem_col + 2, 'FÍSICA', header_fmt)
            ws2.write(sem_row, sem_col + 3, 'FISCAL', header_fmt)
            ws2.write(sem_row, sem_col + 4, 'DIF', header_fmt)
            ws2.write(sem_row, sem_col + 5, 'ACUR%', header_fmt)
            ws2.write(sem_row, sem_col + 6, 'COLAB', header_fmt)
            
            ultimos_semana = historico_semana[-15:] if len(historico_semana) > 15 else historico_semana
            ultimos_semana_rev = list(reversed(ultimos_semana))
            
            for i, h in enumerate(ultimos_semana_rev):
                qtd_f = h.get('Qtd_Fisica', 0) or 0
                qtd_c = h.get('Qtd_Fiscal', 0) or 0
                dif = h.get('Diferenca', 0) or 0
                acur = self.calcular_acuracidade(qtd_f, qtd_c)
                
                if dif == 0:
                    fmt = green_light_fmt
                elif dif > 0:
                    fmt = red_light_fmt
                else:
                    fmt = blue_light_fmt
                
                ws2.write(sem_row + 1 + i, sem_col, h.get('Data_Hora', ''), fmt)
                ws2.write(sem_row + 1 + i, sem_col + 1, h.get('Item', ''), fmt)
                ws2.write(sem_row + 1 + i, sem_col + 2, qtd_f, fmt)
                ws2.write(sem_row + 1 + i, sem_col + 3, qtd_c, fmt)
                ws2.write(sem_row + 1 + i, sem_col + 4, dif, fmt)
                
                if acur is not None:
                    if acur >= 95:
                        ws2.write(sem_row + 1 + i, sem_col + 5, f'{acur}%', green_fmt)
                    elif acur >= 80:
                        ws2.write(sem_row + 1 + i, sem_col + 5, f'{acur}%', yellow_fmt)
                    else:
                        ws2.write(sem_row + 1 + i, sem_col + 5, f'{acur}%', red_fmt)
                else:
                    ws2.write(sem_row + 1 + i, sem_col + 5, '-', fmt)
                
                ws2.write(sem_row + 1 + i, sem_col + 6, h.get('Colaborador', ''), fmt)
            
            # ========================================
            # 📋 RESUMO MENSAL
            # ========================================
            mes_row = 70
            mes_col = 1
            mes_nome = datetime.now().strftime("%B/%Y").upper()
            ws2.merge_range(mes_row, mes_col, mes_row, mes_col + 6, f'📋 RESUMO DO MÊS ({mes_nome})', secao_fmt)
            ws2.set_row(mes_row, 28)
            
            mes_row += 2
            total_mes = len(historico_mes)
            exatos_mes = len([h for h in historico_mes if (h.get('Diferenca', 0) or 0) == 0])
            excesso_mes = len([h for h in historico_mes if (h.get('Diferenca', 0) or 0) > 0])
            falta_mes = len([h for h in historico_mes if (h.get('Diferenca', 0) or 0) < 0])
            
            ws2.write(mes_row, mes_col, 'TOTAL AJUSTES MÊS', ind_label_fmt)
            ws2.write(mes_row, mes_col + 1, total_mes, ind_value_purple_fmt)
            
            ws2.write(mes_row + 1, mes_col, 'EXATOS NO MÊS', ind_label_fmt)
            ws2.write(mes_row + 1, mes_col + 1, exatos_mes, ind_value_green_fmt)
            
            ws2.write(mes_row + 2, mes_col, 'EXCESSO NO MÊS', ind_label_fmt)
            ws2.write(mes_row + 2, mes_col + 1, excesso_mes, ind_value_red_fmt)
            
            ws2.write(mes_row + 3, mes_col, 'FALTA NO MÊS', ind_label_fmt)
            ws2.write(mes_row + 3, mes_col + 1, falta_mes, ind_value_blue_fmt)
            
            # RODAPÉ
            footer_row = 80
            ws2.merge_range(footer_row, 0, footer_row, 15, 
                          '© 2026 - Sistema de Inventário - Expedição e Logística | Desenvolvido por: Deivid - Faturamento', 
                          dev_fmt)
            
            # ⭐ PROTEGER ABA DASHBOARD COM SENHA
            ws2.protect(SENHA_PLANILHA)
            
            # ========================================
            # ABA HISTÓRICO DE AJUSTES
            # ========================================
            ws3 = workbook.add_worksheet('HISTORICO_AJUSTES')
            
            ws3.merge_range('A1:L1', '📋 HISTÓRICO COMPLETO DE AJUSTES - MÊS ATUAL', titulo_fmt)
            ws3.merge_range('A2:L2', f'Mês: {datetime.now().strftime("%B/%Y").upper()} | Gerado em: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}', subtitulo_fmt)
            
            ws3.set_row(0, 40)
            ws3.set_row(1, 25)
            ws3.set_row(2, 28)
            
            # Cabeçalhos
            hist_headers = ['DATA', 'HORA', 'ITEM', 'QTD FÍSICA', 'QTD FISCAL', 'DIFERENÇA', 
                           'STATUS', 'ACURACIDADE %', 'COLABORADOR', 'SEMANA', 'DIA DA SEMANA']
            
            for col, h in enumerate(hist_headers):
                ws3.write(2, col, h, header_fmt)
            
            ws3.set_column('A:A', 12)
            ws3.set_column('B:B', 10)
            ws3.set_column('C:C', 14)
            ws3.set_column('D:F', 12)
            ws3.set_column('G:G', 14)
            ws3.set_column('H:H', 14)
            ws3.set_column('I:I', 16)
            ws3.set_column('J:J', 10)
            ws3.set_column('K:K', 14)
            
            # Ordenar histórico do mês por data (mais recente primeiro)
            historico_mes_ordenado = sorted(historico_mes, key=lambda x: x.get('Data_Hora', ''), reverse=True)
            
            dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            
            for i, h in enumerate(historico_mes_ordenado):
                row = i + 3
                
                data_hora = h.get('Data_Hora', '')
                data = data_hora[:10] if len(data_hora) >= 10 else ''
                hora = data_hora[11:19] if len(data_hora) >= 19 else ''
                
                qtd_f = h.get('Qtd_Fisica', 0) or 0
                qtd_c = h.get('Qtd_Fiscal', 0) or 0
                dif = h.get('Diferenca', 0) or 0
                acur = self.calcular_acuracidade(qtd_f, qtd_c)
                
                # Determinar dia da semana
                dia_semana = ''
                semana_num = ''
                try:
                    if '/' in data:
                        partes = data.split('/')
                        if len(partes) >= 3:
                            dt = datetime(int(partes[2][:4]), int(partes[1]), int(partes[0]))
                            dia_semana = dias_semana[dt.weekday()]
                            semana_num = str(dt.isocalendar()[1])
                except:
                    pass
                
                # Determinar status e formato
                if dif == 0:
                    status = 'EXATO'
                    fmt = green_light_fmt
                    status_fmt = green_fmt
                elif dif > 0:
                    status = f'EXCESSO +{dif}'
                    fmt = red_light_fmt
                    status_fmt = red_fmt
                else:
                    status = f'FALTA {dif}'
                    fmt = blue_light_fmt
                    status_fmt = blue_fmt
                
                ws3.write(row, 0, data, fmt)
                ws3.write(row, 1, hora, fmt)
                ws3.write(row, 2, h.get('Item', ''), fmt)
                ws3.write(row, 3, qtd_f, fmt)
                ws3.write(row, 4, qtd_c, fmt)
                ws3.write(row, 5, dif, fmt)
                ws3.write(row, 6, status, status_fmt)
                
                if acur is not None:
                    if acur >= 95:
                        ws3.write(row, 7, f'{acur}%', green_fmt)
                    elif acur >= 80:
                        ws3.write(row, 7, f'{acur}%', yellow_fmt)
                    else:
                        ws3.write(row, 7, f'{acur}%', red_fmt)
                else:
                    ws3.write(row, 7, '-', fmt)
                
                ws3.write(row, 8, h.get('Colaborador', ''), fmt)
                ws3.write(row, 9, semana_num, fmt)
                ws3.write(row, 10, dia_semana, fmt)
            
            ws3.freeze_panes(3, 0)
            
            # ⭐ PROTEGER ABA HISTÓRICO COM SENHA
            ws3.protect(SENHA_PLANILHA)
            
            # Resumo no final da aba histórico
            resumo_row = len(historico_mes_ordenado) + 5
            ws3.merge_range(resumo_row, 0, resumo_row, 4, '📊 RESUMO DO MÊS', secao_fmt)
            
            ws3.write(resumo_row + 2, 0, 'Total de Ajustes:', ind_label_fmt)
            ws3.write(resumo_row + 2, 1, len(historico_mes), ind_value_purple_fmt)
            
            ws3.write(resumo_row + 3, 0, 'Itens Exatos:', ind_label_fmt)
            ws3.write(resumo_row + 3, 1, exatos_mes, ind_value_green_fmt)
            
            ws3.write(resumo_row + 4, 0, 'Itens Excesso:', ind_label_fmt)
            ws3.write(resumo_row + 4, 1, excesso_mes, ind_value_red_fmt)
            
            ws3.write(resumo_row + 5, 0, 'Itens Falta:', ind_label_fmt)
            ws3.write(resumo_row + 5, 1, falta_mes, ind_value_blue_fmt)
        
        print(f"✅ Relatório salvo: {ARQUIVO_RELATORIO}")
        print(f"🔒 Planilhas protegidas com senha")


# ========================================
# EXECUTAR
# ========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = LancamentoInventario(root)
    root.mainloop()