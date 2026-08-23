import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import json
import os
import base64
from PIL import Image

# --- 0. RUTAS DE LOS ICONOS LOCALES ---
PATH_CHART = "./assets/icons8-arrow-rising-over-colorful-bar-chart-indicating-positive-business-growth-100.png"
PATH_COPY = "./assets/icons8-purple-copy-ui-element-100.png"
PATH_GEAR = "./assets/icons8-purple-gear,-system-configuration-100.png"
PATH_TASK = "./assets/icons8-task-progress-tracking-100.png"
PATH_LEGEND_NORMAL = "./assets/icons8-round-shape-100.png"
PATH_LEGEND_CRITICAL = "./assets/icons8-round-shape-100 (1).png"

try:
    favicon = Image.open(PATH_CHART)
except FileNotFoundError:
    favicon = "📈"

st.set_page_config(page_title="Gantt Studio", page_icon=favicon, layout="wide")

# --- FUNCIONES PARA INYECTAR PNG ---
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

def cargar_icono_local(ruta_imagen, width=35):
    encoded = get_base64_of_bin_file(ruta_imagen)
    if encoded:
        # Se elimina el margin-right quemado para controlarlo mejor con CSS flexbox en el contenedor
        return f'<img src="data:image/png;base64,{encoded}" style="width: {width}px; display: block;" />'
    return ""

