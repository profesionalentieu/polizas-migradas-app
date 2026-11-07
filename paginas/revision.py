# TP3 · ¿Conviene revisar esta póliza antes de migrarla? Una póliza (datos, probabilidad, decisión por costo y regla del TP1 a la vista),
# por qué da eso, lote, registro y cómo funciona el modelo, cada cosa en su pestaña: lo principal se ve sin bajar y lo secundario queda a un clic
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from comun import (GRIS, NARANJA, PORCIENTO, ROJO, NOMBRES, NUMERICAS, VERDE, archivo, decision as caja_decision, ejemplos_rapidos, en_castellano, figura,
                   leer_csv, legible, letra_grande, md, modelo, mostrar_registro, num, pesos, pie, porc, registrar, tabla, validar, valores_iniciales, video)

paq = modelo("tp3_revision_publico.joblib")
flujo, cols, tasa = paq["flujo"], paq["columnas"], paq["tasa_general"]
costos = {int(c["relación de costos"]): c for c in paq["costos"]}
val = paq["validacion"]
# Pólizas típicas para la demostración, con la prima que estima el TP2 (redondeada) como prima en TIME (docs/escenarios_demo.md)
EJEMPLOS = {
    "Auto de persona con paquete": {"prima_mensual": 82900.0},
    "Auto de empresa sin paquete": {"poliza_combinada": "No combinada", "letra_titular_time": "J", "etiqueta_condicion_iva": "Responsable Inscripto",
                                    "prima_mensual": 91400.0},
    "Moto de empresa con paquete": {"ramo": "Motos", "poliza_combinada": "Moto + AP", "letra_titular_time": "J",
                                    "etiqueta_condicion_iva": "Responsable Inscripto", "prima_mensual": 31500.0},
    "Moto de persona con paquete (cerca del umbral)": {"ramo": "Motos", "poliza_combinada": "Moto + AP", "prima_mensual": 25700.0},
}

st.title("TP3 · ¿Conviene revisar esta póliza antes de migrarla?")
st.caption(f"Una de cada quince pólizas del lote llegó a Guidewire sin el código de titular ({porc(tasa)}). Una **regresión logística** estima "
           "la probabilidad de que le pase lo mismo a esta póliza, y un **umbral elegido por costo** decide si conviene revisarla.")

r = st.segmented_control("¿Cuántas veces más cuesta dejar pasar una falla que revisar una póliza de más?", [3, 5, 10, 15], default=10,
                         format_func=lambda v: f"{v} a 1", key="tp3_costo", required=True,
                         help="La empresa no dio los costos: el equipo supuso 10 a 1 (supuesto S10). Con otra relación cambian el umbral y la decisión.")
c_r = costos[r]
umbral = c_r["umbral"]

pestanas = st.tabs(["Una póliza", "Por qué da eso", "Cargar un lote", "Registro", "Cómo funciona el modelo"])


def probabilidad(filas):
    return flujo.predict_proba(pd.DataFrame(filas)[cols])[:, 1]


def regla_tp1(fila):
    return fila["ramo"] == "Autos" and fila["letra_titular_time"] in ("J", "Q")


def decision(p):
    return "revisar" if np.isfinite(umbral) and p >= umbral else "no revisar"


