"""Angular checks - XSS sinks, route guards, token handling, SSR, then state, templates and layering."""
from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from typing import NamedTuple

from .core import Hits, Repo, balanced, define, is_test_path, mask, redact, split_top, strings_in

define('NG-BYPASS-SANITIZER', 'Angular sanitizer bypassed', 'high', 'xss',
       'Follow the value into bypassSecurityTrust*: anything a user or the backend controls is XSS.',
       security=True, owasp='A05')
define('NG-DOM-XSS', 'Raw DOM sink outside Angular\'s sanitizer', 'high', 'xss',
       'innerHTML assignment, insertAdjacentHTML, document.write, eval: check where the string comes from.',
       security=True, owasp='A05')
define('NG-INNERHTML-BINDING', '[innerHTML] binding', 'low', 'xss',
       'Angular sanitizes it - a finding only together with bypassSecurityTrustHtml or a two-way binding.',
       security=True, owasp='A05')
define('NG-SANITIZER-CVE-PATTERN', 'Template shape named in a 2025/2026 Angular XSS advisory', 'medium', 'xss',
       'Two-way binding on innerHTML/src/href, i18n on URL or on* attributes, bound SVG href or attributeName. '
       'Exposed only below the patched version - compare with the DEPS hit for @angular/core.',
       security=True, owasp='A05')
define('NG-TOKEN-STORAGE', 'Token kept in localStorage or sessionStorage', 'medium', 'authentication',
       'Any XSS reads it. RFC 10017 (OAuth for browser-based apps) ranks a BFF with an HttpOnly cookie first.',
       security=True, owasp='A07')
define('NG-SECRET-IN-CLIENT', 'Secret in frontend code', 'high', 'secrets',
       'Everything in the bundle is public. A client secret or private key here is leaked; a referrer-'
       'restricted public API key is low.', security=True, owasp='A07')
define('NG-HTTP-INSECURE', 'Plain http:// URL outside of local development', 'medium', 'crypto',
       'Check which build configuration uses the file.', security=True, owasp='A04')
define('NG-XSRF-OFF', 'HttpClient XSRF protection switched off', 'medium', 'authorization',
       'Matters when the backend authenticates with a cookie. Check the backend CSRF setup.',
       security=True, owasp='A01')
define('NG-INTERCEPTOR-BYPASS', 'Request that bypasses the HttpClient interceptors', 'medium', 'authorization',
       'fetch, XMLHttpRequest, axios or HttpBackend skip the auth and error interceptors. Name what the '
       'interceptor adds that this call misses.', security=True, owasp='A01')
define('NG-TOKEN-ALL-HOSTS', 'Bearer token attached to every outgoing request', 'medium', 'authentication',
       'An interceptor without a URL check sends the token to every host the app calls - CDNs, maps, '
       'analytics. Check req.url against the own API base, or set keycloak-angular\'s urlPattern / bearerExcludedUrls.',
       security=True, owasp='A07')
define('NG-TOKEN-HOST-PREFIX', 'Bearer token decided by a URL prefix without a host boundary', 'medium',
       'authentication', 'https://api.example.com.evil.tld passes startsWith(\'https://api.example.com\'). Fine when '
       'the base ends with / or the code compares new URL(url).origin.', security=True, owasp='A07')
define('NG-TOKEN-IN-PATH', 'Token in a request URL', 'low', 'exposure',
       'Path and query end up in server, proxy and browser logs. A capability link may need it - then short-lived, '
       'single-use and hashed on the server; otherwise a header or the body.', security=True, owasp='A02')
define('NG-IFRAME-WRITE', 'HTML written into an iframe', 'medium', 'xss',
       'contentDocument.write and srcdoc: the sandbox decides. Without allow-scripts nothing runs; allow-scripts '
       'with allow-same-origin lifts the sandbox; no sandbox runs the HTML with the app\'s origin.',
       security=True, owasp='A05')
define('NG-ROUTE-UNGUARDED', 'Sensitive route without a guard while sibling routes have one', 'high',
       'authorization', 'The contrast is the finding - name the route and a guarded sibling. A guard is UX, '
       'the backend must still check; say whether it does.', security=True, owasp='A01')
define('NG-NO-GUARDS', 'App with a login but no route guard at all', 'medium', 'authorization',
       'Check whether every protected view is protected by the backend alone.', security=True, owasp='A01')
define('NG-NO-CSP', 'No Content-Security-Policy found', 'low', 'config',
       'No meta tag, no autoCsp, no header in a server config in this repo. It may be set at the edge - say so.',
       security=True, owasp='A02')
define('NG-PROD-SOURCEMAP', 'Source maps in the production build', 'medium', 'exposure',
       'The full source goes to every visitor. hidden: true keeps them for error tracking only.',
       security=True, owasp='A02')
define('NG-SSR-HOSTS', 'SSR host validation missing or wildcard', 'high', 'ssrf',
       'Angular SSR resolves relative URLs against the Host header (CVE-2026-27739). allowedHosts must '
       'list the real hosts, never "*".', security=True, owasp='A01')
define('NG-SSR-PATTERN', 'SSR shape named in a 2025/2026 advisory', 'medium', 'ssrf',
       'CommonEngine, bootstrapApplication without a context, URLs from REQUEST headers. Compare with the '
       'installed @angular/ssr / platform-server version.', security=True, owasp='A01')
define('NG-COMPONENT-SIZE', 'Component past 300 lines of TypeScript or 150 lines of template', 'medium', 'size',
       'The split is usually along the template.')
define('NG-MANY-INPUTS', 'Component with more than 10 inputs', 'low', 'size',
       'Every call site has to know all of them.')
define('NG-MANY-INJECTS', 'Class injecting more than 5 services', 'medium', 'coupling',
       'Orchestration that belongs in a page or a state service.')
define('NG-STATE-SIZE', 'State service exposing more than 15 signals and resources', 'low', 'size',
       'Two domains in one store - look at which signals are read together.')
define('NG-SUBSCRIBE-LEAK', 'subscribe() in a component without teardown', 'medium', 'reactivity',
       'Every navigation leaves one subscription behind. takeUntilDestroyed or a resource.', rule='STATE-4')
define('NG-EFFECT-WRITES', 'effect() that writes a signal', 'medium', 'reactivity',
       'A computed() or linkedSignal() written the expensive way.', rule='SIG-3')
define('NG-LEGACY-API', 'Decorator APIs the signal API replaced', 'low', 'upgrade',
       'A migration status, not a bug - report the ratio.', rule='SIG-1')
define('NG-LEGACY-CONTROL-FLOW', '*ngIf / *ngFor / *ngSwitch (deprecated since v20)', 'low', 'upgrade',
       'ng generate @angular/core:control-flow migrates them.', rule='TPL-1')
define('NG-NGCLASS', 'ngClass / ngStyle', 'low', 'template', '', rule='TPL-3')
define('NG-INLINE-TEMPLATE', 'Inline template or styles', 'low', 'template', '', rule='FILE-1')
define('NG-STANDALONE-TRUE', 'standalone: true written out (default since v19)', 'low', 'upgrade', '',
       rule='SIG-2')
define('NG-ONPUSH', 'Change detection strategy out of line with the Angular version', 'low', 'reactivity',
       'v22+: OnPush is the default, Default is deprecated (Eager). Below v22: components without OnPush.',
       rule='SIG-2')
define('NG-NGMODULE', 'NgModule declarations', 'low', 'upgrade', '')
define('NG-REMOVED-API', 'Angular API deprecated or removed in v20-v22', 'medium', 'upgrade', '')
define('NG-ANY', 'any at the HTTP boundary', 'low', 'typing', 'The backend contract is a guess from here on.')
define('NG-TRACK-INDEX', '@for tracking by $index', 'low', 'template',
       'Fine for a positional list, a full re-render for one that reorders.', rule='TPL-2')
