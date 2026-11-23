# Brecha potencial, escenarios y priorización — Región Caribe 2019-2025

- **Edición**: `caribe_2019_2025`
- **Región**: Caribe
- **Umbral de elegibilidad**: `500 ha` y `4` años con dato
- **Pesos por defecto del índice (0-100)**: ganancia `0,40`, brecha relativa `0,30`, estabilidad `0,15`, confiabilidad `0,15`
- **Sensibilidad de pesos**: `2.000` juegos Dirichlet(1, 1, 1, 1) con semilla `2026`
- **Tiempo total de ejecución**: `14,53 s`

## 1. Validaciones cruzadas de consistencia matemática

- **Municipios-sistema en o por encima de la referencia ($P_{75}$)**: `144` unidades — brecha máxima = `0,000000 t/ha`, ganancia máxima = `0,000000 t` (OK).
- **Linealidad exacta de S1 en la fracción $x$**: error máximo entre $S_1(0{,}5)$ y $0{,}5 \cdot S_1(1{,}0)$ = `0,000000000000 t` (OK).
- **Combinación sin doble conteo ($\max(S_1, S_2) + S_3$)**: verificado en el 100 % de los municipios elegibles que $\max(S_1, S_2) \le \text{Combinado} \le S_1 + S_2 + S_3$ en $p_{10}$, $p_{50}$ y $p_{90}$ (OK).
- **Rango e integridad del índice de prioridad**: `0` valores nulos en elegibles; rango observado `[12,56; 90,13]` dentro de `[0; 100]` y 100 % reproducible con semilla fija (OK).

## 2. Resumen de brecha potencial por cultivo y sistema (elegibles >= 500 ha)

| Cultivo | Sistema | Municipios elegibles | Con `referencia_regional` (< 5 en depto) | Con `rango_no_informativo` | Ganancia anual $p_{10}$ (t) | Ganancia anual $p_{50}$ (t) | Ganancia anual $p_{90}$ (t) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| Arroz | `riego` | 36 | 9 | 4 | 2.876,62 | 15.016,50 | 26.145,14 |
| Arroz | `secano_manual` | 52 | 1 | 7 | 19.797,29 | 31.291,10 | 42.057,35 |
| Arroz | `secano_mecanizado` | 28 | 1 | 3 | 6.948,96 | 34.032,83 | 70.051,30 |
| Maíz | `tecnificado` | 50 | 7 | 7 | 10.777,52 | 29.112,68 | 52.020,41 |
| Maíz | `tradicional` | 170 | 0 | 21 | 48.142,01 | 83.067,58 | 130.093,71 |
| Yuca | `fresco` | 171 | 0 | 67 | 108.846,65 | 199.882,29 | 348.207,55 |
| Yuca | `industrial` | 20 | 1 | 10 | 6.053,90 | 24.029,10 | 37.880,19 |

## 3. Totales regionales por cultivo de cada escenario al 100 % ($p_{10}$, $p_{50}$, $p_{90}$)

| Cultivo | Producción anual media (t) | S1 Cierre brecha $p_{50}$ (`[p10; p90]`) | S1 % prod. | S2 Tecnificación $p_{50}$ (`[p10; p90]`) | S2 % prod. | % S2 extrapolado | S3 Área no cosechada $p_{50}$ (`[p10; p90]`) | Combinado sin doble conteo $p_{50}$ (`[p10; p90]`) | Combinado % prod. |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Arroz** | 564.802,84 | 83.029,83 (`[69.205,42; 100.446,96]`) | 14,70 % | 60.400,03 (`[57.448,87; 63.562,55]`) | 10,69 % | 41,48 % | 45.344,23 (`[34.133,62; 60.315,68]`) | 156.841,58 (`[138.154,79; 178.932,89]`) | 27,77 % |
| **Maíz** | 621.552,04 | 116.954,67 (`[110.229,30; 123.808,98]`) | 18,82 % | 248.683,10 (`[242.694,04; 254.855,18]`) | 40,01 % | 55,81 % | 39.195,93 (`[34.982,77; 43.957,79]`) | 313.870,35 (`[305.975,57; 322.441,49]`) | 50,50 % |
| **Yuca** | 1.331.408,09 | 236.440,74 (`[220.270,90; 252.771,80]`) | 17,76 % | 0,00 (`[0,00; 0,00]`) | 0,00 % | 0,00 % | 0,00 (`[0,00; 0,00]`) | 236.440,74 (`[220.270,90; 252.771,80]`) | 17,76 % |

