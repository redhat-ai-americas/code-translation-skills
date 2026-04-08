#!/usr/bin/env python3
"""
Migration Run Status Viewer

Generates a single self-contained HTML page that shows the live status of a
migration run: phase progress, skill execution timeline, recent log entries,
gate status, and key metrics — all in one place.

This is the "open this in a browser to see what's happening" tool.

Usage:
    python generate_run_status.py <analysis_dir> \
        [--output run-status.html] \
        [--skills-root <path>] \
        [--project-name "My Project"]

Where <analysis_dir> is the migration-analysis/ directory.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[3] / 'scripts' / 'lib'))
from migration_logger import setup_logging, log_execution
logger = setup_logging(__name__)


# ── Phase metadata ─────────────────────────────────────────────────────────

PHASES = [
    {"num": 0, "name": "Discovery",     "color": "#4a5568", "icon": "🔍"},
    {"num": 1, "name": "Foundation",     "color": "#4cc9f0", "icon": "🏗"},
    {"num": 2, "name": "Mechanical",     "color": "#4361ee", "icon": "⚙"},
    {"num": 3, "name": "Semantic",       "color": "#3a0ca3", "icon": "🧠"},
    {"num": 4, "name": "Verification",   "color": "#7209b7", "icon": "✓"},
    {"num": 5, "name": "Cutover",        "color": "#f72585", "icon": "🚀"},
]

# Full skill manifest for coverage calculations
SKILL_MANIFEST: Dict[str, List[str]] = {
    "behavioral-contract-extractor": ["extract_contracts.py"],
    "haiku-pattern-fixer": ["apply_fix.py"],
    "migration-dashboard": ["generate_dashboard.py", "generate_skill_usage_dashboard.py", "generate_run_status.py"],
    "modernization-advisor": ["check_modernization.py"],
    "py2to3-automated-converter": ["convert.py", "generate_conversion_report.py"],
    "py2to3-behavioral-diff-generator": ["generate_diffs.py", "generate_diff_report.py"],
    "py2to3-build-system-updater": ["update_build.py", "generate_build_report.py"],
    "py2to3-bytes-string-fixer": ["fix_boundaries.py", "generate_boundary_report.py"],
    "py2to3-c-extension-flagger": ["flag_extensions.py", "generate_extension_report.py"],
    "py2to3-canary-deployment-planner": ["plan_canary.py", "generate_canary_report.py"],
    "py2to3-ci-dual-interpreter": ["configure_ci.py", "generate_ci_report.py"],
    "py2to3-codebase-analyzer": ["analyze.py", "build_dep_graph.py", "generate_report.py"],
    "py2to3-compatibility-shim-remover": ["remove_shims.py", "generate_shim_report.py"],
    "py2to3-completeness-checker": ["check_completeness.py", "generate_completeness_report.py"],
    "py2to3-conversion-unit-planner": ["plan_conversion.py", "generate_plan_report.py"],
    "py2to3-custom-lint-rules": ["generate_lint_rules.py", "generate_lint_rules_report.py"],
    "py2to3-data-format-analyzer": ["analyze_data_layer.py", "generate_data_report.py"],
    "py2to3-dead-code-detector": ["detect_dead_code.py", "generate_dead_code_report.py"],
    "py2to3-dynamic-pattern-resolver": ["resolve_patterns.py", "generate_pattern_report.py"],
    "py2to3-encoding-stress-tester": ["stress_test.py", "generate_stress_report.py"],
    "py2to3-future-imports-injector": ["inject_futures.py"],
    "py2to3-gate-checker": ["check_gate.py", "generate_gate_report.py"],
    "py2to3-library-replacement": ["advise_replacements.py", "generate_replacement_report.py"],
    "py2to3-lint-baseline-generator": ["generate_baseline.py", "generate_lint_report.py"],
    "py2to3-migration-state-tracker": ["init_state.py", "update_state.py", "query_state.py"],
    "py2to3-performance-benchmarker": ["benchmark.py", "generate_perf_report.py"],
    "py2to3-project-initializer": ["init_migration_project.py", "quick_size_scan.py"],
    "py2to3-rollback-plan-generator": ["generate_rollback.py", "generate_rollback_report.py"],
    "py2to3-security-scanner": ["security_scan.py"],
    "py2to3-serialization-detector": ["detect_serialization.py", "generate_serialization_report.py"],
    "py2to3-test-scaffold-generator": ["generate_tests.py"],
    "py2to3-type-annotation-adder": ["add_annotations.py", "generate_annotation_report.py"],
    "translation-verifier": ["verify_translation.py"],
    "universal-code-graph": [
        "analyze_universal.py", "language_detect.py", "ts_parser.py",
        "universal_extractor.py", "graph_builder.py",
    ],
    "work-item-generator": ["generate_work_items.py"],
}


# ── Data loaders ───────────────────────────────────────────────────────────

def load_json_safe(path: Path) -> Optional[Dict]:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def load_state(analysis_dir: Path) -> Dict:
    for candidate in [
        analysis_dir / "state" / "migration-state.json",
        analysis_dir / "migration-state.json",
    ]:
        data = load_json_safe(candidate)
        if data:
            return data
    return {}


def load_gate_report(analysis_dir: Path) -> Optional[Dict]:
    for phase_num in range(5, -1, -1):
        phase_dir = analysis_dir / f"phase-{phase_num}-{'discovery foundation mechanical semantic verification cutover'.split()[phase_num]}"
        candidate = phase_dir / "gate-check-report.json"
        data = load_json_safe(candidate)
        if data:
            return data
    return load_json_safe(analysis_dir / "gate-check-report.json")


def load_sizing(analysis_dir: Path) -> Optional[Dict]:
    for candidate in [
        analysis_dir / "phase-0-discovery" / "sizing-report.json",
        analysis_dir / "sizing-report.json",
    ]:
        data = load_json_safe(candidate)
        if data:
            return data
    return None


def load_graph_snapshots(analysis_dir: Path, state: Dict) -> Dict[str, Dict]:
    """Load dependency-graph.json from each phase directory and adapt for visualization."""
    PHASE_DIRS = [
        ("Phase 0 — Discovery", "phase-0-discovery"),
        ("Phase 1 — Foundation", "phase-1-foundation"),
        ("Phase 2 — Mechanical", "phase-2-mechanical"),
        ("Phase 3 — Semantic", "phase-3-semantic"),
        ("Phase 4 — Verification", "phase-4-verification"),
        ("Phase 5 — Cutover", "phase-5-cutover"),
    ]
    snapshots = {}
    modules_state = state.get("modules", {})
    for label, dirname in PHASE_DIRS:
        graph_path = analysis_dir / dirname / "dependency-graph.json"
        raw = load_json_safe(graph_path)
        if raw and raw.get("nodes"):
            snapshots[label] = adapt_graph_for_viz(raw, modules_state)
    return snapshots


def adapt_graph_for_viz(graph_json: Dict, modules_state: Dict) -> Dict:
    """Convert graph_builder output to visualization format."""
    metrics = graph_json.get("metrics", {})
    fan_in_map = metrics.get("fan_in", {})
    fan_out_map = metrics.get("fan_out", {})

    nodes = []
    for n in graph_json.get("nodes", []):
        nid = n.get("id", "")
        parts = nid.rsplit("/", 1)
        package = parts[0].replace("/", ".") if len(parts) > 1 else "root"
        mod = modules_state.get(nid, {})
        fi = fan_in_map.get(nid, 0)
        fo = fan_out_map.get(nid, 0)
        nodes.append({
            "id": nid,
            "package": package,
            "lines": n.get("loc", 10),
            "language": n.get("language", "unknown"),
            "fan_in": fi,
            "fan_out": fo,
            "migration_status": mod.get("status", "not_started"),
            "risk_score": mod.get("risk_score", 0),
            "phase": mod.get("phase", 0),
        })

    edges = [{"from": e["source"], "to": e["target"], "type": e.get("type", "import")}
             for e in graph_json.get("edges", [])]

    clusters = []
    for c in metrics.get("clusters", []):
        cnodes = c.get("nodes", [])
        if cnodes:
            pkg = cnodes[0].rsplit("/", 1)[0].replace("/", ".") if "/" in cnodes[0] else "root"
            clusters.append({"name": pkg, "modules": cnodes})

    return {
        "nodes": nodes,
        "edges": edges,
        "clusters": clusters,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "packages": len(set(n["package"] for n in nodes)),
            "languages": list(set(n["language"] for n in nodes)),
        },
    }


# ── Log parsing ────────────────────────────────────────────────────────────

_AUDIT_START = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s*\|\s*(\S+)\s*\|\s*INFO\s*\|\s*START\s*\|"
)
_AUDIT_END = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s*\|\s*(\S+)\s*\|\s*INFO\s*\|\s*END\s*\|\s*exit=(\d+)\s+duration=([\d.]+)s"
)
_AUDIT_ANY = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s*\|\s*(\S+)\s*\|\s*(\S+)\s*\|\s*(.*)"
)


def parse_logs(analysis_dir: Path) -> Tuple[List[Dict], List[Dict]]:
    """Parse both log sources. Returns (execution_records, raw_log_lines)."""
    executions = []
    raw_lines = []
    pending_starts: Dict[str, Dict] = {}

    audit_path = analysis_dir / "logs" / "migration-audit.log"
    if audit_path.exists():
        try:
            with open(audit_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip()
                    if not line:
                        continue

                    # Capture raw line for log viewer
                    m_any = _AUDIT_ANY.match(line)
                    if m_any:
                        ts, script, level, msg = m_any.groups()
                        raw_lines.append({
                            "ts": ts, "script": script,
                            "level": level.strip(), "msg": msg.strip(),
                        })

                    # Parse START/END pairs into execution records
                    m_start = _AUDIT_START.match(line)
                    if m_start:
                        ts, script = m_start.group(1), m_start.group(2)
                        pending_starts[script] = {"ts": ts, "script": script}
                        continue

                    m_end = _AUDIT_END.match(line)
                    if m_end:
                        ts, script, exit_code, duration = m_end.groups()
                        start = pending_starts.pop(script, None)
                        executions.append({
                            "script": f"{script}.py" if not script.endswith(".py") else script,
                            "start_ts": start["ts"] if start else ts,
                            "end_ts": ts,
                            "exit_code": int(exit_code),
                            "duration_s": float(duration),
                        })
        except (OSError, UnicodeDecodeError):
            pass

    # Enrich from JSONL (has skill names, stdout/stderr sizes)
    jsonl_path = analysis_dir / "logs" / "skill-invocations.jsonl"
    jsonl_by_script: Dict[str, List[Dict]] = {}
    if jsonl_path.exists():
        try:
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        s = entry.get("script", "")
                        jsonl_by_script.setdefault(s, []).append(entry)
                    except json.JSONDecodeError:
                        pass
        except (OSError, UnicodeDecodeError):
            pass

    # Resolve skill names
    script_to_skill = {}
    for skill, scripts in SKILL_MANIFEST.items():
        for s in scripts:
            script_to_skill[s] = skill

    for rec in executions:
        rec["skill"] = script_to_skill.get(rec["script"], "unknown")
        # Check if JSONL has richer data
        jentries = jsonl_by_script.get(rec["script"], [])
        if jentries:
            # Use first matching entry
            j = jentries[0]
            if not rec.get("skill") or rec["skill"] == "unknown":
                rec["skill"] = j.get("skill", rec.get("skill", ""))

    return executions, raw_lines


# ── Analysis ───────────────────────────────────────────────────────────────

def compute_phase_progress(state: Dict) -> List[Dict]:
    """Determine which phases have been reached."""
    current_phase = state.get("phase", 0)
    if isinstance(current_phase, str):
        try:
            current_phase = int(current_phase)
        except ValueError:
            current_phase = 0

    results = []
    for p in PHASES:
        if p["num"] < current_phase:
            status = "complete"
        elif p["num"] == current_phase:
            status = "active"
        else:
            status = "pending"
        results.append({**p, "status": status})
    return results


def compute_skill_summary(executions: List[Dict]) -> Dict:
    """Summarize skill execution."""
    executed_scripts = set(r["script"] for r in executions)
    all_scripts = set(s for scripts in SKILL_MANIFEST.values() for s in scripts)

    skills_touched = set()
    for rec in executions:
        if rec["skill"] != "unknown":
            skills_touched.add(rec["skill"])

    failures = [r for r in executions if r["exit_code"] != 0]
    total_duration = sum(r.get("duration_s", 0) for r in executions)

    return {
        "scripts_run": len(executed_scripts & all_scripts),
        "scripts_total": len(all_scripts),
        "skills_used": len(skills_touched),
        "skills_total": len(SKILL_MANIFEST),
        "invocations": len(executions),
        "failures": len(failures),
        "total_duration_s": round(total_duration, 1),
    }


def build_timeline(executions: List[Dict]) -> List[Dict]:
    """Build a timeline of executions for visualization."""
    timeline = []
    for rec in executions:
        timeline.append({
            "script": rec["script"],
            "skill": rec.get("skill", ""),
            "ts": rec.get("start_ts", ""),
            "duration": rec.get("duration_s", 0),
            "ok": rec.get("exit_code", 0) == 0,
        })
    return timeline


# ── HTML ───────────────────────────────────────────────────────────────────

def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def fmt_duration(s: float) -> str:
    if s >= 3600:
        return f"{int(s//3600)}h {int((s%3600)//60)}m"
    if s >= 60:
        return f"{int(s//60)}m {int(s%60)}s"
    return f"{s:.1f}s"


def generate_html(
    project_name: str,
    state: Dict,
    phase_progress: List[Dict],
    skill_summary: Dict,
    executions: List[Dict],
    raw_lines: List[Dict],
    sizing: Optional[Dict],
    gate_report: Optional[Dict],
    graph_snapshots: Optional[Dict] = None,
) -> str:

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_phase = state.get("phase", 0)
    workflow = state.get("workflow", sizing.get("sizing", {}).get("workflow", "—") if sizing else "—")
    tier = "—"
    if sizing:
        s = sizing.get("sizing", {})
        tier = s.get("effective_tier", s.get("base_tier", "—"))

    initialized = state.get("initialized", "—")
    ss = skill_summary

    # Build phase stepper HTML
    stepper_html = ""
    for p in phase_progress:
        cls = f"step-{p['status']}"
        stepper_html += f"""<div class="step {cls}" style="--phase-color:{p['color']}">
  <div class="step-num">{p['num']}</div>
  <div class="step-name">{p['name']}</div>
