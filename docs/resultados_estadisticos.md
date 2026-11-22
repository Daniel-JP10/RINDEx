# Resultados estadísticos y robustez — Región Caribe 2019-2025

- **Edición**: `caribe_2019_2025`
- **Región**: Caribe
- **Umbral base de elegibilidad**: `500 ha` y `4` años con dato
- **Semilla bootstrap**: `2026` (`5.000` réplicas principales; `1.000` en variantes de robustez)
- **Tiempo total de ejecución**: `51,79 s`

## 1. Clasificación climática anual ENSO (ONI de NOAA, 2019-2025)

| Año | Temporadas móviles | ONI medio anual (°C) | Temporadas Niña (<= -0,5) | Temporadas Niño (>= 0,5) | Temporadas neutras | Clasificación anual |
| :---: | ---: | ---: | ---: | ---: | ---: | :---: |
| 2019 | 12 | 0,6492 | 0 | 9 | 3 | `nino` |
| 2020 | 12 | -0,2108 | 4 | 3 | 5 | `neutro` |
| 2021 | 12 | -0,6508 | 8 | 0 | 4 | `nina` |
| 2022 | 12 | -0,7825 | 12 | 0 | 0 | `nina` |
| 2023 | 12 | 0,8142 | 1 | 7 | 4 | `nino` |
| 2024 | 12 | 0,4100 | 0 | 4 | 8 | `neutro` |
| 2025 | 12 | -0,2817 | 3 | 0 | 9 | `neutro` |

## 2. Tabla resumen de pruebas preespecificadas (H1 a H5, E1 y E2)

