#!/usr/bin/env python3
"""mw-codereview scanner: finds what is worth reviewing in a Spring Boot and/or Angular repository.

    python3 scan.py [root] [--out DIR] [--online] [--resolve] [--baseline auto|none|OLD/scan.json]
                    [--diff [BASE] | --focus DIR,DIR]
    python3 scan.py --out DIR --show SB-SQL-CONCAT,NG-DOM-XSS | endpoints | routes | modules | projects | calls |
                                     entities | privacy | authz | hotspots | keycloak | owasp | tools |
                                     changes | findings | decided
    python3 scan.py --out DIR --decide h12,h40,SB-NO-VALID discarded|accepted "reason"
    python3 scan.py [root] --cat FILE[:FROM-TO]
    python3 scan.py --list-checks

--online   lets npm audit, osv-scanner, trivy and semgrep fetch their databases and rules
--resolve  asks Gradle or Maven for the resolved runtime classpath (runs the build tool, takes a while)
--baseline auto compares with the newest earlier docs/mw-codereview-*/scan.json and carries the
           findings and decisions of the findings.json next to it
--diff     lists only hits in files changed against BASE (default: origin/HEAD, main or master), incl.
           uncommitted and untracked files; --focus does the same for directories
--decide   records a verdict for hits (ids or check ids) in DIR/findings.json; the next run carries it
--cat      prints a file with every secret-like value masked - the only safe way to read config files
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

from lib import (angular, authz, calls, correctness, deps, detect, keycloak, modules, privacy,  # noqa: E402
                 repo as repo_checks, reuse, schema, spring, testgaps, tools, ux)
from lib.core import CHECKS, OWN_OUTPUT, SEVERITIES, Hits, Repo, is_test_path  # noqa: E402

RANK = {s: i for i, s in enumerate(SEVERITIES)}


def _key(hit: dict) -> str:
    evidence = re.sub(r'\d+', '#', hit.get('evidence') or '')
    return hashlib.sha1(f'{hit["check"]}|{hit.get("file")}|{evidence}'.encode()).hexdigest()[:16]


SECURITY_FILE = re.compile(r'(Security|Auth|Jwt|Token|Csrf|Cors|Filter|Interceptor|Guard|Keycloak|Realm|Login|Session|'
                           r'Permission|Access|Role|Tenant|WebConfig|WebMvcConfig)\w*\.(kt|java|ts)$|'
                           r'\.(guard|interceptor)\.ts$|(^|/)application[\w.-]*\.(ya?ml|properties)$|realm[\w.-]*\.json$|'
                           r'(^|/)[\w.-]*nginx[\w.-]*\.conf$', re.I)
SOURCE_EXT = ('.kt', '.java', '.ts', '.html')


def _base(repo: Repo, wanted: str | None) -> str | None:
    head = repo._git('symbolic-ref', '--quiet', '--short', 'refs/remotes/origin/HEAD').strip()
    for ref in ([wanted] if wanted and wanted != 'auto' else [head, 'origin/main', 'origin/master', 'main', 'master']):
        if ref and repo._git('rev-parse', '--verify', '--quiet', ref + '^{commit}').strip():
            return ref
    return None


def changes(repo: Repo, base: str) -> dict[str, str]:
    """Files changed against the merge base with `base`, incl. uncommitted and untracked ones: path -> A|M|D|R."""
    point = repo._git('merge-base', base, 'HEAD').strip() or base
    out = {}
    for line in repo._git('diff', '--name-status', '--relative', '-M', point).splitlines():
        parts = line.split('\t')
        if len(parts) >= 2 and not OWN_OUTPUT.search(parts[-1]):
            out[parts[-1]] = parts[0][0]
    for f in repo.files:
        if repo.is_tracked(f) is False:
            out.setdefault(f, 'A')
    return out


def _file_hashes(repo: Repo) -> dict[str, str]:
    return {f: hashlib.sha1(repo.source(f).text.encode()).hexdigest()[:12] for f in repo.files}


def _since(old: dict, now: dict[str, str]) -> dict:
    before = old.get('meta', {}).get('file_hashes')
    if not before:
        return {}
    changed = sorted(f for f, h in now.items() if f in before and before[f] != h)
    added = sorted(f for f in now if f not in before)
    removed = sorted(f for f in before if f not in now)
    dirs = Counter(os.path.dirname(f) for f in changed + added if f.endswith(SOURCE_EXT))
    return {'changed': len(changed), 'added': len(added), 'removed': len(removed),
            'dirs': [d for d, _ in dirs.most_common()]}


def _anchor_line(root: Path, finding: dict) -> tuple[str, int | None]:
    rel, anchor = finding.get('file'), (finding.get('anchor') or '').strip()
    if not rel or not anchor:
        return 'no anchor - verify by hand', finding.get('line')
    path = root / rel
    if not path.is_file():
        return 'file gone - verify fixed', None
    at = [i for i, line in enumerate(path.read_text(encoding='utf-8', errors='replace').split('\n'), 1) if anchor in line]
    if not at:
        return 'anchor gone - verify fixed', None
    old = finding.get('line') or at[0]
    new = min(at, key=lambda i: abs(i - old))
    return ('still there' if new == old else f'moved {old} -> {new}'), new


def carry(root: Path, baseline: str, hits: list[dict]) -> dict:
    """Findings and decisions of the findings.json next to the baseline, re-anchored on today's tree."""
    prev = Path(baseline).parent / 'findings.json'
    if not prev.is_file():
        return {}
    data = json.loads(prev.read_text(encoding='utf-8'))
    keys = {h['key'] for h in hits}
    decisions = {d['key']: d for d in data.get('decisions', []) if d.get('key') in keys}
    for h in hits:
        if h['key'] in decisions:
            h['decided'] = {k: decisions[h['key']][k] for k in ('verdict', 'reason', 'date') if k in decisions[h['key']]}
    findings = []
    for f in data.get('findings', []):
        if f.get('status') == 'fixed':
            continue
        f = dict(f)
        f['recheck'], f['line'] = _anchor_line(root, f)
        if f.get('hits') and not keys & set(f['hits']) and f['recheck'] == 'no anchor - verify by hand':
            f['recheck'] = 'its hits are gone - verify fixed'
        findings.append(f)
    return {'from': data.get('date'), 'file': str(prev), 'findings': findings, 'decisions': list(decisions.values()),
            'reviewed_dirs': data.get('reviewed_dirs', [])}


