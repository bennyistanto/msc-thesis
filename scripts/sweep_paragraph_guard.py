"""Long-sentence / long-paragraph sweep for the thesis .tex files.

Guards (flag if exceeded):
  SENTENCE  > 45 words
  PARAGRAPH > 180 words  OR  > 6 sentences
"""
import re, sys

SENT_MAX = 45
PARA_WORDS = 180
PARA_SENTS = 6

ABBR = ("e.g.", "i.e.", "cf.", "vs.", "et al.", "Fig.", "Eq.", "no.",
        "approx.", "Dr.", "St.")


def clean_inline(s):
    # normalise LaTeX inline so word/sentence counts reflect prose
    s = re.sub(r'\\(citep|citet|cite|autocite)\s*\{[^}]*\}', 'CITE', s)
    s = re.sub(r'\\(ref|eqref|autoref|Cref|cref)\s*\{[^}]*\}', 'REF', s)
    s = re.sub(r'\$[^$]*\$', 'MATH', s)
    s = re.sub(r'\\[a-zA-Z]+\s*\{([^}]*)\}', r'\1', s)   # \textit{x}->x
    s = re.sub(r'\\[a-zA-Z]+', ' ', s)                    # bare macros
    s = re.sub(r'[{}~]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def split_sentences(p):
    # protect abbreviations, then split on . ! ? followed by space+capital
    tmp = p
    for a in ABBR:
        tmp = tmp.replace(a, a.replace('.', '<DOT>'))
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z(])', tmp)
    return [x.replace('<DOT>', '.').strip() for x in parts if x.strip()]


def is_prose(block):
    b = block.strip()
    if not b:
        return False
    first = b.lstrip()[:1]
    if first == '\\' or first == '%':
        return False
    # skip blocks that are mostly latex structure
    if re.match(r'\\(begin|end|item|caption|includegraphics|section|'
                r'subsection|chapter|label|centering)', b.lstrip()):
        return False
    return True


def analyse(fn):
    raw = open(fn, encoding='utf-8').read()
    # drop comment lines
    lines = [l for l in raw.split('\n') if not l.lstrip().startswith('%')]
    text = '\n'.join(lines)
    # remove whole float/list/math environments so they are not "paragraphs"
    for env in ('figure', 'table', 'tabular', 'tabular\\*', 'equation',
                'align', 'itemize', 'enumerate', 'align\\*'):
        text = re.sub(r'\\begin\{%s\}.*?\\end\{%s\}' % (env, env), '\n\n',
                      text, flags=re.DOTALL)
    paras = re.split(r'\n\s*\n', text)
    long_sents, long_paras = [], []
    for p in paras:
        if not is_prose(p):
            continue
        cp = clean_inline(p)
        if len(cp) < 40:
            continue
        sents = split_sentences(cp)
        nwords = len(cp.split())
        nsent = len(sents)
        if nwords > PARA_WORDS or nsent > PARA_SENTS:
            long_paras.append((nwords, nsent, cp[:70]))
        for s in sents:
            w = len(s.split())
            if w > SENT_MAX:
                long_sents.append((w, s[:120]))
    return long_sents, long_paras


for fn in sys.argv[1:]:
    ls, lp = analyse(fn)
    base = fn.split('/')[-1].split('\\')[-1]
    print('\n==================== %s ====================' % base)
    print('LONG PARAGRAPHS (>%dw or >%ds): %d' % (PARA_WORDS, PARA_SENTS, len(lp)))
    for w, s, head in sorted(lp, reverse=True):
        print('   %3dw %2ds | %s...' % (w, s, head))
    print('LONG SENTENCES (>%dw): %d' % (SENT_MAX, len(ls)))
    for w, head in sorted(ls, reverse=True):
        print('   %3dw | %s...' % (w, head))
