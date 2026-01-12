import plotly.express as px
import plotly.graph_objects as go

def _base_layout(fig, title: str, height: int):
    fig.update_layout(
        title=title,
        height=height,
        margin=dict(l=10, r=10, t=60, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig

def plot_bar(df, x, y, title, orientation="h"):
    fig = px.bar(df, x=x, y=y, orientation=orientation, text_auto=True)
    _base_layout(fig, title, 420)
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zeroline=False)
    fig.update_yaxes(showgrid=False)
    fig.update_traces(marker_line_width=0)
    return fig

def plot_hist(series, title, nbins=20):
    fig = px.histogram(series.dropna(), nbins=nbins)
    _base_layout(fig, title, 360)
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zeroline=False)
    fig.update_traces(marker_line_width=0)
    return fig

def plot_farol_donut(counts, title):
    labels = counts.index.tolist()
    values = counts.values.tolist()
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.62, sort=False)])
    fig.update_layout(
        title=title,
        height=360,
        margin=dict(l=10, r=10, t=60, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
    )
    fig.update_traces(textinfo="percent", textposition="inside")
    return fig
