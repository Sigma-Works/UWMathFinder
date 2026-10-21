#!/usr/bin/env node
/**
 * build-index.mjs — build the study assistant's search index.
 *
 *   npm run build:index
 *
 * For every question in questions.json, embed docText() (course, chapter, skills,
 * exam, and the transcribed question from questions_text.json when we have it)
 * with the same small model the browser uses, then write:
 *
 *   assets/assistant/index.bin   int8 vectors, one row of DIMS bytes per question
 *   assets/assistant/index.json  manifest: model, dims, ids (row order), which exams
 *                                have worked solutions, and build stats
 *
 * Quantization: each vector is L2-normalized (length 1), so every component is in
 * [-1, 1]; we store round(x * 127) as one signed byte. That's 4x smaller than
 * float32 and cosine ranking barely changes (eval/retrieval.mjs reports both).
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { pipeline } from '@huggingface/transformers';
import { MODEL, DTYPE, docText, chapterNames } from './assistant-text.mjs';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = f => JSON.parse(fs.readFileSync(path.join(root, f), 'utf8'));
const OUT_DIR = path.join(root, 'assets', 'assistant');
const BATCH = 32;

/** Embed a list of strings → array of Float32Array (normalized). */
export async function embedAll(extractor, texts) {
  const out = [];
  for (let i = 0; i < texts.length; i += BATCH) {
    const t = await extractor(texts.slice(i, i + BATCH), { pooling: 'mean', normalize: true });
    const dims = t.dims[1];
    for (let j = 0; j < t.dims[0]; j++) out.push(t.data.slice(j * dims, (j + 1) * dims));
  }
  return out;
}

/** float vector in [-1, 1] → Int8Array */
export function quantize(v) {
  const q = new Int8Array(v.length);
  for (let i = 0; i < v.length; i++) q[i] = Math.max(-127, Math.min(127, Math.round(v[i] * 127)));
  return q;
}

/** Everything the eval also needs: the questions in index order and their doc texts. */
export function loadCorpus() {
  const questions = read('questions.json');
  const names = chapterNames(read('chapters.json'));
  const textById = new Map(read('questions_text.json').map(t => [t.id, t]));
  const docs = questions.map(q => ({
    id: q.id,
    course: q.course,
    text: docText(q, names.get(`${q.course}|${q.chapter}`) || q.chapter, textById.get(q.id)),
    transcribed: textById.has(q.id),
  }));
  return { questions, docs };
}

async function main() {
  const t0 = Date.now();
  const { docs } = loadCorpus();
  const extractor = await pipeline('feature-extraction', MODEL, { dtype: DTYPE });
  const vecs = await embedAll(extractor, docs.map(d => d.text));
  const dims = vecs[0].length;

  const bin = new Int8Array(docs.length * dims);
  vecs.forEach((v, i) => bin.set(quantize(v), i * dims));

  const solutions = fs.readdirSync(path.join(root, 'solutions'))
    .filter(f => f.endsWith('.json')).map(f => f.slice(0, -5)).sort();

  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.writeFileSync(path.join(OUT_DIR, 'index.bin'), Buffer.from(bin.buffer));
  const manifest = {
    model: MODEL, dtype: DTYPE, dims, count: docs.length, quantization: 'int8 (x*127), rows L2-normalized before quantizing',
    transcribed: docs.filter(d => d.transcribed).length,
    ids: docs.map(d => d.id),
    solutions,
  };
  fs.writeFileSync(path.join(OUT_DIR, 'index.json'), JSON.stringify(manifest) + '\n');

  const binSize = fs.statSync(path.join(OUT_DIR, 'index.bin')).size;
  const jsonSize = fs.statSync(path.join(OUT_DIR, 'index.json')).size;
  console.log(`embedded ${docs.length} questions (${manifest.transcribed} with transcribed text), ${dims} dims, in ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  console.log(`index.bin  ${binSize} bytes`);
  console.log(`index.json ${jsonSize} bytes`);
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) await main();
