#!/usr/bin/env python3
"""Versioned research artifacts — append-only, open files you own (V2).

Store layout (under TRAILS):
    <name>/meta.json     — {schema, name, created_at, symbols, revisions:[{rev,at,file}]}
    <name>/r1.json       — full trail of revision 1
    <name>/r1.html       — its card page

Rules: a new run under an existing name appends rN+1 and never rewrites an
earlier revision; diffs are deterministic and field-level.
"""
import datetime as dt
import difflib, json, os

SCHEMA = "research-artifact/1"


def _root():
    return os.environ.get("VIBE_TRAILS_DIR") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "trails")


def slugify(name):
    keep = [c if (c.isalnum() or c in "-_") else "-" for c in name.strip().lower()]
    return "".join(keep).strip("-") or "artifact"


def save(name, trail):
    """Write trail as the next revision of the named artifact → (rev, base)."""
    root = _root()
    d = os.path.join(root, slugify(name))
    os.makedirs(d, exist_ok=True)
    mpath = os.path.join(d, "meta.json")
    meta = {"schema": SCHEMA, "name": slugify(name), "created_at": None,
            "symbols": sorted(trail.get("datasets", {})), "revisions": []}
    if os.path.exists(mpath):
        meta = json.load(open(mpath))
    rev = (meta["revisions"][-1]["rev"] + 1) if meta["revisions"] else 1
    now = dt.datetime.now().isoformat(timespec="seconds")
    if rev == 1:
        meta["created_at"] = now
    base = os.path.join(d, f"r{rev}")
    trail = dict(trail)
    html = trail.pop("_html", None)
    trail["artifact"] = {"name": meta["name"], "rev": rev, "saved_at": now}
    json.dump(trail, open(base + ".json", "w"), ensure_ascii=False, indent=1, default=str)
    if html:
        open(base + ".html", "w").write(html)
    meta["revisions"].append({"rev": rev, "at": now, "file": f"r{rev}.json",
                              "question": trail.get("question", "")})
    json.dump(meta, open(mpath, "w"), ensure_ascii=False, indent=1)
    return rev, base


def list_artifacts():
    root = _root()
    out = []
    if not os.path.isdir(root):
        return out
    for n in sorted(os.listdir(root)):
        mp = os.path.join(root, n, "meta.json")
        if os.path.exists(mp):
            m = json.load(open(mp))
            out.append({"name": n, "revisions": len(m["revisions"]),
                        "last_at": m["revisions"][-1]["at"],
                        "question": m["revisions"][-1].get("question", "")})
    return out


def load(name, rev=None):
    """→ (meta, trail) of the named artifact, latest or given revision."""
    d = os.path.join(_root(), slugify(name))
    meta = json.load(open(os.path.join(d, "meta.json")))
    r = rev if rev is not None else meta["revisions"][-1]["rev"]
    trail = json.load(open(os.path.join(d, f"r{r}.json")))
    return meta, trail


def _field(v):
    return v if isinstance(v, dict) else {"value": v}


def _fmt(v, spec=None):
    fv = _field(v)
    if "unavailable" in fv:
        return "unavailable(%s)" % fv["unavailable"]
    x = fv["value"]
    if spec:
        try:
            return spec.format(x)
        except (ValueError, TypeError):
            return str(x)
    if isinstance(x, bool):
        return str(x)
    if isinstance(x, float):
        return f"{x:+.4g}"
    return str(x)


def diff_trails(a, b):
    """Deterministic markdown diff between two trails (revisions of one artifact)."""
    lines = []
    if a.get("question") != b.get("question"):
        lines.append(f"- question changed:\n  - r1: {a.get('question')}\n  - r2: {b.get('question')}")
    syms = sorted(set(a.get("stats", {})) | set(b.get("stats", {})))
    for s in syms:
        sa, sb = a.get("stats", {}).get(s), b.get("stats", {}).get(s)
        if sa is None or sb is None:
            lines.append(f"- {s}: {'removed' if sb is None else 'added'} in r2")
            continue
        for k in sa:
            if k == "label":
                continue
            va, vb = _field(sa[k]), _field(sb[k])
            if va == vb:
                continue
            if "unavailable" in va and "value" in vb:
                lines.append(f"- {s}.{k}: became available {_fmt(sb[k])} (was unavailable: {va['unavailable']})")
            elif "value" in va and "unavailable" in vb:
                lines.append(f"- {s}.{k}: became UNAVAILABLE ({vb['unavailable']}); was {_fmt(sa[k])}")
            elif "value" in va and "value" in vb:
                try:
                    d = float(vb["value"]) - float(va["value"])
                    lines.append(f"- {s}.{k}: {_fmt(sa[k])} → {_fmt(sb[k])} (Δ {d:+.4g})")
                except (TypeError, ValueError):
                    lines.append(f"- {s}.{k}: {_fmt(sa[k])} → {_fmt(sb[k])}")
        ba, bb = a.get("backtests", {}).get(s), b.get("backtests", {}).get(s)
        if ba and bb:
            for k in ("trades", "sum_strategy"):
                if ba.get(k) != bb.get(k):
                    lines.append(f"- {s}.backtest.{k}: {_fmt(ba[k], '{}')} → {_fmt(bb[k], '{}')}")
    da, db = a.get("datasets", {}), b.get("datasets", {})
    for s in sorted(set(da) | set(db)):
        if s in da and s in db and da[s].get("date_range") != db[s].get("date_range"):
            lines.append(f"- {s}.data.range: {da[s].get('date_range')} → {db[s].get('date_range')}")
    fa, fb = a.get("findings", ""), b.get("findings", "")
    if fa != fb:
        ratio = difflib.SequenceMatcher(None, fa, fb).ratio()
        lines.append(f"- findings rewritten (similarity {ratio:.0%}); r2 findings replace r1 — both kept")
    return "\n".join(lines) or "no material changes between revisions"


def export_markdown(meta, trail):
    """One self-contained markdown document for a revision."""
    art = trail.get("artifact", {})
    L = [f"# Research artifact: {meta['name']} · revision r{art.get('rev', '?')}",
         f"- saved: {art.get('saved_at', meta.get('created_at'))}",
         f"- question: {trail.get('question')}",
         f"- symbols: {', '.join(trail.get('datasets', {})) or ', '.join(meta.get('symbols', []))}"]
    for s, m in trail.get("datasets", {}).items():
        L.append(f"- data[{s}]: {m.get('source')} · {m.get('adjustment')} · "
                 f"{m.get('date_range', ['?'])[0]} → {m.get('date_range', ['?'])[-1]} · "
                 f"{m.get('bars')}/{m.get('requested_bars')} bars")
    L.append("\n## plan\n" + str(trail.get("plan", {}).get("plan", "")))
    L.append("\n## stats")
    for s, st in trail.get("stats", {}).items():
        L.append(f"- **{s}**: " + " · ".join(f"{k}={_fmt(v)}" for k, v in st.items() if k != "label"))
    L.append("\n## backtests")
    for s, bt in trail.get("backtests", {}).items():
        L.append(f"- **{s}**: trades={bt.get('trades')} · sum_strategy={_fmt(bt.get('sum_strategy'), '{:+.2%}')} "
                 f"· win_rate={_fmt(bt.get('win_rate'), '{:.0%}')} · note: {bt.get('oos_note')}")
    L.append("\n## findings\n" + str(trail.get("findings", "")))
    L.append(f"\n---\n*schema {trail.get('schema')} · artifact {SCHEMA} · not investment advice*")
    return "\n".join(L)