def _findings_skeleton(out: Path, result: dict):
    target = out / 'findings.json'
    if target.exists():
        return
    carried = result.get('carried') or {}
    target.write_text(json.dumps({
        'date': result['meta']['generated'], 'scope': result['meta'].get('focus', {}).get('label', 'full'),
        'reviewed_dirs': [], 'findings': carried.get('findings', []), 'decisions': carried.get('decisions', []),
    }, indent=1, ensure_ascii=False), encoding='utf-8')


def decide(out_dir: Path, ids: str, verdict: str, reason: str) -> str:
    if verdict not in ('discarded', 'accepted'):
        return 'verdict must be discarded or accepted'
    data = json.loads((out_dir / 'scan.json').read_text(encoding='utf-8'))
    wanted = set(ids.split(','))
    chosen = [h for h in data['hits'] if h['id'] in wanted or h['check'] in wanted]
    target = out_dir / 'findings.json'
    book = json.loads(target.read_text(encoding='utf-8')) if target.exists() else {
        'date': data['meta']['generated'], 'scope': 'full', 'reviewed_dirs': [], 'findings': [], 'decisions': []}
    by_key = {d['key']: d for d in book['decisions']}
    for h in chosen:
        by_key[h['key']] = {'key': h['key'], 'check': h['check'], 'file': h.get('file'), 'line': h.get('line'),
                            'verdict': verdict, 'reason': reason, 'date': data['meta']['generated']}
    book['decisions'] = list(by_key.values())
    target.write_text(json.dumps(book, indent=1, ensure_ascii=False), encoding='utf-8')
    return f'{len(chosen)} hit(s) {verdict}, {len(book["decisions"])} decisions in {target}'


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
        correctness.run(ctx, sp.get('entities'))
        sp['tests'] = testgaps.backend(ctx, sp['modules'])
        inventory['spring'] = sp
        inventory['authz'] = authz.run(ctx, sp.get('entities'))
        for e, copy in zip(ctx.endpoints, sp['endpoints']):
            if e.get('covered_by'):
                copy['covered_by'] = e['covered_by']
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
    personal = privacy.run(repo, hits, ctx, workspaces, (inventory.get('spring') or {}).get('calls'))
    if personal:
        inventory['privacy'] = personal
    inventory['reuse'] = reuse.run(repo, hits, [c for w in workspaces for c in w.comps], ctx.main if ctx else [])
    repo_checks.run(repo, hits, stacks)
    versions = deps.run(repo, stacks, hits, inventory, resolve=args.resolve)
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    tool_status = {} if args.no_tools else tools.run(repo, hits, stacks, args.online,
                                                        Path(tempfile.mkdtemp(prefix='mw-codereview-')),
                                                        out=out, versions=versions)

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

    hashes = _file_hashes(repo)
    resolved, since, carried = [], {}, {}
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
        since = _since(old, hashes)
        since['date'] = old.get('meta', {}).get('generated')
        carried = carry(root, args.baseline, unique)

    focus, changed, base = {}, {}, None
    if repo.git:
        base = _base(repo, args.diff)
        changed = changes(repo, base) if base else {}
    if args.diff:
        files = {f for f, s in changed.items() if s != 'D'}
        focus = {'label': f'diff vs {base}' if base else 'diff (no base branch found)', 'files': len(files)}
    elif args.focus:
        dirs = [d.strip().strip('/') for d in args.focus.split(',') if d.strip()]
        files = {f for f in repo.files if any(f == d or f.startswith(d + '/') for d in dirs)}
        focus = {'label': 'paths ' + ', '.join(dirs), 'files': len(files)}
    if focus:
        for h in unique:
            h['focus'] = h.get('file') in files or any(f in files for f in h.get('files') or [])

    spring_stack = stacks['spring']
    return {
        'meta': {'root': str(root), 'generated': dt.date.today().isoformat(), 'scanner': 'mw-codereview 1',
                 'seconds': round(time.time() - started, 1), 'git': repo.git, 'files': len(repo.files),
                 'untracked': sum(1 for f in repo.files if repo.is_tracked(f) is False),
                 'online': args.online, 'resolve': args.resolve, 'baseline': args.baseline,
                 'version_data': deps.DATA['checked'], 'tree': hashlib.sha1(json.dumps(hashes, sort_keys=True)
                                                                            .encode()).hexdigest()[:16],
                 'file_hashes': hashes, 'since_baseline': since, 'focus': focus,
                 'changes': {'base': base, 'files': changed} if changed else {}},
        'carried': carried,
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
                     + (', SSR' if ws['ssr'] else '')
                     + f', {ws.get("zone_detail") or ("zoneless" if ws["zoneless"] else "zone.js")}')
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
        if front and not sp:
            out.append(f'calls    {ng["path"]}: {len(front)} HTTP calls - no backend in this repo, not matchable')
        elif front:
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
    az = result['inventory'].get('authz')
    if az:
        out.append('authz    ' + (', '.join(f'{c["concept"]} {c["count"]}' for c in az['concepts'])
                                  or 'no authorization concept beyond URL rules'))
        t = az['tenancy']
        if t['tenant_app']:
            out.append(f'         tenant: {", ".join(t["model"]) or "source not found"}; '
                       f'{", ".join(t["isolation"]) or "no isolation found"}'
                       + (f'; context {", ".join(dict.fromkeys(h.split(" (")[0] for h in t["holders"]))}'
                          if t['holders'] else ''))
        if az['object_access']:
            obj = az['object_access']
            out.append(f'         {len(obj)} endpoints with a path id and no object check found '
                       f'({sum(1 for e in obj if e.get("caller"))} take the caller, '
                       f'{sum(1 for e in obj if e.get("admin"))} admin-only) - IDOR sample: --show authz')
        if az.get('interceptors'):
            out.append('         interceptors: ' + ', '.join(f'{i["class"]} covers {i["endpoints"]}'
                                                       for i in az['interceptors']))
    pv = result['inventory'].get('privacy')
    if pv:
        if not pv.get('need'):
            out.append(f'privacy  no schema in this repo - profile from {pv.get("basis") or "forms only"}, '
                       'protection need and score not computable')
        if pv.get('need'):
            out.append(f'privacy  protection need {pv["need"]} ({pv["decided_by"] or "identifying data only"}) - '
                       f'score {pv["score"]}/100, {pv["columns"]["personal"]} of {pv["columns"]["total"]} columns '
                       f'personal in {pv["tables"]["personal"]} of {pv["tables"]["total"]} tables')
            out.append('         ' + ', '.join(f'{k.replace("_", " ")} {v}' for k, v in pv['tiers'].items())
                       + '; subjects ' + ', '.join(f'{k} {len(v)}' for k, v in pv['subjects'].items())
                       + f'; field encryption {len(pv["encrypted_columns"]) or "none"}'
                       + f'; cleanup jobs {len(pv["retention_jobs"]) or "none"}'
                       + (f' reaching {sum(1 for t in pv.get("map", []) if t.get("cleanup"))} personal tables'
                          if pv['retention_jobs'] else ''))
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


