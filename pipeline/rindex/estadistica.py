"""Funciones estadisticas puras no parametricas, tamanos de efecto, bootstrap y permutacion."""

import itertools
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class ResultadoWilcoxon:
    n: int
    estadistico: float
    valor_p: float
    r_biserial_pareado: float


@dataclass(frozen=True)
class ResultadoKruskal:
    n_total: int
    k_grupos: int
    estadistico_h: float
    valor_p: float
    epsilon_cuadrado: float


@dataclass(frozen=True)
class ResultadoFriedman:
    n_bloques: int
    k_tratamientos: int
    estadistico_chi2: float
    valor_p: float
    w_kendall: float


@dataclass(frozen=True)
class ResultadoMannWhitney:
    n_x: int
    n_y: int
    estadistico_u: float
    valor_p: float
    r_biserial: float


@dataclass(frozen=True)
class ResultadoSpearmanExacto:
    n: int
    rho: float
    valor_p_exacto: float


def ajustar_p_holm(valores_p: Sequence[float] | np.ndarray) -> np.ndarray:
    arr = np.asarray(valores_p, dtype=float)
    resultado = np.full_like(arr, np.nan, dtype=float)
    mascara_valida = ~np.isnan(arr)
    p_validos = arr[mascara_valida]
    m = len(p_validos)
    if m == 0:
        return resultado

    orden = np.argsort(p_validos, kind="mergesort")
    p_ordenados = p_validos[orden]
    factores = m - np.arange(m, dtype=float)
    ajustados_ord = np.minimum(1.0, np.maximum.accumulate(p_ordenados * factores))

    ajustados = np.empty(m, dtype=float)
    ajustados[orden] = ajustados_ord
    resultado[mascara_valida] = ajustados
    return resultado


def ajustar_p_benjamini_hochberg(valores_p: Sequence[float] | np.ndarray) -> np.ndarray:
    arr = np.asarray(valores_p, dtype=float)
    resultado = np.full_like(arr, np.nan, dtype=float)
    mascara_valida = ~np.isnan(arr)
    p_validos = arr[mascara_valida]
    if len(p_validos) == 0:
        return resultado

    ajustados = stats.false_discovery_control(p_validos, method="bh")
    resultado[mascara_valida] = np.clip(ajustados, 0.0, 1.0)
    return resultado


def calcular_pendiente_theil_sen(
    tiempos: Sequence[float] | np.ndarray,
    valores: Sequence[float] | np.ndarray,
) -> float:
    x = np.asarray(tiempos, dtype=float)
    y = np.asarray(valores, dtype=float)
    n = len(x)
    if n < 2:
        return float("nan")
    res = stats.theilslopes(y, x, method="separate")
    return float(res.slope)


def calcular_pendientes_municipales(
    df_anual_mpio_cultivo: pd.DataFrame,
    anios_minimos: int = 4,
) -> pd.DataFrame:
    df_pos = df_anual_mpio_cultivo.loc[df_anual_mpio_cultivo["area_cosechada"] > 0].sort_values(
        ["codigo_dane_municipio", "cultivo", "anio"]
    )
    if df_pos.empty:
        return pd.DataFrame(
            columns=[
                "codigo_dane_municipio",
                "cultivo",
                "codigo_dane_departamento",
                "municipio",
                "anios_con_dato",
                "rendimiento_medio",
                "pendiente_theil_sen",
                "pendiente_pct_anual",
            ]
        )

    cod_mpio = df_pos["codigo_dane_municipio"].to_numpy()
    cultivo_arr = df_pos["cultivo"].to_numpy()
    depto_arr = df_pos["codigo_dane_departamento"].to_numpy()
    nom_mpio = df_pos["municipio"].to_numpy()
    anios_arr = df_pos["anio"].to_numpy(dtype=float)
    rend_arr = df_pos["rendimiento"].to_numpy(dtype=float)
    prod_arr = df_pos["produccion"].to_numpy(dtype=float)
    area_arr = df_pos["area_cosechada"].to_numpy(dtype=float)

    cambio = (
        np.nonzero((cod_mpio[1:] != cod_mpio[:-1]) | (cultivo_arr[1:] != cultivo_arr[:-1]))[0] + 1
    )
    inicios = np.concatenate(([0], cambio))
    fines = np.concatenate((cambio, [len(df_pos)]))

    filas_out: list[dict[str, object]] = []
    for ini, fin in zip(inicios, fines, strict=True):
        k = int(fin - ini)
        if k < anios_minimos:
            continue
        x = anios_arr[ini:fin]
        y = rend_arr[ini:fin]
        i_idx, j_idx = np.triu_indices(k, k=1)
        pend = float(np.median((y[j_idx] - y[i_idx]) / (x[j_idx] - x[i_idx])))
        rend_medio = float(prod_arr[ini:fin].sum() / area_arr[ini:fin].sum())
        pend_pct = (pend / rend_medio * 100.0) if rend_medio > 0 else float("nan")
        filas_out.append(
            {
                "codigo_dane_municipio": str(cod_mpio[ini]),
                "cultivo": str(cultivo_arr[ini]),
                "codigo_dane_departamento": str(depto_arr[ini]),
                "municipio": str(nom_mpio[ini]),
                "anios_con_dato": k,
                "rendimiento_medio": rend_medio,
                "pendiente_theil_sen": pend,
                "pendiente_pct_anual": pend_pct,
            }
        )

    return pd.DataFrame(filas_out)


