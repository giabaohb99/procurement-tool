# AGENT HUB — QUY TRÌNH VÀ SƠ ĐỒ BOT TRỢ LÝ

**Bản 1.0 · 05/10/2026 · ai-CR-065.** Tài liệu tổng hợp một chỗ: bot gồm những phần nào, nằm ở đâu, ai được
làm gì, và từng luồng chạy ra sao. Chi tiết từng phần xem: thiết kế [`01`](./01-thiet-ke-ky-thuat.md),
danh sách tính năng + lộ trình [`04`](./04-danh-sach-tinh-nang.md), máy sửa mã [`05`](./05-may-sua-ma.md),
cổng MCP [`06`](./06-cong-mcp.md).

Ký hiệu trạng thái: **[chạy]** đã chạy trên dev · **[làm]** đã chốt thiết kế, đang/sắp làm · **[sau]** để sau.

---

## 1. Ý tưởng một câu

Có **một bot tổng** (VPS 1) nói chuyện với mọi người và gọi mọi công cụ ERP; **riêng việc sửa mã** thì bot tổng
không tự làm mà **giao xuống bot code** (VPS 2), nơi duy nhất có Claude Code và khóa GitHub. Bot code sửa, kiểm,
dựng bản xem thử; đại ca thử xong thì ra lệnh đẩy lên dev hoặc prod. Thêm máy, thêm môi trường chỉ là thêm dòng
trong sổ, quy trình không đổi — kể cả khi bot tự sửa chính nó.

## 2. Sơ đồ tổ chức

```mermaid
flowchart TB
    subgraph NGUOI["Người dùng"]
        DC["Đại ca<br/>(chủ hệ thống)"]
        CQ["Người được cấp quyền sửa mã<br/>(sổ K-01)"]
        NV["Nhân viên đã đăng nhập bot"]
    end

    subgraph KENH["Kênh"]
        TG["Telegram — bot Lạc Lạc [chạy]"]
        WEB["Trợ lý AI trên web ERP [chạy]"]
        MCP["Cổng MCP — Claude Desktop, Cursor… [chạy]"]
        ZL["Zalo OA [sau]"]
    end

    subgraph VPS1["VPS 1 — BOT TỔNG (server dev, sau này cả prod)"]
        POL["agent-poller<br/>nhận tin Telegram"]
        API["api ERP<br/>Trợ lý AI · cổng MCP · trang cá nhân"]
        WK["celery-worker + beat<br/>gom việc · lập kế hoạch · chuông · nhắc · bản tin"]
        SO["Sổ của bot (MySQL dev)<br/>việc · quyền · máy · khóa · nhật ký"]
        RD["Redis — hàng đợi agent_code.&lt;máy&gt;"]
        TOOLS["Công cụ ERP (45 tool)<br/>tra cứu · tạo phiếu · báo cáo · hải quan · Lịch/Drive"]
    end

    subgraph VPS2["VPS 2 — BOT CODE (tạm thời: máy đại ca)"]
        TUN["Đường hầm SSH lên VPS 1"]
        RUN["agent-runner<br/>Claude Code (gói riêng) · git · cổng kiểm"]
        WT["Worktree từng việc<br/>bot/AI-xxxx"]
        PRE["Preview đầy đủ từng việc [làm]<br/>be + fe + worker + redis + mysql + qdrant riêng"]
        CF["Cloudflare Tunnel [làm]<br/>ai-xxxx.preview.&lt;tên miền&gt;"]
    end

    GH["GitHub<br/>nhánh bot/* · erp-v2 · main"]
    DEV["Môi trường DEV<br/>deverp / devthumua"]
    PROD["Môi trường PROD<br/>erp / thumua"]

    DC & CQ & NV --> TG & WEB & MCP
    TG --> POL --> WK
    WEB & MCP --> API --> TOOLS
    WK --> TOOLS
    WK --> SO
    WK -- "giao việc sửa mã" --> RD
    RUN -- "kéo việc qua" --> TUN --> RD
    RUN -- "ghi kết quả" --> TUN --> SO
    RUN --> WT --> PRE --> CF
    RUN -- "đẩy commit đã kiểm" --> GH
    GH -- "deploy.sh dev &lt;commit&gt; [làm]" --> DEV
    GH -- "deploy.sh prod &lt;commit&gt; + OTP [làm]" --> PROD
```

