# Plan de análisis preespecificado — RINDEx (Región Caribe 2019-2025)

En este documetno defino las decisiones metodológicas, criterios de elegibilidad, hipótesis confirmatorias y exploratorias, métricas de brecha potencial y pruebas de robustez de la primera edición de RINDEx antes de ejecutar cualquier análisis inferencial.

## 1. Unidad de análisis

La unidad de análisis primaria es la combinación de **municipio, cultivo, sistema productivo y año** (`codigo_dane_municipio`, `cultivo`, `sistema`, `anio`). En cualquier nivel de agregación (anual, multianual, municipal, departamental o regional), el rendimiento se calcula exclusivamente como la suma de la producción dividida entre la suma del área cosechada:

$$\text{Rendimiento agregado} = \frac{\sum \text{Producción}}{\sum \text{Área cosechada}}$$

Nunca se promedia aritméticamente la columna `rendimiento` reportada en los registros semestrales o desagregados.

## 2. Elegibilidad y umbrales de muestra

Un municipio-cultivo (o municipio-cultivo-sistema, según el análisis) se considera elegible en el escenario base cuando cumple simultáneamente:

- **Área cosechada acumulada** en el periodo 2019-2025 de al menos **500 ha**.
- **Persistencia temporal** de al menos **4 años con dato** de área cosechada positiva dentro de la ventana 2019-2025.

Para evaluar la sensibilidad de las conclusiones al criterio de escala productiva, todos los análisis se replican con umbrales alternativos de **300 ha** y **1.000 ha** acumuladas (manteniendo el requisito mínimo de 4 años con dato). Las unidades por debajo del umbral activo se marcan como muestra insuficiente y no se publican como hallazgo individual.

## 3. Hipótesis confirmatorias

Todas las pruebas confirmatorias se evalúan con nivel de significancia $\alpha = 0{,}05$ e intervalos de confianza al 95 % obtenidos por bootstrap con semilla fija (`2026`) y `5.000` réplicas. Dentro de cada familia de hipótesis se aplica la **corrección de Holm** para comparaciones múltiples.

### H1. Tendencia temporal del rendimiento (2019-2025)

- **Hipótesis nula**: el rendimiento municipal no presenta tendencia de mejora entre 2019 y 2025 (pendiente mediana igual a cero).
- **Método**: estimación de la pendiente no paramétrica de **Theil-Sen** por municipio y cultivo elegible a lo largo de los años disponibles; prueba de **rangos con signo de Wilcoxon** sobre la distribución de pendientes municipales frente a cero, por cultivo.
- **Tamaño del efecto e incertidumbre**: mediana de las pendientes municipales (en t/ha por año y como porcentaje del rendimiento medio del periodo) con su intervalo de confianza bootstrap al 95 %.
- **Regla de interpretación**: dado que la ventana temporal comprende únicamente 7 años, la ausencia de significancia estadística se reporta estrictamente como **sin evidencia de tendencia** y nunca como estancamiento demostrado, salvo que el intervalo de confianza al 95 % de la pendiente mediana quede íntegramente contenido dentro de la banda de equivalencia de $\pm 1\ \%$ anual respecto al rendimiento medio.

### H2. Brecha tecnológica en maíz (tecnificado vs. tradicional)

- **Hipótesis**: dentro de un mismo municipio y año, el maíz tecnificado presenta mayor rendimiento que el maíz tradicional.
- **Diseño y prueba**: diseño pareado sobre los pares `(codigo_dane_municipio, anio)` que registran área cosechada positiva en ambos sistemas (`tecnificado` y `tradicional`); prueba de **rangos con signo de Wilcoxon**.
- **Tamaño del efecto e incertidumbre**: razón mediana de rendimiento ($\text{tecnificado} / \text{tradicional}$) y estimador de ubicación de **Hodges-Lehmann** de la diferencia pareada (en t/ha), con intervalo de confianza bootstrap al 95 % obtenido **remuestreando municipios completos** (bootstrap por conglomerados municipales para preservar la dependencia temporal intrínseca de cada municipio).

### H3. Diferencias por sistema productivo en arroz (riego, secano mecanizado, secano manual)

- **Hipótesis**: el rendimiento del arroz difiere según el sistema productivo (`riego`, `secano_mecanizado`, `secano_manual`).
- **Diseño y prueba**: prueba de **Friedman** sobre las tripletas `(codigo_dane_municipio, anio)` que cuentan con los tres sistemas simultáneamente. Cuando el número de tripletas completas sea reducido o insuficiente, se complementa con comparaciones pareadas mediante la prueba de **rangos con signo de Wilcoxon** sobre todos los pares `(codigo_dane_municipio, anio)` disponibles para cada par de sistemas, corrigiendo los valores $p$ con **Holm**.
- **Tamaño del efecto**: razón mediana de rendimiento entre pares de sistemas y estimador de Hodges-Lehmann con intervalo bootstrap por conglomerados municipales.
- **Nota sobre yuca**: la comparación entre `fresco` e `industrial` en yuca se reporta únicamente de forma **descriptiva**, dado que esa clasificación en EVA obedece al destino comercial del producto y no a un sistema tecnológico de cultivo diferenciado.

### H4. Diferencias interdepartamentales de rendimiento

- **Hipótesis**: el rendimiento municipal del periodo difiere entre los departamentos de la Región Caribe para cada cultivo.
- **Diseño y prueba**: prueba de **Kruskal-Wallis** entre departamentos sobre el rendimiento agregado del periodo 2019-2025 de los municipios elegibles, por cultivo.
- **Tamaño del efecto y post-hoc**: **épsilon cuadrado** ($\varepsilon^2$) con intervalo de confianza bootstrap; comparaciones por pares entre departamentos con la prueba $U$ de **Mann-Whitney** y corrección de **Holm**.

