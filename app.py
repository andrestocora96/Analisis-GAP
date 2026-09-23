import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Control y Análisis GAP - Ventas", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.title("📊 Tablero de Control Gerencial y Análisis GAP")

# 1. FUNCIÓN DE LIMPIEZA DE MONEDA (Corrige el formato $4M vs Cifras Completa)
def convertir_moneda_a_pesos(val):
    if pd.isna(val):
        return 0.0
    s = str(val).replace('$', '').replace(',', '').strip()
    if 'M' in s:
        s = s.replace('M', '')
        try:
            return float(s) * 1_000_000.0
        except:
            return 0.0
    try:
        return float(s)
    except:
        return 0.0

# 2. CARGA DE ARCHIVO Y NORMALIACIÓN
@st.cache_data
def cargar_analisis_gap(file):
    xls = pd.ExcelFile(file)
    
    # Cargar Maestro BASE DE DATOS
    df_bd = pd.DataFrame()
    if 'BASE DE DATOS' in xls.sheet_names:
        df_bd = pd.read_excel(xls, sheet_name='BASE DE DATOS')
        df_bd['Tienda_Clean'] = df_bd['Tienda'].astype(str).str.strip().str.upper()
    
    ciclos = [s for s in xls.sheet_names if s != 'BASE DE DATOS']
    dfs = []
    
    for c in ciclos:
        df = pd.read_excel(xls, sheet_name=c)
        
        # Limpieza de Tienda
        if 'Desglose (2)' in df.columns:
            df.rename(columns={'Desglose (2)': 'Tienda'}, inplace=True)
            
        df = df[df['Tienda'].notna()]
        df = df[~df['Tienda'].astype(str).str.contains('Total|general', case=False, na=False)]
        df['Tienda_Clean'] = df['Tienda'].astype(str).str.strip().str.upper()
        df['Ciclo'] = str(c)
        
        # Limpieza de valores de Ventas y Presupuestos
        df['Ventas_Real_$'] = df['Ventas Act'].apply(convertir_moneda_a_pesos)
        df['Ppto_Real_$'] = df['Ppto'].apply(convertir_moneda_a_pesos)
        df['Transacciones_Real'] = pd.to_numeric(df['Transacciones Act'], errors='coerce').fillna(0)
        df['Ticket_Real_$'] = pd.to_numeric(df['Ticket promedio Act'], errors='coerce').fillna(0)
        
        dfs.append(df)
        
    if dfs:
        df_tot = pd.concat(dfs, ignore_index=True)
        # Cruce estricto con BASE DE DATOS para traer el Gerente y Supervisor correctos
        if not df_bd.empty:
            cols_bd = ['Tienda_Clean', 'Gerente', 'Supervisor', 'Ciudad', 'Segmento', 'Comparable ', 'Pareto', 'Comparable sept']
            cols_bd = [col for col in cols_bd if col in df_bd.columns]
            df_tot = pd.merge(df_tot, df_bd[cols_bd], on='Tienda_Clean', how='left')
            
        return df_tot, ciclos
    return pd.DataFrame(), []

# Sidebar para cargar archivo
st.sidebar.header("📁 Cargar Información")
uploaded_file = st.sidebar.file_uploader("Sube ANALISIS GAP.xlsx", type=['xlsx'])

