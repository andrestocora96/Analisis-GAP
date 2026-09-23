import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Análisis GAP - Ventas", layout="wide")

st.title("📊 Análisis GAP - Control Semanal de Ventas")

# 1. CARGA AUTOMÁTICA Y ESTRUCTURA DE HISTÓRICO
@st.cache_data
def cargar_historico(uploaded_files):
    lista_df = []
    for file in uploaded_files:
        df = pd.read_excel(file)
        
        # Normalizar jerarquía (rellenar gerentes hacia abajo)
        df['Gerente_Supervisor'] = df['Desglose (1)'].ffill()
        df.rename(columns={'Desglose (2)': 'Tienda'}, inplace=True)
        
        # Limpiar filas de totales y vacías
        df = df[~df['Gerente_Supervisor'].str.contains('Total', na=False)]
        df = df.dropna(subset=['Tienda'])
        
        # Identificar periodo desde el nombre del archivo
        df['Archivo_Origen'] = file.name
        lista_df.append(df)
        
    if lista_df:
        return pd.concat(lista_df, ignore_index=True)
    return pd.DataFrame()

# Carga de archivos
st.sidebar.header("📂 Cargar Informes Semanales")
uploaded_files = st.sidebar.file_uploader(
    "Sube tus informes de Excel aquí", 
    accept_multiple_files=True, 
    type=['xlsx']
)

if uploaded_files:
    df_historico = cargar_historico(uploaded_files)
    archivos_disponibles = sorted(df_historico['Archivo_Origen'].unique())
    
    st.sidebar.header("⚙️ Configuración del Análisis")
    semana_evaluar = st.sidebar.selectbox(
        "Semana a Evaluar (Actual):", 
        archivos_disponibles, 
        index=len(archivos_disponibles) - 1
    )
    
    idx_actual = archivos_disponibles.index(semana_evaluar)
    
    if idx_actual == 0:
        st.warning("⚠️ Selecciona al menos dos informes cargados para realizar el análisis comparativo GAP.")
    else:
        semana_anterior = archivos_disponibles[idx_actual - 1]
        st.sidebar.success(f"Comparando contra: **{semana_anterior}**")
        
        # Filtros
        supervisores = ["Todos"] + list(df_historico['Gerente_Supervisor'].unique())
        sup_filtro = st.sidebar.selectbox("Gerente Supervisor:", supervisores)
        
        df_filtrado = df_historico.copy()
        if sup_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Gerente_Supervisor'] == sup_filtro]
            
        df_act = df_filtrado[df_filtrado['Archivo_Origen'] == semana_evaluar]
        df_ant = df_filtrado[df_filtrado['Archivo_Origen'] == semana_anterior]
        
        # Cruce de datos (S vs S-1)
        df_gap = pd.merge(
            df_act[['Tienda', 'Gerente_Supervisor', 'Ventas Act', 'Estado Comparación']],
            df_ant[['Tienda', 'Ventas Act']],
            on='Tienda',
            suffixes=('_Actual', '_Anterior'),
            how='inner'
        )
        
        # Cálculos de brecha / GAP
        df_gap['Var_$'] = df_gap['Ventas Act_Actual'] - df_gap['Ventas Act_Anterior']
        df_gap['Crecimiento_%'] = (df_gap['Var_$'] / df_gap['Ventas Act_Anterior'].replace(0, 1)) * 100
        df_gap['Tendencia'] = df_gap['Var_$'].apply(lambda x: 'Crece 🟢' if x >= 0 else 'Decrece 🔴')

        # Tarjetas Métricas
        c1, c2, c3 = st.columns(3)
        c1.metric("Tiendas Analizadas", f"{len(df_gap)}")
        c2.metric("Tiendas que CRECEN 🟢", f"{(df_gap['Var_$'] >= 0).sum()}")
        c3.metric("Tiendas que DECRECEN 🔴", f"{(df_gap['Var_$'] < 0).sum()}", delta_color="inverse")

        st.markdown("---")

        # Gráfico GAP
        st.subheader(f"📉 Brecha / Crecimiento por Tienda ({semana_evaluar} vs {semana_anterior})")
        df_sorted = df_gap.sort_values(by='Var_$', ascending=True)
        
        fig = px.bar(
            df_sorted,
            y='Tienda',
            x='Var_$',
            color='Tendencia',
            color_discrete_map={'Crece 🟢': '#27ae60', 'Decrece 🔴': '#e74c3c'},
            orientation='h',
            title="Diferencia Monetaria ($) respecto a la Semana Anterior",
            text_auto='.2s'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Matriz de detalle
        st.subheader("📋 Detalle de Brecha (Análisis GAP)")
        st.dataframe(
            df_gap[[
                'Tienda', 'Gerente_Supervisor', 'Ventas Act_Actual', 
                'Ventas Act_Anterior', 'Var_$', 'Crecimiento_%', 'Tendencia'
            ]].style.format({
                'Ventas Act_Actual': '${:,.0f}',
                'Ventas Act_Anterior': '${:,.0f}',
                'Var_$': '${:,.0f}',
                'Crecimiento_%': '{:.2f}%'
            }),
            use_container_width=True
        )
else:
    st.info("👈 Para iniciar el Análisis GAP, carga tus informes semanales en el menú de la izquierda.")