def _context_lines(result: dict) -> list[str]:
    meta, out = result['meta'], []
    ch = meta.get('changes') or {}
    files = ch.get('files') or {}
    if files:
        chain_files = {c['file'] for c in (result['inventory'].get('spring') or {}).get('chains', [])}
        sec = [f for f in sorted(files) if (SECURITY_FILE.search(f) and not is_test_path(f)) or f in chain_files]
        kinds = ', '.join(f'{k} {v}' for k, v in sorted(Counter(files.values()).items()))
        out.append(f'changes  vs {ch["base"]}: {len(files)} files ({kinds})' + (
            '; security-relevant: ' + ', '.join(f'{os.path.basename(f)} ({files[f]})' for f in sec[:12])
            + (f' ... (+{len(sec) - 12})' if len(sec) > 12 else '') if sec else ''))
    since = meta.get('since_baseline') or {}
    if 'changed' in since:
        if not since['changed'] + since['added'] + since['removed']:
            out.append(f'baseline {since["date"]}: code unchanged since then - carry the findings over and spend '
                       '/code-review on a directory no earlier run reviewed')
        else:
            out.append(f'baseline {since["date"]}: {since["changed"]} files changed, {since["added"]} added, '
                       f'{since["removed"]} removed' + (f' - new code in {", ".join(since["dirs"][:5])}'
                                                       if since['dirs'] else ''))
    carried = result.get('carried') or {}
    if carried:
        checks = Counter(f['recheck'].split(' - ')[0] for f in carried['findings'])
        out.append(f'carried  from {carried["from"]}: {len(carried["findings"])} open findings'
                   + (f' ({", ".join(f"{k} {v}" for k, v in checks.most_common())})' if checks else '')
                   + f', {len(carried["decisions"])} decided hits'
                   + (f', /code-review ran on {", ".join(carried["reviewed_dirs"])}' if carried['reviewed_dirs'] else '')
                   + ' - --show findings, --show decided')
    if meta.get('focus'):
        inside = sum(1 for h in result['hits'] if h.get('focus'))
        out.append(f'focus    {meta["focus"]["label"]}: {meta["focus"]["files"]} files, {inside} of {len(result["hits"])} '
                   'hits inside - only those are listed below, the rest: --show <CHECK>')
    return out


