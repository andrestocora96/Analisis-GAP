import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Tablero Gerencial - Control de GAP y Desempeño", 
    layout="wide"
)

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>📊 TABLERO GERENCIAL: CONTROL DE GAP DE PPTO Y EVOLUCIÓN</h2>", unsafe_allow_html=True)

# 1. FUNCIÓN DE CONVERSIÓN MONETARIA
def limpiar_monto(val):
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

@st.cache_data
def cargar_datos(file):
    xls = pd.ExcelFile(file)
    
    df_bd = pd.DataFrame()
    if 'BASE DE DATOS' in xls.sheet_names:
        df_bd = pd.read_excel(xls, sheet_name='BASE DE DATOS')
        df_bd['Tienda_Clean'] = df_bd['Tienda'].astype(str).str.strip().str.upper()
    
    hojas = [s for s in xls.sheet_names if s != 'BASE DE DATOS']
    dfs = []
    
    for h in hojas:
        df = pd.read_excel(xls, sheet_name=h)
        if 'Desglose (2)' in df.columns:
            df.rename(columns={'Desglose (2)': 'Tienda'}, inplace=True)
            
        df = df[df['Tienda'].notna()]
        df = df[~df['Tienda'].astype(str).str.contains('Total|general', case=False, na=False)]
        df['Tienda_Clean'] = df['Tienda'].astype(str).str.strip().str.upper()
        df['Ciclo'] = str(h)
        
        df['Ventas_Real'] = df['Ventas Act'].apply(limpiar_monto)
        df['Ppto_Real'] = df['Ppto'].apply(limpiar_monto)
        df['Transacciones_Real'] = pd.to_numeric(df['Transacciones Act'], errors='coerce').fillna(0)
        
        dfs.append(df)
        
    if dfs:
        df_tot = pd.concat(dfs, ignore_index=True)
        if not df_bd.empty:
            cols_bd = ['Tienda_Clean', 'Gerente', 'Supervisor', 'Ciudad', 'Segmento', 'Comparable ', 'Pareto']
            cols_bd = [c for c in cols_bd if c in df_bd.columns]
            df_tot = pd.merge(df_tot, df_bd[cols_bd], on='Tienda_Clean', how='left')
        return df_tot, hojas
    return pd.DataFrame(), []

# Carga de archivo
st.sidebar.header("📁 Cargar Excel")
uploaded_file = st.sidebar.file_uploader("Sube ANALISIS GAP.xlsx", type=['xlsx'])

