# 프로젝트 모듈과 wrapper 기반 업데이트

하네스를 선택형 Git submodule로 붙이고 **프로젝트 내부 wrapper 하나**로 관리합니다.
기존 복사형 `scripts/install.py`도 유지합니다. Git이 없는 프로젝트는 기존 방식을 쓰시면 됩니다.
이 문서는 새 lifecycle 구현의 계약이며, 실제 모델의 지침 준수 인증은 아닙니다.

## 처음 적용하기

**소비자 프로젝트의 Git 루트**에서 실행하십시오. 하네스 원본 저장소 자체가 대상은 아닙니다.
이미 `.universal-harness/module`이 있다면 다시 `submodule add`하지 말고 위치와 origin을 확인하십시오.
모듈에는 수정하지 않은 upstream 소스를 두며 프로젝트 지침은 기존 AGENTS 관리 블록 밖에 둡니다.

```sh
git submodule add \
  https://github.com/jyb1018/AI-Development-harness.git \
  .universal-harness/module

# 최초 1회만 모듈의 진입점을 실행합니다. 이후에는 아래 wrapper를 사용합니다.
python3 .universal-harness/module/scripts/harness.py --project . install \
  --profile astra --channel edge --dry-run
python3 .universal-harness/module/scripts/harness.py --project . install \
  --profile astra --channel edge

./.universal-harness/harness status
```

위 예시는 **main의 변경을 바로 시험하는 edge 채널을 명시적으로 선택**합니다.
`--channel`을 생략하면 향후 원격 업데이트 정책은 `stable`입니다. stable 태그가 없으면
check/pull/online upgrade는 실패하며 main으로 몰래 전환하지 않습니다.
최초 install은 네트워크 없이 **현재 체크아웃한 정확한 커밋**을 적용합니다.
채널은 그 다음 원격 업데이트를 선택하는 정책이지 최초 체크아웃을 바꾸는 옵션이 아닙니다.

Linux/macOS wrapper는 Python 3.10+의 `python3`을 사용하고 실행 권한을 설치합니다.
전역 PATH, 셸 설정, alias, Python 설치는 변경하지 않습니다.

Windows에서는 이미 설치된 Python 3.10+가 `python`으로 실행되어야 합니다.

```bat
python .universal-harness\module\scripts\harness.py --project . install --profile astra --channel edge
.universal-harness\harness.cmd status
.universal-harness\harness.cmd upgrade
```

wrapper는 자신의 위치로 프로젝트 루트를 찾으므로 다른 디렉터리에서 절대 경로로 실행해도 됩니다.

## 소유권과 파일 구조

```text
project/
  AGENTS.md                       프로젝트 지침 + 작은 하네스 관리 블록
  .gitmodules                     사용자가 추가한 submodule 연결
  .universal-harness/
    module/                       Git submodule: upstream 소스, 정확한 commit으로 고정
    harness                       Unix wrapper
    harness.cmd                   Windows wrapper
    lifecycle.py                  현재 적용된 lifecycle 실행기
    config.json                   프로젝트 소유: 원하는 profile/채널/source
    MODULE.json                   lifecycle 소유: 적용 commit + wrapper/runtime 해시
    STATE.json                    기존 설치기 소유: schema 3, block/payload 해시
    CORE.md / profile.md / ...    현재 적용된 지침과 지원 파일
    .gitignore                    transaction/명령 잠금만 로컬로 제외
    .transaction.json             미완료 업데이트 복구 자료, 성공하면 삭제
  .agents/skills/uh-*/SKILL.md     호스트가 읽는 현재 적용된 스킬
```

**wrapper는 `module/scripts/harness.py`가 아니라 적용된 `lifecycle.py`를 실행합니다.**
따라서 pull로 새 upstream 실행기나 스킬을 내려받아도 즉시 실행/적용되지 않습니다.
upgrade가 성공할 때 실행기도 함께 교체합니다. source-only pull과 실행기 업데이트를 구분합니다.

`STATE.json`을 또 다른 포맷으로 바꾸지 않습니다. `MODULE.json`이 설치 상태 파일의 해시와
적용 커밋을 연결합니다. lifecycle로 전환한 뒤 예전 standalone installer를 섞어 실행하여
STATE가 달라지면 상태 불일치를 보고하고 자동으로 소유권을 재등록하지 않습니다.

## 명령별 효과

