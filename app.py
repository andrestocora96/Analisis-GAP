import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Tablero de Desempeño de Ventas - Análisis GAP", 
    layout="wide"
)

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>TABLERO DE DESEMPEÑO DE VENTAS: EVOLUCIÓN DEL GAP VS PPTO</h2>", unsafe_allow_html=True)

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
        
        # Cruce de Semanas por Tienda
        df_merged = pd.merge(
            df_act[['Tienda_Clean', 'Tienda', 'Gerente', 'Supervisor', 'Ciudad', 'Segmento', 'Pareto', 'Ventas_Real', 'Ppto_Real', 'Transacciones_Real']],
            df_ant[['Tienda_Clean', 'Ventas_Real', 'Ppto_Real', 'Transacciones_Real']],
            on='Tienda_Clean',
            suffixes=('_Act', '_Ant'),
            how='inner'
        )
        
        # CÁLCULOS CLAVE DEL GAP DE PRESUPUESTO Y SU EVOLUCIÓN
        df_merged['GAP_Ppto_Ant'] = df_merged['Ventas_Real_Ant'] - df_merged['Ppto_Real_Ant']
        df_merged['GAP_Ppto_Act'] = df_merged['Ventas_Real_Act'] - df_merged['Ppto_Real_Act']
        df_merged['Evolucion_GAP_$'] = df_merged['GAP_Ppto_Act'] - df_merged['GAP_Ppto_Ant']
        
        # FILTROS SUPERIORES
        st.markdown("---")
        f1, f2, f3 = st.columns(3)
        with f1:
            gerentes = ["Todos"] + sorted([x for x in df_merged['Gerente'].dropna().unique()])
            sel_ger = st.selectbox("GERENTE SUPERVISOR:", gerentes)
        with f2:
            supervisores = ["Todos"] + sorted([x for x in df_merged['Supervisor'].dropna().unique()])
            sel_sup = st.selectbox("SUPERVISOR:", supervisores)
        with f3:
            tiendas = ["Todas"] + sorted([x for x in df_merged['Tienda'].dropna().unique()])
            sel_tienda = st.selectbox("TIENDA / PUNTO:", tiendas)
            
        df_f = df_merged.copy()
        if sel_ger != "Todos": df_f = df_f[df_f['Gerente'] == sel_ger]
        if sel_sup != "Todos": df_f = df_f[df_f['Supervisor'] == sel_sup]
        if sel_tienda != "Todas": df_f = df_f[df_f['Tienda'] == sel_tienda]

        # KPIS GENERALES
        v_act = df_f['Ventas_Real_Act'].sum()
        ppto_act = df_f['Ppto_Real_Act'].sum()
        gap_act = df_f['GAP_Ppto_Act'].sum()
        gap_ant = df_f['GAP_Ppto_Ant'].sum()
        evol_gap = df_f['Evolucion_GAP_$'].sum()
        cumpl_gen = (v_act / ppto_act * 100) if ppto_act > 0 else 0.0

        # Lógica estricta de estado del GAP
        if gap_act < 0 and evol_gap < 0:
            txt_estado = "Aumentó Faltante 🔴"
            col_estado = "#DC2626"
        elif gap_act < 0 and evol_gap >= 0:
            txt_estado = "Recortó Faltante 🟢"
            col_estado = "#16A34A"
        elif gap_act >= 0 and evol_gap >= 0:
            txt_estado = "Amplió Superávit 🟢"
            col_estado = "#16A34A"
        else:
            txt_estado = "Cayó Superávit 🟡"
            col_estado = "#EAB308"

        st.markdown("<br>", unsafe_allow_html=True)

        # FILA 1: TARJETAS KPIS
        k1, k2, k3, k4 = st.columns([1, 1, 1.2, 1])
        
        with k1:
            st.markdown(f"""
            <div style="background-color: #F3F4F6; padding: 15px; border-radius: 10px; text-align: center;">
                <p style="margin:0; font-weight:bold; color:#374151;">VENTAS vs PPTO ACTUAL</p>
                <h3 style="margin:5px 0; color:#111827;">${v_act:,.0f}</h3>
                <p style="margin:0; color:#6B7280;">Ppto: ${ppto_act:,.0f}</p>
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
                <h2 style="margin:5px 0; color:{col_estado};">${evol_gap:+,.0f}</h2>
                <p style="margin:0; font-size:13px; font-weight:bold; color:{col_estado};">
                    {txt_estado}
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # FILA 2: GRÁFICO CENTRAL Y FILTRO
        c_graf, c_sem = st.columns([3, 1])

        def clasificar_evolucion(row):
            g_act = row['GAP_Ppto_Act']
            diff = row['Evolucion_GAP_$']
            if g_act < 0 and diff < 0:
                return "AUMENTÓ FALTANTE (🔴)"
            elif g_act < 0 and diff >= 0:
                return "RECORTÓ FALTANTE (🟢)"
            elif g_act >= 0 and diff >= 0:
                return "AMPLIÓ SUPERÁVIT (🟢)"
            else:
                return "CAYÓ SUPERÁVIT (🟡)"

        df_f['Tipo_Evolucion'] = df_f.apply(clasificar_evolucion, axis=1)

        with c_sem:
            st.markdown("#### FILTRAR EVOLUCIÓN GAP")
            filtro_sem = st.radio(
                "",
                ["Aumentaron Faltante (🔴)", "Recortaron Faltante / Mejoraron (🟢)", "Todas"],
                index=2
            )
            
            df_graf = df_f.copy()
            if "Aumentaron" in filtro_sem:
                df_graf = df_graf[df_graf['Tipo_Evolucion'].str.contains('AUMENTÓ|CAYÓ', regex=True)]
            elif "Recortaron" in filtro_sem:
                df_graf = df_graf[df_graf['Tipo_Evolucion'].str.contains('RECORTÓ|AMPLIÓ', regex=True)]

        with c_graf:
            fig_bar = px.bar(
                df_graf.sort_values(by='Evolucion_GAP_$'),
                y='Tienda', x='Evolucion_GAP_$',
                color='Tipo_Evolucion',
                color_discrete_map={
                    'RECORTÓ FALTANTE (🟢)': '#16A34A', 
                    'AMPLIÓ SUPERÁVIT (🟢)': '#15803D',
                    'AUMENTÓ FALTANTE (🔴)': '#DC2626',
                    'CAYÓ SUPERÁVIT (🟡)': '#EAB308'
                },
                orientation='h',
                title="EVOLUCIÓN DEL GAP VS PPTO (VARIACIÓN ENTRE SEMANA ACTUAL Y ANTERIOR)"
            )
            fig_bar.update_layout(height=max(350, len(df_graf) * 25))
            st.plotly_chart(fig_bar, use_container_width=True)

        # FILA 3: TABLA DETALLE
        st.markdown("### DETALLE DE EVOLUCIÓN DEL GAP POR TIENDA")

        tabla_det = df_f[[
            'Tienda', 'Gerente', 'Ppto_Real_Ant', 'Ventas_Real_Ant', 'GAP_Ppto_Ant',
            'Ppto_Real_Act', 'Ventas_Real_Act', 'GAP_Ppto_Act', 'Evolucion_GAP_$', 'Tipo_Evolucion'
        ]].copy()

        tabla_det.columns = [
            'Tienda', 'Gerente', 'Ppto Sem Ant', 'Ventas Sem Ant', 'GAP Sem Ant',
            'Ppto Sem Act', 'Ventas Sem Act', 'GAP Sem Act', 'Evolución GAP ($)', 'Estado'
        ]

        st.dataframe(
            tabla_det.style.format({
                'Ppto Sem Ant': '${:,.0f}',
                'Ventas Sem Ant': '${:,.0f}',
                'GAP Sem Ant': '${:,.0f}',
                'Ppto Sem Act': '${:,.0f}',
                'Ventas Sem Act': '${:,.0f}',
                'GAP Sem Act': '${:,.0f}',
                'Evolución GAP ($)': '${:+,.0f}'
            }),
            use_container_width=True
        )

else:
    st.info("👈 Por favor sube el archivo ANALISIS GAP.xlsx en el menú lateral.")