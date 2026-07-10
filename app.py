import streamlit as st
import pandas as pd
import graphviz
import os

archivo_nodos = "Nodos_Almacen.csv"
archivo_aristas = "Aristas_Almacen.csv"

from dataset_loader import crear_lista_adyacencia
from graph_engine import procesar_pedido_por_zonas
# Prevenimos que Streamlit colapse si los archivos no están
if not os.path.exists(archivo_nodos) or not os.path.exists(archivo_aristas):
    st.error("⚠️ No se encontraron los archivos CSV. Asegúrate de que estén en la misma carpeta que este script.")
    st.stop()

Adyacencia = crear_lista_adyacencia(archivo_aristas)
df_nodos_interfaz = pd.read_csv(archivo_nodos)

# Generar lista de ubicaciones de inicio (Solo los node_ids, ej: NAV_0_0)
lista_ubicaciones_inicio = df_nodos_interfaz['node_id'].unique().tolist()

# Generar lista de pedidos (node_id + sector, ej: RACK_62_20_H)
def formatear_pedido_para_ui(row):
    sector = str(row['sector']) if 'sector' in row and pd.notna(row['sector']) else ""
    if sector and sector.strip() != "":
        return f"{row['node_id']}_{sector}"
    return str(row['node_id'])

# Filtramos preferentemente los racks para la lista de pedidos
df_solo_racks = df_nodos_interfaz[df_nodos_interfaz['type'] == 'rack']
lista_pedidos_disponibles = df_solo_racks.apply(formatear_pedido_para_ui, axis=1).unique().tolist()




def generar_mapa_graphviz_coordenadasa(la, ruta_nodos_csv, ruta_optima=[]):
    
    dot = graphviz.Graph(engine='neato')
    
 

    dot.attr(dpi='70', splines='false')
    
    aristas_ruta = set()
    nodos_en_ruta = set(ruta_optima)
    
    if ruta_optima:
        for i in range(len(ruta_optima) - 1):
            origen = str(ruta_optima[i])
            destino = str(ruta_optima[i+1])
            aristas_ruta.add((origen, destino))
            aristas_ruta.add((destino, origen))

    df_nodos = pd.read_csv(ruta_nodos_csv)
    for _, row in df_nodos.iterrows():
        nodo_id = str(row['node_id'])
        tipo = row['type']
       
        
      
        x = float(row['x']) / 5.0
        y = float(row['y']) / 5.0
        
        if nodo_id in nodos_en_ruta:
            if ruta_optima and nodo_id == str(ruta_optima[0]): color = 'green'  
            elif ruta_optima and nodo_id == str(ruta_optima[-1]): color = 'red'    
            else: color = 'yellow' 
        else:
            color = 'lightblue' if tipo == 'interseccion' else 'lightgrey' if tipo == 'punto_pasillo' else 'orange'
        
        forma = 'box' if tipo == 'rack' else 'circle'
        # Etiqueta vacía ('') o pequeña para no saturar el plano base
        etiqueta = "" 
        
        
        dot.node(nodo_id, label=etiqueta, pos=f"{x},{y}!", style='filled', fillcolor=color, shape=forma, width='0.3', height='0.3')

    aristasVisitadas = set()
    for nodo, vecinos in la.items():
        for v, distancia in vecinos:
            if (nodo, v) not in aristasVisitadas and (v, nodo) not in aristasVisitadas:
                if (str(nodo), str(v)) in aristas_ruta:
                    # Línea roja de la ruta
                    dot.edge(str(nodo), str(v), color='red', penwidth='3')
                else:
                    # Línea base del almacén, más delgada
                    dot.edge(str(nodo), str(v), color='gray60', penwidth='0.5')
                aristasVisitadas.add((nodo, v))
    
    return dot





st.set_page_config(page_title="Optimizador de Rutas Logísticas", layout="wide")
st.title("📦 Sistema de Enrutamiento - Order Picking")

