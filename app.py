# app.py · Aplicación única del proyecto «Pólizas migradas de TIME a Guidewire» (TP4, R70).
# Punto de entrada: arma la navegación entre páginas. Desde la carpeta de la aplicación:
#     streamlit run app.py
import streamlit as st

st.set_page_config(page_title="Pólizas migradas", layout="wide")

paginas = {
    "El proyecto": [
        st.Page("paginas/inicio.py", title="Inicio", default=True),
        st.Page("paginas/datos_y_limpieza.py", title="Datos y limpieza"),
    ],
    "Los trabajos prácticos": [
        st.Page("paginas/tp1.py", title="TP1 · Quién llega sin titular"),
        st.Page("paginas/tablero.py", title="Tablero"),
        st.Page("paginas/prima_mensual.py", title="TP2 · Prima mensual"),
        st.Page("paginas/revision.py", title="TP3 · Revisar antes de migrar"),
    ],
    "Cómo lo hicimos": [
        st.Page("paginas/metodologia.py", title="Metodología"),
    ],
}
st.navigation(paginas).run()
