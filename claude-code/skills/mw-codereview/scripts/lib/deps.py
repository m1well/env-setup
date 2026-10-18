"""Versions against support lines and known-vulnerable floors, optionally with resolved Gradle/Maven trees."""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
from pathlib import Path

from .core import Hits, Repo, define, version_tuple

DATA = json.loads((Path(__file__).resolve().parent.parent / 'data' / 'versions.json').read_text(encoding='utf-8'))

define('DEPS-BOOT-EOL', 'Spring Boot line out of OSS support', 'high', 'supply-chain',
       'No more public security fixes for Boot, Framework and Security on this line.', security=True, owasp='A03')
define('DEPS-BOOT-PATCH', 'Spring Boot behind the latest patch of its line', 'medium', 'supply-chain',
       'Every Boot patch carries the managed Framework, Security, Tomcat and Jackson fixes.', security=True,
       owasp='A03')
define('DEPS-BOOT-CVE', 'Spring Boot version inside a CVE range', 'high', 'supply-chain',
       'Check whether the app has the vulnerable shape - it is in the evidence.', security=True, owasp='A03')
define('DEPS-BOOT-MANAGED', 'Boot manages a transitive version below its fix', 'medium', 'supply-chain',
       'Even the current Boot patch can lag behind Tomcat or Jackson. Override the version property until '
       'the next Boot patch.', security=True, owasp='A03')
define('DEPS-ANGULAR-EOL', 'Angular major out of support or close to it', 'high', 'supply-chain',
       'Out of LTS means no fixes for the 2026 sanitizer and SSR advisories.', security=True, owasp='A03')
define('DEPS-FLOOR', 'Dependency below a known security fix', 'high', 'supply-chain',
       'Confirm with osv-scanner or the advisory - entries marked verify came from a single source.',
       security=True, owasp='A03')
define('DEPS-RUNTIME-EOL', 'Runtime out of support', 'medium', 'supply-chain', '', security=True, owasp='A03')
define('DEPS-TRANSITIVE-UNKNOWN', 'Transitive JVM versions not resolved', 'low', 'supply-chain',
       'Without --resolve or osv-scanner only explicitly pinned versions were checked.', security=True,
       owasp='A03')

TODAY = dt.date.today()


def _below(version: str, fixed: list[str]) -> str | None:
    """The fix this version is missing, or None. A line with no fix of its own counts as missing the next one."""
    v = version_tuple(version)
    lines = sorted((version_tuple(f), f) for f in fixed)
    same = [f for t, f in lines if t[:2] == v[:2]] or [f for t, f in lines if t[:1] == v[:1] and len(fixed) == 1]
    if same:
        return same[0] if v < version_tuple(same[0]) else None
    newer = [f for t, f in lines if t > v]
    return newer[0] if newer else None


def _floors(hits: Hits, ecosystem: str, versions: dict[str, tuple[str, str | None]], eol_major: bool = False):
    for floor in DATA['floors']:
        if floor['ecosystem'] != ecosystem or floor['package'] not in versions:
            continue
        version, where = versions[floor['package']]
        if eol_major and version_tuple(version)[0] < min(version_tuple(f)[0] for f in floor['fixed']):
            continue
        missing = _below(version, floor['fixed'])
        if missing:
            hits.add('DEPS-FLOOR', where, None,
                     f'{floor["package"]} {version} < {missing}: {floor["ids"]}' +
                     ('   (verify)' if floor.get('verify') else ''), severity=floor['severity'],
                     **_vuln(floor['package'], version, floor['ids']))


def _vuln(package: str, version: str, ids: str) -> dict:
    found = re.findall(r'\b(?:CVE-\d{4}-\d+|GHSA(?:-\w{4}){3})\b', ids)
    return {'package': package, 'version': version, **({'advisory': found[0]} if found else {})}