# --- Una póliza: los datos a la izquierda y el resultado a la derecha -------------------------------------------------------------
with pestanas[0]:
    izq, der = st.columns([3, 2], gap="large")
    with izq:
        st.subheader("Datos de la póliza")
        rango = paq["prima_mensual"]
        ejemplos_rapidos("tp3", paq, valores_iniciales("tp3", paq, {"tp3_ramo": "Autos", "tp3_prima_mensual": float(round(rango["mediana"], -2))}),
                         EJEMPLOS)                              # los valores iniciales van en la sesión, no en cada widget
        entrada = {}
        c = st.columns(2)
        entrada["ramo"] = c[0].selectbox(NOMBRES["ramo"], ["Autos", "Motos"], key="tp3_ramo")
        for i, col in enumerate(paq["opciones"], start=1):
            entrada[col] = c[i % 2].selectbox(NOMBRES[col], [legible(col, v, paq) for v in paq["opciones"][col]], key=f"tp3_{col}")
        for j, col in enumerate(NUMERICAS):
            vistos = [int(v) for v in paq["numericas"][col]]
            entrada[col] = c[(i + 1 + j) % 2].selectbox(NOMBRES[col], vistos, key=f"tp3_{col}")
        entrada["prima_mensual"] = c[(i + 4) % 2].number_input(NOMBRES["prima_mensual"], min_value=0.0,
                                                               step=500.0, format="%.0f", key="tp3_prima_mensual",
                                                               help=md(f"Entre {pesos(rango['min'])} y {pesos(rango['max'])} en los datos."))

    fila, errores, avisos = validar(entrada, paq, con_prima=True)
    with der:
        st.subheader("Resultado")
        for e in errores:
            st.error(md(e))
        if fila is not None:                                     # con errores no se evalúa nada
            for a in avisos:
                st.warning(md("Atención: " + a + ". La probabilidad puede ser menos confiable."))
            p = float(probabilidad([fila])[0])
            dec, dec_regla = decision(p), ("revisar" if regla_tp1(fila) else "no revisar")
            st.metric("Probabilidad de llegar sin titular", porc(p))
            st.caption(f"{num(p / tasa, 1)} veces la tasa general ({porc(tasa)}).")    # sin delta: su flecha sube aunque la póliza esté por debajo
            caja_decision(f"Modelo (logística, {r} a 1): **{dec.capitalize()}**"
                          + (f" (umbral: {porc(umbral)})" if np.isfinite(umbral) else " (con este costo no conviene revisar ninguna)"), dec == "revisar")
            caja_decision(f"Regla del TP1 (auto + persona jurídica): **{dec_regla.capitalize()}**", dec_regla == "revisar")

            # La probabilidad, con la tasa general y el umbral como referencia
            marcas = pd.DataFrame({"x": [tasa] + ([umbral] if np.isfinite(umbral) else []), "valor": [porc(tasa)] + ([porc(umbral)] if np.isfinite(umbral) else []),
                                   "qué": ["tasa general"] + ([f"umbral con {r} a 1"] if np.isfinite(umbral) else [])})
            # Sin eje vertical: la barra y las líneas ocupan todo el alto (con un eje nominal, el alto interno quedaba en cero y no se
            # veían las líneas). La tasa general se rotula a la izquierda de su línea y el umbral a la derecha, para que no se pisen
            barra = alt.Chart(pd.DataFrame({"x": [p]})).mark_bar(color=NARANJA if dec == "revisar" else VERDE).encode(
                x=alt.X("x:Q", title="probabilidad de llegar sin titular", axis=alt.Axis(labelExpr=PORCIENTO),
                        scale=alt.Scale(domain=[0, max(0.35, p * 1.2)])))
            lineas = alt.Chart(marcas).mark_rule(strokeDash=[5, 3], size=2, color="black").encode(x="x:Q", tooltip=["qué:N", "valor:N"])
            textos = [alt.Chart(marcas[marcas["qué"] == q]).mark_text(align=a, dx=d, baseline="bottom", fontSize=14).encode(x="x:Q", y=alt.value(-4), text="qué:N")
                      for q, a, d in [("tasa general", "right", -4), (f"umbral con {r} a 1", "left", 4)]]
            st.altair_chart(letra_grande(alt.layer(barra, lineas, *textos).properties(title=alt.TitleParams("Contra la tasa general y el umbral", offset=26))),
                            width="stretch", height=230)                 # alto y letra grandes: es una columna angosta y se proyecta
            if st.button("Guardar en el registro", key="tp3_guardar"):
                registrar("TP3 · revisión", [{**{NOMBRES[k]: v for k, v in entrada.items()}, "probabilidad": round(p, 4),
                                              f"decisión del modelo ({r} a 1)": dec, "regla del TP1": dec_regla}])
                st.success("Guardada: está en la pestaña «Registro».")
            st.caption("El porqué de esta probabilidad está en la pestaña «Por qué da eso».")

