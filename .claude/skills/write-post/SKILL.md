---
name: write-post
description: 이 블로그(namest504.github.io, Hugo)의 글을 쓰고 검사하고 미리 볼 때. "블로그 글 써줘", "초안 만들어", "글 검사해", "미리보기 띄워", "글 화면 찍어" 요청에 사용. 글쓰기 규칙(말투·구성·코드 블록 문법·비식별·작성일)과 post.py 도구 사용법.
---

# 블로그 글 쓰기

원고는 `content/`(별도 비공개 저장소, 이 저장소에서는 무시됨)에 있고, 레이아웃은 이 저장소에 있다.
도구는 `.claude/skills/write-post/post.py` 하나. 경로는 저장소 루트 기준. Hugo는 `~/.local/hugo/hugo`(다른 위치면 `HUGO=` 환경 변수).

## 순서

```bash
git -C content pull --ff-only          # 관리 화면에서 생긴 커밋을 먼저 받는다
python3 .claude/skills/write-post/post.py new <slug> --title "제목" --category Gradle --tags "A,B" --date 2026-07-25
# content/blog/<slug>.md 를 아래 규칙대로 채운다
python3 .claude/skills/write-post/post.py check <slug>     # 규칙·식별어·링크 검사 + 초안 포함 빌드
python3 .claude/skills/write-post/post.py preview          # http://localhost:1313/ (초안·미래 날짜 포함)
python3 .claude/skills/write-post/post.py shot <slug> --height 5200        # PNG 경로 출력 → Read로 본다
python3 .claude/skills/write-post/post.py shot <slug> --dark --height 1400
git -C content add -A && git -C content commit -m "초안: <slug>"           # push는 사용자에게 맡긴다
```

`check`는 문제가 있으면 종료 코드 1. `preview`는 뒤에서 돌고 `kill $(lsof -ti:1313)`로 끈다.
공개는 lim-host 관리 화면(Tailscale)에서 사용자가 누른다. 초안(`draft: true`)은 사이트에 나오지 않는다.

## 글 규칙 (사용자가 여러 번 지적해 확정된 것)

본보기: `content/blog/terminal-taskbar-progress.md`, `content/blog/executor-shutdownnow-lost-future.md`. 새 글 전에 읽는다.

- 구성: 겪은 상황 2~4문장 → "이 글에서는 …를 적습니다" → `##` 4~6개(동작 원리 → 원인 → 고친 방법과 이유 → 확인한 것 → 남은 것) → `## 마치며`(배운 점 2~3문장). 부제·요약 문장·"코드로 보기" 링크 목록·상투적 마무리 금지. 강조 인용문 `>`은 최대 1개.
- 말투: 1인칭, 짧은 문장, 겪은 일만. 제품·기술 이름은 영어 그대로(Gradle, WSL, JWT, thread). 억지 번역 금지("빌드 도구"). 일반 개념어는 쉬운 한국어("가끔 실패하는 테스트"는 flaky test보다 이것을 택함). 애매하면 바꾸기 전에 묻는다.
- `description`: 무엇에 관한 글인지 사실만 짧게. "~풀어 봅니다/~이야기입니다" 금지. 글 화면에는 안 나오고 목록·검색용.
- `date`: 작업(기여 반영)일 + 7~14일. 미래면 그날 전엔 사이트에 안 나온다(자동 배포가 매일 00:10에 돈다).
- `categories`: 기술 이름 하나. `tags`: 2~4개. 실명·회사명은 사이트 어디에도 안 쓴다(글쓴이 표시 없음).
- 링크: issue·PR·문서는 언급하는 그 자리에 하이퍼링크. gh나 curl로 실제 있는 주소만. public 저장소 코드 링크는 커밋 해시 기준.
- 회사 소재: `content/.private/forbidden-terms.txt`의 표현을 전부 뺀다("운영 중인 웹 서비스", "동료"). 업무 코드·캡처·경로 대신 재현 예제를 새로 쓴다. `check`가 이 목록으로 검사한다.
- 사실만: 참고 문서·코드에 있는 것만. 불확실하면 문장 뒤에 `<!-- 확인 필요: 이유 -->`(검토 후 지운다).

## 코드 블록 문법 (`layouts/_markup/render-codeblock.html`)

- 설명은 코드 안 주석(`//` 한 줄, 길면 `/* */`). 줄 옆 설명 `//>`은 거부됨. 줄은 90자 안에서 끊는다.
- 실제 저장소 코드: ` ```java {file="X.java" link="https://github.com/o/r/blob/<해시>/p#L10-L20" label="10~20행"} ` → 파일 이름 머리줄.
- 바뀐 부분: 속성에 `diff=true`, 각 줄 첫 글자 `+`/`-`/빈칸, 둘째 글자 빈칸.
- 본문 폭에 맞춰 접히므로 스크롤은 없다.

## 함정

- `date`가 미래인 글은 `hugo -D`로도 안 나온다. `check`·`preview`는 `-F`를 붙여 보이게 한다.
- 어두운 화면에서 코드 구두점이 안 보이면 `assets/css/syntax.css` 끝의 dark `.p/.o/.w` 규칙이 지워진 것.
- 관리 화면(lim-host)이 `content`에 커밋을 만든다. 작업 전 `pull` 없이 커밋하면 push가 거부된다.
- `content/.private/`는 Hugo가 빌드에서 뺀다(점으로 시작). 식별어 목록은 여기에만 둔다(공개 저장소 금지).
