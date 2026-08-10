#!/usr/bin/env python3
"""Validate the plugin manifests against each marketplace's published field rules.

The companion script, check-plugin-structure.sh, validates the *skills tree*: where
SKILL.md files sit and what their frontmatter says. This script validates the
*manifests*: the fields OpenAI reads off .codex-plugin/plugin.json to build a listing,
plus the shape of the shared MCP config every platform loads.

Nothing else in CI covers that surface. Setting `skills` to an array, dropping the logo,
or picking a brand color that fails the contrast gate all pass the structure check and a
JSON parse, then fail at submission — which is the slowest possible place to learn.

Checks are named after the error code OpenAI would raise, so a CI failure here maps
directly onto the published submission-error reference rather than needing translation.

Version *parity* across manifests is deliberately not checked here — scripts/tag-release.sh
owns that assertion, and duplicating it would mean two places to update.

Usage:
    python3 scripts/check-plugin-manifests.py
"""

from __future__ import annotations

import json
import os
import re
import struct
import sys
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CODEX = ".codex-plugin/plugin.json"
GROK = ".grok-plugin/plugin.json"
ALL_MANIFESTS = [
    ".claude-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    CODEX,
    GROK,
]
MCP_CONFIG = ".mcp.json"

# The portable Agent Plugins MCP config, at the spec's canonical root path. Distinct
# from MCP_CONFIG on purpose — see the portable-config section in main() for why the
# two files cannot be merged.
PORTABLE_MCP = "mcp.json"
PORTABLE_MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"

# The portable Agent Plugins manifest, at the spec's canonical root path. It coexists
# with the per-client manifests rather than replacing them: no current consumer reads
# a root plugin.json (OpenAI accepts .codex-plugin/, .agent-plugin/ and .claude-plugin/;
# xAI reads .grok-plugin/ then .claude-plugin/), so this is additive.
PORTABLE_PLUGIN = "plugin.json"
PORTABLE_PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
# additionalProperties: false — anything outside this set is rejected. Note that
# `category` and `tags`, which the Cursor and marketplace manifests carry, are NOT
# permitted here; they belong under an `extensions` namespace if ever needed.
PORTABLE_PLUGIN_FIELDS = {
    "$schema", "name", "version", "description", "author",
    "homepage", "repository", "license", "keywords", "extensions",
}
PORTABLE_PLUGIN_REQUIRED = {"$schema", "name"}
PORTABLE_AUTHOR_FIELDS = {"name", "email", "url"}
# From the published schema, verbatim.
PORTABLE_NAME_PATTERN = r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$"
# Each transport `type` is a `const` in the published schema; a server declares exactly
# one. REQUIRED is the field the schema demands alongside `type`; PERMITTED is the full
# set of *declared* properties for that transport. The two are not the same — every
# server sets additionalProperties: false, so a key outside PERMITTED is rejected, but
# the optional keys inside it are perfectly valid. Conflating the two rejects a standard
# stdio server that carries `args`.
PORTABLE_TRANSPORT_REQUIRED = {
    "stdio": "command",
    "streamable-http": "url",
    "sse": "url",
}
PORTABLE_TRANSPORT_PERMITTED = {
    "stdio": {"type", "command", "args", "env", "cwd"},
    "streamable-http": {"type", "url", "headers"},
    "sse": {"type", "url", "headers"},
}
# Optional fields, with the type the schema declares, so a wrong type is caught rather
# than passed through on truthiness.
PORTABLE_SERVER_FIELD_TYPES = {
    "args": ("array of strings", lambda v: isinstance(v, list)
             and all(isinstance(i, str) for i in v)),
    "env": ("object with string values", lambda v: isinstance(v, dict)
            and all(isinstance(i, str) for i in v.values())),
    "cwd": ("string", lambda v: isinstance(v, str)),
    "headers": ("object with string values", lambda v: isinstance(v, dict)
                and all(isinstance(i, str) for i in v.values())),
}

# interface.category must come from this fixed list (plugin_category_unknown).
CATEGORIES = {
    "Productivity", "Creativity", "Developer Tools", "Business & Operations",
    "Data & Analytics", "Communication", "Education & Research", "Security",
    "Finance", "Healthcare", "Travel", "Entertainment", "Other",
}

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".svg")

