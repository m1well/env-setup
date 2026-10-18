"""Which stacks live where: Spring Boot modules and Angular workspaces, with their versions."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .core import Repo, version_tuple

BUILD_FILES = ('build.gradle.kts', 'build.gradle', 'pom.xml')


def _dir(rel: str) -> str:
    return os.path.dirname(rel) or '.'


def _toml_sections(text: str) -> dict[str, dict[str, str]]:
    sections, current = {}, None
    for raw in text.split('\n'):
        line = raw.split('#')[0].strip()
        head = re.match(r'^\[([\w.-]+)\]$', line)
        if head:
            current = sections.setdefault(head.group(1), {})
        elif current is not None and '=' in line:
            key, _, value = line.partition('=')
            current[key.strip().strip('"')] = value.strip()
    return sections


def _catalog(text: str) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """(versions, libraries as group:artifact -> version, plugins as id -> version)."""
    sec = _toml_sections(text)
    versions = {k: v.strip('"\'') for k, v in sec.get('versions', {}).items()}

    def resolve(spec: str) -> str | None:
        ref = re.search(r'version\.ref\s*=\s*"([^"]+)"', spec)
        if ref:
            return versions.get(ref.group(1))
        plain = re.search(r'version\s*=\s*"([^"]+)"', spec)
        return plain.group(1) if plain else None

    libs = {}
    for spec in sec.get('libraries', {}).values():
        if spec.startswith('"'):
            parts = spec.strip('"').split(':')
            if len(parts) == 3:
                libs[f'{parts[0]}:{parts[1]}'] = parts[2]
            continue
        module = re.search(r'module\s*=\s*"([^"]+)"', spec)
        group, name = re.search(r'group\s*=\s*"([^"]+)"', spec), re.search(r'name\s*=\s*"([^"]+)"', spec)
        coord = module.group(1) if module else (f'{group.group(1)}:{name.group(1)}' if group and name else None)
        if coord:
            libs[coord] = resolve(spec) or ''
    plugins = {}
    for spec in sec.get('plugins', {}).values():
        if spec.startswith('"'):
            pid, _, ver = spec.strip('"').partition(':')
            plugins[pid] = ver
            continue
        pid = re.search(r'id\s*=\s*"([^"]+)"', spec)
        if pid:
            plugins[pid.group(1)] = resolve(spec) or ''
    return versions, libs, plugins


def _maven(text: str) -> tuple[dict[str, str], str | None, dict[str, str]]:
    props = {}
    block = re.search(r'<properties>([\s\S]*?)</properties>', text)
    if block:
        props = dict(re.findall(r'<([\w.-]+)>\s*([^<\s][^<]*?)\s*</\1>', block.group(1)))

    def resolve(value: str) -> str:
        return re.sub(r'\$\{([^}]+)\}', lambda m: props.get(m.group(1), m.group(0)), value.strip())

    boot = None
    parent = re.search(r'<parent>([\s\S]*?)</parent>', text)
    if parent and 'spring-boot-starter-parent' in parent.group(1):
        ver = re.search(r'<version>([^<]+)</version>', parent.group(1))
        boot = resolve(ver.group(1)) if ver else None
    deps = {}
    for dep in re.findall(r'<dependency>([\s\S]*?)</dependency>', text):
        g = re.search(r'<groupId>([^<]+)</groupId>', dep)
        a = re.search(r'<artifactId>([^<]+)</artifactId>', dep)
        v = re.search(r'<version>([^<]+)</version>', dep)
        if g and a:
            deps[f'{resolve(g.group(1))}:{resolve(a.group(1))}'] = resolve(v.group(1)) if v else ''
    if not boot:
        boot = deps.get('org.springframework.boot:spring-boot-dependencies') or props.get('spring-boot.version')
    return props, boot, deps


GRADLE_COORD = re.compile(r'["\']([\w.-]+):([\w.-]+):([\w.${}+-]+)["\']')
GRADLE_VAR = re.compile(r'(?:val|var|def)\s+(\w+)\s*(?::\s*String\s*)?=\s*["\']([^"\']+)["\']')
BOOT_PLUGIN = re.compile(r'org\.springframework\.boot["\']\s*\)?\s*version\s*\(?\s*["\']([^"\']+)["\']')


def spring_stack(repo: Repo) -> dict | None:
    builds = [f for f in repo.files if os.path.basename(f) in BUILD_FILES]
    catalogs = [f for f in repo.files if f.endswith('.versions.toml')]
    props_files = [f for f in repo.files if os.path.basename(f) == 'gradle.properties']
    blob = '\n'.join(repo.source(f).text for f in builds + catalogs + props_files)
    if 'org.springframework.boot' not in blob and 'spring-boot' not in blob:
        return None

    gradle_props = {}
    for f in props_files:
        gradle_props.update(re.findall(r'(?m)^\s*([\w.-]+)\s*=\s*(\S+)', repo.source(f).text))
    deps: dict[str, dict] = {}
    boot = None
    catalog_versions = {}
    for f in catalogs:
        versions, libs, plugins = _catalog(repo.source(f).text)
        catalog_versions.update(versions)
        for coord, ver in libs.items():
            deps.setdefault(coord, {'version': ver, 'file': f})
        boot = boot or plugins.get('org.springframework.boot') or \
            libs.get('org.springframework.boot:spring-boot-dependencies')
    if not boot:
        boot = next((v for k, v in catalog_versions.items()
                     if re.fullmatch(r'spring[-_.]?boot', k, re.I)), None)

    gradle_vars = dict(gradle_props)
    for f in builds:
        if not f.endswith('.xml'):
            gradle_vars.update(GRADLE_VAR.findall(repo.source(f).text))

    def resolve(value: str) -> str:
        return re.sub(r'\$\{?(\w+)\}?', lambda m: gradle_vars.get(m.group(1), m.group(0)), value)

    modules = []
    for f in builds:
        text = repo.source(f).text
        if f.endswith('.xml'):
            _, mboot, mdeps = _maven(text)
            boot = boot or mboot
            for coord, ver in mdeps.items():
                deps.setdefault(coord, {'version': ver, 'file': f})
        else:
            m = BOOT_PLUGIN.search(text)
            boot = boot or (resolve(m.group(1)) if m else None)
            for g, a, v in GRADLE_COORD.findall(text):
                deps.setdefault(f'{g}:{a}', {'version': resolve(v), 'file': f})
        base = _dir(f)
        prefix = '' if base == '.' else base + '/'
        main = [x for x in repo.files if x.startswith(prefix + 'src/main/')]
        if not main:
            continue
        kotlin = sum(x.endswith('.kt') for x in main)
        java = sum(x.endswith('.java') for x in main)
        modules.append({'path': base, 'build': 'maven' if f.endswith('.xml') else 'gradle',
                        'language': 'kotlin' if kotlin >= java else 'java',
                        'files': kotlin + java})
    if not boot:
        boot = gradle_props.get('springBootVersion') or gradle_vars.get('springBootVersion')

    java_version = re.search(r'jvmToolchain\s*\(\s*(\d+)|JavaLanguageVersion\.of\s*\(\s*(\d+)|'
                             r'VERSION_(\d+)|<java\.version>(\d+)</java\.version>|'
                             r'<maven\.compiler\.release>(\d+)<', blob)
    kotlin_version = re.search(r'kotlin\(\s*"jvm"\s*\)\s*version\s*"([^"]+)"|'
                               r'org\.jetbrains\.kotlin\.jvm["\']?\)?\s*version\s*["\']([^"\']+)', blob)
    if not kotlin_version:
        kv = next((v for k, v in catalog_versions.items() if k.lower() == 'kotlin'), None)
    else:
        kv = next(g for g in kotlin_version.groups() if g)
    return {
        'boot': boot if boot and not boot.startswith('$') else None,
        'java': next((g for g in java_version.groups() if g), None) if java_version else None,
        'kotlin': kv,
        'build': sorted({m['build'] for m in modules}) or ['gradle' if 'gradle' in blob else 'maven'],
        'modules': modules,
        'deps': deps,
        'build_text': blob,
    }


def _lock_versions(root: Path) -> dict[str, str]:
    lock = root / 'package-lock.json'
    if lock.is_file():
        try:
            data = json.loads(lock.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return {}
        out = {}
        for path, meta in (data.get('packages') or {}).items():
            if path.startswith('node_modules/') and isinstance(meta, dict) and meta.get('version'):
                out.setdefault(path.split('node_modules/')[-1], meta['version'])
        for name, meta in (data.get('dependencies') or {}).items():
            if isinstance(meta, dict) and meta.get('version'):
                out.setdefault(name, meta['version'])
        return out
    pnpm = root / 'pnpm-lock.yaml'
    if pnpm.is_file():
        text = pnpm.read_text(encoding='utf-8', errors='replace')
        return {m.group(1): m.group(2) for m in
                re.finditer(r"(?m)^\s{2,}'?(@?[\w./-]+?)@(\d+\.\d+\.\d+[\w.-]*)'?:\s*$", text)}
    yarn = root / 'yarn.lock'
    if yarn.is_file():
        text = yarn.read_text(encoding='utf-8', errors='replace')
        return {m.group(1): m.group(2) for m in
                re.finditer(r'(?m)^"?(@?[\w./-]+?)@[^\n]*:\n\s+version:?\s+"?([\w.-]+)"?', text)}
    return {}


def angular_stack(repo: Repo) -> list[dict]:
    out = []
    for rel in repo.files:
        if os.path.basename(rel) != 'package.json':
            continue
        try:
            pkg = json.loads(repo.source(rel).text or '{}')
        except ValueError:
            continue
        all_deps = {**(pkg.get('dependencies') or {}), **(pkg.get('devDependencies') or {})}
        if '@angular/core' not in all_deps:
            continue
        base = _dir(rel)
        root = repo.root / base
        installed = _lock_versions(root)
        version = installed.get('@angular/core') or re.sub(r'^[\^~>=<\s]+', '', all_deps['@angular/core'])
        prefix = '' if base == '.' else base + '/'
        projects = []
        ng = root / 'angular.json'
        if ng.is_file():
            try:
                for name, spec in (json.loads(ng.read_text(encoding='utf-8')).get('projects') or {}).items():
                    projects.append({'name': name, 'root': spec.get('root') or '.',
                                     'type': spec.get('projectType')})
            except ValueError:
                pass
        for pj in (f for f in repo.files if f.startswith(prefix) and f.endswith('/project.json')):
            try:
                spec = json.loads(repo.source(pj).text or '{}')
            except ValueError:
                continue
            projects.append({'name': spec.get('name') or os.path.basename(os.path.dirname(pj)),
                             'root': os.path.dirname(pj)[len(prefix):],
                             'type': spec.get('projectType'), 'tags': spec.get('tags') or []})
        lockfile = next((n for n in ('package-lock.json', 'pnpm-lock.yaml', 'yarn.lock', 'bun.lockb')
                         if (root / n).is_file()), None)
        out.append({
            'path': base, 'angular': version, 'major': version_tuple(version)[0],
            'nx': (root / 'nx.json').is_file(), 'lockfile': lockfile,
            'ssr': '@angular/ssr' in all_deps or '@nguniversal/express-engine' in all_deps,
            'zoneless': 'zone.js' not in all_deps,
            'test_runner': 'vitest' if 'vitest' in all_deps else 'jest' if 'jest' in all_deps
            else 'karma' if 'karma' in all_deps else None,
            'projects': projects,
            'installed': installed,
            'declared': all_deps,
        })
    return out


def detect(repo: Repo) -> dict:
    return {'spring': spring_stack(repo), 'angular': angular_stack(repo)}
