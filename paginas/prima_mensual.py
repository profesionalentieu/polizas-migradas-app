# TP2 · ¿Cuánto paga por mes esta póliza? Una póliza (datos y estimación a la vista), por qué da eso, lote, registro y cómo funciona
# el modelo, cada cosa en su pestaña: lo principal se ve sin bajar y lo secundario queda a un clic
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from comun import (AZUL, GRIS, MILES, NOMBRES, NUMERICAS, archivo, en_castellano, figura, leer_csv, legible, letra_grande, md, modelo, mostrar_registro, num, pesos,
                   pie, porc, registrar, tabla, validar)

paq = modelo("tp2_prima_publico.joblib")
flujo, cols, F = paq["flujo"], paq["columnas"], paq["factor_duan"]
val, interno = paq["validacion"], paq["validacion_interno"]

st.title("TP2 · ¿Cuánto paga por mes esta póliza?")
st.caption(md(f"Con los datos que la póliza tenía en TIME, una regresión del logaritmo de la prima estima la **prima mensual** (sin impuestos). "
              f"Explica alrededor del **{porc(val['R²'], 0)}** de la variación; el resto depende de datos que la base no tiene."))

pestanas = st.tabs(["Una póliza", "Por qué da eso", "Cargar un lote", "Registro", "Cómo funciona el modelo"])


def prediccion(filas):
    """Prima mensual estimada, sin el factor de Duan: póliza por póliza se equivoca menos (R69)."""
    X = pd.DataFrame(filas)[cols]
    return np.exp(flujo.predict(X))


def error_del_tramo(prima):
    t = int(np.digitize(prima, paq["tramos"]["cortes"]))
    return paq["tramos"]["mae"][t], paq["tramos"]["error_mediano"][t]