**Ai giữ chìa khóa gì**

| Nơi | Giữ | KHÔNG giữ |
|---|---|---|
| VPS 1 — bot tổng | Token Telegram, khóa Gemini cá nhân của từng người (mã hóa), token Google từng người (mã hóa), khóa MCP (băm) | Claude Code, khóa GitHub, khóa SSH prod |
| VPS 2 — bot code | Claude Code (tài khoản riêng của công ty), khóa GitHub chỉ đẩy `bot/*` + `erp-v2`, khóa SSH đường hầm (chỉ mở cổng), tài khoản MySQL `agent_runner` (chỉ bảng của bot) | Token Telegram, khóa Gemini, khóa SSH prod |
| Đại ca | Quyền duyệt cuối, mã xác nhận lên prod (OTP) | — |

## 3. Vai trò và quyền

| Ai | Làm được | Không làm được |
|---|---|---|
| **Nhân viên** đã `/dangnhap` | Hỏi Trợ lý dưới đúng quyền ERP của mình; tạo / gửi duyệt phiếu từ chat; nghiên cứu; nhắc việc; tin thoại; chuông; Lịch/Drive của mình; khóa MCP của mình; báo lỗi | Giao việc sửa mã; thấy dữ liệu ngoài quyền |
| **Người được cấp quyền** (đại ca nhắn «cho anh X quyền …») | Thêm: lệnh trên việc sửa mã theo cấp — *duyệt kế hoạch* (duyệt, sửa kế hoạch, làm tiếp, đóng) hoặc *gộp dev* (thêm gộp, deploy dev, thu hồi). Phải nêu mã việc | Lên prod; cấp quyền cho người khác |
| **Đại ca** | Mọi thứ; cấp/gỡ quyền; thêm/gỡ máy; thêm môi trường; duyệt thao tác trên VPS 1; lên prod (kèm OTP) | — |
| **Bot tổng** | Gọi công cụ ERP dưới quyền người hỏi; xếp việc; gửi tin | Sửa mã; chạy lệnh trên máy |
| **Bot code** | Sửa mã trong worktree; chạy kiểm; dựng preview; xin deploy | Tự sửa phần quyền / OTP / danh sách tệp cấm của chính nó; lên prod khi chưa duyệt |

## 4. Các luồng

### 4.1 Tin nhắn thường (hỏi, tạo phiếu, nhắc việc…) — [chạy]

```mermaid
flowchart LR
    A["Tin nhắn / tin thoại"] --> B{"Chat đã đăng nhập?"}
    B -- chưa --> B1["Nhắc lấy mã ở Trang cá nhân"]
    B -- rồi --> C{"Câu lệnh nhận ra ngay?<br/>(tạo · thôi · nhắc · chuông · tốn bao nhiêu · cấp quyền · máy…)"}
    C -- có --> C1["Làm ngay, không gọi AI"]
    C -- không --> D{"Có khóa Gemini cá nhân?<br/>Chưa chạm trần lượt/ngày?"}
    D -- không --> D1["Nói rõ lý do, chỉ cách gắn khóa"]
    D -- có --> E["Đọc ý định (Gemini, khóa của người đó)"]
    E -- hỏi --> F["Trợ lý ERP + 45 tool, đúng quyền người hỏi"]
    E -- tra cứu --> G["Nghiên cứu web / kiểm chứng"]
    E -- giao việc sửa mã --> H["Luồng 4.2 (chỉ đại ca + người có quyền)"]
    F --> F1{"Tool trả bản nháp phiếu?"}
    F1 -- có --> F2["Thẻ nháp → «tạo» / «tạo và gửi duyệt» → link phiếu"]
```

Chạy nền theo lịch (không cần ai nhắn): **chuông ERP** → Telegram mỗi phút; **lời nhắc** tới giờ; **bản tin sáng**
7h30 (lịch + việc chờ duyệt); **nhắc trước họp** 15 phút; **nhặt phiếu hỗ trợ** thành việc sửa mã.

### 4.2 Việc sửa mã — [chạy]

