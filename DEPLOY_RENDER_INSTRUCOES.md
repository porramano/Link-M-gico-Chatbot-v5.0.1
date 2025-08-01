# 🚀 Deploy do Link Mágico Chatbot v5.0.1 no Render.com

Este guia detalha o processo de deploy do Link Mágico Chatbot v5.0.1 no Render.com, dividindo a aplicação em dois serviços web: um para o backend Python (API) e outro para o frontend Node.js (servidor web).

## 📦 Arquivos do Projeto

Você recebeu um arquivo ZIP (`link_magico_chatbot_v5.0.1_RENDER_READY.zip`) que contém todos os arquivos necessários, incluindo as correções e configurações para o deploy no Render.com.

## 📋 Pré-requisitos

- Uma conta no [Render.com](https://render.com/)
- Um repositório Git (GitHub, GitLab, Bitbucket) com os arquivos do projeto (você precisará fazer o upload dos arquivos do ZIP para um repositório).
- Chaves de API para:
    - OpenAI
    - OpenRouter
    - Hugging Face (HF_API_KEY)
    - ScrapingBee

## 🔧 Configuração no Render.com

Você precisará criar **dois serviços web** separados no Render.com, um para o backend Python e outro para o frontend Node.js.

### 1. Deploy do Backend Python (API)

Este serviço será responsável pela extração de dados, geração de respostas da IA e gerenciamento de cache.

1.  **Crie um novo serviço web no Render.com:**
    - Acesse o painel do Render.com.
    - Clique em `New` -> `Web Service`.
    - Conecte seu repositório Git onde você fez o upload dos arquivos do projeto.

2.  **Configurações do Serviço:**
    -   **Name:** `link-magico-chatbot-api` (ou um nome de sua preferência)
    -   **Region:** Escolha a região mais próxima de seus usuários.
    -   **Branch:** `main` (ou a branch que contém seu código)
    -   **Root Directory:** `/` (certifique-se de que `api_server.py` e `requirements.txt` estejam na raiz do seu repositório)
    -   **Runtime:** `Python 3`
    -   **Build Command:** `pip install -r requirements.txt`
    -   **Start Command:** `gunicorn api_server:app`
    -   **Instance Type:** Escolha um tipo de instância adequado (o plano gratuito pode ser suficiente para testes, mas para produção, considere um plano pago).

3.  **Variáveis de Ambiente (Environment Variables):**
    É crucial configurar as variáveis de ambiente diretamente no painel do Render.com. Clique em `Advanced` -> `Add Environment Variable` e adicione as seguintes:
    -   `OPENAI_API_KEY`: Sua chave da API OpenAI
    -   `OPENROUTER_API_KEY`: Sua chave da API OpenRouter
    -   `HF_API_KEY`: Sua chave da API Hugging Face
    -   `SCRAPINGBEE_API_KEY`: Sua chave da API ScrapingBee
    -   `LOG_LEVEL`: `info`
    -   `NODE_ENV`: `production`
    -   `PYTHON_API_URL`: Esta variável será preenchida com a URL pública do seu serviço Python **após o deploy**. Deixe-a vazia por enquanto ou coloque um placeholder como `http://localhost:5000` e atualize-a depois.

4.  **Crie o Serviço.** O Render.com iniciará o processo de deploy.

### 2. Deploy do Frontend Node.js (Servidor Web)

Este serviço será responsável por servir a interface do chatbot e a comunicação com o backend Python.

1.  **Crie um novo serviço web no Render.com:**
    - Acesse o painel do Render.com.
    - Clique em `New` -> `Web Service`.
    - Conecte o **mesmo repositório Git** que você usou para o backend Python.

2.  **Configurações do Serviço:**
    -   **Name:** `link-magico-chatbot-frontend` (ou um nome de sua preferência)
    -   **Region:** Escolha a mesma região do backend Python.
    -   **Branch:** `main`
    -   **Root Directory:** `/` (certifique-se de que `server.js`, `package.json`, `index.html` e `chatbot.html` estejam na raiz do seu repositório)
    -   **Runtime:** `Node.js`
    -   **Build Command:** `npm install`
    -   **Start Command:** `node server.js`
    -   **Instance Type:** Escolha um tipo de instância adequado.

3.  **Variáveis de Ambiente (Environment Variables):**
    Adicione as seguintes variáveis:
    -   `LOG_LEVEL`: `info`
    -   `NODE_ENV`: `production`
    -   `PYTHON_API_URL`: **Esta é a URL pública do seu serviço Python (backend)**. Você precisará obter essa URL do serviço Python que você acabou de criar no Render.com (ela estará disponível após o deploy bem-sucedido do backend) e configurá-la aqui.

4.  **Crie o Serviço.** O Render.com iniciará o processo de deploy.

## 🚀 Pós-Deploy

1.  **Obtenha a URL do Backend Python:** Após o deploy bem-sucedido do seu serviço Python, vá para o painel desse serviço no Render.com e copie a `External URL`.

2.  **Atualize a `PYTHON_API_URL` no Frontend Node.js:** Edite as variáveis de ambiente do seu serviço Node.js e cole a URL copiada no campo `PYTHON_API_URL`.

3.  **Acesse o Chatbot:** A URL pública do seu serviço Node.js será a URL principal do seu chatbot. Acesse-a para testar a aplicação.

## ⚠️ Observações Importantes

-   **Redis:** Para um ambiente de produção robusto, você precisará configurar um serviço de banco de dados Redis separado no Render.com e conectar ambos os serviços (Python e Node.js) a ele. As configurações atuais usam um Redis local, que não é adequado para deploy em nuvem. Você pode adicionar a variável de ambiente `REDIS_URL` para apontar para o seu serviço Redis no Render.com.
-   **Persistência de Dados:** O cache atual é em memória. Para persistência de dados (histórico de conversas, dados extraídos), o Redis é essencial.
-   **Custos:** O Render.com oferece um plano gratuito, mas para uso contínuo e maior performance, considere os planos pagos.

Com este guia e os arquivos atualizados, você deve ser capaz de realizar o deploy do seu chatbot com sucesso no Render.com. Se tiver qualquer problema, me avise!

