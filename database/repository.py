"""
Repository para operações de banco de dados relacionadas a análises de contratos.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import json

from .models import AnaliseContrato
from backend.models.models import ContratoInfo


class AnaliseRepository:
    """Repository para gerenciar análises de contratos."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def verificar_duplicado(self, contrato_info: ContratoInfo) -> Optional[AnaliseContrato]:
        """
        Verifica se já existe um contrato duplicado no banco.
        
        Args:
            contrato_info: Objeto ContratoInfo com os dados extraídos
            
        Returns:
            AnaliseContrato existente ou None
        """
        # Primeiro tenta por número de contrato + banco
        if contrato_info.numero_contrato and contrato_info.banco_credor:
            existing = self.db.query(AnaliseContrato).filter(
                and_(
                    AnaliseContrato.numero_contrato == contrato_info.numero_contrato,
                    AnaliseContrato.banco_credor == contrato_info.banco_credor
                )
            ).first()
            if existing:
                return existing
        
        # Se não encontrou, tenta por CPF/CNPJ + banco (para contratos sem número)
        if contrato_info.cpf_cnpj and contrato_info.banco_credor:
            existing = self.db.query(AnaliseContrato).filter(
                and_(
                    AnaliseContrato.cpf_cnpj == contrato_info.cpf_cnpj,
                    AnaliseContrato.banco_credor == contrato_info.banco_credor,
                    AnaliseContrato.numero_contrato.is_(None)
                )
            ).first()
            if existing:
                return existing
        
        return None
    
    def salvar_analise(self, contrato_info: ContratoInfo, arquivo_original: Optional[str] = None) -> Optional[AnaliseContrato]:
        """
        Salva uma análise de contrato no banco de dados.
        Só salva se não existir duplicado.
        
        Args:
            contrato_info: Objeto ContratoInfo com os dados extraídos
            arquivo_original: Nome do arquivo original (opcional)
            
        Returns:
            AnaliseContrato salvo ou existente (se duplicado)
        """
        # Verifica se já existe
        existing = self.verificar_duplicado(contrato_info)
        if existing:
            print(f"ℹ️  Contrato já existe no banco (ID: {existing.id}). Não salvando duplicado.")
            return existing
        # Extrai flags de irregularidades das observações
        observacoes_lower = (contrato_info.observacoes or "").lower()
        tem_taxa_abusiva = any(termo in observacoes_lower for termo in [
            "taxa abusiva", "taxa extremamente alta", "taxa muito alta",
            "prática abusiva", "juros abusivos"
        ])
        tem_cet_alto = any(termo in observacoes_lower for termo in [
            "cet alto", "cet muito alto", "cet extremamente alto",
            "encargos excessivos"
        ])
        tem_clausulas_abusivas = any(termo in observacoes_lower for termo in [
            "cláusulas abusivas", "clausulas abusivas", "violação cdc",
            "violação do cdc", "irregularidades identificadas"
        ])
        
        # Verifica se tem veículo
        tem_veiculo = bool(
            contrato_info.veiculo_marca or
            contrato_info.veiculo_modelo or
            contrato_info.veiculo_ano or
            contrato_info.veiculo_placa
        )
        
        # Serializa recalculo_bacen se existir
        recalculo_bacen_str = None
        if contrato_info.recalculo_bacen:
            recalculo_bacen_str = json.dumps(contrato_info.recalculo_bacen)
        
        # Debug: verifica dados antes de salvar
        print(f"🔍 Dados recebidos para salvar:")
        print(f"   - Veículo marca: {contrato_info.veiculo_marca}")
        print(f"   - Veículo modelo: {contrato_info.veiculo_modelo}")
        print(f"   - Veículo ano: {contrato_info.veiculo_ano}")
        print(f"   - Veículo cor: {contrato_info.veiculo_cor}")
        print(f"   - Veículo placa: {contrato_info.veiculo_placa}")
        print(f"   - Veículo RENAVAM: {contrato_info.veiculo_renavam}")
        print(f"   - Observações: {len(contrato_info.observacoes or '')} caracteres")
        if contrato_info.observacoes:
            print(f"   - Preview observações: {contrato_info.observacoes[:100]}...")
        
        # Cria registro
        analise = AnaliseContrato(
            data_analise=datetime.utcnow(),
            nome_cliente=contrato_info.nome_cliente,
            cpf_cnpj=contrato_info.cpf_cnpj,
            numero_contrato=contrato_info.numero_contrato,
            tipo_contrato=contrato_info.tipo_contrato,
            banco_credor=contrato_info.banco_credor,
            valor_divida=contrato_info.valor_divida,
            valor_parcela=contrato_info.valor_parcela,
            quantidade_parcelas=contrato_info.quantidade_parcelas,
            taxa_juros=contrato_info.taxa_juros,
            data_vencimento_primeira=contrato_info.data_vencimento_primeira,
            data_vencimento_ultima=contrato_info.data_vencimento_ultima,
            veiculo_marca=contrato_info.veiculo_marca,
            veiculo_modelo=contrato_info.veiculo_modelo,
            veiculo_ano=contrato_info.veiculo_ano,
            veiculo_cor=contrato_info.veiculo_cor,
            veiculo_placa=contrato_info.veiculo_placa,
            veiculo_renavam=contrato_info.veiculo_renavam,
            tem_veiculo=tem_veiculo,
            observacoes=contrato_info.observacoes,
            recalculo_bacen=recalculo_bacen_str,
            tem_taxa_abusiva=tem_taxa_abusiva,
            tem_cet_alto=tem_cet_alto,
            tem_clausulas_abusivas=tem_clausulas_abusivas,
            arquivo_original=arquivo_original,
        )
        
        self.db.add(analise)
        self.db.commit()
        self.db.refresh(analise)
        
        # Debug: verifica dados salvos
        print(f"✅ Dados salvos no banco:")
        print(f"   - ID: {analise.id}")
        print(f"   - Veículo marca salva: {analise.veiculo_marca}")
        print(f"   - Veículo modelo salvo: {analise.veiculo_modelo}")
        print(f"   - Observações salvas: {len(analise.observacoes or '')} caracteres")
        
        return analise
    
    def obter_por_id(self, analise_id: int) -> Optional[AnaliseContrato]:
        """Obtém uma análise por ID."""
        return self.db.query(AnaliseContrato).filter(AnaliseContrato.id == analise_id).first()
    
    def listar_analises(
        self,
        limite: int = 100,
        offset: int = 0,
        banco: Optional[str] = None,
        tipo_contrato: Optional[str] = None,
        estado: Optional[str] = None,
    ) -> List[AnaliseContrato]:
        """Lista análises com filtros opcionais."""
        query = self.db.query(AnaliseContrato)
        
        if banco:
            query = query.filter(AnaliseContrato.banco_credor.ilike(f"%{banco}%"))
        if tipo_contrato:
            query = query.filter(AnaliseContrato.tipo_contrato.ilike(f"%{tipo_contrato}%"))
        if estado:
            query = query.filter(AnaliseContrato.estado == estado.upper())
        
        return query.order_by(AnaliseContrato.data_analise.desc()).offset(offset).limit(limite).all()
    
    def estatisticas_por_banco(self, estado: Optional[str] = None) -> List[Dict]:
        """
        Retorna estatísticas agregadas por banco.
        
        Returns:
            Lista de dicionários com estatísticas por banco
        """
        query = self.db.query(
            AnaliseContrato.banco_credor,
            func.count(AnaliseContrato.id).label('total_contratos'),
            func.avg(AnaliseContrato.taxa_juros).label('taxa_juros_media'),
            func.avg(AnaliseContrato.valor_divida).label('valor_medio_divida'),
            func.sum(AnaliseContrato.valor_divida).label('valor_total_divida'),
            func.count(AnaliseContrato.tem_veiculo).filter(AnaliseContrato.tem_veiculo == True).label('total_veiculos'),
            func.count(AnaliseContrato.tem_taxa_abusiva).filter(AnaliseContrato.tem_taxa_abusiva == True).label('total_taxa_abusiva'),
        ).filter(AnaliseContrato.banco_credor.isnot(None))
        
        if estado:
            query = query.filter(AnaliseContrato.estado == estado.upper())
        
        resultados = query.group_by(AnaliseContrato.banco_credor).all()
        
        return [
            {
                "banco": r.banco_credor,
                "total_contratos": r.total_contratos,
                "taxa_juros_media": round(float(r.taxa_juros_media or 0), 2),
                "valor_medio_divida": round(float(r.valor_medio_divida or 0), 2),
                "valor_total_divida": round(float(r.valor_total_divida or 0), 2),
                "total_veiculos": r.total_veiculos,
                "total_taxa_abusiva": r.total_taxa_abusiva,
                "percentual_taxa_abusiva": round((r.total_taxa_abusiva / r.total_contratos * 100) if r.total_contratos > 0 else 0, 2),
            }
            for r in resultados
        ]
    
    def estatisticas_por_produto(self, estado: Optional[str] = None) -> List[Dict]:
        """Retorna estatísticas agregadas por tipo de produto (tipo_contrato)."""
        query = self.db.query(
            AnaliseContrato.tipo_contrato,
            func.count(AnaliseContrato.id).label('total_contratos'),
            func.avg(AnaliseContrato.taxa_juros).label('taxa_juros_media'),
            func.avg(AnaliseContrato.valor_divida).label('valor_medio_divida'),
        ).filter(AnaliseContrato.tipo_contrato.isnot(None))
        
        if estado:
            query = query.filter(AnaliseContrato.estado == estado.upper())
        
        resultados = query.group_by(AnaliseContrato.tipo_contrato).all()
        
        return [
            {
                "produto": r.tipo_contrato,
                "total_contratos": r.total_contratos,
                "taxa_juros_media": round(float(r.taxa_juros_media or 0), 2),
                "valor_medio_divida": round(float(r.valor_medio_divida or 0), 2),
            }
            for r in resultados
        ]
    
    def mapa_divida_mensal(self, ano: int, mes: int, estado: Optional[str] = None) -> Dict:
        """
        Gera relatório mensal tipo "mapa da dívida".
        
        Args:
            ano: Ano do relatório
            mes: Mês do relatório (1-12)
            estado: Filtrar por estado (opcional)
            
        Returns:
            Dicionário com estatísticas do mês
        """
        data_inicio = datetime(ano, mes, 1)
        if mes == 12:
            data_fim = datetime(ano + 1, 1, 1)
        else:
            data_fim = datetime(ano, mes + 1, 1)
        
        query = self.db.query(AnaliseContrato).filter(
            and_(
                AnaliseContrato.data_analise >= data_inicio,
                AnaliseContrato.data_analise < data_fim
            )
        )
        
        if estado:
            query = query.filter(AnaliseContrato.estado == estado.upper())
        
        total_analises = query.count()
        
        # Estatísticas gerais
        stats = query.with_entities(
            func.count(AnaliseContrato.id).label('total'),
            func.avg(AnaliseContrato.taxa_juros).label('taxa_media'),
            func.avg(AnaliseContrato.valor_divida).label('valor_medio'),
            func.sum(AnaliseContrato.valor_divida).label('valor_total'),
            func.avg(AnaliseContrato.idade_cliente).label('idade_media'),
        ).first()
        
        # Top bancos por juros
        top_bancos_juros = query.with_entities(
            AnaliseContrato.banco_credor,
            func.avg(AnaliseContrato.taxa_juros).label('taxa_media')
        ).filter(
            AnaliseContrato.banco_credor.isnot(None),
            AnaliseContrato.taxa_juros.isnot(None)
        ).group_by(
            AnaliseContrato.banco_credor
        ).order_by(
            func.avg(AnaliseContrato.taxa_juros).desc()
        ).limit(10).all()
        
        # Bancos que mais apreendem veículos
        bancos_veiculos = query.with_entities(
            AnaliseContrato.banco_credor,
            func.count(AnaliseContrato.id).label('total_veiculos')
        ).filter(
            AnaliseContrato.banco_credor.isnot(None),
            AnaliseContrato.tem_veiculo == True
        ).group_by(
            AnaliseContrato.banco_credor
        ).order_by(
            func.count(AnaliseContrato.id).desc()
        ).limit(10).all()
        
        # Distribuição por estado
        distribuicao_estado = query.with_entities(
            AnaliseContrato.estado,
            func.count(AnaliseContrato.id).label('total')
        ).filter(
            AnaliseContrato.estado.isnot(None)
        ).group_by(
            AnaliseContrato.estado
        ).all()
        
        # Distribuição por faixa etária
        distribuicao_idade = query.with_entities(
            case(
                (AnaliseContrato.idade_cliente < 25, "18-24"),
                (and_(AnaliseContrato.idade_cliente >= 25, AnaliseContrato.idade_cliente < 35), "25-34"),
                (and_(AnaliseContrato.idade_cliente >= 35, AnaliseContrato.idade_cliente < 45), "35-44"),
                (and_(AnaliseContrato.idade_cliente >= 45, AnaliseContrato.idade_cliente < 55), "45-54"),
                (and_(AnaliseContrato.idade_cliente >= 55, AnaliseContrato.idade_cliente < 65), "55-64"),
                (AnaliseContrato.idade_cliente >= 65, "65+"),
                else_="Não informado"
            ).label('faixa_etaria'),
            func.count(AnaliseContrato.id).label('total')
        ).group_by('faixa_etaria').all()
        
        return {
            "periodo": {
                "ano": ano,
                "mes": mes,
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim.isoformat(),
            },
            "resumo": {
                "total_analises": total_analises,
                "taxa_juros_media": round(float(stats.taxa_media or 0), 2),
                "valor_medio_divida": round(float(stats.valor_medio or 0), 2),
                "valor_total_divida": round(float(stats.valor_total or 0), 2),
                "idade_media": round(float(stats.idade_media or 0), 1) if stats.idade_media else None,
            },
            "top_bancos_juros": [
                {"banco": b.banco_credor, "taxa_media": round(float(b.taxa_media or 0), 2)}
                for b in top_bancos_juros
            ],
            "bancos_mais_veiculos": [
                {"banco": b.banco_credor, "total_veiculos": b.total_veiculos}
                for b in bancos_veiculos
            ],
            "distribuicao_estado": [
                {"estado": d.estado, "total": d.total}
                for d in distribuicao_estado
            ],
            "distribuicao_idade": [
                {"faixa_etaria": d.faixa_etaria, "total": d.total}
                for d in distribuicao_idade
            ],
        }

