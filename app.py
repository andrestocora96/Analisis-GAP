import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Informe Gerencial GAP - Juan Valdez", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 PALETA WARM CORPORATE / BEIGE BEIGE PREMIUM JUAN VALDEZ
st.markdown("""
<style>
    /* Fondo General Crema / Beige Cálido */
    .stApp {
        background-color: #F7F4EF !important;
    }
    
    /* Header Principal Tinto Ejecutivo */
    .jv-header {
        background: linear-gradient(135deg, #58000E 0%, #8C0017 100%);
        padding: 22px;
        border-radius: 14px;
        color: white;
        text-align: center;
        margin-bottom: 22px;
        box-shadow: 0 6px 16px rgba(88, 0, 14, 0.2);
    }
    .jv-header h1 { margin: 0; font-size: 26px; font-weight: 800; color: #FFFFFF; letter-spacing: 0.5px; }
    .jv-header p { margin: 6px 0 0 0; font-size: 13px; color: #F7EBE8; opacity: 0.95; }

    /* Tarjetas de Filtro Switch */
    .filter-card-red {
        background-color: #FCE8E8;
        border: 1px solid #F87171;
        border-left: 5px solid #991B1B;
        border-radius: 10px;
        padding: 10px 16px;
        margin-bottom: 15px;
        box-shadow: 0 2px 6px rgba(153, 27, 27, 0.08);
    }
    .filter-card-title {
        font-weight: 800;
        font-size: 12px;
        color: #7F1D1D;
        text-transform: uppercase;
        margin: 0 0 4px 0;
    }

    div[data-testid="stCheckbox"] > label > div[role="checkbox"][aria-checked="true"] {
        background-color: #8C0017 !important;
    }

    /* Tarjetas KPI sobre Fondo Beige */
    .metric-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 12px rgba(90, 80, 70, 0.08);
        border: 1px solid #EFE8DE;
        text-align: center;
        height: 100%;
    }
    .card-blue { border-left: 5px solid #2563EB; }
    .card-red { border-left: 5px solid #DC2626; }
    .card-green { border-left: 5px solid #16A34A; }
    .card-yellow { border-left: 5px solid #D97706; }
    .card-purple { border-left: 5px solid #7C3AED; }
    .card-amber { border-left: 5px solid #B45309; }
    
    .card-title {
        font-size: 10px;
        font-weight: 800;
        color: #524B42;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .card-value { font-size: 20px; font-weight: 800; margin: 2px 0; }
    .card-sub { font-size: 10px; color: #786F66; font-weight: 600; }

    /* Cajas para Gerentes con Sombra Suave Warm */
    .gerente-box {
        background-color: #FFFFFF;
        border-radius: 14px;
        border: 1px solid #EBE3D5;
        padding: 20px;
        margin-bottom: 22px;
        box-shadow: 0 4px 14px rgba(80, 70, 60, 0.06);
    }
    .gerente-title {
        font-size: 15px;
        font-weight: 800;
        color: #6B0011;
        border-bottom: 2px solid #F4EFE6;
        padding-bottom: 8px;
        margin-bottom: 14px;
    }
    
    /* Estilo de Pestañas Elegantes */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        background-color: #EFE8DE;
        border-radius: 8px;
        padding: 0px 22px;
        font-weight: 700;
        color: #524B42;
        border: 1px solid #E5DCCE;
    }
    .stTabs [aria-selected="true"] {
        background-color: #6B0011 !important;
        color: #FFFFFF !important;
        border-color: #6B0011 !important;
    }
</style>
""", unsafe_allow_html=True)

# CABECERA
st.markdown("""
<div class="jv-header">
    <h1>INFORME GERENCIAL GAP VS PRESUPUESTO & ANÁLISIS DE TRÁFICO (AA)</h1>
    <p>Control Integrado de Ventas, Presupuesto, GAP Transacciones Interanual y Meta de Ticket Promedio</p>
</div>
""", unsafe_allow_html=True)

