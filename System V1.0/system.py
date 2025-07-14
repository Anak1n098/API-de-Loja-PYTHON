import json
from datetime import datetime
import getpass
import os

class Cupom:
    def __init__(self, codigo, desconto, valido_ate, usado=False):
        self.codigo = codigo
        self.desconto = desconto 
        self.valido_ate = valido_ate 
        self.usado = usado

class Usuario:
    def __init__(self, login, senha, tipo, nome=None, historico=None):
        self.login = login
        self.senha = senha
        self.tipo = tipo  
        self.nome = nome
        self.historico = historico if historico is not None else []

class Produto:
    def __init__(self, codigo, nome, preco, quantidade, categoria=None):
        self.codigo = codigo
        self.nome = nome
        self.preco = preco
        self.quantidade = quantidade
        self.categoria = categoria

class Carrinho:
    def __init__(self):
        self.itens = []
        self.cupom_aplicado = None
    
    def adicionar_item(self, produto, quantidade):
        self.itens.append({"produto": produto, "quantidade": quantidade})
    
    def aplicar_cupom(self, cupom):
        self.cupom_aplicado = cupom
    
    def calcular_total(self):
        subtotal = sum(item["produto"].preco * item["quantidade"] for item in self.itens)
        
        if self.cupom_aplicado:
            desconto = subtotal * (self.cupom_aplicado.desconto / 100)
            return subtotal - desconto, desconto
        
        return subtotal, 0
    
    def finalizar_compra(self, estoque, usuario):
        total, desconto = self.calcular_total()
        
        for item in self.itens:
            estoque.atualizar_estoque(item["produto"].codigo, -item["quantidade"])
        
        compra = {
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "itens": [{"nome": item["produto"].nome, "quantidade": item["quantidade"]} for item in self.itens],
            "subtotal": sum(item["produto"].preco * item["quantidade"] for item in self.itens),
            "desconto": desconto,
            "total": total,
            "cupom": self.cupom_aplicado.codigo if self.cupom_aplicado else None
        }
        
        usuario.historico.append(compra)
        
        if self.cupom_aplicado:
            self.cupom_aplicado.usado = True
        
        self.itens = []
        self.cupom_aplicado = None
        return compra

