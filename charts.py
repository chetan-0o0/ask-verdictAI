"""AskVerdict AI — Plotly.js client-side chart generators.
This avoids loading the heavy python plotly module, resolving Vercel deployment size limits.
"""
import json
import uuid

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


def risk_gauge(score: int, verdict: str):
    """Semicircular gauge: 0-100 with APPROVE/ESCALATE/BLOCK zones."""
    element_id = f"gauge-{uuid.uuid4().hex}"
    color = _VCOLORS.get(verdict, _MUTED)
    
    data = [{
        "type": "indicator",
        "mode": "gauge+number",
        "value": score,
        "number": {"font": {"size": 48, "color": color}, "suffix": "/100"},
        "gauge": {
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": _MUTED, "dtick": 25, "tickfont": {"size": 10, "color": _MUTED}},
            "bar": {"color": color, "thickness": 0.3},
            "bgcolor": "rgba(240,240,240,0.03)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 25], "color": "rgba(62,86,65,0.2)"},
                {"range": [26, 69], "color": "rgba(212,168,67,0.15)"},
                {"range": [70, 100], "color": "rgba(130,38,89,0.2)"}
            ],
            "threshold": {"line": {"color": color, "width": 3}, "thickness": 0.8, "value": score}
        },
        "title": {"text": f"<b>{verdict}</b>", "font": {"size": 16, "color": color}}
    }]
    
    layout = {
        "paper_bgcolor": _BG,
        "plot_bgcolor": _BG,
        "font": {"family": "Inter, system-ui, sans-serif", "color": _TEXT, "size": 12},
        "margin": {"l": 20, "r": 20, "t": 40, "b": 20},
        "height": 260
    }
    
    return f"""
    <div id="{element_id}" style="width:100%; height:260px;"></div>
    <script>
        (function() {{
            function render() {{
                if (typeof Plotly === 'undefined') {{
                    setTimeout(render, 50);
                    return;
                }}
                Plotly.newPlot('{element_id}', {json.dumps(data)}, {json.dumps(layout)}, {{responsive: true, displayModeBar: false}});
            }}
            render();
        }})();
    </script>
    """


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
        return ""
    vals.append(vals[0])
    cats_display = cats + [cats[0]]
    colors = [_SCOLORS[c] for c in cats]
    
    element_id = f"radar-{uuid.uuid4().hex}"
    
    data = [{
        "type": "scatterpolar",
        "r": vals,
        "theta": cats_display,
        "fill": "toself",
        "fillcolor": "rgba(0,77,97,0.15)",
        "line": {"color": _TEAL, "width": 2},
        "marker": {"size": 6, "color": [colors[i % 4] for i in range(len(cats_display))]}
    }]
    
    layout = {
        "paper_bgcolor": _BG,
        "plot_bgcolor": _BG,
        "font": {"family": "Inter, system-ui, sans-serif", "color": _TEXT, "size": 12},
        "margin": {"l": 20, "r": 20, "t": 40, "b": 20},
        "height": 280,
        "polar": {
            "bgcolor": _BG,
            "radialaxis": {"visible": True, "gridcolor": _GRID, "color": _MUTED, "dtick": 1, "tickfont": {"size": 9}},
            "angularaxis": {"gridcolor": _GRID, "color": _TEXT, "tickfont": {"size": 11, "color": _TEXT}}
        },
        "title": {"text": "<b>Factor Severity</b>", "font": {"size": 13, "color": _TEXT}, "x": 0.5, "xanchor": "center"},
        "showlegend": False
    }
    
    return f"""
    <div id="{element_id}" style="width:100%; height:280px;"></div>
    <script>
        (function() {{
            function render() {{
                if (typeof Plotly === 'undefined') {{
                    setTimeout(render, 50);
                    return;
                }}
                Plotly.newPlot('{element_id}', {json.dumps(data)}, {json.dumps(layout)}, {{responsive: true, displayModeBar: false}});
            }}
            render();
        }})();
    </script>
    """


