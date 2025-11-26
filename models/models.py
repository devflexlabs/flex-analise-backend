"""
Modelos de dados para informações extraídas de contratos financeiros.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ContratoInfo(BaseModel):
    """Informações extraídas de um contrato financeiro."""
    
    nome_cliente: str = Field(description="Nome completo do cliente/devedor")
    valor_divida: Optional[float] = Field(None, description="Valor total da dívida em reais (se aplicável)")
    quantidade_parcelas: int = Field(description="Número total de parcelas")
    valor_parcela: Optional[float] = Field(None, description="Valor de cada parcela")
    data_vencimento_primeira: Optional[str] = Field(None, description="Data de vencimento da primeira parcela")
    data_vencimento_ultima: Optional[str] = Field(None, description="Data de vencimento da última parcela")
    taxa_juros: Optional[float] = Field(None, description="Taxa de juros (se mencionada)")
    numero_contrato: Optional[str] = Field(None, description="Número do contrato")
    cpf_cnpj: Optional[str] = Field(None, description="CPF ou CNPJ do cliente")
    tipo_contrato: Optional[str] = Field(None, description="Tipo de contrato (empréstimo, financiamento, etc.)")
    observacoes: Optional[str] = Field(None, description="Observações adicionais relevantes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nome_cliente": "João Silva",
                "valor_divida": 50000.00,
                "quantidade_parcelas": 60,
                "valor_parcela": 1250.00,
                "data_vencimento_primeira": "2024-02-15",
                "data_vencimento_ultima": "2029-01-15",
                "taxa_juros": 2.5,
                "numero_contrato": "CT-2024-001",
                "cpf_cnpj": "123.456.789-00",
                "tipo_contrato": "Financiamento",
                "observacoes": "Contrato com garantia real"
            }
        }

