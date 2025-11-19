# 🔧 Solução: Autenticação API Olho Vivo

## 📋 Análise do Problema

**Situação:**
- ✅ Token está **ativo e homologado** na área "Meus Aplicativos"
- ✅ Status: "Chave de ativação homologada e em uso"
- ❌ API retorna `false` na autenticação
- ✅ Status HTTP: 200 (requisição OK)

**Log:**
```
Status code: 200
Response text: false
Response JSON: False (tipo: bool)
```

---

## 🔍 Possíveis Causas

### 1. Headers HTTP Incorretos ⚠️

A API pode estar rejeitando requisições que não têm headers apropriados ou que têm headers incorretos.

**Problema identificado:**
- `Content-Type: application/json` pode estar causando problemas em POST com query string
- Falta de `User-Agent` pode fazer a API rejeitar a requisição

### 2. Formato da Requisição

Algumas APIs são sensíveis à forma como os parâmetros são enviados.

---

## ✅ Correções Implementadas

### 1. Headers HTTP Ajustados

**Antes:**
```python
self.session.headers.update({
    'Content-Type': 'application/json',  # ❌ Pode causar problemas
})
```

**Depois:**
```python
self.session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache'
    # ✅ Removido Content-Type para POST com query string
})
```

### 2. Método de Envio do Token

Agora tenta dois métodos:
1. Token direto na URL: `POST /Login/Autenticar?token={token}`
2. Token via params: `POST /Login/Autenticar` com `params={"token": token}`

### 3. Logs Detalhados

Logs agora mostram:
- URL completa com token
- Headers enviados
- Resposta completa da API

---

## 🧪 Como Testar

### 1. Reiniciar a API

```bash
docker-compose restart api
```

### 2. Verificar Logs

```bash
docker-compose logs -f api
```

**Procure por:**
```
🔐 Tentando autenticar na API Olho Vivo
   URL completa: https://api.olhovivo.sptrans.com.br/v2.1/Login/Autenticar?token=...
   Status code: 200
   Response JSON: True (tipo: bool)  # ✅ Deve ser True agora
```

### 3. Teste Manual via cURL

```bash
curl -X POST "https://api.olhovivo.sptrans.com.br/v2.1/Login/Autenticar?token=1abf7ba19b22829e9d95648f8affe9afaf8c64b9cbb8c8042e6b50cb5d63be81" \
  -H "User-Agent: Mozilla/5.0" \
  -H "Accept: */*"
```

**Resposta esperada:** `true`

---

## 🔍 Se Ainda Não Funcionar

### Verificações Adicionais

1. **Token está correto?**
   - Verificar na área "Meus Aplicativos"
   - Copiar token novamente (pode ter espaços extras)

2. **API está online?**
   ```bash
   curl -I https://api.olhovivo.sptrans.com.br/v2.1/Login/Autenticar
   ```

3. **Problema de rede/firewall?**
   - Verificar se há proxy ou firewall bloqueando
   - Testar de outra rede

4. **Token precisa ser reativado?**
   - Acessar área "Meus Aplicativos"
   - Verificar se há opção de reativar/regenerar token

---

## 📚 Referências

- [Documentação Oficial - Autenticação](https://www.sptrans.com.br/desenvolvedores/api-do-olho-vivo-guia-de-referencia/documentacao-api/#docApi-autenticacao)
- [Área de Desenvolvedores](https://www.sptrans.com.br/desenvolvedores/)

---

## ⚠️ Nota Importante

Se após essas correções a autenticação ainda falhar, pode ser necessário:
1. Contatar o suporte da SPTrans
2. Verificar se há alguma restrição adicional no token
3. Verificar se o token precisa ser usado de uma forma específica


