# 2.x → 3.x 이관

3.0 최초 배포는 기존 core의 권한/검증 경계, 7개 uh-* 스킬, Sol/Astra/generic 프로필을
유지하고 선택형 `uh-tooling`과 3개의 support 파일을 추가했습니다.
현재 선택형 Human Context 스킬과 관리 블록 확장도 함께 설치됩니다.
하네스 manifest schema는 2를 유지하지만, **새 설치 STATE는 블록 소유권을 기록하는 schema 3**입니다.
기존 schema 2는 안전한 이관을 위해 읽을 수 있습니다.
전역 설정을 바꾸거나 기존 제3자 스킬을 제거하는 마이그레이션은 하지 않습니다.

## 적용

하네스 원본을 받은 후 대상 프로젝트에 적용하십시오. 원본 저장소 자체를 대상으로 삼지 않습니다.

```sh
python3 /path/to/AI-Development-harness/scripts/install.py /path/to/project --profile astra --upgrade --dry-run
python3 /path/to/AI-Development-harness/scripts/install.py /path/to/project --profile astra --upgrade
cd /path/to/project
python3 .universal-harness/tooling.py doctor . --strict
```

기존 profile을 유지하십시오. Sol은 `--profile sol`, 모델 중립은 `--profile generic`입니다.
빈 프로젝트는 `--upgrade` 없이 설치합니다. 사용자 수정이 없는 관리 파일만 업그레이드되며,
관리 블록/CORE/스킬/support 파일 하나라도 충돌하면 **계획 단계에서 전체 쓰기를 중단**합니다.
블록 밖 프로젝트 지침 수정은 충돌이 아니며 그대로 보존됩니다.

이전 AGENTS 전체가 설치 당시 해시와 같으면 작은 bootstrap으로 바꾸고 범용 본문은
`.universal-harness/CORE.md`에 설치합니다. 수정된 전체 파일이나 옛 proposal 방식의 설치는
일회성 수동 분리가 필요합니다. 출력된 정확한 블록을 넣은 뒤 `--upgrade --adopt-agents-block`을
사용합니다. 임의의 블록을 강제 등록하거나 도메인 문장을 추측해 지우지 않습니다.
[상태별 동작·이관·복구 가이드](MANAGED-AGENTS.md)를 참고하십시오.

## 글로벌 승격 스킬

find-skills, find-docs, playwright-cli, code-review를 글로벌에 두었다면 프로젝트에
동일 복사본을 추가하지 않습니다. doctor는 frontmatter의 `name`으로 중복을 진단하므로
폴더명만 바꾸어도 같은 이름은 탐지합니다. 동일 본문, 서로 다른 본문, symlink alias를 구분합니다.

설치기는 배포하는 uh-*와 같은 이름이 **관리 대상 경로 외부**에 있으면 쓰기 전에 중단합니다.
글로벌뿐 아니라 상위 프로젝트/다른 로컬 폴더의 중복도 포함합니다. 외부 스킬끼리의 중복은
doctor로 확인합니다. 어떤 복사본을 유지할지 검토하고 사용자 지시에 따라 직접 정리하십시오.
수정된 변종은 의미 있는 별도 이름을 사용해야 합니다. 이름을 바꾸는 작업도 자동으로 하지 않습니다.

파일 스캐너는 호스트 disabled 설정을 해석하지 않으므로 비활성화된 정의도 보고할 수 있습니다.
팀/CI의 활성 글로벌 범위가 다르면 `--global-skill-root /path/to/active-skills`를 반복 지정할 수
있습니다. 이는 기본 경로를 대체합니다. 중복을 숨기기 위해 범위를 줄이지 말고 실제 호스트
설정과 함께 검토하십시오. 특정 사용자의 전역 환경에 의존하는 패키지로 만들지 않습니다.

## 설치와 사용 가능 상태는 다릅니다

전역 프로그램이 PATH에 있어도 호스트 MCP가 연결되지 않을 수 있고, 연결되어도 인증/권한이
없을 수 있습니다. doctor는 설치 흔적만 보여 주며 실제 호출 성공을 주장하지 않습니다.
GitHub/Codex Security plugin 또는 Serena가 보이지 않아도 하네스를 재설치하지 마십시오.
현재 호스트의 도구 노출·연결 상태를 확인하고 해당 작업에 명시된 fallback을 사용합니다.
예약 marketplace를 재추가하거나 인증·전역 설정을 자동으로 변경하지 않습니다.

## 되돌리기

업그레이드 전에 대상 프로젝트의 작업 트리와 하네스 관리 파일을 별도로 보존하십시오.
롤백 자동화는 제공하지 않습니다. 버전 관리된 하네스 변경만 검토해 되돌리며,
사용자의 다른 변경이나 전역 스킬을 삭제하지 않습니다. STATE.json과 관리 파일을
서로 다른 버전으로 임의 조합하지 마십시오.
schema 2 전용 구버전 설치기는 새 schema 3을 거부합니다. 상태 숫자만 낮춰 실행하지 말고,
이후 추가한 프로젝트 지침을 보존하면서 관리 파일·상태를 함께 검토해 복구하십시오.
