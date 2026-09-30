---
title: "빌드 진행률이 작업 표시줄에 안 보이던 이유"
date: 2026-09-29
project: "Gradle"
source: "https://github.com/gradle/gradle/pull/39260"
post: "/blog/terminal-taskbar-progress"
build:
  render: never
  list: always
---

Gradle은 빌드가 얼마나 진행됐는지를 터미널에 신호로 보내는 기능을 이미 갖고 있었습니다. 다만 신호를 받아 줄 수 있는 터미널 목록에 Windows Terminal이 빠져 있어서, 그곳에서는 아무것도 보내지 않았습니다.

Windows Terminal이 창마다 남겨 두는 환경 변수를 보고 알아보도록 고쳤습니다. 이제 빌드를 걸어 두고 다른 일을 하다가도 작업 표시줄 아이콘만 보면 진행 상황을 알 수 있습니다.
