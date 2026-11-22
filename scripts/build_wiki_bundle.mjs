#!/usr/bin/env node
/**
 * Build script for Vercel deployment:
 * 1. Recursively reads ONLY wiki/**\/*.md (strictly forbidden to read raw/).
 * 2. Runs a safety check (0 raw/ paths, 0 PII patterns) and writes api/_wiki_bundle.json.
 * 3. Copies slides/nccu-new-leader-quickstart/deck.html -> public/deck.html so the
 *    deployed web app header link works out of the box on Vercel.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "..");
const WIKI_DIR = path.join(REPO_ROOT, "wiki");
const OUT_BUNDLE = path.join(REPO_ROOT, "api", "_wiki_bundle.json");
const SRC_DECK = path.join(REPO_ROOT, "slides", "nccu-new-leader-quickstart", "deck.html");
const OUT_DECK = path.join(REPO_ROOT, "public", "deck.html");

const PUBLIC_HOTLINES = ["0800-119-119", "0800-018-111"];
const PII_CHECKS = [
  ["taiwan_mobile", /(?<!\d)09\d{2}[-\s]?\d{3}[-\s]?\d{3}(?!\d)/g],
  ["taiwan_national_id", /(?<![A-Za-z0-9])[A-Z][1289]\d{8}(?!\d)/g],
  ["bank_account", /(?<!\d)\d{7}-\d{7}(?!\d)/g],
];

function collectMarkdownFiles(dir, results = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  entries.sort((a, b) => a.name.localeCompare(b.name));
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      collectMarkdownFiles(fullPath, results);
    } else if (entry.isFile() && entry.name.toLowerCase().endsWith(".md")) {
      results.push(fullPath);
    }
  }
  return results;
}

function main() {
  if (!fs.existsSync(WIKI_DIR)) {
    console.error(`[build_wiki_bundle] ERROR: wiki/ directory not found at ${WIKI_DIR}`);
    process.exit(1);
  }

  const mdPaths = collectMarkdownFiles(WIKI_DIR);
  const documents = [];
  let totalChars = 0;

  for (const fullPath of mdPaths) {
    const relPath = path.relative(REPO_ROOT, fullPath).split(path.sep).join("/");

    // Hard safety guard: strictly wiki/ only, never raw/
    if (!relPath.startsWith("wiki/") || relPath.includes("raw/")) {
      console.error(`[build_wiki_bundle] SECURITY ABORT: Illegal path detected: ${relPath}`);
      process.exit(1);
    }

    const content = fs.readFileSync(fullPath, "utf8");

    // Safety PII guard
    let sanitizedCheck = content;
    for (const h of PUBLIC_HOTLINES) {
      sanitizedCheck = sanitizedCheck.replaceAll(h, "");
    }
    for (const [label, regex] of PII_CHECKS) {
      const hits = sanitizedCheck.match(regex);
      if (hits && hits.length > 0) {
        console.error(
          `[build_wiki_bundle] PII ABORT: Detected ${label} (${hits.join(", ")}) in ${relPath}`
        );
        process.exit(1);
      }
    }

    totalChars += content.length;
    documents.push({
      path: relPath,
      chars: content.length,
      content,
    });
  }

  const bundle = {
    generatedAt: new Date().toISOString(),
    sourceRoot: "wiki/",
    docCount: documents.length,
    totalChars,
    documents,
  };

  fs.mkdirSync(path.dirname(OUT_BUNDLE), { recursive: true });
  fs.writeFileSync(OUT_BUNDLE, JSON.stringify(bundle, null, 2), "utf8");

  // Also sync interactive presentation deck.html to public/ if present
  let deckCopied = false;
  if (fs.existsSync(SRC_DECK)) {
    fs.mkdirSync(path.dirname(OUT_DECK), { recursive: true });
    fs.copyFileSync(SRC_DECK, OUT_DECK);
    deckCopied = true;
  }

  console.log("========================================================================");
  console.log(`[build_wiki_bundle] SUCCESS`);
  console.log(`  Output bundle : ${path.relative(REPO_ROOT, OUT_BUNDLE).split(path.sep).join("/")}`);
  console.log(`  Wiki docs     : ${documents.length} files (${totalChars.toLocaleString()} chars)`);
  console.log(`  raw/ included : 0 (strictly excluded)`);
  console.log(`  PII check     : PASS (0 hits)`);
  console.log(`  Deck synced   : ${deckCopied ? "public/deck.html" : "not found (skipped)"}`);
  console.log("  Included files:");
  for (const d of documents) {
    console.log(`    - ${d.path} (${d.chars} chars)`);
  }
  console.log("========================================================================");
}

main();
