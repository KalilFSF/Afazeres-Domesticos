import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Afazeres Domésticos", page_icon="🧹", layout="wide")

ARQUIVO_DATA = "Tabela 1.1.1.xls"

@st.cache_data
def carregar_data(caminho):
    xls = pd.ExcelFile(caminho)
    dados = []

    for ano in xls.sheet_names:
        if "(CV)" in ano:
            continue

        bruto = pd.read_excel(xls, sheet_name=ano, header=None)
        bruto = bruto[~bruto.iloc[:, 0].astype(str).str.contains("Fonte:|Notas:", case=False, na=False)]
        inicio = bruto[bruto.iloc[:, 0].astype(str).str.strip() == "Brasil"].index

        if len(inicio) == 0:
            continue

        df = bruto.iloc[inicio[0]:, :8].copy()
        df = df.dropna(subset=[0])
        df = df[df[0].astype(str).str.strip() != ""]

        df = df.iloc[:, [0, 1, 2, 4, 5, 6, 7]]
        df.columns = [
            "Localidade", "Total", "Total_brancas", "Total_negras_pardas",
            "Homens_brancos", "Homens_negros_pardos", "Mulheres_brancas"
        ]

        df = bruto.iloc[inicio[0]:, [0, 1, 2, 3, 4, 5, 6, 7]].copy()
        df = df.dropna(subset=[0])
        df = df[df[0].astype(str).str.strip() != ""]
        df.columns = [
            "Localidade", "Total", "Total_brancas", "Total_negras_pardas",
            "Homens_brancos", "Homens_negros_pardos",
            "Mulheres_brancas", "Mulheres_negras_pardas"
        ]

        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df["Ano"] = str(ano)
        dados.append(df)

    return pd.concat(dados, ignore_index=True)