define('NG-LAYER-INJECT', 'Lower-layer component injects a service', 'medium', 'layering',
       'Below the page everything should run on input()/output().', rule='LAYER-7')
define('NG-COMPONENT-HTTP', 'Component talks to HttpClient or an api service directly', 'medium', 'layering',
       'Skips whatever the state layer caches or guards.', rule='STATE-9')
define('NG-DEEP-IMPORT', 'Import past a library\'s public entry point', 'high', 'boundary',
       'The library\'s public surface stops meaning anything.', rule='LAYER-13')
define('NG-DETECT-CHANGES', 'Manual change detection', 'low', 'reactivity', '')
define('NG-ZONE', 'zone.js still loaded on v21+', 'low', 'upgrade', 'Zoneless is the default since v21.')
define('NG-CONSOLE', 'console.log in production code', 'low', 'logging', '')
define('NG-NO-SPEC', 'Components and services without a spec file', 'low', 'testing', '')
define('NG-RXJS-STATE', 'BehaviorSubject state in a service', 'low', 'state', '', rule='STATE-4')
define('NG-TEMPLATE-LOGIC', 'Computation in template interpolations', 'low', 'template', '', rule='TPL-4')
define('DEPS-UNUSED', 'Declared npm packages nothing references', 'low', 'supply-chain',
       'No import, no config, no script, no peer of another package. Grep the name once more - then npm uninstall; '
       'every unused package still brings its CVEs into the audit and the image.', owasp='A03')
define('DEPS-BUILD-IN-PROD', 'Build tooling under dependencies', 'low', 'supply-chain',
       'Compilers, bundlers, linters and test runners belong in devDependencies - a production install pulls them '
       'and their advisories in.', owasp='A03')

SENSITIVE_ROUTE = re.compile(r'(?i)(admin|intern|internal|manage|verwaltung|settings|einstellung|account|konto|'
                             r'profile|profil|billing|rechnung|invoice|payment|zahlung|edit|bearbeit|dashboard|'
                             r'user|benutzer|member|mitglied|team|config|backoffice|cockpit|portal|private|privat|'
                             r'\bmy\b|mein|orders?|bestellung|checkout|upload|import|export|report)')
PRE_BOOTSTRAP = re.compile(r'(^|[\'"`/])assets/|\.json\b|/actuator/health')
TRIVIAL_INJECT = {'ElementRef', 'Renderer2', 'DestroyRef', 'ChangeDetectorRef', 'Injector', 'DOCUMENT', 'NgZone',
                  'ViewContainerRef', 'TemplateRef', 'PLATFORM_ID', 'LOCALE_ID', 'DomSanitizer', 'Title', 'Meta',
                  'FormBuilder', 'NonNullableFormBuilder', 'BreakpointObserver', 'APP_BASE_HREF', 'WINDOW'}
LAYERS = re.compile(r'/(atoms|molecules|organisms|ui|templates)/')
PAGE = re.compile(r'(^|/)pages?/|[.-]page(\.component)?\.ts$|(^|/)app(\.component)?\.ts$')
LONG_LIVED = re.compile(r'\b(valueChanges|statusChanges|events|paramMap|queryParamMap|params|queryParams|fragment|'
                        r'data|interval|timer|fromEvent|webSocket|EventSource|observe|breakpoint\w*|select|'
                        r'\w+\$|\w*[Ss]ubject|\w*[Ss]tream|\w*[Cc]hanges|toObservable)\b')
class Api(NamedTuple):
    pattern: str
    flag_from: int
    removed: int | None
    label: str


REMOVED = [Api(*a) for a in [
    (r'\bComponentFactoryResolver\b', 21, 22, 'removed in v22 - use ViewContainerRef.createComponent'),
    (r'\bcreateNgModuleRef\s*\(', 21, 22, 'removed in v22 - createNgModule'),
    (r'\bprovideRoutes\s*\(', 21, 22, 'removed in v22 - provideRouter / ROUTES'),
    (r'\bNgModuleFactory\b', 20, 21, 'removed in v21'),
    (r'\bmoduleId\s*:', 20, 21, 'removed in v21'),
    (r'\bInjectFlags\b', 19, 20, 'removed in v20 - use the options object of inject()'),
    (r'\bTestBed\s*\.\s*get\s*\(', 19, 20, 'removed in v20 - TestBed.inject'),
    (r'\bprovideExperimentalZonelessChangeDetection\b', 19, 20, 'renamed in v20 - provideZonelessChangeDetection'),
    (r'\bafterRender\s*\(', 19, 20, 'renamed in v20 - afterEveryRender'),
    (r"from\s+['\"]@angular/animations", 20, 23, '@angular/animations deprecated since v20.2, removal planned for v23'),
    (r"from\s+['\"]@angular/platform-browser-dynamic", 20, None, 'platform-browser-dynamic deprecated since v20 (JIT)'),
    (r'ChangeDetectionStrategy\s*\.\s*Default\b', 22, None, 'deprecated in v22 - ChangeDetectionStrategy.Eager'),
    (r'\bwithFetch\s*\(', 22, None, 'redundant on v22 - fetch is the default'),
    (r'\bCommonEngine\b', 22, None, 'SSR CommonEngine deprecated in v22 - AngularNodeAppEngine'),
]]


def _json(text: str):
    clean, _ = mask(text, '.ts')
    clean = re.sub(r',(\s*[}\]])', r'\1', clean)
    try:
        return json.loads(clean)
    except ValueError:
        return None


def _objects(bare: str) -> list[list]:
    stack, out = [], []
    for i, ch in enumerate(bare):
        if ch == '{':
            out.append([i, len(bare), stack[-1] if stack else None])
            stack.append(len(out) - 1)
        elif ch == '}' and stack:
            out[stack.pop()][1] = i
    return out


def _innermost(objs: list[list], pos: int) -> int | None:
    best = None
    for idx, (start, end, _) in enumerate(objs):
        if start < pos < end and (best is None or start > objs[best][0]):
            best = idx
    return best


def _function_body(bare: str, pos: int) -> tuple[int, int]:
    """Span of the innermost function, method or arrow body around `pos`, or the whole file."""
    for start, end, _ in sorted((o for o in _objects(bare) if o[0] < pos < o[1]), key=lambda o: -o[0]):
        head = bare[max(0, start - 200):start].rstrip()
        if head.endswith('=>') or (re.search(r'\)\s*(?::\s*[^{};()]+)?$', head) and not re.search(
                r'\b(if|for|while|switch|catch)\s*\([^()]*(?:\([^()]*\)[^()]*)*\)\s*$', head)):
            return start, end
    return 0, len(bare)


def _const_value(code: str, name: str) -> str | None:
    m = re.search(r'\b' + re.escape(name) + r'\s*(?::\s*\w+\s*)?=\s*([\'"`])([^\'"`]*)\1', code)
    return m.group(2) if m else None


def _args(src, open_paren: int) -> list[str]:
    """Code of each top-level argument of the call whose `(` sits at open_paren."""
    close = balanced(src.bare, open_paren)
    parts = split_top(src.bare[open_paren + 1:close if close > 0 else len(src.bare)])
    return [src.code[open_paren + 1 + at:open_paren + 1 + at + len(part)].strip() for at, part in parts]


