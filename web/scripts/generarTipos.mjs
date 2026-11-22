import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { compile } from "json-schema-to-typescript";

const dirActual = path.dirname(fileURLToPath(import.meta.url));
const dirWeb = path.resolve(dirActual, "..");
const dirEsquemas = path.resolve(dirWeb, "..", "contratos", "web");
const dirSalida = path.resolve(dirWeb, "src", "tipos", "generados");

fs.mkdirSync(dirSalida, { recursive: true });

const archivosEsquema = fs
  .readdirSync(dirEsquemas)
  .filter((nombre) => nombre.endsWith(".schema.json"))
  .sort();

const cabecera = [
  "/* Archivo generado automaticamente desde contratos/web/ mediante npm run gen:tipos. */",
  "/* No editar a mano. */",
  "",
].join("\n");

const exportacionesIndice = [];

for (const archivo of archivosEsquema) {
  const rutaCompleta = path.join(dirEsquemas, archivo);
  const esquema = JSON.parse(fs.readFileSync(rutaCompleta, "utf-8"));
  delete esquema.title;
  const base = archivo.replace(".schema.json", "");
  const nombreCamel = base
    .split("_")
    .map((parte) => parte.charAt(0).toUpperCase() + parte.slice(1))
    .join("");
  const nombreTipo = `Contrato${nombreCamel}`;

  const contenidoTs = await compile(esquema, nombreTipo, {
    bannerComment: cabecera.trimEnd(),
    additionalProperties: false,
    strictIndexSignatures: true,
    ignoreMinAndMaxItems: true,
    style: {
      singleQuote: false,
    },
  });

  const archivoDestino = `${base}.ts`;
  fs.writeFileSync(path.join(dirSalida, archivoDestino), contenidoTs, "utf-8");
  exportacionesIndice.push(`export type { ${nombreTipo} } from "./${base}.ts";`);
}

fs.writeFileSync(
  path.join(dirSalida, "index.ts"),
  `${cabecera}${exportacionesIndice.join("\n")}\n`,
  "utf-8",
);

console.log(`Tipos generados en src/tipos/generados/: ${archivosEsquema.length} esquemas.`);
