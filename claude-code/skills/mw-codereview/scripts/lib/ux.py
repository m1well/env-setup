"""Usability for non-technical users: deletes without confirmation, forms without labels, hints, validation and
error messages, double submits, lists without an empty state."""
from __future__ import annotations

import os
import re
from collections import defaultdict

from .core import Hits, balanced, define, split_top

define('UX-DELETE-NO-CONFIRM', 'Delete or discard without a confirmation step', 'high', 'ux',
       'Only handlers that reach the backend (subscribe, an api or state call that writes) are listed - a row '
       'removed from a form is not. A confirm dialog, a "Kandidat" signal that opens one, a confirm directive on '
       'the button, or an undo counts.')
define('UX-NATIVE-DIALOG', 'window.confirm / alert / prompt', 'low', 'ux',
       'It confirms, but it blocks the page, ignores the design, cannot explain consequences and is hard to test.')
define('UX-INPUT-NO-LABEL', 'Form control without a label', 'medium', 'ux',
       'A placeholder is not a label - it disappears on the first keystroke. A <label for>, a wrapping label, a '
       'label input on the field wrapper, or aria-label.', rule='TPL-8')
define('UX-FORM-NO-VALIDATION', 'Form without any validation', 'medium', 'ux',
       'Every value goes to the backend as typed. Check whether the form is a search or filter - then it is fine.')
define('UX-FIELD-NO-VALIDATION', 'Important form fields without validation', 'medium', 'ux',
       'Email, IBAN, dates, amounts and names need required and format rules in the form, not only a 400 from '
       'the backend.')
define('UX-NO-ERROR-MESSAGE', 'Validation without a visible error message', 'medium', 'ux',
       'The form blocks, but nobody tells the user what is wrong. Check whether the field wrapper renders errors.')
define('UX-FORM-NO-HINT', 'Longer form without a single hint', 'low', 'ux',
       'Four or more fields and no help text, no description - every unclear field becomes a support call.')
define('UX-JARGON-NO-HINT', 'Label with an abbreviation and no explanation', 'low', 'ux',
       'IBAN, USt-IdNr, DATEV, BIC: a short hint says what goes in and where to find it.')
define('UX-DOUBLE-SUBMIT', 'Submit or save button that stays clickable while saving', 'medium', 'ux',
       'Two clicks, two records. Bind [disabled] to the pending state.')
define('UX-NO-UNSAVED-GUARD', 'Forms but no protection against losing unsaved input', 'low', 'ux',
       'A click on a menu entry drops everything typed. A canDeactivate guard on edit pages.')
define('UX-EMPTY-STATE', '@for over loaded data without @empty', 'low', 'ux',
       'An empty list renders nothing - the user cannot tell empty from loading from broken.', rule='TPL-1')
define('UX-ICON-BUTTON', 'Button without text or aria-label', 'low', 'ux',
       'An icon alone does not say what happens. Text, aria-label, or at least a title.', rule='TPL-8')
define('UX-PRIMARY-ACTION', 'Save action far below the first field of a long form', 'low', 'ux',
       'Open the page: is the primary action visible without scrolling, or sticky? The user should not search '
       'for the save button.')

VOID = {'input', 'img', 'br', 'hr', 'meta', 'link', 'source', 'area', 'col', 'embed', 'param', 'track', 'wbr'}
TAG = re.compile(r'<(/?)([a-zA-Z][\w:-]*)((?:\s+[^\s"\'>/=]+(?:\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s"\'=<>`]+))?)*)\s*(/?)>')
ATTR = re.compile(r'([^\s"\'>/=]+)(?:\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s"\'=<>`]+)))?')
DELETE = re.compile(r'(?i)(l[oö]e?sch|delete|remove|entfern|storn|k[uü]e?ndig|archiv|verwerf|discard|destroy|revoke|'
                    r'widerruf|purge|deaktivier|deactivat)')
CONFIRM = re.compile(r'[Cc]onfirm|CONFIRM|[Bb]est[aä]e?tig|[Kk]andidat|[Cc]andidate|[Dd]ialog|[Mm]odal|[Pp]rompt|'
                     r'[Öö]ffn|[Oo]effn|[Oo]pen|[Uu]ndo|[Rr][uü]e?ckg[aä]ngig|'
                     r'Frage|Ask|Sicher|(?<![A-Za-zÄÖÜäöü])(frage|ask|sicher)')