def estimador_hodges_lehmann_diferencia(
    diferencias: Sequence[float] | np.ndarray,
) -> float:
    d = np.asarray(diferencias, dtype=float)
    d = d[~np.isnan(d)]
    n = len(d)
    if n == 0:
        return float("nan")
    tri_i, tri_j = np.triu_indices(n)
    promedios_walsh = 0.5 * (d[tri_i] + d[tri_j])
    return float(np.median(promedios_walsh))


def estimador_hodges_lehmann_log_razon(
    diferencias_log: Sequence[float] | np.ndarray,
) -> tuple[float, float]:
    hl_log = estimador_hodges_lehmann_diferencia(diferencias_log)
    if np.isnan(hl_log):
        return float("nan"), float("nan")
    return hl_log, float(np.exp(hl_log))


def prueba_wilcoxon_pareada(
    diferencias: Sequence[float] | np.ndarray,
    alternativa: str = "two-sided",
) -> ResultadoWilcoxon:
    d = np.asarray(diferencias, dtype=float)
    d = d[~np.isnan(d)]
    n_total = len(d)
    d_nz = d[d != 0.0]
    n_nz = len(d_nz)
    if n_nz == 0:
        return ResultadoWilcoxon(
            n=n_total,
            estadistico=0.0,
            valor_p=1.0,
            r_biserial_pareado=0.0,
        )

    res = stats.wilcoxon(d_nz, zero_method="wilcox", alternative=alternativa)
    rangos = stats.rankdata(np.abs(d_nz))
    w_pos = float(np.sum(rangos[d_nz > 0]))
    w_neg = float(np.sum(rangos[d_nz < 0]))
    suma_rangos = w_pos + w_neg
    r_biserial = (w_pos - w_neg) / suma_rangos if suma_rangos > 0 else 0.0

    return ResultadoWilcoxon(
        n=n_total,
        estadistico=float(res.statistic),
        valor_p=float(res.pvalue),
        r_biserial_pareado=float(r_biserial),
    )


def prueba_kruskal_wallis(grupos: Sequence[Sequence[float] | np.ndarray]) -> ResultadoKruskal:
    limpios = [np.asarray(g, dtype=float)[~np.isnan(np.asarray(g, dtype=float))] for g in grupos]
    limpios = [g for g in limpios if len(g) > 0]
    k = len(limpios)
    n_total = int(sum(len(g) for g in limpios))
    if k < 2 or n_total <= k:
        return ResultadoKruskal(
            n_total=n_total,
            k_grupos=k,
            estadistico_h=float("nan"),
            valor_p=float("nan"),
            epsilon_cuadrado=float("nan"),
        )

    res = stats.kruskal(*limpios)
    h = float(res.statistic)
    eps2 = float(np.clip(h / (n_total - 1), 0.0, 1.0)) if n_total > 1 else float("nan")
    return ResultadoKruskal(
        n_total=n_total,
        k_grupos=k,
        estadistico_h=h,
        valor_p=float(res.pvalue),
        epsilon_cuadrado=eps2,
    )


def prueba_friedman(matriz_bloques: np.ndarray) -> ResultadoFriedman:
    mat = np.asarray(matriz_bloques, dtype=float)
    if mat.ndim != 2:
        raise ValueError("La matriz para Friedman debe ser bidimensional (bloques x tratamientos).")
    mascara_completos = ~np.isnan(mat).any(axis=1)
    mat_limpia = mat[mascara_completos]
    n_bloques, k_trat = mat_limpia.shape
    if n_bloques < 2 or k_trat < 3:
        return ResultadoFriedman(
            n_bloques=int(n_bloques),
            k_tratamientos=int(k_trat),
            estadistico_chi2=float("nan"),
            valor_p=float("nan"),
            w_kendall=float("nan"),
        )

    columnas = [mat_limpia[:, j] for j in range(k_trat)]
    res = stats.friedmanchisquare(*columnas)
    chi2 = float(res.statistic)
    w_kendall = float(np.clip(chi2 / (n_bloques * (k_trat - 1)), 0.0, 1.0))
    return ResultadoFriedman(
        n_bloques=int(n_bloques),
        k_tratamientos=int(k_trat),
        estadistico_chi2=chi2,
        valor_p=float(res.pvalue),
        w_kendall=w_kendall,
    )