# --- Una póliza: los datos a la izquierda y la estimación a la derecha ------------------------------------------------------------
with pestanas[0]:
    izq, der = st.columns([3, 2], gap="large")
    with izq:
        st.subheader("Datos de la póliza")
        entrada = {}
        c = st.columns(2)
        categoricas = [col for col in paq["opciones"] if col not in paq["cartera"]]
        for i, col in enumerate(categoricas):
            entrada[col] = c[i % 2].selectbox(NOMBRES[col], [legible(col, v, paq) for v in paq["opciones"][col]], key=f"tp2_{col}")
        for j, col in enumerate(NUMERICAS):
            vistos = [int(v) for v in paq["numericas"][col]]
            defecto = 12 if col == "cantidad_de_meses" else 0
            entrada[col] = c[(i + 1 + j) % 2].selectbox(NOMBRES[col], vistos, index=vistos.index(defecto), key=f"tp2_{col}")
        with st.expander("Cartera (productor, organizador y oficial): seudónimos por tamaño, sin códigos"):
            st.caption("«Productor 1» es el de la cartera más grande, «Productor 2» el que le sigue, y así. Solo aparecen las carteras con "
                       "100 pólizas o más en los datos; cualquier otra entra como «cartera chica o nueva».")
            k = st.columns(3)
            for col, caja in zip(paq["cartera"], k):
                valores = paq["opciones"][col]
                entrada[col] = caja.selectbox(NOMBRES[col], [legible(col, v, paq) for v in valores],
                                              index=valores.index(paq["cartera_defecto"][col]), key=f"tp2_{col}")

    fila, errores, avisos = validar(entrada, paq)
    with der:
        st.subheader("Estimación")
        for e in errores:
            st.error(md(e))
        if fila is not None:                                     # con errores no se estima nada
            for a in avisos:
                st.warning(md("Atención: " + a + ". La estimación puede ser menos confiable."))
            prima = float(prediccion([fila])[0])
            mae_t, mediano_t = error_del_tramo(prima)
            st.metric("Prima mensual estimada", pesos(prima))
            st.markdown(md(f"En las pólizas con estimaciones parecidas, el modelo se equivoca **en promedio {pesos(mae_t)} por mes**, y la "
                           f"mitad de las veces el error es menor que el **{num(mediano_t, 0)} %** de la prima (validación cruzada, con clientes "
                           "que el modelo no vio)."))

            if st.button("Guardar en el registro", key="tp2_guardar"):
                registrar("TP2 · prima mensual", [{**{NOMBRES[k]: v for k, v in entrada.items()}, "prima mensual estimada ($)": round(prima)}])
                st.success("Guardada: está en la pestaña «Registro».")

            # Contexto: dónde cae la estimación entre las primas del entrenamiento
            histo = tabla("prima_histograma.csv")
            ramo = paq["ramo_de_combinada"].get(fila["poliza_combinada"]) or "Todos"
            h = histo[histo["ramo"] == ramo].assign(desde_txt=lambda d: d["desde"].map(pesos), hasta_txt=lambda d: d["hasta"].map(pesos))
            texto_ramo = {"Autos": "los autos", "Motos": "las motos", "Todos": "todas las pólizas"}[ramo]
            base = alt.Chart(h).mark_rect(color=GRIS, stroke="white", strokeWidth=0.5).encode(
                x=alt.X("desde:Q", scale=alt.Scale(type="log"), title="prima mensual ($, escala logarítmica)",
                          axis=alt.Axis(labelExpr=MILES, values=[1e3, 1e4, 1e5, 1e6], grid=False)),       # pocas marcas: la letra es grande
                x2="hasta:Q", y=alt.Y("polizas:Q", title="pólizas", axis=alt.Axis(labelExpr=MILES, tickCount=5)), y2=alt.datum(0),
                tooltip=[alt.Tooltip("desde_txt:N", title="desde"), alt.Tooltip("hasta_txt:N", title="hasta"), alt.Tooltip("polizas:Q", title="pólizas")])
            regla = alt.Chart(pd.DataFrame({"x": [prima]})).mark_rule(color=AZUL, size=3).encode(x="x:Q")
            st.altair_chart(letra_grande((base + regla).properties(title=alt.TitleParams(["Dónde cae entre las primas", f"de {texto_ramo}"], offset=10))),
                            width="stretch", height=400)                 # alto y letra grandes: es una columna angosta y se proyecta
            st.caption("Línea azul: esta póliza. Primas mensuales del entrenamiento; los intervalos con menos de 20 pólizas se unieron con el vecino.")
            st.caption("El porqué de esta cifra está en la pestaña «Por qué da eso».")

