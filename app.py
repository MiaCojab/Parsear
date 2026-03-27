import streamlit as st
import pandas as pd
import json
import re
import urllib.parse

st.title("🔎 Limpiar Excel")

uploaded_file = st.file_uploader("Sube tu CSV", type=["csv"])


# =========================
# ⚡ CACHE (CLAVE)
# =========================
@st.cache_data
def procesar_csv(file):

    df = pd.read_csv(
        file,
        sep=None,
        engine="python",
        encoding="utf-8",
        on_bad_lines="skip"
    )

    df.columns = df.columns.str.strip()

    resultados = []

    for _, row in df.iterrows():

        contenido = str(row.iloc[0])

        try:
            parsed = json.loads(contenido)
            passfile = parsed.get("passfile", "")

            if not passfile:
                continue

            bloques = passfile.split("-----")

            for bloque in bloques:

                data = {}

                host = re.search(r'Host:\s*(.+)', bloque)
                login = re.search(r'Login:\s*(.+)', bloque)
                password = re.search(r'Password:\s*(.+)', bloque)
                user = re.search(r'User:\s*(.+)', bloque)
                passaporte = re.search(r'Passaporte:\s*(.+)', bloque)

                if host:
                    url = host.group(1).strip()
                    data["URL"] = url
                    data["HOST"] = url

                if login:
                    data["LOGIN"] = login.group(1).strip()

                if user:
                    data["USER"] = user.group(1).strip()

                if password:
                    data["PASS"] = password.group(1).strip()

                if passaporte:
                    data["PASSAPORTE"] = passaporte.group(1).strip()

                if data:
                    resultados.append(data)

        except:
            continue

    return resultados


# =========================
# 🚀 EJECUCIÓN
# =========================
if uploaded_file:

    resultados = procesar_csv(uploaded_file)

    st.success(f"Archivo procesado ✅ | Total: {len(resultados)}")

    # 🔹 Vista previa ligera (NO JSON pesado)
    st.subheader("Vista previa")
    st.write(resultados[:5])

    if resultados:

        df_resultados = pd.DataFrame(resultados)

        df_resultados["DOMINIO"] = df_resultados["URL"].apply(
            lambda x: urllib.parse.urlparse(x).netloc if pd.notnull(x) else None
        )

        keywords = ["fifa", "bbva", "banorte", "santander", "inbursa", "scotiabank"]

        df_filtrado = df_resultados[
            df_resultados["URL"]
            .astype(str)
            .str.lower()
            .str.contains("|".join(keywords), na=False)
        ]

        # =========================
        # 📊 TABS = UI ESTABLE
        # =========================
        tab1, tab2, tab3 = st.tabs(["📊 URLs", "🌐 Dominios", "📦 JSON"])

        with tab1:
            if not df_filtrado.empty:
                conteo_url = (
                    df_filtrado.groupby("URL")
                    .size()
                    .reset_index(name="TOTAL")
                    .sort_values(by="TOTAL", ascending=False)
                )
                st.dataframe(conteo_url)

        with tab2:
            if not df_filtrado.empty:
                conteo_dominios = (
                    df_filtrado.groupby("DOMINIO")
                    .size()
                    .reset_index(name="TOTAL")
                    .sort_values(by="TOTAL", ascending=False)
                )
                st.dataframe(conteo_dominios)

        with tab3:
            if not df_filtrado.empty:
                agrupado = {
                    dominio: grupo.to_dict(orient="records")
                    for dominio, grupo in df_filtrado.groupby("DOMINIO")
                }

                st.write("JSON listo para descarga")

                json_grouped = json.dumps(agrupado, indent=2, ensure_ascii=False)

                st.download_button(
                    "⬇️ Descargar JSON agrupado",
                    json_grouped,
                    file_name="agrupado.json",
                    mime="application/json"
                )

    # =========================
    # 💾 DESCARGA FINAL
    # =========================
    json_final = json.dumps(resultados, indent=2, ensure_ascii=False)

    st.download_button(
        "⬇️ Descargar JSON limpio",
        json_final,
        file_name="resultado.json",
        mime="application/json"
    )*
