# TP3 · Segmentos de clientes: los 8 grupos del K-Means de la §63, pensados para alguien de la empresa que no sabe de modelos. Cada grupo
# con su nombre, su perfil, una descripción y sugerencias que salen de los datos; un gráfico que los compara; y una póliza que se carga y se
# ubica en su grupo. Datos agregados (el grupo más chico tiene 543 pólizas) y etiquetas públicas (R90; herramientas/segmentos_app.py)
from html import escape

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from comun import (AZUL, MILES, NARANJA, NOMBRES, NUMERICAS, PORCIENTO, VERDE, ejemplos_rapidos, figura, legible, md, modelo,
                   num, pesos, pie, porc, registrar, tabla, validar, valores_iniciales)

paq = modelo("segmentos_publico.joblib")
grupos = tabla("segmentos_clientes.csv")
tasa = paq["tasa_general"]
# Prioridad para revisar antes de migrar, según cuántas veces falla el grupo respecto del promedio de la cartera
PRIORIDAD = [("Revisar el grupo", 1.5, NARANJA), ("Que decida el modelo del TP3", 1.0, AZUL), ("No hace falta revisarlo entero", 0, VERDE)]
CARTERA = ["nro_productor", "nro_organizador", "oficial_de_negocio"]
# Pólizas típicas, con la prima que estima el modelo público del TP2 (redondeada) como prima en TIME, como en la página del TP3
EJEMPLOS = {
    "Auto de empresa sin paquete": {"poliza_combinada": "No combinada", "letra_titular_time": "J", "etiqueta_condicion_iva": "Responsable Inscripto",
                                    "prima_mensual": 91400.0},
    "Moto de persona sin paquete": {"ramo": "Motos", "poliza_combinada": "No combinada", "prima_mensual": 15200.0},
    "Auto de persona con paquete": {"prima_mensual": 82900.0},
    "Auto con pólizas vinculadas": {"poliza_combinada": "Automotores + APF + Vinculada", "polizas_vinculadas": 2, "prima_mensual": 88000.0},
}


def prioridad(veces):
    return next((texto, color) for texto, corte, color in PRIORIDAD if veces >= corte)


def caja(texto, color):
    st.markdown(f'<div style="background:{color}; color:#fff; padding:0.55rem 0.9rem; border-radius:0.5rem; margin:0.3rem 0 0.6rem 0">'
                f'{texto}</div>', unsafe_allow_html=True)


def cifras(items):
    """Cifras grandes que bajan de renglón si no entran, en vez de cortarse; la explicación aparece al pasar el cursor."""
    bloques = "".join(f'<div title="{escape(ayuda, quote=True)}"><div style="font-size:0.85rem; opacity:0.75">{etiqueta} ⓘ</div>'
                      f'<div style="font-size:1.75rem; line-height:1.25; white-space:nowrap">{valor}</div></div>' for etiqueta, valor, ayuda in items)
    st.markdown(f'<div style="display:flex; flex-wrap:wrap; gap:0.3rem 1.8rem; margin:0.1rem 0 0.7rem 0">{bloques}</div>'.replace("$", "&#36;"),
                unsafe_allow_html=True)


def tarjeta(g, destacada=False):
    """Un grupo: nombre, tamaño, prima típica y fallas a la vista; el perfil, la descripción y las sugerencias debajo."""
    with st.container(border=True):
        st.markdown(f"### Grupo {g.grupo} · {g.nombre}" if destacada else f"#### Grupo {g.grupo} · {g.nombre}")
        polizas = f"{g.polizas:,}".replace(",", ".")
        if destacada:                                            # en la columna angosta, las métricas se cortaban: van en una línea
            st.markdown(md(f"**{polizas} pólizas** ({porc(g.porcentaje)} de la cartera) · prima mensual típica **{pesos(g.prima_mensual_mediana)}** "
                           f"· **{porc(g.tasa_fallas)}** llegan sin titular ({num(g.veces_promedio, 1)} veces el promedio)"))
        else:                                                    # con st.metric, la prima se cortaba («$ 87.2…») aun a 1366 px de ancho
            cifras([("Pólizas", polizas, f"{porc(g.porcentaje)} de la cartera de entrenamiento"),
                    ("Prima típica", pesos(g.prima_mensual_mediana),
                     f"La prima mensual mediana. La mitad de las pólizas del grupo paga entre {pesos(g.prima_mensual_p25)} y {pesos(g.prima_mensual_p75)}."),
                    ("Sin titular", porc(g.tasa_fallas), f"Llegan a GW sin titular: {num(g.veces_promedio, 1)} veces el promedio de la cartera ({porc(tasa)})")])
        st.markdown(f"{g.descripcion}")
        st.caption(f"{g.titular} {porc(g.titular_pct, 0)} · {g.paquete} {porc(g.paquete_pct, 0)} · {g.ramo} {porc(g.ramo_pct, 0)} · "
                   f"{g.iva} {porc(g.iva_pct, 0)} · {g.unidad} {porc(g.unidad_pct, 0)}")
        st.markdown(f"**Qué parece tener contratado.** {g.tiene}  \n**Qué se le podría ofrecer.** {g.ofrecer}")
        texto, color = prioridad(g.veces_promedio)
        caja(f"<b>¿Revisarlo antes de migrar? {texto}.</b> {g.revisar}", color)


