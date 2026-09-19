# =======================================================
# 🤖 Ellie Telecare Dashboard - Estilo BI Moderno e Responsivo
# =======================================================

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

# -------------------------------
# 1️⃣ Leitura e tratamento dos dados
# -------------------------------
arquivo = "telecare.csv"

try:
    df = pd.read_csv(arquivo, sep=";", quotechar='"', encoding="utf-8", engine="python")
except UnicodeDecodeError:
    df = pd.read_csv(arquivo, sep=";", quotechar='"', encoding="latin1", engine="python")

df.columns = [col.strip().upper().replace(" ", "_") for col in df.columns]

for col in ["INICIO_DA_CHAMADA", "FIM_DA_CHAMADA"]:
    df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
    df[col] = pd.to_datetime(df[col], errors="coerce")

df["DURACAO_MIN"] = (df["FIM_DA_CHAMADA"] - df["INICIO_DA_CHAMADA"]).dt.total_seconds() / 60
df = df.dropna(subset=["DURACAO_MIN"])
df["MES"] = df["INICIO_DA_CHAMADA"].dt.to_period('M').astype(str)
df["TIPO_DE_CHAMADA_UP"] = df["TIPO_DE_CHAMADA"].str.upper()
codigo_df = df[df["TIPO_DE_CHAMADA_UP"].isin(["CÓDIGO AZUL", "CÓDIGO AMARELO"])]

# -------------------------------
# 2️⃣ Métricas agregadas
# -------------------------------
total_chamadas = len(df)
media_geral = df["DURACAO_MIN"].mean()

chamadas_mes = df.groupby("MES").size().reset_index(name="QUANTIDADE")
chamadas_bloco = df.groupby("ANDAR").size().reset_index(name="QUANTIDADE")
media_bloco = df.groupby("ANDAR")["DURACAO_MIN"].mean().reset_index()

codigo_count = codigo_df.groupby("TIPO_DE_CHAMADA_UP").size().reset_index(name="QUANTIDADE")
codigo_media = codigo_df.groupby("TIPO_DE_CHAMADA_UP")["DURACAO_MIN"].mean().reset_index()

# -------------------------------
# 3️⃣ Função Ellie (offline)
# -------------------------------
def ellie_responder(pergunta: str) -> str:
    p = pergunta.lower()
    if "total de chamadas" in p:
        return f"O total de chamadas é {total_chamadas}."
    if "média geral" in p or "tempo médio geral" in p:
        return f"A média geral de atendimento é {media_geral:.2f} minutos."
    if "por mês" in p:
        resp = "\n".join([f"{row['MES']}: {row['QUANTIDADE']} chamados" for _, row in chamadas_mes.iterrows()])
        return f"Chamadas por mês:\n{resp}"
    if "por bloco" in p:
        resp = "\n".join([f"{row['ANDAR']}: {row['QUANTIDADE']} chamados" for _, row in chamadas_bloco.iterrows()])
        return f"Chamadas por bloco:\n{resp}"
    if "código azul" in p or "código amarelo" in p:
        resp = "\n".join([
            f"{row['TIPO_DE_CHAMADA_UP']}: {row['QUANTIDADE']} chamados, média {row['DURACAO_MIN']:.2f} minutos" 
            for _, row in codigo_media.merge(codigo_count, on="TIPO_DE_CHAMADA_UP").iterrows()
        ])
        return f"Chamadas Código Azul/Amarelo:\n{resp}"
    return "Desculpe, não entendi. Pergunte sobre total, média geral, mês, bloco ou códigos."

# -------------------------------
# 4️⃣ Dash App
# -------------------------------
app = Dash(__name__, external_stylesheets=[dbc.themes.MINTY])
app.title = "Ellie Telecare Dashboard - Responsivo"

# -------------------------------
# 5️⃣ Função para estilizar gráficos
# -------------------------------
def estilo_fig(fig):
    fig.update_layout(
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="#f9f9f9",
        margin=dict(t=40, b=40, l=20, r=20),
        font=dict(family="Arial", size=12, color="#111"),
        title_font=dict(size=16, color="#111", family="Arial"),
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial"),
    )
    fig.update_traces(marker_line_width=0)
    return fig