# --- Por qué da eso: el aporte de cada variable y la misma póliza en cada unidad -------------------------------------------------
with pestanas[1]:
    if fila is None:
        st.info("Corregí los datos de la póliza en la pestaña «Una póliza» para ver por qué da lo que da.")
    else:
        # El aporte de cada variable, como porcentaje sobre la prima de una póliza típica [CL29, celdas 26–28]
        Z = np.asarray(flujo[:-1].transform(pd.DataFrame([fila])[cols])).ravel()
        nombres_z = flujo[0].get_feature_names_out()
        aportes = pd.Series(Z * flujo[-1].coef_, index=nombres_z)

        def variables_de(n):
            n = n.replace("cat__", "").replace("num__", "")
            return [c for c in cols if c in n]

        def grupo(n):
            v = variables_de(n)
            return "Combinaciones entre variables" if len(v) > 1 else NOMBRES[v[0]]

        por_var = aportes.groupby(aportes.index.map(grupo)).sum()
        por_var = por_var[por_var.abs() > 0.005]
        efecto = ((np.exp(por_var) - 1) * 100).sort_values().rename("efecto").reset_index().rename(columns={"index": "variable"})
        efecto["signo"] = np.where(efecto["efecto"] >= 0, "sube", "baja")
        efecto["efecto_txt"] = efecto["efecto"].map(lambda v: f"{v:+.0f} %")
        tipica = float(np.exp(flujo[-1].intercept_))
        st.markdown(md(f"Estimación de esta póliza: **{pesos(prima)} por mes**. Una póliza típica del entrenamiento paga **{pesos(tipica)}**."))
        a, b = st.columns(2, gap="large")
        barras = alt.Chart(efecto).mark_bar().encode(
            x=alt.X("efecto:Q", title="cambio en la prima (%)"),
            y=alt.Y("variable:N", sort=efecto["variable"].tolist(), title=None, axis=alt.Axis(labelLimit=320, labelOverlap=False)),
            color=alt.Color("signo:N", scale=alt.Scale(domain=["sube", "baja"], range=[AZUL, GRIS]), legend=None),
            tooltip=[alt.Tooltip("variable:N"), alt.Tooltip("efecto_txt:N", title="sobre la prima")])
        a.altair_chart(letra_grande(barras.properties(title="Qué sube o baja la prima de esta póliza")), width="stretch",
                       height=34 * len(efecto) + 110)            # el alto va en st.altair_chart: en .properties, Streamlit lo achica
        a.caption("Comparado con la póliza típica. Los efectos se multiplican: los porcentajes no se suman.")

        # La misma póliza en cada unidad de negocios
        unidades = paq["opciones"]["etiqueta_unidad_de_negocios"]
        por_unidad = pd.DataFrame({"unidad": unidades, "prima": prediccion([{**fila, "etiqueta_unidad_de_negocios": u} for u in unidades])})
        por_unidad["elegida"] = por_unidad["unidad"] == fila["etiqueta_unidad_de_negocios"]
        por_unidad["prima_txt"] = por_unidad["prima"].map(pesos)
        b.altair_chart(letra_grande(alt.Chart(por_unidad).mark_bar().encode(
            x=alt.X("prima:Q", title="prima mensual estimada ($)", axis=alt.Axis(labelExpr=MILES)),
            y=alt.Y("unidad:N", sort="-x", title=None, axis=alt.Axis(labelOverlap=False)),
            color=alt.Color("elegida:N", scale=alt.Scale(domain=[True, False], range=[AZUL, GRIS]), legend=None),
            tooltip=[alt.Tooltip("unidad:N"), alt.Tooltip("prima_txt:N", title="prima mensual")]
        ).properties(title="La misma póliza en cada unidad (azul: la elegida)")), width="stretch", height=28 * len(unidades) + 120)

# --- Un lote --------------------------------------------------------------------------------------------------------------
with pestanas[2]:
    st.markdown("Subí un CSV con una póliza por fila y las mismas columnas que la plantilla. Cada fila se valida por separado: "
                "las que tienen errores se marcan con su motivo y no se estiman, y el resto sigue.")
    d1, d2 = st.columns(2)
    d1.download_button("Descargar la plantilla (12 pólizas inventadas)", archivo("ejemplo_tp2.csv"), "plantilla_tp2.csv", "text/csv")
    d2.download_button("Descargar un ejemplo con errores", archivo("ejemplo_tp2_con_errores.csv"), "ejemplo_tp2_con_errores.csv", "text/csv")
    subido = st.file_uploader("CSV de pólizas", type="csv", key="tp2_csv")
    if subido is not None:
        df = leer_csv(subido, list(paq["opciones"]) + NUMERICAS)
        if df is not None:
            res, validas = [], []
            for i, r in df.iterrows():
                fila_l, err, av = validar(r.to_dict(), paq)
                res.append({"fila": i + 1, "estado": "error" if err else "estimada", "motivo": "; ".join(err), "avisos": "; ".join(av)})
                if fila_l:
                    validas.append((i, fila_l))
            res = pd.DataFrame(res)
            res["prima mensual estimada ($)"] = np.nan
            if validas:
                res.loc[[i for i, _ in validas], "prima mensual estimada ($)"] = prediccion([f for _, f in validas]).round()
            salida = pd.concat([df, res.drop(columns="fila")], axis=1)
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Pólizas estimadas", len(validas))
            k2.metric("Con errores", int((res["estado"] == "error").sum()))
            total = float(res["prima mensual estimada ($)"].sum())
            k3.metric("Total del lote, póliza por póliza", pesos(total))
            k4.metric("Total del lote con el factor de Duan", pesos(total * F))
            st.caption(f"Para estimar **totales de cartera** conviene el factor de Duan (× {num(F, 3)}): sin él, la suma queda por debajo de la real "
                       f"(en validación, {porc(val['suma predicha / real (sin Duan)'], 0)} de la real; con el factor, "
                       f"{porc(val['suma predicha / real (con Duan)'], 0)}). Para **una póliza**, no: póliza por póliza se equivoca menos sin él.")
            st.dataframe(salida, hide_index=True)
            e1, e2 = st.columns(2)
            e1.download_button("Descargar los resultados (CSV)", salida.to_csv(index=False).encode("utf-8-sig"), "resultados_tp2.csv", "text/csv")
            if e2.button("Guardar el lote en el registro", key="tp2_guardar_lote") and validas:
                registrar("TP2 · prima mensual (lote)", [{**{NOMBRES.get(k, k): v for k, v in df.loc[i].items()},
                                                          "prima mensual estimada ($)": res.loc[i, "prima mensual estimada ($)"]} for i, _ in validas])
                st.success(f"Se guardaron {len(validas)} pólizas en el registro.")

