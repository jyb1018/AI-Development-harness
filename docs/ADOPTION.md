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
현재 배포본에는 core 원본 `AGENTS.template.md`와 작은 `AGENTS.bootstrap.md`가 모두 필요합니다.

### 설치 확인

설치 후 `AGENTS.md`의 관리 블록, `.universal-harness/CORE.md`, `profile.md`, `STATE.json`,
그리고 manifest에 등록된 `.agents/skills/uh-*/SKILL.md`가 생성됩니다. 숨김 폴더는 파일 탐색기에서
보이지 않을 수 있으므로 터미널에서도 확인할 수 있습니다.

```sh
ls -la "$HOME/my-new-project"
find "$HOME/my-new-project/.agents/skills" -name SKILL.md
```

## 기존 프로젝트

하네스를 처음 넣는 기존 프로젝트는 AGENTS 원문을 바이트 단위로 보존하고 끝에 작은
관리 블록만 추가합니다. **도메인 불변조건·승인 경계·검증 규칙은 관리 블록 밖에 둡니다.**
범용 본문은 `.universal-harness/CORE.md`에 설치하므로 AGENTS 전체를 매번 병합하지 않습니다.

예전 하네스 설치본은 `--upgrade`로 이관합니다. 예전 전체 파일 해시와 AGENTS가 일치하면
자동 이관하지만, 사용자 수정이 섞였거나 옛 proposal 방식으로 수동 병합한 경우에는
자동 분리하지 않습니다. 충돌 출력의 bootstrap을 검토하고 프로젝트 지침을 보존해 수동 정리한 뒤,
`--upgrade --adopt-agents-block`으로 정확한 단일 블록의 소유권만 등록하십시오.
이 옵션은 CORE/스킬/support 파일 충돌을 우회하는 force가 아닙니다.

일단 블록 방식으로 이관하면 **블록 밖 프로젝트 지침 수정은 정상 업데이트를 막지 않습니다.**
블록 내부나 다른 관리 파일을 사용자가 고친 경우에는 쓰기 전에 충돌을 보고합니다.
기존 `AGENTS.proposed.md`는 보존하되 더 이상 갱신하거나 자동으로 읽게 하지 않습니다.
[관리 블록과 일회성 이관 상세](MANAGED-AGENTS.md)를 참고하십시오.

## 활성화 확인

호스트의 새 세션에서 현재 적용 중인 프로젝트 지침 위치와 `uh-*` 스킬 발견 여부를 확인합니다.
`AGENTS.override.md`, 부모 디렉터리·전역 지침·별도 플러그인 훅이 개입하는지도 확인합니다.
설치 성공은 호스트 로딩 확인이나 모델 행동 검증과 다릅니다.
bootstrap의 경로는 native include가 아니므로 CORE와 profile을 실제로 읽었는지도 확인합니다.
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
STATE.json schema 3은 AGENTS 관리 블록 해시와 나머지 파일 해시를 분리합니다.
이 해시는 변경 소유권 보호용이며 기능 성공 증거가 아닙니다. 구버전 설치기로 강제 다운그레이드하지 마십시오.
설치기는 전체 저장소 트랜잭션은 아니며 파일별 atomic replace를 사용합니다.
중단되면 출력과 상태를 확인하고 재실행합니다. 모르는 파일은 삭제하지 않습니다. 설치 중에는 대상 파일을 동시에 편집하거나 여러 설치기를 병렬 실행하지 마십시오.
이 설치기는 로컬 편의 도구이며 악의적인 동시 파일 변경을 막는 보안 sandbox가 아닙니다.
제거할 때도 STATE.json의 관리 목록과 실제 diff를 대조한 뒤 해당 파일과 관리 블록만 수동 제거합니다.
**프로젝트 지침이 있는 AGENTS.md 전체를 삭제하지 마십시오.**

프로젝트 고유 설정이 필요할 때만 [프로필 예시](PROJECT-PROFILE.template.md)를 사용합니다.
이 문서는 설치/실행의 필수 gate가 아닙니다.
