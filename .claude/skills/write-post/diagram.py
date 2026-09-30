"""글에 넣는 그림 생성기. 상자·화살표·점선 구역만 쓴다. 색은 CSS 변수(currentColor, .acc)라 밝은/어두운 화면 모두 맞는다.
사용: 이 파일 끝의 예처럼 D(w,h,title)로 만들고 box/zone/arrow/path/text/cross를 조합해 save("이름.svg") → content/blog/img/ 에 저장.
글에서는 ![설명](img/이름.svg) 로 넣는다(layouts/_markup/render-image.html이 본문에 직접 심는다).
새 그림을 만들 때는 이 파일의 예제 블록을 지우고 자기 것만 남겨 실행한다. 글 다섯 편에 한 장 정도, 순서·구조가 있을 때만."""
import html
OUT="/home/gnt/projects/03_personal/namest504.github.io/content/blog/img/"
def esc(s): return html.escape(s)
class D:
    def __init__(s,w,h,title): s.w,s.h,s.title=w,h,title; s.e=[]
    def box(s,x,y,w,h,lines,cls="box",tcls=""):
        s.e.append(f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/>')
        n=len(lines); 
        for i,l in enumerate(lines):
            ty=y+h/2+(i-(n-1)/2)*18+5
            s.e.append(f'<text class="{tcls}" x="{x+w/2}" y="{ty}" text-anchor="middle">{esc(l)}</text>')
    def zone(s,x,y,w,h,label):
        s.e.append(f'<rect class="zone" x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/>')
        s.e.append(f'<text class="muted" x="{x+12}" y="{y+18}">{esc(label)}</text>')
    def arrow(s,x1,y1,x2,y2,label="",cls="ln",dy=-8,head=True,tcls="muted"):
        m=' marker-end="url(#ah)"' if head else ""
        s.e.append(f'<path class="{cls}" d="M{x1} {y1} L{x2} {y2}"{m}/>')
        if label: s.e.append(f'<text class="{tcls}" x="{(x1+x2)/2}" y="{(y1+y2)/2+dy}" text-anchor="middle">{esc(label)}</text>')
    def path(s,d,label="",lx=0,ly=0,cls="ln",tcls="muted",head=True):
        m=' marker-end="url(#ah)"' if head else ""
        s.e.append(f'<path class="{cls}" d="{d}"{m}/>')
        if label: s.e.append(f'<text class="{tcls}" x="{lx}" y="{ly}" text-anchor="middle">{esc(label)}</text>')
    def text(s,x,y,t,cls="",anchor="start"): s.e.append(f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}">{esc(t)}</text>')
    def cross(s,x,y,r=7): s.e.append(f'<path class="cross" d="M{x-r} {y-r} L{x+r} {y+r} M{x+r} {y-r} L{x-r} {y+r}"/>')
    def save(s,name):
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {s.w} {s.h}" role="img" aria-labelledby="t"><title id="t">{esc(s.title)}</title><defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="currentColor"/></marker></defs>\n'+"\n".join(s.e)+"\n</svg>\n"
        open(OUT+name,"w").write(svg)

# 1 k8s
d=D(680,300,"집 노트북과 회사 데스크톱이 Tailscale을 통해 직접 연결되는 구조")
d.zone(20,60,250,190,"집 (공유기 두 대 뒤)"); d.zone(410,60,250,190,"회사 (방화벽 · Windows · WSL2 NAT)")
d.box(60,120,170,70,["노트북","control plane"]); d.box(450,120,170,70,["데스크톱의 WSL2","worker (GPU)"])
d.box(265,10,150,40,["조정 서버"])
d.path("M145 120 L145 90 Q145 30 265 30","먼저 등록",60,100,head=False); d.path("M535 120 L535 90 Q535 30 415 30",head=False)
d.arrow(230,155,450,155,cls="ln acc"); d.text(340,146,"직접 통신 (100.x)",cls="acc",anchor="middle")
d.text(340,215,"NAT 통과 · Kubernetes 입장에서는 같은 LAN의 두 노드",cls="muted",anchor="middle")
d.save("k8s-tailscale-cluster.svg")

# 2 executor
d=D(680,280,"client가 닫히는 중에 executor에 넘긴 완료 작업이 shutdownNow로 버려지는 순서")
d.box(20,40,140,60,["send 실패를","알아챈 thread"]); d.box(270,40,140,60,["completion","executor 대기열"]); d.box(520,40,140,60,["사용자의","future"])
d.arrow(160,70,270,70,"① 넘김",dy=-10); d.arrow(410,70,520,70,"실행되면 완료",cls="ln dash",dy=-10)
d.cross(340,150); d.text(340,185,"② client.close() → shutdownNow()",cls="mono",anchor="middle"); d.text(340,205,"대기열에 남은 작업은 실행 없이 버려짐",cls="muted",anchor="middle")
d.arrow(340,100,340,138,cls="ln dash",head=False)
d.text(560,125,"③ 아무도 완료하지 않음",cls="muted",anchor="middle"); d.text(560,143,"get()은 영원히 기다림",cls="muted",anchor="middle")
d.path("M90 100 L90 240 L590 240 L590 100",cls="ln acc",lx=340,ly=232,label="고친 뒤: 닫히는 중이면 그 자리에서 바로 future 완료",tcls="acc")
d.save("executor-shutdownnow-lost-task.svg")

# 3 flaky
d=D(680,260,"네트워크를 거치는 ack가 직접 호출한 되감기보다 늦게 broker에 도착하는 순서")
d.box(20,40,150,50,["consumer"]); d.box(20,160,150,50,["테스트 코드"]); d.box(510,90,150,70,["broker의","cursor"])
d.path("M170 65 L300 65 L410 65 L510 110","① ack (네트워크를 거침)",290,32); d.box(300,50,110,30,["연결 · 큐"],cls="box",tcls="muted")
d.path("M170 185 L510 140","② 되감기 (같은 process에서 바로 호출)",330,205,cls="ln acc",tcls="acc")
d.text(560,190,"도착 순서: ② 다음 ①",cls="mono",anchor="middle"); d.text(560,212,"ack가 되감기를 덮어씀",cls="muted",anchor="middle")
d.save("flaky-ack-rewind-ordering.svg")

# 4 jetbrains
d=D(680,230,"WSL의 Claude Code에서 Windows의 IntelliJ까지 두 단계 중계를 거치는 연결")
d.zone(20,30,300,180,"WSL2"); d.zone(360,30,300,180,"Windows")
d.box(40,70,110,60,["Claude Code"]); d.box(190,70,110,60,["ncat 릴레이","127.0.0.1:64342"],tcls="")
d.box(380,70,110,60,["netsh","portproxy :64343"]); d.box(530,70,110,60,["IntelliJ MCP","127.0.0.1:64342"])
d.arrow(150,100,190,100); d.arrow(300,100,380,100); d.arrow(490,100,530,100); d.text(340,60,"WSL이 본 Windows IP로",cls="muted",anchor="middle")
d.text(245,165,"Host: localhost 그대로",cls="muted",anchor="middle"); d.text(435,165,"0.0.0.0에 열고 루프백으로",cls="muted",anchor="middle")
d.save("jetbrains-mcp-relay-chain.svg")

# 5 nas search
d=D(680,300,"문서 서버의 파일을 색인해 MCP로 검색하는 흐름")
d.box(20,40,120,50,["문서 서버","(읽기 전용)"]); d.box(180,40,110,50,["본문 추출"]); d.box(330,40,110,50,["chunk로","나누기"]); d.box(480,40,180,50,["로컬 임베딩 모델","(밖으로 안 나감)"])
d.arrow(140,65,180,65); d.arrow(290,65,330,65); d.arrow(440,65,480,65)
d.box(480,150,180,50,["PostgreSQL","+ pgvector"]); d.arrow(570,90,570,150,"벡터 저장")
d.box(20,150,120,50,["Claude Code"]); d.box(180,150,110,50,["MCP 서버"]); d.box(330,150,110,50,["질문 벡터","+ 키워드"])
d.arrow(140,175,180,175,"질문"); d.arrow(290,175,330,175); d.arrow(440,175,480,175)
d.path("M330 200 L330 240 L60 240 L60 200","결과와 출처 경로",195,258,cls="ln acc",tcls="acc")
d.save("nas-search-pipeline.svg")

# 6 tailscale bind
d=D(680,250,"0.0.0.0에 bind한 서버와 Tailscale 주소에만 bind한 서버의 차이")
d.zone(20,20,300,210,"0.0.0.0 에 bind"); d.zone(360,20,300,210,"100.x (Tailscale) 에만 bind")
d.box(110,120,120,50,["서비스"]); d.box(450,120,120,50,["서비스"])
d.arrow(40,60,110,130,"인터넷 누구나",dy=-6); d.arrow(300,60,230,130,"내 기기",dy=-6)
d.arrow(380,60,450,130,cls="ln dash"); d.cross(410,90); d.text(372,118,"인터넷",cls="muted")
d.arrow(640,60,570,130,"내 기기 (tailnet)",dy=-6,cls="ln acc",tcls="acc")
d.text(170,205,"로그인 화면이 있어도 노출",cls="muted",anchor="middle"); d.text(510,205,"주소 자체가 안 열림 → 로그인 불필요",cls="muted",anchor="middle")
d.save("tailscale-bind-vs-any.svg")
