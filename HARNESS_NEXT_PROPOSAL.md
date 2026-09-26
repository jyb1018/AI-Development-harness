# Harness 다음 단계 제안

## 권고

이번 변경은 **3.0.x 안정화 후보**입니다. 3.1이나 새 major를 만들 필요는 아직 없습니다. 기존 core·profile·8 Skill 구조를 유지하고, 재현한 실패만 고치는 것이 적절합니다. VERSION은 3.0.0으로 유지했으며 release/tag/merge는 수행하지 않습니다.

가장 먼저 필요한 것은 Skill 수 증가가 아니라 **실제 사용 trace와 통제된 행동 평가**입니다. 이번 감사의 결정적 테스트는 코드 경계를 증명하며 모델의 순성능을 증명하지 않습니다.

## 구현한 범위

- source Skill/필수 tooling support/catalog 사전 검사입니다.
- required metadata 기본 검사·dangling link·alias visit budget입니다.
- 잘못된 JSON object 모양의 명시적 진단입니다.
- full JSON 호환성을 유지하는 opt-in `--summary`입니다.
- 설치 문서의 Skill 수와 model-upgrade 참조 위치 수정입니다.
- 회귀와 재현 가능한 fixture runner, 감사 결과입니다.

새 역할·MCP·Skill·dependency·global config·자동 설치는 추가하지 않았습니다. 감사 문서와 실험 기록은 사용자 프로젝트로 설치되지 않습니다.

## 후속 우선순위

| 우선순위 | 제안 | 채택 기준 / 비용 |
|---|---|---|
| 1 | 3 arm 행동 pilot: host 기본 / core / core+관련 Skill | 동일 고정 task·repo·permissions·budget, fresh context와 실행 가능한 acceptance가 필요합니다. self-report만으로 채점하지 않습니다. |
| 2 | uh-tooling 문서 부분 로딩 | 단일 capability 작업에서 전체 TOOLING 읽기가 실제 trace에 반복되는지 먼저 확인합니다. 효과가 있으면 root router를 짧게 바꿉니다. |
| 3 | warning 영향 범위 구분 | 무관한 invalid Skill이 host-confirmed provider까지 막는 빈도가 높을 때만 설계합니다. incomplete scan/동명 unknown과 단순 unrelated 오류를 혼동하지 않아야 합니다. |
| 4 | optional Skill 통합 | karpathy/ponytail을 뺀 조건이 acceptance를 유지하며 context/time을 줄이는지 확인합니다. 지금 삭제하지 않습니다. |
| 5 | 실제 host-aware diagnostics adapter | disabled/plugin 목록을 공식 read API로 얻을 수 있고 운영 필요가 있을 때만 추가합니다. filesystem으로 active 목록을 추정하지 않습니다. |
| 6 | 폭·깊이·전체 bytes의 엄격한 scan bound | 운영상 매우 큰 catalog가 실제 필요할 때 검토합니다. 단순 1,000개 scan은 이미 짧게 끝났습니다. |

## Core의 최소 가치와 modern model 판단

[2026-09-11 공식 Astra 지침](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)은 Skill description과 과도한 작업 절차를 재검토하도록 권합니다. 이를 “강한 모델에는 모든 검증이 불필요하다”로 확장하지 않습니다. 아래 판단은 source 기반 설계 검토이며 모델별 실험이 아닙니다.

| 현재 core 규칙 묶음 | 판단 | 이유·확인할 회귀 |
|---|---|---|
| 요청 결과·불변식·기존 작업 보존 | 유지 / universal | 모델 능력과 무관한 실제 작업 경계입니다. |
| host authority·untrusted data | 유지 / universal | 파일 지침이 권한을 만들지 못하게 합니다. |
| 관련 source/test 확인 | 유지하되 관련 범위만 | 전체 repository map 의무로 해석하지 않아야 합니다. |
| 짧은 완료 조건·plan 선택형 | 유지 / universal | planning theater를 억제합니다. |
| 가역적 가정 자율 결정·material 질문 | 유지 / universal | 불필요한 중단과 권한 확대를 함께 방지합니다. |
| 기존 코드/표준 기능 우선·작은 coherent diff | 압축 가능 후보 | 최신 모델의 일반 능력과 중복할 수 있습니다. 제거 효과는 미측정입니다. |
| incremental 구현/검증·선택 위임 | 유지 / host-aware | 고정 agent chain을 만들지 않는 경계가 중요합니다. |
| parent outcome·handoff 조건부 | 유지 / universal | 긴 task의 중간 commit을 완료로 오인하지 않게 합니다. |
| 새 증거 없는 retry 중단 | 유지 / universal | flaky 무시·동일 실패 반복을 막습니다. |
| test weakening 금지·실제 boundary 검증 | 유지 / universal | assertion 자체를 왜곡하는 실패는 강한 모델에서도 비용이 큽니다. |
| vertical path·재시도/동시성은 필요한 경우만 | 유지하되 실제 위험에 적용 | 단순 수정에 E2E를 강제하면 과잉검증이 됩니다. |
| 최초 actionable failure·secret-free diagnosis | 유지 / universal | 반복 조사와 민감 정보 출력을 줄입니다. |
| auth/privacy/accessibility/atomicity | 유지 / universal | 일반 최소주의로 삭제하면 안 되는 보호 조건입니다. |
| 독립 리뷰·외부 효과·실제 target 확인 | 유지 / risk-specific | 모든 작업의 필수 검토자 chain으로 확장하지 않습니다. |
| 변경/실행 검사/미검증/완료 상태 보고 | 유지 / universal | verification theater와 premature completion을 구분합니다. |
| 가장 작은 가용 도구·readiness 구분 | 유지 / host-aware | 설치 상태를 성공으로 오인하지 않습니다. |
| exact path·중복 회피·host/context 변화 재확인 | 유지 / host-aware | global/local precedence를 임의로 만들지 않습니다. |
| graph/docs freshness·정직한 fallback | 유지 / task-specific | 인덱스/도구 결과는 현재 source와 대조해야 합니다. |
| profile 1개와 관련 Skill만 로드 | 유지 / context control | Skill 전체를 반복 주입하지 않게 합니다. |

