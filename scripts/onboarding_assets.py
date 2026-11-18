"""Shared renderer for the onboarding assets of onboard-your-agent and onboard-your-gtm-agent.

Each skill's assets/build.py holds only its data and calls build(HERE, CONFIG). Writes, next to it:
benchmark-chart.svg (light/dark aware), benchmark-chart-light.svg / -dark.svg (fixed theme, for the
README), onboarding.html (self-contained page), onboarding-inline.html (bare fragment for an inline
chat widget) and onboarding.png (screenshot of the page; needs Google Chrome).
"""
import html
import pathlib
import shutil
import subprocess
import types

from onboarding_chart import DARK, LIGHT, chart_svg, fixed_svg

DEFAULTS = dict(
    INTEGRATE_TITLE="Try asking Nimble your most complex web research questions",
    INTEGRATE_TEXT="Once you're done testing, call the same APIs from your own apps and agents (MCP, SDK, CLI, & more):",
    INTEGRATE_URL="https://docs.nimbleway.com/integrations/overview",
    SPAN_LAST_ODD_TILE=False,
)


def inline_fragment(c, svg, svg_style):
    """Chart + tiles as a bare HTML fragment for inline chat widgets: no doctype, no body, transparent
    background, host CSS variables with fallbacks."""
    e = html.escape
    span_nb = ".nb-tile:last-child:nth-child(odd){grid-column:1/-1}\n" if c.SPAN_LAST_ODD_TILE else ""
    tiles = "\n".join(
        f'<div class="nb-tile"><p class="nb-t">{e(t)}</p><p class="nb-api">{e(api)}</p>'
        f'<p class="nb-d">{e(d)}</p><p class="nb-ex">&ldquo;{e(ex)}&rdquo;</p></div>' for t, api, d, ex in c.TILES)
    return f'''<style>
.nb{{color:var(--text-primary,#0b0b0b);font-family:var(--font-sans,system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif);padding:4px 0}}
.nb p{{margin:0}}
.nb-h{{font-size:16px;font-weight:500;margin:0 0 4px!important}}
.nb-cap{{font-size:12px;color:var(--text-muted,#898781);margin:2px 0 18px!important}}
.nb-h2{{font-size:15px;font-weight:500;margin:0 0 10px!important}}
.nb-g{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}}
@media (max-width:520px){{.nb-g{{grid-template-columns:1fr}}}}
{span_nb}.nb-tile{{background:var(--surface-2,transparent);border:0.5px solid var(--border,rgba(127,127,127,.35));border-radius:12px;padding:12px 14px}}
.nb-t{{font-weight:500;font-size:14px}}
.nb-api{{font-size:12px;color:var(--text-accent,#2a78d6);margin:2px 0 6px!important}}
.nb-d{{font-size:13px;line-height:1.5;color:var(--text-secondary,#52514e);margin-bottom:6px!important}}
.nb-ex{{font-size:12px;color:var(--text-muted,#898781);font-style:italic}}
.nb-w{{background:var(--surface-1,rgba(127,127,127,.08));border-radius:12px;padding:12px 14px;margin-top:10px;font-size:13px;line-height:1.5}}
.nb-w a{{color:var(--text-accent,#2a78d6)}}
{svg_style}
</style>
<div class="nb">
<p class="nb-h">{e(c.TITLE)}</p>
{svg}
<p class="nb-cap">{e(c.CAPTION)}</p>
<p class="nb-h2">Test Nimble's APIs on these use cases, right here in your AI.</p>
<div class="nb-g">
{tiles}
</div>
<div class="nb-w"><p style="font-weight:500">{e(c.INTEGRATE_TITLE)}</p>
<p style="color:var(--text-secondary,#52514e)">{e(c.INTEGRATE_TEXT)} <a href="{c.INTEGRATE_URL}">{c.INTEGRATE_URL.removeprefix("https://")}</a></p></div>
</div>
'''


