import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. KONFIGURASI HALAMAN
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Rekapan Transaksi Gudang",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. LOAD DATA DARI GOOGLE SHEETS
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600)  # Cache data selama 10 menit
def load_data(sheet_url):
    # Mengubah URL Google Sheets biasa menjadi format CSV export
    if "/edit" in sheet_url:
        export_url = sheet_url.split("/edit")[0] + "/export?format=csv"
    else:
        export_url = sheet_url
        
    df = pd.read_csv(export_url)
    
    # Cleaning nama kolom (menghapus spasi berlebih)
    df.columns = df.columns.str.strip()
    
    # Memastikan kolom angka bertipe numerik
    numeric_cols = ['Document', 'Material', 'Qty PGI']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    return df

# URL Google Sheets Publik Anda
SHEET_URL = "https://docs.google.com/spreadsheets/d/1p34-rItGV12l15ArIroyJdsYWDPL0rOyrj-ekqw3baY/edit?usp=sharing"

try:
    df_raw = load_data(SHEET_URL)
except Exception as e:
    st.error(f"Gagal memuat data dari Google Sheets. Pastikan akses spreadsheet sudah di-set ke 'Anyone with link can view'. Detail: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 3. SIDEBAR / FILTER
# -----------------------------------------------------------------------------
st.sidebar.header("🔍 Filter Data Transaksi")

# Filter Periode
periode_options = ["Semua"] + list(df_raw['Periode'].dropna().unique()) if 'Periode' in df_raw.columns else ["Semua"]
selected_periode = st.sidebar.selectbox("Periode:", periode_options)

# Filter Regional
regional_options = ["Semua"] + list(df_raw['Regional'].dropna().unique()) if 'Regional' in df_raw.columns else ["Semua"]
selected_regional = st.sidebar.selectbox("Regional:", regional_options)

# Filter Supplying Plant
plant_options = ["Semua"] + list(df_raw['Supplying Plant/Pengirim'].dropna().unique()) if 'Supplying Plant/Pengirim' in df_raw.columns else ["Semua"]
selected_plant = st.sidebar.selectbox("Supplying Plant / Pengirim:", plant_options)

# Filter Group Penerima
penerima_options = ["Semua"] + list(df_raw['Group-Penerima'].dropna().unique()) if 'Group-Penerima' in df_raw.columns else ["Semua"]
selected_penerima = st.sidebar.selectbox("Group Penerima:", penerima_options)

# Filter Category
category_options = ["Semua"] + list(df_raw['Categori'].dropna().unique()) if 'Categori' in df_raw.columns else ["Semua"]
selected_category = st.sidebar.selectbox("Kategori:", category_options)

# Filter Brand (Multiselect)
brand_options = list(df_raw['Brand'].dropna().unique()) if 'Brand' in df_raw.columns else []
selected_brand = st.sidebar.multiselect("Brand:", brand_options, default=[])

# Apply Filter ke DataFrame
df_filtered = df_raw.copy()

if selected_periode != "Semua":
    df_filtered = df_filtered[df_filtered['Periode'] == selected_periode]
if selected_regional != "Semua":
    df_filtered = df_filtered[df_filtered['Regional'] == selected_regional]
if selected_plant != "Semua":
    df_filtered = df_filtered[df_filtered['Supplying Plant/Pengirim'] == selected_plant]
if selected_penerima != "Semua":
    df_filtered = df_filtered[df_filtered['Group-Penerima'] == selected_penerima]
if selected_category != "Semua":
    df_filtered = df_filtered[df_filtered['Categori'] == selected_category]
if selected_brand:
    df_filtered = df_filtered[df_filtered['Brand'].isin(selected_brand)]

# -----------------------------------------------------------------------------
# 4. MAIN CONTENT & KPI CARDS
# -----------------------------------------------------------------------------
st.title("📦 Dashboard Rekapan Transaksi Gudang")
st.markdown("Analisis real-time pergerakan barang, dokumen, dan kuantitas PGI.")

# Agregasi KPI
total_qty = int(df_filtered['Qty PGI'].sum()) if 'Qty PGI' in df_filtered.columns else 0
total_mat = int(df_filtered['Material'].sum()) if 'Material' in df_filtered.columns else 0
total_doc = int(df_filtered['Document'].sum()) if 'Document' in df_filtered.columns else 0
total_row = len(df_filtered)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Total Qty PGI", value=f"{total_qty:,}")
with col2:
    st.metric(label="Total Material", value=f"{total_mat:,}")
with col3:
    st.metric(label="Total Dokumen", value=f"{total_doc:,}")
with col4:
    st.metric(label="Jumlah Baris Data", value=f"{total_row:,}")

st.divider()

# -----------------------------------------------------------------------------
# 5. CHART VISUALISASI
# -----------------------------------------------------------------------------
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("📊 Top 10 Brand berdasarkan Qty PGI")
    if not df_filtered.empty and 'Brand' in df_filtered.columns:
        brand_qty = df_filtered.groupby('Brand')['Qty PGI'].sum().reset_index()
        brand_qty = brand_qty.sort_values(by='Qty PGI', ascending=False).head(10)
        
        fig_brand = px.bar(
            brand_qty, 
            x='Qty PGI', 
            y='Brand', 
            orientation='h',
            text='Qty PGI',
            color='Qty PGI',
            color_continuous_scale='Blues'
        )
        fig_brand.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
        st.plotly_chart(fig_brand, use_container_width=True)
    else:
        st.info("Data tidak tersedia untuk menampilkan grafik.")

with chart_col2:
    st.subheader("🍕 Distribusi Kategori")
    if not df_filtered.empty and 'Categori' in df_filtered.columns:
        cat_qty = df_filtered.groupby('Categori')['Qty PGI'].sum().reset_index()
        
        fig_cat = px.pie(
            cat_qty, 
            names='Categori', 
            values='Qty PGI', 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info("Data tidak tersedia untuk menampilkan grafik.")

# Bar Chart Regional per Qty PGI
st.subheader("🗺️ Qty PGI berdasarkan Regional")
if not df_filtered.empty and 'Regional' in df_filtered.columns:
    regional_qty = df_filtered.groupby(['Regional', 'Categori'])['Qty PGI'].sum().reset_index()
    fig_regional = px.bar(
        regional_qty,
        x='Regional',
        y='Qty PGI',
        color='Categori' if 'Categori' in df_filtered.columns else None,
        barmode='group',
        text='Qty PGI',
        labels={'Qty PGI': 'Total Qty PGI', 'Regional': 'Regional'},
        color_discrete_sequence=px.colors.qualitative.Set1
    )
    fig_regional.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    fig_regional.update_layout(xaxis={'categoryorder': 'total descending'})
    st.plotly_chart(fig_regional, use_container_width=True)
else:
    st.info("Data tidak tersedia untuk menampilkan grafik Regional.")

st.divider()

# -----------------------------------------------------------------------------
# 6. TABEL DATA INTERAKTIF
# -----------------------------------------------------------------------------
st.subheader("📋 Detail Tabel Data Transaksi")

# Pilihan Download CSV
csv_data = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Export Data Terfilter ke CSV",
    data=csv_data,
    file_name="Rekapan_Transaksi_Filtered.csv",
    mime="text/csv",
)

# Tampilan Tabel Interaktif
st.dataframe(
    df_filtered,
    use_container_width=True,
    hide_index=True
)
