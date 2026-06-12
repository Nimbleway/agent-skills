#!/usr/bin/env python3
"""
build_dashboard.py — turn a COMPACT widget spec into a valid Databricks AI/BI (Lakeview)
dashboard, then create + publish it. Bakes in the gotchas that make hand-written Lakeview
JSON fail (see references/dashboard-cookbook.md).

Usage:
  python3 build_dashboard.py --spec spec.json [--host <workspace-host>] [--dashboard-id <id>]

- Reads `spec.json` (see SPEC FORMAT below), prints the dashboard_id + editor/published URLs.
- Auth + host come from the Databricks CLI (`databricks api ...`); no token handling here.
- With --dashboard-id it PATCHes an existing dashboard instead of creating one.

SPEC FORMAT (JSON):
{
  "display_name": "🐶 Amazon vs Walmart — Dog Products",
  "warehouse_id": "abc123",
  "datasets": [
    {"name": "main", "query": "SELECT * FROM users.me.dogs"}   // each query is ONE string (one line)
  ],
  "widgets": [
    {"type":"text","md":"# Title\\nSubtitle","pos":[0,0,6,1]},
    {"type":"filter","dataset":"main","field":"source","title":"Source","select":"single","pos":[0,1,2,1]},
    {"type":"counter","dataset":"main","label":"Avg Price","expr":"AVG(`price`)","format":"currency","pos":[0,2,2,3]},
    {"type":"bar","dataset":"main","x":"search_keyword","y":{"expr":"COUNT(`product_name`)"},
       "orientation":"horizontal","title":"Listings per keyword","pos":[0,5,3,6]},
    {"type":"bar","dataset":"main","x":"source","y":{"expr":"AVG(`price`)"},"color":"source",
       "title":"Avg price by source","pos":[3,5,3,6]},
    {"type":"scatter","dataset":"main","x":"price","y":"rating","color":"source","pos":[0,11,3,7]},
    {"type":"pie","dataset":"main","color":"source","angle":{"expr":"COUNT(`product_name`)"},
       "title":"Listings share","pos":[3,11,3,7]},
    {"type":"table","dataset":"main","title":"Products","pos":[0,18,6,9],
       "columns":[
         {"field":"product_url","title":"Open","link":true},
         {"field":"product_name","title":"Product"},
         {"field":"source","title":"Source"},
         {"field":"price","title":"Price","kind":"number"},
         {"field":"rating","title":"Rating","kind":"number"},
         {"field":"sponsored","title":"Ad","kind":"boolean"}
       ]}
  ]
}

pos = [x, y, width, height] on a 6-column grid.

Field/measure shorthand:
- x/y/color/angle/size accept a STRING (a column name → grouped dimension) OR
  {"expr": "<sql>", "name": "<optional alias>"} for a measure/aggregate.
- For counters, `expr` MUST be a top-level aggregate (AVG/SUM/COUNT/MIN/MAX). Do NOT wrap in
  ROUND()/CAST() — that makes AI/BI treat it as a dimension and the tile shows "No data".
  Use "format":"currency"|"number" + "decimals":N for display formatting instead.
"""
import argparse, json, os, re, subprocess, sys, tempfile


def db_api(method, path, body=None):
    cmd = ["databricks", "api", method.lower(), path]
    tmp = None
    if body is not None:
        # Pass the JSON body via a temp file (`--json @file`) instead of an argv string. A serialized
        # dashboard can be large, and a big inline argument risks exceeding the OS argv size limit.
        fd, tmp = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as fh:
            json.dump(body, fh)
        cmd += ["--json", f"@{tmp}"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True)
    finally:
        if tmp:
            os.unlink(tmp)
    if out.returncode != 0:
        sys.exit(f"databricks api {method} {path} failed:\n{out.stderr}\n{out.stdout}")
    return json.loads(out.stdout) if out.stdout.strip() else {}


def get_host(explicit):
    if explicit:
        return explicit.rstrip("/").replace("https://", "").replace("http://", "")
    out = subprocess.run(["databricks", "auth", "describe"], capture_output=True, text=True)
    m = re.search(r"Host:\s*https?://([^\s]+)", out.stdout)
    if not m:
        sys.exit("Could not determine workspace host; pass --host.")
    return m.group(1)


def slug(s):
    return re.sub(r"[^a-z0-9_]", "_", s.lower())[:40] or "f"


AGG_RE = re.compile(r"^\s*(AVG|SUM|COUNT|MIN|MAX|COUNT_IF|APPROX_COUNT_DISTINCT)\s*\(", re.I)


def field_spec(v, fallback_name):
    """Return (name, expression, is_measure) for a string field or {expr,name} object."""
    if isinstance(v, dict):
        expr = v["expr"]
        name = v.get("name") or slug(expr)
        return name, expr, True
    return v, f"`{v}`", False


