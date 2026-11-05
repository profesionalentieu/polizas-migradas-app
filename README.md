# Pólizas migradas de TIME a Guidewire: qué se puede anticipar

Aplicación de Streamlit del trabajo final de **Aprendizaje Automático y Grandes Datos (IC)**, UNRaf (Universidad Nacional de Rafaela).
Autores: Agustín Bértola, Matías Bonafede y Agustín Ferrero.

- **Aplicación publicada:** https://polizas-migradas.streamlit.app/
- **Repositorio:** https://github.com/profesionalentieu/polizas-migradas-app

Una aseguradora migró su cartera de autos y motos del sistema TIME a Guidewire. Con los datos que cada póliza tenía en TIME, la
aplicación responde dos preguntas:

- **TP2 · ¿Cuánto paga por mes una póliza?** Regresión del logaritmo de la prima mensual: polinómica de grado 2 (interacciones entre
  categorías) con Lasso, elegida entre 17 modelos con validación cruzada por cliente.
- **TP3 · ¿Conviene revisar una póliza antes de migrarla?** Regresión logística que estima la probabilidad de que la póliza llegue a
  Guidewire sin código de titular, con un umbral elegido por costo y la regla del TP1 como comparación.

Además tiene páginas sobre los datos y la limpieza, el hallazgo del TP1, un tablero con tres vistas vinculadas y la metodología.

## Cómo ejecutarla en tu computadora

Hace falta **Python 3.13**. Desde la carpeta del repositorio:

```bash
python -m venv .venv
```

En Windows:

```bash
.venv\Scripts\activate
```

En macOS o Linux:

```bash
source .venv/bin/activate
```

Después, en los dos casos:

```bash
pip install -r requirements.txt
streamlit run app.py
```

La aplicación se abre en el navegador, en `http://localhost:8501`.

## Qué hay en el repositorio

| Archivo o carpeta | Qué es |
|---|---|
| `app.py` | Punto de entrada: la navegación entre páginas |
| `comun.py` | Carga de modelos y datos, formato de números, validación de entradas y registro de predicciones |
| `paginas/` | Una página por sección (inicio, datos y limpieza, TP1, tablero, TP2, TP3 y metodología) |
| `modelos/` | Los dos modelos, cada uno con todo su preprocesamiento, guardados con `joblib` (se usan sin reentrenar) |
| `datos/` | Tablas agregadas, resultados de los trabajos y pólizas inventadas para probar la carga en lote |
| `figuras/` | Gráficos de los resultados de los TP |
| `requirements.txt` | Dependencias con versiones exactas |

## Datos y privacidad

- **No hay ninguna fila del dataset original.** Las tablas de `datos/` son conteos, tasas y percentiles de grupos de **20 pólizas o más**.
  Los CSV de ejemplo son pólizas inventadas.
- **Los modelos son versiones públicas:** las unidades de negocios y los productos aparecen como «Unidad A, B…» y «Producto A, B…». En el
  TP2, la cartera (productor, organizador y oficial) entra con seudónimos por tamaño («Productor 1, 2…»), sin códigos; el TP3 no usa la
  cartera.
- Sus métricas son de **validación cruzada de 5 pliegues por cliente** sobre el entrenamiento. Los modelos públicos no se midieron en la
  prueba, para no volver a abrirla.

## Registro de predicciones

La aplicación guarda las predicciones en la sesión del navegador y permite descargarlas en CSV. En Streamlit Community Cloud los archivos
que escribe la aplicación se borran al reiniciarse, así que el registro no se guarda en el servidor: hay que descargarlo antes de cerrar.