with st.sidebar:
    st.header("⚙️ Configuración de la Ruta")
    
    #Input para la ubicación inicial
    default_index = lista_ubicaciones_inicio.index("NAV_0_0") if "NAV_0_0" in lista_ubicaciones_inicio else 0
    punto_inicio_operador = st.selectbox(
        "📍 Ubicación inicial del operador:",
        options=lista_ubicaciones_inicio,
        index=default_index
    )

    st.markdown("---")
    
    archivo_csv = st.file_uploader("📂 Insertar CSV Lista de pedidos", type=["csv"])
   
    
    #lista generada desde el CSV de nodos con sectores
    nodos_seleccionados = st.multiselect(
        "👆 Lista de pedidos (Manual):",
        options=lista_pedidos_disponibles,
        help="Elige los racks objetivo (incluyen la zona)."
    )
    
    calcular = st.button("🚀 Comenzar ruta", use_container_width=True)

# Procesamiento de la lista de pedidos
lista_pedido = []
if archivo_csv is not None:
    df_pedido = pd.read_csv(archivo_csv)
    if 'ubicacion' in df_pedido.columns:
        lista_pedido.extend(df_pedido['ubicacion'].tolist())
    else:
        st.sidebar.error("El CSV debe tener una columna llamada 'ubicacion'.")

if nodos_seleccionados:
    lista_pedido.extend(nodos_seleccionados)

lista_pedido = list(set(lista_pedido))


# RENDERIZADO DEL RESULTADO
col1, col2 = st.columns([2, 1])

if calcular:
    if not lista_pedido:
        st.warning("⚠️ Por favor, ingresa al menos un pedido de destino.")
        try:
            mapa_vacio = generar_mapa_graphviz_coordenadasa(Adyacencia, archivo_nodos)
            st.graphviz_chart(mapa_vacio, use_container_width=True)
        except Exception as e:
            st.error(f"Error al renderizar el grafo: {e}")
    else:
        # Usa el punto de inicio seleccionado en la UI
        distancia_total, ruta = procesar_pedido_por_zonas(Adyacencia, punto_inicio_operador, lista_pedido)
        
        with col1:
            st.subheader("🗺️ Mapa de Ruta del Operario")
            try:
                mapa_renderizado = generar_mapa_graphviz_coordenadasa(Adyacencia, archivo_nodos, ruta)
                st.graphviz_chart(mapa_renderizado, use_container_width=True)
                st.info("💡 Tip: Pasa el cursor sobre el gráfico y usa el botón de la esquina superior derecha para expandir el grafico.")
            except Exception as e:
                st.error(f"El motor de Graphviz falló. Asegúrate de tener Graphviz instalado en tu sistema operativo. Detalle: {e}")
            
        with col2:
            st.subheader("📋 Resumen de la Operación")
            st.metric(label="Distancia Total Recorrida", value=f"{distancia_total} metros")
            
            st.write("**Secuencia de Nodos Visitados:**")
            with st.expander("Ver lista de pasos", expanded=True):
                with st.container(height=350):
                 for idx, paso in enumerate(ruta):
                    if idx == 0:
                        st.write(f"🟢 **Inicio:** {paso}")
                    elif idx == len(ruta) - 1:
                        st.write(f"🔴 **Fin:** {paso}")
                    else:
                        st.write(f"➡️ {paso}")
else:
    with col1:
        st.subheader("🗺️ Mapa del Almacén")
        try:
            mapa_inicial = generar_mapa_graphviz_coordenadasa(Adyacencia, archivo_nodos)
            st.graphviz_chart(mapa_inicial, use_container_width=True)
        except Exception as e:
            st.error(f"⚠️ Error visualizando el grafo: {e}. \n\n**Nota:** Para que el atributo de coordenadas (neato) funcione en Streamlit, debes tener el ejecutable de Graphviz instalado en tu sistema operativo y agregado a las variables de entorno (PATH).")
