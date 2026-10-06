"""Rebuild weekNN/commands.md from the lecture HTML: every code block, in lecture order, under its section heading.

Usage (from the module folder on the lecturer's machine, or anywhere with the lectures):
    python extract_commands.py <Lectures folder> <StudentRepo folder>
Each block is also syntax-checked: shell blocks with `bash -n`, Python blocks with ast.parse. Blocks that are
program output, YAML, netlists or messages are copied but not checked. The summary line counts both.
"""
import ast
import glob
import html
import os
import re
import shutil
import subprocess
import sys

SHELL_START = re.compile(r'^\s*(ros2|python3?|cd|source|export|colcon|docker|bash|ngspice|pip3?|sudo|ls|cat|mkdir|cp|'
                         r'echo|timeout|rviz2|rqt|gz|git|ollama|curl|yolo|candump|cansend|socat|top|htop|kill|pkill|'
                         r'watch|tar|xacro|printenv|nproc|free|df|du|rm)\b(?!:)')   # "gz: 5989 samples" is output


def heading_before(text, pos):
    heads = [(m.start(), m.group(1)) for m in re.finditer(r'<h[23][^>]*>(.*?)</h[23]>', text[:pos], re.S)]
    return clean(heads[-1][1]) if heads else ''


def clean(fragment):
    return html.unescape(re.sub(r'<[^>]+>', '', fragment)).strip()


def kind(code):
    lines = [l for l in code.splitlines() if l.strip() and not l.strip().startswith('#')]
    if not lines:
        return 'text'
    if lines[0].lstrip().startswith(('import ', 'from ', 'def ', 'class ')) or 'rclpy' in code and 'def ' in code:
        return 'python'
    if SHELL_START.match(lines[0]):
        return 'bash'
    return 'text'


def check(code, lang):
    if lang == 'python':
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False
    if lang == 'bash' and shutil.which('bash'):
        r = subprocess.run(['bash', '-n'], input=code, text=True, capture_output=True)
        return r.returncode == 0
    return None


def main(lectures, repo):
    total = checked = failed = 0
    for f in sorted(glob.glob(os.path.join(lectures, 'w*', 'Week[0-9][0-9]_*.html'))):
        if 'RGBD_SLAM' in f:                      # an old lecture kept in the w11 folder
            continue
        week = int(re.search(r'Week(\d\d)_', f).group(1))
        text = open(f, encoding='utf-8').read()
        title = clean(re.search(r'<title>(.*?)</title>', text, re.S).group(1))
        out = ['# Week %02d – commands and code from the lecture, in order' % week, '',
               'Generated from the lecture (%s) by `tools/extract_commands.py`. Run the commands in the module\'s' % title,
               'Docker container (`~/labs` is this repository). Longer programs are in `scripts/` – the lecture shows',
               'the key parts. Output blocks (what you should see) are included so you can compare.', '']
        last_head = None
        for n, m in enumerate(re.finditer(r'<pre[^>]*>(.*?)</pre>', text, re.S), 1):
            code = html.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip('\n')
            lang = kind(code)
            ok = check(code, lang)
            total += 1
            if ok is not None:
                checked += 1
                if not ok:
                    failed += 1
                    print('SYNTAX FAIL week %02d block %d (%s)' % (week, n, lang))
            head = heading_before(text, m.start())
            if head != last_head:
                out += ['## ' + head, '']
                last_head = head
            out += ['```' + ('bash' if lang == 'bash' else 'python' if lang == 'python' else 'text'), code, '```', '']
        path = os.path.join(repo, 'week%02d' % week, 'commands.md')
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('\n'.join(out))
    print('%d blocks, %d syntax-checked, %d failed' % (total, checked, failed))
    return failed


if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1], sys.argv[2]) else 0)
