# Perfil de datos EVA — Región Caribe 2019-2025

- **Edicion**: `caribe_2019_2025`
- **Region**: Caribe
- **Cultivos**: Maíz, Yuca, Arroz
- **Rango de anios**: 2019 a 2025

## 1. Volumen de registros y cobertura municipal por departamento

- **Filas totales en la base cruda nacional**: 166.732
- **Filas filtradas (Caribe, cultivos objetivo, 2019-2025)**: 9.194
- **Municipios unicos en la base filtrada**: 195
- **Registros de San Andres (codigo 88) en base cruda**: 197 totales (38 en cultivos objetivo; 0 en base filtrada por exclusion documentada).

| Codigo DANE | Departamento (config) | Filas filtradas | Municipios unicos (filtrada) | Municipios unicos (cruda depto) |
| :---: | :--- | ---: | ---: | ---: |
| `08` | Atlántico | 691 | 23 | 23 |
| `13` | Bolívar | 2.158 | 46 | 46 |
| `20` | Cesar | 1.317 | 25 | 25 |
| `23` | Córdoba | 1.789 | 30 | 30 |
| `44` | La Guajira | 547 | 15 | 15 |
| `47` | Magdalena | 1.101 | 30 | 30 |
| `70` | Sucre | 1.591 | 26 | 26 |

## 2. Nulos y duplicados

- **Valores nulos en base cruda (todas las 18 columnas)**: 0
- **Valores nulos en base filtrada (todas las 18 columnas)**: 0
- **Filas duplicadas exactas (base cruda)**: 0
- **Filas duplicadas exactas (base filtrada)**: 0
- **Duplicados adicionales por llave `(codigo_dane_municipio, desagregacion_cultivo, periodo)` en base cruda**: 0
- **Duplicados adicionales por llave `(codigo_dane_municipio, desagregacion_cultivo, periodo)` en base filtrada**: 0 (0 filas involucradas)

## 3. Valores de `Desagregacion cultivo` por cultivo y anios de aparicion

| Cultivo | Desagregacion cultivo | Filas | Anios en que aparece |
| :--- | :--- | ---: | :--- |
| Arroz | Arroz riego | 546 | 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| Arroz | Arroz secano manual | 865 | 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| Arroz | Arroz secano mecanizado | 408 | 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| Maíz | Maíz amarillo tecnificado | 553 | 2021, 2022, 2023, 2024, 2025 |
| Maíz | Maíz amarillo tradicional | 1.797 | 2021, 2022, 2023, 2024, 2025 |
| Maíz | Maíz blanco tecnificado | 336 | 2021, 2022, 2023, 2024, 2025 |
| Maíz | Maíz blanco tradicional | 1.174 | 2021, 2022, 2023, 2024, 2025 |
| Maíz | Maíz tecnificado | 202 | 2019, 2020 |
| Maíz | Maíz tradicional | 708 | 2019, 2020 |
| Yuca | Yuca consumo en fresco | 2.325 | 2019, 2020, 2021, 2022, 2023, 2024, 2025 |
| Yuca | Yuca industrial | 280 | 2019, 2020, 2021, 2022, 2023, 2024, 2025 |

## 4. Distribucion de `Periodo` (anual vs. semestral) por cultivo y anio

