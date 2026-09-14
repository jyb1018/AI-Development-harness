# 설치와 적용 확인

## 새 프로젝트: 패치 없이 설치합니다

하네스 원본을 전체 clone하거나 ZIP으로 받아 압축을 풉니다. **새 프로젝트는 설치 대상이지
원본 스킬을 찾는 위치가 아닙니다.** 이전 하네스, `.agents`, Git 저장소가 없어도 됩니다.
원본과 대상을 별도 디렉터리에 두고 Python 3.10 이상으로 실행하십시오.

```sh
git clone https://github.com/jyb1018/AI-Development-harness.git "$HOME/AI-Development-harness"
mkdir -p "$HOME/my-new-project"
python3 "$HOME/AI-Development-harness/scripts/install.py" "$HOME/my-new-project" --profile astra --dry-run
python3 "$HOME/AI-Development-harness/scripts/install.py" "$HOME/my-new-project" --profile astra
```

전체 ZIP으로 받은 경우에도 같은 설치기를 사용합니다. 원본의 `skills/`에서 읽어
대상의 `.agents/skills/`에 복사하므로 현재 작업 디렉터리는 관계없습니다.
`--profile sol` 또는 `--profile generic`도 새 프로젝트에서 동일하게 지원합니다.
대상 디렉터리는 이미 존재해야 합니다. 설치기는 네트워크·sudo·전역 설정을 사용하지 않습니다.
루트, 자기 저장소 내부, symlink를 통한 목적지 이동은 거부합니다.

### 원본 누락 오류

`Incomplete harness source package` 또는 `Missing source: skills/.../SKILL.md`는
**설치 원본이 불완전하다는 뜻**입니다. 대상에 가짜 스킬 파일을 만들거나 검사를 끄지 마십시오.
`install.py` 하나나 `.patch`만 실행하지 말고 전체 clone/ZIP을 다시 확보하십시오.
`.patch`는 기존 하네스 저장소에 변경을 적용하는 용도이며 제품 프로젝트의 설치기가 아닙니다.

초기 v2.0 공개 트리에는 `.agents/skills/`가 누락되어 빈 프로젝트 설치가 실패했습니다.
v2.0.1부터는 원본을 일반 `skills/` 폴더에 포함하고 설치 전에 필요한 파일을 모두 확인합니다.
원본 누락이 있으면 대상에 아무 파일도 쓰지 않고 종료합니다.

### 설치 확인

설치 후 `AGENTS.md`, `.universal-harness/profile.md`, `.universal-harness/STATE.json`,
그리고 `.agents/skills/uh-*/SKILL.md` 일곱 개가 생성됩니다. 숨김 폴더는 파일 탐색기에서
보이지 않을 수 있으므로 터미널에서도 확인할 수 있습니다.

```sh
ls -la "$HOME/my-new-project"
find "$HOME/my-new-project/.agents/skills" -name SKILL.md
```

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
