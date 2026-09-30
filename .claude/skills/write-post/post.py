#!/usr/bin/env python3
"""블로그 글 도구. 저장소 루트에서 실행한다.

  post.py new <slug> --title "제목" --category Gradle --tags "A,B" --date 2026-07-25
  post.py check [slug ...]      머리말·문체·코드 블록·식별어 검사 + Hugo 빌드(초안 포함)
  post.py preview               초안 포함 미리보기 서버(1313)를 뒤에서 띄운다
  post.py shot <slug> [--width 1280] [--dark]   미리보기 화면을 PNG로 찍는다
"""
import argparse, datetime, os, re, subprocess, sys, tempfile, time, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
BLOG = os.path.join(ROOT, "content", "blog")
TERMS = os.path.join(ROOT, "content", ".private", "forbidden-terms.txt")
HUGO = os.environ.get("HUGO", os.path.expanduser("~/.local/hugo/hugo"))
KST = datetime.timezone(datetime.timedelta(hours=9))
TMP = os.environ.get("CLAUDE_JOB_DIR", tempfile.gettempdir())


def die(msg):
    print(msg, file=sys.stderr); sys.exit(1)


def front(text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return None, text
    fm = {}
    for line in m.group(1).split("\n"):
        k, _, v = line.partition(":")
        if _ and not line.startswith(" "):
            fm[k.strip()] = v.strip().strip('"')
    return fm, m.group(2)


def cmd_new(a):
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", a.slug):
        die("slug는 소문자·숫자·하이픈만")
    path = os.path.join(BLOG, a.slug + ".md")
    if os.path.exists(path):
        die(f"이미 있음: {path}")
    d = a.date or datetime.date.today().isoformat()
    tags = ", ".join(f'"{t.strip()}"' for t in a.tags.split(",") if t.strip())
    body = f'''---
title: "{a.title}"
description: ""
date: {d}T21:00:00+09:00
draft: true
categories: ["{a.category}"]
tags: [{tags}]
---

(겪은 불편이나 상황 2~4문장. 부제·요약 없음.)

이 글에서는 …를 적습니다.

## (배경: 어떻게 동작하는가)

## (원인 또는 문제)

## (고친 방법과 이유)

## (확인한 것)

## 마치며

(배운 점 2~3문장.)
'''
    open(path, "w", encoding="utf-8").write(body)
    print(f"만듦: {os.path.relpath(path, ROOT)}  (date는 작업일 + 7~14일로 고칠 것)")


def load_terms():
    if not os.path.exists(TERMS):
        return []
    return [l.strip() for l in open(TERMS, encoding="utf-8") if l.strip() and not l.startswith("#")]


def check_file(path, terms):
    rel = os.path.relpath(path, ROOT)
    text = open(path, encoding="utf-8").read()
    errs, warns = [], []
    fm, body = front(text)
    if fm is None:
        return [f"{rel}: 머리말(---) 없음"], []
    for k in ("title", "description", "date", "draft", "categories", "tags"):
        if k not in fm:
            errs.append(f"머리말에 {k} 없음")
    desc = fm.get("description", "")
    if not desc:
        errs.append("description 비어 있음")
    elif re.search(r"(풀어 봅니다|이야기입니다|정리했습니다|살펴봅니다|알아봅니다)\.?$", desc):
        errs.append(f"description이 소개 문장: {desc}")
    if fm.get("categories", "").count(",") > 0:
        errs.append("categories는 하나만")
    if not re.match(r'^\["[A-Za-z][^"]*"\]$', fm.get("categories", "")):
        warns.append(f"categories는 영어 기술 이름 하나: {fm.get('categories')}")
    try:
        d = datetime.datetime.fromisoformat(fm["date"])
        if d.tzinfo is None:
            warns.append("date에 시간대(+09:00) 없음")
        elif d > datetime.datetime.now(KST):
            warns.append(f"date가 미래({d.date()}): 그날 전에는 사이트에 안 나옴")
    except (KeyError, ValueError):
        errs.append(f"date 형식 오류: {fm.get('date')}")
    if "## 마치며" not in body:
        errs.append("'## 마치며' 없음")
    if "## 코드로 보기" in body:
        errs.append("'코드로 보기' 링크 목록 금지 → 본문 중간에서 짚을 것")
    in_code = False; longest = 0
    for i, line in enumerate(body.split("\n"), 1):
        if line.startswith("```"):
            in_code = not in_code; continue
        if in_code:
            if re.search(r"\s(//|#)>\s", line):
                errs.append(f"{i}행: 줄 옆 설명(//>) 금지 → 코드 안 주석으로")
            longest = max(longest, len(line))
        else:
            if re.search(r"[\U0001F300-\U0001FAFF☀-➿]", line):
                errs.append(f"{i}행: 이모지")
            if re.search(r"(감사합니다|도움이 되(길|셨)|읽어 주셔서)", line):
                errs.append(f"{i}행: 상투적 마무리")
    if longest > 100:
        warns.append(f"코드 줄이 김({longest}자): 90자 안에서 끊을 것")
    for m in re.finditer(r"\[[^\]]*\]\((https?://[^)]+)\)", body):
        u = m.group(1)
        try:
            urllib.request.urlopen(urllib.request.Request(u, method="HEAD", headers={"User-Agent": "post-check"}), timeout=10)
        except Exception:
            try:
                urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "post-check"}), timeout=10)
            except Exception as e:
                warns.append(f"링크 응답 없음: {u} ({e})")
    low = text.lower()
    for t in terms:
        if t.lower() in low:
            errs.append(f"식별어 '{t}'")
    n = len(re.sub(r"```.*?```", "", body, flags=re.S))
    warns += [f"확인 필요 주석 {c}개" for c in [body.count("<!-- 확인 필요")] if c]
    print(f"{rel}: {n}자, {'문제 %d' % len(errs) if errs else '통과'}{', 주의 %d' % len(warns) if warns else ''}")
    for e in errs: print("  ✗", e)
    for w in warns: print("  ·", w)
    return errs, warns


