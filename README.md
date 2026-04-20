# Shop AI Backend

店舗設置型 AI アシスタント バックエンド。Android フロントエンドから接続し、
Structured Search / RAG / Local LLM を組み合わせた応答を返します。

## API
- `POST /api/v1/chat`
- `POST /api/v1/staff-call`
- `GET /health`
- `GET /docs`
- `GET /redoc`
- `GET /openapi.json`

## アーキテクチャ

```
FastAPI
  ├─ ChatOrchestrator
  │    ├─ PolicyService        (pre/final check)
  │    ├─ SessionService       (sessions 永続化)
  │    ├─ StructuredSearchService (locations / products / faq_structured)
  │    ├─ RagService           (document_chunks + fast_llm)
  │    └─ LlmDispatcher        (fast / deep node 呼び分け)
  └─ StaffCallService          (staff_calls 永続化)

PostgreSQL: sessions / question_logs / staff_calls /
            locations / products / inventories / faq_structured /
            documents / document_chunks

Fast LLM Node  (RTX 5080)  → OpenAI 互換 /v1/chat/completions
Deep LLM Node  (mac mini)  → OpenAI 互換 /v1/chat/completions
```

## 起動方法

### Docker Compose（推奨）
```bash
docker compose up --build
```
PostgreSQL と API がまとめて起動し、初回起動時にテーブル作成＋シードデータ投入まで行われます。

### ローカル（Python venv）
```bash
./setup.sh
# .env で POSTGRES_DSN など環境変数を設定
./start.sh
```

## 設定（環境変数）

| Key | 用途 |
|-----|------|
| `POSTGRES_DSN` | 例: `postgresql+asyncpg://shopai:shopai@db:5432/shopai` |
| `LOCAL_FAST_LLM_BASE_URL` | Fast LLM ノード（RTX 5080）のベースURL |
| `LOCAL_FAST_LLM_MODEL`    | Fast LLM モデル名 |
| `LOCAL_DEEP_LLM_BASE_URL` | Deep LLM ノード（mac mini）のベースURL |
| `LOCAL_DEEP_LLM_MODEL`    | Deep LLM モデル名 |
| `ALLOWED_ORIGINS` | CORS 許可オリジン（カンマ区切り） |

## ルーティング仕様（ChatOrchestrator）

| Route | 条件 |
|-------|------|
| `staff_handoff` | `is_staff_call=true` または「スタッフ/店員/呼んで/来て」を含む |
| `structured`    | 「営業時間/トイレ/レジ/売り場/在庫」等のキーワード |
| `rag`           | 「返品/交換/ルール/FAQ」等のキーワード、または `question_level=MEDIUM` |
| `deep_llm`      | `question_level=HARD` |
| `fast_llm`      | 上記以外 |

追加で、precheck / final_check により医療・法的断定、危険表現、個人情報要求は
`safe_fallback` に倒して回答します。

## chat のサンプル
```bash
curl -X POST "http://localhost:8080/api/v1/chat" \
  -H "Content-Type: application/json" \
  -H "X-Device-ID: tablet-001" \
  -d '{
    "messages": [{"role": "user", "content": "営業時間を教えてください"}],
    "model": "shopai-auto",
    "stream": false,
    "device_id": "tablet-001",
    "location_id": "odaiba-branch",
    "language_code": "ja",
    "session_id": "sess-test-001",
    "is_new_session": true,
    "is_staff_call": false,
    "question_level": "EASY",
    "timestamp": 1712497200000,
    "metadata": {"app_version": "1.0.0"}
  }'
```

## Android baseUrl
```kotlin
private const val BASE_URL = "http://<server-ip>:8080/"
```

## ヘッダー
```text
X-Device-ID: tablet-001
Content-Type: application/json
```
