import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import { fileURLToPath } from "node:url";

const LIMITE_BYTES_GZIP = 200 * 1024;
const dirActual = path.dirname(fileURLToPath(import.meta.url));
const dirDist = path.resolve(dirActual, "..", "dist");
const rutaHtml = path.join(dirDist, "index.html");

if (!fs.existsSync(rutaHtml)) {
  console.error("No existe dist/index.html. Ejecute vite build primero.");
  process.exit(1);
}

const html = fs.readFileSync(rutaHtml, "utf-8");
const coincidenciaScripts = [...html.matchAll(/<script[^>]+src="([^"]+)"/g)];
const coincidenciaPreload = [...html.matchAll(/<link[^>]+rel="modulepreload"[^>]+href="([^"]+)"/g)];

const rutasJs = new Set([
  ...coincidenciaScripts.map((m) => m[1].replace(/^\//, "")),
  ...coincidenciaPreload.map((m) => m[1].replace(/^\//, "")),
]);

if (rutasJs.size === 0) {
  console.error("No se detectaron paquetes JS iniciales en dist/index.html.");
  process.exit(1);
}

let totalGzip = 0;
let totalCrudo = 0;

for (const rutaRel of rutasJs) {
  const rutaAbs = path.join(dirDist, rutaRel);
  if (!fs.existsSync(rutaAbs) || !rutaRel.endsWith(".js")) {
    continue;
  }
  const contenido = fs.readFileSync(rutaAbs);
  const comprimido = zlib.gzipSync(contenido, { level: 9 });
  totalCrudo += contenido.length;
  totalGzip += comprimido.length;
  console.log(
    `JS inicial: ${rutaRel} | crudo=${(contenido.length / 1024).toFixed(2)} KB | gzip=${(comprimido.length / 1024).toFixed(2)} KB`,
  );
}

console.log(
  `Total JS inicial gzip: ${(totalGzip / 1024).toFixed(2)} KB (${totalGzip} bytes, crudo=${(totalCrudo / 1024).toFixed(2)} KB). Limite: 200.00 KB.`,
);

if (totalGzip > LIMITE_BYTES_GZIP) {
  console.error(
    `ERROR: el JavaScript inicial comprimido con gzip (${(totalGzip / 1024).toFixed(2)} KB) supera el limite de 200 KB.`,
  );
  process.exit(1);
}
