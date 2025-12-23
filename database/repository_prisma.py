"""
Repository para operações de banco de dados usando Prisma.
"""
from typing import Optional, List, Dict
from datetime import datetime
import json
from prisma.models import AnaliseContrato
from backend.database.prisma_client import prisma
from backend.models.models import ContratoInfo


class AnaliseRepositoryPrisma:
    """Repository para gerenciar análises de contratos usando Prisma."""
    
    async def verificar_duplicado(self, contrato_info: ContratoInfo) -> Optional[AnaliseContrato]:
        """
        Verifica se já existe uma análise para este contrato.
        Verifica por: numero_contrato + banco_credor + cpf_cnpj
        """
        if not contrato_info.numero_contrato or not contrato_info.banco_credor:
            return None
        
        # Busca por número do contrato e banco
        existing = await prisma.analisecontrato.find_first(
            where={
                "numeroContrato": contrato_info.numero_contrato,
                "bancoCredor": contrato_info.banco_credor,
            }
        )
        
        # Se não encontrou, tenta por CPF/CNPJ + banco (para casos sem número de contrato)
        if not existing and contrato_info.cpf_cnpj:
            existing = await prisma.analisecontrato.find_first(
                where={
                    "cpfCnpj": contrato_info.cpf_cnpj,
                    "bancoCredor": contrato_info.banco_credor,
                    "numeroContrato": None,  # Contratos sem número
                }
            )
        
        return existing
    
    async def salvar_analise(self, contrato_info: ContratoInfo, arquivo_original: Optional[str] = None) -> AnaliseContrato:
        """
        Salva uma análise de contrato no banco de dados.
        Só salva se não existir duplicado.
        
        Args:
            contrato_info: Objeto ContratoInfo com os dados extraídos
            arquivo_original: Nome do arquivo original (opcional)
            
        Returns:
            AnaliseContrato salvo ou existente
        """
        # Verifica se já existe
        existing = await self.verificar_duplicado(contrato_info)
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
        
        # Cria registro
        analise = await prisma.analisecontrato.create(
            data={
                "dataAnalise": datetime.utcnow(),
                "nomeCliente": contrato_info.nome_cliente,
                "cpfCnpj": contrato_info.cpf_cnpj,
                "numeroContrato": contrato_info.numero_contrato,
                "tipoContrato": contrato_info.tipo_contrato,
                "bancoCredor": contrato_info.banco_credor,
                "valorDivida": contrato_info.valor_divida,
                "valorParcela": contrato_info.valor_parcela,
                "quantidadeParcelas": contrato_info.quantidade_parcelas,
                "taxaJuros": contrato_info.taxa_juros,
                "dataVencimentoPrimeira": contrato_info.data_vencimento_primeira,
                "dataVencimentoUltima": contrato_info.data_vencimento_ultima,
                "veiculoMarca": contrato_info.veiculo_marca,
                "veiculoModelo": contrato_info.veiculo_modelo,
                "veiculoAno": contrato_info.veiculo_ano,
                "veiculoCor": contrato_info.veiculo_cor,
                "veiculoPlaca": contrato_info.veiculo_placa,
                "veiculoRenavam": contrato_info.veiculo_renavam,
                "temVeiculo": tem_veiculo,
                "observacoes": contrato_info.observacoes,
                "recalculoBacen": recalculo_bacen_str,
                "temTaxaAbusiva": tem_taxa_abusiva,
                "temCetAlto": tem_cet_alto,
                "temClausulasAbusivas": tem_clausulas_abusivas,
                "arquivoOriginal": arquivo_original,
            }
        )
        
        print(f"✅ Análise salva no banco de dados: ID {analise.id}")
        return analise
    
    async def obter_por_id(self, analise_id: int) -> Optional[AnaliseContrato]:
        """Obtém uma análise por ID."""
        return await prisma.analisecontrato.find_unique(where={"id": analise_id})
    
    async def listar_analises(
        self,
        limite: int = 100,
        offset: int = 0,
        banco: Optional[str] = None,
        tipo_contrato: Optional[str] = None,
        estado: Optional[str] = None,
    ) -> List[AnaliseContrato]:
        """Lista análises com filtros opcionais."""
        where = {}
        
        if banco:
            where["bancoCredor"] = {"contains": banco, "mode": "insensitive"}
        if tipo_contrato:
            where["tipoContrato"] = {"contains": tipo_contrato, "mode": "insensitive"}
        if estado:
            where["estado"] = estado.upper()
        
        return await prisma.analisecontrato.find_many(
            where=where,
            take=limite,
            skip=offset,
            order_by={"dataAnalise": "desc"}
        )
    
    async def estatisticas_por_banco(self, estado: Optional[str] = None) -> List[Dict]:
        """
        Retorna estatísticas agregadas por banco usando Prisma.
        """
        where = {"bancoCredor": {"not": None}}
        if estado:
            where["estado"] = estado.upper()
        
        # Busca todos os registros e agrega em Python (Prisma não tem groupBy completo)
        analises = await prisma.analisecontrato.find_many(
            where=where,
            select={
                "bancoCredor": True,
                "taxaJuros": True,
                "valorDivida": True,
                "temVeiculo": True,
                "temTaxaAbusiva": True,
            }
        )
        
        # Agrega por banco
        stats_dict = {}
        for analise in analises:
            banco = analise.bancoCredor
            if not banco:
                continue
            
            if banco not in stats_dict:
                stats_dict[banco] = {
                    "total_contratos": 0,
                    "taxas_juros": [],
                    "valores_divida": [],
                    "total_veiculos": 0,
                    "total_taxa_abusiva": 0,
                }
            
            stats = stats_dict[banco]
            stats["total_contratos"] += 1
            
            if analise.taxaJuros is not None:
                stats["taxas_juros"].append(analise.taxaJuros)
            if analise.valorDivida is not None:
                stats["valores_divida"].append(analise.valorDivida)
            if analise.temVeiculo:
                stats["total_veiculos"] += 1
            if analise.temTaxaAbusiva:
                stats["total_taxa_abusiva"] += 1
        
        # Calcula médias e formata resultado
        resultado = []
        for banco, stats in stats_dict.items():
            taxa_media = sum(stats["taxas_juros"]) / len(stats["taxas_juros"]) if stats["taxas_juros"] else 0
            valor_medio = sum(stats["valores_divida"]) / len(stats["valores_divida"]) if stats["valores_divida"] else 0
            valor_total = sum(stats["valores_divida"])
            
            resultado.append({
                "banco": banco,
                "total_contratos": stats["total_contratos"],
                "taxa_juros_media": round(taxa_media, 2),
                "valor_medio_divida": round(valor_medio, 2),
                "valor_total_divida": round(valor_total, 2),
                "total_veiculos": stats["total_veiculos"],
                "total_taxa_abusiva": stats["total_taxa_abusiva"],
                "percentual_taxa_abusiva": round((stats["total_taxa_abusiva"] / stats["total_contratos"] * 100) if stats["total_contratos"] > 0 else 0, 2),
            })
        
        return resultado
    
    async def estatisticas_por_produto(self, estado: Optional[str] = None) -> List[Dict]:
        """Retorna estatísticas agregadas por tipo de produto."""
        where = {"tipoContrato": {"not": None}}
        if estado:
            where["estado"] = estado.upper()
        
        analises = await prisma.analisecontrato.find_many(
            where=where,
            select={
                "tipoContrato": True,
                "taxaJuros": True,
                "valorDivida": True,
            }
        )
        
        # Agrega por produto
        stats_dict = {}
        for analise in analises:
            produto = analise.tipoContrato
            if not produto:
                continue
            
            if produto not in stats_dict:
                stats_dict[produto] = {
                    "total_contratos": 0,
                    "taxas_juros": [],
                    "valores_divida": [],
                }
            
            stats = stats_dict[produto]
            stats["total_contratos"] += 1
            
            if analise.taxaJuros is not None:
                stats["taxas_juros"].append(analise.taxaJuros)
            if analise.valorDivida is not None:
                stats["valores_divida"].append(analise.valorDivida)
        
        # Calcula médias
        resultado = []
        for produto, stats in stats_dict.items():
            taxa_media = sum(stats["taxas_juros"]) / len(stats["taxas_juros"]) if stats["taxas_juros"] else 0
            valor_medio = sum(stats["valores_divida"]) / len(stats["valores_divida"]) if stats["valores_divida"] else 0
            
            resultado.append({
                "produto": produto,
                "total_contratos": stats["total_contratos"],
                "taxa_juros_media": round(taxa_media, 2),
                "valor_medio_divida": round(valor_medio, 2),
            })
        
        return resultado
    
    async def mapa_divida_mensal(self, ano: int, mes: int, estado: Optional[str] = None) -> Dict:
        """
        Gera relatório mensal tipo "mapa da dívida".
        """
        data_inicio = datetime(ano, mes, 1)
        if mes == 12:
            data_fim = datetime(ano + 1, 1, 1)
        else:
            data_fim = datetime(ano, mes + 1, 1)
        
        where = {
            "dataAnalise": {
                "gte": data_inicio,
                "lt": data_fim,
            }
        }
        
        if estado:
            where["estado"] = estado.upper()
        
        # Busca todas as análises do período
        analises = await prisma.analisecontrato.find_many(where=where)
        
        total_analises = len(analises)
        
        # Calcula estatísticas gerais
        taxas = [a.taxaJuros for a in analises if a.taxaJuros is not None]
        valores = [a.valorDivida for a in analises if a.valorDivida is not None]
        idades = [a.idadeCliente for a in analises if a.idadeCliente is not None]
        
        taxa_media = sum(taxas) / len(taxas) if taxas else 0
        valor_medio = sum(valores) / len(valores) if valores else 0
        valor_total = sum(valores)
        idade_media = sum(idades) / len(idades) if idades else None
        
        # Top bancos por juros
        bancos_juros = {}
        for analise in analises:
            if analise.bancoCredor and analise.taxaJuros is not None:
                if analise.bancoCredor not in bancos_juros:
                    bancos_juros[analise.bancoCredor] = []
                bancos_juros[analise.bancoCredor].append(analise.taxaJuros)
        
        top_bancos_juros = sorted(
            [
                {"banco": banco, "taxa_media": round(sum(taxas) / len(taxas), 2)}
                for banco, taxas in bancos_juros.items()
            ],
            key=lambda x: x["taxa_media"],
            reverse=True
        )[:10]
        
        # Bancos que mais apreendem veículos
        bancos_veiculos = {}
        for analise in analises:
            if analise.bancoCredor and analise.temVeiculo:
                bancos_veiculos[analise.bancoCredor] = bancos_veiculos.get(analise.bancoCredor, 0) + 1
        
        bancos_mais_veiculos = sorted(
            [{"banco": banco, "total_veiculos": count} for banco, count in bancos_veiculos.items()],
            key=lambda x: x["total_veiculos"],
            reverse=True
        )[:10]
        
        # Distribuição por estado
        distribuicao_estado = {}
        for analise in analises:
            if analise.estado:
                distribuicao_estado[analise.estado] = distribuicao_estado.get(analise.estado, 0) + 1
        
        # Distribuição por idade
        distribuicao_idade = {}
        for analise in analises:
            if analise.idadeCliente:
                idade = analise.idadeCliente
                if idade < 25:
                    faixa = "18-24"
                elif idade < 35:
                    faixa = "25-34"
                elif idade < 45:
                    faixa = "35-44"
                elif idade < 55:
                    faixa = "45-54"
                elif idade < 65:
                    faixa = "55-64"
                else:
                    faixa = "65+"
                distribuicao_idade[faixa] = distribuicao_idade.get(faixa, 0) + 1
        
        return {
            "periodo": {
                "ano": ano,
                "mes": mes,
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim.isoformat(),
            },
            "resumo": {
                "total_analises": total_analises,
                "taxa_juros_media": round(taxa_media, 2),
                "valor_medio_divida": round(valor_medio, 2),
                "valor_total_divida": round(valor_total, 2),
                "idade_media": round(idade_media, 1) if idade_media else None,
            },
            "top_bancos_juros": top_bancos_juros,
            "bancos_mais_veiculos": bancos_mais_veiculos,
            "distribuicao_estado": [{"estado": estado, "total": count} for estado, count in distribuicao_estado.items()],
            "distribuicao_idade": [{"faixa_etaria": faixa, "total": count} for faixa, count in distribuicao_idade.items()],
        }