</div>"""

    # Build execution timeline items
    timeline_items = ""
    for rec in reversed(executions[-50:]):  # last 50
        ok_cls = "tl-ok" if rec.get("exit_code", 0) == 0 else "tl-fail"
        timeline_items += f"""<div class="tl-item {ok_cls}">
  <span class="tl-time">{esc(rec.get('start_ts','')[:19])}</span>
  <span class="tl-script">{esc(rec['script'])}</span>
  <span class="tl-skill">{esc(rec.get('skill',''))}</span>
  <span class="tl-dur">{rec.get('duration_s',0):.1f}s</span>
  <span class="tl-exit">{rec.get('exit_code',0)}</span>
</div>"""

    # Build log viewer lines
    log_html = ""
    for entry in raw_lines[-200:]:  # last 200 lines
        lvl_cls = {
            "ERROR": "log-error", "WARNING": "log-warn",
            "WARN": "log-warn", "INFO": "log-info",
        }.get(entry["level"], "log-debug")
        log_html += (
            f'<div class="log-line {lvl_cls}">'
            f'<span class="log-ts">{esc(entry["ts"][:19])}</span>'
            f'<span class="log-src">{esc(entry["script"])}</span>'
            f'<span class="log-lvl">{esc(entry["level"][:5])}</span>'
            f'<span class="log-msg">{esc(entry["msg"])}</span>'
            f'</div>'
        )

    # Gate status summary
    gate_html = ""
    if gate_report and "gates" in gate_report:
        for phase_key, gdata in gate_report["gates"].items():
            status = gdata.get("status", "unknown")
            badge_cls = {"pass": "g-pass", "fail": "g-fail", "warning": "g-warn"}.get(status, "g-unknown")
            criteria = gdata.get("criteria", [])
            crit_count = len(criteria)
            passed = sum(1 for c in criteria if isinstance(c, dict) and c.get("met", False))
            gate_html += f"""<div class="gate-item {badge_cls}">
  <div class="gate-phase">{esc(phase_key)}</div>
  <div class="gate-status">{status.upper()}</div>
  <div class="gate-detail">{passed}/{crit_count} criteria met</div>
