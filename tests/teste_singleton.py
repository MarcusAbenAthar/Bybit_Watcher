from plugins.conexao import Conexao

# Get the instance
conexao1 = Conexao()
conexao2 = Conexao()

# Check if they are the same instance
print(conexao1 is conexao2)  # Should print True
print(conexao1)
print(conexao2)
