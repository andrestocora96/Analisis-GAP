import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análisis GAP de Ventas", layout="wide")

st.title("📊 Tablero de Análisis GAP y Desempeño Multiciclo")

# 1. CARGA DE BASE DE DATOS Y HOJAS TEMPORALES
@st.cache_data
def cargar_archivo_master(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    
    # Cargar Maestro de Tiendas
    if 'BASE DE DATOS' in xls.sheet_names:
        df_base = pd.read_excel(xls, sheet_name='BASE DE DATOS')
        df_base = df_base.rename(columns={'Tienda': 'Tienda_Base'})
    else:
        df_base = pd.DataFrame()
        
    # Cargar Hojas de Fechas/Ciclos (Omitir BASE DE DATOS)
    hojas_fechas = [s for s in xls.sheet_names if s != 'BASE DE DATOS']
    datos_fechas = []
    
    for hoja in hojas_fechas:
        df = pd.read_excel(xls, sheet_name=hoja)
        
        # Asignar Gerente/Supervisor por Forward Fill
        df['Gerente_Supervisor'] = df['Desglose (1)'].ffill()
        df.rename(columns={'Desglose (2)': 'Tienda'}, inplace=True)
        
        # Limpieza
        df = df[~df['Gerente_Supervisor'].str.contains('Total', na=False)]
        df = df.dropna(subset=['Tienda'])
        df['Ciclo_Fecha'] = hoja
        
        # Limpieza de valores numéricos por si vienen formateados como texto
        cols_num = ['Ventas Act', 'Ppto', 'Transacciones Act', 'Ticket promedio Act']
        for col in cols_num:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace('$', '').str.replace('M', '').str.replace(',', ''), 
                    errors='coerce'
                ).fillna(0)
                
        datos_fechas.append(df)
        
    if datos_fechas:
        df_historico = pd.concat(datos_fechas, ignore_index=True)
        # Cruzar con Maestro de Tiendas si existe
        if not df_base.empty:
            df_historico = pd.merge(
                df_historico, 
                df_base, 
                left_on='Tienda', 
                right_on='Tienda_Base', 
                how='left'
            )
        return df_historico, hojas_fechas
    return pd.DataFrame(), []

# Menú lateral para subir archivo
st.sidebar.header("📁 Cargar Libro de Excel")
file_upload = st.sidebar.file_uploader("Sube el archivo ANALISIS GAP.xlsx", type=['xlsx'])

