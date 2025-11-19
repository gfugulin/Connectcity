# 📊 Dados Mockados para Busca de Rotas

## 🎯 Objetivo

Criar dados mockados para permitir testar e apresentar o sistema de busca de rotas sem depender da API backend.

---

## ✅ Implementação

### 1. Modo Mock Ativado

**Arquivo:** `front_connecity/src/services/api.js`

```javascript
const USE_MOCK_DATA = true; // Mude para false para usar API real
```

**Como usar:**
- `true` - Usa dados mockados (ideal para apresentação)
- `false` - Usa API real (quando backend estiver disponível)

---

## 📍 Dados Mockados de Nós (Autocomplete)

### Locais Disponíveis

1. **R. Lavinia Fenton, 53** (`node1`)
2. **Av. Paulista, 1000** (`node2`)
3. **Universidade Presbiteriana Mackenzie** (`node3`)
4. **Estação Sé** (`node4`)
5. **Terminal Bandeira** (`node5`)
6. **Metrô Tatuapé** (`node6`)
7. **Parque Ibirapuera** (`node7`)
8. **Shopping Center Norte** (`node8`)
9. **Aeroporto de Congonhas** (`node9`)
10. **Terminal Lapa** (`node10`)

**Funcionalidade:**
- Autocomplete funciona ao digitar qualquer parte do nome ou ID
- Retorna até 5 resultados
- Inclui coordenadas (lat/lon) para exibição no mapa

---

## 🗺️ Dados Mockados de Rotas

### Rota 1 - Recomendada ⭐

- **Tempo:** 45 min
- **Transferências:** 1
- **Pontuação:** 85
- **Modos:** Trem → Metrô → Caminhada
- **Barreiras Evitadas:** Escadas, Calçadas Ruins
- **Ilustração:** 🚆 (Trem)

### Rota 2 - Com Atraso ⚠️

- **Tempo:** 50 min
- **Transferências:** 2
- **Pontuação:** 70
- **Modos:** Trem → Metrô → Caminhada
- **Barreiras Evitadas:** Escadas
- **Atraso:** Linha 4 - Amarela (até 15 minutos)
- **Ilustração:** 🚌 (Ônibus)

### Rota 3

- **Tempo:** 55 min
- **Transferências:** 1
- **Pontuação:** 60
- **Modos:** Ônibus → Caminhada
- **Barreiras Evitadas:** Nenhuma
- **Ilustração:** 🚶 (Caminhada)

---

## 📋 Detalhes da Rota Mockados

### Passo a Passo (Steps)

1. **Caminhada Inicial**
   - De: R. Lavinia Fenton, 53
   - Para: Estação Sé
   - Tempo: 5 min
   - Distância: 0.5 km

2. **Metrô**
   - De: Estação Sé
   - Para: Estação Trianon-Masp
   - Linha: 3 (Vermelha)
   - Tempo: 15 min
   - Distância: 3.2 km

3. **Caminhada Final**
   - De: Estação Trianon-Masp
   - Para: Av. Paulista, 1000
   - Tempo: 3 min
   - Distância: 0.3 km

**Total:**
- Tempo: 45 min
- Distância: 4.0 km
- Transferências: 1
- Barreiras Evitadas: Escadas, Calçadas Ruins

---

## 🧪 Como Testar

### 1. Buscar Rotas

1. Acesse a página inicial (`/`)
2. Digite no campo "Sua localização":
   - `R. Lavinia Fenton` ou `node1`
3. Digite no campo "Destino":
   - `Av. Paulista` ou `node2`
   - Ou `Universidade Presbiteriana Mackenzie` ou `node3`
4. Selecione um perfil de mobilidade
5. Clique em "Buscar Rota"

### 2. Resultados Esperados

- ✅ 3 rotas serão exibidas
- ✅ Primeira rota marcada como "Recomendada"
- ✅ Segunda rota com aviso de atraso
- ✅ Cada rota mostra tempo, transferências, pontuação e ícones de transporte

### 3. Ver Detalhes

- Clique em qualquer rota para ver detalhes passo a passo
- Detalhes incluem instruções, tempos e distâncias

---

## 🔄 Alternar Entre Mock e API Real

### Usar Dados Mockados (Apresentação)

```javascript
const USE_MOCK_DATA = true;
```

### Usar API Real (Produção)

```javascript
const USE_MOCK_DATA = false;
```

**Nota:** Quando `USE_MOCK_DATA = false`, o sistema tentará usar a API real. Se a API não estiver disponível, os erros serão tratados normalmente.

---

## 📝 Exemplos de Buscas

### Exemplo 1: Casa → Trabalho
- **Origem:** `R. Lavinia Fenton, 53` ou `node1`
- **Destino:** `Av. Paulista, 1000` ou `node2`
- **Resultado:** 3 rotas (45min, 50min, 55min)

### Exemplo 2: Casa → Faculdade
- **Origem:** `R. Lavinia Fenton, 53` ou `node1`
- **Destino:** `Universidade Presbiteriana Mackenzie` ou `node3`
- **Resultado:** 3 rotas com diferentes opções

### Exemplo 3: Estação → Parque
- **Origem:** `Estação Sé` ou `node4`
- **Destino:** `Parque Ibirapuera` ou `node7`
- **Resultado:** 3 rotas alternativas

---

## 🎨 Visual das Rotas

### Cards de Rota

- **Fundo:** Cinza claro (`bg-gray-50`)
- **Tempo:** Texto grande e em negrito
- **Ícones de Transporte:** Trem, Metrô, Caminhada
- **Badge "Recomendada":** Azul, apenas na primeira rota
- **Pontuação:** Canto superior direito
- **Aviso de Atraso:** Card laranja com ícone de alerta (quando aplicável)
- **Ilustração:** Emoji grande representando o modo principal

---

## ✅ Checklist de Funcionalidades Mockadas

- [x] Autocomplete de nós (origem e destino)
- [x] Busca de rotas alternativas (3 rotas)
- [x] Detalhes passo a passo das rotas
- [x] Pontuação das rotas
- [x] Avisos de atraso
- [x] Modos de transporte
- [x] Transferências
- [x] Tempo total
- [x] Barreiras evitadas
- [x] Ilustrações por tipo de rota

---

## 🚀 Próximos Passos

1. **Testar busca de rotas** com diferentes combinações
2. **Verificar detalhes** de cada rota
3. **Validar visual** conforme design de referência
4. **Desativar mock** quando API real estiver pronta

---

## 📚 Referências

- Design de referência: `tela_3/resultados_da_rota_-_visão_geral/screen.png`
- Código: `front_connecity/src/services/api.js`


