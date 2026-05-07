import tkinter as tk
from tkinter import ttk
import sqlite3

def inicializar_banco():
    # conecta ou cria o arquivo
    conexao = sqlite3.connect("loja.db")
    # chama o cursor
    cursor = conexao.cursor()

    # executa o SQL
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
    # salva tudo acima no banco
    conexao.commit()
    # fecha a conexao com o banco
    conexao.close()

def salvar_produto(nome_entry, preco_entry, loja_id=1):
    # pega os valores que o usuário digitou nos campos
    nome = nome_entry.get()
    preco = preco_entry.get()

    if nome and preco:
        try:
            # converte o preço para float antes de salvar
            preco_float = float(preco.replace(',', '.'))
            
            conexao = sqlite3.connect("loja.db")
            cursor = conexao.cursor()
            # insere o produto
            cursor.execute("INSERT INTO produtos (nome_produto, preco_produto) VALUES (?, ?)", (nome, preco_float))
            
            # Pega o ID que o banco acabou de gerar para esse produto
            id_gerado = cursor.lastrowid

            # Inicializa o estoque para esse produto 
            cursor.execute("""
                INSERT INTO estoque (id_loja, id_produto, qtd_atual, qtd_minima) 
                VALUES (?, ?, 0, 5)
            """, (loja_id, id_gerado))
            conexao.commit()
            conexao.close()
            
            print(f"Produto {nome} cadastrado e inicializado no estoque!")

            # limpa os campos após salvar para o usuário cadastrar outro
            nome_entry.delete(0, tk.END)
            preco_entry.delete(0, tk.END)

        except ValueError:
            print("Erro: O preço precisa ser um número!")
    else:
        print("Preencha todos os campos!")

def tela_cadastro(janela, nome_loja):
    # limpa tudo que está na janela para desenhar a nova tela
    for widget in janela.winfo_children():
        widget.destroy()

    tk.Label(janela, text="Cadastro de Novos Produtos", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=20)

    # campo nome
    tk.Label(janela, text="Nome do Produto:").grid(row=1, column=0, padx=10, sticky="e")
    entry_nome = tk.Entry(janela, width=30)
    entry_nome.grid(row=1, column=1, padx=10, pady=5)

    # campo preço
    tk.Label(janela, text="Preço de Venda (R$):").grid(row=2, column=0, padx=10, sticky="e")
    entry_preco = tk.Entry(janela, width=30)
    entry_preco.grid(row=2, column=1, padx=10, pady=5)

    # botão salvar usa lambda para passar os argumentos e rodar só quando clicar no botão
    botao_salvar = tk.Button(janela, text="Salvar Produto", bg="green", fg="white", command=lambda: salvar_produto(entry_nome, entry_preco))
    botao_salvar.grid(row=3, column=0, columnspan=2, pady=20)

    botao_voltar = tk.Button(janela, text="Voltar ao Menu", command=lambda: tela_menu_principal(janela, nome_loja))
    botao_voltar.grid(row=4, column=0, columnspan=2, pady=20)

def tela_estoque(janela, nome_loja):
     # limpa tudo que está na janela para desenhar a nova tela novamente
    for widget in janela.winfo_children():
        widget.destroy()
    label_estoque = tk.Label(janela, text=f"Estoque Atual - {nome_loja}")
    label_estoque.grid(row=0, column=0, columnspan=2, pady=20, padx=20)
            
    conexao = sqlite3.connect("loja.db")
    cursor = conexao.cursor()
    # busca o produto
    cursor.execute("SELECT p.nome_produto, p.preco_produto, e.qtd_atual FROM produtos p JOIN estoque e ON p.id_produto = e.id_produto;")
    # variável recebe a busca
    dados = cursor.fetchall()
    # imprime a busca
    print(dados)
    # fecha o banco
    conexao.close()
    # define os nomes das colunas usadas nas tabelas
    colunas = ("produto", "preco", "quantidade")
    # cria a tabela na janela, 
    # show="headings" esconde uma coluna inicial vazia
    tabela = ttk.Treeview(janela, columns=colunas, show="headings")
    # posição da tabela
    tabela.grid(row=1, column=0, columnspan=2, pady=10)
    # define os textos que vão aparecer 
    # no topo de cada coluna e deixa eles mais bonitos
    tabela.heading("produto", text="Produto")
    tabela.heading("preco", text="Preço (R$)")
    tabela.heading("quantidade", text="Qtd")
    # percorre toda a busca recebida
    for item in dados:
        # insere os produtos na tabela com seus valores, colocando no final
        tabela.insert("", tk.END, values=(item[0], item[1], item[2]))
    # crio e coloco esse botão mais pra baixo
    botao_voltar = tk.Button(janela, text="Voltar ao Menu", command=lambda: tela_menu_principal(janela, nome_loja))
    botao_voltar.grid(row=100, column=0, columnspan=2, pady=40)

    
    


