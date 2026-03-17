from pathlib import Path
import re
import sys

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db import DB_PATH, init_db, list_coupons
from scraper.banks import BANK_SOURCES

st.set_page_config(page_title="Cupones Delivery Chile", layout="wide")
st.title("Cupones Delivery Chile")
st.caption(f"Base de datos: {DB_PATH}")


@st.cache_data(ttl=30)
def load_data():
    init_db()
    rows = list_coupons()
    columns = ["id", "title", "code", "app", "discount", "issuer", "source", "url"]
    return pd.DataFrame(rows, columns=columns)


def apply_filters(df):
    st.sidebar.header("Filtros")
    apps = sorted(df["app"].dropna().unique().tolist())
    selected_apps = st.sidebar.multiselect("App", apps, default=apps)
    issuers = sorted([x for x in df["issuer"].dropna().unique().tolist() if str(x).strip()])
    selected_issuers = st.sidebar.multiselect("Banco/Tarjeta", issuers, default=issuers)
    sources = sorted(df["source"].dropna().unique().tolist())
    selected_sources = st.sidebar.multiselect("Fuente", sources, default=sources)
    min_discount = int(df["discount"].min()) if not df.empty else 0
    max_discount = int(df["discount"].max()) if not df.empty else 100
    if min_discount == max_discount:
        st.sidebar.caption(f"Descuento fijo: {min_discount}%")
        discount_range = (min_discount, max_discount)
    else:
        discount_range = st.sidebar.slider(
            "Rango de descuento (%)",
            min_value=min_discount,
            max_value=max_discount,
            value=(min_discount, max_discount),
        )
    query = st.sidebar.text_input("Buscar texto")

    filtered = df.copy()
    if selected_apps:
        filtered = filtered[filtered["app"].isin(selected_apps)]
    if issuers and selected_issuers:
        filtered = filtered[filtered["issuer"].isin(selected_issuers)]
    if selected_sources:
        filtered = filtered[filtered["source"].isin(selected_sources)]
    filtered = filtered[
        (filtered["discount"] >= discount_range[0]) & (filtered["discount"] <= discount_range[1])
    ]
    if query.strip():
        pattern = query.strip().lower()
        filtered = filtered[
            filtered["title"].str.lower().str.contains(pattern, na=False)
            | filtered["code"].str.lower().str.contains(pattern, na=False)
            | filtered["issuer"].str.lower().str.contains(pattern, na=False)
            | filtered["source"].str.lower().str.contains(pattern, na=False)
        ]

    return filtered


def _extract_weekday(text):
    lowered = str(text).lower()
    patterns = [
        ("lunes", r"\blunes\b"),
        ("martes", r"\bmartes\b"),
        ("miercoles", r"\bmi[eé]rcoles\b"),
        ("jueves", r"\bjueves\b"),
        ("viernes", r"\bviernes\b"),
        ("sabado", r"\bs[aá]bado\b"),
        ("domingo", r"\bdomingo\b"),
    ]
    for label, pattern in patterns:
        if re.search(pattern, lowered):
            return label
    if "todos los dias" in lowered or "todos los días" in lowered:
        return "todos los dias"
    return "no especificado"


def _benefit_value(row):
    parts = []
    discount = int(row.get("discount", 0) or 0)
    code = str(row.get("code", "") or "")
    is_real_code = bool(code) and not code.startswith("SRC-") and not code.startswith("BANK-")
    if discount > 0:
        parts.append(f"{discount}%")
    if is_real_code:
        parts.append(f"cupon {code}")
    if not parts:
        return "sin porcentaje/cupon"
    return " + ".join(parts)


df = load_data()
if df.empty:
    st.info("Aun no hay cupones guardados. Ejecuta `main.py` o `scheduler.py` para poblar datos.")
else:
    col1, col2, col3 = st.columns(3)
    col1.metric("Cupones Totales", int(len(df)))
    col2.metric("Apps Distintas", int(df["app"].nunique()))
    col3.metric("Fuentes", int(df["source"].nunique()))

    filtered_df = apply_filters(df)
    filtered_df = filtered_df.copy()
    filtered_df["beneficio"] = filtered_df.apply(_benefit_value, axis=1)
    filtered_df["banco"] = filtered_df["issuer"].fillna("").replace("", "sin banco")
    filtered_df["dia_semana"] = filtered_df["title"].apply(_extract_weekday)
    ordered_cols = [
        "app",
        "beneficio",
        "banco",
        "dia_semana",
        "title",
        "source",
        "url",
    ]
    filtered_df = filtered_df[ordered_cols]
    st.subheader("Cupones")
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "url": st.column_config.LinkColumn("URL", display_text="Abrir"),
        },
    )
    st.caption(f"Mostrando {len(filtered_df)} de {len(df)} cupones.")

    st.subheader("Cobertura de Bancos Monitoreados")
    monitored_issuers = sorted({source["issuer"] for source in BANK_SOURCES})
    counts = (
        df[df["issuer"].astype(str).str.strip() != ""]
        .groupby("issuer")
        .size()
        .to_dict()
    )
    coverage_rows = [
        {"issuer": issuer, "promos_detectadas": int(counts.get(issuer, 0))}
        for issuer in monitored_issuers
    ]
    st.dataframe(pd.DataFrame(coverage_rows), use_container_width=True, hide_index=True)

    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Descargar CSV",
        data=csv_data,
        file_name="cupones_filtrados.csv",
        mime="text/csv",
    )