UI_STATE = re.compile(r'(?i)filter|chip|selection|auswahl|suche|search|toast|notification|meldung|banner|highlight|'
                      r'focus|class|attr|listener|overlay|tooltip|sort')
DELETE_CALL = re.compile(r'(?i)\b\w*(api|state|service|store|facade|http|client)\w*\s*\.\s*\w*(delete|remove|l[oö]e?sch|'
                         r'entfern)\w*\s*\(')
WRITE = re.compile(r'\.\s*subscribe\s*\(|\b(?:firstValueFrom|lastValueFrom)\s*\(|(?<![\w.])fetch\s*\(|'
                   r'\bhttp\w*\s*\.\s*(?:delete|post|put|patch|request)\s*[<(]')
API_TYPE = re.compile(r'(Api|ApiService|Client|HttpClient|Gateway|Repository)$')
BACKEND_TYPE = re.compile(r'(Service|State|Store|Facade)$')
FIELD = re.compile(r'\b(\w+)\s*=\s*inject\s*\(\s*(\w+)|(?:private|public|protected|readonly)\s+(?:readonly\s+)?(\w+)\s*:\s*(\w+)')
SAVE = re.compile(r'(?i)^(?:\w+\.)*(speicher|save|submit|absend|senden|send|anleg|erstell|create|buch|bestell|zahl|pay|'
                  r'abschlie|uebernehm|übernehm|apply|update|aktualisier)')
FIELD_BIND = re.compile(r'^\[(formField|field|control|formControl)\]$|^formControlName$|^\[formControlName\]$|^\[\(ngModel\)\]$|^\[ngModel\]$')
IMPORTANT = re.compile(r'(?i)(e?mail(adresse)?$|iban|bic|plz|postleitzahl|zip|telefon|phone|mobil|betrag|amount|preis|price|'
                       r'summe|datum|date|vorname|nachname|^name$|firma|company|strasse|street|hausnummer|^ort$|city|'
                       r'stadt|passwor|url|menge|quantity|anzahl|stunden|hours|steuer|^ust|tax|nummer|number|geburt|birth)')
OPTIONAL = re.compile(r'(?i)(notiz|note|kommentar|comment|anmerkung|beschreibung|description|bemerkung|newsletter|'
                      r'suche|search|filter|query)')
ABBREVIATION = re.compile(r'\b(?!(?:PLZ|AGB|OK|PDF|EUR|ID|PIN)\b)[A-ZÄÖÜ]{2,}[a-z]{0,2}(?:-[A-Za-z]+)*\b')
CHOICE = re.compile(r'(?i)select|radio|checkbox|toggle|switch|segment|chip|combobox|autocomplete|date-?picker')
PROJECTED_LABEL = re.compile(r'<(label|mat-label|legend)\b|<[\w-]+[^>]*\s\w*Label[\s>/]')
EMPTY_ATTR = re.compile(r'(?i)leer|empty|anzahl|count|keine')
NOT_LABEL_TYPES = {'hidden', 'submit', 'button', 'reset', 'image'}


class El:
    __slots__ = ('tag', 'attrs', 'start', 'end', 'inner_start', 'inner_end', 'parent')

    def __init__(self, tag, attrs, start, end, parent):
        self.tag, self.attrs, self.start, self.end, self.parent = tag, attrs, start, end, parent
        self.inner_start, self.inner_end = end, end

    def ancestors(self):
        p = self.parent
        while p is not None:
            yield p
            p = p.parent

    def has(self, *names) -> bool:
        return any(n in self.attrs for n in names)


def parse(html: str) -> list[El]:
    out, stack = [], []
    for m in TAG.finditer(html):
        closing, tag, raw, selfclose = m.group(1), m.group(2).lower(), m.group(3), m.group(4)
        if closing:
            for i in range(len(stack) - 1, -1, -1):
                if stack[i].tag == tag:
                    for el in stack[i:]:
                        el.inner_end = m.start()
                    del stack[i:]
                    break
            continue
        attrs = {}
        for a in ATTR.finditer(raw):
            attrs[a.group(1)] = next((g for g in a.group(2, 3, 4) if g is not None), '')
        el = El(tag, attrs, m.start(), m.end(), stack[-1] if stack else None)
        out.append(el)
        if not selfclose and tag not in VOID:
            stack.append(el)
    return out