def prueba_mann_whitney(
    x: Sequence[float] | np.ndarray,
    y: Sequence[float] | np.ndarray,
    alternativa: str = "two-sided",
) -> ResultadoMannWhitney:
    arr_x = np.asarray(x, dtype=float)
    arr_y = np.asarray(y, dtype=float)
    arr_x = arr_x[~np.isnan(arr_x)]
    arr_y = arr_y[~np.isnan(arr_y)]
    n_x, n_y = len(arr_x), len(arr_y)
    if n_x == 0 or n_y == 0:
        return ResultadoMannWhitney(
            n_x=n_x,
            n_y=n_y,
            estadistico_u=float("nan"),
            valor_p=float("nan"),
            r_biserial=float("nan"),
        )

    res = stats.mannwhitneyu(arr_x, arr_y, alternative=alternativa)
    u_stat = float(res.statistic)
    r_biserial = float((2.0 * u_stat) / (n_x * n_y) - 1.0)
    return ResultadoMannWhitney(
        n_x=n_x,
        n_y=n_y,
        estadistico_u=u_stat,
        valor_p=float(res.pvalue),
        r_biserial=r_biserial,
    )


def prueba_spearman_permutacion_exacta(
    x: Sequence[float] | np.ndarray,
    y: Sequence[float] | np.ndarray,
) -> ResultadoSpearmanExacto:
    arr_x = np.asarray(x, dtype=float)
    arr_y = np.asarray(y, dtype=float)
    mascara = ~(np.isnan(arr_x) | np.isnan(arr_y))
    arr_x = arr_x[mascara]
    arr_y = arr_y[mascara]
    n = len(arr_x)
    if n < 3:
        return ResultadoSpearmanExacto(n=n, rho=float("nan"), valor_p_exacto=float("nan"))

    res_sp = stats.spearmanr(arr_x, arr_y)
    rho_obs = float(res_sp.statistic)
    if np.isnan(rho_obs):
        return ResultadoSpearmanExacto(n=n, rho=0.0, valor_p_exacto=1.0)

    r_x = stats.rankdata(arr_x)
    r_y = stats.rankdata(arr_y)
    dx = r_x - np.mean(r_x)
    norm_dx = float(np.linalg.norm(dx))
    if norm_dx == 0.0 or float(np.linalg.norm(r_y - np.mean(r_y))) == 0.0:
        return ResultadoSpearmanExacto(n=n, rho=0.0, valor_p_exacto=1.0)

    matriz_perm = np.array(list(itertools.permutations(r_y)), dtype=float)
    dp = matriz_perm - np.mean(r_y)
    norm_dp = np.linalg.norm(dp, axis=1)
    rhos = (dp @ dx) / (norm_dx * norm_dp)

    extremos = int(np.sum(np.abs(rhos) >= (abs(rho_obs) - 1e-12)))
    valor_p = float(extremos / len(rhos))
    return ResultadoSpearmanExacto(n=n, rho=rho_obs, valor_p_exacto=valor_p)


def remuestrear_municipios_completos(
    df: pd.DataFrame,
    semilla: int,
    col_municipio: str = "codigo_dane_municipio",
) -> pd.DataFrame:
    rng = np.random.default_rng(semilla)
    municipios_unicos = np.sort(df[col_municipio].unique())
    n_mpios = len(municipios_unicos)
    seleccionados = rng.choice(municipios_unicos, size=n_mpios, replace=True)

    grupos = {mpio: sub for mpio, sub in df.groupby(col_municipio, sort=False)}
    partes = [
        grupos[mpio].assign(_id_clon_bootstrap=idx_clon)
        for idx_clon, mpio in enumerate(seleccionados)
    ]
    return pd.concat(partes, ignore_index=True)


def bootstrap_mediana_vectorizado(
    valores_municipales: Sequence[float] | np.ndarray,
    semilla: int,
    replicas: int = 5000,
    nivel_confianza: float = 0.95,
) -> tuple[float, float]:
    arr = np.asarray(valores_municipales, dtype=float)
    arr = arr[~np.isnan(arr)]
    n = len(arr)
    if n < 2:
        return float("nan"), float("nan")

    rng = np.random.default_rng(semilla)
    indices = rng.integers(0, n, size=(replicas, n))
    medianas = np.median(arr[indices], axis=1)

    alfa = 1.0 - nivel_confianza
    inf, sup = np.quantile(medianas, [alfa / 2.0, 1.0 - alfa / 2.0])
    return float(inf), float(sup)


