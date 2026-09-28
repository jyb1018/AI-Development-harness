# Changelog

## Unreleased

### 프로젝트 소유 AGENTS와 관리 블록

- AGENTS 전체 소유권을 작은 bootstrap 블록의 SHA-256 소유권으로 바꿉니다.
  범용 본문은 `.universal-harness/CORE.md`에 설치하고 프로젝트 지침은 바이트 단위로 보존합니다.
- 기존 schema 2의 수정되지 않은 전체 파일은 `--upgrade`로 이관합니다.
  사용자 수정/옛 proposal 병합은 수동 분리 후 정확한 블록만 `--adopt-agents-block`으로 등록합니다.
- 새 STATE schema 3으로 구버전 설치기의 잘못된 재적용을 차단합니다. manifest와 VERSION은 유지합니다.
- 마커 중복·손상·코드 예제, 블록 수정/삭제, CORE 충돌, LF/CRLF/BOM, 동시 수정과 dry-run을 검사합니다.
  프로젝트 영역 편집은 정상 업데이트를 막지 않습니다. 기존 proposal 파일은 삭제하지 않습니다.
- 프로젝트 도메인·승인 경계의 우선 설명과 관련 문서만 읽는 라우팅을 명시합니다.
  실제 호스트의 CORE 로딩/모델 행동 검증은 별도이며 전역 설정이나 다른 프로젝트를 변경하지 않습니다.

### Human Context Layer

- 개발자의 ONBOARD/CATCH-UP/DEEP-DIVE를 돕는 `uh-developer-context-sync`와
  독립적인 `uh-human-diagramming`을 선택형 스킬로 추가합니다.
- 다이어그램의 노드/화살표 근거, 전후 비교, 실패 지도, 읽는 법과 텍스트 대안을
  명시합니다. 설명 생성과 사용자 확인 기준점은 분리하며 상태 저장은 선택 사항입니다.
- 기존 라우터에 `human-diagrams`와 로컬 Mermaid CLI 후보를 추가합니다.
  자동 설치·브라우저 다운로드·외부 업로드 없이 부재/실패와 렌더링 증거를 구분합니다.
- 사용 가이드, 미실행 행동 시나리오 19개, 패키지/라우팅 회귀 테스트를 추가합니다.
  이 스킬 확장 자체는 모델 프로필·버전·지원 파일 매핑과 전역 설정을 변경하지 않습니다.
- 새 런타임, 정식 아키텍처 모델, 제3자 스킬 번들, 실제 모델/렌더러 인증은 포함하지 않습니다.

## 3.0.0 — 2026-09-26

- Add one optional `uh-tooling` skill, a capability catalog and a read-only doctor/router;
  keep the seven existing skills, model profiles, and v2 host evaluation cases intact.
- Distinguish global skill definitions, CLI presence, host-reported MCP/plugins,
  authentication and actual execution evidence. No automatic upstream installation.
- Detect same-name skills by frontmatter across project/global roots, including
  identical definitions, variants and symlink aliases. Never delete user skills.
- Preflight collisions with packaged uh-* skills and install portable tooling support
  files using the existing ownership-hash/atomic-write mechanism. Keep schema 2
  for installer-state compatibility and preserve user edits.
- Add explicit task-specific fallbacks, graph freshness/egress/browser/review boundaries,
  migration guidance, twelve unevaluated behavior scenarios and deterministic tests.
- No merge/release/deploy, global config mutation, paid scan or Sol/Astra behavior
  certification is implied by this release of instructions.

## 2.0.2 — 2026-09-20

- Add a structured behavioral run record that separates model/effort, exact host
  patch version and platform, request-affecting effective config, harness/project
  revisions, permissions/tools, and observed results.
- Add fixed host regression cases for reasoning-summary defaults, native
  empty-continuation blocking, native verification, instruction/skill lifecycle,
  mid-flight authorization revision, and compaction/resume continuity.
- Validate the run-record contract and required host regression case inventory in CI.
- Clarify that host/runtime regressions must be isolated before changing the common
  core or model profiles. No Sol/Astra profile behavior change.

## 2.0.1 — 2026-09-14

- Fix fresh installation from the published source tree, which lacked the hidden
  `.agents/skills` payload. Restore all seven original v2 skills unchanged under
  visible `skills/`; install them into the target's `.agents/skills/` as before.
- Preflight source completeness and explain clone/ZIP versus patch-only usage
  before writing any target files. Installation does not require prior skills,
  a v1 harness, Git history, or running from a particular working directory.
- Restore the omitted validation workflow and ignore file. Add CLI regression
  coverage for all profiles, visible-only copies, extracted ZIPs, missing payload,
  and existing-install compatibility. No model-policy/profile changes.

## 2.0.0 — 2026-09-14

- First repository release; replaces the earlier 1.0.0 conversation ZIP design.
- One compact consumer policy, shared by Sol and Astra, with optional named profiles.
- Seven namespaced, independently written skills; explicit Karpathy/Ponytail/Superpowers provenance.
- No universal full-Superpowers auto-trigger, mandatory multi-agent chain, or per-commit stop.
- Clarification depends on decision impact; test corrections are allowed with contract evidence.
- Completion distinguishes source, local integration, deployed verification, and release.
- Safe installer: dry-run, update ownership hashes, symlink rejection, collision detection, existing AGENTS preservation.
- Separate package regression tests from unevaluated model-behavior cases.
- Replaces v1's coarse hash/issue watcher design with an explicit semantic review scheduling contract.
- Preserves the repository's existing LICENSE; does not import private project material.

## 1.0.0 — prior conversation package

Not a prior commit of this repository. Original ZIP used seven broad skills,
a larger core, a shell installer, and a document-fingerprint GitHub watcher.
No claim is made that its model behavior or live watcher was validated.
