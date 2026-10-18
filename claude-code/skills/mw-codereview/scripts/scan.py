#!/usr/bin/env python3
"""mw-codereview scanner: finds what is worth reviewing in a Spring Boot and/or Angular repository.

    python3 scan.py [root] [--out DIR] [--online] [--resolve] [--baseline auto|none|OLD/scan.json]
    python3 scan.py --out DIR --show SB-SQL-CONCAT,NG-DOM-XSS | endpoints | routes | modules | projects | calls |
                                     entities | privacy | hotspots | keycloak | owasp | tools
    python3 scan.py --list-checks

--online   lets npm audit, osv-scanner, trivy and semgrep fetch their databases and rules
--resolve  asks Gradle or Maven for the resolved runtime classpath (runs the build tool, takes a while)
--baseline auto compares with the newest earlier docs/mw-codereview-*/scan.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from dataclasses import asdict
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import (angular, calls, deps, detect, keycloak, modules, privacy, repo as repo_checks, reuse,  # noqa: E402
                 schema, spring, testgaps, tools, ux)
from lib.core import CHECKS, SEVERITIES, Hits, Repo  # noqa: E402

RANK = {s: i for i, s in enumerate(SEVERITIES)}


def _key(hit: dict) -> str:
    evidence = re.sub(r'\d+', '#', hit.get('evidence') or '')
    return hashlib.sha1(f'{hit["check"]}|{hit.get("file")}|{evidence}'.encode()).hexdigest()[:16]


def _order(hit: dict) -> tuple:
    spec = CHECKS[hit['check']]
    return RANK[hit['severity']], not spec.security, hit['check'], hit.get('file') or '', hit.get('line') or 0


def scan(args) -> dict:
    started = time.time()
    root = Path(args.root).resolve()
    repo = Repo(root)
    stacks = detect.detect(repo)
    hits = Hits()
    inventory = {}
    ctx = None
    if stacks['spring']:
        ctx = spring.Ctx(repo, stacks['spring'], hits)
        sp = spring.run(ctx)
        sp['modules'] = modules.jvm(ctx)
        sp['calls'] = calls.backend(ctx)
        sp.update(schema.run(ctx))
        sp['tests'] = testgaps.backend(ctx, sp['modules'])
        inventory['spring'] = sp
    workspaces = []
    for ws in stacks['angular']:
        w = angular.Workspace(repo, ws)
        ng = angular.run(w, hits)
        ng['projects'] = modules.nx(w, hits)
        ng['calls'] = calls.frontend(w, hits, ctx.endpoints if ctx else None)
        ng.update(ux.run(w, hits))
        ng['tests'] = testgaps.frontend(w, hits)
        inventory.setdefault('angular', []).append(ng)
        workspaces.append(w)
    found = keycloak.run(repo, hits, ctx, stacks['angular'])
    if found:
        inventory['keycloak'] = found
    personal = privacy.run(repo, hits, ctx, workspaces)
    if personal:
        inventory['privacy'] = personal
    inventory['reuse'] = reuse.run(repo, hits, [c for w in workspaces for c in w.comps], ctx.main if ctx else [])
    repo_checks.run(repo, hits, stacks)
    versions = deps.run(repo, stacks, hits, inventory, resolve=args.resolve)
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    tool_status = {} if args.no_tools else tools.run(repo, hits, stacks, args.online,
                                                        Path(tempfile.mkdtemp(prefix='mw-codereview-')))

    unique, seen = [], set()
    for h in hits.items:
        k = (h['check'], h.get('file'), h.get('line'), h.get('evidence'))
        if k not in seen:
            seen.add(k)
            unique.append(h)
    unique.sort(key=_order)
    for i, h in enumerate(unique, 1):
        h['id'] = f'h{i}'
        h['key'] = _key(h)

    resolved = []
    if args.baseline == 'auto':
        earlier = sorted(p for p in (root / 'docs').glob('mw-codereview-*/scan.json') if p.parent != out)
        args.baseline = str(earlier[-1]) if earlier else None
    if args.baseline and Path(args.baseline).is_file():
        old = json.loads(Path(args.baseline).read_text(encoding='utf-8'))
        old_keys = {h.get('key'): h for h in old.get('hits', [])}
        now = {h['key'] for h in unique}
        for h in unique:
            h['new'] = h['key'] not in old_keys
        resolved = [{k: h[k] for k in ('check', 'severity', 'file', 'line', 'evidence') if k in h}
                    for key, h in old_keys.items() if key not in now]

    spring_stack = stacks['spring']
    return {
        'meta': {'root': str(root), 'generated': dt.date.today().isoformat(), 'scanner': 'mw-codereview 1',
                 'seconds': round(time.time() - started, 1), 'git': repo.git, 'files': len(repo.files),
                 'online': args.online, 'resolve': args.resolve, 'baseline': args.baseline,
                 'version_data': deps.DATA['checked']},
        'stacks': {
            'spring': {k: v for k, v in spring_stack.items() if k not in ('build_text', 'deps')} if spring_stack else None,
            'angular': [{k: v for k, v in ws.items() if k not in ('installed', 'declared')} for ws in stacks['angular']],
        },
        'versions': versions,
        'inventory': inventory,
        'tools': tool_status,
        'checks': {c: asdict(CHECKS[c]) for c in sorted({h['check'] for h in unique})},
        'hits': unique,
        'resolved': resolved,
        'files_by_ext': dict(Counter(os.path.splitext(f)[1] or os.path.basename(f) for f in repo.files).most_common(12)),
    }


def _stack_line(result: dict) -> list[str]:
    lines = []
    sp = result['stacks']['spring']
    if sp:
        mods = sp['modules']
        lang = sorted({m['language'] for m in mods}) or ['?']
        lines.append(f'Spring Boot {sp["boot"] or "?"} - {"/".join(lang)}, {"/".join(sp["build"])}, '
                     f'{len(mods)} module(s), Java {sp["java"] or "?"}' + (f', Kotlin {sp["kotlin"]}' if sp['kotlin'] else ''))
    for ws in result['stacks']['angular']:
        lines.append(f'Angular {ws["angular"]} at {ws["path"]} - {"Nx, " if ws["nx"] else ""}{len(ws["projects"])} '
                     f'project(s), tests {ws["test_runner"] or "?"}, lockfile {ws["lockfile"] or "none"}'
                     + (', SSR' if ws['ssr'] else '') + (', zoneless' if ws['zoneless'] else ', zone.js'))
    return lines or ['no Spring Boot or Angular detected - repository checks only']


def _inventory_lines(result: dict) -> list[str]:
    out = []
    sp = result['inventory'].get('spring')
    if sp:
        eps = sp['endpoints']
        chains = sp['chains']
        by_rule = Counter((e.get('url_rule') or ('-' if not chains else 'UNMATCHED')) for e in eps)
        with_method = sum(1 for e in eps if e['auth'] or e['class_auth'])
        public = [e for e in eps if e.get('url_rule') in ('permitAll', 'anonymous') and not (e['auth'] or e['class_auth'])]
        out.append(f'spring   {len(eps)} endpoints, {len(chains)} security chain(s), method security '
                   f'{"on" if sp["method_security"] else "off"}, {with_method} endpoints with a method-level check')
        out.append('         url rule per endpoint: ' + ', '.join(f'{k} {v}' for k, v in by_rule.most_common()))
        if public:
            out.append('         public: ' + ', '.join(f'{e["http"]} {e["path"]}' for e in public[:14])
                       + (f' ... (+{len(public) - 14})' if len(public) > 14 else ''))
        out.append('         classes: ' + ', '.join(f'{k} {v}' for k, v in sorted(sp['counts'].items(), key=lambda kv: -kv[1])))
        builds = defaultdict(list)
        for m in sp.get('modules') or []:
            builds[m['build']].append(m)
        for build, mods in builds.items():
            if len(mods) > 1:
                out.append(f'modules  {build}: {len(mods)} modules, classes/tests - ' + ', '.join(
                    f'{m["path"].split("/")[-1]} {m["types"]}/{m["tests"]}' for m in sorted(mods, key=lambda m: -m['types'])))
        back = sp.get('calls') or []
        if back:
            kinds = Counter(c['kind'] for c in back)
            out.append(f'calls    backend {len(back)} outbound sites (' + ', '.join(f'{k} {v}' for k, v in kinds.most_common())
                       + f'), {sum(c["loop"] for c in back)} in a loop, {sum(c["tx"] for c in back)} inside a transaction')
        if sp.get('entities'):
            mig = sp['migrations']
            out.append(f'schema   {len(sp["entities"])} entities, {mig["files"]} migration files, {mig["tables"]} tables, '
                       f'{mig["foreign_keys"]} foreign keys, engine {mig["engine"] or "?"}, '
                       f'ddl-auto validate {"on" if mig["validate"] else "off"}')
        if sp.get('tests'):
            out.append(f'tests    {sp["tests"]["untested_writes"]} of {sp["tests"]["write_endpoints"]} write endpoints '
                       'reached by no test')
    for ng in result['inventory'].get('angular') or []:
        routes = [r for r in ng['routes'] if not r['redirect'] and r['segment'] != '**']
        own = sum(1 for r in routes if r['guards'])
        inherited = sum(1 for r in routes if not r['guards'] and r['inherited'])
        open_ = [r['path'] for r in routes if not r['guards'] and not r['inherited']]
        out.append(f'angular  {ng["path"]}: {ng["components"]} components/directives, {ng["injectables"]} injectables, '
                   f'{len(routes)} routes ({own} guarded, {inherited} inherit a guard, {len(open_)} open)')
        if open_:
            out.append('         open routes: ' + ', '.join(open_[:16]) + (f' ... (+{len(open_) - 16})' if len(open_) > 16 else ''))
        projects = ng.get('projects') or []
        if projects:
            apps = sum(1 for p in projects if p['type'] == 'application')
            out.append(f'nx       {ng["path"]}: {len(projects)} projects ({apps} apps, {len(projects) - apps} libs), '
                       f'{sum(1 for p in projects if p["tags"])} tagged')
        front = ng.get('calls') or []
        if front:
            matched = Counter(c['matched'] if c['matched'] in ('external', 'dynamic') else 'matched' if c['matched']
                              else 'unmatched' for c in front)
            out.append(f'calls    {ng["path"]}: {len(front)} HTTP calls - ' + ', '.join(f'{k} {v}' for k, v in matched.most_common()))
        out.append(f'ux       {ng["path"]}: {ng.get("forms", 0)} components with a form')
    kc = result['inventory'].get('keycloak')
    if kc:
        realms = kc['realms']
        out.append('keycloak ' + '; '.join(x for x in (
            ('issuer ' + ', '.join(kc['issuers'][:2])) if kc['issuers'] else '',
            f'{len(realms)} realm export(s) ({sum(r["local"] for r in realms)} local)' if realms else '',
            ', '.join(f'{f["library"]} {f["version"]} in {f["path"]}' for f in kc['frontends']),
            'admin API used' if kc['admin_api'] else '',
            ('images ' + ', '.join(kc['images'][:3])) if kc['images'] else '') if x))
    pv = result['inventory'].get('privacy')
    if pv:
        if pv['need']:
            out.append(f'privacy  protection need {pv["need"]} ({pv["decided_by"] or "identifying data only"}) - '
                       f'score {pv["score"]}/100, {pv["columns"]["personal"]} of {pv["columns"]["total"]} columns '
                       f'personal in {pv["tables"]["personal"]} of {pv["tables"]["total"]} tables')
            out.append('         ' + ', '.join(f'{k.replace("_", " ")} {v}' for k, v in pv['tiers'].items())
                       + '; subjects ' + ', '.join(f'{k} {len(v)}' for k, v in pv['subjects'].items())
                       + f'; field encryption {len(pv["encrypted_columns"]) or "none"}'
                       + f'; cleanup jobs {len(pv["retention_jobs"]) or "none"}')
        if pv['recipients']:
            out.append('         recipients: ' + ', '.join(f'{r["name"]} ({r["kind"]}, {r["seat"]})' for r in pv['recipients'])
                       + ('' if pv['consent_manager'] else '; no consent manager'))
        if pv['forms']:
            out.append(f'         forms collecting personal data: {len(pv["forms"])}')
    reuse = result['inventory'].get('reuse') or {}
    if reuse.get('duplicate_blocks') or reuse.get('similar'):
        out.append(f'reuse    {reuse["duplicate_blocks"]} copied blocks ({reuse["duplicate_lines"]} lines), '
                   f'{reuse["similar"]} near-identical pairs')
    return out


def digest(result: dict, examples: int, out_dir: Path) -> str:
    hits = result['hits']
    lines = [f'mw-codereview scan  {result["meta"]["generated"]}  {result["meta"]["root"]}  '
             f'({result["meta"]["seconds"]}s, version data from {result["meta"]["version_data"]})']
    for s in _stack_line(result):
        lines.append('stack    ' + s)
    ext = ', '.join(f'{k} {v}' for k, v in result['files_by_ext'].items())
    lines.append(f'scope    {result["meta"]["files"]} files ({"git ls-files" if result["meta"]["git"] else "walk"}): {ext}')
    if result['tools']:
        parts = []
        for name, st in result['tools'].items():
            text = f'{name} {st["status"]}'
            if 'findings' in st:
                text += f' ({st["findings"]}{", " + st["mode"] if st.get("mode") else ""})'
            if st.get('install'):
                text += f' [{st["install"]}]'
            parts.append(text)
        lines.append('tools    ' + ' | '.join(parts))
    if result['versions'].get('spring', {}).get('resolve'):
        lines.append('resolve  ' + result['versions']['spring']['resolve'])
    lines += _inventory_lines(result)
    sev = Counter(h['severity'] for h in hits)
    security = sum(1 for h in hits if CHECKS[h['check']].security)
    summary = ' | '.join(f'{s} {sev.get(s, 0)}' for s in SEVERITIES)
    if result['meta']['baseline']:
        new = sum(1 for h in hits if h.get('new'))
        summary += f'   [new {new}, known {len(hits) - new}, resolved since baseline {len(result["resolved"])}]'
    lines.append(f'hits     {summary}   ({security} of {len(hits)} security)')
    lines.append('')

    groups = defaultdict(list)
    for h in hits:
        groups[(h['severity'], h['check'])].append(h)
    for (severity, check), group in sorted(groups.items(), key=lambda kv: _order(kv[1][0])):
        spec = CHECKS[check]
        tag = ' security' if spec.security else ''
        rule = ' '.join(x for x in (spec.rule, spec.owasp and f'OWASP {spec.owasp}', spec.gdpr and f'GDPR {spec.gdpr}')
                        if x)
        lines.append(f'[{severity}] {check}  {spec.title}  x{len(group)}{tag}' + (f'  ({rule})' if rule else ''))
        limit = max(examples, 15) if severity in ('critical', 'high') else examples
        for h in group[:limit]:
            where = f'{h["file"]}:{h["line"]}' if h.get('line') else (h.get('file') or '-')
            flags = ''.join(f' [{f}]' for f in ('test', 'new') if h.get(f)) + (' [history]' if h.get('history') else '')
            note = f'   ({h["note"]})' if h.get('note') else ''
            lines.append(f'   {h["id"]:>5} {where}{flags}  {h["evidence"]}{note}')
        if len(group) > limit:
            lines.append(f'         ... {len(group) - limit} more: --show {check}')
        if spec.verify and severity in ('critical', 'high', 'medium'):
            lines.append(f'         verify: {spec.verify}')
    lines.append('')
    lines.append(f'full result: {out_dir / "scan.json"}')
    lines.append(f'one check:   python3 {Path(__file__).resolve()} --out {out_dir} --show <CHECK|endpoints|routes|modules|'
                 'projects|calls|entities|privacy|hotspots|keycloak|owasp|tools>')
    return '\n'.join(lines)


def show(out_dir: Path, what: str) -> str:
    data = json.loads((out_dir / 'scan.json').read_text(encoding='utf-8'))
    lines = []
    if what == 'endpoints':
        for e in (data['inventory'].get('spring') or {}).get('endpoints', []):
            auth = ', '.join(e['auth_text'] or e['auth'] or e['class_auth']) or '-'
            lines.append(f'{e["http"]:<6} {e["path"]:<55} {e["controller"]}.{e["method"]}  url={e.get("url_rule") or "-"}'
                         f'  method={auth}  {e["file"]}:{e["line"]}')
    elif what == 'routes':
        for ng in data['inventory'].get('angular') or []:
            for r in ng['routes']:
                lines.append(f'{r["path"]:<45} {r["target"][:50]:<50} guards={"; ".join(r["guards"]) or "-"}'
                             f'  inherited={r["inherited"]}  {r["file"]}:{r["line"]}')
    elif what == 'modules':
        for m in (data['inventory'].get('spring') or {}).get('modules', []):
            lines.append(f'{m["build"]:<22} {m["path"]:<40} classes {m["types"]:>4}  lines {m["lines"]:>6}  tests {m["tests"]:>4}'
                         f'  uses {", ".join(u.split("/")[-1] for u in m["uses"]) or "-"}'
                         f'  used by {", ".join(u.split("/")[-1] for u in m["used_by"]) or "-"}')
    elif what == 'projects':
        for ng in data['inventory'].get('angular') or []:
            for p in ng.get('projects') or []:
                lines.append(f'{p["name"]:<30} {p["type"] or "?":<11} {",".join(p["tags"]) or "-":<28} files {p["files"]:>4}'
                             f'  components {p["components"]:>3}  uses {", ".join(p["uses"]) or "-"}'
                             f'  used by {", ".join(p["used_by"]) or "-"}')
    elif what == 'calls':
        for c in (data['inventory'].get('spring') or {}).get('calls', []):
            flags = ' '.join(f for f in ('tx', 'loop', 'retry') if c[f])
            lines.append(f'{c["kind"]:<11} {c["verb"]:<10} {c["target"] or "?":<45} {c["where"]}  {c["file"]}:{c["line"]}'
                         + (f'  [{flags}]' if flags else ''))
        for ng in data['inventory'].get('angular') or []:
            for c in ng.get('calls') or []:
                lines.append(f'front-http  {c["verb"]:<10} {c["target"]:<60} -> {c["matched"] or "NO MATCH"}  '
                             f'{c["file"]}:{c["line"]}')
    elif what == 'entities':
        for e in (data['inventory'].get('spring') or {}).get('entities', []):
            rels = '; '.join(f'{r["prop"]} {r["kind"]} {r["target"]}' + (f' mappedBy={r["mapped_by"]}' if r['mapped_by'] else '')
                             + (f' cascade={",".join(r["cascade"])}' if r['cascade'] else '') + (f' {r["coll"]}' if r['coll'] else '')
                             for r in e['relations'])
            lines.append(f'{e["entity"]:<28} {e["table"]:<28} cols {e["columns"]:>3}  version {"y" if e["version"] else "n"}'
                         f'  migrated {"y" if e["in_migrations"] else "n"}  {rels or "-"}  {e["file"]}')
    elif what == 'privacy':
        pv = data['inventory'].get('privacy') or {}
        for t in pv.get('map', []):
            cols = ', '.join(f'{c["column"]} {c["category"]}' + (f' ({c["via"]})' if c['via'] else '')
                             + (' [encrypted]' if c['encrypted'] else '') for c in t['columns'])
            lines.append(f'{t["need"]:<9} {t["table"]:<30} {",".join(t["subjects"]):<20} erasure {t["erasure"] or "-":<28}'
                         f'  {cols}  {t["file"] or ""}')
        for h in pv.get('hubs', []):
            lines.append(f'hub       {h["table"]}: one join reaches {", ".join(h["reached"])} - {", ".join(h["categories"])}')
        for r in pv.get('recipients', []):
            lines.append(f'recipient {r["name"]} ({r["kind"]}, {r["seat"]} company): {", ".join(r["where"])}')
        for f in pv.get('forms', []):
            lines.append(f'form      {f["file"]}: {", ".join(f["fields"])}')
    elif what == 'hotspots':
        weight = {'critical': 8, 'high': 4, 'medium': 2, 'low': 1}
        dirs = defaultdict(lambda: {'score': 0, 'files': set(), 'checks': Counter()})
        for h in data['hits']:
            f = h.get('file') or ''
            if h.get('test') or not f.endswith(('.kt', '.java', '.ts', '.html')):
                continue
            d = dirs[os.path.dirname(f)]
            d['score'] += weight[h['severity']] + (2 if data['checks'][h['check']]['security'] else 0)
            d['files'].add(f)
            d['checks'][h['check']] += 1
        for path, d in sorted(dirs.items(), key=lambda kv: -kv[1]['score'])[:12]:
            lines.append(f'{d["score"]:>4}  {path:<70} {len(d["files"]):>3} files  '
                         + ', '.join(f'{k} {v}' for k, v in d['checks'].most_common(4)))
    elif what == 'keycloak':
        lines.append(json.dumps(data['inventory'].get('keycloak'), indent=1, ensure_ascii=False))
    elif what == 'owasp':
        from lib.core import CHECKS as ALL
        hit_count = Counter(h['check'] for h in data['hits'])
        for cat in [f'A{i:02d}' for i in range(1, 11)]:
            ids = sorted(c.id for c in ALL.values() if c.owasp == cat)
            found = {i: hit_count[i] for i in ids if hit_count.get(i)}
            lines.append(f'{cat}  {len(ids):>3} checks, {sum(found.values()):>4} hits'
                         + (f'  - {", ".join(f"{k} {v}" for k, v in sorted(found.items(), key=lambda kv: -kv[1]))}'
                            if found else '') + ('  (reader only: no automated check)' if not ids else ''))
    elif what == 'tools':
        lines.append(json.dumps(data['tools'], indent=1))
    else:
        wanted = set(what.split(','))
        for h in data['hits']:
            if h['check'] in wanted or h['id'] in wanted:
                lines.append(f'{h["id"]:>5} [{h["severity"]}] {h["check"]} {h.get("file")}:{h.get("line")}  {h["evidence"]}'
                             + (f'   ({h["note"]})' if h.get('note') else '')
                             + (f'\n        files: {", ".join(h["files"])}' if h.get('files') else '')
                             + (f'\n        names: {", ".join(h["names"])}' if h.get('names') else ''))
    return '\n'.join(lines) or f'nothing for {what}'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('root', nargs='?', default='.')
    parser.add_argument('--out', help='output folder for scan.json (default: <root>/docs/mw-codereview-<date>)')
    parser.add_argument('--online', action='store_true', help='let the external scanners use the network')
    parser.add_argument('--resolve', action='store_true', help='resolve the JVM dependency tree with Gradle/Maven')
    parser.add_argument('--no-tools', action='store_true', help='skip the external scanners')
    parser.add_argument('--baseline', default='auto',
                        help='auto (default), none, or the scan.json of an earlier run to mark new and resolved hits')
    parser.add_argument('--examples', type=int, default=6, help='locations shown per check below high')
    parser.add_argument('--show', help='print one or more checks, endpoints, routes or tools from scan.json')
    parser.add_argument('--list-checks', action='store_true')
    args = parser.parse_args()

    if args.list_checks:
        for c in sorted(CHECKS.values(), key=lambda c: (RANK[c.severity], not c.security, c.id)):
            print(f'{c.id:<26} {c.severity:<8} {c.category:<16} {"S" if c.security else " "} {c.title}')
        return
    out_dir = Path(args.out or Path(args.root) / 'docs' / f'mw-codereview-{dt.date.today():%Y%m%d}')
    if args.show:
        print(show(out_dir.resolve(), args.show))
        return
    args.out = str(out_dir)
    if args.baseline == 'none':
        args.baseline = None
    result = scan(args)
    (out_dir / 'scan.json').write_text(json.dumps(result, indent=1, ensure_ascii=False, default=str), encoding='utf-8')
    print(digest(result, args.examples, out_dir.resolve()))


if __name__ == '__main__':
    main()