| Cultivo | Anio | Anual (`AAAA`) | Semestre A (`AAAAA`) | Semestre B (`AAAAB`) | Total semestral | Total registros |
| :--- | :---: | ---: | ---: | ---: | ---: | ---: |
| Arroz | 2019 | 0 | 128 | 130 | 258 | 258 |
| Arroz | 2020 | 0 | 124 | 130 | 254 | 254 |
| Arroz | 2021 | 0 | 125 | 125 | 250 | 250 |
| Arroz | 2022 | 0 | 125 | 137 | 262 | 262 |
| Arroz | 2023 | 0 | 127 | 137 | 264 | 264 |
| Arroz | 2024 | 0 | 129 | 135 | 264 | 264 |
| Arroz | 2025 | 0 | 131 | 136 | 267 | 267 |
| Maíz | 2019 | 0 | 233 | 220 | 453 | 453 |
| Maíz | 2020 | 0 | 233 | 224 | 457 | 457 |
| Maíz | 2021 | 0 | 400 | 387 | 787 | 787 |
| Maíz | 2022 | 0 | 401 | 386 | 787 | 787 |
| Maíz | 2023 | 0 | 388 | 385 | 773 | 773 |
| Maíz | 2024 | 0 | 375 | 381 | 756 | 756 |
| Maíz | 2025 | 0 | 376 | 381 | 757 | 757 |
| Yuca | 2019 | 0 | 202 | 118 | 320 | 320 |
| Yuca | 2020 | 0 | 204 | 124 | 328 | 328 |
| Yuca | 2021 | 0 | 206 | 127 | 333 | 333 |
| Yuca | 2022 | 0 | 211 | 187 | 398 | 398 |
| Yuca | 2023 | 0 | 217 | 188 | 405 | 405 |
| Yuca | 2024 | 0 | 216 | 191 | 407 | 407 |
| Yuca | 2025 | 0 | 219 | 195 | 414 | 414 |

## 5. Validacion cruzada de rendimiento reportado vs. `produccion / area_cosechada`

- **Filas evaluadas con `area_cosechada > 0`**: 8.405 de 9.194
- **Diferencia absoluta mediana (`|rendimiento - produccion/area_cosechada|`)**: 0,000000 t/ha
- **Percentil 95 de diferencia absoluta**: 0,002823 t/ha
- **Diferencia absoluta maxima**: 0,005000 t/ha
- **Filas con diferencia relativa > 1 %**: 8 (0,10 %)

### Las 10 filas con mayor diferencia relativa en la base filtrada

| Codigo Mpio | Municipio | Depto | Cultivo | Desagregacion | Periodo | Area cosechada (ha) | Produccion (t) | Rend. reportado | Rend. calculado | Dif. absoluta | Dif. relativa (%) |
| :---: | :--- | :--- | :--- | :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---:|
| `13140` | Calamar | Bolívar | Maíz | Maíz amarillo tradicional | `2023B` | 327,00 | 25,61 | 0,0800 | 0,0783 | 0,0017 | 2,15 % |
| `13140` | Calamar | Bolívar | Maíz | Maíz blanco tradicional | `2023B` | 72,00 | 5,64 | 0,0800 | 0,0783 | 0,0017 | 2,13 % |
| `08296` | Galapa | Atlántico | Maíz | Maíz amarillo tradicional | `2021A` | 40,00 | 13,42 | 0,3400 | 0,3355 | 0,0045 | 1,34 % |
| `08433` | Malambo | Atlántico | Maíz | Maíz amarillo tradicional | `2023B` | 103,00 | 17,28 | 0,1700 | 0,1678 | 0,0022 | 1,33 % |
| `13780` | Talaigua Nuevo | Bolívar | Maíz | Maíz blanco tradicional | `2021B` | 140,00 | 46,98 | 0,3400 | 0,3356 | 0,0044 | 1,32 % |
| `08832` | Tubará | Atlántico | Maíz | Maíz amarillo tradicional | `2021B` | 243,00 | 81,55 | 0,3400 | 0,3356 | 0,0044 | 1,31 % |
| `13780` | Talaigua Nuevo | Bolívar | Maíz | Maíz amarillo tradicional | `2021A` | 150,00 | 50,34 | 0,3400 | 0,3356 | 0,0044 | 1,31 % |
| `13838` | Turbaná | Bolívar | Maíz | Maíz blanco tradicional | `2021A` | 277,00 | 106,50 | 0,3800 | 0,3845 | 0,0045 | 1,16 % |
| `08137` | Campo de La Cruz | Atlántico | Maíz | Maíz amarillo tecnificado | `2021A` | 450,00 | 213,94 | 0,4800 | 0,4754 | 0,0046 | 0,96 % |
| `70473` | Morroa | Sucre | Maíz | Maíz blanco tradicional | `2022A` | 4,00 | 2,46 | 0,6200 | 0,6150 | 0,0050 | 0,81 % |