def q(dataset, fields):
    return {"name": "main_query",
            "query": {"datasetName": dataset,
                      "fields": [{"name": n, "expression": e} for n, e in fields],
                      "disaggregated": False}}


def q_disagg(dataset, fields):
    qq = q(dataset, fields)
    qq["query"]["disaggregated"] = True
    return qq


def pos(p):
    return {"x": p[0], "y": p[1], "width": p[2], "height": p[3]}


# ---- widget builders -------------------------------------------------------

def w_text(w, i):
    return {"widget": {"name": f"text_{i}", "textbox_spec": w["md"]}, "position": pos(w["pos"])}


def w_counter(w, i):
    expr = w["expr"]
    if not AGG_RE.match(expr):
        print(f"  ! counter '{w.get('label')}' expr is not a top-level aggregate: {expr}\n"
              f"    AI/BI will likely show 'No data'. Use a bare AVG/SUM/COUNT and format via 'format'/'decimals'.",
              file=sys.stderr)
    name = slug(w.get("label", expr))
    val = {"fieldName": name, "displayName": w.get("label", "")}
    fmt = w.get("format")
    if fmt in ("currency", "number"):
        places = w.get("decimals", 2)
        val["format"] = ({"type": "number-currency", "currencyCode": "USD",
                          "decimalPlaces": {"type": "exact", "places": places}}
                         if fmt == "currency" else
                         {"type": "number-plain", "decimalPlaces": {"type": "exact", "places": places}})
    spec = {"version": 2, "widgetType": "counter", "encodings": {"value": val}}
    if w.get("label"):
        spec["frame"] = {"showDescription": True, "description": w["label"]}
    return {"widget": {"name": f"counter_{i}", "queries": [q(w["dataset"], [(name, expr)])], "spec": spec},
            "position": pos(w["pos"])}


def _xy_chart(w, i, wtype):
    fields, enc = [], {}
    xn, xe, _ = field_spec(w["x"], "x")
    fields.append((xn, xe))
    yn, ye, y_is_measure = field_spec(w["y"], "y")
    fields.append((yn, ye))
    disagg = (wtype == "scatter")  # scatter plots raw points; bar/line/area group
    enc["x"] = {"fieldName": xn, "scale": {"type": "quantitative" if wtype == "scatter" else "categorical"},
                "displayName": xn}
    enc["y"] = {"fieldName": yn, "scale": {"type": "quantitative"}, "displayName": yn}
    if wtype in ("bar", "line", "area") and w.get("orientation") == "horizontal":
        enc["x"], enc["y"] = (
            {"fieldName": yn, "scale": {"type": "quantitative"}, "displayName": yn},
            {"fieldName": xn, "scale": {"type": "categorical"}, "displayName": xn},
        )
    for opt in ("color", "size"):
        if opt in w:
            on, oe, om = field_spec(w[opt], opt)
            fields.append((on, oe))
            enc[opt] = {"fieldName": on,
                        "scale": {"type": "quantitative" if om else "categorical"}, "displayName": on}
    if wtype == "bar":
        enc["label"] = {"show": True}
    query = q_disagg(w["dataset"], fields) if disagg else q(w["dataset"], fields)
    spec = {"version": 3, "widgetType": wtype, "encodings": enc}
    if w.get("title"):
        spec["frame"] = {"showTitle": True, "title": w["title"]}
    return {"widget": {"name": f"{wtype}_{i}", "queries": [query], "spec": spec}, "position": pos(w["pos"])}


def w_pie(w, i):
    fields, enc = [], {}
    cn, ce, _ = field_spec(w["color"], "color")
    an, ae, _ = field_spec(w["angle"], "angle")
    fields = [(cn, ce), (an, ae)]
    enc["color"] = {"fieldName": cn, "scale": {"type": "categorical"}, "displayName": cn}
    enc["angle"] = {"fieldName": an, "scale": {"type": "quantitative"}, "displayName": an}
    spec = {"version": 3, "widgetType": w.get("type", "pie"), "encodings": enc}
    if w.get("title"):
        spec["frame"] = {"showTitle": True, "title": w["title"]}
    return {"widget": {"name": f"pie_{i}", "queries": [q(w["dataset"], fields)], "spec": spec},
            "position": pos(w["pos"])}