# --- Por qué da eso: el aporte de cada variable, en «cuánto multiplica las chances» [CL32, celdas 18–19 y 47–51] ---------------------
with pestanas[1]:
    if fila is None:
        st.info("Corregí los datos de la póliza en la pestaña «Una póliza» para ver por qué da lo que da.")
    else:
        st.markdown(f"Probabilidad de esta póliza: **{porc(p)}**, {num(p / tasa, 1)} veces la tasa general ({porc(tasa)}).")
        Z = np.asarray(flujo[:-1].transform(pd.DataFrame([fila])[cols])).ravel()
        nombres_z = [n.split("__", 1)[1] for n in flujo[0].get_feature_names_out()]
        aportes = pd.Series(Z * flujo[-1].coef_.ravel(), index=nombres_z)
        grupo = lambda n: next(NOMBRES.get(c, c) for c in cols if n.startswith(c)) if not n.startswith("log_prima") else NOMBRES["prima_mensual"]
        por_var = aportes.groupby(aportes.index.map(grupo)).sum()
        por_var = por_var[por_var.abs() > 0.01]
        ef = pd.DataFrame({"variable": por_var.index, "veces": np.exp(por_var.to_numpy())}).sort_values("veces")
        ef["signo"] = np.where(ef["veces"] >= 1, "aumenta", "disminuye")
        ef["veces_txt"] = ef["veces"].map(lambda v: num(v, 2))
        tope = max(1.25, 1.15 * float(np.max(np.maximum(ef["veces"], 1 / ef["veces"]))))      # escala simétrica alrededor de 1
        st.altair_chart(letra_grande(alt.Chart(ef).mark_bar().encode(       # en escala logarítmica, las barras arrancan en 1 («no cambia»): el 0 no existe
            x=alt.X("veces:Q", scale=alt.Scale(type="log", domain=[1 / tope, tope]), title="cuánto multiplica las chances de llegar sin titular (escala logarítmica)",
                    axis=alt.Axis(labelExpr="replace(format(datum.value, '~g'), '.', ',')")),        # coma decimal, como en el resto de la app
            x2=alt.datum(1),
            y=alt.Y("variable:N", sort=ef["variable"].tolist(), title=None, axis=alt.Axis(labelLimit=320, labelOverlap=False)),
            color=alt.Color("signo:N", scale=alt.Scale(domain=["aumenta", "disminuye"], range=[ROJO, GRIS]), legend=None),
            tooltip=["variable:N", alt.Tooltip("veces_txt:N", title="multiplica las chances por")]
        ).properties(title="Qué sube o baja el riesgo de esta póliza, frente a una póliza típica")), width="stretch", height=34 * len(ef) + 120)
        st.caption("Un valor de 1,5 quiere decir que esa característica multiplica por 1,5 las chances de llegar sin titular. "
                   "La logística suma los aportes en log-chances, así que los efectos se multiplican.")

# --- Un lote --------------------------------------------------------------------------------------------------------------
with pestanas[2]:
    st.markdown(f"Subí un CSV con una póliza por fila y las mismas columnas que la plantilla. Cada fila se valida por separado. "
                f"La decisión usa la relación de costos elegida arriba (**{r} a 1**).")
    d1, d2 = st.columns(2)
    d1.download_button("Descargar la plantilla (12 pólizas inventadas)", archivo("ejemplo_tp3.csv"), "plantilla_tp3.csv", "text/csv")
    d2.download_button("Descargar un ejemplo con errores", archivo("ejemplo_tp3_con_errores.csv"), "ejemplo_tp3_con_errores.csv", "text/csv")
    subido = st.file_uploader("CSV de pólizas", type="csv", key="tp3_csv")
    if subido is not None:
        df = leer_csv(subido, ["ramo"] + list(paq["opciones"]) + NUMERICAS + ["prima_mensual"])
        if df is not None:
            res, validas = [], []
            for i, fila_csv in df.iterrows():
                fila_l, err, av = validar(fila_csv.to_dict(), paq, con_prima=True)
                res.append({"estado": "error" if err else "evaluada", "motivo": "; ".join(err), "avisos": "; ".join(av)})
                if fila_l:
                    validas.append((i, fila_l))
            res = pd.DataFrame(res)
            res["probabilidad"], res[f"modelo ({r} a 1)"], res["regla del TP1"] = np.nan, "", ""
            if validas:
                ps = probabilidad([f for _, f in validas])
                idx = [i for i, _ in validas]
                res.loc[idx, "probabilidad"] = ps.round(4)
                res.loc[idx, f"modelo ({r} a 1)"] = [decision(x) for x in ps]
                res.loc[idx, "regla del TP1"] = ["revisar" if regla_tp1(f) else "no revisar" for _, f in validas]
            salida = pd.concat([df, res], axis=1)
            k1, k2, k3 = st.columns(3)
            k1.metric("Pólizas evaluadas", len(validas))
            k2.metric("Con errores", int((res["estado"] == "error").sum()))
            k3.metric(f"El modelo manda a revisar ({r} a 1)", int((res[f"modelo ({r} a 1)"] == "revisar").sum()))
            st.dataframe(salida, hide_index=True)
            e1, e2 = st.columns(2)
            e1.download_button("Descargar los resultados (CSV)", salida.to_csv(index=False).encode("utf-8-sig"), "resultados_tp3.csv", "text/csv")
            if e2.button("Guardar el lote en el registro", key="tp3_guardar_lote") and validas:
                registrar("TP3 · revisión (lote)", [{**{NOMBRES.get(k, k): v for k, v in df.loc[i].items()}, "probabilidad": res.loc[i, "probabilidad"],
                                                     f"decisión del modelo ({r} a 1)": res.loc[i, f"modelo ({r} a 1)"],
                                                     "regla del TP1": res.loc[i, "regla del TP1"]} for i, _ in validas])
                st.success(f"Se guardaron {len(validas)} pólizas en el registro.")