</div>"""

    # Build graph phase buttons and data blocks
    graph_phase_buttons = ""
    graph_data_blocks = ""
    if graph_snapshots:
        for i, (label, _data) in enumerate(graph_snapshots.items()):
            active_cls = "active" if i == 0 else ""
            graph_phase_buttons += f'<button class="{active_cls}" onclick="switchGraph(this, {i})">{esc(label)}</button>'
            graph_data_blocks += f'<script type="application/json" class="graph-snapshot" data-idx="{i}">{json.dumps(_data, default=str)}</script>'

    # Build the full HTML
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Run Status — {esc(project_name)}</title>
<style>
:root {{
  --bg: #0f172a; --bg2: #1e293b; --bg3: #334155;
  --fg: #f1f5f9; --fg2: #94a3b8; --fg3: #64748b;
  --border: #475569;
  --green: #22c55e; --red: #dc2626; --orange: #f97316;
  --yellow: #eab308; --blue: #3b82f6; --purple: #a855f7; --cyan: #06b6d4;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--bg); color: var(--fg); line-height: 1.5;
}}

/* ── Top bar ── */
.topbar {{
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-bottom: 1px solid var(--border);
  padding: 20px 32px;
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 12px;
}}
.topbar h1 {{ font-size: 1.4rem; }}
.topbar .meta {{ color: var(--fg2); font-size: 0.85rem; }}
.topbar .meta span {{ margin-left: 16px; }}

/* ── Tab navigation ── */
.tabs {{
  display: flex; background: var(--bg2);
  border-bottom: 1px solid var(--border);
  padding: 0 24px;
}}
.tab {{
  padding: 12px 20px; cursor: pointer;
  color: var(--fg3); font-size: 0.9rem; font-weight: 500;
  border-bottom: 2px solid transparent;
  transition: all 0.15s;
}}
.tab:hover {{ color: var(--fg2); }}
.tab.active {{ color: var(--fg); border-bottom-color: var(--blue); }}

/* ── Content area ── */
.content {{ padding: 24px 32px; max-width: 1400px; margin: 0 auto; }}
.panel {{ display: none; }}
.panel.active {{ display: block; }}

/* ── Cards ── */
.cards {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 14px; margin-bottom: 28px;
}}
.card {{
  background: var(--bg2); border: 1px solid var(--border);
  border-radius: 10px; padding: 16px 18px; text-align: center;
}}
.card .val {{ font-size: 1.8rem; font-weight: 700; line-height: 1.2; }}
.card .lbl {{ color: var(--fg2); font-size: 0.82rem; margin-top: 2px; }}
.card .sub {{ color: var(--fg3); font-size: 0.75rem; }}

/* ── Phase stepper ── */
.stepper {{
  display: flex; gap: 0; margin-bottom: 28px;
  background: var(--bg2); border: 1px solid var(--border);
  border-radius: 10px; overflow: hidden;
}}
.step {{
  flex: 1; padding: 16px 12px; text-align: center;
  border-right: 1px solid var(--border);
  transition: all 0.2s;
}}
.step:last-child {{ border-right: none; }}
.step-num {{
  width: 32px; height: 32px; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.9rem;
  margin-bottom: 4px;
}}
.step-name {{ font-size: 0.8rem; color: var(--fg2); }}
.step-complete {{ background: rgba(34,197,94,0.08); }}
.step-complete .step-num {{ background: var(--green); color: #000; }}
.step-complete .step-name {{ color: var(--green); }}
.step-active {{ background: rgba(59,130,246,0.12); }}
.step-active .step-num {{ background: var(--blue); color: #fff; animation: pulse 2s infinite; }}
.step-active .step-name {{ color: var(--blue); font-weight: 600; }}
.step-pending .step-num {{ background: var(--bg3); color: var(--fg3); }}
@keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.6; }} }}

/* ── Section box ── */
.section {{
  background: var(--bg2); border: 1px solid var(--border);
  border-radius: 10px; padding: 20px 22px; margin-bottom: 20px;
}}
.section h2 {{
  font-size: 1.05rem; margin-bottom: 14px;
  padding-bottom: 8px; border-bottom: 1px solid var(--border);
}}

/* ── Timeline ── */
.tl-item {{
  display: grid; grid-template-columns: 140px 1fr 1fr 60px 40px;
  padding: 6px 10px; font-size: 0.84rem;
  border-left: 3px solid var(--green);
  margin-bottom: 2px; background: rgba(255,255,255,0.02);
  border-radius: 0 4px 4px 0;
}}
.tl-fail {{ border-left-color: var(--red); background: rgba(220,38,38,0.05); }}
.tl-time {{ color: var(--fg3); font-family: monospace; font-size: 0.8rem; }}
.tl-script {{ font-weight: 500; }}
.tl-skill {{ color: var(--fg2); }}
.tl-dur {{ color: var(--cyan); text-align: right; }}
.tl-exit {{ text-align: center; }}
.tl-fail .tl-exit {{ color: var(--red); font-weight: 700; }}

/* ── Log viewer ── */
.log-viewer {{
  max-height: 500px; overflow-y: auto;
  font-family: "SF Mono", "Fira Code", "Consolas", monospace;
  font-size: 0.78rem; line-height: 1.7;
  background: #0c1222; border-radius: 8px; padding: 12px;
}}
.log-line {{
  display: grid; grid-template-columns: 140px 160px 50px 1fr;
  padding: 1px 0;
  border-bottom: 1px solid rgba(255,255,255,0.03);
}}
.log-ts {{ color: var(--fg3); }}
.log-src {{ color: var(--cyan); }}
.log-lvl {{ font-weight: 600; }}
.log-msg {{ color: var(--fg2); }}
.log-error .log-lvl {{ color: var(--red); }}
.log-error .log-msg {{ color: #fca5a5; }}
.log-warn .log-lvl {{ color: var(--orange); }}
.log-warn .log-msg {{ color: #fed7aa; }}
.log-info .log-lvl {{ color: var(--fg3); }}

.log-filter {{
  display: flex; gap: 8px; margin-bottom: 10px;
}}
.log-filter input {{
  flex: 1; padding: 8px 12px; background: var(--bg3);
  border: 1px solid var(--border); border-radius: 6px;
  color: var(--fg); font-size: 0.85rem; font-family: monospace;
}}
.log-filter input::placeholder {{ color: var(--fg3); }}
.log-filter button {{
  padding: 8px 14px; background: var(--bg3);
  border: 1px solid var(--border); border-radius: 6px;
  color: var(--fg2); cursor: pointer; font-size: 0.82rem;
}}
.log-filter button:hover {{ color: var(--fg); border-color: var(--fg2); }}
.log-filter button.active {{ background: var(--blue); color: white; border-color: var(--blue); }}

/* ── Gates ── */
.gates {{ display: flex; gap: 10px; flex-wrap: wrap; }}
.gate-item {{
  padding: 12px 18px; border-radius: 8px;
  border: 1px solid var(--border); min-width: 140px; text-align: center;
}}
.gate-phase {{ font-weight: 600; font-size: 0.9rem; }}
.gate-status {{ font-size: 0.82rem; font-weight: 700; margin: 4px 0; }}
.gate-detail {{ font-size: 0.75rem; color: var(--fg3); }}
.g-pass {{ background: rgba(34,197,94,0.08); }}
.g-pass .gate-status {{ color: var(--green); }}
.g-fail {{ background: rgba(220,38,38,0.08); }}
.g-fail .gate-status {{ color: var(--red); }}
.g-warn {{ background: rgba(234,179,8,0.08); }}
.g-warn .gate-status {{ color: var(--yellow); }}
.g-unknown {{ background: rgba(148,163,184,0.05); }}

/* ── Graph tab ── */
.graph-controls {{
  display: flex; gap: 10px; margin-bottom: 14px; align-items: center; flex-wrap: wrap;
}}
.graph-controls button {{
  padding: 8px 16px; background: var(--bg3);
  border: 1px solid var(--border); border-radius: 6px;
  color: var(--fg2); cursor: pointer; font-size: 0.82rem;
  transition: all 0.15s;
}}
.graph-controls button:hover {{ color: var(--fg); border-color: var(--fg2); }}
.graph-controls button.active {{ background: var(--blue); color: white; border-color: var(--blue); }}
.graph-controls .spacer {{ flex: 1; }}
.graph-controls .info {{ color: var(--fg3); font-size: 0.78rem; }}
.graph-legend {{
  display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 14px;
  padding: 10px 14px; background: var(--bg2); border: 1px solid var(--border); border-radius: 8px;
}}
.gl-item {{ display: flex; align-items: center; gap: 6px; font-size: 0.78rem; color: var(--fg2); }}
.gl-swatch {{ width: 12px; height: 12px; border-radius: 3px; }}
.graph-stats {{
  display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 14px;
  font-size: 0.82rem; color: var(--fg2);
}}
.graph-stats span {{ color: var(--fg); font-weight: 600; }}
.graph-canvas-wrap {{
  position: relative; border: 1px solid var(--border);
  border-radius: 10px; overflow: hidden; background: #0c1222;
}}
.graph-canvas-wrap canvas {{ display: block; width: 100%; }}
.graph-tooltip {{
  position: absolute; display: none; background: rgba(15,23,42,0.96);
  border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px;
  font-size: 0.8rem; z-index: 20; pointer-events: none;
  max-width: 320px; box-shadow: 0 8px 24px rgba(0,0,0,0.5);
}}
.graph-tooltip h4 {{ color: var(--blue); margin-bottom: 6px; }}
.graph-tooltip .meta {{ color: var(--fg2); line-height: 1.6; }}
.graph-tooltip .meta span {{ color: var(--fg); }}
.no-graph {{ text-align: center; padding: 80px 20px; color: var(--fg3); }}
.no-graph h3 {{ font-size: 1.1rem; margin-bottom: 8px; color: var(--fg2); }}

/* ── Responsive ── */
@media (max-width: 768px) {{
  .topbar {{ padding: 16px; }}
  .content {{ padding: 16px; }}
  .tl-item {{ grid-template-columns: 1fr; gap: 2px; }}
  .log-line {{ grid-template-columns: 1fr; }}
  .cards {{ grid-template-columns: repeat(2, 1fr); }}
}}
</style>
</head>
<body>

<!-- Top Bar -->
<div class="topbar">
  <div>
    <h1>{esc(project_name)}</h1>
    <div class="meta">
      Run Status
      <span>Generated: {now}</span>
    </div>
  </div>
  <div style="text-align:right">
    <div class="meta">
      <span>Workflow: <strong>{esc(str(workflow))}</strong></span>
      <span>Tier: <strong>{esc(str(tier))}</strong></span>
      <span>Started: <strong>{esc(str(initialized)[:19])}</strong></span>
    </div>
  </div>
</div>

<!-- Tabs -->
<div class="tabs">
  <div class="tab active" onclick="showTab('overview')">Overview</div>
  <div class="tab" onclick="showTab('timeline')">Timeline</div>
  <div class="tab" onclick="showTab('logs')">Logs</div>
  <div class="tab" onclick="showTab('graph')">Graph</div>
</div>

<div class="content">

<!-- ═══════ OVERVIEW TAB ═══════ -->
<div class="panel active" id="panel-overview">

  <!-- Phase Stepper -->
  <div class="stepper">
    {stepper_html}
  </div>

  <!-- Summary Cards -->
  <div class="cards">
    <div class="card">
      <div class="val" style="color:var(--blue)">{ss['scripts_run']}<span style="font-size:1rem;color:var(--fg3)">/{ss['scripts_total']}</span></div>
      <div class="lbl">Scripts Run</div>
      <div class="sub">{round(ss['scripts_run']/ss['scripts_total']*100) if ss['scripts_total'] else 0}% coverage</div>
    </div>
    <div class="card">
      <div class="val" style="color:var(--green)">{ss['skills_used']}<span style="font-size:1rem;color:var(--fg3)">/{ss['skills_total']}</span></div>
      <div class="lbl">Skills Used</div>
      <div class="sub">{round(ss['skills_used']/ss['skills_total']*100) if ss['skills_total'] else 0}% coverage</div>
    </div>
    <div class="card">
      <div class="val" style="color:{'var(--red)' if ss['failures'] else 'var(--green)'}">{ss['failures']}</div>
      <div class="lbl">Failures</div>
      <div class="sub">exit &ne; 0</div>
    </div>
    <div class="card">
      <div class="val" style="color:var(--purple)">{ss['invocations']}</div>
      <div class="lbl">Invocations</div>
      <div class="sub">{fmt_duration(ss['total_duration_s'])}</div>
    </div>
    <div class="card">
      <div class="val" style="color:var(--cyan)">{current_phase}</div>
      <div class="lbl">Current Phase</div>
      <div class="sub">{PHASES[min(current_phase,5)]['name']}</div>
    </div>
  </div>

  <!-- Gates -->
  {"" if not gate_html else f'''<div class="section">
    <h2>Gate Status</h2>
    <div class="gates">{gate_html}</div>
  </div>'''}

  <!-- Recent Executions -->
  <div class="section">
    <h2>Recent Script Executions</h2>
    <div style="font-size:0.78rem;color:var(--fg3);margin-bottom:8px;display:grid;grid-template-columns:140px 1fr 1fr 60px 40px;padding:0 10px">
      <span>Time</span><span>Script</span><span>Skill</span><span style="text-align:right">Duration</span><span style="text-align:center">Exit</span>
    </div>
    {timeline_items if timeline_items else '<div style="color:var(--fg3);padding:20px;text-align:center">No executions recorded yet</div>'}
  </div>
</div>

<!-- ═══════ TIMELINE TAB ═══════ -->
<div class="panel" id="panel-timeline">
  <div class="section">
    <h2>Execution Timeline</h2>
    <div class="chart-box" style="position:relative;height:400px;margin-top:12px">
      <canvas id="tlCanvas"></canvas>
    </div>
  </div>

  <div class="section">
    <h2>Duration by Skill</h2>
    <div class="chart-box" style="position:relative;height:360px;margin-top:12px">
      <canvas id="durCanvas"></canvas>
    </div>
  </div>
</div>

<!-- ═══════ LOGS TAB ═══════ -->
<div class="panel" id="panel-logs">
  <div class="section">
    <h2>Audit Log</h2>
    <div class="log-filter">
      <input type="text" id="logSearch" placeholder="Filter logs (regex supported)..." oninput="filterLogs()">
      <button class="active" onclick="toggleLevel(this,'all')">All</button>
      <button onclick="toggleLevel(this,'ERROR')">Errors</button>
      <button onclick="toggleLevel(this,'WARN')">Warnings</button>
    </div>
    <div class="log-viewer" id="logViewer">
      {log_html if log_html else '<div style="color:var(--fg3);padding:20px;text-align:center">No log entries found</div>'}
    </div>
  </div>
</div>

<!-- ═══════ GRAPH TAB ═══════ -->
<div class="panel" id="panel-graph">
{{"" if not graph_snapshots else f'''
  <div class="graph-controls">
    {graph_phase_buttons}
    <div class="spacer"></div>
    <div class="info">Drag nodes · Scroll to zoom · Click to highlight connections</div>
  </div>

  <div class="graph-legend" id="graphLegend"></div>

  <div class="graph-stats" id="graphStats"></div>

  <div class="graph-canvas-wrap" style="height:600px">
    <canvas id="graphCanvas"></canvas>
    <div class="graph-tooltip" id="graphTooltip"></div>
  </div>
'''}}
{{"" if graph_snapshots else '<div class="no-graph"><h3>No Graph Data Available</h3><p>Graph snapshots are generated during Phase 0 (Discovery), Phase 2 (Mechanical), and Phase 5 (Cutover).<br>Run the migration to generate dependency graph visualizations.</p></div>'}}
</div>

</div><!-- content -->

<!-- Graph snapshots -->
{graph_data_blocks}

<!-- Embedded data for charts -->
<script type="application/json" id="execData">{json.dumps(build_timeline(executions), default=str)}</script>

<script>
// ── Tab switching ──
let graphInited = false;
function showTab(name) {{
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('panel-' + name).classList.add('active');
  event.target.classList.add('active');
  if (name === 'timeline') requestAnimationFrame(drawCharts);
  if (name === 'graph' && !graphInited) {{ graphInited = true; initGraphData(); setupGraphInteraction(); }}
}}

// ── Log filtering ──
let activeLevel = 'all';
function filterLogs() {{
  const q = document.getElementById('logSearch').value.toLowerCase();
  let re = null;
  try {{ re = new RegExp(q, 'i'); }} catch(e) {{}}
  document.querySelectorAll('.log-line').forEach(el => {{
    const text = el.textContent;
    const lvl = el.querySelector('.log-lvl')?.textContent?.trim() || '';
    const matchLevel = activeLevel === 'all' || lvl.startsWith(activeLevel.slice(0,4));
    const matchText = !q || (re ? re.test(text) : text.toLowerCase().includes(q));
    el.style.display = (matchLevel && matchText) ? '' : 'none';
  }});
}}
function toggleLevel(btn, level) {{
  document.querySelectorAll('.log-filter button').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  activeLevel = level;
  filterLogs();
}}

// ── Charts ──
function drawCharts() {{
  const data = JSON.parse(document.getElementById('execData').textContent);
  drawTimelineChart(data);
  drawDurationChart(data);
}}

function drawTimelineChart(data) {{
  const canvas = document.getElementById('tlCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = 400 * dpr;
  canvas.style.height = '400px';
  canvas.style.width = '100%';
  ctx.scale(dpr, dpr);
  const W = rect.width, H = 400;

  if (!data.length) {{
    ctx.fillStyle = '#94a3b8'; ctx.font = '14px sans-serif';
    ctx.textAlign = 'center'; ctx.fillText('No execution data', W/2, H/2);
    return;
  }}

  // Parse timestamps and compute positions
  const parsed = data.map(d => ({{
    ...d,
    t: new Date(d.ts || 0).getTime(),
    dur: d.duration || 0,
  }})).filter(d => d.t > 0).sort((a,b) => a.t - b.t);

  if (!parsed.length) return;

  const tMin = parsed[0].t;
  const tMax = parsed[parsed.length-1].t + (parsed[parsed.length-1].dur * 1000);
  const tRange = Math.max(tMax - tMin, 1000);

  const left = 180, right = 40, top = 30, bottom = 40;
  const chartW = W - left - right;
  const barH = Math.min(20, (H - top - bottom) / parsed.length - 3);

  // Time axis
  ctx.strokeStyle = '#475569'; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(left, top); ctx.lineTo(left, H - bottom); ctx.stroke();

  parsed.forEach((d, i) => {{
    const y = top + i * (barH + 3);
    const x1 = left + ((d.t - tMin) / tRange) * chartW;
    const barW = Math.max(3, (d.dur / (tRange/1000)) * chartW);

    // Label
    ctx.fillStyle = '#e2e8f0'; ctx.font = '11px monospace';
    ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    const lbl = d.script.length > 22 ? d.script.slice(0,19)+'...' : d.script;
    ctx.fillText(lbl, left - 6, y + barH/2);

    // Bar
    ctx.fillStyle = d.ok ? '#3b82f6' : '#dc2626';
    ctx.beginPath();
    ctx.roundRect(x1, y, barW, barH, 3);
    ctx.fill();

    // Duration label
    if (barW > 30) {{
      ctx.fillStyle = '#fff'; ctx.font = '10px sans-serif'; ctx.textAlign = 'left';
      ctx.fillText(d.duration.toFixed(1)+'s', x1 + 4, y + barH/2);
    }}
  }});
}}

function drawDurationChart(data) {{
  const canvas = document.getElementById('durCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = 360 * dpr;
  canvas.style.height = '360px';
  canvas.style.width = '100%';
  ctx.scale(dpr, dpr);
  const W = rect.width, H = 360;

  // Aggregate duration by skill
  const bySkill = {{}};
  data.forEach(d => {{
    const sk = d.skill || 'unknown';
    bySkill[sk] = (bySkill[sk] || 0) + (d.duration || 0);
  }});

  const sorted = Object.entries(bySkill).sort((a,b) => b[1] - a[1]).slice(0, 20);
  if (!sorted.length) {{
    ctx.fillStyle = '#94a3b8'; ctx.font = '14px sans-serif';
    ctx.textAlign = 'center'; ctx.fillText('No data', W/2, H/2);
    return;
  }}

  const maxVal = Math.max(...sorted.map(s => s[1]));
  const leftPad = 240, rightPad = 60;
  const barArea = W - leftPad - rightPad;
  const barH = Math.min(22, (H - 30) / sorted.length - 3);

  sorted.forEach((item, i) => {{
    const y = 15 + i * (barH + 3);
    const barW = maxVal > 0 ? (item[1] / maxVal) * barArea : 0;

    ctx.fillStyle = '#e2e8f0'; ctx.font = '11px monospace';
    ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    const lbl = item[0].length > 32 ? item[0].slice(0,29)+'...' : item[0];
    ctx.fillText(lbl, leftPad - 8, y + barH/2);

    const grad = ctx.createLinearGradient(leftPad, 0, leftPad + barW, 0);
    grad.addColorStop(0, '#06b6d4');
    grad.addColorStop(1, '#a855f7');
    ctx.fillStyle = grad;
    ctx.beginPath(); ctx.roundRect(leftPad, y, barW, barH, 3); ctx.fill();

    ctx.fillStyle = '#94a3b8'; ctx.font = '11px sans-serif'; ctx.textAlign = 'left';
    ctx.fillText(item[1].toFixed(1) + 's', leftPad + barW + 6, y + barH/2);
  }});
}}

// ── Graph Visualization ──
const MIGRATION_COLORS = {{
  not_started: '#4a5568',
  in_progress: '#eab308',
  migrated: '#3b82f6',
  tested: '#22c55e',
  verified: '#22c55e',
  deployed: '#a855f7',
}};
const GRAPH_PALETTE = [
  '#58a6ff','#bc8cff','#f778ba','#56d364',
  '#f0883e','#ffd33d','#ff7b72','#79c0ff',
  '#d2a8ff','#7ee787','#ffa657','#ff9bce',
];

let graphSnapshots = [];
let activeGraphIdx = 0;
let gNodes = [], gEdges = [], gClusters = [];
let gNodeMap = {{}};
let gCamX = 0, gCamY = 0, gCamScale = 1;
let gDragNode = null, gIsDragging = false, gIsPanning = false, gLastMouse = null;
let gSelectedNode = null, gHoverNode = null;
let gPackageColors = {{}};
let gSimRunning = false;
let gAnimFrame = null;

function initGraphData() {{
  const blocks = document.querySelectorAll('.graph-snapshot');
  blocks.forEach(b => {{
    try {{ graphSnapshots.push(JSON.parse(b.textContent)); }} catch(e) {{}}
  }});
  if (graphSnapshots.length) loadGraph(0);
}}

function loadGraph(idx) {{
  activeGraphIdx = idx;
  const snap = graphSnapshots[idx];
  if (!snap) return;

  // Reset camera
  gCamX = 0; gCamY = 0; gCamScale = 1;
  gSelectedNode = null; gHoverNode = null;

  // Build package color map
  const pkgs = [...new Set(snap.nodes.map(n => n.package))];
  gPackageColors = {{}};
  pkgs.forEach((p, i) => {{ gPackageColors[p] = GRAPH_PALETTE[i % GRAPH_PALETTE.length]; }});

  // Initialize nodes with positions
  gClusters = snap.clusters || [];
  gNodes = snap.nodes.map((n, i) => {{
    const ci = gClusters.findIndex(c => c.modules && c.modules.includes(n.id));
    const cluster = gClusters[ci] || {{ modules: [] }};
    const angle = gClusters.length > 0 ? (ci / gClusters.length) * Math.PI * 2 - Math.PI/2 : (i / snap.nodes.length) * Math.PI * 2;
    const members = cluster.modules || [];
    const mi = members.indexOf(n.id);
    const spread = 60 + members.length * 12;
    const subAngle = members.length > 0 ? (mi / members.length) * Math.PI * 2 : 0;
    const cx = Math.cos(angle) * 220;
    const cy = Math.sin(angle) * 220;
    return {{
      ...n,
      x: cx + Math.cos(subAngle) * spread + (Math.random()-0.5)*20,
      y: cy + Math.sin(subAngle) * spread + (Math.random()-0.5)*20,
      vx: 0, vy: 0,
      r: Math.max(6, Math.sqrt(n.lines || 10) * 0.7),
      color: gPackageColors[n.package] || '#8b949e',
      clusterIdx: ci >= 0 ? ci : -1,
      statusColor: MIGRATION_COLORS[n.migration_status] || MIGRATION_COLORS.not_started,
    }};
  }});
  gNodeMap = {{}};
  gNodes.forEach(n => {{ gNodeMap[n.id] = n; }});
  gEdges = snap.edges.map(e => ({{ ...e, source: gNodeMap[e.from], target: gNodeMap[e.to] }})).filter(e => e.source && e.target);

  // Update legend
  updateGraphLegend(pkgs);
  // Update stats
  updateGraphStats(snap.stats || {{}});

  // Start simulation
  if (!gSimRunning) {{ gSimRunning = true; graphLoop(); }}
}}

function updateGraphLegend(pkgs) {{
  const el = document.getElementById('graphLegend');
  if (!el) return;
  let html = '<strong style="color:#f1f5f9;font-size:0.82rem;margin-right:8px">Packages:</strong>';
  pkgs.forEach(p => {{
    html += '<div class="gl-item"><div class="gl-swatch" style="background:' + gPackageColors[p] + '"></div>' + p + '</div>';
  }});
  html += '<span style="border-left:1px solid #475569;margin:0 8px"></span>';
  html += '<strong style="color:#f1f5f9;font-size:0.82rem;margin-right:8px">Status:</strong>';
  Object.entries(MIGRATION_COLORS).forEach(([k,v]) => {{
    html += '<div class="gl-item"><div class="gl-swatch" style="background:' + v + ';border-radius:50%"></div>' + k.replace('_',' ') + '</div>';
  }});
  el.innerHTML = html;
}}

function updateGraphStats(stats) {{
  const el = document.getElementById('graphStats');
  if (!el) return;
  el.innerHTML = 'Nodes: <span>' + (stats.node_count||0) + '</span> · ' +
    'Edges: <span>' + (stats.edge_count||0) + '</span> · ' +
    'Packages: <span>' + (stats.packages||0) + '</span> · ' +
    'Languages: <span>' + (stats.languages||[]).join(', ') + '</span>';
}}

function switchGraph(btn, idx) {{
  document.querySelectorAll('.graph-controls button').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  loadGraph(idx);
}}

// Force simulation
function gSimulate() {{
  const alpha = 0.3, friction = 0.88;
  for (let i = 0; i < gNodes.length; i++) {{
    for (let j = i+1; j < gNodes.length; j++) {{
      let dx = gNodes[j].x - gNodes[i].x;
      let dy = gNodes[j].y - gNodes[i].y;
      let d2 = dx*dx + dy*dy;
      if (d2 < 1) d2 = 1;
      const f = 1200 / d2;
      const fx = dx / Math.sqrt(d2) * f;
      const fy = dy / Math.sqrt(d2) * f;
      gNodes[i].vx -= fx; gNodes[i].vy -= fy;
      gNodes[j].vx += fx; gNodes[j].vy += fy;
    }}
  }}
  for (const e of gEdges) {{
    const dx = e.target.x - e.source.x;
    const dy = e.target.y - e.source.y;
    const d = Math.sqrt(dx*dx + dy*dy) || 1;
    const f = (d - 80) * 0.008;
    const fx = dx/d * f;
    const fy = dy/d * f;
    e.source.vx += fx; e.source.vy += fy;
    e.target.vx -= fx; e.target.vy -= fy;
  }}
  // Cluster gravity
  const cc = {{}};
  for (const n of gNodes) {{
    if (n.clusterIdx < 0) continue;
    if (!cc[n.clusterIdx]) cc[n.clusterIdx] = {{x:0,y:0,c:0}};
    cc[n.clusterIdx].x += n.x; cc[n.clusterIdx].y += n.y; cc[n.clusterIdx].c++;
  }}
  for (const k in cc) {{ cc[k].x /= cc[k].c; cc[k].y /= cc[k].c; }}
  for (const n of gNodes) {{
    if (n.clusterIdx >= 0 && cc[n.clusterIdx]) {{
      n.vx += (cc[n.clusterIdx].x - n.x) * 0.005;
      n.vy += (cc[n.clusterIdx].y - n.y) * 0.005;
    }}
    n.vx -= n.x * 0.0005;
    n.vy -= n.y * 0.0005;
  }}
  for (const n of gNodes) {{
    if (n === gDragNode) continue;
    n.vx *= friction; n.vy *= friction;
    n.x += n.vx * alpha; n.y += n.vy * alpha;
  }}
}}

function gScreenToWorld(sx, sy, canvas) {{
  const r = canvas.getBoundingClientRect();
  const cw = r.width, ch = r.height;
  return {{ x: (sx - r.left - cw/2)/gCamScale + gCamX, y: (sy - r.top - ch/2)/gCamScale + gCamY }};
}}

function gWorldToScreen(wx, wy, canvas) {{
  const r = canvas.getBoundingClientRect();
  const cw = r.width, ch = r.height;
  return {{ x: (wx - gCamX)*gCamScale + cw/2, y: (wy - gCamY)*gCamScale + ch/2 }};
}}

function gDrawArrow(ctx, x1, y1, x2, y2, color, width, alpha) {{
  const dx = x2-x1, dy = y2-y1;
  const len = Math.sqrt(dx*dx+dy*dy);
  if (len < 1) return;
  const ux = dx/len, uy = dy/len;
  const ex = x2 - ux*8, ey = y2 - uy*8;
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.strokeStyle = color; ctx.lineWidth = width;
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(ex, ey); ctx.stroke();
  const hl = 6 * width;
  ctx.fillStyle = color;
  ctx.beginPath(); ctx.moveTo(ex, ey);
  ctx.lineTo(ex - ux*hl - uy*hl*0.4, ey - uy*hl + ux*hl*0.4);
  ctx.lineTo(ex - ux*hl + uy*hl*0.4, ey - uy*hl - ux*hl*0.4);
  ctx.closePath(); ctx.fill();
  ctx.restore();
}}

function gDraw() {{
  const canvas = document.getElementById('graphCanvas');
  if (!canvas || !canvas.offsetParent) return;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.parentElement.getBoundingClientRect();
  const W = rect.width, H = rect.height;
  canvas.width = W * dpr; canvas.height = H * dpr;
  canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  ctx.clearRect(0, 0, W, H);
  ctx.save();
  ctx.translate(W/2, H/2);
  ctx.scale(gCamScale, gCamScale);
  ctx.translate(-gCamX, -gCamY);

  const hlSet = new Set();
  const hlEdges = new Set();
  if (gSelectedNode) {{
    hlSet.add(gSelectedNode.id);
    for (const e of gEdges) {{
      if (e.source.id === gSelectedNode.id || e.target.id === gSelectedNode.id) {{
        hlSet.add(e.source.id); hlSet.add(e.target.id); hlEdges.add(e);
      }}
    }}
  }}

  // Cluster hulls
  const cg = {{}};
  for (const n of gNodes) {{
    if (n.clusterIdx < 0) continue;
    if (!cg[n.clusterIdx]) cg[n.clusterIdx] = [];
    cg[n.clusterIdx].push(n);
  }}
  for (const [idx, grp] of Object.entries(cg)) {{
    if (grp.length < 2) continue;
    const cx = grp.reduce((s,n)=>s+n.x,0)/grp.length;
    const cy = grp.reduce((s,n)=>s+n.y,0)/grp.length;
    let maxR = 0;
    for (const n of grp) {{ const d = Math.sqrt((n.x-cx)**2+(n.y-cy)**2)+n.r+20; if(d>maxR) maxR=d; }}
    ctx.save();
    ctx.globalAlpha = 0.06; ctx.fillStyle = grp[0].color;
    ctx.beginPath(); ctx.arc(cx,cy,maxR,0,Math.PI*2); ctx.fill();
    ctx.globalAlpha = 0.15; ctx.strokeStyle = grp[0].color; ctx.lineWidth = 1; ctx.setLineDash([4,4]); ctx.stroke(); ctx.setLineDash([]);
    ctx.globalAlpha = 0.35; ctx.fillStyle = grp[0].color;
    ctx.font = 'bold 11px -apple-system, sans-serif'; ctx.textAlign = 'center';
    const clbl = (gClusters[idx]?.name || '').toUpperCase();
    ctx.fillText(clbl, cx, cy - maxR + 6);
    ctx.restore();
  }}

  // Edges
  for (const e of gEdges) {{
    const isHL = hlEdges.has(e); const dimmed = gSelectedNode && !isHL;
    const alpha = dimmed ? 0.07 : (isHL ? 0.7 : 0.2);
    const w = isHL ? 1.5 : 0.8;
    const col = isHL ? e.source.color : '#30363d';
    gDrawArrow(ctx, e.source.x, e.source.y, e.target.x, e.target.y, col, w, alpha);
  }}

  // Nodes
  for (const n of gNodes) {{
    const dimmed = gSelectedNode && !hlSet.has(n.id);
    const isSel = n === gSelectedNode;
    const isHov = n === gHoverNode;
    ctx.save();
    ctx.globalAlpha = dimmed ? 0.15 : 1;

    if (isSel && !dimmed) {{ ctx.shadowColor = n.color; ctx.shadowBlur = 20; }}

    // Main circle (package color)
    ctx.fillStyle = n.color;
    ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI*2); ctx.fill();
    ctx.shadowBlur = 0;

    // Migration status ring
    if (!dimmed) {{
      ctx.strokeStyle = n.statusColor;
      ctx.lineWidth = 2.5;
      ctx.beginPath(); ctx.arc(n.x, n.y, n.r + 3, 0, Math.PI*2); ctx.stroke();
    }}

    // Hover ring
    if (isHov && !dimmed) {{
      ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(n.x, n.y, n.r + 6, 0, Math.PI*2); ctx.stroke();
    }}

    // Label
    if (!dimmed || isSel) {{
      const label = n.id.split('/').pop();
      ctx.fillStyle = dimmed ? 'rgba(139,148,158,0.4)' : '#e1e4e8';
      ctx.font = (isSel || isHov ? '600' : '400') + ' 10px -apple-system, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(label, n.x, n.y + n.r + 14);
    }}
    ctx.restore();
  }}
  ctx.restore();
}}

function graphLoop() {{
  gSimulate(); gDraw();
  gAnimFrame = requestAnimationFrame(graphLoop);
}}

// Graph interaction
function setupGraphInteraction() {{
  const canvas = document.getElementById('graphCanvas');
  if (!canvas) return;

  function getNodeAt(ex, ey) {{
    const {{x,y}} = gScreenToWorld(ex, ey, canvas);
    for (let i = gNodes.length-1; i >= 0; i--) {{
      const n = gNodes[i];
      const dx = n.x-x, dy = n.y-y;
      if (dx*dx+dy*dy < (n.r+4)**2) return n;
    }}
    return null;
  }}

  canvas.addEventListener('mousedown', e => {{
    const node = getNodeAt(e.clientX, e.clientY);
    if (node) {{ gDragNode = node; gIsDragging = false; }}
    else {{ gIsPanning = true; }}
    gLastMouse = {{x: e.clientX, y: e.clientY}};
  }});

  canvas.addEventListener('mousemove', e => {{
    const dx = e.clientX - (gLastMouse?.x||e.clientX);
    const dy = e.clientY - (gLastMouse?.y||e.clientY);
    if (gDragNode) {{
      gIsDragging = true;
      gDragNode.x += dx / gCamScale; gDragNode.y += dy / gCamScale;
      gDragNode.vx = 0; gDragNode.vy = 0;
    }} else if (gIsPanning) {{
      gCamX -= dx / gCamScale; gCamY -= dy / gCamScale;
    }}
    gLastMouse = {{x: e.clientX, y: e.clientY}};

    const node = getNodeAt(e.clientX, e.clientY);
    gHoverNode = node;
    canvas.style.cursor = node ? 'grab' : (gIsPanning ? 'grabbing' : 'default');

    const tip = document.getElementById('graphTooltip');
    if (node && tip) {{
      let html = '<h4>' + node.id.split('/').pop() + '</h4><div class="meta">';
      html += '<strong>' + node.id + '</strong><br>';
      html += 'Package: <span>' + node.package + '</span> · Lines: <span>' + (node.lines||0) + '</span><br>';
      html += 'Language: <span>' + (node.language||'') + '</span><br>';
      html += 'Fan in: <span>' + (node.fan_in||0) + '</span> · Fan out: <span>' + (node.fan_out||0) + '</span><br>';
      html += 'Status: <span style="color:' + (MIGRATION_COLORS[node.migration_status]||'#4a5568') + '">' + (node.migration_status||'not_started').replace('_',' ') + '</span>';
      if (node.risk_score) html += ' · Risk: <span>' + node.risk_score + '</span>';
      html += '</div>';
      tip.innerHTML = html; tip.style.display = 'block';
      const r = canvas.getBoundingClientRect();
      let tx = e.clientX - r.left + 16, ty = e.clientY - r.top + 16;
      if (tx + 320 > r.width) tx = e.clientX - r.left - 330;
      if (ty + 150 > r.height) ty = e.clientY - r.top - 150;
      tip.style.left = tx + 'px'; tip.style.top = ty + 'px';
    }} else if (tip) {{ tip.style.display = 'none'; }}
  }});

  canvas.addEventListener('mouseup', e => {{
    if (gDragNode && !gIsDragging) {{
      gSelectedNode = gSelectedNode === gDragNode ? null : gDragNode;
    }}
    gDragNode = null; gIsPanning = false; gIsDragging = false;
  }});

  canvas.addEventListener('wheel', e => {{
    e.preventDefault();
    const factor = e.deltaY > 0 ? 0.92 : 1.08;
    gCamScale = Math.max(0.2, Math.min(5, gCamScale * factor));
  }}, {{ passive: false }});
}}
</script>
</body>
</html>"""


