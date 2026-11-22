# Validación de limpieza, sistemas y agregación — Región Caribe 2019-2025

- **Edicion**: `caribe_2019_2025`
- **Region**: Caribe
- **Tolerancia numerica de conservacion**: `1e-06`

## 1. Conservación de sumas entre niveles de agregación

| Nivel / Tabla | Filas | Area sembrada (ha) | Area cosechada (ha) | Produccion (t) | Max. dif. absoluta vs. filtrada | Estado |
| :--- | ---: | ---: | ---: | ---: | ---: | :---: |
| `eva_filtrada (base)` | 9.194 | 3.682.511,46 | 3.420.546,26 | 17.679.166,48 | 0,00000000 | OK |
| `eva_limpia` | 9.194 | 3.682.511,46 | 3.420.546,26 | 17.679.166,48 | 0,00000000 | OK |
| `anual_municipio_sistema` | 4.219 | 3.682.511,46 | 3.420.546,26 | 17.679.166,48 | 0,00000000 | OK |
| `anual_municipio_cultivo` | 3.374 | 3.682.511,46 | 3.420.546,26 | 17.679.166,48 | 0,00000000 | OK |
| `anual_departamento_cultivo` | 147 | 3.682.511,46 | 3.420.546,26 | 17.679.166,48 | 0,00000000 | OK |
| `anual_region_cultivo` | 21 | 3.682.511,46 | 3.420.546,26 | 17.679.166,48 | 0,00000000 | OK |
| `periodo_municipio_cultivo` | 497 | 3.682.511,46 | 3.420.546,26 | 17.679.166,48 | 0,00000000 | OK |
| `periodo_municipio_sistema` | 652 | 3.682.511,46 | 3.420.546,26 | 17.679.166,48 | 0,00000001 | OK |

## 2. Coincidencia de totales regionales por cultivo con `perfil_datos.md`

| Cultivo | Area sembrada (ha) | Area cosechada (ha) | Area no cosechada (ha) | Produccion regional (t) | Rendimiento agregado (t/ha) |
| :--- | ---: | ---: | ---: | ---: | ---: |
| **Arroz** | 993.879,57 | 920.270,11 | 73.609,46 | 3.983.214,59 | 4,3283 |
| **Maíz** | 1.777.098,51 | 1.671.139,08 | 105.959,43 | 4.358.996,03 | 2,6084 |
| **Yuca** | 911.533,38 | 829.137,07 | 82.396,31 | 9.336.955,86 | 11,2611 |

## 3. Coherencia jerárquica (municipio -> departamento -> región)

- **Celdas evaluadas (departamento-cultivo-anio)**: 147 — diferencia maxima municipio vs. departamento: `0,00000000`
- **Celdas evaluadas (region-cultivo-anio)**: 21 — diferencia maxima departamento vs. region: `0,00000000`

## 4. Conteo de filas atípicas por cultivo, sistema y criterio

| Cultivo | Sistema | Filas totales | Filas con cosecha > 0 | `fuera_de_rango` | `atipico_robusto` (`|z| > 3,5`) | Total atipicas (union) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| Arroz | `riego` | 546 | 522 | 0 | 5 | 5 |
| Arroz | `secano_manual` | 865 | 742 | 0 | 0 | 0 |
| Arroz | `secano_mecanizado` | 408 | 358 | 0 | 0 | 0 |
| Maíz | `tecnificado` | 1.091 | 970 | 0 | 9 | 9 |
| Maíz | `tradicional` | 3.679 | 3.435 | 3 | 9 | 9 |
| Yuca | `fresco` | 2.325 | 2.152 | 0 | 37 | 37 |
| Yuca | `industrial` | 280 | 226 | 1 | 12 | 12 |

### Las 15 filas con puntuación `|z_robusto|` más extrema

