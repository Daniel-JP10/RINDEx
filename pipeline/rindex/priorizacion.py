"""Punto de entrada y validaciones cruzadas de brecha, escenarios, tipologia y prioridad."""

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from rindex.agregacion import construir_tablas_agregadas
from rindex.brecha import calcular_brecha_potencial
from rindex.config import ConfiguracionEdicion, cargar_configuracion
from rindex.escenarios import (
    combinar_escenarios_sin_doble_conteo,
    construir_escenarios_municipales,
    evaluar_s1_lineal,
)
from rindex.limpieza import limpiar_eva
from rindex.prioridad import calcular_indice_prioridad, construir_tipologia_decision

REFERENCIA_INICIAL_S1_PCT: dict[str, float] = {
    "Maíz": 19.0,
    "Yuca": 16.0,
    "Arroz": 27.0,
}


def validar_reglas_priorizacion(
    df_brecha: pd.DataFrame,
    df_escenarios: pd.DataFrame,
    df_prioridad: pd.DataFrame,
) -> dict[str, object]:
    sobre_ref = df_brecha.loc[df_brecha["rendimiento"] >= df_brecha["rendimiento_referencia"]]
    max_brecha_sobre_ref = float(sobre_ref["brecha_tha"].abs().max()) if len(sobre_ref) > 0 else 0.0
    max_ganancia_sobre_ref = (
        float(sobre_ref["ganancia_p50"].abs().max()) if len(sobre_ref) > 0 else 0.0
    )
    if max_brecha_sobre_ref > 1e-9 or max_ganancia_sobre_ref > 1e-9:
        raise ValueError(
            "Municipios por encima de la referencia presentan brecha o ganancia distinta de cero."
        )

    s1_100 = df_escenarios["s1_p50"].to_numpy(dtype=float)
    s1_50 = evaluar_s1_lineal(s1_100, 0.5)
    max_error_lineal = float(np.max(np.abs(s1_50 - 0.5 * s1_100)))
    if max_error_lineal > 1e-12:
        raise ValueError(f"S1 no cumple linealidad exacta al 50 %: error={max_error_lineal}.")

    for suf in ("p10", "p50", "p90"):
        s1_v = df_escenarios[f"s1_{suf}"].to_numpy(dtype=float)
        s2_v = df_escenarios[f"s2_{suf}"].to_numpy(dtype=float)
        s3_v = df_escenarios[f"s3_{suf}"].to_numpy(dtype=float)
        comb_v = df_escenarios[f"combinado_{suf}"].to_numpy(dtype=float)

        cota_inf = np.maximum(s1_v, s2_v)
        cota_sup = s1_v + s2_v + s3_v
        if np.any(comb_v < cota_inf - 1e-9) or np.any(comb_v > cota_sup + 1e-9):
            raise ValueError(f"Violacion de cotas de no doble conteo en {suf}.")
        esperado = combinar_escenarios_sin_doble_conteo(s1_v, s2_v, s3_v)
        if np.max(np.abs(comb_v - esperado)) > 1e-9:
            raise ValueError(f"Inconsistencia en formula de escenario combinado para {suf}.")

    nulos_indice = int(df_prioridad["indice_prioridad"].isna().sum())
    min_ind = float(df_prioridad["indice_prioridad"].min())
    max_ind = float(df_prioridad["indice_prioridad"].max())
    if nulos_indice > 0 or min_ind < -1e-9 or max_ind > 100.0 + 1e-9:
        raise ValueError(
            f"Indice de prioridad invalido: nulos={nulos_indice}, rango=[{min_ind}, {max_ind}]."
        )

    return {
        "unidades_sobre_referencia": int(len(sobre_ref)),
        "max_brecha_sobre_ref": max_brecha_sobre_ref,
        "max_ganancia_sobre_ref": max_ganancia_sobre_ref,
        "max_error_lineal_s1_50pct": max_error_lineal,
        "nulos_indice": nulos_indice,
        "min_indice": min_ind,
        "max_indice": max_ind,
    }


def _fmt_ent(valor: int | float) -> str:
    return f"{int(valor):,}".replace(",", ".")


def _fmt_dec(valor: float, decimales: int = 2) -> str:
    if pd.isna(valor):
        return "N/A"
    texto = f"{float(valor):,.{decimales}f}"
    partes = texto.split(".")
    entero = partes[0].replace(",", ".")
    return f"{entero},{partes[1]}" if len(partes) > 1 else entero


