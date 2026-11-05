# Datos y limpieza: del archivo original a la base limpia, en conteos (sin filas ni nombres de columnas)
import altair as alt
import streamlit as st
from comun import AZUL, pie, tabla

ind = tabla("limpieza_indicadores.csv").set_index("indicador")["valor"]
imp = tabla("limpieza_imputaciones.csv")
pasos = tabla("limpieza_pasos.csv")
miles = lambda v: f"{int(v):,}".replace(",", ".")

st.title("Datos y limpieza")
st.markdown("El punto de partida es un Excel con las pólizas del lote 107: una fila por póliza, con sus datos en TIME y el resultado "
            "de la migración a Guidewire. El archivo original **no se modifica**: se guardó una copia de solo lectura con su huella digital.")

k = st.columns(4)
k[0].metric("Pólizas en el original", miles(ind["Filas del dataset original"]))
k[1].metric("Columnas en el original", miles(ind["Columnas del dataset original"]))
k[2].metric("Pólizas en la base limpia", miles(ind["Filas de la base limpia"]))
k[3].metric("Operaciones registradas", miles(ind["Operaciones registradas en el registro de cambios"]))

st.subheader("Tres reglas que seguimos")
st.markdown(f"""
1. **No borrar nada.** Las {miles(ind['Filas apartadas (copias de integración, con motivo)'])} filas que sobraban (copias de la misma
   póliza que dejó la integración) y las {miles(ind['Columnas apartadas (vacías, constantes o sin uso, con motivo)'])} columnas que no
   servían (vacías, constantes o sin uso) se movieron a hojas aparte, cada una con su motivo y su número de fila original.
2. **Toda imputación lleva una bandera.** Cuando un dato faltante se completó con una regla, una columna `imputado_…` lo marca, para
   que cualquier análisis pueda separarlo.
3. **En la base limpia, solo reglas.** Lo que se aprende de los datos (modas, medias, escalas, agrupamiento de categorías raras) se
   calcula después, dentro de cada modelo y solo con el entrenamiento, para no filtrar información.
""")

st.subheader("Datos completados por regla")
st.altair_chart(alt.Chart(imp).mark_bar(color=AZUL).encode(
    x=alt.X("celdas imputadas:Q", title="celdas completadas"), y=alt.Y("variable:N", sort="-x", title=None),
    tooltip=["variable:N", "celdas imputadas:Q"]).properties(height=200), width="stretch")
st.caption("Por ejemplo, en las pólizas mensuales la cantidad de cuotas está vacía y se completa con 0 (supuesto del equipo, no confirmado "
           "por la empresa). La categoría «No combinada» también es imputada (supuesto), y por eso se declara en los dos modelos.")

st.subheader("Los pasos de la limpieza")
st.dataframe(pasos[["paso", "operaciones"]], hide_index=True)
st.caption("Cada operación quedó en la hoja «registro_de_cambios» de la base limpia, con la decisión del equipo que la aprobó.")

st.subheader("La partición, antes de mirar los datos")
st.markdown(f"""
Antes de explorar, separamos el **80 % de los clientes** para entrenar ({miles(ind['Pólizas de entrenamiento (80 %, por cliente)'])}
pólizas) y el **20 %** para la prueba final ({miles(ind['Pólizas de prueba (20 %, por cliente)'])} pólizas). La partición es **por
cliente**: todas las pólizas de un mismo cliente quedan del mismo lado, para que ningún modelo «reconozca» a un cliente que ya vio.
""")

st.subheader("Lo que corregimos de la limpieza anterior")
st.markdown("""
Antes de este trabajo, otra herramienta de IA había limpiado el mismo archivo. La usamos solo como consulta y verificamos con código
cada cosa que hizo. Encontramos 8 errores verificados y otras decisiones sin registro; por ejemplo:
- leyó como números identificadores que eran texto y **perdió los ceros iniciales**;
- creó un «cliente consolidado» que **completaba el código de un sistema con el de otra fila**;
- **reemplazó códigos por etiquetas** inventadas y **agrupó categorías raras** sin dejar registro;
- **imputó sin bandera** y contó mal filas y columnas.
""")
pie()
