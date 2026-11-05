# TP1 · El hallazgo principal: en autos, las empresas llegan a GW sin titular 2,8 veces más (§50.8, R37), con la ficha de la U4
import altair as alt
import streamlit as st
from comun import AZUL, GRIS, PORCIENTO, num, pie, porc, tabla

seg = tabla("segmentos.csv")
TIPOS = ["Empresas", "Personas", "Tipo sin confirmar"]

st.title("TP1 · Quién llega a Guidewire sin titular")
unidad = st.selectbox("Unidad de negocios", ["Todas"] + sorted(u for u in seg["unidad"].unique() if u != "Todas"),
                      help="Con «Todas» se ve el gráfico del TP1. Elegí una unidad para ver si el patrón se repite ahí.")
d = seg[(seg["unidad"] == unidad) & seg["ramo"].isin(["Autos", "Motos"]) & seg["tipo"].isin(TIPOS)].copy()
prom = seg[(seg["unidad"] == unidad) & seg["ramo"].isin(["Autos", "Motos"]) & (seg["tipo"] == "Todos")]

autos = d[d["ramo"] == "Autos"].set_index("tipo")
if {"Empresas", "Personas"} <= set(autos.index):
    veces = autos.loc["Empresas", "tasa_falla"] / autos.loc["Personas", "tasa_falla"]
    titulo = f"En autos, las empresas migran sin titular {num(veces, 1)} veces más"
else:
    titulo = "En esta unidad no hay suficientes pólizas de autos para comparar empresas y personas"
st.subheader(titulo)
st.caption("% de pólizas sin código de titular en Guidewire, por tipo de titular y ramo · línea punteada: promedio del ramo")

d["destacada"] = (d["ramo"] == "Autos") & (d["tipo"] == "Empresas")
d["tasa"] = d["tasa_falla"].map(porc)                          # texto con coma decimal
barras = alt.Chart(d).mark_bar().encode(
    x=alt.X("tasa_falla:Q", title="% sin titular", axis=alt.Axis(labelExpr=PORCIENTO), scale=alt.Scale(domain=[0, max(0.21, d["tasa_falla"].max() * 1.1)])),
    y=alt.Y("tipo:N", sort=TIPOS, title=None),
    color=alt.Color("destacada:N", scale=alt.Scale(domain=[True, False], range=[AZUL, GRIS]), legend=None),
    tooltip=[alt.Tooltip("tipo:N"), alt.Tooltip("tasa:N", title="sin titular"), alt.Tooltip("polizas:Q", title="pólizas")])
etiquetas = barras.mark_text(align="left", dx=4).encode(text="tasa:N", color=alt.value("black"))
linea = alt.Chart(prom).mark_rule(strokeDash=[4, 3], color="black").encode(x="tasa_falla:Q")
paneles = []                                                     # un panel por ramo, con el mismo eje (ficha de la U4)
for r in [r for r in ["Autos", "Motos"] if r in set(d["ramo"])]:
    capas = [barras.transform_filter(alt.datum.ramo == r), etiquetas.transform_filter(alt.datum.ramo == r)]
    if r in set(prom["ramo"]):
        capas.append(linea.transform_filter(alt.datum.ramo == r))
    paneles.append(alt.layer(*capas).properties(width=520, height=110, title=r))
if paneles:
    st.altair_chart(alt.vconcat(*paneles), width="content")
else:
    st.info("Esta unidad no tiene grupos de 20 pólizas o más.")

st.markdown(f"""
**Qué muestra.** En autos, las pólizas de **empresas** (personas jurídicas) llegan a Guidewire sin código de titular mucho más seguido
que las de **personas**. En motos no hay diferencia. La prueba de chi cuadrado se hizo **por cliente**, no por póliza, para que un
cliente con muchas pólizas no pese de más: en autos la diferencia es significativa y en motos no.

**Con cuidado.** El tipo de titular es un **supuesto del equipo**: sale de la letra del código de TIME (D = persona física, J = persona
jurídica; L, C, I y Q, inferidas). Las tasas cuentan pólizas y son del entrenamiento (la prueba no se mira). Los grupos de menos de
20 pólizas no se muestran.

**Para qué sirvió.** Este hallazgo es la «regla del TP1» (revisar los autos de personas jurídicas), que en el TP3 se compara con el
modelo.
""")
pie()
