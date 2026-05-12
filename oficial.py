import tkinter as tk
from tkinter import ttk
import sqlite3

class RepositorioEstoque:
    def __init__(self, nome_banco): #funcao construtora - nome_banco define qual .db será manipulado
        self.nome_banco = nome_banco
        self.inicializar_banco()

    def conectar(self): #funcao de conexao com bd
        conexao = sqlite3.connect(self.nome_banco)
        conexao.execute("PRAGMA foreign_keys = ON;") # regra de chave estrangeira
        return conexao

    def inicializar_banco(self):  # conecta ou cria o arquivo
        conexao = self.conectar()
        cursor = conexao.cursor() # chama o cursor

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
        
        cursor.execute("SELECT COUNT(*) FROM loja")
        qtd_lojas = cursor.fetchone()[0]
        if qtd_lojas == 0:
            cursor.execute("INSERT INTO loja (nome_loja) VALUES ('Matriz')")
            print("Banco criado! Loja 'Matriz' ja foi inserida automaticamente.")       
        conexao.commit() # salva tudo acima no banco
        conexao.close() # fecha a conexao com o banco
        pass

    def buscar_todas_lojas(self):
        conexao = self.conectar()
        cursor = conexao.cursor()

        cursor.execute ("SELECT id_loja, nome_loja FROM loja;") # realiza a busca no bd
        lojas = cursor.fetchall()
        conexao.close()
        return lojas

    def salvar_produto(self, nome:str, preco:float, loja_id:int): # pega os valores que o usuário digitou nos campos
        conexao = self.conectar()
        cursor = conexao.cursor()
        
        cursor.execute("INSERT INTO produtos (nome_produto, preco_produto) VALUES (?, ?)", (nome, preco))
        
        id_gerado = cursor.lastrowid # pega o ID que o banco acabou de gerar para esse produto

        # Inicializa o estoque para esse produto 
        cursor.execute("""
            INSERT INTO estoque (id_loja, id_produto, qtd_atual, qtd_minima) 
            VALUES (?, ?, 0, 5)
        """, (loja_id, id_gerado))
        conexao.commit()
        conexao.close()

    def buscar_estoque_loja(self, loja_id: int):
        conexao = self.conectar()
        cursor = conexao.cursor()

        # busca o nome, preco e qtd do produto no bd,
        # usa INNERJOIN para unir as tabelas de produtos e de estoque onde id_produto é igual
        # usa WHERE para pegar os resultados apenas da loja selecionada
        cursor.execute("""
            SELECT p.nome_produto, p.preco_produto, e.qtd_atual
            FROM produtos p
            JOIN estoque e ON p.id_produto = e.id_produto
            WHERE e.id_loja = ?;
            """, (loja_id,))
        
        dados_estoque = cursor.fetchall()
        conexao.close()
        return dados_estoque


