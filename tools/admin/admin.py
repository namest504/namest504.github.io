#!/usr/bin/env python3
"""원고의 공개 상태를 바꾸는 작은 관리 화면.

원고 저장소(CONTENT_DIR)의 blog/*.md 머리말에서 draft 값을 바꾸고, 커밋해서 올린 뒤
공개 사이트 배포를 시작시킨다. Tailscale 주소에만 묶어서 띄울 것.

환경 변수
  CONTENT_DIR  원고 저장소 경로
  BIND, PORT   묶을 주소와 포트
  PREVIEW_URL  미리보기 서버 주소
  PUSH         1이면 커밋 뒤 push (기본 1)
  GH_TOKEN     있으면 배포 작업을 바로 시작시킨다
  DEPLOY_REPO  배포 작업이 있는 저장소 (기본 namest504/namest504.github.io)
"""
import datetime, html, json, os, re, secrets, subprocess, threading, time, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CONTENT = os.environ["CONTENT_DIR"]
BIND = os.environ.get("BIND", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8791"))
PREVIEW = os.environ.get("PREVIEW_URL", "").rstrip("/")
PUSH = os.environ.get("PUSH", "1") == "1"
TOKEN = os.environ.get("GH_TOKEN", "")
REPO = os.environ.get("DEPLOY_REPO", "namest504/namest504.github.io")
KST = datetime.timezone(datetime.timedelta(hours=9))
FORM_KEY = secrets.token_urlsafe(16)
LOCK = threading.Lock()
NAME = re.compile(r"^[a-z0-9][a-z0-9-]*\.md$")


def git(*args):
    return subprocess.run(["git", "-C", CONTENT, *args], capture_output=True, text=True, timeout=60)


def posts():
    out = []
    d = os.path.join(CONTENT, "blog")
    for f in sorted(os.listdir(d)):
        if not NAME.match(f):
            continue
        text = open(os.path.join(d, f), encoding="utf-8").read()
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not m:
            continue
        fm = m.group(1)
        get = lambda k: (re.search(rf'^{k}:\s*"?(.*?)"?\s*$', fm, re.M) or [None, ""])[1]
        try:
            date = datetime.datetime.fromisoformat(get("date"))
            if date.tzinfo is None:
                date = date.replace(tzinfo=KST)
        except ValueError:
            date = None
        draft = get("draft") == "true"
        if draft:
            state = "초안"
        elif date and date > datetime.datetime.now(KST):
            state = "예약"
        else:
            state = "공개"
        out.append({"file": f, "title": get("title"), "date": date, "state": state})
    out.sort(key=lambda p: p["date"] or datetime.datetime.min.replace(tzinfo=KST), reverse=True)
    return out


def set_field(f, key, value):
    path = os.path.join(CONTENT, "blog", f)
    text = open(path, encoding="utf-8").read()
    head, body = re.match(r"^(---\n.*?\n---\n)(.*)$", text, re.S).groups()
    if re.search(rf"^{key}:.*$", head, re.M):
        head = re.sub(rf"^{key}:.*$", f"{key}: {value}", head, count=1, flags=re.M)
    else:
        head = head[:-4] + f"{key}: {value}\n---\n"
    open(path, "w", encoding="utf-8").write(head + body)


def deploy():
    if not TOKEN:
        return "배포는 다음 자동 배포(매일 0시 10분) 때 반영됩니다."
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/actions/workflows/hugo.yaml/dispatches",
        data=json.dumps({"ref": "main"}).encode(), method="POST",
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"})
    try:
        urllib.request.urlopen(req, timeout=20)
        return "배포를 시작했습니다. 몇 분 뒤 사이트에 반영됩니다."
    except Exception as e:  # noqa: BLE001
        return f"배포를 시작하지 못했습니다: {e}"


def change(f, key, value, message):
    with LOCK:
        if PUSH:
            r = git("pull", "--rebase", "--quiet")
            if r.returncode:
                return "원고를 받아 오지 못했습니다: " + r.stderr.strip()
        set_field(f, key, value)
        git("add", "-A")
        r = git("commit", "-q", "-m", message)
        if r.returncode:
            return "바뀐 내용이 없습니다."
        if PUSH:
            r = git("push", "--quiet")
            if r.returncode:
                return "원고를 올리지 못했습니다: " + r.stderr.strip()
            return deploy()
        return "커밋했습니다. (시험 방식이라 올리지 않았습니다.)"


def sync_loop():
    while True:
        time.sleep(60)
        if PUSH:
            with LOCK:
                git("pull", "--rebase", "--quiet")


PAGE = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex">
<title>원고 관리</title><style>
body{margin:0;font-family:system-ui,sans-serif;background:#fff;color:#191919;line-height:1.6}
main{max-width:860px;margin:0 auto;padding:32px 20px 64px}
h1{font-size:22px;margin:0 0 20px}
.msg{padding:12px 16px;margin-bottom:20px;border:1px solid #191919;font-size:15px}
.row{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;padding:18px 0;border-top:1px solid #e4e4e4}
.info{flex:1 1 320px;min-width:0}
.title{font-size:17px;font-weight:700;color:#191919;text-decoration:none}
.meta{font-size:14px;color:#5c5c5c}
.state{display:inline-block;padding:1px 10px;border-radius:12px;font-size:13px;font-weight:700;margin-right:8px}
.공개{background:#e6f2ee;color:#0d5a48}.초안{background:#f0f0f0;color:#3a3a3a}.예약{background:#fff1d6;color:#7a4b00}
form{display:flex;gap:8px;align-items:center;margin:0}
button,input{font:inherit;min-height:44px;padding:0 14px;border:1px solid #191919;background:#fff;color:#191919;border-radius:6px}
button{cursor:pointer}button.go{background:#191919;color:#fff}
@media (prefers-color-scheme:dark){body{background:#161616;color:#ededed}.title{color:#ededed}.meta{color:#a6a6a6}
.row{border-color:#333}.msg{border-color:#ededed}button,input{background:#161616;color:#ededed;border-color:#ededed}
button.go{background:#ededed;color:#161616}.초안{background:#2a2a2a;color:#c4c4c4}.공개{background:#17332b;color:#7fd1b9}.예약{background:#3a2c10;color:#f0c674}}
</style></head><body><main><h1>원고 관리</h1>__MSG____ROWS__</main></body></html>"""


def render(msg=""):
    rows = []
    for p in posts():
        f, t = html.escape(p["file"]), html.escape(p["title"])
        day = p["date"].astimezone(KST).strftime("%Y-%m-%d") if p["date"] else ""
        link = f'{PREVIEW}/blog/{f[:-3]}/' if PREVIEW else "#"
        key = f'<input type="hidden" name="key" value="{FORM_KEY}"><input type="hidden" name="file" value="{f}">'
        if p["state"] == "초안":
            btn = (f'<form method="post" action="/publish" onsubmit="return confirm(\'공개할까요?\\n{t}\')">'
                   f'{key}<button class="go">공개</button></form>')
        else:
            btn = (f'<form method="post" action="/unpublish" onsubmit="return confirm(\'초안으로 되돌릴까요?\\n{t}\')">'
                   f'{key}<button>초안으로</button></form>')
        date_form = (f'<form method="post" action="/date">{key}'
                     f'<input type="date" name="date" value="{day}" aria-label="작성일">'
                     f'<button>날짜 변경</button></form>')
        rows.append(f'<div class="row"><div class="info"><a class="title" href="{link}">{t}</a>'
                    f'<div class="meta"><span class="state {p["state"]}">{p["state"]}</span>{day}</div></div>'
                    f'{date_form}{btn}</div>')
    m = f'<div class="msg">{html.escape(msg)}</div>' if msg else ""
    return PAGE.replace("__MSG__", m).replace("__ROWS__", "\n".join(rows))


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body="", location=None):
        data = body.encode()
        self.send_response(code)
        if location:
            self.send_header("Location", location)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path != "/":
            return self.send(404, "없는 주소입니다.")
        msg = urllib.parse.parse_qs(u.query).get("msg", [""])[0]
        self.send(200, render(msg))

    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        form = urllib.parse.parse_qs(self.rfile.read(n).decode())
        f = form.get("file", [""])[0]
        if form.get("key", [""])[0] != FORM_KEY or not NAME.match(f) \
                or not os.path.isfile(os.path.join(CONTENT, "blog", f)):
            return self.send(400, "잘못된 요청입니다.")
        if self.path == "/publish":
            msg = change(f, "draft", "false", f"공개: {f[:-3]}")
        elif self.path == "/unpublish":
            msg = change(f, "draft", "true", f"초안으로: {f[:-3]}")
        elif self.path == "/date":
            d = form.get("date", [""])[0]
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
                return self.send(400, "날짜 형식이 잘못됐습니다.")
            msg = change(f, "date", f"{d}T09:00:00+09:00", f"작성일 변경: {f[:-3]} {d}")
        else:
            return self.send(404, "없는 주소입니다.")
        self.send(303, location="/?msg=" + urllib.parse.quote(msg))

    def log_message(self, fmt, *args):
        print(self.address_string(), fmt % args, flush=True)


if __name__ == "__main__":
    threading.Thread(target=sync_loop, daemon=True).start()
    ThreadingHTTPServer((BIND, PORT), Handler).serve_forever()
