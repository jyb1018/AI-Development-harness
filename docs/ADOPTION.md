# 설치와 적용 확인

## 새 프로젝트

저장소의 신뢰한 revision을 로컬에 두고 Python 3.10 이상으로 실행합니다.
```sh
python3 scripts/install.py /absolute/path/to/project --profile astra --dry-run
python3 scripts/install.py /absolute/path/to/project --profile astra
```
대상 디렉터리는 이미 존재해야 합니다. 설치기는 네트워크·sudo·전역 설정을 사용하지 않습니다.
루트, 자기 저장소 내부, symlink를 통한 목적지 이동은 거부합니다.

## 기존 프로젝트

기존 AGENTS가 있으면 `.universal-harness/AGENTS.proposed.md`를 검토하여 필요한 규칙만
원래 AGENTS에 통합합니다. **제안 파일은 이름만으로 자동 적용되지 않습니다.**
기존 도메인 권위, 보안, 테스트 명령은 보존하고 낡은 ceremony만 제거합니다.
사용자가 고친 설치 파일은 자동 덮어쓰지 않습니다. 충돌은 쓰기 전에 보고됩니다.
백업/수정 내용을 검토해 수동 병합한 뒤 다시 설치하거나 현재 설치를 유지하십시오.

## 활성화 확인

호스트의 새 세션에서 현재 적용 중인 프로젝트 지침 위치와 `uh-*` 스킬 발견 여부를 확인합니다.
`AGENTS.override.md`, 부모 디렉터리·전역 지침·별도 플러그인 훅이 개입하는지도 확인합니다.
설치 성공은 호스트 로딩 확인이나 모델 행동 검증과 다릅니다.
호스트가 `.agents/skills`를 탐색하지 않으면 지원하는 위치에 수동 배치하거나 해당 SKILL.md를 명시적으로 읽게 합니다.

모든 스킬을 상시 실행하지 마십시오. 기본 원칙은 core에 이미 있습니다.
`uh-karpathy`와 `uh-ponytail`은 검토를 깊게 할 때 사용하는 별도 초점입니다.
Superpowers 전체가 이미 강제 로드되면 상충하는 규칙을 무시한다고 선언하지 말고,
사용자가 그 프로젝트에서 어느 프로세스를 사용할지 정한 뒤 설정을 변경해야 합니다.

## 업데이트와 제거

```sh
python3 scripts/install.py /absolute/path/to/project --profile astra --upgrade --dry-run
python3 scripts/install.py /absolute/path/to/project --profile astra --upgrade
```
STATE.json의 파일 해시는 변경 소유권 보호용이며 기능 성공 증거가 아닙니다.
설치기는 전체 저장소 트랜잭션은 아니며 파일별 atomic replace를 사용합니다.
중단되면 출력과 상태를 확인하고 재실행합니다. 모르는 파일은 삭제하지 않습니다. 설치 중에는 대상 파일을 동시에 편집하거나 여러 설치기를 병렬 실행하지 마십시오.
이 설치기는 로컬 편의 도구이며 악의적인 동시 파일 변경을 막는 보안 sandbox가 아닙니다.
제거할 때도 STATE.json의 관리 목록과 실제 diff를 대조한 뒤 해당 파일만 수동 제거합니다.
핵심을 기존 AGENTS에 병합했다면 추가한 규칙만 빼고 원래 지침은 남깁니다.

프로젝트 고유 설정이 필요할 때만 [프로필 예시](PROJECT-PROFILE.template.md)를 사용합니다.
이 문서는 설치/실행의 필수 gate가 아닙니다.
