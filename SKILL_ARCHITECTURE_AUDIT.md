# Skill Architecture Audit

2026-09-26 · 기준 `218e2a4` · Skill 전체 8개를 직접 읽었습니다. 분류는 **설계상 기대 가치**이며 모델 efficacy 측정값이 아닙니다. 파일 크기는 기준 revision의 정확한 byte 수입니다.

## 전수 inventory

모두 배포 원본 `skills/<name>/SKILL.md`에서 소비자의 `.agents/skills/<name>/SKILL.md`로 설치되는 project-local adaptation입니다. global 설치를 수행하지 않습니다. 기본 도구는 host의 read/search/edit/test이며 Skill 자체가 새 권한을 제공하지 않습니다.

| 이름 / 분류 | 목적·trigger | 입력 → 예상 출력 | 의존성·도구 / 실패 동작 | 중복·core 관계 / 비용 |
|---|---|---|---|---|
| `uh-debug` / Essential | 원인 불명의 반복 test/runtime/CI 실패를 좁힙니다. | 실패 명령·환경·원본 오류·관련 소스 → 반증 가능한 가설, 구분 실험, 수정·회귀 증거 | 파일/로그/실행 수단입니다. 반복 동일 실패는 새 가설 또는 구체적 blocker로 전환합니다. | core 증거 규칙, tdd/integration과 일부 겹칩니다. 1,492 B, 대략 373 tokens입니다. |
| `uh-integration` / Situational | 서비스·DB·proxy·image·device 경계를 실제로 연결합니다. | 승인된 환경·입력·provider/consumer revision → 관찰 가능한 vertical acceptance | 실제 adapter/runtime가 필요합니다. 없으면 safe local 검증과 미확인 경계를 구분합니다. | debug·tdd와 조합 가능하나 fake를 E2E로 오인하지 않는 고유 가치가 있습니다. 1,618 B / ~405 tokens입니다. |
| `uh-karpathy` / Optional | 중요한 가정·범위 모호성, 요청 밖 diff를 줄입니다. | 요청·영향 경로·불변식 → 필요한 결정과 좁은 성공 조건 | 특별한 binary가 없습니다. 사소한 가정은 기존 관례로 결정합니다. | core의 가정·작은 변경 규칙과 높은 의미 중복입니다. 1,287 B / ~322 tokens입니다. |
| `uh-ponytail` / Optional | 새 wrapper/framework/dependency의 필요성을 평가합니다. | 실제 제안·현재 코드 → 더 작은 안전한 대안 또는 채택 근거 | 소스/기존 dependency입니다. 알 수 없는 코드를 미관상 삭제하지 않습니다. | core 최소화와 일부 중복하지만 구체적 대안 비교는 유용합니다. 1,111 B / ~278 tokens입니다. |
| `uh-tdd` / Situational | 안정된 deterministic 계약·재현 regression에 red-green을 적용합니다. | 고정된 예상 행동·실행 가능한 reproducer → 실제 red/green 및 필요한 refactor 검증 | 테스트 실행 환경입니다. ML 품질·시각 UX에는 적절한 평가를 선택하고 red를 꾸미지 않습니다. | debug/integration과 경계가 다릅니다. 모든 작업의 선행 조건이 아닙니다. 1,331 B / ~333 tokens입니다. |
| `uh-review` / Essential | 요청된 review 또는 실질적 위험을 증거로 검토합니다. | 요구·불변식·고정 diff·실행 증거 → 위치/재현/영향이 있는 findings | 고위험 출시는 실제 독립 reviewer가 필요할 수 있습니다. 부재 시 self-review라고 표시합니다. | core와 겹치지만 리뷰 증거·독립성 구별이 중요합니다. 1,442 B / ~361 tokens입니다. |
| `uh-tooling` / Situational | 구체적인 도구 필요·runtime 부재·global/local 충돌을 다룹니다. | 현재 host catalog·project·필요 capability → unverified 후보/검사 조건/fallback | 설치된 tooling.py/json/TOOLING.md, 선택 provider입니다. 부재·모호성 시 native fallback입니다. | debug/review/model-upgrade와 호출 상황이 겹칩니다. 2,846 B / ~712 tokens, 별도 도구 문서 추가 비용이 있습니다. |
| `uh-model-upgrade` / Situational | model/host/skill-loading 변화 영향을 분리 평가합니다. | 고정 task/revision/config·실제 run → 비교/불확실성/유지·변경·rollback 제안 | 실제 평가 protocol은 원본 `evals/README.md`입니다. target에 설치되지 않는 참조를 명확히 수정했습니다. | core의 일반 검증과 달리 controlled comparison 전용입니다. 1,968 B / ~492 tokens입니다. |