class Estoque:
    def __init__(self):
        self.produtos = self.carregar_produtos()
        self.usuarios = self.carregar_usuarios()
        self.cupons = self.carregar_cupons()
        self.usuario_logado = None
        self.vendas = self.carregar_vendas()
    
    def carregar_produtos(self):
        try:
            with open("produtos.json", "r") as f:
                dados = json.load(f)
                return [Produto(**p) for p in dados]
        except FileNotFoundError:
            return []
    
    def carregar_usuarios(self):
        try:
            with open("usuarios.json", "r") as f:
                dados = json.load(f)
                usuarios = []
                for u in dados:
                    user_data = u.copy()
                    historico = user_data.pop('historico', [])
                    usuario = Usuario(**user_data)
                    usuario.historico = historico
                    usuarios.append(usuario)
                return usuarios
        except FileNotFoundError:
            return [
                Usuario("admin", "admin123", "admin", "Administrador"),
                Usuario("cliente", "cliente123", "cliente", "Cliente Exemplo")
            ]
        except Exception as e:
            print(f"Erro ao carregar usuários: {e}")
            return []
    
    def carregar_cupons(self):
        try:
            with open("cupons.json", "r") as f:
                dados = json.load(f)
                return [Cupom(**c) for c in dados]
        except FileNotFoundError:
            return []
    
    def carregar_vendas(self):
        try:
            with open("vendas.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def salvar_dados(self):
        with open("produtos.json", "w") as f:
            json.dump([vars(p) for p in self.produtos], f)
        
        with open("usuarios.json", "w") as f:
            usuarios_para_salvar = []
            for u in self.usuarios:
                usuario_dict = {
                    "login": u.login,
                    "senha": u.senha,
                    "tipo": u.tipo,
                    "nome": u.nome,
                    "historico": u.historico
                }
                usuarios_para_salvar.append(usuario_dict)
            json.dump(usuarios_para_salvar, f)
        
        with open("cupons.json", "w") as f:
            json.dump([vars(c) for c in self.cupons], f)
        
        with open("vendas.json", "w") as f:
            json.dump(self.vendas, f)
    
    def gerar_nota_fiscal(self, compra, usuario):
        """Gera um arquivo TXT com os dados da compra"""
        
        if not os.path.exists('notas_fiscais'):
            os.makedirs('notas_fiscais')
        
        data_arquivo = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"notas_fiscais/nota_fiscal_{data_arquivo}.txt"
        
        conteudo = f"""
==================================
        NOTA FISCAL
==================================
LOJA: Loja
CNPJ: 12.345.678/0001-99
Endereço: Exemploe, 123 - Centro

Data: {compra['data']}
Cliente: {usuario.nome if usuario.nome else usuario.login}
{'='*40}

ITENS COMPRADOS:
"""
        for item in compra['itens']:
            conteudo += f"\n{item['quantidade']} x {item['nome']}"
        
        conteudo += f"""
{'='*40}
Subtotal: R$ {compra['subtotal']:.2f}
Desconto: R$ {compra['desconto']:.2f}
TOTAL: R$ {compra['total']:.2f}

Cupom utilizado: {compra.get('cupom', 'Nenhum')}
{'='*40}
Obrigado pela sua compra!
Volte sempre!
{'='*40}
"""
        
        with open(nome_arquivo, 'w', encoding='utf-8') as arquivo:
            arquivo.write(conteudo)
        
        return nome_arquivo
    
    def login(self):
        tentativas = 3
        while tentativas > 0:
            login = input("Login: ")
            senha = getpass.getpass("Senha: ")
            
            for usuario in self.usuarios:
                if usuario.login == login and usuario.senha == senha:
                    self.usuario_logado = usuario
                    print(f"\nBem-vindo, {usuario.nome if usuario.nome else usuario.login}!")
                    return True
            
            tentativas -= 1
            print(f"Credenciais inválidas. Tentativas restantes: {tentativas}")
        
        print("Acesso bloqueado. Tente novamente mais tarde.")
        return False
    
    def cadastrar_usuario(self):
        print("\n--- CADASTRO DE USUÁRIO ---")
        login = input("Login: ")
        senha = getpass.getpass("Senha: ")
        nome = input("Nome completo: ")
        tipo = "cliente"
        
        if any(u.login == login for u in self.usuarios):
            print("Login já existe. Escolha outro.")
            return
        
        novo_usuario = Usuario(login, senha, tipo, nome)
        self.usuarios.append(novo_usuario)
        self.salvar_dados()
        print("Cadastro realizado com sucesso!")
    
    def criar_cupom(self):
        if self.usuario_logado.tipo != 'admin':
            print("Acesso negado. Somente administradores podem criar cupons.")
            return
        
        print("\n--- CRIAR NOVO CUPOM ---")
        codigo = input("Código do cupom: ").upper()
        
        if any(c.codigo == codigo for c in self.cupons):
            print("Já existe um cupom com este código.")
            return
        
        try:
            desconto = float(input("Desconto (%): "))
            valido_ate = input("Válido até (dd/mm/aaaa): ")
            datetime.strptime(valido_ate, "%d/%m/%Y")
        except ValueError:
            print("Formato inválido. Use números para desconto e dd/mm/aaaa para data.")
            return
        
        novo_cupom = Cupom(codigo, desconto, valido_ate)
        self.cupons.append(novo_cupom)
        self.salvar_dados()
        print(f"Cupom {codigo} criado com sucesso!")
    
    def listar_cupons_validos(self):
        hoje = datetime.now().strftime("%d/%m/%Y")
        cupons_validos = []
        
        for cupom in self.cupons:
            if not cupom.usado:
                try:
                    data_cupom = datetime.strptime(cupom.valido_ate, "%d/%m/%Y")
                    data_hoje = datetime.strptime(hoje, "%d/%m/%Y")
                    if data_cupom >= data_hoje:
                        cupons_validos.append(cupom)
                except:
                    continue
        
        if not cupons_validos:
            print("Nenhum cupom válido disponível.")
            return
        
        print("\n--- CUPONS VÁLIDOS ---")
        for cupom in cupons_validos:
            print(f"Código: {cupom.codigo} | Desconto: {cupom.desconto}% | Válido até: {cupom.valido_ate}")
        print("----------------------")
    
    def verificar_cupom(self, codigo):
        hoje = datetime.now().strftime("%d/%m/%Y")
        
        for cupom in self.cupons:
            if cupom.codigo == codigo and not cupom.usado:
                try:
                    data_cupom = datetime.strptime(cupom.valido_ate, "%d/%m/%Y")
                    data_hoje = datetime.strptime(hoje, "%d/%m/%Y")
                    if data_cupom >= data_hoje:
                        return cupom
                except:
                    continue
        return None
    
    def adicionar_produto(self, produto):
        if self.usuario_logado.tipo not in ['admin', 'funcionario']:
            print("Acesso negado. Somente administradores e funcionários podem adicionar produtos.")
            return
            
        if any(p.codigo == produto.codigo for p in self.produtos):
            print("Já existe um produto com este código.")
            return
            
        self.produtos.append(produto)
        self.salvar_dados()
        print(f"Produto {produto.nome} adicionado ao estoque.")
    
    def remover_produto(self, codigo):
        if self.usuario_logado.tipo != 'admin':
            print("Acesso negado. Somente administradores podem remover produtos.")
            return
            
        for produto in self.produtos:
            if produto.codigo == codigo:
                self.produtos.remove(produto)
                self.salvar_dados()
                print(f"Produto {produto.nome} removido do estoque.")
                return
        print("Produto não encontrado.")
    
    def listar_produtos(self, categoria=None):
        print("\n--- LISTA DE PRODUTOS ---")
        produtos_filtrados = [p for p in self.produtos if not categoria or p.categoria == categoria]
        
        if not produtos_filtrados:
            print("Nenhum produto encontrado.")
            return
        
        for produto in produtos_filtrados:
            status = " (ESGOTADO)" if produto.quantidade == 0 else ""
            print(f"Código: {produto.codigo} | Nome: {produto.nome}{status}")
            print(f"Preço: R${produto.preco:.2f} | Quantidade: {produto.quantidade}")
            print(f"Categoria: {produto.categoria or 'Sem categoria'}\n")
        print("-------------------------")
    
    def atualizar_estoque(self, codigo, quantidade):
        if self.usuario_logado.tipo not in ['admin', 'funcionario']:
            print("Acesso negado. Somente administradores e funcionários podem atualizar estoque.")
            return
            
        for produto in self.produtos:
            if produto.codigo == codigo:
                produto.quantidade += quantidade
                self.salvar_dados()
                print(f"Estoque de {produto.nome} atualizado. Nova quantidade: {produto.quantidade}")
                return
        print("Produto não encontrado.")

def menu_admin(estoque):
    while True:
        print("\n--- MENU ADMINISTRADOR ---")
        print("1. Gerenciar produtos")
        print("2. Gerenciar cupons")
        print("3. Relatório de vendas")
        print("4. Sair")
        
        opcao = input("Escolha uma opção: ")
        
        if opcao == "1":
            menu_gerenciar_produtos(estoque)
        elif opcao == "2":
            menu_gerenciar_cupons(estoque)
        elif opcao == "3":
            gerar_relatorio_vendas(estoque)
        elif opcao == "4":
            print("Saindo do sistema...")
            estoque.salvar_dados()
            break
        else:
            print("Opção inválida. Tente novamente.")

def menu_gerenciar_produtos(estoque):
    while True:
        print("\n--- GERENCIAR PRODUTOS ---")
        print("1. Adicionar produto")
        print("2. Remover produto")
        print("3. Listar produtos")
        print("4. Atualizar estoque")
        print("5. Voltar")
        
        opcao = input("Escolha uma opção: ")
        
        if opcao == "1":
            codigo = input("Código do produto: ")
            nome = input("Nome do produto: ")
            preco = float(input("Preço do produto: R$"))
            quantidade = int(input("Quantidade em estoque: "))
            categoria = input("Categoria (opcional): ") or None
            
            produto = Produto(codigo, nome, preco, quantidade, categoria)
            estoque.adicionar_produto(produto)
        
        elif opcao == "2":
            codigo = input("Código do produto a remover: ")
            estoque.remover_produto(codigo)
        
        elif opcao == "3":
            categoria = input("Filtrar por categoria (deixe em branco para todas): ") or None
            estoque.listar_produtos(categoria)
        
        elif opcao == "4":
            codigo = input("Código do produto: ")
            quantidade = int(input("Quantidade a adicionar (negativo para remover): "))
            estoque.atualizar_estoque(codigo, quantidade)
        
        elif opcao == "5":
            break
        
        else:
            print("Opção inválida. Tente novamente.")

def menu_gerenciar_cupons(estoque):
    while True:
        print("\n--- GERENCIAR CUPONS ---")
        print("1. Criar cupom")
        print("2. Listar cupons válidos")
        print("3. Listar todos os cupons")
        print("4. Voltar")
        
        opcao = input("Escolha uma opção: ")
        
        if opcao == "1":
            estoque.criar_cupom()
        elif opcao == "2":
            estoque.listar_cupons_validos()
        elif opcao == "3":
            print("\n--- TODOS OS CUPONS ---")
            for cupom in estoque.cupons:
                status = " (USADO)" if cupom.usado else " (VÁLIDO)" if datetime.strptime(cupom.valido_ate, "%d/%m/%Y") >= datetime.now() else " (EXPIRADO)"
                print(f"Código: {cupom.codigo} | Desconto: {cupom.desconto}% | Válido até: {cupom.valido_ate}{status}")
            print("----------------------")
        elif opcao == "4":
            break
        else:
            print("Opção inválida. Tente novamente.")

def gerar_relatorio_vendas(estoque):
    if estoque.usuario_logado.tipo != 'admin':
        print("Acesso negado. Somente administradores podem ver relatórios de vendas.")
        return
    
    print("\n--- RELATÓRIO DE VENDAS ---")
    
    if not estoque.vendas:
        print("Nenhuma venda registrada.")
        return
    
    total_vendas = sum(v['total'] for v in estoque.vendas)
    total_descontos = sum(v['desconto'] for v in estoque.vendas)
    
    print(f"Total de vendas: R${total_vendas:.2f}")
    print(f"Total de descontos aplicados: R${total_descontos:.2f}")
    print(f"Valor líquido: R${total_vendas - total_descontos:.2f}")
    
    print("\nÚltimas 10 vendas:")
    for venda in estoque.vendas[-10:]:
        print(f"\nData: {venda['data']}")
        print(f"Cupom usado: {venda.get('cupom', 'Nenhum')}")
        print(f"Subtotal: R${venda['subtotal']:.2f}")
        print(f"Desconto: R${venda['desconto']:.2f}")
        print(f"Total: R${venda['total']:.2f}")
        print("Itens:")
        for item in venda['itens']:
            print(f"- {item['quantidade']} x {item['nome']}")
    
    print("\n----------------------")

def menu_cliente(estoque):
    carrinho = Carrinho()
    
    while True:
        print("\n--- MENU CLIENTE ---")
        print("1. Listar produtos")
        print("2. Adicionar ao carrinho")
        print("3. Ver carrinho")
        print("4. Aplicar cupom")
        print("5. Finalizar compra")
        print("6. Ver cupons válidos")
        print("7. Ver histórico de compras")
        print("8. Sair")
        
        opcao = input("Escolha uma opção: ")
        
        if opcao == "1":
            categoria = input("Filtrar por categoria (deixe em branco para todas): ") or None
            estoque.listar_produtos(categoria)
        
        elif opcao == "2":
            codigo = input("Código do produto: ")
            quantidade = int(input("Quantidade: "))
            
            produto = next((p for p in estoque.produtos if p.codigo == codigo), None)
            if produto:
                if produto.quantidade >= quantidade:
                    carrinho.adicionar_item(produto, quantidade)
                    print(f"{quantidade} x {produto.nome} adicionado ao carrinho.")
                else:
                    print("Quantidade indisponível em estoque.")
            else:
                print("Produto não encontrado.")
        
        elif opcao == "3":
            if not carrinho.itens:
                print("Carrinho vazio.")
                continue
                
            print("\n--- SEU CARRINHO ---")
            for item in carrinho.itens:
                print(f"{item['quantidade']} x {item['produto'].nome} - R${item['produto'].preco:.2f} cada")
            
            subtotal = sum(item['produto'].preco * item['quantidade'] for item in carrinho.itens)
            desconto = carrinho.cupom_aplicado.desconto if carrinho.cupom_aplicado else 0
            total = subtotal * (1 - desconto/100) if carrinho.cupom_aplicado else subtotal
            
            if carrinho.cupom_aplicado:
                print(f"\nCupom aplicado: {carrinho.cupom_aplicado.codigo} ({carrinho.cupom_aplicado.desconto}% de desconto)")
                print(f"Subtotal: R${subtotal:.2f}")
                print(f"Desconto: R${subtotal * (desconto/100):.2f}")
            
            print(f"\nTOTAL: R${total:.2f}")
            print("--------------------")
        
        elif opcao == "4":
            if not carrinho.itens:
                print("Adicione produtos ao carrinho antes de aplicar cupom.")
                continue
                
            codigo = input("Digite o código do cupom: ").upper()
            cupom = estoque.verificar_cupom(codigo)
            
            if cupom:
                carrinho.aplicar_cupom(cupom)
                print(f"Cupom {codigo} aplicado com sucesso! Desconto de {cupom.desconto}%")
            else:
                print("Cupom inválido, expirado ou já utilizado.")
        
        elif opcao == "5":
            if not carrinho.itens:
                print("Carrinho vazio. Adicione produtos antes de finalizar.")
                continue
                
            compra = carrinho.finalizar_compra(estoque, estoque.usuario_logado)
            estoque.vendas.append(compra)
            
            nome_arquivo = estoque.gerar_nota_fiscal(compra, estoque.usuario_logado)
            
            estoque.salvar_dados()
            
            print("\n--- COMPRA FINALIZADA ---")
            print(f"Data: {compra['data']}")
            if compra.get('cupom'):
                print(f"Cupom usado: {compra['cupom']}")
                print(f"Subtotal: R${compra['subtotal']:.2f}")
                print(f"Desconto: R${compra['desconto']:.2f}")
            print(f"Total: R${compra['total']:.2f}")
            print(f"\nNota fiscal gerada: {nome_arquivo}")
            print("------------------------")
        
        elif opcao == "6":
            estoque.listar_cupons_validos()
        
        elif opcao == "7":
            if not estoque.usuario_logado.historico:
                print("Nenhuma compra registrada.")
                continue
                
            print("\n--- SEU HISTÓRICO ---")
            for i, compra in enumerate(estoque.usuario_logado.historico, 1):
                print(f"\nCompra #{i} - {compra['data']}")
                if compra.get('cupom'):
                    print(f"Cupom usado: {compra['cupom']}")
                for item in compra['itens']:
                    print(f"{item['quantidade']} x {item['nome']}")
                print(f"Total: R${compra['total']:.2f}")
            print("---------------------")
        
        elif opcao == "8":
            print("Saindo do sistema...")
            break
        
        else:
            print("Opção inválida. Tente novamente.")

def main():
    estoque = Estoque()
    
    print("\n=== SISTEMA DE ESTOQUE E VENDAS ===")
    while True:
        print("\n1. Login")
        print("2. Cadastrar-se")
        print("3. Sair")
        
        opcao = input("Escolha uma opção: ")
        
        if opcao == "1":
            if estoque.login():
                if estoque.usuario_logado.tipo == 'admin':
                    menu_admin(estoque)
                else:
                    menu_cliente(estoque)
        
        elif opcao == "2":
            estoque.cadastrar_usuario()
        
        elif opcao == "3":
            print("Saindo do sistema...")
            estoque.salvar_dados()
            break
        
        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main()
