import pandas as pd
import sqlite3
import streamlit as st
import plotly.express as px

# Ruta del archivo
#file_path = r"\\servernas\Validaciones-Metrología\COORVSC-CALIFICACIONES\CALIFICACIONES\EQUIPOS\Secador de Lecho Fluido Glatt 600 kg N°4\calificación 2024\VSC\EventHistory.csv"

# Leer y limpiar los datos
data = pd.read_csv(
    "EventHistory1.csv",
    encoding='latin1',
    skiprows=5,  # Saltar las líneas iniciales no relevantes 
    names=["Timestamp", "Evento" ]
)

data = data[data["Timestamp"].str.contains(r"\d{2}-\d{2}-\d{4}", na=False)]
data.reset_index(drop=True, inplace=True)

# Convertir la columna Timestamp a formato datetime
data["Timestamp"] = pd.to_datetime(data["Timestamp"])

# Separar la columna "Evento" en "Evento" y "Usuario"
data["Usuario"] = data["Evento"].str.extract(r'Por (.+)$')
data["Evento"] = data["Evento"].str.extract(r"^(.*?) -")

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

# Consulta para el total de eventos
total_eventos = len(data)

# Eventos y usuarios únicos
eventos_unicos = data["Evento"].dropna().unique()
usuarios_unicos = data["Usuario"].dropna().unique()

# Cerrar conexión SQLite
conn.close()

# --- Configuración del Dashboard ---
st.set_page_config(page_title="Dashboard de Eventos", layout="wide")

# --- Encabezado ---
st.title("Dashboard de Eventos de Sistema")
st.markdown("## Visualización interactiva de los eventos registrados")

# --- Métricas ---
col1, col2, col3 = st.columns(3)
col1.metric("Total de Eventos", total_eventos)
col2.metric("Tipos de Eventos Únicos", len(eventos_unicos))
col3.metric("Usuarios Únicos", len(usuarios_unicos))

# --- Tabla de Eventos Únicos ---
st.subheader("Eventos Únicos")
st.dataframe(pd.DataFrame(eventos_unicos, columns=["Eventos Únicos"]), use_container_width=True)

# --- Tabla de Usuarios Únicos ---
st.subheader("Usuarios Únicos")
st.dataframe(pd.DataFrame(usuarios_unicos, columns=["Usuarios Únicos"]), use_container_width=True)

# --- Selector de rango de fechas ---
st.subheader("Filtrar por Rango de Fechas")
start_date, end_date = st.date_input(
    "Seleccione el rango de fechas:", 
    [data["Timestamp"].min().date(), data["Timestamp"].max().date()],
    key="date_range_selector"  # Clave única para el widget
)
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Filtrar los datos por rango de fechas
filtered_data = data[(data["Timestamp"] >= start_date) & (data["Timestamp"] <= end_date)]

# Mostrar los datos filtrados (todos los eventos)
st.subheader("Lista Completa de Eventos Filtrados")
st.dataframe(filtered_data, use_container_width=True)

# --- Gráfico de Pastel para Usuarios con Más Alarmas ---
st.subheader("Usuarios con Más Alarmas")
fig_pie_usuarios = px.pie(result_usuarios, names="Usuario", values="Frecuencia", title="Usuarios con Más Alarmas")
st.plotly_chart(fig_pie_usuarios, use_container_width=True)

# --- Histograma de Eventos por Hora ---
st.subheader("Distribución de Eventos por Hora del Día")
filtered_data["Hora"] = filtered_data["Timestamp"].dt.hour

fig_histogram = px.histogram(filtered_data, x="Hora", nbins=24, title="Histograma de Eventos por Hora del Día",
                             labels={"Hora": "Hora del Día", "count": "Cantidad de Eventos"})
st.plotly_chart(fig_histogram, use_container_width=True)