def _vuln_lines(hits: list[dict]) -> list[str]:
    groups = defaultdict(list)
    for h in hits:
        if h.get('package'):
            groups[h['package'].lower()].append(h)
    if not groups:
        return []
    sources = Counter(h['check'] for g in groups.values() for h in g)
    out = [f'vulns    {len(groups)} packages in {sum(sources.values())} hits ('
           + ', '.join(f'{k} {v}' for k, v in sources.most_common()) + ') - one line per package:']
    ranked = sorted(groups.values(), key=lambda g: (min(RANK[h['severity']] for h in g), -len(g)))
    for g in ranked[:25]:
        g = sorted(g, key=lambda h: RANK[h['severity']])
        versions = '/'.join(sorted({h['version'] for h in g if h.get('version')}))
        advisories = {h['advisory'] for h in g if h.get('advisory')}
        note = next((h['note'] for h in g if h.get('note')), '')
        n = len(advisories) or len(g)
        out.append(f'   [{g[0]["severity"]}] {g[0]["package"]} {versions}  {n} advisor{"y" if n == 1 else "ies"}  '
                   + ', '.join(f'{k} {v}' for k, v in Counter(h['check'] for h in g).most_common())
                   + f'  {g[0]["id"]}' + (f'   ({note})' if note else ''))
    if len(ranked) > 25:
        out.append(f'   ... {len(ranked) - 25} more packages')
    return out


