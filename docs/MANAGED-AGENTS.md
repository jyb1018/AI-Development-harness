# AGENTS.md: 프로젝트 소유 영역과 하네스 관리 블록

`AGENTS.md`는 프로젝트 지침입니다. 설치기가 소유하는 것은 파일 전체가 아니라
`UNIVERSAL-HARNESS:BEGIN`과 `UNIVERSAL-HARNESS:END` 사이의 작은 bootstrap뿐입니다.
도메인 불변조건, 승인 경계, 아키텍처 제약, 검증 명령과 문서 라우팅은 블록 밖에 둡니다.

## 설치 후 구조

```text
AGENTS.md                         프로젝트 소유
  ├─ 프로젝트 도메인/승인/라우팅     설치기가 수정하지 않습니다.
  └─ 하네스 bootstrap 관리 블록      독립 해시로 보호합니다.
       ├─ .universal-harness/CORE.md
       └─ .universal-harness/profile.md
.universal-harness/STATE.json       설치 소유권만 기록합니다.
.agents/skills/uh-*/SKILL.md         기존 파일 단위 소유권을 유지합니다.
```

원본 `AGENTS.template.md`는 범용 core 계약을 계속 보관하지만, 대상에서는
`.universal-harness/CORE.md`로 설치됩니다. 새 `AGENTS.bootstrap.md`에는 관리 블록만 있습니다.
기존 루트 AGENTS에 처음 추가할 때는 **끝에 한 번 덧붙입니다.** 앞에 있는 YAML frontmatter,
UTF-8 BOM, 한국어, LF/CRLF, 마지막 줄바꿈의 유무를 임의 정규화하지 않습니다.
블록 위치를 옮겨도 내부 바이트를 유지하면 소유권 검사가 유효합니다.
하위 디렉터리의 `AGENTS.md`, override 파일, 전역 지침은 건드리지 않습니다.

## 도메인 지침의 예시

다음은 프로젝트가 실제로 채택한 경우에만 사용할 예시이며, 설치기가 생성하지 않습니다.

```md
# Project instructions

## Domain invariants
- 추론 결과로 정답 데이터를 덮어쓰지 않습니다.
- Detector와 Recognizer의 독립 교체 가능성을 유지합니다.

## Approval boundaries
- 모델 교체와 비용이 발생하는 평가 실행은 명시적 승인 후 수행합니다.

## Instruction routing
- 모델을 변경할 때는 docs/model-policy.md를 읽습니다.
- 데이터셋을 변경할 때는 docs/data-policy.md를 읽습니다.
- 서브시스템 경계를 변경할 때는 관련 아키텍처 문서와 ADR을 읽습니다.
```

하네스의 일반 기본값은 프로젝트의 구체적인 제약을 대체하지 않습니다. 동시에 저장소 문서가
호스트의 지침 우선순위를 정하거나 사용자 승인·안전 경계를 우회할 수는 없습니다.
`uh-developer-context-sync`는 이 프로젝트 소유 불변조건과 승인 경계를 우선 설명합니다.
함수 목록, 일시적인 TODO, 최근 커밋 요약까지 AGENTS에 누적하지 마십시오.

## 일반 설치와 업데이트

하네스를 처음 넣는 프로젝트는 기존 AGENTS 원문을 그대로 보존하고 관리 블록만 추가합니다.
기존 하네스 설치본은 아래 이관 분기를 적용하므로 먼저 dry-run으로 확인하십시오.

```sh
python3 /path/to/harness/scripts/install.py /path/to/project --profile astra --dry-run
python3 /path/to/harness/scripts/install.py /path/to/project --profile astra

python3 /path/to/harness/scripts/install.py /path/to/project --profile astra --upgrade --dry-run
python3 /path/to/harness/scripts/install.py /path/to/project --profile astra --upgrade
```

| 현재 상태 | 동작 |
|---|---|
| 새 프로젝트, AGENTS 없음 | bootstrap만 있는 AGENTS와 CORE를 설치합니다. |
| 하네스 설치 기록이 없는 기존 AGENTS | 기존 바이트를 보존하고 블록을 추가합니다. |
| 블록 소유권 기록이 일치함 | 블록만 갱신하고 양쪽의 프로젝트 영역을 그대로 둡니다. |
| 프로젝트 영역만 수정됨 | 정상 업데이트합니다. 해당 영역은 해시 관리 대상이 아닙니다. |
| 블록 수정·삭제·줄바꿈 재서식 | 충돌로 중단합니다. 새 버전과 우연히 같아도 소유권을 몰래 재설정하지 않습니다. |
| 중복·역순·잘못된 마커 또는 코드 예제 안의 마커 | 모호한 범위를 추측하지 않고 중단합니다. |
| 사용자 수정 CORE/스킬/support | 기존 파일 단위 충돌 보호를 유지합니다. |

## 예전 전체 파일 소유 방식에서 이관

기존 `STATE.json` schema 2를 읽되, 성공 후에는 **schema 3**을 기록합니다.
`harness.json`의 manifest schema와 VERSION은 이 PR에서 바꾸지 않습니다.

