import pandas as pd
import sqlite3
import streamlit as st
import plotly.express as px

# --- Configuración del Dashboard ---
st.set_page_config(page_title="Dashboard de Eventos", layout="wide")
st.title("Dashboard de Eventos de Sistema")
st.markdown("## Visualización interactiva de los eventos registrados")

# --- Cargador de Archivo ---
uploaded_file = st.file_uploader("Seleccione el archivo CSV de Eventos", type=["csv"])

if uploaded_file is not None:
    try:
        # Leer y limpiar los datos
        data = pd.read_csv(
            uploaded_file,
            encoding='latin1',
            skiprows=5,  # Saltar las líneas iniciales no relevantes
            names=["Timestamp", "Evento"]
        )
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.stop()

    # Filtrar filas que tengan un formato de fecha en 'Timestamp'
    data = data[data["Marca de tiempo"].str.contains(r"\d{2}-\d{2}-\d{4}", na=False)]
    data.reset_index(drop=True, inplace=True)

    # Convertir la columna Timestamp a formato datetime
    data["Marca de tiempo"] = pd.to_datetime(data["Marca de tiempo"])

    # Separar la columna "Evento" en "Evento" y "Usuario"
    # Se extrae el usuario a partir de la parte final que contiene 'Por ...'
    data["Usuario"] = data["Evento"].str.extract(r'Por (.+)$')
    # Se extrae la descripción del evento, que es la parte antes del " -"
    data["Evento"] = data["Evento"].str.extract(r"^(.*?) -")

    # --- Filtro: Conservar solo registros con un usuario registrado ---
    data = data[
        data["Usuario"].notna() &
        (data["Usuario"].str.strip() != "") &
        (data["Usuario"].str.lower() != "none")
    ]

    # Guardar en SQLite
    conn = sqlite3.connect("EventHistory.db")
    data.to_sql("Eventos", conn, if_exists="replace", index=False)

    # Consulta para los usuarios con más eventos
    query_usuarios = """
    SELECT Usuario, COUNT(*) as Frecuencia
    FROM Eventos
    GROUP BY Usuario
    ORDER BY Frecuencia DESC
    """
    result_usuarios = pd.read_sql_query(query_usuarios, conn)

    # Métricas generales
    total_eventos = len(data)
    eventos_unicos = data["Evento"].dropna().unique()
    usuarios_unicos = data["Usuario"].dropna().unique()

    # Cerrar conexión SQLite
    conn.close()

    # --- Visualización de Métricas ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Eventos", total_eventos)
    col2.metric("Tipos de Eventos Únicos", len(eventos_unicos))
    col3.metric("Usuarios Únicos", len(usuarios_unicos))

    # --- Tablas de Eventos y Usuarios ---
    st.subheader("Eventos Únicos")
    st.dataframe(pd.DataFrame(eventos_unicos, columns=["Eventos Únicos"]), use_container_width=True)

    st.subheader("Usuarios Únicos")
    st.dataframe(pd.DataFrame(usuarios_unicos, columns=["Usuarios Únicos"]), use_container_width=True)

    # --- Selector de Rango de Fechas ---
    st.subheader("Filtrar por Rango de Fechas")
    start_date, end_date = st.date_input(
        "Seleccione el rango de fechas:",
        [data["Timestamp"].min().date(), data["Timestamp"].max().date()],
        key="date_range_selector"
    )
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Filtrar los datos por rango de fechas
    filtered_data = data[(data["Marca de tiempo"] >= start_date) & (data["Marca de tiempo"] <= end_date)]

    st.subheader("Lista Completa de Eventos Filtrados")
    st.dataframe(filtered_data, use_container_width=True)

    # --- Gráfico de Pastel para Usuarios con Más Eventos ---
    st.subheader("Usuarios con Más Eventos")
    fig_pie_usuarios = px.pie(result_usuarios, names="Usuario", values="Frecuencia", title="Usuarios con Más Eventos")
    st.plotly_chart(fig_pie_usuarios, use_container_width=True)

    # --- Histograma de Eventos por Hora ---
    st.subheader("Distribución de Eventos por Hora del Día")
    filtered_data["Hora"] = filtered_data["Marca de tiempo"].dt.hour

    fig_histogram = px.histogram(
        filtered_data,
        x="Hora",
        nbins=24,
        title="Histograma de Eventos por Hora del Día",
        labels={"Hora": "Hora del Día", "count": "Cantidad de Eventos"}
    )
    st.plotly_chart(fig_histogram, use_container_width=True)
else:
    st.info("Cargue un archivo CSV para comenzar el análisis.")