st.title("Segmentos de clientes: qué tiene y qué ofrecerle a cada grupo")
st.caption("Separamos las 12.650 pólizas de entrenamiento en **8 grupos de clientes parecidos**, mirando solo sus datos en TIME (tipo de "
           "cliente, paquete, ramo, condición ante el IVA, unidad, prima, cartera…) y sin mirar si la póliza falló. Después contamos cuántas "
           "fallas tuvo cada grupo. Las sugerencias salen de los datos: son ideas para evaluar, no recomendaciones probadas.")

pestanas = st.tabs(["Los 8 grupos", "Comparar los grupos", "¿En qué grupo está una póliza?", "Cómo se armaron"])

# --- Los 8 grupos, de más fallas a menos ------------------------------------------------------------------------------------------
with pestanas[0]:
    st.markdown("Ordenados de más fallas a menos. El color dice qué hacer antes de migrar: **naranja**, revisar el grupo; **azul**, "
                "que decida el modelo del TP3 póliza por póliza; **verde**, no hace falta revisarlo entero.")
    for fila in range(0, len(grupos), 2):
        c = st.columns(2, gap="medium")
        for j, (_, g) in enumerate(grupos.iloc[fila:fila + 2].iterrows()):
            with c[j]:
                tarjeta(g)

# --- Comparar: tamaño, prima típica y fallas, lado a lado ------------------------------------------------------------------------
with pestanas[1]:
    d = grupos.assign(etiqueta=lambda t: t["grupo"].astype(str) + " · " + t["nombre"],
                      que_hacer=lambda t: [prioridad(v)[0] for v in t["veces_promedio"]],
                      polizas_txt=lambda t: t["polizas"].map(lambda v: f"{v:,}".replace(",", ".")),
                      prima_txt=lambda t: t["prima_mensual_mediana"].map(pesos),
                      tasa_txt=lambda t: t["tasa_fallas"].map(porc))
    orden = d["etiqueta"].tolist()
    color = alt.Color("que_hacer:N", title="Antes de migrar", legend=None,
                      scale=alt.Scale(domain=[p[0] for p in PRIORIDAD], range=[p[2] for p in PRIORIDAD]))
    ayuda = [alt.Tooltip("etiqueta:N", title="grupo"), alt.Tooltip("polizas_txt:N", title="pólizas"),
             alt.Tooltip("prima_txt:N", title="prima mensual típica"), alt.Tooltip("tasa_txt:N", title="llegan sin titular")]

    def barras(campo, titulo, formato, etiquetas, ticks=4):
        """Un gráfico de barras por medida, con los grupos en el mismo orden; los nombres van solo en el primero."""
        eje_y = alt.Axis(labelLimit=330, labelFontSize=14) if etiquetas else None
        g = alt.Chart(d).mark_bar().encode(
            y=alt.Y("etiqueta:N", sort=orden, title=None, axis=eje_y), color=color, tooltip=ayuda,
            x=alt.X(f"{campo}:Q", title=None, axis=alt.Axis(labelExpr=formato, tickCount=ticks, labelFontSize=13)))
        return g.properties(title=alt.TitleParams(titulo, fontSize=16, anchor="start"))

    c1, c2, c3 = st.columns([2.2, 1, 1])
    c1.altair_chart(barras("polizas", "Tamaño (pólizas)", MILES, True), height=380)
    c2.altair_chart(barras("prima_mensual_mediana", "Prima típica ($)", MILES, False, 3), height=380)
    promedio = alt.Chart(pd.DataFrame({"x": [tasa]})).mark_rule(strokeDash=[5, 3], color="black", size=2).encode(x="x:Q")
    c3.altair_chart(alt.layer(barras("tasa_fallas", "Llegan sin titular", PORCIENTO, False), promedio), height=380)
    st.markdown(" ".join(f'<span style="background:{c}; color:#fff; padding:0.2rem 0.6rem; border-radius:0.4rem; margin-right:0.4rem">{t}</span>'
                         for t, _, c in PRIORIDAD), unsafe_allow_html=True)
    st.caption(f"La línea punteada es el promedio de la cartera ({porc(tasa)}). Prima típica: la mediana de la prima mensual del grupo.")
    vista = pd.DataFrame({
        "Grupo": d["etiqueta"], "Pólizas": d["polizas_txt"], "% de la cartera": d["porcentaje"].map(lambda v: porc(v)),
        "Tipo de cliente": d["titular"] + " (" + d["titular_pct"].map(lambda v: porc(v, 0)) + ")",
        "Paquete": d["paquete"] + " (" + d["paquete_pct"].map(lambda v: porc(v, 0)) + ")",
        "Ramo": d["ramo"] + " (" + d["ramo_pct"].map(lambda v: porc(v, 0)) + ")",
        "IVA": d["iva"] + " (" + d["iva_pct"].map(lambda v: porc(v, 0)) + ")",
        "Unidad": d["unidad"] + " (" + d["unidad_pct"].map(lambda v: porc(v, 0)) + ")",
        "Prima mensual típica": d["prima_txt"], "Llegan sin titular": d["tasa_txt"],
        "Veces el promedio": d["veces_promedio"].map(lambda v: num(v, 2)), "De todas las fallas": d["porcentaje_de_las_fallas"].map(lambda v: porc(v, 0)),
    })
    st.dataframe(vista, hide_index=True)
    st.caption("Entre paréntesis, qué parte del grupo tiene ese valor (el más común). Ningún grupo tiene menos de 543 pólizas.")

