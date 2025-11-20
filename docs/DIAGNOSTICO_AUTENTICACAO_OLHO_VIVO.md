# 🔍 Diagnóstico: Autenticação API Olho Vivo

## ❌ Problema

**Log do Docker:**
```
❌ Falha na autenticação da API Olho Vivo. Resposta: false
   Status: 200, URL: https://api.olhovivo.sptrans.com.br/v2.1/Login/Autenticar
```

**Status HTTP:** 200 (OK)  
**Resposta:** `false` (token rejeitado)

---

## 📋 Análise da Documentação

Conforme a [documentação oficial](https://www.sptrans.com.br/desenvolvedores/api-do-olho-vivo-guia-de-referencia/documentacao-api/#docApi-autenticacao):

### Método de Autenticação

```
POST /Login/Autenticar?token={token}
```

**Parâmetros:**
- `[string]token` - Sua chave de acesso que deve ser gerada na área "Meus Aplicativos"

**Resposta:**
- `true` - Autenticação bem-sucedida
- `false` - Erro na autenticação

---

## ✅ Implementação Atual

O código está implementado corretamente:

```python
url = f"{self.BASE_URL}/Login/Autenticar"
params = {"token": self.token}
response = self.session.post(url, params=params, timeout=10)
```

**URL Base:** `https://api.olhovivo.sptrans.com.br/v2.1` ✅  
**Método:** POST ✅  
**Parâmetro:** `token` na query string ✅

---

## 🔍 Possíveis Causas

### 1. Token Inválido ou Expirado ⚠️ **MAIS PROVÁVEL**

O token `1abf7ba19b22829e9d95648f8affe9afaf8c64b9cbb8c8042e6b50cb5d63be81` pode estar:
- ❌ Expirado
- ❌ Inválido
- ❌ Não ativado na área "Meus Aplicativos"

**Solução:**
1. Acessar: https://www.sptrans.com.br/desenvolvedores/
2. Fazer login na área "Meus Aplicativos"
3. Verificar se o token está ativo
4. Gerar um novo token se necessário

### 2. Token Não Configurado Corretamente

O token pode não estar sendo passado corretamente.

**Verificação:**
- ✅ Token está definido em `api/app/main.py` (linha 98)
- ✅ Token está sendo passado para `OlhoVivoClient`
- ✅ Token está sendo enviado na query string

### 3. Problema com Sessão HTTP

A API pode exigir que a sessão seja mantida após autenticação.

**Status:** ✅ O código já usa `requests.Session()` para manter cookies

---

## 🧪 Como Testar Manualmente

### Teste 1: cURL

```bash
curl -X POST "https://api.olhovivo.sptrans.com.br/v2.1/Login/Autenticar?token=1abf7ba19b22829e9d95648f8affe9afaf8c64b9cbb8c8042e6b50cb5d63be81"
```

**Resposta esperada:**
- `true` - Token válido
- `false` - Token inválido

### Teste 2: Python

```python
import requests

token = "1abf7ba19b22829e9d95648f8affe9afaf8c64b9cbb8c8042e6b50cb5d63be81"
url = "https://api.olhovivo.sptrans.com.br/v2.1/Login/Autenticar"

response = requests.post(url, params={"token": token})
print(f"Status: {response.status_code}")
print(f"Resposta: {response.text}")
print(f"JSON: {response.json()}")
```

---

## 🔧 Melhorias Implementadas

### 1. Logs Detalhados

Agora o código mostra:
- ✅ URL completa
- ✅ Primeiros e últimos caracteres do token (para verificação)
- ✅ Status code
- ✅ Resposta completa
- ✅ Tipo da resposta (boolean, string, etc.)

### 2. Mensagens de Erro Mais Informativas

Inclui link para área de desenvolvedores da SPTrans.

---

## 📝 Próximos Passos

### 1. Verificar Token

**Ação:** Acessar https://www.sptrans.com.br/desenvolvedores/ e verificar:
- [ ] Token está ativo
- [ ] Token não expirou
- [ ] Token está correto

### 2. Gerar Novo Token (se necessário)

**Ação:** Se o token estiver inválido:
1. Acessar área "Meus Aplicativos"
2. Gerar novo token
3. Atualizar no código ou variável de ambiente

### 3. Testar Manualmente

**Ação:** Testar autenticação via cURL ou Python antes de usar no sistema.

### 4. Configurar Variável de Ambiente

**Recomendação:** Usar variável de ambiente em vez de hardcoded:

```bash
# Linux/Mac
export OLHO_VIVO_TOKEN="seu_novo_token_aqui"

# Windows PowerShell
$env:OLHO_VIVO_TOKEN="seu_novo_token_aqui"

# Docker Compose
environment:
  - OLHO_VIVO_TOKEN=seu_novo_token_aqui
```

---

## 📚 Referências

- [Documentação Oficial - Autenticação](https://www.sptrans.com.br/desenvolvedores/api-do-olho-vivo-guia-de-referencia/documentacao-api/#docApi-autenticacao)
- [Área de Desenvolvedores](https://www.sptrans.com.br/desenvolvedores/)
- [Meus Aplicativos](https://www.sptrans.com.br/desenvolvedores/) (requer login)

---

## ⚠️ Importante

**O token fornecido pode estar:**
1. Expirado
2. Inválido
3. Não ativado

**A solução mais provável é gerar um novo token na área "Meus Aplicativos" da SPTrans.**