def cmd_check(a):
    files = [os.path.join(BLOG, s + ".md") for s in a.slugs] if a.slugs else \
        sorted(p for p in (os.path.join(BLOG, f) for f in os.listdir(BLOG)) if p.endswith(".md") and not p.endswith("_index.md"))
    terms = load_terms()
    if not terms:
        print("주의: 식별어 목록이 없음", TERMS)
    total = 0
    for p in files:
        e, _ = check_file(p, terms); total += len(e)
    out = os.path.join(TMP, "post-check-site")
    r = subprocess.run([HUGO, "--gc", "--minify", "-D", "-F", "-d", out, "--quiet"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        print("Hugo 빌드 실패:\n" + r.stderr); sys.exit(1)
    print(f"Hugo 빌드(초안·미래 포함) 통과 → {out}")
    sys.exit(1 if total else 0)


def cmd_preview(a):
    if subprocess.run(["lsof", "-ti:1313"], capture_output=True).stdout:
        print("이미 1313에서 실행 중: http://localhost:1313/"); return
    log = open(os.path.join(TMP, "post-preview.log"), "w")
    subprocess.Popen([HUGO, "server", "-D", "-F", "--port", "1313", "--bind", "0.0.0.0", "--baseURL", "http://localhost:1313/"],
                     cwd=ROOT, stdout=log, stderr=log, start_new_session=True)
    for _ in range(30):
        time.sleep(1)
        try:
            urllib.request.urlopen("http://localhost:1313/", timeout=2); break
        except Exception:
            pass
    else:
        die("서버가 뜨지 않음: " + log.name)
    print("미리보기: http://localhost:1313/  (끄기: kill $(lsof -ti:1313))")


def cmd_shot(a):
    url = f"http://localhost:1313/blog/{a.slug}/"
    try:
        urllib.request.urlopen(url, timeout=5)
    except Exception:
        die(f"{url} 응답 없음. 먼저 post.py preview")
    out = os.path.join(TMP, f"shot-{a.slug}{'-dark' if a.dark else ''}.png")
    args = ["chromium-browser", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
            "--virtual-time-budget=6000", f"--window-size={a.width},{a.height}", f"--screenshot={out}"]
    if a.dark:
        args += ["--blink-settings=preferredColorScheme=0", "--force-dark-mode"]
    subprocess.run(args + [url], capture_output=True, timeout=90)
    if not os.path.exists(out):
        die("캡처 실패")
    print(out)


p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
s = p.add_subparsers(dest="cmd", required=True)
n = s.add_parser("new"); n.add_argument("slug"); n.add_argument("--title", required=True); n.add_argument("--category", required=True)
n.add_argument("--tags", default=""); n.add_argument("--date"); n.set_defaults(f=cmd_new)
c = s.add_parser("check"); c.add_argument("slugs", nargs="*"); c.set_defaults(f=cmd_check)
s.add_parser("preview").set_defaults(f=cmd_preview)
h = s.add_parser("shot"); h.add_argument("slug"); h.add_argument("--width", type=int, default=1280); h.add_argument("--height", type=int, default=4000)
h.add_argument("--dark", action="store_true"); h.set_defaults(f=cmd_shot)
a = p.parse_args(); a.f(a)