with pestanas[3]:
    mostrar_registro()

# --- Cómo funciona el modelo: qué pasaría en la cartera, cómo se eligió, la prueba y, a un clic, las figuras -------------------------
with pestanas[4]:
    st.subheader("El modelo en 50 segundos")
    v, _ = st.columns([3, 1])
    with v:
        video("tp3_como_funciona.mp4", "Animación sin audio, con las cifras del modelo público de esta aplicación (validación cruzada por cliente). "
              "Debajo, la explicación por escrito y lo que pasaría en toda la cartera.")
    st.subheader(f"Qué pasaría en toda la cartera con {r} a 1")
    regla = paq["regla_tp1"]
    resumen = pd.DataFrame({
        "": ["Pólizas que se revisan", "Fallas que se encuentran", "De cada 100 revisadas, cuántas fallan", "Costo por póliza (en «revisiones»)"],
        "Modelo (logística)": [porc(c_r["pólizas revisadas"]), porc(c_r["fallas detectadas"]), num(100 * c_r["precisión"], 1),
                               num(c_r["costo por póliza · modelo"])],
        "Regla del TP1": [porc(regla["pólizas revisadas"]), porc(regla["fallas detectadas"]), num(100 * regla["precisión"], 1),
                          num(c_r["costo por póliza · regla del TP1"])],
        "No revisar nada": ["0,0 %", "0,0 %", "—", num(c_r["costo por póliza · no revisar nada"])],
        "Revisar todo": ["100,0 %", "100,0 %", num(100 * tasa, 1), num(c_r["costo por póliza · revisar todo"])],
    })
    st.dataframe(resumen, hide_index=True)
    st.caption("Validación cruzada de 5 pliegues estratificados y por cliente, sobre el entrenamiento (12.650 pólizas). "
               "El costo cuenta una revisión de más como 1 y una falla que se escapa como la relación elegida.")
    st.markdown(f"""
**Cómo se eligió.** Comparamos 16 modelos (logística, k vecinos, Bayes ingenuo, árboles, SVM, bosque aleatorio, potenciación por
gradiente y votación) con la misma validación por cliente y la precisión promedio como métrica principal, porque la falla es rara y la
exactitud engaña (decir siempre «no falla» acierta el {porc(1 - tasa, 0)}). Ninguno se distinguió de la logística. La prueba se abrió
una sola vez, al final, para informar.

**El modelo de esta aplicación** es la versión pública, sin la cartera: precisión promedio de **{num(val['precision_promedio'])}** en
validación, contra **{num(paq['validacion_interno']['precision_promedio'])}** del modelo completo. No se midió en la prueba.
""")
    st.markdown("**Prueba (3.147 pólizas de clientes nuevos), todos los modelos, con el umbral de costo elegido en validación**")
    st.dataframe(en_castellano(tabla("resultados_tp3_prueba.csv")), hide_index=True)
    with st.expander("Entrenamiento, validación y prueba de todos los modelos"):
        st.dataframe(en_castellano(tabla("resultados_tp3_consolidada.csv")), hide_index=True)
    for f, texto in [("tp3_metricas_por_modelo", "Métricas por modelo en validación"),
                     ("tp3_matrices_de_confusion", "Matrices de confusión en validación, con el umbral de costo de cada modelo"),
                     ("tp3_prueba_matrices_todos", "Matrices de confusión en la prueba de los doce modelos de la tabla"),
                     ("tp3_prueba_matriz_de_confusion", "Matriz de confusión en la prueba: el modelo final y el mejor ensamble")]:
        figura(f, texto)

pie()