# Two-tier limits: OpenAI accepts a longer value when validating the package and a
# shorter one at final submission. The submission limit is the binding gate, so it is
# what fails here — catching it at PR time instead of at the portal.
LIMIT_DISPLAY_NAME = 30        # 80 at package validation
LIMIT_SHORT_DESCRIPTION = 30   # 240 at package validation
LIMIT_DEVELOPER_NAME = 80      # 120 at package validation
LIMIT_DEFAULT_PROMPT = 128     # 512 at package validation
LIMIT_LONG_DESCRIPTION = 4000
LIMIT_DESCRIPTION = 1024
MAX_DEFAULT_PROMPTS = 3
MAX_CAPABILITIES = 20

problems: list[str] = []
checked = 0


def rel(path: str) -> str:
    """Strip a single leading './' from a declared path.

    Not str.lstrip('./') — that strips *characters*, so './.mcp.json' would come back
    as 'mcp.json' and every dotfile path would silently mismatch.
    """
    return path[2:] if path.startswith("./") else path


def fail(code: str, detail: str) -> None:
    global checked
    checked += 1
    problems.append(f"  {code:<40} {detail}")


def check(code: str, condition: bool, detail: str) -> bool:
    """Record one named check. Returns the condition so callers can short-circuit."""
    global checked
    checked += 1
    if not condition:
        problems.append(f"  {code:<40} {detail}")
    return condition


