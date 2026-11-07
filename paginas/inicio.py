# Inicio: el proyecto y las dos preguntas, con su respuesta en cifras a la vista; las etapas, los modelos, la privacidad y cómo recorrer
# la aplicación, en pestañas
import streamlit as st
from comun import md, modelo, num, pesos, porc, pie

p2, p3 = modelo("tp2_prima_publico.joblib"), modelo("tp3_revision_publico.joblib")
v2, v3 = p2["validacion"], p3["validacion"]
c10 = next(c for c in p3["costos"] if c["relación de costos"] == 10)

st.title("Pólizas migradas de TIME a Guidewire: qué se puede anticipar")
st.caption("Aprendizaje Automático y Grandes Datos (IC) · UNRaf, Universidad Nacional de Rafaela · "
           "Agustín Bértola, Matias Bonafede y Agustín Ferrero")

st.markdown("""
Una aseguradora pasó su cartera de autos y motos del sistema viejo (**TIME**) al nuevo (**Guidewire**, GW). Trabajamos con el
**lote 107**: 15.804 pólizas, con los datos que tenía cada una en TIME y el resultado de la migración. Con esos datos nos hicimos
dos preguntas:

1. **¿Cuánto paga por mes una póliza?** Si con los datos de TIME se puede estimar la prima, se pueden detectar precios raros
   antes de migrar (TP2, regresión).
2. **¿Qué pólizas van a llegar a GW sin el código de titular?** Es la falla más común de la migración. Si se anticipa, se puede
   revisar la póliza antes (TP3, clasificación).
""")

k = st.columns(4)
k[0].metric("TP2 · R² en validación", porc(v2["R²"], 0),
            help="Proporción de la variación del logaritmo de la prima que explica el modelo, con clientes que no vio.")
k[1].metric("TP2 · error medio por póliza", pesos(v2["MAE ($, sin Duan)"]), help="Por mes, en validación cruzada por cliente.")
k[2].metric("TP3 · pólizas a revisar (10 a 1)", porc(c10["pólizas revisadas"], 0),
            help="Con un costo de 10 a 1: dejar pasar una falla cuesta 10 veces más que revisar una póliza de más.")
k[3].metric("TP3 · fallas que encuentra", porc(c10["fallas detectadas"], 0), help="Revisando esas pólizas, en validación cruzada por cliente.")

pestanas = st.tabs(["Las cuatro etapas", "Los modelos y por qué", "Datos y privacidad", "Cómo recorrerla"])

with pestanas[0]:
    c = st.columns(4)
    c[0].markdown("**TP1 · Datos y comunicación**  \nLimpieza sin borrar nada y el hallazgo principal: en autos, las empresas llegan sin titular 2,8 veces más.")
    c[1].markdown("**TP2 · Regresión**  \n17 modelos para estimar la prima mensual. Ninguno le gana con claridad al más simple: interacciones entre categorías con Lasso.")
    c[2].markdown("**TP3 · Clasificación**  \n16 modelos y un umbral elegido por costo para decidir qué pólizas revisar. Queda la regresión logística.")
    c[3].markdown("**TP4 · Despliegue**  \nEsta aplicación, con los dos modelos, el tablero y la metodología.")

with pestanas[1]:
    a, b = st.columns(2)
    a.markdown(md(f"""
**Prima mensual (TP2): polinómica de grado 2 con Lasso.**
- Entre 17 modelos (k vecinos, árboles, bosques, potenciación por gradiente, Ridge, Elastic Net…), **ninguno se distinguió**
  en validación cruzada por cliente. Elegimos el más simple que explica cada estimación variable por variable.
- Con clientes que no vio, explica el **{porc(v2['R²'])}** de la variación del logaritmo de la prima (R² en validación) y se
  equivoca en promedio en **{pesos(v2['MAE ($, sin Duan)'])} por mes**.
- Sirve para tener una referencia del precio de una póliza; no reemplaza al motor de tarificación, que usa datos que esta base no tiene
  (el vehículo, la suma asegurada y la zona).
"""))
    b.markdown(f"""
**Revisión antes de migrar (TP3): regresión logística con umbral de costo.**
- Ningún modelo (ni los ensambles) se distinguió de la logística, que además da probabilidades confiables y se puede explicar.
- Ordena el riesgo: su precisión promedio es **{num(v3['precision_promedio'])}**, contra **{num(p3['tasa_general'])}** de elegir
  al azar. Con un costo de 10 a 1 (dejar pasar una falla cuesta 10 veces más que revisar una póliza de más), manda a revisar el
  **{porc(c10['pólizas revisadas'], 0)}** de las pólizas y encuentra el **{porc(c10['fallas detectadas'], 0)}** de las fallas.
- La decisión final la toma una persona: el modelo dice qué conviene mirar primero.
""")

with pestanas[2]:
    st.markdown("La aplicación no tiene ninguna fila del dataset. Muestra conteos y tasas de grupos de 20 pólizas o más. "
                "Los modelos son versiones públicas: las unidades de negocios y los productos aparecen como «Unidad A, B…» y «Producto A, B…», y "
                "en el TP2 la cartera (productor, organizador y oficial) va con seudónimos por tamaño («Productor 1, 2…»), sin códigos. "
                "El TP3 no usa la cartera, que no le aportaba. Las cifras de la aplicación son de validación cruzada.")

with pestanas[3]:
    st.markdown("""
- **Datos y limpieza:** del archivo original a la base limpia, en números.
- **TP1:** el gráfico principal del primer trabajo, por ramo, tipo de cliente y unidad.
- **Tablero:** tres vistas vinculadas (fallas, primas y pólizas a revisar) con un mismo filtro. Hacé clic en una unidad para resaltarla.
- **TP2 y TP3:** en la pestaña «Una póliza» cargás los datos y ves el resultado al lado; el porqué, el lote, el registro y cómo
  funciona cada modelo están en las otras pestañas.
- **Metodología:** cómo validamos, qué problemas aparecieron y cómo los resolvimos.
""")
pie()
