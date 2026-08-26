import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import json
import os

# --- 0. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gantt Studio", page_icon="📊", layout="wide")

# --- 1. CONFIGURACIÓN CSS Y MATERIAL DESIGN ICONS ---
dark_material_css = f"""
<style>
    /* Importar fuente Roboto y Google Material Symbols (Rounded & Filled) */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,1,0');
    
    html, body, [class*="css"], .stMarkdown p, label, .stSelectbox {{ 
        font-family: 'Roboto', sans-serif; 
        font-size: 17px !important; 
    }}
    .stApp {{ background-color: #121212; }}
    
    /* Clase base para los íconos Material */
    .mat-icon {{
        font-family: 'Material Symbols Rounded';
        font-weight: normal;
        font-style: normal;
        line-height: 1;
        letter-spacing: normal;
        text-transform: none;
        display: inline-block;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
        -webkit-font-smoothing: antialiased;
        vertical-align: middle;
    }}
    
    .title-flex {{ display: flex; align-items: center; gap: 12px; margin-bottom: 0.5rem; color: #FFFFFF; font-weight: 500; }}
    .sidebar-title {{ display: flex; align-items: center; gap: 12px; font-size: 1.25rem; margin-top: 1rem; margin-bottom: 0.5rem; color: #FFFFFF; }}
    
    .action-bar {{
        display: flex; align-items: center; justify-content: space-between;
        background-color: #1E1E1E; padding: 16px 24px; border-radius: 12px;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.3); border: 1px solid #333333; margin-bottom: 24px;
    }}
    .action-text {{ color: #B0BEC5; font-size: 15px; margin: 0; }}
    .stExpander {{ background-color: #1E1E1E !important; border: 1px solid #333333 !important; border-radius: 8px !important; }}
    h1, h2, h3, p {{ color: #E0E0E0 !important; }}
    [data-testid="stTabs"] button {{ font-size: 18px !important; padding-bottom: 10px !important; }}
    
    /* Colores de identidad visual */
    .icon-primary {{ color: #AB47BC; }} /* Púrpura Material */
    .icon-critical {{ color: #EF5350; }} /* Rojo Material */
    .icon-normal {{ color: #42A5F5; }} /* Azul Material */
</style>
"""
st.markdown(dark_material_css, unsafe_allow_html=True)

ARCHIVO_DATOS = "datos_gantt_cpm.json"

# --- 2. GESTIÓN DE DATOS (SOLO LECTURA) ---
def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"Proyecto Vacío": {"fecha_inicio": datetime.date.today().strftime("%Y-%m-%d"), "tareas": []}}

datos_app = cargar_datos()

# --- 3. BARRA LATERAL ---
st.sidebar.markdown(f'<div class="sidebar-title"><span class="mat-icon icon-primary" style="font-size: 28px;">folder_copy</span> <span>Proyectos</span></div>', unsafe_allow_html=True)
lista_proyectos = list(datos_app.keys())
proyecto_seleccionado = st.sidebar.selectbox("Seleccionar Espacio", lista_proyectos, label_visibility="collapsed")

st.sidebar.markdown("""
    <br><hr><br>
    <p style='color: #B0BEC5; font-size: 14px;'>
        <i>Nota: Este panel funciona en modo visualizador. Edita el archivo JSON en tu editor de código para actualizar el Gantt y los detalles.</i>
    </p>
""", unsafe_allow_html=True)

# --- 4. PREPARACIÓN DE DATOS ---
df = pd.DataFrame(datos_app[proyecto_seleccionado]["tareas"])

