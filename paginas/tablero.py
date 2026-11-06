# Tablero (LAB06, propuesta P2): tres vistas vinculadas por un filtro común y por un clic en la unidad.
# El LAB06 usa plotly; acá se usa Altair, que viene con Streamlit (R70; documentación de Altair: selection_point)
import altair as alt
import streamlit as st
from comun import AZUL, GRIS, MILES, PORCIENTO, pesos, pie, porc, tabla

seg = tabla("segmentos.csv")

st.title("Tablero: fallas, primas y pólizas a revisar, por unidad")
st.markdown("Elegí un ramo y un tipo de cliente. Las tres vistas muestran lo mismo para cada unidad de negocios: **cuántas pólizas "
            "llegaron sin titular** (TP1), **cuánto pagan por mes** (TP2) y **cuántas mandaría a revisar el modelo** (TP3). "
            "**Hacé clic en una barra** para resaltar esa unidad en las tres vistas; doble clic para volver.")

f1, f2 = st.columns(2)
ramo = f1.segmented_control("Ramo", ["Todos", "Autos", "Motos"], default="Todos", required=True, key="tab_ramo")
tipo = f2.segmented_control("Tipo de cliente", ["Todos", "Personas", "Empresas", "Tipo sin confirmar"], default="Todos", required=True, key="tab_tipo")

total = seg[(seg["ramo"] == ramo) & (seg["tipo"] == tipo) & (seg["unidad"] == "Todas")]
datos = seg[(seg["ramo"] == ramo) & (seg["tipo"] == tipo) & (seg["unidad"] != "Todas")].copy()
if total.empty:
    st.warning("Este grupo tiene menos de 20 pólizas: no se muestra.")
    st.stop()
t = total.iloc[0]
k = st.columns(4)
k[0].metric("Pólizas", f"{int(t['polizas']):,}".replace(",", "."))
k[1].metric("Llegaron sin titular", porc(t["tasa_falla"]))
k[2].metric("Prima mensual mediana", pesos(t["prima_mediana"]))
k[3].metric("El modelo mandaría a revisar", porc(t["revisaria_modelo"]))

if datos.empty:
    st.info("Ninguna unidad tiene 20 pólizas o más en este grupo.")
else:
    for c in ["tasa_falla", "revisaria_modelo"]:                  # textos con coma decimal y punto de miles para los tooltips
        datos[c + "_txt"] = datos[c].map(porc)
    for c in ["prima_mediana", "prima_p25", "prima_p75"]:
        datos[c + "_txt"] = datos[c].map(pesos)
    orden = datos.sort_values("polizas", ascending=False)["unidad"].tolist()
    clic = alt.selection_point(fields=["unidad"], on="click", clear="dblclick")
    color = alt.condition(clic, alt.value(AZUL), alt.value(GRIS))
    y = alt.Y("unidad:N", sort=orden, title=None)
    comun_tt = [alt.Tooltip("unidad:N"), alt.Tooltip("polizas:Q", title="pólizas")]
    base = alt.Chart(datos).properties(width=230, height=24 * len(datos) + 20)
    v1 = base.mark_bar().encode(
        x=alt.X("tasa_falla:Q", title="% sin titular", axis=alt.Axis(labelExpr=PORCIENTO)), y=y, color=color,
        tooltip=comun_tt + [alt.Tooltip("tasa_falla_txt:N", title="sin titular")]
    ).add_params(clic).properties(title="1 · Llegaron sin titular (TP1)")
    promedio = alt.Chart(total).mark_rule(strokeDash=[4, 3], color="black").encode(x="tasa_falla:Q")
    v2 = alt.layer(
        base.mark_rule(size=1).encode(x=alt.X("prima_p10:Q", title="prima mensual ($)", axis=alt.Axis(labelExpr=MILES)), x2="prima_p90:Q", y=y, color=color),
        base.mark_bar(size=12).encode(x="prima_p25:Q", x2="prima_p75:Q", y=y, color=color),
        base.mark_tick(color="white", thickness=2, size=12).encode(
            x="prima_mediana:Q", y=y,
            tooltip=comun_tt + [alt.Tooltip("prima_mediana_txt:N", title="mediana"),
                                alt.Tooltip("prima_p25_txt:N", title="25 %"), alt.Tooltip("prima_p75_txt:N", title="75 %")]),
    ).properties(title="2 · Prima mensual: mediana, mitad central y 80 % (TP2)")
    v3 = base.mark_bar().encode(
        x=alt.X("revisaria_modelo:Q", title="% a revisar", axis=alt.Axis(labelExpr=PORCIENTO)), y=y, color=color,
        tooltip=comun_tt + [alt.Tooltip("revisaria_modelo_txt:N", title="a revisar")]
    ).properties(title="3 · El modelo mandaría a revisar (TP3)")
    apiladas = st.toggle("Mostrar las vistas una debajo de la otra (para pantallas angostas)", key="tab_apiladas")
    unir = alt.vconcat if apiladas else alt.hconcat
    st.altair_chart(unir(v1 + promedio, v2, v3).resolve_scale(y="shared"), width="content")
    with st.expander("Cómo leer las tres vistas"):
        st.caption("Línea punteada en la vista 1: la tasa del grupo elegido. Vista 2: la marca blanca es la mediana; la barra, la mitad central "
                   "de las primas (del 25 % al 75 %); la línea fina, del 10 % al 90 %. Vista 3: decisiones del modelo público con 10 a 1, "
                   "medidas con validación cruzada (cada póliza la evaluó un modelo que no la vio). "
                   "No se muestran las unidades con menos de 20 pólizas en el grupo.")
pie()