| Hipótesis | Familia | n | Estadístico | p | p ajustado | Efecto | Intervalo de 95 % | Decisión | Robustez |
| :--- | :---: | ---: | :--- | ---: | ---: | :--- | :---: | :--- | :--- |
| H1 Tendencia (Arroz) | `H1` | 86 | W = 1.540,50 | 0,7030 | 0,7938 | mediana pendiente (t/ha/anio): 0,0000 | [-0,0231; 0,0248] | equivalencia practica (+/- 1 % anual) | **firme** |
| H1 Tendencia (Maíz) | `H1` | 180 | W = 4.659,50 | 0,0183 | 0,0549 | mediana pendiente (t/ha/anio): 0,0000 | [-0,0183; 0,0000] | equivalencia practica (+/- 1 % anual) | **fragil** (umbral_300ha, sin_2019, sin_2021, sin_2022, sin_2023, sin_2025) |
| H1 Tendencia (Yuca) | `H1` | 172 | W = 3.363,00 | 0,3969 | 0,7938 | mediana pendiente (t/ha/anio): 0,0000 | [0,0000; 0,0000] | equivalencia practica (+/- 1 % anual) | **firme** |
| H2 Brecha tecnologica en maiz (tecnificado vs tradicional) | `H2` | 60 | W = 27,00 | < 0,0001 | < 0,0001 | razon Hodges-Lehmann: 1,6729 | [1,5483; 1,8017] | diferencia significativa (tecnificado > tradicional) | **firme** |
| H3 Arroz (riego vs secano_mecanizado) | `H3` | 5 | W = 0,00 | 0,0625 | 0,0625 | razon Hodges-Lehmann: 1,1377 | [1,0609; 1,2133] | sin evidencia de diferencia | **fragil** (umbral_300ha, sin_2019, municipio_anio) |
| H3 Arroz (riego vs secano_manual) | `H3` | 10 | W = 0,00 | 0,0020 | 0,0039 | razon Hodges-Lehmann: 2,0190 | [1,6288; 2,7345] | diferencia significativa (razon mayor a 1) | **firme** |
| H3 Arroz (secano_mecanizado vs secano_manual) | `H3` | 31 | W = 0,00 | < 0,0001 | < 0,0001 | razon Hodges-Lehmann: 1,6174 | [1,4805; 1,8183] | diferencia significativa (razon mayor a 1) | **firme** |
| H4 Diferencia departamental (Arroz) | `H4` | 86 | H = 34,61 | < 0,0001 | < 0,0001 | epsilon_cuadrado: 0,4071 | [0,2768; 0,5861] | diferencia interdepartamental significativa | **firme** |
| H4 Diferencia departamental (Maíz) | `H4` | 180 | H = 19,09 | 0,0040 | 0,0080 | epsilon_cuadrado: 0,1066 | [0,0571; 0,2341] | diferencia interdepartamental significativa | **firme** |
| H4 Diferencia departamental (Yuca) | `H4` | 172 | H = 5,08 | 0,5330 | 0,5330 | epsilon_cuadrado: 0,0297 | [0,0155; 0,1351] | sin evidencia de diferencia interdepartamental | **firme** |
| H5 Variabilidad interanual CV (Friedman 3 cultivos) | `H5` | 76 | chi2_F = 2,55 | 0,2791 | 0,2791 | W de Kendall: 0,0168 | [0,0012; 0,0921] | sin evidencia de diferencia de variabilidad | **firme** |
| H5 Variabilidad CV (Arroz vs Maíz) | `H5` | 76 | W = 1.105,00 | 0,0638 | 0,1914 | diferencia HL de CV: -0,0286 | [-0,0698; 0,0010] | sin evidencia de diferencia de variabilidad | **firme** |
| H5 Variabilidad CV (Arroz vs Yuca) | `H5` | 76 | W = 1.386,00 | 0,6901 | 0,6901 | diferencia HL de CV: -0,0072 | [-0,0424; 0,0253] | sin evidencia de diferencia de variabilidad | **firme** |
| H5 Variabilidad CV (Maíz vs Yuca) | `H5` | 76 | W = 1.176,00 | 0,1373 | 0,2746 | diferencia HL de CV: 0,0253 | [-0,0071; 0,0688] | sin evidencia de diferencia de variabilidad | **firme** |
| E1 Exploratoria: ONI vs rendimiento regional (Arroz) | `E1` | 7 | rho = 0,07 | 0,9063 | 0,9063 | rho de Spearman: 0,0714 | N/A | sin evidencia de asociacion exploratoria | **firme** |
| E1 Exploratoria: ONI vs tasa area no cosechada (Arroz) | `E1` | 7 | rho = -0,07 | 0,9063 | 0,9063 | rho de Spearman: -0,0714 | N/A | sin evidencia de asociacion exploratoria | **firme** |
| E1 Exploratoria: ONI vs rendimiento regional (Maíz) | `E1` | 7 | rho = 0,32 | 0,4976 | 0,9063 | rho de Spearman: 0,3214 | N/A | sin evidencia de asociacion exploratoria | **firme** |
| E1 Exploratoria: ONI vs tasa area no cosechada (Maíz) | `E1` | 7 | rho = -0,36 | 0,4444 | 0,9063 | rho de Spearman: -0,3571 | N/A | sin evidencia de asociacion exploratoria | **firme** |
| E1 Exploratoria: ONI vs rendimiento regional (Yuca) | `E1` | 7 | rho = 0,25 | 0,5948 | 0,9063 | rho de Spearman: 0,2500 | N/A | sin evidencia de asociacion exploratoria | **firme** |
| E1 Exploratoria: ONI vs tasa area no cosechada (Yuca) | `E1` | 7 | rho = -0,14 | 0,7825 | 0,9063 | rho de Spearman: -0,1429 | N/A | sin evidencia de asociacion exploratoria | **firme** |
| E1 Exploratoria: anos Nina vs neutros (Arroz) | `E1` | 86 | W = 1.800,00 | 0,9041 | 0,9063 | diferencia HL (t/ha): 0,0099 | [-0,1052; 0,1336] | sin evidencia de asociacion exploratoria | **firme** |
| E1 Exploratoria: anos Nina vs neutros (Maíz) | `E1` | 180 | W = 7.406,00 | 0,6613 | 0,9063 | diferencia HL (t/ha): -0,0155 | [-0,0819; 0,0517] | sin evidencia de asociacion exploratoria | **firme** |
| E1 Exploratoria: anos Nina vs neutros (Yuca) | `E1` | 172 | W = 5.839,00 | 0,7129 | 0,9063 | diferencia HL (t/ha): -0,0149 | [-0,2399; 0,1747] | sin evidencia de asociacion exploratoria | **firme** |
| E2 Exploratoria: tasa no cosechada 2022-2025 vs 2019-2021 (Arroz) | `E2` | 68 | W = 964,00 | 0,2743 | 0,9063 | diferencia HL (pp): 0,9288 | [-0,7176; 3,1706] | sin evidencia de asociacion exploratoria | **fragil** (sin_2021) |
| E2 Exploratoria: tasa no cosechada 2022-2025 vs 2019-2021 (Maíz) | `E2` | 143 | W = 4.760,00 | 0,6134 | 0,9063 | diferencia HL (pp): 0,4660 | [-1,1435; 2,0778] | sin evidencia de asociacion exploratoria | **firme** |
| E2 Exploratoria: tasa no cosechada 2022-2025 vs 2019-2021 (Yuca) | `E2` | 138 | W = 2.784,00 | < 0,0001 | 0,0004 | diferencia HL (pp): 4,6539 | [2,6657; 6,7138] | asociacion exploratoria significativa (FDR < 0,05) | **firme** |