def _events(el: El) -> list[tuple[str, str]]:
    return [(k[1:-1], v) for k, v in el.attrs.items() if k.startswith('(') and k.endswith(')') and not k.startswith('[(')]


def _methods(code: str, bare: str) -> dict[str, str]:
    out = {}
    for m in re.finditer(r'(?m)^\s*(?:(?:public|protected|private|async|override|readonly)\s+)*(\w+)\s*(?:<[^>]*>)?\s*'
                         r'\(([^)]*)\)\s*(?::\s*[^{=;]+)?\{', bare):
        if m.group(1) in ('if', 'for', 'while', 'switch', 'catch', 'constructor', 'function'):
            continue
        close = balanced(bare, m.end() - 1, '{', '}')
        out.setdefault(m.group(1), code[m.end():close if close > 0 else len(code)])
    for m in re.finditer(r'(?m)^\s*(?:(?:public|protected|private|readonly)\s+)*(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*'
                         r'(?::\s*[^=]+)?=>\s*\{', bare):
        close = balanced(bare, m.end() - 1, '{', '}')
        out.setdefault(m.group(1), code[m.end():close if close > 0 else len(code)])
    return out


def _line(html: str, offset: int) -> int:
    return html.count('\n', 0, offset) + 1


def _fields(bare: str) -> dict[str, str]:
    return {m.group(1) or m.group(3): m.group(2) or m.group(4) for m in FIELD.finditer(bare)}


class Svc:
    def __init__(self, src):
        self.methods = _methods(src.code, src.bare)
        self.fields = _fields(src.bare)

    def body(self, name: str) -> str | None:
        if name not in self.methods:
            return None
        body = self.methods[name]
        return body + '\n'.join(self.methods[n] for n in re.findall(r'\bthis\.(\w+)\s*\(', body) if n in self.methods)


def _writes(text: str, fields: dict[str, str], services: dict[str, Svc], depth: int = 1) -> bool:
    """Whether the code reaches the backend - directly, through an api, or through one state or service method."""
    if WRITE.search(text):
        return True
    for recv, method in re.findall(r'\b(\w+)\s*\??\.\s*(\w+)\s*\(', text):
        kind = fields.get(recv)
        if not kind or not (API_TYPE.search(kind) or BACKEND_TYPE.search(kind)):
            continue
        svc = services.get(kind)
        body = svc.body(method) if svc else None
        if API_TYPE.search(kind) or body is None or depth == 0 or _writes(body, svc.fields, services, depth - 1):
            return True
    return False


class Comp:
    def __init__(self, info: dict, repo):
        self.info = info
        src = repo.source(info['file'])
        self.code, self.bare = src.code, src.bare
        self.ts_rel = info['file']
        self.html_rel = info['template'] or info['file']
        self.html = repo.source(info['template']).code if info['template'] else info.get('inline_html') or ''
        sel = re.search(r'\bselector\s*:\s*[\'"`]([^\'"`]+)[\'"`]', self.code)
        self.selectors = [s.strip() for s in sel.group(1).split(',')] if sel else []
        self.outputs = set(re.findall(r'\b(\w+)\s*=\s*(?:output|outputFromObservable)\s*[<(]', self.bare)) | \
            set(re.findall(r'@Output\s*\([^)]*\)\s*(\w+)', self.bare))
        self.methods = _methods(self.code, self.bare)
        self.fields = _fields(self.bare)
        self.els = parse(self.html) if self.html else []
        scss = re.sub(r'\.ts$', '.scss', info['file'])
        self.styles = repo.source(scss).text if scss in repo.files else ''

    def body(self, handler: str) -> str:
        call = re.match(r'\s*(?:this\.)?(\w+)\s*\(', handler)
        if not call or call.group(1) not in self.methods:
            return ''
        body = self.methods[call.group(1)]
        nested = [self.methods[n] for n in re.findall(r'\bthis\.(\w+)\s*\(', body) if n in self.methods]
        return body + '\n'.join(nested)


