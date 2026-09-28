# Universal Harness 3.0

**GPT-5.6 Sol과 GPT-6 Astra에서 같은 핵심 규칙을 사용하는, 얇은 개발 지침 + 선택형 스킬 패키지입니다.**
모델의 일을 대신 조직하는 운영체제가 아니라, 목표·권한·검증의 경계를 잡습니다.
웹/서버/CLI/모바일/데이터·ML 프로젝트에 적용할 수 있지만, 각 프로젝트의 런타임·도메인 규칙은 보존해야 합니다.

## 3.0: 글로벌 도구와 로컬 하네스를 연결합니다

기존 2.x core·7개 스킬·모델 프로필을 유지하면서 **`uh-tooling` 하나**를 추가합니다.
범용 스킬은 글로벌에 두고, 프로젝트에는 필요한 도구를 선택하는 규칙과 읽기 전용
점검기를 설치합니다. 전역 설정, 제3자 스킬, MCP/plugin, 인증은 자동으로 변경하지 않습니다.

```text
Global skills / CLI / host MCP / plugins
                 ↓ 현재 호스트에서 노출·권한·대상 확인
uh-tooling → 필요한 capability만 선택 → 실제 실행 증거
                 └ 부재/실패 → 명시적 native fallback
```

Context7, Serena, Graphify, Playwright, DevTools, GitHub, CodeRabbit, Codex Security,
Sentry 등을 작업별로 연결하되 **전부 설치하거나 매번 실행할 의무는 없습니다.**
설치 상태와 사용 가능/인증/검증 완료를 구분하며, 동일 `name`의 글로벌·로컬 스킬은
본문이 같아도 중복으로 진단합니다. 자동 삭제나 로컬 override를 가정하지 않습니다.

```sh
# 대상 프로젝트에 3.0을 설치/업그레이드한 뒤
python3 .universal-harness/tooling.py doctor . --strict
python3 .universal-harness/tooling.py route . --capability library-docs
```

[도구 선택·상태·fallback 계약](docs/TOOLING.md) · [2.x → 3.0 업그레이드](docs/MIGRATION-3.md)

## 선택형 확장: 개발자 컨텍스트와 사람용 다이어그램

`uh-developer-context-sync`로 **처음 온보딩(ONBOARD)**, **변경 따라잡기(CATCH-UP)**,
**한 개념 깊게 보기(DEEP-DIVE)**를 요청할 수 있습니다. 커밋 나열보다 목적·경계·결정·
불변 조건·실패 경로를 설명하며, `uh-human-diagramming`을 독립적으로 재사용합니다.
두 스킬은 관련 요청에서만 읽으며 기존 설치기가 함께 배포합니다.

```text
uh-developer-context-sync로 이 프로젝트를 다이어그램 중심으로 온보딩해 주세요.
uh-developer-context-sync로 제가 지정한 기준 커밋 이후 달라진 구조와 위험을 설명해 주세요.
uh-human-diagramming으로 이 PR의 호출 순서와 실패 경로만 그려 주세요.
```

Mermaid가 기본이며, 실제 SVG/PNG가 필요하면 이미 설치된 `mmdc`를
`human-diagrams` capability로 확인합니다. Structurizr/C4와 인터랙티브 HTML은 선택 사항이고
자동 설치하지 않습니다. 설명을 생성한 커밋과 사용자가 확인한 커밋을 구분하며,
기준점·렌더러가 없어도 확인 가능한 현재 상태와 한계를 설명합니다.

[사용법·다이어그램·기준점 계약](docs/HUMAN-CONTEXT.md) ·
[미실행 행동 평가 시나리오 19개](evals/human-context-cases.json)

## 유지하는 2.0의 설계