## 6. Anomalias de area y produccion

- **Filas con `area_cosechada > area_sembrada` (base filtrada)**: 2.015 (en base cruda nacional: 13.208)
- **Filas con `produccion > 0` y `area_cosechada == 0` (base filtrada)**: 0 (en base cruda nacional: 0)
- **Filas con `area_cosechada == 0` y `produccion == 0` (base filtrada)**: 789

### Distribucion por cultivo y anio de filas con `area_cosechada > area_sembrada`

| Cultivo | Anio | Filas con `area_cosechada > area_sembrada` | Exceso acumulado (ha) |
| :--- | :---: | ---: | ---: |
| Arroz | 2022 | 81 | 44.438,90 |
| Arroz | 2023 | 80 | 39.710,50 |
| Arroz | 2024 | 97 | 43.617,50 |
| Arroz | 2025 | 107 | 44.965,50 |
| Maíz | 2022 | 253 | 53.826,52 |
| Maíz | 2023 | 266 | 68.257,90 |
| Maíz | 2024 | 252 | 65.726,50 |
| Maíz | 2025 | 260 | 69.494,45 |
| Yuca | 2022 | 151 | 32.915,70 |
| Yuca | 2023 | 140 | 29.492,65 |
| Yuca | 2024 | 163 | 35.985,50 |
| Yuca | 2025 | 165 | 31.684,20 |

### Top 10 filas con mayor exceso `area_cosechada - area_sembrada` (base filtrada)

| Codigo Mpio | Municipio | Depto | Cultivo | Desagregacion | Periodo | Area sembrada (ha) | Area cosechada (ha) | Exceso (ha) | Produccion (t) |
| :---: | :--- | :--- | :--- | :--- | :---: | ---: | ---: | ---: | ---: |
| `70429` | Majagual | Sucre | Arroz | Arroz secano mecanizado | `2024B` | 2.050,00 | 12.060,00 | 10.010,00 | 62.712,00 |
| `70429` | Majagual | Sucre | Arroz | Arroz secano mecanizado | `2022B` | 2.900,00 | 11.800,00 | 8.900,00 | 60.180,00 |
| `70429` | Majagual | Sucre | Arroz | Arroz secano mecanizado | `2025B` | 6.269,00 | 13.596,00 | 7.327,00 | 88.374,00 |
| `13006` | Achí | Bolívar | Arroz | Arroz secano mecanizado | `2022B` | 6.660,00 | 13.321,00 | 6.661,00 | 46.623,50 |
| `70429` | Majagual | Sucre | Arroz | Arroz secano mecanizado | `2023B` | 2.100,00 | 8.040,00 | 5.940,00 | 41.808,00 |
| `23807` | Tierralta | Córdoba | Arroz | Arroz secano manual | `2022B` | 0,00 | 4.200,00 | 4.200,00 | 12.516,00 |
| `13006` | Achí | Bolívar | Arroz | Arroz secano mecanizado | `2023B` | 6.660,00 | 10.660,00 | 4.000,00 | 37.310,00 |
| `23807` | Tierralta | Córdoba | Arroz | Arroz secano manual | `2025B` | 0,00 | 3.210,00 | 3.210,00 | 9.630,00 |
| `23807` | Tierralta | Córdoba | Arroz | Arroz secano manual | `2024B` | 0,00 | 2.930,00 | 2.930,00 | 8.731,40 |
| `23855` | Valencia | Córdoba | Arroz | Arroz secano manual | `2024B` | 56,00 | 2.956,00 | 2.900,00 | 5.912,00 |

