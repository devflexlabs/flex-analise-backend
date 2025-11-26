"""
Aplicação web para extração de informações de contratos financeiros.
Interface com upload de PDF e visualização dos resultados.
"""
import streamlit as st
import json
from backend.processors.document_processor import DocumentProcessor
import os
from dotenv import load_dotenv
from datetime import datetime

# Carrega variáveis de ambiente da pasta config ou raiz
from pathlib import Path
env_path = Path(__file__).parent.parent.parent / "config" / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Configuração da página
st.set_page_config(
    page_title="Extrator de Contratos Financeiros",
    page_icon="📄",
    layout="wide"
)

# Título e descrição
st.title("📄 Extrator de Contratos Financeiros")
st.markdown("""
Esta aplicação utiliza IA para extrair automaticamente informações de contratos financeiros.
Anexe um PDF e obtenha os dados estruturados em segundos.
""")

# Verifica qual IA está disponível
has_ollama = False
has_groq = bool(os.getenv("GROQ_API_KEY"))
has_openai = bool(os.getenv("OPENAI_API_KEY"))

# Verifica Ollama (local, sem API key)
try:
    import ollama
    ollama.list()  # Testa se está rodando
    has_ollama = True
except:
    pass

has_any_ia = has_ollama or has_groq or has_openai
demo_mode = not has_any_ia

if demo_mode:
    from backend.extractors.simple_extractor import SimpleContractExtractor
    st.error("⚠️ **ATENÇÃO: Modo Demo com Limitações Sérias**")
    st.warning("🚨 **Quota do Gemini excedida ou sem IA configurada**")
    st.markdown("""
    **O modo demo usa extração básica (regex) que NÃO funciona bem com formatos variados.**
    
    **Configure uma IA gratuita ou barata:**
    """)
    
    with st.expander("🆓 Opção 1: Ollama (100% GRATUITO - Recomendado)"):
        st.markdown("""
        **Instalação (2 minutos):**
        1. Baixe em: https://ollama.ai
        2. Instale o programa
        3. Abra o terminal e execute: `ollama pull llama3.2`
        4. Pronto! Não precisa de chave de API
        
        **Vantagens:**
        - ✅ 100% gratuito (sem custos)
        - ✅ Roda localmente (seus dados não saem do seu computador)
        - ✅ Sem limites de uso
        - ✅ Funciona offline
        
        **Reinicie a aplicação após instalar!**
        """)
    
    with st.expander("💰 Opção 2: Groq (GRATUITO)"):
        st.markdown("""
        **Configuração:**
        1. Acesse: https://console.groq.com/keys
        2. Crie conta (grátis)
        3. Crie uma API key
        4. No arquivo `.env`, adicione: `GROQ_API_KEY=sua_chave_aqui`
        5. Reinicie a aplicação
        
        **Custo:** Gratuito para uso moderado
        """)
    
    st.markdown("---")
    st.markdown("**⚠️ Você pode continuar testando o modo demo, mas os resultados podem estar INCORRETOS ou INCOMPLETOS.**")
else:
    # Usa o extrator múltiplo que detecta automaticamente qual IA usar
    from backend.extractors.contract_extractor_multiplo import ContractExtractorMultiplo
    
    # Mostra qual IA está sendo usada
    if has_ollama:
        st.success("✅ Usando Ollama (100% GRATUITO)")
    elif has_groq:
        st.success("✅ Usando Groq (GRATUITO)")
    elif has_openai:
        st.info("ℹ️ Usando OpenAI")

# Função auxiliar para formatar datas
def formatar_data(data_str: str) -> str:
    """
    Formata data de YYYY-MM-DD para DD/MM/YYYY (padrão brasileiro).
    """
    if not data_str:
        return data_str
    
    try:
        # Tenta parsear no formato YYYY-MM-DD
        if len(data_str) == 10 and data_str.count('-') == 2:
            data_obj = datetime.strptime(data_str, "%Y-%m-%d")
            return data_obj.strftime("%d/%m/%Y")
        # Se já estiver em outro formato, tenta parsear e formatar
        elif len(data_str) == 10 and data_str.count('/') == 2:
            # Já está no formato DD/MM/YYYY ou MM/DD/YYYY
            try:
                data_obj = datetime.strptime(data_str, "%d/%m/%Y")
                return data_obj.strftime("%d/%m/%Y")
            except:
                try:
                    data_obj = datetime.strptime(data_str, "%m/%d/%Y")
                    return data_obj.strftime("%d/%m/%Y")
                except:
                    return data_str
        else:
            return data_str
    except:
        # Se não conseguir parsear, retorna como está
        return data_str