`Karpathy + Ponytail + Superpowers 전체`를 동시에 상시 주입하지 않습니다.
Karpathy식 가정 확인·작은 변경·결과 검증을 핵심에 통합하고, Ponytail의 최소주의는
추상화/의존성을 추가하려는 순간에 깊게 적용합니다. Superpowers에서는 디버깅·TDD·검증·리뷰의
유용한 개념을 선택해 **별도로 재작성**했습니다. 원본 플러그인, 훅, 오케스트레이터는 설치하지 않습니다.
출처와 변경점은 [SOURCES.md](docs/SOURCES.md)에 명시했습니다.

**“5.5 → 5.6이 실패를 일으켰다”는 인과관계는 검증되지 않았습니다.**
이 패키지는 특정 모델의 성격에 대한 단정을 규칙으로 만들지 않습니다.
공식 지침과 실제 작업 결과를 분리하고, 모델·호스트·하네스를 따로 비교합니다.
현재 상태는 **구성/설치 검증 대상이며 Sol/Astra 실사용 성능 인증은 미수행**입니다.

## 선택형 프로젝트 모듈 — wrapper로 업데이트합니다

Git 프로젝트에는 원본을 `.universal-harness/module` submodule로 붙일 수 있습니다.
**새 Git 프로젝트에서는 이 방식을 권장합니다.** 최초 1회만 module의 lifecycle 진입점을 실행해
프로젝트 내부 wrapper를 만들고, 이후에는 별도 clone 경로나 전역 PATH 설정 없이 wrapper만 사용합니다.

### 최초 적용

소비자 프로젝트의 **Git 루트**에서 실행하십시오.

```sh
git submodule add \
  https://github.com/jyb1018/AI-Development-harness.git \
  .universal-harness/module

# 적용 전에 실제 변경 계획을 먼저 확인합니다.
python3 .universal-harness/module/scripts/harness.py --project . install \
  --profile astra --channel edge --dry-run

# 최초 1회 실제 적용합니다.
python3 .universal-harness/module/scripts/harness.py --project . install \
  --profile astra --channel edge

# 이후부터는 이 wrapper를 사용합니다.
./.universal-harness/harness status
```

위 예시는 `main`을 따라가는 **edge 채널**입니다. Sol은 `--profile sol`,
모델 중립 환경은 `--profile generic`을 사용합니다. `--channel`을 생략하면 업데이트 정책은
`stable`이지만, 유효한 stable 태그가 없으면 main으로 자동 전환하지 않습니다.

Windows에서는 같은 submodule을 추가한 뒤 Python 3.10+의 `python`과
생성된 `harness.cmd`를 사용합니다.

```bat
python .universal-harness\module\scripts\harness.py --project . install --profile astra --channel edge
.universal-harness\harness.cmd status
```

### 이후 평소 사용

```sh
./.universal-harness/harness status
./.universal-harness/harness check
./.universal-harness/harness pull
./.universal-harness/harness diff
./.universal-harness/harness upgrade
```

`pull`은 소스만 받으며 **지침과 wrapper 실행기는 바꾸지 않습니다**. `upgrade`는 후보를 받아
도메인 지침·관리 파일의 충돌을 검사한 뒤 적용합니다. `upgrade --offline`은 이미 받은 소스,
`upgrade --dry-run`은 네트워크 없이 현재 소스의 적용 계획만 사용합니다.
실패 시 파일·모듈 커밋 복구를 시도하고, 중단 뒤 수정된 파일은 덮어쓰지 않습니다.
부모 Git index·commit·전역 설정은 자동 변경하지 않습니다.

stable/edge/pinned 선택, 기존 복사형 설치본 전환, 팀 clone, 실패 복구의 상세 절차는
[프로젝트 모듈·wrapper 가이드](docs/LIFECYCLE.md)를 참고하십시오.
아래의 기존 복사형 설치기도 유지하며, Git이 없는 프로젝트에서 사용할 수 있습니다.

## 설치 — 빈 프로젝트도 지원합니다

Python 3.10 이상이면 됩니다. **이 저장소는 완전한 설치 원본이며, 이전 하네스나 스킬이 필요하지 않습니다.**
`.patch`는 하네스 저장소 수정용 파일일 뿐입니다. 새 프로젝트에 패치를 적용하거나
`install.py` 하나만 복사하지 말고 **전체 clone 또는 ZIP**을 사용하십시오.

