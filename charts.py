"""AskVerdict AI — Plotly chart helpers for the Gradio UI."""
import plotly.graph_objects as go

# ── Jewel-tone palette ────────────────────────────────────────
_BG = "rgba(0,0,0,0)"
_GRID = "rgba(240,240,240,0.06)"
_TEXT = "#F0F0F0"
_MUTED = "#a0a0a0"
_TEAL = "#00899e"       # lighter teal for chart readability
_DARK_TEAL = "#004D61"
_RUBY = "#822659"
_FOREST = "#3E5641"
_AMBER = "#d4a843"
_ORANGE = "#c87a3f"

_VCOLORS = {"APPROVE": _FOREST, "ESCALATE": _AMBER, "BLOCK": _RUBY}
_SCOLORS = {"CRITICAL": _RUBY, "HIGH": _ORANGE, "MEDIUM": _AMBER, "LOW": _TEAL}


def _layout(**kw):
    base = dict(
        paper_bgcolor=_BG, plot_bgcolor=_BG,
        font=dict(family="Inter, system-ui, sans-serif", color=_TEXT, size=12),
        margin=dict(l=20, r=20, t=40, b=20),
    )
    base.update(kw)
    return go.Layout(**base)


def risk_gauge(score: int, verdict: str):
    """Semicircular gauge: 0-100 with APPROVE/ESCALATE/BLOCK zones."""
    color = _VCOLORS.get(verdict, _MUTED)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(font=dict(size=48, color=color), suffix="/100"),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor=_MUTED,
                      dtick=25, tickfont=dict(size=10, color=_MUTED)),
            bar=dict(color=color, thickness=0.3),
            bgcolor="rgba(240,240,240,0.03)",
            borderwidth=0,
            steps=[
                dict(range=[0, 25], color="rgba(62,86,65,0.2)"),
                dict(range=[26, 69], color="rgba(212,168,67,0.15)"),
                dict(range=[70, 100], color="rgba(130,38,89,0.2)"),
            ],
            threshold=dict(line=dict(color=color, width=3), thickness=0.8, value=score),
        ),
        title=dict(text=f"<b>{verdict}</b>", font=dict(size=16, color=color)),
    ))
    fig.update_layout(_layout(height=260))
    return fig


def severity_radar(factors: list):
    """Radar chart of factor severity counts."""
    cats = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    counts = {c: 0 for c in cats}
    for f in (factors or []):
        s = str(f.get("severity", "")).upper()
        if s in counts:
            counts[s] += 1
    vals = [counts[c] for c in cats]
    if not any(vals):
        return None
    vals.append(vals[0])
    cats_display = cats + [cats[0]]
    colors = [_SCOLORS[c] for c in cats]
    fig = go.Figure(go.Scatterpolar(
        r=vals, theta=cats_display, fill="toself",
        fillcolor="rgba(0,77,97,0.15)",
        line=dict(color=_TEAL, width=2),
        marker=dict(size=6, color=[colors[i % 4] for i in range(len(cats_display))]),
    ))
    fig.update_layout(_layout(
        height=280,
        polar=dict(
            bgcolor=_BG,
            radialaxis=dict(visible=True, gridcolor=_GRID, color=_MUTED,
                            dtick=1, tickfont=dict(size=9)),
            angularaxis=dict(gridcolor=_GRID, color=_TEXT,
                             tickfont=dict(size=11, color=_TEXT)),
        ),
        title=dict(text="<b>Factor Severity</b>", font=dict(size=13, color=_TEXT),
                   x=0.5, xanchor="center"),
        showlegend=False,
    ))
    return fig


def breakdown_waterfall(breakdown: dict):
    """Waterfall chart: baseline -> factor deltas -> final score."""
    bd = breakdown or {}
    lines = bd.get("lines", [])
    if not lines:
        return None
    labels = ["Baseline"]
    values = [bd.get("baseline", 30)]
    measures = ["absolute"]
    for l in lines:
        label = l["label"][:35] + ("…" if len(l["label"]) > 35 else "")
        labels.append(label)
        values.append(l["delta"])
        measures.append("relative")
    labels.append("Final Score")
    values.append(bd.get("total", 0))
    measures.append("total")
    fig = go.Figure(go.Waterfall(
        orientation="v", measure=measures, x=labels, y=values,
        connector=dict(line=dict(color=_GRID, width=1)),
        increasing=dict(marker=dict(color=_RUBY)),
        decreasing=dict(marker=dict(color=_FOREST)),
        totals=dict(marker=dict(color=_DARK_TEAL)),
        textposition="outside",
        text=[f"{'+' if v >= 0 else ''}{v}" if m == "relative" else str(v)
              for v, m in zip(values, measures)],
        textfont=dict(size=10, color=_TEXT),
    ))
    fig.update_layout(_layout(
        height=320,
        title=dict(text="<b>Risk Breakdown</b>", font=dict(size=13, color=_TEXT),
                   x=0.5, xanchor="center"),
        xaxis=dict(tickfont=dict(size=9, color=_MUTED), tickangle=-30,
                   gridcolor=_GRID),
        yaxis=dict(title="Risk Points", gridcolor=_GRID,
                   tickfont=dict(size=10, color=_MUTED)),
        showlegend=False,
    ))
    return fig


def batch_bar(rows: list):
    """Horizontal bar chart of batch counterparties ranked by risk."""
    if not rows:
        return None
    rows_sorted = sorted(rows, key=lambda r: int(r[1].get("risk_score", 0)))
    names = [r[0] for r in rows_sorted]
    scores = [int(r[1].get("risk_score", 0)) for r in rows_sorted]
    colors = [_VCOLORS.get(r[1].get("verdict", ""), _MUTED) for r in rows_sorted]
    fig = go.Figure(go.Bar(
        y=names, x=scores, orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[str(s) for s in scores], textposition="outside",
        textfont=dict(size=11, color=_TEXT),
    ))
    h = max(250, len(names) * 40 + 80)
    fig.update_layout(_layout(
        height=h,
        title=dict(text="<b>Risk Distribution</b>", font=dict(size=13, color=_TEXT),
                   x=0.5, xanchor="center"),
        xaxis=dict(range=[0, 110], title="Risk Score", gridcolor=_GRID,
                   tickfont=dict(size=10, color=_MUTED)),
        yaxis=dict(tickfont=dict(size=11, color=_TEXT), automargin=True),
        showlegend=False,
    ))
    return fig
