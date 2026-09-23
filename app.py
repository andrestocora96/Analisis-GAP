import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la aplicación
st.set_page_config(
    page_title="Tablero de Control - Análisis GAP", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.title("📊 Tablero de Control y Análisis GAP de Ventas")

# 1. FUNCIÓN DE CARGA Y LIMPIEZA
@st.cache_data
def cargar_datos_completos(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    
    # Cargar Maestro BASE DE DATOS
    df_base = pd.DataFrame()
    if 'BASE DE DATOS' in xls.sheet_names:
        df_base = pd.read_excel(xls, sheet_name='BASE DE DATOS')
        df_base = df_base.rename(columns={'Tienda': 'Tienda_Maestro'})
    
    # Cargar pestañas de fechas/ciclos
    hojas_ciclos = [s for s in xls.sheet_names if s != 'BASE DE DATOS']
    lista_dfs = []
    
    for hoja in hojas_ciclos:
        df = pd.read_excel(xls, sheet_name=hoja)
        
        # Propagar supervisor/gerente si vienen en celdas combinadas
        if 'Desglose (1)' in df.columns:
            df['Gerente_Supervisor_Raw'] = df['Desglose (1)'].ffill()
        if 'Desglose (2)' in df.columns:
            df.rename(columns={'Desglose (2)': 'Tienda'}, inplace=True)
            
        # Filtrar filas de totales o vacías
        df = df[df['Tienda'].notna()]
        df = df[~df['Tienda'].astype(str).str.contains('Total|general', case=False, na=False)]
        df['Ciclo'] = str(hoja)
        
        # Limpieza de columnas numéricas
        cols_numericas = ['Ventas Act', 'Ppto', 'Transacciones Act', 'Ticket promedio Act']
        for col in cols_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace('$', '', regex=False)
                           .str.replace('M', '', regex=False)
                           .str.replace(',', '', regex=False),
                    errors='coerce'
                ).fillna(0)
                
        lista_dfs.append(df)
        
    if lista_dfs:
        df_historico = pd.concat(lista_dfs, ignore_index=True)
        if not df_base.empty:
            df_historico = pd.merge(
                df_historico, 
                df_base, 
                left_on='Tienda', 
                right_on='Tienda_Maestro', 
                how='left'
            )
        return df_historico, hojas_ciclos
    return pd.DataFrame(), []

# Cargar archivo desde el Sidebar
st.sidebar.header("📁 Carga de Información")
archivo_excel = st.sidebar.file_uploader("Sube el archivo ANALISIS GAP.xlsx", type=['xlsx'])

if archivo_excel:
    df_tot, ciclos = cargar_datos_completos(archivo_excel)
    
    if len(ciclos) < 2:
        st.warning("⚠️ Se requieren al menos 2 pestañas de fechas/ciclos para comparar el análisis GAP.")
    else:
        # Selección de Ciclos a comparar
        st.sidebar.header("⚙️ Configuración de Comparación")
        ciclo_act = st.sidebar.selectbox("Ciclo Evaluado (Actual):", ciclos, index=len(ciclos)-1)
        ciclo_ant = st.sidebar.selectbox("Ciclo Comparativo (Anterior):", ciclos, index=max(0, len(ciclos)-2))
        
        # Separación y Cruce de Datasets por Fechas
        df_act = df_tot[df_tot['Ciclo'] == ciclo_act].copy()
        df_ant = df_tot[df_tot['Ciclo'] == ciclo_ant].copy()
        
        cols_merge = ['Tienda', 'Gerente', 'Supervisor', 'Ciudad', 'Segmento', 'Comparable ', 'Pareto']
        cols_merge = [c for c in cols_merge if c in df_act.columns]
        
        df_merged = pd.merge(
            df_act[cols_merge + ['Ventas Act', 'Ppto', 'Transacciones Act', 'Ticket promedio Act']],
            df_ant[['Tienda', 'Ventas Act', 'Ppto', 'Transacciones Act', 'Ticket promedio Act']],
            on='Tienda',
            suffixes=('_Act', '_Ant'),
            how='inner'
        )
        
        # Cálculos del GAP y Variaciones
        df_merged['GAP_Ppto_$'] = df_merged['Ventas Act_Act'] - df_merged['Ppto_Act']
        df_merged['Cumplimiento_%'] = (df_merged['Ventas Act_Act'] / df_merged['Ppto_Act'].replace(0, 1)) * 100
        df_merged['Var_Ventas_$'] = df_merged['Ventas Act_Act'] - df_merged['Ventas Act_Ant']
        df_merged['Var_Ventas_%'] = (df_merged['Var_Ventas_$'] / df_merged['Ventas Act_Ant'].replace(0, 1)) * 100
        df_merged['Var_Trans'] = df_merged['Transacciones Act_Act'] - df_merged['Transacciones Act_Ant']
        df_merged['Var_Ticket'] = df_merged['Ticket promedio Act_Act'] - df_merged['Ticket promedio Act_Ant']

        # --- NAVEGACIÓN PRINCIPAL CON PESTAÑAS ---
        tab1, tab2, tab3, tab4 = st.tabs([
            "🏢 Resumen Gerencial", 
            "🏬 Detalle Tienda a Tienda", 
            "🎟️ Transacciones & Ticket", 
            "📋 Matriz & Maestro"
        ])

        # -------------------------------------------------------------
        # PESTAÑA 1: RESUMEN GERENCIAL
        # -------------------------------------------------------------
        with tab1:
            st.subheader(f"📊 Desempeño Consolidado por Gerencias ({ciclo_act})")
            
            # Selector de Agrupación con Botones
            agrupador = st.radio(
                "Ver Consolidado por:", 
                ["Gerente", "Supervisor", "Segmento", "Ciudad"], 
                horizontal=True
            )
            
            if agrupador in df_merged.columns:
                df_gerencial = df_merged.groupby(agrupador).agg(
                    Ventas_Actuales=('Ventas Act_Act', 'sum'),
                    Presupuesto=('Ppto_Act', 'sum'),
                    GAP_Ppto=('GAP_Ppto_$', 'sum'),
                    Ventas_Anteriores=('Ventas Act_Ant', 'sum'),
                    Var_Ventas=('Var_Ventas_$', 'sum'),
                    Transacciones=('Transacciones Act_Act', 'sum')
                ).reset_index()
                
                df_gerencial['Cumplimiento_%'] = (df_gerencial['Ventas_Actuales'] / df_gerencial['Presupuesto'].replace(0, 1)) * 100
                df_gerencial['Var_Ventas_%'] = (df_gerencial['Var_Ventas'] / df_gerencial['Ventas_Anteriores'].replace(0, 1)) * 100
                
                # Tarjetas Macro
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Ventas Totales", f"${df_gerencial['Ventas_Actuales'].sum():,.0f}")
                c2.metric("Presupuesto Total", f"${df_gerencial['Presupuesto'].sum():,.0f}")
                c3.metric("GAP vs Presupuesto", f"${df_gerencial['GAP_Ppto'].sum():,.0f}")
                c4.metric("Crecimiento vs Ciclo Anterior", f"${df_gerencial['Var_Ventas'].sum():,.0f}")

                st.markdown("---")

                # Gráfico Visual de Cumplimiento por Gerencia/Grupo
                fig_ger = px.bar(
                    df_gerencial.sort_values(by='Cumplimiento_%', ascending=False),
                    x=agrupador,
                    y='Cumplimiento_%',
                    color='Cumplimiento_%',
                    color_continuous_scale='Greens',
                    text_auto='.1f',
                    title=f"% Cumplimiento de Presupuesto por {agrupador}"
                )
                fig_ger.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Meta 100%")
                st.plotly_chart(fig_ger, use_container_width=True)

                # Tabla Resumen Gerencial
                st.dataframe(
                    df_gerencial.style.format({
                        'Ventas_Actuales': '${:,.0f}',
                        'Presupuesto': '${:,.0f}',
                        'GAP_Ppto': '${:,.0f}',
                        'Ventas_Anteriores': '${:,.0f}',
                        'Var_Ventas': '${:,.0f}',
                        'Cumplimiento_%': '{:.1f}%',
                        'Var_Ventas_%': '{:.1f}%'
                    }),
                    use_container_width=True
                )

        # -------------------------------------------------------------
        # PESTAÑA 2: DETALLE TIENDA A TIENDA (ANÁLISIS GAP)
        # -------------------------------------------------------------
        with tab2:
            st.subheader("🎯 Identificación de Brechas (Tiendas que Crece vs Decrecen)")
            
            # Botones de Filtro de Crecimiento/Decrecimiento
            filtro_vista = st.radio(
                "Filtrar tiendas por:", 
                ["Todas las Tiendas", "Sólo Tiendas que Decrecen (Críticas 🔴)", "Sólo Tiendas que Crecen (🟢)"],
                horizontal=True
            )
            
            df_tiendas_view = df_merged.copy()
            if "Decrecen" in filtro_vista:
                df_tiendas_view = df_tiendas_view[df_tiendas_view['Var_Ventas_$'] < 0]
            elif "Crecen" in filtro_vista:
                df_tiendas_view = df_tiendas_view[df_tiendas_view['Var_Ventas_$'] >= 0]
                
            # Gráfico Divergente GAP
            fig_gap = px.bar(
                df_tiendas_view.sort_values(by='Var_Ventas_$'),
                y='Tienda',
                x='Var_Ventas_$',
                color='Var_Ventas_$',
                color_continuous_scale='RdYlGn',
                orientation='h',
                title="Diferencia de Ventas ($) entre Ciclos Evaluados",
                text_auto='.2s'
            )
            fig_gap.update_layout(height=max(400, len(df_tiendas_view) * 20))
            st.plotly_chart(fig_gap, use_container_width=True)

        # -------------------------------------------------------------
        # PESTAÑA 3: TRANSACCIONES Y TICKET PROMEDIO
        # -------------------------------------------------------------
        with tab3:
            st.subheader("🎟️ Comportamiento de Tráfico (Transacciones) y Ticket Promedio")
            
            metric_view = st.radio(
                "Métrica a Visualizar:", 
                ["Variación en Transacciones (#)", "Variación en Ticket Promedio ($)"],
                horizontal=True
            )
            
            if "Transacciones" in metric_view:
                fig_t = px.bar(
                    df_merged.sort_values(by='Var_Trans'),
                    x='Tienda',
                    y='Var_Trans',
                    color='Var_Trans',
                    color_continuous_scale='Viridis',
                    title="Variación de Clientes/Transacciones Atendidas (#)"
                )
                st.plotly_chart(fig_t, use_container_width=True)
            else:
                fig_tk = px.scatter(
                    df_merged,
                    x='Ticket promedio Act_Ant',
                    y='Ticket promedio Act_Act',
                    size='Ventas Act_Act',
                    color='Gerente' if 'Gerente' in df_merged.columns else None,
                    hover_name='Tienda',
                    title="Comparación Ticket Promedio (Eje X: Anterior vs Eje Y: Actual)"
                )
                st.plotly_chart(fig_tk, use_container_width=True)

        # -------------------------------------------------------------
        # PESTAÑA 4: MATRIZ Y MAESTRO DE DATOS COMPLETO
        # -------------------------------------------------------------
        with tab4:
            st.subheader("📋 Matriz Consolidada de Resultados")
            st.dataframe(
                df_merged.style.format({
                    'Ventas Act_Act': '${:,.0f}',
                    'Ppto_Act': '${:,.0f}',
                    'GAP_Ppto_$': '${:,.0f}',
                    'Cumplimiento_%': '{:.1f}%',
                    'Ventas Act_Ant': '${:,.0f}',
                    'Var_Ventas_$': '${:,.0f}',
                    'Var_Ventas_%': '{:.1f}%',
                    'Transacciones Act_Act': '{:,.0f}',
                    'Ticket promedio Act_Act': '${:,.0f}'
                }),
                use_container_width=True
            )

else:
    st.info("👈 Por favor, sube el archivo Excel (ANALISIS GAP.xlsx) en el menú lateral para activar la visualización.")