# Função auxiliar para formatar valores monetários no padrão brasileiro
def formatar_moeda(valor: float) -> str:
    """
    Formata valor monetário no padrão brasileiro: R$ 19.653,70
    """
    if valor is None or valor == 0:
        return "R$ 0,00"
    
    try:
        # Converte para inteiro de centavos para evitar problemas de ponto flutuante
        valor_centavos = int(round(valor * 100))
        inteiro = valor_centavos // 100
        decimal = valor_centavos % 100
        
        # Formata parte inteira com pontos para milhares
        inteiro_str = f"{inteiro:,}".replace(',', '.')
        
        # Formata decimal com 2 dígitos
        decimal_str = f"{decimal:02d}"
        
        return f"R$ {inteiro_str},{decimal_str}"
    except:
        # Fallback simples
        return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# Sidebar com informações
with st.sidebar:
    st.header("ℹ️ Sobre")
    st.markdown("""
    **Funcionalidades:**
    - ✅ Upload de PDF
    - ✅ Extração automática de informações
    - ✅ Visualização estruturada
    - ✅ Exportação em JSON
    
    **Informações extraídas:**
    - Nome do cliente
    - Valor da dívida
    - Quantidade de parcelas
    - Valor das parcelas
    - Datas de vencimento
    - Taxa de juros
    - E muito mais...
    """)
    
    st.markdown("---")
    if demo_mode:
        st.markdown("**Modo:** Demo (Extração Básica)")
        st.markdown("**Status:** ⚠️ Sem IA Configurada")
    else:
        if has_ollama:
            st.markdown("**Modo:** IA (Ollama)")
            st.markdown("**Status:** ✅ Gratuito")
        elif has_groq:
            st.markdown("**Modo:** IA (Groq)")
            st.markdown("**Status:** ✅ Gratuito")
        elif has_openai:
            st.markdown("**Modo:** IA (OpenAI)")
            st.markdown("**Status:** ✅ Configurado")
    st.markdown("---")
    st.markdown("**Desenvolvido com:**")
    if not demo_mode:
        st.markdown("- OpenAI GPT")
    st.markdown("- Streamlit")
    st.markdown("- LangChain")

# Área de upload
st.header("📤 Upload do Contrato")

uploaded_file = st.file_uploader(
    "Selecione um arquivo PDF ou imagem (JPEG, PNG)",
    type=['pdf', 'jpg', 'jpeg', 'png'],
    help="Faça upload do contrato em formato PDF ou imagem (JPEG/PNG). Imagens serão processadas com OCR."
)

