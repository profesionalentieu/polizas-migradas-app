# comun.py · Lo que comparten todas las páginas: carga de modelos y datos, formato de números, validación de entradas y registro.
# Estructura tomada de las apps de la cátedra: el modelo se carga una sola vez con @st.cache_resource y los datos con
# @st.cache_data [CL29, celdas 76–80; app_clase32.py; app_clase35.py].
from pathlib import Path
import datetime
import re
import unicodedata
import warnings

import joblib
import numpy as np
import pandas as pd
import streamlit as st

AQUI = Path(__file__).resolve().parent
# Una cartera chica o nueva («Otro productor») entra al modelo como una categoría que no vio, y cae a propósito en el grupo de las
# carteras chicas (handle_unknown="infrequent_if_exist"); scikit-learn lo avisa cada vez, y ese aviso no se muestra (como en la §55)
warnings.filterwarnings("ignore", message="Found unknown categories")
FUENTE = ("Fuente: lote 107 de pólizas migradas de TIME a Guidewire (corte: 29/10/2025), solo la parte de entrenamiento (12.650 pólizas). "
          "Datos agregados (ninguna celda con menos de 20 pólizas) y modelos en versión pública, sin códigos de cartera.")
AZUL, GRIS, ROJO = "#003A63", "#9A9A9A", "#B03A2E"
# Ejes de Altair con punto de miles y coma decimal (Vega formatea en inglés)
MILES = "replace(format(datum.value, ',.0f'), /,/g, '.')"
PORCIENTO = "replace(format(datum.value, '.0%'), '%', ' %')"


# --- Carga -------------------------------------------------------------------------------------------------------------------
@st.cache_resource
def modelo(nombre):
    """Carga un modelo público con todo su preprocesamiento (se entrenó en la §67 del cuaderno)."""
    return joblib.load(AQUI / "modelos" / nombre)


@st.cache_data
def tabla(nombre):
    """Lee una tabla agregada de la carpeta datos/."""
    return pd.read_csv(AQUI / "datos" / nombre)


def archivo(nombre):
    """Bytes de un archivo de datos/, para los botones de descarga."""
    return (AQUI / "datos" / nombre).read_bytes()


# --- Formato (coma decimal y punto de miles, como en Argentina) ---------------------------------------------------------------
def pesos(v):
    return f"$ {v:,.0f}".replace(",", ".")


def md(texto):
    """Escapa los $ para Markdown: dos $ en un mismo texto activan el modo matemático de Streamlit."""
    return texto.replace("$", r"\$")


def porc(v, decimales=1):
    return f"{100 * v:.{decimales}f} %".replace(".", ",")


def num(v, decimales=3):
    return f"{v:.{decimales}f}".replace(".", ",")


def en_castellano(df, decimales=3):
    """Tabla para mostrar: los números como texto con coma decimal y punto de miles (st.dataframe los muestra en inglés)."""
    def f(v):
        if isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool) and np.isfinite(v):
            d = 0 if abs(v) >= 1000 else decimales
            return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return "—" if isinstance(v, float) else v
    return df.apply(lambda col: col.map(f) if col.dtype.kind in "fi" else col)


def figura(nombre, texto):
    """Una figura de los resultados dentro de un desplegable: queda a un clic y no alarga la página."""
    with st.expander(texto):
        st.image(str(AQUI / "figuras" / f"{nombre}.png"), width="stretch")


def pie():
    st.divider()
    st.caption(FUENTE)


