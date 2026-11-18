"""Benchmark scatter chart for the onboarding assets (see onboarding_assets.py)."""
import html

# Plot geometry (viewBox units).
W, H = 640, 300
L, R, T, B = 64, 560, 16, 248


def px(c, cost):
    return L + cost / c.X_MAX * (R - L)


def py(c, score):
    return B - (score - c.Y_MIN) / (c.Y_MAX - c.Y_MIN) * (B - T)


def chart_svg(c, standalone):
    e = html.escape
    out = []
    style = """
  .grid{stroke:#e1e0d9;stroke-width:1}
  .axis{stroke:#c3c2b7;stroke-width:1}
  .tick{fill:#898781;font-size:11px}
  .ttl{fill:#52514e;font-size:12px}
  .lbl{fill:#52514e;font-size:12px}
  .lbl.n{fill:#2a78d6;font-weight:600}
  .pt{fill:#888780;stroke:#fcfcfb;stroke-width:2}
  .pt.n{fill:#2a78d6}
  @media (prefers-color-scheme: dark){
    .grid{stroke:#2c2c2a}.axis{stroke:#383835}
    .ttl,.lbl{fill:#c3c2b7}.lbl.n,.pt.n{fill:#3987e5}.pt{stroke:#1a1a19}
  }"""
    ns = ' xmlns="http://www.w3.org/2000/svg"' if standalone else ""
    out.append(f'<svg{ns} viewBox="0 0 {W} {H}" width="100%" role="img" aria-labelledby="bc-title bc-desc" '
               f'font-family="system-ui,-apple-system,Segoe UI,Helvetica,Arial,sans-serif">')
    out.append(f'<title id="bc-title">{e(c.TITLE)}</title>')
    desc = "; ".join(f"{n} {s:.3f} at ${c:.2f}" for n, s, c in c.PROVIDERS)
    out.append(f'<desc id="bc-desc">{c.Y_LABEL} versus cost per run. {e(desc)}.</desc>')
    if standalone:
        out.append(f"<style>{style}\n</style>")
    for i in range(8):
        v = c.Y_MIN + i * c.Y_STEP
        y = py(c, v)
        out.append(f'<line class="{"axis" if i == 0 else "grid"}" x1="{L}" x2="{R}" y1="{y:.1f}" y2="{y:.1f}"/>')
        out.append(f'<text class="tick" x="{L - 8}" y="{y + 4:.1f}" text-anchor="end">{v:.2f}</text>')
    for i in range(7):
        v = i * c.X_STEP
        x = px(c, v)
        out.append(f'<text class="tick" x="{x:.1f}" y="{B + 18}" text-anchor="middle">${v:.2f}</text>')
    out.append(f'<text class="ttl" x="{(L + R) / 2:.0f}" y="{H - 6}" text-anchor="middle">Cost per run (USD)</text>')
    out.append(f'<text class="ttl" transform="translate(14 {(T + B) / 2:.0f}) rotate(-90)" text-anchor="middle">{c.Y_LABEL}</text>')
    for i, (name, score, cost) in enumerate(c.PROVIDERS):
        x, y = px(c, cost), py(c, score)
        n = " n" if i == 0 else ""
        r = 7 if i == 0 else 5.5
        out.append(f'<circle class="pt{n}" cx="{x:.1f}" cy="{y:.1f}" r="{r}"/>')
        out.append(f'<text class="lbl{n}" x="{x + 11:.1f}" y="{y + 4:.1f}">{e(name)}</text>')
    out.append("</svg>")
    return "\n".join(out), style


LIGHT = dict(grid="#e1e0d9", axis="#c3c2b7", tick="#898781", ink="#52514e", accent="#2a78d6", pt="#888780", bg="#ffffff")
DARK = dict(grid="#2c2c2a", axis="#383835", tick="#898781", ink="#c3c2b7", accent="#3987e5", pt="#888780", bg="#0d1117")


def fixed_svg(c, svg, theme):
    """Standalone chart with one fixed theme and a solid background (GitHub <picture>)."""
    t = theme
    style = (f".grid{{stroke:{t['grid']};stroke-width:1}}.axis{{stroke:{t['axis']};stroke-width:1}}"
             f".tick{{fill:{t['tick']};font-size:11px}}.ttl,.lbl{{fill:{t['ink']};font-size:12px}}"
             f".hd{{fill:{t['ink']};font-size:15px;font-weight:600}}"
             f".lbl.n{{fill:{t['accent']};font-weight:600}}.pt{{fill:{t['pt']};stroke:{t['bg']};stroke-width:2}}.pt.n{{fill:{t['accent']}}}")
    head, body = svg.split(">", 1)
    head = head.replace(f'viewBox="0 0 {W} {H}"', f'viewBox="0 -34 {W} {H + 34}"')
    return (f"{head}>\n<style>{style}</style>\n<rect x=\"0\" y=\"-34\" width=\"{W}\" height=\"{H + 34}\" fill=\"{t['bg']}\"/>\n"
            f"<text class=\"hd\" x=\"{L}\" y=\"-10\">{html.escape(c.TITLE)}</text>\n"
            + body.split("</style>", 1)[-1] if "</style>" in body else body)