class AppEstoque:
    def __init__(self, janela_raiz, repositorio):
        self.janela = janela_raiz
        self.db = repositorio # estabelecemos o acesso da interface para a database

        # Variaveis de estado
        self.loja_atual_id = None
        self.loja_atual_nome = ""
        
        self.mostrar_tela_inicial() #inicia a interface

    def limpar_tela(self):
        for widget in self.janela.winfo_children():
            widget.destroy()
    
    def mostrar_tela_inicial(self):
        self.limpar_tela()

        # titulos
        tk.Label(self.janela, text="Bem vindo ao Sistema de Estoque!", font=("Arial",16)).grid(row=0, column=0, columnspan=2, pady=20, padx=20)
        tk.Label(self.janela, text="Selecione a loja que trabalha:", font=("Arial",12)).grid(row=1, column=0, padx=10, sticky="w")
        
        # busca as lojas existentes na db
        self.lojas_db = self.db.buscar_todas_lojas()

        # mostra o nome da primeira loja da lista
        self.loja_selecionada = tk.StringVar(self.janela)
        self.loja_selecionada.set(self.lojas_db[0][1]) 

        opcoes_nomes = [loja[1] for loja in self.lojas_db] #cria uma lista de nomes das lojas para as opcoes do menu
        menu_lojas = tk.OptionMenu(self.janela, self.loja_selecionada, *opcoes_nomes)
        menu_lojas.grid(row=1, column=1, padx=10, sticky="w")
        
        # botao confirma loja
        botao_confirmar = tk.Button(self.janela, text="Entrar na loja", command=self.confirmar_loja)
        botao_confirmar.grid(row=2, column=0, columnspan=2, pady=20)        
    
    def confirmar_loja(self):
        # pega a loja selecionada na interface
        nome_escolhido = self.loja_selecionada.get()

        # procura a loja selecionada nas lojas existentes
        for loja in self.lojas_db:
            if loja[1] == nome_escolhido:
                self.loja_atual_id = loja[0]
                self.loja_atual_nome = loja[1]
                break
        print(f"Entrando na loja: {self.loja_atual_nome} (ID: {self.loja_atual_id})")
        self.mostrar_tela_menu_principal()
    
    def mostrar_tela_menu_principal(self):
        self.limpar_tela()

        # titulo painel
        label_menu_principal = tk.Label(self.janela, text=f"Painel de Controle - {self.loja_atual_nome}")
        label_menu_principal.grid(row=0, column=0, columnspan=2, pady=20, padx=20)

        # botao cadastro
        botao_cadastrar = tk.Button(self.janela, text="Cadastrar Novo Produto", width=25, command=self.mostrar_tela_cadastro)
        botao_cadastrar.grid(row=1, column=0, columnspan=2, pady=20)

        # botao estoque
        botao_estoque = tk.Button(self.janela, text="Visualizar Estoque da Loja", width=25, command=self.mostrar_tela_estoque)
        botao_estoque.grid(row=2, column=0, columnspan=2, pady=20)

        #botao voltar
        botao_voltar = tk.Button(self.janela, text="Voltar", width=25, command=self.mostrar_tela_inicial)
        botao_voltar.grid(row=3, column=0, columnspan=2, pady=20)
        
    def mostrar_tela_cadastro(self):
        self.limpar_tela()

        # titulo cadastro
        tk.Label(self.janela, text="Cadastro de Novos Produtos", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=20)

        # campo nome
        tk.Label(self.janela, text="Nome do Produto:").grid(row=1, column=0, padx=10, sticky="e") 
        self.entry_produto = tk.Entry(self.janela, width=30)
        self.entry_produto.grid(row=1, column=1, padx=10, pady=5)
        
        # campo preço
        tk.Label(self.janela, text="Preço de Venda (R$):").grid(row=2, column=0, padx=10, sticky="e") 
        self.entry_preco = tk.Entry(self.janela, width=30)
        self.entry_preco.grid(row=2, column=1, padx=10, pady=5)

        # mensagens avisos 
        # inicia vazia "" e guardada no self para ser alteradad depois
        self.label_feedback = tk.Label(self.janela, text="", font=("Arial", 10, "bold"))
        self.label_feedback.grid(row=4, column=0, columnspan=2, pady=20)

        # botão salvar 
        botao_salvar = tk.Button(self.janela, text="Salvar Produto", bg="green", fg="white", command=self.clique_salvar_produto)
        botao_salvar.grid(row=3, column=0, columnspan=2, pady=20)

        # botao voltar menu
        botao_voltar = tk.Button(self.janela, text="Voltar ao Menu", command=self.mostrar_tela_menu_principal)
        botao_voltar.grid(row=5, column=0, columnspan=2, pady=20)
    
    def clique_salvar_produto(self):
        produto_digitado = self.entry_produto.get()
        preco_digitado = self.entry_preco.get()

        if not produto_digitado or not preco_digitado:
            # mensagem: erro
            self.label_feedback.config(text="Erro: Preencha todos os campos!",fg="red")
            return

        try:
            preco_float = float(preco_digitado.replace(',','.'))
            
            if preco_float < 0:
                self.label_feedback.config(text="Erro! O preço não pode ser negativo!", fg="red")
                return
            
            # puxa a funcao do bd
            self.db.salvar_produto(produto_digitado, preco_float, self.loja_atual_id)

            # mensagem: sucesso
            self.label_feedback.config(text=f"Sucesso: {produto_digitado} cadastrado!", fg="green")
            

            self.entry_produto.delete(0, tk.END)
            self.entry_preco.delete(0, tk.END)

        except ValueError:
            # mensagem: erro de conversao
            self.label_feedback.config(text="Erro: O preço precisa ser um número válido", fg="red")

    def mostrar_tela_estoque(self):
        self.limpar_tela()

        tk.Label(self.janela, text=f"Estoque Atual - {self.loja_atual_nome}", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=20)
        
        # envia o id da loja e busca os dados
        dados_estoque = self.db.buscar_estoque_loja(self.loja_atual_id)

        # configuracao de treeview (tabela)
        colunas = ("produto", "preco", "quantidade")
        tabela = ttk.Treeview(self.janela, columns=colunas, show="headings")
        tabela.grid(row=1, column=0, columnspan=2, padx=20, pady=10)

        tabela.heading("produto", text="Produto") 
        tabela.heading("preco", text="Preço")
        tabela.heading("quantidade", text="Qtd")

        # preenchimento de treeview usando os headings
        for item in dados_estoque:
            # "" = nivel raiz / tk.END = final da lista 
            tabela.insert("", tk.END, values=(item[0], f"R$ {item[1]:.2f}", item[2]))
        
        # botao voltar
        tk.Button(self.janela, text="Voltar ao Menu", command=self.mostrar_tela_menu_principal).grid(row=2, column=0, columnspan=2, pady=20)        


if __name__ == "__main__":
    # Janela Tkinter
    janela_principal = tk.Tk()
    janela_principal.title("Sistema de Estoque - V2")
    janela_principal.geometry("800x600")

    # Instância bd
    repositorio = RepositorioEstoque("loja.db")

    # inicia o app passando a janela e o banco
    app = AppEstoque(janela_principal, repositorio)

    # roda o loop da interface
    janela_principal.mainloop()