def limpiar_monto(val):
    if pd.isna(val): return 0.0
    s = str(val).replace('$', '').replace(',', '').strip()
    if 'M' in s:
        s = s.replace('M', '')
        try: return float(s) * 1_000_000.0
        except: return 0.0
    try: return float(s)
    except: return 0.0

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
        
        col_v_aa = [c for c in df.columns if 'Venta' in c and ('AA' in c or 'Ant' in c or 'Anterior' in c)]
        df['Ventas_AA'] = df[col_v_aa[0]].apply(limpiar_monto) if col_v_aa else 0.0

        col_tx_act = [c for c in df.columns if ('Transacc' in c or 'Tx' in c) and ('AA' not in c and 'Ant' not in c)]
        col_tx_aa = [c for c in df.columns if ('Transacc' in c or 'Tx' in c) and ('AA' in c or 'Ant' in c or 'Anterior' in c)]
        
        df['Tx_Real'] = pd.to_numeric(df[col_tx_act[0]], errors='coerce').fillna(0) if col_tx_act else 0.0
        df['Tx_AA'] = pd.to_numeric(df[col_tx_aa[0]], errors='coerce').fillna(0) if col_tx_aa else 0.0
            
        dfs.append(df)
        
    if dfs:
        df_tot = pd.concat(dfs, ignore_index=True)
        if not df_bd.empty:
            cols_bd = ['Tienda_Clean', 'Gerente', 'Supervisor', 'Ciudad', 'Segmento', 'Comparable ', 'Comparable', 'Pareto']
            cols_bd = [c for c in cols_bd if c in df_bd.columns]
            df_tot = pd.merge(df_tot, df_bd[cols_bd], on='Tienda_Clean', how='left')
        return df_tot, hojas
    return pd.DataFrame(), []

st.sidebar.header("📁 Configuración de Datos")
uploaded_file = st.sidebar.file_uploader("Cargar ANALISIS GAP.xlsx", type=['xlsx'])

# PARÁMETRO CONFIGURABLE DE META TICKET PROMEDIO
st.sidebar.markdown("---")
st.sidebar.header("🎯 Metas Comerciales")
meta_ticket_pct = st.sidebar.number_input("Meta Crecimiento Ticket Promedio (%):", value=10.0, step=0.5, format="%.1f")