def resolve_jvm(repo: Repo, stack: dict, timeout: int = 600) -> tuple[dict[str, str], str]:
    out, status = {}, ''
    root = repo.root
    gradlew = root / 'gradlew'
    if gradlew.is_file():
        tasks = [(':' + m['path'].replace('/', ':') if m['path'] != '.' else '') + ':dependencies'
                 for m in stack['modules']]
        cmd = [str(gradlew), '-q', '--console=plain', *sorted(set(tasks)), '--configuration', 'runtimeClasspath']
    elif (root / 'pom.xml').is_file():
        mvn = str(root / 'mvnw') if (root / 'mvnw').is_file() else 'mvn'
        cmd = [mvn, '-B', '-q', 'dependency:list', '-DincludeScope=runtime', '-DoutputFile=/dev/stdout',
               '-DappendOutput=true']
    else:
        return out, 'no gradlew or pom.xml at the scan root'
    try:
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as exc:
        return out, f'{os.path.basename(cmd[0])} failed: {exc}'
    text = proc.stdout
    for m in re.finditer(r'([\w.-]+):([\w.-]+):(?:(?:jar|pom|war|bundle):)?(?:[\w-]+:)?([\w.+-]+?)(?:\s*->\s*([\w.+-]+))?'
                         r'(?=[\s:(]|$)', text):
        coord, version = f'{m.group(1)}:{m.group(2)}', m.group(4) or m.group(3)
        if re.match(r'\d', version):
            old = out.get(coord)
            if not old or version_tuple(version) < version_tuple(old):
                out[coord] = version
    for m in re.finditer(r'(?<![\w.:-])([\w.-]+):([A-Za-z][\w.-]*)\s*->\s*([\w.+-]+)', text):
        coord = f'{m.group(1)}:{m.group(2)}'
        if coord not in out and re.match(r'\d', m.group(3)):
            out[coord] = m.group(3)
    status = f'{os.path.basename(cmd[0])} exit {proc.returncode}, {len(out)} artifacts'
    if proc.returncode and not out:
        status += ': ' + (proc.stderr.strip().split('\n') or [''])[-1][:200]
    return out, status


def run(repo: Repo, stacks: dict, hits: Hits, inventory: dict, resolve: bool = False) -> dict:
    info = {}
    spring = stacks.get('spring')
    if spring:
        info['spring'] = spring_versions(repo, spring, hits, resolve, inventory.get('spring') or {})
    for ws in stacks.get('angular') or []:
        info.setdefault('angular', []).append(angular_versions(ws, hits))
    runtimes(repo, hits)
    return info


def _shape_present(require: str, stack: dict, inventory: dict) -> bool:
    build = stack['build_text']
    chains = inventory.get('chains') or []
    if require == 'actuator':
        return 'actuator' in build
    if require == 'security':
        return bool(re.search(r'spring-boot-starter-security|spring-security-', build))
    if require == 'no-chain':
        return not chains
    if require == 'endpoint-request-to':
        return any(p.startswith('<actuator:') for c in chains for r in c['rules'] for p in r['patterns'])
    if require.startswith('path:'):
        return any(e['path'].startswith(require[5:]) for e in inventory.get('endpoints') or [])
    return True


def spring_versions(repo: Repo, stack: dict, hits: Hits, resolve: bool, inventory: dict) -> dict:
    build_file = next((f for f in repo.files if os.path.basename(f) in ('build.gradle.kts', 'build.gradle', 'pom.xml')
                       or f.endswith('.versions.toml')), None)
    boot = stack.get('boot')
    result = {'boot': boot}
    if boot:
        v = version_tuple(boot)
        line = f'{v[0]}.{v[1] if len(v) > 1 else 0}'
        spec = DATA['spring-boot']['lines'].get(line)
        if not spec:
            oldest = min(DATA['spring-boot']['lines'], key=version_tuple)
            if v < version_tuple(oldest):
                hits.add('DEPS-BOOT-EOL', build_file, None, f'Spring Boot {boot}: line {line} long out of support',
                         severity='critical' if v[0] < 3 else None)
        else:
            end = spec['oss_end']
            if end and dt.date.fromisoformat(end) < TODAY:
                hits.add('DEPS-BOOT-EOL', build_file, None,
                         f'Spring Boot {boot}: OSS support for {line} ended {end}'
                         + (f', last patch {spec["latest"]}' if spec['latest'] else ''))
            elif spec['latest'] and not re.search(r'-(M|RC)\d', spec['latest']) and \
                    v < version_tuple(spec['latest']):
                hits.add('DEPS-BOOT-PATCH', build_file, None, f'Spring Boot {boot} < {spec["latest"]} '
                                                              f'(OSS until {end})')
        for cve in DATA['spring-boot']['cves']:
            if v >= version_tuple(cve['introduced']) and _below(boot, cve['fixed']):
                if not all(_shape_present(r, stack, inventory) for r in cve.get('requires', [])):
                    continue
                prop = cve.get('property')
                if prop and prop not in stack['build_text'] and not any(
                        prop in repo.source(f).text for f in repo.files
                        if re.search(r'(application|bootstrap)[\w.-]*\.(ya?ml|properties)$', f)):
                    continue
                hits.add('DEPS-BOOT-CVE', build_file, None, f'{cve["id"]} ({boot} < {_below(boot, cve["fixed"])}): '
                                                            f'{cve["shape"]}', severity=cve['severity'],
                         **_vuln('org.springframework.boot:spring-boot', boot, cve['id']))
    explicit = {c: (d['version'], d['file']) for c, d in stack['deps'].items() if d.get('version')}
    resolved = {}
    if resolve:
        resolved, status = resolve_jvm(repo, stack)
        result['resolve'] = status
    versions = dict(explicit)
    for coord, version in resolved.items():
        versions[coord] = (version, build_file)
    _floors(hits, 'maven', versions)
    known = sorted((k for k in DATA['boot_managed'] if boot and version_tuple(k)[:2] == version_tuple(boot)[:2]
                    and version_tuple(k) >= version_tuple(boot)), key=version_tuple)
    if known and not resolved:
        for coord, managed in DATA['boot_managed'][known[0]].items():
            if coord in explicit:
                continue
            if re.search(DATA['overrides'].get(coord, '$^'), stack['build_text']):
                continue
            floor = next((f for f in DATA['floors'] if f['package'] == coord), None)
            if floor and _below(managed, floor['fixed']):
                hits.add('DEPS-BOOT-MANAGED', build_file, None,
                         f'Boot {boot} manages {coord} {managed}{" or older" if known[0] != boot else ""} '
                         f'< {_below(managed, floor["fixed"])}: {floor["ids"]}',
                         severity='high' if floor['severity'] == 'critical' else 'medium',
                         **_vuln(coord, managed, floor['ids']))
    if not resolved:
        hits.add('DEPS-TRANSITIVE-UNKNOWN', build_file, None,
                 f'{len(explicit)} explicit versions checked, transitive tree not resolved')
    result['resolved'] = len(resolved)
    if resolved:
        result['artifacts'] = resolved
    return result


