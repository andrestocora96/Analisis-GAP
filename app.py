import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(page_title="Tablero de Desempeño de Ventas", layout="wide")

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>TABLERO DE DESEMPEÑO DE VENTAS: ANÁLISIS GAP SEMANAL</h2>", unsafe_allow_html=True)

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
    
    # Cargar Maestro BASE DE DATOS
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
        
        # Parsear variables
        df['Ventas_Real'] = df['Ventas Act'].apply(limpiar_monto)
        df['Ppto_Real'] = df['Ppto'].apply(limpiar_monto)
        df['Transacciones_Real'] = pd.to_numeric(df['Transacciones Act'], errors='coerce').fillna(0)
        df['Ticket_Real'] = pd.to_numeric(df['Ticket promedio Act'], errors='coerce').fillna(0)
        
        dfs.append(df)
        
    if dfs:
        df_tot = pd.concat(dfs, ignore_index=True)
        if not df_bd.empty:
            cols_bd = ['Tienda_Clean', 'Gerente', 'Supervisor', 'Ciudad', 'Segmento', 'Comparable ', 'Pareto']
            cols_bd = [c for c in cols_bd if c in df_bd.columns]
            df_tot = pd.merge(df_tot, df_bd[cols_bd], on='Tienda_Clean', how='left')
        return df_tot, hojas
    return pd.DataFrame(), []

# Carga de archivo en la barra lateral
st.sidebar.header("📁 Cargar Excel")
uploaded_file = st.sidebar.file_uploader("Sube el archivo ANALISIS GAP.xlsx", type=['xlsx'])

