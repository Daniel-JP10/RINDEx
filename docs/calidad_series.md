# Diagnóstico de calidad de series y valores repetidos — Región Caribe 2019-2025

- **Edición**: `caribe_2019_2025`
- **Región**: Caribe
- **Criterio de `serie_poco_informativa`**: `proporcion_repetidos > 0,50` (más del 50 % de los pares de años consecutivos con rendimiento idéntico).

## 1. Repetición interanual en `anual_municipio_cultivo` (por cultivo)

| Cultivo | Series (>= 2 años) | Series 100 % constantes (%) | Pares consecutivos | Pares idénticos (%) | Series poco informativas (> 50 % rep.) |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Arroz | 109 | 2 (1,83 %) | 606 | 109 (17,99 %) | 8 (7,34 %) |
| Maíz | 189 | 4 (2,12 %) | 1.130 | 215 (19,03 %) | 15 (7,94 %) |
| Yuca | 189 | 16 (8,47 %) | 1.117 | 511 (45,75 %) | 67 (35,45 %) |

## 2. Repetición interanual en `anual_municipio_sistema` (por cultivo y sistema)

| Cultivo | Sistema | Series (>= 2 años) | Series 100 % constantes (%) | Pares consecutivos | Pares idénticos (%) | Series poco informativas (> 50 % rep.) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| Arroz | `riego` | 45 | 0 (0,00 %) | 239 | 56 (23,43 %) | 4 (8,89 %) |
| Arroz | `secano_manual` | 72 | 3 (4,17 %) | 406 | 133 (32,76 %) | 11 (15,28 %) |
| Arroz | `secano_mecanizado` | 35 | 0 (0,00 %) | 186 | 44 (23,66 %) | 3 (8,57 %) |
| Maíz | `tecnificado` | 63 | 5 (7,94 %) | 350 | 92 (26,29 %) | 12 (19,05 %) |
| Maíz | `tradicional` | 184 | 6 (3,26 %) | 1.093 | 300 (27,45 %) | 23 (12,50 %) |
| Yuca | `fresco` | 189 | 17 (8,99 %) | 1.117 | 581 (52,01 %) | 75 (39,68 %) |
| Yuca | `industrial` | 35 | 6 (17,14 %) | 137 | 68 (49,64 %) | 15 (42,86 %) |

## 3. Distribución de la longitud máxima de rachas de valor repetido por serie

### 3.1. En `anual_municipio_cultivo`

| Cultivo | Racha máx. = 1 | Racha = 2 | Racha = 3 | Racha = 4 | Racha = 5 | Racha = 6 | Racha = 7 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Arroz | 55 | 25 | 21 | 3 | 4 | 0 | 1 |
| Maíz | 89 | 53 | 25 | 14 | 3 | 1 | 4 |
| Yuca | 33 | 33 | 41 | 45 | 17 | 5 | 15 |

### 3.2. En `anual_municipio_sistema`

| Cultivo | Sistema | Racha máx. = 1 | Racha = 2 | Racha = 3 | Racha = 4 | Racha = 5 | Racha = 6 | Racha = 7 |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Arroz | `riego` | 17 | 15 | 8 | 2 | 3 | 0 | 0 |
| Arroz | `secano_manual` | 12 | 21 | 27 | 7 | 3 | 1 | 1 |
| Arroz | `secano_mecanizado` | 15 | 9 | 10 | 0 | 1 | 0 | 0 |
| Maíz | `tecnificado` | 20 | 22 | 12 | 4 | 4 | 0 | 1 |
| Maíz | `tradicional` | 54 | 61 | 37 | 20 | 5 | 1 | 6 |
| Yuca | `fresco` | 14 | 35 | 48 | 50 | 19 | 7 | 16 |
| Yuca | `industrial` | 7 | 13 | 6 | 3 | 5 | 1 | 0 |

## 4. Pendientes Theil-Sen iguales a cero en H1 y tratamiento en Wilcoxon

- **Método de tratamiento de ceros en `scipy.stats.wilcoxon`**: `zero_method='wilcox'` (descarta las diferencias exactamente iguales a cero antes de asignar rangos).