def _asks(el: El, evt: str) -> bool:
    return bool(CONFIRM.search(evt) or CONFIRM.search(el.tag) or any('confirm' in k.lower() for k in el.attrs) or
                any(CONFIRM.search(a.tag) for a in el.ancestors()))


def _confirmed_outputs(c: Comp) -> dict[str, bool]:
    result = {}
    for o in c.outputs:
        emits = []
        for el in c.els:
            for evt, handler in _events(el):
                if re.search(r'\b' + o + r'\s*\.\s*emit\s*\(', handler):
                    emits.append(bool(_asks(el, evt) or CONFIRM.search(c.body(handler))))
        for name, body in c.methods.items():
            if re.search(r'\bthis\.' + o + r'\s*\.\s*emit\s*\(', body):
                callers = [_asks(el, evt) for el in c.els for evt, handler in _events(el)
                           if re.search(r'(?<![\w.])(?:this\.)?' + name + r'\s*\(', handler)]
                emits.append(bool(CONFIRM.search(name) or CONFIRM.search(body) or (callers and all(callers))))
        if emits:
            result[o] = all(emits)
    return result


def check_deletes(comps: list[Comp], hits: Hits, services: dict[str, Svc]):
    by_selector = {s: c for c in comps for s in c.selectors}
    confirmed = {id(c): _confirmed_outputs(c) for c in comps}
    for c in comps:
        for el in c.els:
            child = by_selector.get(el.tag)
            for evt, handler in _events(el):
                if re.fullmatch(r'\s*\w+\s*\.\s*emit\s*\(.*\)\s*;?\s*', handler, re.S):
                    continue
                body = c.body(handler)
                if not (DELETE.search(evt) or DELETE.search(handler) or DELETE_CALL.search(body)) or \
                        UI_STATE.search(evt + ' ' + handler):
                    continue
                if _asks(el, evt) or CONFIRM.search(handler) or \
                        any(a.has('role') and a.attrs['role'] in ('dialog', 'alertdialog') for a in el.ancestors()) or \
                        CONFIRM.search(body) or not _writes(handler + '\n' + body, c.fields, services):
                    continue
                if child is not None and confirmed[id(child)].get(evt):
                    continue
                note = ''
                if child is not None and evt in confirmed[id(child)]:
                    note = f'{child.info["name"]} emits ({evt}) without a confirmation'
                hits.add('UX-DELETE-NO-CONFIRM', c.html_rel, _line(c.html, el.start),
                         f'<{el.tag} ({evt})="{handler.strip()[:70]}">', **({'note': note} if note else {}))


def _visible(el: El) -> bool:
    if el.attrs.get('type', '').lower() in NOT_LABEL_TYPES or el.has('hidden', 'aria-hidden'):
        return False
    return el.attrs.get('tabindex') != '-1'


def _field_key(el: El) -> str | None:
    for k, v in el.attrs.items():
        if FIELD_BIND.match(k):
            return re.sub(r'\[[^\]]*\]|\(\)', '', v or el.attrs.get('name') or '').split('.')[-1].strip() or el.attrs.get('name')
    if el.tag in ('input', 'select', 'textarea'):
        return el.attrs.get('name') or el.attrs.get('id') or el.attrs.get('formControlName')
    return None


def _controls(c: Comp) -> list[El]:
    out = []
    for el in c.els:
        bound = any(FIELD_BIND.match(k) for k in el.attrs)
        if (el.tag in ('input', 'select', 'textarea') or (bound and '-' in el.tag)) and _visible(el):
            if el.tag != 'input' and not bound and any(FIELD_BIND.match(k) for a in el.ancestors() for k in a.attrs):
                continue
            out.append(el)
    return [el for el in out if not any(a in out for a in el.ancestors())]