| Codigo Mpio | Municipio | Depto | Cultivo | Sistema | Periodo | Area cosechada (ha) | Produccion (t) | Rendimiento (t/ha) | `z_robusto` | `fuera_de_rango` | `atipico_robusto` |
| :---: | :--- | :--- | :--- | :--- | :---: | ---: | ---: | ---: | ---: |:---:|:---:|
| `70233` | El Roble | Sucre | Yuca | `industrial` | `2020A` | 580,00 | 1.045,00 | 1,8017 | -8,68 | True | True |
| `20250` | El Paso | Cesar | Yuca | `industrial` | `2024B` | 1,00 | 2,00 | 2,0000 | -8,26 | False | True |
| `20517` | Pailitas | Cesar | Arroz | `riego` | `2019B` | 66,80 | 66,40 | 0,9940 | -7,05 | False | True |
| `20517` | Pailitas | Cesar | Arroz | `riego` | `2020B` | 74,00 | 74,00 | 1,0000 | -7,03 | False | True |
| `23350` | La Apartada | Córdoba | Arroz | `riego` | `2022A` | 10,00 | 10,00 | 1,0000 | -7,03 | False | True |
| `13140` | Calamar | Bolívar | Maíz | `tradicional` | `2023B` | 327,00 | 25,61 | 0,0783 | -6,44 | True | True |
| `13140` | Calamar | Bolívar | Maíz | `tradicional` | `2023B` | 72,00 | 5,64 | 0,0783 | -6,44 | True | True |
| `70771` | Sucre | Sucre | Yuca | `fresco` | `2025B` | 6,00 | 12,00 | 2,0000 | -5,95 | False | True |
| `70771` | Sucre | Sucre | Yuca | `fresco` | `2024A` | 10,00 | 20,00 | 2,0000 | -5,95 | False | True |
| `08560` | Ponedera | Atlántico | Yuca | `fresco` | `2021B` | 80,00 | 160,00 | 2,0000 | -5,95 | False | True |
| `70771` | Sucre | Sucre | Yuca | `fresco` | `2025A` | 6,00 | 12,00 | 2,0000 | -5,95 | False | True |
| `20250` | El Paso | Cesar | Yuca | `fresco` | `2021A` | 22,00 | 47,00 | 2,1364 | -5,71 | False | True |
| `20787` | Tamalameque | Cesar | Yuca | `fresco` | `2022B` | 163,00 | 350,45 | 2,1500 | -5,69 | False | True |
| `70678` | San Benito Abad | Sucre | Yuca | `industrial` | `2024A` | 100,00 | 400,00 | 4,0000 | -5,44 | False | True |
| `08137` | Campo de La Cruz | Atlántico | Maíz | `tecnificado` | `2021A` | 450,00 | 213,94 | 0,4754 | -5,36 | False | True |

## 5. Persistencia de `area_cosechada > area_sembrada` al agregar por año y periodo

- **Registros semestrales (`eva_limpia`) con `area_cosechada > area_sembrada`**: 2.015 de 9.194
- **Casos anuales en `anual_municipio_sistema` con `area_cosechada > area_sembrada`**: 509 de 4.219
- **Casos anuales en `anual_municipio_cultivo` con `area_cosechada > area_sembrada`**: 408 de 3.374
- **Casos acumulados (2019-2025) en `periodo_municipio_sistema` que persisten**: 76 de 652
- **Casos acumulados (2019-2025) en `periodo_municipio_cultivo` que persisten**: 59 de 497

## 6. Municipios elegibles por cultivo según umbral de área cosechada acumulada

| Cultivo | Municipios totales | `elegible_300` (>= 300 ha y >= 4 anios) | `elegible_500` (>= 500 ha y >= 4 anios) | `elegible_1000` (>= 1.000 ha y >= 4 anios) |
| :--- | ---: | ---: | ---: | ---: |
| Arroz | 111 | 94 | 86 | 73 |
| Maíz | 193 | 188 | 180 | 168 |
| Yuca | 193 | 182 | 172 | 150 |

- **Municipios con los 3 cultivos simultaneamente elegibles (para H5)**: `300 ha`: 89 | `500 ha`: 76 | `1.000 ha`: 54

## 7. Disponibilidad de pares para H2 (maíz) y tripletas/pares para H3 (arroz)

- **H2 Maíz (`tecnificado` vs. `tradicional` con `area_cosechada > 0`)**: **375** pares municipio-anio en **61** municipios.
- **H3 Arroz — tripletas completas (`riego`, `secano_mecanizado`, `secano_manual`)**: **19** municipio-anios.
- **H3 Arroz — pares `riego` vs. `secano_mecanizado`**: **25** municipio-anios.
- **H3 Arroz — pares `riego` vs. `secano_manual`**: **59** municipio-anios.
- **H3 Arroz — pares `secano_mecanizado` vs. `secano_manual`**: **209** municipio-anios.

## 8. Tasa de área no cosechada por año y cultivo (2019-2021 vs. 2022-2025, descriptiva)

