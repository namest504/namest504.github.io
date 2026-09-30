---
title: "대문자와 소문자 때문에 통과하지 못한 인증 토큰"
date: 2025-10-29
project: "Spring Security"
source: "https://github.com/spring-projects/spring-security/pull/18101"
build:
  render: never
  list: always
---

인증 토큰의 머리말에는 이 토큰이 어떤 종류인지 적는 칸이 있습니다. 이 값을 검사하는 코드가 대문자와 소문자를 다른 글자로 취급해서, 뜻이 같은 값인데도 표기에 따라 검사 결과가 달라졌습니다. 예전에 쓰던 검사 방식은 둘을 구분하지 않았기 때문에, 버전을 올리면서 동작이 달라진 셈이었습니다.

글자 크기를 가리지 않고 비교하도록 고쳤습니다.