class Workspace:
    def __init__(self, repo: Repo, ws: dict):
        self.repo, self.ws = repo, ws
        prefix = '' if ws['path'] == '.' else ws['path'] + '/'
        self.prefix = prefix
        self.files = [f for f in repo.files if f.startswith(prefix)]
        self.ts = [f for f in self.files if f.endswith('.ts') and not f.endswith('.d.ts')]
        self.main_ts = [f for f in self.ts if not is_test_path(f)]
        self.html = [f for f in self.files if f.endswith('.html') and not is_test_path(f)]
        self.major = ws['major']
        self.aliases = {}
        for name in ('tsconfig.base.json', 'tsconfig.json'):
            path = repo.root / prefix / name
            if path.is_file():
                data = _json(path.read_text(encoding='utf-8', errors='replace')) or {}
                for alias, targets in ((data.get('compilerOptions') or {}).get('paths') or {}).items():
                    if targets:
                        self.aliases[alias.rstrip('/*')] = os.path.normpath(os.path.join(ws['path'], targets[0]))
                break
        self.apps = sorted(((self.prefix + p['root'].strip('/') + '/' if p['root'] not in ('', '.') else self.prefix,
                             p['name']) for p in ws['projects'] if p.get('type') == 'application'),
                           key=lambda a: -len(a[0]))

    def app_of(self, rel: str) -> str | None:
        return next((name for root, name in self.apps if rel.startswith(root)), None)

    def route_app(self, route: dict) -> str:
        """The application project a route belongs to, else its root routes file."""
        return self.app_of(route['app']) or route['app']


def run(w: Workspace, hits: Hits) -> dict:
    repo = w.repo
    comps = components(w, hits)
    routes = route_inventory(w, hits)
    w.comps, w.routes = comps, routes
    check_security(w, hits, routes)
    check_tokens(w, hits)
    check_iframes(w, hits, comps)
    check_packages(w, hits)
    check_templates(w, hits, comps)
    check_structure(w, hits, comps)
    return {'path': w.ws['path'], 'components': len(comps),
            'injectables': sum(1 for f in w.main_ts if '@Injectable' in repo.source(f).bare),
            'routes': routes}



def components(w: Workspace, hits: Hits) -> list[dict]:
    out = []
    for rel in w.main_ts:
        src = w.repo.source(rel)
        bare, code = src.bare, src.code
        m = re.search(r'@(Component|Directive)\s*\(', bare)
        if not m:
            continue
        close = balanced(bare, m.end() - 1)
        meta_bare, meta_code = bare[m.end():close], code[m.end():close]
        cls = re.search(r'\bclass\s+(\w+)', bare[close:])
        info = {'file': rel, 'kind': m.group(1).lower(), 'name': cls.group(1) if cls else os.path.basename(rel),
                'line': src.line_at(m.start()), 'ts_lines': src.text.count('\n') + 1,
                'inline_template': bool(re.search(r'\btemplate\s*:', meta_bare)),
                'inline_styles': bool(re.search(r'\bstyles\s*:', meta_bare)),
                'standalone_true': bool(re.search(r'\bstandalone\s*:\s*true', meta_bare)),
                'onpush': 'OnPush' in meta_bare, 'cd_default': 'ChangeDetectionStrategy.Default' in meta_bare
                or re.search(r'ChangeDetectionStrategy\s*\.\s*Default', meta_bare) is not None,
                'explicit_cd': 'changeDetection' in meta_bare, 'template': None, 'template_lines': 0}
        tpl = re.search(r'\btemplateUrl\s*:\s*[\'"]([^\'"]+)[\'"]', meta_code)
        if tpl:
            path = os.path.normpath(os.path.join(os.path.dirname(rel), tpl.group(1)))
            if path in w.repo.files or (w.repo.root / path).is_file():
                info['template'] = path
                info['template_lines'] = w.repo.source(path).text.count('\n') + 1
        inline = re.search(r'\btemplate\s*:\s*`', meta_code)
        if inline:
            end = meta_code.find('`', inline.end())
            info['inline_html'] = meta_code[inline.end():end]
            info['template_lines'] = info['inline_html'].count('\n') + 1
        info['inputs'] = len(re.findall(r'=\s*(?:input|model)(?:\.required)?\s*[<(]', bare)) + \
            len(re.findall(r'@Input\s*\(', bare))
        injects = re.findall(r'\binject\s*\(\s*(\w+)', bare)
        ctor = re.search(r'\bconstructor\s*\(', bare)
        if ctor:
            c_close = balanced(bare, ctor.end() - 1)
            for _, part in split_top(bare[ctor.end():c_close]):
                t = re.search(r':\s*([\w.]+)', part)
                if t:
                    injects.append(t.group(1))
        info['injects'] = [i for i in injects if i not in TRIVIAL_INJECT]
        out.append(info)

        if info['ts_lines'] > 300 or info['template_lines'] > 150:
            hits.add('NG-COMPONENT-SIZE', rel, info['line'],
                     f'{info["name"]}: {info["ts_lines"]} lines ts, {info["template_lines"]} lines template')
        if info['inputs'] > 10:
            hits.add('NG-MANY-INPUTS', rel, info['line'], f'{info["name"]}: {info["inputs"]} inputs')
        if len(info['injects']) > 5:
            hits.add('NG-MANY-INJECTS', rel, info['line'], f'{info["name"]}: injects {", ".join(info["injects"])}')
        if LAYERS.search('/' + rel) and info['injects'] and info['kind'] == 'component':
            hits.add('NG-LAYER-INJECT', rel, info['line'],
                     f'{info["name"]} ({LAYERS.search("/" + rel).group(1)}) injects {", ".join(info["injects"])}')
        http = [i for i in info['injects'] if i == 'HttpClient' or re.search(r'(Api|ApiService|Client|Http)$', i)]
        page = PAGE.search(rel)
        if http and info['kind'] == 'component' and not (page and len(http) == 1):
            hits.add('NG-COMPONENT-HTTP', rel, info['line'], f'{info["name"]} injects {", ".join(http)}',
                     **({'severity': 'low', 'note': 'page orchestrating several APIs - a state service would hold '
                                                    'what they share'} if page else {}))
        if not re.search(r'takeUntilDestroyed|takeUntil\s*\(|DestroyRef|\.unsubscribe\s*\(|untilDestroyed|'
                         r'Subscription\b', bare):
            long_lived = []
            for sm in re.finditer(r'\.\s*subscribe\s*\(', bare):
                stmt = re.split(r'[;{}]', bare[max(0, sm.start() - 400):sm.start()])[-1]
                if LONG_LIVED.search(stmt) and not re.search(r'\b(first|take)\s*\(', stmt):
                    long_lived.append(sm)
            if long_lived:
                hits.add('NG-SUBSCRIBE-LEAK', rel, src.line_at(long_lived[0].start()),
                         f'{info["name"]}: {len(long_lived)} subscribe() on a long-lived stream, no teardown - '
                         + src.line(src.line_at(long_lived[0].start())).strip()[:80])
    return out



