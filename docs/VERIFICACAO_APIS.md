# 🔍 Verificação das APIs GTFS e OSM

## 📊 Status das APIs

### ✅ API Overpass (OpenStreetMap)
**URL:** `http://overpass-api.de/api/interpreter`

**Status:** ✅ **FUNCIONANDO E IMPLEMENTADO**

A API Overpass está respondendo corretamente. O erro "encoding error: Your input contains only whitespace" é esperado quando não há query enviada, o que confirma que a API está ativa.

**Autenticação:** Não requer autenticação (API pública)

**Query Overpass QL Utilizada:**
```overpass
[out:xml][timeout:300];
(
  way["highway"~"^(primary|secondary|tertiary|residential|service|footway|cycleway|steps|path)$"]({bbox});
  way["public_transport"="platform"]({bbox});
  way["railway"~"^(tram|subway|light_rail)$"]({bbox});
  node["public_transport"="stop_position"]({bbox});
  node["railway"="station"]({bbox});
  node["railway"="tram_stop"]({bbox});
  node["railway"="subway_entrance"]({bbox});
);
out geom;
```

**Dados Coletados:**
- Vias (ruas, calçadas, ciclovias, escadas)
- Paradas de transporte público
- Estações ferroviárias
- Informações de acessibilidade
- Qualidade de superfície
- Riscos de alagamento

**Teste:**
- Acessar a URL retorna página de resposta OSM3S
- API está pronta para receber queries Overpass QL
- Query testada com sucesso para área do Centro de SP

**Documentação Completa:** Ver `docs/API_OPENSTREETMAP.md`

---

### ✅ SPTrans API Olho Vivo
**URL Base:** `https://api.olhovivo.sptrans.com.br/v2.1`

**Status:** ✅ **CONFIGURADO E FUNCIONANDO**

**Autenticação:**
- Método: POST `/Login/Autenticar?token={token}`
- Token fornecido: `1abf7ba19b22829e9d95648f8affe9afaf8c64b9cbb8c8042e6b50cb5d63be81`
- Protocolo: HTTPS (HTTP será desativado em 02/01/2024)

**Endpoints Disponíveis:**
1. **Linhas:**
   - `GET /Linha/Buscar?termosBusca={termos}` - Buscar linhas
   - `GET /Linha/BuscarLinhaSentido?termosBusca={termos}` - Buscar linha por sentido

2. **Paradas:**
   - `GET /Parada/Buscar?termosBusca={termos}` - Buscar paradas
   - `GET /Parada/BuscarParadasPorLinha?codigoLinha={codigo}` - Paradas por linha
   - `GET /Parada/BuscarParadasPorCorredor?codigoCorredor={codigo}` - Paradas por corredor

3. **Posição dos Veículos (Tempo Real):**
   - `GET /Posicao` - Todas as posições
   - `GET /Posicao/Linha?codigoLinha={codigo}` - Posição por linha
   - `GET /Posicao/Garagem?codigoGaragem={codigo}` - Posição por garagem

4. **Previsão de Chegada:**
   - `GET /Previsao?codigoParada={parada}&codigoLinha={linha}` - Previsão específica
   - `GET /Previsao/Linha?codigoLinha={codigo}` - Previsão por linha
   - `GET /Previsao/Parada?codigoParada={codigo}` - Previsão por parada

5. **Outros:**
   - `GET /Corredor` - Lista de corredores
   - `GET /Empresa` - Lista de empresas
   - `GET /Velocidade` - Velocidade nas vias