# --- Nombres legibles de las variables y de sus valores ---------------------------------------------------------------------
NOMBRES = {
    "poliza_combinada": "Póliza combinada (paquete contratado)", "etiqueta_producto_time": "Producto",
    "etiqueta_unidad_de_negocios": "Unidad de negocios", "letra_titular_time": "Tipo de titular",
    "etiqueta_condicion_iva": "Condición ante el IVA", "frecuencia_de_pago": "Frecuencia de pago",
    "pertenece_grupo_estadistico": "Pertenece a un grupo estadístico", "despacho_digital": "Despacho digital",
    "indicador_de_clausula_de_no_anulacion_y_no_modificacion": "Cláusula de no anulación", "tipo_renovacion_time": "Tipo de renovación",
    "cantidad_de_cuotas": "Cantidad de cuotas (0 = mensual)", "cantidad_de_meses": "Meses de vigencia",
    "polizas_vinculadas": "Pólizas vinculadas (0 si no tiene)", "prima_mensual": "Prima mensual en TIME ($)", "ramo": "Ramo",
    "nro_productor": "Productor", "nro_organizador": "Organizador", "oficial_de_negocio": "Oficial de negocios",
}
# La cartera va con seudónimos por tamaño («Productor 1» = la cartera más grande); «__otro__» es cualquier cartera chica o nueva
OTRA_CARTERA = {"nro_productor": "Otro productor", "nro_organizador": "Otro organizador", "oficial_de_negocio": "Otro oficial"}
LEGIBLE = {"True": "Sí", "False": "No", "1.0": "Sí", "0.0": "No", "vacío": "Sin dato",
           "automatic": "Automática", "manual": "Manual", "not_have": "Sin renovación"}
NUMERICAS = ["cantidad_de_cuotas", "cantidad_de_meses", "polizas_vinculadas"]


def legible(col, valor, paq):
    """Cómo se muestra al usuario un valor que el modelo conoce."""
    if col == "letra_titular_time":
        return f"{valor} · {paq['etiqueta_letra'].get(valor, '')}"
    if valor == "__otro__":
        return f"{OTRA_CARTERA[col]} (cartera chica o nueva)"
    return LEGIBLE.get(str(valor), str(valor))


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto).strip().lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def a_modelo(col, texto, paq):
    """Traduce lo que escribió el usuario (en el formulario o en el CSV) al valor que espera el modelo; None si no lo reconoce."""
    buscado = _normalizar(texto)
    for v in paq["opciones"][col]:
        alias = {_normalizar(OTRA_CARTERA[col])} if v == "__otro__" else set()
        if buscado in {_normalizar(v), _normalizar(legible(col, v, paq)), _normalizar(LEGIBLE.get(str(v), v))} | alias:
            return v
    return None


# --- Validación: rangos, tipos y combinaciones, para no dar predicciones sin sentido -----------------------------------------
def _numero(texto):
    """Convierte a número un valor del formulario o del CSV. Acepta «13500», «13.500», «13500,5» y «13500.5»; None si no es un número."""
    if isinstance(texto, (int, float, np.number)):
        return float(texto)
    s = str(texto).strip().replace("$", "").replace(" ", "")
    if "," in s:                                                 # coma decimal: los puntos son de miles
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", s):                  # solo puntos de miles
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def _entero(texto):
    """Convierte a número entero. Devuelve None si no es un número entero."""
    v = _numero(texto)
    return int(v) if v is not None and np.isfinite(v) and v == int(v) else None


