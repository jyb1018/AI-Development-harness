# Universal Harness 2.0

**GPT-5.6 Sol과 GPT-6 Astra에서 같은 핵심 규칙을 사용하는, 얇은 개발 지침 + 선택형 스킬 패키지입니다.**
모델의 일을 대신 조직하는 운영체제가 아니라, 목표·권한·검증의 경계를 잡습니다.
웹/서버/CLI/모바일/데이터·ML 프로젝트에 적용할 수 있지만, 각 프로젝트의 런타임·도메인 규칙은 보존해야 합니다.

## 2.0의 판단

`Karpathy + Ponytail + Superpowers 전체`를 동시에 상시 주입하지 않습니다.
Karpathy식 가정 확인·작은 변경·결과 검증을 핵심에 통합하고, Ponytail의 최소주의는
추상화/의존성을 추가하려는 순간에 깊게 적용합니다. Superpowers에서는 디버깅·TDD·검증·리뷰의
유용한 개념을 선택해 **별도로 재작성**했습니다. 원본 플러그인, 훅, 오케스트레이터는 설치하지 않습니다.
출처와 변경점은 [SOURCES.md](docs/SOURCES.md)에 명시했습니다.

**“5.5 → 5.6이 실패를 일으켰다”는 인과관계는 검증되지 않았습니다.**
이 패키지는 특정 모델의 성격에 대한 단정을 규칙으로 만들지 않습니다.
공식 지침과 실제 작업 결과를 분리하고, 모델·호스트·하네스를 따로 비교합니다.
현재 상태는 **구성/설치 검증 대상이며 Sol/Astra 실사용 성능 인증은 미수행**입니다.

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
원본에는 `skills/`, `profiles/`, `harness.json`, `AGENTS.template.md`, `scripts/`가 함께 있어야 합니다.

```text
하네스 원본                         설치 후 대상 프로젝트
skills/uh-*/SKILL.md       ─────→  .agents/skills/uh-*/SKILL.md
AGENTS.template.md        ─────→  AGENTS.md
profiles/astra.md         ─────→  .universal-harness/profile.md
                                 .universal-harness/STATE.json
```

원본 스킬은 **숨김 폴더가 아닌 `skills/`**에 있습니다. 대상의 `.agents/`는 설치기가 만듭니다.
기존 `AGENTS.md`가 있으면 보존하고 `.universal-harness/AGENTS.proposed.md`를 만들어
수동 병합 필요 상태를 알립니다. 기존 스킬·전역 설정·CI·비밀값·프로젝트 코드는 변경하지 않습니다.

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
| `uh-model-upgrade` | 모델/호스트/스킬 변경 영향 평가 |

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