if uploaded_file:
    df_tot, lista_ciclos = cargar_datos(uploaded_file)
    
    if len(lista_ciclos) >= 2:
        c_act = st.sidebar.selectbox("Semana/Ciclo Actual:", lista_ciclos, index=len(lista_ciclos)-1)
        c_ant = st.sidebar.selectbox("Semana/Ciclo Anterior:", lista_ciclos, index=max(0, len(lista_ciclos)-2))
        
        # Datasets
        df_act = df_tot[df_tot['Ciclo'] == c_act].copy()
        df_ant = df_tot[df_tot['Ciclo'] == c_ant].copy()
        
        # Cruce
        df_merged = pd.merge(
            df_act[['Tienda_Clean', 'Tienda', 'Gerente', 'Supervisor', 'Ciudad', 'Segmento', 'Pareto', 'Ventas_Real', 'Ppto_Real', 'Transacciones_Real', 'Ticket_Real']],
            df_ant[['Tienda_Clean', 'Ventas_Real', 'Ppto_Real', 'Transacciones_Real', 'Ticket_Real']],
            on='Tienda_Clean',
            suffixes=('_Act', '_Ant'),
            how='inner'
        )
        
        # FILTROS SUPERIORES EN LÍNEA (Como la imagen de referencia)
        st.markdown("---")
        f1, f2, f3 = st.columns(3)
        with f1:
            gerentes = ["Todos"] + sorted([x for x in df_merged['Gerente'].dropna().unique()])
            sel_ger = st.selectbox("GERENTE SUPERVISOR (Desglose 1):", gerentes)
        with f2:
            supervisores = ["Todos"] + sorted([x for x in df_merged['Supervisor'].dropna().unique()])
            sel_sup = st.selectbox("SUPERVISOR:", supervisores)
        with f3:
            tiendas = ["Todas"] + sorted([x for x in df_merged['Tienda'].dropna().unique()])
            sel_tienda = st.selectbox("TIENDA / PUNTO (Desglose 2):", tiendas)
            
        # Filtrado
        df_f = df_merged.copy()
        if sel_ger != "Todos":
            df_f = df_f[df_f['Gerente'] == sel_ger]
        if sel_sup != "Todos":
            df_f = df_f[df_f['Supervisor'] == sel_sup]
        if sel_tienda != "Todas":
            df_f = df_f[df_f['Tienda'] == sel_tienda]

        # Cálculos de Indicadores Totales
        v_act = df_f['Ventas_Real_Act'].sum()
        v_ant = df_f['Ventas_Real_Ant'].sum()
        ppto_act = df_f['Ppto_Real_Act'].sum()
        trans_act = df_f['Transacciones_Real_Act'].sum()
        trans_ant = df_f['Transacciones_Real_Ant'].sum()
        
        var_v_pct = ((v_act - v_ant) / v_ant * 100) if v_ant > 0 else 0.0
        cumpl_ppto = (v_act / ppto_act * 100) if ppto_act > 0 else 0.0
        var_trans_pct = ((trans_act - trans_ant) / trans_ant * 100) if trans_ant > 0 else 0.0

        st.markdown("<br>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # FILA 1: TARJETAS DE KPIS (VENTAS, CRECIMIENTO, PPTO, TRANSACCIONES)
        # -------------------------------------------------------------
        k1, k2, k3, k4 = st.columns([1, 1, 1.2, 1])
        
        with k1:
            st.markdown(f"""
            <div style="background-color: #F3F4F6; padding: 15px; border-radius: 10px; text-align: center;">
                <p style="margin:0; font-weight:bold; color:#374151;">VENTAS ACTUALES (SEM. ACTUAL)</p>
                <h2 style="margin:5px 0; color:#111827;">${v_act:,.0f}</h2>
                <p style="margin:0; font-weight:bold; color:{'#16A34A' if var_v_pct>=0 else '#DC2626'};">
                    {'⬆' if var_v_pct>=0 else '⬇'} {var_v_pct:+.1f}% vs. Anterior
                </p>
            </div>
            """, unsafe_allow_html=True)

        with k2:
            st.markdown(f"""
            <div style="background-color: #F3F4F6; padding: 15px; border-radius: 10px; text-align: center;">
                <p style="margin:0; font-weight:bold; color:#374151;">CRECIMIENTO % (VS SEM. ANTERIOR)</p>
                <h1 style="margin:10px 0; color:{'#16A34A' if var_v_pct>=0 else '#DC2626'};">{var_v_pct:+.1f}%</h1>
            </div>
            """, unsafe_allow_html=True)

        with k3:
            # Gráfico de Medidor / Gauge de Cumplimiento
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = cumpl_ppto,
                number = {'suffix': "%", 'valueformat': ".1f"},
                title = {'text': "CUMPLIMIENTO PPTO", 'font': {'size': 13}},
                gauge = {
                    'axis': {'range': [0, 120]},
                    'bar': {'color': "#EAB308" if cumpl_ppto < 100 else "#16A34A"},
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
                <p style="margin:0; font-weight:bold; color:#374151;">TOTAL TRANSACCIONES</p>
                <h2 style="margin:5px 0; color:#111827;">{trans_act:,.0f}</h2>
                <p style="margin:0; font-weight:bold; color:{'#16A34A' if var_trans_pct>=0 else '#DC2626'};">
                    {var_trans_pct:+.1f}%
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # -------------------------------------------------------------
        # FILA 2: GRÁFICO CENTRAL + SEMÁFORO DE FILTRO
        # -------------------------------------------------------------
        c_graf, c_sem = st.columns([3, 1])

        df_f['Diff_Ventas_$'] = df_f['Ventas_Real_Act'] - df_f['Ventas_Real_Ant']
        df_f['Diff_Pct'] = ((df_f['Ventas_Real_Act'] - df_f['Ventas_Real_Ant']) / df_f['Ventas_Real_Ant'].replace(0, 1)) * 100
        df_f['Tipo_Crecimiento'] = df_f['Diff_Ventas_$'].apply(lambda x: 'CRECIMIENTO ($)' if x >= 0 else 'DECRECIMIENTO ($)')

        with c_sem:
            st.markdown("#### SEMÁFORO DE TIENDA")
            filtro_semaforo = st.radio(
                "",
                ["Crecimiento", "Decrecimiento", "Todas"],
                index=2
            )
            
            df_graf = df_f.copy()
            if filtro_semaforo == "Crecimiento":
                df_graf = df_graf[df_graf['Diff_Ventas_$'] >= 0]
            elif filtro_semaforo == "Decrecimiento":
                df_graf = df_graf[df_graf['Diff_Ventas_$'] < 0]

        with c_graf:
            fig_bar = px.bar(
                df_graf.sort_values(by='Diff_Ventas_$'),
                y='Tienda', x='Diff_Ventas_$',
                color='Tipo_Crecimiento',
                color_discrete_map={'CRECIMIENTO ($)': '#16A34A', 'DECRECIMIENTO ($)': '#DC2626'},
                orientation='h',
                title="CRECIMIENTO/DECRECIMIENTO DE VENTAS POR TIENDA (VS SEMANA ANTERIOR)"
            )
            fig_bar.update_layout(height=max(350, len(df_graf) * 25))
            st.plotly_chart(fig_bar, use_container_width=True)

        # -------------------------------------------------------------
        # FILA 3: TABLA DETALLE DE TIENDAS CON COLORES DE ESTADO
        # -------------------------------------------------------------
        st.markdown("### DETALLE DE TIENDAS Y ESTADO DE COMPARACIÓN")

        def evaluar_estado(row):
            cumple = row['Ventas_Real_Act'] >= row['Ppto_Real_Act']
            crece = row['Diff_Ventas_$'] >= 0
            if cumple and crece:
                return "Cumple Ppto y crece 🟢"
            elif cumple and not crece:
                return "Cumple Ppto pero decrece 🟡"
            elif not cumple and crece:
                return "No cumple Ppto pero crece 🟧"
            else:
                return "No cumple Ppto y decrece 🔴"

        df_f['Estado Comparación'] = df_f.apply(evaluar_estado, axis=1)
        df_f['Vs Ppto $'] = df_f['Ventas_Real_Act'] - df_f['Ppto_Real_Act']

        tabla_mostrar = df_f[[
            'Tienda', 'Gerente', 'Ventas_Real_Act', 'Diff_Pct', 'Vs Ppto $', 'Estado Comparación'
        ]].copy()

        tabla_mostrar.columns = ['Tienda', 'Gerente', 'Ventas Act', '% Var Vs Sem Ant', 'Vs Ppto $', 'Estado Comparación']

        st.dataframe(
            tabla_mostrar.style.format({
                'Ventas Act': '${:,.0f}',
                '% Var Vs Sem Ant': '{:+.1f}%',
                'Vs Ppto $': '${:,.0f}'
            }),
            use_container_width=True
        )

else:
    st.info("👈 Por favor sube el archivo ANALISIS GAP.xlsx en el menú lateral.")