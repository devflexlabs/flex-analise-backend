"""
Extrator de contratos com suporte a múltiplas IAs (OpenAI, Ollama, Groq, Gemini).

NOTAS SOBRE RECÁLCULO COM BASE NO BACEN:
=========================================
Para implementar recálculo de contratos com base em dados do BACEN, será necessário:

1. METODOLOGIA DE AMORTIZAÇÃO:
   - Identificar qual tabela foi usada: Price (parcelas fixas) ou SAC (amortização constante)
   - Price: PMT = PV * [i(1+i)^n] / [(1+i)^n - 1]
   - SAC: Amortização = PV / n, Juros = Saldo * i, Parcela = Amortização + Juros
   - O contrato geralmente indica a metodologia, mas pode não estar explícito

2. ACESSO A SÉRIES TEMPORAIS DO BACEN:
   - API do BACEN: https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados
   - Taxa Selic: código 11 (ao dia) ou 432 (ao mês)
   - CDI: código 12 (ao dia)
   - IPCA: código 433 (ao mês)
   - Para taxas históricas: usar data de contratação do contrato
   - Exemplo: se contrato foi assinado em 15/03/2024, buscar taxa Selic de 15/03/2024

3. TAXAS PÓS-FIXADAS:
   - Se contrato for assinado hoje com taxa pós-fixada (ex: CDI + 2% a.a.):
     * A taxa efetiva só será conhecida 30 dias após (quando o CDI do período for divulgado)
     * Para análise imediata: usar CDI atual como estimativa
     * Adicionar aviso: "Taxa pós-fixada - valor final só será conhecido após período de referência"
   - Para contratos antigos: buscar taxa histórica do período de referência

4. IMPLEMENTAÇÃO FUTURA:
   - Criar módulo bacen_integration.py para buscar séries temporais
   - Criar módulo financial_calculator.py para cálculos (Price, SAC, juros compostos)
   - Validar cálculos do contrato vs. recálculo com taxas BACEN
   - Identificar divergências que possam indicar irregularidades
"""
import os
from typing import Optional
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from backend.processors.document_processor import DocumentProcessor
from backend.models.models import ContratoInfo
from backend.calculators.recalculo_bacen import RecalculoBacen

from pathlib import Path
import os

# Carrega .env da pasta backend/config ou raiz
env_path = Path(__file__).parent.parent / "config" / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)