def _labelled(el: El, label_for: set[str], html: str) -> bool:
    if el.has('aria-label', '[attr.aria-label]', 'aria-labelledby', '[attr.aria-labelledby]', 'title', '[title]',
              'label', '[label]', 'ariaLabel', '[ariaLabel]'):
        return True
    if el.attrs.get('id') in label_for or el.attrs.get('[id]') in label_for:
        return True
    if '-' in el.tag and html[el.inner_start:el.inner_end].strip():
        return True
    for depth, a in enumerate(el.ancestors()):
        if a.tag == 'label' or a.has('label', '[label]', 'legend'):
            return True
        if depth < 2 and PROJECTED_LABEL.search(html[a.end:a.inner_end]):
            return True
    return False


def _hinted(el: El, html: str) -> bool:
    if el.has('hint', '[hint]', 'aria-describedby', '[attr.aria-describedby]', 'description', '[description]',
              'helpText', '[helpText]', 'title'):
        return True
    for a in el.ancestors():
        if a.has('hint', '[hint]', 'description', '[description]', 'helpText', '[helpText]'):
            return True
        if a.tag in ('mat-form-field',) and '<mat-hint' in html[a.start:a.inner_end]:
            return True
    return False


def _label_text(el: El, html: str, labels: dict[str, str]) -> str:
    for k in ('label', '[label]', 'aria-label'):
        if k in el.attrs:
            return el.attrs[k]
    for a in el.ancestors():
        if 'label' in a.attrs:
            return a.attrs['label']
        if a.tag == 'label':
            return re.sub(r'<[^>]+>', ' ', html[a.inner_start:a.inner_end])
    return labels.get(el.attrs.get('id', ''), '')


def _validated(c: Comp) -> tuple[set[str] | None, bool]:
    """(validated field names or None when unknown, any validator at all)."""
    names, anything, unknown = set(), False, False
    if not re.search(r'\bform\s*(?:<[^>]*>)?\s*\(|\bFormGroup\b|\bFormControl\b|\.group\s*\(|ngModel', c.bare + c.html):
        return None, False
    for m in re.finditer(r'\bform\s*(?:<[^>]*>)?\s*\(', c.bare):
        close = balanced(c.bare, m.end() - 1)
        parts = split_top(c.bare[m.end():close])
        if len(parts) < 2:
            continue
        start, schema = parts[1]
        if not re.search(r'=>', schema):
            unknown = True
            continue
        schema_code = c.code[m.end() + start:m.end() + start + len(schema)]
        params = set(re.findall(r'\(?\s*(\w+)\s*(?::\s*[\w<>\[\]]+)?\s*\)?\s*=>', schema_code))
        for call in re.finditer(r'\b(\w+)\s*\(\s*(\w+)\s*\.\s*([\w.]+)', schema_code):
            fn, root, path = call.groups()
            if root in params and fn not in ('disabled', 'hidden', 'readonly', 'debounce', 'metadata', 'property',
                                             'applyEach', 'apply', 'applyWhen', 'applyWhenValue'):
                names.add(path.split('.')[-1])
                anything = True
    for m in re.finditer(r'\b(?:group|FormGroup)\s*(?:<[^>]*>)?\s*\(\s*\{', c.bare):
        close = balanced(c.bare, m.end() - 1, '{', '}')
        body = c.bare[m.end():close]
        for start, part in split_top(body):
            key = re.match(r'\s*[\'"]?(\w+)[\'"]?\s*:\s*([\s\S]*)', part)
            if not key:
                continue
            value = key.group(2).strip()
            code_value = c.code[m.end() + start:m.end() + start + len(part)]
            arr = re.match(r'\[([\s\S]*)\]$', value)
            ctrl = re.match(r'(?:new\s+FormControl|\w+\.control)\s*(?:<[^>]*>)?\s*\(([\s\S]*)\)$', value)
            if 'Validators.' in code_value or 'validators' in code_value or \
                    (arr and len(split_top(arr.group(1))) >= 2) or (ctrl and len(split_top(ctrl.group(1))) >= 2):
                names.add(key.group(1))
                anything = True
    for el in c.els:
        if any(k in ('[(ngModel)]', '[ngModel]') for k in el.attrs) and \
                el.has('required', '[required]', 'pattern', '[pattern]', 'minlength', 'maxlength', 'min', 'max', 'email'):
            names.add(_field_key(el) or '')
            anything = True
    if re.search(r'\bValidators\s*\.', c.bare):
        anything = True
    return (None if unknown and not anything else names), anything