# ── Entry point ────────────────────────────────────────────────────────────

@log_execution
def main():
    parser = argparse.ArgumentParser(description="Generate migration run status viewer.")
    parser.add_argument("analysis_dir", help="Path to migration-analysis/ directory")
    parser.add_argument("--output", "-o", default=None, help="Output HTML path")
    parser.add_argument("--skills-root", default=None, help="Path to skills repo root")
    parser.add_argument("--project-name", default="Migration Project", help="Project name")
    args = parser.parse_args()

    analysis_dir = Path(args.analysis_dir).resolve()
    if not analysis_dir.is_dir():
        print(f"Error: {analysis_dir} not found", file=sys.stderr)
        return 1

    # Load data
    state = load_state(analysis_dir)
    sizing = load_sizing(analysis_dir)
    gate_report = load_gate_report(analysis_dir)
    executions, raw_lines = parse_logs(analysis_dir)
    graph_snapshots = load_graph_snapshots(analysis_dir, state)

    # Compute
    phase_progress = compute_phase_progress(state)
    skill_summary = compute_skill_summary(executions)

    project_name = args.project_name
    if state.get("project_name"):
        project_name = state["project_name"]

    # Generate
    html = generate_html(
        project_name, state, phase_progress, skill_summary,
        executions, raw_lines, sizing, gate_report, graph_snapshots,
    )

    output_path = Path(args.output) if args.output else analysis_dir / "run-status.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    summary = {
        "status": "complete",
        "output": str(output_path),
        "current_phase": state.get("phase", 0),
        "scripts_run": skill_summary["scripts_run"],
        "skills_used": skill_summary["skills_used"],
        "failures": skill_summary["failures"],
        "total_duration_s": skill_summary["total_duration_s"],
        "graph_snapshots": list(graph_snapshots.keys()) if graph_snapshots else [],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