def _secret_lines(hits: list[dict]) -> list[str]:
    groups = defaultdict(list)
    for h in hits:
        if h.get('secret'):
            groups[h['secret']].append(h)
    if not groups:
        return []
    found = sorted({h['check'] for g in groups.values() for h in g})
    out = [f'secrets  {len(groups)} distinct values in {sum(map(len, groups.values()))} hits ({", ".join(found)}):']
    for value, g in sorted(groups.items(), key=lambda kv: (min(RANK[h['severity']] for h in kv[1]), -len(kv[1])))[:15]:
        where = sorted({f'{h["file"]}:{h["line"]}' if h.get('line') else h.get('file') or '-' for h in g})
        note = next((h['note'] for h in g if h.get('note')), '')
        out.append(f'   {value}  {" ".join(h["id"] for h in g)}  {where[0]}'
                   + (f' (+{len(where) - 1} more)' if len(where) > 1 else '') + (f'   ({note})' if note else ''))
    if len(groups) > 15:
        out.append(f'   ... {len(groups) - 15} more values')
    return out


def digest(result: dict, examples: int, out_dir: Path) -> str:
    hits = result['hits']
    shown = [h for h in hits if h.get('focus', True)]
    meta = result['meta']
    lines = [f'mw-codereview scan  {meta["generated"]}  {meta["root"]}  '
             f'({meta["seconds"]}s, version data from {meta["version_data"]})']
    for s in _stack_line(result):
        lines.append('stack    ' + s)
    ext = ', '.join(f'{k} {v}' for k, v in result['files_by_ext'].items())
    listing = ('git ls-files' + (f' incl. {meta["untracked"]} untracked' if meta.get('untracked') else '')
               if meta['git'] else 'walk')
    lines.append(f'scope    {meta["files"]} files ({listing}): {ext}')
    if result['tools']:
        parts = []
        for name, st in result['tools'].items():
            text = f'{name} {st["status"]}'
            if 'findings' in st:
                text += f' ({st["findings"]}{", " + st["mode"] if st.get("mode") else ""})'
            if st.get('note'):
                text += f' - {st["note"]}'
            if st.get('install'):
                text += f' [{st["install"]}]'
            parts.append(text)
        lines.append('tools    ' + ' | '.join(parts))
    if result['versions'].get('spring', {}).get('resolve'):
        lines.append('resolve  ' + result['versions']['spring']['resolve'])
    lines += _context_lines(result)
    lines += _inventory_lines(result)
    lines += _vuln_lines(shown)
    lines += _secret_lines(shown)
    sev = Counter(h['severity'] for h in shown)
    security = sum(1 for h in shown if CHECKS[h['check']].security)
    summary = ' | '.join(f'{s} {sev.get(s, 0)}' for s in SEVERITIES)
    flags = []
    if meta['baseline']:
        new = sum(1 for h in shown if h.get('new'))
        flags.append(f'new {new}, known {len(shown) - new}, resolved since baseline {len(result["resolved"])}')
    decided = sum(1 for h in shown if h.get('decided'))
    if decided:
        flags.append(f'decided earlier {decided}')
    lines.append(f'hits     {summary}' + (f'   [{"; ".join(flags)}]' if flags else '')
                 + f'   ({security} of {len(shown)} security)')
    lines.append('')

    groups = defaultdict(list)
    for h in shown:
        groups[(h['severity'], h['check'])].append(h)
    for (severity, check), group in sorted(groups.items(), key=lambda kv: _order(kv[1][0])):
        spec = CHECKS[check]
        tag = ' security' if spec.security else ''
        rule = ' '.join(x for x in (spec.rule, spec.owasp and f'OWASP {spec.owasp}', spec.gdpr and f'GDPR {spec.gdpr}')
                        if x)
        lines.append(f'[{severity}] {check}  {spec.title}  x{len(group)}{tag}' + (f'  ({rule})' if rule else ''))
        if all(h.get('package') for h in group):
            lines.append('         grouped per package under vulns')
            continue
        open_ = [h for h in group if not h.get('decided')]
        limit = max(examples, 15) if severity in ('critical', 'high') else examples
        for h in open_[:limit]:
            where = f'{h["file"]}:{h["line"]}' if h.get('line') else (h.get('file') or '-')
            flags = ''.join(f' [{f}]' for f in ('test', 'new', 'ignored') if h.get(f)) + (' [history]' if h.get('history') else '')
            note = f'   ({h["note"]})' if h.get('note') else ''
            lines.append(f'   {h["id"]:>5} {where}{flags}  {h["evidence"]}{note}')
        if len(open_) > limit:
            lines.append(f'         ... {len(open_) - limit} more: --show {check}')
        verdicts = Counter((h['decided'].get('verdict'), h['decided'].get('date'), h['decided'].get('reason', ''))
                           for h in group if h.get('decided'))
        for (verdict, date, reason), n in verdicts.most_common(3):
            lines.append(f'         {n} {verdict} on {date}: {reason[:120]}')
        if spec.verify and severity in ('critical', 'high', 'medium') and open_:
            lines.append(f'         verify: {spec.verify}')
    lines.append('')
    lines.append(f'full result: {out_dir / "scan.json"}')
    lines.append(f'one check:   python3 {Path(__file__).resolve()} --out {out_dir} --show <CHECK|endpoints|routes|modules|'
                 'projects|calls|entities|privacy|authz|hotspots|keycloak|owasp|tools|changes|findings|decided>')
    return '\n'.join(lines)