def bootstrap_hodges_lehmann_vectorizado(
    valores_municipales: Sequence[float] | np.ndarray,
    semilla: int,
    replicas: int = 5000,
    exponenciar: bool = False,
    nivel_confianza: float = 0.95,
) -> tuple[float, float]:
    arr = np.asarray(valores_municipales, dtype=float)
    arr = arr[~np.isnan(arr)]
    n = len(arr)
    if n < 2:
        return float("nan"), float("nan")

    rng = np.random.default_rng(semilla)
    indices = rng.integers(0, n, size=(replicas, n))
    tri_i, tri_j = np.triu_indices(n)

    tamano_lote = 500
    estimaciones = np.empty(replicas, dtype=float)
    for inicio in range(0, replicas, tamano_lote):
        fin = min(inicio + tamano_lote, replicas)
        muestra_lote = arr[indices[inicio:fin]]
        walsh_lote = 0.5 * (muestra_lote[:, tri_i] + muestra_lote[:, tri_j])
        estimaciones[inicio:fin] = np.median(walsh_lote, axis=1)

    if exponenciar:
        estimaciones = np.exp(estimaciones)

    alfa = 1.0 - nivel_confianza
    inf, sup = np.quantile(estimaciones, [alfa / 2.0, 1.0 - alfa / 2.0])
    return float(inf), float(sup)


def bootstrap_epsilon_cuadrado_vectorizado(
    valores_municipales: Sequence[float] | np.ndarray,
    codigos_grupo: Sequence[str] | np.ndarray,
    semilla: int,
    replicas: int = 5000,
    nivel_confianza: float = 0.95,
) -> tuple[float, float]:
    vals = np.asarray(valores_municipales, dtype=float)
    grps = np.asarray(codigos_grupo)
    mascara = ~np.isnan(vals)
    vals = vals[mascara]
    grps = grps[mascara]
    n = len(vals)
    _, ids_grupo = np.unique(grps, return_inverse=True)
    k = int(ids_grupo.max() + 1) if n > 0 else 0
    if n <= k or k < 2:
        return float("nan"), float("nan")

    rng = np.random.default_rng(semilla)
    indices = rng.integers(0, n, size=(replicas, n))
    val_boot = vals[indices]
    grp_boot = ids_grupo[indices]
    rangos = stats.rankdata(val_boot, axis=1)

    suma_r2_sobre_n = np.zeros(replicas, dtype=float)
    grupos_presentes = np.zeros(replicas, dtype=int)
    for g in range(k):
        m_g = grp_boot == g
        n_g = m_g.sum(axis=1)
        r_g = np.where(m_g, rangos, 0.0).sum(axis=1)
        activo = n_g > 0
        grupos_presentes += activo.astype(int)
        suma_r2_sobre_n += np.where(activo, (r_g * r_g) / np.maximum(n_g, 1), 0.0)

    h_boot = (12.0 / (n * (n + 1.0))) * suma_r2_sobre_n - 3.0 * (n + 1.0)
    eps2_boot = np.where(grupos_presentes >= 2, np.clip(h_boot / (n - 1.0), 0.0, 1.0), np.nan)
    validas = eps2_boot[~np.isnan(eps2_boot)]
    if len(validas) < 2:
        return float("nan"), float("nan")

    alfa = 1.0 - nivel_confianza
    inf, sup = np.quantile(validas, [alfa / 2.0, 1.0 - alfa / 2.0])
    return float(inf), float(sup)


def bootstrap_w_kendall_vectorizado(
    matriz_bloques: np.ndarray,
    semilla: int,
    replicas: int = 5000,
    nivel_confianza: float = 0.95,
) -> tuple[float, float]:
    mat = np.asarray(matriz_bloques, dtype=float)
    mat = mat[~np.isnan(mat).any(axis=1)]
    n, k = mat.shape
    if n < 2 or k < 3:
        return float("nan"), float("nan")

    rangos_bloques = stats.rankdata(mat, axis=1)
    rng = np.random.default_rng(semilla)
    indices = rng.integers(0, n, size=(replicas, n))
    rangos_boot = rangos_bloques[indices]
    sumas_col = rangos_boot.sum(axis=1)
    chi2_boot = (12.0 / (n * k * (k + 1.0))) * np.sum(sumas_col * sumas_col, axis=1) - (
        3.0 * n * (k + 1.0)
    )
    w_boot = np.clip(chi2_boot / (n * (k - 1.0)), 0.0, 1.0)

    alfa = 1.0 - nivel_confianza
    inf, sup = np.quantile(w_boot, [alfa / 2.0, 1.0 - alfa / 2.0])
    return float(inf), float(sup)