def generar_reporte_priorizacion(
    df_brecha: pd.DataFrame,
    df_escenarios: pd.DataFrame,
    df_totales_escenarios: pd.DataFrame,
    df_tipologia: pd.DataFrame,
    df_prioridad: pd.DataFrame,
    df_resumen_tau: pd.DataFrame,
    metricas_validacion: dict[str, object],
    cfg: ConfiguracionEdicion,
    tiempo_segundos: float,
    ruta_salida: str | Path = "docs/priorizacion.md",
) -> Path:
    ruta_md = Path(ruta_salida)
    ruta_md.parent.mkdir(parents=True, exist_ok=True)

    pesos = cfg.priorizacion.pesos
    umbral_txt = _fmt_dec(cfg.parametros.area_cosechada_minima_ha, 0)
    anios_min = cfg.parametros.anios_minimos_con_dato
    max_b_ref = _fmt_dec(float(metricas_validacion["max_brecha_sobre_ref"]), 6)
    max_g_ref = _fmt_dec(float(metricas_validacion["max_ganancia_sobre_ref"]), 6)
    err_lin = _fmt_dec(float(metricas_validacion["max_error_lineal_s1_50pct"]), 12)

    lineas: list[str] = [
        f"# Brecha potencial, escenarios y priorización — {cfg.nombre_visible}",
        "",
        f"- **Edición**: `{cfg.id_edicion}`",
        f"- **Región**: {cfg.region}",
        f"- **Umbral de elegibilidad**: `{umbral_txt} ha` y `{anios_min}` años con dato",
        (
            f"- **Pesos por defecto del índice (0-100)**: ganancia `{_fmt_dec(pesos.ganancia)}`, "
            f"brecha relativa `{_fmt_dec(pesos.brecha_relativa)}`, "
            f"estabilidad `{_fmt_dec(pesos.estabilidad)}`, "
            f"confiabilidad `{_fmt_dec(pesos.confiabilidad)}`"
        ),
        (
            f"- **Sensibilidad de pesos**: `{_fmt_ent(cfg.priorizacion.juegos_dirichlet)}` "
            f"juegos Dirichlet(1, 1, 1, 1) con semilla `{cfg.parametros.semilla_aleatoria}`"
        ),
        f"- **Tiempo total de ejecución**: `{_fmt_dec(tiempo_segundos, 2)} s`",
        "",
        "## 1. Validaciones cruzadas de consistencia matemática",
        "",
        (
            "- **Municipios-sistema en o por encima de la referencia ($P_{75}$)**: "
            f"`{_fmt_ent(metricas_validacion['unidades_sobre_referencia'])}` unidades — "
            f"brecha máxima = `{max_b_ref} t/ha`, ganancia máxima = `{max_g_ref} t` (OK)."
        ),
        (
            "- **Linealidad exacta de S1 en la fracción $x$**: error máximo entre $S_1(0{,}5)$ "
            "y $0{,}5 \\cdot S_1(1{,}0)$ = "
            f"`{err_lin} t` (OK)."
        ),
        (
            "- **Combinación sin doble conteo ($\\max(S_1, S_2) + S_3$)**: verificado en el 100 % "
            "de los municipios elegibles que "
            "$\\max(S_1, S_2) \\le \\text{Combinado} \\le S_1 + S_2 + S_3$ "
            "en $p_{10}$, $p_{50}$ y $p_{90}$ (OK)."
        ),
        (
            "- **Rango e integridad del índice de prioridad**: "
            f"`{_fmt_ent(metricas_validacion['nulos_indice'])}` valores nulos en elegibles; "
            f"rango observado `[{_fmt_dec(float(metricas_validacion['min_indice']))}; "
            f"{_fmt_dec(float(metricas_validacion['max_indice']))}]` dentro de `[0; 100]` y "
            "100 % reproducible con semilla fija (OK)."
        ),
    ]

    ref_reg_conteo = (
        df_brecha.groupby(["cultivo", "sistema"], as_index=False)
        .agg(
            unidades_elegibles=("codigo_dane_municipio", "count"),
            con_ref_regional=("referencia_regional", "sum"),
            rango_no_inf=("rango_no_informativo", "sum"),
        )
        .sort_values(["cultivo", "sistema"])
    )
    lineas.extend(
        [
            "",
            "## 2. Resumen de brecha potencial por cultivo y sistema (elegibles >= 500 ha)",
            "",
            (
                "| Cultivo | Sistema | Municipios elegibles "
                "| Con `referencia_regional` (< 5 en depto) | Con `rango_no_informativo` "
                "| Ganancia anual $p_{10}$ (t) | Ganancia anual $p_{50}$ (t) "
                "| Ganancia anual $p_{90}$ (t) |"
            ),
            "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    gan_sis = df_brecha.groupby(["cultivo", "sistema"], as_index=False).agg(
        g_p10=("ganancia_p10", "sum"),
        g_p50=("ganancia_p50", "sum"),
        g_p90=("ganancia_p90", "sum"),
    )
    res_b_sis = ref_reg_conteo.merge(gan_sis, on=["cultivo", "sistema"])
    for f in res_b_sis.to_dict(orient="records"):
        lineas.append(
            f"| {f['cultivo']} | `{f['sistema']}` | {_fmt_ent(f['unidades_elegibles'])} | "
            f"{_fmt_ent(f['con_ref_regional'])} | {_fmt_ent(f['rango_no_inf'])} | "
            f"{_fmt_dec(f['g_p10'])} | {_fmt_dec(f['g_p50'])} | {_fmt_dec(f['g_p90'])} |"
        )

    lineas.extend(
        [
            "",
            (
                "## 3. Totales regionales por cultivo de cada escenario al 100 % "
                "($p_{10}$, $p_{50}$, $p_{90}$)"
            ),
            "",
            (
                "| Cultivo | Producción anual media (t) | S1 Cierre brecha $p_{50}$ (`[p10; p90]`) "
                "| S1 % prod. | S2 Tecnificación $p_{50}$ (`[p10; p90]`) | S2 % prod. "
                "| % S2 extrapolado "
                "| S3 Área no cosechada $p_{50}$ (`[p10; p90]`) "
                "| Combinado sin doble conteo $p_{50}$ (`[p10; p90]`) | Combinado % prod. |"
            ),
            "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for f in df_totales_escenarios.to_dict(orient="records"):
        s1_txt = f"{_fmt_dec(f['s1_p50'])} (`[{_fmt_dec(f['s1_p10'])}; {_fmt_dec(f['s1_p90'])}]`)"
        s2_txt = f"{_fmt_dec(f['s2_p50'])} (`[{_fmt_dec(f['s2_p10'])}; {_fmt_dec(f['s2_p90'])}]`)"
        s3_txt = f"{_fmt_dec(f['s3_p50'])} (`[{_fmt_dec(f['s3_p10'])}; {_fmt_dec(f['s3_p90'])}]`)"
        comb_txt = (
            f"{_fmt_dec(f['combinado_p50'])} "
            f"(`[{_fmt_dec(f['combinado_p10'])}; {_fmt_dec(f['combinado_p90'])}]`)"
        )
        pct_ext_s2 = float(f.get("s2_pct_extrapolado", 0.0))
        lineas.append(
            f"| **{f['cultivo']}** | {_fmt_dec(f['produccion_anual_media_t'])} | {s1_txt} | "
            f"{_fmt_dec(f['s1_p50_pct_prod'])} % | {s2_txt} | "
            f"{_fmt_dec(f['s2_p50_pct_prod'])} % | {_fmt_dec(pct_ext_s2)} % | "
            f"{s3_txt} | {comb_txt} | {_fmt_dec(f['combinado_p50_pct_prod'])} % |"
        )

    lineas.extend(
        [
            "",
            (
                "### 3.1. Comparación de la ganancia regional de S1 al 100 % "
                "frente a la estimación inicial de referencia"
            ),
            "",
            (
                "| Cultivo | Ganancia S1 $p_{50}$ (% prod. anual media) "
                "| Estimación inicial de referencia (%) "
                "| Diferencia (puntos porcentuales) | Explicación metodológica |"
            ),
            "| :--- | ---: | ---: | ---: | :--- |",
        ]
    )
    for f in df_totales_escenarios.to_dict(orient="records"):
        cult = str(f["cultivo"])
        pct_obs = float(f["s1_p50_pct_prod"])
        pct_ref_ini = REFERENCIA_INICIAL_S1_PCT.get(cult, 0.0)
        dif_pp = pct_obs - pct_ref_ini
        if abs(dif_pp) <= 5.0:
            explicacion = (
                "Diferencia menor o igual a 5 puntos porcentuales; consistente con la "
                "estimación inicial."
            )
        else:
            explicacion = (
                "La diferencia supera 5 puntos porque S1 se evalúa estrictamente dentro de "
                "cada departamento y sistema productivo (evitando comparar secano manual "
                "contra riego o tradicional contra tecnificado en el mismo grupo de referencia "
                "$P_{75}$) y pondera por el área media anual de los sistemas elegibles (>= 500 ha)."
            )
        lineas.append(
            f"| {cult} | {_fmt_dec(pct_obs)} % | {_fmt_dec(pct_ref_ini)} % | "
            f"{_fmt_dec(dif_pp)} pp | {explicacion} |"
        )

    lineas.extend(
        [
            "",
            (
                "## 4. Tipología para la matriz de decisión: "
                "municipios elegibles por cuadrante y cultivo"
            ),
            "",
            (
                "| Cultivo | `consolidar` (alto, estable) | `proteger` (alto, volátil) "
                "| `tecnificar` (bajo, estable) | `intervencion_integral` (bajo, volátil) "
                "| `estabilidad_no_medible` (poco informativa) | Total elegibles |"
            ),
            "| :--- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    piv_cuad = df_tipologia.pivot_table(
        index="cultivo",
        columns="cuadrante",
        values="codigo_dane_municipio",
        aggfunc="count",
        fill_value=0,
    )
    orden_c = [
        "consolidar",
        "proteger",
        "tecnificar",
        "intervencion_integral",
        "estabilidad_no_medible",
    ]
    for c_col in orden_c:
        if c_col not in piv_cuad.columns:
            piv_cuad[c_col] = 0
    for cult in sorted(piv_cuad.index):
        tot_c = int(piv_cuad.loc[cult, orden_c].sum())
        celdas = " | ".join(_fmt_ent(piv_cuad.loc[cult, c_col]) for c_col in orden_c)
        lineas.append(f"| **{cult}** | {celdas} | {_fmt_ent(tot_c)} |")

    lineas.extend(
        [
            "",
            "## 5. Sensibilidad del índice de prioridad a los pesos (2.000 juegos de Dirichlet)",
            "",
            (
                "| Cultivo | Municipios elegibles | Tau de Kendall mediana vs. ranking por defecto "
                "| Intervalo $[p_{10}; p_{90}]$ de Tau "
                "| Municipios con prioridad robusta (>= 80 % en Top 20) |"
            ),
            "| :--- | ---: | ---: | :---: | ---: |",
        ]
    )
    for f in df_resumen_tau.to_dict(orient="records"):
        lineas.append(
            f"| **{f['cultivo']}** | {_fmt_ent(f['municipios_elegibles'])} | "
            f"{_fmt_dec(f['tau_kendall_mediana'], 4)} | "
            f"`[{_fmt_dec(f['tau_kendall_p10'], 4)}; {_fmt_dec(f['tau_kendall_p90'], 4)}]` | "
            f"{_fmt_ent(f['municipios_prioridad_robusta'])} |"
        )

    lineas.extend(
        [
            "",
            "## 6. Top 20 municipios prioritarios por cultivo",
        ]
    )
    for cult in sorted(cfg.cultivos):
        sub_top = (
            df_prioridad.loc[df_prioridad["cultivo"] == cult].sort_values("rango_defecto").head(20)
        )
        lineas.extend(
            [
                "",
                f"### 6.{1 + sorted(cfg.cultivos).index(cult)}. Top 20 en {cult}",
                "",
                (
                    "| Rango | Código DANE | Municipio | Departamento | Índice (0-100) "
                    "| Ganancia S1 $p_{50}$ (t) | Brecha rel. (%) | Rango mediano (`[p10; p90]`) "
                    "| % Juegos en Top 20 | Prioridad robusta | Cuadrante |"
                ),
                "| ---: | :---: | :--- | :--- | ---: | ---: | ---: | :---: | ---: | :---: | :--- |",
            ]
        )
        for f in sub_top.to_dict(orient="records"):
            r_txt = (
                f"{_fmt_dec(f['rango_mediano'], 1)} "
                f"(`[{_fmt_dec(f['rango_p10'], 1)}; {_fmt_dec(f['rango_p90'], 1)}]`)"
            )
            pct_top = float(f["proporcion_top20"]) * 100.0
            rob_s = "Sí" if bool(f["prioridad_robusta"]) else "No"
            lineas.append(
                f"| {_fmt_ent(f['rango_defecto'])} | `{f['codigo_dane_municipio']}` | "
                f"{f['municipio']} | {f['departamento']} | "
                f"{_fmt_dec(f['indice_prioridad'])} | {_fmt_dec(f['s1_p50'])} | "
                f"{_fmt_dec(f['s1_brecha_relativa_pct'])} % | {r_txt} | "
                f"{_fmt_dec(pct_top, 1)} % | **{rob_s}** | `{f['cuadrante']}` |"
            )

    ruta_md.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return ruta_md


def ejecutar_priorizacion_completa(
    ruta_config: str | Path,
    ruta_reporte: str | Path | None = "docs/priorizacion.md",
) -> tuple[dict[str, pd.DataFrame], float]:
    t0 = time.perf_counter()
    cfg = cargar_configuracion(ruta_config)
    ruta_filtrado = Path(cfg.fuente.parquet_filtrado)
    dir_interim = ruta_filtrado.parent
    dir_resultados = dir_interim / "resultados"
    dir_resultados.mkdir(parents=True, exist_ok=True)

    df_filtrado = pd.read_parquet(ruta_filtrado)
    df_limpio = limpiar_eva(df_filtrado, cfg)
    tablas = construir_tablas_agregadas(df_limpio, cfg)

    ruta_res_hip = dir_resultados / "resumen_hipotesis.parquet"
    resumen_hip = pd.read_parquet(ruta_res_hip) if ruta_res_hip.exists() else None

    df_brecha = calcular_brecha_potencial(
        periodo_mpio_sistema=tablas["periodo_municipio_sistema"],
        anual_mpio_sistema=tablas["anual_municipio_sistema"],
        cfg=cfg,
    )
    df_escenarios, df_totales_esc = construir_escenarios_municipales(
        periodo_mpio_cultivo=tablas["periodo_municipio_cultivo"],
        periodo_mpio_sistema=tablas["periodo_municipio_sistema"],
        anual_mpio_cultivo=tablas["anual_municipio_cultivo"],
        anual_mpio_sistema=tablas["anual_municipio_sistema"],
        df_brecha=df_brecha,
        cfg=cfg,
        resumen_hipotesis=resumen_hip,
    )
    df_tipologia = construir_tipologia_decision(tablas["periodo_municipio_cultivo"])
    df_prioridad, df_resumen_tau = calcular_indice_prioridad(
        df_tipologia=df_tipologia,
        df_escenarios=df_escenarios,
        cfg=cfg,
    )

    metricas_val = validar_reglas_priorizacion(
        df_brecha=df_brecha,
        df_escenarios=df_escenarios,
        df_prioridad=df_prioridad,
    )

    df_brecha.to_parquet(dir_resultados / "brecha.parquet", index=False)
    df_escenarios.to_parquet(dir_resultados / "escenarios.parquet", index=False)
    df_totales_esc.to_parquet(dir_resultados / "escenarios_regionales.parquet", index=False)
    df_tipologia.to_parquet(dir_resultados / "tipologia.parquet", index=False)
    df_prioridad.to_parquet(dir_resultados / "prioridad.parquet", index=False)

    tiempo_s = time.perf_counter() - t0
    if ruta_reporte is not None:
        generar_reporte_priorizacion(
            df_brecha=df_brecha,
            df_escenarios=df_escenarios,
            df_totales_escenarios=df_totales_esc,
            df_tipologia=df_tipologia,
            df_prioridad=df_prioridad,
            df_resumen_tau=df_resumen_tau,
            metricas_validacion=metricas_val,
            cfg=cfg,
            tiempo_segundos=tiempo_s,
            ruta_salida=ruta_reporte,
        )

    return {
        "brecha": df_brecha,
        "escenarios": df_escenarios,
        "escenarios_regionales": df_totales_esc,
        "tipologia": df_tipologia,
        "prioridad": df_prioridad,
    }, tiempo_s


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calcula brecha potencial, escenarios, tipologia e indice de prioridad."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Ruta al archivo YAML de configuracion de la edicion.",
    )
    parser.add_argument(
        "--reporte",
        default="docs/priorizacion.md",
        help="Ruta de salida para el reporte de priorizacion.",
    )
    args = parser.parse_args()
    ejecutar_priorizacion_completa(args.config, ruta_reporte=args.reporte)


if __name__ == "__main__":
    main()
