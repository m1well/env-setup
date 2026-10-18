"""How the code is cut: Gradle/Maven modules of the backend, Nx projects of the frontend."""
from __future__ import annotations

import os
import re
from collections import Counter, defaultdict

from .core import Hits, Repo, define

define('ARCH-MODULE-TINY', 'Build module with three classes or fewer', 'low', 'architecture',
       'A merge candidate unless it has its own reason to exist: a separate data owner, consumers that must '
       'not see the rest, a comment in settings.gradle.kts that says why.')
define('ARCH-MODULE-HUGE', 'Build module past 80 classes and 3000 lines, or past 8000 lines', 'low', 'architecture',
       'Look at the package groups in the evidence: groups that never import each other are the split line.')
define('ARCH-MODULE-SHARED-DOMAIN', 'Domain code in the shared module', 'low', 'architecture',
       'Every module depends on common/shared, so every change there touches all of them. Controllers, services '
       'and entities belong to the feature that owns them.', rule='STR-8')
define('ARCH-MODULE-FANOUT', 'Module that imports six or more sibling modules', 'low', 'architecture',
       'Either an orchestrator that should say so in its name, or logic that sits in the wrong module.')
define('ARCH-MODULE-LAYERED', 'Modules cut by technical layer instead of by feature', 'low', 'architecture',
       'api/service/persistence modules mean every feature change touches every module. Cut by domain, keep '
       'the layers as packages inside.', rule='STR-8')
define('ARCH-ENTITY-SHARED', 'Module uses another module\'s entities or repositories', 'medium', 'boundary',
       'The other module\'s tables are now part of this module\'s contract. Go through its service API or an '
       'event instead.', rule='STR-8')
define('NX-NO-BOUNDARIES', 'Nx workspace without enforced module boundaries', 'medium', 'boundary',
       'Without @nx/enforce-module-boundaries and depConstraints every lib can import every other one.',
       rule='LAYER-13')
define('NX-NO-TYPE-RULES', 'Boundary rules cover scope but not type', 'low', 'boundary',
       'type:* tags exist, no constraint uses them - a ui lib can import a feature or data-access lib.',
       rule='LAYER-13')
define('NX-UNTAGGED', 'Nx projects without tags', 'low', 'boundary', 'Untagged projects slip through every rule.',
       rule='LAYER-13')
define('NX-LIB-TINY', 'Nx library with two files or fewer', 'low', 'architecture',
       'A lib costs a project.json, a tsconfig, a path alias and a build target. Merge it unless it is a '
       'deliberate public entry point (secondary entry, a lazy route).')
define('NX-LIB-HUGE', 'Nx library past 60 files or 40 components', 'low', 'architecture',
       'Split along the routes or the domain types it serves.')
define('NX-APP-FAT', 'Nx application that carries the code itself', 'low', 'architecture',
       'Apps should be thin shells: routes, providers, the shell layout. Features belong in libs.')
define('NX-CYCLE', 'Import cycle between Nx projects', 'medium', 'boundary',
       'Name both directions and the import that closes the cycle.', rule='LAYER-6')
define('NX-SHARED-SINGLE-USER', 'Shared library used by one scope only', 'low', 'architecture',
       'It is not shared. Moving it into its consumer\'s scope makes the shared surface honest.')
define('NX-SHARED-UPWARD', 'Shared library imports a feature library', 'medium', 'boundary',
       'shared depends on a domain now - every app that needs shared gets that domain too.', rule='LAYER-6')
define('NX-LIB-UNUSED', 'Nx library no other project imports', 'low', 'dead-code',
       'Dead, or only reached through a relative path - both are worth a look.')

SHARED_NAME = re.compile(r'^(common|commons|shared|core|util|utils|base|lib|libs|kernel|foundation)$', re.I)
LAYER_NAME = re.compile(r'^(api|web|rest|controller|controllers|service|services|domain|model|models|persistence|'
                        r'repository|repositories|infrastructure|infra|adapter|adapters|dto|dtos|entity|entities|'
                        r'dao|application|usecase|usecases)$', re.I)


def _build_root(repo: Repo, module: str) -> str:
    parts = [] if module == '.' else module.split('/')
    for i in range(len(parts), -1, -1):
        base = '/'.join(parts[:i]) or '.'
        prefix = '' if base == '.' else base + '/'
        if any(prefix + n in repo.files for n in ('settings.gradle.kts', 'settings.gradle')):
            return base
        pom = prefix + 'pom.xml'
        if pom in repo.files and '<modules>' in repo.source(pom).text:
            return base
    return module


