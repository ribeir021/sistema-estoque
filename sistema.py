import tkinter as tk
from tkinter import ttk
import sqlite3
import datetime  # eu garanto a importação para registrar o horário das vendas

def inicializar_banco():
    # eu conecto ou crio o arquivo do banco de dados
    conexao = sqlite3.connect("loja.db")
    cursor = conexao.cursor()

    # eu executo os scripts de criação das tabelas estruturadas
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
    conexao.commit()
    conexao.close()

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

def vender_produto(id_loja, id_produto, qtd_a_vender):
    try:
        qtd_venda = int(qtd_a_vender)

        if qtd_venda <= 0:
            print("Erro: A quantidade de venda deve ser maior que zero!")
            return False

        conexao = sqlite3.connect("loja.db")
        cursor = conexao.cursor()
        cursor.execute(
            "SELECT qtd_atual FROM estoque WHERE id_loja = ? AND id_produto = ?",
            (id_loja, id_produto),
        )
        resultado = cursor.fetchone()

        if resultado:
            qtd_atual = resultado[0]

            if qtd_atual >= qtd_venda:
                cursor.execute(
                    "UPDATE estoque SET qtd_atual = qtd_atual - ? WHERE id_loja = ? AND id_produto = ?",
                    (qtd_venda, id_loja, id_produto),
                )

                data_atual = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

                cursor.execute(
                    "INSERT INTO vendas (id_loja, id_produto, qtd_vendida, data_venda) VALUES (?, ?, ?, ?)",
                    (id_loja, id_produto, qtd_venda, data_atual),
                )

                conexao.commit()
                conexao.close()

                print(f"Sucesso: Venda de {qtd_venda} unidades realizada com sucesso!")
                return True
            else:
                print(f"Erro: Estoque insuficiente! Essa loja só tem {qtd_atual} unidades disponíveis.")
        else:
            print("Erro: Este produto não está vinculado ao estoque desta loja!")

        conexao.close()
        return False

    except ValueError:
        print("Erro: Por favor, insira um número inteiro válido para a quantidade!")
        return False

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

def tela_venda(janela, nome_loja):
    # eu limpo a tela para desenhar o painel de saídas
    for widget in janela.winfo_children():
        widget.destroy()
        
    id_loja_atual = int(nome_loja.split()[1])
    
    tk.Label(janela, text=f"Registrar Venda - {nome_loja}", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=20)
    
    # eu monto o campo do ID do item
    tk.Label(janela, text="ID do Produto:").grid(row=1, column=0, padx=10, sticky="e")
    entry_id = tk.Entry(janela, width=30)
    entry_id.grid(row=1, column=1, padx=10, pady=5)
    
    # eu monto o campo da quantidade vendida
    tk.Label(janela, text="Quantidade a Vender:").grid(row=2, column=0, padx=10, sticky="e")
    entry_qtd = tk.Entry(janela, width=30)
    entry_qtd.grid(row=2, column=1, padx=10, pady=5)
    
    def executar_venda():
        id_prod = entry_id.get()
        qtd = entry_qtd.get()
        
        if id_prod and qtd:
            # eu envio as variáveis para a função de validação e banco de dados
            sucesso = vender_produto(id_loja_atual, int(id_prod), int(qtd))
            if sucesso:
                entry_id.delete(0, tk.END)
                entry_qtd.delete(0, tk.END)
        else:
            print("Preencha todos os campos!")

    botao_confirmar = tk.Button(janela, text="Confirmar Venda", bg="blue", fg="white", font=("Arial", 10, "bold"), command=executar_venda)
    botao_confirmar.grid(row=3, column=0, columnspan=2, pady=20)
    
    botao_voltar = tk.Button(janela, text="Voltar ao Menu", command=lambda: tela_menu_principal(janela, nome_loja))
    botao_voltar.grid(row=4, column=0, columnspan=2, pady=10)

def tela_estoque(janela, nome_loja):
    for widget in janela.winfo_children():
        widget.destroy()

    label_estoque = tk.Label(janela, text=f"Estoque Atual - {nome_loja}")
    label_estoque.grid(row=0, column=0, columnspan=2, pady=20, padx=20)
            
    id_loja_atual = int(nome_loja.split()[1])
    conexao = sqlite3.connect("loja.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT p.nome_produto, p.preco_produto, e.qtd_atual, e.qtd_minima FROM produtos p JOIN estoque e ON p.id_produto = e.id_produto WHERE e.id_loja=?",(id_loja_atual,))
    dados = cursor.fetchall()
    conexao.close()

    colunas = ("produto", "preco", "quantidade")
    tabela = ttk.Treeview(janela, columns=colunas, show="headings")
    tabela.grid(row=1, column=0, columnspan=2, pady=10)

    tabela.heading("produto", text="Produto")
    tabela.heading("preco", text="Preço (R$)")
    tabela.heading("quantidade", text="Qtd")
    tabela.tag_configure("alerta", background="#ffcccc", foreground="black")

    for item in dados:
        if item[2] <= item[3]:
            tabela.insert("", tk.END, values=(item[0], item[1], item[2]), tags=("alerta",))
        else:
            tabela.insert("", tk.END, values=(item[0], item[1], item[2]))

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
        

    botao_voltar = tk.Button(janela, text="Voltar ao Menu", command=lambda: tela_menu_principal(janela, nome_loja))
    botao_voltar.grid(row=200, column=0, columnspan=2, pady=40)

def tela_menu_principal(janela, nome_loja):
    for widget in janela.winfo_children():
        widget.destroy()

    label_menu_principal = tk.Label(janela, text=f"Painel de Controle - {nome_loja}")
    label_menu_principal.grid(row=0, column=0, columnspan=2, pady=20, padx=20)

    botao_cadastrar_produto = tk.Button(janela, text="Cadastrar Novo Produto", command=lambda: tela_cadastro(janela, nome_loja))
    botao_cadastrar_produto.grid(row=1, column=0, columnspan=2, pady=15)

    # eu incluo o botão de vendas no menu principal mapeando para a nova tela gráfica
    botao_registrar_venda = tk.Button(janela, text="Registrar Venda", command=lambda: tela_venda(janela, nome_loja))
    botao_registrar_venda.grid(row=2, column=0, columnspan=2, pady=15)

    botao_ver_estoque = tk.Button(janela, text="Visualizar Estoque", command=lambda: tela_estoque(janela, nome_loja))
    botao_ver_estoque.grid(row=3, column=0, columnspan=2, pady=15)

    botao_voltar = tk.Button(janela, text="Voltar ao Menu", command=lambda: tela_inicial(janela))
    botao_voltar.grid(row=4, column=0, columnspan=2, pady=15)

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
    
def iniciar_interface():
    janela = tk.Tk()
    janela.title("Sistema de Gerenciamento de Estoque")
    janela.geometry("800x600")
    tela_inicial(janela)
    janela.mainloop()

if __name__ == "__main__":
    inicializar_banco()
    iniciar_interface()
