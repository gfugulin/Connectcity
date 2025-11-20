# 🚌 API Olho Vivo - SPTrans

## 📋 Visão Geral

A API Olho Vivo da SPTrans fornece dados em **tempo real** do sistema de transporte público de São Paulo, incluindo:
- Posição dos veículos em tempo real
- Previsão de chegada nas paradas
- Informações de linhas e paradas
- Velocidade nas vias

**URL Base:** `https://api.olhovivo.sptrans.com.br/v2.1`

**Documentação Oficial:** [https://www.sptrans.com.br/desenvolvedores/api-do-olho-vivo-guia-de-referencia/documentacao-api/](https://www.sptrans.com.br/desenvolvedores/api-do-olho-vivo-guia-de-referencia/documentacao-api/)

---

## 🔐 Autenticação

### Token de Acesso
```
1abf7ba19b22829e9d95648f8affe9afaf8c64b9cbb8c8042e6b50cb5d63be81
```

### Método de Autenticação

```http
POST /Login/Autenticar?token={token}
```

**Resposta:**
- `true` - Autenticação bem-sucedida
- `false` - Falha na autenticação

**Exemplo:**
```python
from integration.olho_vivo_client import OlhoVivoClient

client = OlhoVivoClient("1abf7ba19b22829e9d95648f8affe9afaf8c64b9cbb8c8042e6b50cb5d63be81")
if client.authenticate():
    print("✅ Autenticado com sucesso!")
```

---

## 📡 Endpoints Principais

### 1. Buscar Linhas

```http
GET /Linha/Buscar?termosBusca={termos}
```

**Parâmetros:**
- `termosBusca` (string): Número ou nome da linha (ex: "8000", "Lapa")

**Resposta:**
```json
[
  {
    "cl": 1273,
    "lc": false,
    "lt": "8000",
    "sl": 1,
    "tl": 10,
    "tp": "PCA.RAMOS DE AZEVEDO",
    "ts": "TERMINAL LAPA"
  }
]
```

**Campos:**
- `cl`: Código identificador da linha
- `lt`: Letreiro numérico
- `sl`: Sentido (1 = Principal→Secundário, 2 = Secundário→Principal)
- `tp`: Terminal Principal
- `ts`: Terminal Secundário

---

### 2. Buscar Paradas

```http
GET /Parada/Buscar?termosBusca={termos}
```

**Parâmetros:**
- `termosBusca` (string): Nome ou código da parada

**Resposta:**
```json
[
  {
    "cp": 4200953,
    "np": "PARADA ROBERTO SELMI DEI B/C",
    "ed": "RUA ROBERTO SELMI DEI",
    "py": -23.675901,
    "px": -46.752812
  }
]
```

**Campos:**
- `cp`: Código da parada
- `np`: Nome da parada
- `ed`: Endereço
- `py`: Latitude
- `px`: Longitude

---

### 3. Posição dos Veículos (Tempo Real)

```http
GET /Posicao/Linha?codigoLinha={codigo}
```

**Parâmetros:**
- `codigoLinha` (int): Código da linha

**Resposta:**
```json
{
  "hr": "22:57",
  "vs": [
    {
      "p": "11433",
      "a": false,
      "py": -23.540150375000003,
      "px": -46.64414075
    }
  ]
}
```

**Campos:**
- `hr`: Horário da consulta
- `vs`: Lista de veículos
  - `p`: Prefixo do veículo
  - `a`: Acessível (true/false)
  - `py`: Latitude
  - `px`: Longitude

---

### 4. Previsão de Chegada

```http
GET /Previsao?codigoParada={parada}&codigoLinha={linha}
```

**Parâmetros:**
- `codigoParada` (int): Código da parada
- `codigoLinha` (int): Código da linha

**Resposta:**
```json
{
  "hr": "23:09",
  "p": {
    "cp": 4200953,
    "np": "PARADA ROBERTO SELMI DEI B/C",
    "py": -23.675901,
    "px": -46.752812,
    "l": [
      {
        "c": "7021-10",
        "cl": 1989,
        "sl": 1,
        "lt0": "TERM. JOÃO DIAS",
        "lt1": "JD. MARACÁ",
        "qv": 1,
        "vs": [
          {
            "p": "74558",
            "t": "23:11",
            "a": true,
            "py": -23.67603,
            "px": -46.75891166666667
          }
        ]
      }
    ]
  }
}
```

**Campos:**
- `hr`: Horário da consulta
- `qv`: Quantidade de veículos
- `vs`: Lista de veículos
  - `p`: Prefixo do veículo
  - `t`: Previsão de chegada (HH:MM)
  - `a`: Acessível
  - `py`, `px`: Coordenadas do veículo

---

## 💻 Uso no Código

### Cliente Python

```python
from integration.olho_vivo_client import OlhoVivoClient

# Inicializar cliente
client = OlhoVivoClient("1abf7ba19b22829e9d95648f8affe9afaf8c64b9cbb8c8042e6b50cb5d63be81")

# Autenticar
if client.authenticate():
    # Buscar linhas
    linhas = client.buscar_linhas("8000")
    print(f"Encontradas {len(linhas)} linhas")
    
    # Buscar paradas
    paradas = client.buscar_paradas("Lapa")
    print(f"Encontradas {len(paradas)} paradas")
    
    # Obter posição dos veículos
    if linhas:
        codigo_linha = linhas[0]["cl"]
        posicoes = client.obter_posicao_veiculos(codigo_linha)
        print(f"Veículos em trânsito: {len(posicoes.get('vs', []))}")
    
    # Obter previsão de chegada
    if paradas and linhas:
        codigo_parada = paradas[0]["cp"]
        codigo_linha = linhas[0]["cl"]
        previsao = client.obter_previsao_chegada(codigo_parada, codigo_linha)
        print(f"Previsão: {previsao}")
```

---

## 🔄 Integração com o Sistema

### Diferença entre GTFS e Olho Vivo

| Aspecto | GTFS | Olho Vivo |
|---------|------|-----------|
| **Tipo de Dados** | Estáticos | Tempo Real |
| **Conteúdo** | Rotas, horários, paradas | Posição veículos, previsão |
| **Atualização** | Semanal/Mensal | Contínua |
| **Uso** | Planejamento de rotas | Monitoramento em tempo real |

### Casos de Uso

1. **GTFS (Dados Estáticos):**
   - Planejamento de rotas
   - Cálculo de caminhos
   - Informações de paradas e linhas

2. **Olho Vivo (Tempo Real):**
   - Mostrar posição dos ônibus no mapa
   - Previsão de chegada nas paradas
   - Status de acessibilidade em tempo real
   - Monitoramento de tráfego

### Integração Recomendada

```python
# 1. Usar GTFS para planejamento de rotas
gtfs_processor = GTFSProcessor()
nodes, edges = gtfs_processor.convert_to_conneccity_format()

# 2. Usar Olho Vivo para dados em tempo real
olho_vivo = OlhoVivoClient(TOKEN)
olho_vivo.authenticate()

# 3. Combinar dados para experiência completa
# - GTFS: Rota planejada
# - Olho Vivo: Posição atual dos veículos na rota
```

---

## ⚠️ Observações Importantes

1. **Protocolo HTTPS:**
   - A API migrou para HTTPS
   - HTTP será desativado em 02/01/2024
   - Sempre use `https://api.olhovivo.sptrans.com.br`

2. **Autenticação:**
   - Token deve ser mantido seguro
   - Autenticação é necessária antes de cada sessão
   - Token pode expirar (verificar periodicamente)

3. **Rate Limiting:**
   - Respeitar limites de requisições
   - Implementar cache quando possível
   - Não fazer requisições excessivas

4. **Dados em Tempo Real:**
   - Previsões são baseadas no horário da consulta
   - Atualizar dados regularmente para precisão
   - Considerar latência de rede

---

## 📚 Referências

- [Documentação Oficial](https://www.sptrans.com.br/desenvolvedores/api-do-olho-vivo-guia-de-referencia/documentacao-api/)
- [Portal de Desenvolvedores](https://www.sptrans.com.br/desenvolvedores/)
- [Área de Login](https://www.sptrans.com.br/desenvolvedores/login-desenvolvedores/)