## 3. Interpretación por familia de hipótesis (lenguaje de asociación observada)

### H1. Tendencia temporal del rendimiento municipal (2019-2025)
En los municipios elegibles de la Región Caribe la pendiente mediana de Theil-Sen es 0,0000 t/ha/año en los tres cultivos y no supera el umbral de significancia tras la corrección de Holm (con intervalos de confianza relativos contenidos dentro de la banda de +/- 1 % anual en el escenario base); en arroz y yuca el resultado es firme, mientras que en maíz es frágil porque la ligera pendiente negativa alcanza significancia estadística al ampliar la muestra a 300 ha o al excluir años individuales.

### H2. Brecha tecnológica observada en maíz (tecnificado vs. tradicional)
En los municipios elegibles que registran ambos sistemas de maíz en los mismos años (60 municipios, 368 pares municipio-año), el sistema tecnificado se asocia de forma firme con un rendimiento superior al tradicional, con una razón de Hodges-Lehmann de 1,67 veces (IC 95 %: 1,55 a 1,80; razón mediana 1,66) que se mantiene en todas las variantes de sensibilidad.

### H3. Diferencias observadas entre sistemas en arroz (y nota descriptiva en yuca)
En las comparaciones pareadas por municipio corregidas con Holm (D1 y D2), tanto el arroz bajo riego (razón HL = 2,02; firme) como el secano mecanizado (razón HL = 1,62; firme) se asocian con rendimientos significativamente mayores que el secano manual, mientras que el contraste directo entre riego y secano mecanizado cuenta con solo 5 municipios elegibles con par (frágil por tamaño muestral en nivel municipal frente a municipio-año o umbral de 300 ha) y el complemento de Friedman sobre las 19 tripletas completas arroja chi2 = 36,11 (p = < 0,0001, W = 0,9501). De forma descriptiva en yuca (cuya desagregación responde al destino comercial), la yuca en fresco presenta un rendimiento regional ponderado de 10,70 t/ha (mediana municipal 10,58 t/ha en 193 municipios) frente a 17,64 t/ha en yuca industrial (mediana municipal 15,35 t/ha en 43 municipios).

### H4. Diferencias interdepartamentales de rendimiento del periodo
La prueba de Kruskal-Wallis evidencia diferencias interdepartamentales estadísticamente significativas y firmes en el rendimiento municipal del periodo para arroz (épsilon cuadrado = 0,41) y maíz (épsilon cuadrado = 0,11), mientras que en yuca (épsilon cuadrado = 0,03; p ajustado = 0,5330) no se observa evidencia de diferenciación departamental.

### H5. Variabilidad interanual del rendimiento (CV) entre cultivos
En los 76 municipios donde arroz, maíz y yuca son simultáneamente elegibles, ni la prueba ómnibus de Friedman (W de Kendall = 0,0168; p = 0,2791) ni las comparaciones pareadas de Wilcoxon con corrección de Holm muestran diferencias estadísticamente significativas en el coeficiente de variación interanual del rendimiento, resultado que se mantiene firme en todas las variantes.

### E1. Análisis exploratorio de asociación con el índice climático ONI (ENSO)
En el análisis exploratorio climático (corregido por Benjamini-Hochberg), ni las correlaciones exactas de Spearman a escala regional anual (n = 7 años) con el índice ONI ni las comparaciones intramunicipales pareadas entre años La Niña (2021-2022) y años neutros (2020, 2024, 2025) muestran asociaciones estadísticamente significativas, con estabilidad firme en todas las variantes.

### E2. Análisis exploratorio del quiebre 2022 en la tasa de área no cosechada
Tras excluir los municipios con área cosechada acumulada superior a la sembrada (D4), la comparación exploratoria entre 2022-2025 y 2019-2021 muestra un incremento estadísticamente significativo y firme en la tasa de área no cosechada de yuca (+4,65 puntos porcentuales; FDR = 0,0004), el cual se interpreta como desfase asociado al ciclo vegetativo largo del cultivo tras el cambio metodológico de 2022 (D3) y no como pérdida; en maíz no se observa cambio significativo (firme) y en arroz el resultado base no significativo es sensible a la exclusión de 2021 (frágil).