| Cultivo | Municipios elegibles (`n`) | Pendientes Theil-Sen = 0 | % Pendientes = 0 | `n` efectivo en Wilcoxon (`n != 0`) | Estadístico `W` | Valor `p` |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| Arroz | 86 | 8 | 9,30 % | 78 | 1.540,50 | 0,7030 |
| Maíz | 180 | 26 | 14,44 % | 154 | 4.659,50 | 0,0183 |
| Yuca | 172 | 51 | 29,65 % | 121 | 3.363,00 | 0,3969 |

## 5. Repetición semestral: rendimiento idéntico entre semestres A y B del mismo año

| Cultivo | Sistema | Pares A-B en el mismo municipio-año | Pares con `rendimiento_A == rendimiento_B` | Porcentaje idéntico A vs. B |
| :--- | :--- | ---: | ---: | ---: |
| Arroz | `riego` | 235 | 105 | 44,68 % |
| Arroz | `secano_manual` | 262 | 135 | 51,53 % |
| Arroz | `secano_mecanizado` | 134 | 46 | 34,33 % |
| Maíz | `tecnificado` | 376 | 176 | 46,81 % |
| Maíz | `tradicional` | 1.545 | 871 | 56,38 % |
| Yuca | `fresco` | 844 | 608 | 72,04 % |
| Yuca | `industrial` | 48 | 33 | 68,75 % |

## 6. Concentración en valores redondos frente a distribución uniforme

- **Referencia uniforme en 2 decimales (`0,00` a `0,99`)**: `1,00 %` enteros exactos (`,00`); `2,00 %` terminados en `,00` o `,50`; `10,00 %` terminados en un decimal exacto (`,X0`, incluidos `,00` y `,50`).
- **Referencia uniforme en 1 decimal (`,0` a `,9`)**: `10,00 %` enteros exactos (`,0`); `20,00 %` terminados en `,0` o `,5`.

### 6.1. Filas semestrales con cosecha positiva (`eva_limpia`)

| Cultivo | Sistema | Filas (`area_cosechada > 0`) | Enteros exactos (`,00`) | Terminados en `,00` o `,50` (múltiplos de 0,5) | Terminados en `,X0` (1 decimal) |
| :--- | :--- | ---: | ---: | ---: | ---: |
| Arroz | `riego` | 522 | 168 (32,18 %) | 213 (40,80 %) | 262 (50,19 %) |
| Arroz | `secano_manual` | 742 | 220 (29,65 %) | 334 (45,01 %) | 467 (62,94 %) |
| Arroz | `secano_mecanizado` | 358 | 71 (19,83 %) | 133 (37,15 %) | 219 (61,17 %) |
| Maíz | `tecnificado` | 970 | 441 (45,46 %) | 670 (69,07 %) | 898 (92,58 %) |
| Maíz | `tradicional` | 3.435 | 1.204 (35,05 %) | 1.895 (55,17 %) | 2.870 (83,55 %) |
| Yuca | `fresco` | 2.152 | 1.952 (90,71 %) | 2.046 (95,07 %) | 2.096 (97,40 %) |
| Yuca | `industrial` | 226 | 214 (94,69 %) | 220 (97,35 %) | 223 (98,67 %) |

### 6.2. Series anuales agregadas (`anual_municipio_sistema`)

| Cultivo | Sistema | Registros anuales (`area_cosechada > 0`) | Enteros exactos (`,00`) | Terminados en `,00` o `,50` | Terminados en `,X0` |
| :--- | :--- | ---: | ---: | ---: | ---: |
| Arroz | `riego` | 287 | 77 (26,83 %) | 95 (33,10 %) | 110 (38,33 %) |
| Arroz | `secano_manual` | 480 | 113 (23,54 %) | 168 (35,00 %) | 231 (48,12 %) |
| Arroz | `secano_mecanizado` | 224 | 35 (15,62 %) | 62 (27,68 %) | 102 (45,54 %) |
| Maíz | `tecnificado` | 418 | 122 (29,19 %) | 173 (41,39 %) | 226 (54,07 %) |
| Maíz | `tradicional` | 1.280 | 286 (22,34 %) | 445 (34,77 %) | 644 (50,31 %) |
| Yuca | `fresco` | 1.308 | 1.003 (76,68 %) | 1.048 (80,12 %) | 1.075 (82,19 %) |
| Yuca | `industrial` | 178 | 157 (88,20 %) | 160 (89,89 %) | 162 (91,01 %) |
