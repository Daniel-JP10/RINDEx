# Resultados estadísticos y robustez — Región Caribe 2019-2025

- **Edición**: `caribe_2019_2025`
- **Región**: Caribe
- **Umbral base de elegibilidad**: `500 ha` y `4` años con dato
- **Semilla bootstrap**: `2026` (`5.000` réplicas principales; `1.000` en variantes de robustez)
- **Tiempo total de ejecución**: `106,29 s`

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
| H1 Tendencia (Arroz) | `H1` | 86 | W = 1.540,50 | 0,7030 | 0,7938 | mediana pendiente (t/ha/anio): 0,0000 (0,00 %/año) | [-0,0231; 0,0248] ([-0,46 %; 0,86 %]) | sin evidencia de tendencia (equivalencia practica +/- 1 % anual) | **firme** |
| H1 Tendencia (Maíz) | `H1` | 180 | W = 4.659,50 | 0,0183 | 0,0549 | mediana pendiente (t/ha/anio): 0,0000 (0,00 %/año) | [-0,0183; 0,0000] ([-0,64 %; 0,00 %]) | sin evidencia de tendencia en escenario base; tendencia negativa estadisticamente significativa solo al excluir series poco informativas, de magnitud practicamente despreciable (-0,17 % anual) | **fragil** (umbral_300ha, sin_2019, sin_2021, sin_2022, sin_2023, sin_2025, sin_poco_informativas_D7) |
| H1 Tendencia (Yuca) | `H1` | 172 | W = 3.363,00 | 0,3969 | 0,7938 | mediana pendiente (t/ha/anio): 0,0000 (0,00 %/año) | [0,0000; 0,0000] ([0,00 %; 0,00 %]) | la tendencia no es medible por la repeticion de valores | **firme** |
| H2 Brecha tecnologica en maiz (tecnificado vs tradicional) | `H2` | 60 | W = 27,00 | < 0,0001 | < 0,0001 | razon Hodges-Lehmann: 1,6729 | [1,5483; 1,8017] | diferencia significativa (tecnificado > tradicional) | **firme** |
| H3 Arroz (riego vs secano_mecanizado) | `H3` | 5 | W = 0,00 | 0,0625 | 0,0625 | razon Hodges-Lehmann: 1,1377 | [1,0609; 1,2133] | insuficiente (n < 6, D6) | **insuficiente** |
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

### 2.1. Sensibilidad adicional post-hoc (D7: H1 y H5 excluyendo series poco informativas)

| Hipótesis (sensibilidad post-hoc D7) | Familia | n (sin poco informativas) | Estadístico | p | p ajustado | Efecto | Intervalo de 95 % | Decisión en sensibilidad D7 |
| :--- | :---: | ---: | :--- | ---: | ---: | :--- | :---: | :--- |
| H1 Tendencia (Arroz) | `H1` | 79 | W = 1.388,50 | 0,8472 | 0,9007 | mediana pendiente (t/ha/anio): 0,0000 (0,00 %/año) | [-0,0272; 0,0313] ([-0,61 %; 1,28 %]) | sin evidencia de tendencia |
| H1 Tendencia (Maíz) | `H1` | 167 | W = 4.416,00 | 0,0141 | 0,0422 | mediana pendiente (t/ha/anio): -0,0016 (-0,17 %/año) | [-0,0231; 0,0000] ([-1,19 %; 0,00 %]) | tendencia negativa estadisticamente significativa solo al excluir series poco informativas, de magnitud practicamente despreciable (-0,17 % anual) |
| H1 Tendencia (Yuca) | `H1` | 112 | W = 2.212,50 | 0,4504 | 0,9007 | mediana pendiente (t/ha/anio): 0,0000 (0,00 %/año) | [-0,0659; 0,0581] ([-0,34 %; 0,60 %]) | la tendencia no es medible por la repeticion de valores |
| H5 Variabilidad interanual CV (Friedman 3 cultivos) | `H5` | 46 | chi2_F = 0,39 | 0,8223 | 0,8223 | W de Kendall: 0,0043 | [0,0005; 0,0940] | sin evidencia de diferencia de variabilidad |
| H5 Variabilidad CV (Arroz vs Maíz) | `H5` | 46 | W = 462,00 | 0,3976 | 0,9700 | diferencia HL de CV: -0,0190 | [-0,0630; 0,0207] | sin evidencia de diferencia de variabilidad |
| H5 Variabilidad CV (Arroz vs Yuca) | `H5` | 46 | W = 449,00 | 0,3233 | 0,9700 | diferencia HL de CV: -0,0302 | [-0,0904; 0,0275] | sin evidencia de diferencia de variabilidad |
| H5 Variabilidad CV (Maíz vs Yuca) | `H5` | 46 | W = 524,00 | 0,8626 | 0,9700 | diferencia HL de CV: 0,0040 | [-0,0443; 0,0510] | sin evidencia de diferencia de variabilidad |

