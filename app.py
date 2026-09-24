import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Tablero Ejecutivo - Control de GAP y Ventas", 
    layout="wide"
)

# ESTILOS CSS PARA DISEÑO EJECUTIVO (TARJETAS BORDEADAS Y BOTONES)
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 14px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        text-align: center;
        margin-bottom: 10px;
    }
    .card-green { border-left: 6px solid #16A34A; border-top: 1px solid #E5E7EB; border-right: 1px solid #E5E7EB; border-bottom: 1px solid #E5E7EB; }
    .card-red { border-left: 6px solid #DC2626; border-top: 1px solid #E5E7EB; border-right: 1px solid #E5E7EB; border-bottom: 1px solid #E5E7EB; }
    .card-yellow { border-left: 6px solid #EAB308; border-top: 1px solid #E5E7EB; border-right: 1px solid #E5E7EB; border-bottom: 1px solid #E5E7EB; }
    .card-blue { border-left: 6px solid #2563EB; border-top: 1px solid #E5E7EB; border-right: 1px solid #E5E7EB; border-bottom: 1px solid #E5E7EB; }
    
    .card-title { font-size: 11px; font-weight: 700; color: #4B5563; text-transform: uppercase; margin-bottom: 4px; }
    .card-value { font-size: 20px; font-weight: 800; margin: 0; }
    .card-sub { font-size: 11px; color: #6B7280; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; color: #1E3A8A; font-weight: 800;'>TABLERO EJECUTIVO DE DESEMPEÑO Y CONTROL DE GAP</h2>", unsafe_allow_html=True)

# 1. FUNCIÓN DE LIMPIEZA
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
        
        dfs.append(df)
        
    if dfs:
        df_tot = pd.concat(dfs, ignore_index=True)
        if not df_bd.empty:
            cols_bd = ['Tienda_Clean', 'Gerente', 'Supervisor', 'Ciudad', 'Segmento', 'Comparable ', 'Pareto']
            cols_bd = [c for c in cols_bd if c in df_bd.columns]
            df_tot = pd.merge(df_tot, df_bd[cols_bd], on='Tienda_Clean', how='left')
        return df_tot, hojas
    return pd.DataFrame(), []

# Cargar Excel
st.sidebar.header("📁 Cargar Datos")
uploaded_file = st.sidebar.file_uploader("Sube ANALISIS GAP.xlsx", type=['xlsx'])

if uploaded_file:
    df_tot, lista_ciclos = cargar_datos(uploaded_file)
    
    if len(lista_ciclos) >= 2:
        c_act = st.sidebar.selectbox("Semana / Corte Actual:", lista_ciclos, index=len(lista_ciclos)-1)
        c_ant = st.sidebar.selectbox("Semana / Corte Anterior:", lista_ciclos, index=max(0, len(lista_ciclos)-2))
        
        df_act = df_tot[df_tot['Ciclo'] == c_act].copy()
        df_ant = df_tot[df_tot['Ciclo'] == c_ant].copy()
        
        df_merged = pd.merge(
            df_act[['Tienda_Clean', 'Tienda', 'Gerente', 'Supervisor', 'Ciudad', 'Segmento', 'Ventas_Real', 'Ppto_Real']],
            df_ant[['Tienda_Clean', 'Tienda', 'Gerente', 'Supervisor', 'Ventas_Real', 'Ppto_Real']],
            on='Tienda_Clean',
            suffixes=('_Act', '_Ant'),
            how='outer'
        )
        
        df_merged['Tienda'] = df_merged['Tienda_Act'].combine_first(df_merged['Tienda_Ant'])
        df_merged['Gerente'] = df_merged['Gerente_Act'].combine_first(df_merged['Gerente_Ant'])
        df_merged['Supervisor'] = df_merged['Supervisor_Act'].combine_first(df_merged['Supervisor_Ant'])
        
        for col in ['Ventas_Real_Act', 'Ppto_Real_Act', 'Ventas_Real_Ant', 'Ppto_Real_Ant']:
            df_merged[col] = df_merged[col].fillna(0.0)
            
        # GAP = Ventas - Presupuesto (GAP > 0 Superávit | GAP < 0 Faltante)
        df_merged['GAP_Ant'] = df_merged['Ventas_Real_Ant'] - df_merged['Ppto_Real_Ant']
        df_merged['GAP_Act'] = df_merged['Ventas_Real_Act'] - df_merged['Ppto_Real_Act']
        df_merged['Evolucion_GAP_$'] = df_merged['GAP_Act'] - df_merged['GAP_Ant']
        
        df_merged['Cumpl_Act_%'] = (df_merged['Ventas_Real_Act'] / df_merged['Ppto_Real_Act'].replace(0, 1)) * 100
        df_merged['Var_Ventas_%'] = ((df_merged['Ventas_Real_Act'] - df_merged['Ventas_Real_Ant']) / df_merged['Ventas_Real_Ant'].replace(0, 1)) * 100

        def clasificar_escenario(row):
            g_ant = row['GAP_Ant']
            g_act = row['GAP_Act']
            diff = row['Evolucion_GAP_$']
            
            if g_ant < 0 and g_act >= 0:
                return "Pasa a Positivo 🟢"
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
            sel_ger = st.selectbox("GERENCIA / REGIONAL:", gerentes)
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

        # KPIS EJECUTIVOS TOP
        num_tiendas = len(df_f[df_f['Ventas_Real_Act'] > 0]) if sel_ger == "Todos" and sel_sup == "Todos" and sel_tienda == "Todas" else len(df_f)
        v_act = df_f['Ventas_Real_Act'].sum()
        ppto_act = df_f['Ppto_Real_Act'].sum()
        gap_act = df_f['GAP_Act'].sum()
        gap_ant = df_f['GAP_Ant'].sum()
        evol_gap = df_f['Evolucion_GAP_$'].sum()
        cumpl_gen = (v_act / ppto_act * 100) if ppto_act > 0 else 0.0

        st.markdown("<br>", unsafe_allow_html=True)

        # TARJETAS EJECUTIVAS PRINCIPALES
        k1, k2, k3, k4 = st.columns([1, 1, 1.2, 1])
        
        with k1:
            st.markdown(f"""
            <div class="metric-card card-blue">
                <div class="card-title">TIENDAS CON ACTIVIDAD</div>
                <div class="card-value" style="color:#2563EB;">{num_tiendas}</div>
                <div class="card-sub">Venta Total: ${v_act:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

        with k2:
            color_gap = "#16A34A" if gap_act >= 0 else "#DC2626"
            st.markdown(f"""
            <div class="metric-card {'card-green' if gap_act>=0 else 'card-red'}">
                <div class="card-title">GAP PPTO ACTUAL</div>
                <div class="card-value" style="color:{color_gap};">${gap_act:,.0f}</div>
                <div class="card-sub">GAP Anterior: ${gap_ant:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

        with k3:
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = cumpl_gen,
                number = {'suffix': "%", 'valueformat': ".1f"},
                title = {'text': "CUMPLIMIENTO CUMPLE PPTO", 'font': {'size': 12, 'color': '#374151'}},
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
            fig_gauge.update_layout(height=140, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig_gauge, use_container_width=True)

        with k4:
            color_evol = "#16A34A" if evol_gap >= 0 else "#DC2626"
            st.markdown(f"""
            <div class="metric-card {'card-green' if evol_gap>=0 else 'card-red'}">
                <div class="card-title">EVOLUCIÓN DEL GAP ($)</div>
                <div class="card-value" style="color:{color_evol};">${evol_gap:+,.0f}</div>
                <div class="card-sub" style="font-weight:bold; color:{color_evol};">
                    {'Avanzó Posición 🟢' if evol_gap>=0 else 'Aumentó Faltante 🔴'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # DISTRIBUCIÓN DE ESCENARIOS EN TARJETAS BORDEADAS
        conteo = df_f['Escenario'].value_counts()
        
        e1, e2, e3, e4, e5, e6 = st.columns(6)
        
        with e1:
            st.markdown(f"""<div class="metric-card card-green"><div class="card-title">Pasa a Positivo</div><div class="card-value" style="color:#16A34A;">{conteo.get('Pasa de Negativo a Positivo 🟢', 0)}</div><div class="card-sub">Tiendas</div></div>""", unsafe_allow_html=True)
        with e2:
            st.markdown(f"""<div class="metric-card card-green"><div class="card-title">Amplió Superávit</div><div class="card-value" style="color:#16A34A;">{conteo.get('Amplió Superávit 🟢', 0)}</div><div class="card-sub">Tiendas</div></div>""", unsafe_allow_html=True)
        with e3:
            st.markdown(f"""<div class="metric-card card-green"><div class="card-title">Mantuvo Superávit</div><div class="card-value" style="color:#16A34A;">{conteo.get('Mantuvo Superávit 🟢', 0)}</div><div class="card-sub">Tiendas</div></div>""", unsafe_allow_html=True)
        with e4:
            st.markdown(f"""<div class="metric-card card-green"><div class="card-title">Recortó Faltante</div><div class="card-value" style="color:#16A34A;">{conteo.get('Recortó Faltante 🟢', 0)}</div><div class="card-sub">Tiendas</div></div>""", unsafe_allow_html=True)
        with e5:
            st.markdown(f"""<div class="metric-card card-yellow"><div class="card-title">Mantuvo Faltante</div><div class="card-value" style="color:#EAB308;">{conteo.get('Mantuvo Faltante 🟡', 0)}</div><div class="card-sub">Tiendas</div></div>""", unsafe_allow_html=True)
        with e6:
            st.markdown(f"""<div class="metric-card card-red"><div class="card-title">Aumentó Faltante</div><div class="card-value" style="color:#DC2626;">{conteo.get('Aumentó Faltante 🔴', 0)}</div><div class="card-sub">Tiendas</div></div>""", unsafe_allow_html=True)

        st.markdown("---")

        # NAVEGACIÓN EN PESTAÑAS (TABS)
        tab_gerencial, tab_tiendas = st.tabs(["👔 Visión Gerencial & Supervisores", "🏬 Análisis Detallado por Tienda"])

        # PESTAÑA 1: VISIÓN GERENCIAL Y SUPERVISORES
        with tab_gerencial:
            st.markdown("### 📊 RESUMEN CONSOLIDADO POR GERENCIA / REGIONAL")
            
            # Filtramos solo las gerencias con actividad real
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

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 👔 COMPARATIVO POR SUPERVISOR")
            
            df_sup = df_f.groupby(['Supervisor', 'Gerente']).agg(
                Ventas_Act=('Ventas_Real_Act', 'sum'),
                Ppto_Act=('Ppto_Real_Act', 'sum'),
                Evolucion_GAP=('Evolucion_GAP_$', 'sum')
            ).reset_index()
            df_sup['Cumplimiento_%'] = (df_sup['Ventas_Act'] / df_sup['Ppto_Act'].replace(0, 1)) * 100
            df_sup = df_sup.sort_values(by='Cumplimiento_%', ascending=True)

            fig_sup = px.bar(
                df_sup,
                y='Supervisor', x='Cumplimiento_%',
                color='Cumplimiento_%',
                color_continuous_scale=['#DC2626', '#FEF3C7', '#16A34A'],
                orientation='h',
                title="CUMPLIMIENTO DE PRESUPUESTO (%) POR SUPERVISOR",
                text_auto='.1f%'
            )
            fig_sup.update_layout(height=max(350, len(df_sup) * 30))
            st.plotly_chart(fig_sup, use_container_width=True)

        # PESTAÑA 2: ANÁLISIS DETALLADO POR TIENDA Y GRÁFICO
        with tab_tiendas:
            st.markdown("### 📈 GRÁFICA DE EVOLUCIÓN DEL GAP POR TIENDA")
            
            c_graf, c_sem = st.columns([3, 1])

            with c_sem:
                filtro_sem = st.radio(
                    "Filtrar por resultado:",
                    ["🟢 Solo Positivos / Avanzó", "🔴 Solo Negativos / Faltante", "Todas las Tiendas"],
                    index=2
                )
                
                df_graf = df_f.copy()
                if "Positivos" in filtro_sem:
                    df_graf = df_graf[df_graf['Evolucion_GAP_$'] >= 0]
                elif "Negativos" in filtro_sem:
                    df_graf = df_graf[df_graf['Evolucion_GAP_$'] < 0]

            with c_graf:
                fig_bar = px.bar(
                    df_graf.sort_values(by='Evolucion_GAP_$', ascending=True),
                    y='Tienda', x='Evolucion_GAP_$',
                    color='Escenario',
                    color_discrete_map={
                        'Pasa de Negativo a Positivo 🟢': '#15803D',
                        'Amplió Superávit 🟢': '#16A34A',
                        'Mantuvo Superávit 🟢': '#22C55E',
                        'Recortó Faltante 🟢': '#4ADE80',
                        'Mantuvo Faltante 🟡': '#EAB308',
                        'Aumentó Faltante 🔴': '#DC2626'
                    },
                    orientation='h',
                    title="DIFERENCIA DE GAP ($) - SEMANA ACTUAL VS ANTERIOR"
                )
                fig_bar.update_layout(height=max(400, len(df_graf) * 25))
                st.plotly_chart(fig_bar, use_container_width=True)

            st.markdown("---")
            st.markdown("### 📋 TABLA DETALLADA POR TIENDA (PRIORIZANDO EFICIENCIA %)")

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
    st.info("👈 Por favor sube el archivo ANALISIS GAP.xlsx en el menú lateral para activar el tablero.")