def _module_of(rel: str, paths: list[str]) -> str | None:
    best = None
    for p in paths:
        prefix = '' if p == '.' else p + '/'
        if rel.startswith(prefix) and (best is None or len(p) > len(best) or best == '.'):
            best = p
    return best


def _scc(edges: dict[str, set[str]]) -> list[list[str]]:
    index, low, stack, on, out = {}, {}, [], set(), []

    def visit(v):
        index[v] = low[v] = len(index)
        stack.append(v)
        on.add(v)
        for w in edges.get(v, ()):
            if w not in index:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                out.append(sorted(comp))

    for v in list(edges):
        if v not in index:
            visit(v)
    return out


def _groups(packages: dict[str, set[str]]) -> list[list[str]]:
    """Package groups inside one module that never import each other."""
    parent = {p: p for p in packages}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for p, targets in packages.items():
        for t in targets:
            if t in parent:
                parent[find(p)] = find(t)
    out = defaultdict(list)
    for p in packages:
        out[find(p)].append(p)
    return sorted(out.values(), key=len, reverse=True)


def jvm(ctx) -> list[dict]:
    hits, repo = ctx.hits, ctx.repo
    paths = [m['path'] for m in ctx.stack['modules']]
    if not paths:
        return []
    owner = {}
    info = {p: {'path': p, 'build': _build_root(repo, p), 'types': 0, 'lines': 0, 'tests': 0,
                'stereotypes': Counter(), 'uses': {}, 'used_by': set(), 'app': False,
                'packages': defaultdict(int)} for p in paths}
    for j in ctx.main:
        mod = _module_of(j.rel, paths)
        if not mod:
            continue
        m = info[mod]
        top = [c for c in j.classes if c.owner is None]
        m['types'] += max(1, len(top))
        m['lines'] += sum(1 for line in j.src.code_lines if line.strip())
        m['stereotypes'][j.stereotype or 'other'] += 1
        m['app'] |= j.stereotype == 'app'
        m['packages'][j.package] += max(1, len(top))
        for c in top:
            owner[f'{j.package}.{c.name}'] = (mod, j.stereotype if c is j.cls else None)
    for s in ctx.tests:
        mod = _module_of(s.rel, paths)
        if mod:
            info[mod]['tests'] += 1
    pkg_owner = defaultdict(set)
    for fq, (mod, _) in owner.items():
        pkg_owner[fq.rsplit('.', 1)[0]].add(mod)

    shared_use = defaultdict(list)
    pkg_edges = {p: defaultdict(set) for p in paths}
    for j in ctx.main:
        mod = _module_of(j.rel, paths)
        if not mod:
            continue
        for imp in j.imports:
            target = owner.get(imp)
            if target:
                dst, stereo = target
            else:
                mods = pkg_owner.get(imp.rsplit('.', 1)[0]) or pkg_owner.get(imp)
                if not mods or len(mods) != 1:
                    continue
                dst, stereo = next(iter(mods)), None
            if dst == mod:
                dst_pkg = imp.rsplit('.', 1)[0]
                if dst_pkg != j.package:
                    pkg_edges[mod][j.package].add(dst_pkg)
                continue
            if info[dst]['build'] != info[mod]['build']:
                continue
            info[mod]['uses'].setdefault(dst, (j.rel, imp))
            info[dst]['used_by'].add(mod)
            if stereo in ('entity', 'repository') and not info[mod]['app']:
                shared_use[(mod, dst)].append((j, imp))

    builds = defaultdict(list)
    for m in info.values():
        builds[m['build']].append(m)
    for build, mods in builds.items():
        if len(mods) < 2:
            continue
        layered = [m['path'].split('/')[-1] for m in mods if LAYER_NAME.match(m['path'].split('/')[-1])]
        if len(layered) >= 2:
            hits.add('ARCH-MODULE-LAYERED', build if build != '.' else None, None,
                     f'build {build}: modules {", ".join(layered)} are named after layers')
        for m in mods:
            name = m['path'].split('/')[-1]
            if m['types'] <= 3 and not m['app']:
                users = sorted(u.split('/')[-1] for u in m['used_by'])
                hits.add('ARCH-MODULE-TINY', m['path'], None,
                         f'{name}: {m["types"]} classes, {m["lines"]} lines, used by '
                         + (', '.join(users) if users else 'no module'))
            if (m['types'] > 80 and m['lines'] > 3000) or m['lines'] > 8000:
                groups = _groups({p: set(t) for p, t in pkg_edges[m['path']].items()} |
                                 {p: set() for p in m['packages'] if p not in pkg_edges[m['path']]})
                sizes = [sum(m['packages'][p] for p in g) for g in groups]
                independent = [(g, s) for g, s in zip(groups, sizes) if s >= 10]
                hits.add('ARCH-MODULE-HUGE', m['path'], None,
                         f'{name}: {m["types"]} classes, {m["lines"]} lines'
                         + (f', {len(independent)} package groups that never import each other: '
                            + '; '.join(f'{os.path.commonprefix(g).rstrip(".").split(".")[-1] or g[0]} ({s})'
                                        for g, s in independent[:4]) if len(independent) > 1 else ''))
            st = m['stereotypes']
            domain = {k: st[k] for k in ('controller', 'service', 'entity', 'repository') if st.get(k)}
            if SHARED_NAME.match(name) and (domain or m['types'] > 40):
                hits.add('ARCH-MODULE-SHARED-DOMAIN', m['path'], None,
                         f'{name}: {m["types"]} classes, ' + (', '.join(f'{k} {v}' for k, v in domain.items())
                                                                or 'no stereotypes'))
            siblings = [u for u in m['uses'] if not info[u]['app'] and not SHARED_NAME.match(u.split('/')[-1])]
            if len(siblings) >= 6 and not m['app']:
                hits.add('ARCH-MODULE-FANOUT', m['path'], None,
                         f'{name} imports {len(siblings)} modules: ' + ', '.join(s.split('/')[-1] for s in sorted(siblings)))
    for (mod, dst), uses in shared_use.items():
        j, imp = uses[0]
        hits.add('ARCH-ENTITY-SHARED', j.rel, j.src.line_at(max(0, j.src.bare.find(imp))),
                 f'{mod.split("/")[-1]} imports {imp.split(".")[-1]} from {dst.split("/")[-1]}'
                 + (f' (+{len(uses) - 1} more imports)' if len(uses) > 1 else ''))
    return [{'path': m['path'], 'build': m['build'], 'types': m['types'], 'lines': m['lines'], 'tests': m['tests'],
             'app': m['app'], 'stereotypes': dict(m['stereotypes']), 'uses': sorted(m['uses']),
             'used_by': sorted(m['used_by'])} for m in info.values()]


