# SƠ ĐỒ KỸ THUẬT — Mini Tool Quản lý Thu Mua
## (Bản vẽ chuẩn — kỹ thuật đọc được, người ngoài cũng hiểu được)

| | |
|---|---|
| **Phiên bản** | v1.0 |
| **Ngày** | 2026-07-08 |
| **Chuẩn dùng** | Mermaid (diagram-as-code) — render trên GitHub / VS Code / Mermaid Live; dạng chữ ai cũng đọc được |
| **Đi kèm** | [technical-design.md](technical-design.md) · [quy-trinh-tai-lieu.md](quy-trinh-tai-lieu.md) |

> 💡 Cách xem: mở file này trên **GitHub** hoặc **VS Code** (có extension Mermaid) sẽ thấy hình vẽ. Dán code vào **mermaid.live** để xem/xuất ảnh PNG cho slide/hợp đồng.

---

## 1. Sơ đồ kiến trúc hệ thống (Architecture)
*Người ngoài hiểu: trình duyệt → web → máy chủ xử lý → cơ sở dữ liệu.*

```mermaid
flowchart LR
    U["👤 Người dùng<br/>(trình duyệt)"]
    CF["☁️ Cloudflare Tunnel<br/>thumua.degoholding.vn"]
    WEB["🌐 Web / Nginx<br/>React (giao diện)"]
    API["⚙️ API — FastAPI<br/>(xử lý nghiệp vụ)"]
    DB[("🗄️ MariaDB<br/>DB: procurement")]

    U -->|HTTPS| CF --> WEB
    WEB -->|gọi API /api/...| API
    API -->|SQLAlchemy| DB
    API -.->|JWT + Fernet| API
```

---

## 2. Bản đồ chức năng theo vai trò (Use-case)
*Người ngoài hiểu: ai làm được việc gì trong hệ thống.*

```mermaid
flowchart LR
    R1(["👤 Người yêu cầu"])
    R2(["🛒 Nhân sự thu mua"])
    R3(["👔 Quản lý thu mua"])
    R4(["🔧 Admin"])

    R1 --- U1["Tạo Yêu cầu khảo sát"]
    R1 --- U2["Xem kết quả & chọn Phương án"]
    R1 --- U3["Tạo Yêu cầu mua"]

    R2 --- U4["Khảo sát NCC & Sản phẩm"]
    R2 --- U5["Tạo Option cho từng dòng"]
    R2 --- U6["Lập Đơn mua hàng (PO)"]
    R2 --- U7["Nhận hàng"]

    R3 --- U8["Duyệt / Phân bổ NSTM"]
    R3 --- U9["Chốt hoàn thành khảo sát"]
    R3 --- U10["Duyệt PO / Thanh toán"]

    R4 --- U11["Phân quyền & cấu hình"]
    R4 --- U12["Toàn quyền dữ liệu"]
```

---

## 3. Luồng nghiệp vụ end-to-end (theo vai trò) ⭐
*Đây là "bản vẽ xây nhà" chính. Mỗi khung là một vai trò.*

```mermaid
flowchart TD
    subgraph YC["👤 Người yêu cầu"]
        A["① Tạo Yêu cầu khảo sát"]
        E["③ Xem kết quả<br/>(ẩn NCC) → chọn Phương án"]
        G["④ Tạo Yêu cầu mua (PR)"]
    end
    subgraph SYS["⚙️ Hệ thống"]
        B["Tự gán NSTM<br/>theo phân loại"]
    end
    subgraph TM["🛒 Nhân sự thu mua"]
        C["② Khảo sát NCC & Sản phẩm"]
        D["Tạo Option (phương án)<br/>cho từng dòng đã duyệt"]
        I["⑤ Lập Đơn mua hàng (PO)"]
        J["⑥ Nhận hàng"]
    end
    subgraph QL["👔 Quản lý thu mua"]
        F["Chốt hoàn thành khảo sát"]
        H["Hoàn thành phiếu YCKS"]
        M["⑨ Yêu cầu thanh toán"]
    end

    A --> B --> C --> D --> F --> E --> G --> H --> I --> J
    J --> K["⑦ Tồn kho (+)"]
    J --> L["⑧ Công nợ<br/>(tiền hàng + vận chuyển)"]
    L --> M
```

---

## 4. Vòng đời trạng thái — Yêu cầu khảo sát (State machine)
*Người ngoài hiểu: phiếu đi qua những trạng thái nào, ai bấm nút gì để chuyển.*