def check_forms(comps: list[Comp], hits: Hits, ws_text: str) -> int:
    double, jargon, forms = {}, [], 0
    for c in comps:
        if not c.els:
            continue
        controls = _controls(c)
        label_for = {el.attrs.get('for') or el.attrs.get('[for]') or el.attrs.get('[attr.for]') for el in c.els
                     if el.tag == 'label'}
        labels = {el.attrs.get('for'): re.sub(r'<[^>]+>', ' ', c.html[el.inner_start:el.inner_end])
                  for el in c.els if el.tag == 'label' and el.attrs.get('for')}
        for el in controls:
            if not _labelled(el, label_for, c.html):
                hits.add('UX-INPUT-NO-LABEL', c.html_rel, _line(c.html, el.start),
                         c.html[el.start:el.end][:120] + ('   (placeholder only)' if el.has('placeholder', '[placeholder]')
                                                         else ''))
            text = _label_text(el, c.html, labels)
            if text and ABBREVIATION.search(text) and not _hinted(el, c.html):
                jargon.append((c, el, text.strip()))
        bound = [el for el in controls if _field_key(el)]
        saves = re.search(r'\bsubmit\s*\(|\bsubmission\s*:', c.bare) or any(
            el.attrs.get('type') == 'submit' or el.has('(ngSubmit)', '(submit)', '[formRoot]') or
            any(SAVE.search(h.strip()) for _, h in _events(el)) for el in c.els)
        if len(bound) >= 2 and saves:
            forms += 1
            validated, anything = _validated(c)
            keys = [_field_key(el) for el in bound]
            typed = [_field_key(el) for el in bound if not CHOICE.search(el.tag + ' ' + el.attrs.get('type', ''))]
            first = _line(c.html, bound[0].start)
            if validated is not None and not anything:
                hits.add('UX-FORM-NO-VALIDATION', c.ts_rel, c.info['line'],
                         f'{c.info["name"]}: {len(bound)} fields ({", ".join(dict.fromkeys(keys[:6]))}), no validator')
            elif validated is not None:
                weak = [k for k in typed if k and IMPORTANT.search(k) and not OPTIONAL.search(k) and k not in validated]
                if weak:
                    hits.add('UX-FIELD-NO-VALIDATION', c.ts_rel, c.info['line'],
                             f'{c.info["name"]}: {", ".join(dict.fromkeys(weak))} without a validator')
            if anything and not re.search(r'(?i)error|fehler|invalid|touched|mat-error|aria-invalid', c.html):
                hits.add('UX-NO-ERROR-MESSAGE', c.html_rel, first, f'{c.info["name"]}: validators, no error output in the template')
            if len(bound) >= 4 and not any(_hinted(el, c.html) for el in bound) and \
                    not re.search(r'(?i)hint|aria-describedby|description|hilfe|hinweis|<small|form-text|tooltip', c.html):
                hits.add('UX-FORM-NO-HINT', c.html_rel, first, f'{c.info["name"]}: {len(bound)} fields, no hint')
            if len(bound) >= 8:
                action = next((el for el in c.els if el.start > bound[0].start and (
                    el.attrs.get('type') == 'submit' or re.search(r'(?i)actions?$|action-?bar', el.tag) or
                    any(SAVE.search(h.strip()) for _, h in _events(el)))), None)
                if action and _line(c.html, action.start) - first > 80 and \
                        not re.search(r'(?i)sticky|action-?bar|fixed', c.html + c.styles):
                    hits.add('UX-PRIMARY-ACTION', c.html_rel, _line(c.html, action.start),
                             f'{c.info["name"]}: {len(bound)} fields, save action {_line(c.html, action.start) - first} '
                             'lines below the first field, nothing sticky')
        for el in c.els:
            if el.tag != 'button':
                continue
            submits = el.attrs.get('type') == 'submit' or any(SAVE.search(h.strip()) for e, h in _events(el) if e == 'click')
            if submits and not el.has('[disabled]', 'disabled', '[attr.disabled]', '[loading]', '[busy]', '[pending]',
                                      '[aria-disabled]', '[attr.aria-disabled]'):
                double[c.html_rel] = double.get(c.html_rel, 0) + 1
            inner = re.sub(r'<[^>]+>', '', c.html[el.inner_start:el.inner_end])
            if not inner.strip() and not el.has('aria-label', '[attr.aria-label]', 'title', '[title]', 'aria-labelledby',
                                                 '[ariaLabel]', 'matTooltip', '[matTooltip]'):
                hits.add('UX-ICON-BUTTON', c.html_rel, _line(c.html, el.start), c.html[el.start:el.end][:120])
    if double:
        top = sorted(double.items(), key=lambda kv: -kv[1])
        hits.add('UX-DOUBLE-SUBMIT', top[0][0], None, f'{sum(double.values())} buttons in {len(double)} templates: '
                 + ', '.join(f'{os.path.basename(f)} ({n})' for f, n in top[:8]), files=[f for f, _ in top[:40]])
    if jargon:
        c, el, text = jargon[0]
        hits.add('UX-JARGON-NO-HINT', c.html_rel, _line(c.html, el.start),
                 f'{len(jargon)} labels: ' + ', '.join(dict.fromkeys(t[:30] for _, _, t in jargon[:10])),
                 files=sorted({x.html_rel for x, _, _ in jargon})[:40])
    if forms >= 3 and not re.search(r'canDeactivate|CanDeactivateFn|beforeunload', ws_text):
        hits.add('UX-NO-UNSAVED-GUARD', None, None, f'{forms} components with forms, no canDeactivate and no beforeunload')
    return forms


