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
VERDE, NARANJA = "#2E7D32", "#B35400"        # decisión del TP3: verde para «No revisar» y naranja para «Revisar» (se leen con letra blanca)
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


def video(nombre, texto):
    """La animación de cómo funciona el modelo: un MP4 sin audio, hecho con herramientas/videos_app.py y las cifras del modelo público."""
    st.video(str(AQUI / "videos" / nombre))
    st.caption(texto)


def decision(texto, revisar):
    """Una decisión en una caja de color: naranja si conviene revisar y verde si no. El texto admite **negrita** de Markdown."""
    color, signo = (NARANJA, "⚠") if revisar else (VERDE, "✓")
    html = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
    st.markdown(f'<div style="background:{color}; color:#fff; padding:0.7rem 1rem; border-radius:0.5rem; font-size:1.1rem; '
                f'margin-bottom:0.7rem">{signo} {html}</div>', unsafe_allow_html=True)


def letra_grande(grafico, letra=15):
    """Letra más grande en los ejes y el título: los gráficos se leen en una columna angosta y proyectados (la letra de Altair es de 11 px)."""
    return grafico.configure_axis(labelFontSize=letra, titleFontSize=letra).configure_title(fontSize=letra + 2)


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


def valores_iniciales(prefijo, paq, extras=None):
    """Valor inicial de cada campo del formulario, tal como lo muestra el widget: el primer valor de cada categoría (el más común),
    12 meses, 0 cuotas y 0 vinculadas, y la cartera chica o nueva."""
    cartera = paq.get("cartera_defecto", {})
    d = {f"{prefijo}_{col}": legible(col, cartera.get(col, v[0]), paq) for col, v in paq["opciones"].items()}
    d |= {f"{prefijo}_{col}": 12 if col == "cantidad_de_meses" else 0 for col in NUMERICAS}
    return d | (extras or {})


def ejemplos_rapidos(prefijo, paq, iniciales, ejemplos):
    """Pone los valores iniciales del formulario y un selector que carga pólizas típicas. Cada ejemplo es {columna: valor del modelo},
    con solo lo que cambia respecto de los valores iniciales. La carga corre como callback, antes de que se dibujen los widgets:
    es el momento en que Streamlit deja cambiar sus valores."""
    for k, v in iniciales.items():
        st.session_state.setdefault(k, v)
    clave = f"{prefijo}_ejemplo"

    def cargar():
        nombre = st.session_state[clave]
        if nombre:
            st.session_state.update(iniciales)
            st.session_state.update({f"{prefijo}_{col}": legible(col, v, paq) if col in paq["opciones"] else v
                                     for col, v in ejemplos[nombre].items()})
            st.session_state[f"{clave}_cargado"] = nombre
            st.session_state[clave] = None                     # el selector vuelve a quedar vacío: se puede cargar el mismo ejemplo otra vez

    st.selectbox("Ejemplos rápidos", list(ejemplos), index=None, placeholder="Elegí una póliza típica para cargar sus datos",
                 key=clave, on_change=cargar)
    if st.session_state.get(f"{clave}_cargado"):
        st.caption(f"Último ejemplo cargado: «{st.session_state[f'{clave}_cargado']}». Se puede cambiar cualquier dato.")


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


# --- La pestaña «Todos los modelos» del TP2 y del TP3: todo lo que se comparó, más grande que en el artículo (R91) -----------------
ELEGIDOS = {"TP2": "grado 2 + Lasso", "TP3": "regresión logística"}
# Los que sobreajustan: la mayor brecha entre entrenamiento y validación de cada TP (los mismos que en rojo en el artículo)
# (por TP: k vecinos sobreajusta en el TP2, pero no en el TP3)
SOBREAJUSTAN = {"TP2": ["k vecinos", "grado 2 sin freno", "bosque aleatorio · por objetivo", "potenciación por gradiente · por objetivo",
                        "grado 2 + Lasso · por objetivo en unidad y cartera"],
                "TP3": ["SVM con núcleo gaussiano", "bosque aleatorio · por objetivo", "potenciación por gradiente · por objetivo",
                        "votación suave · por objetivo", "logística · por objetivo en unidad y cartera (§61)"]}


def coma(v, d=3):
    return f"{v:.{d}f}".replace(".", ",")


