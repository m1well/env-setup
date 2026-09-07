#!/usr/bin/env python3
"""Counts what a codebase is made of: files, lines, comments and declared types.

Language-agnostic. Uses `git ls-files` when the directory is a repository, so
.gitignore is honoured for free, and falls back to a filtered walk otherwise.

Comment detection is a line-based state machine that masks string literals
first, so `val s = "// not a comment"` counts as code. A line counts as a
comment only when it starts with one; trailing comments stay on the code line,
which is the same rule cloc uses.
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

# extension -> (language, comment style)
LANGS = {
    ".kt": ("Kotlin", "c"), ".kts": ("Kotlin", "c"),
    ".java": ("Java", "c"),
    ".ts": ("TypeScript", "c"), ".tsx": ("TypeScript", "c"),
    ".js": ("JavaScript", "c"), ".jsx": ("JavaScript", "c"), ".mjs": ("JavaScript", "c"),
    ".vue": ("Vue", "html"), ".svelte": ("Svelte", "html"),
    ".py": ("Python", "py"), ".go": ("Go", "c"), ".rs": ("Rust", "c"),
    ".rb": ("Ruby", "hash"), ".php": ("PHP", "c"), ".cs": ("C#", "c"),
    ".swift": ("Swift", "c"), ".c": ("C", "c"), ".h": ("C", "c"),
    ".cpp": ("C++", "c"), ".hpp": ("C++", "c"),
    ".sql": ("SQL", "sql"),
    ".sh": ("Shell", "hash"), ".bash": ("Shell", "hash"), ".zsh": ("Shell", "hash"),
    ".yaml": ("YAML", "hash"), ".yml": ("YAML", "hash"),
    ".toml": ("TOML", "hash"), ".ini": ("INI", "hash"),
    ".properties": ("Properties", "hash"), ".env": ("Env", "hash"),
    ".json": ("JSON", "none"), ".txt": ("Text", "none"),
    ".xml": ("XML", "html"), ".html": ("HTML", "html"), ".htm": ("HTML", "html"),
    ".css": ("CSS", "block"), ".scss": ("SCSS", "c"), ".less": ("LESS", "c"),
    ".md": ("Markdown", "html"), ".markdown": ("Markdown", "html"),
    ".gradle": ("Gradle", "c"), ".tf": ("Terraform", "hash"),
    ".lua": ("Lua", "lua"), ".vim": ("Vim", "quote"),
}
NAMED = {
    "Dockerfile": ("Dockerfile", "hash"), "Makefile": ("Makefile", "hash"),
    "Jenkinsfile": ("Groovy", "c"), ".gitignore": ("Config", "hash"),
    ".dockerignore": ("Config", "hash"), ".editorconfig": ("Config", "hash"),
}
# languages whose files hold classes - the "class files" count
CLASS_LANGS = {"Kotlin", "Java", "TypeScript", "JavaScript", "C#", "Swift", "Python", "Go", "Rust"}

COMMENTS = {
    "c":     {"line": ("//",), "block": (("/*", "*/"),)},
    "hash":  {"line": ("#",), "block": ()},
    "py":    {"line": ("#",), "block": (('"""', '"""'), ("'''", "'''"))},
    "sql":   {"line": ("--",), "block": (("/*", "*/"),)},
    "html":  {"line": (), "block": (("<!--", "-->"),)},
    "block": {"line": (), "block": (("/*", "*/"),)},
    "lua":   {"line": ("--",), "block": (("--[[", "]]"),)},
    "quote": {"line": ('"',), "block": ()},
    "none":  {"line": (), "block": ()},
}

SKIP_DIRS = {".git", "node_modules", "build", "dist", "out", "target", ".gradle",
             ".idea", ".vscode", "venv", ".venv", "__pycache__", ".next", ".angular",
             ".nuxt", "vendor", "coverage", ".terraform", "Pods", ".mvn"}
SKIP_FILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "composer.lock",
              "Cargo.lock", "poetry.lock", "go.sum", "gradle.lockfile"}
SKIP_PATTERNS = (re.compile(r"\.min\.(js|css)$"), re.compile(r"\.(lock|map)$"),
                 re.compile(r"\.generated\.[a-z]+$"))

# documentation, not production: a docs tree counts as docs whatever is in it
DOC_DIRS = re.compile(r"(^|/)(docs?|documentation|adrs?|rfcs?|wiki|manual|guides?)(/|$)", re.I)
DOC_LANGS = {"Markdown", "Text"}
DOC_FILES = re.compile(r"^(README|CHANGELOG|CONTRIBUTING|LICENSE|NOTICE|AUTHORS"
                       r"|CODE_OF_CONDUCT|SECURITY|MEMORY|DECISIONS)(\.|$)", re.I)

TEST_PATTERNS = [re.compile(p) for p in (
    r"(^|/)src/test/", r"(^|/)tests?/", r"(^|/)__tests__/", r"(^|/)spec/",
    r"\.(spec|test)\.[jt]sx?$", r"(Test|Tests|Spec|IT)\.(kt|java|cs)$",
    r"_test\.(py|go|rb)$", r"test_[^/]+\.py$",
)]

STR_RE = re.compile(r'"(?:[^"\\]|\\.)*"' r"|'(?:[^'\\]|\\.)*'" r"|`(?:[^`\\]|\\.)*`")

MODIFIERS = (r"(?:(?:public|private|protected|internal|abstract|open|final|static|"
             r"sealed|data|value|inner|enum|annotation|expect|actual|companion|"
             r"export|default|declare|const|readonly|fun|record|partial)\s+)*")
TYPE_RE = {
    "Kotlin": re.compile(r"^\s*(?:@[\w.]+(?:\([^)]*\))?\s*)*" + MODIFIERS +
                         r"(class|interface|object|typealias)\s+(\w+)"),
    "Java": re.compile(r"^\s*(?:@[\w.]+(?:\([^)]*\))?\s*)*" + MODIFIERS +
                       r"(class|interface|enum|record|@interface)\s+(\w+)"),
    "TypeScript": re.compile(r"^\s*(?:@[\w.]+(?:\([^)]*\))?\s*)*" + MODIFIERS +
                             r"(class|interface|enum|type)\s+(\w+)"),
}
TYPE_RE["JavaScript"] = re.compile(r"^\s*" + MODIFIERS + r"(class)\s+(\w+)")
TYPE_RE["C#"] = TYPE_RE["Java"]
KOTLIN_KIND = re.compile(r"\b(data|enum|sealed|annotation|value|fun)\s+(?:class|interface)")
DECORATOR_RE = re.compile(
    r"^\s*@(Component|Directive|Injectable|Pipe|NgModule|Input|Output"
    r"|Service|Repository|RestController|Controller|Configuration|Entity|Table"
    r"|SpringBootApplication|FeignClient|ConfigurationProperties)\b")


def is_test(rel: str) -> bool:
    return any(p.search(rel) for p in TEST_PATTERNS)


def side_of(rel: str, lang: str) -> str:
    name = rel.rsplit("/", 1)[-1]
    if lang in DOC_LANGS or DOC_FILES.match(name) or DOC_DIRS.search(rel):
        return "docs"
    return "test" if is_test(rel) else "production"



def classify(path: Path):
    if path.name in NAMED:
        return NAMED[path.name]
    return LANGS.get(path.suffix.lower())


def collect(root: Path, include_all: bool):
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                             capture_output=True, text=True, timeout=60)
        if out.returncode == 0:
            names = [n for n in out.stdout.split("\0") if n]
            files, source = [root / n for n in names], "git"
        else:
            raise FileNotFoundError
    except (FileNotFoundError, subprocess.SubprocessError):
        files, source = [], "walk"
        for p in root.rglob("*"):
            if p.is_file() and not any(part in SKIP_DIRS for part in p.parts):
                files.append(p)

    kept, skipped = [], 0
    for f in files:
        rel = str(f.relative_to(root))
        if any(part in SKIP_DIRS for part in f.relative_to(root).parts):
            skipped += 1
            continue
        if not include_all and (f.name in SKIP_FILES or
                                any(p.search(f.name) for p in SKIP_PATTERNS)):
            skipped += 1
            continue
        kept.append((f, rel))
    return kept, source, skipped


def count_file(path: Path, style: str):
    rules = COMMENTS[style]
    total = blank = comment = code = 0
    closing = None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    lines = text.splitlines()
    for raw in lines:
        total += 1
        line = raw.strip()
        if not line:
            blank += 1
            continue
        if closing:
            comment += 1
            idx = line.find(closing)
            if idx >= 0:
                rest = line[idx + len(closing):]
                closing = None
                if rest.strip():
                    comment -= 1
                    code += 1
            continue
        masked = STR_RE.sub('""', line) if style != "py" else line
        started = False
        for opener, closer in rules["block"]:
            if masked.startswith(opener):
                comment += 1
                started = True
                rest = line[len(opener):]
                if closer not in rest:
                    closing = closer
                break
        if started:
            continue
        if any(masked.startswith(p) for p in rules["line"]):
            comment += 1
            continue
        for opener, closer in rules["block"]:
            if opener in masked and closer not in masked[masked.find(opener):]:
                closing = closer
                break
        code += 1
    return total, code, comment, blank, lines


def scan_types(lines, lang, types, decorators):
    pattern = TYPE_RE.get(lang)
    for raw in lines:
        if DECORATOR_RE.match(raw):
            decorators[DECORATOR_RE.match(raw).group(1)] += 1
        if not pattern:
            continue
        m = pattern.match(raw)
        if not m:
            continue
        kind = m.group(1)
        if lang == "Kotlin":
            k = KOTLIN_KIND.search(raw)
            if k:
                kind = f"{k.group(1)} {kind}"
        elif lang == "Java" and kind == "@interface":
            kind = "annotation"
        types[f"{lang}: {kind}"] += 1


def human(n):
    return f"{n:,}".replace(",", ".")


def main():
    ap = argparse.ArgumentParser(description="Count files, lines and types in a codebase.")
    ap.add_argument("path", nargs="?", default=".", help="directory to scan (default: .)")
    ap.add_argument("--json", action="store_true", help="machine readable output")
    ap.add_argument("--all", action="store_true", help="include lock files and minified output")
    ap.add_argument("--top", type=int, default=10, help="how many largest files to list")
    args = ap.parse_args()

    root = Path(args.path).resolve()
    if not root.is_dir():
        sys.exit(f"not a directory: {root}")

    files, source, skipped = collect(root, args.all)
    per_lang = defaultdict(lambda: dict(files=0, total=0, code=0, comment=0, blank=0))
    types, decorators = Counter(), Counter()
    largest = []
    totals = dict(files=0, class_files=0, total=0, code=0, comment=0, blank=0, unknown=0)
    split = {k: dict(files=0, code=0) for k in ("production", "test", "docs")}

    for path, rel in files:
        totals["files"] += 1
        known = classify(path)
        if not known:
            totals["unknown"] += 1
            continue
        lang, style = known
        counted = count_file(path, style)
        if not counted:
            continue
        total, code, comment, blank, lines = counted
        bucket = per_lang[lang]
        bucket["files"] += 1
        bucket["total"] += total
        bucket["code"] += code
        bucket["comment"] += comment
        bucket["blank"] += blank
        for key, value in (("total", total), ("code", code), ("comment", comment), ("blank", blank)):
            totals[key] += value
        if lang in CLASS_LANGS:
            totals["class_files"] += 1
            scan_types(lines, lang, types, decorators)
        side = side_of(rel, lang)
        split[side]["files"] += 1
        split[side]["code"] += code
        largest.append((code, rel, side))

    result = dict(root=str(root), file_source=source, skipped=skipped, totals=totals,
                  languages={k: v for k, v in sorted(per_lang.items(),
                                                     key=lambda x: -x[1]["code"])},
                  types=dict(types.most_common()), decorators=dict(decorators.most_common()),
                  split=split,
                  largest=[dict(code=c, file=f, side=side) for c, f, side in
                           sorted(largest, reverse=True)[:args.top]])

    if args.json:
        print(json.dumps(result, indent=2))
        return

    lines_total = totals["total"] or 1
    print(f"{root}")
    print(f"file list from {source}, {skipped} skipped (lock files, build output)\n")

    print("OVERALL")
    print(f"  files                {human(totals['files']):>10}"
          f"   of those class files {human(totals['class_files'])}"
          f", not counted {human(totals['unknown'])}")
    print(f"  lines                {human(totals['total']):>10}")
    print(f"    code               {human(totals['code']):>10}   {totals['code']/lines_total:6.1%}")
    print(f"    comment            {human(totals['comment']):>10}   {totals['comment']/lines_total:6.1%}")
    print(f"    blank              {human(totals['blank']):>10}   {totals['blank']/lines_total:6.1%}")

    print("\nBY LANGUAGE")
    print(f"  {'language':<14}{'files':>8}{'code':>10}{'comment':>10}{'blank':>8}{'com%':>7}")
    for lang, v in result["languages"].items():
        pct = v["comment"] / (v["code"] + v["comment"]) if v["code"] + v["comment"] else 0
        print(f"  {lang:<14}{human(v['files']):>8}{human(v['code']):>10}"
              f"{human(v['comment']):>10}{human(v['blank']):>8}{pct:>7.1%}")

    if types:
        print("\nDECLARED TYPES")
        for name, n in sorted(types.items()):
            print(f"  {name:<28}{human(n):>7}")
        print(f"  {'total':<28}{human(sum(types.values())):>7}")

    if decorators:
        print("\nANNOTATIONS AND DECORATORS")
        row = [f"{k} {human(v)}" for k, v in decorators.most_common()]
        for i in range(0, len(row), 4):
            print("  " + "   ".join(row[i:i + 4]))

    counted = sum(v["code"] for v in split.values()) or 1
    print("\nPRODUCTION VS TEST VS DOCS")
    for side in ("production", "test", "docs"):
        v = split[side]
        print(f"  {side:<13}{human(v['files']):>6} files  {human(v['code']):>9} code"
              f"{v['code'] / counted:>9.1%}")
    prod = split["production"]["code"]
    if prod:
        print(f"  test code per production code: {split['test']['code'] / prod:.2f}")

    if result["largest"]:
        print("\nLARGEST FILES (code lines)")
        for item in result["largest"]:
            tag = "" if item["side"] == "production" else f"  [{item['side']}]"
            print(f"  {human(item['code']):>7}  {item['file']}{tag}")


if __name__ == "__main__":
    main()
