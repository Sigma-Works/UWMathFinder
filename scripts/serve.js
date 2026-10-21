#!/usr/bin/env node
/**
 * serve.js — tiny static file server for local testing (Lighthouse, spot-check page).
 * `node scripts/serve.js [port]` serves the repo root. A POST to /eval/spotcheck.json or
 * /eval/retrieval_queries.json writes the request body to that file, which is how the spot-check
 * and query-review pages save.
 */
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');
const port = Number(process.argv[2]) || 8000;
const WRITABLE = ['/eval/spotcheck.json', '/eval/retrieval_queries.json'];
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.png': 'image/png', '.svg': 'image/svg+xml', '.pdf': 'application/pdf',
  '.onnx': 'application/octet-stream', '.bin': 'application/octet-stream', '.wasm': 'application/wasm',
  '.woff2': 'font/woff2', '.txt': 'text/plain', '.xml': 'application/xml' };

http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  if (req.method === 'POST' && WRITABLE.includes(url)) {
    let body = '';
    req.on('data', c => { body += c; });
    req.on('end', () => {
      try { JSON.parse(body); } catch { res.writeHead(400); return res.end('bad json'); }
      fs.writeFileSync(path.join(root, url), body);
      res.writeHead(200); res.end('saved');
    });
    return;
  }
  let file = path.join(root, url);
  if (!file.startsWith(root)) { res.writeHead(403); return res.end(); }
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); return res.end('not found'); }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' });
    res.end(data);
  });
}).listen(port, () => console.log(`Serving ${root} at http://localhost:${port}/`));