if file_upload:
    df_tot, lista_ciclos = cargar_archivo_master(file_upload)
    
    if len(lista_ciclos) < 2:
        st.warning("⚠️ El archivo necesita al menos 2 hojas de fechas/ciclos para calcular comparaciones GAP.")
    else:
        # 2. FILTROS DINÁMICOS
        st.sidebar.header("⚙️ Configuración y Filtros")
        
        ciclo_actual = st.sidebar.selectbox("Seleccionar Ciclo / Fecha Actual:", lista_ciclos, index=len(lista_ciclos)-1)
        ciclo_anterior = st.sidebar.selectbox("Seleccionar Ciclo / Fecha Comparativa:", lista_ciclos, index=max(0, len(lista_ciclos)-2))
        
        # Filtros opcionales por Maestro
        gerentes = ["Todos"] + sorted(list(df_tot['Gerente'].dropna().unique())) if 'Gerente' in df_tot.columns else ["Todos"]
        supervisores = ["Todos"] + sorted(list(df_tot['Supervisor'].dropna().unique())) if 'Supervisor' in df_tot.columns else ["Todos"]
        
        filtro_ger = st.sidebar.selectbox("Gerente:", gerentes)
        filtro_sup = st.sidebar.selectbox("Supervisor:", supervisores)
        
        # Aplicar Filtros
        df_f = df_tot.copy()
        if filtro_ger != "Todos":
            df_f = df_f[df_f['Gerente'] == filtro_ger]
        if filtro_sup != "Todos":
            df_f = df_f[df_f['Supervisor'] == filtro_sup]
            
        # Separar dataset por fechas
        df_act = df_f[df_f['Ciclo_Fecha'] == ciclo_actual]
        df_ant = df_f[df_f['Ciclo_Fecha'] == ciclo_anterior]
        
        # Cruce de fechas para métricas
        df_merged = pd.merge(
            df_act[['Tienda', 'Gerente', 'Supervisor', 'Segmento', 'Ventas Act', 'Ppto', 'Transacciones Act', 'Ticket promedio Act']],
            df_ant[['Tienda', 'Ventas Act', 'Ppto', 'Transacciones Act', 'Ticket promedio Act']],
            on='Tienda',
            suffixes=('_Act', '_Ant'),
            how='inner'
        )
        
        # Cálculos de GAP de Presupuesto y Variación de Fechas
        df_merged['GAP_Ppto_Act'] = df_merged['Ventas Act_Act'] - df_merged['Ppto_Act']
        df_merged['Cumplimiento_%'] = (df_merged['Ventas Act_Act'] / df_merged['Ppto_Act'].replace(0, 1)) * 100
        
        df_merged['Var_Ventas_$'] = df_merged['Ventas Act_Act'] - df_merged['Ventas Act_Ant']
        df_merged['Var_Trans'] = df_merged['Transacciones Act_Act'] - df_merged['Transacciones Act_Ant']
        df_merged['Var_Ticket'] = df_merged['Ticket promedio Act_Act'] - df_merged['Ticket promedio Act_Ant']

        # 3. TARJETAS MÉTIRCAS RESUMEN
        st.subheader(f"🎯 Indicadores GAP Globales ({ciclo_actual} vs {ciclo_anterior})")
        m1, m2, m3, m4 = st.columns(4)
        
        total_ventas = df_merged['Ventas Act_Act'].sum()
        total_ppto = df_merged['Ppto_Act'].sum()
        gap_total_ppto = total_ventas - total_ppto
        
        m1.metric("Ventas Totales", f"${total_ventas:,.0f}")
        m2.metric("Presupuesto Total", f"${total_ppto:,.0f}")
        m3.metric("GAP vs Presupuesto", f"${gap_total_ppto:,.0f}", delta_color="normal")
        m4.metric("Variación Ventas vs Fecha Ant.", f"${df_merged['Var_Ventas_$'].sum():,.0f}")

        st.markdown("---")

        # 4. GRÁFICOS DE ANÁLISIS
        tab1, tab2, tab3 = st.tabs(["📉 GAP Presupuesto", "🔄 Variación de Ciclo", "🎟️ Transacciones y Ticket"])
        
        with tab1:
            st.subheader("Brecha vs Presupuesto por Tienda (GAP Ppto)")
            fig_gap = px.bar(
                df_merged.sort_values(by='GAP_Ppto_Act'),
                y='Tienda',
                x='GAP_Ppto_Act',
                color='GAP_Ppto_Act',
                color_continuous_scale='RdYlGn',
                orientation='h',
                title="Diferencia Monetaria vs Presupuesto ($)"
            )
            st.plotly_chart(fig_gap, use_container_width=True)

        with tab2:
            st.subheader("Crecimiento/Decrecimiento de Ventas vs Ciclo Anterior")
            fig_var = px.bar(
                df_merged.sort_values(by='Var_Ventas_$'),
                y='Tienda',
                x='Var_Ventas_$',
                color='Var_Ventas_$',
                color_continuous_scale='Blugrn',
                orientation='h',
                title="Variación de Ventas entre Fechas ($)"
            )
            st.plotly_chart(fig_var, use_container_width=True)

        with tab3:
            st.subheader("Análisis de Transacciones y Ticket Promedio")
            col_a, col_b = st.columns(2)
            with col_a:
                fig_trans = px.bar(df_merged, x='Tienda', y='Var_Trans', title="Variación en Transacciones (#)")
                st.plotly_chart(fig_trans, use_container_width=True)
            with col_b:
                fig_tick = px.line(df_merged, x='Tienda', y=['Ticket promedio Act_Act', 'Ticket promedio Act_Ant'], title="Comparativa Ticket Promedio ($)")
                st.plotly_chart(fig_tick, use_container_width=True)

        # 5. TABLA DE DETALLE COMPLETA
        st.subheader("📋 Matriz Detallada de GAP y Métricas")
        st.dataframe(
            df_merged[[
                'Tienda', 'Gerente', 'Supervisor', 'Ventas Act_Act', 
                'Ppto_Act', 'GAP_Ppto_Act', 'Cumplimiento_%', 'Var_Ventas_$', 'Var_Trans', 'Var_Ticket'
            ]].style.format({
                'Ventas Act_Act': '${:,.0f}',
                'Ppto_Act': '${:,.0f}',
                'GAP_Ppto_Act': '${:,.0f}',
                'Cumplimiento_%': '{:.1f}%',
                'Var_Ventas_$': '${:,.0f}',
                'Var_Trans': '{:,.0f}',
                'Var_Ticket': '${:,.0f}'
            }),
            use_container_width=True
        )

else:
    st.info("👈 Por favor, carga tu archivo Excel (ANALISIS GAP.xlsx) en la barra lateral para generar el tablero.")