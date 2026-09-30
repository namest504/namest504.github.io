---
title: "닫히는 중인 클라이언트로 메시지를 보내면"
date: 2026-09-23
project: "Apache Pulsar"
source: "https://github.com/apache/pulsar/pull/26686"
build:
  render: never
  list: always
---

메시지 전송이 실패하면 "실패했다"는 결과를 알려 주는 일을 따로 맡은 일꾼에게 넘깁니다. 그런데 클라이언트가 닫히는 중에는 이 일꾼도 곧 정리됩니다. 넘겨 둔 일이 처리되기 전에 일꾼이 사라지면, 보낸 쪽은 결과를 끝없이 기다리게 됩니다.

클라이언트가 닫히는 중이라면 일꾼에게 넘기지 않고 그 자리에서 바로 결과를 알려 주도록 고쳤습니다.