def angular_versions(ws: dict, hits: Hits) -> dict:
    rel = (ws['path'] + '/' if ws['path'] != '.' else '') + 'package.json'
    version = ws['angular']
    major = str(ws['major'])
    spec = DATA['angular']['lines'].get(major)
    if spec:
        end = dt.date.fromisoformat(spec['eol'])
        if end < TODAY:
            hits.add('DEPS-ANGULAR-EOL', rel, None, f'Angular {version}: v{major} out of support since {spec["eol"]}')
        elif (end - TODAY).days <= 60:
            hits.add('DEPS-ANGULAR-EOL', rel, None, f'Angular {version}: v{major} support ends {spec["eol"]}',
                     severity='medium')
    elif ws['major'] < int(min(DATA['angular']['lines'], key=int)):
        hits.add('DEPS-ANGULAR-EOL', rel, None, f'Angular {version}: long out of support', severity='critical')
    installed = {name: (v, rel) for name, v in ws['installed'].items()}
    if not installed:
        installed = {name: (re.sub(r'^[\^~>=<\s]+', '', v), rel) for name, v in ws['declared'].items()
                     if isinstance(v, str) and re.match(r'[\^~>=<\s]*\d', v)}
    _floors(hits, 'npm', installed, eol_major=True)
    return {'path': ws['path'], 'angular': version, 'lockfile': ws['lockfile']}


def runtimes(repo: Repo, hits: Hits):
    node_eol = DATA['node']
    seen = set()
    for rel in repo.files:
        name = os.path.basename(rel)
        text = repo.source(rel).text if name in ('.nvmrc', '.node-version', 'package.json') or \
            re.match(r'(Dockerfile|Containerfile)', name) else ''
        majors = []
        if name in ('.nvmrc', '.node-version'):
            majors = re.findall(r'v?(\d+)', text.strip())[:1]
        elif name == 'package.json':
            m = re.search(r'"node"\s*:\s*"[^\d"]*(\d+)', text)
            majors = [m.group(1)] if m else []
        elif text:
            majors = re.findall(r'(?im)^\s*FROM\s+(?:\S+/)?node:(\d+)', text)
            for m in re.finditer(r'(?im)^\s*FROM\s+\S*(?:temurin|openjdk|jdk|jre|corretto|zulu|liberica)\S*?:(\d+)', text):
                java = int(m.group(1))
                if java not in DATA['java_lts'] and java < DATA['java_latest_feature']:
                    hits.add('DEPS-RUNTIME-EOL', rel, None, f'Java {java} is a non-LTS release without updates',
                             severity='low')
        for major in majors:
            end = node_eol.get(major)
            if end and dt.date.fromisoformat(end) < TODAY and (rel, major) not in seen:
                seen.add((rel, major))
                hits.add('DEPS-RUNTIME-EOL', rel, None, f'Node {major} out of support since {end}')