def route_inventory(w: Workspace, hits: Hits) -> list[dict]:
    routes, lazy = [], []
    for rel in w.main_ts:
        src = w.repo.source(rel)
        bare, code = src.bare, src.code
        if not re.search(r'\bpath\s*:', bare) or not re.search(
                r'\b(component|loadComponent|loadChildren|redirectTo|children)\s*:', bare):
            continue
        objs = _objects(bare)
        owned = defaultdict(dict)
        for km in re.finditer(r'\b(path|component|loadComponent|loadChildren|redirectTo|children|canActivate|'
                              r'canMatch|canActivateChild|canLoad|resolve|providers|title)\s*:', bare):
            idx = _innermost(objs, km.start())
            if idx is not None:
                owned[idx].setdefault(km.group(1), km.end())
        file_routes = {}
        for idx, keys in owned.items():
            if 'path' not in keys:
                continue
            value = re.match(r'\s*[\'"`]([^\'"`]*)[\'"`]', code[keys['path']:keys['path'] + 200])
            target = ''
            for k in ('component', 'loadComponent', 'loadChildren'):
                if k in keys:
                    snippet = code[keys[k]:min(keys[k] + 240, objs[idx][1])]
                    imp = re.search(r'import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', snippet)
                    name = re.match(r'\s*(\w+)', snippet)
                    target = f'{k}: {imp.group(1) if imp else (name.group(1) if name else "?")}'
                    if k == 'loadChildren' and imp:
                        lazy.append((rel, idx, imp.group(1)))
                    break
            guards = []
            for g in ('canActivate', 'canMatch', 'canActivateChild', 'canLoad'):
                if g in keys:
                    arr = code[keys[g]:keys[g] + 200]
                    names = re.findall(r'(\w+(?:Guard|guard|Fn)?)\b', arr.split(']')[0])
                    guards.append(f'{g}: {", ".join(n for n in names if n not in ("inject", "map"))[:60]}')
            file_routes[idx] = {'file': rel, 'line': src.line_at(objs[idx][0]),
                                'segment': value.group(1) if value else '?', 'target': target,
                                'redirect': 'redirectTo' in keys, 'children': 'children' in keys,
                                'guards': guards, '_idx': idx}
        for idx, r in file_routes.items():
            parent, chain = objs[idx][2], []
            while parent is not None:
                if parent in file_routes:
                    chain.append(file_routes[parent])
                parent = objs[parent][2]
            r['_parents'] = chain
        routes += file_routes.values()

    by_file_idx = {(r['file'], r['_idx']): r for r in routes}
    links = []
    for rel, idx, spec in lazy:
        parent = by_file_idx.get((rel, idx))
        if spec.startswith('.'):
            base = os.path.normpath(os.path.join(os.path.dirname(rel), spec))
        else:
            alias = max((a for a in w.aliases if spec == a or spec.startswith(a + '/')), key=len, default=None)
            base = w.aliases.get(alias, '') if alias else ''
        if not base:
            continue
        base = re.sub(r'\.ts$', '', base)
        scope = os.path.dirname(os.path.dirname(base)) if base.endswith(('/index', 'src/index')) else \
            os.path.dirname(base) if os.path.basename(base) != base else base
        links.append((scope, base, parent))
    for r in routes:
        if r['_parents']:
            continue
        match = max(((scope, base, parent) for scope, base, parent in links
                     if parent and parent['file'] != r['file'] and
                     (r['file'].startswith(base) or r['file'].startswith(scope + '/'))),
                    key=lambda x: len(x[0]), default=None)
        if match:
            r['_lazy'] = match[2]
            r['lazy_parent'] = f'{match[2]["file"]}:{match[2]["line"]}'

    def effective(r: dict, seen: frozenset) -> tuple[str, bool, bool, str]:
        chain = r['_parents']
        root = chain[-1] if chain else r
        base_path, base_guard, app = '', False, root['file']
        if root.get('_lazy') is not None and id(root['_lazy']) not in seen:
            base_path, own, inherited, app = effective(root['_lazy'], seen | {id(r)})
            base_guard = own or inherited
        segments = [base_path.strip('/')] + [p['segment'] for p in reversed(chain)] + [r['segment']]
        path = '/' + '/'.join(s.strip('/') for s in segments if s and s.strip('/'))
        return path, bool(r['guards']), base_guard or any(p['guards'] for p in chain), app

    for r in routes:
        r['path'], _, r['inherited'], r['app'] = effective(r, frozenset())
    for r in routes:
        r.pop('_lazy', None)

    guarded = [r for r in routes if r['guards']]
    for r in routes:
        if r['redirect'] or r['segment'] == '**' or not (r['target'] or r['children']):
            continue
        if not r['guards'] and not r['inherited'] and SENSITIVE_ROUTE.search(r['path']):
            same_app = [g for g in guarded if w.route_app(g) == w.route_app(r)]
            if same_app:
                hits.add('NG-ROUTE-UNGUARDED', r['file'], r['line'],
                         f'{r["path"]} ({r["target"] or "children"}) - guarded sibling: {same_app[0]["path"]} '
                         f'({same_app[0]["guards"][0]})')
    for r in routes:
        for k in ('_idx', '_parents'):
            r.pop(k, None)
    return routes



