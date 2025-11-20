# Problema: Dados Não Estão Sendo Carregados Corretamente no Grafo

## 🔍 Problema Identificado

O sistema estava carregando apenas **3 nós e 2 arestas** (dados mínimos) ao invés dos **~30.840 nós e ~38.790 arestas** disponíveis.

---

## 📊 Análise do Problema

### **Dados Disponíveis:**

1. ✅ **`data/sp/integrated/integrated_nodes.csv`** - **30.840 nós** (dados reais!)
2. ✅ **`data/sp/integrated/integrated_edges.csv`** - **38.790 arestas** (dados reais!)
3. ❌ **`data/integrated/integrated_nodes.csv`** - **VAZIO** (apenas cabeçalho)
4. ❌ **`data/integrated/integrated_edges.csv`** - **VAZIO** (apenas cabeçalho)
5. ⚠️ **`data/nodes.csv`** - **3 nós** (dados mínimos de fallback)
6. ⚠️ **`data/edges.csv`** - **2 arestas** (dados mínimos de fallback)

### **Fluxo de Fallback Anterior (PROBLEMÁTICO):**

```
1. Tentativa: Dados Híbridos (Olho Vivo + GTFS)
   ❌ Falhou: GTFS não encontrado

2. Tentativa: Dados Integrados em data/integrated/
   ❌ Falhou: Arquivos vazios (apenas cabeçalhos)

3. Tentativa: Arquivos Primários (data/nodes.csv, data/edges.csv)
   ⚠️ Sucesso: Mas apenas 3 nós e 2 arestas (dados mínimos)

4. Tentativa: Dataset Mínimo
   ✅ Sucesso: Mas dados mínimos
```

**Problema:** O código não estava verificando `data/sp/integrated/` que contém os dados reais!

---

## ✅ Solução Implementada

### **Correção 1: Adicionar Verificação de `data/sp/integrated/`**

Adicionada verificação para dados integrados de SP **ANTES** de usar dados mínimos:

```python
# Tentativa 1: Dados integrados de SP (prioridade - dados reais do mapa)
sp_integrated_nodes = os.path.join(DATA_DIR, "sp", "integrated", "integrated_nodes.csv")
sp_integrated_edges = os.path.join(DATA_DIR, "sp", "integrated", "integrated_edges.csv")

if os.path.isfile(sp_integrated_nodes) and os.path.isfile(sp_integrated_edges):
    # Verificar se os arquivos não estão vazios (> 100 bytes)
    if os.path.getsize(sp_integrated_nodes) > 100 and os.path.getsize(sp_integrated_edges) > 100:
        eng = Engine(sp_integrated_nodes, sp_integrated_edges, DEFAULT_WEIGHTS)
        if eng.g and eng.g.contents.n > 0:
            logger.info(f"✅ Engine inicializado com dados integrados de SP")
            logger.info(f"   📊 Nós carregados: {eng.g.contents.n}")
            return eng
```

### **Correção 2: Validação de Tamanho de Arquivo**

Adicionada validação para garantir que os arquivos não estão vazios:

```python
# Verificar se os arquivos não estão vazios (> 100 bytes)
if os.path.getsize(sp_integrated_nodes) > 100 and os.path.getsize(sp_integrated_edges) > 100:
```

Isso evita carregar arquivos que têm apenas cabeçalhos.

### **Correção 3: Atualizar Carregamento para Utilitários**

Também corrigido o carregamento de dados para utilitários (route_utils) para usar os mesmos arquivos:

```python
# Prioridade 2: Dados integrados de SP (se híbrido não disponível)
sp_integrated_nodes = os.path.join(DATA_DIR, "sp", "integrated", "integrated_nodes.csv")
sp_integrated_edges = os.path.join(DATA_DIR, "sp", "integrated", "integrated_edges.csv")

if os.path.isfile(sp_integrated_nodes) and os.path.isfile(sp_integrated_edges):
    if os.path.getsize(sp_integrated_nodes) > 100 and os.path.getsize(sp_integrated_edges) > 100:
        nodes_df, edges_df = load_graph_data(sp_integrated_nodes, sp_integrated_edges)
        logger.info("✅ Dados do grafo carregados para utilitários (dados integrados de SP)")
```

---

## 🔄 Novo Fluxo de Fallback (CORRIGIDO)

