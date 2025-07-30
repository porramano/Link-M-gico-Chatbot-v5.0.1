const express = require("express");
const cors = require("cors");
const helmet = require("helmet");
const winston = require("winston");
const axios = require("axios");
const { v4: uuidv4 } = require("uuid");
require("dotenv").config();

const app = express();
const PORT = process.env.PORT || 3000;

// URL da API Python - CORRIGIDA para ambiente de produção
const PYTHON_API_URL = process.env.PYTHON_API_URL || "http://localhost:5000";

// Configuração de logs melhorada
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || "info",
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    }),
    new winston.transports.File({ 
      filename: "server.log",
      maxsize: 5242880, // 5MB
      maxFiles: 5
    }),
  ],
});

// Middlewares de segurança e CORS
app.use(helmet({
  contentSecurityPolicy: false,
  crossOriginEmbedderPolicy: false,
}));

app.use(cors({
  origin: true, // Permite qualquer origem
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
}));

app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true, limit: "10mb" }));

// Middleware de logging de requisições
app.use((req, res, next) => {
  logger.info(`${req.method} ${req.path}`, {
    ip: req.ip,
    userAgent: req.get('User-Agent'),
    body: req.method === 'POST' ? req.body : undefined
  });
  next();
});

// Servir arquivos estáticos
app.use(express.static(__dirname));

// Função para verificar saúde da API Python
async function checkPythonApiHealth() {
  try {
    const response = await axios.get(`${PYTHON_API_URL}/`, { timeout: 5000 });
    return response.status === 200;
  } catch (error) {
    logger.error("API Python não está respondendo:", error.message);
    return false;
  }
}