def check_security(w: Workspace, hits: Hits, routes: list[dict]):
    repo = w.repo
    has_auth = False
    for rel in w.main_ts:
        src = repo.source(rel)
        bare, code = src.bare, src.code
        for m in re.finditer(r'\bbypassSecurityTrust(Html|Script|Style|Url|ResourceUrl)\s*\(', bare):
            hits.add('NG-BYPASS-SANITIZER', rel, src.line_at(m.start()), src.line(src.line_at(m.start())).strip())
        for m in re.finditer(r'\.(innerHTML|outerHTML)\s*=(?!=)|\binsertAdjacentHTML\s*\(|\bdocument\s*\.\s*write(ln)?\s*\(|'
                             r'(?<![\w.])eval\s*\(|\bnew\s+Function\s*\(|\bset(Timeout|Interval)\s*\(\s*[\'"`]|'
                             r'createContextualFragment\s*\(|setProperty\s*\([^,]+,\s*[\'"]innerHTML[\'"]', code):
            if re.search(r'contentWindow\s*\??\.\s*$', code[max(0, m.start() - 30):m.start()]):
                continue
            hits.add('NG-DOM-XSS', rel, src.line_at(m.start()), src.line(src.line_at(m.start())).strip())
        for m in re.finditer(r'\b(localStorage|sessionStorage)\s*\.\s*setItem\s*\(\s*([^,]+),', code):
            if re.search(r'(?i)(token|jwt|auth|access|refresh|session|bearer|id_token|credential)', m.group(2)):
                hits.add('NG-TOKEN-STORAGE', rel, src.line_at(m.start()), src.line(src.line_at(m.start())).strip())
        for m in re.finditer(r'\b(localStorage|sessionStorage)\s*\[\s*[\'"][^\'"]*(?i:token|jwt)[^\'"]*[\'"]\s*\]\s*=|'
                             r'\bstorage\s*:\s*(localStorage|sessionStorage)\b', code):
            hits.add('NG-TOKEN-STORAGE', rel, src.line_at(m.start()), src.line(src.line_at(m.start())).strip())
        for m in re.finditer(r'\bwithNoXsrfProtection\s*\(|HttpClientXsrfModule\s*\.\s*disable\s*\(', bare):
            hits.add('NG-XSRF-OFF', rel, src.line_at(m.start()), src.line(src.line_at(m.start())).strip())
        for m in re.finditer(r'(?<![\w.])fetch\s*\(|\bnew\s+XMLHttpRequest\s*\(|\baxios\s*[.(]|\bnew\s+HttpClient\s*\(|'
                             r'inject\s*\(\s*HttpBackend\s*\)|:\s*HttpBackend\b', bare):
            extra = {}
            if m.group(0).startswith('fetch'):
                url = (_args(src, m.end() - 1) or [''])[0]
                url = _const_value(code, url) or url if re.fullmatch(r'[\w.]+', url) else url
                start, end = _function_body(bare, m.start())
                if PRE_BOOTSTRAP.search(url) and not re.search(r'\binject\s*\(', bare[start:end]):
                    extra = {'severity': 'low', 'note': 'pre-bootstrap fetch of a static file or health check - '
                                                        'no injector yet, nothing to authenticate'}
            hits.add('NG-INTERCEPTOR-BYPASS', rel, src.line_at(m.start()), src.line(src.line_at(m.start())).strip(),
                     **extra)
        if re.search(r'HttpInterceptorFn|implements\s+HttpInterceptor\b', bare) and \
                re.search(r'Authorization|Bearer', code) and not re.search(r'\.url\b|urlWithParams|\burlPattern\b', code):
            m = re.search(r'Authorization|Bearer', code)
            hits.add('NG-TOKEN-ALL-HOSTS', rel, src.line_at(m.start()), src.line(src.line_at(m.start())).strip())
        for m in re.finditer(r'\bincludeBearerTokenInterceptor\b|\benableBearerInterceptor\s*:\s*true', code):
            if not re.search(r'urlPattern|bearerExcludedUrls|shouldAddToken', code):
                hits.add('NG-TOKEN-ALL-HOSTS', rel, src.line_at(m.start()), src.line(src.line_at(m.start())).strip())
        if re.search(r'(?i)\b(login|logout|isAuthenticated|isLoggedIn|accessToken|authService|oidc|keycloak|msal)\b', bare):
            has_auth = True
        if re.search(r'(^|/)environment[\w.-]*\.ts$', rel):
            dev_file = re.search(r'(?i)(dev|local|test|e2e|mock|stub)', os.path.basename(rel))
            for m in re.finditer(r'(\w+)\s*:\s*[\'"`]([^\'"`]{4,})[\'"`]', code):
                key, value = m.group(1), m.group(2)
                if re.search(r'(?i)(secret|password|passwd|private.?key|client.?secret|token)$', key) and \
                        not value.startswith(('${', '%', '<', '{{')):
                    hits.add('NG-SECRET-IN-CLIENT', rel, src.line_at(m.start()), f'{key}: {redact(value)}',
                             severity='medium' if dev_file else None)
                elif re.search(r'(?i)api.?key$', key) and not value.startswith(('${', '%', '<')):
                    hits.add('NG-SECRET-IN-CLIENT', rel, src.line_at(m.start()), f'{key}: {redact(value)}',
                             severity='low', note='public API keys are fine when restricted by referrer')
            if not dev_file:
                for m in re.finditer(r'[\'"`](http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\])[^\'"`]+)', code):
                    hits.add('NG-HTTP-INSECURE', rel, src.line_at(m.start()), m.group(1))
        if re.search(r'(^|/)(server|main\.server)\.ts$', rel):
            for m in re.finditer(r'\bnew\s+CommonEngine\s*\(|\brenderModule\s*\(|\brenderApplication\s*\(', bare):
                hits.add('NG-SSR-PATTERN', rel, src.line_at(m.start()), src.line(src.line_at(m.start())).strip())
            boot = re.search(r'bootstrapApplication\s*\(([^)]*)\)', bare)
            if rel.endswith('main.server.ts') and boot and len(split_top(boot.group(1))) < 3 and \
                    'BootstrapContext' not in bare and 'context' not in boot.group(1):
                hits.add('NG-SSR-PATTERN', rel, src.line_at(boot.start()),
                         'bootstrapApplication without the BootstrapContext (CVE-2025-59052 shape)')
            for m in re.finditer(r'\b(req|request)\s*\.\s*(headers|get)\b[^\n]*\b(host|x-forwarded)', code, re.I):
                hits.add('NG-SSR-PATTERN', rel, src.line_at(m.start()), src.line(src.line_at(m.start())).strip())

    apps = defaultdict(list)
    for r in routes:
        apps[w.route_app(r)].append(r)
    for app, app_routes in apps.items() if has_auth else ():
        if any(r['guards'] or r['inherited'] for r in app_routes):
            continue
        if len(apps) == 1:
            hits.add('NG-NO-GUARDS', routes[0]['file'], routes[0]['line'],
                     f'{len(routes)} routes, none guarded, auth code present')
        elif any(SENSITIVE_ROUTE.search(r['path']) and not re.search(r'(?i):\w*token', r['path']) for r in app_routes):
            hits.add('NG-NO-GUARDS', app_routes[0]['file'], app_routes[0]['line'],
                     f'{app}: {len(app_routes)} routes, none guarded, auth code present')

    build_configs = []
    for name in ('angular.json', 'workspace.json'):
        p = repo.root / w.prefix / name
        if p.is_file():
            data = _json(p.read_text(encoding='utf-8', errors='replace')) or {}
            for pname, spec in (data.get('projects') or {}).items():
                if isinstance(spec, dict):
                    build_configs.append((w.prefix + name, pname, spec.get('architect') or spec.get('targets') or {}))
    for pj in (f for f in w.files if f.endswith('/project.json')):
        data = _json(repo.source(pj).text) or {}
        build_configs.append((pj, data.get('name', pj), data.get('targets') or {}))
    auto_csp, allowed_hosts = False, None
    for rel, pname, targets in build_configs:
        build = targets.get('build') or {}
        options = build.get('options') or {}
        sec = options.get('security') or {}
        auto_csp |= bool(sec.get('autoCsp'))
        if 'allowedHosts' in sec:
            allowed_hosts = sec['allowedHosts']
        prod = (build.get('configurations') or {}).get('production') or {}
        sm = prod.get('sourceMap', options.get('sourceMap'))
        if sm is True or (isinstance(sm, dict) and sm.get('scripts') and not sm.get('hidden')):
            src = repo.source(rel)
            line = next((i for i, l in enumerate(src.lines, 1) if '"sourceMap"' in l), None)
            hits.add('NG-PROD-SOURCEMAP', rel, line, f'{pname}: production sourceMap = {json.dumps(sm)}')
    server_text = '\n'.join(repo.source(f).text for f in w.files
                            if re.search(r'(^|/)(server|main\.server)\.ts$', f))
    if w.ws['ssr'] and server_text:
        hosts = re.search(r'allowedHosts\s*:\s*\[([^\]]*)\]', server_text)
        values = allowed_hosts if allowed_hosts is not None else (strings_in(hosts.group(1)) if hosts else None)
        if values is None and 'NG_ALLOWED_HOSTS' not in server_text:
            hits.add('NG-SSR-HOSTS', next((f for f in w.files if f.endswith('angular.json')), None), None,
                     'SSR without allowedHosts')
        elif values and '*' in values:
            hits.add('NG-SSR-HOSTS', next((f for f in w.files if f.endswith('angular.json')), None), None,
                     f'allowedHosts: {values}')
    index_csp = any('Content-Security-Policy' in repo.source(f).text for f in w.files if f.endswith('index.html'))
    edge_csp = any(re.search(r'Content-Security-Policy', repo.source(f).text) for f in repo.files
                   if f.endswith(('.conf', '_headers', 'vercel.json', 'firebase.json', 'netlify.toml',
                                  'staticwebapp.config.json', '.ts', '.js', 'Caddyfile', '.yaml', '.yml'))
                   and not is_test_path(f))
    if not (index_csp or auto_csp or edge_csp or 'ngCspNonce' in server_text or 'CSP_NONCE' in server_text):
        hits.add('NG-NO-CSP', next((f for f in w.files if f.endswith('index.html')), None), None,
                 'no CSP meta tag, no security.autoCsp, no CSP header in any server config of the repo')



URL_RECV = r'\b((?:\w+\s*\??\.\s*)*\w*(?:[uU]rl|URL|[uU]ri|href)\w*)\s*\??\.\s*'
HOST_CHECK = re.compile(URL_RECV + r'(startsWith|includes)\s*\(|' + URL_RECV + r'(indexOf)\s*\(')
REGEX_LIT = r'/((?:\\.|\[(?:\\.|[^\]\\\n])*\]|[^/\\\n\[])+)/([gimsuy]*)'
SETS_TOKEN = re.compile(r'\bAuthorization\b|\bBearer\b|includeBearerTokenCondition|INCLUDE_BEARER_TOKEN_INTERCEPTOR_CONFIG|'
                        r'createInterceptorCondition|shouldAddToken|bearerPrefix')