### 3.1. Comparación de la ganancia regional de S1 al 100 % frente a la estimación inicial de referencia

| Cultivo | Ganancia S1 $p_{50}$ (% prod. anual media) | Estimación inicial de referencia (%) | Diferencia (puntos porcentuales) | Explicación metodológica |
| :--- | ---: | ---: | ---: | :--- |
| Arroz | 14,70 % | 27,00 % | -12,30 pp | La diferencia supera 5 puntos porque S1 se evalúa estrictamente dentro de cada departamento y sistema productivo (evitando comparar secano manual contra riego o tradicional contra tecnificado en el mismo grupo de referencia $P_{75}$) y pondera por el área media anual de los sistemas elegibles (>= 500 ha). |
| Maíz | 18,82 % | 19,00 % | -0,18 pp | Diferencia menor o igual a 5 puntos porcentuales; consistente con la estimación inicial. |
| Yuca | 17,76 % | 16,00 % | 1,76 pp | Diferencia menor o igual a 5 puntos porcentuales; consistente con la estimación inicial. |

## 4. Tipología para la matriz de decisión: municipios elegibles por cuadrante y cultivo

| Cultivo | `consolidar` (alto, estable) | `proteger` (alto, volátil) | `tecnificar` (bajo, estable) | `intervencion_integral` (bajo, volátil) | `estabilidad_no_medible` (poco informativa) | Total elegibles |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Arroz** | 24 | 19 | 16 | 20 | 7 | 86 |
| **Maíz** | 43 | 46 | 41 | 37 | 13 | 180 |
| **Yuca** | 28 | 31 | 28 | 25 | 60 | 172 |

## 5. Sensibilidad del índice de prioridad a los pesos (2.000 juegos de Dirichlet)

| Cultivo | Municipios elegibles | Tau de Kendall mediana vs. ranking por defecto | Intervalo $[p_{10}; p_{90}]$ de Tau | Municipios con prioridad robusta (>= 80 % en Top 20) |
| :--- | ---: | ---: | :---: | ---: |
| **Arroz** | 86 | 0,7486 | `[0,4407; 0,8911]` | 7 |
| **Maíz** | 180 | 0,7290 | `[0,4190; 0,8734]` | 6 |
| **Yuca** | 172 | 0,7520 | `[0,4318; 0,8862]` | 5 |

## 6. Top 20 municipios prioritarios por cultivo

### 6.1. Top 20 en Arroz

