# Path permite guardar y comprobar rutas de archivos.
from pathlib import Path

# pyplot contiene las funciones para crear y mostrar gráficos.
import matplotlib.pyplot as plt
# pandas sirve para leer y organizar los datos del CSV.
import pandas as pd

# Ruta del archivo con las cotizaciones históricas del índice S&P 500.
ARCHIVO_DATOS = Path("datos/sp500_indice_2021_2026.csv")


# Función reutilizable: lee y devuelve la serie de precios del índice.
def cargar_indice():
    """Leer los cierres del índice y devolverlos ordenados por fecha."""
    # Comprobar que el CSV existe antes de intentar leerlo.
    if not ARCHIVO_DATOS.exists():
        # Lanzar un error claro para que quien llame a la función
        # sepa que hace falta descargar primero los datos del índice.
        raise FileNotFoundError(
            f"No se encuentra {ARCHIVO_DATOS}. Descarga primero el índice."
        )

    # Leer solo las columnas necesarias: la fecha y el precio de cierre.
    datos = pd.read_csv(ARCHIVO_DATOS, usecols=["Date", "Close"])
    # Convertir las fechas de texto a fechas que pandas puede ordenar y graficar.
    datos["Date"] = pd.to_datetime(datos["Date"])
    # Usar la fecha como índice, seleccionar los cierres y ordenarlos cronológicamente.
    return datos.set_index("Date")["Close"].sort_index()


# Función principal que prepara y muestra el gráfico del índice.
def main():
    # Intentar cargar los precios; cargar_indice puede fallar si falta el CSV.
    try:
        precios = cargar_indice()
    # Capturar específicamente el error de archivo ausente.
    except FileNotFoundError as error:
        # Mostrar la explicación del error al usuario.
        print(error)
        # Terminar sin intentar graficar datos que no existen.
        return

    # Dibujar la serie de precios; figsize define el tamaño y legend=False
    # oculta la leyenda porque solo hay una serie.
    precios.plot(figsize=(14, 8), legend=False)
    # Poner el título del gráfico.
    plt.title("Evolución del índice S&P 500")
    # Nombrar el eje horizontal, donde aparecen las fechas.
    plt.xlabel("Fecha")
    # Nombrar el eje vertical, que contiene los valores del índice.
    plt.ylabel("Valor del índice")
    # Mostrar una cuadrícula para ayudar a leer el gráfico.
    plt.grid(True)
    # Ajustar los márgenes para evitar que se corten etiquetas o título.
    plt.tight_layout()
    # Abrir la ventana con el gráfico.
    plt.show()


# Ejecutar main solo cuando este archivo se inicia directamente,
# y no cuando se importa desde otro módulo, como comparador.py.
if __name__ == "__main__":
    main()