try:
    df_data = carregar_data(ARQUIVO_DATA)

    st.sidebar.header("Filtros")
    anos = sorted(df_data["Ano"].unique(), reverse=True)
    ano = st.sidebar.selectbox("Selecione o ano:", anos)

    localidades = df_data["Localidade"].unique().tolist()
    padrao = [x for x in ["Brasil", "Bahia", "Pernambuco", "Amazonas", "Ceará"] if x in localidades]
    selecionadas = st.sidebar.multiselect(
        "Selecione as Regiões/UFs:",
        options=localidades,
        default=padrao
    )

    st.sidebar.header("📤 Upload de dados")
    arquivo_upload = st.sidebar.file_uploader(
        "Envie uma tabela (.xls, .xlsx ou .csv)",
        type=["xls", "xlsx", "csv"],
        help="Se enviado, o arquivo carregado será usado no lugar da Tabela 1.1.1 local."
    )

    if arquivo_upload is not None:
        if arquivo_upload.name.lower().endswith(".csv"):
            bruto_upload = pd.read_csv(arquivo_upload, header=None)
            bruto_upload = bruto_upload.dropna(subset=[0])
            bruto_upload = bruto_upload[bruto_upload[0].astype(str).str.strip() != ""]
            df_data = bruto_upload.iloc[:, :8].copy()
            df_data.columns = [
                "Localidade", "Total", "Total_brancas", "Total_negras_pardas",
                "Homens_brancos", "Homens_negros_pardos",
                "Mulheres_brancas", "Mulheres_negras_pardas"
            ]
            for col in df_data.columns[1:]:
                df_data[col] = pd.to_numeric(df_data[col], errors="coerce")
            df_data["Ano"] = "Arquivo enviado"
        else:
            df_data = carregar_data(arquivo_upload)
    else:
        df_data = carregar_data(ARQUIVO_DATA)

    st.title("📊 Horas dedicadas a cuidados e afazeres domésticos")
    st.markdown(
        "Análise da média de horas semanais dedicadas por pessoas de 14 anos ou mais."
    )

    df_filtrado = df_data[
        (df_data["Ano"] == ano) &
        (df_data["Localidade"].isin(selecionadas))
    ].copy()

    if df_filtrado.empty:
        st.warning("Nenhuma localidade selecionada nos filtros.")
    else:
        st.subheader(f"📋 Tabela por localidade ({ano})")

        tabela = df_filtrado[[
            "Localidade", "Total", "Homens_brancos", "Homens_negros_pardos",
            "Mulheres_brancas", "Mulheres_negras_pardas"
        ]].rename(columns={
            "Localidade": "Estado / Região",
            "Total": "Total",
            "Homens_brancos": "Homens brancos",
            "Homens_negros_pardos": "Homens negros/pardos",
            "Mulheres_brancas": "Mulheres brancas",
            "Mulheres_negras_pardas": "Mulheres negras/pardas"
        }).reset_index(drop=True)

        st.dataframe(tabela, use_container_width=True)

        st.markdown("---")
        st.subheader("📈 Gráficos comparativos")

        col1, col2 = st.columns(2)

        with col1:
            df_genero_filtrado = df_filtrado.copy()
            df_genero_filtrado["Média homens"] = (
                df_genero_filtrado["Homens_brancos"] +
                df_genero_filtrado["Homens_negros_pardos"]
            ) / 2

            df_genero_filtrado["Média mulheres"] = (
                df_genero_filtrado["Mulheres_brancas"] +
                df_genero_filtrado["Mulheres_negras_pardas"]
            ) / 2

            comparativo = df_genero_filtrado.melt(
                id_vars=["Localidade"],
                value_vars=["Média homens", "Média mulheres"],
                var_name="Gênero",
                value_name="Horas semanais"
            )

            fig_bar = px.bar(
                comparativo,
                x="Localidade",
                y="Horas semanais",
                color="Gênero",
                barmode="group",
                title=f"Média de horas por gênero ({ano})",
                labels={"Localidade": "Estado / Região"},
                color_discrete_sequence=["#1f77b4", "#e377c2"]
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            historico = df_data[df_data["Localidade"].isin(selecionadas)].copy()
            historico["Total"] = historico["Total"]

            fig_line = px.line(
                historico,
                x="Ano",
                y="Total",
                color="Localidade",
                markers=True,
                title="Evolução temporal do total de horas dedicadas",
                labels={"Total": "Horas/Semana", "Ano": "Ano"}
            )
            st.plotly_chart(fig_line, use_container_width=True)

        colunas_box = {
            "Homens brancos": "Homens_brancos",
            "Homens negros/pardos": "Homens_negros_pardos",
            "Mulheres brancas": "Mulheres_brancas",
            "Mulheres negras/pardas": "Mulheres_negras_pardas"
        }

        box_data = df_filtrado[["Localidade"] + list(colunas_box.values())].melt(
            id_vars="Localidade",
            var_name="Grupo",
            value_name="Horas semanais"
        )

        mapa_grupos = {v: k for k, v in colunas_box.items()}
        box_data["Grupo"] = box_data["Grupo"].map(mapa_grupos)

        fig_box = px.box(
            box_data,
            x="Grupo",
            y="Horas semanais",
            points="all",
            color="Grupo",
            hover_data=["Localidade"],
            title=f"Distribuição das horas semanais por grupo ({ano})",
            labels={"Grupo": "Grupo", "Horas semanais": "Horas/Semana"}
        )
        st.plotly_chart(fig_box, use_container_width=True)

        st.caption(
            "O boxplot apresenta mediana, quartis e dispersão dos valores entre as localidades. "
            "Os pontos representam os valores de cada localidade."
        )

        st.markdown("---")
        st.subheader("📰 Reportagens e conteúdos relacionados")
        st.markdown(
            "Explore conteúdos sobre **Carga Mental Feminina** e **Economia do Cuidado**, "
            "temas que contextualizam a distribuição do trabalho doméstico e de cuidado."
        )
        
        noticia1, noticia2 = st.columns(2)
        with noticia1:
            st.image(
                "image.png",
                caption="Carga mental feminina: planejamento e organização cotidiana",
                use_container_width=True
            )
            st.markdown("### “Tudo eu nessa casa!” – como a carga mental feminina afeta a saúde física e psíquica das mulheres")
            st.write(
                "A carga mental envolve lembrar, antecipar, organizar e coordenar tarefas "
                "domésticas e familiares — responsabilidades frequentemente invisíveis."
            )
            st.markdown(
                "[Veja mais sobre essa reportagem de carga mental feminina](https://aerp.org.br/redeaerp/tudo-eu-nessa-casa-como-a-carga-mental-feminina-afeta-a-saude-fisica-e-psiquica-das-mulheres/)"
            )
        
        with noticia2:
            st.image(
                "image2.png",
                caption="Economia do cuidado: atividades de cuidado e apoio",
                use_container_width=True
            )
            st.markdown("### Economia do Cuidado")
            st.write(
                "A economia do cuidado reúne atividades essenciais, remuneradas ou não, "
                "como cuidar de crianças, idosos e pessoas dependentes, além de manter a vida cotidiana."
            )
            st.markdown(
                "[Veja mais sobre essa reportagem de economia do cuidado](https://revistapesquisa.fapesp.br/economia-do-cuidado/)"
            )

except Exception as e:
    st.error(f"Erro ao carregar os arquivos: {e}")
    st.info("Certifique-se de que o arquivo 'Tabela 1.1.1.xls' está no mesmo diretório do script.")
