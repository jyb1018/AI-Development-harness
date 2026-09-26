# Harness 3.0 실험 기록

기준: `218e2a40de5001fbf185c94e2c229148079ebcb9` / 3.0.0. 실제 Python/OS 정보는 [원시 결과](evals/audit-2026-09-26/evidence/experiments.json)에 있습니다. Work Linux/Python 3.11에서 수행했으며 Codex CLI는 PATH에 없었습니다. 실제 모델별 호출 수는 **0**입니다.

## 재현 방법

```sh
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
python3 evals/audit-2026-09-26/run_experiments.py --output /tmp/harness-audit-results.json
```

별도 임시 프로젝트를 생성·정리하며 사용자 프로젝트/전역 설정을 수정하지 않습니다. fake PATH와 I/O 장애 주입은 각 기록에 명시합니다. Python assertion을 사용하는 audit runner는 `python -O`로 실행하지 마십시오. 위 runner는 모델 행동 benchmark가 아닙니다.

## 주요 실험

| ID | 가설 / setup / Harness·Skill 조건 | 결과 | 해석·한계 |
|---|---|---|---|
| E01 | 기준 원본의 validator와 전체 unittest가 통과하는지 확인합니다. | **EXECUTED: 82/82 PASS**입니다. | 기존 coverage 바깥 결함이 없다는 보장은 아닙니다. [기준 로그](evals/audit-2026-09-26/evidence/baseline-tests.log)입니다. |
| E02 | required description가 없는 find-skills, malformed value, YAML separator 누락을 실제 scanner/router에 입력합니다. PATH는 fake npx입니다. | 기준: 후보 선택/경고 없음 → 패치: 경고+후보 없음입니다. 정상 metadata는 계속 후보입니다. | 실제 npx 실행·host loader 검증은 없습니다. [before](evals/audit-2026-09-26/evidence/baseline-probes.json), [after](evals/audit-2026-09-26/evidence/patched-probes.json)입니다. |
| E03 | MAX_DIRS를 4로 줄이고 40개 symlink alias를 만듭니다. | 기준 40개/경고 없음 → 패치 3개/한도 경고입니다. | 실제 OS symlink입니다. 4는 경계 재현용 설정이며 기본값은 2,000입니다. |
| E04 | skill root 아래 dangling symlink를 만듭니다. | 기준 경고 없음 → 패치 warning입니다. | root의 broken link와 하위 link를 구별했습니다. |
| E05 | STATE·run-record의 root/setup을 배열/null로 만듭니다. | 기준 traceback → 패치 명시적 오류입니다. | 기존 target 파일이 보존됩니다. 다른 모든 malformed schema를 완전히 검증한 것은 아닙니다. |
| E06 | 원본 Skill을 metadata 없는 파일, 다른 name, invalid UTF-8, over-budget로 바꿉니다. | 기준 손상 파일도 설치됨 → 패치 무변경 실패입니다. | 패키지 source trust 자체를 보증하지 않습니다. |
| E07 | tooling support mapping을 항목별 제거하고 catalog JSON을 손상시킵니다. | 첫 패치 후에도 누락 설치를 발견했습니다. 추가 수정 후 쓰기 전 실패입니다. | [2차 red 로그](evals/audit-2026-09-26/evidence/second-pass-red.log)와 새 회귀로 남겼습니다. |
| E08 | A~F 6종×generic/sol/astra의 bootstrap을 실행합니다. global roots는 빈 목록입니다. | 정상 15조합은 dry-run/설치/재설치/doctor PASS, F의 3조합은 unmanaged 충돌을 무변경 거부했습니다. | host의 실제 Skill activation은 NOT RUN입니다. F는 잘못된 부분 파일을 자동 삭제하는 것이 성공이 아닙니다. |
| E09 | 기존 프로젝트 형태 10종에 설치합니다. 기존 AGENTS/소스/data/weight 표식 파일의 SHA256을 비교합니다. | 10/10 보존·manual merge pending·8 Skill discovery·idempotence PASS입니다. | skeleton fixture이며 애플리케이션 구현/테스트/학습 성공을 뜻하지 않습니다. |
| E10 | 10/100/1,000/2,100 Skill의 scan을 실제 파일로 실행합니다. | 10/100/1,000은 전수 발견, 2,100은 1,999개+한도 경고입니다. | 루트 디렉터리도 1 visit입니다. 생성시간을 제외한 scan 시간이 기록됩니다. 자연어 선택 정확도는 아닙니다. |
| E11 | 11 capability를 absent/host-reported/offline/무관한 손상 Skill 4조건으로 조회합니다. | 4행 실험에 포함된 44 route 결과를 기록했습니다. readiness는 전부 unverified입니다. | --available은 synthetic 입력입니다. 실제 provider 인증·사용은 없습니다. |
| E12 | installer의 4번째 atomic write에 OSError를 주입합니다. | 3개 파일 기록 후 STATE 없음 → 같은 원본 재실행 완료입니다. | **SIMULATED I/O 장애를 사용하는 EXECUTED 코드 실험**입니다. 전원 차단/동시 편집 실험은 아닙니다. |
| E13 | 실제 CLI에서 1,000 Skill full route와 --summary의 bytes·route를 비교합니다. | 310,330 → 1,413 B, 동일 route, 99.54% 감소입니다. | provider는 호출하지 않았습니다. 실제 model tokens/latency 절감률이 아닙니다. [결과](evals/audit-2026-09-26/evidence/summary-comparison.json)입니다. |
| E14 | 소비자 설치 후 model-upgrade의 evals 참조가 존재하는지 확인합니다. | target `evals/README.md` 없음이 확인됐습니다. | source checkout에는 존재하므로 참조 위치를 명확히 했습니다. 문구를 agent가 따르는지는 미평가입니다. |
| E15 | 비공개 CV/OCR benchmark의 고정 revision에서 지침·설정·의존성·테스트 예시를 읽습니다. | 프로젝트 특수 권한과 ML/일반 테스트 구별, 기존 지침 보존 필요성을 SOURCE로 확인했습니다. | 읽기/분석만 수행했습니다. private 상세는 별도 부록이며 제품 테스트/학습/설치는 NOT RUN입니다. |
| E16 | 모든 수정 뒤 package validation, 전체 unittest 및 fixture runner를 다시 실행합니다. | 최종 **94/94 PASS**는 [패치 테스트 로그](evals/audit-2026-09-26/evidence/patched-tests.log)에 기록했습니다. fixture runner 37/37 PASS입니다. | 모델 행동·사용자 Mac·외부 서비스 검증은 포함하지 않습니다. |