| Cultivo | Anio | Subperiodo | Area sembrada (ha) | Area cosechada (ha) | Area no cosechada (ha) | Tasa de area no cosechada (%) |
| :--- | :---: | :---: | ---: | ---: | ---: | ---: |
| Arroz | 2019 | 2019-2021 (pre-quiebre) | 145.901,38 | 142.286,95 | 3.614,43 | 2,48 % |
| Arroz | 2020 | 2019-2021 (pre-quiebre) | 156.263,49 | 150.204,51 | 6.058,98 | 3,88 % |
| Arroz | 2021 | 2019-2021 (pre-quiebre) | 155.552,00 | 118.785,70 | 36.766,30 | 23,64 % |
| Arroz | 2022 | 2022-2025 (post-quiebre) | 138.969,95 | 133.319,90 | 5.650,05 | 4,07 % |
| Arroz | 2023 | 2022-2025 (post-quiebre) | 134.261,00 | 126.854,00 | 7.407,00 | 5,52 % |
| Arroz | 2024 | 2022-2025 (post-quiebre) | 133.099,50 | 119.713,00 | 13.386,50 | 10,06 % |
| Arroz | 2025 | 2022-2025 (post-quiebre) | 129.832,25 | 129.106,05 | 726,20 | 0,56 % |
| Maíz | 2019 | 2019-2021 (pre-quiebre) | 236.309,82 | 222.760,75 | 13.549,07 | 5,73 % |
| Maíz | 2020 | 2019-2021 (pre-quiebre) | 260.068,18 | 239.632,18 | 20.436,00 | 7,86 % |
| Maíz | 2021 | 2019-2021 (pre-quiebre) | 259.730,67 | 241.689,50 | 18.041,17 | 6,95 % |
| Maíz | 2022 | 2022-2025 (post-quiebre) | 251.083,49 | 231.996,35 | 19.087,14 | 7,60 % |
| Maíz | 2023 | 2022-2025 (post-quiebre) | 257.194,10 | 243.786,35 | 13.407,75 | 5,21 % |
| Maíz | 2024 | 2022-2025 (post-quiebre) | 258.125,10 | 239.847,40 | 18.277,70 | 7,08 % |
| Maíz | 2025 | 2022-2025 (post-quiebre) | 254.587,15 | 251.426,55 | 3.160,60 | 1,24 % |
| Yuca | 2019 | 2019-2021 (pre-quiebre) | 116.276,74 | 109.928,47 | 6.348,27 | 5,46 % |
| Yuca | 2020 | 2019-2021 (pre-quiebre) | 124.122,05 | 115.471,45 | 8.650,60 | 6,97 % |
| Yuca | 2021 | 2019-2021 (pre-quiebre) | 118.822,96 | 111.127,00 | 7.695,96 | 6,48 % |
| Yuca | 2022 | 2022-2025 (post-quiebre) | 127.278,80 | 115.188,00 | 12.090,80 | 9,50 % |
| Yuca | 2023 | 2022-2025 (post-quiebre) | 147.029,35 | 118.892,65 | 28.136,70 | 19,14 % |
| Yuca | 2024 | 2022-2025 (post-quiebre) | 138.723,45 | 131.052,30 | 7.671,15 | 5,53 % |
| Yuca | 2025 | 2022-2025 (post-quiebre) | 139.280,03 | 127.477,20 | 11.802,83 | 8,47 % |

### Comparación descriptiva por subperiodo (2019-2021 vs. 2022-2025)

| Cultivo | Subperiodo | Area sembrada (ha) | Area cosechada (ha) | Area no cosechada (ha) | Tasa acumulada de area no cosechada (%) |
| :--- | :---: | ---: | ---: | ---: | ---: |
| **Arroz** | 2019-2021 (pre-quiebre) | 457.716,87 | 411.277,16 | 46.439,71 | 10,15 % |
| **Arroz** | 2022-2025 (post-quiebre) | 536.162,70 | 508.992,95 | 27.169,75 | 5,07 % |
| **Maíz** | 2019-2021 (pre-quiebre) | 756.108,67 | 704.082,43 | 52.026,24 | 6,88 % |
| **Maíz** | 2022-2025 (post-quiebre) | 1.020.989,84 | 967.056,65 | 53.933,19 | 5,28 % |
| **Yuca** | 2019-2021 (pre-quiebre) | 359.221,75 | 336.526,92 | 22.694,83 | 6,32 % |
| **Yuca** | 2022-2025 (post-quiebre) | 552.311,63 | 492.610,15 | 59.701,48 | 10,81 % |