with pestanas[3]:
    mostrar_registro()

# --- Cómo funciona el modelo: cómo se eligió, la tabla de resultados y, a un clic, las figuras ---------------------------------
with pestanas[4]:
    st.markdown(md(f"""
**Qué es.** Una **regresión del logaritmo de la prima** con interacciones entre las categorías (polinómica de grado 2) y freno
Lasso. Explica alrededor del **{porc(val['R²'], 0)}** de la variación; el resto depende de datos que la base no tiene, como el
vehículo, la suma asegurada y la zona.

**Cómo se eligió.** Probamos 17 modelos con la misma validación cruzada de 5 pliegues **por cliente** (las pólizas de un mismo
cliente nunca quedan de los dos lados). Un modelo nuevo reemplaza al actual solo si gana en los 5 pliegues por más que el desvío
entre pliegues, y si la diferencia se sostiene en 15 particiones más. Ninguno lo logró: quedó el más simple, **grado 2 + Lasso**.
La prueba (3.147 pólizas de clientes nuevos) solo se usó para informar.

**El modelo de esta aplicación** es el elegido, con la cartera en seudónimos en lugar de códigos: R² de **{num(val['R²'])}** en
validación, contra **{num(interno['R²'])}** del modelo con los códigos; error medio de **{pesos(val['MAE ($, sin Duan)'])}** contra
**{pesos(interno['MAE ($, sin Duan)'])}** por mes. Sin la cartera, el R² bajaba a **{num(paq['validacion_sin_cartera']['R²'])}**.
No se midió en la prueba, para no volver a abrirla.
"""))
    res2 = tabla("resultados_tp2.csv")
    elegir = {"R² · entrenamiento": "R² entren.", "R² · validación": "R² valid.", "R² · prueba": "R² prueba",
              "R² ajustado · validación": "R² ajust. valid.", "RMSE · prueba": "RMSE prueba (log)",
              "MAE ($) · validación": "MAE valid. ($)", "MAE ($) · prueba": "MAE prueba ($)", "MAPE ($, %) · prueba": "MAPE prueba ($, %)"}
    vista = res2[["modelo"] + [c for c in elegir if c in res2.columns]].rename(columns=elegir)
    st.dataframe(en_castellano(vista), hide_index=True)
    st.caption("En pesos, con el factor de Duan, como en el informe. Validación: media de los 5 pliegues por cliente. "
               "Prueba: 3.147 pólizas de clientes que ningún modelo vio.")
    for f, texto in [("tp2_barras_de_metricas", "Métricas por modelo en entrenamiento, validación y prueba"),
                     ("tp2_predicho_contra_real", "Predicho contra real para cada modelo, en la prueba"),
                     ("tp2_residuos_del_elegido", "Residuos del modelo elegido: colas pesadas y más dispersión en las primas bajas"),
                     ("tp2_importancia_de_variables", "Importancia de las variables por permutación (con la cartera, en el modelo completo)")]:
        figura(f, texto)

pie()