## Model profile 규칙 분류

현재 이름은 model-specific이지만 규칙 상당수는 universal/host-specific입니다. obsolete로 확정한 규칙은 없습니다.

| Profile의 실제 규칙 | 분류 | 판단 |
|---|---|---|
| generic: 실제 model/host가 필요한 때 확인 | universal / host-specific | 유지합니다. |
| generic: 실제 도구·권한·task-sized 검증 | universal | core와 중복하지만 451 B의 작은 메모입니다. |
| generic: 다른 profile을 로드하지 않음 | universal | context 혼동 방지입니다. |
| sol: 과거 모델별 역할 배정 강제 금지 | universal / historical | 과거 setup 호환성 메모이며 Sol defect 증명은 아닙니다. |
| sol: effective effort 유지 후 비교 | reasoning-level-specific 원칙 | 특정 effort 우열을 강제하지 않아 적절합니다. |
| sol: 독립 작업만 병렬·host orchestration 중복 금지 | universal / host-specific | 모델 전용 규칙이라고 보기 어렵습니다. |
| sol: parent outcome·source/runtime 구분 | universal | behavior pilot 후 core와 압축 가능성 검토입니다. |
| astra: 도입 시 관련 instruction 충돌 점검 | Astra-motivated / universal implementation | 매 편집 전체 감사로 바뀌지 않는 조건이 중요합니다. |
| astra: 일상 결정 진행·material 질문만 | Astra-motivated / universal | 실제 질문 감소 효과는 미측정입니다. |
| astra: safe 독립 작업 지속 | Astra-motivated / universal | premature stop 보정 가설이며 성능 인증은 아닙니다. |
| astra: tool 결과·API/UI scope 구별 | host-specific / universal | 모델 능력보다 도구 경계의 문제입니다. |
| astra: denied approval 우회 금지 | universal | profile에서 중복되더라도 안전기준을 낮추지 않습니다. |
| 세 profile: 모델 선택·권한·effort 강제 없음 | universal | 반드시 유지합니다. |

medium/high/x-high가 올라갈수록 설명을 더 많이 주입할 근거는 없습니다. 먼저 같은 core+관련 Skill로 effort만 비교하고, 그 다음 얇은 core arm을 추가해야 변수를 분리할 수 있습니다. high를 쓰지 말아야 한다거나 x-high에는 Skill을 모두 빼야 한다는 결론은 이번 증거로 낼 수 없습니다.

## 행동 pilot 설계 — SIMULATED / NOT RUN

최소 pilot은 routine bug, integration boundary, ML/data 보호 사례의 3 task입니다. 각 task에 3 arm×3 fresh runs로 27 runs를 만들 수 있습니다. 이는 제안일 뿐 호출·비용을 실행하거나 승인받았다는 뜻이 아닙니다. 모델/effort 비교를 동시에 전부 곱하지 말고, 첫 pilot이 유용할 때 별도 실험으로 확장합니다.

- 동일 workspace snapshot·fixture·tool/permission·budget·completion criteria를 사용합니다.
- acceptance는 실행 가능한 assertions와 artifacts로 판정합니다. 답변의 “검증했습니다”라는 문구를 점수로 삼지 않습니다.
- correctness/safety를 먼저, 불필요한 질문·변경·검사·tool calls를 다음, 시간/실제 usage를 마지막에 비교합니다.
- host patch/model snapshot/effort와 관측되지 않는 설정을 분리합니다.
- Skill 선택/전체 loading/반복 discovery를 trace로 기록하고 false positive와 false negative를 구분합니다.
- 작은 표본에서는 수치의 원인을 단정하지 않고 원시 counts와 실패 사례를 제시합니다.

## Harness Doctor의 방향

이미 `.universal-harness/tooling.py doctor`가 있으므로 두 번째 doctor를 만들 필요는 없습니다. 현재 역할은 파일/PATH 기반 중복·기본 metadata·누락 단서입니다. 이번 summary와 오류 수정이 바로 작은 유용성 개선입니다.

자동 설치/로그인/삭제/host config 변경, dependency solver, background watcher는 추가하지 않습니다. 향후 scope/version/dependency 진단이 필요하면 먼저 읽기 전용 관측 데이터와 실제 사용자 실패 사례를 확보해야 합니다.

## Upgrade와 rollback

별도 branch의 수정이 검토된 후 기존 installer `--upgrade --dry-run`으로 사용자 수정 충돌을 확인하고 `--upgrade`합니다. 수동 편집한 파일은 보존되며 병합이 필요합니다. source Skill 참조 수정과 tooling 지원 파일도 기존 hash 소유권 규칙을 따릅니다.

현재 bootstrap regressions는 profile 3개와 existing fixture를 다시 확인합니다. 큰 구조 변경은 이 브랜치에 포함하지 않습니다. 회귀 시 이전 승인 revision의 관리 파일만 검토해 되돌리며 사용자 작업/전역 Skill을 삭제하지 않습니다. release/merge는 별도 결정입니다.