def check_lists(comps: list[Comp], hits: Hits):
    missing = defaultdict(int)
    total = 0
    for c in comps:
        html = c.html
        for m in re.finditer(r'@for\s*\(([^;)]*)', html):
            if '(' not in m.group(1):
                continue
            before = html[max(0, m.start() - 400):m.start()]
            if re.search(r'<(select|datalist|optgroup)\b(?![\s\S]*</\1>)', before) or \
                    re.search(r'@if\s*\(.{0,120}?(length|\.size|isEmpty|leer|empty)', before[-250:], re.I) or \
                    any(el.start < m.start() < el.inner_end and any(EMPTY_ATTR.search(k) for k in el.attrs)
                        for el in c.els):
                continue
            total += 1
            open_paren = html.find('(', m.start())
            close = balanced(html, open_paren)
            brace = html.find('{', close)
            end = balanced(html, brace, '{', '}') if brace > 0 else -1
            if end < 0 or not re.match(r'\s*@empty\b', html[end + 1:end + 40]):
                missing[c.html_rel] += 1
    if missing:
        top = sorted(missing.items(), key=lambda kv: -kv[1])
        hits.add('UX-EMPTY-STATE', top[0][0], None, f'{sum(missing.values())} of {total} loops over loaded data in '
                 f'{len(missing)} templates: ' + ', '.join(f'{os.path.basename(f)} ({n})' for f, n in top[:8]),
                 files=[f for f, _ in top[:40]])


def run(w, hits: Hits) -> dict:
    comps = [Comp(info, w.repo) for info in w.comps if info['kind'] == 'component']
    w.ux_comps = comps
    services = {}
    for rel in w.main_ts:
        src = w.repo.source(rel)
        if '@Injectable' in src.bare:
            svc = Svc(src)
            for name in re.findall(r'\bclass\s+(\w+)', src.bare):
                services.setdefault(name, svc)
    check_deletes(comps, hits, services)
    ws_text = '\n'.join(w.repo.source(f).code for f in w.main_ts)
    forms = check_forms(comps, hits, ws_text)
    check_lists(comps, hits)
    for rel in w.main_ts:
        src = w.repo.source(rel)
        for m in re.finditer(r'(?<![\w.])(?:window\s*\.\s*)?(confirm|alert|prompt)\s*\(', src.bare):
            if re.search(r'(?m)^\s*(?:async\s+)?' + m.group(1) + r'\s*\([^)]*\)\s*(:\s*[^{]+)?\{', src.bare):
                continue
            hits.add('UX-NATIVE-DIALOG', rel, src.line_at(m.start()), src.line(src.line_at(m.start())).strip())
    return {'forms': forms}
