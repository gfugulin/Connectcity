# 🔄 Estratégia Híbrida de Dados: API Olho Vivo + GTFS Local

## 📋 Visão Geral

O sistema agora usa uma **estratégia híbrida** que combina:
- **API Olho Vivo** (prioridade): Dados em tempo real
- **GTFS Local** (fallback): Dados estáticos estruturais

---

## 🎯 Por que Híbrido?

### API Olho Vivo (Tempo Real) - PRIORIDADE
**Uso:**
- ✅ Posição dos veículos em tempo real
- ✅ Previsão de chegada nas paradas
- ✅ Busca de paradas e linhas dinâmica
- ✅ Informações atualizadas constantemente

**Limitações:**
- ❌ **Não fornece estrutura do grafo** (não tem arestas/conexões)
- ❌ Requer conexão com internet
- ❌ Pode ter rate limiting

### GTFS Local (Estrutura Estática) - FALLBACK ESSENCIAL
**Uso:**
- ✅ **Estrutura completa do grafo** (nós e arestas)
- ✅ Conexões entre paradas
- ✅ Rotas completas
- ✅ Funciona offline

**Limitações:**
- ❌ Dados estáticos (não atualizados em tempo real)
- ❌ Pode estar desatualizado

### Solução Híbrida
**Combina o melhor dos dois:**
- 🚀 **API Olho Vivo**: Dados em tempo real (posição, previsões)
- 📁 **GTFS Local**: Estrutura completa do grafo (obrigatório para rotas)
- 🔄 **Fallback automático**: Se API falhar, usa GTFS completo

---

## 🔄 Fluxo de Priorização

```
1. Verificar API Olho Vivo
   ↓ (se disponível)
   ✅ Autenticar e marcar como disponível
   ↓
2. Carregar GTFS Local (OBRIGATÓRIO)
   ↓ (se disponível)
   ✅ Processar arquivos GTFS
   ✅ Gerar estrutura completa do grafo (nós + arestas)
   ↓
3. Estratégia Híbrida
   ↓
   Estrutura do Grafo: GTFS Local (sempre)
   Dados em Tempo Real: API Olho Vivo (quando disponível)
   ↓
4. Fallback
   ↓ (se GTFS falhar)
   Usar dados integrados (OSM+GTFS)
   ↓ (se falhar)
   Usar dados primários (nodes.csv, edges.csv)
   ↓ (se tudo falhar)
   Usar dataset mínimo
```

**Nota Importante:** 
- GTFS Local é **obrigatório** para estrutura do grafo
- API Olho Vivo é **opcional** mas recomendado para dados em tempo real
- Sem GTFS, as rotas não funcionarão (não há estrutura do grafo)

---

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# Token da API Olho Vivo (obrigatório)
OLHO_VIVO_TOKEN=1abf7ba19b22829e9d95648f8affe9afaf8c64b9cbb8c8042e6b50cb5d63be81

# Diretório GTFS local (opcional, mas recomendado)
GTFS_LOCAL_DIR=GTFS
```

### No Código

```python
from integration.hybrid_data_processor import HybridDataProcessor

# Inicializar processador híbrido
processor = HybridDataProcessor(
    olho_vivo_token="seu_token_aqui",
    gtfs_dir="GTFS"  # Opcional
)

# Verificar disponibilidade
status = processor.initialize()
# {
#   'olho_vivo': True,
#   'gtfs_local': True
# }

# Carregar dados
nodes, edges = processor.load_data()

