"""
Modelos SQLAlchemy para armazenamento de análises de contratos.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Optional

Base = declarative_base()


class AnaliseContrato(Base):
    """
    Modelo para armazenar análises de contratos financeiros.
    
    Este modelo armazena 100% das análises realizadas para permitir
    mineração de dados e geração de relatórios como "mapa da dívida".
    """
    __tablename__ = "analises_contratos"
    
    # ID único
    id = Column(Integer, primary_key=True, index=True)
    
    # Timestamp da análise
    data_analise = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Dados do cliente
    nome_cliente = Column(String(255), nullable=False, index=True)
    cpf_cnpj = Column(String(20), index=True)  # Indexado para busca rápida
    
    # Dados do contrato
    numero_contrato = Column(String(100), index=True)
    tipo_contrato = Column(String(100), index=True)  # Financiamento, Empréstimo, etc.
    banco_credor = Column(String(255), index=True)  # Indexado para relatórios por banco
    
    # Valores financeiros
    valor_divida = Column(Float)
    valor_parcela = Column(Float)
    quantidade_parcelas = Column(Integer)
    taxa_juros = Column(Float, index=True)  # Indexado para análises de juros
    
    # Datas
    data_vencimento_primeira = Column(String(20))  # YYYY-MM-DD
    data_vencimento_ultima = Column(String(20))
    
    # Informações do veículo (se aplicável)
    veiculo_marca = Column(String(100), index=True)
    veiculo_modelo = Column(String(255))
    veiculo_ano = Column(String(10))
    veiculo_cor = Column(String(50))
    veiculo_placa = Column(String(10), index=True)
    veiculo_renavam = Column(String(20))
    tem_veiculo = Column(Boolean, default=False, index=True)  # Flag para filtros rápidos
    
    # Observações e análise
    observacoes = Column(Text)  # Texto completo das observações
    
    # Recálculo BACEN (JSON serializado)
    recalculo_bacen = Column(Text)  # JSON string do recálculo
    
    # Campos adicionais para relatórios e mineração de dados
    # Localização (pode ser extraída do CPF ou informada manualmente)
    estado = Column(String(2), index=True)  # RS, SP, etc.
    cidade = Column(String(100), index=True)
    
    # Idade do cliente (pode ser calculada a partir de data de nascimento se disponível)
    idade_cliente = Column(Integer, index=True)
    
    # Flags para análise de irregularidades (extraídas das observações)
    tem_taxa_abusiva = Column(Boolean, default=False, index=True)
    tem_cet_alto = Column(Boolean, default=False, index=True)
    tem_clausulas_abusivas = Column(Boolean, default=False, index=True)
    
    # Metadados
    arquivo_original = Column(String(500))  # Nome do arquivo original (opcional)
    
    # Índices compostos para queries comuns
    __table_args__ = (
        Index('idx_banco_tipo', 'banco_credor', 'tipo_contrato'),
        Index('idx_data_banco', 'data_analise', 'banco_credor'),
        Index('idx_estado_banco', 'estado', 'banco_credor'),
        Index('idx_tem_veiculo_banco', 'tem_veiculo', 'banco_credor'),
    )
    
    def to_dict(self):
        """Converte o modelo para dicionário."""
        return {
            "id": self.id,
            "data_analise": self.data_analise.isoformat() if self.data_analise else None,
            "nome_cliente": self.nome_cliente,
            "cpf_cnpj": self.cpf_cnpj,
            "numero_contrato": self.numero_contrato,
            "tipo_contrato": self.tipo_contrato,
            "banco_credor": self.banco_credor,
            "valor_divida": self.valor_divida,
            "valor_parcela": self.valor_parcela,
            "quantidade_parcelas": self.quantidade_parcelas,
            "taxa_juros": self.taxa_juros,
            "data_vencimento_primeira": self.data_vencimento_primeira,
            "data_vencimento_ultima": self.data_vencimento_ultima,
            "veiculo_marca": self.veiculo_marca,
            "veiculo_modelo": self.veiculo_modelo,
            "veiculo_ano": self.veiculo_ano,
            "veiculo_cor": self.veiculo_cor,
            "veiculo_placa": self.veiculo_placa,
            "veiculo_renavam": self.veiculo_renavam,
            "tem_veiculo": self.tem_veiculo,
            "observacoes": self.observacoes,
            "recalculo_bacen": self.recalculo_bacen,
            "estado": self.estado,
            "cidade": self.cidade,
            "idade_cliente": self.idade_cliente,
            "tem_taxa_abusiva": self.tem_taxa_abusiva,
            "tem_cet_alto": self.tem_cet_alto,
            "tem_clausulas_abusivas": self.tem_clausulas_abusivas,
            "arquivo_original": self.arquivo_original,
        }