```mermaid
stateDiagram-v2
    [*] --> draft: Tạo mới
    draft --> submitted: Gửi duyệt
    submitted --> approved: Quản lý duyệt
    approved --> processing: (tự động) Đang xử lý
    submitted --> rejected: Từ chối
    rejected --> submitted: Sửa & gửi lại
    processing --> survey_done: Chốt hoàn thành (mỗi dòng ≥1 option)
    survey_done --> pr_created: Người YC tạo Yêu cầu mua
    pr_created --> done: Quản lý hoàn thành
    done --> [*]

    note right of processing
        NSTM tạo Option ở
        processing hoặc survey_done
    end note
```

---

## 5. Vòng đời trạng thái — Đơn mua hàng (PO)
*Người ngoài hiểu: đơn hàng từ nháp đến nhận đủ.*

```mermaid
stateDiagram-v2
    [*] --> draft: Tạo PO
    draft --> submitted: Gửi duyệt
    submitted --> approved: Duyệt
    approved --> partial: Nhận một phần
    partial --> received: Nhận đủ
    approved --> received: Nhận đủ 1 lần
    draft --> cancelled: Hủy
    submitted --> cancelled: Hủy
    approved --> cancelled: Hủy
    received --> [*]
    cancelled --> [*]
```

---

## 6. Mô hình dữ liệu (ERD — Entity Relationship)
*Kỹ thuật đọc: các bảng và quan hệ. `||--o{` = một–nhiều.*

```mermaid
erDiagram
    SURVEY_REQUEST  ||--o{ SR_LINE          : "gồm nhiều dòng"
    SR_LINE         ||--o{ SR_OPTION        : "có nhiều option"
    SR_OPTION       }o--|| SUPPLIER         : "thuộc 1 NCC"
    SR_OPTION       }o--|| SURVEY           : "chụp từ phiếu KS"
    SURVEY          ||--o{ SURVEY_PROD_LINE : "gồm dòng SP"
    SR_LINE         ||--o| PURCHASE_REQUEST : "sinh ra PR"
    PURCHASE_REQUEST||--o{ PURCHASE_ORDER   : "tạo PO"
    PURCHASE_ORDER  ||--o{ PO_ITEM          : "gồm dòng hàng"
    PO_ITEM         }o--|| PRODUCT          : "là sản phẩm"
    PO_ITEM         ||--o{ PO_DELIVERY      : "giao nhiều lần"
    PO_DELIVERY     ||--o| GOODS_RECEIPT    : "sinh phiếu nhập"
    GOODS_RECEIPT   ||--o{ INVENTORY        : "cộng tồn"
    PURCHASE_ORDER  ||--o{ PAYABLE          : "sinh công nợ"
    PAYABLE         }o--o{ PAYMENT_REQUEST  : "gom vào phiếu TT"
    SUPPLIER        ||--o{ PURCHASE_ORDER   : "bán hàng"

    SURVEY_REQUEST {
        string code "YCKS + DDMMYY + seq"
        string requester
        string department
        string status "draft..done"
        int assignee_id "NSTM chính"
    }
    SR_LINE {
        string internal_line_code "ẩn với người YC"
        string item_group "phân loại"
        decimal request_qty
        string assignee "NSTM dòng"
        bool is_completed
        string pr_code "PYC sinh ra"
    }
    SR_OPTION {
        int public_id "ID ẩn danh (Option 1,2..)"
        bool is_chosen
        string supplier_code "ẩn với người YC"
        string snap_product_name "snapshot"
        decimal snap_price_by_volume
        decimal snap_shipping_cost
    }
    SUPPLIER {
        string code
        string name
        string supplier_type "goods / shipping"
    }
    PRODUCT {
        string code "Mã VTBB/NL"
        string name
        string hh_code "Mã HH (liên kết)"
        string hh_name "Tên SP (HH)"
        string item_group "Phân loại"
        string unit "ĐVT"
    }
    PURCHASE_REQUEST {
        string code "PYC"
        string supplier_code
        string status
    }
    PURCHASE_ORDER {
        string code "PO"
        string pr_code "nguồn PYC"
        string supplier_code
        int company_id "pháp nhân"
        string order_date
        decimal vat_rate
        string status "draft..received"
    }
    PO_ITEM {
        string product_code
        string fg_code "Mã HH"
        string fg_name "Tên HH"
        decimal qty_order
        decimal qty_received
        decimal price
        string line_status
    }
    PO_DELIVERY {
        int delivery_no "lần giao"
        string carrier_code "đơn vị VC"
        decimal ship_qty
        decimal received_qty
        string received_date
        decimal shipping_amount
    }
    GOODS_RECEIPT {
        string warehouse_code
        decimal qty
        string received_date
    }
    INVENTORY {
        string product_code
        string warehouse_code
        decimal qty_on_hand
    }
    PAYABLE {
        string supplier_code
        string kind "hàng hóa / vận chuyển"
        decimal amount
        string due_date
    }
    PAYMENT_REQUEST {
        string code
        string supplier_code
        decimal total
    }
```

