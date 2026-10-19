"""Generate the practice-problem variants shown in the site's "New Problems" tab.

Usage (from the repo root; needs `pip install -r scripts/variants/requirements.txt`):
    python3 scripts/variants/build.py            # write variants/*.json
    python3 scripts/variants/build.py --check    # regenerate and fail if variants/ is out of date (CI)
    python3 scripts/variants/build.py --course 'Math 126'   # rebuild one course (repeatable)
    python3 scripts/variants/build.py --show ID  # print a few variants of one template, for review

Each template (m120.py ... m224.py, one file per course) is modelled on a real UW exam problem
(based_on={'exam': exam_id, 'problem': n}) or, for topics with no archived problems,
on the textbook section (based_on={'style': 'Stewart §16.4'}). Variants are seeded,
so the output only changes when a template does. Every variant's answer is
re-derived independently by the template's check() before it is written.
"""
import json
import multiprocessing
import os
import random
import re
import sys

import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

from common import TEMPLATES, Reject  # noqa: E402
import m120, m124, m125, m126, m207, m208, m224  # noqa: E402,F401  (registers the templates)
import time  # noqa: E402

PER_TEMPLATE = 40      # variants written per template
MIN_VARIANTS = 20      # a template that can't make this many distinct problems is a bug
OUT = os.path.join(ROOT, 'variants')


class BuildError(Exception):
    """A template failed; raised as an ordinary exception so it crosses the process pool."""


def load(f):
    with open(os.path.join(ROOT, f), encoding='utf-8') as fh:
        return json.load(fh)


def slug(s):
    return '-'.join(''.join(c if c.isalnum() else ' ' for c in s.lower()).split())


def based_on(t, exams, questions):
    """Resolve a template's based_on into a citation the site can show."""
    b = t['based_on']
    if 'style' in b:
        return {'style': b['style']}
    e = next((x for x in exams if x['id'].lower() == b['exam'].lower()), None)
    assert e, f"{t['id']}: unknown exam {b['exam']}"
    q = next((x for x in questions if x['source']['exam_id'].lower() == e['id'].lower()
              and x['source'].get('problem') == b['problem']), None)
    assert q, f"{t['id']}: {e['id']} has no problem {b['problem']} in questions.json"
    who = e.get('instructor') if e.get('instructor') not in (None, 'Staff') and e['type'] != 'Final' else ''
    label = f"{e['course']} {e['type']}, {e['quarter']} {e['year']}{f' ({who})' if who else ''}, Problem {b['problem']}"
    return {'exam': e['id'], 'problem': b['problem'], 'label': label, 'pdf': e.get('pdf'), 'question': q['id']}


def lint(tid, v):
    """Catch text that would render wrongly: control characters (e.g. a stray \\f from an unescaped
    '\\frac'), and a '<' followed by a letter inside math, which the browser would read as an HTML tag."""
    for k in ('problem', 'answer', 'solution'):
        if re.search(r'[\x00-\x09\x0b-\x1f]', v[k]):
            raise BuildError(f"✗ {tid}: control character in the {k} (an unescaped backslash?)")
        for seg in re.findall(r'\$[^$]*\$|\\\[.*?\\\]', v[k], re.S):
            if re.search(r'<[A-Za-z/!?]', seg):
                raise BuildError(f"✗ {tid}: '<' before a letter inside math in the {k} (use \\lt): {seg[:60]}")


def generate(t):
    out, seen = [], set()
    for attempt in range(PER_TEMPLATE * 40):
        if len(out) == PER_TEMPLATE:
            break
        rng = random.Random(f"{t['id']}#{attempt}")
        try:
            v = t['make'](rng)
        except Reject:
            continue
        if v['problem'] in seen:
            continue
        lint(t['id'], v)
        try:
            t['check'](v['data'])
        except Exception as err:
            raise BuildError(f"✗ {t['id']} attempt {attempt}: check failed: {err!r}\n{v['problem']}\n{v['answer']}") from None
        sp.core.cache.clear_cache()   # SymPy's cache otherwise grows across thousands of variants
        seen.add(v['problem'])
        out.append({'id': f"{t['id']}-{len(out) + 1:02d}", 'problem': v['problem'], 'answer': v['answer'], 'solution': v['solution']})
    if len(out) < MIN_VARIANTS:
        raise BuildError(f"✗ {t['id']}: only {len(out)} distinct variants")
    return out


