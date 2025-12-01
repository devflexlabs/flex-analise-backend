#!/bin/bash

# Script de setup para macOS - Resolve problemas de instalação de dependências
# Uso: ./scripts/setup_macos.sh

set -e

echo "🍎 Configurando ambiente para macOS..."

# Verifica se Homebrew está instalado
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew não encontrado. Instalando Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Instala dependências de build necessárias
echo "📦 Instalando dependências de build..."
brew install pkg-config meson ninja

# Verifica versão do Python
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "🐍 Python detectado: $PYTHON_VERSION"

# Python 3.14 pode ter problemas com algumas dependências
# Recomenda usar Python 3.11 ou 3.12
if [[ "$PYTHON_VERSION" == 3.14* ]]; then
    echo "⚠️  Python 3.14 detectado. Algumas dependências podem não ter wheels pré-compilados."
    echo "💡 Recomendação: Use Python 3.11 ou 3.12 para melhor compatibilidade."
    echo ""
    read -p "Deseja continuar mesmo assim? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo "Instalação cancelada."
        exit 1
    fi
fi

# Cria um ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "🔧 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativa o ambiente virtual
echo "🔌 Ativando ambiente virtual..."
source venv/bin/activate

# Atualiza pip
echo "⬆️  Atualizando pip..."
pip install --upgrade pip setuptools wheel

# Instala dependências básicas primeiro
echo "📚 Instalando dependências básicas..."
pip install numpy scipy pillow

# Tenta instalar scikit-image com uma versão específica que tem melhor suporte
echo "🖼️  Instalando scikit-image..."
pip install scikit-image || {
    echo "⚠️  Falha ao instalar scikit-image. Tentando versão alternativa..."
    pip install scikit-image==0.22.0 || {
        echo "❌ Falha ao instalar scikit-image. Você pode pular easyocr se não precisar de OCR."
        echo "💡 Para instalar sem easyocr, remova a linha 'easyocr>=1.7.0' do requirements.txt"
    }
}

# Instala as demais dependências
echo "📦 Instalando demais dependências..."
pip install -r requirements.txt || {
    echo "⚠️  Algumas dependências falharam. Tentando instalar sem easyocr..."
    # Cria um requirements temporário sem easyocr
    grep -v "easyocr" requirements.txt > requirements_temp.txt || true
    pip install -r requirements_temp.txt
    rm -f requirements_temp.txt
    echo "✅ Dependências instaladas (sem easyocr)."
    echo "💡 Se precisar de OCR, instale easyocr separadamente depois."
}

echo ""
echo "✅ Setup concluído!"
echo ""
echo "Para usar o ambiente virtual:"
echo "  source venv/bin/activate"
echo ""
echo "Para desativar:"
echo "  deactivate"


