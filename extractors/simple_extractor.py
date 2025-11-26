"""
Extrator simples de contratos usando regex e processamento de texto.
Funciona sem necessidade de API key (modo demo).
"""
import re
from typing import Optional
from backend.processors.document_processor import DocumentProcessor
from backend.models.models import ContratoInfo


class SimpleContractExtractor:
    """Extrai informações básicas de contratos usando regex (sem IA)."""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
    
    def extract_from_text(self, text: str) -> ContratoInfo:
        """
        Extrai informações básicas usando regex.
        
        Args:
            text: Texto do contrato
            
        Returns:
            Objeto ContratoInfo com informações extraídas
        """
        processed_text = self.document_processor.clean_text(text)
        text_lower = processed_text.lower()
        
        # Extrai nome do cliente (procura por padrões comuns)
        nome_cliente = self._extract_nome(text, processed_text)
        
        # Extrai CPF/CNPJ
        cpf_cnpj = self._extract_cpf_cnpj(processed_text)
        
        # Extrai valores monetários
        valor_divida = self._extract_valor_principal(processed_text, text_lower)
        valor_parcela = self._extract_valor_parcela(processed_text, text_lower)
        
        # Extrai quantidade de parcelas
        quantidade_parcelas = self._extract_parcelas(processed_text, text_lower)
        
        # Extrai datas
        data_vencimento_primeira = self._extract_data_primeira(processed_text)
        data_vencimento_ultima = self._extract_data_ultima(processed_text)
        
        # Extrai taxa de juros
        taxa_juros = self._extract_taxa_juros(processed_text, text_lower)
        
        # Extrai número do contrato
        numero_contrato = self._extract_numero_contrato(processed_text)
        
        # Extrai tipo de contrato
        tipo_contrato = self._extract_tipo_contrato(text_lower)
        
        # Observações
        observacoes = self._extract_observacoes(processed_text)
        
        return ContratoInfo(
            nome_cliente=nome_cliente or "Não identificado",
            valor_divida=valor_divida or 0.0,
            quantidade_parcelas=quantidade_parcelas or 0,
            valor_parcela=valor_parcela,
            data_vencimento_primeira=data_vencimento_primeira,
            data_vencimento_ultima=data_vencimento_ultima,
            taxa_juros=taxa_juros,
            numero_contrato=numero_contrato,
            cpf_cnpj=cpf_cnpj,
            tipo_contrato=tipo_contrato,
            observacoes=observacoes
        )
    
    def _extract_nome(self, text: str, processed_text: str) -> Optional[str]:
        """Extrai nome do cliente."""
        # Padrões mais específicos - procura na seção de dados do emitente
        patterns = [
            # Padrão: "Nome/Razão Social" seguido do nome
            r'Nome/Razão\s+Social\s+([A-ZÁÉÍÓÚÂÊÔÇ][A-ZÁÉÍÓÚÂÊÔÇ\s]+?)(?:\n|CPF|CNPJ|Endereço)',
            # Padrão: "Nome do cliente" ou similar
            r'(?:Nome\s+do\s+cliente|Nome/Razão\s+Social|Emitente)[\s:]+([A-ZÁÉÍÓÚÂÊÔÇ][A-ZÁÉÍÓÚÂÊÔÇ\s]+?)(?:\n|CPF|CNPJ)',
            # Padrão genérico antes de CPF
            r'([A-ZÁÉÍÓÚÂÊÔÇ][A-ZÁÉÍÓÚÂÊÔÇ\s]{5,30}?)\s+CPF\s+[\d.-]+',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, processed_text)
            if match:
                nome = match.group(1).strip()
                # Limpa o nome (remove espaços extras, quebras de linha)
                nome = ' '.join(nome.split())
                # Verifica se não é um cabeçalho ou rótulo
                if (len(nome.split()) >= 2 and 
                    nome.upper() not in ['BANCO AGENCIA CONTA', 'NOME RAZAO SOCIAL', 'EMITENTE'] and
                    not nome.startswith('Nome') and
                    len(nome) > 5):
                    return nome
        return None
    
    def _extract_cpf_cnpj(self, text: str) -> Optional[str]:
        """Extrai CPF ou CNPJ do cliente (não da empresa)."""
        # CPF: XXX.XXX.XXX-XX
        cpf_pattern = r'\d{3}\.\d{3}\.\d{3}-\d{2}'
        # CNPJ: XX.XXX.XXX/XXXX-XX
        cnpj_pattern = r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'
        
        # Procura CPF primeiro (geralmente é do cliente)
        # Procura na seção de dados do emitente/cliente
        cpf_section = re.search(r'CPF\s+(\d{3}\.\d{3}\.\d{3}-\d{2})', text, re.IGNORECASE)
        if cpf_section:
            return cpf_section.group(1)
        
        # Se não encontrou na seção CPF, procura todos os CPFs e pega o primeiro
        # (geralmente o primeiro é do cliente)
        cpf_matches = list(re.finditer(cpf_pattern, text))
        if cpf_matches:
            # Pega o primeiro CPF que aparece (geralmente é do cliente)
            return cpf_matches[0].group(0)
        
        # Se não tem CPF, procura CNPJ (mas só se for do cliente, não da empresa)
        cnpj_section = re.search(r'(?:CPF|CNPJ)\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', text, re.IGNORECASE)
        if cnpj_section:
            return cnpj_section.group(1)
        
        return None
    
    def _extract_valor_principal(self, text: str, text_lower: str) -> Optional[float]:
        """Extrai valor principal da dívida."""
        # Padrões específicos primeiro (ordem de prioridade)
        patterns = [
            # "Valor Total Financiado" - este é o valor principal do financiamento
            r'Valor\s+Total\s+Financiado\s+R\$\s*([\d.,]+)',
            # "Valor total do(s) bem(s)" - valor do bem
            r'Valor\s+total\s+do\(s\)\s+[Bb]em\([ns]\)\s+R\$\s*([\d.,]+)',
            # "Valor total do crédito"
            r'Valor\s+total\s+do\s+crédito\s+R\$\s*([\d.,]+)',
            # "Valor líquido de crédito"
            r'Valor\s+[Ll]íquido\s+de\s+crédito\s+R\$\s*([\d.,]+)',
            # "Valor Total do Crédito"
            r'Valor\s+Total\s+do\s+Crédito\s+R\$\s*([\d.,]+)',
            # Padrões genéricos
            r'(?:valor\s+(?:total|financiado|da\s+dívida|do\s+contrato)|total|financiamento)[\s:]+(?:r\$|rs)?\s*([\d.,]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                valor_str = match.group(1).replace('.', '').replace(',', '.')
                try:
                    valor = float(valor_str)
                    if valor > 100:  # Valores muito pequenos provavelmente não são o principal
                        return valor
                except:
                    continue
        
        # Procura todos os valores monetários e tenta identificar o principal
        valores_encontrados = re.findall(r'R\$\s*([\d.,]+)', text, re.IGNORECASE)
        if valores_encontrados:
            try:
                valores_float = []
                for v in valores_encontrados:
                    try:
                        valor = float(v.replace('.', '').replace(',', '.'))
                        if 1000 <= valor <= 1000000:  # Valores razoáveis para financiamento
                            valores_float.append(valor)
                    except:
                        continue
                
                if valores_float:
                    # Remove duplicatas e ordena
                    valores_float = sorted(set(valores_float))
                    # Pega um valor médio-alto (geralmente o valor financiado está no meio)
                    if len(valores_float) >= 2:
                        # Pega o segundo maior (o maior pode ser valor total pago)
                        return valores_float[-2] if len(valores_float) > 1 else valores_float[-1]
                    return valores_float[-1]
            except:
                pass
        
        return None
    
    def _extract_valor_parcela(self, text: str, text_lower: str) -> Optional[float]:
        """Extrai valor da parcela."""
        patterns = [
            # Padrão específico: "(I) Valor das parcelas" seguido de R$ e valor
            r'\(I\)\s+Valor\s+das\s+parcelas\s+R\$\s*([\d.,]+)',
            # Padrão específico: "(A) Valor das parcelas"
            r'\(A\)\s+Valor\s+das\s+parcelas\s+R\$\s*([\d.,]+)',
            # Padrões genéricos
            r'(?:valor\s+(?:da|de\s+cada)?\s*parcela|parcela\s+de)[\s:]+(?:r\$|rs)?\s*([\d.,]+)',
            r'(?:r\$|rs)\s*([\d.,]+)\s*(?:por\s+parcela|mensal)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                valor_str = match.group(1).replace('.', '').replace(',', '.')
                try:
                    valor = float(valor_str)
                    if 10 <= valor <= 100000:  # Valores razoáveis para parcela
                        return valor
                except:
                    continue
        return None
    
    def _extract_parcelas(self, text: str, text_lower: str) -> Optional[int]:
        """Extrai quantidade de parcelas."""
        patterns = [
            # Padrão específico: "(II) Quantidade de parcelas" seguido de número
            r'\(II\)\s+Quantidade\s+de\s+parcelas\s+(\d+)',
            # Padrão específico: "Quantidade de parcelas" ou "(B) Quantidade de parcelas"
            r'(?:\(B\)\s+)?Quantidade\s+de\s+parcelas\s+(\d+)',
            # Padrão: número seguido de "parcelas" na mesma linha
            r'(\d+)\s+parcelas?',
            # Padrão: "em X parcelas" ou "de X parcelas"
            r'(?:em|de)\s+(\d+)\s+parcelas?',
            # Padrão genérico
            r'(\d+)\s*(?:parcelas?|vezes|meses?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    num = int(match.group(1))
                    if 1 <= num <= 1000:  # Valores razoáveis
                        return num
                except:
                    continue
        return None
    
    def _extract_data_primeira(self, text: str) -> Optional[str]:
        """Extrai data da primeira parcela."""
        patterns = [
            # Padrão específico: "Vencimento da 1ª parcela" ou "(A) Vencimento da 1ª parcela"
            r'(?:\(A\)\s+)?Vencimento\s+da\s+1[ªa]\s+parcela\s+(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
            # Padrão genérico
            r'(?:primeira\s+parcela|vencimento\s+primeira|1[ªa]\s+parcela)[\s:]+(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})(?:\s+.*?primeira)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dia, mes, ano = match.groups()
                ano = '20' + ano if len(ano) == 2 else ano
                return f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"
        return None
    
    def _extract_data_ultima(self, text: str) -> Optional[str]:
        """Extrai data da última parcela."""
        patterns = [
            # Padrão específico: "Vencimento da última parcela"
            r'Vencimento\s+da\s+última\s+parcela\s+(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
            # Padrão genérico
            r'(?:última\s+parcela|vencimento\s+última)[\s:]+(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})(?:\s+.*?última)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                dia, mes, ano = match.groups()
                ano = '20' + ano if len(ano) == 2 else ano
                return f"{ano}-{mes.zfill(2)}-{dia.zfill(2)}"
        return None
    
    def _extract_taxa_juros(self, text: str, text_lower: str) -> Optional[float]:
        """Extrai taxa de juros."""
        patterns = [
            r'(?:taxa\s+de\s+juros|juros)[\s:]+(\d+[,.]?\d*)\s*%',
            r'(\d+[,.]?\d*)\s*%\s*(?:ao\s+mês|mensal|de\s+juros)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    taxa = float(match.group(1).replace(',', '.'))
                    if 0 < taxa < 100:
                        return taxa
                except:
                    continue
        return None
    
    def _extract_numero_contrato(self, text: str) -> Optional[str]:
        """Extrai número do contrato."""
        patterns = [
            # Padrão específico: "Proposta 108774681" ou "Cédula de Crédito Bancário - Proposta 108774681"
            r'Proposta\s+(\d+)',
            # Padrão: "Número do Contrato" ou "Nº Contrato"
            r'(?:N[úu]mero\s+do\s+Contrato|N[º°]\s+Contrato|Contrato\s+N[º°]?)[\s:]+([A-Z0-9-]+)',
            # Padrão: "CT-" ou "Contrato-"
            r'(?:CT|Contrato)[\s-]*([0-9-]+)',
            # Padrão genérico
            r'(?:n[úu]mero|n[º°]|contrato)[\s:]+([A-Z0-9-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                num = match.group(1).strip()
                if len(num) > 0:
                    return num
        return None
    
    def _extract_tipo_contrato(self, text_lower: str) -> Optional[str]:
        """Extrai tipo de contrato."""
        tipos = {
            'financiamento': 'Financiamento',
            'empréstimo': 'Empréstimo',
            'consignado': 'Consignado',
            'pessoal': 'Pessoal',
            'veículo': 'Financiamento de Veículo',
            'imóvel': 'Financiamento Imobiliário',
        }
        
        for key, value in tipos.items():
            if key in text_lower:
                return value
        return None
    
    def _extract_observacoes(self, text: str) -> Optional[str]:
        """Extrai observações."""
        # Procura seção de observações
        match = re.search(r'(?:observa[çc][õo]es?|notas?)[\s:]+(.+?)(?:\n\n|\Z)', text, re.IGNORECASE | re.DOTALL)
        if match:
            obs = match.group(1).strip()[:200]  # Limita a 200 caracteres
            return obs
        return None
    
    def extract_from_pdf(self, pdf_path: str) -> ContratoInfo:
        """Extrai informações de um PDF."""
        text = self.document_processor.extract_text_from_pdf(pdf_path)
        return self.extract_from_text(text)