# Exportar
processor.export_to_csv("data/hybrid")
```

---

## 📊 Estratégias de Carregamento

### Estratégia 1: Híbrida (Ideal) ⭐
**Quando:** API Olho Vivo ✅ + GTFS Local ✅

**Comportamento:**
- **Estrutura do Grafo:** GTFS Local (nós + arestas)
- **Dados em Tempo Real:** API Olho Vivo (posição de veículos, previsões)
- **Busca de Paradas:** API Olho Vivo (quando necessário)

**Vantagens:**
- ✅ Estrutura completa do grafo (rotas funcionam)
- ✅ Dados em tempo real (posição de ônibus, previsões)
- ✅ Melhor experiência do usuário

### Estratégia 2: Apenas API Olho Vivo ⚠️
**Quando:** API Olho Vivo ✅ + GTFS Local ❌

**Comportamento:**
- **Estrutura do Grafo:** ❌ Não disponível (API não fornece)
- **Dados em Tempo Real:** ✅ API Olho Vivo
- ⚠️ **CRÍTICO**: Sem estrutura do grafo, **rotas não funcionam**

**Recomendação:** ⚠️ **GTFS Local é obrigatório**. Sem ele, o sistema não pode calcular rotas.

### Estratégia 3: Apenas GTFS Local ✅
**Quando:** API Olho Vivo ❌ + GTFS Local ✅

**Comportamento:**
- **Estrutura do Grafo:** ✅ GTFS Local (nós + arestas)
- **Dados em Tempo Real:** ❌ Não disponível
- ✅ **Funcional**: Rotas funcionam normalmente

**Vantagens:**
- ✅ Funciona offline
- ✅ Estrutura completa do grafo
- ✅ Rotas funcionam normalmente
- ⚠️ Sem dados em tempo real (posição de ônibus, previsões)

### Estratégia 4: Fallback Completo
**Quando:** API Olho Vivo ❌ + GTFS Local ❌

**Comportamento:**
- Usa dados integrados (OSM+GTFS) se disponíveis
- Usa dados primários (nodes.csv, edges.csv)
- Usa dataset mínimo como último recurso

---

## 🔍 Verificação de Status

### Via API

```bash
GET /real-data/hybrid/status
```

**Resposta:**
```json
{
  "olho_vivo": {
    "available": true,
    "description": "API Olho Vivo - Dados em tempo real",
    "use_case": "Posição de veículos, previsão de chegada, busca de paradas"
  },
  "gtfs_local": {
    "available": true,
    "description": "GTFS Local - Dados estáticos estruturais",
    "use_case": "Estrutura do grafo, conexões entre paradas, rotas completas",
    "directory": "GTFS"
  },
  "strategy": "hybrid"
}
```

### Via Logs

```
📊 Status das fontes de dados: {'olho_vivo': True, 'gtfs_local': True}
✅ Engine inicializado com dados híbridos (estratégia: hybrid)
   - API Olho Vivo: ✅
   - GTFS Local: ✅
```

---

## 🚀 Inicialização Automática

O sistema tenta automaticamente na inicialização:

1. **Primeiro:** Dados híbridos (API Olho Vivo + GTFS)
2. **Segundo:** Dados integrados (OSM+GTFS)
3. **Terceiro:** Dados primários (nodes.csv, edges.csv)
4. **Último:** Dataset mínimo

---

## 📝 Exemplo de Uso

### 1. Configurar Variáveis

```bash
export OLHO_VIVO_TOKEN="1abf7ba19b22829e9d95648f8affe9afaf8c64b9cbb8c8042e6b50cb5d63be81"
export GTFS_LOCAL_DIR="GTFS"
```

### 2. Iniciar API

```bash
docker-compose up -d
```

### 3. Verificar Logs

```
📊 Status das fontes de dados: {'olho_vivo': True, 'gtfs_local': True}
✅ API Olho Vivo disponível
✅ GTFS local disponível
📡 Carregando dados da API Olho Vivo...
📁 Carregando dados GTFS local como fallback...
🔄 Combinando dados da API Olho Vivo com GTFS local...
✅ Dados combinados: 15000 nós, 50000 arestas
✅ Engine inicializado com dados híbridos (estratégia: hybrid)
```

---

## ⚠️ Troubleshooting

### Problema: "API Olho Vivo não disponível"

**Causas:**
- Token inválido ou expirado
- Sem conexão com internet
- API temporariamente indisponível

**Solução:**
- Verificar token
- Verificar conexão
- Sistema usa GTFS local automaticamente como fallback

### Problema: "GTFS local não disponível"

**Causas:**
- Diretório não existe
- Arquivos essenciais faltando
- Caminho incorreto

**Solução:**
- Verificar se pasta GTFS existe
- Verificar se tem stops.txt, routes.txt, trips.txt, stop_times.txt
- Configurar GTFS_LOCAL_DIR corretamente

### Problema: "Nenhuma fonte de dados disponível"

**Causa:** Ambas as fontes falharam

**Solução:**
- Sistema usa fallback para dados integrados ou primários
- Verificar logs para detalhes

---

## ✅ Vantagens da Estratégia Híbrida

1. **Resiliência:** Sistema funciona mesmo se uma fonte falhar
2. **Atualização:** Dados em tempo real quando disponíveis
3. **Completude:** Estrutura completa do grafo sempre disponível
4. **Performance:** Cache local reduz dependência de API
5. **Flexibilidade:** Adapta-se automaticamente às fontes disponíveis

---

## 📚 Referências

- [API Olho Vivo](docs/API_OLHO_VIVO.md)
- [Processar GTFS Local](docs/PROCESSAR_GTFS_LOCAL.md)
- [Fluxo Completo de Dados](docs/FLUXO_COMPLETO_DADOS.md)

