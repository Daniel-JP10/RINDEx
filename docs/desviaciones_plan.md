# Registro de desviaciones y precisiones al plan de análisis — RINDEx (Región Caribe 2019-2025)

- **Fecha de registro**: 2026-11-22
- **Edición**: `caribe_2019_2025`
- **Estado**: documentado y versionado tras el perfilado de limpieza/agregación y antes de ejecutar cualquier prueba inferencial (`H1` a `H5`, `E1`, `E2`).

Este documento registra cinco precisiones y desviaciones metodológicas respecto a `docs/plan_analisis.md`, adoptadas a partir de la estructura observada en las tablas agregadas (tamaños muestrales de pares/tripletas y persistencia de desfases de área) sin haber calculado aún ningún estadístico de prueba ni valor $p$.

## D1. Independencia de observaciones en H2 y H3 (unidad municipal vs. municipio-año)

- **Motivación**: en los diseños pareados entre sistemas productivos dentro de un mismo municipio a lo largo de varios años (`H2` en maíz con 375 pares en 61 municipios, y `H3` en arroz), tratar cada par `(codigo_dane_municipio, anio)` como una observación independiente en la prueba de rangos con signo de Wilcoxon subestima la varianza debido a la autocorrelación intramunicipal entre años.
- **Decisión**: en la **prueba principal** de `H2` y de cada comparación por pares de `H3`, la unidad de análisis independiente es el **municipio**. Para cada municipio con al menos un año con ambos sistemas activos ($\text{Área cosechada} > 0$), se calcula primero el promedio intramunicipal de las diferencias logarítmicas anuales entre los dos sistemas:

$$\bar{d}_i = \frac{1}{|T_i|} \sum_{t \in T_i} \ln\left(\frac{y_{i,t}^{(A)}}{y_{i,t}^{(B)}}\right)$$

Sobre los valores municipales $\bar{d}_i$ se aplican la prueba de rangos con signo de Wilcoxon, el estimador de ubicación de Hodges-Lehmann (reportado en escala de razón como $\exp(\hat{\Delta}_{\text{HL}})$) y el intervalo de confianza bootstrap al 95 % remuestreando municipios completos. El análisis agrupando directamente todos los pares `(codigo_dane_municipio, anio)` se conserva y reporta explícitamente como **variante de sensibilidad** en el módulo de robustez.

## D2. Prueba principal en H3 (arroz) ante tamaño muestral de tripletas completas

- **Motivación**: la validación de agregación (`docs/validacion_limpieza.md`) mostró que en toda la Región Caribe 2019-2025 existen únicamente **19 tripletas** `(codigo_dane_municipio, anio)` con los tres sistemas de arroz (`riego`, `secano_mecanizado`, `secano_manual`) simultáneamente activos, cifra inferior al umbral operativo de 30 bloques completos, mientras que por pares de sistemas existen 25, 59 y 209 municipio-años disponibles.
- **Decisión**: conforme a la cláusula prevista en la sección 3 (`H3`) de `docs/plan_analisis.md`, cuando hay menos de 30 tripletas la **prueba confirmatoria principal** de la familia `H3` pasa a ser el conjunto de las **tres comparaciones pareadas de Wilcoxon** (`riego` vs. `secano_mecanizado`, `riego` vs. `secano_manual`, y `secano_mecanizado` vs. `secano_manual`) agregadas a nivel municipal según `D1` y corregidas por multiplicidad mediante **Holm**. La prueba ómnibus de **Friedman** (con $W$ de Kendall) sobre los bloques con los tres sistemas se ejecuta y reporta como **análisis complementario**.

## D3. Interpretación agronómica de la tasa de área no cosechada en yuca

- **Motivación**: a diferencia del maíz y el arroz (ciclos transitorios cortos de 3 a 5 meses), la yuca presenta un ciclo vegetativo largo (8 a 14 meses) que con frecuencia trasciende el corte del año calendario entre siembra y cosecha.
- **Decisión**: la tasa anual de área no cosechada en yuca ($(\text{Área sembrada} - \text{Área cosechada}) / \text{Área sembrada}$) se interpreta y documenta estrictamente como **posible efecto del desfase por ciclo largo del cultivo** entre años o semestres consecutivos, y nunca como pérdida física de superficie cultivada.

## D4. Tratamiento en E2 de municipios con área cosechada acumulada mayor que el área sembrada

- **Motivación**: en la tabla `periodo_municipio_cultivo` persisten 59 combinaciones municipio-cultivo cuyo acumulado total 2019-2025 registra $\sum \text{Área cosechada} > \sum \text{Área sembrada}$ (tasa acumulada de área no cosechada negativa), producto de inconsistencias administrativas de reporte de área sembrada en EVA tras el cambio operativo de 2022.
- **Decisión**: los municipios-cultivo cuyo acumulado 2019-2025 presenta $\text{Área cosechada} > \text{Área sembrada}$ quedan marcados explícitamente con una bandera de anomalía de balance de área y **se excluyen de la comparación pareada intramunicipal de `E2`** (tasa de área no cosechada 2019-2021 vs. 2022-2025), evitando que tasas negativas artificiales distorsionen la prueba sobre el quiebre metodológico. De igual forma, dentro de cada subperiodo de `E2` solo se evalúan tasas válidas en $[0, 1]$ (donde $\text{Área sembrada} \ge \text{Área cosechada}$ y $\text{Área sembrada} > 0$).

## D5. Regla de clasificación ENSO preespecificada en la configuración

- **Motivación**: evitar grados de libertad del investigador al definir años El Niño, La Niña y neutros para la hipótesis exploratoria `E1`.
- **Decisión**: la regla de clasificación climática se fija íntegramente en `config/caribe_2019_2025.yaml` antes de cruzar con los datos de rendimiento:
  - Fuente oficial: serie ASCII del índice ONI (Oceanic Niño Index, ERSST.v5 en la región Niño 3.4) de NOAA CPC (`https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt`).
  - Umbral absoluto: $0{,}5\ ^\circ\text{C}$.
  - Regla anual: para cada año calendario se calcula `oni_anual` como la media aritmética de las 12 temporadas móviles trimestrales (`DJF` a `NDJ`) de ese año. El año se clasifica como **Niña** si $\text{oni\_anual} \le -0{,}5$, **Niño** si $\text{oni\_anual} \ge 0{,}5$, y **neutro** cuando $-0{,}5 < \text{oni\_anual} < 0{,}5$. Adicionalmente se contabilizan para cada año el número de temporadas móviles con $\text{ONI} \le -0{,}5$ (`temporadas_nina`) y con $\text{ONI} \ge 0{,}5$ (`temporadas_nino`).
