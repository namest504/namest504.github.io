"""글에 넣는 그래프 생성기. 가로 막대·세로 묶음 막대·선 그래프를 SVG로 만든다.

색은 사이트 CSS 변수(var(--text), var(--link), var(--muted), var(--line), var(--code-bg))라
밝은/어두운 화면 모두 맞는다. 저장 위치는 content/blog/img/, 글에는 ![설명](img/이름.svg).

    import sys; sys.path.insert(0, ".claude/skills/write-post")
    from chart import bars, grouped, line
    bars("query-time.svg", "조회 조건별 응답 시간", unit="초",
         rows=[("전체 조회", 5), ("조건 조회 (고치기 전)", 305), ("조건 조회 (고친 뒤)", 2.9)],
         highlight=[2], log=True)

규칙: 강조색은 한 가지(고친 뒤·채택한 값)에만. 값은 막대·점 옆에 그대로 적는다.
값 차이가 수십 배를 넘으면 log=True. 실제로 잰 값만 쓴다.
`python3 chart.py` 는 예제 3장을 $CLAUDE_JOB_DIR/tmp/chart-demo/ 에 만든다.
"""
import html
import math
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "content", "blog", "img")
TEXT, MUTED, ACC, LINE, SOFT = "var(--text)", "var(--muted)", "var(--link)", "var(--line)", "var(--code-bg)"


def _esc(s):
    return html.escape(str(s))


def _num(v, unit=""):
    if isinstance(v, float) and not v.is_integer():
        t = f"{v:,.2f}" if abs(v) < 10 else f"{v:,.1f}"
        t = t.rstrip("0").rstrip(".")
    else:
        t = f"{int(v):,}"
    return f"{t}{unit}"


def _tw(s):
    """대략적인 글자 폭(px, 13~14px 글꼴). 한글은 넓게."""
    return sum(13.5 if ord(c) > 0x2E80 else 7.6 for c in str(s))


def _save(name, w, h, title, body, out):
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, name)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t">'
           f'<title id="t">{_esc(title)}</title>\n' + "\n".join(body) + "\n</svg>\n")
    with open(p, "w", encoding="utf-8") as f:
        f.write(svg)
    print(os.path.relpath(p))
    return p


def _nice(v):
    if v <= 0:
        return 1
    e = 10 ** math.floor(math.log10(v))
    for m in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if m * e >= v - 1e-9:
            return m * e
    return 10 * e


def _step(vmax):
    """눈금이 4~6개가 되는 깔끔한 간격(1·2·5 × 10^k)."""
    raw = vmax / 4
    e = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if m * e >= raw - 1e-12:
            return m * e
    return 10 * e


def bars(name, title, rows, unit="", highlight=(), log=False, note="", out=OUT):
    """가로 막대. rows=[(이름, 값), ...]. highlight=강조할 행 번호들."""
    W, bar_h, gap, top = 680, 26, 14, 14
    label_w = int(max(_tw(l) for l, _ in rows)) + 22
    right = int(max(_tw(_num(v, unit)) for _, v in rows)) + 18
    plot_w = W - label_w - right
    vals = [v for _, v in rows]
    if log:
        lo, hi = math.floor(math.log10(min(vals))), math.ceil(math.log10(max(vals)))
        if hi == lo:
            hi += 1
        sc = lambda v: (math.log10(v) - lo) / (hi - lo) * plot_w
        ticks = [10 ** k for k in range(lo, hi + 1)]
    else:
        step = _step(max(vals))
        top_v = step * math.ceil(max(vals) / step - 1e-9)
        sc = lambda v: v / top_v * plot_w
        ticks = [round(step * i, 10) for i in range(int(round(top_v / step)) + 1)]
    y_end = top + len(rows) * (bar_h + gap) - gap + 6
    H = y_end + 22 + (22 if note or log else 0)
    b = []
    for t in ticks:
        x = label_w + sc(t)
        b.append(f'<line x1="{x:.1f}" y1="{top - 4}" x2="{x:.1f}" y2="{y_end}" style="stroke:{LINE};stroke-width:1"/>')
        b.append(f'<text x="{x:.1f}" y="{y_end + 16}" text-anchor="middle" class="muted">{_esc(_num(t))}</text>')
    for i, (lab, v) in enumerate(rows):
        y = top + i * (bar_h + gap)
        hl = i in highlight
        w = max(sc(v), 2)
        cls = ' class="acc"' if hl else ""
        b.append(f'<text x="{label_w - 12}" y="{y + bar_h / 2 + 5}" text-anchor="end"{cls}>{_esc(lab)}</text>')
        b.append(f'<rect x="{label_w}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="3" '
                 f'style="fill:{ACC if hl else SOFT};stroke:{ACC if hl else TEXT};stroke-width:1.2"/>')
        b.append(f'<text x="{label_w + w + 8:.1f}" y="{y + bar_h / 2 + 5}" class="mono{" acc" if hl else ""}">'
                 f'{_esc(_num(v, unit))}</text>')
    if note or log:
        b.append(f'<text x="{label_w}" y="{H - 6}" class="muted">{_esc(note or "가로축은 로그 눈금")}</text>')
    return _save(name, W, H, title, b, out)


