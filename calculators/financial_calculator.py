"""
Cálculos financeiros: Tabela Price, SAC, juros compostos, etc.
"""
import math
from typing import Optional, List, Dict
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class FinancialCalculator:
    """Calculadora financeira para amortizações e juros."""
    
    @staticmethod
    def converter_taxa_anual_para_mensal(taxa_anual: float) -> float:
        """
        Converte taxa anual para mensal (juros compostos).
        
        Args:
            taxa_anual: Taxa anual em % (ex: 12.0 = 12% a.a.)
            
        Returns:
            Taxa mensal em % (ex: 0.9489 = 0.9489% a.m.)
        """
        if taxa_anual <= 0:
            return 0.0
        
        # Converte % para decimal
        taxa_decimal = taxa_anual / 100.0
        
        # Fórmula: (1 + i_anual)^(1/12) - 1
        taxa_mensal_decimal = math.pow(1 + taxa_decimal, 1/12) - 1
        
        # Converte de volta para %
        return taxa_mensal_decimal * 100.0
    
    @staticmethod
    def converter_taxa_mensal_para_anual(taxa_mensal: float) -> float:
        """
        Converte taxa mensal para anual (juros compostos).
        
        Args:
            taxa_mensal: Taxa mensal em % (ex: 1.0 = 1% a.m.)
            
        Returns:
            Taxa anual em % (ex: 12.6825 = 12.6825% a.a.)
        """
        if taxa_mensal <= 0:
            return 0.0
        
        # Converte % para decimal
        taxa_decimal = taxa_mensal / 100.0
        
        # Fórmula: (1 + i_mensal)^12 - 1
        taxa_anual_decimal = math.pow(1 + taxa_decimal, 12) - 1
        
        # Converte de volta para %
        return taxa_anual_decimal * 100.0
    
    @staticmethod
    def calcular_tabela_price(
        valor_principal: float,
        taxa_juros_mensal: float,
        numero_parcelas: int,
        data_primeira_parcela: Optional[date] = None
    ) -> Dict:
        """
        Calcula amortização pela Tabela Price (parcelas fixas).
        
        Fórmula: PMT = PV * [i(1+i)^n] / [(1+i)^n - 1]
        
        Args:
            valor_principal: Valor principal (PV)
            taxa_juros_mensal: Taxa de juros mensal em % (ex: 2.5 = 2.5% a.m.)
            numero_parcelas: Número de parcelas
            data_primeira_parcela: Data da primeira parcela (opcional)
            
        Returns:
            Dicionário com:
            - valor_parcela: Valor de cada parcela
            - total_pago: Total pago ao final
            - total_juros: Total de juros pagos
            - parcelas: Lista de parcelas detalhadas
        """
        if valor_principal <= 0 or numero_parcelas <= 0:
            return {
                "valor_parcela": 0.0,
                "total_pago": 0.0,
                "total_juros": 0.0,
                "parcelas": []
            }
        
        # Converte taxa de % para decimal
        i = taxa_juros_mensal / 100.0
        n = numero_parcelas
        PV = valor_principal
        
        # Calcula valor da parcela (PMT)
        if i == 0:
            # Sem juros, parcela = principal / número de parcelas
            PMT = PV / n
        else:
            # Fórmula Price: PMT = PV * [i(1+i)^n] / [(1+i)^n - 1]
            numerador = i * math.pow(1 + i, n)
            denominador = math.pow(1 + i, n) - 1
            PMT = PV * (numerador / denominador)
        
        # Calcula parcelas detalhadas
        saldo_devedor = PV
        parcelas = []
        total_juros = 0.0
        
        data_atual = data_primeira_parcela or date.today()
        
        for num_parcela in range(1, numero_parcelas + 1):
            # Juros do período
            juros = saldo_devedor * i
            
            # Amortização
            if num_parcela == numero_parcelas:
                # Última parcela: amortiza o saldo restante
                amortizacao = saldo_devedor
                PMT_ajustado = amortizacao + juros
            else:
                amortizacao = PMT - juros
                PMT_ajustado = PMT
            
            # Atualiza saldo devedor
            saldo_devedor -= amortizacao
            if saldo_devedor < 0.01:  # Arredondamento
                saldo_devedor = 0.0
            
            total_juros += juros
            
            parcela_info = {
                "numero": num_parcela,
                "data_vencimento": data_atual.strftime("%Y-%m-%d") if data_atual else None,
                "valor_parcela": round(PMT_ajustado, 2),
                "juros": round(juros, 2),
                "amortizacao": round(amortizacao, 2),
                "saldo_devedor": round(saldo_devedor, 2)
            }
            parcelas.append(parcela_info)
            
            # Próximo mês
            data_atual = data_atual + relativedelta(months=1)
        
        total_pago = PMT * (n - 1) + parcelas[-1]["valor_parcela"]
        
        return {
            "valor_parcela": round(PMT, 2),
            "total_pago": round(total_pago, 2),
            "total_juros": round(total_juros, 2),
            "parcelas": parcelas
        }
    
    @staticmethod
    def calcular_sac(
        valor_principal: float,
        taxa_juros_mensal: float,
        numero_parcelas: int,
        data_primeira_parcela: Optional[date] = None
    ) -> Dict:
        """
        Calcula amortização pelo Sistema de Amortização Constante (SAC).
        
        Args:
            valor_principal: Valor principal (PV)
            taxa_juros_mensal: Taxa de juros mensal em % (ex: 2.5 = 2.5% a.m.)
            numero_parcelas: Número de parcelas
            data_primeira_parcela: Data da primeira parcela (opcional)
            
        Returns:
            Dicionário com:
            - valor_parcela_inicial: Valor da primeira parcela
            - valor_parcela_final: Valor da última parcela
            - total_pago: Total pago ao final
            - total_juros: Total de juros pagos
            - parcelas: Lista de parcelas detalhadas
        """
        if valor_principal <= 0 or numero_parcelas <= 0:
            return {
                "valor_parcela_inicial": 0.0,
                "valor_parcela_final": 0.0,
                "total_pago": 0.0,
                "total_juros": 0.0,
                "parcelas": []
            }
        
        # Converte taxa de % para decimal
        i = taxa_juros_mensal / 100.0
        n = numero_parcelas
        PV = valor_principal
        
        # Amortização constante
        amortizacao_constante = PV / n
        
        # Calcula parcelas detalhadas
        saldo_devedor = PV
        parcelas = []
        total_juros = 0.0
        
        data_atual = data_primeira_parcela or date.today()
        
        for num_parcela in range(1, numero_parcelas + 1):
            # Juros do período
            juros = saldo_devedor * i
            
            # Parcela = amortização + juros
            valor_parcela = amortizacao_constante + juros
            
            # Atualiza saldo devedor
            saldo_devedor -= amortizacao_constante
            if saldo_devedor < 0.01:  # Arredondamento
                saldo_devedor = 0.0
            
            total_juros += juros
            
            parcela_info = {
                "numero": num_parcela,
                "data_vencimento": data_atual.strftime("%Y-%m-%d") if data_atual else None,
                "valor_parcela": round(valor_parcela, 2),
                "juros": round(juros, 2),
                "amortizacao": round(amortizacao_constante, 2),
                "saldo_devedor": round(saldo_devedor, 2)
            }
            parcelas.append(parcela_info)
            
            # Próximo mês
            data_atual = data_atual + relativedelta(months=1)
        
        total_pago = sum(p["valor_parcela"] for p in parcelas)
        
        return {
            "valor_parcela_inicial": round(parcelas[0]["valor_parcela"], 2) if parcelas else 0.0,
            "valor_parcela_final": round(parcelas[-1]["valor_parcela"], 2) if parcelas else 0.0,
            "total_pago": round(total_pago, 2),
            "total_juros": round(total_juros, 2),
            "parcelas": parcelas
        }
    
    @staticmethod
    def detectar_metodologia_amortizacao(
        valor_principal: float,
        taxa_juros_mensal: float,
        numero_parcelas: int,
        valor_parcela_contrato: float,
        tolerancia: float = 0.01
    ) -> Optional[str]:
        """
        Detecta qual metodologia de amortização foi usada (Price ou SAC).
        
        Args:
            valor_principal: Valor principal
            taxa_juros_mensal: Taxa de juros mensal em %
            numero_parcelas: Número de parcelas
            valor_parcela_contrato: Valor da parcela informado no contrato
            tolerancia: Tolerância para comparação (em %)
            
        Returns:
            "price", "sac", ou None se não conseguir determinar
        """
        # Calcula Price
        resultado_price = FinancialCalculator.calcular_tabela_price(
            valor_principal, taxa_juros_mensal, numero_parcelas
        )
        valor_price = resultado_price["valor_parcela"]
        
        # Calcula SAC (primeira parcela)
        resultado_sac = FinancialCalculator.calcular_sac(
            valor_principal, taxa_juros_mensal, numero_parcelas
        )
        valor_sac_inicial = resultado_sac["valor_parcela_inicial"]
        
        # Compara com valor do contrato
        diff_price = abs(valor_price - valor_parcela_contrato) / valor_parcela_contrato
        diff_sac = abs(valor_sac_inicial - valor_parcela_contrato) / valor_parcela_contrato
        
        # Se Price está mais próximo (dentro da tolerância)
        if diff_price <= tolerancia and diff_price < diff_sac:
            return "price"
        
        # Se SAC está mais próximo (dentro da tolerância)
        if diff_sac <= tolerancia and diff_sac < diff_price:
            return "sac"
        
        # Se nenhum está próximo, pode ser outro sistema ou valores incorretos
        return None

