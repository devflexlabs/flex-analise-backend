"""
Integração com API do BACEN para buscar séries temporais.
API: https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados
"""
import requests
from datetime import datetime, date
from typing import Optional, Dict, List
from dateutil.relativedelta import relativedelta


class BacenIntegration:
    """Integração com API do Banco Central do Brasil."""
    
    # Códigos das séries temporais do BACEN
    SERIES_CODES = {
        "selic_diaria": 11,      # Taxa Selic (ao dia) - %
        "selic_mensal": 432,     # Taxa Selic (ao mês) - %
        "cdi_diario": 12,        # CDI (ao dia) - %
        "ipca_mensal": 433,      # IPCA (ao mês) - %
        "ipca_acumulado_12m": 13522,  # IPCA acumulado 12 meses - %
    }
    
    BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
    
    def __init__(self):
        """Inicializa a integração com BACEN."""
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "FlexAnalise/1.0"
        })
    
    def _format_date(self, date_obj: date) -> str:
        """Formata data para formato do BACEN (dd/MM/yyyy)."""
        if isinstance(date_obj, str):
            # Tenta parsear se for string
            try:
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
            except:
                try:
                    date_obj = datetime.strptime(date_obj, "%d/%m/%Y").date()
                except:
                    return None
        return date_obj.strftime("%d/%m/%Y")
    
    def buscar_taxa_selic(self, data: date, diaria: bool = False) -> Optional[float]:
        """
        Busca taxa Selic para uma data específica.
        
        Args:
            data: Data para buscar a taxa
            diaria: Se True, usa série diária (código 11), senão mensal (código 432)
            
        Returns:
            Taxa Selic em % ao ano, ou None se não encontrado
        """
        codigo = self.SERIES_CODES["selic_diaria"] if diaria else self.SERIES_CODES["selic_mensal"]
        return self._buscar_taxa_por_codigo(codigo, data, diaria)
    
    def buscar_cdi(self, data: date) -> Optional[float]:
        """
        Busca CDI para uma data específica.
        
        Args:
            data: Data para buscar o CDI
            
        Returns:
            CDI em % ao ano, ou None se não encontrado
        """
        return self._buscar_taxa_por_codigo(self.SERIES_CODES["cdi_diario"], data, diaria=True)
    
    def buscar_ipca(self, data: date, acumulado_12m: bool = False) -> Optional[float]:
        """
        Busca IPCA para uma data específica.
        
        Args:
            data: Data para buscar o IPCA
            acumulado_12m: Se True, retorna IPCA acumulado 12 meses
            
        Returns:
            IPCA em %, ou None se não encontrado
        """
        codigo = self.SERIES_CODES["ipca_acumulado_12m"] if acumulado_12m else self.SERIES_CODES["ipca_mensal"]
        return self._buscar_taxa_por_codigo(codigo, data, diaria=False)
    
    def _buscar_taxa_por_codigo(self, codigo: int, data: date, diaria: bool = False) -> Optional[float]:
        """
        Busca taxa por código da série do BACEN.
        
        Args:
            codigo: Código da série do BACEN
            data: Data para buscar
            diaria: Se True, busca valor exato da data, senão busca do mês
            
        Returns:
            Valor da taxa em %, ou None se não encontrado
        """
        try:
            # Para séries mensais, busca o mês inteiro e pega o último valor
            if not diaria:
                # Primeiro dia do mês
                data_inicio = date(data.year, data.month, 1)
                # Último dia do mês
                if data.month == 12:
                    data_fim = date(data.year, 12, 31)
                else:
                    data_fim = date(data.year, data.month + 1, 1) - relativedelta(days=1)
            else:
                # Para séries diárias, busca alguns dias antes e depois para garantir
                data_inicio = data - relativedelta(days=5)
                data_fim = data + relativedelta(days=5)
            
            url = f"{self.BASE_URL}/{codigo}/dados"
            params = {
                "dataInicial": self._format_date(data_inicio),
                "dataFinal": self._format_date(data_fim),
                "formato": "json"
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            dados = response.json()
            
            if not dados:
                return None
            
            # Para séries diárias, procura o valor exato da data
            if diaria:
                data_str = self._format_date(data)
                for item in dados:
                    if item.get("data") == data_str:
                        valor = item.get("valor")
                        return float(valor) if valor is not None else None
                # Se não encontrou exato, pega o mais próximo antes da data
                for item in reversed(dados):
                    item_data = datetime.strptime(item.get("data"), "%d/%m/%Y").date()
                    if item_data <= data:
                        valor = item.get("valor")
                        return float(valor) if valor is not None else None
            else:
                # Para séries mensais, pega o último valor do período
                # Formato: "01/2024" ou "02/2024"
                data_str = f"{data.month:02d}/{data.year}"
                for item in reversed(dados):
                    if item.get("data").endswith(data_str):
                        valor = item.get("valor")
                        return float(valor) if valor is not None else None
            
            # Se não encontrou, retorna o último valor disponível
            if dados:
                ultimo = dados[-1]
                valor = ultimo.get("valor")
                return float(valor) if valor is not None else None
            
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Erro ao buscar taxa do BACEN: {e}")
            return None
        except Exception as e:
            print(f"⚠️ Erro ao processar dados do BACEN: {e}")
            return None
    
    def buscar_taxa_historica(self, codigo: int, data_inicio: date, data_fim: date) -> List[Dict]:
        """
        Busca série histórica de uma taxa.
        
        Args:
            codigo: Código da série do BACEN
            data_inicio: Data inicial
            data_fim: Data final
            
        Returns:
            Lista de dicionários com data e valor
        """
        try:
            url = f"{self.BASE_URL}/{codigo}/dados"
            params = {
                "dataInicial": self._format_date(data_inicio),
                "dataFinal": self._format_date(data_fim),
                "formato": "json"
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"⚠️ Erro ao buscar série histórica do BACEN: {e}")
            return []