Essential은 “매번 로드”라는 뜻이 아닙니다. 거의 모든 저장소에서 재사용 가능한 가치라는 분류입니다. 어느 Skill도 Harmful로 확정하지 않았습니다. karpathy/ponytail의 부분 중복은 Redundant 후보이지만 통째 삭제할 행동 근거가 없습니다. **8개 모두 실제 순성능 효과는 Unknown**입니다.

## 외부 provider inventory와 설치 범위

다음은 `integrations/tooling.json`이 아는 후보이며 실제 설치된 제3자 Skill 목록이 아닙니다. 사용자의 Mac global 상태를 이 Work 환경의 목록으로 대체하지 않았습니다.

| Provider | 종류 / 관련 Skill 이름 | 필요한 런타임 | 권장 책임 범위·현재 판단 |
|---|---|---|---|
| find-skills | skill / `find-skills` | npx | global 선택 설치 후보입니다. 매 요청의 필수 discovery가 아닙니다. |
| skill-creator | builtin / `skill-creator` | 현재 host 노출 | 호스트 제공본을 우선합니다. 같은 이름의 프로젝트 복제를 권하지 않습니다. |
| Context7 | CLI / `find-docs`, `context7-cli` | ctx7 또는 host가 제공하는 실제 인터페이스 | 버전별 공개 문서 사용법은 global, 프로젝트 버전 선택은 local입니다. |
| Serena | MCP / 없음 | active MCP; PATH의 serena만으로 부족합니다. | 도구 연결은 host, 프로젝트/language backend 선택은 local입니다. |
| Graphify | CLI / `graphify` | graphify | 실행기·일반 사용법은 global 후보, index/revision/범위는 local입니다. |
| Playwright | CLI / `playwright-cli` | playwright-cli와 browser | 일반 사용법은 global, origin/테스트 계정/acceptance는 local입니다. |
| Chrome DevTools | MCP / 없음 | 현재 host MCP | browser 관측 전용이며 host의 session 권한을 따릅니다. |
| GitHub | plugin / 없음 | 현재 host plugin | 전역 도구 후보이며 정확한 repo/ref/허용 효과는 작업별입니다. |
| GitHub CLI | CLI / 없음 | gh | PATH는 인증을 보장하지 않습니다. |
| CodeRabbit | CLI / `code-review` | coderabbit | 범용 review skill은 global 후보입니다. 비공개 diff 전송·비용·독립성은 별도 확인입니다. |
| Codex Security | plugin / 없음 | 현재 host plugin | 선택형 보안 capability이며 모든 변경의 mandatory gate가 아닙니다. |
| Sentry | MCP / 없음 | 현재 host MCP | 범용 조회 사용법은 global 후보, org/project/environment와 데이터 취급은 local입니다. |

