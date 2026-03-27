import streamlit as st
import pandas as pd
import json
import re
import urllib.parse

st.title("🔎 Limpiar Excel")

uploaded_file = st.file_uploader("Sube tu CSV", type=["csv"])

if uploaded_file:

    try:
        df = pd.read_csv(
            uploaded_file,
            sep=None,
            engine="python",
            encoding="utf-8",
            on_bad_lines="skip"
        )

        df.columns = df.columns.str.strip()

        st.success("Archivo cargado correctamente ✅")

        resultados = []

        # =========================
        # 🔄 Procesar columna A
        # =========================
        for _, row in df.iterrows():

            contenido = str(row.iloc[0])

            try:
                parsed = json.loads(contenido)
                passfile = parsed.get("passfile", "")

                if not passfile:
                    continue

                bloques = passfile.split("-----")

                for bloque in bloques:

                    data = {
                        "URL": None,
                        "HOST": None,
                        "LOGIN": None,
                        "USER": None,
                        "PASSAPORTE": None,
                        "PASS": None
                    }

                    host = re.search(r'Host:\s*(.+)', bloque)
                    login = re.search(r'Login:\s*(.+)', bloque)
                    password = re.search(r'Password:\s*(.+)', bloque)
                    user = re.search(r'User:\s*(.+)', bloque)
                    passaporte = re.search(r'Passaporte:\s*(.+)', bloque)

                    if host:
                        url = host.group(1).strip()
                        data["HOST"] = url
                        data["URL"] = url

                    if login:
                        data["LOGIN"] = login.group(1).strip()

                    if user:
                        data["USER"] = user.group(1).strip()

                    if password:
                        data["PASS"] = password.group(1).strip()

                    if passaporte:
                        data["PASSAPORTE"] = passaporte.group(1).strip()

                    # =========================
                    # 🧹 Eliminar null y vacíos
                    # =========================
                    data_limpio = {
                        k: v for k, v in data.items()
                        if v not in [None, ""]
                    }

                    if data_limpio:
                        resultados.append(data_limpio)

            except Exception:
                continue  # ← IMPORTANTE

        # =========================
        # 📊 Resultados
        # =========================
        st.subheader("Resultados limpios")
        st.write(f"Total objetos: {len(resultados)}")
        st.json(resultados[:10])

        # =========================
        # 📊 DataFrame
        # =========================
        if resultados:

            df_resultados = pd.DataFrame(resultados)

            # 🔒 Evitar error si falta URL
            df_resultados["URL"] = df_resultados.get("URL")

            # =========================
            # 🌐 Extraer dominio
            # =========================
            df_resultados["DOMINIO"] = df_resultados["URL"].apply(
                lambda x: urllib.parse.urlparse(x).netloc if pd.notnull(x) else None
            )

            # =========================
            # 🔍 Filtrar por keywords
            # =========================
            keywords = ["fifa", "bbva", "banorte", "santander", "inbursa", "scotiabank"]

            df_filtrado = df_resultados[
                df_resultados["URL"]
                .astype(str)
                .str.lower()
                .str.contains("|".join(keywords), na=False)
            ]

            if not df_filtrado.empty:

                # =========================
                # 📊 Conteo por URL
                # =========================
                st.subheader("📊 Conteo por URL (keywords)")

                conteo_url = (
                    df_filtrado
                    .groupby("URL")
                    .size()
                    .reset_index(name="TOTAL")
                    .sort_values(by="TOTAL", ascending=False)
                )

                st.dataframe(conteo_url)

                # =========================
                # 🌐 Conteo por dominio
                # =========================
                st.subheader("🌐 Conteo por dominio")

                conteo_dominios = (
                    df_filtrado
                    .groupby("DOMINIO")
                    .size()
                    .reset_index(name="TOTAL")
                    .sort_values(by="TOTAL", ascending=False)
                )

                st.dataframe(conteo_dominios)

                # =========================
                # 📦 JSON agrupado por dominio
                # =========================
                st.subheader("📦 JSON agrupado por dominio")

                agrupado = {}

                for dominio, grupo in df_filtrado.groupby("DOMINIO"):
                    agrupado[dominio] = grupo.to_dict(orient="records")

                st.json(agrupado)

                # =========================
                # 💾 Descargar JSON agrupado
                # =========================
                json_grouped = json.dumps(agrupado, indent=4, ensure_ascii=False)

                st.download_button(
                    "⬇️ Descargar JSON agrupado por dominio",
                    json_grouped,
                    file_name="agrupado_por_dominio.json",
                    mime="application/json"
                )

            else:
                st.warning("No hay coincidencias con las keywords")

        # =========================
        # 💾 Descargar JSON limpio
        # =========================
        json_final = json.dumps(resultados, indent=4, ensure_ascii=False)

        st.download_button(
            "⬇️ Descargar JSON limpio",
            json_final,
            file_name="resultado_limpio.json",
            mime="application/json"
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")