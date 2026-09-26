# Sol / Astra 적용 판단

## 같은 정책, 별개의 실행 환경

Universal Harness는 프롬프트/스킬 층입니다. 모델, Codex 런타임, 플러그인 로더,
권한 설정, shell·browser·subagent 도구, 프로젝트 자체 테스트는 서로 다른 층입니다.
“하네스를 제거”해도 Codex 자체의 agent runtime이 사라지는 것은 아닙니다.

| 항목 | GPT-5.6 Sol | GPT-6 Astra |
|---|---|---|
| 공통 core | AGENTS.template.md | 동일 |
| 프로필 | profiles/sol.md | profiles/astra.md |
| 기본 실행 | 한 작업 책임자; 분리 가능한 경우 선택 위임 | 동일 |
| 주요 점검 | source-only 완료, 의미 없는 검증 반복, effort 비용 | 지침 충돌, 과도한 질문·중단, 실제 도구 결과 확인 |
| 모델/effort 설정 | 기존 유효 설정에서 시작해 평가 | 기존 유효 설정을 우선 비교; 지원 값은 호스트에서 확인 |
| 성능 인증 | 미실행 | 미실행 |

공식 [5.6 발표](https://openai.com/index/gpt-5-6/)는 병렬 작업 기능을 설명합니다.
따라서 “강한 모델에는 subagent가 필요 없다”도 보편 규칙이 아닙니다.
독립된 탐색·검증을 병렬화할 수 있지만 서로 의존하는 수정은 한 흐름으로 조정합니다.

공식 [모델 가이드](https://developers.openai.com/api/docs/guides/latest-model)는 Astra가
파일/스킬 지시에 민감할 수 있고 중요한 추가 정보가 필요하면 질문할 수 있다고 설명합니다.
여기서 도출한 설계는 **충돌 제거와 일상적 가정의 범위 명시**이지, 무조건 질문 금지나 안전 승인 우회가 아닙니다.

## 설정은 자동으로 건드리지 않음

설치기의 `--profile`은 호환성 메모만 고릅니다. `config.toml`, model ID, effort,
API 파라미터, max/ultra 또는 tool availability를 변경하지 않습니다.
API와 Codex UI의 설정 이름이 같다고 가정하지 않습니다.
호스트가 새 도구를 제공해도 공개/유료/파괴적 동작의 권한이 자동 확대되지는 않습니다.

## Host/runtime 버전도 평가 변수입니다

같은 모델·하네스·프로젝트라도 Codex 같은 호스트의 **patch version과 기본 요청 설정**이
달라지면 결과가 달라질 수 있습니다. 따라서 모델 비교 기록에는 `evals/run-record.template.json`을
사용해 정확한 host version, platform, reasoning effort와 request-affecting effective config를
별도 필드로 남깁니다. `model_reasoning_summary`처럼 호스트가 기본값을 바꿀 수 있는 설정은
모델 성격이나 하네스 회귀로 합쳐서 기록하지 않습니다.

호스트 업데이트 직후 문제가 생겼다면 우선 같은 모델·하네스·project revision에서 host/config만
분리해 비교합니다. 공식 릴리스 노트나 source diff는 가설의 근거가 될 수 있지만, 실제 provider
재현이 불가능하면 그 경계는 `unknown`으로 남깁니다. host가 native loop protection이나
user verification을 제공할 때도 하네스가 이를 우회하거나 중복 구현하지 않습니다.

일부 host 상태는 thread 시작 때 고정되지 않습니다. host/cloud skill provider·인증 범위·resource
세대, 진행 중 authorization, compaction/resume처럼 **실행 중 바뀔 수 있는 상태**가 관련된 회귀는
초기 설정만 기록하지 말고 관측 가능한 변경 이벤트와 적용 시점을 함께 남깁니다. 해당 capability가
실제로 없는 환경은 `not_applicable`, 존재 여부나 적용 상태를 확인할 수 없는 계층은 `unknown`으로
구분합니다. 이런 host lifecycle 차이를 Sol/Astra 성격 차이로 곧바로 옮기지 않습니다.

## 이전 분석의 정정

연동 실패 뒤에 모델 업그레이드가 있었다는 관찰만으로 업그레이드가 원인이라고 결론 내릴 수 없습니다.
지침 누적, 자동 배포, 실제 테스트 경계 누락, 환경 차이도 원인이 될 수 있습니다.
2.0의 가벼운 설계는 검증할 가설입니다. 모델별 개선 주장은 고정 과제·revision·권한·환경을 통제한 결과가 있어야 합니다.