## 7. Totales por anio y cultivo (area sembrada, area cosechada y produccion)

| Cultivo | Anio | Registros | Area sembrada (ha) | Area cosechada (ha) | Area no cosechada (ha) | Produccion (t) | Rendimiento agregado (t/ha) |
| :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Arroz | 2019 | 258 | 145.901,38 | 142.286,95 | 3.614,43 | 620.053,14 | 4,3578 |
| Arroz | 2020 | 254 | 156.263,49 | 150.204,51 | 6.058,98 | 692.726,97 | 4,6119 |
| Arroz | 2021 | 250 | 155.552,00 | 118.785,70 | 36.766,30 | 501.545,54 | 4,2223 |
| Arroz | 2022 | 262 | 138.969,95 | 133.319,90 | 5.650,05 | 560.290,76 | 4,2026 |
| Arroz | 2023 | 264 | 134.261,00 | 126.854,00 | 7.407,00 | 529.990,41 | 4,1780 |
| Arroz | 2024 | 264 | 133.099,50 | 119.713,00 | 13.386,50 | 518.120,55 | 4,3280 |
| Arroz | 2025 | 267 | 129.832,25 | 129.106,05 | 726,20 | 560.487,22 | 4,3413 |
| Maíz | 2019 | 453 | 236.309,82 | 222.760,75 | 13.549,07 | 587.604,01 | 2,6378 |
| Maíz | 2020 | 457 | 260.068,18 | 239.632,18 | 20.436,00 | 662.101,25 | 2,7630 |
| Maíz | 2021 | 787 | 259.730,67 | 241.689,50 | 18.041,17 | 621.289,39 | 2,5706 |
| Maíz | 2022 | 787 | 251.083,49 | 231.996,35 | 19.087,14 | 607.541,49 | 2,6188 |
| Maíz | 2023 | 773 | 257.194,10 | 243.786,35 | 13.407,75 | 646.290,18 | 2,6511 |
| Maíz | 2024 | 756 | 258.125,10 | 239.847,40 | 18.277,70 | 591.308,42 | 2,4654 |
| Maíz | 2025 | 757 | 254.587,15 | 251.426,55 | 3.160,60 | 642.861,29 | 2,5569 |
| Yuca | 2019 | 320 | 116.276,74 | 109.928,47 | 6.348,27 | 1.239.615,63 | 11,2766 |
| Yuca | 2020 | 328 | 124.122,05 | 115.471,45 | 8.650,60 | 1.316.715,07 | 11,4029 |
| Yuca | 2021 | 333 | 118.822,96 | 111.127,00 | 7.695,96 | 1.214.741,20 | 10,9311 |
| Yuca | 2022 | 398 | 127.278,80 | 115.188,00 | 12.090,80 | 1.282.636,23 | 11,1352 |
| Yuca | 2023 | 405 | 147.029,35 | 118.892,65 | 28.136,70 | 1.340.232,08 | 11,2726 |
| Yuca | 2024 | 407 | 138.723,45 | 131.052,30 | 7.671,15 | 1.485.998,75 | 11,3390 |
| Yuca | 2025 | 414 | 139.280,03 | 127.477,20 | 11.802,83 | 1.457.016,90 | 11,4296 |

### Subtotales por cultivo (2019-2025)

| Cultivo | Registros | Area sembrada (ha) | Area cosechada (ha) | Area no cosechada (ha) | Produccion (t) | Rendimiento agregado (t/ha) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Arroz** | 1.819 | 993.879,57 | 920.270,11 | 73.609,46 | 3.983.214,59 | 4,3283 |
| **Maíz** | 4.770 | 1.777.098,51 | 1.671.139,08 | 105.959,43 | 4.358.996,03 | 2,6084 |
| **Yuca** | 2.605 | 911.533,38 | 829.137,07 | 82.396,31 | 9.336.955,86 | 11,2611 |