class ContractExtractorMultiplo:
    """Extrai informações de contratos usando diferentes IAs (OpenAI, Ollama, Groq, Gemini)."""
    
    def __init__(self, provider: str = "auto", model_name: Optional[str] = None):
        """
        Inicializa o extrator.
        
        Args:
            provider: "openai", "ollama", "groq", "gemini", ou "auto" (detecta automaticamente)
            model_name: Nome do modelo (opcional, usa padrão por provider)
        """
        self.provider = provider.lower()
        self.document_processor = DocumentProcessor()
        self.output_parser = PydanticOutputParser(pydantic_object=ContratoInfo)
        self.recalculador = RecalculoBacen()  # Inicializa recalculador BACEN
        
        # Se auto, detecta qual está disponível
        if self.provider == "auto":
            self.provider = self._detectar_provider()
        
        # Inicializa o LLM baseado no provider
        self.llm = self._inicializar_llm(model_name)
        
        # Template do prompt - CALIBRADO para máxima assertividade
        # Este prompt foi refinado para:
        # 1. Extração mais precisa de dados numéricos e datas
        # 2. Análise crítica mais assertiva de irregularidades
        # 3. Identificação mais confiável de bancos/instituições
        # 4. Melhor tratamento de diferentes formatos de contrato
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """Você é um especialista em análise de contratos financeiros brasileiros com conhecimento profundo em:
- Legislação brasileira (CDC, normas BACEN/CMN)
- Cálculos financeiros (tabela Price, SAC, juros compostos)
- Identificação de práticas abusivas em contratos bancários
- Análise crítica de taxas, encargos e cláusulas contratuais

Sua tarefa é extrair informações estruturadas de contratos financeiros com MÁXIMA PRECISÃO, independente do formato ou ordem das informações.

CRITÉRIOS DE QUALIDADE:
- PRECISÃO NUMÉRICA: Todos os valores monetários, taxas e datas devem ser extraídos EXATAMENTE como aparecem
- ANÁLISE CRÍTICA: Identifique TODAS as irregularidades e práticas abusivas possíveis
- COMPLETUDE: Não deixe campos importantes vazios se a informação estiver disponível no documento

IMPORTANTE: 
- Os contratos podem ter formatos COMPLETAMENTE DIFERENTES (cada banco/financeira tem seu próprio layout)
- Pode ser contrato ORIGINAL ou ADITIVO DE RENEGOCIAÇÃO
- As informações podem estar em qualquer ordem e com nomenclaturas diferentes
- Procure por sinônimos e variações (ex: "emitente", "devedor", "cliente", "contratante")
- Valores podem estar escritos de várias formas (R$ 50.000,00, R$ 50000.00, 50000 reais, etc.)
- SEJA METICULOSO: Leia cada seção do documento, incluindo rodapés, cabeçalhos e anexos

CAMpos E VARIAÇÕES COMUNS:
- Nome do cliente: "Nome/Razão Social", "Cliente", "Emitente", "Devedor", "Contratante", "Solicitante"
- Valor da dívida: "Valor Total Financiado", "Valor Total do Crédito", "Valor Total Confessado", "Saldo Devedor Remanescente", "Valor Total a Pagar", "Valor do Financiamento"
- Parcelas: "Quantidade de parcelas", "Número de parcelas", pode estar como "(II) Quantidade de parcelas", "053 parcelas", etc.
- Valor parcela: "Valor das parcelas", "(I) Valor das parcelas", "Valor de cada parcela mensal", "Parcela de"
- Datas: "Vencimento da 1ª parcela", "Data do 1° Vencimento", "Primeira parcela", formato pode ser DD/MM/YYYY ou DD-MM-YYYY
- Taxa juros: "Taxa de juros da operação", "Taxa de juros", "Juros Remuneratórios", "Taxa de juros mensal", "Taxa de juros anual" 
  * CRÍTICO: NÃO confundir com CET (Custo Efetivo Total). Priorize sempre a "Taxa de juros da operação"
  * Pode estar como "% a.m." (ao mês), "% a.a." (ao ano), ou apenas "%" (assuma mensal se não especificado)
  * Se encontrar taxa anual, converta para mensal usando: (1 + taxa_anual)^(1/12) - 1
  * Se encontrar taxa mensal, mantenha como está
  * Se encontrar apenas CET, deixe taxa_juros como null (CET não é taxa de juros)
- Número contrato: "Nº", "Número", "Proposta", "Contrato nº", "Cédula de Crédito Bancário Nº", "Aditivo de Renegociação nº"
- Banco/Instituição Financeira: Procure por logo, nome da instituição, "Instituição Financeira", "Credor", "Banco", "Financeira", "AYMORÉ", "Santander", "Itaú", "Bradesco", etc. Pode estar no cabeçalho, rodapé ou qualquer seção

Extraia as seguintes informações quando disponíveis:
1. Nome completo do cliente/devedor/emitente (procure em várias seções, incluindo assinatura) - OBRIGATÓRIO
2. Valor total da dívida/financiamento (priorize "Valor Total Financiado" ou "Saldo Devedor Remanescente" em renegociações) - pode ser null se não encontrado
3. Quantidade de parcelas (pode estar escrito como "053" ou "53") - pode ser null se não encontrado no contrato
4. Valor de cada parcela mensal - pode ser null se não encontrado
5. Data de vencimento da primeira parcela (formato YYYY-MM-DD)
6. Data de vencimento da última parcela (se disponível)
7. Taxa de juros mensal da OPERAÇÃO (priorize % ao mês) - NÃO confundir com CET. Use a "Taxa de juros da operação", não o "CET" (Custo Efetivo Total)
8. Número do contrato/proposta/aditivo
9. CPF ou CNPJ do cliente (não da empresa/banco - procure na seção do cliente)
10. Tipo de contrato (financiamento, empréstimo, aditivo de renegociação, etc.)
11. Nome do banco ou instituição financeira credora (OBRIGATÓRIO extrair quando disponível):
    - CRÍTICO: Mesmo que o nome não esteja escrito, identifique pelo logo, CNPJ, ou outros indicadores
    - Procure por: logo do banco (mesmo que só apareça a logo), nome da instituição financeira, CNPJ da instituição, "Instituição Financeira", "Credor", "Banco", "Financeira"
    - Exemplos conhecidos:
      * Santander: logo vermelho, "Santander", "AYMORÉ CRÉDITO", CNPJ 07.707.650/0001-10
      * Banco do Brasil: logo azul, "Banco do Brasil", "BB"
      * Itaú: logo laranja, "Itaú", "Itaú Unibanco"
      * Bradesco: logo azul/verde, "Bradesco"
      * Caixa: "Caixa Econômica Federal", "CEF"
      * Outros: procure por qualquer menção a instituição financeira, CNPJ, ou logo
    - Pode estar no cabeçalho, rodapé, ou em qualquer seção do documento
    - Se houver logo (mesmo sem texto), identifique o banco pelo logo e mencione no campo banco_credor
    - Se encontrar CNPJ, pode identificar o banco pelo CNPJ conhecido
    - Se não encontrar nenhum indicador, deixe como null
12. Informações do veículo (se aplicável - apenas para contratos de financiamento de veículos):
    - Marca do veículo (ex: NISSAN, TOYOTA, FORD, etc.)
    - Modelo completo do veículo (ex: V-DRIVE DRIVE 1.0 12V A4B, COROLLA XEI 2.0 FLEX, etc.)
    - Ano/Modelo do veículo (ex: 2021, 2012, etc.)
    - Cor do veículo (ex: branca, preta, prata, etc.)
    - Placa do veículo (se mencionada no contrato)
    - RENAVAM do veículo (se mencionado no contrato - número de registro do veículo)
12. Observações relevantes: escreva um texto completo e bem formatado. OBRIGATORIAMENTE inclua DOIS PARÁGRAFOS:

    PARÁGRAFO 1 - Informações do contrato:
    - Informações sobre o bem financiado: marca, modelo, ano, valor à vista (se aplicável)
    - Valor total financiado/confessado
    - Quantidade de parcelas e valor de cada parcela
    - Taxa de juros mensal e anual
    - CET (Custo Efetivo Total) se disponível
    - Outras informações: seguros, garantias, condições contratuais importantes

    PARÁGRAFO 2 - ANÁLISE OBRIGATÓRIA DE IRREGULARIDADES E CLÁUSULAS ABUSIVAS (ESTE PARÁGRAFO É OBRIGATÓRIO):
    Você DEVE SEMPRE incluir este segundo parágrafo analisando explicitamente:
    
    * Taxas de juros (ANÁLISE OBRIGATÓRIA):
      - Taxas entre 2-3% a.m. = NORMAL (padrão de mercado)
      - Taxas entre 3-4% a.m. = ALTA (mencione explicitamente e compare com mercado)
      - Taxas entre 4-5% a.m. = MUITO ALTA (mencione explicitamente como potencialmente abusiva)
      - Taxas acima de 5% a.m. = EXTREMAMENTE ALTA e ABUSIVA (mencione explicitamente como prática abusiva)
      - Compare sempre com padrão de mercado: 2-4% a.m. é comum para financiamento de veículos, 1-3% para empréstimos consignados
      - Se a taxa estiver acima do padrão, identifique como possível violação de normas BACEN sobre taxas abusivas
    
    * CET (Custo Efetivo Total) - ANÁLISE OBRIGATÓRIA:
      - Se o CET estiver muito acima da taxa de juros (diferença > 2% a.m. ou > 30% a.a.), identifique como ENCARGOS EXCESSIVOS
      - CET entre 40-60% a.a. = ALTO (mencione explicitamente)
      - CET entre 60-80% a.a. = MUITO ALTO (mencione explicitamente como potencialmente abusivo)
      - CET acima de 80% a.a. = EXTREMAMENTE ALTO e ABUSIVO (mencione explicitamente como prática abusiva)
      - Se o CET não estiver claramente informado no contrato, identifique como FALTA DE TRANSPARÊNCIA (violação de normas BACEN)
    
    * Cláusulas abusivas segundo CDC (Código de Defesa do Consumidor):
      - Multas acima de 2% = ABUSIVA (identifique explicitamente)
      - Juros moratórios acima de 1% ao mês = possivelmente ABUSIVO (identifique explicitamente)
      - Cláusulas que limitam direitos do consumidor
      - Condições não transparentes
      - Encargos desproporcionais
    
    * Irregularidades com normas do BACEN/CMN (ANÁLISE OBRIGATÓRIA):
      - Falta de transparência no CET ou nas condições (viola Circular BACEN 3.517/2017)
      - Encargos não mencionados claramente (viola normas de transparência)
      - Taxas ou tarifas desproporcionais (viola princípio da proporcionalidade)
      - CET não informado ou informado de forma confusa (viola obrigação de transparência)
      - Taxa de juros não claramente identificada (viola normas de transparência)
      - Informações essenciais em letras miúdas ou de difícil leitura (viola transparência)
    
    * Outras irregularidades: identifique qualquer condição abusiva ou irregular
    
    IMPORTANTE: Sempre termine este segundo parágrafo com uma frase clara como:
    - "IRREGULARIDADES IDENTIFICADAS: [liste cada uma explicitamente]" OU
    - "NÃO FORAM IDENTIFICADAS IRREGULARIDADES EVIDENTES, porém [mencione taxas altas ou condições questionáveis se houver]"
    
    FORMATO: Use quebras de linha duplas (\n\n) para separar os dois parágrafos principais.

INSTRUÇÕES ESPECÍFICAS:
- IMPORTANTE: O contrato pode ser de QUALQUER TIPO: financiamento de veículos, empréstimo, aditivo de renegociação, serviço de negociação de dívida, etc. Adapte a extração ao tipo de contrato.
- Seja MUITO cuidadoso e procure em TODAS as seções do documento
- Para valores monetários, converta para número decimal (ex: R$ 50.000,00 -> 50000.00)
- Para datas, use formato YYYY-MM-DD (ex: 28/02/2025 -> 2025-02-28)
- Em aditivos de renegociação, o valor principal geralmente é "Saldo Devedor Remanescente" ou "Valor Total Confessado"
- Em contratos de serviços (negociação de dívida, etc.), o valor_divida pode ser null se não houver dívida direta no contrato
- Quantidade de parcelas pode estar com zeros à esquerda (053 = 53)
- Se uma informação não estiver clara ou não existir, deixe como None/null
- SEMPRE procure no documento inteiro, não apenas nas primeiras páginas
- CRÍTICO: O campo "observacoes" DEVE ser sempre completo e bem formatado. NÃO corte o texto no meio. Se o texto for muito longo, resuma mas mantenha a análise de irregularidades completa.
- Para observações: escreva em parágrafos completos e bem formatados, sem quebras de linha no meio das palavras. Inclua:
  * Informações do bem financiado (marca, modelo, ano)
  * Análise de possíveis irregularidades:
    - Taxas de juros excessivas (acima de 5% ao mês pode ser considerado alto)
    - CET muito elevado ou não transparente
    - Cláusulas que podem violar o CDC
    - Irregularidades com normas do BACEN/CMN
    - Encargos, tarifas ou multas excessivas
    - Condições abusivas ou desproporcionais
    - Falta de transparência
  * Outras informações relevantes
- CRÍTICO PARA OBSERVAÇÕES: Você DEVE SEMPRE incluir uma análise explícita de irregularidades. Procure e identifique:
  * Taxa de juros acima de 3% a.m. (pode ser considerada alta) ou acima de 5% a.m. (MUITO ALTA, possivelmente abusiva)
  * CET muito acima da taxa de juros (diferença > 2% indica encargos excessivos)
  * CET acima de 60% a.a. (pode ser considerado alto)
  * Multas acima de 2% (abusivas segundo CDC)
  * Juros moratórios acima de 1% ao mês (podem ser abusivos)
  * Falta de transparência nas informações
  * Cláusulas que podem violar o CDC (Código de Defesa do Consumidor)
  * Violações potenciais de normas do BACEN/CMN
  * Encargos ou tarifas desproporcionais
- OBRIGATÓRIO: Sempre termine as observações com uma seção específica sobre irregularidades encontradas. Se encontrar, liste cada uma explicitamente. Se não encontrar irregularidades evidentes, ainda assim mencione se há taxas altas ou condições questionáveis, e diga claramente "Não foram identificadas irregularidades evidentes no contrato".
- IMPORTANTE: Escreva as observações em parágrafos completos e coerentes, separados por quebras de linha duplas (\n\n). Não use espaços entre caracteres de uma mesma palavra. Use R$ para valores monetários (padrão brasileiro).

{format_instructions}"""),
            ("human", """Analise o seguinte contrato e extraia as informações solicitadas. O contrato pode ser de QUALQUER TIPO (financiamento, empréstimo, aditivo de renegociação, serviço de negociação de dívida, etc.) - procure cuidadosamente em TODAS as seções.

CRÍTICO - OBSERVAÇÕES DEVEM TER 2 PARÁGRAFOS OBRIGATÓRIOS (MÁXIMO 500 palavras no total):

PARÁGRAFO 1 (máximo 200 palavras): Informações básicas do contrato (valor, parcelas, taxas, bem financiado ou objeto do contrato, etc.)

PARÁGRAFO 2 (máximo 300 palavras): ANÁLISE OBRIGATÓRIA DE IRREGULARIDADES E CLÁUSULAS ABUSIVAS
Você DEVE SEMPRE incluir este segundo parágrafo analisando METICULOSAMENTE:

ANÁLISE DE TAXAS (OBRIGATÓRIA):
- Taxas entre 3-4% a.m. = ALTA (mencione explicitamente e compare com mercado)
- Taxas entre 4-5% a.m. = MUITO ALTA (mencione explicitamente como potencialmente abusiva)
- Taxas acima de 5% a.m. = EXTREMAMENTE ALTA e ABUSIVA (mencione explicitamente como prática abusiva)

ANÁLISE DE CET (OBRIGATÓRIA):
- CET entre 60-80% a.a. = MUITO ALTO (mencione explicitamente como potencialmente abusivo)
- CET acima de 80% a.a. = EXTREMAMENTE ALTO e ABUSIVO (mencione explicitamente)
- Diferença entre CET e taxa de juros > 30% a.a. = ENCARGOS EXCESSIVOS (identifique explicitamente)

ANÁLISE DE ENCARGOS (OBRIGATÓRIA):
- Multas acima de 2% = ABUSIVA segundo CDC Art. 52, §1º (identifique explicitamente)
- Juros moratórios acima de 1% ao mês = ABUSIVO segundo jurisprudência (identifique explicitamente)
- Soma de multa + juros moratórios > 2% ao mês = ABUSIVO (identifique explicitamente)

ANÁLISE DE CLÁUSULAS (OBRIGATÓRIA):
- Cláusulas que limitam direitos do consumidor (identifique quais)
- Condições não transparentes ou difíceis de entender (identifique quais)
- Qualquer cláusula que possa violar CDC ou normas BACEN/CMN (identifique especificamente)

SEMPRE termine o segundo parágrafo com: "IRREGULARIDADES IDENTIFICADAS: [liste cada uma]" OU "NÃO FORAM IDENTIFICADAS IRREGULARIDADES EVIDENTES, porém [mencione taxas altas ou condições questionáveis se houver]"

IMPORTANTE: 
- Mantenha as observações concisas mas completas. NÃO corte o texto no meio. O JSON DEVE estar completo e válido.
- Campos numéricos (quantidade_parcelas, valor_divida, valor_parcela, taxa_juros) podem ser null se não estiverem disponíveis no contrato.
- Use null (não 0) quando a informação não estiver presente no documento.
- O campo nome_cliente é OBRIGATÓRIO e sempre deve ter um valor.
- CRÍTICO - BANCO/INSTITUIÇÃO FINANCEIRA: 
  * Se houver logo do banco (mesmo sem texto), identifique pelo logo (ex: logo vermelho = Santander, logo azul = Banco do Brasil, etc.)
  * Procure por CNPJ da instituição financeira e identifique o banco pelo CNPJ
  * Procure por qualquer menção a "Instituição Financeira", "Credor", "Banco", "Financeira"
  * Exemplos: "Santander", "AYMORÉ CRÉDITO", "Banco do Brasil", "Itaú", "Bradesco", "Caixa Econômica Federal"
  * Se identificar o banco, preencha o campo banco_credor com o nome completo

Contrato a analisar:
{contract_text}""")
        ])
    
    def _detectar_provider(self) -> str:
        """Detecta qual provider está disponível."""
        # Prioridade: Groq (com modelos Gemini) primeiro (gratuito e melhor para cálculos), 
        # depois Ollama, depois OpenAI
        
        # Prioridade: Groq primeiro (gratuito, rápido, e suporta Gemini para cálculos precisos)
        # Verifica Groq (gratuito, muito rápido, suporta modelos Gemini)
        if os.getenv("GROQ_API_KEY"):
            return "groq"
        
        # Verifica Ollama (local, sempre disponível se instalado)
        try:
            import ollama
            # Testa se o servidor está rodando
            ollama.list()
            return "ollama"
        except:
            pass
        
        # Verifica OpenAI (mais caro, mas funciona bem)
        if os.getenv("OPENAI_API_KEY"):
            return "openai"
        
        raise ValueError(
            "Nenhum provider de IA configurado. Configure pelo menos um:\n"
            "- Groq (GRATUITO, suporta Gemini): GROQ_API_KEY no .env\n"
            "- Ollama (GRÁTIS, local): Instale em https://ollama.ai\n"
            "- OpenAI: OPENAI_API_KEY no .env"
        )
    
    def _inicializar_llm(self, model_name: Optional[str]):
        """Inicializa o LLM baseado no provider."""
        if self.provider == "ollama":
            from langchain_ollama import ChatOllama
            model = model_name or "llama3.2"  # Modelo gratuito e bom
            return ChatOllama(model=model, temperature=0.0)
        
        elif self.provider == "groq":
            from langchain_groq import ChatGroq
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY não encontrada no .env")
            # Modelos disponíveis no Groq:
            # - Llama: llama-3.1-8b-instant (rápido), llama-3.3-70b-versatile (preciso)
            # - Mixtral: mixtral-8x7b-32768 (balanceado)
            # NOTA: gemma2-9b-it e gemma-7b-it foram descontinuados
            # Prioriza Llama 3.3 para precisão, depois Llama 3.1 para velocidade
            modelos_disponiveis = model_name or [
                "llama-3.3-70b-versatile",  # Llama - mais preciso (recomendado)
                "llama-3.1-8b-instant",     # Llama - mais rápido
                "mixtral-8x7b-32768"       # Mixtral - balanceado
            ]
            if isinstance(modelos_disponiveis, str):
                modelos_disponiveis = [modelos_disponiveis]
            
            ultimo_erro = None
            for modelo in modelos_disponiveis:
                try:
                    return ChatGroq(model=modelo, temperature=0.0, groq_api_key=api_key)
                except Exception as e:
                    erro_str = str(e).lower()
                    if "decommissioned" in erro_str or "not found" in erro_str:
                        continue
                    elif "rate_limit" in erro_str or "429" in erro_str or "tokens per day" in erro_str:
                        ultimo_erro = f"Limite de tokens do Groq excedido. Modelo tentado: {modelo}. " \
                                     f"O limite diário de tokens foi atingido. Tente novamente mais tarde ou configure outro provedor de IA."
                        continue
                    ultimo_erro = str(e)
            
            if ultimo_erro:
                raise Exception(f"Erro ao usar Groq: {ultimo_erro}")
            raise Exception(f"Nenhum modelo Groq funcionou. Tentei: {modelos_disponiveis}")
        
        elif self.provider == "openai":
            from langchain_openai import ChatOpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY não encontrada no .env")
            model = model_name or "gpt-4o-mini"
            return ChatOpenAI(model=model, temperature=0.0, api_key=api_key)
        
        else:
            raise ValueError(f"Provider desconhecido: {self.provider}")
    
    def _limpar_observacoes(self, texto: str) -> str:
        """
        Limpa apenas problemas específicos de formatação, sem alterar texto já correto.
        Apenas corrige valores monetários que não usam R$ e remove espaços múltiplos.
        """
        if not texto:
            return texto
        
        import re
        
        # Apenas corrige valores monetários que não usam R$ (padrão brasileiro)
        # "R 19.653" ou "R19.653" -> "R$ 19.653"
        texto = re.sub(r'\bR\s+(\d)', r'R$ \1', texto)
        texto = re.sub(r'\bR(\d)', r'R$ \1', texto)
        
        # Remove apenas espaços múltiplos (preserva quebras de linha)
        texto = re.sub(r'[ \t]+', ' ', texto)
        
        # Remove espaços no início e fim de linhas (mas preserva quebras de linha)
        linhas = texto.split('\n')
        linhas = [linha.strip() for linha in linhas]
        texto = '\n'.join(linhas)
        
        # Remove linhas vazias múltiplas (mantém no máximo uma linha vazia)
        texto = re.sub(r'\n\n\n+', '\n\n', texto)
        
        return texto.strip()
    
    def _truncar_texto(self, text: str, max_chars: int = 8000) -> str:
        """
        Trunca o texto mantendo início e fim (onde geralmente estão as informações importantes).
        
        Args:
            text: Texto original
            max_chars: Tamanho máximo aproximado (deixa margem para o prompt)
            
        Returns:
            Texto truncado preservando início e fim
        """
        if len(text) <= max_chars:
            return text
        
        # Mantém início (dados do cliente) e fim (condições finais)
        chars_inicio = 3500  # Primeiros 3500 chars (dados principais)
        chars_fim = 2000     # Últimos 2000 chars (condições, assinatura)
        
        inicio = text[:chars_inicio]
        fim = text[-chars_fim:]
        
        return f"{inicio}\n\n[... texto do meio removido para reduzir tamanho ...]\n\n{fim}"
    
    def _detectar_banco_por_cnpj(self, text: str) -> Optional[str]:
        """
        Detecta banco por CNPJ conhecidos no texto.
        
        Args:
            text: Texto do contrato
            
        Returns:
            Nome do banco se encontrado, None caso contrário
        """
        # CNPJs conhecidos de bancos principais e financeiras
        bancos_cnpj = {
            "07.707.650/0001-10": "Santander",  # Aymoré Crédito (Santander)
            "00.000.000/0001-91": "Banco do Brasil",
            "60.701.190/0001-04": "Itaú Unibanco",
            "60.746.948/0001-12": "Bradesco",
            "00.360.305/0001-04": "Caixa Econômica Federal",
            "33.014.126/0001-96": "Banco Inter",
            "59.025.094/0001-70": "Nubank",
            "62.173.620/0001-80": "Banco Original",
            "17.167.412/0001-13": "Banco Pan",
            "04.452.473/0001-80": "Banco Safra",
            "92.702.067/0001-96": "Banco Votorantim",
            "33.000.118/0001-41": "Banco BTG Pactual",
            "17.222.333/0001-91": "Banco C6",
            "28.517.628/0001-88": "Banco Next",
            "61.186.680/0001-74": "Banco Daycoval",
            "07.206.816/0001-30": "Banco Rendimento",
            "04.862.600/0001-10": "Banco Fibra",
            "11.222.333/0001-81": "Banco ABC Brasil",
            "05.114.027/0001-93": "Banco Mercantil",
            "17.352.248/0001-02": "Banco Pine",
            "04.452.473/0001-80": "Banco Safra",
            "92.702.067/0001-96": "Banco Votorantim",
            "33.000.118/0001-41": "Banco BTG Pactual",
        }
        
        # Procura CNPJs no texto (formato XX.XXX.XXX/XXXX-XX)
        import re
        cnpj_pattern = r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'
        cnpjs_encontrados = re.findall(cnpj_pattern, text)
        
        for cnpj in cnpjs_encontrados:
            if cnpj in bancos_cnpj:
                return bancos_cnpj[cnpj]
        
        # Também procura por nomes de bancos conhecidos no texto (mais completo)
        bancos_nomes = {
            # Santander
            "santander": "Santander",
            "aymoré": "Santander",
            "aymore": "Santander",
            "aymoré crédito": "Santander",
            "aymore credito": "Santander",
            # Banco do Brasil
            "banco do brasil": "Banco do Brasil",
            "bb ": "Banco do Brasil",
            " banco brasil": "Banco do Brasil",
            # Itaú
            "itau": "Itaú",
            "itaú": "Itaú",
            "itau unibanco": "Itaú Unibanco",
            "itaú unibanco": "Itaú Unibanco",
            # Bradesco
            "bradesco": "Bradesco",
            # Caixa
            "caixa": "Caixa Econômica Federal",
            "caixa econômica": "Caixa Econômica Federal",
            "caixa economica": "Caixa Econômica Federal",
            "cef": "Caixa Econômica Federal",
            # Outros bancos
            "banco inter": "Banco Inter",
            "inter": "Banco Inter",
            "nubank": "Nubank",
            "banco original": "Banco Original",
            "banco pan": "Banco Pan",
            "pan ": "Banco Pan",
            "banco safra": "Banco Safra",
            "safra": "Banco Safra",
            "banco votorantim": "Banco Votorantim",
            "votorantim": "Banco Votorantim",
            "btg pactual": "Banco BTG Pactual",
            "btg": "Banco BTG Pactual",
            "banco c6": "Banco C6",
            "c6 bank": "Banco C6",
            "banco next": "Banco Next",
            "next": "Banco Next",
            "banco daycoval": "Banco Daycoval",
            "daycoval": "Banco Daycoval",
            "banco rendimento": "Banco Rendimento",
            "rendimento": "Banco Rendimento",
            "banco fibra": "Banco Fibra",
            "fibra": "Banco Fibra",
            "banco abc": "Banco ABC Brasil",
            "banco mercantil": "Banco Mercantil",
            "mercantil": "Banco Mercantil",
            "banco pine": "Banco Pine",
            "pine": "Banco Pine",
            # Financeiras e outras instituições
            "creditas": "Creditas",
            "geru": "Geru",
            "simplic": "Simplic",
            "banco digio": "Digio",
            "digio": "Digio",
            "banco neon": "Neon",
            "neon": "Neon",
            "banco picpay": "PicPay",
            "picpay": "PicPay",
            "banco will": "Will Bank",
            "will bank": "Will Bank",
            "banco pagbank": "PagBank",
            "pagbank": "PagBank",
        }
        
        text_lower = text.lower()
        # Procura por nomes completos primeiro (mais específico)
        for nome_banco, nome_completo in sorted(bancos_nomes.items(), key=lambda x: len(x[0]), reverse=True):
            if nome_banco in text_lower:
                return nome_completo
        
        # Procura por padrões comuns de menção a instituições financeiras
        padroes_instituicao = [
            (r'institui[çc][ãa]o\s+financeira[:\s]+([A-Z][A-Z\s]+)', lambda m: m.group(1).strip()),
            (r'credor[:\s]+([A-Z][A-Z\s]+)', lambda m: m.group(1).strip()),
            (r'banco[:\s]+([A-Z][A-Z\s]+)', lambda m: m.group(1).strip()),
        ]
        
        for padrao, extrair in padroes_instituicao:
            matches = re.finditer(padrao, text, re.IGNORECASE)
            for match in matches:
                nome_encontrado = extrair(match)
                # Verifica se o nome encontrado contém algum banco conhecido
                nome_lower = nome_encontrado.lower()
                for nome_banco, nome_completo in bancos_nomes.items():
                    if nome_banco in nome_lower or nome_lower in nome_banco:
                        return nome_completo
        
        return None
    
    def _aplicar_recalculo_bacen(self, result: ContratoInfo) -> ContratoInfo:
        """
        Aplica recálculo com dados do BACEN ao resultado da extração.
        
        Args:
            result: Resultado da extração do contrato
            
        Returns:
            Resultado com recálculo aplicado (se possível)
        """
        # Só recalcula se houver dados suficientes
        if not (result.valor_divida and result.quantidade_parcelas and 
                result.taxa_juros and result.data_vencimento_primeira):
            return result
        
        try:
            print("🔄 Iniciando recálculo com dados do BACEN...")
            recalculo = self.recalculador.recalcular_contrato(
                valor_principal=result.valor_divida,
                taxa_juros_contrato=result.taxa_juros,
                numero_parcelas=result.quantidade_parcelas,
                valor_parcela_contrato=result.valor_parcela,
                data_contratacao=result.data_vencimento_primeira,
                data_primeira_parcela=result.data_vencimento_primeira,
                tipo_taxa="prefixada",  # Assume prefixada por padrão (pode ser detectado no futuro)
                indexador="selic"
            )
            
            if recalculo.get("sucesso"):
                result.recalculo_bacen = recalculo
                print("✅ Recálculo com BACEN concluído com sucesso")
                
                # Adiciona informações de recálculo nas observações se houver divergências
                if recalculo.get("comparacao") and recalculo["comparacao"].get("diferenca_price"):
                    diff = recalculo["comparacao"]["diferenca_price"]
                    if diff > 1.0:  # Diferença maior que R$ 1,00
                        aviso = f"\n\n⚠️ RECÁLCULO BACEN: Divergência detectada entre valor da parcela do contrato (R$ {result.valor_parcela:.2f}) e cálculo Price (R$ {recalculo['recalculo_price']['valor_parcela']:.2f}). Diferença: R$ {diff:.2f}."
                        if result.observacoes:
                            result.observacoes += aviso
                        else:
                            result.observacoes = aviso
            else:
                print(f"⚠️ Recálculo com BACEN não foi possível: {recalculo.get('erro')}")
        except Exception as e:
            print(f"⚠️ Erro ao recalcular com BACEN: {e}")
            # Não falha a extração se o recálculo falhar
        
        return result
    
    def _truncar_texto_inteligente(self, text: str, max_chars: int = 3000) -> str:
        """
        Trunca o texto mantendo início e fim (onde geralmente estão as informações importantes).
        Limite do Groq: 6000 tokens/minuto (TPM) para modelo llama-3.1-8b-instant.
        Considerando que o prompt consome ~2000-2500 tokens, deixamos ~3500 tokens para o texto.
        1 token ≈ 4 chars, então ~3000 chars é seguro para o texto do contrato.
        """
        if len(text) <= max_chars:
            return text
        
        # Calcula proporção para manter início e fim
        # Mantém mais do início (onde estão dados principais) e menos do fim
        chars_inicio = int(max_chars * 0.65)  # 65% no início
        chars_fim = int(max_chars * 0.30)     # 30% no fim (5% para mensagem de truncamento)
        
        inicio = text[:chars_inicio]
        fim = text[-chars_fim:]
        
        return f"{inicio}\n\n[... texto intermediário removido para reduzir tamanho ...]\n\n{fim}"
    
    def extract_from_text(self, text: str) -> ContratoInfo:
        """Extrai informações de um contrato a partir de texto."""
        if not text or not text.strip():
            raise ValueError("Texto do contrato não pode estar vazio")
        
        processed_text = self.document_processor.clean_text(text)
        
        # Trunca o texto se necessário (limite do Groq é 6000 tokens/minuto para llama-3.1-8b-instant)
        # O prompt consome ~2000-2500 tokens, então deixamos ~3500 tokens para o texto
        # 1 token ≈ 4 chars, então ~14000 chars seria o limite teórico, mas para ser conservador usamos 3000 chars
        processed_text = self._truncar_texto_inteligente(processed_text, max_chars=3000)
        
        chain = self.prompt_template | self.llm | self.output_parser
        
        try:
            result = chain.invoke({
                "contract_text": processed_text,
                "format_instructions": self.output_parser.get_format_instructions()
            })
            
            # Tenta detectar banco por CNPJ se não foi identificado pela IA
            if not result.banco_credor or result.banco_credor.strip() == "":
                banco_detectado = self._detectar_banco_por_cnpj(text)
                if banco_detectado:
                    result.banco_credor = banco_detectado
                    print(f"🔍 DEBUG: Banco detectado por CNPJ: {banco_detectado}")
            
            # Log de debug
            if result.banco_credor:
                print(f"✅ DEBUG: Banco identificado: {result.banco_credor}")
            else:
                print(f"⚠️  DEBUG: Banco NÃO identificado no contrato")
            
            # Aplica recálculo com BACEN
            result = self._aplicar_recalculo_bacen(result)
            
            # Não altera observações - o JSON já vem correto da IA
            # A função _limpar_observacoes só deve ser chamada manualmente se necessário
            
            return result
        except Exception as e:
            error_msg = str(e)
            
            # Se for erro de parsing (JSON incompleto ou validação), tenta novamente com texto menor
            if "Failed to parse" in error_msg or "parse" in error_msg.lower() or "json" in error_msg.lower() or "validation error" in error_msg.lower():
                # Tenta novamente com texto menor para evitar corte do JSON
                original_cleaned = self.document_processor.clean_text(text)
                processed_text = self._truncar_texto_inteligente(original_cleaned, max_chars=3000)
                try:
                    result = chain.invoke({
                        "contract_text": processed_text,
                        "format_instructions": self.output_parser.get_format_instructions()
                    })
                    
                    # Tenta detectar banco por CNPJ se não foi identificado pela IA
                    if not result.banco_credor or result.banco_credor.strip() == "":
                        banco_detectado = self._detectar_banco_por_cnpj(text)
                        if banco_detectado:
                            result.banco_credor = banco_detectado
                            print(f"🔍 DEBUG: Banco detectado por CNPJ: {banco_detectado}")
                    
                    # Log de debug
                    if result.banco_credor:
                        print(f"✅ DEBUG: Banco identificado: {result.banco_credor}")
                    else:
                        print(f"⚠️  DEBUG: Banco NÃO identificado no contrato")
                    
                    # Aplica recálculo com BACEN
                    result = self._aplicar_recalculo_bacen(result)
                    
                    return result
                except Exception as e2:
                    # Se ainda falhar, tenta com texto ainda menor
                    processed_text = self._truncar_texto_inteligente(original_cleaned, max_chars=2000)
                    try:
                        result = chain.invoke({
                            "contract_text": processed_text,
                            "format_instructions": self.output_parser.get_format_instructions()
                        })
                        
                        # Tenta detectar banco por CNPJ se não foi identificado pela IA
                        if not result.banco_credor or result.banco_credor.strip() == "":
                            banco_detectado = self._detectar_banco_por_cnpj(text)
                            if banco_detectado:
                                result.banco_credor = banco_detectado
                                print(f"🔍 DEBUG: Banco detectado por CNPJ: {banco_detectado}")
                        
                        # Log de debug
                        if result.banco_credor:
                            print(f"✅ DEBUG: Banco identificado: {result.banco_credor}")
                        else:
                            print(f"⚠️  DEBUG: Banco NÃO identificado no contrato")
                        
                        # Aplica recálculo com BACEN
                        result = self._aplicar_recalculo_bacen(result)
                        
                        return result
                    except Exception as e3:
                        raise Exception(f"Erro ao extrair informações do contrato (JSON incompleto ou inválido): {str(e3)}")
            
            if "413" in error_msg or "too large" in error_msg.lower() or "tokens per minute" in error_msg.lower() or "tpm" in error_msg.lower():
                # Se ainda for muito grande, reduz progressivamente
                # Usa o texto original limpo, não o já truncado
                original_cleaned = self.document_processor.clean_text(text)
                # Tenta com tamanhos menores: 2000, 1500, 1000
                tamanhos = [2000, 1500, 1000]
                ultimo_erro = None
                
                for tamanho in tamanhos:
                    try:
                        processed_text_reduzido = self._truncar_texto_inteligente(original_cleaned, max_chars=tamanho)
                        result = chain.invoke({
                            "contract_text": processed_text_reduzido,
                            "format_instructions": self.output_parser.get_format_instructions()
                        })
                        
                        # Tenta detectar banco por CNPJ se não foi identificado pela IA
                        if not result.banco_credor or result.banco_credor.strip() == "":
                            banco_detectado = self._detectar_banco_por_cnpj(text)
                            if banco_detectado:
                                result.banco_credor = banco_detectado
                                print(f"🔍 DEBUG: Banco detectado por CNPJ: {banco_detectado}")
                        
                        # Log de debug
                        if result.banco_credor:
                            print(f"✅ DEBUG: Banco identificado: {result.banco_credor}")
                        else:
                            print(f"⚠️  DEBUG: Banco NÃO identificado no contrato")
                        
                        # Aplica recálculo com BACEN
                        result = self._aplicar_recalculo_bacen(result)
                        
                        return result
                    except Exception as e2:
                        error_msg2 = str(e2)
                        if "413" in error_msg2 or "too large" in error_msg2.lower() or "tokens per minute" in error_msg2.lower() or "tpm" in error_msg2.lower():
                            ultimo_erro = e2
                            continue
                        else:
                            # Outro tipo de erro, propaga
                            raise e2
                
                # Se todos os tamanhos falharam, lança erro explicativo
                if ultimo_erro:
                    raise Exception(
                        f"O contrato é muito grande para processar. Mesmo reduzindo o tamanho, ainda excede o limite de tokens do Groq (6000 TPM). "
                        f"Por favor, tente com um contrato menor ou configure outro provedor de IA (OpenAI, Gemini, Ollama) no arquivo .env. "
                        f"Erro detalhado: {str(ultimo_erro)}"
                    )
                raise Exception(f"Erro ao processar contrato (muito grande): {error_msg}")
            
            # Trata erro de rate limit do Groq
            if "rate_limit" in error_msg.lower() or "429" in error_msg or "tokens per day" in error_msg.lower() or "rate limit reached" in error_msg.lower():
                raise Exception(
                    f"Limite de tokens do Groq excedido. O limite diário de tokens foi atingido. "
                    f"Por favor, tente novamente mais tarde ou configure outro provedor de IA (OpenAI, Gemini, Ollama) no arquivo .env. "
                    f"Erro detalhado: {error_msg}"
                )
            
            raise Exception(f"Erro ao extrair informações do contrato: {str(e)}")
    
    def extract_from_pdf(self, pdf_path: str) -> ContratoInfo:
        """Extrai informações de um contrato a partir de um arquivo PDF."""
        text = self.document_processor.extract_text_from_pdf(pdf_path)
        return self.extract_from_text(text)
    
    def extract_to_dict(self, text: Optional[str] = None, pdf_path: Optional[str] = None) -> dict:
        """Extrai informações e retorna como dicionário."""
        if pdf_path:
            result = self.extract_from_pdf(pdf_path)
        elif text:
            result = self.extract_from_text(text)
        else:
            raise ValueError("Forneça text ou pdf_path")
        
        return result.model_dump()

