import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Informe Gerencial GAP - Juan Valdez", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 PALETA DE COLORES CORPORATIVA Y ESTILOS CSS PREMIUM JUAN VALDEZ
st.markdown("""
<style>
    /* Estilo General */
    .stApp {
        background-color: #F8FAFC;
    }
    
    /* Header Principal */
    .jv-header {
        background: linear-gradient(135deg, #7A0016 0%, #A20021 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(122, 0, 22, 0.25);
    }
    .jv-header h1 {
        margin: 0;
        font-size: 26px;
        font-weight: 800;
        letter-spacing: 0.5px;
        color: #FFFFFF;
    }
    .jv-header p {
        margin: 5px 0 0 0;
        font-size: 13px;
        color: #F1F5F9;
        opacity: 0.9;
    }

    /* Cajas de Filtro Switch Rojo Claro Corporativo */
    .filter-card-red {
        background-color: #FEF2F2;
        border: 1px solid #FCA5A5;
        border-left: 5px solid #DC2626;
        border-radius: 10px;
        padding: 10px 16px;
        margin-bottom: 15px;
        box-shadow: 0 2px 6px rgba(220, 38, 38, 0.06);
    }
    .filter-card-title {
        font-weight: 800;
        font-size: 13px;
        color: #991B1B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 0 0 4px 0;
    }

    /* Personalización del Switch de Streamlit a Rojo Corporativo */
    div[data-testid="stCheckbox"] > label > div[role="checkbox"][aria-checked="true"] {
        background-color: #DC2626 !important;
    }

    /* Tarjetas de KPI Principales */
    .metric-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
        text-align: center;
        height: 100%;
        transition: transform 0.2s ease;
    }
    .card-blue { border-left: 6px solid #2563EB; }
    .card-red { border-left: 6px solid #DC2626; }
    .card-green { border-left: 6px solid #16A34A; }
    .card-yellow { border-left: 6px solid #EAB308; }
    .card-jv { border-left: 6px solid #A20021; }
    
    .card-title {
        font-size: 11px;
        font-weight: 800;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .card-value {
        font-size: 22px;
        font-weight: 800;
        margin: 2px 0;
    }
    .card-sub {
        font-size: 11px;
        color: #64748B;
        font-weight: 500;
    }

    /* Tarjetas de Gerentes */
    .gerente-box {
        background-color: #FFFFFF;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        padding: 18px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
    .gerente-title {
        font-size: 16px;
        font-weight: 800;
        color: #7A0016;
        border-bottom: 2px solid #F1F5F9;
        padding-bottom: 8px;
        margin-bottom: 12px;
    }
    
    /* Pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #FFFFFF;
        border-radius: 8px;
        padding: 0px 20px;
        font-weight: 700;
        color: #475569;
        border: 1px solid #E2E8F0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #A20021 !important;
        color: #FFFFFF !important;
        border-color: #A20021 !important;
    }
</style>
""", unsafe_allow_html=True)

# CABECERA INSTITUCIONAL
st.markdown("""
<div class="jv-header">
    <h1>INFORME GERENCIAL GAP VS PRESUPUESTO DE VENTAS</h1>
    <p>Control de Desempeño Comercial y Evolución de Brechas</p>
</div>
""", unsafe_allow_html=True)

# 1. FUNCIÓN DE LIMPIEZA MONETARIA
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
            cols_bd = ['Tienda_Clean', 'Gerente', 'Supervisor', 'Ciudad', 'Segmento', 'Comparable ', 'Comparable', 'Pareto']
            cols_bd = [c for c in cols_bd if c in df_bd.columns]
            df_tot = pd.merge(df_tot, df_bd[cols_bd], on='Tienda_Clean', how='left')
        return df_tot, hojas
    return pd.DataFrame(), []

# CARGA DE DATOS
st.sidebar.header("📁 Configuración de Datos")
uploaded_file = st.sidebar.file_uploader("Cargar ANALISIS GAP.xlsx", type=['xlsx'])