---

## 7. Trình tự "Nhận hàng → Tồn kho + Công nợ" (Sequence)
*Kỹ thuật đọc: vì sao một thao tác nhận hàng lại tự sinh cả tồn kho lẫn công nợ.*

```mermaid
sequenceDiagram
    actor NSTM as 🛒 NSTM
    participant API as API (PO nhận hàng)
    participant POS as po_service.recompute_effects
    participant GR as Goods Receipt
    participant INV as inv_service (Tồn kho)
    participant PAY as pay_service (Công nợ)

    NSTM->>API: Xác nhận đã nhận (delivery)
    API->>POS: recompute_effects(po, user)
    POS->>GR: sinh phiếu nhập kho
    POS->>INV: apply_delivery() → cộng tồn
    POS->>PAY: upsert() luồng 1 — tiền hàng
    POS->>PAY: upsert() luồng 2 — tiền vận chuyển
    POS-->>API: hoàn tất (đồng bộ)
    API-->>NSTM: Tồn kho & Công nợ đã cập nhật

    Note over POS,PAY: KHÔNG ghi thẳng delivery mà bỏ qua<br/>recompute_effects (sẽ mất tồn/công nợ)
```

---

## 8. Luồng chi tiết: Yêu cầu khảo sát 5A → 5D (có điểm quyết định)
*Chi tiết hơn sơ đồ 3 — thể hiện nhánh duyệt / trả lại và ai làm ở bước nào.*

```mermaid
flowchart TD
    A["Người YC tạo YCKS"] --> B{"Trưởng phòng/QL<br/>duyệt?"}
    B -- "Từ chối" --> A2["Trả lại + lý do"] --> A
    B -- "Duyệt" --> C["Hệ thống tự gán NSTM<br/>theo phân loại từng dòng"]
    C --> D["NSTM khảo sát NCC & SP"]
    D --> E["NSTM tạo Option cho<br/>từng dòng ĐÃ DUYỆT"]
    E --> F{"Mỗi dòng có ≥1 option?"}
    F -- "Chưa" --> E
    F -- "Đủ" --> G["QL chốt: survey_done"]
    G --> H["Người YC xem kết quả<br/>(ẩn NCC) chọn Phương án"]
    H --> I["Gom option đã chọn<br/>theo NCC → PYC nháp"]
    I --> J["QL/Admin: Hoàn thành (done)"]
```

---

## 9. Luồng công nợ & thanh toán (2 luồng)
*Vì sao mỗi lần nhận hàng lại sinh 2 khoản nợ, rồi gom thành phiếu thanh toán.*

```mermaid
flowchart LR
    R["Nhận hàng<br/>(1 lần giao)"] --> P1["Công nợ — Tiền hàng<br/>(SL nhận × đơn giá + VAT)"]
    R --> P2["Công nợ — Vận chuyển<br/>(phí VC của lần giao)"]
    P1 --> AG["Gộp theo NCC"]
    P2 --> AG
    AG --> PR["Yêu cầu thanh toán<br/>(1 NCC/phiếu, gom nhiều PO)"]
    PR --> PRINT["In phiếu / trình duyệt"]
```

---

## 10. Ghi chú cho người đọc

- **Sơ đồ 1–5, 8, 9** dễ cho **người ngoài** (phòng Thu mua) đọc để nắm luồng & quyết định.
- **Sơ đồ 6–7** thiên về **kỹ thuật** (data model đầy đủ + trình tự xử lý).
- Mọi sơ đồ khớp hệ thống thật (trạng thái, bảng, hàm đúng tên). Khi luồng đổi → cập nhật sơ đồ **kèm Change Request** trong [change-log.md](change-log.md).

*Hết. Chi tiết mô tả xem [technical-design.md](technical-design.md).*