if uploaded_file:
    df_tot, lista_ciclos = cargar_datos(uploaded_file)
    
    if len(lista_ciclos) >= 2:
        c_act = st.sidebar.selectbox("Semana Actual / Corte:", lista_ciclos, index=len(lista_ciclos)-1)
        c_ant = st.sidebar.selectbox("Semana Anterior / Corte:", lista_ciclos, index=max(0, len(lista_ciclos)-2))
        
        df_act = df_tot[df_tot['Ciclo'] == c_act].copy()
        df_ant = df_tot[df_tot['Ciclo'] == c_ant].copy()
        
        cols_act = ['Tienda_Clean', 'Tienda', 'Gerente', 'Supervisor', 'Ciudad', 'Segmento', 'Ventas_Real', 'Ppto_Real', 'Ventas_AA', 'Tx_Real', 'Tx_AA']
        for c in ['Pareto', 'Comparable ', 'Comparable']:
            if c in df_act.columns and c not in cols_act: cols_act.append(c)
                
        cols_ant = ['Tienda_Clean', 'Tienda', 'Gerente', 'Supervisor', 'Ventas_Real', 'Ppto_Real', 'Ventas_AA', 'Tx_Real', 'Tx_AA']
        for c in ['Pareto', 'Comparable ', 'Comparable']:
            if c in df_ant.columns and c not in cols_ant: cols_ant.append(c)

        df_merged = pd.merge(
            df_act[cols_act], df_ant[cols_ant],
            on='Tienda_Clean', suffixes=('_Act', '_Ant'), how='outer'
        )
        
        df_merged['Tienda'] = df_merged['Tienda_Act'].combine_first(df_merged['Tienda_Ant'])
        df_merged['Gerente'] = df_merged['Gerente_Act'].combine_first(df_merged['Gerente_Ant'])
        df_merged['Supervisor'] = df_merged['Supervisor_Act'].combine_first(df_merged['Supervisor_Ant'])
        
        if 'Pareto_Act' in df_merged.columns and 'Pareto_Ant' in df_merged.columns:
            df_merged['Pareto'] = df_merged['Pareto_Act'].combine_first(df_merged['Pareto_Ant'])
        elif 'Pareto_Act' in df_merged.columns: df_merged['Pareto'] = df_merged['Pareto_Act']
        elif 'Pareto' not in df_merged.columns: df_merged['Pareto'] = 'NO'

        comp_col = None
        for c in ['Comparable _Act', 'Comparable_Act', 'Comparable ']:
            if c in df_merged.columns: comp_col = c; break
        df_merged['Comparable_Val'] = df_merged[comp_col] if comp_col else 'NO'
            
        for col in ['Ventas_Real_Act', 'Ppto_Real_Act', 'Ventas_Real_Ant', 'Ppto_Real_Ant', 'Ventas_AA_Act', 'Tx_Real_Act', 'Tx_AA_Act']:
            df_merged[col] = df_merged[col].fillna(0.0)
            
        # CÁLCULOS CLAVE
        df_merged['GAP_Ant'] = df_merged['Ventas_Real_Ant'] - df_merged['Ppto_Real_Ant']
        df_merged['GAP_Act'] = df_merged['Ventas_Real_Act'] - df_merged['Ppto_Real_Act']
        df_merged['Evolucion_GAP_$'] = df_merged['GAP_Act'] - df_merged['GAP_Ant']
        df_merged['Cumpl_Act_%'] = (df_merged['Ventas_Real_Act'] / df_merged['Ppto_Real_Act'].replace(0, 1)) * 100

        # CÁLCULOS DE TRANSACCIONES VS AÑO ANTERIOR (AA)
        df_merged['GAP_Tx_AA'] = df_merged['Tx_Real_Act'] - df_merged['Tx_AA_Act']
        df_merged['Var_Tx_AA_%'] = ((df_merged['Tx_Real_Act'] - df_merged['Tx_AA_Act']) / df_merged['Tx_AA_Act'].replace(0, 1)) * 100

        # CÁLCULOS DE TICKET PROMEDIO Y EVALUACIÓN FRENTE A META CONFIGURABLE
        df_merged['Ticket_Act'] = df_merged['Ventas_Real_Act'] / df_merged['Tx_Real_Act'].replace(0, 1)
        df_merged['Ticket_AA'] = df_merged['Ventas_AA_Act'] / df_merged['Tx_AA_Act'].replace(0, 1)
        df_merged['Ticket_Objetivo'] = df_merged['Ticket_AA'] * (1 + (meta_ticket_pct / 100.0))
        df_merged['GAP_Ticket_$'] = df_merged['Ticket_Act'] - df_merged['Ticket_Objetivo']
        df_merged['Var_Ticket_AA_%'] = ((df_merged['Ticket_Act'] - df_merged['Ticket_AA']) / df_merged['Ticket_AA'].replace(0, 1)) * 100

        def clasificar_escenario(row):
            g_ant, g_act, diff = row['GAP_Ant'], row['GAP_Act'], row['Evolucion_GAP_$']
            if g_ant < 0 and g_act >= 0: return "Pasa de Negativo a Positivo 🟢"
            elif g_ant >= 0 and g_act >= 0 and diff > 0: return "Amplió Superávit 🟢"
            elif g_ant >= 0 and g_act >= 0 and diff == 0: return "Mantuvo Superávit 🟢"
            elif g_ant < 0 and g_act < 0 and diff > 0: return "Recortó Faltante 🟢"
            elif g_ant < 0 and g_act < 0 and diff == 0: return "Mantuvo Faltante 🟡"
            else: return "Aumentó Faltante 🔴"

        df_merged['Escenario'] = df_merged.apply(clasificar_escenario, axis=1)

        # FILTROS SUPERIORES EN CAJAS TÉRMICAS
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            st.markdown('<div class="filter-card-red"><div class="filter-card-title">Filtro Tiendas Pareto</div>', unsafe_allow_html=True)
            solo_pareto = st.toggle("Solo Tiendas Pareto", value=False, key="sw_pareto")
            st.markdown('</div>', unsafe_allow_html=True)
        with f_col2:
            st.markdown('<div class="filter-card-red"><div class="filter-card-title">Filtro Tiendas Comparables</div>', unsafe_allow_html=True)
            solo_comparable = st.toggle("Solo Tiendas Comparables", value=False, key="sw_comp")
            st.markdown('</div>', unsafe_allow_html=True)

        df_base = df_merged.copy()
        patron_valid = 'SI|S|1|PARETO|TRUE|COMPARABLE'
        if solo_pareto: df_base = df_base[df_base['Pareto'].astype(str).str.upper().str.contains(patron_valid, regex=True, na=False)]
        if solo_comparable: df_base = df_base[df_base['Comparable_Val'].astype(str).str.upper().str.contains(patron_valid, regex=True, na=False)]

        # RENDERIZADO INTEGRAL DE KPIS
        def render_kpi_block(df_scope, key_suffix="main"):
            df_activas = df_scope[df_scope['Ventas_Real_Act'] > 0]
            num_tiendas = len(df_activas)
            v_act = df_scope['Ventas_Real_Act'].sum()
            ppto_act = df_scope['Ppto_Real_Act'].sum()
            gap_act = df_scope['GAP_Act'].sum()
            gap_ant = df_scope['GAP_Ant'].sum()
            cumpl_gen = (v_act / ppto_act * 100) if ppto_act > 0 else 0.0

            tx_act = df_scope['Tx_Real_Act'].sum()
            tx_aa = df_scope['Tx_AA_Act'].sum()
            gap_tx_aa = tx_act - tx_aa
            var_tx_aa = ((tx_act - tx_aa) / tx_aa * 100) if tx_aa > 0 else 0.0

            v_aa = df_scope['Ventas_AA_Act'].sum()
            ticket_act = (v_act / tx_act) if tx_act > 0 else 0.0
            ticket_aa = (v_aa / tx_aa) if tx_aa > 0 else 0.0
            ticket_obj = ticket_aa * (1 + (meta_ticket_pct / 100.0))
            gap_ticket_monto = ticket_act - ticket_obj
            var_ticket_aa = ((ticket_act - ticket_aa) / ticket_aa * 100) if ticket_aa > 0 else 0.0

            k1, k2, k3, k4, k5 = st.columns([1, 1, 1, 1.2, 1])
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
                    <div class="card-sub">GAP Ant: ${gap_ant:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            with k3:
                col_tx_c = "#16A34A" if gap_tx_aa >= 0 else "#DC2626"
                st.markdown(f"""
                <div class="metric-card card-purple">
                    <div class="card-title">GAP TRANSACCIONES (VS AA)</div>
                    <div class="card-value" style="color:{col_tx_c};">{gap_tx_aa:+,.0f} Tx</div>
                    <div class="card-sub" style="color:{col_tx_c}; font-weight:bold;">Var: {var_tx_aa:+.1f}% vs AA</div>
                </div>
                """, unsafe_allow_html=True)
            with k4:
                col_tk_c = "#16A34A" if gap_ticket_monto >= 0 else "#DC2626"
                st.markdown(f"""
                <div class="metric-card card-amber">
                    <div class="card-title">TICKET PROMEDIO (${meta_ticket_pct:.0f}% META)</div>
                    <div class="card-value" style="color:{col_tk_c};">${ticket_act:,.0f}</div>
                    <div class="card-sub" style="color:{col_tk_c}; font-weight:bold;">GAP Meta: ${gap_ticket_monto:+,.0f} ({var_ticket_aa:+.1f}% vs AA)</div>
                </div>
                """, unsafe_allow_html=True)
            with k5:
                fig_g = go.Figure(go.Indicator(
                    mode = "gauge+number", value = cumpl_gen,
                    number = {'suffix': "%", 'valueformat': ".1f"},
                    gauge = {
                        'axis': {'range': [0, 120]},
                        'bar': {'color': "#16A34A" if cumpl_gen >= 100 else "#6B0011"},
                        'steps': [
                            {'range': [0, 85], 'color': "#FEE2E2"},
                            {'range': [85, 100], 'color': "#FEF3C7"},
                            {'range': [100, 120], 'color': "#DCFCE7"}
                        ]
                    }
                ))
                fig_g.update_layout(
                    height=125, margin=dict(l=5, r=5, t=5, b=5),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_g, use_container_width=True, key=f"gauge_{key_suffix}")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<h4 style='text-align:left; color:#423B33; font-size:13px; font-weight:800;'>🏬 ESTADO DE TIENDAS POR ESCENARIO</h4>", unsafe_allow_html=True)
            
            conteo = df_activas['Escenario'].value_counts()
            e1, e2, e3, e4, e5, e6 = st.columns(6)
            with e1: st.markdown(f"""<div class="metric-card card-green"><div class="card-title">PASA A POSITIVO</div><div class="card-value" style="color:#16A34A;">{conteo.get('Pasa de Negativo a Positivo 🟢', 0)}</div><div class="card-sub">Tiendas</div></div>""", unsafe_allow_html=True)
            with e2: st.markdown(f"""<div class="metric-card card-green"><div class="card-title">AMPLIÓ SUPERÁVIT</div><div class="card-value" style="color:#16A34A;">{conteo.get('Amplió Superávit 🟢', 0)}</div><div class="card-sub">Tiendas</div></div>""", unsafe_allow_html=True)
            with e3: st.markdown(f"""<div class="metric-card card-green"><div class="card-title">MANTUVO SUPERÁVIT</div><div class="card-value" style="color:#16A34A;">{conteo.get('Mantuvo Superávit 🟢', 0)}</div><div class="card-sub">Tiendas</div></div>""", unsafe_allow_html=True)
            with e4: st.markdown(f"""<div class="metric-card card-green"><div class="card-title">RECORTÓ FALTANTE</div><div class="card-value" style="color:#16A34A;">{conteo.get('Recortó Faltante 🟢', 0)}</div><div class="card-sub">Tiendas</div></div>""", unsafe_allow_html=True)
            with e5: st.markdown(f"""<div class="metric-card card-yellow"><div class="card-title">MANTUVO FALTANTE</div><div class="card-value" style="color:#D97706;">{conteo.get('Mantuvo Faltante 🟡', 0)}</div><div class="card-sub">Tiendas</div></div>""", unsafe_allow_html=True)
            with e6: st.markdown(f"""<div class="metric-card card-red"><div class="card-title">AUMENTÓ FALTANTE</div><div class="card-value" style="color:#DC2626;">{conteo.get('Aumentó Faltante 🔴', 0)}</div><div class="card-sub">Tiendas</div></div>""", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["📊 Informe Gerencial GAP", "🔍 Análisis por Gerencia"])

        # PESTAÑA 1: INFORME GERENCIAL
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
                        st.markdown(f"""<div class="gerente-box"><div class="gerente-title">📍 GERENCIA REGIONAL: {str(ger).upper()}</div>""", unsafe_allow_html=True)
                        render_kpi_block(df_g, key_suffix=f"ger_{idx}")
                        st.markdown("</div>", unsafe_allow_html=True)

        # PESTAÑA 2: ANÁLISIS DETALLADO
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
            st.markdown("### 👔 CUMPLIMIENTO INTERACTIVO Y GAP DE TRANSACCIONES POR SUPERVISOR")
            
            df_sup_agg = df_tab2.groupby(['Supervisor', 'Gerente']).agg(
                Ventas_Act=('Ventas_Real_Act', 'sum'),
                Ppto_Act=('Ppto_Real_Act', 'sum'),
                Tx_Act=('Tx_Real_Act', 'sum'),
                Tx_AA=('Tx_AA_Act', 'sum')
            ).reset_index()
            
            df_sup_agg['Cumpl_%'] = (df_sup_agg['Ventas_Act'] / df_sup_agg['Ppto_Act'].replace(0, 1)) * 100
            df_sup_agg['GAP_Tx_AA'] = df_sup_agg['Tx_Act'] - df_sup_agg['Tx_AA']

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                fig_sup = px.bar(
                    df_sup_agg.sort_values(by='Cumpl_%', ascending=True),
                    y='Supervisor', x='Cumpl_%', color='Cumpl_%',
                    color_continuous_scale=['#8C0017', '#FEF3C7', '#16A34A'],
                    orientation='h', title="CUMPLIMIENTO DE PRESUPUESTO (%)", text_auto='.1f%'
                )
                fig_sup.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_sup, use_container_width=True, key="fig_sup_chart")
                
            with col_g2:
                fig_tx = px.bar(
                    df_sup_agg.sort_values(by='GAP_Tx_AA', ascending=True),
                    y='Supervisor', x='GAP_Tx_AA', color='GAP_Tx_AA',
                    color_continuous_scale=['#DC2626', '#D97706', '#2563EB'],
                    orientation='h', title="GAP DE TRANSACCIONES VS AÑO ANTERIOR (Tx)", text_auto=',.0f'
                )
                fig_tx.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_tx, use_container_width=True, key="fig_tx_chart")

            st.markdown("---")
            st.markdown("### 🏬 EVOLUCIÓN DEL GAP Y DIAGNÓSTICO POR TIENDA")
            
            fig_tiendas = px.bar(
                df_tab2.sort_values(by='Evolucion_GAP_$', ascending=True),
                y='Tienda', x='Evolucion_GAP_$', color='Escenario',
                color_discrete_map={
                    'Pasa de Negativo a Positivo 🟢': '#15803D',
                    'Amplió Superávit 🟢': '#16A34A',
                    'Mantuvo Superávit 🟢': '#22C55E',
                    'Recortó Faltante 🟢': '#4ADE80',
                    'Mantuvo Faltante 🟡': '#D97706',
                    'Aumentó Faltante 🔴': '#8C0017'
                },
                orientation='h', title="VARIACIÓN DE GAP DE PPTO ($) POR TIENDA"
            )
            fig_tiendas.update_layout(height=max(400, len(df_tab2) * 22), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_tiendas, use_container_width=True, key="fig_tiendas_chart")

            # TABLA DE CAUSA RAÍZ INTERANUAL
            st.markdown("#### 📋 TABLA DE CAUSA RAÍZ: VENTAS, GAP TRANSACCIONES (AA) Y EVALUACIÓN DE TICKET")
            tabla_causa = df_tab2.sort_values(by='Cumpl_Act_%', ascending=False)[[
                'Tienda', 'Gerente', 'Supervisor', 'Cumpl_Act_%', 'GAP_Act', 'Evolucion_GAP_$', 
                'Tx_Real_Act', 'GAP_Tx_AA', 'Ticket_Act', 'GAP_Ticket_$', 'Escenario'
            ]].copy()
            
            tabla_causa.columns = [
                'Tienda', 'Gerente', 'Supervisor', 'Cumpl %', 'GAP Act ($)', 'Evol GAP ($)',
                'Tx Act', 'GAP Tx (VS AA)', 'Ticket Act ($)', f'GAP Ticket vs {meta_ticket_pct:.0f}% ($)', 'Escenario'
            ]
            
            st.dataframe(
                tabla_causa.style.format({
                    'Cumpl %': '{:.1f}%',
                    'GAP Act ($)': '${:,.0f}',
                    'Evol GAP ($)': '${:+,.0f}',
                    'Tx Act': '{:,.0f}',
                    'GAP Tx (VS AA)': '{:+,.0f}',
                    'Ticket Act ($)': '${:,.0f}',
                    f'GAP Ticket vs {meta_ticket_pct:.0f}% ($)': '${:+,.0f}'
                }),
                use_container_width=True
            )

else:
    st.info("👈 Por favor sube el archivo ANALISIS GAP.xlsx en el menú lateral para desplegar el informe gerencial.")