## 3. Interpretación por familia de hipótesis (lenguaje de asociación observada)

### H1. Tendencia temporal del rendimiento municipal (2019-2025)
Aplicando la regla de decisión por cultivo de D7: (1) en **arroz**, la sensibilidad D7 no cambia la conclusión (p ajustado = 0,7938 en base y 0,9007 en D7) y el intervalo de confianza al 95 % de la pendiente relativa en el escenario base ([-0,46 %; +0,86 %] anual) queda contenido dentro de +/- 1 % anual, por lo que la decisión es **sin evidencia de tendencia (equivalencia práctica +/- 1 % anual)**; (2) en **maíz**, la prueba principal no alcanza significancia tras la corrección de Holm (p ajustado = 0,0549), pero al excluir las 13 series poco informativas en D7 (n = 167) pasa a p ajustado = 0,0422 con pendiente mediana de -0,0016 t/ha/año (-0,17 % anual sobre el rendimiento medio municipal, IC 95 %: [-1,19 %; 0,00 %]; -0,08 % del rendimiento mediano municipal de 2,00 t/ha), por lo que se reportan ambos resultados: **tendencia negativa estadísticamente significativa solo al excluir series poco informativas, de magnitud prácticamente despreciable (-0,17 % anual)**; y (3) en **yuca**, dada la repetición de valores (45,75 % de pares consecutivos idénticos y 29,65 % de pendientes exactamente nulas), se mantiene que **la tendencia no es medible por la repetición de valores**.

### H2. Brecha tecnológica observada en maíz (tecnificado vs. tradicional)
En los municipios elegibles que registran ambos sistemas de maíz en los mismos años (60 municipios, 368 pares municipio-año), el sistema tecnificado se asocia de forma firme con un rendimiento superior al tradicional, con una razón de Hodges-Lehmann de 1,67 veces (IC 95 %: 1,55 a 1,80; razón mediana 1,66) que se mantiene en todas las variantes de sensibilidad.

### H3. Diferencias observadas entre sistemas en arroz (y nota descriptiva en yuca)
En las comparaciones pareadas por municipio corregidas con Holm (D1 y D2), tanto el arroz bajo riego (razón HL = 2,02; firme) como el secano mecanizado (razón HL = 1,62; firme) se asocian con rendimientos significativamente mayores que el secano manual, mientras que el contraste directo entre riego y secano mecanizado cuenta con solo 5 municipios elegibles con par y se clasifica como **insuficiente** según D6 (dado que con n < 6 el valor p bilateral exacto mínimo en Wilcoxon es 0,0625 > 0,05); el complemento de Friedman sobre las 19 tripletas completas arroja chi2 = 36,11 (p = < 0,0001, W = 0,9501). De forma descriptiva en yuca (cuya desagregación responde al destino comercial), la yuca en fresco presenta un rendimiento regional ponderado de 10,70 t/ha (mediana municipal 10,58 t/ha en 193 municipios) frente a 17,64 t/ha en yuca industrial (mediana municipal 15,35 t/ha en 43 municipios).

### H4. Diferencias interdepartamentales de rendimiento del periodo
La prueba de Kruskal-Wallis evidencia diferencias interdepartamentales estadísticamente significativas y firmes en el rendimiento municipal del periodo para arroz (épsilon cuadrado = 0,41) y maíz (épsilon cuadrado = 0,11), mientras que en yuca (épsilon cuadrado = 0,03; p ajustado = 0,5330) no se observa evidencia de diferenciación departamental.

### H5. Variabilidad interanual del rendimiento (CV) entre cultivos
En los 76 municipios donde arroz, maíz y yuca son simultáneamente elegibles (así como en los 52 municipios que restan al excluir las series poco informativas en la sensibilidad post-hoc D7), ni la prueba ómnibus de Friedman ni las comparaciones pareadas de Wilcoxon con corrección de Holm muestran diferencias estadísticamente significativas en el coeficiente de variación interanual del rendimiento (firme).

