"""AskVerdict AI — web UI (Gradio). This is the deployable prototype.

Local:  python app.py
Deploy: push to a Hugging Face Space (SDK: gradio). Set secrets there:
        USE_MOCK=false, LLM_PROVIDER=groq, GROQ_API_KEY, BRIGHTDATA_API_TOKEN
"""
import html
import tempfile

import gradio as gr

import agent
import charts
import config
import report

# ── Jewel-tone palette ────────────────────────────────────────
# Background: #1A1A1A   Text: #F0F0F0   Teal: #004D61
# Ruby: #822659         Forest: #3E5641  Amber: #d4a843
_COLORS = {
    "APPROVE": ("#3E5641", "APPROVE"),
    "ESCALATE": ("#d4a843", "ESCALATE"),
    "BLOCK": ("#822659", "BLOCK"),
}
_SEV = {"CRITICAL": "#822659", "HIGH": "#c87a3f",
        "MEDIUM": "#d4a843", "LOW": "#00899e"}
_ORDER = {"BLOCK": 0, "ESCALATE": 1, "APPROVE": 2}

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* ── Global ───────────────────────────────────────────────── */
.gradio-container {
  background: #1A1A1A !important;
  color: #F0F0F0 !important;
  font-family: 'Inter', system-ui, sans-serif !important;
}
.dark { --body-background-fill: #1A1A1A !important; }

/* ── Header ───────────────────────────────────────────────── */
#header-row { margin-bottom: 6px; }
#app-title {
  font-size: 36px; font-weight: 900; letter-spacing: -1px;
  background: linear-gradient(135deg, #00899e, #004D61, #822659);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}
#app-subtitle {
  color: #808080; margin-top: -6px; font-size: 14px;
  font-weight: 500; letter-spacing: 0.3px;
}

/* ── Cards ────────────────────────────────────────────────── */
.vcard {
  border: 1px solid rgba(0,77,97,0.2);
  border-radius: 16px; padding: 24px;
  background: linear-gradient(135deg, #222222, #1e1e1e);
  box-shadow: 0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.02);
}
.badge {
  display: inline-block; padding: 10px 22px; border-radius: 999px;
  font-weight: 800; font-size: 15px; color: #F0F0F0; letter-spacing: 1px;
  text-transform: uppercase;
  box-shadow: 0 2px 12px rgba(0,0,0,0.4);
}
.score { color: #909090; margin-left: 14px; font-size: 14px; font-weight: 500; }
.summary {
  font-size: 15px; line-height: 1.65; margin: 18px 0;
  color: #d0d0d0; font-weight: 400;
}
.factor {
  border-left: 3px solid rgba(0,77,97,0.6); padding: 10px 0 10px 16px;
  margin: 12px 0; background: rgba(255,255,255,0.015); border-radius: 0 8px 8px 0;
}
.sev { font-weight: 700; font-size: 11px; letter-spacing: 1px; text-transform: uppercase; }
.src { font-size: 11px; margin-top: 4px; }
.src a { color: #00899e; text-decoration: none; opacity: 0.85; }
.src a:hover { opacity: 1; text-decoration: underline; }
.rec {
  margin-top: 18px; padding: 16px; border-radius: 12px;
  background: linear-gradient(135deg, #252525, #202020);
  color: #d0d0d0; border: 1px solid rgba(0,77,97,0.12);
  font-size: 14px; line-height: 1.6;
}

/* ── Batch table ──────────────────────────────────────────── */
.btable { width: 100%; border-collapse: collapse; font-size: 13px; }
.btable th {
  text-align: left; color: #808080; font-weight: 600; padding: 12px 14px;
  border-bottom: 1px solid rgba(0,77,97,0.15);
  font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
}
.btable td {
  padding: 14px; border-bottom: 1px solid rgba(255,255,255,0.04);
  color: #d0d0d0;
}
.btable tr:hover td { background: rgba(0,77,97,0.05); }
.bbadge {
  display: inline-block; padding: 5px 14px; border-radius: 999px;
  font-weight: 800; font-size: 11px; color: #F0F0F0; letter-spacing: 0.5px;
}

/* ── Status lines ─────────────────────────────────────────── */
.sline { margin: 12px 0 4px; font-size: 13px; font-weight: 600; }
.sline.ok { color: #3E5641; }
.sline.hit { color: #822659; }
.changed { margin: 6px 0; font-size: 13px; font-weight: 600; color: #d4a843; }
.seen { margin: 6px 0; font-size: 13px; color: #808080; }

/* ── Pipeline steps ───────────────────────────────────────── */
.pipe { display: flex; gap: 8px; flex-wrap: wrap; margin: 16px 0 6px; }
.pstep {
  font-size: 11px; font-weight: 600; color: #b0d0b8;
  background: rgba(62,86,65,0.2); border: 1px solid rgba(62,86,65,0.3);
  border-radius: 999px; padding: 5px 12px;
  transition: all 0.2s ease;
}
.pstep:hover { border-color: rgba(62,86,65,0.6); background: rgba(62,86,65,0.35); }
.pstep b { color: #5a9e66; }

/* ── Empty state ──────────────────────────────────────────── */
.empty {
  border: 1px dashed rgba(0,77,97,0.25); border-radius: 16px;
  padding: 36px 28px; background: rgba(30,30,30,0.5); color: #808080;
}
.empty h3 {
  color: #d0d0d0; margin: 0 0 16px; font-size: 17px; font-weight: 700;
}

/* ── Verification badges ──────────────────────────────────── */
.vok { font-size: 11px; font-weight: 700; color: #5a9e66; margin-left: 6px; }
.vno { font-size: 11px; font-weight: 700; color: #d4a843; margin-left: 6px; }

/* ── Integrity ────────────────────────────────────────────── */
.integ {
  margin: 12px 0 4px; font-size: 12px; font-weight: 600; padding: 10px 14px;
  border-radius: 10px;
}
.integ.ok { color: #5a9e66; background: rgba(62,86,65,0.15); }
.integ.warn { color: #d4a843; background: rgba(212,168,67,0.1); }

/* ── Risk calculation ─────────────────────────────────────── */
.calc {
  margin: 16px 0 6px; border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px; background: rgba(30,30,30,0.5); padding: 14px 16px;
}
.calc h4 {
  margin: 0 0 10px; color: #808080; font-size: 11px; font-weight: 700;
  letter-spacing: 0.5px; text-transform: uppercase;
}
.crow {
  display: flex; justify-content: space-between; font-size: 13px;
  padding: 4px 0; color: #d0d0d0;
}
.crow .d { font-variant-numeric: tabular-nums; font-weight: 700; }
.crow .up { color: #c87a3f; }
.crow .down { color: #5a9e66; }
.crow.base { color: #808080; }
.crow.tot {
  border-top: 1px solid rgba(255,255,255,0.06); margin-top: 8px;
  padding-top: 10px; font-weight: 800; color: #F0F0F0;
}

/* ── Confidence & reasoning ───────────────────────────────── */
.conf {
  display: inline-block; margin: 14px 0 4px; font-size: 12px; font-weight: 700;
  padding: 5px 12px; border-radius: 999px; letter-spacing: 0.3px;
}
.conf.HIGH { background: rgba(62,86,65,0.2); color: #5a9e66; }
.conf.MEDIUM { background: rgba(212,168,67,0.12); color: #d4a843; }
.conf.LOW { background: rgba(130,38,89,0.15); color: #c46b94; }
.confreason { font-size: 12px; color: #808080; margin: 4px 0 0; }

.whyblock {
  margin: 16px 0 6px; border-left: 3px solid #3E5641;
  padding: 10px 0 10px 16px;
}
.whyblock h4 {
  margin: 0 0 8px; color: #5a9e66; font-size: 11px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.5px;
}
.whyblock li { color: #b0b0b0; font-size: 13px; line-height: 1.8; list-style: none; }
.whyblock li:before { content: "\\2713  "; color: #5a9e66; font-weight: 700; }

.contra {
  margin: 12px 0 4px; font-size: 12px; padding: 10px 14px;
  border-radius: 10px; background: rgba(30,30,30,0.5); color: #909090;
}
.contra b { color: #00899e; }
.contra.conflict { background: rgba(212,168,67,0.08); color: #d4a843; }

/* ── Gauge bar ────────────────────────────────────────────── */
.gauge {
  height: 8px; border-radius: 999px; background: rgba(255,255,255,0.04);
  margin: 16px 0 8px; overflow: hidden;
}
.gauge > i { display: block; height: 100%; border-radius: 999px; transition: width 0.6s ease; }
.gscale {
  display: flex; justify-content: space-between; color: #606060;
  font-size: 10px; letter-spacing: 0.3px; margin-bottom: 6px;
}

/* ── Footer ───────────────────────────────────────────────── */
.foot {
  margin-top: 18px; color: #606060; font-size: 12px;
  text-align: center; padding: 12px 0;
  border-top: 1px solid rgba(255,255,255,0.04);
}
.foot b { color: #00899e; }

/* ── Gradio overrides ─────────────────────────────────────── */
button.primary, .primary {
  background: linear-gradient(135deg, #3E5641, #4a6b4e) !important;
  color: #F0F0F0 !important; border: none !important;
  font-weight: 700 !important; font-size: 14px !important;
  border-radius: 10px !important; padding: 12px 24px !important;
  box-shadow: 0 2px 12px rgba(62,86,65,0.3) !important;
  transition: all 0.2s ease !important;
}
button.primary:hover, .primary:hover {
  box-shadow: 0 4px 20px rgba(62,86,65,0.5) !important;
  transform: translateY(-1px) !important;
}
.tab-nav button {
  font-weight: 600 !important; font-size: 13px !important;
  letter-spacing: 0.3px !important;
}
"""


def _render(result: dict) -> str:
    d = result["decision"]
    sanc = result.get("sanctions") or {}
    change = result.get("change") or {}
    color, label = _COLORS.get(d["verdict"], ("#808080", d["verdict"]))
    factors = ""
    for f in d.get("factors", []):
        sev = str(f.get("severity", "")).upper()
        sc = _SEV.get(sev, "#808080")
        src = html.escape(str(f.get("source", "")))
        vflag = ('<span class="vok" title="Citation traced to collected evidence">'
                 '&#10003; verified</span>' if f.get("verified")
                 else '<span class="vno" title="Source not found in collected '
                 'evidence">&#9888; unverified</span>')
        factors += (
            f'<div class="factor">'
            f'<span class="sev" style="color:{sc}">{sev}</span> '
            f'{html.escape(str(f.get("finding", "")))} {vflag}'
            f'<div class="src">source: <a href="{src}" target="_blank">{src}</a></div>'
            f'</div>'
        )

    if sanc.get("hit"):
        sanc_html = (f'<div class="sline hit">&#9888; OFAC sanctions screen: '
                     f'HIT &mdash; matches "{html.escape(str(sanc.get("matched","")))}"</div>')
    else:
        sanc_html = ('<div class="sline ok">&#10003; OFAC sanctions screen: clear</div>')

    change_html = ""
    if change and change.get("changed"):
        change_html = (
            f'<div class="changed">&#8635; Change since last check: '
            f'{html.escape(str(change.get("old_verdict")))} &rarr; '
            f'{html.escape(str(change.get("new_verdict")))} '
            f'(risk {change.get("old_risk")} &rarr; {change.get("new_risk")}, '
            f'{html.escape(str(change.get("direction")))})</div>')
    elif change:
        change_html = ('<div class="seen">&#8635; Previously checked &middot; '
                       'no material change</div>')

    try:
        pct = max(0, min(100, int(d.get("risk_score", 0))))
    except (TypeError, ValueError):
        pct = 0
    gauge = (
        f'<div class="gscale"><span>0 APPROVE</span>'
        f'<span>26 ESCALATE</span><span>70 BLOCK</span><span>100</span></div>'
        f'<div class="gauge"><i style="width:{pct}%;background:{color}"></i></div>'
    )

    web_ran = bool(result.get("evidence"))
    pipe = (
        '<div class="pipe">'
        '<span class="pstep"><b>&#10003;</b> OFAC screened</span>'
        + (f'<span class="pstep"><b>&#10003;</b> Live web ({len(result.get("evidence", []))} sources)</span>'
           if web_ran else '<span class="pstep">Web skipped (sanctions hit)</span>')
        + '<span class="pstep"><b>&#10003;</b> Sanitized</span>'
        '<span class="pstep"><b>&#10003;</b> Verdict</span>'
        '</div>'
    )

    integ = d.get("integrity") or {}
    integ_html = ""
    if integ.get("total"):
        if integ.get("all_verified"):
            integ_html = ('<div class="integ ok">&#10003; Evidence integrity: '
                          f'{integ["verified"]}/{integ["total"]} findings cited '
                          'and traced to collected sources</div>')
        else:
            integ_html = ('<div class="integ warn">&#9888; Evidence integrity: '
                          f'{integ["verified"]}/{integ["total"]} findings traced &middot; '
                          f'{html.escape(str(d.get("evidence_warning","")))}</div>')

    bd = d.get("breakdown") or {}
    calc_html = ""
    if bd.get("lines"):
        rows = (f'<div class="crow base"><span>Base risk (unknown counterparty)'
                f'</span><span class="d">{bd.get("baseline",0)}</span></div>')
        for l in bd["lines"]:
            delta = l["delta"]
            sign = "+" if delta >= 0 else "\u2212"
            kind = "up" if delta >= 0 else "down"
            rows += (f'<div class="crow"><span>{html.escape(str(l["label"]))}</span>'
                     f'<span class="d {kind}">{sign}{abs(delta)}</span></div>')
        rows += (f'<div class="crow tot"><span>Final risk score</span>'
                 f'<span class="d">{bd.get("total",0)}/100</span></div>')
        calc_html = f'<div class="calc"><h4>Risk calculation</h4>{rows}</div>'

    ct = d.get("confidence_tag") or {}
    conf_html = ""
    if ct.get("level"):
        conf_html = (f'<div><span class="conf {ct["level"]}">Evidence confidence: '
                     f'{ct["level"]}</span>'
                     f'<div class="confreason">{html.escape(str(ct.get("reason","")))}'
                     f'</div></div>')

    why = d.get("why_not_higher") or []
    why_html = ""
    if why:
        items = "".join(f'<li>{html.escape(str(w))}</li>' for w in why)
        why_html = (f'<div class="whyblock"><h4>Why not higher risk?</h4>'
                    f'<ul style="margin:0;padding:0">{items}</ul></div>')

    contra = d.get("contradiction") or {}
    contra_html = ""
    if contra.get("checked"):
        cls = "contra conflict" if contra.get("conflict") else "contra"
        contra_html = (f'<div class="{cls}"><b>Adversarial-evidence check:</b> '
                       f'{html.escape(str(contra.get("note","")))}</div>')

    return (
        f'<div class="vcard">'
        f'<span class="badge" style="background:{color}">{label}</span>'
        f'<span class="score">risk {d["risk_score"]}/100 &middot; '
        f'{html.escape(str(d["confidence"]))} confidence</span>'
        f'{gauge}'
        f'{sanc_html}{change_html}'
        f'{pipe}'
        f'{integ_html}'
        f'{conf_html}'
        f'<div class="summary">{html.escape(str(d["summary"]))}</div>'
        f'<div>{factors}</div>'
        f'{calc_html}'
        f'{why_html}'
        f'{contra_html}'
        f'<div class="rec"><b>Recommendation:</b> '
        f'{html.escape(str(d["recommendation"]))}</div>'
        f'</div>'
    )


_EMPTY_STATE = (
    '<div class="empty"><h3>Enter a counterparty to begin a live investigation.</h3>'
    '<div class="pipe">'
    '<span class="pstep"><b>1</b> OFAC sanctions screen</span>'
    '<span class="pstep"><b>2</b> Live web via Bright Data</span>'
    '<span class="pstep"><b>3</b> Sanitize untrusted input</span>'
    '<span class="pstep"><b>4</b> Cited verdict + score</span>'
    '</div></div>'
)


def run_check(name, amount):
    name = (name or "").strip()
    if not name:
        yield "Enter a counterparty name to begin.", "", None, None, None, None
        return
    log = []
    yield "Investigating the live web...", "", None, None, None, None
    result = agent.run(name, amount, on_step=lambda m: log.append(m))
    trail = "\n".join(f"\u00b7 {m}" for m in log)
    try:
        pdf_path = report.generate_report(result, out_dir=tempfile.gettempdir())
    except Exception:
        pdf_path = None
    d = result["decision"]
    gauge_fig = charts.risk_gauge(d.get("risk_score", 0), d.get("verdict", ""))
    radar_fig = charts.severity_radar(d.get("factors", []))
    waterfall_fig = charts.breakdown_waterfall(d.get("breakdown"))
    yield trail, _render(result), pdf_path, gauge_fig, radar_fig, waterfall_fig


def _parse_names(text):
    raw = []
    for line in (text or "").splitlines():
        raw.extend(part.strip() for part in line.split(","))
    seen, out = set(), []
    for n in raw:
        if n and n.lower() not in seen:
            seen.add(n.lower())
            out.append(n)
    return out


def _render_batch(rows):
    rows = sorted(rows, key=lambda r: (_ORDER.get(r[1]["verdict"], 3),
                                       -int(r[1].get("risk_score", 0))))
    body = ""
    for name, d in rows:
        color, label = _COLORS.get(d["verdict"], ("#808080", d["verdict"]))
        top = d.get("factors", [])
        top_finding = html.escape(str(top[0].get("finding", "")) if top else "")
        body += (
            f'<tr>'
            f'<td><b>{html.escape(name)}</b></td>'
            f'<td><span class="bbadge" style="background:{color}">{label}</span></td>'
            f'<td>{d.get("risk_score", "?")}/100</td>'
            f'<td>{top_finding}</td>'
            f'</tr>'
        )
    return (
        '<div class="vcard"><table class="btable">'
        '<tr><th>Counterparty</th><th>Verdict</th><th>Risk</th>'
        '<th>Top finding</th></tr>'
        f'{body}</table></div>'
    )


def run_batch(text):
    names = _parse_names(text)
    if not names:
        yield "Paste one counterparty per line to begin.", "", None
        return
    log = [f"Screening {len(names)} counterparties..."]
    yield "\n".join(log), "", None
    rows = []
    for i, name in enumerate(names, 1):
        log.append(f"[{i}/{len(names)}] {name}")
        yield "\n".join(log), (_render_batch(rows) if rows else ""), None
        result = agent.run(name, "", on_step=lambda m: None)
        rows.append((name, result["decision"]))
        yield "\n".join(log), _render_batch(rows), charts.batch_bar(rows)
    log.append("Done. Highest-risk counterparties are listed first.")
    yield "\n".join(log), _render_batch(rows), charts.batch_bar(rows)


with gr.Blocks(css=_CSS, theme=gr.themes.Base()) as demo:
    gr.HTML('<div id="header-row">'
            '<div id="app-title">AskVerdict AI</div>'
            '<div id="app-subtitle">Autonomous counterparty due diligence — '
            'reads the live web before you wire a dollar.</div></div>')

    with gr.Tab("Single check"):
        with gr.Row():
            name_in = gr.Textbox(label="Counterparty / vendor name",
                                 placeholder="e.g. Wirecard AG")
            amount_in = gr.Textbox(label="Payment amount (optional)",
                                   placeholder="e.g. 50000 USD")
        btn = gr.Button("Run due diligence", variant="primary")
        status = gr.Textbox(label="Investigation trail", lines=6)
        card = gr.HTML(_EMPTY_STATE)
        with gr.Row():
            gauge_plot = gr.Plot(label="Risk Score")
            radar_plot = gr.Plot(label="Factor Severity")
        waterfall_plot = gr.Plot(label="Risk Breakdown")
        report_file = gr.File(label="Download due-diligence report (PDF)",
                              interactive=False)
        btn.click(run_check, inputs=[name_in, amount_in],
                  outputs=[status, card, report_file,
                           gauge_plot, radar_plot, waterfall_plot])
        gr.Examples([["Apple Inc", "11111"], ["Wirecard AG", "50000"]],
                    inputs=[name_in, amount_in])

    with gr.Tab("Batch screening"):
        gr.HTML('<div style="color:#808080;margin:4px 0 10px;font-size:14px">'
                'Paste a vendor list — one counterparty per line. AskVerdict AI '
                'checks them all and ranks the riskiest first.</div>')
        batch_in = gr.Textbox(
            label="Counterparty list", lines=8,
            placeholder="Apple Inc\nMicrosoft Corporation\nWirecard AG\nSiemens AG")
        bbtn = gr.Button("Screen all counterparties", variant="primary")
        bstatus = gr.Textbox(label="Progress", lines=6)
        btable = gr.HTML()
        batch_chart = gr.Plot(label="Risk Distribution")
        bbtn.click(run_batch, inputs=[batch_in],
                   outputs=[bstatus, btable, batch_chart])
        gr.Examples(
            [["Apple Inc\nMicrosoft Corporation\nWirecard AG\nSiemens AG"]],
            inputs=[batch_in])

    gr.HTML('<div class="foot">Powered by <b>Bright Data</b> (live web) &middot; '
            '<b>OFAC</b> sanctions screening &middot; <b>Cognee</b> memory &middot; '
            '<b>Groq / AI&#47;ML API</b> &middot; deployed on Hugging Face</div>')

if __name__ == "__main__":
    mode = "MOCK (offline)" if config.USE_MOCK else f"LIVE ({config.LLM_PROVIDER})"
    print(f"AskVerdict AI starting — data mode: {mode}")
    demo.launch()