```mermaid
sequenceDiagram
    autonumber
    actor DC as Đại ca / người có quyền
    participant B1 as Bot tổng (VPS 1)
    participant B2 as Bot code (VPS 2)
    participant GH as GitHub
    participant ENV as Dev / Prod

    DC->>B1: «màn công nợ lọc sai ngày» (chữ, ảnh, thoại hoặc phiếu hỗ trợ)
    B1->>B1: Gom tin 30 giây, chấm việc NHỎ hay ĐẦY ĐỦ
    alt Việc đầy đủ
        B1->>B2: Rà soát mã thật (Opus)
        B2-->>B1: Phân tích
        B1->>B1: Lập kế hoạch (Gemini)
        B1->>DC: Thẻ kế hoạch
        DC->>B1: «duyệt»
    else Việc nhỏ (đường tắt)
        B1->>B1: Kế hoạch gọn, ≤3 tệp → tự duyệt
    end
    B1->>B2: Giao sửa mã (hàng đợi của máy)
    B2->>B2: Sửa trong worktree → cổng kiểm (pytest / typecheck / lint / vitest)
    B2->>GH: Đẩy nhánh bot/AI-xxxx
    B2->>B2: Dựng preview riêng của việc [làm]
    B2-->>B1: Thẻ kết quả + link preview
    B1->>DC: «AI-xxxx xong, xem thử: ai-xxxx.preview…»
    DC->>B1: «gộp và deploy dev AI-xxxx»
    B1->>B2: Xin gộp + deploy
    B2->>GH: Gộp vào erp-v2
    B2->>ENV: deploy.sh dev <commit> (khóa SSH khóa cứng) [làm]
    B2-->>B1: Ghi nhật ký deploy
    DC->>B1: «lên prod AI-xxxx» + OTP [làm]
    B1->>ENV: deploy.sh prod <commit> (từ VPS 1, không từ VPS 2)
```

Máy sửa mã tắt thì việc nằm chờ trong hàng đợi, bot báo «đang chờ máy X». Việc **dính máy** đã bắt đầu nó.
Model: việc nhỏ `claude-opus-5`, việc đầy đủ `claude-opus-5-5` (đặt trong `.env.runner`).

### 4.3 Bản xem thử (preview) — [làm]

- Mỗi việc kiểm xanh → một bộ stack ĐẦY ĐỦ riêng (backend, frontend, worker, redis, MySQL, qdrant) trên VPS 2, dữ
  liệu tự seed như local, địa chỉ `ai-xxxx.preview.<tên miền>` qua Cloudflare Tunnel.
- Máy hiện tại: 1 bộ một lúc. VPS preview riêng (8 vCPU / 16 GB): 2–3 bộ cùng lúc. Tự tắt khi việc đóng hoặc sau 24 giờ.
- **Để sau:** chép DB dev sang preview khi cần test với dữ liệu thật.

### 4.4 Bot code thao tác trên VPS 1 — [làm]

| Thao tác | Duyệt | Bảo vệ |
|---|---|---|
| Xem dữ liệu / log dev | Không | MySQL chỉ đọc, ghi nhật ký |
| Xem dữ liệu prod | «đúng» | Ghi nhật ký |
| Sửa dữ liệu / chạy lệnh dev | «đúng» | Thẻ hiện nguyên văn lệnh → **sao lưu trước** → chạy → nhật ký + **lệnh hoàn tác** |
| Mọi thay đổi prod | «đúng» + **OTP** | Như trên |

«hoàn tác thao tác #12» → bot chạy lệnh hoàn tác đã ghi. «lịch sử thao tác prod» → liệt kê.

### 4.5 Bot tự cải thiện — [chạy, thêm luật ở bước làm]

Mã của bot nằm cùng kho, nên «sửa bot» là một việc sửa mã như mọi việc khác (AI-0001 chính là bot sửa giao diện
của bot). Ba luật cứng thi hành trong mã: bot code **không** được sửa sổ quyền, phần OTP / lệnh lên prod, và danh sách
tệp cấm sửa; mọi thay đổi qua cổng kiểm + đại ca duyệt; lên prod luôn cần OTP.

### 4.6 Mở rộng — sổ môi trường và sổ máy

- **Sổ máy** [chạy]: «thêm máy của anh Được» · «máy nào đang bật» · «AI-0012 cho máy X làm» · «cho máy X được deploy».
- **Sổ môi trường** [làm]: «thêm môi trường staging: vps …, nhánh …, lệnh deploy …» → bot tổng ghi, truyền cho bot code
  mỗi lần giao việc. Thêm VPS thứ 3, 4 = thêm dòng.
