# Sistema de Armazenamento de Análises de Contratos

Este módulo implementa o armazenamento persistente de 100% das análises de contratos realizadas, permitindo mineração de dados e geração de relatórios como o "Mapa da Dívida".

## Objetivo

Armazenar todas as análises de contratos para:
- Minerar dados de inadimplência de forma efetiva
- Gerar relatórios mensais tipo "Mapa da Dívida"
- Identificar práticas abusivas por banco/instituição
- Apontar qual banco aplica mais juros
- Identificar quais bancos mais apreendem veículos
- Calcular médias de juros por produto bancário
- Potencial uso como sistema de análise de risco para instituições financeiras

## Estrutura do Banco de Dados

### Tabela: `analises_contratos`

Armazena todas as informações extraídas de cada análise de contrato, incluindo:

- **Dados do Cliente**: nome, CPF/CNPJ, idade, localização (estado, cidade)
- **Dados do Contrato**: número, tipo, banco credor, valores, taxas, parcelas
- **Informações do Veículo**: marca, modelo, ano, cor, placa, RENAVAM (se aplicável)
- **Análise**: observações, flags de irregularidades (taxa abusiva, CET alto, cláusulas abusivas)
- **Metadados**: data da análise, arquivo original

### Índices

O banco possui índices otimizados para:
- Busca por banco e tipo de contrato
- Busca por data e banco
- Busca por estado e banco
- Busca por veículos e banco

## Configuração

### SQLite (Padrão)

Por padrão, o sistema usa SQLite. O banco será criado automaticamente em:
```
flex-analise-backend/analises_contratos.db
```

### PostgreSQL (Opcional)

Para usar PostgreSQL, configure a variável de ambiente:
```bash
DATABASE_URL=postgresql://usuario:senha@localhost:5432/analises_contratos
```

E descomente no `requirements.txt`:
```
psycopg2-binary>=2.9.0
```

## Uso

### Inicialização Automática

O banco de dados é inicializado automaticamente quando a API é iniciada.

### Salvamento Automático

Toda análise realizada através do endpoint `/api/extract` é **automaticamente salva** no banco de dados.

### Endpoints de Relatórios

#### 1. Estatísticas por Banco
```
GET /api/relatorios/estatisticas-banco?estado=RS
```

Retorna:
- Total de contratos por banco
- Taxa média de juros por banco
- Valor médio e total de dívidas
- Total de veículos financiados
- Percentual de contratos com taxa abusiva

#### 2. Estatísticas por Produto
```
GET /api/relatorios/estatisticas-produto?estado=RS
```

Retorna estatísticas agregadas por tipo de produto (empréstimo, financiamento, etc.)

#### 3. Mapa da Dívida (Relatório Mensal)
```
GET /api/relatorios/mapa-divida?ano=2024&mes=12&estado=RS
```

Retorna relatório completo com:
- Resumo geral (total de análises, taxas médias, valores)
- Top 10 bancos por taxa de juros
- Top 10 bancos que mais apreendem veículos
- Distribuição por estado
- Distribuição por faixa etária

#### 4. Listar Análises
```
GET /api/relatorios/analises?limite=100&offset=0&banco=Santander&tipo_contrato=Financiamento&estado=RS
```

Lista análises com filtros opcionais.

#### 5. Obter Análise Específica
```
GET /api/relatorios/analise/{analise_id}
```

Obtém uma análise específica por ID.

## Exemplos de Uso

### Python

```python
from backend.database import get_session
from backend.database.repository import AnaliseRepository

# Obter estatísticas por banco
db = get_session()
repository = AnaliseRepository(db)

# Estatísticas gerais
stats = repository.estatisticas_por_banco(estado="RS")
print(stats)

# Mapa da dívida de dezembro/2024
mapa = repository.mapa_divida_mensal(ano=2024, mes=12, estado="RS")
print(mapa)

db.close()
```

### cURL

```bash
# Estatísticas por banco no RS
curl "http://localhost:8000/api/relatorios/estatisticas-banco?estado=RS"

# Mapa da dívida - Dezembro 2024
curl "http://localhost:8000/api/relatorios/mapa-divida?ano=2024&mes=12"

# Listar análises do Santander
curl "http://localhost:8000/api/relatorios/analises?banco=Santander&limite=50"
```

## Campos Adicionais para Mineração

O modelo inclui campos adicionais que podem ser preenchidos manualmente ou via integração:

- **estado**: Estado do cliente (ex: RS, SP)
- **cidade**: Cidade do cliente
- **idade_cliente**: Idade do cliente (pode ser calculada a partir de data de nascimento)

Estes campos podem ser extraídos de:
- CPF (primeiros dígitos indicam região)
- Integração com sistemas externos
- Formulários de cadastro

## Flags de Irregularidades

O sistema automaticamente detecta e marca:
- `tem_taxa_abusiva`: Taxa de juros acima de 5% a.m.
- `tem_cet_alto`: CET muito elevado
- `tem_clausulas_abusivas`: Cláusulas que violam CDC

Estas flags são extraídas automaticamente das observações da análise.

## Próximos Passos

1. **Integração com CPF**: Extrair estado/cidade a partir do CPF
2. **Dashboard**: Interface web para visualizar relatórios
3. **Exportação**: Exportar relatórios em PDF/Excel
4. **Alertas**: Notificações quando detectar padrões de irregularidades
5. **API de Análise de Risco**: Endpoint para instituições financeiras consultarem dados agregados