### E1. Análisis exploratorio de asociación con el índice climático ONI (ENSO)
En el análisis exploratorio climático (corregido por Benjamini-Hochberg), ni las correlaciones exactas de Spearman a escala regional anual (n = 7 años) con el índice ONI ni las comparaciones intramunicipales pareadas entre años La Niña (2021-2022) y años neutros (2020, 2024, 2025) muestran asociaciones estadísticamente significativas (firme). Conforme a D8, la ausencia de correlación regional con el ONI anual no descarta eventos hidrometeorológicos locales, y el pico de área no cosechada de arroz en 2021 (36.766,30 ha; 23,64 %) se describe como un episodio concentrado geográficamente sin atribución climática.

### E2. Análisis exploratorio del quiebre 2022 en la tasa de área no cosechada
Tras excluir los municipios con área cosechada acumulada superior a la sembrada (D4), la comparación exploratoria entre 2022-2025 y 2019-2021 muestra un incremento estadísticamente significativo y firme en la tasa de área no cosechada de yuca (+4,65 puntos porcentuales; FDR = 0,0004), el cual se interpreta como desfase asociado al ciclo vegetativo largo del cultivo tras el cambio metodológico de 2022 (D3) y no como pérdida; en maíz no se observa cambio significativo (firme) y en arroz el resultado base no significativo es sensible a la exclusión de 2021 (frágil).

## 4. Análisis descriptivo de concentración del área no cosechada de arroz en 2021 (D8)

- **Área no cosechada regional de arroz en 2021**: `36.766,30 ha` sobre `155.552,00 ha` sembradas (`23,64 %`).
- **Aporte de los 5 municipios con mayor área no cosechada**: `27.725,00 ha` (**`75,41 %`** del total regional).
- **Aporte de los 10 municipios con mayor área no cosechada**: `32.750,00 ha` (**`89,08 %`** del total regional).
- *Nota metodológica (D8)*: descripción estrictamente geográfica sin atribución causal climática.

| Rango | Código DANE | Municipio | Departamento | Área sembrada 2021 (ha) | Área cosechada 2021 (ha) | Área no cosechada 2021 (ha) | Tasa propia no cosechada (%) | % del total regional | % acumulado regional |
| ---: | :---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `70429` | Majagual | Sucre | 20.620,00 | 9.709,00 | 10.911,00 | 52,91 % | 29,68 % | 29,68 % |
| 2 | `23068` | Ayapel | Córdoba | 6.450,00 | 950,00 | 5.500,00 | 85,27 % | 14,96 % | 44,64 % |
| 3 | `13006` | Achí | Bolívar | 14.838,00 | 9.629,00 | 5.209,00 | 35,11 % | 14,17 % | 58,80 % |
| 4 | `70265` | Guaranda | Sucre | 14.534,00 | 10.529,00 | 4.005,00 | 27,56 % | 10,89 % | 69,70 % |
| 5 | `70708` | San Marcos | Sucre | 5.350,00 | 3.250,00 | 2.100,00 | 39,25 % | 5,71 % | 75,41 % |
| 6 | `13655` | San Jacinto del Cauca | Bolívar | 10.700,00 | 9.500,00 | 1.200,00 | 11,21 % | 3,26 % | 78,67 % |
| 7 | `70678` | San Benito Abad | Sucre | 4.980,00 | 3.832,00 | 1.148,00 | 23,05 % | 3,12 % | 81,80 % |
| 8 | `70124` | Caimito | Sucre | 1.280,00 | 155,00 | 1.125,00 | 87,89 % | 3,06 % | 84,85 % |
| 9 | `13458` | Montecristo | Bolívar | 3.350,00 | 2.452,00 | 898,00 | 26,81 % | 2,44 % | 87,30 % |
| 10 | `70771` | Sucre | Sucre | 1.584,00 | 930,00 | 654,00 | 41,29 % | 1,78 % | 89,08 % |

## 5. Niveles de evidencia por cultivo y resumen municipal (D9)

| Cultivo | Pares consecutivos | Pares idénticos (%) | Filas semestrales (`> 0 ha`) | Rendimientos enteros (`,00`) (%) | Nivel de evidencia del cultivo | Municipios `alto` | Municipios `medio` | Municipios `bajo` |
| :--- | ---: | ---: | ---: | ---: | :---: | ---: | ---: | ---: |
| **Arroz** | 606 | 109 (17,99 %) | 1.622 | 459 (28,30 %) | **`alto`** | 64 | 28 | 19 |
| **Maíz** | 1.130 | 215 (19,03 %) | 4.405 | 1.645 (37,34 %) | **`alto`** | 119 | 49 | 25 |
| **Yuca** | 1.117 | 511 (45,75 %) | 2.378 | 2.166 (91,08 %) | **`bajo`** | 38 | 76 | 79 |