TOKEN_EXPR = re.compile(r'(?i)(?<![\w])(?!(?:next|page|continuation)_?token)\w*token\w*')
HTTP_CALL = re.compile(r'\b\w*[hH]ttp\w*\s*\.\s*(get|post|put|patch|delete|head|request|jsonp)\s*(?:<[^()]*?>)?\s*\(|'
                       r'\bhttpResource(?:\s*\.\s*\w+)?\s*(?:<[^()]*?>)?\s*\(|(?<![\w.])fetch\s*\(')


def _env_values(w: Workspace, key: str) -> list[str]:
    out = []
    for rel in w.main_ts:
        if re.search(r'(^|/)environment[\w.-]*\.ts$', rel):
            out += re.findall(r'\b' + re.escape(key) + r'\s*:\s*[\'"`]([^\'"`]*)[\'"`]', w.repo.source(rel).code)
    return out


def _prefix_safe(w: Workspace, code: str, arg: str) -> bool | None:
    """Whether a startsWith base keeps the host boundary: True, False, or None when it cannot be resolved."""
    arg = arg.strip()
    lit = re.fullmatch(r'([\'"`])([^\'"`$]*)\1', arg)
    values = [lit.group(2)] if lit else []
    if not values and re.search(r'/[\'"`]\s*$|\+\s*[\'"]/[\'"]\s*$', arg):
        return True
    if not values and re.fullmatch(r'[\w.]+(\(\))?', arg):
        name = arg.rstrip('()').split('.')[-1]
        const = _const_value(code, name)
        values = [const] if const is not None else re.findall(r'\b' + name + r'\s*:\s*[\'"`]([^\'"`]*)[\'"`]', code) \
            or (_env_values(w, name) if '.' in arg else [])
    if not values:
        return None
    return all(v.endswith('/') or (v.startswith('/') and not v.startswith('//')) for v in values)


def _weak_regex(source: str, flags: str) -> bool:
    try:
        rx = re.compile(source, re.I if 'i' in flags else 0)
    except re.error:
        return False
    flat = re.sub(r'\(\?:|[()^]', '', source)
    lit = re.match(r'(?:\\[/.:-]|[\w:/-]|\.(?![*+?{]))*', flat).group(0).replace('\\', '')
    host = re.match(r'(?:https?:)?//[^/]+', lit)
    if host:
        probes = [host.group(0) + '.evil.tld/x', 'https://evil.tld/?u=' + lit]
    elif lit.startswith('/'):
        probes = ['https://evil.tld' + lit + 'x']
    else:
        probes = ['https://evil.tld/x']
    return any(rx.search(p) for p in probes)


def _exclusion(bare: str, pos: int) -> bool:
    """The match sits in `if (url check) return next(req)` - a skip list, where a bypass sends no token."""
    for m in re.finditer(r'\bif\s*\(', bare[max(0, pos - 300):pos]):
        start = max(0, pos - 300) + m.end() - 1
        close = balanced(bare, start)
        if close > pos:
            negated = re.search(r'!\s*\(?\s*$', bare[start + 1:pos])
            body = bare[close + 1:close + 120].lstrip().lstrip('{').lstrip()
            return not negated and bool(re.match(r'return\s+next\s*(\.\s*handle\s*)?\(\s*\w+\s*\)', body))
    return False


def check_tokens(w: Workspace, hits: Hits):
    for rel in w.main_ts:
        src = w.repo.source(rel)
        code, bare = src.code, src.bare
        if SETS_TOKEN.search(code) and not re.search(r'new\s+URL\s*\([^)]*\)\s*\.\s*(origin|host|hostname)\b|'
                                                     r'\.\s*(origin|hostname)\s*[!=]==?', code):
            for m in HOST_CHECK.finditer(bare):
                method = m.group(2) or m.group(4)
                if method == 'indexOf':
                    after = bare[balanced(bare, m.end() - 1) + 1:][:20]
                    if re.match(r'\s*(===?|<=?)\s*0\b', after):
                        method = 'startsWith'
                    elif re.match(r'\s*(!==?\s*-\s*1|>\s*-\s*1|>=\s*0)', after):
                        method = 'includes'
                    else:
                        continue
                safe = _prefix_safe(w, code, (_args(src, m.end() - 1) or [''])[0]) if method == 'startsWith' else False
                if safe or _exclusion(bare, m.start()):
                    continue
                line = src.line_at(m.start())
                hits.add('NG-TOKEN-HOST-PREFIX', rel, line, src.line(line).strip(),
                         **({'note': 'base not resolved - safe only if it always ends with /'} if safe is None else {}))
            for m in re.finditer(r'\burlPattern\s*:\s*' + REGEX_LIT + r'|' + REGEX_LIT + r'\s*\.\s*test\s*\(\s*' +
                                 URL_RECV.replace(r'\s*\??\.\s*', '') + r'\s*\)', code):
                source, flags = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
                if _weak_regex(source, flags) and not _exclusion(bare, m.start()):
                    line = src.line_at(m.start())
                    hits.add('NG-TOKEN-HOST-PREFIX', rel, line, src.line(line).strip())
        found = []
        for m in HTTP_CALL.finditer(bare):
            args = _args(src, m.end() - 1)[1 if m.group(1) == 'request' else 0:]
            arg_code = args[0] if args else ''
            pieces = re.findall(r'\$\{([^}]*)\}', arg_code) + re.findall(r'\+\s*([\w.]+(?:\(\))?)', arg_code)
            if any(TOKEN_EXPR.search(p) for p in pieces) or re.search(r'/:token\b|/token/(\$\{|[\'"]\s*\+)', arg_code):
                found.append(m)
        if found:
            line = src.line_at(found[0].start())
            hits.add('NG-TOKEN-IN-PATH', rel, line, src.line(line).strip(),
                     **({'note': f'{len(found)} calls in this file'} if len(found) > 1 else {}))


def _sandbox(tag: str) -> tuple[str, str] | None:
    """(severity, reason) for an <iframe ...> tag, None when its sandbox keeps scripts out."""
    m = re.search(r'\ssandbox(?:\s*=\s*(?:"([^"]*)"|\'([^\']*)\'))?', tag)
    if not m:
        return 'medium', 'iframe without sandbox'
    tokens = set((m.group(1) or m.group(2) or '').split())
    if 'allow-scripts' not in tokens:
        return None
    if 'allow-same-origin' in tokens:
        return 'medium', 'sandbox with allow-scripts and allow-same-origin - the frame can lift its own sandbox'
    return 'low', 'allow-scripts in an opaque origin'


def check_iframes(w: Workspace, hits: Hits, comps: list[dict]):
    by_file = {c['file']: c for c in comps}
    for rel in w.main_ts:
        src = w.repo.source(rel)
        code = src.code
        if 'contentDocument' not in code and 'contentWindow' not in code and 'srcdoc' not in code:
            continue
        aliases = re.findall(r'\b(?:const|let|var)\s+(\w+)\s*=\s*[^;\n]*\.\s*(?:contentDocument|contentWindow\s*\??\.\s*document)\b'
                             r'(?!\s*\??\.)', code)
        sink = re.compile(r'\.\s*(?:contentDocument|contentWindow\s*\??\.\s*document)\s*\??\.\s*write(?:ln)?\s*\(|'
                          r'\.\s*srcdoc\s*=(?!=)|setAttribute\s*\(\s*[\'"]srcdoc[\'"]' +
                          ''.join(r'|\b' + a + r'\s*\??\.\s*write(?:ln)?\s*\(' for a in aliases))
        writes = list(sink.finditer(code))
        comp = by_file.get(rel)
        html = (w.repo.source(comp['template']).code if comp['template'] else comp.get('inline_html') or '') if comp else ''
        bound = re.search(r'\[(?:attr\.)?srcdoc\]\s*=', html)
        if not writes and not bound:
            continue
        frames = re.findall(r'<iframe\b[^>]*>', html)
        made = re.findall(r'(?:sandbox\s*\.\s*(?:add|value)\s*[(=]|setAttribute\s*\(\s*[\'"]sandbox[\'"]\s*,)\s*'
                          r'[\'"`]([^\'"`]*)', code)
        if frames:
            verdicts = [_sandbox(f) for f in frames]
        elif made or re.search(r'createElement\s*\(\s*[\'"]iframe', code):
            verdicts = [_sandbox(f' sandbox="{" ".join(made)}"' if made else '')]
        else:
            verdicts = [('medium', 'iframe not in this template - check its sandbox')]
        worst = next((v for v in verdicts if v and v[0] == 'medium'), next((v for v in verdicts if v), None))
        if not worst:
            continue
        severity, reason = worst
        if not writes and 'bypassSecurityTrustHtml' not in code:
            severity = 'low'
            reason += '; [srcdoc] is sanitized by Angular'
        at = writes[0].start() if writes else None
        line = src.line_at(at) if at is not None else None
        hits.add('NG-IFRAME-WRITE', rel, line, (src.line(line).strip() if line else f'{comp["name"]}: [srcdoc] binding')
                 + f' - {reason}', severity=severity)


