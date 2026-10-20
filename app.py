import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Rekapan Transaksi Gudang", page_layout="wide")

st.markdown("""
<style>
    .main .block-container { padding-top: 1.5rem; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("📦 Dashboard Rekapan Transaksi Gudang")
st.caption("Monitoring Outbound STO, Quantities, & Distribution")

# URL Google Sheets CSV export
SHEET_URL = "https://docs.google.com/spreadsheets/d/1p34-rItGV12l15ArIroyJdsYWDPL0rOyrj-ekqw3baY/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        # Clean column names (strip whitespace)
        df.columns = df.columns.str.strip()
        
        # Fuzzy matching untuk mencari kolom Supplying Plant / Pengirim
        supplying_col = None
        for col in df.columns:
            cleaned_col_lower = col.lower().replace(" ", "").replace("/", "").replace("_", "")
            if "supplying" in cleaned_col_lower or "pengirim" in cleaned_col_lower:
                supplying_col = col
                break
        
        if supplying_col and supplying_col != "Supplying Plant/Pengirim":
            df.rename(columns={supplying_col: "Supplying Plant/Pengirim"}, inplace=True)
            
        # Ensure numerical columns
        for num_col in ['Document', 'Material', 'Qty PGI']:
            if num_col in df.columns:
                df[num_col] = pd.to_numeric(df[num_col], errors='coerce').fillna(0)
                
        return df
    except Exception as e:
        st.error(f"Gagal memuat data dari Google Sheets: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("Data kosong atau gagal diakses. Pastikan pengaturan Google Sheets diset ke 'Anyone with the link' (Viewer).")
    st.stop()

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Filter Data Transaksi")

# 1. Filter Periode
periode_options = ["Semua"] + sorted([str(x) for x in df['Periode'].dropna().unique()]) if 'Periode' in df.columns else ["Semua"]
selected_periode = st.sidebar.selectbox("Periode:", periode_options)

df_filtered = df.copy()
if selected_periode != "Semua":
    df_filtered = df_filtered[df_filtered['Periode'].astype(str) == selected_periode]

# 2. Filter Regional
regional_options = ["Semua"] + sorted([str(x) for x in df_filtered['Regional'].dropna().unique()]) if 'Regional' in df_filtered.columns else ["Semua"]
selected_regional = st.sidebar.selectbox("Regional:", regional_options)

if selected_regional != "Semua":
    df_filtered = df_filtered[df_filtered['Regional'].astype(str) == selected_regional]

# 3. Filter Supplying Plant / Pengirim
supplying_col_name = "Supplying Plant/Pengirim" if "Supplying Plant/Pengirim" in df_filtered.columns else None

if supplying_col_name:
    plant_list = sorted([str(x) for x in df_filtered[supplying_col_name].dropna().unique() if str(x).strip() != ""])
    plant_options = ["Semua"] + plant_list
    selected_plant = st.sidebar.selectbox("Supplying Plant / Pengirim:", plant_options)
    
    if selected_plant != "Semua":
        df_filtered = df_filtered[df_filtered[supplying_col_name].astype(str) == selected_plant]
else:
    st.sidebar.warning("Kolom Supplying Plant/Pengirim tidak ditemukan di data.")

# 4. Filter Category
category_options = ["Semua"] + sorted([str(x) for x in df_filtered['Categori'].dropna().unique()]) if 'Categori' in df_filtered.columns else ["Semua"]
selected_category = st.sidebar.selectbox("Category:", category_options)

if selected_category != "Semua":
    df_filtered = df_filtered[df_filtered['Categori'].astype(str) == selected_category]

# --- KPI METRICS ---
col1, col2, col3, col4 = st.columns(4)
total_qty = int(df_filtered['Qty PGI'].sum()) if 'Qty PGI' in df_filtered.columns else 0
total_mat = int(df_filtered['Material'].sum()) if 'Material' in df_filtered.columns else 0
total_doc = int(df_filtered['Document'].sum()) if 'Document' in df_filtered.columns else 0
total_rows = len(df_filtered)

col1.metric("Total Qty PGI", f"{total_qty:,}")
col2.metric("Total Material", f"{total_mat:,}")
col3.metric("Total Document", f"{total_doc:,}")
col4.metric("Baris Transaksi", f"{total_rows:,}")

st.markdown("---")

# --- DETAIL TABEL & GRAFIK SUPPLYING PLANT / PENGIRIM ---
st.subheader("🏢 Detail & Distribusi Supplying Plant / Pengirim")

if supplying_col_name and supplying_col_name in df_filtered.columns:
    # 1. Tabel Agregasi Detail Per Supplying Plant
    plant_summary = df_filtered.groupby(supplying_col_name).agg(
        Total_Qty_PGI=('Qty PGI', 'sum'),
        Total_Material=('Material', 'sum'),
        Total_Document=('Document', 'sum'),
        Jumlah_Transaksi=('Qty PGI', 'count')
    ).reset_index().sort_values(by='Total_Qty_PGI', ascending=False)

    col_chart, col_table = st.columns([1, 1])

    with col_chart:
        st.markdown("##### 📊 Top Supplying Plant Berdasarkan Qty PGI")
        fig_plant = px.bar(
            plant_summary.head(15),
            x=supplying_col_name,
            y='Total_Qty_PGI',
            color=supplying_col_name,
            text_auto='.2s',
            labels={'Total_Qty_PGI': 'Total Qty PGI', supplying_col_name: 'Supplying Plant / Pengirim'},
            title="Breakdown Qty PGI per Plant Pengirim"
        )
        fig_plant.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig_plant, use_container_width=True)

    with col_table:
        st.markdown("##### 📋 Ringkasan Angka Detail Per Plant")
        st.dataframe(
            plant_summary.rename(columns={
                supplying_col_name: 'Supplying Plant / Pengirim',
                'Total_Qty_PGI': 'Qty PGI',
                'Total_Material': 'Material',
                'Total_Document': 'Document',
                'Jumlah_Transaksi': 'Baris Data'
            }),
            use_container_width=True,
            hide_index=True
        )
else:
    st.info("Kolom Supplying Plant / Pengirim tidak tersedia untuk menampilkan breakdown detail.")

st.markdown("---")

# --- GRAFIK REGIONAL & BRAND ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🏢 Qty PGI berdasarkan Regional")
    if 'Regional' in df_filtered.columns and 'Categori' in df_filtered.columns:
        fig_reg = px.bar(
            df_filtered,
            x='Regional',
            y='Qty PGI',
            color='Categori',
            barmode='group',
            text_auto='.2s',
            title="Qty PGI per Regional & Kategori"
        )
        st.plotly_chart(fig_reg, use_container_width=True)

with col_right:
    st.subheader("🏷️ Top 10 Brand berdasarkan Qty PGI")
    if 'Brand' in df_filtered.columns and 'Qty PGI' in df_filtered.columns:
        brand_df = df_filtered.groupby('Brand')['Qty PGI'].sum().reset_index().sort_values(by='Qty PGI', ascending=False).head(10)
        fig_brand = px.bar(
            brand_df,
            x='Qty PGI',
            y='Brand',
            orientation='h',
            text_auto='.2s',
            color='Qty PGI',
            color_continuous_scale='Viridis'
        )
        fig_brand.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_brand, use_container_width=True)

# --- TABEL DATA TRANSPOSE / RAW DATA ---
st.subheader("📋 Log Detail Transaksi Gudang")
st.dataframe(df_filtered, use_container_width=True)