# ---------------------------------------------------------------------------
# Color contrast — WCAG relative luminance, the same formula OpenAI's gate uses.
# ---------------------------------------------------------------------------
def _luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    channels = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# ---------------------------------------------------------------------------
# Image dimensions, from the file header. Every supported format is parsed rather
# than assumed: a format we cannot measure is reported, never silently passed.
# ---------------------------------------------------------------------------
def image_size(path: str) -> tuple[int, int] | None:
    with open(path, "rb") as fh:
        data = fh.read()

    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])

    if data[:2] == b"\xff\xd8":  # JPEG — walk to the first SOF marker
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                          0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
        return None

    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        chunk = data[12:16]
        if chunk == b"VP8X":
            w = int.from_bytes(data[24:27], "little") + 1
            h = int.from_bytes(data[27:30], "little") + 1
            return w, h
        if chunk == b"VP8 ":
            return struct.unpack("<HH", data[26:30])[0] & 0x3FFF, \
                   struct.unpack("<HH", data[26:30])[1] & 0x3FFF
        if chunk == b"VP8L":
            bits = int.from_bytes(data[21:25], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        return None

    if b"<svg" in data[:1024]:
        try:
            root = ET.fromstring(data.decode("utf-8", "replace"))
        except ET.ParseError:
            return None
        box = root.get("viewBox")
        if box:
            nums = re.findall(r"-?[\d.]+", box)
            if len(nums) == 4:
                return int(float(nums[2])), int(float(nums[3]))
        w, h = root.get("width"), root.get("height")
        if w and h:
            # A percentage width is not a dimension, so it stays unmeasured rather
            # than being silently coerced to a number that would pass the gate.
            if "%" in w or "%" in h:
                return None
            try:
                return (int(float(re.sub(r"[a-z]+$", "", w.strip()))),
                        int(float(re.sub(r"[a-z]+$", "", h.strip()))))
            except ValueError:
                return None
        return None

    return None


def check_asset(field: str, value: object, required: bool) -> None:
    """Validate one declared asset path and, when it is an image, its dimensions."""
    if value is None:
        if required:
            fail(f"plugin_{field}_path_missing", f"interface.{field} is required")
        return

    if not check("declared_asset_path_wrong_type", isinstance(value, str),
                 f"interface.{field} must be a string"):
        return
    path = str(value)

    check("declared_asset_path_empty", path != "", f"interface.{field} is empty")
    check("declared_asset_path_has_outer_whitespace", path == path.strip(),
          f"interface.{field} has leading/trailing whitespace")
    check("declared_asset_path_has_control_character",
          not any(ord(c) < 0x20 or ord(c) == 0x7F for c in path),
          f"interface.{field} contains a control character")
    check("branding_asset_path_missing_root_prefix", path.startswith("./"),
          f"interface.{field} must start with './' (got {path!r})")
    check("declared_asset_path_unsafe",
          not os.path.isabs(path) and ".." not in path.split("/"),
          f"interface.{field} must be a relative path inside the plugin")

    abs_path = os.path.join(REPO_ROOT, rel(path))
    if not check("declared_asset_file_missing", os.path.exists(abs_path),
                 f"interface.{field} -> {path} does not exist"):
        return
    if not check("declared_asset_not_regular_file", os.path.isfile(abs_path),
                 f"interface.{field} -> {path} is not a regular file"):
        return

    ext = os.path.splitext(path)[1].lower()
    if not check("image_file_format_unsupported", ext in IMAGE_EXTS,
                 f"interface.{field} must end in one of {', '.join(IMAGE_EXTS)}"):
        return

    size_bytes = os.path.getsize(abs_path)
    check("image_file_too_large", size_bytes <= 5 * 1024 * 1024,
          f"interface.{field} is {size_bytes / 1024 / 1024:.2f} MiB, limit 5 MiB")

    dims = image_size(abs_path)
    if not check("raster_image_decode_failed", dims is not None,
                 f"interface.{field} -> {path}: could not read dimensions; "
                 f"extend image_size() for this format rather than skipping it"):
        return

    w, h = dims
    prefix = "svg" if ext == ".svg" else "raster_image"
    check(f"{prefix}_dimensions_not_square", w == h,
          f"interface.{field} is {w}x{h}, must be square")
    check(f"{prefix}_dimensions_too_small", w >= 48 and h >= 48,
          f"interface.{field} is {w}x{h}, minimum 48x48")
    if prefix == "raster_image":
        check("raster_image_dimensions_too_large", w <= 4096 and h <= 4096,
              f"interface.{field} is {w}x{h}, maximum 4096x4096")


def check_https(field: str, code: str, value: object) -> None:
    """Validate an optional listing URL. `field` names it for humans, `code` for OpenAI."""
    if value is None:
        return
    if not check(f"plugin_{code}_wrong_type", isinstance(value, str),
                 f"interface.{field} must be a string"):
        return
    url = str(value)
    check(f"plugin_{code}_empty", url != "", f"interface.{field} is empty")
    check(f"plugin_{code}_format", url.startswith("https://"),
          f"interface.{field} must be HTTPS (got {url!r})")
    check(f"plugin_{code}_too_long", len(url) <= 2048,
          f"interface.{field} is {len(url)} chars, limit 2048")


def check_color(field: str, code: str, value: object, against: str, label: str) -> None:
    """Validate a brand color's format and its contrast against the surface behind it.

    `field` names it for humans, `code` for OpenAI's error reference.
    """
    if value is None:
        return
    if not check(f"plugin_{code}_wrong_type", isinstance(value, str),
                 f"interface.{field} must be a string"):
        return
    color = str(value)
    if not check(f"plugin_{code}_format",
                 bool(re.fullmatch(r"#[0-9A-Fa-f]{6}", color)),
                 f"interface.{field} must be a six-digit hex color (got {color!r})"):
        return
    ratio = contrast_ratio(color, against)
    check(f"plugin_{code}_contrast", ratio >= 2.0,
          f"interface.{field} {color} has {ratio:.2f}:1 against {label}, minimum 2:1")


def main() -> int:
    os.chdir(REPO_ROOT)

    # -- every manifest must be readable, well-formed JSON ------------------
    print("Manifests parse:")
    manifests: dict[str, dict] = {}
    for path in ALL_MANIFESTS + [MCP_CONFIG, PORTABLE_MCP, PORTABLE_PLUGIN]:
        if not check("plugin_manifest_missing", os.path.isfile(path), f"{path} not found"):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                loaded = json.load(fh)
        except UnicodeDecodeError:
            fail("plugin_manifest_unreadable", f"{path} is not valid UTF-8")
            continue
        except json.JSONDecodeError as exc:
            fail("plugin_manifest_json_malformed", f"{path} line {exc.lineno}: {exc.msg}")
            continue
        if not check("plugin_manifest_root_not_object", isinstance(loaded, dict),
                     f"{path} top level must be a JSON object"):
            continue
        manifests[path] = loaded
        print(f"  ok       {path}")

    # -- the shared MCP config ---------------------------------------------
    # Claude Code accepts either a bare server map or an {"mcpServers": {...}}
    # wrapper; the official Linear, Asana, and GitHub plugins ship the bare map.
    # Either shape is fine, but it must be one of them and it must be non-empty,
    # because the Codex manifest declares this file as its MCP surface.
    mcp = manifests.get(MCP_CONFIG)
    if mcp is not None:
        servers = mcp.get("mcpServers", mcp)
        check("mcp_config_shape", isinstance(servers, dict) and len(servers) > 0,
              f"{MCP_CONFIG} must declare at least one server, as a bare map or "
              f'under an "mcpServers" key')
        if isinstance(servers, dict):
            for name, cfg in servers.items():
                check("mcp_server_entry", isinstance(cfg, dict),
                      f"{MCP_CONFIG}: server {name!r} must be an object")

    # -- the Grok manifest's inline MCP declaration must not drift ----------
    #
    # The Grok manifest declares mcpServers as an inline object rather than as a path
    # to .mcp.json, and that is deliberate. xAI's indexer reads only the "mcpServers"
    # key out of a .mcp.json file; ours is a bare server map, so a path declaration
    # would index zero servers and the Grok listing would claim the plugin ships no
    # MCP server at all. Declaring inline is what lets .mcp.json stay byte-identical
    # and keeps Claude Code's Connector registration untouched.
    #
    # The cost of that is one duplicated server config. This asserts the copies agree,
    # so a URL or transport change in .mcp.json cannot silently leave the Grok listing
    # pointing somewhere else. Do NOT "simplify" the Grok manifest to a path — it looks
    # tidier and quietly breaks the listing.
    print("\nGrok manifest, inline MCP declaration:")
    grok = manifests.get(GROK)
    problems_before = len(problems)
    inline = None
    canonical = None
    if grok is not None and mcp is not None:
        inline = grok.get("mcpServers")
        if check("grok_mcp_servers_inline", isinstance(inline, dict),
                 f"{GROK} must declare mcpServers as an inline object, not a path — "
                 f"a path resolves to a bare server map that xAI indexes as zero servers"):
            canonical = mcp.get("mcpServers", mcp)
            if isinstance(canonical, dict):
                missing = set(canonical) - set(inline)
                extra = set(inline) - set(canonical)
                check("grok_mcp_servers_missing", not missing,
                      f"{GROK} is missing server(s) present in {MCP_CONFIG}: "
                      f"{sorted(missing)}")
                check("grok_mcp_servers_extra", not extra,
                      f"{GROK} declares server(s) absent from {MCP_CONFIG}: "
                      f"{sorted(extra)}")
                for name in sorted(set(canonical) & set(inline)):
                    check("grok_mcp_server_drift", inline[name] == canonical[name],
                          f"{GROK} server {name!r} does not match {MCP_CONFIG}: "
                          f"{inline[name]!r} != {canonical[name]!r}")
    elif grok is None:
        fail("grok_manifest_missing", f"{GROK} not found")

    # Claim agreement only when the comparison actually ran and found nothing wrong.
    #
    # All three conditions are load-bearing. `problems_before` is snapshotted after the
    # earlier .mcp.json shape validation, so "no new problems here" does not imply the
    # canonical config is well-formed — both isinstance guards are what establish that.
    # Without them a malformed config (say {"mcpServers": null}) reaches len() and raises
    # TypeError, crashing the checker instead of reporting the error it exists to report;
    # a string value would print a server count taken from its character length.
    if (
        len(problems) == problems_before
        and isinstance(inline, dict)
        and isinstance(canonical, dict)
    ):
        print(f"  ok       {len(canonical)} server(s) match {MCP_CONFIG}")
    # -- the portable Agent Plugins MCP config, at the canonical root path --
    #
    # Two MCP files, deliberately. They describe the same endpoint in different
    # vocabularies, and no single file satisfies every consumer:
    #
    #   portable mcp.json   "type": "streamable-http"   (a schema const)
    #   Claude .mcp.json    "type": "http"
    #   Codex               no type key; HTTP inferred from the presence of url
    #
    # The portable schema also sets additionalProperties: false at the root and on
    # every server, so there is no room to carry a second vocabulary in one file.
    # Do not "harmonise" these — of the two, only .mcp.json is read by Claude Code's
    # Connector registration, so collapsing them breaks the primary install path.
    print(f"\nPortable MCP config ({PORTABLE_MCP}):")
    portable = manifests.get(PORTABLE_MCP)
    portable_problems_before = len(problems)
    if portable is not None:
        check("portable_mcp_schema_missing", "$schema" in portable,
              f"{PORTABLE_MCP} must declare $schema — it is required by the spec")
        if "$schema" in portable:
            check("portable_mcp_schema_wrong", portable["$schema"] == PORTABLE_MCP_SCHEMA,
                  f"{PORTABLE_MCP} $schema must be exactly {PORTABLE_MCP_SCHEMA!r}, "
                  f"got {portable['$schema']!r}")
        extra = set(portable) - {"$schema", "mcpServers"}
        check("portable_mcp_additional_properties", not extra,
              f"{PORTABLE_MCP} permits only $schema and mcpServers at the top level "
              f"(additionalProperties: false); found {sorted(extra)}")

        p_servers = portable.get("mcpServers")
        if check("portable_mcp_servers_missing",
                 isinstance(p_servers, dict) and len(p_servers) > 0,
                 f"{PORTABLE_MCP} must declare mcpServers with at least one server"):
            for name, cfg in p_servers.items():
                if not check("portable_mcp_server_wrong_type", isinstance(cfg, dict),
                             f"{PORTABLE_MCP}: server {name!r} must be an object"):
                    continue
                transport = cfg.get("type")
                if not check(
                    "portable_mcp_transport_invalid",
                    transport in PORTABLE_TRANSPORT_REQUIRED,
                    f"{PORTABLE_MCP}: server {name!r} type must be one of "
                    f"{sorted(PORTABLE_TRANSPORT_REQUIRED)}, got {transport!r} — note "
                    f'"http" is the Claude vocabulary and is not valid here',
                ):
                    continue

                # The schema types this as a string with minLength 1, so check the type
                # rather than truthiness — a number or object is truthy and would
                # otherwise pass a gate whose whole job is rejecting invalid shapes.
                required = PORTABLE_TRANSPORT_REQUIRED[transport]
                value = cfg.get(required)
                check("portable_mcp_server_missing_field",
                      isinstance(value, str) and value.strip() != "",
                      f"{PORTABLE_MCP}: server {name!r} with type {transport!r} requires "
                      f"{required!r} as a non-empty string, got {type(value).__name__}"
                      + ("" if value is None else f" ({value!r})"))

                # PERMITTED, not {type, required}: the optional declared fields are valid.
                allowed = PORTABLE_TRANSPORT_PERMITTED[transport]
                server_extra = set(cfg) - allowed
                check("portable_mcp_server_additional_properties", not server_extra,
                      f"{PORTABLE_MCP}: server {name!r} with type {transport!r} permits "
                      f"only {sorted(allowed)} (additionalProperties: false); found "
                      f"{sorted(server_extra)}")

                for field, (described, ok) in PORTABLE_SERVER_FIELD_TYPES.items():
                    if field in cfg and field in allowed:
                        check("portable_mcp_server_field_wrong_type", ok(cfg[field]),
                              f"{PORTABLE_MCP}: server {name!r} field {field!r} must be "
                              f"{described}, got {type(cfg[field]).__name__}")
    elif not os.path.isfile(os.path.join(REPO_ROOT, PORTABLE_MCP)):
        fail("portable_mcp_missing", f"{PORTABLE_MCP} not found at the plugin root")
    # Otherwise the file exists but did not parse into a JSON object, and the
    # plugin_manifest_* checks above already said so. Claiming "not found" here would
    # add a second, contradictory error for one underlying problem.
    # Only claim validity when every check in this section actually passed.
    if len(problems) == portable_problems_before and isinstance(portable, dict):
        print(f"  ok       {len(portable.get('mcpServers', {}))} server(s), "
              f"schema and transports valid")

    # -- the portable Agent Plugins manifest ---------------------------------
    print(f"\nPortable manifest ({PORTABLE_PLUGIN}):")
    pp = manifests.get(PORTABLE_PLUGIN)
    pp_problems_before = len(problems)
    if pp is not None:
        missing_required = PORTABLE_PLUGIN_REQUIRED - set(pp)
        check("portable_plugin_required_missing", not missing_required,
              f"{PORTABLE_PLUGIN} is missing required field(s): "
              f"{sorted(missing_required)}")
        if "$schema" in pp:
            check("portable_plugin_schema_wrong",
                  pp["$schema"] == PORTABLE_PLUGIN_SCHEMA,
                  f"{PORTABLE_PLUGIN} $schema must be exactly "
                  f"{PORTABLE_PLUGIN_SCHEMA!r}, got {pp['$schema']!r}")

        disallowed = set(pp) - PORTABLE_PLUGIN_FIELDS
        check("portable_plugin_additional_properties", not disallowed,
              f"{PORTABLE_PLUGIN} permits only {sorted(PORTABLE_PLUGIN_FIELDS)} "
              f"(additionalProperties: false); found {sorted(disallowed)} — note "
              f"'category' and 'tags' belong under an extensions namespace")

        name = pp.get("name")
        if check("portable_plugin_name_wrong_type", isinstance(name, str) and name,
                 f"{PORTABLE_PLUGIN} name must be a non-empty string"):
            check("portable_plugin_name_pattern",
                  bool(re.match(PORTABLE_NAME_PATTERN, name)),
                  f"{PORTABLE_PLUGIN} name {name!r} must match {PORTABLE_NAME_PATTERN}")
            check("portable_plugin_name_too_long", len(name) <= 64,
                  f"{PORTABLE_PLUGIN} name is {len(name)} chars, limit 64")

        author = pp.get("author")
        if author is not None:
            if check("portable_plugin_author_wrong_type", isinstance(author, dict),
                     f"{PORTABLE_PLUGIN} author must be an object"):
                author_extra = set(author) - PORTABLE_AUTHOR_FIELDS
                check("portable_plugin_author_additional_properties",
                      not author_extra,
                      f"{PORTABLE_PLUGIN} author permits only "
                      f"{sorted(PORTABLE_AUTHOR_FIELDS)}; found {sorted(author_extra)}")

        keywords = pp.get("keywords")
        if keywords is not None:
            check("portable_plugin_keywords_wrong_type",
                  isinstance(keywords, list)
                  and all(isinstance(k, str) for k in keywords),
                  f"{PORTABLE_PLUGIN} keywords must be an array of strings")

        extensions = pp.get("extensions")
        if extensions is not None:
            if check("portable_plugin_extensions_wrong_type",
                     isinstance(extensions, dict),
                     f"{PORTABLE_PLUGIN} extensions must be an object"):
                for ns, value in extensions.items():
                    check("portable_plugin_extension_wrong_type",
                          isinstance(value, dict),
                          f"{PORTABLE_PLUGIN} extensions[{ns!r}] must be an object")
    elif not os.path.isfile(os.path.join(REPO_ROOT, PORTABLE_PLUGIN)):
        fail("portable_plugin_missing",
             f"{PORTABLE_PLUGIN} not found at the plugin root")
    # Same reasoning as the MCP config above: a file that exists but failed to parse
    # into an object has already been reported by the plugin_manifest_* checks.
    if len(problems) == pp_problems_before and isinstance(pp, dict):
        print(f"  ok       schema, name, and {len(set(pp) - {'$schema'})} "
              f"declared field(s) valid")

    codex = manifests.get(CODEX)
    if codex is None:
        print("\nERROR: cannot validate the Codex manifest — it did not parse.")
        return 1

    # -- top-level Codex fields --------------------------------------------
    print("\nCodex manifest, top level:")
    name = codex.get("name")
    check("plugin_name_missing", isinstance(name, str) and name != "",
          "name is required and must be a non-empty string")
    if isinstance(name, str):
        check("plugin_name_too_long", len(name) <= 64,
              f"name is {len(name)} chars, limit 64")
        check("plugin_name_format",
              bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name)),
              f"name {name!r} must start alphanumeric and use only letters, digits, _ and -")

    version = codex.get("version")
    check("plugin_version_missing", isinstance(version, str) and version != "",
          "version is required")
    if isinstance(version, str):
        check("plugin_version_not_semver",
              bool(re.fullmatch(r"\d+\.\d+\.\d+", version)),
              f"version {version!r} must be semver (X.Y.Z)")

    description = codex.get("description")
    check("plugin_description_missing", isinstance(description, str) and description != "",
          "description is required")
    if isinstance(description, str):
        check("plugin_description_too_long", len(description) <= LIMIT_DESCRIPTION,
              f"description is {len(description)} chars, limit {LIMIT_DESCRIPTION}")

    author = codex.get("author")
    author_name = None
    if author is not None:
        if check("plugin_author_wrong_type", isinstance(author, dict),
                 "author must be an object"):
            author_name = author.get("name")
            if author_name is not None:
                check("plugin_author_name_too_long",
                      isinstance(author_name, str) and len(author_name) <= 120,
                      "author.name must be a string of at most 120 chars")
            email = author.get("email")
            if email is not None:
                check("plugin_author_email_too_long",
                      isinstance(email, str) and len(email) <= 320,
                      "author.email must be a string of at most 320 chars")
            url = author.get("url")
            if url is not None and check("plugin_author_url_wrong_type",
                                         isinstance(url, str), "author.url must be a string"):
                check("plugin_author_url_not_https", str(url).startswith("https://"),
                      "author.url must be HTTPS")
                check("plugin_author_url_has_credentials", "@" not in str(url).split("//")[-1].split("/")[0],
                      "author.url must not contain credentials")

    homepage = codex.get("homepage")
    if homepage is not None:
        check("plugin_homepage_format",
              isinstance(homepage, str) and homepage.startswith("https://"),
              "homepage must be HTTPS")

    # -- content surfaces --------------------------------------------------
    print("\nCodex manifest, content surfaces:")
    skills = codex.get("skills")
    if skills is not None:
        if check("plugin_skills_path_wrong_type", isinstance(skills, str),
                 f"skills must be a string path, not {type(skills).__name__} — "
                 f"an array is rejected outright"):
            check("plugin_skills_path_empty", skills != "", "skills is empty")
            check("plugin_skills_path_unsupported",
                  rel(skills).rstrip("/") == "skills",
                  f"skills must resolve to the root skills/ directory (got {skills!r})")
            check("plugin_skills_directory_missing", os.path.isdir(rel(skills)),
                  f"declared skills directory {skills!r} does not exist")
            check("plugin_skills_path_not_directory", os.path.isdir(rel(skills)),
                  f"{skills!r} must be a directory")

    mcp_field = codex.get("mcpServers")
    if mcp_field is not None:
        if check("mcp_servers_path_wrong_type", isinstance(mcp_field, str),
                 "mcpServers must be a string path"):
            check("mcp_servers_path_unsupported", rel(mcp_field) == MCP_CONFIG,
                  f"mcpServers must resolve to the root {MCP_CONFIG} (got {mcp_field!r})")
            check("mcp_servers_file_missing", os.path.isfile(rel(mcp_field)),
                  f"declared {mcp_field!r} does not exist")

    apps = codex.get("apps")
    if apps is not None:
        if check("plugin_apps_path_wrong_type", isinstance(apps, str),
                 "apps must be a string path"):
            check("plugin_apps_path_unsupported", rel(apps) == ".app.json",
                  f"apps must resolve to the root .app.json (got {apps!r})")
            check("plugin_apps_file_missing", os.path.isfile(rel(apps)),
                  f"declared {apps!r} does not exist")

    # -- the interface block -----------------------------------------------
    print("\nCodex manifest, interface block:")
    interface = codex.get("interface")
    if not check("plugin_interface_wrong_type", isinstance(interface, dict),
                 "interface must be a JSON object"):
        return report()

    display_name = interface.get("displayName")
    if check("plugin_display_name_empty",
             isinstance(display_name, str) and display_name.strip() != "",
             "interface.displayName is required and must be non-empty"):
        check("plugin_display_name_too_long", len(display_name) <= LIMIT_DISPLAY_NAME,
              f"interface.displayName is {len(display_name)} chars, "
              f"limit {LIMIT_DISPLAY_NAME} at submission")

    short_description = interface.get("shortDescription")
    if check("plugin_short_description_missing",
             isinstance(short_description, str) and short_description.strip() != "",
             "interface.shortDescription is required and must be non-empty"):
        check("plugin_short_description_too_long",
              len(short_description) <= LIMIT_SHORT_DESCRIPTION,
              f"interface.shortDescription is {len(short_description)} chars, "
              f"limit {LIMIT_SHORT_DESCRIPTION} at submission")
        check("plugin_short_description_character_unsupported",
              "\n" not in short_description,
              "interface.shortDescription must be a single line")

    long_description = interface.get("longDescription")
    if check("plugin_long_description_empty",
             isinstance(long_description, str) and long_description.strip() != "",
             "interface.longDescription is required and must be non-empty"):
        check("plugin_long_description_too_long",
              len(long_description) <= LIMIT_LONG_DESCRIPTION,
              f"interface.longDescription is {len(long_description)} chars, "
              f"limit {LIMIT_LONG_DESCRIPTION}")

    developer_name = interface.get("developerName")
    if check("plugin_developer_name_empty",
             isinstance(developer_name, str) and developer_name.strip() != "",
             "interface.developerName is required and must be non-empty"):
        check("plugin_developer_name_too_long",
              len(developer_name) <= LIMIT_DEVELOPER_NAME,
              f"interface.developerName is {len(developer_name)} chars, "
              f"limit {LIMIT_DEVELOPER_NAME} at submission")
        if author_name is not None:
            check("developer_name_defaulted", developer_name == author_name,
                  f"interface.developerName {developer_name!r} must match "
                  f"author.name {author_name!r}, or the verified identity is used for both")

    category = interface.get("category")
    if category is not None:
        check("plugin_category_unknown", category in CATEGORIES,
              f"interface.category {category!r} must be one of: "
              f"{', '.join(sorted(CATEGORIES))}")

    capabilities = interface.get("capabilities")
    if capabilities is not None:
        if check("plugin_capabilities_wrong_type", isinstance(capabilities, list),
                 "interface.capabilities must be a list of strings"):
            check("plugin_capabilities_too_many", len(capabilities) <= MAX_CAPABILITIES,
                  f"interface.capabilities has {len(capabilities)} entries, "
                  f"limit {MAX_CAPABILITIES}")
            for entry in capabilities:
                if not check("plugin_capability_wrong_type", isinstance(entry, str),
                             f"capability {entry!r} must be a string"):
                    continue
                check("plugin_capability_empty", entry.strip() != "",
                      "capability entries must be non-empty")
                check("plugin_capability_too_long", len(entry) <= 120,
                      f"capability {entry!r} is {len(entry)} chars, limit 120")

    for field, code in (
        ("websiteURL", "website_url"),
        ("privacyPolicyURL", "privacy_policy_url"),
        ("termsOfServiceURL", "terms_of_service_url"),
        ("supportURL", "support_url"),
    ):
        check_https(field, code, interface.get(field))

    # Light surface behind brandColor, dark surface behind brandColorDark.
    check_color("brandColor", "brand_color",
                interface.get("brandColor"), "#FFFFFF", "white")
    check_color("brandColorDark", "brand_color_dark",
                interface.get("brandColorDark"), "#212121", "#212121")

    prompts = interface.get("defaultPrompt")
    if prompts is not None:
        if isinstance(prompts, str):
            prompts = [prompts]
        if check("plugin_default_prompt_wrong_type", isinstance(prompts, list),
                 "interface.defaultPrompt must be a string or a list of strings"):
            check("plugin_default_prompt_too_many", len(prompts) <= MAX_DEFAULT_PROMPTS,
                  f"interface.defaultPrompt has {len(prompts)} entries, "
                  f"maximum {MAX_DEFAULT_PROMPTS}")
            for prompt in prompts:
                if not check("plugin_default_prompt_entry_wrong_type",
                             isinstance(prompt, str), f"prompt {prompt!r} must be a string"):
                    continue
                check("plugin_default_prompt_empty", prompt.strip() != "",
                      "prompt entries must be non-empty")
                check("plugin_default_prompt_too_long", len(prompt) <= LIMIT_DEFAULT_PROMPT,
                      f"prompt is {len(prompt)} chars, limit {LIMIT_DEFAULT_PROMPT} "
                      f"at submission: {prompt[:60]!r}...")
                check("plugin_default_prompt_character_unsupported", "\n" not in prompt,
                      "prompt entries must be a single line")

    check_asset("logo", interface.get("logo"), required=True)
    check_asset("composerIcon", interface.get("composerIcon"), required=True)
    check_asset("logoDark", interface.get("logoDark"), required=False)

    screenshots = interface.get("screenshots")
    if screenshots is not None:
        if check("plugin_screenshots_wrong_type", isinstance(screenshots, list),
                 "interface.screenshots must be a list"):
            for idx, shot in enumerate(screenshots):
                check_asset(f"screenshots[{idx}]", shot, required=False)

    return report()


def report() -> int:
    print(f"\nRan {checked} check(s).")
    if problems:
        print(f"\n{len(problems)} manifest problem(s) found:\n")
        for line in problems:
            print(line)
        print("\nEach code above is OpenAI's published submission error. Fix the field,")
        print("or update this checker if the platform's documented rule has changed.")
        return 1
    print("All plugin manifest fields satisfy the published marketplace rules.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