```sh
# 하네스 원본과 대상 프로젝트를 서로 다른 디렉터리에 둡니다.
git clone https://github.com/jyb1018/AI-Development-harness.git "$HOME/AI-Development-harness"
mkdir -p "$HOME/my-new-project"

python3 "$HOME/AI-Development-harness/scripts/install.py" "$HOME/my-new-project" --profile astra --dry-run
python3 "$HOME/AI-Development-harness/scripts/install.py" "$HOME/my-new-project" --profile astra
# Sol은 --profile sol, 모델 중립 환경은 --profile generic
```

Git이 없어도 전체 ZIP을 풀고 위 명령의 원본 경로만 바꾸면 됩니다.
실행 위치는 어디든 가능하며, 대상은 이미 존재하는 빈 폴더여도 됩니다.
원본에는 `skills/`, `profiles/`, `harness.json`, `AGENTS.template.md`, `AGENTS.bootstrap.md`, `scripts/`, `integrations/`, `docs/`가 함께 있어야 합니다.

```text
하네스 원본                         설치 후 대상 프로젝트
skills/uh-*/SKILL.md       ─────→  .agents/skills/uh-*/SKILL.md
AGENTS.template.md        ─────→  .universal-harness/CORE.md
AGENTS.bootstrap.md       ─────→  AGENTS.md의 관리 블록만
profiles/astra.md         ─────→  .universal-harness/profile.md
                                 .universal-harness/STATE.json
scripts/tooling.py        ─────→  .universal-harness/tooling.py
integrations/tooling.json ─────→  .universal-harness/tooling.json
docs/TOOLING.md           ─────→  .universal-harness/TOOLING.md
```

원본 스킬은 **숨김 폴더가 아닌 `skills/`**에 있습니다. 대상의 `.agents/`는 설치기가 만듭니다.
하네스를 처음 넣는 기존 `AGENTS.md`는 원문 바이트를 보존하고 작은 관리 블록만 덧붙입니다.
범용 본문은 `CORE.md`로 분리하며, 도메인 불변조건·승인 경계·문서 라우팅은 블록 밖에 둡니다.
블록 밖 수정은 업데이트를 막지 않고, 블록과 다른 관리 파일의 사용자 수정은 충돌로 보호합니다.
기존 제3자 스킬·전역 설정·CI·비밀값·프로젝트 코드는 변경하지 않습니다.

예전 전체 파일 소유 방식은 수정되지 않은 AGENTS만 `--upgrade`로 자동 이관합니다.
도메인 지침이 섞인 수정본이나 옛 proposal 방식은 일회성 수동 분리 후
`--upgrade --adopt-agents-block`으로 정확한 bootstrap만 등록합니다. 새 STATE는 schema 3이며,
구버전 설치기의 전체 파일 재적용을 거부합니다. [관리 블록·이관 가이드](docs/MANAGED-AGENTS.md)를 참고하십시오.
bootstrap은 native include가 아니므로 호스트에서 CORE와 profile을 실제로 읽는지도 확인하십시오.

```sh
# v2 기존 설치 업데이트: 사용자가 수정한 파일은 덮어쓰지 않습니다.
python3 "$HOME/AI-Development-harness/scripts/install.py" /path/to/project --profile sol --upgrade --dry-run
python3 "$HOME/AI-Development-harness/scripts/install.py" /path/to/project --profile sol --upgrade
```

[설치/활성화 확인 및 오류 해결](docs/ADOPTION.md) · [v1/두꺼운 하네스에서 이관](docs/MIGRATION.md)

## 평소 작업

```text
요청과 실제 성공 조건 → 관련 코드 확인 → 작은 구현 → 필요한 검증 → 결과
```

