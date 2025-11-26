# Sistema de Extração de Informações de Contratos Financeiros

Sistema que utiliza LLM (Large Language Model) para extrair informações estruturadas de contratos financeiros.

## Funcionalidades

- Extrai informações de contratos financeiros (PDF ou texto)
- Identifica automaticamente:
  - Nome do cliente
  - Valor da dívida
  - Quantidade de parcelas
  - Datas importantes
  - Outras informações relevantes

## Instalação

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Configure sua chave da API OpenAI:
   - Crie um arquivo `.env` na raiz do projeto
   - Adicione: `OPENAI_API_KEY=sua_chave_aqui`
   - (Você pode copiar o arquivo `.env.example` como base)

## Uso

### Opção 1: Interface Web (Recomendado) 🚀

A forma mais fácil de usar o sistema é através da interface web:

```bash
python -m streamlit run app.py
```

A aplicação abrirá no navegador onde você pode:
- 📤 Fazer upload de PDFs
- 🤖 Processar automaticamente com IA
- 📊 Visualizar resultados formatados
- 💾 Baixar dados em JSON

### Opção 2: Script Rápido (Linha de Comando)
```bash
python quick_extract.py contrato.pdf
```
O resultado será exibido no console e salvo em um arquivo JSON.

### Opção 3: Usando Python

#### Processar um contrato PDF:
```python
from contract_extractor import ContractExtractor

extractor = ContractExtractor()
result = extractor.extract_from_pdf("caminho/para/contrato.pdf")
print(result)
```

#### Processar um contrato de texto:
```python
result = extractor.extract_from_text("texto do contrato aqui...")
print(result)
```

#### Retornar como dicionário:
```python
result_dict = extractor.extract_to_dict(pdf_path="contrato.pdf")
# ou
result_dict = extractor.extract_to_dict(text="texto do contrato...")
```

### Opção 4: Executar Exemplos
```bash
python example.py
```

## Estrutura do Projeto

- `app.py` - **Aplicação web principal (Streamlit)** - Interface para upload de PDFs
- `contract_extractor.py` - Módulo principal de extração usando LLM
- `models.py` - Modelos de dados para informações extraídas (Pydantic)
- `document_processor.py` - Processamento de documentos (PDF/texto)
- `example.py` - Exemplos de uso detalhados
- `quick_extract.py` - Script rápido para linha de comando
- `.env.example` - Exemplo de arquivo de configuração
- `iniciar.bat` / `iniciar.sh` - Scripts para iniciar a aplicação web rapidamente

## Informações Extraídas

O sistema extrai automaticamente:
- ✅ Nome do cliente
- ✅ Valor da dívida
- ✅ Quantidade de parcelas
- ✅ Valor de cada parcela
- ✅ Datas de vencimento
- ✅ Taxa de juros
- ✅ Número do contrato
- ✅ CPF/CNPJ
- ✅ Tipo de contrato
- ✅ Observações relevantes

## Requisitos

- Python 3.8+
- Chave da API OpenAI (ou outra LLM compatível)

