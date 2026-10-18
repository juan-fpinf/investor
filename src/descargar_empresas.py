
from pathlib import Path
from datetime import date
import time

import pandas as pd
import yfinance as yf


# ==========================================
# CONFIGURACIÓN
# ==========================================

FECHA_INICIO = "2021-10-01"
FECHA_FIN = "2026-11-01"  # Fecha final exclusiva

CARPETA_DATOS = Path("datos")
ARCHIVO_SALIDA = CARPETA_DATOS / "sp500_empresas_2021_2026.csv"
ARCHIVO_ERRORES = CARPETA_DATOS / "errores_descarga.csv"

TAMANO_LOTE = 50


# ==========================================
# 1. OBTENER LA LISTA DEL S&P 500
# ==========================================


def obtener_empresas():
    print("Obteniendo la lista de empresas del S&P 500...")

    url = (
        "https://raw.githubusercontent.com/"
        "Ate329/top-us-stock-tickers/main/tickers/sp500.csv"
    )

    try:
        empresas = pd.read_csv(url)

        # Comprobar que existe la columna de símbolos.
        if "symbol" not in empresas.columns:
            raise ValueError(
                f"No se encuentra la columna 'symbol'. "
                f"Columnas recibidas: {list(empresas.columns)}"
            )

        simbolos = (
            empresas["symbol"]
            .dropna()
            .astype(str)
            .str.strip()
            .str.replace(".", "-", regex=False)
        )

        simbolos = sorted(set(
            simbolo for simbolo in simbolos
            if simbolo and simbolo.lower() != "nan"
        ))

        if not simbolos:
            raise ValueError("La lista de símbolos está vacía.")

        print(f"Símbolos encontrados: {len(simbolos)}")
        return simbolos

    except Exception as error:
        print(f"No se pudo obtener la lista de empresas: {error}")
        return []



# ==========================================
# 2. DESCARGAR LAS COTIZACIONES
# ==========================================

def descargar_lote(simbolos):
    """
    Descarga un lote de símbolos y transforma
    las columnas en una tabla convencional.
    """

    datos = yf.download(
        tickers=simbolos,
        start=FECHA_INICIO,
        end=FECHA_FIN,
        interval="1d",
        group_by="ticker",
        auto_adjust=False,
        actions=False,
        threads=True,
        progress=False,
        timeout=30,
        multi_level_index=True
    )

    if datos is None or datos.empty:
        return pd.DataFrame(), list(simbolos)

    resultados = []
    fallidos = []

    for simbolo in simbolos:
        try:
            # Con varios símbolos, yfinance devuelve
            # columnas organizadas por ticker y precio.
            if isinstance(datos.columns, pd.MultiIndex):
                if simbolo not in datos.columns.get_level_values(0):
                    # En algunas versiones el orden puede variar.
                    if simbolo not in datos.columns.get_level_values(1):
                        fallidos.append(simbolo)
                        continue

                    empresa = datos.xs(
                        simbolo, axis=1, level=1
                    ).copy()
                else:
                    empresa = datos[simbolo].copy()
            else:
                if len(simbolos) != 1:
                    fallidos.append(simbolo)
                    continue

                empresa = datos.copy()

            # Descartar sesiones sin cotización.
            columnas_precio = [
                c for c in ["Open", "High", "Low", "Close", "Volume"]
                if c in empresa.columns
            ]

            if not columnas_precio:
                fallidos.append(simbolo)
                continue

            empresa = empresa.dropna(
                subset=["Close"] if "Close" in empresa.columns
                else columnas_precio
            )

            if empresa.empty:
                fallidos.append(simbolo)
                continue

            empresa.index.name = "Date"
            empresa = empresa.reset_index()
            empresa["Ticker"] = simbolo

            resultados.append(empresa)

        except Exception as error:
            print(f"Error con {simbolo}: {error}")
            fallidos.append(simbolo)

    if resultados:
        return pd.concat(resultados, ignore_index=True), fallidos

    return pd.DataFrame(), fallidos


# ==========================================
# 3. PROCESO PRINCIPAL
# ==========================================

def main():
    CARPETA_DATOS.mkdir(parents=True, exist_ok=True)

    simbolos = obtener_empresas()

    if not simbolos:
        print("No se ha obtenido la lista de símbolos.")
        return

    # Evitar mezclar resultados de ejecuciones anteriores.
    if ARCHIVO_SALIDA.exists():
        ARCHIVO_SALIDA.unlink()

    errores = []
    total_registros = 0

    numero_lotes = (
        len(simbolos) + TAMANO_LOTE - 1
    ) // TAMANO_LOTE

    for inicio in range(0, len(simbolos), TAMANO_LOTE):
        lote = simbolos[inicio:inicio + TAMANO_LOTE]
        numero_lote = inicio // TAMANO_LOTE + 1

        print(
            f"\nLote {numero_lote}/{numero_lotes}: "
            f"descargando {len(lote)} símbolos..."
        )

        try:
            datos, fallidos = descargar_lote(lote)

            if not datos.empty:
                # Escribir por lotes para no acumular
                # todos los datos en memoria.
                datos.to_csv(
                    ARCHIVO_SALIDA,
                    mode="a",
                    index=False,
                    header=not ARCHIVO_SALIDA.exists(),
                    encoding="utf-8-sig"
                )

                total_registros += len(datos)
                descargados = datos["Ticker"].nunique()

                print(
                    f"Empresas con datos: {descargados} | "
                    f"Registros: {len(datos)}"
                )
            else:
                print("El lote no ha devuelto cotizaciones.")

            for simbolo in fallidos:
                errores.append({
                    "Ticker": simbolo,
                    "Error": "Sin datos o descarga fallida"
                })

        except Exception as error:
            print(f"Error en el lote: {error}")

            for simbolo in lote:
                errores.append({
                    "Ticker": simbolo,
                    "Error": str(error)
                })

        # Pausa breve entre lotes.
        time.sleep(2)

    # Guardar el informe de errores.
    if errores:
        pd.DataFrame(errores).drop_duplicates(
            subset=["Ticker"]
        ).to_csv(
            ARCHIVO_ERRORES,
            index=False,
            encoding="utf-8-sig"
        )

    print("\n" + "=" * 50)
    print("DESCARGA FINALIZADA")
    print("=" * 50)
    print(f"Periodo solicitado: {FECHA_INICIO} a 31/10/2026")
    print(f"Registros descargados: {total_registros}")

    if ARCHIVO_SALIDA.exists():
        resultado = pd.read_csv(ARCHIVO_SALIDA)
        print(f"Empresas con datos: {resultado['Ticker'].nunique()}")
        print(f"Archivo: {ARCHIVO_SALIDA.resolve()}")
    else:
        print("No se ha generado el CSV. Revisa la conexión y los errores.")

    if errores:
        print(f"Símbolos con incidencias: {len(errores)}")
        print(f"Informe de incidencias: {ARCHIVO_ERRORES.resolve()}")


if __name__ == "__main__":
    main()