| Rango | Código DANE | Municipio | Departamento | Índice (0-100) | Ganancia S1 $p_{50}$ (t) | Brecha rel. (%) | Rango mediano (`[p10; p90]`) | % Juegos en Top 20 | Prioridad robusta | Cuadrante |
| ---: | :---: | :--- | :--- | ---: | ---: | ---: | :---: | ---: | :---: | :--- |
| 1 | `70265` | Guaranda | Sucre | 85,66 | 8.933,15 | 20,99 % | 1,0 (`[1,0; 9,0]`) | 98,5 % | **Sí** | `tecnificar` |
| 2 | `23001` | Montería | Córdoba | 85,31 | 3.598,43 | 33,47 % | 3,0 (`[2,0; 6,0]`) | 100,0 % | **Sí** | `tecnificar` |
| 3 | `23807` | Tierralta | Córdoba | 84,45 | 4.945,24 | 20,63 % | 3,0 (`[2,0; 11,0]`) | 97,5 % | **Sí** | `consolidar` |
| 4 | `23555` | Planeta Rica | Córdoba | 83,11 | 4.346,60 | 64,97 % | 7,0 (`[1,0; 42,0]`) | 74,7 % | **No** | `tecnificar` |
| 5 | `70708` | San Marcos | Sucre | 83,02 | 4.299,50 | 42,18 % | 6,0 (`[3,0; 19,0]`) | 91,5 % | **Sí** | `tecnificar` |
| 6 | `23570` | Pueblo Nuevo | Córdoba | 81,88 | 4.497,19 | 53,79 % | 9,0 (`[1,0; 38,0]`) | 73,0 % | **No** | `intervencion_integral` |
| 7 | `70233` | El Roble | Sucre | 78,20 | 614,15 | 48,09 % | 6,0 (`[2,0; 15,0]`) | 96,4 % | **Sí** | `tecnificar` |
| 8 | `23580` | Puerto Libertador | Córdoba | 77,92 | 1.605,19 | 43,85 % | 11,0 (`[5,0; 31,0]`) | 77,8 % | **No** | `intervencion_integral` |
| 9 | `70400` | La Unión | Sucre | 77,76 | 870,75 | 67,44 % | 12,0 (`[2,0; 30,0]`) | 74,5 % | **No** | `intervencion_integral` |
| 10 | `13006` | Achí | Bolívar | 77,73 | 10.315,87 | 20,31 % | 14,0 (`[5,0; 29,0]`) | 70,7 % | **No** | `proteger` |
| 11 | `23466` | Montelíbano | Córdoba | 77,25 | 3.495,24 | 43,58 % | 15,0 (`[7,0; 43,0]`) | 62,5 % | **No** | `tecnificar` |
| 12 | `70771` | Sucre | Sucre | 76,20 | 1.874,55 | 33,11 % | 13,0 (`[5,0; 37,0]`) | 67,5 % | **No** | `tecnificar` |
| 13 | `13430` | Magangué | Bolívar | 74,05 | 1.433,81 | 29,67 % | 15,0 (`[10,0; 29,0]`) | 75,6 % | **No** | `intervencion_integral` |
| 14 | `20770` | San Martín | Cesar | 72,78 | 2.104,80 | 15,79 % | 14,0 (`[8,0; 26,0]`) | 77,3 % | **No** | `tecnificar` |
| 15 | `23660` | Sahagún | Córdoba | 72,10 | 918,29 | 23,63 % | 16,0 (`[12,0; 23,0]`) | 81,6 % | **Sí** | `consolidar` |
| 16 | `13442` | María La Baja | Bolívar | 71,89 | 1.282,22 | 40,36 % | 20,0 (`[9,0; 47,0]`) | 51,1 % | **No** | `proteger` |
| 17 | `13655` | San Jacinto del Cauca | Bolívar | 71,02 | 3.032,37 | 11,37 % | 17,0 (`[9,0; 32,0]`) | 62,8 % | **No** | `consolidar` |
| 18 | `23855` | Valencia | Córdoba | 71,01 | 4.088,63 | 41,20 % | 31,0 (`[13,0; 59,0]`) | 25,8 % | **No** | `intervencion_integral` |
| 19 | `23675` | San Bernardo del Viento | Córdoba | 70,33 | 636,85 | 16,86 % | 12,0 (`[5,0; 25,0]`) | 80,1 % | **Sí** | `consolidar` |
| 20 | `13810` | Tiquisio | Bolívar | 69,14 | 1.437,53 | 24,10 % | 24,0 (`[14,0; 47,0]`) | 38,1 % | **No** | `intervencion_integral` |

### 6.2. Top 20 en Maíz

