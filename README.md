# Shop AI Backend Mock

GitHub から clone / download 後にすぐ起動できる、Android フロント接続用のモックバックエンドです。

## API
- `POST /api/v1/chat`
- `POST /api/v1/staff-call`
- `GET /health`
- `GET /docs`
- `GET /redoc`
- `GET /openapi.json`

## すぐ起動する方法

### Linux / Ubuntu / Proxmox VM
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
git clone <YOUR_REPO_URL>
cd shop_ai_backend_mock
./setup.sh
./start.sh
```

### ZIP を展開した場合
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip unzip
unzip shop_ai_backend_mock_github_ready.zip
cd shop_ai_backend_github_ready
./setup.sh
./start.sh
```

## Docker で起動する方法
```bash
docker compose up --build
```

## アクセス
- Swagger UI: `http://<server-ip>:8080/docs`
- ReDoc: `http://<server-ip>:8080/redoc`
- OpenAPI JSON: `http://<server-ip>:8080/openapi.json`

## Android の baseUrl
```kotlin
private const val BASE_URL = "http://<server-ip>:8080/"
```

## ヘッダー
```text
X-Device-ID: tablet-001
Content-Type: application/json
```

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

## モック分岐
- 「営業時間」→ structured モック
- 「トイレ」「お手洗い」→ structured モック
- 「スタッフ」「店員」「呼んで」「来て」または `is_staff_call=true` → staff handoff モック
- `question_level=MEDIUM` → RAG モック
- `question_level=HARD` → deep LLM モック
- その他 → fast LLM モック
