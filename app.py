import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Informe Gerencial GAP - Juan Valdez", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 PALETA WARM CORPORATE / BEIGE PREMIUM JUAN VALDEZ & BOTONES ESTILIZADOS
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

    /* Tarjetas KPI Superiores */
    .metric-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 12px 8px;
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
    .card-teal { border-left: 5px solid #0D9488; }
    
    .card-title { font-size: 10px; font-weight: 800; color: #524B42; text-transform: uppercase; margin-bottom: 4px; }
    .card-value { font-size: 18px; font-weight: 800; margin: 2px 0; }
    .card-sub { font-size: 10px; color: #786F66; font-weight: 600; }

    /* ESTILIZACIÓN DE BOTONES DE ESCENARIO COMO TARJETAS ELEGANTES */
    div[data-testid="stColumn"] div[data-testid="stButton"] > button {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        color: #1E293B !important;
        padding: 10px 4px !important;
        height: auto !important;
        min-height: 72px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
        transition: all 0.2s ease-in-out !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
    }

    div[data-testid="stColumn"] div[data-testid="stButton"] > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 14px rgba(0,0,0,0.1) !important;
        border-color: #CBD5E1 !important;
        background-color: #FAFAFA !important;
    }

    /* Borde temático diferenciado por columnas */
    div[data-testid="stColumn"]:nth-child(1) div[data-testid="stButton"] > button { border-left: 4px solid #16A34A !important; }
    div[data-testid="stColumn"]:nth-child(2) div[data-testid="stButton"] > button { border-left: 4px solid #16A34A !important; }
    div[data-testid="stColumn"]:nth-child(3) div[data-testid="stButton"] > button { border-left: 4px solid #16A34A !important; }
    div[data-testid="stColumn"]:nth-child(4) div[data-testid="stButton"] > button { border-left: 4px solid #16A34A !important; }
    div[data-testid="stColumn"]:nth-child(5) div[data-testid="stButton"] > button { border-left: 4px solid #D97706 !important; }
    div[data-testid="stColumn"]:nth-child(6) div[data-testid="stButton"] > button { border-left: 4px solid #DC2626 !important; }

    /* Titulo Gris Discreto para Sección GAP Escenarios */
    .gap-section-title {
        font-size: 11px;
        font-weight: 700;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-top: 14px;
        margin-bottom: 8px;
    }

    /* Caja de Resumen Ejecutivo */
    .ai-box {
        background-color: #FFFFFF;
        border: 1px solid #D97706;
        border-left: 6px solid #B45309;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 25px;
        box-shadow: 0 4px 14px rgba(180, 83, 9, 0.1);
    }
    .ai-title { font-size: 16px; font-weight: 800; color: #78350F; margin-bottom: 12px; border-bottom: 1px solid #FDE68A; padding-bottom: 6px; }

    /* Cajas para Gerentes con Encabezado Oscuro Diferencial */
    .gerente-box {
        background-color: #FFFFFF;
        border-radius: 14px;
        border: 1px solid #D1C7B7;
        padding: 0px 20px 20px 20px;
        margin-bottom: 25px;
        box-shadow: 0 6px 16px rgba(80, 70, 60, 0.08);
        overflow: hidden;
    }
    .gerente-title-banner {
        background: linear-gradient(90deg, #58000E 0%, #7A0016 100%);
        color: #FFFFFF;
        font-size: 15px;
        font-weight: 800;
        padding: 12px 20px;
        margin: 0 -20px 18px -20px;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
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

# -----------------------------------------------------------------------------
# 🔒 CONTROL DE ACCESO MEDIANTE CONTRASEÑA
# -----------------------------------------------------------------------------
PASSWORD_CORRECTA = "JuanValdez2026*"

def verificar_password():
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if not st.session_state["autenticado"]:
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("""
            <div style="background-color: #FFFFFF; padding: 30px; border-radius: 14px; border: 1px solid #D1C7B7; text-align: center; box-shadow: 0 6px 16px rgba(80, 70, 60, 0.1);">
                <h2 style="color: #6B0011; margin-bottom: 10px;">☕ Acceso Restringido</h2>
                <p style="color: #64748B; font-size: 13px;">Ingrese la clave de acceso autorizada para ver el Informe Gerencial GAP Juan Valdez.</p>
            </div>
            """, unsafe_allow_html=True)
            
            pwd_input = st.text_input("Contraseña:", type="password", key="input_pwd")
            if st.button("Ingresar al Tablero", type="primary", use_container_width=True):
                if pwd_input == PASSWORD_CORRECTA:
                    st.session_state["autenticado"] = True
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta. Intente nuevamente.")
        return False
    return True

if not verificar_password():
    st.stop()

# CABECERA INSTITUCIONAL
st.markdown("""
<div class="jv-header">
    <h1>INFORME GERENCIAL GAP VS PRESUPUESTO & ANÁLISIS DE TRÁFICO (AA)</h1>
    <p>Control Integrado de Ventas, Crecimiento AA, Presupuesto, GAP Transacciones Interanual y Meta de Ticket Promedio</p>
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

# PERSISTENCIA
NOMBRE_ARCHIVO_OFICIAL = "ANALISIS GAP.xlsx"

st.sidebar.header("📁 Gestión de Base de Datos")

if st.sidebar.button("🔒 Cerrar Sesión", use_container_width=True):
    st.session_state["autenticado"] = False
    st.rerun()

st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader("Actualizar Excel (Opcional):", type=['xlsx'])

if uploaded_file is not None:
    if st.sidebar.button("💾 Guardar como Base Oficial", type="primary", use_container_width=True):
        with open(NOMBRE_ARCHIVO_OFICIAL, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.cache_data.clear()
        st.sidebar.success("✅ ¡Base de datos guardada permanentemente!")
        st.rerun()

file_to_process = None
if uploaded_file is not None:
    file_to_process = uploaded_file
elif os.path.exists(NOMBRE_ARCHIVO_OFICIAL):
    file_to_process = NOMBRE_ARCHIVO_OFICIAL
    st.sidebar.caption("🟢 Usando base de datos oficial guardada.")
else:
    st.sidebar.warning("👈 Por favor sube el archivo ANALISIS GAP.xlsx y guárdalo como base oficial.")

st.sidebar.markdown("---")
st.sidebar.header("🎯 Metas Comerciales")
meta_ticket_pct = st.sidebar.number_input("Meta Crecimiento Ticket Promedio (%):", value=10.0, step=0.5, format="%.1f")

# -----------------------------------------------------------------------------
# POP-UP / DIALOG EMBEDDED E INTERACTIVO DE ALTO IMPACTO
# -----------------------------------------------------------------------------
@st.dialog("🏬 Detalle Interactivo por Escenario", width="large")
def mostrar_popup_escenario(nombre_escenario, df_filtrado):
    st.markdown(f"### Escenario: **{nombre_escenario}**")
    
    if not df_filtrado.empty:
        total_gap = df_filtrado['GAP_Act'].sum()
        total_evol = df_filtrado['Evolucion_GAP_$'].sum()
        v_total = df_filtrado['Ventas_Real_Act'].sum()
        p_total = df_filtrado['Ppto_Real_Act'].sum()
        cumpl_prom = (v_total / p_total * 100) if p_total > 0 else 0.0

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Tiendas", len(df_filtrado))
        with m2:
            st.metric("GAP Presupuesto Act.", f"${total_gap:,.0f}")
        with m3:
            st.metric("Cumplimiento Promedio", f"{cumpl_prom:.1f}%")

        st.markdown("---")
        
        busqueda = st.text_input("🔍 Buscar Tienda o Supervisor:", "", key="search_popup_input")
        
        df_pop_view = df_filtrado.copy()
        if busqueda:
            patron = busqueda.strip().upper()
            df_pop_view = df_pop_view[
                df_pop_view['Tienda'].astype(str).str.upper().str.contains(patron, na=False) |
                df_pop_view['Supervisor'].astype(str).str.upper().str.contains(patron, na=False)
            ]

        # Gráfica interactiva de distribución dentro del pop-up
        if not df_pop_view.empty:
            fig_pop = px.bar(
                df_pop_view.sort_values(by='GAP_Act', ascending=True),
                y='Tienda', x='GAP_Act', color='GAP_Act',
                color_continuous_scale=['#DC2626', '#EAB308', '#16A34A'],
                orientation='h', title="DISTRIBUCIÓN DE GAP POR TIENDA ($)",
                text_auto=',.0f'
            )
            fig_pop.update_coloraxes(showscale=False)
            fig_pop.update_traces(textposition='outside', cliponaxis=False)
            fig_pop.update_layout(
                height=max(250, len(df_pop_view) * 25),
                margin=dict(r=80, l=10, t=30, b=10),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_pop, use_container_width=True, key="fig_pop_chart")

            st.markdown("#### 📋 Detalle Tabular")
            tabla_popup = df_pop_view[[
                'Tienda', 'Supervisor', 'Gerente', 'Cumpl_Act_%', 'GAP_Act', 'Evolucion_GAP_$'
            ]].copy()
            
            tabla_popup.columns = [
                'Tienda', 'Supervisor', 'Gerente', 'Cumpl %', 'GAP Act ($)', 'Diferencia GAP ($)'
            ]
            
            st.dataframe(
                tabla_popup.sort_values(by='GAP Act ($)', ascending=True).style.format({
                    'Cumpl %': '{:.1f}%',
                    'GAP Act ($)': '${:,.0f}',
                    'Diferencia GAP ($)': '${:+,.0f}'
                }),
                use_container_width=True,
                height=300
            )
        else:
            st.warning("No se encontraron tiendas que coincidan con la búsqueda.")
    else:
        st.info("No hay tiendas registradas bajo este escenario con los filtros aplicados.")

if file_to_process:
    df_tot, lista_ciclos = cargar_datos(file_to_process)
    
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
            
        df_merged['GAP_Ant'] = df_merged['Ventas_Real_Ant'] - df_merged['Ppto_Real_Ant']
        df_merged['GAP_Act'] = df_merged['Ventas_Real_Act'] - df_merged['Ppto_Real_Act']
        df_merged['Evolucion_GAP_$'] = df_merged['GAP_Act'] - df_merged['GAP_Ant']
        df_merged['Cumpl_Act_%'] = (df_merged['Ventas_Real_Act'] / df_merged['Ppto_Real_Act'].replace(0, 1)) * 100

        # Crecimiento de Ventas Vs Año Anterior (AA)
        df_merged['Diff_Ventas_AA'] = df_merged['Ventas_Real_Act'] - df_merged['Ventas_AA_Act']
        df_merged['Var_Ventas_AA_%'] = ((df_merged['Ventas_Real_Act'] - df_merged['Ventas_AA_Act']) / df_merged['Ventas_AA_Act'].replace(0, 1)) * 100

        df_merged['GAP_Tx_AA'] = df_merged['Tx_Real_Act'] - df_merged['Tx_AA_Act']
        df_merged['Var_Tx_AA_%'] = ((df_merged['Tx_Real_Act'] - df_merged['Tx_AA_Act']) / df_merged['Tx_AA_Act'].replace(0, 1)) * 100

        df_merged['Ticket_Act'] = df_merged['Ventas_Real_Act'] / df_merged['Tx_Real_Act'].replace(0, 1)
        df_merged['Ticket_AA'] = df_merged['Ventas_AA_Act'] / df_merged['Tx_AA_Act'].replace(0, 1)
        df_merged['Ticket_Objetivo'] = df_merged['Ticket_AA'] * (1 + (meta_ticket_pct / 100.0))
        df_merged['GAP_Ticket_$'] = df_merged['Ticket_Act'] - df_merged['Ticket_Objetivo']
        df_merged['Var_Ticket_AA_%'] = ((df_merged['Ticket_Act'] - df_merged['Ticket_AA']) / df_merged['Ticket_AA'].replace(0, 1)) * 100

        # CLASIFICACIÓN DE ESCENARIOS
        def clasificar_escenario(row):
            g_ant, g_act, diff = row['GAP_Ant'], row['GAP_Act'], row['Evolucion_GAP_$']
            if g_act >= 0:
                if g_ant < 0:
                    return "Pasa de Negativo a Positivo 🟢"
                elif diff > 0:
                    return "Amplió Superávit 🟢"
                else:
                    return "Mantuvo Superávit 🟢"
            else:
                if diff > 0:
                    return "Recortó Faltante 🟢"
                elif diff == 0:
                    return "Mantuvo Faltante 🟡"
                else:
                    return "Aumentó Faltante 🔴"

        df_merged['Escenario'] = df_merged.apply(clasificar_escenario, axis=1)

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

        def generar_diagnostico_gerencial(df_data):
            v_act = df_data['Ventas_Real_Act'].sum()
            ppto_act = df_data['Ppto_Real_Act'].sum()
            gap_act = df_data['GAP_Act'].sum()
            cumpl = (v_act / ppto_act * 100) if ppto_act > 0 else 0.0
            
            v_aa = df_data['Ventas_AA_Act'].sum()
            diff_v_aa = v_act - v_aa
            var_v_aa = ((v_act - v_aa) / v_aa * 100) if v_aa > 0 else 0.0

            tx_act = df_data['Tx_Real_Act'].sum()
            tx_aa = df_data['Tx_AA_Act'].sum()
            gap_tx = tx_act - tx_aa
            var_tx = ((tx_act - tx_aa) / tx_aa * 100) if tx_aa > 0 else 0.0
            
            tk_act = (v_act / tx_act) if tx_act > 0 else 0.0
            tk_aa = (v_aa / tx_aa) if tx_aa > 0 else 0.0
            tk_obj = tk_aa * (1 + (meta_ticket_pct / 100.0))
            gap_tk = tk_act - tk_obj
            
            conteo = df_data['Escenario'].value_counts()
            tiendas_verdes = conteo.get('Pasa de Negativo a Positivo 🟢', 0) + conteo.get('Amplió Superávit 🟢', 0) + conteo.get('Mantuvo Superávit 🟢', 0) + conteo.get('Recortó Faltante 🟢', 0)

            cond_gap = df_data['GAP_Act'] < 0
            cond_tx = df_data['GAP_Tx_AA'] < 0
            cond_tk = df_data['GAP_Ticket_$'] < 0
            
            df_foco_total = df_data[cond_gap & cond_tx & cond_tk].sort_values(by='GAP_Act', ascending=True)

            analisis = []
            analisis.append(f"<b>📌 Diagnóstico Consolidado Compañía:</b><br>El cumplimiento global se sitúa en el <b>{cumpl:.1f}%</b> con un GAP de presupuesto de <b>${gap_act:,.0f}</b>. Las ventas actuales registran un incremento/variación frente al año anterior de <b>${diff_v_aa:+,.0f} ({var_v_aa:+.1f}% vs AA)</b>. De un total de {len(df_data)} puntos evaluados, <b>{tiendas_verdes}</b> se ubican en terreno positivo/avance, mientras que <b>{len(df_foco_total)}</b> puntos cumplen con el criterio estricto de <b>Tienda Foco de Atención Crítica</b> (déficit presupuestal + caída de tráfico + subconsumo de ticket).")
            
            if gap_tx < 0 and gap_tk < 0:
                causa = f"<b>🔍 Causa Raíz Comercial:</b> Desviación por Causal Doble. Pérdida de tráfico interanual de <b>{gap_tx:+,.0f} Transacciones ({var_tx:+.1f}% vs AA)</b> combinada con un Ticket Promedio de <b>${tk_act:,.0f}</b> (Faltan ${abs(gap_tk):,.0f} por ticket para la meta del {meta_ticket_pct:.0f}%)."
            elif gap_tx < 0:
                causa = f"<b>🔍 Causa Raíz Comercial:</b> Caída de Tráfico. Disminución de <b>{gap_tx:+,.0f} Transacciones ({var_tx:+.1f}% vs AA)</b>."
            elif gap_tk < 0:
                causa = f"<b>🔍 Causa Raíz Comercial:</b> Subconsumo de Ticket. Se ubica <b>${abs(gap_tk):,.0f}</b> por debajo del objetivo de crecimiento."
            else:
                causa = "<b>🔍 Causa Raíz Comercial:</b> Desempeño Operativo Sostenido."
            analisis.append(causa)

            analisis.append("<b>📍 Análisis por Gerencia Regional y Tiendas Foco de Atención Crítica:</b>")
            gerentes = sorted([g for g in df_data['Gerente'].dropna().unique() if str(g) != 'nan'])
            
            for ger in gerentes:
                df_g = df_data[df_data['Gerente'] == ger]
                v_g = df_g['Ventas_Real_Act'].sum()
                p_g = df_g['Ppto_Real_Act'].sum()
                gap_g = df_g['GAP_Act'].sum()
                cump_g = (v_g / p_g * 100) if p_g > 0 else 0.0
                
                v_g_aa = df_g['Ventas_AA_Act'].sum()
                var_v_g_aa = ((v_g - v_g_aa) / v_g_aa * 100) if v_g_aa > 0 else 0.0
                
                df_foco_reg = df_g[(df_g['GAP_Act'] < 0) & (df_g['GAP_Tx_AA'] < 0) & (df_g['GAP_Ticket_$'] < 0)].sort_values(by='GAP_Act', ascending=True)
                
                txt_ger = f"• <b>Gerencia {str(ger).upper()}:</b> Cumplimiento al <b>{cump_g:.1f}%</b> | Crecimiento Ventas AA: <b>{var_v_g_aa:+.1f}%</b> | GAP Presupuesto: <b>${gap_g:,.0f}</b>."
                if not df_foco_reg.empty:
                    txt_ger += f"<br>&nbsp;&nbsp;&nbsp;&nbsp;⚠️ <i>Tiendas Foco Crítico ({len(df_foco_reg)} Puntos):</i>"
                    for _, row_f in df_foco_reg.iterrows():
                        txt_ger += f"<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- <b>{row_f['Tienda']}</b> (Sup. {row_f['Supervisor']}): Cumpl. <b>{row_f['Cumpl_Act_%']:.1f}%</b> | GAP: <b>${row_f['GAP_Act']:,.0f}</b> | Var Tx AA: <b>{row_f['Var_Tx_AA_%']:+.1f}%</b> | Ticket: <b>${row_f['Ticket_Act']:,.0f}</b>"
                else:
                    txt_ger += "<br>&nbsp;&nbsp;&nbsp;&nbsp;✅ <i>Sin tiendas que reúnan simultáneamente las 3 condiciones de alerta crítica.</i>"
                analisis.append(txt_ger)

            return "<br><br>".join(analisis)

        # RENDERIZADO INTEGRAL DE KPIS CON TARJETAS RESTRUCTURADAS COMO BOTONES INTERACTIVOS
        def render_kpi_block(df_scope, key_suffix="main"):
            df_activas = df_scope[df_scope['Ventas_Real_Act'] > 0]
            num_tiendas = len(df_activas)
            v_act = df_scope['Ventas_Real_Act'].sum()
            ppto_act = df_scope['Ppto_Real_Act'].sum()
            gap_act = df_scope['GAP_Act'].sum()
            gap_ant = df_scope['GAP_Ant'].sum()
            cumpl_gen = (v_act / ppto_act * 100) if ppto_act > 0 else 0.0

            v_aa = df_scope['Ventas_AA_Act'].sum()
            diff_v_aa = v_act - v_aa
            var_v_aa = ((v_act - v_aa) / v_aa * 100) if v_aa > 0 else 0.0

            tx_act = df_scope['Tx_Real_Act'].sum()
            tx_aa = df_scope['Tx_AA_Act'].sum()
            gap_tx_aa = tx_act - tx_aa
            var_tx_aa = ((tx_act - tx_aa) / tx_aa * 100) if tx_aa > 0 else 0.0

            ticket_act = (v_act / tx_act) if tx_act > 0 else 0.0
            ticket_aa = (v_aa / tx_aa) if tx_aa > 0 else 0.0
            ticket_obj = ticket_aa * (1 + (meta_ticket_pct / 100.0))
            gap_ticket_monto = ticket_act - ticket_obj
            var_ticket_aa = ((ticket_act - ticket_aa) / ticket_aa * 100) if ticket_aa > 0 else 0.0

            k1, k2, k3, k4, k5, k6 = st.columns([1, 1, 1, 1, 1.2, 1])
            with k1:
                st.markdown(f"""
                <div class="metric-card card-blue">
                    <div class="card-title">TIENDAS EVALUADAS</div>
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
                col_v_c = "#16A34A" if diff_v_aa >= 0 else "#DC2626"
                st.markdown(f"""
                <div class="metric-card card-teal">
                    <div class="card-title">CRECIMIENTO VENTAS (VS AA)</div>
                    <div class="card-value" style="color:{col_v_c};">${diff_v_aa:+,.0f}</div>
                    <div class="card-sub" style="color:{col_v_c}; font-weight:bold;">Var: {var_v_aa:+.1f}% vs AA</div>
                </div>
                """, unsafe_allow_html=True)
            with k4:
                col_tx_c = "#16A34A" if gap_tx_aa >= 0 else "#DC2626"
                st.markdown(f"""
                <div class="metric-card card-purple">
                    <div class="card-title">GAP TRANSACCIONES (VS AA)</div>
                    <div class="card-value" style="color:{col_tx_c};">{gap_tx_aa:+,.0f} Tx</div>
                    <div class="card-sub" style="color:{col_tx_c}; font-weight:bold;">Var: {var_tx_aa:+.1f}% vs AA</div>
                </div>
                """, unsafe_allow_html=True)
            with k5:
                col_tk_c = "#16A34A" if gap_ticket_monto >= 0 else "#DC2626"
                st.markdown(f"""
                <div class="metric-card card-amber">
                    <div class="card-title">TICKET PROMEDIO (${meta_ticket_pct:.0f}% META)</div>
                    <div class="card-value" style="color:{col_tk_c};">${ticket_act:,.0f}</div>
                    <div class="card-sub" style="color:{col_tk_c}; font-weight:bold;">GAP Meta: ${gap_ticket_monto:+,.0f} ({var_ticket_aa:+.1f}% vs AA)</div>
                </div>
                """, unsafe_allow_html=True)
            with k6:
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

            # SECCIÓN GAP CON TARJETAS RESTRUCTURADAS COMO BOTONES INTERACTIVOS
            st.markdown('<div class="gap-section-title">GAP & DISTRIBUCIÓN DE TIENDAS POR ESCENARIO (HAZ CLIC PARA VER POP-UP INTERACTIVO)</div>', unsafe_allow_html=True)
            
            conteo = df_activas['Escenario'].value_counts()
            
            escenarios_info = [
                ("Pasa de Negativo a Positivo 🟢", "PASA A POSITIVO", conteo.get('Pasa de Negativo a Positivo 🟢', 0), "#16A34A"),
                ("Amplió Superávit 🟢", "AMPLIÓ SUPERÁVIT", conteo.get('Amplió Superávit 🟢', 0), "#16A34A"),
                ("Mantuvo Superávit 🟢", "MANTUVO SUPERÁVIT", conteo.get('Mantuvo Superávit 🟢', 0), "#16A34A"),
                ("Recortó Faltante 🟢", "RECORTÓ FALTANTE", conteo.get('Recortó Faltante 🟢', 0), "#16A34A"),
                ("Mantuvo Faltante 🟡", "MANTUVO FALTANTE", conteo.get('Mantuvo Faltante 🟡', 0), "#D97706"),
                ("Aumentó Faltante 🔴", "AUMENTÓ FALTANTE", conteo.get('Aumentó Faltante 🔴', 0), "#DC2626")
            ]

            e_cols = st.columns(6)
            for i, (nombre_esc, label_esc, cant, color_hex) in enumerate(escenarios_info):
                with e_cols[i]:
                    label_btn = f"{label_esc}\n\n{cant}\nTiendas"
                    if st.button(label_btn, key=f"btn_esc_{i}_{key_suffix}", use_container_width=True):
                        df_esc_filtrado = df_activas[df_activas['Escenario'] == nombre_esc]
                        mostrar_popup_escenario(nombre_esc, df_esc_filtrado)

        tab1, tab2 = st.tabs(["📊 Informe Gerencial GAP", "🔍 Análisis por Gerencia"])

        # PESTAÑA 1
        with tab1:
            st.markdown("### 🏢 RESUMEN GENERAL DE LA COMPAÑÍA")
            
            col_ai_btn, _ = st.columns([1, 2])
            with col_ai_btn:
                btn_ia = st.button("📊 Generar Diagnóstico Gerencial", type="primary", use_container_width=True)

            if btn_ia:
                with st.spinner("Generando diagnóstico por gerencia y consolidando tiendas foco..."):
                    resumen_texto = generar_diagnostico_gerencial(df_base)
                    st.markdown(f"""
                    <div class="ai-box">
                        <div class="ai-title">📋 DIAGNÓSTICO EJECUTIVO Y REGIONAL DE DESEMPEÑO</div>
                        <div style="color: #451A03; font-size: 13px; line-height: 1.6;">{resumen_texto}</div>
                    </div>
                    """, unsafe_allow_html=True)

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
                            <div class="gerente-title-banner">📍 GERENCIA REGIONAL: {str(ger).upper()}</div>
                        """, unsafe_allow_html=True)
                        
                        render_kpi_block(df_g, key_suffix=f"ger_{idx}")
                        
                        st.markdown("</div>", unsafe_allow_html=True)

        # PESTAÑA 2: ANÁLISIS DETALLADO
        with tab2:
            st.markdown("### 🎯 FILTROS DE ANÁLISIS DETALLADO")
            
            if "tab2_ger" not in st.session_state:
                st.session_state["tab2_ger"] = "Todos"
            if "tab2_sup" not in st.session_state:
                st.session_state["tab2_sup"] = "Todos"
            if "tab2_tienda" not in st.session_state:
                st.session_state["tab2_tienda"] = "Todas"

            def reset_filtros_tab2():
                st.session_state["tab2_ger"] = "Todos"
                st.session_state["tab2_sup"] = "Todos"
                st.session_state["tab2_tienda"] = "Todas"

            f1, f2, f3, f4 = st.columns([2, 2, 2, 1])

            with f1:
                gerentes_sel = ["Todos"] + sorted([g for g in df_base['Gerente'].dropna().unique() if str(g) != 'nan'])
                s_ger = st.selectbox("Seleccionar Gerente:", gerentes_sel, key="tab2_ger")
            with f2:
                df_temp = df_base if s_ger == "Todos" else df_base[df_base['Gerente'] == s_ger]
                sups_sel = ["Todos"] + sorted([s for s in df_temp['Supervisor'].dropna().unique() if str(s) != 'nan'])
                s_sup = st.selectbox("Seleccionar Supervisor:", sups_sel, key="tab2_sup")
            with f3:
                df_temp_tienda = df_temp if s_sup == "Todos" else df_temp[df_temp['Supervisor'] == s_sup]
                tiendas_sel = ["Todas"] + sorted([t for t in df_temp_tienda['Tienda'].dropna().unique() if str(t) != 'nan'])
                s_tienda = st.selectbox("Seleccionar Tienda:", tiendas_sel, key="tab2_tienda")
            with f4:
                st.markdown("<br>", unsafe_allow_html=True)
                st.button("🔄 Reiniciar Filtros", use_container_width=True, on_click=reset_filtros_tab2)

            df_tab2 = df_base.copy()
            if s_ger != "Todos": df_tab2 = df_tab2[df_tab2['Gerente'] == s_ger]
            if s_sup != "Todos": df_tab2 = df_tab2[df_tab2['Supervisor'] == s_sup]
            if s_tienda != "Todas": df_tab2 = df_tab2[df_tab2['Tienda'] == s_tienda]

            st.markdown("---")
            
            label_scope = s_tienda if s_tienda != 'Todas' else (s_sup if s_sup != 'Todos' else (s_ger if s_ger != 'Todos' else 'GLOBAL'))
            st.markdown(f"### 📈 INDICADORES CLAVE DE GESTIÓN ({label_scope})")
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
            df_sup_agg['Var_Tx_AA_%'] = ((df_sup_agg['Tx_Act'] - df_sup_agg['Tx_AA']) / df_sup_agg['Tx_AA'].replace(0, 1)) * 100

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                fig_sup = px.bar(
                    df_sup_agg.sort_values(by='Cumpl_%', ascending=True),
                    y='Supervisor', x='Cumpl_%', color='Cumpl_%',
                    color_continuous_scale=['#8C0017', '#FEF3C7', '#16A34A'],
                    orientation='h', title="CUMPLIMIENTO DE PRESUPUESTO (%) POR SUPERVISOR",
                    text_auto='.1f'
                )
                fig_sup.update_coloraxes(showscale=False)
                fig_sup.update_traces(texttemplate='%{x:.1f}%', textposition='outside', cliponaxis=False)
                fig_sup.update_layout(
                    height=350, 
                    margin=dict(r=90, l=10, t=30, b=10),
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_sup, use_container_width=True, key="fig_sup_chart")
                
            with col_g2:
                fig_tx = px.bar(
                    df_sup_agg.sort_values(by='Var_Tx_AA_%', ascending=True),
                    y='Supervisor', x='Var_Tx_AA_%', color='Var_Tx_AA_%',
                    color_continuous_scale=['#DC2626', '#D97706', '#2563EB'],
                    orientation='h', title="VARIACIÓN % DE TRANSACCIONES VS AÑO ANTERIOR POR SUPERVISOR",
                    text_auto='.1f'
                )
                fig_tx.update_coloraxes(showscale=False)
                fig_tx.update_traces(texttemplate='%{x:+.1f}%', textposition='outside', cliponaxis=False)
                fig_tx.update_layout(
                    height=350, 
                    margin=dict(r=90, l=10, t=30, b=10),
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_tx, use_container_width=True, key="fig_tx_chart")

            st.markdown("---")
            st.markdown("### 🏬 EVOLUCIÓN DEL GAP Y TRANSACCIONES POR TIENDA")
            
            col_bar1, col_bar2 = st.columns(2)
            
            with col_bar1:
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
                fig_tiendas.update_traces(cliponaxis=False)
                fig_tiendas.update_layout(
                    height=max(420, len(df_tab2) * 22), 
                    margin=dict(r=60, l=10, t=30, b=10),
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_tiendas, use_container_width=True, key="fig_tiendas_chart")

            with col_bar2:
                fig_tx_tiendas = px.bar(
                    df_tab2.sort_values(by='Var_Tx_AA_%', ascending=True),
                    y='Tienda', x='Var_Tx_AA_%', color='Var_Tx_AA_%',
                    color_continuous_scale=['#DC2626', '#EAB308', '#2563EB'],
                    orientation='h', title="VARIACIÓN DE TRANSACCIONES VS AÑO ANTERIOR (%) POR TIENDA"
                )
                fig_tx_tiendas.update_coloraxes(showscale=False)
                fig_tx_tiendas.update_traces(texttemplate='%{x:+.1f}%', textposition='outside', cliponaxis=False)
                fig_tx_tiendas.update_layout(
                    height=max(420, len(df_tab2) * 22), 
                    margin=dict(r=90, l=10, t=30, b=10),
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_tx_tiendas, use_container_width=True, key="fig_tx_tiendas_chart")

            st.markdown("#### 📋 TABLA DE CAUSA RAÍZ: VENTAS, GAP TRANSACCIONES (AA) Y EVALUACIÓN DE TICKET")
            tabla_causa = df_tab2.sort_values(by='Cumpl_Act_%', ascending=False)[[
                'Tienda', 'Gerente', 'Supervisor', 'Cumpl_Act_%', 'GAP_Act', 'Evolucion_GAP_$', 
                'Tx_Real_Act', 'Var_Tx_AA_%', 'Ticket_Act', 'GAP_Ticket_$', 'Escenario'
            ]].copy()
            
            tabla_causa.columns = [
                'Tienda', 'Gerente', 'Supervisor', 'Cumpl %', 'GAP Act ($)', 'Evol GAP ($)',
                'Tx Act', 'Var Tx AA %', 'Ticket Act ($)', f'GAP Ticket vs {meta_ticket_pct:.0f}% ($)', 'Escenario'
            ]
            
            st.dataframe(
                tabla_causa.style.format({
                    'Cumpl %': '{:.1f}%',
                    'GAP Act ($)': '${:,.0f}',
                    'Evol GAP ($)': '${:+,.0f}',
                    'Tx Act': '{:,.0f}',
                    'Var Tx AA %': '{:+.1f}%',
                    'Ticket Act ($)': '${:,.0f}',
                    f'GAP Ticket vs {meta_ticket_pct:.0f}% ($)': '${:+,.0f}'
                }),
                use_container_width=True
            )

else:
    st.info("👈 Por favor sube el archivo ANALISIS GAP.xlsx en el menú lateral y presiona 'Guardar como Base Oficial'.")