if not df.empty:
    df["ID"] = pd.to_numeric(df["ID"], errors='coerce')
    df["Depende_De"] = df["Depende_De"].astype(str).replace("nan", "")
    df["Fecha_Inicio"] = pd.to_datetime(df["Fecha_Inicio"], errors='coerce')
    df["Fecha_Fin"] = pd.to_datetime(df["Fecha_Fin"], errors='coerce')
    
    df["Dias"] = (df["Fecha_Fin"] - df["Fecha_Inicio"]).dt.days + 1
    df["Dias"] = df["Dias"].fillna(0).astype(int)
    
    if "Progreso (%)" in df.columns: 
        df["Texto_Barra"] = df["Progreso (%)"].astype(str) + "%"
    
    df["Desc_Corta"] = df.get("Descripcion", "").apply(lambda x: (str(x)[:60] + '...') if len(str(x)) > 60 else str(x))

    proj_start = df["Fecha_Inicio"].min()
    proj_end = df["Fecha_Fin"].max()
    duracion_proyecto = (proj_end - proj_start).days + 1 if pd.notnull(proj_start) and pd.notnull(proj_end) else 0
    fecha_mostrar = proj_start if pd.notnull(proj_start) else datetime.date.today()

    # --- 5. ALGORITMO CPM PARA RUTA CRÍTICA ---
    def parse_deps(dep_str):
        if pd.isna(dep_str) or not str(dep_str).strip(): return []
        try: return [int(float(d.strip())) for d in str(dep_str).split(",") if d.strip().isdigit()]
        except: return []

    tareas_dict = {}
    for idx, row in df.dropna(subset=["ID"]).iterrows():
        tareas_dict[row["ID"]] = {
            "id": int(row["ID"]), 
            "dias": max(1, int(row["Dias"])), 
            "deps": parse_deps(row["Depende_De"]),
            "es": 0, "ef": 0, "ls": 0, "lf": 0, "holgura": 0, "critica": False
        }

    for tid in sorted(tareas_dict.keys()):
        t = tareas_dict[tid]
        valid_deps = [dep for dep in t["deps"] if dep in tareas_dict]
        t["es"] = 0 if not valid_deps else max([tareas_dict[dep]["ef"] for dep in valid_deps], default=0)
        t["ef"] = t["es"] + t["dias"]

    duracion_logica = max((t["ef"] for t in tareas_dict.values()), default=0)

    for tid in sorted(tareas_dict.keys(), reverse=True):
        t = tareas_dict[tid]
        sucesores = [s for s in tareas_dict.values() if tid in s["deps"]]
        t["lf"] = duracion_logica if not sucesores else min([s["ls"] for s in sucesores], default=duracion_logica)
        t["ls"] = t["lf"] - t["dias"]
        t["holgura"] = t["ls"] - t["es"]
        if t["holgura"] <= 0: t["critica"] = True

    estados = []
    for idx, row in df.iterrows():
        tid = row["ID"]
        if pd.notna(tid) and tid in tareas_dict:
            estados.append("Ruta Crítica" if tareas_dict[tid]["critica"] else "Tareas Programadas")
        else:
            estados.append("Tareas Programadas")
            
    df["Estado_Visual"] = estados

else:
    duracion_proyecto = 0
    fecha_mostrar = datetime.date.today()

# --- TÍTULO PRINCIPAL ---
st.markdown(f'<h1 class="title-flex"><span class="mat-icon icon-primary" style="font-size: 45px;">monitoring</span> {proyecto_seleccionado}</h1>', unsafe_allow_html=True)

# --- 6. BARRA DE ACCIÓN GLOBAL ---
st.markdown(f"""
<div class="action-bar">
    <p class="action-text"><strong>Inicio:</strong> {fecha_mostrar.strftime('%d/%m/%Y')} &nbsp;&nbsp;|&nbsp;&nbsp; <strong>Duración Total:</strong> {duracion_proyecto} días</p>
</div>
""", unsafe_allow_html=True)