**Documentação:** [https://www.sptrans.com.br/desenvolvedores/api-do-olho-vivo-guia-de-referencia/documentacao-api/](https://www.sptrans.com.br/desenvolvedores/api-do-olho-vivo-guia-de-referencia/documentacao-api/)

**Nota:** A API Olho Vivo fornece dados em **tempo real**, diferente do GTFS que fornece dados estáticos. São complementares:
- **GTFS:** Rotas, horários, paradas (dados estáticos)
- **Olho Vivo:** Posição dos veículos, previsão de chegada (dados em tempo real)

### ⚠️ SPTrans GTFS
**Status:** ⚠️ **REQUER AUTENTICAÇÃO VIA PORTAL**

A SPTrans requer cadastro/login no portal de desenvolvedores para acessar dados GTFS estáticos. A API Olho Vivo é a alternativa recomendada para dados em tempo real.

**URLs Configuradas no Código:**
```python
# integration/sp_data_collector.py
"gtfs_sources": {
    "sptrans": "https://www.sptrans.com.br/gtfs/gtfs.zip",
    "metro": "https://www.metro.sp.gov.br/gtfs/gtfs.zip",
    "cptm": "https://www.cptm.sp.gov.br/gtfs/gtfs.zip"
}
```

---

## 🔧 Correções Necessárias

### 1. Verificar URLs GTFS Corretas

**Fontes Alternativas para São Paulo:**

1. **SPTrans:**
   - Verificar: https://www.sptrans.com.br/desenvolvimento/
   - Possível URL: https://www.sptrans.com.br/arquivos/gtfs.zip
   - Ou: https://www.sptrans.com.br/gtfs/gtfs.zip (direto)

2. **Metrô SP:**
   - Verificar: https://www.metro.sp.gov.br/desenvolvimento/
   - Possível URL: https://www.metro.sp.gov.br/arquivos/gtfs.zip

3. **CPTM:**
   - Verificar: https://www.cptm.sp.gov.br/desenvolvimento/
   - Possível URL: https://www.cptm.sp.gov.br/arquivos/gtfs.zip

4. **Fontes Alternativas:**
   - **TransitFeeds:** https://transitfeeds.com/p/sptrans/ (pode ter links atualizados)
   - **GTFS Brasil:** Repositórios comunitários

### 2. Testar URLs Diretas

```bash
# Testar download direto
curl -I https://www.sptrans.com.br/gtfs/gtfs.zip
curl -I https://www.sptrans.com.br/arquivos/gtfs.zip
curl -I https://www.metro.sp.gov.br/gtfs/gtfs.zip
```

### 3. Verificar Outras Cidades

**Belo Horizonte:**
- URL do Dataset: `https://ckan.pbh.gov.br/dataset/gtfs`
- **URL Direta de Download:** `https://s3.amazonaws.com/mobilibus-uploads/gtfs/GTFSBHTRANS.zip`
- Status: ✅ **FUNCIONANDO** (testado - download iniciado com sucesso)
- Atualização: Semanal (arquivo atualizado diariamente, mas metadados atualizados semanalmente)

**Outras cidades:**
- Rio de Janeiro: `https://www.riocard.com/gtfs/`
- Porto Alegre: `https://www.poa.leg.br/gtfs/`
- Curitiba: `https://www.urbs.curitiba.pr.gov.br/gtfs/`

---

## ✅ URLs Verificadas e Funcionando

### Belo Horizonte (BHTrans)
- **URL:** `https://s3.amazonaws.com/mobilibus-uploads/gtfs/GTFSBHTRANS.zip`
- **Status:** ✅ Funcionando
- **Formato:** ZIP direto
- **Atualização:** Semanal

### Overpass API (OSM)
- **URL:** `http://overpass-api.de/api/interpreter`
- **Status:** ✅ Funcionando
- **Método:** POST com query Overpass QL

---

## 📝 Recomendações

### 1. Atualizar URLs no Código

Criar um arquivo de configuração que pode ser atualizado facilmente:

```python
# config/gtfs_sources.json
{
  "belo_horizonte": {
    "bhtrans": {
      "url": "https://s3.amazonaws.com/mobilibus-uploads/gtfs/GTFSBHTRANS.zip",
      "verified": true,
      "last_checked": "2024-11-19",
      "requires_auth": false
    }
  },
  "sao_paulo": {
    "sptrans": {
      "url": "https://www.sptrans.com.br/gtfs/gtfs.zip",
      "verified": false,
      "last_checked": "2024-11-19",
      "requires_auth": true,
      "auth_url": "https://www.sptrans.com.br/desenvolvedores/login-desenvolvedores/",
      "note": "Requer cadastro/login como desenvolvedor"
    },
    "metro": {
      "url": "https://www.metro.sp.gov.br/gtfs/gtfs.zip",
      "verified": false,
      "last_checked": "2024-11-19",
      "requires_auth": false
    },
    "cptm": {
      "url": "https://www.cptm.sp.gov.br/gtfs/gtfs.zip",
      "verified": false,
      "last_checked": "2024-11-19",
      "requires_auth": false
    }
  }
}
```

### 2. Implementar Validação de URLs

Adicionar verificação antes de tentar download:

```python
def verify_gtfs_url(url: str) -> bool:
    """Verifica se URL GTFS está acessível"""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except:
        return False
```

### 3. Adicionar Fallbacks

Se uma fonte falhar, tentar alternativas:

```python
def download_gtfs_with_fallback(sources: List[str]) -> Optional[str]:
    """Tenta baixar GTFS de múltiplas fontes"""
    for source_url in sources:
        if verify_gtfs_url(source_url):
            try:
                return download_gtfs_data(source_url)
            except:
                continue
    return None
```

### 4. Monitoramento

Adicionar logs e alertas quando URLs falharem:

```python
if not verify_gtfs_url(url):
    logger.warning(f"URL GTFS não acessível: {url}")
    # Enviar alerta ou usar cache
```

---

## ✅ Próximos Passos

1. **Testar URLs diretas de download:**
   - Verificar se arquivos .zip estão acessíveis diretamente
   - Testar com curl/wget

2. **Verificar páginas de desenvolvimento:**
   - Acessar seções de "Desenvolvimento" ou "Dados Abertos"
   - Procurar por links de download GTFS

3. **Atualizar código:**
   - Corrigir URLs no código
   - Adicionar validação de URLs
   - Implementar fallbacks

4. **Documentar URLs corretas:**
   - Criar lista de URLs verificadas
   - Adicionar data de verificação
   - Manter atualizado

---

## 🔗 Links Úteis

- **GTFS Brasil:** Repositórios comunitários
- **TransitFeeds:** https://transitfeeds.com/ (catálogo de feeds GTFS)
- **OpenStreetMap:** https://www.openstreetmap.org/
- **Overpass API Docs:** https://wiki.openstreetmap.org/wiki/Overpass_API