| Rango | Código DANE | Municipio | Departamento | Índice (0-100) | Ganancia S1 $p_{50}$ (t) | Brecha rel. (%) | Rango mediano (`[p10; p90]`) | % Juegos en Top 20 | Prioridad robusta | Cuadrante |
| ---: | :---: | :--- | :--- | ---: | ---: | ---: | :---: | ---: | :---: | :--- |
| 1 | `20045` | Becerril | Cesar | 89,79 | 2.485,36 | 54,98 % | 3,0 (`[1,0; 11,0]`) | 98,2 % | **Sí** | `tecnificar` |
| 2 | `47288` | Fundación | Magdalena | 89,42 | 1.599,21 | 51,65 % | 2,0 (`[1,0; 4,0]`) | 100,0 % | **Sí** | `tecnificar` |
| 3 | `20001` | Valledupar | Cesar | 88,26 | 3.001,06 | 53,24 % | 5,0 (`[1,0; 33,1]`) | 81,8 % | **Sí** | `tecnificar` |
| 4 | `23189` | Ciénaga de Oro | Córdoba | 87,03 | 4.921,30 | 39,76 % | 6,0 (`[2,0; 15,0]`) | 96,3 % | **Sí** | `consolidar` |
| 5 | `47541` | Pedraza | Magdalena | 82,63 | 1.363,94 | 56,19 % | 12,0 (`[2,0; 66,0]`) | 63,1 % | **No** | `tecnificar` |
| 6 | `23660` | Sahagún | Córdoba | 82,40 | 1.726,34 | 33,69 % | 7,0 (`[3,0; 20,0]`) | 90,3 % | **Sí** | `consolidar` |
| 7 | `20032` | Astrea | Cesar | 81,84 | 2.507,46 | 44,68 % | 16,0 (`[8,0; 45,0]`) | 62,4 % | **No** | `tecnificar` |
| 8 | `70742` | San Luis de Sincé | Sucre | 80,70 | 1.142,02 | 50,86 % | 15,0 (`[5,0; 36,0]`) | 65,3 % | **No** | `tecnificar` |
| 9 | `13052` | Arjona | Bolívar | 80,37 | 3.936,16 | 47,06 % | 24,0 (`[9,0; 80,0]`) | 42,1 % | **No** | `tecnificar` |
| 10 | `13442` | María La Baja | Bolívar | 80,09 | 3.991,26 | 20,22 % | 8,0 (`[2,0; 45,0]`) | 74,2 % | **No** | `consolidar` |
| 11 | `13433` | Mahates | Bolívar | 79,06 | 3.128,85 | 36,27 % | 23,0 (`[6,0; 53,0]`) | 44,4 % | **No** | `proteger` |
| 12 | `47161` | Cerro de San Antonio | Magdalena | 78,48 | 695,27 | 49,76 % | 11,0 (`[5,0; 25,0]`) | 81,7 % | **Sí** | `tecnificar` |
| 13 | `70418` | Los Palmitos | Sucre | 78,43 | 414,69 | 60,92 % | 6,0 (`[1,0; 31,0]`) | 79,8 % | **No** | `tecnificar` |
| 14 | `20621` | La Paz | Cesar | 77,90 | 1.675,92 | 38,82 % | 23,0 (`[6,0; 77,0]`) | 46,8 % | **No** | `tecnificar` |
| 15 | `44078` | Barrancas | La Guajira | 77,72 | 1.148,83 | 37,71 % | 17,0 (`[11,0; 31,0]`) | 62,5 % | **No** | `tecnificar` |
| 16 | `47692` | San Sebastián de Buenavista | Magdalena | 77,49 | 1.621,82 | 49,60 % | 27,0 (`[9,0; 100,0]`) | 40,0 % | **No** | `tecnificar` |
| 17 | `13654` | San Jacinto | Bolívar | 77,35 | 2.662,80 | 30,64 % | 25,0 (`[8,0; 52,0]`) | 40,2 % | **No** | `tecnificar` |
| 18 | `23855` | Valencia | Córdoba | 76,87 | 2.657,95 | 30,42 % | 27,0 (`[9,0; 55,0]`) | 35,4 % | **No** | `consolidar` |
| 19 | `44874` | Villanueva | La Guajira | 76,46 | 765,27 | 53,04 % | 22,0 (`[8,0; 51,0]`) | 47,0 % | **No** | `tecnificar` |
| 20 | `23570` | Pueblo Nuevo | Córdoba | 75,30 | 1.622,93 | 38,91 % | 32,0 (`[11,0; 78,0]`) | 31,6 % | **No** | `intervencion_integral` |

### 6.3. Top 20 en Yuca