IMPORT = re.compile(r'''(?:\bfrom\s+|\bimport\s*\(\s*)['"]([^'"]+)['"]''')


def _eslint(repo: Repo, prefix: str) -> str:
    texts = []
    for f in repo.files:
        if f.startswith(prefix) and re.search(r'(^|/)(eslint\.config\.[cm]?[jt]s|\.eslintrc(\.json|\.js|\.cjs)?)$', f) \
                and 'node_modules' not in f:
            texts.append(repo.source(f).text)
    return '\n'.join(texts)


def nx(w, hits: Hits) -> list[dict]:
    ws, repo = w.ws, w.repo
    if not ws['nx'] or not ws['projects']:
        return []
    prefix = w.prefix
    projects = []
    for p in ws['projects']:
        root = os.path.normpath(prefix + p['root']) if p['root'] not in ('', '.') else prefix.rstrip('/') or '.'
        projects.append({**p, 'root': root, 'files': [], 'components': 0, 'lines': 0, 'uses': {}, 'used_by': set()})
    projects.sort(key=lambda p: -len(p['root']))

    def project_of(rel: str):
        return next((p for p in projects if p['root'] != '.' and (rel + '/').startswith(p['root'] + '/')), None)

    comp_files = {c['file'] for c in w.comps if c['kind'] == 'component'}
    for rel in w.main_ts:
        p = project_of(rel)
        if p:
            p['files'].append(rel)
            p['components'] += rel in comp_files
            p['lines'] += sum(1 for line in w.repo.source(rel).code_lines if line.strip())
    alias_project = {}
    for alias, target in w.aliases.items():
        p = project_of(target)
        if p:
            alias_project[alias] = p
    for p in projects:
        for rel in p['files']:
            src = repo.source(rel)
            for m in IMPORT.finditer(src.code):
                spec = m.group(1)
                if spec.startswith('.'):
                    q = project_of(os.path.normpath(os.path.join(os.path.dirname(rel), spec)))
                else:
                    alias = max((a for a in alias_project if spec == a or spec.startswith(a + '/')), key=len, default=None)
                    q = alias_project.get(alias)
                if q is not None and q is not p:
                    p['uses'].setdefault(q['name'], (rel, src.line_at(m.start()), spec))
                    q['used_by'].add(p['name'])
    by_name = {p['name']: p for p in projects}

    eslint = _eslint(repo, prefix)
    rule = re.search(r'enforce-module-boundaries', eslint)
    tagged_rules = re.findall(r'sourceTag\s*["\']?\s*:\s*["\']([^"\']+)["\']', eslint)
    project_json = next((f for f in w.files if f.endswith('project.json')), None)
    if not rule or not [t for t in tagged_rules if t != '*']:
        hits.add('NX-NO-BOUNDARIES', next((f for f in w.files if re.search(r'eslint\.config|\.eslintrc', f)), project_json),
                 None, 'no @nx/enforce-module-boundaries rule' if not rule else 'depConstraints only for sourceTag "*"')
    tags = {t for p in projects for t in p.get('tags') or []}
    if any(t.startswith('type:') for t in tags) and rule and not any(t.startswith('type:') for t in tagged_rules):
        hits.add('NX-NO-TYPE-RULES', next((f for f in w.files if re.search(r'eslint\.config|\.eslintrc', f)), None), None,
                 f'type tags {", ".join(sorted(t for t in tags if t.startswith("type:")))}, constraints only on '
                 + ', '.join(sorted(set(tagged_rules))[:6]))
    untagged = [p for p in projects if not p.get('tags') and not p['name'].endswith('e2e')]
    if untagged and tags:
        hits.add('NX-UNTAGGED', untagged[0]['root'] + '/project.json', None,
                 f'{len(untagged)} of {len(projects)} projects: ' + ', '.join(p['name'] for p in untagged[:10]))

    libs = [p for p in projects if p['type'] == 'library']

    def scope(p):
        found = [t.split(':', 1)[1] for t in p.get('tags') or [] if t.startswith('scope:')]
        if found:
            return found[0]
        rel = p['root'][len(prefix):] if p['root'].startswith(prefix) else p['root']
        parts = rel.split('/')
        return parts[1] if len(parts) > 2 and parts[0] in ('libs', 'packages') else parts[0]

    def is_shared(p):
        return scope(p) == 'shared' or '/shared/' in '/' + p['root'] + '/'

    for p in libs:
        real = [f for f in p['files'] if not f.endswith(('/index.ts', '/public-api.ts', 'test-setup.ts'))]
        if len(real) <= 2:
            hits.add('NX-LIB-TINY', p['root'] + '/project.json', None,
                     f'{p["name"]}: {len(real)} file(s), used by ' + (', '.join(sorted(p['used_by'])[:5]) or 'nobody'))
        if len(real) > 60 or p['components'] > 40:
            hits.add('NX-LIB-HUGE', p['root'] + '/project.json', None,
                     f'{p["name"]}: {len(real)} files, {p["components"]} components, {p["lines"]} lines')
        if not p['used_by'] and not p['name'].endswith(('e2e', 'testing')):
            hits.add('NX-LIB-UNUSED', p['root'] + '/project.json', None, f'{p["name"]}: no project imports it')
        if is_shared(p):
            users = {scope(by_name[u]) for u in p['used_by'] if u in by_name and not is_shared(by_name[u])}
            if len(users) == 1 and len(p['used_by']) >= 1 and \
                    not any(is_shared(by_name[u]) for u in p['used_by'] if u in by_name):
                hits.add('NX-SHARED-SINGLE-USER', p['root'] + '/project.json', None,
                         f'{p["name"]}: imported only by scope {next(iter(users))} ({", ".join(sorted(p["used_by"])[:5])})')
            for q_name, (rel, line, spec) in p['uses'].items():
                q = by_name[q_name]
                if q['type'] == 'library' and not is_shared(q):
                    hits.add('NX-SHARED-UPWARD', rel, line, f'{p["name"]} imports {q_name} ({spec})')
    if libs:
        for p in projects:
            if p['type'] == 'application' and p['components'] > 25:
                hits.add('NX-APP-FAT', p['root'] + '/project.json', None,
                         f'{p["name"]}: {p["components"]} components, {len(p["files"])} files in the app itself')
    for comp in _scc({p['name']: set(p['uses']) for p in projects}):
        a = by_name[comp[0]]
        b_name = next(n for n in a['uses'] if n in comp)
        rel, line, spec = a['uses'][b_name]
        hits.add('NX-CYCLE', rel, line, f'cycle {" <-> ".join(comp)}: {a["name"]} imports {spec}')
    return [{'name': p['name'], 'root': p['root'], 'type': p['type'], 'tags': p.get('tags') or [],
             'files': len(p['files']), 'components': p['components'], 'lines': p['lines'],
             'uses': sorted(p['uses']), 'used_by': sorted(p['used_by'])} for p in projects]