def page_html(c, svg, svg_style):
    e = html.escape
    span_tile = "  .tile:last-child:nth-child(odd){grid-column:1/-1}\n" if c.SPAN_LAST_ODD_TILE else ""
    tiles = "\n".join(
        f'''    <div class="tile">
      <p class="t">{e(t)}</p>
      <p class="api">{e(api)}</p>
      <p class="d">{e(d)}</p>
      <p class="ex">&ldquo;{e(ex)}&rdquo;</p>
    </div>''' for t, api, d, ex in c.TILES)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{c.PAGE_TITLE}</title>
<style>
  :root{{--bg:#ffffff;--card:#ffffff;--soft:#f6f5f2;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--line:rgba(11,11,11,.12);--accent:#2a78d6}}
  @media (prefers-color-scheme: dark){{:root{{--bg:#1a1a19;--card:#232321;--soft:#2a2a28;--ink:#f0efec;--ink2:#c3c2b7;--muted:#898781;--line:rgba(255,255,255,.12);--accent:#3987e5}}}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}}
  main{{max-width:720px;margin:0 auto;padding:20px 16px 24px}}
  h1{{font-size:17px;font-weight:600;margin:0 0 4px}}
  .cap{{font-size:12px;color:var(--muted);margin:2px 0 20px}}
  h2{{font-size:15px;font-weight:600;margin:0 0 10px}}
  .grid4{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}}
  @media (max-width:560px){{.grid4{{grid-template-columns:1fr}}}}
{span_tile}  .tile{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px}}
  .tile p{{margin:0}}
  .t{{font-weight:600;font-size:14px}}
  .api{{font-size:12px;color:var(--accent);margin:2px 0 6px!important}}
  .d{{font-size:13px;color:var(--ink2);margin-bottom:6px!important}}
  .ex{{font-size:12px;color:var(--muted);font-style:italic}}
  .wide{{background:var(--soft);border-radius:12px;padding:12px 14px;margin-top:10px;font-size:13px}}
  .wide p{{margin:0}}
  .wide a{{color:var(--accent)}}
  {svg_style}
</style>
</head>
<body>
<main>
  <h1>{e(c.TITLE)}</h1>
  {svg}
  <p class="cap">{e(c.CAPTION)}</p>
  <h2>Test Nimble's APIs on these use cases, right here in your AI.</h2>
  <div class="grid4">
{tiles}
  </div>
  <div class="wide">
    <p><strong>{e(c.INTEGRATE_TITLE)}</strong></p>
    <p style="color:var(--ink2)">{e(c.INTEGRATE_TEXT)} <a href="{c.INTEGRATE_URL}">{c.INTEGRATE_URL.removeprefix("https://")}</a></p>
  </div>
</main>
</body>
</html>
'''


def build(here, config):
    """Write the chart SVGs, the page, the inline fragment and the PNG for one onboarding skill."""
    c = types.SimpleNamespace(**{**DEFAULTS, **config})
    svg, style = chart_svg(c, standalone=True)
    (here / "benchmark-chart.svg").write_text(svg + "\n")
    inline_svg, _ = chart_svg(c, standalone=False)
    (here / "onboarding.html").write_text(page_html(c, inline_svg, style))
    (here / "onboarding-inline.html").write_text(inline_fragment(c, inline_svg, style))
    (here / "benchmark-chart-light.svg").write_text(fixed_svg(c, svg, LIGHT) + "\n")
    (here / "benchmark-chart-dark.svg").write_text(fixed_svg(c, svg, DARK) + "\n")
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or \
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if pathlib.Path(chrome).exists():
        subprocess.run([chrome, "--headless=new", "--hide-scrollbars", "--force-device-scale-factor=2",
                        f"--window-size=720,{c.WINDOW_HEIGHT}", f"--screenshot={here / 'onboarding.png'}",
                        (here / "onboarding.html").as_uri()], check=True, capture_output=True)
    else:
        print("Chrome not found; onboarding.png not rebuilt")
    print("built", ", ".join(p.name for p in sorted(here.glob("*")) if p.suffix in {".svg", ".html", ".png"}))