def validar(entrada, paq, con_prima=False):
    """Revisa una póliza. Devuelve (fila para el modelo o None, errores, avisos).
    Errores: la estimación no se hace (categoría desconocida, número inválido o fuera del rango del entrenamiento, ramo contradictorio).
    Avisos: la estimación se hace, pero conviene leerla con cuidado (combinación que no aparece en los datos de entrenamiento)."""
    fila, errores, avisos = {}, [], []
    for col in paq["opciones"]:
        texto = entrada.get(col)
        if texto is None or (isinstance(texto, float) and np.isnan(texto)) or str(texto).strip() == "":
            errores.append(f"falta «{NOMBRES[col]}»")
            continue
        v = a_modelo(col, texto, paq)
        if v is None:
            validos = ", ".join(legible(col, o, paq) for o in paq["opciones"][col])
            errores.append(f"«{NOMBRES[col]}» = «{texto}» no es un valor conocido (valores posibles: {validos})")
        else:
            fila[col] = v
    for col in NUMERICAS:
        v = _entero(entrada.get(col, ""))
        vistos = paq["numericas"][col]
        if v is None:
            errores.append(f"«{NOMBRES[col]}» = «{entrada.get(col, '')}» no es un número entero")
        elif not min(vistos) <= v <= max(vistos):
            errores.append(f"«{NOMBRES[col]}» = {v} está fuera del rango de los datos ({int(min(vistos))} a {int(max(vistos))})")
        else:
            fila[col] = float(v)
            if float(v) not in vistos:
                avisos.append(f"«{NOMBRES[col]}» = {v} no aparece en los datos de entrenamiento")
    if "frecuencia_de_pago" in fila and "cantidad_de_cuotas" in fila:
        if (fila["frecuencia_de_pago"], fila["cantidad_de_cuotas"]) not in {tuple(c) for c in paq["combinaciones_pago"]}:
            avisos.append(f"la combinación «{fila['frecuencia_de_pago']}» con {int(fila['cantidad_de_cuotas'])} cuotas no aparece en los datos")
    if con_prima:
        rango = paq["prima_mensual"]
        prima = _numero(entrada.get("prima_mensual", ""))
        if prima is None or not np.isfinite(prima):
            errores.append(f"«{NOMBRES['prima_mensual']}» = «{entrada.get('prima_mensual', '')}» no es un número")
        elif not rango["min"] <= prima <= rango["max"]:
            errores.append(f"«{NOMBRES['prima_mensual']}» = {pesos(prima)} está fuera del rango de los datos ({pesos(rango['min'])} a {pesos(rango['max'])})")
        else:
            fila["log_prima_mensual"] = float(np.log(prima))
            if not rango["p01"] <= prima <= rango["p99"]:
                avisos.append(f"la prima de {pesos(prima)} está entre el 1 % más extremo de los datos")
        ramo = str(entrada.get("ramo", "")).strip().capitalize()
        if ramo not in ("Autos", "Motos"):
            errores.append(f"«Ramo» = «{entrada.get('ramo', '')}» tiene que ser Autos o Motos")
        else:
            fila["ramo"] = ramo
            esperado = paq["ramo_de_combinada"].get(fila.get("poliza_combinada"))
            if esperado and esperado != ramo:
                errores.append(f"el ramo «{ramo}» no coincide con la póliza combinada «{fila['poliza_combinada']}», que es de {esperado}")
    return (fila if not errores else None), errores, avisos


def leer_csv(subido, columnas):
    """Lee el CSV subido; si faltan columnas, lo dice y no sigue."""
    try:
        df = pd.read_csv(subido, dtype=str, sep=None, engine="python", encoding="utf-8-sig")
    except Exception as e:                                       # archivo vacío, mal codificado o que no es un CSV
        st.error(f"No se pudo leer el archivo como CSV ({e}). Usá la plantilla.")
        return None
    faltan = [c for c in columnas if c not in df.columns]
    if faltan:
        st.error("Al archivo le faltan columnas: " + ", ".join(faltan) + ". Usá la plantilla.")
        return None
    if len(df) > 5000:
        st.error(f"El archivo tiene {len(df)} filas; el máximo es 5.000.")
        return None
    return df


# --- Registro de predicciones -------------------------------------------------------------------------------------------------
def registrar(pagina, filas):
    """Agrega predicciones al registro de la sesión (una por póliza)."""
    ahora = datetime.datetime.now().isoformat(timespec="seconds")
    st.session_state.setdefault("registro", []).extend({"fecha y hora": ahora, "página": pagina, **f} for f in filas)


def mostrar_registro():
    st.subheader("Registro de predicciones de esta sesión")
    st.caption("En Streamlit Community Cloud, los archivos que escribe la aplicación se borran cada vez que se reinicia. Por eso el registro "
               "se guarda solo en esta sesión del navegador: **descargalo antes de cerrar la pestaña**, porque al recargar la página se pierde.")
    registro = st.session_state.get("registro", [])
    if not registro:
        st.info("Todavía no guardaste ninguna predicción. Usá el botón «Guardar en el registro» en las pestañas «Una póliza» o «Cargar un lote».")
        return
    df = pd.DataFrame(registro)
    st.dataframe(df, hide_index=True)
    c1, c2 = st.columns(2)
    c1.download_button("Descargar el registro (CSV)", df.to_csv(index=False).encode("utf-8-sig"), "registro_de_predicciones.csv", "text/csv")
    if c2.button("Vaciar el registro"):
        st.session_state["registro"] = []
        st.rerun()
