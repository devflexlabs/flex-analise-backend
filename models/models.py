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
    quantidade_parcelas: Optional[int] = Field(None, description="Número total de parcelas (se disponível)")
    valor_parcela: Optional[float] = Field(None, description="Valor de cada parcela")
    data_vencimento_primeira: Optional[str] = Field(None, description="Data de vencimento da primeira parcela")
    data_vencimento_ultima: Optional[str] = Field(None, description="Data de vencimento da última parcela")
    taxa_juros: Optional[float] = Field(None, description="Taxa de juros (se mencionada)")
    numero_contrato: Optional[str] = Field(None, description="Número do contrato")
    cpf_cnpj: Optional[str] = Field(None, description="CPF ou CNPJ do cliente")
    tipo_contrato: Optional[str] = Field(None, description="Tipo de contrato (empréstimo, financiamento, etc.)")
    banco_credor: Optional[str] = Field(None, description="Nome do banco ou instituição financeira credora (ex: Santander, Banco do Brasil, Itaú, etc.)")
    # Informações do veículo (se aplicável)
    veiculo_marca: Optional[str] = Field(None, description="Marca do veículo")
    veiculo_modelo: Optional[str] = Field(None, description="Modelo do veículo")
    veiculo_ano: Optional[str] = Field(None, description="Ano do veículo")
    veiculo_cor: Optional[str] = Field(None, description="Cor do veículo")
    veiculo_placa: Optional[str] = Field(None, description="Placa do veículo (se mencionada)")
    veiculo_renavam: Optional[str] = Field(None, description="RENAVAM do veículo (se mencionado no contrato)")
    observacoes: Optional[str] = Field(None, description="Observações adicionais relevantes")
    # Informações de recálculo com BACEN (opcional)
    recalculo_bacen: Optional[dict] = Field(None, description="Resultado do recálculo usando dados do BACEN")
    
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
                "banco_credor": "Santander",
                "observacoes": "Contrato com garantia real"
            }
        }

