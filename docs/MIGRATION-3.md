# 2.x → 3.0 이관

3.0은 기존 core의 권한/검증 경계, 7개 uh-* 스킬, Sol/Astra/generic 프로필을 유지하고
선택형 `uh-tooling`과 3개의 support 파일을 추가합니다. 저장소 VERSION은 3.0.0이지만
설치 STATE와 harness manifest의 `schema_version: 2`는 하위 호환을 위해 유지합니다.
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
수정된 AGENTS/스킬/support 파일 하나라도 충돌하면 **계획 단계에서 전체 쓰기를 중단**합니다.
관리되지 않는 기존 AGENTS.md는 그대로 두고 AGENTS.proposed.md를 만들어 수동 병합을 요구합니다.

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