- 예전 설치기가 소유한 AGENTS 전체 해시가 현재 파일과 정확히 같으면 `--upgrade`로
  자동 이관합니다. 제거하는 것은 설치 당시 그대로인 범용 본문뿐입니다.
- 예전 전체 파일에 도메인 규칙을 추가하거나 고쳤다면 자동으로 분리하지 않습니다.
  어떤 문장이 사용자 지침인지 정규식이나 모델 추측으로 지우지 않습니다.
- 예전 `AGENTS.proposed.md` 방식의 설치도 수동 병합 여부를 알 수 없으므로 일회성
  검토를 요구합니다. 새 블록을 더해 범용 본문을 중복 활성화하지 않습니다.

충돌 출력에는 새 bootstrap 원문을 **화면으로만 제안**합니다. 충돌 시 proposal 파일,
AGENTS, CORE, 스킬, STATE를 새로 쓰거나 변경하지 않습니다.
필요한 도메인 지침을 보존하고 오래된 범용 하네스 본문만 수동으로 제거한 뒤,
[정확한 bootstrap 원본](../AGENTS.bootstrap.md)을 코드 펜스 밖에 한 번 넣으십시오.

```sh
python3 /path/to/harness/scripts/install.py /path/to/project \
  --profile astra --upgrade --adopt-agents-block --dry-run
python3 /path/to/harness/scripts/install.py /path/to/project \
  --profile astra --upgrade --adopt-agents-block
```

`--adopt-agents-block`는 force가 아닙니다. LF/CRLF 차이를 제외하고 **현재 배포본과 정확히
일치하는 단일 블록**만 새로 소유권 등록합니다. 다른 파일의 충돌은 우회하지 않습니다.
수동 정리를 완료했는지는 사람이 확인해야 합니다. 설치기는 도메인 문장의 의미를 판별하거나
블록 밖에 남은 예전 지침을 자동 삭제하지 않습니다.
기존 `AGENTS.proposed.md`는 그대로 남기되 새 STATE의 관리 목록에서는 제외합니다.

## 상태와 업데이트 안전성

새 상태에는 다음처럼 역할을 분리해 기록합니다. 아래 해시는 구조를 보여 주는 예시입니다.

```json
{
  "schema_version": 3,
  "core_status": "managed_block",
  "agents": {
    "mode": "managed_block",
    "sha256": "<BEGIN부터 END까지의 실제 바이트 해시>"
  },
  "files": {
    ".universal-harness/CORE.md": "<파일 전체 해시>"
  }
}
```

전체 `AGENTS.md` 해시는 `files`에 넣지 않습니다. 마커 자체는 보호 범위에 포함하고,
END 마커 뒤의 줄바꿈과 블록 밖 영역은 포함하지 않습니다. 다른 관리 파일은 기존 SHA-256
소유권 보호를 사용합니다. 상태 해시는 출처 서명이나 악의적인 변경을 막는 보안 경계가 아닙니다.

schema 2 전용 구버전 설치기는 schema 3을 거부하므로 잘못된 전체 파일 소유권으로 되돌아가지
않습니다. 되돌릴 때는 이전 관리 파일과 상태를 함께 검토해 복구하며, 나중에 추가한 프로젝트
지침을 잃지 않게 보존하십시오. STATE의 숫자만 2로 고쳐서 강제로 실행하지 마십시오.

모든 계획상 충돌은 쓰기 전에 확인하고, AGENTS의 동시 편집도 쓰기 전에 재확인합니다.
다만 기존과 같이 **파일별 atomic replace이지 전체 설치 트랜잭션은 아닙니다.** 디스크 오류나
중간 종료가 발생하면 일부 파일만 바뀔 수 있습니다. 재시도 전에 diff와 상태를 검토하고,
필요하면 정확한 bootstrap을 수동 확인·등록하십시오. 설치 중 편집과 병렬 설치는 피하십시오.

## 호스트 로딩 확인

Markdown의 파일 경로는 native include가 아닙니다. bootstrap은 에이전트에게 CORE와 profile을
실제로 읽도록 요청합니다. 설치 성공과 해당 호스트에서 실제로 읽혔다는 증거는 구분합니다.
새 세션에서 적용된 루트/하위 AGENTS와 override를 확인하고, CORE/profile 읽기가 관찰되는지
확인하십시오. 참조 파일이 없거나 읽을 수 없다면 없는 규칙을 지어내지 않고 누락을 알립니다.
프로젝트 문서와 선택형 스킬은 관련 작업에 필요한 것만 읽습니다.

## 제거

관리 블록과 STATE의 관리 파일 목록을 실제 diff와 비교해 수동 제거합니다.
**AGENTS.md 파일 전체를 삭제하지 마십시오.** 프로젝트 소유 지침과 관련 없는 파일은 남깁니다.
설치·제거는 다른 저장소, 전역 설정, 모델 실행, merge, 배포를 승인하지 않습니다.