# --- Una póliza: los datos a la izquierda y su grupo a la derecha -----------------------------------------------------------------
with pestanas[2]:
    izq, der = st.columns([3, 2], gap="large")
    with izq:
        st.subheader("Datos de la póliza")
        rango = paq["prima_mensual"]
        ejemplos_rapidos("seg", paq, valores_iniciales("seg", paq, {"seg_ramo": "Autos", "seg_prima_mensual": float(round(rango["mediana"], -2))}),
                         EJEMPLOS)
        entrada = {}
        c = st.columns(2)
        entrada["ramo"] = c[0].selectbox(NOMBRES["ramo"], ["Autos", "Motos"], key="seg_ramo")
        i = 0
        for i, col in enumerate([k for k in paq["opciones"] if k not in CARTERA], start=1):
            entrada[col] = c[i % 2].selectbox(NOMBRES[col], [legible(col, v, paq) for v in paq["opciones"][col]], key=f"seg_{col}")
        for j, col in enumerate(NUMERICAS):
            entrada[col] = c[(i + 1 + j) % 2].selectbox(NOMBRES[col], [int(v) for v in paq["numericas"][col]], key=f"seg_{col}")
        entrada["prima_mensual"] = c[(i + 4) % 2].number_input(NOMBRES["prima_mensual"], min_value=0.0, step=500.0, format="%.0f",
                                                               key="seg_prima_mensual",
                                                               help=md(f"Entre {pesos(rango['min'])} y {pesos(rango['max'])} en los datos."))
        with st.expander("Cartera (productor, organizador y oficial): si no la conocés, dejá «Otro»"):
            k = st.columns(3)
            for j, col in enumerate(CARTERA):
                entrada[col] = k[j].selectbox(NOMBRES[col], [legible(col, v, paq) for v in paq["opciones"][col]], key=f"seg_{col}")

    fila, errores, avisos = validar(entrada, paq, con_prima=True)
    with der:
        st.subheader("Su grupo")
        for e in errores:
            st.error(md(e))
        if fila is not None:
            for a in avisos:
                st.warning(md("Atención: " + a + ". El grupo puede ser menos confiable."))
            z = np.asarray(paq["preprocesador"].transform(pd.DataFrame([fila])[paq["columnas"]])).ravel()
            distancias = np.sqrt(((paq["centroides"] - z) ** 2).sum(axis=1))
            n = int(np.argmin(distancias))
            g = grupos.iloc[n]
            tarjeta(g, destacada=True)
            segundo = int(np.argsort(distancias)[1])
            st.caption(f"Se ubica en el grupo cuyo «centro» (la póliza promedio del grupo) está más cerca. El que le sigue es el grupo "
                       f"{grupos.iloc[segundo].grupo} ({grupos.iloc[segundo].nombre}). Para la probabilidad de esta póliza en particular, "
                       "usá la página «TP3 · Revisar antes de migrar».")
            if st.button("Guardar en el registro", key="seg_guardar"):
                registrar("TP3 · segmentos", [{**{NOMBRES[k_]: v for k_, v in entrada.items()}, "grupo": f"{g.grupo} · {g.nombre}"}])
                st.success("Guardada: está en la pestaña «Registro» de las páginas del TP2 y del TP3.")