def _column(c, order):
    kind = c.get("kind", "string")
    type_map = {"string": "string", "number": "float", "boolean": "boolean", "integer": "integer"}
    col = {
        "fieldName": c["field"], "displayName": c["field"], "title": c.get("title", c["field"]),
        "type": type_map.get(kind, "string"),
        "displayAs": "link" if c.get("link") else ("number" if kind in ("number", "integer") else kind),
        "visible": True, "order": order,
        "allowSearch": bool(c.get("search", kind == "string" and not c.get("link"))),
        "alignContent": "right" if kind in ("number", "integer") else ("center" if kind == "boolean" else "left"),
        "linkUrlTemplate": "{{ @ }}", "linkTextTemplate": (c.get("link_text", "Open ↗") if c.get("link") else "{{ @ }}"),
        "linkTitleTemplate": "{{ @ }}", "linkOpenInNewTab": True, "highlightLinks": bool(c.get("link")),
        "allowHTML": False, "useMonospaceFont": False, "preserveWhitespace": False,
        "imageUrlTemplate": "{{ @ }}", "imageTitleTemplate": "{{ @ }}", "imageWidth": "", "imageHeight": "",
        "booleanValues": ["false", "true"],
    }
    if kind == "number":
        col["numberFormat"] = c.get("number_format", "0.00")
    if kind == "integer":
        col["numberFormat"] = c.get("number_format", "0,0")
    return col


def w_table(w, i):
    cols = w["columns"]
    fields = [(c["field"], f"`{c['field']}`") for c in cols]
    spec = {
        "version": 1, "widgetType": "table",
        "allowHTMLByDefault": False, "condensed": True, "withRowNumber": False,
        "itemsPerPage": w.get("page_size", 25), "paginationSize": "default", "invisibleColumns": [],
        "encodings": {"columns": [_column(c, n) for n, c in enumerate(cols)]},
    }
    if w.get("title"):
        spec["frame"] = {"showTitle": True, "title": w["title"]}
    return {"widget": {"name": f"table_{i}", "queries": [q_disagg(w["dataset"], fields)], "spec": spec},
            "position": pos(w["pos"])}


def w_filter(w, i):
    field = w["field"]
    qname = f"filter_{slug(field)}_{i}_q"
    multi = w.get("select", "single") == "multi"
    query = {"name": qname, "query": {"datasetName": w["dataset"], "fields": [
        {"name": field, "expression": f"`{field}`"},
        {"name": f"{field}_associativity", "expression": "COUNT_IF(`associative_filter_predicate_group`)"},
    ], "disaggregated": False}}
    spec = {"version": 2, "widgetType": "filter-multi-select" if multi else "filter-single-select",
            "encodings": {"fields": [{"fieldName": field, "displayName": field, "queryName": qname}]},
            "frame": {"showTitle": True, "title": w.get("title", field)}, "disallowAll": False}
    return {"widget": {"name": f"filter_{i}", "queries": [query], "spec": spec}, "position": pos(w["pos"])}


BUILDERS = {
    "text": w_text, "counter": w_counter, "table": w_table, "filter": w_filter,
    "pie": w_pie, "donut": w_pie,
    "bar": lambda w, i: _xy_chart(w, i, "bar"),
    "line": lambda w, i: _xy_chart(w, i, "line"),
    "area": lambda w, i: _xy_chart(w, i, "area"),
    "scatter": lambda w, i: _xy_chart(w, i, "scatter"),
}


def build_serialized(spec):
    datasets = []
    for d in spec["datasets"]:
        query = d["query"]
        if "\n" in query:
            # queryLines are joined WITHOUT whitespace — collapse to one line to avoid welded tokens.
            query = re.sub(r"\s+", " ", query).strip()
        datasets.append({"name": d["name"], "displayName": d.get("display_name", d["name"]),
                         "queryLines": [query]})
    layout = []
    for i, w in enumerate(spec["widgets"]):
        b = BUILDERS.get(w["type"])
        if not b:
            sys.exit(f"Unknown widget type: {w['type']}")
        layout.append(b(w, i))
    return {"datasets": datasets,
            "pages": [{"name": "page", "displayName": spec.get("page_title", "Overview"), "layout": layout}]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--host", default=None)
    ap.add_argument("--dashboard-id", default=None)
    args = ap.parse_args()

    spec = json.load(open(args.spec))
    wh = spec["warehouse_id"]
    serialized = json.dumps(build_serialized(spec))
    host = get_host(args.host)

    if args.dashboard_id:
        cur = db_api("GET", f"/api/2.0/lakeview/dashboards/{args.dashboard_id}")
        res = db_api("PATCH", f"/api/2.0/lakeview/dashboards/{args.dashboard_id}",
                     {"display_name": spec["display_name"], "warehouse_id": wh,
                      "etag": cur["etag"], "serialized_dashboard": serialized})
        did = args.dashboard_id
    else:
        res = db_api("POST", "/api/2.0/lakeview/dashboards",
                     {"display_name": spec["display_name"], "warehouse_id": wh,
                      "serialized_dashboard": serialized})
        did = res["dashboard_id"]

    db_api("POST", f"/api/2.0/lakeview/dashboards/{did}/published",
           {"warehouse_id": wh, "embed_credentials": True})

    print(json.dumps({
        "dashboard_id": did,
        "editor": f"https://{host}/dashboardsv3/{did}/editor",
        "published": f"https://{host}/dashboardsv3/{did}/published",
    }, indent=2))


if __name__ == "__main__":
    main()