상시 적용되는 핵심은 하나입니다. 모든 스킬을 매번 읽거나 실행하지 않습니다.
작은 버그에는 별도 계약서·스카우트·리뷰 패키지를 만들지 않습니다.
복잡한 작업도 목표와 결정을 유지하면서 진행하며, 커밋마다 멈추거나 새 스레드를 강제하지 않습니다.

| 스킬 | 언제 사용하는가 |
|---|---|
| `uh-karpathy` | 의미 있는 가정·범위 결정, 요청 외 수정 위험 |
| `uh-ponytail` | 신규 추상화·의존성·플랫폼 설계 제안 |
| `uh-debug` | 원인이 불명확하거나 재발하는 실패 |
| `uh-tdd` | 결정적 로직, 재현 가능한 버그, 안정된 계약 |
| `uh-integration` | API·DB·배포 이미지·다중 서비스 실제 연결 |
| `uh-review` | 명시적 리뷰 요청 또는 큰 보안·데이터 위험 |
| `uh-tooling` | 도구 선택, 실행기 부재, 글로벌/로컬 중복, 도구 증거 확인 |
| `uh-model-upgrade` | 모델/호스트/스킬 변경 영향 평가 |
| `uh-developer-context-sync` | 사람이 프로젝트를 처음 이해하거나 변경 맥락을 따라잡아야 할 때 |
| `uh-human-diagramming` | 경계·흐름·상태·전후 변화·실패 관계를 그림으로 설명할 때 |

스킬 호출 표기는 호스트에 따라 다릅니다. 이름을 지정하거나 해당 SKILL.md를 읽도록 요청하면 됩니다.
[프로젝트 예시](docs/EXAMPLES.md)에 API·UI·ML·고위험 작업의 차이를 담았습니다.

## Sol / Astra

두 모델 모두 동일한 핵심과 안전 기준을 사용합니다. 프로필은 작은 호환성 메모입니다.
모델 ID, reasoning effort, 도구, 승인 설정은 호스트에서 선택하며 이 패키지가 바꾸지 않습니다.
특히 Astra에서 상충하는 전역 스킬·훅과 불필요한 질문 루프를 점검합니다.
Sol에서는 기존 effort를 출발점으로 실제 작업에서 비교하되 하위 에이전트 역할을 강제하지 않습니다.
[모델 근거와 한계](docs/MODELS.md)를 참고하십시오.

## 검증

```sh
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

CI는 구조·링크·설치기 회귀만 검사합니다. 모델을 호출하거나 유료 사용량을 발생시키지 않습니다.
[행동 평가](evals/README.md)는 별도입니다. 고정 사례에 대한 실제 실행 기록 없이
“Sol/Astra 검증 완료” 또는 속도·품질 개선 수치를 만들지 않습니다.
3.0은 [도구 관련 행동 시나리오 12개](evals/tooling-cases.json)를 추가하며, 기존 host 회귀 사례를 유지합니다.

## 모델 업데이트 알림

v1의 웹문서 전체 해시 변경을 곧바로 “하네스 수정 필요”로 취급하지 않습니다.
2.0은 **공식 변경 확인 → 현재 하네스 영향 판단 → 필요한 경우만 알림 → 비교 평가 → 변경** 순서입니다.
[모델 업데이트 운영](docs/MODEL-UPGRADES.md)에 재사용 가능한 예약 지침을 제공합니다.
이 저장소를 설치한다고 ChatGPT 예약이 생기지는 않습니다. 개인 예약은 ChatGPT에서 별도로 관리합니다.
GitHub에는 기본 검증 CI만 있으며, 알림을 위해 이슈·권한·보호 설정을 자동 생성하지 않습니다.

## 한계

텍스트 지침은 보안 경계가 아닙니다. sandbox, permissions, protected branches,
배포 승인과 CI가 실제 통제를 담당해야 합니다. 기존 전역 플러그인은 자동 비활성화되지 않습니다.

원본 LICENSE를 유지합니다. 새 내용은 프로젝트 라이선스에 따르며,
특정 인물·업스트림 프로젝트 또는 OpenAI의 공식 인증/보증을 뜻하지 않습니다.