외부 upstream 스킬 본문을 전부 vendoring하거나 품질 인증하지 않았습니다. catalog에 dependency 버전·설치 recipe·인증 정보는 없습니다. `find-skills` upstream은 공식 소스를 읽어 구별했습니다. keyword 기반 ecosystem 검색·설치 지원이며, 이미 설치된 모든 Skill의 호출 순서를 결정하는 host loader가 아닙니다. 현재 upstream의 폭넓은 trigger와 사용자에게 재질문하는 fallback 예시는 기본 task 흐름을 늘릴 가능성이 있으나, 사용자의 설치 revision과 행동은 UNKNOWN입니다. [공식 source](https://github.com/vercel-labs/skills/blob/main/skills/find-skills/SKILL.md)를 기준으로 한 제한된 분석입니다.

## Global/local 중복과 precedence

실행된 회귀는 동일 본문, 다른 본문, renamed folder, parent repo, symlink alias를 다룹니다. identity는 directory 이름이 아니라 frontmatter name입니다. 본문 hash는 supporting files의 동일성을 뜻하지 않습니다.

`inventory()`는 같은 name의 provider를 ambiguous로 표시하고 `route()`에서 제외합니다. installer는 설치할 uh-*의 다른 경로 노출을 발견하면 쓰기 전에 중단합니다. 오래된 global과 새 local 중 하나를 자동으로 고르지 않습니다. 동일 본문도 두 노출 경로로 취급합니다.

[공식 Skill 문서](https://learn.chatgpt.com/docs/build-skills)에 따르면 동명 Skill은 병합되지 않으며 selector에 함께 나타날 수 있습니다. 이를 local 우선이라는 보장으로 바꿀 수 없습니다. 실제 선택·중복 context 로딩은 host/version에 따라 확인해야 하며 여기서는 NOT RUN입니다.

| 충돌 축 | 패키지의 해결 방식 / 한계 |
|---|---|
| Skill vs host/system/developer | core가 상위 authority를 명시합니다. 파일은 새 권한을 만들지 못합니다. |
| Skill vs user | 명시된 사용자 범위 내에서 적용해야 합니다. 이 패키지는 별도 실행 가능한 instruction arbiter를 갖고 있지 않습니다. |
| Skill vs repository | 프로젝트 불변식·domain/검증/권한을 보존합니다. 기존 AGENTS는 자동 교체하지 않습니다. |
| Skill vs core | 선택형 심화 지침입니다. 일반 Skill이 core의 안전·scope를 무효화할 수 없습니다. |
| Skill vs profile | profile은 두 번째 정책이 아니라 compatibility note입니다. 모델 설정을 강제하지 않습니다. |
| Skill vs Skill | 적용 경계를 나눠 사용해야 합니다. dependency DAG나 topological invocation 순서는 구현하지 않았습니다. |
| global vs local | exact path와 host 설정을 확인합니다. package 차원의 자동 precedence는 없습니다. |

## Discovery와 loading 경로

1. 호스트는 설치된 Skill metadata를 발견합니다. Harness의 8개 이름/trigger는 core에도 간단히 안내됩니다.
2. agent는 작업에 맞는 Skill 본문을 선택적으로 읽습니다. 패키지 자체가 자연어 classifier를 실행하지 않습니다.
3. tooling이 필요한 경우 capability ID로 catalog를 조회합니다. route의 고정 provider 순서가 “task 적합도 점수”는 아닙니다.
4. provider 부재 시 기존 도구·소스/공식 문서·로컬 검사로 진행하며 미검증 acceptance를 표시합니다.
5. 외부 설치는 user/host authority가 있어야 합니다. find-skills도 기본 선행 단계가 아닙니다.

이 구조에서 실제 자연어 선택 정확도는 model/host metadata exposure에 달려 있습니다. 정확·모호·복합·유사·없는 Skill 요청의 [trigger 사례](evals/audit-2026-09-26/trigger-cases.json)를 만들었지만 **SIMULATED 기대값이며 precision/recall 점수는 없습니다.**

## Trigger 품질 — SIMULATED 분석

각 Skill당 positive 2개, negative 1개를 준비했습니다. 직접 이름 호출과 자연어 변형을 포함합니다. 추가 5개는 복합·유사·Skill 없음·권한 충돌입니다.

| Skill | 주요 false positive 후보 | 주요 false negative 후보 | 판단 |
|---|---|---|---|
| debug | 원인이 명확한 syntax typo에도 긴 조사 | 증상이 “가끔 멈춥니다”처럼 failure라는 단어가 없음 | 본문은 명백한 오류에 ceremony를 금지합니다. metadata 언어별 실험이 필요합니다. |
| integration | 단순 UI/순수함수까지 E2E 강제 | desktop capture→CV→overlay 경계가 웹 용어로 표현되지 않음 | description의 device/other boundaries가 보완하지만 실제 선택은 미측정입니다. |
| karpathy | 일상적인 사소한 불확실성에 질문 | “이 부분 알아서 정리”라는 넓은 scope | consequential이라는 경계가 있으나 모델 해석에 의존합니다. |
| ponytail | 이미 승인된 dependency의 단순 유지보수 | “재사용 가능하게 해 주세요”가 추상화 제안으로 연결되지 않음 | optional 비교로 유지하는 편이 타당합니다. |
| tdd | stochastic ML metric/색상 변경 | 안정된 regression인데 TDD 언급 없음 | deterministic/contract 조건이 적절합니다. |
| review | API라는 단어만으로 독립 review 강제 | 작은 권한 변경의 위험을 놓침 | 본문은 file count/명칭보다 실제 영향으로 판단합니다. |
| tooling | 거의 모든 개발 작업에 등장하는 docs/repo/review | 구체적 PATH 증상을 capability 실패로 연결하지 못함 | 301자 metadata는 8개 중 가장 깁니다. 부정 조건을 앞쪽에 배치하는 후속 실험이 유용합니다. |
| model-upgrade | 모델 단어가 있는 제품 기능 개발 | host patch만 바뀐 regression | host/skill-loading을 포함한 점은 적절합니다. |

## Context 비용

`characters / 4`는 거친 비교용 추정치이며 실제 Astra/Sol tokenizer·청구량이 아닙니다. 특히 한국어 문서는 이 추정이 부정확할 수 있습니다.

| 항목 | 기준 비용 | 해석 |
|---|---:|---|
| core | 5,799 B / ~1,450 tokens | High value / low-to-moderate cost입니다. 핵심 보호 경계를 유지합니다. |
| astra / sol / generic profile | 791 / 680 / 451 B | 작은 비용이며 대부분 universal 안전장치입니다. |
| 8개 Skill name+description | 1,216 chars / ~304 tokens | host wrapper와 path는 제외했습니다. |
| 8개 Skill 파일 전부 | 13,095 B / ~3,274 tokens | 모두 로드할 필요가 없습니다. |
| tooling 본문 | 2,846 B / ~712 tokens | situational하며 catalog/doc를 추가로 읽으면 더 커집니다. |
| 기준 TOOLING.md | 9,236 B | 설치되어 있어도 상시 로딩 비용은 아닙니다. 단일 capability에 전부 읽을 필요는 없습니다. |
| 1,000 synthetic Skill의 full route | 310,330 B | 진단 정보가 큰 context 비용이 될 수 있습니다. |
| 같은 route + summary | 1,413 B | 동일 route, 99.54% 출력 감소입니다. |

이번 참조 수정으로 `uh-model-upgrade` 본문은 조금 늘었지만, source/target 혼동을 해소합니다. 다른 Skill/core/profile 크기는 유지했습니다. 실제 prompt caching·중복 로딩·token billing은 UNKNOWN입니다.

공식 문서는 초기 Skill 목록에 budget이 있고 규모에 따라 description 축약·일부 누락이 가능하다고 설명합니다. 따라서 filesystem에서 1,000개를 찾았다고 agent가 모두 보거나 정확히 선택한다고 결론 내릴 수 없습니다. 이는 [공식 loading 설명](https://learn.chatgpt.com/docs/build-skills)과 우리의 scan 측정을 결합한 추론입니다.

## Failure recovery

| 실패 | 현재 처리 / 증거 |
|---|---|
| 배포 source 파일 없음 | 기존 preflight가 무변경 실패합니다. ZIP/전체 clone을 안내합니다. |
| source Skill 손상/name 불일치 | 이번 패치가 무변경 실패합니다. |
| global metadata 기본 필드 이상 | warning, strict 1, route fallback입니다. 전체 YAML 검사는 아닙니다. |
| required CLI/PATH 없음 | not_observed/instructions_only/runtime_unverified 상태로 구분합니다. fake PATH 회귀이며 실제 설치 복구는 미수행입니다. |
| tool/MCP 없음·인증 오류 | host 확인 후 safe fallback 지침입니다. 실제 auth flow는 NOT RUN입니다. |
| version mismatch·renamed Skill | 알려진 catalog 이름만 인식합니다. hash 차이는 version semver 판정이 아닙니다. |
| circular dependency | 자동 진단하지 않습니다. 기본 8개에는 실행 가능한 dependency graph가 없습니다. |
| 끊어진 link·탐색 한도 | 패치로 가시적 경고가 됩니다. |
| global/local 설치 실패·marketplace | 자동 설치/로그인/재등록을 하지 않습니다. 외부 installer 동작은 범위 밖입니다. |
| 권한/쓰기 오류 | OS 오류를 보고하며 파일별 atomic/STATE-last를 적용합니다. 주입 장애 재실행을 확인했습니다. |
| 오래된 state/사용자 수정 | hash 보호로 충돌을 보고합니다. state를 임의 재생성해 사용자 변경을 덮지 않습니다. |

## 통합·승격 제안

- core에는 권한·완료·증거·사용자 작업 보존만 남기는 방향이 맞습니다. debug/review의 세부 절차를 더 core에 넣지 않습니다.
- karpathy/ponytail은 당장 삭제하지 않고 선택형으로 유지합니다. usage trace에서 대부분 core와 같은 판단만 반복한다면 통합 후보입니다.
- tooling은 “지침을 더 추가”하기보다 summary와 capability별 필요한 부분만 읽는 방향이 좋습니다.
- 범용 도구 사용법은 global 후보입니다. 모든 프로젝트가 browser/Graphify/Sentry를 필요로 하는 것은 아니므로 필수 global 설치 목록으로 만들지 않습니다.
- 프로젝트 용어·데이터 split/평가 접근·실험 횟수/예산·검증 명령·artifact 의미는 local-only입니다. 다른 프로젝트에 일반화해 주입하면 위험합니다.
- 같은 uh-*를 전역과 로컬에 이중 배포하지 않습니다. 팀이 version-control할 패키지는 현재 local 배포를 유지하는 것이 가장 단순합니다.