공개 로그는 임시 경로를 일부 익명화하고 줄 끝 공백을 제거했습니다. 검사 결과와 오류 내용은 보존했습니다.

새 regression의 처음 red 단계는 [regressions-red.log](evals/audit-2026-09-26/evidence/regressions-red.log)에 있습니다. 여기서 failure 수는 subTest assertion 수이며 독립 실험 수와 합산하지 않습니다. F06 summary 테스트는 신규 기능의 계약 검사이므로 기준 버전에 대해 red를 꾸미지 않았습니다.

## Bootstrap A~F의 정확한 구성

| Case | 초기 상태 | 기대·관측 |
|---|---|---|
| A | 빈 디렉터리, Git 없음 | 성공, 8개 Skill 발견입니다. |
| B | README만 존재 | README hash 보존, 성공입니다. |
| C | `git init`만 수행 | Git 보존, 성공입니다. |
| D | package.json만 존재 | 원본 package.json 보존, 성공입니다. |
| E | pyproject.toml과 빈 Python entry | 원본 보존, 성공입니다. |
| F | 사용자 관리인 손상된 uh-debug 일부 | 덮어쓰기 없이 실패합니다. 사용자 파일 정리가 필요하다는 정확한 중단입니다. |

추가로 기존 배포 suite가 script-only·원본 missing skill/profile/core/manifest·숨김폴더 없이 복사·ZIP 설치를 다룹니다. 따라서 과거의 “target에 선행 Skill이 없으면 시작 불가”는 현재 정상 전체 배포에서는 재현되지 않습니다. **원본 불완전과 target empty는 서로 다른 경우**입니다.

## 기존 프로젝트 10종과 행동 비교 — SIMULATED

위 설치 실험과 아래 행동 기대표는 별개입니다. No Harness는 “호스트 기본 지침까지 제거”하는 조건이 아니라 추가 Universal Harness만 없는 조건이어야 합니다.

