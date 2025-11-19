# CONNECITY Frontend - Versão Vanilla JS

## 🚀 Início Rápido

### 1. Adicionar scripts ao HTML

Adicione estas linhas antes do `</body>` em cada HTML:

```html
<!-- Adicionar antes de </body> -->
<script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
<script src="js/api.js"></script>
<script src="js/router.js"></script>
<script src="js/home.js"></script> <!-- Apenas na tela inicial -->
```

### 2. Estrutura de Arquivos

```
front_connecity/
├── index.html (tela_2 - renomear)
├── routes.html (tela_3 - renomear)
├── route-detail.html (tela_4 - renomear)
├── favorites.html (tela_7 - renomear)
├── profile.html (tela_9 - renomear)
└── js/
    ├── api.js          ✅ Cliente HTTP
    ├── router.js       ✅ Navegação
    ├── home.js         ✅ Tela inicial
    └── routes.js       ✅ Resultados
```

### 3. Testar

1. Certifique-se de que o backend está rodando:
   ```bash
   cd api
   uvicorn app.main:app --reload --port 8080
   ```

2. Abra `index.html` no navegador (ou use um servidor local):
   ```bash
   # Python
   python -m http.server 8000
   
   # Node.js
   npx serve .
   ```

3. Teste a busca de rotas usando IDs de nós válidos (ex: "node1", "node2")

## 📝 Próximos Passos

1. ✅ Renomear arquivos HTML para nomes mais simples
2. ✅ Adicionar IDs aos inputs nos HTMLs
3. ✅ Implementar tela de detalhes (route-detail.js)
4. ✅ Implementar favoritos (favorites.js)
5. ✅ Adicionar busca de nós/autocomplete

## 🔧 Configuração

A URL da API está configurada em `js/api.js`:
```javascript
const API_BASE = 'http://localhost:8080';
```

Para produção, altere para a URL do servidor.

