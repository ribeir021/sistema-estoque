import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sqlite3
import datetime

# Cria o banco de dados e as tabelas necessárias para o sistema se não existirem.
def inicializar_banco():
    with sqlite3.connect("loja.db") as conexao:
        conexao.execute("PRAGMA foreign_keys = ON;")
        cursor = conexao.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS loja (
                    id_loja INTEGER PRIMARY KEY,
                    nome_loja TEXT
                );
                CREATE TABLE IF NOT EXISTS produtos(
                    id_produto INTEGER PRIMARY KEY,
                    nome_produto TEXT,
                    preco_produto REAL
                );
                CREATE TABLE IF NOT EXISTS estoque(
                    id_loja INTEGER REFERENCES loja(id_loja),
                    id_produto INTEGER REFERENCES produtos(id_produto),
                    qtd_atual INTEGER,
                    qtd_minima INTEGER,
                    PRIMARY KEY (id_loja, id_produto)
                );
                CREATE TABLE IF NOT EXISTS vendas(
                    id_venda INTEGER PRIMARY KEY,
                    id_loja INTEGER REFERENCES loja(id_loja),
                    id_produto INTEGER REFERENCES produtos(id_produto),
                    qtd_vendida INTEGER,
                    data_venda TEXT
                );
                CREATE TABLE IF NOT EXISTS entradas_estoque(
                    id_entrada INTEGER PRIMARY KEY,         
                    id_loja INTEGER REFERENCES loja(id_loja),
                    id_produto INTEGER REFERENCES produtos(id_produto),
                    qtd_recebida INTEGER,         
                    preco_custo REAL,
                    data_entrada TEXT
                );
            """)
        lojas = [(1, 'Loja 1'), (2, 'Loja 2'), (3, 'Loja 3')]
        cursor.executemany("INSERT OR IGNORE INTO loja (id_loja, nome_loja) VALUES (?, ?)", lojas)
              
    conexao.close()

# Cadastra um novo produto no banco de dados e define seu estoque inicial na loja.
def salvar_produto(nome_entry, preco_entry, qtd_entry, loja_id=1):
    nome = nome_entry.get()
    preco = preco_entry.get()
    qtd = qtd_entry.get()
    
    if nome and preco and qtd:
        try:
            preco_float = float(preco.replace(',', '.'))
            qtd_inicial = int(qtd)
            conexao = sqlite3.connect("loja.db")
            cursor = conexao.cursor()
            
            cursor.execute("INSERT INTO produtos (nome_produto, preco_produto) VALUES (?, ?)", (nome, preco_float))
            id_gerado = cursor.lastrowid

            cursor.execute("""
                INSERT INTO estoque (id_loja, id_produto, qtd_atual, qtd_minima) 
                VALUES (?, ?, ?, 5)
            """, (loja_id, id_gerado, qtd_inicial))
            
            conexao.commit()
            conexao.close()
            
            print(f"Produto {nome} cadastrado com {qtd_inicial} unidades no estoque!")

            nome_entry.delete(0, tk.END)
            preco_entry.delete(0, tk.END)
            qtd_entry.delete(0, tk.END)
            
        except ValueError:
            print("Erro: Verifique se o preço e a quantidade são números válidos!")
    else:
        print("Preencha todos os campos!")

# Adiciona a quantidade informada ao estoque de um produto existente na loja selecionada.
def adicionar_estoque(id_loja, id_produto, qtd_a_entrar):
    with sqlite3.connect("loja.db") as conexao:
        cursor = conexao.cursor()
        
        cursor.execute("SELECT id_produto FROM produtos WHERE id_produto = ?", (id_produto,))
        produto_existe = cursor.fetchone()
        
        if not produto_existe:
            messagebox.showerror("Erro de ID", f"O ID {id_produto} não existe no cadastro de produtos!")
            return False
        
        cursor.execute(
            "UPDATE estoque SET qtd_atual = qtd_atual + ? WHERE id_loja = ? AND id_produto = ?",
            (qtd_a_entrar, id_loja, id_produto)
        )
        
        if cursor.rowcount == 0:
            cursor.execute(
                "INSERT INTO estoque (id_loja, id_produto, qtd_atual, qtd_minima) VALUES (?, ?, ?, 5)",
                (id_loja, id_produto, qtd_a_entrar)
            )
            messagebox.showinfo("Produto Vinculado", f"Produto {id_produto} foi vinculado à Loja {id_loja} com {qtd_a_entrar} unidades.")
        else:
            messagebox.showinfo("Sucesso", f"Foram adicionadas {qtd_a_entrar} unidades ao estoque da loja {id_loja}!")
            
    return True

# Registra a venda de um produto, subtraindo do estoque e salvando o histórico da transação.
def vender_produto(id_loja, id_produto, qtd_a_vender):
    try:
        qtd_venda = int(qtd_a_vender)
        if qtd_venda <= 0:
            messagebox.showerror("Erro de Quantidade", "Quantidade inválida! Insira um número maior que zero.")
            return False

        with sqlite3.connect("loja.db") as conexao:
            cursor = conexao.cursor()
            cursor.execute(
                "SELECT qtd_atual FROM estoque WHERE id_loja = ? AND id_produto = ?",
                (id_loja, id_produto)
            )
            resultado = cursor.fetchone()

            if resultado and resultado[0] >= qtd_venda:
                cursor.execute(
                    "UPDATE estoque SET qtd_atual = qtd_atual - ? WHERE id_loja = ? AND id_produto = ?",
                    (qtd_venda, id_loja, id_produto)
                )
                
                data_atual = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                cursor.execute(
                    "INSERT INTO vendas (id_loja, id_produto, qtd_vendida, data_venda) VALUES (?, ?, ?, ?)",
                    (id_loja, id_produto, qtd_venda, data_atual)
                )
                messagebox.showinfo("Sucesso", f"Venda de {qtd_venda} unidades realizada com sucesso!")
                return True
            else:
                messagebox.showerror("Erro de Estoque", "Estoque insuficiente ou o produto não existe nesta loja!")
                return False

    except ValueError:
        messagebox.showerror("Erro de Digitação", "O ID e a Quantidade precisam ser números inteiros!")
        return False
    
# Apaga completamente todos os registros de estoque da loja atualmente selecionada.
def limpar_estoque(janela, nome_loja):
    id_loja_atual = int(nome_loja.split()[1])

    with sqlite3.connect("loja.db") as conexao:
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM estoque WHERE id_loja = ?", (id_loja_atual,))
    
    messagebox.showinfo("Sucesso", f"O estoque da {nome_loja} foi completamente apagado!")
    
    tela_estoque(janela, nome_loja)

# Constrói a interface gráfica para o cadastro de novos produtos no sistema.
def tela_cadastro(janela, nome_loja):
    for widget in janela.winfo_children():
        widget.destroy()
        
    id_loja_atual = int(nome_loja.split()[1])

    tk.Label(janela, text="Cadastro de Novos Produtos", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=20)
    tk.Label(janela, text="Nome do Produto:").grid(row=1, column=0, padx=10, sticky="e")
    entry_nome = tk.Entry(janela, width=30)
    entry_nome.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(janela, text="Preço de Venda (R$):").grid(row=2, column=0, padx=10, sticky="e")
    entry_preco = tk.Entry(janela, width=30)
    entry_preco.grid(row=2, column=1, padx=10, pady=5)
    
    tk.Label(janela, text="Quantidade:").grid(row=3, column=0, padx=10, sticky="e")
    entry_qtd = tk.Entry(janela, width=30)
    entry_qtd.grid(row=3, column=1, padx=10, pady=5)

    botao_salvar = tk.Button(janela, text="Salvar Produto", bg="green", fg="white", command=lambda: salvar_produto(entry_nome, entry_preco, entry_qtd, id_loja_atual))
    botao_salvar.grid(row=4, column=0, columnspan=2, pady=20)

    botao_voltar = tk.Button(janela, text="Voltar ao Menu", command=lambda: tela_menu_principal(janela, nome_loja))
    botao_voltar.grid(row=5, column=0, columnspan=2, pady=20)

# Constrói a interface gráfica para dar entrada de itens no estoque da loja.
def tela_entrada(janela, nome_loja):
    for widget in janela.winfo_children():
        widget.destroy()
    
    id_loja_atual = int(nome_loja.split()[1])
    
    tk.Label(janela, text=f"Registrar Entrada - {nome_loja}", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=20)
    tk.Label(janela, text="ID do Produto:").grid(row=1, column=0, padx=10, sticky="e")
    entry_id = tk.Entry(janela, width=30)
    entry_id.grid(row=1, column=1, padx=10, pady=5)
    
    tk.Label(janela, text="Quantidade a Adicionar:").grid(row=2, column=0, padx=10, sticky="e")
    entry_qtd = tk.Entry(janela, width=30)
    entry_qtd.grid(row=2, column=1, padx=10, pady=5)

    def executar_entrada():
        id_prod = entry_id.get()
        qtd = entry_qtd.get()
                
        if id_prod and qtd:
            try:
                id_prod_int = int(id_prod)
                qtd_int = int(qtd)
                
                if qtd_int <= 0:
                    messagebox.showerror("Erro de Quantidade", "A quantidade a adicionar deve ser maior que zero!")
                    return
                        
                sucesso = adicionar_estoque(id_loja_atual, id_prod_int, qtd_int)
                if sucesso:
                    entry_id.delete(0, tk.END)
                    entry_qtd.delete(0, tk.END)
                    
            except ValueError:
                messagebox.showerror("Erro de Digitação", "O ID do produto e a Quantidade precisam ser números inteiros válidos!")
        else:
            messagebox.showwarning("Atenção", "Por favor, preencha todos os campos antes de confirmar!")

    botao_confirmar = tk.Button(janela, text="Confirmar Entrada", bg="blue", fg="white", font=("Arial", 10, "bold"), command=executar_entrada)
    botao_confirmar.grid(row=3, column=0, columnspan=2, pady=20)
        
    botao_voltar = tk.Button(janela, text="Voltar ao Menu", command=lambda: tela_menu_principal(janela, nome_loja))
    botao_voltar.grid(row=4, column=0, columnspan=2, pady=10)

# Constrói a interface gráfica responsável por registrar e processar as vendas.
def tela_venda(janela, nome_loja):
    for widget in janela.winfo_children():
        widget.destroy()
    
    id_loja_atual = int(nome_loja.split()[1])
    
    tk.Label(janela, text=f"Registrar Venda - {nome_loja}", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=20)
    tk.Label(janela, text="ID do Produto:").grid(row=1, column=0, padx=10, sticky="e")
    entry_id = tk.Entry(janela, width=30)
    entry_id.grid(row=1, column=1, padx=10, pady=5)
    
    tk.Label(janela, text="Quantidade a Vender:").grid(row=2, column=0, padx=10, sticky="e")
    entry_qtd = tk.Entry(janela, width=30)
    entry_qtd.grid(row=2, column=1, padx=10, pady=5)

    def executar_venda():
        id_prod = entry_id.get()
        qtd = entry_qtd.get()
        
        if id_prod and qtd:
            sucesso = vender_produto(id_loja_atual, id_prod, qtd)
            if sucesso:
                entry_id.delete(0, tk.END)
                entry_qtd.delete(0, tk.END)
        else:
            messagebox.showwarning("Atenção", "Por favor, preencha todos os campos antes de confirmar!")

    botao_confirmar = tk.Button(janela, text="Confirmar Venda", bg="blue", fg="white", font=("Arial", 10, "bold"), command=executar_venda)
    botao_confirmar.grid(row=3, column=0, columnspan=2, pady=20)
    
    botao_voltar = tk.Button(janela, text="Voltar ao Menu", command=lambda: tela_menu_principal(janela, nome_loja))
    botao_voltar.grid(row=4, column=0, columnspan=2, pady=10)

# Exibe a interface gráfica com a tabela de produtos e quantidades do estoque atual.
def tela_estoque(janela, nome_loja):
    for widget in janela.winfo_children():
        widget.destroy()

    label_estoque = tk.Label(janela, text=f"Estoque Atual - {nome_loja}", font=("Arial", 12, "bold"))
    label_estoque.grid(row=0, column=0, columnspan=2, pady=20, padx=20)
            
    id_loja_atual = int(nome_loja.split()[1])
    conexao = sqlite3.connect("loja.db")
    cursor = conexao.cursor()
    
    cursor.execute("""
        SELECT p.id_produto, p.nome_produto, p.preco_produto, e.qtd_atual, e.qtd_minima 
        FROM produtos p 
        JOIN estoque e ON p.id_produto = e.id_produto 
        WHERE e.id_loja=?
    """, (id_loja_atual,))
    dados = cursor.fetchall()
    conexao.close()

    colunas = ("id", "produto", "preco", "quantidade")
    tabela = ttk.Treeview(janela, columns=colunas, show="headings")
    tabela.grid(row=1, column=0, columnspan=2, pady=10)

    tabela.heading("id", text="ID")
    tabela.heading("produto", text="Produto")
    tabela.heading("preco", text="Preço (R$)")
    tabela.heading("quantidade", text="Qtd")
    
    tabela.column("id", width=50, anchor="center")
    tabela.column("produto", width=250)
    tabela.column("preco", width=100, anchor="center")
    tabela.column("quantidade", width=80, anchor="center")
    
    tabela.tag_configure("alerta", background="#ffcccc", foreground="black")

    for item in dados:
        if item[3] <= item[4]:
            tabela.insert("", tk.END, values=(item[0], item[1], f"R$ {item[2]:.2f}", item[3]), tags=("alerta",))
        else:
            tabela.insert("", tk.END, values=(item[0], item[1], f"R$ {item[2]:.2f}", item[3]))

    try:
        with open("promocoes.txt", "r", encoding="utf-8") as arquivo:
            texto_promocoes = arquivo.read()
            
        tk.Label(janela, text="Promoções Ativas:", font=("Arial", 12, "bold")).grid(row=2, column=0, columnspan=2, pady=5)
        caixa_texto = tk.Text(janela, height=5, width=60)
        caixa_texto.grid(row=3, column=0, columnspan=2, pady=5)
        caixa_texto.insert(tk.END, texto_promocoes)
        caixa_texto.config(state=tk.DISABLED)
        
    except FileNotFoundError:
        print("Aviso: Arquivo não encontrado.")

    botao_limpar = tk.Button(janela, text="Limpar Estoque da Loja", bg="orange", command=lambda: limpar_estoque(janela, nome_loja))
    botao_limpar.grid(row=7, column=0, columnspan=2, pady=5)

    botao_voltar = tk.Button(janela, text="Voltar ao Menu", command=lambda: tela_menu_principal(janela, nome_loja))
    botao_voltar.grid(row=8, column=0, columnspan=2, pady=5)

# Monta a interface do menu principal com as opções de navegação do sistema.
def tela_menu_principal(janela, nome_loja):
    for widget in janela.winfo_children():
        widget.destroy()

    label_menu_principal = tk.Label(janela, text=f"Painel de Controle - {nome_loja}")
    label_menu_principal.grid(row=0, column=0, columnspan=2, pady=20, padx=20)

    botao_cadastrar_produto = tk.Button(janela, text="Cadastrar Novo Produto", command=lambda: tela_cadastro(janela, nome_loja))
    botao_cadastrar_produto.grid(row=1, column=0, columnspan=2, pady=15)

    botao_registrar_entrada = tk.Button(janela, text="Registrar Entrada", command=lambda: tela_entrada(janela, nome_loja))
    botao_registrar_entrada.grid(row=2, column=0, columnspan=2, pady=15)

    botao_registrar_venda = tk.Button(janela, text="Registrar Venda", command=lambda: tela_venda(janela, nome_loja))
    botao_registrar_venda.grid(row=3, column=0, columnspan=2, pady=15)

    botao_ver_estoque = tk.Button(janela, text="Visualizar Estoque", command=lambda: tela_estoque(janela, nome_loja))
    botao_ver_estoque.grid(row=4, column=0, columnspan=2, pady=15)

    botao_voltar = tk.Button(janela, text="Voltar ao Menu", command=lambda: tela_inicial(janela))
    botao_voltar.grid(row=5, column=0, columnspan=2, pady=15)

# Exibe a primeira tela do sistema, permitindo escolher a loja antes de iniciar.
def tela_inicial(janela):
    for widget in janela.winfo_children():
        widget.destroy()

    label_saudacao = tk.Label(janela, text="Olá, Bem Vindo ao Sistema!", font=("Arial", 16))
    label_saudacao.grid(row=0, column=0, columnspan=2, pady=20, padx=20)

    label_loja = tk.Label(janela, text="Selecione sua Loja:", font=("Arial", 12))
    label_loja.grid(row=1, column=0, padx=10, sticky="w")

    loja_selecionada = tk.StringVar(janela)
    loja_selecionada.set("Loja 1")

    opcoes_lojas = ["Loja 1", "Loja 2", "Loja 3"]        
    menu_lojas = tk.OptionMenu(janela, loja_selecionada, *opcoes_lojas)
    menu_lojas.grid(row=1, column=1, padx=10, sticky="w")

    def confirmar_loja():
        loja_escolhida = loja_selecionada.get()
        print(f"Entrando na {loja_escolhida}...")
        tela_menu_principal(janela, loja_escolhida)

    botao_confirmar = tk.Button(janela, text="Entrar na Loja", command=confirmar_loja)
    botao_confirmar.grid(row=2, column=0, columnspan=2, pady=20)

    botao_sair_programa = tk.Button(janela, text="Sair do Programa", command=janela.destroy)
    botao_sair_programa.grid(row=3, column=0, columnspan=2, pady=20)

# Inicializa e mantém a janela principal do Tkinter rodando em loop contínuo.
def iniciar_interface():
    janela = tk.Tk()
    janela.title("Sistema de Gerenciamento de Estoque")
    janela.geometry("800x600")
    tela_inicial(janela)
    janela.mainloop()

if __name__ == "__main__":
    inicializar_banco()
    iniciar_interface()