def grouped(name, title, groups, series, values, unit="", highlight_series=None, note="", out=OUT):
    """세로 묶음 막대. groups=[x축 묶음 이름], series=[계열 이름], values[계열][묶음].
    묶음끼리 단위가 다르면 묶음마다 따로 비율을 잡는다(값은 그대로 적힌다)."""
    W, H, left, bottom, top = 680, 300, 20, 70, 30
    plot_w, plot_h = W - left * 2, H - top - bottom
    n_g, n_s = len(groups), len(series)
    gw = plot_w / n_g
    bw = min(56, gw * 0.72 / n_s)
    b = [f'<line x1="{left}" y1="{top + plot_h}" x2="{W - left}" y2="{top + plot_h}" style="stroke:{TEXT};stroke-width:1"/>']
    for g, gname in enumerate(groups):
        gmax = max(values[s][g] for s in range(n_s)) or 1
        cx = left + gw * g + gw / 2
        x0 = cx - bw * n_s / 2
        for s in range(n_s):
            v = values[s][g]
            h = v / gmax * (plot_h - 24)
            x = x0 + s * bw
            hl = s == highlight_series
            b.append(f'<rect x="{x + 3:.1f}" y="{top + plot_h - h:.1f}" width="{bw - 6:.1f}" height="{h:.1f}" rx="2" '
                     f'style="fill:{ACC if hl else SOFT};stroke:{ACC if hl else TEXT};stroke-width:1.2"/>')
            b.append(f'<text x="{x + bw / 2:.1f}" y="{top + plot_h - h - 7:.1f}" text-anchor="middle" '
                     f'class="mono{" acc" if hl else ""}">{_esc(_num(v, unit))}</text>')
        b.append(f'<text x="{cx:.1f}" y="{top + plot_h + 22}" text-anchor="middle">{_esc(gname)}</text>')
    lx = left
    for s, sname in enumerate(series):
        hl = s == highlight_series
        b.append(f'<rect x="{lx}" y="{H - 24}" width="14" height="14" rx="2" '
                 f'style="fill:{ACC if hl else SOFT};stroke:{ACC if hl else TEXT};stroke-width:1.2"/>')
        b.append(f'<text x="{lx + 20}" y="{H - 12}" class="muted">{_esc(sname)}</text>')
        lx += 36 + _tw(sname)
    if note:
        b.append(f'<text x="{W - left}" y="{H - 12}" text-anchor="end" class="muted">{_esc(note)}</text>')
    return _save(name, W, H, title, b, out)


