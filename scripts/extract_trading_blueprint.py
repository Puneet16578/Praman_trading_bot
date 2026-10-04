"""Regenerate the extracted body of docs/desk/TRADING_BLUEPRINT.md from the blueprint PDF.

Uses pdfplumber (already a project requirement). Tables become Markdown tables; other text keeps
its order, with headings recovered from font size and monospace runs kept as code blocks. Only the
part above AMENDMENTS_MARKER is rewritten, so the approved Praman amendments are never touched.
"""
from collections import Counter
import hashlib
from pathlib import Path
import sys

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / 'docs/desk/blueprint/Praman_High_Selectivity_Trading_System_Blueprint.pdf'
OUTPUT = ROOT / 'docs/desk/TRADING_BLUEPRINT.md'
AMENDMENTS_MARKER = '<!-- PRAMAN AMENDMENTS BELOW: maintained by hand, never regenerated -->'
HEADER_SIZE = 7.5


def _cell(text):
    text = (text or '').replace('-\n', '-')  # rejoin words hyphenated across cell lines
    return ' '.join(text.split()).replace('|', '\\|')


def _table(rows):
    rows = [[_cell(c) for c in row] for row in rows]
    lines = ['| ' + ' | '.join(rows[0]) + ' |', '|' + '---|' * len(rows[0])]
    lines += ['| ' + ' | '.join(row) + ' |' for row in rows[1:]]
    return lines


def _line_style(line):
    size = Counter(round(c['size'], 1) for c in line['chars']).most_common(1)[0][0]
    font = Counter(c['fontname'] for c in line['chars']).most_common(1)[0][0]
    return size, font


def page_blocks(page):
    """Ordered (top, kind, payload) blocks for one page."""
    tables = page.find_tables()
    boxes = [t.bbox for t in tables]
    blocks = [(t.bbox[1], 'table', t.extract()) for t in tables]
    inside = lambda l: any(x0 - 1 <= l['x0'] and l['x1'] <= x1 + 1 and top - 1 <= l['top'] and l['bottom'] <= bottom + 1
                           for x0, top, x1, bottom in boxes)
    for line in page.extract_text_lines():
        if inside(line):
            continue
        size, font = _line_style(line)
        if size <= HEADER_SIZE:
            continue
        kind = ('h2' if size >= 16 else 'h3' if size >= 12 else 'h4' if size >= 10.5 and 'Bold' in font
                else 'code' if 'Mono' in font else 'text')
        blocks.append((line['top'], kind, line['text'].strip()))
    return sorted(blocks, key=lambda b: b[0])


def _is_bullet(kind, payload):
    return kind == 'text' and (payload.startswith('•') or payload[:1].islower())


def render(pdf_path=PDF):
    out, code, para = [], [], []

    def close_list():
        if out and out[-1].startswith('- '):
            out.append('')

    def flush():
        if code:
            out.extend(['```', *code, '```', '']); code.clear()
        if para:
            out.extend([' '.join(para), '']); para.clear()

    with pdfplumber.open(pdf_path) as pdf:
        for number, page in enumerate(pdf.pages, 1):
            for _, kind, payload in page_blocks(page):
                if not _is_bullet(kind, payload):
                    close_list()
                if kind == 'table':
                    flush(); out.extend(_table(payload)); out.append('')
                elif kind == 'code':
                    if para:
                        flush()
                    code.append(payload)
                elif kind in ('h2', 'h3', 'h4'):
                    flush(); out.extend([{'h2': '## ', 'h3': '### ', 'h4': '#### '}[kind] + payload, ''])
                elif payload.startswith('•'):
                    flush(); out.append('- ' + payload.lstrip('• ').strip())
                elif out and out[-1].startswith('- ') and not para and payload[:1].islower():
                    out[-1] += ' ' + payload  # wrapped bullet continuation
                else:
                    if code:
                        flush()
                    para.append(payload)
            flush()
            close_list()
            out.append(f'<!-- end of PDF page {number} -->')
            out.append('')
    return '\n'.join(out)


def main():
    digest = hashlib.sha256(PDF.read_bytes()).hexdigest()
    head = ['# Praman trading blueprint', '',
            'Extracted from `docs/desk/blueprint/Praman_High_Selectivity_Trading_System_Blueprint.pdf` '
            f'(SHA-256 `{digest}`) by `python scripts/extract_trading_blueprint.py` using pdfplumber. '
            'The text above the amendments marker is regenerated from the PDF; the user-approved '
            '"Praman amendments" below it are maintained by hand and take precedence over the blueprint '
            'where they differ. CLAUDE.md and AGENTS.md take precedence over both.', '', '']
    body = '\n'.join(head) + render() + '\n'
    tail = ''
    if OUTPUT.exists():
        existing = OUTPUT.read_text(encoding='utf-8')
        if AMENDMENTS_MARKER in existing:
            tail = existing[existing.index(AMENDMENTS_MARKER):]
    OUTPUT.write_text(body + (tail or AMENDMENTS_MARKER + '\n'), encoding='utf-8', newline='\n')
    print(f'Wrote {OUTPUT.as_posix()} from PDF sha256 {digest}')


if __name__ == '__main__':
    sys.exit(main())
