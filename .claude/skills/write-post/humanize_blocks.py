#!/usr/bin/env python3
"""humanize-korean 윤문 전후 처리.

mask:   글의 front matter를 떼고, 코드 블록·표·그림·HTML 주석을 ⟦B01⟧ 자리표시로 바꿔
        <run_dir>/01_input.txt 에 쓴다. 원문은 source.md, 뗀 블록은 blocks.json 에 둔다.
unmask: <run_dir>/final.md(윤문본)에서 HUMANIZE-SUMMARY 블록을 지우고 자리표시를 되돌린 뒤,
        링크 주소·인라인 코드·헤딩 단계·숫자가 원문과 같은지 검사한다.
        문제가 없고 글 파일이 mask 이후 바뀌지 않았으면 글 파일을 덮어쓴다.

    python3 humanize_blocks.py mask   content/blog/<slug>.md _workspace/<run_id>
    python3 humanize_blocks.py unmask _workspace/<run_id> content/blog/<slug>.md
"""
import collections
import json
import pathlib
import re
import sys

FM_RE = re.compile(r"\A---\n.*?\n---\n", re.S)
LINK_RE = re.compile(r"\]\(([^)\s]+)")
ICODE_RE = re.compile(r"`([^`\n]+)`")
HEAD_RE = re.compile(r"^(#{1,6}) ", re.M)
NUM_RE = re.compile(r"\d+(?:\.\d+)?")


def split_fm(text):
    m = FM_RE.match(text)
    return (m.group(0), text[m.end():]) if m else ("", text)


def mask(body):
    lines, out, blocks, i = body.split("\n"), [], [], 0

    def hold(chunk):
        blocks.append(chunk)
        out.append(f"⟦B{len(blocks):02d}⟧")

    while i < len(lines):
        line, s = lines[i], lines[i].lstrip()
        fence = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence:
            mark, j = fence.group(1), i + 1
            close = re.compile(r"^\s*" + re.escape(mark[0]) + "{" + str(len(mark)) + r",}\s*$")
            while j < len(lines) and not close.match(lines[j]):
                j += 1
            hold("\n".join(lines[i:j + 1]))
            i = j + 1
        elif s.startswith("<!--"):
            j = i
            while j < len(lines) and "-->" not in lines[j]:
                j += 1
            hold("\n".join(lines[i:j + 1]))
            i = j + 1
        elif s.startswith("|"):
            j = i
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                j += 1
            hold("\n".join(lines[i:j]))
            i = j
        elif re.match(r"^\s*!\[.*\]\(.*\)\s*$", line) or re.match(r"^\s*\{\{[<%].*[>%]\}\}\s*$", line) \
                or re.match(r"^\s*<(figure|img|div|details|summary|/)", s):
            hold(line)
            i += 1
        else:
            out.append(line)
            i += 1
    return "\n".join(out), blocks


def strip_numbers_scope(text):
    return re.sub(r"\]\([^)]*\)|`[^`]*`", "", text)


def compare(before, after):
    issues, C = [], collections.Counter
    lb, la = C(LINK_RE.findall(before)), C(LINK_RE.findall(after))
    if lb != la:
        issues.append(f"링크 주소가 다름: 빠짐 {dict(lb - la)} / 생김 {dict(la - lb)}")
    # 횟수까지 비교한다. "최소 5개, 최대 5개"에서 5 하나가 빠져도 잡혀야 한다.
    cb, ca = C(ICODE_RE.findall(before)), C(ICODE_RE.findall(after))
    if cb != ca:
        issues.append(f"인라인 코드가 다름: 빠짐 {dict(cb - ca)} / 생김 {dict(ca - cb)}")
    hb, ha = HEAD_RE.findall(before), HEAD_RE.findall(after)
    if hb != ha:
        issues.append(f"헤딩 단계가 다름: {hb} → {ha}")
    nb = C(NUM_RE.findall(strip_numbers_scope(before)))
    na = C(NUM_RE.findall(strip_numbers_scope(after)))
    if nb != na:
        issues.append(f"숫자가 다름: 빠짐 {dict(nb - na)} / 생김 {dict(na - nb)}")
    return issues


def cmd_mask(post, run_dir):
    post, run_dir = pathlib.Path(post), pathlib.Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    text = post.read_text(encoding="utf-8")
    fm, body = split_fm(text)
    masked, blocks = mask(body)
    (run_dir / "01_input.txt").write_text(masked, encoding="utf-8")
    (run_dir / "source.md").write_text(text, encoding="utf-8")
    (run_dir / "blocks.json").write_text(json.dumps({"fm": fm, "blocks": blocks}, ensure_ascii=False),
                                         encoding="utf-8")
    print(f"{run_dir}/01_input.txt: 자리표시 {len(blocks)}개")


def cmd_unmask(run_dir, post):
    run_dir, post = pathlib.Path(run_dir), pathlib.Path(post)
    source = (run_dir / "source.md").read_text(encoding="utf-8")
    if post.read_text(encoding="utf-8") != source:
        sys.exit(f"중단: {post}가 mask 이후 바뀌었습니다. mask부터 다시 하세요.")
    meta = json.loads((run_dir / "blocks.json").read_text(encoding="utf-8"))
    final = (run_dir / "final.md").read_text(encoding="utf-8")
    final = re.sub(r"\n*<!--\s*HUMANIZE-SUMMARY.*?-->\s*", "\n", final, flags=re.S)
    issues = []
    found = re.findall(r"⟦B(\d\d)⟧", final)
    if found != [f"{k:02d}" for k in range(1, len(meta["blocks"]) + 1)]:
        issues.append(f"자리표시 순서·개수가 다름: {found}")
    for k, block in enumerate(meta["blocks"], 1):
        final = re.sub(r"^[ \t]*⟦B%02d⟧[ \t]*$" % k, lambda _m, b=block: b, final, count=1, flags=re.M)
    if "⟦B" in final:
        issues.append("자리표시가 혼자 한 줄에 있지 않음")
    src_body = split_fm(source)[1]
    issues += compare(src_body, final)
    if issues:
        print("적용하지 않음:")
        for issue in issues:
            print("  ✗", issue)
        sys.exit(1)
    lead = re.match(r"\n*", src_body).group(0)
    post.write_text(meta["fm"] + lead + final.strip("\n") + "\n", encoding="utf-8")
    print(f"{post}: 윤문본 적용")


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in ("mask", "unmask"):
        sys.exit(__doc__)
    (cmd_mask if sys.argv[1] == "mask" else cmd_unmask)(sys.argv[2], sys.argv[3])
