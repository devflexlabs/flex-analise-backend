# 🍎 Guia de Instalação para macOS

Este guia ajuda a resolver problemas comuns ao instalar as dependências do projeto no macOS.

## ⚠️ Problemas Comuns

### 1. Erro: `env: python: No such file or directory`

**Causa:** O macOS geralmente só tem `python3`, não `python`. Alguns pacotes tentam usar `python` diretamente.

**Solução:** Use o script de setup automático:
```bash
chmod +x scripts/setup_macos.sh
./scripts/setup_macos.sh
```

### 2. Erro ao compilar `scikit-image`

**Causa:** Falta de dependências de build ou Python muito novo (3.14).

**Soluções:**

**Opção A - Instalar dependências de build:**
```bash
brew install pkg-config meson ninja
pip install scikit-image
```

**Opção B - Usar Python 3.11 ou 3.12 (recomendado):**
```bash
# Instalar Python 3.12 via Homebrew
brew install python@3.12

# Criar venv com Python 3.12
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Opção C - Pular easyocr (se não precisar de OCR local):**
```bash
pip install -r requirements-no-ocr.txt
```

### 3. Python 3.14 muito novo

Python 3.14 é muito recente e algumas dependências podem não ter wheels pré-compilados, forçando compilação do código-fonte.

**Recomendação:** Use Python 3.11 ou 3.12 para melhor compatibilidade.

```bash
# Verificar versão atual
python3 --version

# Instalar Python 3.12 via Homebrew
brew install python@3.12

# Usar Python 3.12
python3.12 -m venv venv
source venv/bin/activate
```

### 4. Erro: `pkg-config: command not found`

**Solução:**
```bash
brew install pkg-config
```

### 5. Erro ao instalar `easyocr`

`easyocr` depende de `scikit-image` e `torch`, que podem ser pesados de instalar.

**Soluções:**

**Opção A - Instalar sem easyocr:**
```bash
pip install -r requirements-no-ocr.txt
```

O sistema ainda funcionará usando:
- Tesseract OCR (local)
- Google Vision API (se configurado)
- AWS Textract (se configurado)

**Opção B - Instalar easyocr separadamente depois:**
```bash
# Primeiro instalar dependências básicas
pip install torch torchvision
pip install scikit-image
pip install easyocr
```

## 🚀 Instalação Rápida (Recomendado)

```bash
# 1. Instalar Homebrew (se não tiver)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Instalar Python 3.12 (recomendado)
brew install python@3.12

# 3. Executar script de setup
chmod +x scripts/setup_macos.sh
./scripts/setup_macos.sh
```

## 🔍 Verificação

Após a instalação, verifique se tudo está funcionando:

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Verificar instalação
python --version
pip list | grep -E "(openai|langchain|fastapi|scikit-image)"

# Testar importação
python -c "import openai, langchain, fastapi; print('✅ Dependências OK')"
```

## 📝 Notas Adicionais

- **Homebrew:** Se você não tem Homebrew instalado, instale primeiro: https://brew.sh
- **Xcode Command Line Tools:** Pode ser necessário instalar: `xcode-select --install`
- **Ambiente Virtual:** Sempre use um ambiente virtual para isolar as dependências
- **OCR:** Se não precisar de OCR local, use `requirements-no-ocr.txt` para instalação mais rápida

## 🆘 Ainda com Problemas?

1. Verifique a versão do Python: `python3 --version`
2. Verifique se tem Homebrew: `brew --version`
3. Tente instalar dependências uma por uma para identificar qual está falhando
4. Considere usar Python 3.11 ou 3.12 em vez de 3.14