# --- 7. RENDERIZADO DEL GANTT Y MAPA DE DEPENDENCIAS ---
if not df.empty:
    df_plot = df.dropna(subset=["ID", "Fecha_Inicio", "Fecha_Fin"]).copy()

    if not df_plot.empty:
        dark_material_red = "#EF5350"
        dark_material_blue = "#42A5F5"
        dark_material_amber = "#FFCA28"
        
        id_to_name = dict(zip(df_plot['ID'], df_plot['Tarea']))
        
        def obtener_nombres_dependencias(dep_str):
            deps = parse_deps(dep_str) 
            if not deps: return "Ninguna"
            nombres = [id_to_name.get(d, f"ID {d}") for d in deps]
            return " | ".join(nombres)
            
        df_plot["Depende_De_Nombres"] = df_plot["Depende_De"].apply(obtener_nombres_dependencias)
        
        # PESTAÑAS (Usando emojis formales alineados al estilo Material)
        tab_gantt, tab_red = st.tabs(["📊 Diagrama de Gantt", "🔗 Mapa de Dependencias"])
        
        with tab_gantt:
            fig = px.timeline(
                df_plot, x_start="Fecha_Inicio", x_end="Fecha_Fin", y="Tarea", color="Estado_Visual",
                color_discrete_map={"Ruta Crítica": dark_material_red, "Tareas Programadas": dark_material_blue}, 
                text="Texto_Barra",
                hover_data={
                    "Estado_Visual": False, 
                    "Texto_Barra": False, 
                    "Desc_Corta": True, 
                    "Fecha_Inicio": True, 
                    "Fecha_Fin": True, 
                    "Dias": True, 
                    "Depende_De_Nombres": True, 
                    "Progreso (%)": False
                },
                labels={
                    "Desc_Corta": "Descripción",
                    "Depende_De_Nombres": "Depende de",
                    "Fecha_Inicio": "Inicio",
                    "Fecha_Fin": "Fin"
                },
                template="plotly_dark"
            )
            
            fig.update_traces(textposition="inside", insidetextanchor="middle", textfont=dict(color="#FFFFFF", size=16, family="Roboto"))
            fig.update_yaxes(autorange="reversed", title="", tickfont=dict(size=16))
            fig.update_xaxes(title="", showgrid=True, gridcolor="#333333", tickfont=dict(size=16))
            
            hoy_ts = pd.Timestamp(datetime.date.today()).timestamp() * 1000
            fig.add_vline(x=hoy_ts, line_width=2, line_dash="dash", line_color=dark_material_amber, annotation_text="Hoy")

            fig.update_layout(
                title_text="", paper_bgcolor="#1E1E1E", plot_bgcolor="#1E1E1E", 
                margin=dict(l=20, r=20, t=20, b=20), showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Leyenda con iconos Material Circle
            leyenda_html = f"""
            <div style="display: flex; justify-content: center; gap: 40px; margin-top: -10px; margin-bottom: 20px; font-size: 16px; color: #E0E0E0;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="mat-icon icon-critical" style="font-size: 20px;">circle</span> <span>Ruta Crítica</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="mat-icon icon-normal" style="font-size: 20px;">circle</span> <span>Tareas Programadas</span>
                </div>
            </div>
            """
            st.markdown(leyenda_html, unsafe_allow_html=True)
            
        with tab_red:
            try:
                import graphviz
                dot = graphviz.Digraph(engine='dot')
                dot.attr(bgcolor='#1E1E1E', rankdir='LR') 
                dot.attr('node', shape='rect', style='filled, rounded', fontname='Roboto', fontcolor='white', color='#333333')
                dot.attr('edge', color='#78909C', arrowsize='0.8')
                
                for tid, t_data in tareas_dict.items():
                    nombre_tarea = id_to_name.get(tid, str(tid))
                    if len(nombre_tarea) > 25:
                        palabras = nombre_tarea.split()
                        mitad = len(palabras) // 2
                        nombre_tarea = " ".join(palabras[:mitad]) + "\\n" + " ".join(palabras[mitad:])
                        
                    color_fondo = dark_material_red if t_data["critica"] else dark_material_blue
                    dot.node(str(tid), label=f"[{tid}] {nombre_tarea}", fillcolor=color_fondo)
                    
                for tid, t_data in tareas_dict.items():
                    for dep in t_data["deps"]:
                        if dep in tareas_dict:
                            dot.edge(str(dep), str(tid))
                
                st.graphviz_chart(dot, use_container_width=True)
                st.markdown("<p style='text-align: center; color: #B0BEC5; font-size: 14px;'>Este mapa muestra el flujo lógico. Las tareas en rojo son los 'cuellos de botella' que bloquean el tiempo total del proyecto.</p>", unsafe_allow_html=True)
            
            except ImportError:
                st.warning("Para ver el mapa de dependencias, necesitas instalar Graphviz. Ejecuta: `pip install graphviz`")
else:
    st.info("No hay tareas válidas configuradas en el JSON.")

st.divider()

# --- 8. DETALLES DE TAREAS (VISOR SMART) ---
st.markdown(f'<h3 class="title-flex"><span class="mat-icon icon-primary" style="font-size: 32px;">task_alt</span> Detalles de Tareas</h3>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

if not df.empty:
    for index, row in df.iterrows():
        f_inicio = row["Fecha_Inicio"].strftime("%d %b") if pd.notnull(row["Fecha_Inicio"]) else "Sin fecha"
        f_fin = row["Fecha_Fin"].strftime("%d %b %Y") if pd.notnull(row["Fecha_Fin"]) else "Sin fecha"
        
        # Emojis formales alineados a los colores de Material Design de la app
        indicador = "🔴" if row["Estado_Visual"] == "Ruta Crítica" else "🔵"
        titulo_expander = f"{indicador} {row['Tarea']} &nbsp; | &nbsp; ⏳ {f_inicio} - {f_fin} ({row['Dias']} días)"
        
        with st.expander(titulo_expander, expanded=False):
            st.markdown(f"""
            <div style="padding: 10px; color: #E0E0E0;">
                <p style="font-size: 1.1rem; line-height: 1.6;">
                    {row.get('Descripcion', 'No hay descripción detallada configurada para esta tarea.')}
                </p>
                <p style="font-size: 0.9rem; color: #9E9E9E; margin-top: 10px;">
                    <strong>Dependencias:</strong> {row.get('Depende_De_Nombres', 'Ninguna') if str(row.get('Depende_De_Nombres', '')).strip() != '' else 'Ninguna'} 
                    | <strong>Estado:</strong> {row['Estado_Visual']}
                </p>
            </div>
            """, unsafe_allow_html=True)