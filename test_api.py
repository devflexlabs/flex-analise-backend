#!/usr/bin/env python3
"""
Script de teste para verificar se os endpoints de relatórios estão funcionando.
"""
import urllib.request
import urllib.error
import json
import sys

# URL da API - pode ser configurada via variável de ambiente ou argumento
import os
API_URL = os.getenv("PYTHON_API_URL", "http://localhost:8000")

# Se passou URL como argumento, usa ela
if len(sys.argv) > 1:
    API_URL = sys.argv[1]

def test_estatisticas_banco():
    """Testa o endpoint de estatísticas por banco."""
    print("=" * 60)
    print("🧪 Testando: GET /api/relatorios/estatisticas-banco")
    print("=" * 60)
    
    url = f"{API_URL}/api/relatorios/estatisticas-banco"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            print(f"Status Code: {status_code}")
            
            if status_code == 200:
                data = json.loads(response.read().decode('utf-8'))
                print(f"✅ Sucesso! Retornou {len(data)} bancos")
                if data:
                    print("\n📊 Dados recebidos:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    print("ℹ️  Lista vazia (nenhum dado no banco ainda)")
                return True
            else:
                print(f"❌ Erro {status_code}")
                return False
                
    except urllib.error.URLError as e:
        if "Connection refused" in str(e) or "Name or service not known" in str(e):
            print(f"❌ Erro: Não foi possível conectar à API em {API_URL}")
            print("   Certifique-se de que a API está rodando!")
        else:
            print(f"❌ Erro de conexão: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_mapa_divida():
    """Testa o endpoint de mapa da dívida."""
    print("\n" + "=" * 60)
    print("🧪 Testando: GET /api/relatorios/mapa-divida")
    print("=" * 60)
    
    from datetime import datetime
    now = datetime.now()
    url = f"{API_URL}/api/relatorios/mapa-divida?ano={now.year}&mes={now.month}"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            print(f"Status Code: {status_code}")
            
            if status_code == 200:
                data = json.loads(response.read().decode('utf-8'))
                print(f"✅ Sucesso!")
                print(f"Total de análises: {data.get('resumo', {}).get('total_analises', 0)}")
                print("\n📊 Resumo:")
                print(json.dumps(data.get('resumo', {}), indent=2, ensure_ascii=False))
                return True
            else:
                print(f"❌ Erro {status_code}")
                return False
                
    except urllib.error.URLError as e:
        if "Connection refused" in str(e) or "Name or service not known" in str(e):
            print(f"❌ Erro: Não foi possível conectar à API em {API_URL}")
        else:
            print(f"❌ Erro de conexão: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def test_health():
    """Testa o endpoint de health check."""
    print("\n" + "=" * 60)
    print("🧪 Testando: GET /health")
    print("=" * 60)
    
    url = f"{API_URL}/health"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            status_code = response.getcode()
            print(f"Status Code: {status_code}")
            
            if status_code == 200:
                data = json.loads(response.read().decode('utf-8'))
                print(f"✅ API está funcionando!")
                print(f"Resposta: {json.dumps(data, indent=2)}")
                return True
            else:
                print(f"❌ Erro {status_code}")
                return False
                
    except urllib.error.URLError as e:
        if "Connection refused" in str(e) or "Name or service not known" in str(e):
            print(f"❌ Erro: Não foi possível conectar à API em {API_URL}")
            print("   Certifique-se de que a API está rodando!")
        else:
            print(f"❌ Erro de conexão: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    print("\n🚀 Iniciando testes da API de Relatórios")
    print(f"📍 URL da API: {API_URL}\n")
    
    # Testa health primeiro
    health_ok = test_health()
    
    if not health_ok:
        print("\n⚠️  API não está respondendo. Verifique se está rodando.")
        sys.exit(1)
    
    # Testa endpoints de relatórios
    stats_ok = test_estatisticas_banco()
    mapa_ok = test_mapa_divida()
    
    print("\n" + "=" * 60)
    print("📋 Resumo dos Testes")
    print("=" * 60)
    print(f"Health Check: {'✅ OK' if health_ok else '❌ FALHOU'}")
    print(f"Estatísticas por Banco: {'✅ OK' if stats_ok else '❌ FALHOU'}")
    print(f"Mapa da Dívida: {'✅ OK' if mapa_ok else '❌ FALHOU'}")
    print("=" * 60)
    
    if health_ok and stats_ok and mapa_ok:
        print("\n✅ Todos os testes passaram!")
        sys.exit(0)
    else:
        print("\n⚠️  Alguns testes falharam. Verifique os logs acima.")
        sys.exit(1)

