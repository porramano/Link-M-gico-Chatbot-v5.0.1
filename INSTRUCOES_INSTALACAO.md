# 🚀 Link Mágico Chatbot v5.0.1 - Instruções de Instalação

## 📋 Pré-requisitos

- Python 3.11+
- Node.js 20+
- Redis Server
- Chaves de API configuradas

## 🔧 Instalação

### 1. Extrair Arquivos
```bash
unzip link_magico_chatbot_v5.0.1_CORRIGIDO.zip
cd link_magico_chatbot_v5.0.1_CORRIGIDO
```

### 2. Configurar Variáveis de Ambiente
Edite o arquivo `.env` com suas chaves:
```env
# Configurações do Link Mágico Chatbot v5.0.1
PORT=3000
PYTHON_API_URL=http://localhost:5000

# Chaves de API para IA
OPENAI_API_KEY=sua_chave_openai
OPENROUTER_API_KEY=sua_chave_openrouter
HF_API_KEY=sua_chave_huggingface

# Configurações de scraping
SCRAPINGBEE_API_KEY=sua_chave_scrapingbee

# Configurações de logs
LOG_LEVEL=info
NODE_ENV=development
```

### 3. Instalar Dependências Python
```bash
pip install flask flask-cors requests beautifulsoup4 trafilatura redis python-dotenv jinja2
```

### 4. Instalar Dependências Node.js
```bash
npm install express cors helmet winston axios uuid dotenv
```

### 5. Iniciar Redis
```bash
redis-server
```

## 🚀 Execução

### 1. Iniciar API Python (Terminal 1)
```bash
python api_server_melhorado.py
```

### 2. Iniciar Frontend Node.js (Terminal 2)
```bash
node server_melhorado.js
```

### 3. Acessar o Sistema
- **Painel de Controle:** http://localhost:3000
- **Interface do Chatbot:** http://localhost:3000/chatbot
- **API Health Check:** http://localhost:3000/health

## 📱 Como Usar

### 1. Criar um Chatbot
1. Acesse http://localhost:3000
2. Preencha:
   - **Nome do Assistente:** @seu_assistente
   - **URL da Página:** URL da página de vendas
   - **Instruções:** Personalize o comportamento
3. Clique em "🚀 Ativar Chatbot Inteligente"

### 2. Testar o Chatbot
1. Clique no link gerado
2. Faça perguntas como:
   - "Qual o preço?"
   - "Quais os benefícios?"
   - "Tem garantia?"
   - "Como faço para comprar?"

### 3. Compartilhar
Use os botões sociais para compartilhar o link do chatbot.

## 🔍 Monitoramento

### Logs
- **Python:** Arquivo `api_server.log`
- **Node.js:** Arquivo `server.log`
- **Console:** Logs em tempo real

### Estatísticas
- Acesse: http://localhost:3000/api/cache/stats
- Monitore sessões ativas e cache

## 🛠️ Solução de Problemas

### Problema: API Python não inicia
**Solução:**
```bash
# Verificar porta em uso
lsof -i :5000

# Usar porta alternativa
PORT=5001 python api_server_melhorado.py
```

### Problema: Redis não conecta
**Solução:**
```bash
# Verificar se Redis está rodando
redis-cli ping

# Iniciar Redis se necessário
redis-server
```

### Problema: Extração de dados falha
**Solução:**
1. Verificar chave ScrapingBee no `.env`
2. Testar URL manualmente
3. Verificar logs para detalhes

### Problema: Chatbot não responde
**Solução:**
1. Verificar chave OpenRouter no `.env`
2. Sistema funciona com fallback inteligente
3. Verificar logs da API Python

## 📊 Arquivos Principais

| Arquivo | Descrição |
|---------|-----------|
| `api_server_melhorado.py` | API Python principal |
| `server_melhorado.js` | Frontend Node.js |
| `data_extractor_melhorado.py` | Extração de dados |
| `response_generator_melhorado.py` | Geração de respostas IA |
| `cache_manager_melhorado.py` | Sistema de cache |
| `index.html` | Interface principal |
| `chatbot.html` | Interface do chatbot |

## 🎯 Funcionalidades

### ✅ Extração Inteligente
- Extrai dados de qualquer página de vendas
- Sistema de fallback robusto
- Cache automático para performance

### ✅ IA Especialista em Vendas
- Respostas focadas em conversão
- Redirecionamento inteligente
- Superação de objeções

### ✅ Interface Moderna
- Design responsivo
- Experiência fluida
- Compartilhamento social

### ✅ Sistema Robusto
- Logs detalhados
- Tratamento de erros
- Fallbacks automáticos

## 📞 Suporte

Para dúvidas ou problemas:
1. Consulte os logs do sistema
2. Verifique as configurações no `.env`
3. Teste as APIs individualmente
4. Consulte o `RELATORIO_TESTES_CHATBOT.md`

---

**Link Mágico Chatbot v5.0.1 - Especialista em Vendas IA**
*Sistema completamente corrigido e otimizado*