### H5. Variabilidad interanual entre cultivos

- **Hipótesis**: la inestabilidad interanual del rendimiento municipal, medida a través del coeficiente de variación interanual ($CV = s / \bar{y}$ sobre los rendimientos anuales de cada municipio), difiere entre maíz, yuca y arroz.
- **Diseño y prueba**: prueba de **Friedman** restringida a los municipios en los que los tres cultivos son simultáneamente elegibles; comparaciones post-hoc por pares de cultivos mediante **Wilcoxon de rangos con signo** con corrección de **Holm** y tamaño del efecto de Hodges-Lehmann.

## 4. Hipótesis exploratorias

Los análisis exploratorios se identifican explícitamente con el rótulo **exploratorio** en toda tabla, documento o visualización, y sus valores $p$ se ajustan controlando la tasa de falsos descubrimientos mediante **Benjamini-Hochberg (FDR)**.

### E1. Asociación con variabilidad climática ENSO (índice ONI de NOAA)

- **Relación regional anual**: correlación de rangos de **Spearman** ($\rho$) entre el índice anual ONI (Oceanic Niño Index de NOAA) y dos indicadores anuales regionales por cultivo: (a) rendimiento agregado regional y (b) tasa regional de área no cosechada. Dada la longitud de la serie ($n = 7$ años), la inferencia se realiza mediante **prueba de permutación exacta** sobre las $7! = 5.040$ permutaciones posibles.
- **Comparación intramunicipal**: dentro de cada municipio y cultivo elegible, comparación del rendimiento medio en años clasificados como **La Niña** frente a años **neutros/El Niño** mediante prueba pareada de **Wilcoxon**.

### E2. Quiebre metodológico de reporte en 2022 sobre el área no cosechada

- **Objetivo**: evaluar el cambio estructural en la tasa anual de área no cosechada ($(\text{Área sembrada} - \text{Área cosechada}) / \text{Área sembrada}$) entre el subperiodo **2019-2021** y el subperiodo **2022-2025**, derivado del cambio operativo en EVA donde las siembras del semestre A cosechadas en el semestre B generan desfases semestrales.

## 5. Brecha potencial y simulación de ganancia de producción

Para cada municipio elegible, cultivo y sistema productivo:

1. **Referente alcanzable**: se define el techo departamental como el **percentil 75 ($P_{75}$)** del rendimiento de los municipios elegibles del mismo departamento, cultivo y sistema productivo.
2. **Brecha de rendimiento**: para todo municipio con rendimiento inferior a $P_{75}$, la brecha cerrable es $\Delta y = \max(0,\ P_{75} - y_{i,t})$.
3. **Escenarios de ganancia en toneladas**: para capturar la variabilidad interanual del área cosechada y del rendimiento municipal, se remuestrean por bootstrap los años observados de cada municipio y se reporta la distribución de ganancia potencial anual en toneladas exclusivamente mediante el rango de percentiles **$p_{10}$, $p_{50}$ y $p_{90}$** (nunca como cifra puntual única).

## 6. Protocolo de robustez y clasificación de hallazgos

Todo hallazgo confirmatorio se somete obligatoriamente a tres ejes de sensibilidad:

1. **Umbral de área cosechada acumulada**: `300 ha`, `500 ha` (base) y `1.000 ha`.
2. **Sensibilidad temporal (leave-one-year-out)**: repetición de la prueba excluyendo un año a la vez ($2019, 2020, \dots, 2025$), verificando en particular que la exclusión de 2022 o de 2025 no invierta la conclusión.
3. **Tratamiento de valores atípicos**: ejecución con la base completa frente a la base que excluye registros marcados por fuera de los límites agronómicos de plausibilidad (`fuera_de_rango`) o por puntuación $z$ robusta (`atipico_robusto`).

Cada hallazgo recibe una clasificación final estandarizada:

- **Firme**: la dirección del efecto y la conclusión estadística tras corrección de multiplicidad se mantienen en todas las variantes de umbral, exclusión anual y filtrado de atípicos.
- **Frágil**: la significancia corregida o el signo sustantivo del efecto cambian en al menos una variante de sensibilidad.
- **Insuficiente**: el número de unidades elegibles o pares disponibles no alcanza el tamaño muestral mínimo configurado.

## 7. Lenguaje e interpretación

Todos los resultados cuantitativos del proyecto se formulan y comunican como **asociaciones observadas** y diferencias descriptivas o inferenciales condicionadas a los registros EVA. No se realizan afirmaciones causales ni atribuciones de impacto directo de intervenciones.

## 8. Limitaciones conocidas de la fuente

1. **Naturaleza administrativa de las EVA**: los registros provienen de evaluaciones municipales por consenso técnico y no de un censo probabilístico ni de mediciones directas de cosecha en parcela.
2. **Quiebre operativo en 2022**: a partir de 2022 se registran cosechas en el semestre B cuya área sembrada fue contabilizada en el semestre A, lo que invalida cualquier cálculo de área no cosechada a escala semestral y exige trabajar sobre agregados anuales.
3. **Cobertura posiblemente incompleta en 2025**: el último año del corte puede presentar rezagos de consolidación en el área cosechada de ciertos municipios o semestres, por lo que se etiqueta explícitamente y se verifica mediante validación dejando 2025 fuera.
4. **Diseño observacional sin covariables de manejo en finca**: no se observan dosis de fertilización, variedad específica de semilla, fecha exacta de siembra ni acceso efectivo a crédito o asistencia técnica a nivel de productor.
