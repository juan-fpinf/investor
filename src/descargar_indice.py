
from pathlib import Path

import pandas as pd
import yfinance as yf


# ==========================================
# CONFIGURACIÓN
# ==========================================

SIMBOLO = "^GSPC"

FECHA_INICIO = "2021-10-01"
FECHA_FIN = "2026-11-01"  # Fecha final exclusiva

CARPETA_DATOS = Path("datos")
ARCHIVO_SALIDA = CARPETA_DATOS / "sp500_indice_2021_2026.csv"


# ==========================================
# DESCARGAR DATOS DEL ÍNDICE
# ==========================================

def main():
    CARPETA_DATOS.mkdir(parents=True, exist_ok=True)

    print("Descargando cotizaciones del índice S&P 500...")
    print(f"Periodo: {FECHA_INICIO} a 31/10/2026")

    try:
        datos = yf.download(
            tickers=SIMBOLO,
            start=FECHA_INICIO,
            end=FECHA_FIN,
            interval="1d",
            auto_adjust=False,
            actions=False,
            progress=False,
            timeout=30
        )

        if datos.empty:
            print("No se han recibido datos.")
            print("Comprueba la conexión e inténtalo de nuevo.")
            return

        # Algunas versiones de yfinance devuelven
        # columnas MultiIndex incluso para un solo símbolo.
        if isinstance(datos.columns, pd.MultiIndex):
            datos.columns = datos.columns.get_level_values(0)

        # Convertir el índice de fechas en una columna.
        datos.index.name = "Date"
        datos = datos.reset_index()

        # Identificar el índice bursátil.
        datos["Ticker"] = SIMBOLO

        # Ordenar las columnas.
        columnas = [
            "Date", "Ticker", "Open", "High",
            "Low", "Close", "Adj Close", "Volume"
        ]

        columnas_disponibles = [
            columna for columna in columnas
            if columna in datos.columns
        ]

        datos = datos[columnas_disponibles]

        # Guardar el CSV.
        datos.to_csv(
            ARCHIVO_SALIDA,
            index=False,
            encoding="utf-8-sig"
        )

        print("\nDescarga completada correctamente.")
        print(f"Sesiones bursátiles descargadas: {len(datos)}")
        print(f"Archivo generado: {ARCHIVO_SALIDA.resolve()}")

        print("\nÚltimas cotizaciones:")
        print(datos.tail().to_string(index=False))

    except Exception as error:
        print(f"Error durante la descarga: {error}")


if __name__ == "__main__":
    main()
