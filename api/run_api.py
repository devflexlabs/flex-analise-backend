"""
Script wrapper para executar a API.
Facilita a execução mantendo o diretório raiz no path.
"""
import sys
from pathlib import Path
import os

# Adiciona o diretório raiz ao path (sobe 3 níveis: api -> backend -> raiz)
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Muda o diretório de trabalho para a raiz
os.chdir(root_dir)

# Importa e executa a API
if __name__ == "__main__":
    import uvicorn
    # Usa string de importação para o reload funcionar
    uvicorn.run("backend.api.api_server:app", host="0.0.0.0", port=8000, reload=True)