// Função para extrair dados via API Python
async function extractPageDataViaPython(url) {
  try {
    logger.info(`Solicitando extração de dados da API Python para: ${url}`);
    
    const response = await axios.post(`${PYTHON_API_URL}/extract_data`, 
      { url: url },
      { 
        timeout: 60000, // 60 segundos para extração
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
    
    if (response.data && response.data.data) {
      logger.info("Dados extraídos com sucesso pela API Python.");
      return {
        success: true,
        data: response.data.data,
        cached: response.data.cached || false
      };
    } else {
      logger.error("API Python não retornou dados válidos:", response.data);
      return { success: false, error: "Dados inválidos retornados pela API" };
    }
  } catch (error) {
    logger.error("Erro ao solicitar extração de dados da API Python:", {
      message: error.message,
      code: error.code,
      response: error.response?.data
    });
    return { 
      success: false, 
      error: `Erro na comunicação com API Python: ${error.message}` 
    };
  }
}

// Função para gerar resposta via API Python
async function generateResponseViaPython(userQuestion, structuredData, sessionId, instructions = "") {
  try {
    logger.info(`Solicitando resposta da API Python para sessão: ${sessionId}`);
    
    const response = await axios.post(`${PYTHON_API_URL}/generate_response`, {
      user_question: userQuestion,
      structured_data: structuredData,
      session_id: sessionId,
      instructions: instructions
    }, {
      timeout: 30000, // 30 segundos para geração de resposta
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (response.data && response.data.response) {
      logger.info("Resposta gerada com sucesso pela API Python.");
      return {
        success: true,
        response: response.data.response,
        session_id: response.data.session_id
      };
    } else {
      logger.error("API Python não retornou resposta válida:", response.data);
      return { success: false, error: "Resposta inválida da API Python" };
    }
  } catch (error) {
    logger.error("Erro ao solicitar resposta da API Python:", {
      message: error.message,
      code: error.code,
      response: error.response?.data
    });
    return { 
      success: false, 
      error: `Erro na comunicação com API Python: ${error.message}` 
    };
  }
}

// ROTAS

// Rota principal - painel de controle
app.get("/", (req, res) => {
  logger.info("Servindo página principal");
  res.sendFile(__dirname + "/index.html");
});

// Rota para interface do chatbot
app.get("/chatbot", (req, res) => {
  logger.info("Servindo interface do chatbot");
  res.sendFile(__dirname + "/chatbot.html");
});

// Rota de verificação de saúde
app.get("/health", async (req, res) => {
  const pythonApiHealthy = await checkPythonApiHealth();
  
  res.json({
    status: "online",
    service: "LinkMágico Chatbot Frontend",
    version: "5.0.1",
    timestamp: new Date().toISOString(),
    python_api: {
      url: PYTHON_API_URL,
      healthy: pythonApiHealthy
    },
    environment: {
      node_env: process.env.NODE_ENV || "development",
      port: PORT
    }
  });
});

// Rota para extrair dados da página de vendas
app.post("/api/extract", async (req, res) => {
  try {
    const { url } = req.body;
    
    if (!url) {
      return res.status(400).json({ 
        error: "URL é obrigatória",
        received: req.body 
      });
    }

    // Validação básica de URL
    try {
      new URL(url);
    } catch (urlError) {
      return res.status(400).json({ 
        error: "URL inválida",
        url: url 
      });
    }

    logger.info(`Processando extração para: ${url}`);

    const result = await extractPageDataViaPython(url);

    if (result.success) {
      res.json({
        data: result.data,
        cached: result.cached,
        timestamp: new Date().toISOString()
      });
    } else {
      res.status(500).json({
        error: result.error || "Erro na extração de dados",
        url: url
      });
    }

  } catch (error) {
    logger.error("Erro no endpoint /api/extract:", error);
    res.status(500).json({ 
      error: "Erro interno do servidor",
      details: error.message 
    });
  }
});

// Rota para gerar resposta do chatbot
app.post("/api/chat", async (req, res) => {
  try {
    const { user_question, structured_data, session_id, instructions } = req.body;

    if (!user_question || !session_id) {
      return res.status(400).json({ 
        error: "user_question e session_id são obrigatórios",
        received: { user_question: !!user_question, session_id: !!session_id }
      });
    }

    // Garante que structured_data seja um objeto
    const safeStructuredData = structured_data || {};

    logger.info(`Processando chat para sessão: ${session_id}`);

    const result = await generateResponseViaPython(
      user_question, 
      safeStructuredData, 
      session_id, 
      instructions || ""
    );

    if (result.success) {
      res.json({
        response: result.response,
        session_id: result.session_id,
        timestamp: new Date().toISOString()
      });
    } else {
      res.status(500).json({
        error: result.error || "Erro na geração de resposta",
        session_id: session_id
      });
    }

  } catch (error) {
    logger.error("Erro no endpoint /api/chat:", error);
    res.status(500).json({ 
      error: "Erro interno do servidor",
      details: error.message 
    });
  }
});

// Rota para obter estatísticas do cache (proxy para API Python)
app.get("/api/cache/stats", async (req, res) => {
  try {
    const response = await axios.get(`${PYTHON_API_URL}/cache/stats`, { timeout: 5000 });
    res.json(response.data);
  } catch (error) {
    logger.error("Erro ao obter estatísticas do cache:", error.message);
    res.status(500).json({ 
      error: "Erro ao obter estatísticas do cache",
      details: error.message 
    });
  }
});

// Rota para invalidar cache (proxy para API Python)
app.post("/api/cache/invalidate", async (req, res) => {
  try {
    const response = await axios.post(`${PYTHON_API_URL}/cache/invalidate`, req.body, { timeout: 5000 });
    res.json(response.data);
  } catch (error) {
    logger.error("Erro ao invalidar cache:", error.message);
    res.status(500).json({ 
      error: "Erro ao invalidar cache",
      details: error.message 
    });
  }
});

// Middleware de tratamento de erros
app.use((error, req, res, next) => {
  logger.error("Erro não tratado:", error);
  res.status(500).json({
    error: "Erro interno do servidor",
    message: process.env.NODE_ENV === "development" ? error.message : "Erro interno"
  });
});

// Middleware para rotas não encontradas
app.use((req, res) => {
  logger.warn(`Rota não encontrada: ${req.method} ${req.path}`);
  res.status(404).json({
    error: "Rota não encontrada",
    path: req.path,
    method: req.method,
    available_routes: [
      "GET /",
      "GET /chatbot",
      "GET /health",
      "POST /api/extract",
      "POST /api/chat",
      "GET /api/cache/stats",
      "POST /api/cache/invalidate"
    ]
  });
});

// Inicialização do servidor
async function startServer() {
  try {
    // Verifica conectividade com API Python
    const pythonApiHealthy = await checkPythonApiHealth();
    
    if (!pythonApiHealthy) {
      logger.warn("⚠️  API Python não está respondendo. Algumas funcionalidades podem não funcionar.");
      logger.warn(`   Verifique se a API Python está rodando em: ${PYTHON_API_URL}`);
    } else {
      logger.info("✅ API Python está online e respondendo.");
    }

    app.listen(PORT, "0.0.0.0", () => {
      logger.info(`🚀 Servidor Node.js rodando na porta ${PORT}`);
      logger.info(`📱 Painel de controle: http://localhost:${PORT}`);
      logger.info(`🤖 Interface do chatbot: http://localhost:${PORT}/chatbot`);
      logger.info(`🔗 API Python configurada para: ${PYTHON_API_URL}`);
      logger.info(`📊 Verificação de saúde: http://localhost:${PORT}/health`);
      
      // Log das variáveis de ambiente importantes
      logger.info("🔧 Configurações:");
      logger.info(`   NODE_ENV: ${process.env.NODE_ENV || "development"}`);
      logger.info(`   LOG_LEVEL: ${process.env.LOG_LEVEL || "info"}`);
      logger.info(`   PYTHON_API_URL: ${PYTHON_API_URL}`);
    });

  } catch (error) {
    logger.error("Erro ao iniciar servidor:", error);
    process.exit(1);
  }
}

// Tratamento de sinais para shutdown graceful
process.on('SIGTERM', () => {
  logger.info('Recebido SIGTERM. Encerrando servidor graciosamente...');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('Recebido SIGINT. Encerrando servidor graciosamente...');
  process.exit(0);
});

// Tratamento de erros não capturados
process.on('uncaughtException', (error) => {
  logger.error('Erro não capturado:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Promise rejeitada não tratada:', { reason, promise });
  process.exit(1);
});

// Iniciar servidor
startServer();

