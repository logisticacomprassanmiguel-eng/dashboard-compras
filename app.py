import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Compras y Logística", 
    page_icon="📊", 
    layout="wide"
)

# Estilos visuales
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: bold; color: #1E3A8A; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Tablero de Control - Gestión de Compras")

# --- PASO DE ENLACE DE GOOGLE SHEETS ---
# Pega aquí el enlace CSV obtenido en el PASO 1:

# --- PASO DE ENLACE DE GOOGLE SHEETS ---
URL_SHEET = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRZt9DDcAyGzkPpIipOwJX7jXkJfrK5NYbxXIZDQA4p2hw6H8I07yxVMt1nu6Ib5SGCLJ7fWwC7vtI3/pub?gid=284841416&single=true&output=csv"

@st.cache_data(ttl=300)
def cargar_datos(url):
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        
        # Limpieza de datos
        if 'Monto' in df.columns:
            df['Monto'] = pd.to_numeric(df['Monto'].astype(str).str.replace(',', '').str.replace('S/', '').str.replace('$', ''), errors='coerce')
        if 'Lead Time' in df.columns:
            df['Lead Time'] = pd.to_numeric(df['Lead Time'], errors='coerce')
        
        # Fechas
        for col_fecha in ['FECHA DE emisión', 'Entrega Real', 'Fecha estimada', 'FECHA DE COTIZACIÓN']:
            if col_fecha in df.columns:
                df[col_fecha] = pd.to_datetime(df[col_fecha], dayfirst=True, errors='coerce')
                
        return df
    except Exception as e:
        st.error(f"Error al cargar datos. Verifica el enlace de Google Sheets: {e}")
        return pd.DataFrame()

df = cargar_datos(URL_SHEET)

if not df.empty:
    # --- FILTROS LATERALES ---
    st.sidebar.header("🔍 Filtros de Búsqueda")
    
    ubicacion_opt = df['Ubicacion'].dropna().unique().tolist() if 'Ubicacion' in df.columns else []
    ubicaciones = st.sidebar.multiselect("Ubicación:", ubicacion_opt, default=ubicacion_opt)
    
    moneda_opt = df['Moneda'].dropna().unique().tolist() if 'Moneda' in df.columns else []
    monedas = st.sidebar.multiselect("Moneda:", moneda_opt, default=moneda_opt)

    # Filtrar DataFrame
    df_filtered = df.copy()
    if ubicaciones and 'Ubicacion' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['Ubicacion'].isin(ubicaciones)]
    if monedas and 'Moneda' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['Moneda'].isin(monedas)]

    # --- TARJETAS DE INDICADORES (KPIs) ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Total Órdenes", f"{len(df_filtered)}")
    
    monto_soles = df_filtered[df_filtered['Moneda'] == 'SOLES']['Monto'].sum() if 'Moneda' in df_filtered.columns else 0
    monto_dolares = df_filtered[df_filtered['Moneda'] == 'DOLAR']['Monto'].sum() if 'Moneda' in df_filtered.columns else 0
    
    c2.metric("💰 Total Soles", f"S/ {monto_soles:,.2f}")
    c3.metric("💵 Total Dólares", f"$ {monto_dolares:,.2f}")
    
    lead_time_avg = df_filtered['Lead Time'].mean() if 'Lead Time' in df_filtered.columns else 0
    c4.metric("⏱️ Lead Time Promedio", f"{lead_time_avg:.1f} días")

    st.markdown("---")

    # --- GRÁFICOS INTERACTIVOS ---
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("🏆 Top 10 Proveedores por Monto")
        if 'Proveedor' in df_filtered.columns and 'Monto' in df_filtered.columns:
            top_prov = df_filtered.groupby('Proveedor')['Monto'].sum().reset_index().sort_values('Monto', ascending=False).head(10)
            fig_prov = px.bar(top_prov, x='Monto', y='Proveedor', orientation='h', color='Monto', color_continuous_scale='Blues', text_auto='.2s')
            fig_prov.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_prov, use_container_width=True)

    with g2:
        st.subheader("💳 Distribución por Modalidad de Pago")
        if 'Pago' in df_filtered.columns and 'Monto' in df_filtered.columns:
            pago_df = df_filtered.groupby('Pago')['Monto'].sum().reset_index()
            fig_pago = px.pie(pago_df, values='Monto', names='Pago', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig_pago, use_container_width=True)

    g3, g4 = st.columns(2)

    with g3:
        st.subheader("🚛 Envíos por Transportista")
        if 'Transportista' in df_filtered.columns:
            trans_df = df_filtered['Transportista'].value_counts().reset_index()
            trans_df.columns = ['Transportista', 'Envíos']
            fig_trans = px.bar(trans_df, x='Envíos', y='Transportista', orientation='h', color_discrete_sequence=['#2563EB'])
            st.plotly_chart(fig_trans, use_container_width=True)

    with g4:
        st.subheader("📍 Lead Time Promedio por Ubicación")
        if 'Ubicacion' in df_filtered.columns and 'Lead Time' in df_filtered.columns:
            lt_ubi = df_filtered.groupby('Ubicacion')['Lead Time'].mean().reset_index()
            fig_lt = px.bar(lt_ubi, x='Ubicacion', y='Lead Time', color='Ubicacion', text_auto='.1f')
            st.plotly_chart(fig_lt, use_container_width=True)

    # Vista previa de datos
    with st.expander("📄 Ver detalle de datos filtrados"):
        st.dataframe(df_filtered, use_container_width=True)
else:
    st.info("No hay datos disponibles para mostrar.")