def line(name, title, xs, series, unit="", marks=(), highlight_series=0, note="", ymin=0, out=OUT):
    """선 그래프. xs=[x 이름], series=[(계열 이름, [값 또는 None ...]), ...].
    marks=[(x 번호, 글)] 은 세로 점선으로 사건을 표시한다."""
    W, H, left, bottom, top, right = 680, 290, 52, 56, 30, 30
    plot_w, plot_h = W - left - right, H - top - bottom
    allv = [v for _, vs in series for v in vs if v is not None]
    vmax = _nice(max(allv))
    step = plot_w / max(len(xs) - 1, 1)
    X = lambda i: left + i * step
    Y = lambda v: top + plot_h - (v - ymin) / (vmax - ymin) * plot_h
    b = []
    for i in range(5):
        v = ymin + (vmax - ymin) * i / 4
        b.append(f'<line x1="{left}" y1="{Y(v):.1f}" x2="{W - right}" y2="{Y(v):.1f}" style="stroke:{LINE};stroke-width:1"/>')
        b.append(f'<text x="{left - 8}" y="{Y(v) + 4:.1f}" text-anchor="end" class="muted">{_esc(_num(v))}</text>')
    for i, x in enumerate(xs):
        b.append(f'<text x="{X(i):.1f}" y="{top + plot_h + 20}" text-anchor="middle" class="muted">{_esc(x)}</text>')
    for i, t in marks:
        b.append(f'<line x1="{X(i):.1f}" y1="{top - 8}" x2="{X(i):.1f}" y2="{top + plot_h}" '
                 f'style="stroke:{MUTED};stroke-width:1;stroke-dasharray:4 4"/>')
        b.append(f'<text x="{X(i) - 6:.1f}" y="{top - 12}" text-anchor="end" class="muted">{_esc(t)}</text>')
    for s, (sname, vs) in enumerate(series):
        hl = s == highlight_series
        col = ACC if hl else TEXT
        pts = [(X(i), Y(v), v) for i, v in enumerate(vs) if v is not None]
        d = " ".join(f"{'M' if k == 0 else 'L'}{x:.1f} {y:.1f}" for k, (x, y, _) in enumerate(pts))
        b.append(f'<path d="{d}" style="fill:none;stroke:{col};stroke-width:{2.2 if hl else 1.5}"/>')
        for x, y, v in pts:
            b.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" style="fill:{col}"/>')
            b.append(f'<text x="{x:.1f}" y="{y - 10:.1f}" text-anchor="middle" class="mono{" acc" if hl else ""}">'
                     f'{_esc(_num(v, unit))}</text>')
    if len(series) > 1:
        lx = left
        for s, (sname, _) in enumerate(series):
            col = ACC if s == highlight_series else TEXT
            b.append(f'<line x1="{lx}" y1="{H - 17}" x2="{lx + 18}" y2="{H - 17}" style="stroke:{col};stroke-width:2"/>')
            b.append(f'<text x="{lx + 24}" y="{H - 12}" class="muted">{_esc(sname)}</text>')
            lx += 44 + _tw(sname)
    if note:
        b.append(f'<text x="{W - right}" y="{H - 12}" text-anchor="end" class="muted">{_esc(note)}</text>')
    return _save(name, W, H, title, b, out)


if __name__ == "__main__":
    demo = os.path.join(os.environ.get("CLAUDE_JOB_DIR", "/tmp"), "tmp", "chart-demo")
    bars("demo-bars.svg", "조회 조건별 응답 시간", unit="초",
         rows=[("전체 조회", 5), ("조건 조회 (고치기 전)", 305), ("조건 조회 (고친 뒤)", 2.9)],
         highlight=[2], log=True, out=demo)
    grouped("demo-grouped.svg", "전력 상한별 측정값", groups=["처리량 (청크/초)", "온도 (°C)", "팬 (%)"],
            series=["250W (기본)", "120W"], values=[[36.4, 80, 83], [34.2, 61, 46]], highlight_series=1,
            note="묶음마다 세로 비율이 다르다", out=demo)
    line("demo-line.svg", "가상 디스크 크기 변화", xs=["09-01", "09-28", "10-02", "10-20", "압축 뒤"],
         series=[("vhdx", [155, 116, 131.2, 140, 88])], unit="G", marks=[(4, "압축")], out=demo)
