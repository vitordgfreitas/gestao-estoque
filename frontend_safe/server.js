// Servidor simples para servir o SPA no Render
// Todas as rotas retornam index.html para permitir React Router funcionar

import express from 'express';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const port = process.env.PORT || 10000;

// Serve arquivos estáticos da pasta dist
app.use(express.static(join(__dirname, 'dist')));

// Todas as rotas retornam index.html (SPA routing)
app.get('*', (req, res) => {
  res.sendFile(join(__dirname, 'dist', 'index.html'));
});

app.listen(port, () => {
  console.log(`Servidor rodando na porta ${port}`);
  console.log(`Acesse: http://localhost:${port}`);
});
