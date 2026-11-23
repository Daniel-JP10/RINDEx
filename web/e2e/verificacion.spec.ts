import { expect, test } from "@playwright/test";

const ANCHOS: ReadonlyArray<{ nombre: string; width: number; height: number }> = [
  { nombre: "escritorio 1440 px", width: 1440, height: 900 },
  { nombre: "movil 390 px", width: 390, height: 844 },
];

const SECCIONES_CON_VISTA: ReadonlyArray<{ id: string; testIdEsperado?: string }> = [
  { id: "panorama" },
  { id: "el_golpe" },
  { id: "mapa_brecha" },
  { id: "por_que_rinde_menos", testIdEsperado: "grafico-pesas" },
  { id: "lo_que_no_sabemos", testIdEsperado: "panel-calidad" },
  { id: "matriz", testIdEsperado: "grafico-matriz" },
  { id: "simula", testIdEsperado: "simulador-escenarios" },
  { id: "prioriza", testIdEsperado: "tabla-prioridad" },
  { id: "conexion_la_mojana" },
  { id: "metodologia", testIdEsperado: "panel-metodologia" },
];

for (const vista of ANCHOS) {
  test.describe(`Verificacion visual y maquetacion en ${vista.nombre}`, () => {
    test.use({ viewport: { width: vista.width, height: vista.height } });

    test("no presenta desbordamiento horizontal y ningun panel se superpone en portada ni tablero", async ({
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

      const cajaVisual = await page.getByTestId("panel-fijo").boundingBox();
      const cajaNarrativa = await page.locator(".tablero-narrativa").boundingBox();
      expect(cajaVisual).not.toBeNull();
      expect(cajaNarrativa).not.toBeNull();
      if (cajaVisual && cajaNarrativa) {
        const sepH =
          cajaNarrativa.x + cajaNarrativa.width <= cajaVisual.x + 1 ||
          cajaVisual.x + cajaVisual.width <= cajaNarrativa.x + 1;
        const sepV =
          cajaVisual.y + cajaVisual.height <= cajaNarrativa.y + 1 ||
          cajaNarrativa.y + cajaNarrativa.height <= cajaVisual.y + 1;
        expect(sepH || sepV).toBe(true);
      }
    });

    test("el pie de pagina es el ultimo elemento y no deja espacio vacio debajo", async ({
      page,
    }) => {
      await page.goto("/", { waitUntil: "networkidle" });
      await expect(page.getByTestId("frase-gancho-portada")).toBeVisible();

      await page.evaluate(() => {
        window.scrollTo({ top: document.documentElement.scrollHeight, behavior: "instant" });
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

      await page.getByRole("button", { name: "Arroz 2021", exact: true }).click();
      await page.waitForTimeout(800);

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

      const scrollOk = await page.evaluate(
        () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
      );
      expect(scrollOk).toBe(true);
    });

    test("los filtros, linea de tiempo, simulador y tabla de prioridad operan sin desbordamiento", async ({
      page,
    }) => {
      await page.goto("/", { waitUntil: "networkidle" });
      await expect(page.getByTestId("kpi-produccion")).toBeVisible();

      const prodInicial = await page.getByTestId("kpi-produccion").textContent();

      /* Filtrar por Cordoba (23) */
      await page.getByTestId("filtro-departamento").selectOption("23");
      await page.waitForTimeout(200);
      const prodCordoba = await page.getByTestId("kpi-produccion").textContent();
      expect(prodCordoba).not.toBe(prodInicial);
      const atenuados = await page.locator('path.municipio-ruta[data-atenuado="true"]').count();
      expect(atenuados).toBeGreaterThan(100);

      /* Filtrar por cuadrante Tecnificar */
      await page.getByTestId("filtro-cuadrante").selectOption("tecnificar");
      await page.waitForTimeout(150);

      /* Seleccionar anio 2021 en la linea de tiempo */
      await page.getByRole("button", { name: "2021", exact: true }).click();
      await page.waitForTimeout(250);
      await expect(page.locator(".mapa-bloque")).toHaveAttribute("data-modo-mapa", "anio");
      await expect(page.getByTestId("mapa-leyenda")).toContainText("Rendimiento 2021");

      /* Limpiar filtros restaura el total regional inicial */
      await page.getByRole("button", { name: "Limpiar filtros" }).click();
      await page.waitForTimeout(150);
      await expect(page.getByTestId("kpi-produccion")).toHaveText(prodInicial ?? "");

      /* Abrir simulador y ajustar deslizador a 50 % */
      await page.getByRole("button", { name: "Escenarios", exact: true }).click();
      await expect(page.getByTestId("simulador-escenarios")).toBeVisible();
      await page.getByTestId("simulador-deslizador").fill("50");
      await expect(page.getByTestId("simulador-pct-valor")).toHaveText("50 %");

      /* Abrir tabla de prioridad y comprobar filas */
      await page.getByRole("button", { name: "Prioridad", exact: true }).click();
      await expect(page.getByTestId("tabla-prioridad")).toBeVisible();
      const filasTabla = await page.locator("tbody tr.fila-prioridad").count();
      expect(filasTabla).toBeGreaterThan(10);

      /* Sin desbordamiento horizontal tras recorrer todas las vistas */
      const scrollOk = await page.evaluate(
        () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
      );
      expect(scrollOk).toBe(true);
    });
  });
}

test("las 11 secciones y todas sus vistas analiticas cargan sin errores ni peticiones externas", async ({
  page,
}) => {
  const erroresConsola: string[] = [];
  const erroresPagina: string[] = [];
  const peticionesExternas: string[] = [];

  page.on("console", (msg) => {
    if (msg.type() === "error") {
      erroresConsola.push(msg.text());
    }
  });
  page.on("pageerror", (err) => {
    erroresPagina.push(err.message);
  });
  page.on("request", (req) => {
    const url = req.url();
    if (!url.startsWith("http://127.0.0.1:") && !url.startsWith("data:")) {
      peticionesExternas.push(url);
    }
  });

  await page.goto("/", { waitUntil: "networkidle" });
  await expect(page.locator("#portada")).toBeVisible();
  await expect(page.getByTestId("frase-gancho-portada")).toContainText("681.536");

  for (const sec of SECCIONES_CON_VISTA) {
    const paso = page.locator(`#${sec.id}`);
    await expect(paso).toBeAttached();
    await paso.click();
    if (sec.testIdEsperado) {
      await expect(page.getByTestId(sec.testIdEsperado)).toBeVisible();
    }
    await page.waitForTimeout(150);
  }

  /* Probar tambien cambio a Yuca y Maiz */
  await page.locator('.pildora-cultivo[data-cultivo="Yuca"]').click();
  await page.waitForTimeout(200);
  await page.locator('.pildora-cultivo[data-cultivo="Maíz"]').click();
  await page.waitForTimeout(200);

  expect(erroresConsola, `Errores de consola: ${erroresConsola.join("; ")}`).toEqual([]);
  expect(erroresPagina, `Errores de pagina: ${erroresPagina.join("; ")}`).toEqual([]);
  expect(
    peticionesExternas,
    `Peticiones a dominios externos detectadas: ${peticionesExternas.join(", ")}`,
  ).toEqual([]);
});