if uploaded_file:
    df_tot, lista_ciclos = cargar_datos(uploaded_file)
    
    if len(lista_ciclos) >= 2:
        c_act = st.sidebar.selectbox("Semana Actual / Corte:", lista_ciclos, index=len(lista_ciclos)-1)
        c_ant = st.sidebar.selectbox("Semana Anterior / Corte:", lista_ciclos, index=max(0, len(lista_ciclos)-2))
        
        df_act = df_tot[df_tot['Ciclo'] == c_act].copy()
        df_ant = df_tot[df_tot['Ciclo'] == c_ant].copy()
        
        # Identificar columnas relevantes
        cols_act = ['Tienda_Clean', 'Tienda', 'Gerente', 'Supervisor', 'Ciudad', 'Segmento', 'Ventas_Real', 'Ppto_Real']
        for col_extra in ['Pareto', 'Comparable ', 'Comparable']:
            if col_extra in df_act.columns and col_extra not in cols_act:
                cols_act.append(col_extra)
                
        cols_ant = ['Tienda_Clean', 'Tienda', 'Gerente', 'Supervisor', 'Ventas_Real', 'Ppto_Real']
        for col_extra in ['Pareto', 'Comparable ', 'Comparable']:
            if col_extra in df_ant.columns and col_extra not in cols_ant:
                cols_ant.append(col_extra)

        df_merged = pd.merge(
            df_act[cols_act],
            df_ant[cols_ant],
            on='Tienda_Clean',
            suffixes=('_Act', '_Ant'),
            how='outer'
        )
        
        df_merged['Tienda'] = df_merged['Tienda_Act'].combine_first(df_merged['Tienda_Ant'])
        df_merged['Gerente'] = df_merged['Gerente_Act'].combine_first(df_merged['Gerente_Ant'])
        df_merged['Supervisor'] = df_merged['Supervisor_Act'].combine_first(df_merged['Supervisor_Ant'])
        
        # Unificar Columna Pareto
        if 'Pareto_Act' in df_merged.columns and 'Pareto_Ant' in df_merged.columns:
            df_merged['Pareto'] = df_merged['Pareto_Act'].combine_first(df_merged['Pareto_Ant'])
        elif 'Pareto_Act' in df_merged.columns:
            df_merged['Pareto'] = df_merged['Pareto_Act']
        elif 'Pareto' not in df_merged.columns:
            df_merged['Pareto'] = 'NO'

        # Unificar Columna Comparable
        comp_col = None
        for c in ['Comparable _Act', 'Comparable_Act', 'Comparable ']:
            if c in df_merged.columns:
                comp_col = c
                break
        if comp_col:
            df_merged['Comparable_Val'] = df_merged[comp_col]
        else:
            df_merged['Comparable_Val'] = 'NO'
            
        for col in ['Ventas_Real_Act', 'Ppto_Real_Act', 'Ventas_Real_Ant', 'Ppto_Real_Ant']:
            df_merged[col] = df_merged[col].fillna(0.0)
            
        # CÁLCULO DE GAP = Ventas - Presupuesto
        df_merged['GAP_Ant'] = df_merged['Ventas_Real_Ant'] - df_merged['Ppto_Real_Ant']
        df_merged['GAP_Act'] = df_merged['Ventas_Real_Act'] - df_merged['Ppto_Real_Act']
        df_merged['Evolucion_GAP_$'] = df_merged['GAP_Act'] - df_merged['GAP_Ant']
        
        df_merged['Cumpl_Act_%'] = (df_merged['Ventas_Real_Act'] / df_merged['Ppto_Real_Act'].replace(0, 1)) * 100

        # LÓGICA DE ESCENARIOS
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

        # ----------------------------------------------------------------------
        # FILTROS COMBINADOS: PARETO Y COMPARABLES (ROJO CLARO CORPORATIVO)
        # ----------------------------------------------------------------------
        f_col1, f_col2 = st.columns(2)
        
        with f_col1:
            st.markdown('<div class="filter-card-red"><div class="filter-card-title">Filtro Tiendas Pareto</div>', unsafe_allow_html=True)
            solo_pareto = st.toggle("Solo Tiendas Pareto", value=False, key="sw_pareto")
            st.markdown('</div>', unsafe_allow_html=True)

        with f_col2:
            st.markdown('<div class="filter-card-red"><div class="filter-card-title">Filtro Tiendas Comparables</div>', unsafe_allow_html=True)
            solo_comparable = st.toggle("Solo Tiendas Comparables", value=False, key="sw_comp")
            st.markdown('</div>', unsafe_allow_html=True)

        # Aplicar lógica de filtrado cruzado dinámico
        df_base = df_merged.copy()
        patron_valid = 'SI|S|1|PARETO|TRUE|COMPARABLE'

        if solo_pareto:
            df_base = df_base[df_base['Pareto'].astype(str).str.upper().str.contains(patron_valid, regex=True, na=False)]
            
        if solo_comparable:
            df_base = df_base[df_base['Comparable_Val'].astype(str).str.upper().str.contains(patron_valid, regex=True, na=False)]

        # RENDERIZADO DE MÉRITO DE TARJETAS SUPERIORES
        def render_kpi_block(df_scope, key_suffix="main"):
            df_activas = df_scope[df_scope['Ventas_Real_Act'] > 0]
            num_tiendas = len(df_activas)
            v_act = df_scope['Ventas_Real_Act'].sum()
            ppto_act = df_scope['Ppto_Real_Act'].sum()
            gap_act = df_scope['GAP_Act'].sum()
            gap_ant = df_scope['GAP_Ant'].sum()
            evol_gap = df_scope['Evolucion_GAP_$'].sum()
            cumpl_gen = (v_act / ppto_act * 100) if ppto_act > 0 else 0.0

            k1, k2, k3, k4 = st.columns([1, 1, 1.2, 1])
            with k1:
                st.markdown(f"""
                <div class="metric-card card-blue">
                    <div class="card-title">TIENDAS EN EVALUACIÓN</div>
                    <div class="card-value" style="color:#2563EB;">{num_tiendas}</div>
                    <div class="card-sub">Ventas: ${v_act:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            with k2:
                col_g = "#16A34A" if gap_act >= 0 else "#DC2626"
                st.markdown(f"""
                <div class="metric-card {'card-green' if gap_act>=0 else 'card-red'}">
                    <div class="card-title">GAP PPTO ACTUAL</div>
                    <div class="card-value" style="color:{col_g};">${gap_act:,.0f}</div>
                    <div class="card-sub">GAP Anterior: ${gap_ant:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            with k3:
                fig_g = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = cumpl_gen,
                    number = {'suffix': "%", 'valueformat': ".1f"},
                    gauge = {
                        'axis': {'range': [0, 120]},
                        'bar': {'color': "#16A34A" if cumpl_gen >= 100 else "#A20021"},
                        'steps': [
                            {'range': [0, 85], 'color': "#FEE2E2"},
                            {'range': [85, 100], 'color': "#FEF3C7"},
                            {'range': [100, 120], 'color': "#DCFCE7"}
                        ]
                    }
                ))
                fig_g.update_layout(height=130, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig_g, use_container_width=True, key=f"gauge_{key_suffix}")
            with k4:
                col_e = "#16A34A" if evol_gap >= 0 else "#DC2626"
                st.markdown(f"""
                <div class="metric-card {'card-green' if evol_gap>=0 else 'card-red'}">
                    <div class="card-title">EVOLUCIÓN DEL GAP ($)</div>
                    <div class="card-value" style="color:{col_e};">${evol_gap:+,.0f}</div>
                    <div class="card-sub" style="font-weight:bold; color:{col_e};">
                        {'Avanzó Posición 🟢' if evol_gap>=0 else 'Aumentó Faltante 🔴'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<h4 style='text-align:left; color:#334155; font-size:14px; font-weight:800;'>🏬 ESTADO DE TIENDAS POR ESCENARIO</h4>", unsafe_allow_html=True)
            
            conteo = df_activas['Escenario'].value_counts()
            e1, e2, e3, e4, e5, e6 = st.columns(6)
            with e1:
                st.markdown(f"""<div class="metric-card card-green"><div class="card-title">PASA A POSITIVO</div><div class="card-value" style="color:#16A34A;">{conteo.get('Pasa de Negativo a Positivo 🟢', 0)}</div><div class="card-sub">Tiendas</div></div>""", unsafe_allow_html=True)
            with e2:
                st.markdown(f"""<div class="metric-card card-green"><div class="card-title">AMPLIÓ SUPERÁVIT</div><div class="card-value" style="color:#16A34A;">{conteo.get('Amplió Superávit 🟢', 0)}</div><div class="card-sub">Tiendas</div></div>""", unsafe_allow_html=True)
            with e3:
                st.markdown(f"""<div class="metric-card card-green"><div class="card-title">MANTUVO SUPERÁVIT</div><div class="card-value" style="color:#16A34A;">{conteo.get('Mantuvo Superávit 🟢', 0)}</div><div class="card-sub">Tiendas</div></div>""", unsafe_allow_html=True)
            with e4:
                st.markdown(f"""<div class="metric-card card-green"><div class="card-title">RECORTÓ FALTANTE</div><div class="card-value" style="color:#16A34A;">{conteo.get('Recortó Faltante 🟢', 0)}</div><div class="card-sub">Tiendas</div></div>""", unsafe_allow_html=True)
            with e5:
                st.markdown(f"""<div class="metric-card card-yellow"><div class="card-title">MANTUVO FALTANTE</div><div class="card-value" style="color:#EAB308;">{conteo.get('Mantuvo Faltante 🟡', 0)}</div><div class="card-sub">Tiendas</div></div>""", unsafe_allow_html=True)
            with e6:
                st.markdown(f"""<div class="metric-card card-red"><div class="card-title">AUMENTÓ FALTANTE</div><div class="card-value" style="color:#DC2626;">{conteo.get('Aumentó Faltante 🔴', 0)}</div><div class="card-sub">Tiendas</div></div>""", unsafe_allow_html=True)

        # ESTRUCTURA EN 2 PESTAÑAS PRINCIPALES
        tab1, tab2 = st.tabs(["📊 Informe Gerencial GAP", "🔍 Análisis por Gerencia"])

        # ==============================================================================
        # PESTAÑA 1: INFORME GERENCIAL GAP (RESUMEN GENERAL + CADA GERENTE)
        # ==============================================================================
        with tab1:
            st.markdown("### 🏢 RESUMEN GENERAL DE LA COMPAÑÍA")
            render_kpi_block(df_base, key_suffix="global")
            
            st.markdown("---")
            st.markdown("### 👔 DETALLE CONSOLIDADO POR GERENTE REGIONAL")
            
            lista_gerentes = sorted([g for g in df_base['Gerente'].dropna().unique() if str(g) != 'nan'])
            
            for idx, ger in enumerate(lista_gerentes):
                df_g = df_base[df_base['Gerente'] == ger]
                if df_g['Ventas_Real_Act'].sum() > 0 or df_g['Ppto_Real_Act'].sum() > 0:
                    with st.container():
                        st.markdown(f"""
                        <div class="gerente-box">
                            <div class="gerente-title">📍 GERENCIA REGIONAL: {str(ger).upper()}</div>
                        """, unsafe_allow_html=True)
                        
                        render_kpi_block(df_g, key_suffix=f"ger_{idx}")
                        
                        st.markdown("</div>", unsafe_allow_html=True)

        # ==============================================================================
        # PESTAÑA 2: ANÁLISIS POR GERENCIA (INTERACTIVA SUPERVISOR Y TIENDAS)
        # ==============================================================================
        with tab2:
            st.markdown("### 🎯 FILTROS DE ANÁLISIS DETALLADO")
            
            f1, f2 = st.columns(2)
            with f1:
                gerentes_sel = ["Todos"] + sorted([g for g in df_base['Gerente'].dropna().unique() if str(g) != 'nan'])
                s_ger = st.selectbox("Seleccionar Gerente:", gerentes_sel, key="tab2_ger")
            with f2:
                df_temp = df_base if s_ger == "Todos" else df_base[df_base['Gerente'] == s_ger]
                sups_sel = ["Todos"] + sorted([s for s in df_temp['Supervisor'].dropna().unique() if str(s) != 'nan'])
                s_sup = st.selectbox("Seleccionar Supervisor:", sups_sel, key="tab2_sup")

            df_tab2 = df_base.copy()
            if s_ger != "Todos": df_tab2 = df_tab2[df_tab2['Gerente'] == s_ger]
            if s_sup != "Todos": df_tab2 = df_tab2[df_tab2['Supervisor'] == s_sup]

            st.markdown("---")
            st.markdown(f"### 📈 INDICADORES CLAVE DE GESTIÓN ({s_sup if s_sup != 'Todos' else (s_ger if s_ger != 'Todos' else 'GLOBAL')})")
            render_kpi_block(df_tab2, key_suffix="tab2_kpis")

            st.markdown("---")
            st.markdown("### 👔 CUMPLIMIENTO INTERACTIVO POR SUPERVISOR")
            
            df_sup_agg = df_tab2.groupby(['Supervisor', 'Gerente']).agg(
                Ventas_Act=('Ventas_Real_Act', 'sum'),
                Ppto_Act=('Ppto_Real_Act', 'sum'),
                Evolucion_GAP=('Evolucion_GAP_$', 'sum')
            ).reset_index()
            
            df_sup_agg['Cumpl_ %'] = (df_sup_agg['Ventas_Act'] / df_sup_agg['Ppto_Act'].replace(0, 1)) * 100
            df_sup_agg = df_sup_agg.sort_values(by='Cumpl_ %', ascending=True)

            fig_sup = px.bar(
                df_sup_agg,
                y='Supervisor', x='Cumpl_ %',
                color='Cumpl_ %',
                color_continuous_scale=['#A20021', '#FEF3C7', '#16A34A'],
                orientation='h',
                title="CUMPLIMIENTO DE PRESUPUESTO (%) POR SUPERVISOR",
                text_auto='.1f%'
            )
            fig_sup.update_layout(height=max(350, len(df_sup_agg) * 32))
            st.plotly_chart(fig_sup, use_container_width=True, key="fig_sup_chart")

            st.markdown("---")
            st.markdown("### 🏬 EVOLUCIÓN DEL GAP POR TIENDA (BARRAS HORIZONTALES)")
            
            fig_tiendas = px.bar(
                df_tab2.sort_values(by='Evolucion_GAP_$', ascending=True),
                y='Tienda', x='Evolucion_GAP_$',
                color='Escenario',
                color_discrete_map={
                    'Pasa de Negativo a Positivo 🟢': '#15803D',
                    'Amplió Superávit 🟢': '#16A34A',
                    'Mantuvo Superávit 🟢': '#22C55E',
                    'Recortó Faltante 🟢': '#4ADE80',
                    'Mantuvo Faltante 🟡': '#EAB308',
                    'Aumentó Faltante 🔴': '#A20021'
                },
                orientation='h',
                title="VARIACIÓN DE GAP DE PPTO ($) POR TIENDA"
            )
            fig_tiendas.update_layout(height=max(400, len(df_tab2) * 22))
            st.plotly_chart(fig_tiendas, use_container_width=True, key="fig_tiendas_chart")

else:
    st.info("👈 Por favor sube el archivo ANALISIS GAP.xlsx en el menú lateral para desplegar el informe gerencial.")