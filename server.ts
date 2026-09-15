import express from 'express';
import cors from 'cors';
import path from 'path';
import multer from 'multer';
import { createServer as createViteServer } from 'vite';
import { documentStorage } from './server/storage';
import { processAgentQuery } from './server/agent';

// Ensure Vite dev server inlines /api/v1 rather than any stale localhost:8000
process.env.VITE_API_BASE_URL = '/api/v1';

async function startServer() {
  const app = express();
  const PORT = 3000;

  // Basic middleware
  app.use(cors());
  app.use(express.json());

  // Multer setup for document uploads
  const upload = multer({
    storage: multer.memoryStorage(),
    limits: { fileSize: 10 * 1024 * 1024 },
  });

  // Health check
  app.get('/health', (req, res) => {
    res.json({ status: 'ok', project: 'Intelli-CA' });
  });

  // --- Document Routes ---
  app.get(['/api/v1/documents', '/api/v1/documents/'], (req, res) => {
    const skip = parseInt(req.query.skip as string, 10) || 0;
    const limit = parseInt(req.query.limit as string, 10) || 100;
    const docs = documentStorage.listDocuments(skip, limit);
    res.json(docs);
  });

  app.post('/api/v1/documents/upload', upload.single('file'), (req, res) => {
    const file = req.file;
    if (!file) {
      return res.status(400).json({ detail: 'No file provided' });
    }

    const allowedExtensions = ['.pdf', '.docx', '.xlsx'];
    const originalname = file.originalname || '';
    const hasValidExt = allowedExtensions.some((ext) =>
      originalname.toLowerCase().endsWith(ext)
    );

    if (!hasValidExt) {
      return res.status(400).json({
        detail: 'Invalid file extension. Only PDF, DOCX, and XLSX are allowed.',
      });
    }

    try {
      const doc = documentStorage.saveDocument(file);
      res.json(doc);
    } catch (err: any) {
      res.status(500).json({ detail: err.message || 'Failed to upload document' });
    }
  });

  app.get('/api/v1/documents/:id', (req, res) => {
    const docId = parseInt(req.params.id, 10);
    const doc = documentStorage.getDocument(docId);
    if (!doc) {
      return res.status(404).json({ detail: 'Document not found' });
    }
    res.json(doc);
  });

  app.delete('/api/v1/documents/:id', (req, res) => {
    const docId = parseInt(req.params.id, 10);
    const success = documentStorage.deleteDocument(docId);
    if (!success) {
      return res.status(404).json({ detail: 'Document not found' });
    }
    res.json({ message: 'Document deleted successfully' });
  });

  app.post('/api/v1/documents/:id/process', (req, res) => {
    const docId = parseInt(req.params.id, 10);
    const success = documentStorage.processDocument(docId);
    if (!success) {
      return res.status(404).json({ detail: 'Document not found' });
    }
    res.json({ message: 'Document processed successfully', document_id: docId });
  });

  app.post('/api/v1/documents/search', (req, res) => {
    const { query, limit } = req.body || {};
    const results = documentStorage.search(query || '', limit || 5);
    res.json(results);
  });

  // --- Agent & RAG Routes ---
  app.post('/api/v1/agent/query', async (req, res) => {
    try {
      const { query, limit, filters } = req.body || {};
      if (!query) {
        return res.status(400).json({ detail: 'Query is required' });
      }
      const response = await processAgentQuery({ query, limit, filters });
      res.json(response);
    } catch (err: any) {
      res.status(500).json({ detail: err.message || 'Agent query failed' });
    }
  });

  app.post('/api/v1/chat', async (req, res) => {
    const { content, session_id } = req.body || {};
    const sessionId = session_id || Date.now();
    try {
      const agentRes = await processAgentQuery({ query: content || '' });
      res.json({
        content: agentRes.answer,
        role: 'assistant',
        session_id: sessionId,
      });
    } catch (err: any) {
      res.status(500).json({ detail: err.message || 'Chat generation failed' });
    }
  });

  app.post('/api/v1/rag/query', async (req, res) => {
    const { query, limit } = req.body || {};
    try {
      const agentRes = await processAgentQuery({ query: query || '', limit });
      res.json({
        answer: agentRes.answer,
        citations: agentRes.citations,
        is_sufficient: agentRes.citations.length > 0,
      });
    } catch (err: any) {
      res.status(500).json({ detail: err.message || 'RAG query failed' });
    }
  });

  // --- Vite Dev Middleware or Static File Serving ---
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*all', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