# --- Cómo se armaron los grupos -------------------------------------------------------------------------------------------------
with pestanas[3]:
    st.markdown(f"""
**Qué es el *clustering*.** Es agrupar sin respuesta conocida (aprendizaje no supervisado): en lugar de aprender a predecir algo,
el método busca pólizas que se parecen entre sí y las junta. Usamos *K-Means*: cada grupo tiene un «centro» (la póliza promedio del
grupo) y cada póliza va al centro más cercano, mirando sus datos de TIME (tipo de cliente, paquete, ramo, IVA, unidad, prima,
cartera, cuotas…). **No usamos si la póliza falló**: las fallas se contaron después, para ver si algún grupo se destaca.

**Por qué 8 grupos.** Probamos de 2 a 10 grupos y medimos cuatro criterios: el codo de la inercia, la silueta, el índice de
Davies-Bouldin y el de Calinski-Harabasz. No coinciden (eligen 5, 10, 8 y 2). Antes de mirar los grupos fijamos una regla: el número
con el mejor Davies-Bouldin (8), salvo que la mejor silueta (10) le gane por 0,01 o más; le ganaba por 0,007, así que quedaron **8**.
Lo importante no depende de ese número: con 4 grupos o más ya aparece uno de pólizas sin paquete con muchas fallas, y con 7 o más
queda limpio el de las empresas sin paquete, con una falla cada seis o siete pólizas.

**Cómo se calculó cada cosa** (con las 12.650 pólizas de entrenamiento; la prueba no se usó):
- **Perfil:** para cada grupo, el valor más común de cada dato (tipo de cliente, paquete, ramo, IVA, unidad) y qué porcentaje del grupo
  lo tiene. La **prima típica** es la mediana de la prima mensual: la mitad del grupo paga menos y la otra mitad, más.
- **Tasa de fallas:** las pólizas del grupo que llegaron a GW sin titular, divididas por las pólizas del grupo, y cuántas veces es eso
  el promedio de la cartera ({porc(tasa)}).
- **Sugerencias:** salen de comparar el perfil del grupo con el de los otros grupos. «Qué parece tener contratado» es su paquete más
  común; «qué se le podría ofrecer», lo que tienen otros grupos de clientes parecidos y a ese le falta (un paquete, coberturas o
  pólizas vinculadas). Son ideas que salen de los datos, para evaluar con el área comercial.
  «¿Revisarlo antes de migrar?» sigue una regla fija sobre la tasa: **1,5 veces el promedio o más, revisar el grupo** (naranja);
  **entre 1 y 1,5, que decida el modelo del TP3** póliza por póliza (azul); **menos de 1, no hace falta revisarlo entero** (verde).
  En los grupos grandes que reúnen el 15 % de las fallas o más (el 3 y el 6), el texto avisa que igual conviene que decida el modelo.
- **Una póliza nueva** va al grupo de centro más cercano, con los mismos datos y la misma preparación que usó *K-Means*.

**Hasta dónde llegan.** Los grupos se superponen (silueta de 0,14, cuando 1 sería una separación perfecta) y, salvo el de las empresas,
no separan las fallas: sirven para **describir la cartera y decidir qué ofrecerle a cada tipo de cliente**, no para predecir. Para
decidir qué pólizas revisar está el modelo del TP3.
""")
    figura("tp3_segmentos_eleccion_k", "Los cuatro criterios para elegir la cantidad de grupos y el grupo con más fallas de cada k")

pie()