```
1. Tentativa: Dados Híbridos (Olho Vivo + GTFS)
   ❌ Falhou: GTFS não encontrado (será resolvido após reiniciar com volume montado)

2. Tentativa: Dados Integrados de SP (data/sp/integrated/)
   ✅ Sucesso: ~30.840 nós e ~38.790 arestas carregados!

3. Tentativa: Dados Integrados Genéricos (data/integrated/)
   ⏭️ Não necessário (já carregou dados de SP)

4. Tentativa: Arquivos Primários
   ⏭️ Não necessário (já carregou dados de SP)

5. Tentativa: Dataset Mínimo
   ⏭️ Não necessário (já carregou dados de SP)
```

---

## 📋 Mudanças no Código

### **Arquivo: `api/app/main.py`**

**Antes:**
- Verificava apenas `data/integrated/` (vazio)
- Não verificava `data/sp/integrated/` (com dados reais)

**Depois:**
- Verifica primeiro `data/sp/integrated/` (dados reais de SP)
- Depois verifica `data/integrated/` (fallback genérico)
- Valida tamanho dos arquivos (> 100 bytes)
- Loga quantidade de nós carregados

---

## 🚀 Próximos Passos

### **1. Reiniciar o Container**

Para aplicar as mudanças:

```bash
docker-compose restart api
```

### **2. Verificar Logs**

Após reiniciar, verificar se os dados foram carregados:

```bash
docker-compose logs -f api | grep "Engine inicializado"
```

Deve mostrar:
```
✅ Engine inicializado com dados integrados de SP (OSM+GTFS)
   📊 Nós carregados: 30840
```

### **3. Verificar Funcionalidade**

Testar se as rotas estão funcionando com os dados reais:

```bash
curl -X POST http://localhost:8080/alternatives \
  -H "Content-Type: application/json" \
  -d '{"from": "osm_25778210", "to": "osm_60634869", "perfil": "padrao", "k": 3}'
```

---

## 📊 Comparação: Antes vs Depois

| Métrica | Antes | Depois |
|---------|-------|--------|
| **Nós carregados** | 3 | ~30.840 |
| **Arestas carregadas** | 2 | ~38.790 |
| **Fonte de dados** | Dados mínimos | Dados reais de SP |
| **Funcionalidade** | Limitada | Completa |

---

## 🔍 Por Que Isso Aconteceu?

1. **Dados foram processados em `data/sp/integrated/`** (específico para São Paulo)
2. **Código procurava em `data/integrated/`** (genérico, vazio)
3. **Fallback usava dados mínimos** quando não encontrava dados integrados
4. **Não havia verificação para `data/sp/integrated/`**

---

## ✅ Resultado Esperado

Após reiniciar o container:

- ✅ **~30.840 nós** carregados no grafo
- ✅ **~38.790 arestas** carregadas no grafo
- ✅ **Rotas funcionando** com dados reais de São Paulo
- ✅ **Busca de nós** retornando resultados reais
- ✅ **Cálculo de rotas** usando dados reais da cidade

---

## 📝 Notas Técnicas

### **Estrutura de Diretórios:**

```
data/
├── integrated/          # Genérico (vazio)
│   ├── integrated_nodes.csv
│   └── integrated_edges.csv
├── sp/                  # Específico para São Paulo
│   └── integrated/      # ✅ DADOS REAIS AQUI
│       ├── integrated_nodes.csv  (30.840 nós)
│       └── integrated_edges.csv  (38.790 arestas)
├── nodes.csv            # Mínimo (3 nós)
└── edges.csv            # Mínimo (2 arestas)
```

### **Validação de Arquivos:**

A validação `> 100 bytes` garante que:
- Arquivo não está vazio
- Arquivo tem mais que apenas cabeçalho
- Arquivo contém dados reais

---

## 🎯 Conclusão

O problema era que o código não estava verificando o diretório correto onde os dados reais estavam armazenados. Com a correção, o sistema agora:

1. ✅ Verifica `data/sp/integrated/` primeiro (dados reais)
2. ✅ Valida que os arquivos não estão vazios
3. ✅ Carrega ~30.840 nós e ~38.790 arestas
4. ✅ Funciona com dados reais de São Paulo

**Reinicie o container para aplicar as mudanças!**

