# 🚌 Integração API Olho Vivo - Implementação Completa

## 📋 Resumo

Integração completa da API Olho Vivo da SPTrans no sistema CONNECITY, permitindo visualização de ônibus em tempo real no mapa e previsão de chegada nas paradas.

---

## ✅ O que foi implementado

### 1. Backend (API)

#### Arquivo: `api/app/olho_vivo_api.py`

**Endpoints criados:**
- `GET /olho-vivo/linhas/buscar?termos={termos}` - Busca linhas de ônibus
- `GET /olho-vivo/paradas/buscar?termos={termos}` - Busca paradas
- `GET /olho-vivo/paradas/por-linha/{codigo_linha}` - Paradas por linha
- `GET /olho-vivo/posicao?codigo_linha={codigo}` - Posição dos veículos (tempo real)
- `GET /olho-vivo/previsao?codigo_parada={parada}&codigo_linha={linha}` - Previsão de chegada
- `GET /olho-vivo/previsao/parada/{codigo_parada}` - Previsão para todas as linhas de uma parada
- `GET /olho-vivo/corredores` - Lista de corredores
- `GET /olho-vivo/empresas` - Lista de empresas

**Autenticação:**
- Token configurado: `1abf7ba19b22829e9d95648f8affe9afaf8c64b9cbb8c8042e6b50cb5d63be81`
- Autenticação automática na inicialização
- Cliente singleton para reutilização de sessão

---

### 2. Frontend

#### 2.1 Serviço de API (`front_connecity/src/services/api.js`)

**Métodos adicionados:**
```javascript
- buscarLinhasOlhoVivo(termos)
- buscarParadasOlhoVivo(termos)
- obterPosicaoVeiculos(codigoLinha)
- obterPrevisaoChegada(codigoParada, codigoLinha)
- obterPrevisaoPorParada(codigoParada)
- buscarParadasPorLinha(codigoLinha)
```

#### 2.2 Componente Map (`front_connecity/src/components/Map.jsx`)

**Funcionalidades:**
- ✅ Exibição de ônibus em tempo real no mapa
- ✅ Marcadores verdes com ícone de ônibus
- ✅ Popup com informações do veículo (prefixo, acessibilidade)
- ✅ Atualização automática a cada 30 segundos
- ✅ Filtro por linha (opcional)

**Props:**
- `showRealtime` (boolean) - Ativa/desativa tempo real
- `codigoLinha` (number, opcional) - Filtra por linha específica

#### 2.3 Componente StopInfo (`front_connecity/src/components/StopInfo.jsx`)

**Funcionalidades:**
- ✅ Exibe previsão de chegada para uma parada
- ✅ Lista todas as linhas que atendem a parada
- ✅ Mostra horário previsto de chegada de cada ônibus
- ✅ Indica se o ônibus é acessível
- ✅ Atualização automática a cada 30 segundos

**Props:**
- `codigoParada` (number) - Código da parada Olho Vivo
- `nomeParada` (string) - Nome da parada
- `lat`, `lon` (number) - Coordenadas

#### 2.4 Página Home (`front_connecity/src/pages/Home.jsx`)

**Funcionalidades:**
- ✅ Toggle para ativar/desativar tempo real
- ✅ Exibição de ônibus no mapa quando ativado
- ✅ Interface visual com switch estilizado

#### 2.5 Página RouteDetail (`front_connecity/src/pages/RouteDetail.jsx`)

**Funcionalidades:**
- ✅ Mapa interativo com rota
- ✅ Toggle para ativar tempo real
- ✅ Seção de previsão de chegada (quando ativado)
- ✅ Lista de paradas com previsões

---

## 🎯 Como usar

### 1. Ativar tempo real na Home

1. Selecione origem e destino
2. Ative o toggle "Mostrar ônibus em tempo real"
3. Os ônibus aparecerão no mapa como marcadores verdes

### 2. Ver previsão de chegada

