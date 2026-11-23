/* Genera web/public/og.png (1200x630) con Playwright a partir de la portada renderizada */

import path from "node:path";
import { chromium } from "@playwright/test";
import { preview } from "vite";

const PUERTO = 4175;
const RUTA_OG = path.resolve(process.cwd(), "public", "og.png");

async function ejecutar() {
  const servidor = await preview({
    preview: {
      host: "127.0.0.1",
      port: PUERTO,
      strictPort: true,
    },
  });

  try {
    const navegador = await chromium.launch({ headless: true });
    try {
      const contexto = await navegador.newContext({
        viewport: { width: 1200, height: 630 },
        deviceScaleFactor: 1,
      });
      const page = await contexto.newPage();
      await page.goto(`http://127.0.0.1:${PUERTO}`, { waitUntil: "networkidle" });
      await page.waitForSelector('[data-testid="frase-gancho-portada"]');

      /* Ajusta la portada para llenar exactamente 1200x630 como tarjeta editorial OG */
      await page.addStyleTag({
        content: `
          .encabezado, .portada-degradado-salida, .portada-indicador-scroll { display: none !important; }
          .portada { min-height: 630px !important; height: 630px !important; overflow: hidden !important; justify-content: center !important; }
          .portada-rejilla { padding: 32px 48px !important; gap: 32px !important; }
          .portada-mapa-svg { max-height: 490px !important; }
          .portada-titulo { font-size: 3.1rem !important; }
        `,
      });
      await page.waitForTimeout(1400);
      await page.screenshot({
        path: RUTA_OG,
        clip: { x: 0, y: 0, width: 1200, height: 630 },
      });
      console.info(`[og] Imagen generada en ${RUTA_OG} (1200x630)`);
      await contexto.close();
    } finally {
      await navegador.close();
    }
  } finally {
    await new Promise((resolve) => {
      servidor.httpServer.close(() => resolve());
    });
  }
}

ejecutar()
  .then(() => process.exit(0))
  .catch((err) => {
    console.error(err);
    process.exit(1);
  });