def tela_menu_principal(janela, nome_loja):
    # limpa tudo que está na janela para desenhar a nova tela novamente
    for widget in janela.winfo_children():
        widget.destroy()
    # texto do painel
    label_menu_principal = tk.Label(janela, text=f"Painel de Controle - {nome_loja}")
    label_menu_principal.grid(row=0, column=0, columnspan=2, pady=20, padx=20)
    # cadastra usando lambda dnv
    botao_cadastrar_produto = tk.Button(janela, text="Cadastrar Novo Produto", command=lambda: tela_cadastro(janela, nome_loja))
    botao_cadastrar_produto.grid(row=1, column=0, columnspan=2, pady=20)

    botao_ver_estoque = tk.Button(janela, text= "Visualizar Estoque", command=lambda: tela_estoque(janela, nome_loja))
    botao_ver_estoque.grid(row=2, column=0, columnspan=2, pady=20)

    botao_voltar = tk.Button(janela, text="Voltar ao Menu", command=lambda: tela_inicial(janela))
    botao_voltar.grid(row=3, column=0, columnspan=2, pady=20)


def tela_inicial(janela):
    for widget in janela.winfo_children():
        widget.destroy()
    # adiciona um texto na tela
    label_saudacao = tk.Label(janela, text = "Olá, Bem Vindo ao Sistema!", font = ("Arial", 16))
    label_saudacao.grid(row=0, column=0, columnspan=2, pady=20, padx=20)

    # configura o seletor de lojas
    label_loja = tk.Label(janela, text="Selecione sua Loja:", font=("Arial", 12))
    label_loja.grid(row=1, column=0, padx=10, sticky="w")

    # cria uma variável que o Tkinter consegue "vigiar"
    loja_selecionada = tk.StringVar(janela)
    loja_selecionada.set("Loja 1") # valor padrão inicial

    # criando o OptionMenu
    opcoes_lojas = ["Loja 1", "Loja 2", "Loja 3"]        # "*" serve para desempacotar a lista
    menu_lojas = tk.OptionMenu(janela, loja_selecionada, *opcoes_lojas)
    menu_lojas.grid(row=1, column=1, padx=10, sticky="w")

    def confirmar_loja():
        loja_escolhida = loja_selecionada.get()
        print(f"Entrando na {loja_escolhida}...")
        tela_menu_principal(janela, loja_escolhida)

    # botão para confirmar a seleção
    botao_confirmar = tk.Button(janela, text="Entrar na Loja", command=confirmar_loja)
    botao_confirmar.grid(row=2, column=0, columnspan=2, pady=20)


def iniciar_interface():
    # cria a janela principal
    janela = tk.Tk()

    # configura o título
    janela.title("Sistema de Gerenciamento de Estoque")
    
    # define o tamanho
    janela.geometry("800x600")

    tela_inicial(janela)

    # o motor que mantém a janela aberta
    janela.mainloop()

    
'''
utilizo este bloco para garantir que o sistema 
só inicie se este arquivo for executado diretamente,
evitando que a interface ou o banco abram sozinhos 
caso eu importe este script em outro lugar no futuro
'''
if __name__ == "__main__":
    inicializar_banco()
    iniciar_interface()