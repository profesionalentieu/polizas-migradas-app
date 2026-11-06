# Metodología, en pestañas: cómo validamos, la fuga, la regla de las 15 particiones, los laboratorios aplicados, los problemas y el uso de IA
import pandas as pd
import streamlit as st
from comun import pie

st.title("Metodología")
st.caption("Cómo validamos, qué técnicas de la cátedra usamos, qué problemas aparecieron, cómo trabajamos con IA y los límites del trabajo.")

pestanas = st.tabs(["Cómo evitamos engañarnos", "Laboratorios aplicados", "Problemas y soluciones", "Trabajo con IA", "Límites"])

with pestanas[0]:
    st.markdown("""
    - **Partición por cliente.** El 20 % de los clientes quedó aparte desde el principio, para la prueba final. Todas las pólizas de un
      cliente quedan del mismo lado.
    - **Validación cruzada de 5 pliegues, también por cliente.** Los modelos se comparan y se eligen ahí, nunca con la prueba. En el TP3,
      además, cada pliegue tiene la misma proporción de fallas.
    - **Todo lo que se aprende de los datos, dentro de cada pliegue.** El escalado, la agrupación de categorías raras, la codificación
      y la búsqueda de hiperparámetros (con una segunda validación cruzada adentro, por cliente) se ajustan solo con el entrenamiento
      de cada pliegue, con un `Pipeline`.
    - **La prueba solo informa.** En el TP3 se abrió una sola vez, al final. En el TP2 se abrió dos veces (la segunda, para informar
      las métricas de todos los modelos que pide la consigna), y se declara. Los modelos de esta aplicación se midieron solo en validación.
    - **La regla de las 15 particiones.** Un modelo nuevo reemplaza al actual solo si gana en los 5 pliegues por más que el desvío entre
      pliegues, y si la diferencia se sostiene en 15 particiones más. Cuatro variantes parecían ganar; solo una se sostuvo.
    - **La fuga, medida.** Usar como dato algo que solo se conoce después (por ejemplo, lo que sale de Guidewire, o el premio, que
      incluye la prima) infla los resultados. Lo dejamos afuera y medimos cuánto inflaba: con el premio, el R² del TP2 pasa de 0,52 a 0,999.
    """)

with pestanas[1]:
    labs = pd.DataFrame([
        ("LAB01", "Entorno reproducible", "Entorno virtual con versiones exactas, semilla única y datos verificados con su huella"),
        ("LAB02", "Manipulación e integración", "Lectura del Excel sin pérdidas, tipos, duplicados y diccionario de datos"),
        ("LAB03", "Visualización exploratoria", "Descriptiva, asimetría de la prima y razón de correlación eta² para ordenar las variables"),
        ("LAB04", "Limpieza y transformación", "Faltantes, imputación por regla con bandera y comparación de estrategias de imputación"),
        ("LAB05", "Flujos de trabajo y fuga de datos", "Partición por cliente antes de mirar, flujo entero dentro de cada pliegue y modelo guardado"),
        ("LAB06", "Tablero interactivo", "El tablero de esta aplicación, con tres vistas vinculadas"),
        ("LAB07", "Validación y métricas de regresión", "Validación cruzada por cliente, curvas de aprendizaje y el optimismo de elegir, medido"),
        ("LAB08", "Métricas de clasificación", "Matriz de confusión, curvas de precisión y exhaustividad, umbral por costo y calibración"),
        ("LAB09", "Modelos lineales", "La misma recta por tres caminos, polinómica, Ridge contra Lasso y coeficientes de la logística"),
        ("LAB10", "Clasificadores comparados", "Todos los clasificadores del TP3 con el mismo protocolo y la misma línea de base"),
    ], columns=["laboratorio", "tema", "cómo lo usamos"])
    st.dataframe(labs, hide_index=True)
    st.caption("Fuera del material cargado, y declarados: ensambles y K-Means (los pide la consigna; documentación de scikit-learn), SMOTE "
               "(imbalanced-learn), la codificación por objetivo, la validación estratificada por cliente y la vuelta a pesos con el factor de "
               "Duan (1983). En esta aplicación, los gráficos interactivos usan Altair en lugar de plotly.")

with pestanas[2]:
    problemas = pd.DataFrame([
        ("Varias pólizas del mismo cliente", "Partición y validación por cliente", "Ningún cliente en los dos lados"),
        ("Columnas que «saben» la respuesta", "Escenario estricto y ampliado; la fuga se mide", "En el TP3 la fuga es chica; en el TP2, el premio llevaba el R² a 0,999"),
        ("Diferencias de milésimas que parecen ganancias", "Regla de los 5 pliegues y confirmación con 15 particiones", "Se sostuvo una de cuatro"),
        ("La falla es rara (6,8 %) y la exactitud engaña", "Precisión promedio y umbral elegido por costo", "Revisar una de cada cuatro pólizas en lugar de más de la mitad"),
        ("Volver del logaritmo a pesos subestima la suma", "Factor de Duan para totales; sin él para una póliza", "El total del lote cierra y el error por póliza es menor"),
        ("Los residuos no tienen varianza constante", "El error se informa por tramo de prima", "Esta aplicación muestra el error del tramo de cada estimación"),
        ("Ningún modelo pasa de cierto nivel", "Curvas de aprendizaje", "Faltan variables (el vehículo, la suma asegurada, la zona), no filas"),
        ("La cartera y los nombres identifican a la empresa", "Etiquetas genéricas para unidades y productos, y seudónimos para la cartera", "Esta aplicación no tiene nada que identifique a la empresa"),
    ], columns=["problema", "qué hicimos", "resultado"])
    st.dataframe(problemas, hide_index=True)

with pestanas[3]:
    st.markdown("""
    Usamos un asistente de programación con IA para escribir código, ejecutar el cuaderno y redactar borradores. Las reglas fueron:
    el equipo aprueba cada decisión antes de aplicarla; toda técnica cita la clase o el laboratorio de donde sale; cada cifra de los
    informes se verifica contra la salida del cuaderno; y los intentos que no funcionaron quedan en el cuaderno, con su motivo.
    La limpieza que había hecho otra IA antes se usó solo como consulta, y sus errores quedaron documentados.
    """)

with pestanas[4]:
    st.markdown("""
    - La base no tiene las variables con las que se calcula el precio, y la empresa no las comparte.
    - Los costos de los errores del TP3 no los dio la empresa: el umbral se apoya en un supuesto (10 a 1), con la sensibilidad a la vista.
    - El tipo de titular y la categoría «No combinada» son supuestos del equipo.
    - Los modelos describen asociaciones en este lote, no causas.
    """)
pie()