1. Busque uma rota
2. Selecione uma rota para ver detalhes
3. Ative o toggle "Mostrar ônibus em tempo real"
4. A seção "Previsão de Chegada" aparecerá automaticamente
5. Veja os horários previstos de chegada em cada parada

---

## 🔧 Configuração

### Token da API

O token está configurado em:
- `api/app/olho_vivo_api.py` (linha 20)
- Variável de ambiente: `OLHO_VIVO_TOKEN` (opcional)

Para usar outro token:
```bash
export OLHO_VIVO_TOKEN="seu_token_aqui"
```

---

## 📊 Dados em Tempo Real

### Posição dos Veículos

**Atualização:** A cada 30 segundos

**Dados retornados:**
- Prefixo do veículo
- Coordenadas (lat, lon)
- Status de acessibilidade
- Horário da consulta

### Previsão de Chegada

**Atualização:** A cada 30 segundos

**Dados retornados:**
- Código e nome da parada
- Linhas que atendem a parada
- Quantidade de veículos previstos
- Horário previsto de chegada (HH:MM)
- Status de acessibilidade de cada veículo
- Posição atual do veículo

---

## 🚀 Próximos Passos (Melhorias Futuras)

1. **Mapeamento GTFS → Olho Vivo**
   - Criar tabela de mapeamento entre códigos GTFS e Olho Vivo
   - Extrair automaticamente códigos de paradas das rotas

2. **Filtros Avançados**
   - Filtrar apenas ônibus acessíveis
   - Filtrar por linha específica
   - Filtrar por corredor

3. **Notificações**
   - Alertas quando ônibus está chegando
   - Notificação de atrasos

4. **Histórico**
   - Salvar histórico de previsões
   - Análise de pontualidade

5. **Otimizações**
   - Cache de dados estáticos (linhas, paradas)
   - Debounce nas atualizações
   - WebSocket para atualizações push (se disponível)

---

## 📝 Notas Técnicas

### Limitações Atuais

1. **Mapeamento de Paradas:**
   - Os códigos de paradas GTFS não estão automaticamente mapeados para códigos Olho Vivo
   - É necessário mapeamento manual ou busca por proximidade

2. **Performance:**
   - Múltiplas requisições podem impactar performance
   - Considerar cache e debounce

3. **Cobertura:**
   - API Olho Vivo cobre apenas São Paulo
   - Outras cidades precisarão de APIs diferentes

### Estrutura de Dados

**Posição de Veículo:**
```json
{
  "p": "11433",      // Prefixo
  "a": false,        // Acessível
  "py": -23.5401,    // Latitude
  "px": -46.6441     // Longitude
}
```

**Previsão de Chegada:**
```json
{
  "hr": "23:09",     // Horário consulta
  "p": {
    "cp": 4200953,   // Código parada
    "np": "NOME",    // Nome parada
    "l": [           // Linhas
      {
        "c": "7021-10",  // Código linha
        "qv": 1,         // Quantidade veículos
        "vs": [          // Veículos
          {
            "p": "74558",  // Prefixo
            "t": "23:11",  // Previsão chegada
            "a": true      // Acessível
          }
        ]
      }
    ]
  }
}
```

---

## ✅ Status da Implementação

- [x] Backend - Endpoints da API Olho Vivo
- [x] Frontend - Serviço de API
- [x] Frontend - Componente Map com tempo real
- [x] Frontend - Componente StopInfo
- [x] Frontend - Integração na Home
- [x] Frontend - Integração no RouteDetail
- [ ] Mapeamento automático GTFS → Olho Vivo
- [ ] Cache de dados estáticos
- [ ] Filtros avançados
- [ ] Notificações

---

## 📚 Documentação Relacionada

- `docs/API_OLHO_VIVO.md` - Documentação completa da API
- `docs/VERIFICACAO_APIS.md` - Status das APIs
- `docs/FLUXO_COMPLETO_DADOS.md` - Fluxo de dados do sistema


