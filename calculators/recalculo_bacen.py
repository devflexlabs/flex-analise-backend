"""
Módulo de recálculo de contratos com base em dados do BACEN.
Integra busca de taxas históricas com cálculos financeiros.
"""
from datetime import date, datetime
from typing import Optional, Dict, List
from .bacen_integration import BacenIntegration
from .financial_calculator import FinancialCalculator


class RecalculoBacen:
    """Recalculador de contratos usando dados do BACEN."""
    
    def __init__(self):
        """Inicializa o recalculador."""
        self.bacen = BacenIntegration()
        self.calculator = FinancialCalculator()
    
    def parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Converte string de data para objeto date."""
        if not date_str:
            return None
        
        try:
            # Tenta formato YYYY-MM-DD
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            try:
                # Tenta formato DD/MM/YYYY
                return datetime.strptime(date_str, "%d/%m/%Y").date()
            except:
                return None
    
    def recalcular_contrato(
        self,
        valor_principal: float,
        taxa_juros_contrato: Optional[float],
        numero_parcelas: int,
        valor_parcela_contrato: Optional[float],
        data_contratacao: Optional[str] = None,
        data_primeira_parcela: Optional[str] = None,
        tipo_taxa: str = "prefixada",  # "prefixada" ou "posfixada"
        indexador: str = "selic",  # "selic" ou "cdi"
        metodologia: Optional[str] = None  # "price", "sac", ou None (detecta automaticamente)
    ) -> Dict:
        """
        Recalcula contrato usando taxas do BACEN.
        
        Args:
            valor_principal: Valor principal do contrato
            taxa_juros_contrato: Taxa de juros informada no contrato (em % a.m.)
            numero_parcelas: Número de parcelas
            valor_parcela_contrato: Valor da parcela informado no contrato
            data_contratacao: Data de contratação (YYYY-MM-DD)
            data_primeira_parcela: Data da primeira parcela (YYYY-MM-DD)
            tipo_taxa: "prefixada" ou "posfixada"
            indexador: "selic" ou "cdi" (para taxas pós-fixadas)
            metodologia: "price", "sac", ou None (detecta automaticamente)
            
        Returns:
            Dicionário com resultados do recálculo
        """
        resultado = {
            "sucesso": False,
            "erro": None,
            "metodologia_detectada": None,
            "taxa_bacen": None,
            "taxa_contrato": taxa_juros_contrato,
            "diferenca_taxa": None,
            "recalculo_price": None,
            "recalculo_sac": None,
            "comparacao": None,
            "aviso_taxa_posfixada": None
        }
        
        try:
            # Parse de datas
            data_contrato = self.parse_date(data_contratacao) or self.parse_date(data_primeira_parcela) or date.today()
            data_primeira = self.parse_date(data_primeira_parcela) or data_contrato
            
            # Para taxas pós-fixadas, busca taxa do BACEN
            taxa_bacen = None
            if tipo_taxa == "posfixada":
                # Busca taxa do indexador na data de contratação
                if indexador.lower() == "selic":
                    taxa_bacen = self.bacen.buscar_taxa_selic(data_contrato, diaria=False)
                elif indexador.lower() == "cdi":
                    taxa_bacen = self.bacen.buscar_cdi(data_contrato)
                
                if taxa_bacen:
                    # Converte taxa anual do BACEN para mensal
                    taxa_bacen_mensal = self.calculator.converter_taxa_anual_para_mensal(taxa_bacen)
                    
                    # Se há spread no contrato, adiciona
                    if taxa_juros_contrato:
                        # Assume que taxa_juros_contrato é o spread
                        taxa_efetiva = taxa_bacen_mensal + taxa_juros_contrato
                    else:
                        taxa_efetiva = taxa_bacen_mensal
                    
                    resultado["taxa_bacen"] = taxa_bacen
                    resultado["taxa_bacen_mensal"] = taxa_bacen_mensal
                    resultado["taxa_efetiva_mensal"] = taxa_efetiva
                    resultado["aviso_taxa_posfixada"] = (
                        f"Taxa pós-fixada baseada em {indexador.upper()} do período. "
                        f"Valor final só será conhecido após período de referência. "
                        f"Usando {indexador.upper()} de {data_contrato.strftime('%d/%m/%Y')}: {taxa_bacen:.2f}% a.a."
                    )
                else:
                    resultado["aviso_taxa_posfixada"] = (
                        f"Não foi possível buscar {indexador.upper()} do BACEN para a data {data_contrato.strftime('%d/%m/%Y')}. "
                        f"Usando taxa do contrato como estimativa."
                    )
                    taxa_efetiva = taxa_juros_contrato or 0.0
            else:
                # Taxa prefixada: usa taxa do contrato
                taxa_efetiva = taxa_juros_contrato or 0.0
            
            if taxa_efetiva <= 0:
                resultado["erro"] = "Taxa de juros não disponível para recálculo"
                return resultado
            
            # Detecta metodologia se não informada
            if not metodologia and valor_parcela_contrato:
                metodologia = self.calculator.detectar_metodologia_amortizacao(
                    valor_principal,
                    taxa_efetiva,
                    numero_parcelas,
                    valor_parcela_contrato
                )
                resultado["metodologia_detectada"] = metodologia
            
            # Recalcula com Price
            recalculo_price = self.calculator.calcular_tabela_price(
                valor_principal,
                taxa_efetiva,
                numero_parcelas,
                data_primeira
            )
            resultado["recalculo_price"] = recalculo_price
            
            # Recalcula com SAC
            recalculo_sac = self.calculator.calcular_sac(
                valor_principal,
                taxa_efetiva,
                numero_parcelas,
                data_primeira
            )
            resultado["recalculo_sac"] = recalculo_sac
            
            # Compara com valores do contrato
            comparacao = {
                "valor_parcela_contrato": valor_parcela_contrato,
                "valor_parcela_price": recalculo_price["valor_parcela"],
                "valor_parcela_sac_inicial": recalculo_sac["valor_parcela_inicial"],
                "diferenca_price": None,
                "diferenca_sac": None,
                "total_pago_price": recalculo_price["total_pago"],
                "total_pago_sac": recalculo_sac["total_pago"],
                "total_juros_price": recalculo_price["total_juros"],
                "total_juros_sac": recalculo_sac["total_juros"]
            }
            
            if valor_parcela_contrato:
                comparacao["diferenca_price"] = abs(recalculo_price["valor_parcela"] - valor_parcela_contrato)
                comparacao["diferenca_sac"] = abs(recalculo_sac["valor_parcela_inicial"] - valor_parcela_contrato)
            
            resultado["comparacao"] = comparacao
            
            # Calcula diferença de taxa se houver taxa do BACEN
            if taxa_bacen and taxa_juros_contrato:
                taxa_anual_contrato = self.calculator.converter_taxa_mensal_para_anual(taxa_juros_contrato)
                resultado["diferenca_taxa"] = abs(taxa_anual_contrato - taxa_bacen)
            
            resultado["sucesso"] = True
            
        except Exception as e:
            resultado["erro"] = str(e)
            resultado["sucesso"] = False
        
        return resultado
    
    def validar_contrato(
        self,
        valor_principal: float,
        taxa_juros_contrato: Optional[float],
        numero_parcelas: int,
        valor_parcela_contrato: Optional[float],
        data_contratacao: Optional[str] = None
    ) -> Dict:
        """
        Valida se os valores do contrato estão corretos.
        
        Returns:
            Dicionário com validações e possíveis irregularidades
        """
        validacao = {
            "valido": True,
            "irregularidades": [],
            "aviso": []
        }
        
        try:
            # Recalcula contrato
            recalculo = self.recalcular_contrato(
                valor_principal=valor_principal,
                taxa_juros_contrato=taxa_juros_contrato,
                numero_parcelas=numero_parcelas,
                valor_parcela_contrato=valor_parcela_contrato,
                data_contratacao=data_contratacao
            )
            
            if not recalculo["sucesso"]:
                validacao["aviso"].append(f"Não foi possível recalcular: {recalculo.get('erro')}")
                return validacao
            
            # Compara valores
            if valor_parcela_contrato and recalculo["comparacao"]:
                diff_price = recalculo["comparacao"]["diferenca_price"]
                diff_sac = recalculo["comparacao"]["diferenca_sac"]
                
                # Tolerância de R$ 1,00
                if diff_price and diff_price > 1.0:
                    validacao["irregularidades"].append(
                        f"Divergência no valor da parcela: contrato informa R$ {valor_parcela_contrato:.2f}, "
                        f"mas cálculo Price resulta em R$ {recalculo['recalculo_price']['valor_parcela']:.2f} "
                        f"(diferença de R$ {diff_price:.2f})"
                    )
                    validacao["valido"] = False
                
                if diff_sac and diff_sac > 1.0:
                    validacao["aviso"].append(
                        f"Se for SAC, divergência: primeira parcela deveria ser R$ {recalculo['recalculo_sac']['valor_parcela_inicial']:.2f} "
                        f"(diferença de R$ {diff_sac:.2f})"
                    )
            
            # Verifica se metodologia foi detectada
            if recalculo["metodologia_detectada"]:
                validacao["metodologia"] = recalculo["metodologia_detectada"]
            else:
                validacao["aviso"].append("Não foi possível detectar a metodologia de amortização (Price ou SAC)")
            
        except Exception as e:
            validacao["aviso"].append(f"Erro na validação: {str(e)}")
        
        return validacao

