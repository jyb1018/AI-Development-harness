# 출처 및 설계 선택

확인일: 2026-09-14. 아래는 참고 출처이며 자동으로 내려받는 의존성이 아닙니다.
스킬 본문은 이 저장소에 맞춰 새로 작성했습니다. 원본 소스·예제·훅을 vendoring하지 않았습니다.
따라서 upstream 업데이트가 이 패키지 동작을 몰래 바꾸지 않습니다.

| 출처 | 확인한 내용 | 2.0에서의 사용 |
|---|---|---|
| [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) | 가정 확인, 단순성, 좁은 변경, 목표 기준 실행 | 핵심 + `uh-karpathy`; 사소한 불확실성마다 질문/정지하는 방식은 채택하지 않음 |
| [yshms/karpathy-claude-skills](https://github.com/yshms/karpathy-claude-skills) | 제3자의 정리이며 Karpathy 공식 스킬이 아님을 명시 | 출처/해석/프로젝트 자체 규칙을 구분 |
| [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | 재사용·최소 구현, 안전성을 줄이지 않는 최소주의 | `uh-ponytail`; 원본의 모드·명령·훅·벤치마크 수치는 가져오지 않음 |
| [obra/superpowers](https://github.com/obra/superpowers) | 조합 가능한 스킬 기반 개발 방법론; 계획, TDD, 하위 에이전트 및 리뷰 흐름 | 디버깅·TDD·검증·리뷰 개념만 선택; 전체 방법론은 설치하지 않음 |
| [OpenAI GPT-5.6](https://openai.com/index/gpt-5-6/) | 모델 계열과 도구/병렬 작업 기능 | 도구 가용성을 확인하고 독립된 작업에만 위임 |
| [OpenAI GPT-6 Astra](https://openai.com/index/gpt-6-astra/) | Astra 기능 및 코딩/도구 사용 | 모델 이름에 맞춘 고정 역할극 대신 실제 목표와 검증 유지 |
| [OpenAI Model guidance](https://developers.openai.com/api/docs/guides/latest-model) | Astra의 지침 민감도, 질문/후속 실행, 마이그레이션 지침 | 충돌 지침 감사, 승인 범위 내 지속, 모델/effort 분리 평가 |
| [Codex Build skills](https://developers.openai.com/codex/build-skills) | 호스트의 스킬 형식/사용 | SKILL.md 패키징; 호스트별 활성화 여부는 별도 확인 |
| [Codex AGENTS.md](https://developers.openai.com/codex/agent-configuration/agents-md) | 프로젝트/상위 지침의 로딩 | 핵심 파일을 하나로 통합하고 기존 지침을 보존 |

README 참조 blob 식별자(공급망 pin이 아니라 당시 읽은 자료의 식별):
- Karpathy: `7cf07a786532bebe01c65179c8e2c3a98cc0a09b`
- yshms: `d46c96def18ef362d7958ce273eded86f40dfc0b`
- Ponytail: `50b33a736986b43a8d1f666a6e3389fcab99997c`
- Superpowers: `09a91c6d03cfa3d874c5c33b6f8cc3d0b2d89645`

Karpathy는 사람의 이름이고 위 프로젝트들은 제3자의 해석입니다. 이 패키지는 어느 쪽의 공식 배포도 아닙니다.
향후 원본 내용을 직접 복사한다면 해당 revision과 라이선스·저작권 고지를 별도로 보존해야 합니다.
공식 문서도 URL이 같아도 캐시/시점이 다를 수 있으므로, 실제 모델 ID·호스트 버전은 실행 환경에서 확인합니다.