IMPLICIT = {'typescript', 'tslib', '@angular/compiler', '@angular/compiler-cli', '@angular/language-service',
            '@angular/cli', '@angular-devkit/core', '@angular-devkit/schematics', '@schematics/angular', '@types/node',
            'nx', '@nx/workspace', '@nx/devkit', '@swc/core', '@swc/helpers', '@swc-node/register', 'ts-node', 'jiti',
            'prettier', 'rxjs'}
BUILD_TOOL = re.compile(r'^(@angular-devkit/|@angular/(build|cli|compiler-cli|language-service)$|@schematics/|nx$|@nx/|'
                        r'typescript$|typescript-eslint$|@typescript-eslint/|eslint|@eslint/|angular-eslint$|@angular-eslint/|'
                        r'jest|@jest/|ts-jest$|karma|jasmine|vitest$|@vitest/|vite$|@analogjs/vite|webpack|prettier|'
                        r'@types/|ng-packagr$|@playwright/test$|cypress$)')
CONFIG_FILE = re.compile(r'^((angular|project|nx|workspace)\.json|tsconfig[\w.-]*\.json|\.?(eslint|jest|vitest|vite|karma|'
                         r'playwright|cypress|prettier|babel|postcss|tailwind|stylelint|lint-?staged|commitlint|webpack|'
                         r'proxy|swc)[\w.-]*|\.(eslintrc|prettierrc|babelrc|swcrc|stylelintrc)[\w.]*)$')
IMPORT_SPEC = re.compile(r'(?:\bfrom\s*|\bimport\s*\(?\s*|\brequire\s*\(\s*|\b(?:jest|vi)\s*\.\s*(?:mock|requireActual|'
                         r'importActual)\s*\(\s*|@(?:use|import|forward)\s+|reference\s+types\s*=\s*)[\'"]~?([^\'"\s]+)[\'"]')
IMPLIED_BY = [(re.compile(r'^(@eslint/|@typescript-eslint/|typescript-eslint$|@angular-eslint/|angular-eslint$|'
                          r'eslint-(plugin|config)-|jsonc-eslint-parser$)'), 'eslint'),
              (re.compile(r'^prettier-plugin-'), 'prettier'), (re.compile(r'^(@vitest/|jsdom$|happy-dom$)'), 'vitest'),
              (re.compile(r'^jest-environment-|^jsdom$'), 'jest'), (re.compile(r'^karma-'), 'karma'),
              (re.compile(r'^jasmine-core$'), 'karma-jasmine'), (re.compile(r'^@oxc-project/runtime$'), 'vite')]


def _package(spec: str) -> str | None:
    if spec.startswith(('.', '/', 'node:')) or not re.match(r'[@\w]', spec):
        return None
    parts = spec.split('/')
    return '/'.join(parts[:2]) if spec.startswith('@') else parts[0]


def _mentioned(name: str, text: str) -> bool:
    return re.search(r'(?:(?<![\w@/.-])|(?<=node_modules/))' + re.escape(name) + r'(?![\w-])', text) is not None


def check_packages(w: Workspace, hits: Hits):
    rel = w.prefix + 'package.json'
    pkg = _json(w.repo.source(rel).text) if rel in w.repo.files else None
    if not isinstance(pkg, dict):
        return
    prod, dev = pkg.get('dependencies') or {}, pkg.get('devDependencies') or {}
    lines = w.repo.source(rel).lines

    def line_of(name: str) -> int | None:
        return next((i for i, l in enumerate(lines, 1) if f'"{name}"' in l), None)

    tools = sorted(n for n in prod if BUILD_TOOL.match(n))
    if tools:
        hits.add('DEPS-BUILD-IN-PROD', rel, line_of(tools[0]), f'{len(tools)} build tools under dependencies: '
                 + ', '.join(tools[:10]), names=tools)

    declared = {**prod, **dev}
    used = set(IMPLICIT)
    for f in w.files:
        if f.endswith(('.ts', '.tsx', '.js', '.mjs', '.cjs', '.jsx', '.mts', '.cts', '.scss', '.sass', '.css', '.html')):
            text = w.repo.source(f).text
            used |= {p for p in map(_package, IMPORT_SPEC.findall(text)) if p}
            used |= {x for x in re.findall(r'[\'"`](@?[\w.-]+(?:/[\w.-]+)?)[/\'"`]', text) if x in declared}
    configs = '\n'.join(w.repo.source(f).text for f in w.files if CONFIG_FILE.match(os.path.basename(f)))
    scripts = ' '.join(str(v) for v in (pkg.get('scripts') or {}).values())
    modules = w.repo.root / w.prefix / 'node_modules'
    bins = {}
    for name in declared:
        meta = _json((modules / name / 'package.json').read_text(encoding='utf-8', errors='replace')) \
            if (modules / name / 'package.json').is_file() else None
        if not isinstance(meta, dict):
            continue
        optional = {k for k, v in (meta.get('peerDependenciesMeta') or {}).items() if isinstance(v, dict) and v.get('optional')}
        used |= (set(meta.get('peerDependencies') or {}) - optional) | set(meta.get('dependencies') or {})
        b = meta.get('bin')
        bins[name] = [name.split('/')[-1]] if isinstance(b, str) else list(b) if isinstance(b, dict) else []

    def referenced(name: str) -> bool:
        if name in used or _mentioned(name, configs) or _mentioned(name, scripts) or \
                any(_mentioned(b, scripts) for b in bins.get(name, [name.split('/')[-1]])):
            return True
        if name.startswith('@types/'):
            base = name[7:].replace('__', '/')
            base = '@' + base if '/' in base else base
            return referenced(base) if base in declared else base in used or _mentioned(base, configs)
        return any(rx.match(name) and parent in declared and referenced(parent) for rx, parent in IMPLIED_BY)

    unused = sorted(n for n in declared if not referenced(n))
    if unused:
        hits.add('DEPS-UNUSED', rel, line_of(unused[0]), f'{len(unused)} packages nothing references: '
                 + ', '.join(unused[:12]), names=unused)