# --- 1. CONFIGURACIÓN CSS AVANZADA ---
dark_material_css = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"], .stMarkdown p, label, .stSelectbox {{ 
        font-family: 'Roboto', sans-serif; 
        font-size: 17px !important; 
    }}
    .stApp {{ background-color: #121212; }}
    
    .title-flex {{ display: flex; align-items: center; gap: 12px; margin-bottom: 0.5rem; color: #FFFFFF; font-weight: 500; }}
    
    /* Armonización de la Barra Lateral */
    .sidebar-title {{ 
        display: flex; 
        align-items: center; 
        gap: 12px; /* Espacio exacto entre icono y texto */
        font-size: 1.25rem; /* Tamaño de letra reducido para armonizar con icono de 24px */
        margin-top: 1rem; 
        margin-bottom: 0.5rem; 
        color: #FFFFFF; 
        font-weight: 500; 
    }}
    
    /* Contenedor de la barra de acciones superior */
    .action-bar {{
        display: flex; align-items: center; justify-content: space-between;
        background-color: #1E1E1E; padding: 16px 24px; border-radius: 12px;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.3); border: 1px solid #333333;
        margin-bottom: 24px;
        height: 100%;
    }}
    .action-text {{ color: #B0BEC5; font-size: 15px; margin: 0; }}
    
    /* Botón Guardar Cambios - Estilo Material Primario Limpio */
    .stButton > button {{
        background-color: #1E88E5 !important; /* Azul primario sólido */
        color: #ffffff !important; 
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 24px !important; 
        font-size: 16px !important; 
        font-weight: 500 !important; 
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        box-shadow: 0px 3px 5px rgba(0,0,0,0.4) !important;
        transition: background-color 0.2s, box-shadow 0.2s, transform 0.1s !important;
        display: inline-flex; align-items: center; justify-content: center;
        width: 100%;
        height: 54px; /* Obliga al botón a tener la misma altura que la Action Bar */
    }}
    .stButton > button:hover {{
        background-color: #2196F3 !important; /* Azul un tono más brillante */
        box-shadow: 0px 6px 12px rgba(0,0,0,0.5) !important;
        transform: translateY(-1px) !important;
    }}
    .stButton > button:active {{
        transform: translateY(1px) !important;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.3) !important;
    }}

    [data-testid="stDataFrame"], [data-testid="stMetricWidget"] {{
        background-color: #1E1E1E !important; border-radius: 12px;
        padding: 16px; box-shadow: 0px 4px 6px rgba(0,0,0,0.3); border: 1px solid #333333 !important;
    }}
    [data-testid="stDataFrame"] table {{ font-size: 16px !important; }}
    h1, h2, h3, p {{ color: #E0E0E0 !important; }}
</style>
"""
st.markdown(dark_material_css, unsafe_allow_html=True)

ARCHIVO_DATOS = "datos_gantt_cpm.json"

# --- 2. GESTIÓN DE DATOS ---
datos_base_multi = {
    "Proyecto Principal": {
        "fecha_inicio": (datetime.date.today() - datetime.timedelta(days=10)).strftime("%Y-%m-%d"),
        "tareas": [
            {"ID": 1, "Tarea": "Configuración Inicial", "Dias": 10, "Depende_De": "", "Progreso (%)": 40},
            {"ID": 2, "Tarea": "Desarrollo de Módulos", "Dias": 15, "Depende_De": "1", "Progreso (%)": 0},
        ]
    }
}

def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        try:
            with open(ARCHIVO_DATOS, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for t in data: t.pop("Equipo", None)
                    return {"Proyecto Migrado": {"fecha_inicio": datetime.date.today().strftime("%Y-%m-%d"), "tareas": data}}
                return data
        except:
            pass
    return datos_base_multi.copy()

def guardar_datos(datos):
    with open(ARCHIVO_DATOS, "w") as f:
        json.dump(datos, f, indent=4)

datos_app = cargar_datos()

# --- 3. BARRA LATERAL ---
# Ajustado a 24px para armonizar con el texto 1.25rem
st.sidebar.markdown(f'<div class="sidebar-title">{cargar_icono_local(PATH_COPY, 24)} <span>Proyectos</span></div>', unsafe_allow_html=True)

lista_proyectos = list(datos_app.keys())
proyecto_seleccionado = st.sidebar.selectbox("Seleccionar Espacio", lista_proyectos, label_visibility="collapsed")

with st.sidebar.expander("➕ Nuevo Proyecto"):
    nuevo_nombre = st.text_input("Nombre del proyecto")
    if st.button("Crear Proyecto", key="btn_crear_proj"):
        if nuevo_nombre and nuevo_nombre not in datos_app:
            datos_app[nuevo_nombre] = {"fecha_inicio": datetime.date.today().strftime("%Y-%m-%d"), "tareas": []}
            guardar_datos(datos_app)
            st.rerun()

st.sidebar.divider()
# Ajustado a 24px
st.sidebar.markdown(f'<div class="sidebar-title">{cargar_icono_local(PATH_GEAR, 24)} <span>Configuración</span></div>', unsafe_allow_html=True)
fecha_str_actual = datos_app[proyecto_seleccionado].get("fecha_inicio", datetime.date.today().strftime("%Y-%m-%d"))
fecha_obj_actual = datetime.datetime.strptime(fecha_str_actual, "%Y-%m-%d").date()
nueva_fecha_inicio = st.sidebar.date_input("Inicio de Operaciones", fecha_obj_actual)

st.sidebar.markdown("<br><p style='color: #B0BEC5; font-size: 14px;'>No olvides guardar los cambios globales en la parte superior.</p>", unsafe_allow_html=True)

# --- 4. PREPARACIÓN DE DATOS ---
df = pd.DataFrame(datos_app[proyecto_seleccionado]["tareas"])
if df.empty: df = pd.DataFrame(columns=["ID", "Tarea", "Dias", "Depende_De", "Progreso (%)"])
else: df = df.drop(columns=["Equipo"], errors='ignore')

df["ID"] = pd.to_numeric(df["ID"], errors='coerce')
df["Depende_De"] = df["Depende_De"].astype(str).replace("nan", "")
df["Dias"] = pd.to_numeric(df["Dias"], errors='coerce').fillna(1).astype(int)

# --- 5. ALGORITMO CPM ---
def parse_deps(dep_str):
    if not dep_str.strip(): return []
    try: return [int(d.strip()) for d in str(dep_str).split(",") if d.strip().isdigit()]
    except: return []

tareas_dict = {}
for idx, row in df.dropna(subset=["ID"]).iterrows():
    tareas_dict[row["ID"]] = {
        "id": int(row["ID"]), "dias": row["Dias"], "deps": parse_deps(row["Depende_De"]),
        "es": 0, "ef": 0, "ls": 0, "lf": 0, "holgura": 0, "critica": False
    }

for tid in sorted(tareas_dict.keys()):
    t = tareas_dict[tid]
    t["es"] = 0 if not t["deps"] else max([tareas_dict[dep]["ef"] for dep in t["deps"] if dep in tareas_dict], default=0)
    t["ef"] = t["es"] + t["dias"]

duracion_proyecto = max((t["ef"] for t in tareas_dict.values()), default=0)

for tid in sorted(tareas_dict.keys(), reverse=True):
    t = tareas_dict[tid]
    sucesores = [s for s in tareas_dict.values() if tid in s["deps"]]
    t["lf"] = duracion_proyecto if not sucesores else min([s["ls"] for s in sucesores])
    t["ls"] = t["lf"] - t["dias"]
    t["holgura"] = t["ls"] - t["es"]
    if t["holgura"] == 0: t["critica"] = True

inicios, fines, estados = [], [], []
for idx, row in df.iterrows():
    tid = row["ID"]
    if pd.notna(tid) and tid in tareas_dict:
        t_data = tareas_dict[tid]
        inicios.append(nueva_fecha_inicio + datetime.timedelta(days=t_data["es"]))
        fines.append(nueva_fecha_inicio + datetime.timedelta(days=t_data["ef"]))
        estados.append("Ruta Crítica" if t_data["critica"] else "Tareas No Críticas")
    else:
        inicios.append(nueva_fecha_inicio); fines.append(nueva_fecha_inicio); estados.append("Tareas No Críticas")

df["Inicio"] = inicios; df["Fin"] = fines; df["Estado_Visual"] = estados
if "Progreso (%)" in df.columns: df["Texto_Barra"] = df["Progreso (%)"].astype(str) + "%"

# --- TÍTULO PRINCIPAL ---
st.markdown(f'<h1 class="title-flex">{cargar_icono_local(PATH_CHART, 45)} {proyecto_seleccionado}</h1>', unsafe_allow_html=True)

# --- 6. BARRA DE ACCIÓN GLOBAL ---
col_info, col_btn = st.columns([4, 1]) # Ajusté el ratio para que el botón no sea excesivamente ancho en pantallas grandes

with col_info:
    st.markdown(f"""
    <div class="action-bar">
        <div>
            <p class="action-text"><strong>Inicio:</strong> {nueva_fecha_inicio.strftime('%d/%m/%Y')} &nbsp;&nbsp;|&nbsp;&nbsp; <strong>Duración Estimada:</strong> {duracion_proyecto} días</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_btn:
    # Este botón actúa sobre los cambios pendientes en el editor
    # El CSS obliga al botón a tener la misma altura que la Action Bar para alineación perfecta
    guardar = st.button("Guardar Cambios", key="btn_save_global")

# --- 7. RENDERIZADO DEL GANTT ---
if not df.dropna(subset=["ID"]).empty:
    df_plot = df.dropna(subset=["ID"]).copy()
    
    dark_material_red, dark_material_blue, dark_material_amber = "#EF5350", "#42A5F5", "#FFCA28"
    
    fig = px.timeline(
        df_plot, x_start="Inicio", x_end="Fin", y="Tarea", color="Estado_Visual",
        color_discrete_map={"Ruta Crítica": dark_material_red, "Tareas No Críticas": dark_material_blue}, text="Texto_Barra",
        hover_data={"Estado_Visual": False, "Texto_Barra": False, "Inicio": True, "Fin": True, "Dias": True, "Progreso (%)": True},
        template="plotly_dark"
    )
    
    fig.update_traces(textposition="inside", insidetextanchor="middle", textfont=dict(color="#FFFFFF", size=16, family="Roboto"))
    fig.update_yaxes(autorange="reversed", title="", tickfont=dict(size=16))
    fig.update_xaxes(title="", showgrid=True, gridcolor="#333333", tickfont=dict(size=16))
    
    hoy_ts = pd.Timestamp(datetime.date.today()).timestamp() * 1000
    fig.add_vline(x=hoy_ts, line_width=2, line_dash="dash", line_color=dark_material_amber, annotation_text="Hoy")
    
    fig.update_layout(
        title_text="",
        paper_bgcolor="#1E1E1E", plot_bgcolor="#1E1E1E", margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    leyenda_html = f"""
    <div style="display: flex; justify-content: center; gap: 40px; margin-top: -10px; margin-bottom: 20px; font-size: 16px; color: #E0E0E0;">
        <div style="display: flex; align-items: center; gap: 8px;">
            {cargar_icono_local(PATH_LEGEND_CRITICAL, 22)} <span>Ruta Crítica</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
            {cargar_icono_local(PATH_LEGEND_NORMAL, 22)} <span>Tareas No Críticas</span>
        </div>
    </div>
    """
    st.markdown(leyenda_html, unsafe_allow_html=True)
else:
    st.info("Añade tareas en el panel inferior para visualizar el diagrama.")

st.divider()

# --- 8. EDITOR DE DATOS ---
st.markdown(f'<h3 class="title-flex">{cargar_icono_local(PATH_TASK, 32)} Editor de Tareas</h3>', unsafe_allow_html=True)

df_editado = st.data_editor(
    df[["ID", "Tarea", "Dias", "Depende_De", "Progreso (%)"]],
    num_rows="dynamic",
    column_config={
        "ID": st.column_config.NumberColumn("ID (Automático)", disabled=True),
        "Dias": st.column_config.NumberColumn("Días", min_value=1, step=1),
        "Depende_De": st.column_config.TextColumn("Depende de (IDs)"),
        "Progreso (%)": st.column_config.NumberColumn("Avance %", min_value=0, max_value=100, step=5),
    },
    use_container_width=True,
    key="editor_tareas"
)

# --- 9. LÓGICA DE GUARDADO ---
if guardar:
    df_limpio = df_editado.dropna(subset=["Tarea"]).copy()
    
    if not df_limpio.empty:
        max_id = df_limpio["ID"].max()
        max_id = 0 if pd.isna(max_id) else max_id
        
        nuevos_ids = []
        for index, row in df_limpio.iterrows():
            if pd.isna(row["ID"]):
                max_id += 1
                nuevos_ids.append(max_id)
            else:
                nuevos_ids.append(int(row["ID"]))
        df_limpio["ID"] = nuevos_ids
    
    datos_app[proyecto_seleccionado]["fecha_inicio"] = nueva_fecha_inicio.strftime("%Y-%m-%d")
    datos_app[proyecto_seleccionado]["tareas"] = df_limpio.to_dict("records")
    guardar_datos(datos_app)
    
    st.success("¡Proyecto guardado con éxito!")
    st.rerun()