fig_chamadas_mes = estilo_fig(
    px.bar(chamadas_mes, x="MES", y="QUANTIDADE", text="QUANTIDADE",
           color="QUANTIDADE", color_continuous_scale="Teal")
)
fig_bloco = estilo_fig(
    px.bar(chamadas_bloco, x="ANDAR", y="QUANTIDADE", text="QUANTIDADE",
           color="QUANTIDADE", color_continuous_scale="Blues")
)
fig_media_bloco = estilo_fig(
    px.bar(media_bloco, x="ANDAR", y="DURACAO_MIN", text="DURACAO_MIN",
           color="DURACAO_MIN", color_continuous_scale="Oranges")
)
fig_codigo = estilo_fig(
    px.bar(codigo_count, x="TIPO_DE_CHAMADA_UP", y="QUANTIDADE", text="QUANTIDADE",
           color="TIPO_DE_CHAMADA_UP", color_discrete_map={"CÓDIGO AZUL":"blue","CÓDIGO AMARELO":"gold"})
)
fig_codigo_media = estilo_fig(
    px.bar(codigo_media, x="TIPO_DE_CHAMADA_UP", y="DURACAO_MIN", text="DURACAO_MIN",
           color="TIPO_DE_CHAMADA_UP", color_discrete_map={"CÓDIGO AZUL":"blue","CÓDIGO AMARELO":"gold"})
)

# -------------------------------
# 6️⃣ Layout Responsivo e Moderno
# -------------------------------
card_style = {
    "borderRadius": "15px",
    "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
    "padding": "25px",
    "textAlign": "center",
    "backgroundColor": "#ffffff",
    "marginBottom": "20px",
}

app.layout = dbc.Container([
    html.H1("🤖 Ellie Telecare Dashboard", className="text-center my-4", style={"color":"#333"}),

    # Cards métricas responsivos
    dbc.Row([
        dbc.Col(dbc.Card([
            html.H5("Total de Chamadas", className="card-title"),
            html.H2(f"{total_chamadas}", className="card-text")
        ], style=card_style), xs=12, sm=6, md=3),
        dbc.Col(dbc.Card([
            html.H5("Média Geral de Atendimento (min)", className="card-title"),
            html.H2(f"{media_geral:.2f}", className="card-text")
        ], style=card_style), xs=12, sm=6, md=3),
    ], className="mb-4", justify="start"),

    # Gráficos responsivos
    dbc.Row([
        dbc.Col(dcc.Graph(figure=fig_chamadas_mes, style={"borderRadius":"15px"}), xs=12, md=6),
        dbc.Col(dcc.Graph(figure=fig_bloco, style={"borderRadius":"15px"}), xs=12, md=6),
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(figure=fig_media_bloco, style={"borderRadius":"15px"}), xs=12, md=6),
        dbc.Col(dcc.Graph(figure=fig_codigo, style={"borderRadius":"15px"}), xs=12, md=6),
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Graph(figure=fig_codigo_media, style={"borderRadius":"15px"}), xs=12, md=6)
    ], className="mb-4"),

    html.Hr(),

    # Chat responsivo
    html.H3("💬 Converse com a Ellie (offline)", className="my-3", style={"color":"#333"}),
    dbc.Row([
        dbc.Col([
            dbc.Textarea(id="user-input", placeholder="Digite sua pergunta...", 
                         style={"width":"100%", "height":"100px", "borderRadius":"10px", "resize":"vertical"}),
            dbc.Button("Enviar", id="btn-enviar", color="success", className="my-2", style={"borderRadius":"10px"}),
            html.Div(id="chat-output", style={
                "whiteSpace":"pre-line",
                "marginTop":"20px",
                "border":"1px solid #ccc",
                "padding":"15px",
                "borderRadius":"15px",
                "backgroundColor":"#f8f9fa",
                "color":"#111",
                "boxShadow":"0 4px 8px rgba(0,0,0,0.05)",
                "minHeight":"150px"
            })
        ], xs=12, md=8)
    ])
], fluid=True, style={"backgroundColor":"#f0f2f5", "padding":"20px"})

# -------------------------------
# 7️⃣ Callback Chat
# -------------------------------
@app.callback(
    Output("chat-output", "children"),
    Input("btn-enviar", "n_clicks"),
    State("user-input", "value")
)
def atualizar_chat(n_clicks, pergunta):
    if n_clicks == 0 or not pergunta:
        return ""
    return f"🧑 Você: {pergunta}\n🤖 Ellie: {ellie_responder(pergunta)}"

# -------------------------------
# 8️⃣ Rodar App
# -------------------------------
if __name__ == "__main__":
    print("🚀 Abra no navegador: http://127.0.0.1:8050")
    app.run(debug=True)