def breakdown_waterfall(breakdown: dict):
    """Waterfall chart: baseline -> factor deltas -> final score."""
    bd = breakdown or {}
    lines = bd.get("lines", [])
    if not lines:
        return ""
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
    
    element_id = f"waterfall-{uuid.uuid4().hex}"
    
    text = [f"{'+' if v >= 0 else ''}{v}" if m == "relative" else str(v)
            for v, m in zip(values, measures)]
            
    data = [{
        "type": "waterfall",
        "orientation": "v",
        "measure": measures,
        "x": labels,
        "y": values,
        "connector": {"line": {"color": _GRID, "width": 1}},
        "increasing": {"marker": {"color": _RUBY}},
        "decreasing": {"marker": {"color": _FOREST}},
        "totals": {"marker": {"color": _DARK_TEAL}},
        "textposition": "outside",
        "text": text,
        "textfont": {"size": 10, "color": _TEXT}
    }]
    
    layout = {
        "paper_bgcolor": _BG,
        "plot_bgcolor": _BG,
        "font": {"family": "Inter, system-ui, sans-serif", "color": _TEXT, "size": 12},
        "margin": {"l": 20, "r": 20, "t": 40, "b": 20},
        "height": 320,
        "title": {"text": "<b>Risk Breakdown</b>", "font": {"size": 13, "color": _TEXT}, "x": 0.5, "xanchor": "center"},
        "xaxis": {"tickfont": {"size": 9, "color": _MUTED}, "tickangle": -30, "gridcolor": _GRID},
        "yaxis": {"title": "Risk Points", "gridcolor": _GRID, "tickfont": {"size": 10, "color": _MUTED}},
        "showlegend": False
    }
    
    return f"""
    <div id="{element_id}" style="width:100%; height:320px;"></div>
    <script>
        (function() {{
            function render() {{
                if (typeof Plotly === 'undefined') {{
                    setTimeout(render, 50);
                    return;
                }}
                Plotly.newPlot('{element_id}', {json.dumps(data)}, {json.dumps(layout)}, {{responsive: true, displayModeBar: false}});
            }}
            render();
        }})();
    </script>
    """


def batch_bar(rows: list):
    """Horizontal bar chart of batch counterparties ranked by risk."""
    if not rows:
        return ""
    rows_sorted = sorted(rows, key=lambda r: int(r[1].get("risk_score", 0)))
    names = [r[0] for r in rows_sorted]
    scores = [int(r[1].get("risk_score", 0)) for r in rows_sorted]
    colors = [_VCOLORS.get(r[1].get("verdict", ""), _MUTED) for r in rows_sorted]
    h = max(250, len(names) * 40 + 80)
    
    element_id = f"batch-{uuid.uuid4().hex}"
    
    data = [{
        "type": "bar",
        "y": names,
        "x": scores,
        "orientation": "h",
        "marker": {"color": colors, "line": {"width": 0}},
        "text": [str(s) for s in scores],
        "textposition": "outside",
        "textfont": {"size": 11, "color": _TEXT}
    }]
    
    layout = {
        "paper_bgcolor": _BG,
        "plot_bgcolor": _BG,
        "font": {"family": "Inter, system-ui, sans-serif", "color": _TEXT, "size": 12},
        "margin": {"l": 20, "r": 20, "t": 40, "b": 20},
        "height": h,
        "title": {"text": "<b>Risk Distribution</b>", "font": {"size": 13, "color": _TEXT}, "x": 0.5, "xanchor": "center"},
        "xaxis": {"range": [0, 110], "title": "Risk Score", "gridcolor": _GRID, "tickfont": {"size": 10, "color": _MUTED}},
        "yaxis": {"tickfont": {"size": 11, "color": _TEXT}, "automargin": True},
        "showlegend": False
    }
    
    return f"""
    <div id="{element_id}" style="width:100%; height:{h}px;"></div>
    <script>
        (function() {{
            function render() {{
                if (typeof Plotly === 'undefined') {{
                    setTimeout(render, 50);
                    return;
                }}
                Plotly.newPlot('{element_id}', {json.dumps(data)}, {json.dumps(layout)}, {{responsive: true, displayModeBar: false}});
            }}
            render();
        }})();
    </script>
    """