def show(out_dir: Path, what: str) -> str:
    data = json.loads((out_dir / 'scan.json').read_text(encoding='utf-8'))
    lines = []
    if what == 'endpoints':
        for e in (data['inventory'].get('spring') or {}).get('endpoints', []):
            auth = ', '.join(e['auth_text'] or e['auth'] or e['class_auth']) or '-'
            lines.append(f'{e["http"]:<6} {e["path"]:<55} {e["controller"]}.{e["method"]}  url={e.get("url_rule") or "-"}'
                         f'  method={auth}' + (f'  covered by {", ".join(e["covered_by"])}' if e.get('covered_by') else '')
                         + f'  {e["file"]}:{e["line"]}')
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
        sp = data['inventory'].get('spring')
        for c in (sp or {}).get('calls', []):
            flags = ' '.join(f for f in ('tx', 'loop', 'retry', 'per_request') if c.get(f))
            lines.append(f'{c["kind"]:<11} {c["verb"]:<10} {c["target"] or "?":<45} {c["where"]}  {c["file"]}:{c["line"]}'
                         + (f'  host {c["host"]}' if c.get('host') else '') + (f'  [{flags}]' if flags else ''))
        for ng in data['inventory'].get('angular') or []:
            front = ng.get('calls') or []
            if front and not sp:
                targets = Counter(c['target'].split('?')[0] for c in front)
                lines.append(f'front-http  {ng["path"]}: {len(front)} calls to {len(targets)} paths - no backend in this '
                             'repo, nothing to match')
                continue
            for c in front:
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
                         f'  cleanup {t.get("cleanup") or "-"}  {cols}  {t["file"] or ""}')
        for h in pv.get('hubs', []):
            how = 'joinable by value, no foreign key' if h.get('by') == 'name' else 'one join'
            lines.append(f'hub       {h["table"]}: {how} reaches {", ".join(h["reached"])} - {", ".join(h["categories"])}')
        for r in pv.get('recipients', []):
            seat = 'seat unknown' if r['seat'] == 'unknown' else f'{r["seat"]} company'
            lines.append(f'recipient {r["name"]} ({r["kind"]}, {seat}){" " + r["host"] if r.get("host") else ""}: '
                         f'{", ".join(r["where"])}')
        for j in pv.get('retention_jobs', []):
            lines.append(f'cleanup   {j}')
        for f in pv.get('forms', []):
            lines.append(f'form      {f["file"]}: {", ".join(f["fields"])}')
    elif what == 'authz':
        az = data['inventory'].get('authz') or {}
        for c in az.get('concepts', []):
            lines.append(f'concept   {c["concept"]:<14} {c["count"]:>4}  {c["signal"]:<42} first {c["where"]}'
                         + (f'  converter {c["converter"] or "none"}' if 'converter' in c else ''))
        t = az.get('tenancy') or {}
        lines.append(f'tenancy   tenant app {"yes" if t.get("tenant_app") else "no"}, {t.get("tenant_tables", 0)} tables '
                     'with a tenant column')
        for key in ('model', 'isolation', 'holders'):
            lines += [f'{key:<9} {v}' for v in t.get(key) or []]
        if az.get('hibernate'):
            lines.append(f'hibernate {az["hibernate"]}')
        for i in az.get('interceptors', []):
            lines.append(f'interceptor {i["class"]} covers {i["endpoints"]} endpoints  include {", ".join(i["include"]) or "-"}'
                         f'  exclude {", ".join(i["exclude"]) or "-"}  {i["where"]}')
        for e in az.get('object_access', []):
            flags = ''.join(f' [{f}]' for f in ('caller', 'admin') if e.get(f))
            lines.append(f'object    {e["http"]:<6} {e["path"]:<55} {e["handler"]}  url={e["rule"]}{flags}  {e["where"]}')
    elif what == 'hotspots':
        weight = {'critical': 8, 'high': 4, 'medium': 2, 'low': 1}
        meta, sp = data['meta'], data['inventory'].get('spring') or {}
        sources = [f for f in meta.get('file_hashes') or {} if f.endswith(SOURCE_EXT) and not is_test_path(f)]
        tags = defaultdict(set)
        for f in sources:
            if SECURITY_FILE.search(f):
                tags[os.path.dirname(f)].add('security')
        for c in sp.get('chains', []):
            tags[os.path.dirname(c['file'])].add('security')
        for e in sp.get('endpoints', []):
            if e.get('url_rule') in ('permitAll', 'anonymous'):
                tags[os.path.dirname(e['file'])].add('public')
        entity_file = {e['table']: e['file'] for e in sp.get('entities', [])}
        for t in (data['inventory'].get('privacy') or {}).get('map', []):
            if t['need'] in ('high', 'very high') and t['table'] in entity_file:
                tags[os.path.dirname(entity_file[t['table']])].add('pii')
        for d in (meta.get('since_baseline') or {}).get('dirs', []):
            tags[d].add('new code')
        reviewed = (data.get('carried') or {}).get('reviewed_dirs') or []
        dirs = defaultdict(lambda: {'score': 0, 'checks': Counter()})
        for h in data['hits']:
            f = h.get('file') or ''
            if h.get('test') or h.get('decided') or not f.endswith(SOURCE_EXT) or h.get('focus') is False:
                continue
            d = dirs[os.path.dirname(f)]
            d['score'] += (weight[h['severity']] + (2 if data['checks'][h['check']]['security'] else 0)) * (
                2 if h.get('new') else 1)
            d['checks'][h['check']] += 1
        sizes = Counter(os.path.dirname(f) for f in sources)
        ranked = []
        for path, d in dirs.items():
            mark = set(tags.get(path, ()))
            if 'new code' not in mark and any(path == r or path.startswith(r.rstrip('/') + '/') for r in reviewed):
                mark.add('reviewed')
            factor = 1.5 ** len(mark - {'reviewed'}) * (0.5 if 'reviewed' in mark else 1)
            ranked.append((round(d['score'] * factor), path, d, mark))
        for score, path, d, mark in sorted(ranked, key=lambda r: -r[0])[:12]:
            lines.append(f'{score:>4}  {path:<70} {sizes.get(path, 0):>3} files  '
                         + ', '.join(f'{k} {v}' for k, v in d['checks'].most_common(4))
                         + (f'  [{", ".join(sorted(mark))}]' if mark else ''))
        if lines:
            lines.append(f'{len(sources)} source files outside tests; decided hits do not count, new hits count double')
    elif what == 'changes':
        ch = data['meta'].get('changes') or {}
        for f, s in sorted((ch.get('files') or {}).items()):
            lines.append(f'{s}  {f}' + ('  [security]' if SECURITY_FILE.search(f) else ''))
    elif what == 'findings':
        c = data.get('carried') or {}
        for f in c.get('findings', []):
            lines.append(f'{f.get("id", "?"):<4} {f.get("priority", "?")} {f.get("severity", "?"):<8} '
                         f'{(f.get("title") or "")[:70]:<70} {f.get("file") or "-"}:{f.get("line") or "-"}  '
                         f'since {f.get("first_seen") or c.get("from")}  {f["recheck"]}')
    elif what == 'decided':
        for h in data['hits']:
            if h.get('decided'):
                d = h['decided']
                lines.append(f'{h["id"]:>5} {h["check"]} {h.get("file")}:{h.get("line")}  {d.get("verdict")} '
                             f'{d.get("date")}: {d.get("reason")}')
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
    parser.add_argument('--out', help='output folder for scan.json (default: <root>/docs/mw-codereview-<date>, '
                                      'with --diff or --focus a folder in the temp directory)')
    parser.add_argument('--online', action='store_true', help='let the external scanners use the network')
    parser.add_argument('--resolve', action='store_true', help='resolve the JVM dependency tree with Gradle/Maven')
    parser.add_argument('--no-tools', action='store_true', help='skip the external scanners')
    parser.add_argument('--baseline', default='auto',
                        help='auto (default), none, or the scan.json of an earlier run to mark new and resolved hits')
    parser.add_argument('--examples', type=int, default=6, help='locations shown per check below high')
    parser.add_argument('--show', help='print one or more checks, endpoints, routes or tools from scan.json')
    parser.add_argument('--diff', nargs='?', const='auto', metavar='BASE',
                        help='list only hits in files changed against BASE (default origin/HEAD, main or master)')
    parser.add_argument('--focus', metavar='DIR,DIR', help='list only hits in these directories')
    parser.add_argument('--decide', nargs=3, metavar=('IDS', 'VERDICT', 'REASON'),
                        help='record discarded|accepted for hit ids or check ids in --out/findings.json')
    parser.add_argument('--cat', metavar='FILE[:FROM-TO]', help='print a file with secret values masked')
    parser.add_argument('--list-checks', action='store_true')
    args = parser.parse_args()

    if args.list_checks:
        for c in sorted(CHECKS.values(), key=lambda c: (RANK[c.severity], not c.security, c.id)):
            print(f'{c.id:<26} {c.severity:<8} {c.category:<16} {"S" if c.security else " "} {c.title}')
        return
    if args.cat:
        m = re.match(r'^(.*?)(?::(\d+)(?:-(\d+))?)?$', args.cat)
        print(repo_checks.cat(Path(args.root).resolve(), m.group(1), int(m.group(2)) if m.group(2) else None,
                              int(m.group(3)) if m.group(3) else None))
        return
    session = Path(tempfile.gettempdir()) / f'mw-codereview-{Path(args.root).resolve().name}-{dt.date.today():%Y%m%d}'
    out_dir = Path(args.out or (session if args.diff or args.focus else
                                Path(args.root) / 'docs' / f'mw-codereview-{dt.date.today():%Y%m%d}'))
    if args.show:
        print(show(out_dir.resolve(), args.show))
        return
    if args.decide:
        print(decide(out_dir.resolve(), *args.decide))
        return
    args.out = str(out_dir)
    if args.baseline == 'none':
        args.baseline = None
    result = scan(args)
    (out_dir / 'scan.json').write_text(json.dumps(result, indent=1, ensure_ascii=False, default=str), encoding='utf-8')
    _findings_skeleton(out_dir, result)
    print(digest(result, args.examples, out_dir.resolve()))


if __name__ == '__main__':
    main()
