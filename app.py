    
import psycopg2  # type: ignore
import streamlit as st


# --- 1. CONFIGURACIÓN Y CONEXIÓN A LA BASE DE DATOS ---
def obtener_conexion():
    conn = psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        port=st.secrets["postgres"]["port"],
        dbname=st.secrets["postgres"]["dbname"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"]
    )
    return conn

def crear_tabla():
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # Crear la tabla si no existe en PostgreSQL
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id SERIAL PRIMARY KEY,
            titulo TEXT NOT NULL,
            categoria TEXT DEFAULT 'General',
            prioridad TEXT DEFAULT 'Media',
            completada BOOLEAN NOT NULL DEFAULT FALSE
        )
    ''')
        
    conn.commit()
    cursor.close()
    conn.close()

crear_tabla()

# --- 2. FUNCIONES DE LA BASE DE DATOS (CRUD) ---
def agregar_tarea(titulo, categoria, prioridad):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO tareas (titulo, categoria, prioridad, completada) VALUES (%s, %s, %s, FALSE)',
        (titulo, categoria, prioridad)
    )
    conn.commit()
    cursor.close()
    conn.close()

def obtener_tareas(filtro_estado="Todas", filtro_categoria="Todas"):
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    query = 'SELECT id, titulo, categoria, prioridad, completada FROM tareas WHERE 1=1'
    parametros = []
    
    if filtro_estado == "Pendientes":
        query += ' AND completada = FALSE'
    elif filtro_estado == "Completadas":
        query += ' AND completada = TRUE'
        
    if filtro_categoria != "Todas":
        query += ' AND categoria = %s'
        parametros.append(filtro_categoria)
        
    query += ' ORDER BY id DESC'
    
    cursor.execute(query, parametros)
    filas = cursor.fetchall()
    cursor.close()
    conn.close()
    return filas

def cambiar_estado_tarea(tarea_id, estado_actual):
    conn = obtener_conexion()
    cursor = conn.cursor()
    nuevo_estado = not estado_actual
    cursor.execute('UPDATE tareas SET completada = %s WHERE id = %s', (nuevo_estado, tarea_id))
    conn.commit()
    cursor.close()
    conn.close()

def eliminar_tarea(tarea_id):
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tareas WHERE id = %s', (tarea_id,))
    conn.commit()
    cursor.close()
    conn.close()

# --- 3. INTERFAZ DE USUARIO EN STREAMLIT ---
st.set_page_config(page_title="Gestor de Tareas Cloud", page_icon="📝", layout="centered")

st.title("📝 Gestor de Tareas Avanzado")
st.write("Aplicación sincronizada en tiempo real usando **Streamlit** y **Supabase (PostgreSQL)**.")

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