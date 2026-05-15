
import streamlit as st
import pandas as pd
import folium

from io import BytesIO
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, A4


# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================

st.set_page_config(
    page_title="Mapa de Postos",
    layout="wide"
)


# =========================
# LEITURA DOS DADOS
# =========================

@st.cache_data
def carregar_dados():

    df = pd.read_excel("mapa_global_atualizado.xlsx")

    # =========================
    # PADRONIZAR COORDENADAS
    # =========================

    df["Latitude"] = (
        df["Latitude"]
        .astype(str)
        .str.replace(",", ".", regex=False)
    )

    df["Longitude"] = (
        df["Longitude"]
        .astype(str)
        .str.replace(",", ".", regex=False)
    )

    # Converter para float
    df["Latitude"] = pd.to_numeric(
        df["Latitude"],
        errors="coerce"
    )

    df["Longitude"] = pd.to_numeric(
        df["Longitude"],
        errors="coerce"
    )

    return df[
        [
            "Cidade",
            "Posto",
            "Endereço",
            "Localização google maps",
            "Forma de coleta",
            "TD",
            "Territórios de Desenvolvimento",
            "Central de Emissão",
            "Latitude",
            "Longitude"
        ]
    ]


df = carregar_dados()


# =========================
# TÍTULOS
# =========================

st.title("Instituto de Cidadania Digital - Félix Pacheco")
st.subheader("Unidades de Serviços Digitais")


# =========================
# FILTROS
# =========================

col1, col2, col3 = st.columns(3)

with col1:

    territorio = st.selectbox(
        "Território de Desenvolvimento",
        ["Todos"] + sorted(
            df["Territórios de Desenvolvimento"]
            .dropna()
            .astype(str)
            .unique()
        )
    )

with col2:

    tipo_posto = st.selectbox(
        "Tipo de Posto",
        ["Todos"] + sorted(
            df["Forma de coleta"]
            .dropna()
            .astype(str)
            .unique()
        )
    )

with col3:

    central = st.selectbox(
        "Central de Emissão",
        ["Todos"] + sorted(
            df["Central de Emissão"]
            .dropna()
            .astype(str)
            .unique()
        )
    )


# =========================
# APLICAR FILTROS
# =========================

if territorio != "Todos":

    df = df.query(
        "`Territórios de Desenvolvimento` == @territorio"
    )

if tipo_posto != "Todos":

    df = df.query(
        "`Forma de coleta` == @tipo_posto"
    )

if central != "Todos":

    df = df.query(
        "`Central de Emissão` == @central"
    )


# =========================
# INDICADORES
# =========================

TOTAL_MUNICIPIOS_ESTADO = 224

municipios_digitais = (
    df[
        df["Forma de coleta"]
        .astype(str)
        .str.contains("digital", case=False, na=False)
    ]["Cidade"]
    .nunique()
)

postos_digitais = len(
    df[
        df["Forma de coleta"]
        .astype(str)
        .str.contains("digital", case=False, na=False)
    ]
)

municipios_filtrados = df["Cidade"].nunique()

meta_atual = df["Cidade"].nunique()

if meta_atual == 0:
    meta_atual = 1

municipios_sem_digital = (
    meta_atual - municipios_digitais
)

percentual_digital = (
    municipios_digitais / meta_atual
) * 100


# =========================
# MÉTRICAS
# =========================

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Postos digitais",
    postos_digitais
)

col2.metric(
    "Municípios digitais",
    municipios_digitais
)

col3.metric(
    "Municípios sem digital",
    municipios_sem_digital
)

col4.metric(
    "Cobertura digital",
    f"{percentual_digital:.1f}%"
)

st.progress(percentual_digital / 100)

st.caption(
    f"{municipios_digitais} de "
    f"{meta_atual} municípios "
    f"com posto digital"
)

st.divider()


# =========================
# MAPA
# =========================

st.subheader("Mapa dos Postos")

mapa = folium.Map(
    location=[-5.20, -42.75],
    zoom_start=7
)

marker_cluster = MarkerCluster().add_to(mapa)

for _, row in df.iterrows():

    lat = row["Latitude"]
    lon = row["Longitude"]

    # Ignorar coordenadas inválidas
    if pd.isna(lat) or pd.isna(lon):
        continue

    forma = str(row["Forma de coleta"]).lower()

    if "digital" in forma:
        cor = "green"

    elif "manual" in forma:
        cor = "blue"

    else:
        cor = "red"

    popup = f"""
    <b>{row['Cidade']}</b><br>
    <b>Posto:</b> {row['Posto']}<br>
    <b>Coleta:</b> {row['Forma de coleta']}<br>
    <b>Central:</b> {row['Central de Emissão']}
    """

    folium.Marker(
        location=[lat, lon],
        popup=popup,
        tooltip=row["Cidade"],
        icon=folium.Icon(color=cor)
    ).add_to(marker_cluster)

st_folium(
    mapa,
    width="100%",
    height=600
)

st.divider()


# =========================
# TABELA
# =========================

df = df.reset_index(drop=True)

df.index = df.index + 1

df_tabela = df[
    [
        "Cidade",
        "Posto",
        "Forma de coleta",
        "Central de Emissão",
        "Territórios de Desenvolvimento"
    ]
]

st.subheader("Tabela de Postos")

st.dataframe(
    df_tabela,
    use_container_width=True
)


# =========================
# DOWNLOAD PDF
# =========================

st.divider()

if st.button("Gerar relatório PDF"):

    pdf_buffer = BytesIO()

    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=landscape(A4),
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()

    elementos = []

    titulo = Paragraph(
        "Relatório de Postos de Identificação",
        styles["Title"]
    )

    elementos.append(titulo)

    elementos.append(Spacer(1, 12))

    filtros_texto = f"""
    Território: {territorio}<br/>
    Tipo de posto: {tipo_posto}<br/>
    Central de emissão: {central}<br/>
    Quantidade total de postos: {len(df)}<br/>
    Municípios com posto digital: {municipios_digitais} de {TOTAL_MUNICIPIOS_ESTADO}<br/>
    Cobertura digital estadual: {percentual_digital:.1f}%
    """

    filtros = Paragraph(
        filtros_texto,
        styles["BodyText"]
    )

    elementos.append(filtros)

    elementos.append(Spacer(1, 12))

    dados_tabela = [[
        "Nº",
        "Município",
        "Central de Emissão",
        "Tipo de Posto"
    ]]

    for indice, row in df.iterrows():

        dados_tabela.append([
            str(indice),
            str(row["Cidade"]),
            str(row["Central de Emissão"]),
            str(row["Forma de coleta"])
        ])

    tabela = Table(
        dados_tabela,
        colWidths=[40, 180, 180, 140]
    )

    tabela.setStyle(TableStyle([

        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),

        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),

        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

        ("FONTSIZE", (0, 0), (-1, -1), 9),

        ("GRID", (0, 0), (-1, -1), 1, colors.black),

        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),

    ]))

    elementos.append(tabela)

    doc.build(elementos)

    st.download_button(
        label="Baixar PDF",
        data=pdf_buffer.getvalue(),
        file_name="relatorio_postos.pdf",
        mime="application/pdf"
    )

