"""
Modelos de dados Pydantic para requisições e respostas da API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from .models import ContratoInfo

class HealthResponse(BaseModel):
    status: str = Field("ok", description="Status da API")

class RootResponse(BaseModel):
    message: str = Field(description="Mensagem de boas-vindas")
    version: str = Field(description="Versão da API")

class EstatisticaBanco(BaseModel):
    banco: str = Field(description="Nome do banco")
    total_contratos: int = Field(description="Total de contratos analisados")
    taxa_juros_media: float = Field(description="Taxa média de juros (%)")
    valor_medio_divida: float = Field(description="Valor médio da dívida (R$)")
    valor_total_divida: float = Field(description="Valor total das dívidas (R$)")
    total_veiculos: int = Field(description="Total de veículos financiados")
    total_taxa_abusiva: int = Field(description="Total de contratos com suspeita de taxa abusiva")
    percentual_taxa_abusiva: float = Field(description="Percentual de contratos com suspeita de taxa abusiva (%)")

class EstatisticaProduto(BaseModel):
    produto: str = Field(description="Tipo de produto/contrato")
    total_contratos: int = Field(description="Total de contratos analisados")
    taxa_juros_media: float = Field(description="Taxa média de juros (%)")
    valor_medio_divida: float = Field(description="Valor médio da dívida (R$)")

class PeriodoInfo(BaseModel):
    ano: int
    mes: int
    data_inicio: str
    data_fim: str

class ResumoMapa(BaseModel):
    total_analises: int
    taxa_juros_media: float
    valor_medio_divida: float
    valor_total_divida: float
    idade_media: Optional[float] = None

class BancoJuros(BaseModel):
    banco: str
    taxa_media: float

class BancoVeiculos(BaseModel):
    banco: str
    total_veiculos: int

class DistribuicaoEstado(BaseModel):
    estado: str
    total: int

class DistribuicaoIdade(BaseModel):
    faixa_etaria: str
    total: int

class MapaDividaResponse(BaseModel):
    periodo: PeriodoInfo
    resumo: ResumoMapa
    top_bancos_juros: List[BancoJuros]
    bancos_mais_veiculos: List[BancoVeiculos]
    distribuicao_estado: List[DistribuicaoEstado]
    distribuicao_idade: List[DistribuicaoIdade]

class AnaliseItem(BaseModel):
    id: int
    data_analise: Optional[str]
    nome_cliente: str
    cpf_cnpj: Optional[str]
    numero_contrato: Optional[str]
    tipo_contrato: Optional[str]
    banco_credor: Optional[str]
    valor_divida: Optional[float]
    valor_parcela: Optional[float]
    quantidade_parcelas: Optional[int]
    taxa_juros: Optional[float]
    data_vencimento_primeira: Optional[str]
    data_vencimento_ultima: Optional[str]
    veiculo_marca: Optional[str]
    veiculo_modelo: Optional[str]
    veiculo_ano: Optional[str]
    veiculo_cor: Optional[str]
    veiculo_placa: Optional[str]
    veiculo_renavam: Optional[str]
    tem_veiculo: bool
    observacoes: Optional[str]
    recalculo_bacen: Optional[str]
    estado: Optional[str]
    cidade: Optional[str]
    idade_cliente: Optional[int]
    tem_taxa_abusiva: bool
    tem_cet_alto: bool
    tem_clausulas_abusivas: bool
    arquivo_original: Optional[str]

class ExtractResponse(ContratoInfo):
    analise_id: Optional[int] = Field(None, description="ID da análise salva no banco de dados")
    ja_existia: bool = Field(False, description="Indica se o contrato já existia no banco de dados")