def grafico_entrenamiento_validacion_prueba(tp):
    """Los tres puntos de cada modelo en una fila, ordenados por la brecha entre entrenamiento y validación (arriba, la mayor)."""
    import json
    import altair as alt
    if tp == "TP2":
        res, met, eje = tabla("resultados_tp2.csv"), "R²", "R² del log de la prima (más alto es mejor)"
        res = res[~res["modelo"].str.startswith("línea de base")]
    else:
        res, met, eje = tabla("resultados_tp3_consolidada.csv"), "precisión promedio", "precisión promedio (más alto es mejor; azar: 0,068)"
    conjuntos = ["entrenamiento", "validación", "prueba"]
    res = res.assign(brecha=res[f"{met} · entrenamiento"] - res[f"{met} · validación"]).sort_values("brecha", ascending=False)
    res["etiqueta"] = [m + ("  ★ elegido" if m == ELEGIDOS[tp] else "") for m in res["modelo"]]
    largo = res.melt(id_vars=["modelo", "etiqueta", "brecha"], value_vars=[f"{met} · {c}" for c in conjuntos], var_name="conjunto", value_name="valor")
    largo["conjunto"] = largo["conjunto"].str.split(" · ").str[1]
    largo["valor_txt"] = largo["valor"].map(coma)
    largo["brecha_txt"] = largo["brecha"].map(coma)
    rangos = largo.groupby("etiqueta", as_index=False)["valor"].agg(minimo="min", maximo="max")
    rojos = [e for e, m in zip(res["etiqueta"], res["modelo"]) if m in SOBREAJUSTAN[tp]]
    color_etiqueta = (f"indexof({json.dumps(rojos)}, datum.value) >= 0 ? '{ROJO}' : "
                      f"(indexof(datum.value, 'elegido') >= 0 ? '{AZUL}' : '#222222')")
    y = alt.Y("etiqueta:N", sort=list(res["etiqueta"]), title=None,
              axis=alt.Axis(labelLimit=460, labelFontSize=13, labelColor=alt.ExprRef(color_etiqueta)))
    reglas = alt.Chart(rangos).mark_rule(color="#D0D0D0", strokeWidth=5).encode(y=y, x=alt.X("minimo:Q"), x2="maximo:Q")
    puntos = alt.Chart(largo).mark_point(filled=True, size=130, opacity=1).encode(
        y=y, x=alt.X("valor:Q", title=eje, scale=alt.Scale(zero=False),
                     axis=alt.Axis(labelExpr="replace(format(datum.value, '.2f'), '.', ',')", titleFontSize=13, labelFontSize=12)),
        color=alt.Color("conjunto:N", scale=alt.Scale(domain=conjuntos, range=[GRIS, AZUL, NARANJA]),
                        legend=alt.Legend(orient="top", title=None, labelFontSize=13)),
        shape=alt.Shape("conjunto:N", scale=alt.Scale(domain=conjuntos, range=["circle", "circle", "diamond"]), legend=None),
        tooltip=[alt.Tooltip("modelo:N"), alt.Tooltip("conjunto:N"), alt.Tooltip("valor_txt:N", title=met),
                 alt.Tooltip("brecha_txt:N", title="brecha entrenamiento − validación")])
    st.altair_chart((reglas + puntos).properties(height=34 * len(res) + 40), width="stretch")
    return res