| 명령 | 원격 조회/전송 | module checkout | 적용 파일 |
|---|---|---|---|
| `status` | 하지 않습니다 | 그대로 둡니다 | 상태·해시를 읽기만 합니다 |
| `check` | 채널 ref를 조회합니다 | 그대로 둡니다 | 그대로 둡니다 |
| `diff` | 하지 않습니다 | 그대로 둡니다 | applied → source Git 변경 통계만 보여 줍니다 |
| `pull` | ref 확인 후 fetch합니다 | 고정 SHA로 옮깁니다 | 지침·실행기·설치 상태를 바꾸지 않습니다 |
| `upgrade` | ref 확인 후 fetch합니다 | 검증된 적용 계획과 함께 옮깁니다 | 충돌 검사·적용·해시 확인을 거쳐 갱신합니다 |
| `upgrade --offline` | 하지 않습니다 | 현재 source를 사용합니다 | 현재 source를 적용합니다 |
| `upgrade --dry-run` | 하지 않습니다 | 현재 source를 사용합니다 | 계획만 출력합니다 |
| `doctor` | 기존 doctor 계약을 따릅니다 | 그대로 둡니다 | 적용된 읽기 전용 도구 점검기를 실행합니다 |
| `recover` | 하지 않습니다 | 필요한 경우 이전 SHA로 복구합니다 | 남아 있는 transaction을 복구합니다 |

**dry-run은 최신 원격 버전의 미리보기가 아니라 현재 체크아웃의 미리보기**입니다.
원격 후보를 먼저 검토하려면 다음 순서가 명확합니다.

```sh
./.universal-harness/harness check
./.universal-harness/harness pull
./.universal-harness/harness diff
./.universal-harness/harness upgrade --dry-run
./.universal-harness/harness upgrade --offline
```

평소에는 `./.universal-harness/harness upgrade` 한 번으로 fetch + 적용하시면 됩니다.
`status`의 `source_revision`, `gitlink_revision`, `applied_revision`은 각각 현재 source,
부모 Git index의 포인터, 실제 적용 기준입니다. status는 오프라인이므로 “최신”을 주장하지 않습니다.
`diff`는 의미적 위험 점수나 사람의 이해도 판정이 아닙니다. 중요한 변경 해설은
[Human Context Layer](HUMAN-CONTEXT.md)에 요청하시면 됩니다.

## 채널과 정확한 버전 선택

프로젝트가 원하는 설정은 `.universal-harness/config.json`에서 관리합니다.
업데이트 중에는 기존 config를 덮어쓰지 않습니다. `profile`도 이 파일의 값을 유지합니다.

```json
{
  "schema_version": 1,
  "source": "https://github.com/jyb1018/AI-Development-harness.git",
  "profile": "astra",
  "channel": "edge"
}
```

`stable`은 원격의 `vMAJOR.MINOR.PATCH` 태그만 숫자 버전 순으로 선택합니다. prerelease는 제외하고,
annotated/lightweight tag 모두 최종 commit으로 해석합니다. 선택한 stable 태그와 manifest 버전이
불일치하면 적용하지 않으며, 이미 적용한 버전보다 낮은 stable로 자동 강등하지 않습니다. **GitHub Release 발행 여부나 서명을 검증하는 기능은 아닙니다.**
태그 이름이 stable이거나 테스트가 통과했다고 해당 지침의 안전성·성능이 인증되지는 않습니다.

`edge`는 `refs/heads/main`, `pinned`는 config의 `ref`에 적은 전체 commit SHA를 사용합니다.
명령별 `--channel edge`, `--ref <전체 SHA>`, `--ref refs/tags/v3.1.0`으로 후보를 명시할 수 있습니다.
이는 config를 바꾸지 않는 일회성 선택입니다. `main`, `HEAD~1` 같은 모호한 ref는 받지 않습니다.
ref가 원격 조회와 fetch 사이에 이동하면 새로운 값을 묵인하지 않고 중단합니다.

```sh
# 의도한 특정 버전으로 전환하거나 되돌리기: 동일한 소유권 검사를 통과해야 합니다.
./.universal-harness/harness upgrade --ref refs/tags/v3.1.0
# 고정 커밋: 축약 SHA가 아닌 실제 전체 commit ID를 넣으십시오.
./.universal-harness/harness upgrade --ref <FULL_COMMIT_SHA>
```

원격 source는 config, `.gitmodules`, module origin이 일치해야 합니다. HTTPS/SSH 또는 명시적인
절대 로컬 경로를 지원하며 URL에 자격증명을 넣지 않습니다. 인증은 기존 Git 환경을 사용합니다.
origin 변경, 자동 설치, 하위 submodule 재귀 업데이트, 개인 브라우저/인증 설정 수리는 하지 않습니다.

## 기존 복사형 설치본 전환

먼저 module을 추가하고 위 최초 install을 실행합니다. 설치된 profile을 동일하게 지정하십시오.
이미 관리 블록 구조인 설치본은 기존 installer의 계획과 해시 보호를 재사용하여 전환합니다.
예전 schema 2의 도메인 혼합 AGENTS는 [관리 블록 이관](MANAGED-AGENTS.md)에 따라 한 번 분리해야 합니다.
정리한 블록을 등록할 때 최초 lifecycle install에도 `--adopt-agents-block`을 전달할 수 있습니다.
이 옵션은 프로젝트 지침 삭제나 CORE/스킬/wrapper 충돌을 우회하는 force가 아닙니다.
옛 `AGENTS.proposed.md`는 삭제하지 않습니다.