def build_course(course):
    """Generate and check every template of one course. Returns (file name, file object, index entry)."""
    chapters = load('chapters.json')['courses']
    exams, questions = load('exams.json'), load('questions.json')
    names = {c['id']: c['name'] for c in chapters[course]['chapters']}
    order = list(names)
    ts = sorted((t for t in TEMPLATES if t['course'] == course), key=lambda t: (order.index(t['chapter']), t['id']))
    data = []
    for t in ts:
        t0 = time.time()
        assert t['chapter'] in names, f"{t['id']}: {t['chapter']} is not a {course} chapter"
        variants = generate(t)
        data.append({'id': t['id'], 'chapter': t['chapter'], 'chapter_name': names[t['chapter']],
                     'title': t['title'], 'based_on': based_on(t, exams, questions), 'variants': variants})
        print(f"  {t['id']:<34} {len(variants)} variants  ({time.time() - t0:.0f}s)", flush=True)
    name = f"{slug(course)}.json"
    entry = {'file': f'variants/{name}', 'templates': len(data), 'variants': sum(len(t['variants']) for t in data),
             'topics': [{'chapter': c, 'name': names[c], 'templates': sum(t['chapter'] == c for t in data)}
                        for c in order if any(t['chapter'] == c for t in data)]}
    return name, {'course': course, 'templates': data}, entry


def courses():
    return sorted({t['course'] for t in TEMPLATES}, key=lambda c: int(c.split()[-1]))


def build(only=None):
    """Build every course (in parallel, one process per course), or only the named ones.
    Courses not rebuilt keep their entry from the existing variants/index.json."""
    ids = [t['id'] for t in TEMPLATES]
    assert len(ids) == len(set(ids)), 'duplicate template ids'
    todo = [c for c in courses() if not only or c in only]
    assert not only or len(todo) == len(only), f'unknown course in {only}'
    with multiprocessing.Pool(min(len(todo), os.cpu_count() or 1)) as pool:
        results = pool.map(build_course, todo)
    files = {name: obj for name, obj, _ in results}
    index = load('variants/index.json')['courses'] if only else {}
    index.update({course: entry for course, (_, _, entry) in zip(todo, results)})
    index = {c: index[c] for c in courses() if c in index}
    files['index.json'] = {'note': 'Generated by scripts/variants/build.py; do not edit by hand.', 'courses': index}
    return files


def dump(obj):
    return json.dumps(obj, indent=1, ensure_ascii=False) + '\n'


def main(argv):
    if argv[:1] == ['--show']:
        t = next(t for t in TEMPLATES if t['id'] == argv[1])
        for v in generate(t)[: int(argv[2]) if len(argv) > 2 else 3]:
            print(f"── {v['id']}\nPROBLEM: {v['problem']}\nANSWER: {v['answer']}\nSOLUTION: {v['solution']}\n")
        return
    only = [argv[i + 1] for i, a in enumerate(argv) if a == '--course']
    files = build(only)
    if argv[:1] == ['--check']:
        stale = [n for n, obj in files.items()
                 if not os.path.exists(os.path.join(OUT, n)) or open(os.path.join(OUT, n), encoding='utf-8').read() != dump(obj)]
        extra = sorted(set(os.listdir(OUT)) - set(files)) if os.path.isdir(OUT) else []
        if stale or extra:
            raise SystemExit(f"✗ variants/ is out of date ({', '.join(stale + extra)}). Run python3 scripts/variants/build.py and commit the result.")
        print('✓ variants/ is up to date and every answer checks out')
        return
    os.makedirs(OUT, exist_ok=True)
    for n, obj in files.items():
        with open(os.path.join(OUT, n), 'w', encoding='utf-8') as fh:
            fh.write(dump(obj))
    total = sum(c['variants'] for c in files['index.json']['courses'].values())
    print(f"✓ Wrote {len(files) - 1} course file(s); {total} checked variants across {len(files['index.json']['courses'])} courses")


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except BuildError as err:
        raise SystemExit(str(err))
