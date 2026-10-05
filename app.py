import sqlite3

import streamlit as st


# --- 1. CONFIGURACIÓN Y CONEXIÓN A LA BASE DE DATOS ---
def obtener_conexion():
    conn = sqlite3.connect('tareas.db', check_same_thread=False)
    return conn

def crear_tabla():
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # Crear la tabla si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            categoria TEXT DEFAULT 'General',
            prioridad TEXT DEFAULT 'Media',
            completada BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    
    # Asegurar que las columnas existan si provienes de la versión anterior
    cursor.execute("PRAGMA table_info(tareas)")
    columnas = [col[1] for col in cursor.fetchall()]
    if 'categoria' not in columnas:
        cursor.execute("ALTER TABLE tareas ADD COLUMN categoria TEXT DEFAULT 'General'")
    if 'prioridad' not in columnas:
        cursor.execute("ALTER TABLE tareas ADD COLUMN prioridad TEXT DEFAULT 'Media'")
        
    conn.commit()
    conn.close()

crear_tabla()

# --- 2. FUNCIONES DE LA BASE DE DATOS (CRUD) ---
def agregar_tarea(titulo, categoria, prioridad):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO tareas (titulo, categoria, prioridad, completada) VALUES (?, ?, ?, 0)',
        (titulo, categoria, prioridad)
    )
    conn.commit()
    conn.close()

def obtener_tareas(filtro_estado="Todas", filtro_categoria="Todas"):
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    query = 'SELECT id, titulo, categoria, prioridad, completada FROM tareas WHERE 1=1'
    parametros = []
    
    if filtro_estado == "Pendientes":
        query += ' AND completada = 0'
    elif filtro_estado == "Completadas":
        query += ' AND completada = 1'
        
    if filtro_categoria != "Todas":
        query += ' AND categoria = ?'
        parametros.append(filtro_categoria)
        
    cursor.execute(query, parametros)
    filas = cursor.fetchall()
    conn.close()
    return filas

def cambiar_estado_tarea(tarea_id, estado_actual):
    conn = obtener_conexion()
    cursor = conn.cursor()
    nuevo_estado = 0 if estado_actual else 1
    cursor.execute('UPDATE tareas SET completada = ? WHERE id = ?', (nuevo_estado, tarea_id))
    conn.commit()
    conn.close()

def eliminar_tarea(tarea_id):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tareas WHERE id = ?', (tarea_id,))
    conn.commit()
    conn.close()

# --- 3. INTERFAZ DE USUARIO EN STREAMLIT ---
st.set_page_config(page_title="Gestor de Tareas SQLite Pro", page_icon="📝", layout="centered")

st.title("📝 Gestor de Tareas Avanzado")
st.write("Aplicación con categorías, prioridades y filtros usando **Streamlit** y **SQLite**.")

st.divider()

# Formulario para agregar una nueva tarea
st.subheader("➕ Agregar nueva tarea")
with st.form("form_agregar", clear_on_submit=True):
    nueva_tarea = st.text_input("Descripción de la tarea:")
    col_cat, col_prio = st.columns(2)
    categoria = col_cat.selectbox("Categoría:", ["General", "Trabajo", "Personal", "Estudios", "Hogar"])
    prioridad = col_prio.selectbox("Prioridad:", ["Alta 🔴", "Media 🟡", "Baja 🟢"])
    
    btn_agregar = st.form_submit_button("Agregar Tarea")
    
    if btn_agregar and nueva_tarea.strip() != "":
        agregar_tarea(nueva_tarea.strip(), categoria, prioridad)
        st.success(f"Tarea '{nueva_tarea}' agregada exitosamente.")
        st.rerun()

st.divider()
with open("tareas.db", "rb") as fp:
    st.download_button("Descargar tareas.db", fp, file_name="tareas.db")
    
# --- BARRA LATERAL / SECCIÓN DE FILTROS ---
st.sidebar.header("🔍 Filtros de Tareas")
filtro_estado = st.sidebar.radio("Filtrar por estado:", ["Todas", "Pendientes", "Completadas"])
filtro_categoria = st.sidebar.selectbox("Filtrar por categoría:", ["Todas", "General", "Trabajo", "Personal", "Estudios", "Hogar"])

# Mostrar lista de tareas filtradas
st.subheader(f"📋 Lista de Tareas ({filtro_estado})")

lista_tareas = obtener_tareas(filtro_estado, filtro_categoria)

if not lista_tareas:
    st.info("No se encontraron tareas con los filtros seleccionados.")
else:
    for tarea_id, titulo, cat, prio, completada in lista_tareas:
        col_check, col_texto, col_cat, col_prio, col_del = st.columns([0.08, 0.42, 0.2, 0.2, 0.1])
        
        # Checkbox para cambiar el estado
        estado_check = col_check.checkbox("", value=bool(completada), key=f"check_{tarea_id}")
        if estado_check != bool(completada):
            cambiar_estado_tarea(tarea_id, completada)
            st.rerun()
            
        # Título de la tarea
        if completada:
            col_texto.markdown(f"~~{titulo}~~")
        else:
            col_texto.write(titulo)
            
        # Categoría y Prioridad
        col_cat.caption(f"📁 {cat}")
        col_prio.caption(f"{prio}")
            
        # Botón para eliminar
        if col_del.button("🗑️", key=f"del_{tarea_id}"):
            eliminar_tarea(tarea_id)
            st.rerun()