def todos_los_modelos(tp):
    """Pestaña «Todos los modelos»: entrenamiento, validación y prueba; curvas de aprendizaje; predicho contra real (TP2) o matrices de
    confusión (TP3); curvas de validación y los hiperparámetros de cada uno. Todo es validación cruzada por cliente, salvo lo que dice «prueba»."""
    ap = tabla("todos_curvas_aprendizaje.csv")
    ap = ap[ap["tp"] == tp]
    fin = ap.sort_values("pólizas de entrenamiento").groupby("modelo").last()
    fin["brecha"] = fin["entrenamiento"] - fin["validación"]
    n_modelos, elegido = len(fin), ELEGIDOS[tp]
    met = "R²" if tp == "TP2" else "precisión promedio"
    st.markdown(f"Acá están **los {n_modelos} modelos que comparamos**, no solo el elegido ({elegido}). Todo sale de la misma validación "
                "cruzada de 5 pliegues **por cliente** (las pólizas de un cliente nunca quedan de los dos lados); la prueba (3.147 pólizas de "
                "clientes nuevos) aparece solo donde lo dice, y se abrió recién con el modelo ya elegido.")

    st.subheader("1. Entrenamiento, validación y prueba de cada modelo")
    res = grafico_entrenamiento_validacion_prueba(tp).set_index("modelo")
    st.markdown(f"""
**Cómo se lee.** Cada fila es un modelo, con tres puntos: **gris**, cómo le va con las pólizas con las que aprendió; **azul**, con
clientes que no vio (validación); **naranja**, en la prueba. Si el gris queda lejos del azul, el modelo **memorizó** (sobreajuste):
arriba están los de mayor brecha, con el nombre en rojo. Si los tres quedan juntos pero no muy altos, el modelo **no tiene de dónde
aprender más** (subajuste). El elegido tiene una brecha de **{coma(res.loc[elegido, 'brecha'])}**; el de mayor brecha,
**{res.index[0]}**, de **{coma(res['brecha'].iloc[0])}**. Pasá el cursor por un punto para ver su valor.
""")

    st.subheader("2. Curvas de aprendizaje de todos los modelos")
    st.image(str(AQUI / "figuras" / f"{tp.lower()}_curvas_aprendizaje_todos.png"), width="stretch")
    planos = int((fin["brecha"] < 0.03).sum())
    st.markdown(f"""
**Cómo se lee.** Cada panel es un modelo entrenado con cada vez más pólizas (eje horizontal): en gris, su {met} con las pólizas con
las que aprendió; en azul, con clientes que no vio. **Sobreajusta** el modelo cuyas curvas quedan separadas (la brecha está escrita
en cada panel): aprende detalles de esas pólizas que no se repiten en clientes nuevos. **Subajusta** el que tiene las dos
curvas juntas y planas: con más pólizas no mejora, porque el límite son **las variables que faltan** (el vehículo, la suma asegurada,
la zona, el historial), no la cantidad de datos.

**Por qué quedó el elegido.** {elegido} tiene las curvas juntas (brecha de {coma(fin.loc[elegido, 'brecha'])}) y su validación es
tan buena como la del mejor: ningún modelo más complejo le ganó en los 5 pliegues por más que el desvío. Entre modelos que empatan, se
queda el más simple, que además se puede explicar variable por variable. {planos} de los {n_modelos} modelos tienen una brecha menor que 0,03.

Los hiperparámetros de cada curva son los que más eligió la búsqueda en los 5 pliegues, y hay 6 tamaños por curva, del
{"25" if tp == "TP2" else "10"} % al 100 % del entrenamiento de cada pliegue, como en el cuaderno.
""")

    if tp == "TP2":
        st.subheader("3. Predicho contra real de todos los modelos, en la prueba")
        st.image(str(AQUI / "figuras" / "tp2_predicho_contra_real.png"), width="stretch")
        st.markdown("""
**Cómo se lee.** Cada punto es una póliza de la prueba: su prima real (eje horizontal) contra la que estimó el modelo (eje vertical),
en escala logarítmica. Sobre la diagonal, el modelo acierta. Todos dibujan la misma nube, porque les faltan los mismos datos: se
quedan cortos en las primas muy altas y se pasan en las muy bajas. El árbol arma escalones (da pocas primas distintas) y k vecinos, la
nube más ancha.
""")
    else:
        st.subheader("3. Matrices de confusión de todos los modelos")
        st.image(str(AQUI / "figuras" / "tp3_matrices_validacion_todos.png"), width="stretch")
        st.markdown("""
**Cómo se lee.** Cada matriz cruza lo que pasó (filas: con titular o sin titular) con lo que decidió el modelo (columnas: no revisar
o revisar), con el umbral que minimiza el costo cuando dejar pasar una falla cuesta 10 veces más que revisar una póliza de más. Arriba
de cada una: qué parte de las pólizas manda a revisar, qué parte de las fallas encuentra y el costo por póliza. Estas son de
**validación**, para los 16 modelos; las de la **prueba**, de los 12 de la tabla del informe, están en el desplegable.

**Un detalle honesto.** En validación, varios modelos tienen un costo algo menor que la logística (de 0,575 a 0,599 contra 0,608).
Son cifras algo optimistas para todos, porque cada umbral se eligió sobre los mismos puntajes con los que se mide el costo. La elección
no se hizo por esta cifra, sino antes, por la precisión promedio (donde ninguno se distinguió más que el desvío), por la calibración de
las probabilidades y por la simplicidad. En la prueba, que no se usó para elegir, la logística resultó la de menor costo (0,623).
""")
        figura("tp3_prueba_matrices_todos", "Matrices de confusión en la prueba (los 12 modelos de la tabla del informe)")

    st.subheader("4. Curvas de validación")
    st.image(str(AQUI / "figuras" / f"{tp.lower()}_curvas_validacion_todos.png"), width="stretch")
    st.markdown("""
**Cómo se lee.** Acá cambia un solo ajuste del modelo (eje horizontal) y se mide con las pólizas con las que aprendió (gris) y con
clientes que no vio (azul). Con un ajuste que lo hace muy simple, le va parecido en los dos; con uno que lo hace muy flexible, memoriza:
el gris sigue subiendo y el azul baja. La línea naranja marca el mejor valor en validación, que es el que conviene.
""")

    with st.expander("Los hiperparámetros de cada modelo y el control contra el cuaderno"):
        h = tabla("todos_hiperparametros.csv")
        h = h[h["tp"] == tp].drop(columns="tp")
        st.dataframe(en_castellano(h, 4), hide_index=True)
        st.caption("Validación anidada: en cada pliegue, una búsqueda interna de 3 pliegues por cliente elige los hiperparámetros. «Fijados» son "
                   "los que más eligió en los 5 pliegues, con los que se trazaron las curvas de aprendizaje. La validación reproducida da la "
                   "del cuaderno.")
