"""그림·그래프 SVG만 사이트 스타일로 찍어 본다(밝은/어두운 화면 두 장).

    python3 .claude/skills/write-post/svgshot.py content/blog/img/a.svg [b.svg ...]

출력: $CLAUDE_JOB_DIR/tmp/svgshot/{light,dark}.png. Read로 열어 글자 겹침·잘림을 확인한다.
먼저 post.py check 를 한 번 돌려 사이트 CSS가 빌드돼 있어야 한다.
"""
import glob
import os
import shutil
import subprocess
import sys

JOB = os.environ.get("CLAUDE_JOB_DIR", "/tmp")
# 첫 SVG 이름별로 따로 저장한다(여럿이 동시에 찍어도 덮이지 않게)
OUT = os.path.join(JOB, "tmp", "svgshot", os.path.splitext(os.path.basename(sys.argv[1]))[0] if len(sys.argv) > 1 else "_")
css = sorted(glob.glob(os.path.join(JOB, "post-check-site", "css", "*.css")))
if not css:
    sys.exit("사이트 CSS 없음: 먼저 post.py check 실행")
browser = (shutil.which("chromium-browser") or shutil.which("chromium")
           or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
os.makedirs(OUT, exist_ok=True)
figs = "".join(f'<figure class="diagram body">{open(p, encoding="utf-8").read()}</figure>' for p in sys.argv[1:])
height = 60 + 330 * len(sys.argv[1:])
for theme in ("light", "dark"):
    page = os.path.join(OUT, f"{theme}.html")
    with open(page, "w", encoding="utf-8") as f:
        f.write(f'<!doctype html><html lang="ko" data-theme="{theme}"><head><meta charset="utf-8">'
                f'<link rel="stylesheet" href="file://{css[-1]}">'
                '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gothic+A1:wght@400;700'
                '&family=JetBrains+Mono&display=swap">'
                '<style>body{display:block;min-height:0;padding:16px}.diagram{width:728px;margin:0 0 28px}</style>'
                f'</head><body>{figs}</body></html>')
    png = os.path.join(OUT, f"{theme}.png")
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=5000",
                    f"--window-size=780,{height}", f"--screenshot={png}", f"file://{page}"],
                   capture_output=True, timeout=90)
    print(png)