기존 wrapper/config 등 같은 경로에 다른 파일이 있으면 덮어쓰지 않고 중단합니다.
기존 `.universal-harness/.gitignore`도 자동 병합하지 않습니다. 의도와 기존 내용을 확인한 뒤
사용자가 정리해야 하며, 설치기가 임의로 설정 파일의 소유권을 가져오지 않습니다.

## 실패, 동시 편집, 복구

적용 계획은 선택한 immutable commit의 임시 스냅샷에서 기존 `install.py`의 계획 함수를 호출해
만듭니다. 이때 **선택한 upstream Python 코드를 실행합니다**. 신뢰한 source/ref에만 install/upgrade를
실행하십시오. check/pull/status/diff는 candidate Python 코드를 실행하지 않습니다.
로컬 Git 인증/필터 등 기존 Git 실행 환경의 동작까지 격리하는 보안 sandbox는 아닙니다.

일반적인 적용 순서는 후보 선택 → 소스 스냅샷 → 소유권·경로 충돌 검사 → 복구 journal 작성 →
module checkout → 파일별 atomic replace → STATE/MODULE 기록 → 적용 해시 확인 → journal 제거입니다.
예전 버전에서 제거된 payload는 **이전 설치기가 소유했고 해시가 그대로인 파일만** 제거합니다.
사용자 문서, 프로젝트 소스, 제3자 스킬, 부모 저장소의 index/다른 변경은 삭제하거나 reset하지 않습니다.

일반적인 쓰기·검증 실패에는 이전 bytes/권한/module commit 복구를 시도합니다.
중단 이후 사용자가 수정한 파일이 발견되면 덮어쓰지 않고 journal을 남깁니다.
프로세스 강제 종료나 정전 뒤에는 아래처럼 확인하십시오.

```sh
./.universal-harness/harness status
./.universal-harness/harness recover
```

명령 잠금 폴더가 남으면 **실행 중인 프로세스가 없음을 먼저 확인**하고 그 잠금만 수동 제거한 뒤
recover를 실행합니다. 자동 잠금 해제나 시간만 보고 살아 있는 프로세스를 추측하지 않습니다.
최초 설치 중 wrapper 생성 전에 실패했다면 module의 `scripts/harness.py --project . recover`를
사용하십시오. source가 로컬 수정 상태이거나 다른 커밋으로 이동했다면 먼저 수동으로 검토해야 합니다.

journal에는 기존 프로젝트 지침의 복구용 내용이 포함될 수 있습니다. 로컬 제외 상태를 유지하고
공유·커밋하지 마십시오. 성공한 journal은 보관하지 않습니다. 업데이트는 완전한 파일시스템
트랜잭션이 아니며, 전원 손실 내구성이나 악의적인 동시 파일 변경까지 보장하지 않습니다.

## 팀에서 동일한 적용 상태 재현하기

upgrade는 부모 저장소에 `git add`, commit, push, merge를 실행하지 않습니다.
사용자가 diff를 검토한 뒤 module gitlink, AGENTS 관리 블록, 적용된 CORE/스킬,
config, STATE, MODULE, wrapper/runtime을 **하나의 변경 세트로 커밋**하십시오.
다른 개발자는 부모 프로젝트에 기록된 버전을 받으면 됩니다.

```sh
git clone --recurse-submodules <YOUR_PROJECT_URL>
# 이미 clone한 프로젝트에서 부모 프로젝트의 기록된 포인터를 초기화/맞출 때:
git submodule update --init -- .universal-harness/module
./.universal-harness/harness status
```

`git submodule update --init`은 부모에 고정된 commit을 받는 작업이고,
`harness pull/upgrade`는 설정한 upstream 후보를 새로 선택하는 작업입니다.
부모 `git pull`만 했는데 submodule checkout이 따라오지 않은 상태는 status에서 구분합니다.
자동 pull hook, watcher, 예약 작업, 서명 검증, 패키지 레지스트리 배포는 포함하지 않습니다.

## 검증 범위

`tests/test_lifecycle.py`는 외부 네트워크 대신 임시 Git 저장소와 **실제 submodule/Git/설치기**를
사용합니다. wrapper 경로, 채널 선택, 도메인 보존, 충돌, dry-run, 중단/복구, 부모 index 보존과
전체 배포물 smoke test를 검사합니다. 로컬 source가 부분 복원본일 때 전체 배포물 검사는 skip하며,
전체 저장소 CI에서는 실제 manifest/스킬/도구 파일로 검사합니다.
[별도의 행동 시나리오](../evals/lifecycle-cases.json)는 실행 결과가 아닙니다.
GitHub 원격 인증, 모든 파일시스템 장애, 실제 Sol/Astra의 지침 로딩은 별도 검증 대상입니다.