- **Báo tài nguyên** [làm]: mỗi ngày RAM/CPU/đĩa từng máy, số việc, lượt Claude/Gemini, việc kẹt; hỏi «tình hình máy».

## 5. Trạng thái tổng (05/10/2026)

| Phase | Nội dung | Trạng thái |
|---|---|---|
| 0–2 | Bot sửa mã, đăng nhập, khóa cá nhân, bot lên dev, máy sửa mã tách rời, đường tắt | [chạy] |
| 3 | Chuông, nhắc việc, tin thoại, trần lượt | [chạy] |
| 4 | Cổng MCP | [chạy], chưa ai thử bằng ứng dụng thật |
| 5 | Google cá nhân: Lịch, Drive, bản tin sáng, nhắc họp | Mã đã lên dev; chờ đại ca: redirect URI, «In production», `GOOGLE_CLIENT_SECRET` |
| **6** | Quy trình code hai máy chủ (nhóm V): sổ môi trường, `deploy.sh` + nhật ký, thao tác VPS 1 có duyệt/sao lưu/hoàn tác, OTP, 3 luật, báo tài nguyên, preview | [làm] — tiếp theo |
| **7** | Tự vận hành (nhóm O): theo dõi sức khỏe, tự chẩn đoán, tự khôi phục dev, prod chỉ đề xuất, sổ sự cố | [làm] sau phase 6 |
| **8** | Lõi mở: gọi MCP bên ngoài, A2A giữa các bot, giao việc tính ngân sách, sổ sự kiện chung | [sau] |
| 9 | Zalo OA, nhiều bot | [sau] — chờ OA + tên bot |
| 10 | Thư ký biên bản họp | [sau] — chờ tệp ghi âm thật |

## 6. Đối chiếu với các mô hình bên ngoài (05/10/2026)

Mô hình của hệ là **orchestrator – worker** (điều phối – thực thi), một trong các mẫu trong bài «Building Effective Agents»
của Anthropic, đi cùng **tool calling / MCP** (agent dùng công cụ) và sắp tới **A2A** (agent nói chuyện với agent). Hệ là
**agentic**: tự lên kế hoạch, gọi công cụ, làm nhiều bước. Nguyên tắc: **chỉ học ý tưởng, không clone thay lõi** — phần
khó nhất (quyền ERP từng người, phạm vi dữ liệu, khóa cá nhân, sổ việc, chi phí) các khung chung không có.

| Tiêu chí | Thông lệ ở các khung mở (mcp-agent, Agent Swarm, cli-agent-orchestrator, OpenAI Agents SDK) | Hệ mình |
|---|---|---|
| Điều phối – thực thi | Lead / supervisor giao cho worker | Có: bot tổng → bot code, sổ máy, việc dính máy |
| Công cụ qua chuẩn chung | MCP client gọi công cụ ngoài | Một nửa: có cổng MCP **mở ra** (`06`); **gọi vào** công cụ MCP ngoài chưa có → M-09 |
| Agent nói chuyện với agent | A2A | Chưa; đang dùng hàng đợi Redis tự viết → N-06 |
| Người duyệt ở chỗ nguy hiểm (HITL) | Cổng duyệt trong luồng | Có: duyệt kế hoạch, gộp, sổ quyền; thêm OTP prod + duyệt thao tác → V-03, V-04 |
| Worker cách ly | Docker / worktree riêng từng việc | Có: worktree riêng, runner không giữ token bot; preview riêng → V-07 |
| Theo dõi, truy vết | Sổ sự kiện / trace | Có sổ tin + sổ lượt chạy; gom một khuôn → N-08 |
| Ngân sách | Theo dõi token, chặn khi quá | Có trần lượt/ngày theo người, báo chi phí; giao việc theo ngân sách → N-07 |
| Tự vận hành | Ít khung có sẵn | Chưa → nhóm O |
| Quyền theo người dùng thật | Hầu như không có | **Có — điểm mạnh riêng** (chạy dưới quyền ERP của từng người, khóa cá nhân) |

Giấy phép khi mượn mã: MIT / Apache 2.0 dùng được (giữ giấy phép, ghi nguồn); **AGPL tránh**; kho không ghi giấy phép
chỉ đọc để học.