def check_templates(w: Workspace, hits: Hits, comps: list[dict]):
    sources = [(f, w.repo.source(f).code) for f in w.html]
    sources += [(c['file'], c['inline_html']) for c in comps if c.get('inline_html')]
    legacy_cf, ngclass, track_index, logic = defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int)
    for rel, html in sources:
        src_line = (lambda off, h=html: h.count('\n', 0, off) + 1)
        for m in re.finditer(r'\[innerHTML\]\s*=', html):
            hits.add('NG-INNERHTML-BINDING', rel, src_line(m.start()), html.split('\n')[src_line(m.start()) - 1].strip())
        for m in re.finditer(r'\[\((innerHTML|outerHTML|src|href)\)\]|bindon-(innerHTML|src|href)|'
                             r'i18n-(href|src|action|formaction|xlink:href|on\w+)\b|\[attr\.xlink:href\]|'
                             r'<script[^>]*\[(attr\.)?(xlink:)?href\]|\[attr\.attributeName\]|attributeName\s*=\s*"\{\{',
                             html):
            hits.add('NG-SANITIZER-CVE-PATTERN', rel, src_line(m.start()), m.group(0))
        legacy_cf[rel] += len(re.findall(r'\*ng(If|For|Switch\w*)\s*=', html))
        ngclass[rel] += len(re.findall(r'\[?ng(Class|Style)\]?\s*=', html))
        track_index[rel] += len(re.findall(r'@for\s*\([^)]*track\s+\$index', html))
        for m in re.finditer(r'\{\{([^}]*)\}\}', html):
            expr = m.group(1).split('|')[0]
            if re.search(r'\w+\s*\(\s*[^)\s]', expr) or re.search(r'[\w)\]]\s*[+\-*/%]\s*[\w(]', expr) or \
                    expr.count('?') >= 2:
                logic[rel] += 1
    _aggregate(hits, 'NG-LEGACY-CONTROL-FLOW', legacy_cf, len(sources), 'templates',
               severity='medium' if w.major >= 22 else None)
    _aggregate(hits, 'NG-NGCLASS', ngclass, len(sources), 'templates')
    _aggregate(hits, 'NG-TRACK-INDEX', track_index, len(sources), 'templates')
    _aggregate(hits, 'NG-TEMPLATE-LOGIC', logic, len(sources), 'templates')


def _aggregate(hits: Hits, check: str, counts: dict, total: int, unit: str, severity: str | None = None):
    found = {f: n for f, n in counts.items() if n}
    if not found:
        return
    top = sorted(found.items(), key=lambda kv: -kv[1])
    hits.add(check, top[0][0], None,
             f'{len(found)} of {total} {unit}, {sum(found.values())} occurrences - '
             + ', '.join(f'{os.path.basename(f)} ({n})' for f, n in top[:8]),
             severity=severity, files=[f for f, _ in top[:40]])



def check_structure(w: Workspace, hits: Hits, comps: list[dict]):
    repo = w.repo
    legacy, standalone, ngmodule, anys, console, detect, rxstate = (defaultdict(int) for _ in range(7))
    inline = {c['file']: 1 for c in comps if c['inline_template'] or c['inline_styles']}
    for c in comps:
        if c['standalone_true'] and w.major >= 19:
            standalone[c['file']] += 1
    real = [c for c in comps if c['kind'] == 'component']
    if w.major >= 22:
        _aggregate(hits, 'NG-ONPUSH', {c['file']: 1 for c in real if c['onpush']}, len(real),
                   'components set OnPush explicitly (default since v22)')
    elif real:
        without = {c['file']: 1 for c in real if not c['onpush']}
        if without and len(without) < len(real):
            _aggregate(hits, 'NG-ONPUSH', without, len(real), 'components without OnPush', severity='medium')
    for rel in w.main_ts:
        src = repo.source(rel)
        bare = src.bare
        legacy[rel] += len(re.findall(r'@(Input|Output|ViewChild|ViewChildren|ContentChild|ContentChildren)\s*\(|'
                                      r'\bnew\s+EventEmitter\b', bare))
        ngmodule[rel] += len(re.findall(r'@NgModule\s*\(', bare))
        anys[rel] += len(re.findall(r'\.(get|post|put|patch|delete|request)\s*<\s*any\s*>|:\s*Observable\s*<\s*any\s*>',
                                    bare))
        console[rel] += len(re.findall(r'\bconsole\s*\.\s*(log|debug|info|trace)\s*\(', bare))
        detect[rel] += len(re.findall(r'\.\s*detectChanges\s*\(\s*\)', bare))
        if '@Injectable' in bare:
            rxstate[rel] += len(re.findall(r'\bnew\s+BehaviorSubject\s*[<(]', bare))
            exposed = [m for m in re.finditer(r'(?m)^\s*(?!private|#|protected)(?:readonly\s+)?(?:public\s+)?\w+\s*='
                                              r'\s*(signal|computed|linkedSignal|resource|rxResource|httpResource|'
                                              r'toSignal)\s*[<(]', bare)]
            if len(exposed) > 15:
                hits.add('NG-STATE-SIZE', rel, None, f'{len(exposed)} exposed signals/resources')
            injected = [i for i in re.findall(r'\binject\s*\(\s*(\w+)', bare) if i not in TRIVIAL_INJECT]
            if len(injected) > 5:
                hits.add('NG-MANY-INJECTS', rel, None, f'injects {", ".join(injected)}')
        for m in re.finditer(r'\beffect\s*\(', bare):
            close = balanced(bare, m.end() - 1)
            body = bare[m.end():close]
            if re.search(r'\.\s*(set|update)\s*\(', body):
                hits.add('NG-EFFECT-WRITES', rel, src.line_at(m.start()), src.line(src.line_at(m.start())).strip())
        for m in re.finditer(r'from\s+[\'"](@[\w.-]+/[\w.-]+(?:/[\w.-]+)*?)/(src|lib)/[^\'"]*[\'"]', src.code):
            hits.add('NG-DEEP-IMPORT', rel, src.line_at(m.start()), m.group(0), severity=None if w.ws['nx'] else 'medium')
        for m in re.finditer(r'from\s+[\'"](\.\./)+(?:[\w.-]+/)*libs/[^\'"]+[\'"]', src.code):
            hits.add('NG-DEEP-IMPORT', rel, src.line_at(m.start()), m.group(0))
        for api in REMOVED:
            m = re.search(api.pattern, src.code)
            if m and w.major >= api.flag_from:
                sev = 'high' if api.removed and w.major >= api.removed else \
                    'medium' if api.removed and w.major >= api.removed - 1 else 'low'
                hits.add('NG-REMOVED-API', rel, src.line_at(m.start()), api.label, severity=sev)
    total = len(w.main_ts)
    _aggregate(hits, 'NG-LEGACY-API', legacy, total, 'files')
    _aggregate(hits, 'NG-STANDALONE-TRUE', standalone, len(comps), 'components')
    _aggregate(hits, 'NG-INLINE-TEMPLATE', inline, len(comps), 'components')
    _aggregate(hits, 'NG-NGMODULE', ngmodule, total, 'files')
    _aggregate(hits, 'NG-ANY', anys, total, 'files')
    _aggregate(hits, 'NG-CONSOLE', console, total, 'files')
    _aggregate(hits, 'NG-DETECT-CHANGES', detect, total, 'files')
    _aggregate(hits, 'NG-RXJS-STATE', rxstate, total, 'files')
    if w.major >= 21 and 'zone.js' in w.ws['declared'] and not w.ws['zoneless']:
        hits.add('NG-ZONE', w.prefix + 'package.json', None, f'zone.js {w.ws["declared"]["zone.js"]} on Angular {w.ws["angular"]}')
    specs = set(f for f in w.ts if f.endswith('.spec.ts'))
    targets = [c['file'] for c in comps if c['kind'] == 'component'] + \
        [f for f in w.main_ts if '@Injectable' in repo.source(f).bare]
    missing = {f: 1 for f in targets if re.sub(r'\.ts$', '.spec.ts', f) not in specs}
    if targets and len(missing) > len(targets) * 0.3:
        _aggregate(hits, 'NG-NO-SPEC', missing, len(targets), 'components/services')