if uploaded_file:
    df_data, lista_ciclos = cargar_analisis_gap(uploaded_file)
    
    if len(lista_ciclos) < 2:
        st.warning("⚠️ Debes tener al menos 2 pestañas de fechas/ciclos para el Análisis GAP.")
    else:
        st.sidebar.header("⚙️ Configuración del Análisis")
        
        # Selección de Ciclos
        c_act = st.sidebar.selectbox("Fecha Evaluada (Actual):", lista_ciclos, index=len(lista_ciclos)-1)
        c_ant = st.sidebar.selectbox("Fecha Comparativa (Anterior):", lista_ciclos, index=max(0, len(lista_ciclos)-2))
        
        # Datasets separados
        df_act = df_data[df_data['Ciclo'] == c_act].copy()
        df_ant = df_data[df_data['Ciclo'] == c_ant].copy()
        
        # Cruce de Fechas por Tienda
        df_merged = pd.merge(
            df_act[['Tienda_Clean', 'Tienda', 'Gerente', 'Supervisor', 'Ciudad', 'Segmento', 'Comparable ', 'Pareto', 'Ventas_Real_$', 'Ppto_Real_$', 'Transacciones_Real', 'Ticket_Real_$']],
            df_ant[['Tienda_Clean', 'Ventas_Real_$', 'Ppto_Real_$', 'Transacciones_Real', 'Ticket_Real_$']],
            on='Tienda_Clean',
            suffixes=('_Act', '_Ant'),
            how='inner'
        )
        
        # Cálculos de GAP y Variaciones Reales
        df_merged['GAP_Ppto_$'] = df_merged['Ventas_Real_$_Act'] - df_merged['Ppto_Real_$_Act']
        df_merged['Cumplimiento_%'] = (df_merged['Ventas_Real_$_Act'] / df_merged['Ppto_Real_$_Act'].replace(0, 1)) * 100
        
        df_merged['Var_Ventas_$'] = df_merged['Ventas_Real_$_Act'] - df_merged['Ventas_Real_$_Ant']
        df_merged['Var_Ventas_%'] = (df_merged['Var_Ventas_$'] / df_merged['Ventas_Real_$_Ant'].replace(0, 1)) * 100
        
        df_merged['Var_Trans'] = df_merged['Transacciones_Real_Act'] - df_merged['Transacciones_Real_Ant']
        df_merged['Var_Ticket'] = df_merged['Ticket_Real_$_Act'] - df_merged['Ticket_Real_$_Ant']

        # --- NAVEGACIÓN PRINCIPAL ---
        tab1, tab2, tab3, tab4 = st.tabs([
            "👔 Resumen por Gerencia", 
            "🏬 Análisis por Tiendas & GAP", 
            "🎟️ Transacciones & Ticket Promedio", 
            "🔍 Matriz General & Filtros"
        ])

        # -------------------------------------------------------------
        # PESTAÑA 1: RESUMEN GENERAL POR GERENCIA
        # -------------------------------------------------------------
        with tab1:
            st.subheader(f"👔 Desempeño Consolidado Gerencial ({c_act} vs {c_ant})")
            
            # Agrupado por Gerente
            df_ger = df_merged.groupby('Gerente', dropna=False).agg(
                Ventas_Actuales=('Ventas_Real_$_Act', 'sum'),
                Presupuesto_Actual=('Ppto_Real_$_Act', 'sum'),
                GAP_Presupuesto=('GAP_Ppto_$', 'sum'),
                Ventas_Anteriores=('Ventas_Real_$_Ant', 'sum'),
                Crecimiento_Ventas=('Var_Ventas_$', 'sum'),
                Transacciones=('Transacciones_Real_Act', 'sum')
            ).reset_index()
            
            df_ger['Cumplimiento_%'] = (df_ger['Ventas_Actuales'] / df_ger['Presupuesto_Actual'].replace(0, 1)) * 100
            df_ger['Crecimiento_%'] = (df_ger['Crecimiento_Ventas'] / df_ger['Ventas_Anteriores'].replace(0, 1)) * 100

            # Tarjetas Resumen Global
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Ventas Totales", f"${df_ger['Ventas_Actuales'].sum():,.0f}")
            col2.metric("Presupuesto Total", f"${df_ger['Presupuesto_Actual'].sum():,.0f}")
            col3.metric("GAP vs Presupuesto Total", f"${df_ger['GAP_Presupuesto'].sum():,.0f}", delta_color="normal")
            col4.metric("Crecimiento vs Fecha Ant.", f"${df_ger['Crecimiento_Ventas'].sum():,.0f}", f"{((df_ger['Ventas_Actuales'].sum()/df_ger['Ventas_Anteriores'].sum().replace(0,1))-1)*100:.1f}%")

            st.markdown("---")

            # Botones de Selección Visual
            st.markdown("##### 🔘 Selecciona la métrica para comparar entre Gerencias:")
            vista_gerencial = st.radio(
                "", 
                ["Cumplimiento vs Presupuesto (%)", "GAP Monetario vs Presupuesto ($)", "Crecimiento de Ventas vs Ciclo Anterior ($)"],
                horizontal=True
            )

            if "Cumplimiento" in vista_gerencial:
                fig = px.bar(
                    df_ger.sort_values(by='Cumplimiento_%', ascending=False),
                    x='Gerente', y='Cumplimiento_%', text_auto='.1f',
                    color='Cumplimiento_%', color_continuous_scale='Greens',
                    title="% Cumplimiento de Presupuesto por Gerencia"
                )
                fig.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Meta 100%")
                st.plotly_chart(fig, use_container_width=True)
                
            elif "GAP Monetario" in vista_gerencial:
                fig = px.bar(
                    df_ger.sort_values(by='GAP_Presupuesto', ascending=False),
                    x='Gerente', y='GAP_Presupuesto', text_auto='.2s',
                    color='GAP_Presupuesto', color_continuous_scale='RdYlGn',
                    title="GAP Monetario vs Presupuesto ($) por Gerencia"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                fig = px.bar(
                    df_ger.sort_values(by='Crecimiento_Ventas', ascending=False),
                    x='Gerente', y='Crecimiento_Ventas', text_auto='.2s',
                    color='Crecimiento_Ventas', color_continuous_scale='Blugrn',
                    title="Crecimiento de Ventas ($) vs Fecha Anterior por Gerencia"
                )
                st.plotly_chart(fig, use_container_width=True)

            # Matriz Gerencial
            st.markdown("#### 📋 Consolidado de Indicadores por Gerencia")
            st.dataframe(
                df_ger.style.format({
                    'Ventas_Actuales': '${:,.0f}',
                    'Presupuesto_Actual': '${:,.0f}',
                    'GAP_Presupuesto': '${:,.0f}',
                    'Cumplimiento_%': '{:.1f}%',
                    'Ventas_Anteriores': '${:,.0f}',
                    'Crecimiento_Ventas': '${:,.0f}',
                    'Crecimiento_%': '{:.1f}%',
                    'Transacciones': '{:,.0f}'
                }),
                use_container_width=True
            )

        # -------------------------------------------------------------
        # PESTAÑA 2: ANÁLISIS DETALLADO POR TIENDA
        # -------------------------------------------------------------
        with tab2:
            st.subheader("🏬 Detalle por Tiendas & Identificación de Brechas")
            
            # Filtros dinámicos superiores
            f1, f2, f3 = st.columns(3)
            with f1:
                filtro_ger_t = st.selectbox("Filtrar por Gerente:", ["Todos"] + sorted(list(df_merged['Gerente'].dropna().unique())))
            with f2:
                filtro_sup_t = st.selectbox("Filtrar por Supervisor:", ["Todos"] + sorted(list(df_merged['Supervisor'].dropna().unique())))
            with f3:
                filtro_pareto = st.selectbox("Filtrar por Pareto:", ["Todos"] + sorted(list(df_merged['Pareto'].dropna().unique())))

            # Aplicar filtros
            df_t_view = df_merged.copy()
            if filtro_ger_t != "Todos":
                df_t_view = df_t_view[df_t_view['Gerente'] == filtro_ger_t]
            if filtro_sup_t != "Todos":
                df_t_view = df_t_view[df_t_view['Supervisor'] == filtro_sup_t]
            if filtro_pareto != "Todos":
                df_t_view = df_t_view[df_t_view['Pareto'] == filtro_pareto]

            st.markdown("---")

            # Botones de Crecimiento vs Decrecimiento %
            st.markdown("##### 🔘 Estado de Crecimiento de Tiendas:")
            filtro_estado = st.radio(
                "",
                ["Todas las Tiendas", "Tiendas que DECRECEN % (Atención 🔴)", "Tiendas que CRECEN % (🟢)"],
                horizontal=True
            )
            
            if "DECRECEN" in filtro_estado:
                df_t_view = df_t_view[df_t_view['Var_Ventas_%'] < 0]
            elif "CRECEN" in filtro_estado:
                df_t_view = df_t_view[df_t_view['Var_Ventas_%'] >= 0]

            # Gráfico GAP de Crecimiento %
            fig_t = px.bar(
                df_t_view.sort_values(by='Var_Ventas_%'),
                y='Tienda', x='Var_Ventas_%',
                color='Var_Ventas_%', color_continuous_scale='RdYlGn',
                orientation='h', text_auto='.1f',
                title="Variación Porcentual de Ventas (%) entre Fechas Medidas"
            )
            fig_t.update_layout(height=max(400, len(df_t_view) * 22))
            st.plotly_chart(fig_t, use_container_width=True)

        # -------------------------------------------------------------
        # PESTAÑA 3: TRANSACCIONES Y TICKET PROMEDIO
        # -------------------------------------------------------------
        with tab3:
            st.subheader("🎟️ Comportamiento de Tráfico y Ticket Promedio")
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("#### Variación de Transacciones (#)")
                fig_tr = px.bar(
                    df_merged.sort_values(by='Var_Trans', ascending=False).head(15),
                    x='Tienda', y='Var_Trans', color='Var_Trans', color_continuous_scale='Viridis',
                    title="Top 15 Tiendas con Mayor Cambio en Clientes Atendidos"
                )
                st.plotly_chart(fig_tr, use_container_width=True)
                
            with col_b:
                st.markdown("#### Ticket Promedio ($)")
                fig_tk = px.scatter(
                    df_merged,
                    x='Ticket_Real_$_Ant', y='Ticket_Real_$_Act',
                    size='Ventas_Real_$_Act', color='Gerente', hover_name='Tienda',
                    title="Comparativa Ticket Promedio (Eje X: Ant. vs Eje Y: Act.)"
                )
                st.plotly_chart(fig_tk, use_container_width=True)

        # -------------------------------------------------------------
        # PESTAÑA 4: MATRIZ COMPLETA DE DATOS
        # -------------------------------------------------------------
        with tab4:
            st.subheader("📋 Matriz Completa de Datos y Filtros Libres")
            st.dataframe(
                df_merged[[
                    'Tienda', 'Gerente', 'Supervisor', 'Segmento', 'Pareto',
                    'Ventas_Real_$_Act', 'Ppto_Real_$_Act', 'GAP_Ppto_$', 'Cumplimiento_%',
                    'Ventas_Real_$_Ant', 'Var_Ventas_$', 'Var_Ventas_%',
                    'Transacciones_Real_Act', 'Ticket_Real_$_Act'
                ]].style.format({
                    'Ventas_Real_$_Act': '${:,.0f}',
                    'Ppto_Real_$_Act': '${:,.0f}',
                    'GAP_Ppto_$': '${:,.0f}',
                    'Cumplimiento_%': '{:.1f}%',
                    'Ventas_Real_$_Ant': '${:,.0f}',
                    'Var_Ventas_$': '${:,.0f}',
                    'Var_Ventas_%': '{:.1f}%',
                    'Transacciones_Real_Act': '{:,.0f}',
                    'Ticket_Real_$_Act': '${:,.0f}'
                }),
                use_container_width=True
            )

else:
    st.info("👈 Por favor, sube el archivo ANALISIS GAP.xlsx en el menú de la izquierda para comenzar.")