# Guia de Deploy no Render.com para Link Mágico Chatbot v5.0.1

Este guia detalha como fazer o deploy da nova arquitetura do Link Mágico Chatbot (Node.js + Python API) no Render.com.

---

## 🚀 **Visão Geral do Deploy**

Você precisará criar **dois serviços separados** no Render.com:

1.  **Serviço Python (Backend)**: Irá hospedar a API Python (`api_server.py`) que lida com a extração de dados, análise e geração de respostas da IA.
2.  **Serviço Node.js (Frontend)**: Irá hospedar o servidor Node.js (`server.js`) que serve a interface web do chatbot e se comunica com a API Python.

---

## 📁 **Estrutura de Arquivos para o Deploy**

Certifique-se de que seus arquivos estejam organizados da seguinte forma no seu repositório Git (ex: GitHub, GitLab, Bitbucket):

```
seu-repositorio/
├── api_server.py
├── analyzer.py
├── data_extractor.py
├── knowledge_base.py
├── knowledge_base_simple.py
├── precision_optimizer.py
├── response_generator.py
├── cache_manager.py
├── requirements.txt         # Para o serviço Python
├── Procfile                 # Para o serviço Python
├── upload/                  # Este será o diretório raiz do seu serviço Node.js
│   ├── server.js
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── .env                 # Variáveis de ambiente para o Node.js
└── .env                     # Variáveis de ambiente para o Python (opcional, pode usar diretamente no Render)
```

**Importante:** O arquivo `.env` dentro da pasta `upload/` é para o serviço Node.js. O arquivo `.env` na raiz do repositório é para o serviço Python. No Render.com, é recomendado configurar as variáveis de ambiente diretamente na interface do serviço, em vez de depender dos arquivos `.env` no repositório.

---

## 🛠️ **Passos para o Deploy no Render.com**

### **Passo 1: Preparar seu Repositório Git**

1.  **Crie um novo repositório Git** (se ainda não tiver um) e faça o upload de todos os arquivos do projeto para ele, seguindo a estrutura acima.
2.  **Certifique-se de que os arquivos `requirements.txt` e `Procfile` (para Python) e `package.json` e `Procfile` (para Node.js) estejam nos locais corretos.**

### **Passo 2: Deploy do Serviço Python (Backend)**

1.  Acesse o [Render.com Dashboard](https://dashboard.render.com/).
2.  Clique em **"New"** e selecione **"Web Service"**.
3.  **Conecte seu repositório Git** e selecione o repositório do seu projeto.
4.  **Configurações do Serviço Python:**
    *   **Name**: `link-magico-api` (ou outro nome de sua preferência)
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt && python -m spacy download pt_core_news_sm`
    *   **Start Command**: `gunicorn api_server:app --bind 0.0.0.0:$PORT`
    *   Adicione suas chaves de API aqui. Exemplo:
        *   `OPENROUTER_API_KEY`: `sua_chave_openrouter`
        *   `HF_API_KEY`: `sua_chave_huggingface`
        *   `SCRAPINGBEE_API_KEY`: `sua_chave_scrapingbee`
        *   `PORT`: `5000` (ou a porta que você configurou no `api_server.py`)
6.  Clique em **"Create Web Service"**.
7.  Aguarde o deploy. Uma vez concluído, o Render.com fornecerá uma **URL pública** para sua API Python (ex: `https://link-magico-api.onrender.com`). **Copie esta URL, você precisará dela para o serviço Node.js.**

### **Passo 3: Deploy do Serviço Node.js (Frontend)**

1.  No [Render.com Dashboard](https://dashboard.render.com/), clique em **"New"** e selecione **"Web Service"** novamente.
2.  **Conecte seu repositório Git** e selecione o mesmo repositório do seu projeto.
3.  **Configurações do Serviço Node.js:**
    *   **Name**: `link-magico-chatbot` (ou outro nome de sua preferência)
    *   **Root Directory**: `upload/` (este é o diretório onde estão os arquivos do Node.js)
    *   **Runtime**: `Node.js`
    *   **Build Command**: `npm install`
    *   **Start Command**: `node server.js`
    *   **Plan Type**: Escolha o plano desejado.
4.  **Variáveis de Ambiente (Environment Variables)**:
    *   Adicione suas variáveis de ambiente aqui. **Esta é a parte mais importante para a comunicação entre os serviços:**
        *   `PORT`: `3000` (ou a porta que você configurou no `server.js`)
        *   `PYTHON_API_URL`: **Cole a URL pública do seu serviço Python** que você copiou no Passo 2 (ex: `https://link-magico-api.onrender.com`)
        *   Outras chaves de API que o Node.js possa precisar (se houver)
5.  Clique em **"Create Web Service"**.

---

## ✅ **Verificação Pós-Deploy**

1.  **Aguarde o deploy de ambos os serviços.** Isso pode levar alguns minutos.
2.  **Verifique os logs** de ambos os serviços no Render.com para garantir que não há erros.
3.  **Acesse a URL pública do seu serviço Node.js** (ex: `https://link-magico-chatbot.onrender.com`).
4.  **Teste o chatbot** inserindo uma URL de página de vendas e interagindo com a IA.

---

## 💡 **Dicas Importantes**

*   **Variáveis de Ambiente**: Sempre use as variáveis de ambiente do Render.com para suas chaves de API e URLs de serviço. Nunca as coloque diretamente no código ou em arquivos `.env` que serão versionados no Git.
*   **CORS**: Certifique-se de que sua API Python (`api_server.py`) tenha o CORS configurado corretamente para permitir requisições do seu frontend Node.js. (Já foi configurado com `CORS(app)`).
*   **Logs**: Monitore os logs no Render.com para depurar quaisquer problemas que possam surgir durante ou após o deploy.
*   **Domínios Personalizados**: Você pode configurar domínios personalizados para seus serviços no Render.com, se desejar.

Com estes passos, você deverá conseguir fazer o deploy completo do seu Link Mágico Chatbot v5.0.1 no Render.com!

