/* Audita el contenido de web/dist antes de desplegar en Cloudflare Pages */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const LIMITE_ARCHIVO_BYTES = 25 * 1024 * 1024;
const EXTENSIONES_PROHIBIDAS = new Set([".md", ".map", ".parquet", ".py"]);
const EXTENSIONES_TEXTO = new Set([
  ".html",
  ".js",
  ".mjs",
  ".css",
  ".json",
  ".topojson",
  ".svg",
  ".txt",
  "",
]);

const PATRONES_SENSIBLES = [
  { nombre: "ruta local Windows (C:/)", regex: /[A-Za-z]:[/\\](?:Users|Proyectos|Windows|Program Files)/ },
  { nombre: "ruta local Unix (/home/ o /Users/)", regex: /(?:^|[\s"'`(])(?:\/home\/|\/Users\/)/ },
  { nombre: "correo electronico", regex: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/ },
  {
    nombre: "cadena con forma de token",
    regex: /\b(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{35}|AKIA[0-9A-Z]{16}|xoxb-[A-Za-z0-9-]+|eyJhbGci[A-Za-z0-9._-]{20,})\b/,
  },
];

const dirActual = path.dirname(fileURLToPath(import.meta.url));
const dirDist = path.resolve(dirActual, "..", "dist");

if (!fs.existsSync(dirDist)) {
  console.error("ERROR: no existe web/dist. Ejecute npm run build primero.");
  process.exit(1);
}

function recorrerArchivos(dirBase, dirRel = "") {
  const resultado = [];
  for (const entrada of fs.readdirSync(dirBase, { withFileTypes: true })) {
    const rel = dirRel ? `${dirRel}/${entrada.name}` : entrada.name;
    const abs = path.join(dirBase, entrada.name);
    if (entrada.isDirectory()) {
      if (entrada.name.toLowerCase() === "capturas") {
        resultado.push({ rel, abs, esDirectorioCapturas: true, bytes: 0 });
      }
      resultado.push(...recorrerArchivos(abs, rel));
    } else if (entrada.isFile()) {
      const stat = fs.statSync(abs);
      resultado.push({ rel, abs, esDirectorioCapturas: false, bytes: stat.size });
    }
  }
  return resultado;
}

const entradas = recorrerArchivos(dirDist).sort((a, b) => a.rel.localeCompare(b.rel));
const hallazgosError = [];
let totalBytes = 0;

console.log("=== Inventario de web/dist ===");
for (const item of entradas) {
  if (item.esDirectorioCapturas) {
    hallazgosError.push(`Directorio prohibido encontrado: ${item.rel}`);
    continue;
  }
  totalBytes += item.bytes;
  const kb = (item.bytes / 1024).toFixed(2);
  console.log(`${item.rel} | ${item.bytes} bytes (${kb} KB)`);

  const ext = path.extname(item.rel).toLowerCase();
  if (EXTENSIONES_PROHIBIDAS.has(ext)) {
    hallazgosError.push(`Extension prohibida (${ext}): ${item.rel}`);
  }
  if (item.rel.toLowerCase().includes("capturas")) {
    hallazgosError.push(`Ruta de capturas dentro de dist: ${item.rel}`);
  }
  if (item.bytes > LIMITE_ARCHIVO_BYTES) {
    hallazgosError.push(
      `Archivo supera el limite de 25 MiB (${(item.bytes / (1024 * 1024)).toFixed(2)} MiB): ${item.rel}`,
    );
  }

  if (EXTENSIONES_TEXTO.has(ext)) {
    const contenido = fs.readFileSync(item.abs, "utf-8");
    for (const patron of PATRONES_SENSIBLES) {
      const match = patron.regex.exec(contenido);
      if (match) {
        hallazgosError.push(
          `Patron prohibido [${patron.nombre}] en ${item.rel}: "${match[0]}"`,
        );
      }
    }
  }
}

const totalKb = (totalBytes / 1024).toFixed(2);
const totalMb = (totalBytes / (1024 * 1024)).toFixed(2);
console.log(`=== Total web/dist: ${entradas.length} archivos | ${totalBytes} bytes (${totalKb} KB / ${totalMb} MiB) ===`);

if (hallazgosError.length > 0) {
  console.error("ERRORES DETECTADOS EN web/dist:");
  for (const err of hallazgosError) {
    console.error(`- ${err}`);
  }
  process.exit(1);
}

console.log("VERIFICACION DE dist/ APROBADA: 0 archivos prohibidos, 0 fugas, todos <= 25 MiB.");
