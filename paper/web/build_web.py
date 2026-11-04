#!/usr/bin/env python3
"""Convert the thesis LaTeX source into the web article shown on the app's Paper page.

Output:
  frontend/src/content/paper.json      article metadata, contents, body HTML, references
  frontend/public/paper/figures/*.png  web-sized figures

The converter understands exactly the LaTeX subset this thesis uses (headings, lists,
figures, tables built from Tables/*_body.tex, biblatex author-year citations, cross
references, light inline math). Anything else raises an error instead of being dropped,
so a new macro in the source fails the build loudly.

Run from the repository root:
  python paper/web/build_web.py [--png-dir paper_results/figures]

The figures in the thesis are PDFs. The web needs raster images, so --png-dir must hold
a PNG with the same stem for each PDF figure (the plotting scripts write both). Pillow,
if installed, downsizes them for the web; otherwise they are copied as they are.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper"
OUT_JSON = ROOT / "frontend" / "src" / "content" / "paper.json"
OUT_FIG = ROOT / "frontend" / "public" / "paper" / "figures"
FIG_URL = "/paper/figures"
MAX_FIG_WIDTH = 1800
WORDS_PER_MINUTE = 230


class LatexError(Exception):
    pass


# --------------------------------------------------------------------------- source reading


def strip_comments(text: str) -> str:
    return "\n".join(re.sub(r"(?<!\\)%.*$", "", line) for line in text.splitlines())


def read_tex(path: Path) -> str:
    text = strip_comments(path.read_text(encoding="utf-8"))
    # \tabinput{Tables/x.tex} is a primitive \input of a generated table body.
    return re.sub(
        r"\\tabinput\{([^}]*)\}",
        lambda m: strip_comments((PAPER / m.group(1)).read_text(encoding="utf-8")),
        text,
    )


def braced(text: str, start: int) -> tuple[str, int]:
    """Return (content, index after closing brace) for the group opening at text[start]."""
    if start >= len(text) or text[start] != "{":
        raise LatexError(f"expected '{{' at: {text[start : start + 40]!r}")
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "\\":
            continue
        if c == "{" and text[i - 1] != "\\":
            depth += 1
        elif c == "}" and text[i - 1] != "\\":
            depth -= 1
            if depth == 0:
                return text[start + 1 : i], i + 1
    raise LatexError(f"unbalanced braces at: {text[start : start + 60]!r}")


def bracketed(text: str, start: int) -> tuple[str | None, int]:
    """Optional [..] argument at text[start] (skipping spaces)."""
    j = start
    while j < len(text) and text[j] in " \t":
        j += 1
    if j < len(text) and text[j] == "[":
        depth = 0
        for i in range(j, len(text)):
            if text[i] == "[":
                depth += 1
            elif text[i] == "]":
                depth -= 1
                if depth == 0:
                    return text[j + 1 : i], i + 1
        raise LatexError(f"unbalanced brackets at: {text[j : j + 60]!r}")
    return None, start


def env_body(text: str, name: str, start: int) -> tuple[str, int]:
    """Body of the environment whose \\begin{name} ends at `start`; handles nesting."""
    pat = re.compile(r"\\(begin|end)\{" + re.escape(name) + r"\}")
    depth = 1
    for m in pat.finditer(text, start):
        depth += 1 if m.group(1) == "begin" else -1
        if depth == 0:
            return text[start : m.start()], m.end()
    raise LatexError(f"unclosed environment {name}")


def command_arg(text: str, name: str) -> str:
    m = re.search(r"\\" + name + r"\{", text)
    if not m:
        raise LatexError(f"missing \\{name}")
    return braced(text, m.end() - 1)[0]


# --------------------------------------------------------------------------- bibliography


@dataclass
class BibEntry:
    key: str
    kind: str
    fields: dict[str, str]
    cited: bool = False

    def names(self) -> list[str]:
        raw = self.fields.get("author", "")
        parts, depth, cur = [], 0, ""
        tokens = re.split(r"(\{|\}|\s+and\s+)", raw)
        for t in tokens:
            if t == "{":
                depth += 1
            elif t == "}":
                depth -= 1
            if depth == 0 and re.fullmatch(r"\s+and\s+", t or ""):
                parts.append(cur.strip())
                cur = ""
            else:
                cur += t
        parts.append(cur.strip())
        return [p for p in parts if p]

    @staticmethod
    def family(name: str) -> str:
        if name.startswith("{") and name.endswith("}"):
            return name[1:-1]
        return name.split(",")[0].strip()

    def cite_label(self) -> str:
        names = self.names()
        fams = [self.family(n) for n in names if n != "others"]
        if len(names) == 1:
            return fams[0]
        if len(names) == 2 and "others" not in names:
            return f"{fams[0]} and {fams[1]}"
        return f"{fams[0]} et al."

    @property
    def year(self) -> str:
        return self.fields.get("year", "n.d.")


def parse_bib(path: Path) -> dict[str, BibEntry]:
    text = strip_comments(path.read_text(encoding="utf-8"))
    entries: dict[str, BibEntry] = {}
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        body, _ = braced(text, m.end(0) - len(m.group(0)) + m.group(0).index("{"))
        body = body[body.index(",") + 1 :]
        fields: dict[str, str] = {}
        i = 0
        while i < len(body):
            fm = re.compile(r"\s*(\w+)\s*=\s*").match(body, i)
            if not fm:
                break
            name = fm.group(1).lower()
            j = fm.end()
            if body[j] == "{":
                value, j = braced(body, j)
            else:
                vm = re.compile(r"[^,\n]+").match(body, j)
                value, j = vm.group(0).strip(), vm.end()
            fields[name] = " ".join(value.split())
            sm = re.compile(r"\s*,?").match(body, j)
            i = sm.end()
        entries[m.group(2)] = BibEntry(m.group(2), m.group(1).lower(), fields)
    return entries


def bib_text(value: str) -> str:
    """Bib field value -> escaped HTML (strip case-protecting braces, fix dashes)."""
    value = value.replace("{", "").replace("}", "")
    value = value.replace("---", "\u2014").replace("--", "\u2013")
    return html.escape(value)


def format_reference(e: BibEntry) -> str:
    f = e.fields
    names = e.names()
    shown = names
    if len(names) > 9:  # maxbibnames=9 -> first author + et al.
        shown = names[:1]
    authors = []
    for n in shown:
        if n == "others":
            continue
        if n.startswith("{"):
            authors.append(bib_text(n))
        else:
            parts = [p.strip() for p in n.split(",")]
            if len(parts) == 3:  # Last, Jr., First
                authors.append(bib_text(f"{parts[0]}, {parts[2]}, {parts[1]}"))
            else:
                authors.append(bib_text(", ".join(parts)))
    etal = len(names) > 9 or "others" in names
    if etal:
        author_str = "; ".join(authors) + " et al."
    elif len(authors) > 1:
        author_str = "; ".join(authors[:-1]) + " and " + authors[-1]
    else:
        author_str = authors[0]

    bits = [f"{author_str} ({html.escape(e.year)}).", f"{bib_text(f['title'])}."]
    if "booktitle" in f:
        venue = f"In <em>{bib_text(f['booktitle'])}</em>"
        if "pages" in f:
            venue += f", pp. {bib_text(f['pages'])}"
        bits.append(venue + ".")
    elif "journal" in f:
        venue = f"<em>{bib_text(f['journal'])}</em>"
        if "volume" in f:
            venue += f" {bib_text(f['volume'])}"
            if "number" in f:
                venue += f"({bib_text(f['number'])})"
        if "pages" in f:
            venue += f", {bib_text(f['pages'])}"
        bits.append(venue + ".")
    for key in ("type", "school", "institution", "howpublished", "publisher"):
        if key in f and not (key == "type" and e.kind == "mastersthesis" and "school" not in f):
            bits.append(bib_text(f[key]) + ".")
    if "note" in f:
        bits.append(bib_text(f["note"]) + ".")
    if "doi" in f:
        url = f"https://doi.org/{f['doi']}"
    elif f.get("eprinttype", "").lower() == "arxiv" and "eprint" in f:
        url = f"https://arxiv.org/abs/{f['eprint']}"
        bits.append(f"arXiv:{html.escape(f['eprint'])}.")
    else:
        url = f.get("url")
    if url:
        bits.append(f'<a href="{html.escape(url)}">{html.escape(url)}</a>')
    return " ".join(bits)


# --------------------------------------------------------------------------- numbering


@dataclass
class Target:
    number: str
    anchor: str
    kind: str


@dataclass
class State:
    bib: dict[str, BibEntry]
    labels: dict[str, Target] = field(default_factory=dict)
    chapter: str = ""
    sec: int = 0
    sub: int = 0
    fig: int = 0
    tab: int = 0
    appendix_index: int = 0
    toc: list[dict] = field(default_factory=list)
    figures_used: list[str] = field(default_factory=list)
    dry: bool = False  # first pass: collect label numbers only, write nothing


# --------------------------------------------------------------------------- inline


GREEK = {"Delta": "\u0394", "alpha": "\u03b1", "pm": "\u00b1", "times": "\u00d7"}


def render_math(src: str) -> str:
    return f'<span class="math">{math_inner(src)}</span>'


def math_inner(src: str) -> str:
    out, i = [], 0
    while i < len(src):
        c = src[i]
        if c == "\\":
            m = re.compile(r"\\([A-Za-z]+)").match(src, i)
            if not m:
                raise LatexError(f"bad math: {src!r}")
            name = m.group(1)
            i = m.end()
            if name in GREEK:
                out.append(GREEK[name])
            elif name == "text":
                arg, i = braced(src, i)
                out.append(html.escape(arg))
            else:
                raise LatexError(f"unknown math command \\{name} in ${src}$")
        elif c in "^_":
            tag = "sup" if c == "^" else "sub"
            i += 1
            if src[i] == "{":
                arg, i = braced(src, i)
            elif src[i] == "\\":
                m = re.compile(r"\\([A-Za-z]+)").match(src, i)
                arg_end = m.end()
                if m.group(1) == "text":
                    arg, arg_end = braced(src, arg_end)
                    arg = "\\text{" + arg + "}"
                else:
                    arg = m.group(0)
                i = arg_end
            else:
                arg, i = src[i], i + 1
            out.append(f"<{tag}>{math_inner(arg)}</{tag}>")
        elif c == "-":
            out.append("\u2212")
            i += 1
        elif c.isalpha():
            out.append(f"<i>{c}</i>")
            i += 1
        else:
            out.append(html.escape(c))
            i += 1
    return "".join(out)


SIMPLE = {
    "%": "%",
    "_": "_",
    "&": "&amp;",
    "#": "#",
    "$": "$",
    ",": "\u2009",
    " ": " ",
    "ldots": "\u2026",
    "textwidth": "",
    "centering": "",
    "small": "",
    "footnotesize": "",
    "hfill": "",
    "raggedright": "",
    "arraybackslash": "",
    "noindent": "",
}
WRAP = {"textbf": "strong", "emph": "em", "texttt": "code", "nolinkurl": "code", "textsc": "span"}


def cite(state: State, keys: str, post: str | None, textual: bool) -> str:
    parts = []
    for key in [k.strip() for k in keys.split(",")]:
        if key not in state.bib:
            raise LatexError(f"unknown citation key {key}")
        e = state.bib[key]
        e.cited = True
        label = html.escape(e.cite_label())
        if textual:
            parts.append(f'{label} (<a class="cite" href="#ref-{key}">{e.year}</a>)')
        else:
            parts.append(f'<a class="cite" href="#ref-{key}">{label}, {e.year}</a>')
    if textual:
        return "; ".join(parts)
    inner = "; ".join(parts)
    if post:
        inner += ", " + render_inline(state, post)
    return f"({inner})"


def render_inline(state: State, s: str) -> str:
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            if i + 1 < len(s) and s[i + 1] == "\\":
                out.append("<br>")
                i += 2
                continue
            m = re.compile(r"\\([A-Za-z]+|.)").match(s, i)
            name = m.group(1)
            i = m.end()
            if name in SIMPLE:
                out.append(SIMPLE[name])
                if name.isalpha() and i < len(s) and s[i] == " " and SIMPLE[name] == "":
                    i += 1
            elif name in WRAP:
                arg, i = braced(s, i)
                tag = WRAP[name]
                out.append(f"<{tag}>{render_inline(state, arg)}</{tag}>")
            elif name == "foreignlanguage":
                _, i = braced(s, i)
                arg, i = braced(s, i)
                out.append(render_inline(state, arg))
            elif name in ("parencite", "textcite"):
                post, i = bracketed(s, i)
                keys, i = braced(s, i)
                out.append(cite(state, keys, post, textual=name == "textcite"))
            elif name == "ref":
                key, i = braced(s, i)
                if key not in state.labels:
                    raise LatexError(f"unresolved reference {key}")
                t = state.labels[key]
                out.append(f'<a class="xref" href="#{t.anchor}">{t.number}</a>')
            elif name == "paragraph":
                arg, i = braced(s, i)
                out.append(f'<strong class="run-in">{render_inline(state, arg)}</strong> ')
            elif name == "label":
                _, i = braced(s, i)
            else:
                raise LatexError(f"unknown command \\{name} near {s[max(0, i - 40) : i + 40]!r}")
        elif c == "$":
            j = s.index("$", i + 1)
            out.append(render_math(s[i + 1 : j]))
            i = j + 1
        elif c == "{" or c == "}":
            i += 1
        elif c == "~":
            out.append("\u00a0")
            i += 1
        elif s.startswith("---", i):
            out.append("\u2014")
            i += 3
        elif s.startswith("--", i):
            out.append("\u2013")
            i += 2
        elif s.startswith("``", i):
            out.append("\u201c")
            i += 2
        elif s.startswith("''", i):
            out.append("\u201d")
            i += 2
        elif c == "`":
            out.append("\u2018")
            i += 1
        elif c == "'":
            out.append("\u2019")
            i += 1
        elif c in '<>&"':
            out.append(html.escape(c))
            i += 1
        else:
            out.append(c)
            i += 1
    return re.sub(r"\s+", " ", "".join(out)).strip()


# --------------------------------------------------------------------------- blocks


BLOCK = re.compile(
    r"\\(chapter|section|subsection)\*?\{|\\begin\{(figure|table|itemize|enumerate|description)\}"
)


def take_label(text: str, i: int) -> tuple[str | None, int]:
    m = re.compile(r"\s*\\label\{([^}]*)\}").match(text, i)
    return (m.group(1), m.end()) if m else (None, i)


def paragraphs(state: State, text: str) -> list[str]:
    out = []
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if para:
            out.append(f"<p>{render_inline(state, para)}</p>")
    return out


def render_list(state: State, env: str, body: str) -> str:
    items = re.split(r"\\item(?![A-Za-z])", body)[1:]
    if env == "description":
        rows = []
        for it in items:
            term, j = bracketed(it, 0)
            dt, dd = render_inline(state, term or ""), render_inline(state, it[j:])
            rows.append(f"<dt>{dt}</dt><dd>{dd}</dd>")
        return f'<dl class="paper-dl">{"".join(rows)}</dl>'
    tag = "ol" if env == "enumerate" else "ul"
    lis = "".join(f"<li>{render_inline(state, it)}</li>" for it in items)
    return f"<{tag}>{lis}</{tag}>"


def column_aligns(spec: str) -> list[str]:
    spec = re.sub(r">\{[^}]*\}", "", spec)
    aligns, i = [], 0
    while i < len(spec):
        c = spec[i]
        if c in "lrc":
            aligns.append({"l": "left", "r": "right", "c": "center"}[c])
        elif c == "X":
            aligns.append("left")
        elif c == "p":
            _, i = braced(spec, i + 1)
            aligns.append("left")
            continue
        i += 1
    return aligns


def split_cells(row: str) -> list[str]:
    return re.split(r"(?<!\\)&", row)


def render_tabular(state: State, spec: str, body: str) -> str:
    aligns = column_aligns(spec)
    body = re.sub(r"\\(toprule|bottomrule)", "", body)
    body = re.sub(r"\\cmidrule(\([a-z]*\))?\{[^}]*\}", "", body)
    chunks = re.split(r"\\midrule", body)
    split_rows = [[r.strip() for r in re.split(r"\\\\", c) if r.strip()] for c in chunks]
    head_rows, groups = split_rows[0], split_rows[1:]

    def row_html(row: str, cell_tag: str) -> str:
        cells, col = [], 0
        for raw in split_cells(row):
            raw = raw.strip()
            span = 1
            m = re.match(r"\\multicolumn\{(\d+)\}\{([^}]*)\}", raw)
            if m:
                span = int(m.group(1))
                content, _ = braced(raw, m.end())
                align = "center"
            else:
                content = raw
                align = aligns[col] if col < len(aligns) else "left"
            attrs = f' colspan="{span}"' if span > 1 else ""
            attrs += f' class="a-{align}"'
            cells.append(f"<{cell_tag}{attrs}>{render_inline(state, content)}</{cell_tag}>")
            col += span
        return f"<tr>{''.join(cells)}</tr>"

    thead = "".join(row_html(r, "th") for r in head_rows)
    tbodies = "".join(
        "<tbody>" + "".join(row_html(r, "td") for r in rows) + "</tbody>" for rows in groups if rows
    )
    return f'<div class="table-scroll"><table><thead>{thead}</thead>{tbodies}</table></div>'


def number_float(state: State, kind: str) -> str:
    if kind == "figure":
        state.fig += 1
        return f"{state.chapter}.{state.fig}"
    state.tab += 1
    return f"{state.chapter}.{state.tab}"


def render_float(state: State, kind: str, body: str, png_dir: Path) -> str:
    """Figures and tables. A table env may hold several caption+tabular groups (minipages)."""
    out = []
    pending_caption: tuple[str, str] | None = None  # (number, caption html)
    pending_anchor, last_num = "", ""
    tok = re.compile(
        r"\\caption|\\label\{([^}]*)\}|\\includegraphics|\\begin\{(tabular|tabularx)\}"
    )
    i = 0
    figure_img = ""
    while True:
        m = tok.search(body, i)
        if not m:
            break
        if m.group(0) == "\\caption":
            _, j = bracketed(body, m.end())
            cap, i = braced(body, j)
            num = number_float(state, kind)
            pending_anchor = f"{'fig' if kind == 'figure' else 'tab'}-{num.replace('.', '-')}"
            pending_caption = (num, render_inline(state, cap))
            last_num = num
            if kind == "figure" and figure_img:
                out.append(figure_html(pending_anchor, figure_img, pending_caption))
                figure_img, pending_caption = "", None
            continue
        if m.group(1) is not None:
            if not last_num:
                raise LatexError(f"label {m.group(1)} before any caption")
            state.labels[m.group(1)] = Target(last_num, pending_anchor, kind)
            i = m.end()
            continue
        if m.group(0) == "\\includegraphics":
            opt, j = bracketed(body, m.end())
            path, i = braced(body, j)
            figure_img = image_html(state, path, opt or "", png_dir)
            if pending_caption:
                out.append(figure_html(pending_anchor, figure_img, pending_caption))
                figure_img, pending_caption = "", None
            continue
        env = m.group(2)
        j = m.end()
        if env == "tabularx":
            _, j = braced(body, j)
        spec, j = braced(body, j)
        tbody, i = env_body(body, env, j)
        table = render_tabular(state, spec, tbody)
        if not pending_caption:
            raise LatexError("table without caption")
        num, cap = pending_caption
        out.append(
            f'<figure class="paper-table" id="{pending_anchor}">'
            f'<figcaption><span class="float-label">Table {num}.</span> {cap}</figcaption>'
            f"{table}</figure>"
        )
        pending_caption = None
    return "".join(out)


def figure_html(anchor: str, img: str, caption: tuple[str, str]) -> str:
    num, cap = caption
    return (
        f'<figure class="paper-figure" id="{anchor}">{img}'
        f'<figcaption><span class="float-label">Figure {num}.</span> {cap}</figcaption></figure>'
    )


def image_html(state: State, path: str, opt: str, png_dir: Path) -> str:
    stem = Path(path).stem
    src = png_dir / f"{stem}.png"
    if Path(path).suffix.lower() != ".pdf":
        src = PAPER / path
    if not src.exists():
        raise LatexError(f"no web image for {path} (looked for {src})")
    dest = OUT_FIG / f"{stem}.png"
    width = height = None
    if state.dry:
        return ""
    OUT_FIG.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image  # optional

        with Image.open(src) as im:
            if im.width > MAX_FIG_WIDTH:
                im = im.resize(
                    (MAX_FIG_WIDTH, round(im.height * MAX_FIG_WIDTH / im.width)), Image.LANCZOS
                )
            im.save(dest, optimize=True)
            width, height = im.size
    except ImportError:
        shutil.copyfile(src, dest)
    state.figures_used.append(dest.name)
    m = re.search(r"width=([\d.]*)\\textwidth", opt)
    scale = float(m.group(1) or 1) if m else 1.0
    size = f' width="{width}" height="{height}"' if width else ""
    style = f' style="max-width:{scale * 100:.0f}%"' if scale < 1 else ""
    url = f"{FIG_URL}/{dest.name}"
    return (
        f'<a class="figure-zoom" href="{url}" target="_blank" rel="noopener"'
        f' aria-label="Open the full-size figure">'
        f'<img src="{url}" alt="" loading="lazy"{size}{style}></a>'
    )


def render_chapter(state: State, text: str, png_dir: Path, appendix: bool) -> str:
    out, i = [], 0
    while True:
        m = BLOCK.search(text, i)
        out.extend(paragraphs(state, text[i : m.start() if m else len(text)]))
        if not m:
            break
        if m.group(1):
            level = m.group(1)
            title, j = braced(text, m.end() - 1)
            label, i = take_label(text, j)
            if level == "chapter":
                if appendix:
                    state.chapter = chr(ord("A") + state.appendix_index)
                    state.appendix_index += 1
                else:
                    state.chapter = str(int(state.chapter or 0) + 1)
                state.sec = state.sub = state.fig = state.tab = 0
                number, tag = state.chapter, "h2"
                anchor = f"ch-{number}"
                display = f"Appendix {number}" if appendix else f"Chapter {number}"
            elif level == "section":
                state.sec += 1
                state.sub = 0
                number, tag = f"{state.chapter}.{state.sec}", "h3"
                anchor, display = f"sec-{number.replace('.', '-')}", number
            else:
                state.sub += 1
                number, tag = f"{state.chapter}.{state.sec}.{state.sub}", "h4"
                anchor, display = f"sec-{number.replace('.', '-')}", number
            if label:
                state.labels[label] = Target(number, anchor, level)
            title_html = render_inline(state, title)
            if level != "subsection":
                state.toc.append(
                    {
                        "id": anchor,
                        "number": number,
                        "title": html.unescape(re.sub("<[^>]+>", "", title_html)),
                        "level": 1 if level == "chapter" else 2,
                    }
                )
            out.append(
                f'<{tag} id="{anchor}"><span class="heading-number">{display}</span> '
                f"{title_html}</{tag}>"
            )
        else:
            env = m.group(2)
            body, i = env_body(text, env, m.end())
            if env in ("figure", "table"):
                out.append(render_float(state, env, body, png_dir))
            else:
                out.append(render_list(state, env, body))
    return "\n".join(out)


# --------------------------------------------------------------------------- main


def collect_labels(bib: dict[str, BibEntry], chapters: list[tuple[str, bool]], png_dir: Path):
    """First pass, so forward references (e.g. Chapter 1 -> Chapter 5) resolve in the second."""
    dry = State(bib=bib, labels=_AnyLabels(), dry=True)
    for text, appendix in chapters:
        render_chapter(dry, text, png_dir, appendix)
    for e in bib.values():
        e.cited = False
    return dict(dry.labels)


class _AnyLabels(dict):
    """Label table for the first pass: references to not-yet-seen labels get a placeholder."""

    def __missing__(self, key):
        return Target("?", "", "?")

    def __contains__(self, key):
        return True


def pdf_date(pdf: Path) -> date:
    """The PDF's own /CreationDate. File mtimes change on every git checkout."""
    m = re.search(rb"/CreationDate\s*\(D:(\d{4})(\d{2})(\d{2})", pdf.read_bytes())
    if not m:
        raise LatexError(f"no /CreationDate in {pdf}")
    return date(*(int(g) for g in m.groups()))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--png-dir", type=Path, default=ROOT / "paper_results" / "figures")
    args = ap.parse_args()

    main_tex = read_tex(PAPER / "main.tex")
    bib = parse_bib(PAPER / "bibliography.bib")

    abstract_src, _ = env_body(main_tex, "abstract", main_tex.index("\\begin{abstract}") + 16)
    abstract_src = re.sub(r"\\addchaptertocentry\{[^}]*\}", "", abstract_src)
    ack_src, _ = env_body(
        main_tex, "acknowledgements", main_tex.index("\\begin{acknowledgements}") + 24
    )
    ack_src = re.sub(r"\\addchaptertocentry\{\\acknowledgementname\}", "", ack_src)
    greek = re.search(
        r"\\chapter\{Περίληψη στα Ελληνικά\}\s*\\addchaptertocentry\{[^}]*\}"
        r"(.*?)\\selectlanguage\{english\}",
        main_tex,
        re.S,
    )
    if not greek:
        raise LatexError("Greek abstract not found")

    body_part = main_tex[main_tex.index("\\mainmatter") :]
    appendix_at = body_part.index("\\appendix")
    chapters: list[tuple[str, bool]] = []
    for m in re.finditer(r"\\include\{([^}]*)\}", body_part):
        chapters.append((read_tex(PAPER / f"{m.group(1)}.tex"), m.start() > appendix_at))

    state = State(bib=bib, labels=collect_labels(bib, chapters, args.png_dir))
    body = "\n".join(render_chapter(state, text, args.png_dir, app) for text, app in chapters)

    cited = sorted(
        (e for e in bib.values() if e.cited),
        key=lambda e: (e.cite_label().lower(), e.year),
    )
    references = [{"id": f"ref-{e.key}", "html": format_reference(e)} for e in cited]

    abstract_html = "".join(paragraphs(state, abstract_src))
    words = len(re.sub("<[^>]+>", " ", abstract_html + body).split())
    pdf = PAPER / "main.pdf"
    built = pdf_date(pdf)

    paper = {
        "meta": {
            "title": render_inline(state, command_arg(main_tex, "thesistitle")),
            "author": re.sub(r"\\textsc\{([^}]*)\}", r"\1", command_arg(main_tex, "author")),
            "supervisor": re.sub(
                r"\\textsc\{([^}]*)\}", r"\1", command_arg(main_tex, "supervisor")
            ),
            "degree": command_arg(main_tex, "degree"),
            "university": command_arg(main_tex, "university"),
            "department": command_arg(main_tex, "department"),
            "date": built.isoformat(),
            "pdfPath": "paper/main.pdf",
        },
        "abstract": abstract_html,
        "abstractGreek": "".join(paragraphs(state, greek.group(1))),
        "acknowledgements": "".join(paragraphs(state, ack_src)),
        "toc": state.toc,
        "body": body,
        "references": references,
        "wordCount": words,
        "readingMinutes": max(1, round(words / WORDS_PER_MINUTE)),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(paper, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    stale = {p.name for p in OUT_FIG.glob("*.png")} - set(state.figures_used)
    for name in stale:
        (OUT_FIG / name).unlink()
    print(
        f"wrote {OUT_JSON.relative_to(ROOT)}: {len(state.toc)} headings, "
        f"{len(state.figures_used)} figures, {len(references)} references, "
        f"{words} words (~{paper['readingMinutes']} min)"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LatexError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
