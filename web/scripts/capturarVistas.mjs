/* Toma capturas visuales en 1440 px y 390 px de las vistas clave de RINDEx */

import fs from "node:fs";
import path from "node:path";
import { chromium } from "@playwright/test";
import { preview } from "vite";

const PUERTO = 4174;
const DIR_CAPTURAS = path.resolve(process.cwd(), "capturas");

async function ejecutar() {
  fs.mkdirSync(DIR_CAPTURAS, { recursive: true });

  const servidor = await preview({
    preview: {
      host: "127.0.0.1",
      port: PUERTO,
      strictPort: true,
    },
  });

  const urlBase = `http://127.0.0.1:${PUERTO}`;
  const archivosGenerados = [];

  try {
    const navegador = await chromium.launch({ headless: true });

    try {
      const vistas = [
        { sufijo: "1440", width: 1440, height: 900 },
        { sufijo: "390", width: 390, height: 844 },
      ];

      for (const vista of vistas) {
        const contexto = await navegador.newContext({
          viewport: { width: vista.width, height: vista.height },
          deviceScaleFactor: 1,
        });
        const page = await contexto.newPage();
        await page.goto(urlBase, { waitUntil: "networkidle" });
        await page.waitForSelector('[data-testid="frase-gancho-portada"]');
        await page.waitForTimeout(1400);

        const guardar = async (nombre) => {
          const destino = path.join(DIR_CAPTURAS, `${nombre}_${vista.sufijo}.png`);
          await page.screenshot({ path: destino, fullPage: false });
          archivosGenerados.push(path.relative(path.resolve(process.cwd(), ".."), destino));
        };

        /* 1. Portada */
        await page.evaluate(() => window.scrollTo(0, 0));
        await page.waitForTimeout(250);
        await guardar("portada");

        /* 2. Panorama */
        await page.locator("#panorama").scrollIntoViewIfNeeded();
        await page.locator("#panorama").click();
        await page.waitForTimeout(450);
        await guardar("panorama");

        /* 3. El golpe con acercamiento a La Mojana */
        await page.locator("#el_golpe").scrollIntoViewIfNeeded();
        await page.locator("#el_golpe").click();
        await page.waitForTimeout(900);
        await guardar("el_golpe");

        /* 4. Mapa de brecha con ficha municipal abierta */
        await page.locator("#mapa_brecha").scrollIntoViewIfNeeded();
        await page.locator("#mapa_brecha").click();
        await page.waitForTimeout(600);
        const entrada = page.getByRole("combobox", { name: /Buscar municipio/i });
        await entrada.click();
        await entrada.fill("Ciénaga de Oro");
        await entrada.press("Enter");
        await page.waitForSelector('[data-testid="ficha-municipal"]');
        await page.waitForTimeout(500);
        await guardar("mapa_brecha_ficha");

        /* 5. Pie de pagina */
        await page.evaluate(() => {
          window.scrollTo(0, document.documentElement.scrollHeight);
        });
        await page.waitForTimeout(400);
        await guardar("pie_pagina");

        await contexto.close();
      }
    } finally {
      await navegador.close();
    }
  } finally {
    await new Promise((resolve) => {
      servidor.httpServer.close(() => resolve());
    });
  }

  for (const ruta of archivosGenerados) {
    console.info(`[captura] ${ruta}`);
  }
}

ejecutar()
  .then(() => {
    process.exit(0);
  })
  .catch((err) => {
    console.error(err);
    process.exit(1);
  });