| Rango | Código DANE | Municipio | Departamento | Índice (0-100) | Ganancia S1 $p_{50}$ (t) | Brecha rel. (%) | Rango mediano (`[p10; p90]`) | % Juegos en Top 20 | Prioridad robusta | Cuadrante |
| ---: | :---: | :--- | :--- | ---: | ---: | ---: | :---: | ---: | :---: | :--- |
| 1 | `70473` | Morroa | Sucre | 90,13 | 3.937,15 | 47,00 % | 2,0 (`[1,0; 7,0]`) | 99,9 % | **Sí** | `tecnificar` |
| 2 | `23090` | Canalete | Córdoba | 86,52 | 6.041,19 | 40,45 % | 8,0 (`[2,0; 32,0]`) | 79,0 % | **No** | `tecnificar` |
| 3 | `23189` | Ciénaga de Oro | Córdoba | 86,19 | 12.094,63 | 27,50 % | 5,0 (`[1,0; 20,0]`) | 90,1 % | **Sí** | `consolidar` |
| 4 | `47053` | Aracataca | Magdalena | 85,78 | 3.789,26 | 34,91 % | 5,0 (`[1,0; 17,0]`) | 92,6 % | **Sí** | `tecnificar` |
| 5 | `70418` | Los Palmitos | Sucre | 85,00 | 4.968,64 | 30,67 % | 6,0 (`[3,0; 19,0]`) | 91,5 % | **Sí** | `tecnificar` |
| 6 | `20614` | Río de Oro | Cesar | 84,95 | 4.262,78 | 34,96 % | 8,0 (`[2,0; 26,0]`) | 83,9 % | **Sí** | `tecnificar` |
| 7 | `70508` | Ovejas | Sucre | 84,01 | 6.242,68 | 27,65 % | 9,0 (`[3,0; 31,0]`) | 76,8 % | **No** | `tecnificar` |
| 8 | `70233` | El Roble | Sucre | 82,13 | 5.166,66 | 43,66 % | 17,0 (`[3,0; 71,0]`) | 54,9 % | **No** | `intervencion_integral` |
| 9 | `47170` | Chivolo | Magdalena | 81,53 | 3.298,22 | 33,50 % | 11,0 (`[3,0; 36,0]`) | 71,3 % | **No** | `tecnificar` |
| 10 | `20550` | Pelaya | Cesar | 80,21 | 3.490,76 | 40,02 % | 17,0 (`[9,0; 44,1]`) | 59,0 % | **No** | `tecnificar` |
| 11 | `13468` | Santa Cruz de Mompox | Bolívar | 79,35 | 3.356,09 | 36,94 % | 19,0 (`[5,0; 58,0]`) | 54,1 % | **No** | `intervencion_integral` |
| 12 | `70742` | San Luis de Sincé | Sucre | 79,02 | 5.006,56 | 23,17 % | 19,0 (`[7,0; 47,0]`) | 52,1 % | **No** | `proteger` |
| 13 | `20570` | Pueblo Bello | Cesar | 79,01 | 5.242,35 | 46,29 % | 32,0 (`[9,0; 79,0]`) | 34,6 % | **No** | `estabilidad_no_medible` |
| 14 | `20228` | Curumaní | Cesar | 78,98 | 2.767,01 | 32,74 % | 16,0 (`[5,0; 41,0]`) | 57,8 % | **No** | `tecnificar` |
| 15 | `13836` | Turbaco | Bolívar | 78,65 | 4.829,31 | 59,32 % | 32,0 (`[8,0; 79,0]`) | 34,5 % | **No** | `estabilidad_no_medible` |
| 16 | `13873` | Villanueva | Bolívar | 78,33 | 9.714,52 | 32,18 % | 30,0 (`[10,0; 70,0]`) | 33,9 % | **No** | `intervencion_integral` |
| 17 | `23815` | Tuchín | Córdoba | 78,01 | 3.214,88 | 37,70 % | 22,0 (`[13,0; 49,0]`) | 45,8 % | **No** | `tecnificar` |
| 18 | `13580` | Regidor | Bolívar | 76,36 | 2.602,63 | 33,97 % | 24,0 (`[13,0; 49,0]`) | 37,2 % | **No** | `tecnificar` |
| 19 | `23670` | San Andrés de Sotavento | Córdoba | 75,78 | 3.509,95 | 36,79 % | 34,0 (`[19,0; 64,0]`) | 17,2 % | **No** | `intervencion_integral` |
| 20 | `70001` | Sincelejo | Sucre | 75,27 | 1.708,99 | 17,60 % | 9,0 (`[1,0; 41,1]`) | 73,8 % | **No** | `consolidar` |
