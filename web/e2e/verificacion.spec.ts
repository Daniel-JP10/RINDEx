import { expect, test } from "@playwright/test";

const ANCHOS: ReadonlyArray<{ nombre: string; width: number; height: number }> = [
  { nombre: "escritorio 1440 px", width: 1440, height: 900 },
  { nombre: "movil 390 px", width: 390, height: 844 },
];

for (const vista of ANCHOS) {
  test.describe(`Verificacion visual y maquetacion en ${vista.nombre}`, () => {
    test.use({ viewport: { width: vista.width, height: vista.height } });

    test("no presenta desbordamiento horizontal y la portada no superpone texto sobre el mapa", async ({
      page,
    }) => {
      await page.goto("/", { waitUntil: "networkidle" });
      await expect(page.getByTestId("frase-gancho-portada")).toContainText("681.536");

      const medidas = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        innerWidth: window.innerWidth,
      }));
      expect(medidas.scrollWidth).toBeLessThanOrEqual(medidas.clientWidth);
      expect(medidas.scrollWidth).toBeLessThanOrEqual(medidas.innerWidth);

      const cajaTexto = await page.getByTestId("portada-bloque-texto").boundingBox();
      const cajaMapa = await page.getByTestId("portada-bloque-mapa").boundingBox();
      expect(cajaTexto).not.toBeNull();
      expect(cajaMapa).not.toBeNull();

      if (cajaTexto && cajaMapa) {
        const separadosHorizontal = cajaTexto.x + cajaTexto.width <= cajaMapa.x + 1;
        const separadosVertical = cajaTexto.y + cajaTexto.height <= cajaMapa.y + 1;
        expect(separadosHorizontal || separadosVertical).toBe(true);
      }
    });

    test("el pie de pagina es el ultimo elemento y no deja espacio vacio debajo", async ({
      page,
    }) => {
      await page.goto("/", { waitUntil: "networkidle" });
      await expect(page.getByTestId("frase-gancho-portada")).toBeVisible();

      await page.evaluate(() => {
        window.scrollTo(0, document.documentElement.scrollHeight);
      });
      await page.waitForTimeout(200);

      const infoPie = await page.evaluate(() => {
        const app = document.querySelector(".aplicacion-rindex");
        const ultimo = app?.lastElementChild;
        const pie = document.querySelector("footer.pie-pagina");
        if (!pie || !ultimo) {
          return null;
        }
        const rectPie = pie.getBoundingClientRect();
        const fondoPieEnDoc = rectPie.bottom + window.scrollY;
        const altoDocumento = document.documentElement.scrollHeight;
        return {
          esUltimoElemento: ultimo === pie,
          diferenciaFinalPx: Math.abs(altoDocumento - fondoPieEnDoc),
        };
      });

      expect(infoPie).not.toBeNull();
      expect(infoPie?.esUltimoElemento).toBe(true);
      expect(infoPie?.diferenciaFinalPx ?? 999).toBeLessThanOrEqual(4);
    });

    test("en el_golpe cambia el cultivo activo a Arroz y la leyenda permanece visible dentro del panel", async ({
      page,
    }) => {
      await page.goto("/", { waitUntil: "networkidle" });
      await expect(page.getByTestId("frase-gancho-portada")).toBeVisible();

      const pasoGolpe = page.locator("#el_golpe");
      await pasoGolpe.scrollIntoViewIfNeeded();
      await pasoGolpe.click();
      await page.waitForTimeout(850);

      const botonArroz = page.locator('.pildora-cultivo[data-cultivo="Arroz"]');
      await expect(botonArroz).toHaveAttribute("aria-pressed", "true");

      const rectPanel = await page.getByTestId("panel-fijo").boundingBox();
      const rectLeyenda = await page.getByTestId("mapa-leyenda").boundingBox();
      expect(rectPanel).not.toBeNull();
      expect(rectLeyenda).not.toBeNull();

      if (rectPanel && rectLeyenda) {
        expect(rectLeyenda.y).toBeGreaterThanOrEqual(rectPanel.y - 1);
        expect(rectLeyenda.y + rectLeyenda.height).toBeLessThanOrEqual(
          rectPanel.y + rectPanel.height + 2,
        );
        expect(rectLeyenda.x).toBeGreaterThanOrEqual(rectPanel.x - 1);
        expect(rectLeyenda.x + rectLeyenda.width).toBeLessThanOrEqual(
          rectPanel.x + rectPanel.width + 2,
        );
      }

      /* Verificar tambien sin desbordamiento horizontal despues del acercamiento */
      const scrollOk = await page.evaluate(
        () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
      );
      expect(scrollOk).toBe(true);
    });
  });
}