# Processa o arquivo quando enviado
if uploaded_file is not None:
    # Salva o arquivo temporariamente
    with st.spinner("Processando arquivo..."):
        # Salva em arquivo temporário
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        try:
            # Detecta tipo de arquivo
            file_ext = uploaded_file.name.lower().split('.')[-1]
            is_image = file_ext in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif']
            
            # Inicializa o extrator (demo ou com IA)
            if demo_mode:
                extractor = SimpleContractExtractor()
                with st.spinner("📄 Processando contrato (modo demo - pode estar incorreto)..."):
                    if is_image:
                        # Para imagens, extrai texto com OCR primeiro
                        from backend.processors.document_processor import DocumentProcessor
                        doc_processor = DocumentProcessor()
                        texto_extraido = doc_processor.extract_text_from_image(temp_path)
                        resultado = extractor.extract_from_text(texto_extraido)
                    else:
                        resultado = extractor.extract_from_pdf(temp_path)
            else:
                # Usa o extrator múltiplo que detecta automaticamente qual IA usar
                # Groq tem prioridade (gratuito e rápido)
                extractor = ContractExtractorMultiplo(provider="auto")
                if is_image:
                    with st.spinner("📷 Processando imagem com OCR e analisando com IA..."):
                        # Para imagens, extrai texto com OCR primeiro
                        from backend.processors.document_processor import DocumentProcessor
                        doc_processor = DocumentProcessor()
                        texto_extraido = doc_processor.extract_text_from_image(temp_path)
                        resultado = extractor.extract_from_text(texto_extraido)
                else:
                    with st.spinner("🤖 Analisando contrato com IA..."):
                        resultado = extractor.extract_from_pdf(temp_path)
            
            # Remove arquivo temporário
            os.remove(temp_path)
            
            # Exibe resultados
            if demo_mode:
                st.warning("⚠️ **Resultados do modo demo** - Verifique cuidadosamente! Podem estar INCORRETOS ou INCOMPLETOS!")
                if resultado.quantidade_parcelas == 0 or resultado.valor_divida == 0.0:
                    st.error("🚨 **ATENÇÃO:** Dados críticos não foram extraídos corretamente (parcelas=0 ou valor=0). Configure a IA para resultados precisos!")
            else:
                st.success("✅ Contrato processado com sucesso!")
            
            st.header("📊 Informações Extraídas")
            
            if demo_mode:
                st.info("💡 **Importante:** Verifique os dados extraídos. O modo demo pode ter errado valores, nomes ou parcelas. Para precisão, configure a IA.")
            
            # Organiza informações em colunas
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("👤 Dados do Cliente")
                st.markdown(f"**Nome:** {resultado.nome_cliente}")
                if resultado.cpf_cnpj:
                    st.markdown(f"**CPF/CNPJ:** {resultado.cpf_cnpj}")
                if resultado.numero_contrato:
                    st.markdown(f"**Nº Contrato:** {resultado.numero_contrato}")
                if resultado.tipo_contrato:
                    st.markdown(f"**Tipo:** {resultado.tipo_contrato}")
            
            with col2:
                st.subheader("💰 Valores")
                if resultado.valor_divida:
                    st.markdown(f"**Valor da Dívida:** {formatar_moeda(resultado.valor_divida)}")
                st.markdown(f"**Parcelas:** {resultado.quantidade_parcelas}")
                if resultado.valor_parcela:
                    st.markdown(f"**Valor da Parcela:** {formatar_moeda(resultado.valor_parcela)}")
                if resultado.taxa_juros:
                    st.markdown(f"**Taxa de Juros:** {resultado.taxa_juros}%")
            
            # Datas
            if resultado.data_vencimento_primeira or resultado.data_vencimento_ultima:
                st.subheader("📅 Datas de Vencimento")
                col3, col4 = st.columns(2)
                with col3:
                    if resultado.data_vencimento_primeira:
                        # Formata data para padrão brasileiro (DD/MM/YYYY)
                        data_formatada = formatar_data(resultado.data_vencimento_primeira)
                        st.markdown(f"**Primeira Parcela:** {data_formatada}")
                with col4:
                    if resultado.data_vencimento_ultima:
                        # Formata data para padrão brasileiro (DD/MM/YYYY)
                        data_formatada = formatar_data(resultado.data_vencimento_ultima)
                        st.markdown(f"**Última Parcela:** {data_formatada}")
            
            # Observações - mostra exatamente como vem do JSON, sem formatação
            if resultado.observacoes:
                st.subheader("📝 Observações")
                st.text(resultado.observacoes)
            
            # Exibe dados completos em formato JSON
            with st.expander("🔍 Ver dados completos (JSON)"):
                st.json(resultado.model_dump())
            
            # Botão para download do JSON
            json_str = json.dumps(resultado.model_dump(), indent=2, ensure_ascii=False)
            st.download_button(
                label="💾 Baixar resultado em JSON",
                data=json_str,
                file_name=f"contrato_extraido_{resultado.numero_contrato or 'sem_numero'}.json",
                mime="application/json"
            )
            
        except Exception as e:
            # Remove arquivo temporário em caso de erro
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            st.error(f"❌ Erro ao processar o contrato: {str(e)[:500]}")
            
            # Mensagens de ajuda específicas
            if "429" in str(e) or "quota" in str(e).lower() or "Quota exceeded" in str(e) or "rate limit" in str(e).lower():
                st.error("🚨 **QUOTA EXCEDIDA!**")
                st.markdown("""
                **Limite de requisições atingido. Soluções:**
                
                **Opção 1: Aguarde** ⏰
                - Aguarde alguns minutos e tente novamente
                
                **Opção 2: Ollama (100% GRATUITO, SEM LIMITES)** 🆓
                1. Baixe: https://ollama.ai
                2. Instale o programa
                3. Terminal: `ollama pull llama3.2`
                4. Reinicie a aplicação
                """)
            elif "404" in str(e) or "not found" in str(e).lower():
                st.warning("💡 **Erro de modelo:** O modelo da IA não foi encontrado. Verifique a configuração.")
            elif "API" in str(e) or "api_key" in str(e).lower():
                st.warning("💡 **Erro de API:** Verifique se a chave da API está correta no arquivo .env")
            elif "Tesseract" in str(e) or "OCR" in str(e):
                st.error("🚨 **Tesseract OCR não instalado!**")
                st.markdown("""
                **Para processar imagens, você precisa instalar o Tesseract OCR:**
                
                **Windows:**
                1. Baixe: https://github.com/UB-Mannheim/tesseract/wiki
                2. Instale o programa
                3. Adicione ao PATH ou configure a variável de ambiente
                
                **Linux:**
                ```bash
                sudo apt-get install tesseract-ocr
                sudo apt-get install tesseract-ocr-por  # Para português
                ```
                
                **Mac:**
                ```bash
                brew install tesseract
                brew install tesseract-lang  # Para português
                ```
                
                Após instalar, reinicie a aplicação.
                """)
            else:
                st.info("Verifique se o arquivo é um PDF válido e contém texto legível.")

else:
    # Instruções quando não há arquivo
    st.info("👆 Faça upload de um arquivo PDF ou imagem (JPEG/PNG) acima para começar a extração.")
    
    # Mostra exemplo
    with st.expander("📋 Exemplo de informações que serão extraídas"):
        exemplo = {
            "nome_cliente": "João Silva",
            "valor_divida": 50000.00,
            "quantidade_parcelas": 60,
            "valor_parcela": 1250.00,
            "data_vencimento_primeira": "2024-02-15",
            "data_vencimento_ultima": "2029-01-15",
            "taxa_juros": 2.5,
            "numero_contrato": "CT-2024-001",
            "cpf_cnpj": "123.456.789-00",
            "tipo_contrato": "Financiamento"
        }
        st.json(exemplo)