| Fixture / 요청 예 | No Harness | 3.0에서 기대하는 추가 가치 | 관련 Skill / 검증 경계 |
|---|---|---|---|
| Node backend / 작은 버그 | 모델 기본 탐색·수정 가능 | scope/실제 reproducer 유지 | debug+tdd, 함수/API assertion입니다. |
| React / UI 수정 | 기본 UI 도구 사용 가능 | 단위 PASS와 시각 검증 구분 | 필요 시 tooling, browser availability입니다. |
| TS monorepo / dependency migration | 기본 dependency 추적 가능 | repo별 toolchain·영향 범위 보존 | integration+review, workspace별 build입니다. |
| Python backend / API 추가 | 기본 구현 가능 | real adapter와 fake 경계 구분 | tdd+integration입니다. |
| Python ML / 신규 모델 feature | 기본 ML 지식 활용 가능 | deterministic code와 품질 평가 구분 | tdd는 전달 로직, quality는 별도 eval입니다. |
| CV/OCR / performance investigation | 기본 profiling 가능 | 모델·데이터 artifact/실험 예산 보존 | debug+integration, approved profiler입니다. |
| mixed language / race condition | 기본 원인 추론 가능 | 첫 실패/반복/경계 증거 유지 | debug+review, concurrency 조건입니다. |
| legacy / architecture refactor | 기본 refactor 가능 | 새 abstraction의 실익 비교 | karpathy+ponytail입니다. |
| large suite / flaky | 기본 테스트 선택 가능 | 나중 PASS가 실패를 지우지 않음 | debug+tdd, seed/order/time 조건입니다. |
| poor docs / undocumented 분석 | 기본 탐색 가능 | 모르는 시스템을 추정 사실로 쓰지 않음 | 선택 tooling, source로 graph 확인입니다. |
| 추가 task / CI 실패 | 기존 로그 조사 가능 | 실제 runtime 도달 여부·native permission 구분 | debug+tooling입니다. |

세 조건의 accepted outcomes·시간·토큰·질문 수를 실행해 비교하지 않았습니다. 표로 우승 조건을 선언하지 않습니다.

## 미실행·접근 불가 항목

| 항목 | 상태·이유 |
|---|---|
| Astra/Sol×medium/high/x-high controlled trials | NOT RUN: 해당 실행기의 모델별 fresh-context 평가를 수행하지 않았습니다. |
| 실제 trigger precision/recall | NOT RUN: 29개 사례의 기대 rubric만 준비했습니다. |
| 실제 global/local loader winner와 중복 주입량 | UNKNOWN: 사용자의 host/active catalog/설치 revision을 관측하지 못했습니다. |
| API/유료 모델·외부 review·browser/auth | NOT RUN: 이 감사가 해당 실행을 한 것으로 기록하지 않습니다. |
| macOS/Windows 로컬 실험 | NOT RUN: 로컬은 Linux입니다. 원격 CI 결과는 PR Checks에서 따로 확인합니다. |
| circular dependencies·version solver | NOT IMPLEMENTED: 이 package는 resolver/runtime가 아닙니다. |
| context-full·compaction·host refresh의 행동 | SIMULATED: 기존 catalog와 충돌 표의 기대만 검토했습니다. |

## 20개 Phase와 증거 연결

| Phase | 결과 위치 |
|---|---|
| 1 구조 | 전체 감사 architecture / source files입니다. |
| 2 inventory | Skill 감사 8개 전수 table입니다. |
| 3 global/local | 중복 회귀·precedence table입니다. |
| 4 discovery | 실제 route 실험과 SIMULATED trigger corpus입니다. |
| 5 trigger | 29개 기대 사례이며 실제 선택률은 미측정입니다. |
| 6 loading | byte 측정·lazy loading 분석입니다. |
| 7 conflict | Red Team의 SIMULATED 충돌 10종입니다. |
| 8 recovery | E02~E07, E11~E12입니다. |
| 9 empty | E08/기존 배포 회귀입니다. |
| 10 existing | E09와 행동 비교의 명시적 분리입니다. |
| 11 real project | E15, 비공개 읽기 전용 부록입니다. |
| 12 behavior | 실행 증거 보유 여부와 pathological behavior 가설 구분입니다. |
| 13 modern models | 규칙별 유지/압축 후보와 공식 최신 prompting 자료입니다. |
| 14 profiles | 개선 제안의 rule 분류입니다. |
| 15 economics | E10/E13와 context-cost.json입니다. |
| 16 consolidation | Skill 감사의 optional/global/local 제안입니다. |
| 17 adversarial | before/after probes 및 2차 support mutation입니다. |
| 18 false positives | 전체 감사 rejected findings입니다. |
| 19 improvement | 제한된 scripts/docs/한 Skill 참조 수정입니다. |
| 20 regress | E16 및 패치 재공격입니다. |