if uploaded_file:
    df_tot, lista_ciclos = cargar_datos(uploaded_file)
    
    if len(lista_ciclos) >= 2:
        c_act = st.sidebar.selectbox("Semana/Ciclo Actual:", lista_ciclos, index=len(lista_ciclos)-1)
        c_ant = st.sidebar.selectbox("Semana/Ciclo Anterior:", lista_ciclos, index=max(0, len(lista_ciclos)-2))
        
        df_act = df_tot[df_tot['Ciclo'] == c_act].copy()
        df_ant = df_tot[df_tot['Ciclo'] == c_ant].copy()
        
        # Cruce Completo Outer (Toda la Compañía)
        df_merged = pd.merge(
            df_act[['Tienda_Clean', 'Tienda', 'Gerente', 'Supervisor', 'Ciudad', 'Segmento', 'Pareto', 'Ventas_Real', 'Ppto_Real', 'Transacciones_Real']],
            df_ant[['Tienda_Clean', 'Tienda', 'Gerente', 'Supervisor', 'Ventas_Real', 'Ppto_Real', 'Transacciones_Real']],
            on='Tienda_Clean',
            suffixes=('_Act', '_Ant'),
            how='outer'
        )
        
        df_merged['Tienda'] = df_merged['Tienda_Act'].combine_first(df_merged['Tienda_Ant'])
        df_merged['Gerente'] = df_merged['Gerente_Act'].combine_first(df_merged['Gerente_Ant'])
        df_merged['Supervisor'] = df_merged['Supervisor_Act'].combine_first(df_merged['Supervisor_Ant'])
        
        for col in ['Ventas_Real_Act', 'Ppto_Real_Act', 'Transacciones_Real_Act', 'Ventas_Real_Ant', 'Ppto_Real_Ant', 'Transacciones_Real_Ant']:
            df_merged[col] = df_merged[col].fillna(0.0)
        
        # CÁLCULOS DEL GAP
        # GAP = Ventas - Presupuesto (Positivo = Superávit | Negativo = Faltante)
        df_merged['GAP_Ant'] = df_merged['Ventas_Real_Ant'] - df_merged['Ppto_Real_Ant']
        df_merged['GAP_Act'] = df_merged['Ventas_Real_Act'] - df_merged['Ppto_Real_Act']
        df_merged['Evolucion_GAP_$'] = df_merged['GAP_Act'] - df_merged['GAP_Ant']
        
        # Porcentajes de Cumplimiento y Variación
        df_merged['Cumpl_Act_%'] = (df_merged['Ventas_Real_Act'] / df_merged['Ppto_Real_Act'].replace(0, 1)) * 100
        df_merged['Var_Ventas_%'] = ((df_merged['Ventas_Real_Act'] - df_merged['Ventas_Real_Ant']) / df_merged['Ventas_Real_Ant'].replace(0, 1)) * 100

        # CLASIFICACIÓN DE ESCENARIOS LÓGICOS DETALLADOS
        def clasificar_escenario(row):
            g_ant = row['GAP_Ant']
            g_act = row['GAP_Act']
            diff = row['Evolucion_GAP_$']
            
            if g_ant < 0 and g_act >= 0:
                return "Pasa de Negativo a Positivo 🟢"
            elif g_ant >= 0 and g_act >= 0 and diff > 0:
                return "Amplió Superávit 🟢"
            elif g_ant >= 0 and g_act >= 0 and diff == 0:
                return "Mantuvo Superávit 🟢"
            elif g_ant < 0 and g_act < 0 and diff > 0:
                return "Recortó Faltante 🟢"
            elif g_ant < 0 and g_act < 0 and diff == 0:
                return "Mantuvo Faltante 🟡"
            else:
                return "Aumentó Faltante 🔴"

        df_merged['Escenario'] = df_merged.apply(clasificar_escenario, axis=1)

        # FILTROS SUPERIORES
        st.markdown("---")
        f1, f2, f3 = st.columns(3)
        with f1:
            gerentes = ["Todos"] + sorted([str(x) for x in df_merged['Gerente'].dropna().unique() if str(x) != 'nan'])
            sel_ger = st.selectbox("GERENTE / REGIONAL:", gerentes)
        with f2:
            supervisores = ["Todos"] + sorted([str(x) for x in df_merged['Supervisor'].dropna().unique() if str(x) != 'nan'])
            sel_sup = st.selectbox("SUPERVISOR:", supervisores)
        with f3:
            tiendas = ["Todas"] + sorted([str(x) for x in df_merged['Tienda'].dropna().unique() if str(x) != 'nan'])
            sel_tienda = st.selectbox("TIENDA / PUNTO:", tiendas)
            
        df_f = df_merged.copy()
        if sel_ger != "Todos": df_f = df_f[df_f['Gerente'] == sel_ger]
        if sel_sup != "Todos": df_f = df_f[df_f['Supervisor'] == sel_sup]
        if sel_tienda != "Todas": df_f = df_f[df_f['Tienda'] == sel_tienda]

        # KPIS GENERALES & NÚMERO TOTAL DE TIENDAS
        num_tiendas = len(df_f)
        v_act = df_f['Ventas_Real_Act'].sum()
        ppto_act = df_f['Ppto_Real_Act'].sum()
        gap_act = df_f['GAP_Act'].sum()
        gap_ant = df_f['GAP_Ant'].sum()
        evol_gap = df_f['Evolucion_GAP_$'].sum()
        cumpl_gen = (v_act / ppto_act * 100) if ppto_act > 0 else 0.0

        st.markdown("<br>", unsafe_allow_html=True)

        # FILA 1: TARJETAS KPIS CON CONTEO DE TIENDAS
        k1, k2, k3, k4 = st.columns([1, 1, 1.2, 1])
        
        with k1:
            st.markdown(f"""
            <div style="background-color: #F3F4F6; padding: 15px; border-radius: 10px; text-align: center;">
                <p style="margin:0; font-weight:bold; color:#374151;">TIENDAS EVALUADAS</p>
                <h2 style="margin:5px 0; color:#1E3A8A;">{num_tiendas} Tiendas</h2>
                <p style="margin:0; color:#6B7280;">Ventas: ${v_act:,.0f}</p>
            </div>
            """, unsafe_allow_html=True)

        with k2:
            st.markdown(f"""
            <div style="background-color: #F3F4F6; padding: 15px; border-radius: 10px; text-align: center;">
                <p style="margin:0; font-weight:bold; color:#374151;">GAP PRESUPUESTO ACTUAL</p>
                <h2 style="margin:5px 0; color:{'#16A34A' if gap_act>=0 else '#DC2626'};">${gap_act:,.0f}</h2>
                <p style="margin:0; color:#6B7280;">Semana Anterior: ${gap_ant:,.0f}</p>
            </div>
            """, unsafe_allow_html=True)

        with k3:
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = cumpl_gen,
                number = {'suffix': "%", 'valueformat': ".1f"},
                title = {'text': "CUMPLIMIENTO PPTO ACTUAL", 'font': {'size': 13}},
                gauge = {
                    'axis': {'range': [0, 120]},
                    'bar': {'color': "#16A34A" if cumpl_gen >= 100 else "#DC2626"},
                    'steps': [
                        {'range': [0, 85], 'color': "#FEE2E2"},
                        {'range': [85, 100], 'color': "#FEF3C7"},
                        {'range': [100, 120], 'color': "#DCFCE7"}
                    ]
                }
            ))
            fig_gauge.update_layout(height=160, margin=dict(l=10, r=10, t=25, b=10))
            st.plotly_chart(fig_gauge, use_container_width=True)

        with k4:
            st.markdown(f"""
            <div style="background-color: #F3F4F6; padding: 15px; border-radius: 10px; text-align: center;">
                <p style="margin:0; font-weight:bold; color:#374151;">EVOLUCIÓN DEL GAP</p>
                <h2 style="margin:5px 0; color:{'#16A34A' if evol_gap>=0 else '#DC2626'};">${evol_gap:+,.0f}</h2>
                <p style="margin:0; font-size:12px; font-weight:bold; color:{'#16A34A' if evol_gap>=0 else '#DC2626'};">
                    {'Mejoró Posición 🟢' if evol_gap>=0 else 'Aumentó Faltante 🔴'}
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # SECCIÓN: RESUMEN DE CONTEO DE TIENDAS POR ESCENARIOS
        st.markdown("### 🏬 DISTRIBUCIÓN DE TIENDAS POR ESCENARIO")
        
        conteo_escenarios = df_f['Escenario'].value_counts()
        
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("Pasa a Positivo", f"{conteo_escenarios.get('Pasa de Negativo a Positivo 🟢', 0)} tiendas")
        c2.metric("Amplió Superávit", f"{conteo_escenarios.get('Amplió Superávit 🟢', 0)} tiendas")
        c3.metric("Mantuvo Superávit", f"{conteo_escenarios.get('Mantuvo Superávit 🟢', 0)} tiendas")
        c4.metric("Recortó Faltante", f"{conteo_escenarios.get('Recortó Faltante 🟢', 0)} tiendas")
        c5.metric("Mantuvo Faltante", f"{conteo_escenarios.get('Mantuvo Faltante 🟡', 0)} tiendas")
        c6.metric("Aumentó Faltante", f"{conteo_escenarios.get('Aumentó Faltante 🔴', 0)} tiendas")

        st.markdown("---")

        # SECCIÓN: RESUMEN CONSOLIDADO POR GERENCIA / REGIONAL
        st.markdown("### 👔 RESUMEN CONSOLIDADO POR GERENCIA / REGIONAL")
        
        df_ger = df_f.groupby('Gerente').agg(
            Num_Tiendas=('Tienda', 'count'),
            Ventas_Ant=('Ventas_Real_Ant', 'sum'),
            Ventas_Act=('Ventas_Real_Act', 'sum'),
            Ppto_Act=('Ppto_Real_Act', 'sum'),
            GAP_Ant=('GAP_Ant', 'sum'),
            GAP_Act=('GAP_Act', 'sum'),
            Evolucion_GAP=('Evolucion_GAP_$', 'sum')
        ).reset_index()

        df_ger['Cumplimiento_%'] = (df_ger['Ventas_Act'] / df_ger['Ppto_Act'].replace(0, 1)) * 100
        df_ger['Var_Ventas_%'] = ((df_ger['Ventas_Act'] - df_ger['Ventas_Ant']) / df_ger['Ventas_Ant'].replace(0, 1)) * 100

        # Ordenar jerárquicamente por Cumplimiento %
        df_ger = df_ger.sort_values(by='Cumplimiento_%', ascending=False)

        st.dataframe(
            df_ger[[
                'Gerente', 'Num_Tiendas', 'Cumplimiento_%', 'Var_Ventas_%', 
                'Ventas_Act', 'Ppto_Act', 'GAP_Act', 'GAP_Ant', 'Evolucion_GAP'
            ]].style.format({
                'Num_Tiendas': '{:,.0f}',
                'Cumplimiento_%': '{:.1f}%',
                'Var_Ventas_%': '{:+.1f}%',
                'Ventas_Act': '${:,.0f}',
                'Ppto_Act': '${:,.0f}',
                'GAP_Act': '${:,.0f}',
                'GAP_Ant': '${:,.0f}',
                'Evolucion_GAP': '${:+,.0f}'
            }),
            use_container_width=True
        )

        st.markdown("---")

        # SECCIÓN: DETALLE DE TIENDAS ORDENADAS POR EFICIENCIA (% VAR Y CUMPLIMIENTO)
        st.markdown("### 📋 DETALLE DE TIENDAS (ORDENADO POR CUMPLIMIENTO %)")

        # Ordenar por Porcentaje de Cumplimiento (Eficiencia)
        tabla_tiendas = df_f.sort_values(by='Cumpl_Act_%', ascending=False)[[
            'Tienda', 'Gerente', 'Supervisor', 'Cumpl_Act_%', 'Var_Ventas_%',
            'Ventas_Real_Act', 'Ppto_Real_Act', 'GAP_Act', 'GAP_Ant', 'Evolucion_GAP_$', 'Escenario'
        ]].copy()

        tabla_tiendas.columns = [
            'Tienda', 'Gerente', 'Supervisor', 'Cumplimiento %', 'Var Ventas %',
            'Ventas Act', 'Ppto Act', 'GAP Act ($)', 'GAP Ant ($)', 'Evolución GAP ($)', 'Escenario'
        ]

        st.dataframe(
            tabla_tiendas.style.format({
                'Cumplimiento %': '{:.1f}%',
                'Var Ventas %': '{:+.1f}%',
                'Ventas Act': '${:,.0f}',
                'Ppto Act': '${:,.0f}',
                'GAP Act ($)': '${:,.0f}',
                'GAP Ant ($)': '${:,.0f}',
                'Evolución GAP ($)': '${:+,.0f}'
            }),
            use_container_width=True
        )

else:
    st.info("👈 Por favor sube el archivo ANALISIS GAP.xlsx en el menú lateral.")