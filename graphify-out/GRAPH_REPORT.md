# Graph Report - backend  (2026-09-18)

## Corpus Check
- Large corpus: 906 files · ~3,531,449 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder.

## Summary
- 9586 nodes · 30108 edges · 417 communities (263 shown, 154 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 3251 edges (avg confidence: 0.95)
- Token cost: 129,871 input · 0 output

## Community Hubs (Navigation)
- Core Models & Base Mixins
- Document Access Control
- Audit, Scoping & Notification
- Doc Catalog Security Levels
- Document Controller & Sanitize
- Alembic Migrations (nhom 1)
- Alembic Migrations (nhom 2)
- Legacy Dat Xe Integration
- Approval Flow & Delegation
- Auth Tokens & Permissions
- Document Clone & Attachment Window
- Survey Request Controller
- Purchase Order & Payable
- Purchase Request Service
- Core Framework Utilities
- App Settings & File Access Log
- Work Controller (Kanban)
- Attachment Upload Guard
- Legacy Dat Xe Export Builder
- Employee Controller
- Work Group & Audit
- Product Catalog Controller
- Doc Catalog Book Controller
- Forum Model & Announcement
- Survey Request Model & Service
- Coffee Point POS Ledger
- Employee Assistant Tool
- Forum Controller
- Work Label & List Config
- Community 29
- Survey Progress Export
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80
- Community 81
- Community 82
- Community 83
- Community 84
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92
- Community 93
- Community 94
- Community 95
- Community 96
- Community 97
- Community 98
- Community 99
- Community 100
- Community 101
- Community 102
- Community 103
- Community 104
- Community 105
- Community 106
- Community 107
- Community 108
- Community 109
- Community 110
- Community 111
- Community 112
- Community 113
- Community 114
- Community 115
- Community 116
- Community 117
- Community 118
- Community 119
- Community 120
- Community 121
- Community 122
- Community 123
- Community 124
- Community 125
- Community 126
- Community 127
- Community 128
- Community 129
- Community 130
- Community 131
- Community 132
- Community 133
- Community 134
- Community 135
- Community 136
- Community 137
- Community 138
- Community 139
- Community 140
- Community 141
- Community 142
- Community 143
- Community 144
- Community 145
- Community 146
- Community 147
- Community 148
- Community 149
- Community 150
- Community 151
- Community 152
- Community 153
- Community 154
- Community 155
- Community 156
- Community 157
- Community 158
- Community 159
- Community 160
- Community 161
- Community 162
- Community 163
- Community 164
- Community 165
- Community 166
- Community 167
- Community 168
- Community 169
- Community 170
- Community 171
- Community 172
- Community 173
- Community 174
- Community 175
- Community 176
- Community 177
- Community 178
- Community 179
- Community 180
- Community 181
- Community 182
- Community 183
- Community 184
- Community 185
- Community 186
- Community 187
- Community 188
- Community 189
- Community 190
- Community 191
- Community 192
- Community 193
- Community 194
- Community 195
- Community 196
- Community 197
- Community 198
- Community 199
- Community 200
- Community 201
- Community 202
- Community 203
- Community 204
- Community 205
- Community 206
- Community 207
- Community 208
- Community 209
- Community 210
- Community 211
- Community 212
- Community 213
- Community 214
- Community 215
- Community 216
- Community 217
- Community 218
- Community 219
- Community 220
- Community 221
- Community 222
- Community 223
- Community 224
- Community 225
- Community 226
- Community 227
- Community 228
- Community 229
- Community 230
- Community 231
- Community 232
- Community 233
- Community 234
- Community 235
- Community 236
- Community 237
- Community 238
- Community 239
- Community 240
- Community 241
- Community 242
- Community 243
- Community 244
- Community 245
- Community 246
- Community 247
- Community 248
- Community 249
- Community 250
- Community 251
- Community 252
- Community 253
- Community 254
- Community 255
- Community 256
- Community 257
- Community 258
- Community 259
- Community 260
- Community 261
- Community 262
- Community 263
- Community 264
- Community 265
- Community 266
- Community 267
- Community 268
- Community 269
- Community 270
- Community 271
- Community 272
- Community 273
- Community 274
- Community 386
- Community 387
- Community 388
- Community 389
- Community 390
- Community 391
- Community 392
- Community 396
- Community 397
- Community 398
- Community 411
- Community 412
- Community 413
- Community 414
- Community 415

## God Nodes (most connected - your core abstractions)
1. `success()` - 718 edges
2. `Employee` - 342 edges
3. `record()` - 271 edges
4. `get_perm_profile()` - 264 edges
5. `Base` - 240 edges
6. `_post()` - 235 edges
7. `AuditMixin` - 229 edges
8. `User` - 212 edges
9. `Document` - 191 edges
10. `Company` - 143 edges

## Surprising Connections (you probably didn't know these)
- `main()` --indirect_call--> `error()`  [INFERRED]
  scripts/legacy_sync/verify_legacy_bucket.py → app/core/response.py
- `_existing_instances()` --uses--> `ApprovalInstance`  [INFERRED]
  scripts/legacy_sync/import_approval_history.py → app/modules/approval/instance_model.py
- `count_steps()` --uses--> `ApprovalInstance`  [INFERRED]
  scripts/legacy_sync/verify_approval_history.py → app/modules/approval/instance_model.py
- `show_one()` --uses--> `ApprovalInstance`  [INFERRED]
  scripts/legacy_sync/verify_approval_history.py → app/modules/approval/instance_model.py
- `build_actions()` --uses--> `ApprovalTask`  [INFERRED]
  scripts/legacy_sync/import_approval_history.py → app/modules/approval/instance_model.py

## Import Cycles
- 3-file cycle: `app/modules/report/excel/__init__.py -> app/modules/report/excel/builder.py -> app/modules/report/excel/pivot.py -> app/modules/report/excel/__init__.py`
- 3-file cycle: `app/modules/report/excel/__init__.py -> app/modules/report/excel/builder.py -> app/modules/report/excel/sheet_import_landed_cost.py -> app/modules/report/excel/__init__.py`
- 3-file cycle: `app/modules/report/excel/__init__.py -> app/modules/report/excel/builder.py -> app/modules/report/excel/sheet_shipping.py -> app/modules/report/excel/__init__.py`

## Hyperedges (group relationships)
- **Ba tài liệu lõi của hệ thống công việc nhà máy** — app_modules_assistant_knowledge_source_nhamay_01_quy_dinh_he_thong_cong_viec, app_modules_assistant_knowledge_source_nhamay_02_huong_dan_van_hanh_tro_ly_ai, app_modules_assistant_knowledge_source_nhamay_03_bo_cau_hoi_lam_ro_cong_viec [EXTRACTED 1.00]
- **Hệ thống bộ nhớ AI — sổ đăng ký + danh mục + HD.HT.01 §5.7** — app_modules_assistant_knowledge_source_nhamay_09_so_dang_ky_cong_viec, app_modules_assistant_knowledge_source_nhamay_10_danh_muc_tai_lieu, app_modules_assistant_knowledge_source_nhamay_02_huong_dan_van_hanh_tro_ly_ai [EXTRACTED 1.00]
- **Chuỗi thiết kế → đầu ra: 10 hạng mục → 6 giai đoạn → M1-M13** — app_modules_assistant_knowledge_source_nhamay_01_quy_dinh_he_thong_cong_viec_10_hang_muc, app_modules_assistant_knowledge_source_nhamay_02_huong_dan_van_hanh_tro_ly_ai_6_giai_doan, app_modules_assistant_knowledge_source_nhamay_02_huong_dan_van_hanh_tro_ly_ai_m1_m13 [INFERRED 0.90]
- **Luồng thu mua cốt lõi: YCBG → Khảo sát → YCMH → ĐMH → Nhận hàng → Công nợ → YCTT** — app_modules_assistant_packs_10_quy_trinh_thu_mua_ycbg, app_modules_assistant_packs_10_quy_trinh_thu_mua_phieu_khao_sat, app_modules_assistant_packs_10_quy_trinh_thu_mua_ycmh, app_modules_assistant_packs_10_quy_trinh_thu_mua_dmh, app_modules_assistant_packs_10_quy_trinh_thu_mua_nhan_hang, app_modules_assistant_packs_10_quy_trinh_thu_mua_cong_no, app_modules_assistant_packs_10_quy_trinh_thu_mua_yctt [EXTRACTED 1.00]
- **Hệ thống tri thức nhà máy: QĐ.HT.01, HM1-HM10, M1-M12, G1-G6** — app_modules_assistant_packs_nhamay_tri_thuc_co_dong_qd_ht_01, app_modules_assistant_packs_nhamay_tri_thuc_co_dong_hd_ht_01, app_modules_assistant_packs_nhamay_tri_thuc_co_dong_muoi_hang_muc, app_modules_assistant_packs_nhamay_tri_thuc_co_dong_muoi_hai_khuon_mau, app_modules_assistant_packs_nhamay_tri_thuc_co_dong_sau_giai_doan_hoi_thoai [EXTRACTED 1.00]
- **Bộ gói tri thức trợ lý AI: các phân hệ nghiệp vụ** — app_modules_assistant_packs_readme_goi_tri_thuc_assistant, app_modules_assistant_packs_10_quy_trinh_thu_mua_quy_trinh_thu_mua, app_modules_assistant_packs_20_van_thu_van_ban_phan_he_van_thu, app_modules_assistant_packs_30_du_an_cong_viec_phan_he_du_an, app_modules_assistant_packs_40_nghi_phep_phan_he_nghi_phep, app_modules_assistant_packs_50_dat_phong_hop_phan_he_dat_phong, app_modules_assistant_packs_60_nhan_su_ho_so_ho_so_nhan_su, app_modules_assistant_packs_nhamay_tri_thuc_co_dong_nhamay_dego_organic [EXTRACTED 1.00]

## Communities (417 total, 154 thin omitted)

### Community 0 - "Core Models & Base Mixins"
Cohesion: 0.02
Nodes (191): Import mọi model để Base.metadata đầy đủ (dùng cho Alembic autogenerate)., AuditMixin, Base, LegacyIdMixin, Cột chuẩn cho mọi bảng (theo quy ước DB)., Khóa của bản ghi tương ứng bên app đặt xe cũ (Firebase Realtime DB). Giá trị là…, BỘ MÃ SỐ CỦA BA LỚP NHẬT KÝ — số nguyên, theo R2/QĐ-11 (bao-CR-312, P1). Mọi…, AgentCursor (+183 more)

### Community 1 - "Document Access Control"
Cohesion: 0.02
Nodes (173): Văn bản đang áp dụng cho CHÍNH người hỏi — không cần quyền gì thêm ngoài đăng…, _run_document_read(), _run_my_documents(), DocTypeLinkRule, QUY TẮC QUAN HỆ CHA–CON giữa các loại văn bản (E01, E02). Mỗi dòng là một câu:…, approving_this_document(), block_self_ban(), _book_ids() (+165 more)

### Community 2 - "Audit, Scoping & Notification"
Cohesion: 0.03
Nodes (154): Session, URL ảnh chữ ký của một NHÂN SỰ (qua tài khoản đăng nhập gắn với nhân sự đó).…, URL ảnh chữ ký của một TÀI KHOẢN. Trả "" nếu chưa tải chữ ký lên., resolve_signature(), resolve_signature_by_employee(), dep(), user_has_permission(), approves_only_in_dept_proc() (+146 more)

### Community 3 - "Doc Catalog Security Levels"
Cohesion: 0.03
Nodes (146): ensure_valid(), label(), label_maps(), Session, Tra nhãn mức mật / độ khẩn từ danh mục. Trước đây `document/export.py` giữ một…, Trả `(nhãn mức mật, nhãn độ khẩn)` theo `value`. Đọc cả dòng đã ngừng dùng: văn…, Số lạ (dữ liệu cũ, dòng đã bị xóa tay dưới DB) thì in ra chính con số — giống…, Bậc mang mã này đang là số mấy. Dùng cho những chỗ mã nguồn cần trỏ tới MỘT bậc… (+138 more)

### Community 4 - "Document Controller & Sanitize"
Cohesion: 0.04
Nodes (122): parse_ids(), 12, 15,x' -> [12, 15]. Rỗng -> [] (nghĩa là xuất theo bộ lọc, không theo tick…, Làm sạch NỘI DUNG văn bản trước khi lưu — chống XSS lưu trữ. `content_html`…, `content_html` đã lọc. `None`/rỗng trả chuỗi rỗng. Chỉ gọi khi content_html…, sanitize_document_html(), activate_due(), approve_document(), confirm_reviewed() (+114 more)

### Community 7 - "Legacy Dat Xe Integration"
Cohesion: 0.05
Nodes (96): error(), _handle(), Request, Session, Cửa NHẬN của app đặt xe cũ: `POST /api/sync/datxe/events` (§5.2 bản thiết kế).…, Nhận MỘT sự kiện từ app cũ. Thân yêu cầu theo hợp đồng §5.2: `{event_id,…, receive_legacy_event(), LegacyCatalog (+88 more)

### Community 8 - "Approval Flow & Delegation"
Cohesion: 0.04
Nodes (83): Delegation, _currently_effective(), delegatees_of(), delegators_of(), find_delegation(), Session, ỦY QUYỀN CÓ THỜI HẠN — tra lúc chạy (I12). Ủy quyền **không đổi người được giao…, Những ai đang ủy quyền cho người này — dùng dựng màn Việc của tôi. (+75 more)

### Community 9 - "Auth Tokens & Permissions"
Cohesion: 0.04
Nodes (91): _check_session(), create_access_token(), create_refresh_token(), create_reset_token(), _create_token(), decode_token(), decode_token_claims(), _dept_ref_map() (+83 more)

### Community 10 - "Document Clone & Attachment Window"
Cohesion: 0.05
Nodes (74): Company, Pháp nhân nhận hóa đơn (có phân cấp qua `parent`)., app_modules_document, DocumentAccess, HẠN XEM TỆP ĐÍNH KÈM của văn bản. Một văn bản đặt được ngày *"xem tệp tới…, Văn bản này đã quá hạn cho xem tệp chưa. So bằng `>` chứ không `>=`: đặt hạn…, view_window_expired(), list_clones() (+66 more)

### Community 11 - "Survey Request Controller"
Cohesion: 0.06
Nodes (88): add_option_(), approve_(), available_survey_lines_(), bulk_delete_survey_requests(), _can_act_as_requester_side(), _can_edit_own(), cancel_(), choose_option_() (+80 more)

### Community 12 - "Purchase Order & Payable"
Cohesion: 0.06
Nodes (86): Ghi kép id ↔ tên cho MỘT ô nhân sự trên chứng từ (vd. `nspt_id`/`nspt`). Có id…, sync_employee_ref(), _revert_po(), app_modules_payable, debt_days(), Suy ra số ngày công nợ từ hình thức thanh toán của NCC (vd 'Công nợ 30 ngày')., POUpdate, apply_auto_progress() (+78 more)

### Community 13 - "Purchase Request Service"
Cohesion: 0.06
Nodes (85): Đồng bộ cặp (`department_id`, `department`) trên một phiếu — CR-086.…, sync_department_ref(), Đồng bộ cờ Đơn gấp cho cả NHÓM: YCMH + mọi ĐMH cùng pr_code = is_urgent. Dùng…, sync_urgent_group(), PurchaseRequest, Yêu cầu mua (PYC) — header., apply_auto_urgent(), apply_supplier_info() (+77 more)

### Community 14 - "Core Framework Utilities"
Cohesion: 0.07
Nodes (49): Ghi & đọc nhật ký thao tác (audit log) dùng chung., get_current_user(), Xác thực (JWT) + phân quyền (RBAC) dùng chung — giống AuthMiddleware., Dependency: chặn nếu user không có quyền `action` trên `entity`., require(), pagination(), Tham số phân trang dùng chung cho mọi danh sách., Generic CRUD router factory — dùng cho các danh mục đơn giản (đỡ lặp code). (+41 more)

### Community 15 - "App Settings & File Access Log"
Cohesion: 0.05
Nodes (78): _cast(), _decrypt(), encrypt(), _fernet(), get(), _load(), Cấu hình hiệu lực (effective settings). - Key thường: lưu DB (plaintext), DB ĐÈ…, Giá trị hiệu lực: DB (nếu có) → .env. Secret được giải mã khi trả về (chỉ dùng… (+70 more)

### Community 16 - "Work Controller (Kanban)"
Cohesion: 0.06
Nodes (82): _actor(), add_group_member(), add_list_member(), archive_group(), archive_list(), create_group(), create_label_field(), create_label_option() (+74 more)

### Community 17 - "Attachment Upload Guard"
Cohesion: 0.05
Nodes (79): is_private(), Đọc nội dung một `StoredFile`, tự chọn kho theo `source`. Thay cho…, read_file_bytes(), ensure_batch_ok(), Trần số tệp mỗi lượt tải lên (BM-030)., _block_version_in_approval(), chain(), _chain_rows() (+71 more)

### Community 18 - "Legacy Dat Xe Export Builder"
Cohesion: 0.04
Nodes (76): _approvals(), build_booking(), build_seal(), _companies_of(), copy_legacy_fields(), ensure_seal_type(), _first_approval(), fit_to_columns() (+68 more)

### Community 19 - "Employee Controller"
Cohesion: 0.06
Nodes (72): _block_sensitive(), _block_set_password_out_of_scope(), create_employee(), delete_employee(), delete_employee_signature(), _employee_in_scope(), export_employees_csv(), export_employees_xlsx() (+64 more)

### Community 20 - "Work Group & Audit"
Cohesion: 0.07
Nodes (71): activity_kind_labels(), Phân hệ Công việc — tên `entity` dùng khi ghi nhật ký (`core/audit.record`).…, Bộ nhãn `[{value, label}]` cho ô lọc ngoài giao diện., add_member(), archive_group(), create_group(), _get_group_or_403(), list_members() (+63 more)

### Community 21 - "Product Catalog Controller"
Cohesion: 0.06
Nodes (68): bulk_delete_products(), create_product(), delete_product(), export_products_csv(), get_product(), import_products_csv(), clean(), norm_group() (+60 more)

### Community 22 - "Doc Catalog Book Controller"
Cohesion: 0.06
Nodes (68): create_book(), delete_book(), get_book(), get_counter(), list_books(), delete, get, patch (+60 more)

### Community 23 - "Forum Model & Announcement"
Cohesion: 0.05
Nodes (70): create_forum_announcement(), CR-200 (F12) — ô «Đăng thông báo lên diễn đàn» trong hộp thoại Ban hành. Clone…, ForumAudience, ForumBoard, ForumBoardStatus, ForumBodyFormat, ForumModerationAction, ForumModerationLog (+62 more)

### Community 24 - "Survey Request Model & Service"
Cohesion: 0.07
Nodes (71): assert_unique_product_codes(), Mã hàng phải DUY NHẤT trên phiếu YCMH (ĐMH KHÔNG còn dùng luật này — bao-…, Liên kết mỗi lần tạo YCMH từ 1 option của 1 dòng YCKS (1 dòng có thể tạo NHIỀU…, Phiếu YÊU CẦU KHẢO SÁT (Task 5). Người YC lập để nhờ thu mua khảo sát sản…, Option gắn vào 1 dòng yêu cầu = 1 kết quả khảo sát SP đã duyệt (snapshot). Bảng…, SurveyRequest, SurveyRequestOption, SurveyRequestPr (+63 more)

### Community 25 - "Coffee Point POS Ledger"
Cohesion: 0.07
Nodes (64): adjust_ledger(), _policy_locked(), Dòng đã được một kỳ cấp dùng tới thì CHỈ ĐỌC — đổi mức = thêm dòng mới, để "mức…, resolve_pos_order(), CoffeeLedger, CoffeeLedgerType, CoffeeMemberStatus, CoffeePolicy (+56 more)

### Community 26 - "Employee Assistant Tool"
Cohesion: 0.06
Nodes (51): _clamp(), _dump(), Tool HỒ SƠ NHÂN SỰ của trợ lý AI (T45 `employee_lookup`). Trả lời «anh Nam…, Dựng dòng kết quả THEO danh sách trắng, không `model_dump()` cả hồ sơ. Chép cả…, _run(), label_of(), BỘ MÃ SỐ CỦA HỒ SƠ NHÂN SỰ — theo R2/QĐ-11. Cột nào mang nghĩa *phân loại · cấp…, Nhãn tiếng Việt của một mã số. Mã lạ → chuỗi rỗng. Trả rỗng chứ KHÔNG trả lại… (+43 more)

### Community 27 - "Forum Controller"
Cohesion: 0.06
Nodes (63): _authors(), _board_names(), create_board(), create_post(), delete_board(), delete_post(), feed(), get_post() (+55 more)

### Community 28 - "Work Label & List Config"
Cohesion: 0.08
Nodes (63): Một TRƯỜNG nhãn của list — "Phiên bản", "Độ ưu tiên", "Tag"… (B-08). Trường…, Một giá trị trong bộ giá trị của trường nhãn ("Thumua", "v2"…)., WorkLabelField, WorkLabelOption, _assert_can_change_type(), _clean_name(), _count_values(), create_label_field() (+55 more)

### Community 29 - "Community 29"
Cohesion: 0.07
Nodes (64): POItemIn, BỘ MÃ RIÊNG CỦA YÊU CẦU MUA HÀNG — số nguyên, theo R2/QĐ-11. ⚠️ Đây KHÔNG phải…, PurchaseRequestItem, PurchaseRequestItemOption, PHƯƠNG ÁN mua gắn vào 1 dòng YCMH (bao-CR-310) — NCC + giá do NSTM đề xuất. Vì…, Dòng hàng của yêu cầu mua (theo Sheet: giá đề xuất, kho, NSPT, trạng thái...)., assign_supplier_bulk(), _check_room() (+56 more)

### Community 30 - "Survey Progress Export"
Cohesion: 0.06
Nodes (58): _build_query(), _cond_map(), _decorate(), export_xlsx(), _line_visible_cond(), list_progress(), get, Request (+50 more)

### Community 31 - "Community 31"
Cohesion: 0.07
Nodes (56): hash_password(), perm_cache_clear(), Xóa cache quyền khi admin sửa vai trò/quyền/gán vai trò., Role, Phạm vi dữ liệu theo NGƯỜI DÙNG (Lớp B). Mỗi dòng = 1 giá trị được cấp/loại…, UserRole, UserScope, delete_user() (+48 more)

### Community 32 - "Community 32"
Cohesion: 0.07
Nodes (57): counter_lookup(), create_member(), create_partner(), create_policy(), create_self_order(), get_meta(), list_ledger(), list_members() (+49 more)

### Community 33 - "Community 33"
Cohesion: 0.07
Nodes (59): get_users_by_role_codes(), Tài khoản thuộc các vai trò theo mã (vd Quản lý TM / Admin TM)., VehicleBooking, _approvers(), _assigned_driver_user(), _context(), _creator(), _dispatchers() (+51 more)

### Community 34 - "Community 34"
Cohesion: 0.07
Nodes (53): app_core, app_modules_catalog, PurchaseHistory, Lịch sử mua hàng — SNAPSHOT 1 dòng hàng của ĐMH tại thời điểm dòng đó vào…, Session, Lịch sử mua hàng — ghi snapshot khi dòng ĐMH vào `completed` + truy vấn cho UI., Ghi 1 record snapshot cho dòng vừa vào `completed`. Gọi từ…, Bọc `snapshot_line` — lỗi ghi lịch sử KHÔNG được chặn luồng tiến độ mua hàng. (+45 more)

### Community 35 - "Community 35"
Cohesion: 0.05
Nodes (45): Nạp mọi tệp có khai bộ mã, để sổ đăng ký của `status_catalog` đầy đủ. Cùng vai…, BỘ MÃ PREFIX chủ đề diễn đàn (F13a) — nhãn hiển thị cho…, BỘ MÃ NGHỈ PHÉP — loại nghỉ và buổi. Dùng cho `tab_document.metadata` của loại…, Số công khi giấy khai nghỉ GỌN trong một ngày. Hai mốc nửa ngày: bắt đầu ở nửa…, same_day_work_credit(), all_sets(), Code, CodeSet (+37 more)

### Community 36 - "Community 36"
Cohesion: 0.06
Nodes (60): doc_model(), policy(), Đăng ký chứng từ cho phép bình luận (CR-029). Mỗi entity bình luận → (entity…, (entity cha, nhãn, route FE) — None nếu entity không được phép bình luận., Model của chứng từ, để kiểm phạm vi dữ liệu. Import bên trong hàm để tránh vòng…, is_image(), Ảnh thì hiện luôn ra, file khác chỉ hiện tên — dùng cho đính kèm bình luận., delete_attachments_for() (+52 more)

### Community 37 - "Community 37"
Cohesion: 0.06
Nodes (56): Thông tin nhân sự của người dùng để in phiếu: họ tên, chức vụ, bộ phận, trưởng…, resolve_actor_profile(), _context_tokens(), Chính sách mật khẩu dùng chung cho MỌI cửa đặt mật khẩu (BM-016 — bao-CR-405).…, Bỏ dấu tiếng Việt để so khớp — `Nguyễn` và `nguyen` là cùng một chuỗi., Những chuỗi mật khẩu KHÔNG được chứa: mã nhân viên, email, phần trước @ của…, Kiểm một mật khẩu MỚI trước khi băm. Trả lại chính chuỗi đó, hoặc ném 400.…, _strip_accents() (+48 more)

### Community 38 - "Community 38"
Cohesion: 0.05
Nodes (46): build_signature(), Chữ ký chia sẻ giữa ERP và các hệ ngoài (máy nói với máy, KHÔNG phải token…, Ký một cục dữ liệu. Tách riêng để test được mà không cần settings., Bộ header để GỬI ĐI. Nguồn chưa khai hoặc chưa có khóa thì ném lỗi ngay thay vì…, Kiểm chữ ký của yêu cầu NHẬN VỀ. Trả `(hợp lệ, lý do)`. Lý do là câu tiếng Việt…, sign_headers(), verify_signature(), _apply_filters() (+38 more)

### Community 39 - "Community 39"
Cohesion: 0.09
Nodes (57): ItemGroup, Phân loại VTBB/NL + thời gian quy định (Sheet phân loại)., LogLevel, _auto_pay(), _last_row(), Import Đơn mua hàng — sheet 6 "TIẾN ĐỘ MUA HÀNG" (header dòng 4, data từ dòng…, Dòng 'Hoàn thành' -> tạo YCTT + ghi ĐÃ CHI (chỉ khi Ghi). Dry-run chỉ đếm + log., Mã dạng số (Số HĐ, Misa...) — Excel lưu số nên openpyxl đọc float 779.0; cắt… (+49 more)

### Community 40 - "Community 40"
Cohesion: 0.08
Nodes (58): Recap MỘT phiếu Yêu cầu thanh toán theo mã — cùng khuôn với…, _run_read_request(), _line_out(), PaymentRequest, PaymentRequestLine, Dòng đề nghị chi. CR-066: mã PO / số hóa đơn / ngày hóa đơn là dữ liệu NHẬP TAY…, Phiếu yêu cầu thanh toán — CHỈ 1 NCC/phiếu, gom nhiều khoản nợ (nhiều PO). In…, apply_line_offsets() (+50 more)

### Community 41 - "Community 41"
Cohesion: 0.09
Nodes (58): LeaveRequest, apply_keyword_search(), cancel(), check_date_range(), check_editable(), check_enough_lines(), check_gender(), check_hourly() (+50 more)

### Community 42 - "Community 42"
Cohesion: 0.06
Nodes (52): pick_columns(), Lọc bộ cột theo danh sách key người dùng đang hiện trên bảng (`cols=a,b,c`).…, apply_operator_filters_map(), Như `apply_operator_filters` nhưng whitelist là map {field: cột} — cho màn JOIN…, apply_ref_filters(), Lọc danh sách theo Ô THAM CHIẾU (phòng ban / nhân sự) bằng ID — CR-088. Nối…, Tên hiện hành của bản ghi được trỏ tới — chỉ dùng để dựng nhánh lùi cho dòng id…, Điều kiện "ô tham chiếu này trỏ tới bản ghi `rid`". `rid` không hợp lệ -> None. (+44 more)

### Community 43 - "Community 43"
Cohesion: 0.09
Nodes (54): Danh sách `seq` theo thứ tự, mỗi chặng một lần., stages(), _patch_snapshot(), Session, SỬA LUỒNG THÌ PHIẾU ĐANG CHẠY BÁM THEO (CR-114). Mặc định của bộ máy là **phiếu…, Đọc lại phiên VÀ KHÓA nó, chỉ trả về khi phiên còn mở. SQLite (bộ test) không…, Đẩy thay đổi của một bước xuống mọi phiếu ĐANG CHẠY theo luồng đó.…, Ghi đè bước `node.id` trong bản chụp của phiếu. `False` = phiếu không có bước… (+46 more)

### Community 44 - "Community 44"
Cohesion: 0.09
Nodes (53): apply_scope(), Lọc query theo HỢP các grant có quyền `action` trên entity., approve_(), bulk_delete_surveys(), by_supplier_(), cancel_(), clone_(), create_() (+45 more)

### Community 45 - "Community 45"
Cohesion: 0.07
Nodes (51): _email_of(), IssueRecipient, notify_document_issued(), Session, Thông báo cho thành viên khi một phiên bản văn bản được ban hành. Danh sách…, Ưu tiên email hồ sơ nhân sự; tài khoản dạng mã NV không phải địa chỉ mail., Mọi tài khoản đang hoạt động có nhân sự thuộc phạm vi văn bản., Tạo chuông + email nền cho đúng tập người nhận sau khi ban hành. Email không… (+43 more)

### Community 46 - "Community 46"
Cohesion: 0.07
Nodes (47): cell_value(), check_row_limit(), Col, Any, Response, Xuất Excel (.xlsx) cho các màn danh sách — CR-068. Dùng chung cho Yêu cầu mua…, `created_at` lưu UTC (naive) -> quy về giờ VN cho khớp với màn hình., Dựng file .xlsx và trả về cho trình duyệt tải xuống. `filename` chưa gồm đuôi… (+39 more)

### Community 47 - "Community 47"
Cohesion: 0.06
Nodes (53): build_field_col(), _empty_for_kind(), ensure_file_matches(), _field_norms(), _gen_code(), _match_col(), _norm(), Session (+45 more)

### Community 48 - "Community 48"
Cohesion: 0.08
Nodes (51): apply_datetime_range(), apply_equals(), apply_filters(), apply_range_filters(), apply_sort_from_request(), is_numeric_column(), looks_like_integer(), Request (+43 more)

### Community 49 - "Community 49"
Cohesion: 0.10
Nodes (52): denied(), Danh tính + phiên DB của NGƯỜI HỎI để tool chạy đúng quyền của họ., Trả về khi thiếu quyền — KHÔNG trả rỗng lặng lẽ để model khỏi tưởng 'không có…, ToolContext, analytics_query(), _apply_filters(), _clamp(), contract_count_by_status() (+44 more)

### Community 50 - "Community 50"
Cohesion: 0.07
Nodes (40): chunk_text(), _hard_split(), Cắt văn bản dài thành đoạn (chunk) để nhúng vector. Thuần: không đụng DB, không…, Bỏ thẻ HTML nhưng GIỮ ranh giới khối thành xuống dòng (để tách câu không dính…, Cắt cứng một câu dài quá ngưỡng theo cửa sổ ký tự., Cắt `text` (có thể chứa HTML) thành danh sách đoạn, mỗi đoạn <= ~max_chars ký…, strip_html(), Embedder (+32 more)

### Community 51 - "Community 51"
Cohesion: 0.08
Nodes (47): _block_code_change(), _block_delete_used_type(), _check_tier(), _check_type_create(), _check_year_end_config(), create_tier(), delete_tier(), list_tiers() (+39 more)

### Community 52 - "Community 52"
Cohesion: 0.10
Nodes (45): Ảnh chụp phiếu + dòng (JSON) để revert., _snap(), Điều kiện của ô tìm kiếm đa trường: 6 cột trên phiếu HOẶC mã/tên hàng ở bảng…, search_condition(), Nhãn tiếng Việt của `approve_status` (B-04). Mã lạ -> rỗng. Trả rỗng chứ không…, Phiếu khảo sát (header) — dùng chung NCC & SP (survey_type)., Survey, SurveyProductLine (+37 more)

### Community 53 - "Community 53"
Cohesion: 0.10
Nodes (48): approve_po(), bulk_delete_pos(), cancel_po(), clone_po(), complete_po(), copy_po(), create_po(), delete_po() (+40 more)

### Community 54 - "Community 54"
Cohesion: 0.09
Nodes (50): approve_booking(), booking_overview(), booking_timeline(), _changed_labels(), create_booking(), delete_booking(), dispatch_reject_booking(), dispatch_return_booking() (+42 more)

### Community 55 - "Community 55"
Cohesion: 0.09
Nodes (45): Danh sách quyền dùng chung (nguồn chân lý duy nhất). Quyền = ENTITY (đối tượng)…, create_role(), delete_role(), get_permissions(), get_role(), list_roles(), permission_meta(), delete (+37 more)

### Community 56 - "Community 56"
Cohesion: 0.08
Nodes (48): _is_lock_error(), Session, HAI NGƯỜI CÙNG BẤM TRÊN MỘT PHIẾU — biến kẹt khóa CSDL thành câu người đọc…, Chạy `viec()`; kẹt khóa thì cuộn lại và trả 409 — KHÔNG chạy lại. Lỗi không…, run_with_contention_retry(), can_read(), Người này có được xem phiếu duyệt của chứng từ đó không. Loại chứng từ **chưa…, _acting_employee_id() (+40 more)

### Community 57 - "Community 57"
Cohesion: 0.09
Nodes (47): app_modules_work, Việc thường hay CỘT MỐC (B-14). Cột mốc là một task như mọi task khác, chỉ khác…, WorkTaskKind, Một task cho cả kanban lẫn danh sách. `subtask_done/total` là tiến độ "n/m"…, Một giá trị nhãn trên task. Trả ĐỦ mọi cột `value_*` chứ không chỉ cột hợp…, task_label_out(), task_out(), collect() (+39 more)

### Community 58 - "Community 58"
Cohesion: 0.05
Nodes (12): _audit(), van ban va phien ban van ban (M6) + ma so hieu cho phap nhan/phong ban (M2)…, Bốn cột chuẩn + khóa chính. Là HÀM vì mỗi `create_table` phải nhận một bộ đối…, upgrade(), _add(), _columns(), downgrade(), _drop() (+4 more)

### Community 59 - "Community 59"
Cohesion: 0.12
Nodes (20): _bool_value(), _css_color(), _css_font(), _css_number(), DocxHtmlConverter, level_at(), _ListInfo, _merge() (+12 more)

### Community 60 - "Community 60"
Cohesion: 0.07
Nodes (46): success(), update_avatar(), Sao lưu ngay (bấm tay) — đẩy task vào worker, trả về ngay., run_now(), bulk_(), create_clones(), F06–F09 — sinh bản nháp cho từng pháp nhân con và báo cho họ., parse_import_file() (+38 more)

### Community 61 - "Community 61"
Cohesion: 0.09
Nodes (43): has_global_scope(), Người này có grant `action` trên `entity` với phạm vi **tất cả** không? Khác…, add_node(), _block_delete_step_in_use(), _block_scope_on_declare(), _block_while_running(), create_flow(), delete_flow() (+35 more)

### Community 62 - "Community 62"
Cohesion: 0.08
Nodes (43): approve(), bulk_handover(), _cancel_pending_tasks(), claim_task(), _clear_results_from_step(), _employee_names(), _ensure_open(), give_comment() (+35 more)

### Community 63 - "Community 63"
Cohesion: 0.08
Nodes (41): Trả các đoạn liên quan nhất tới `query`, mỗi đoạn gồm text + nguồn + link +…, search_docs(), Nền cho lớp tool loại A: ngữ cảnh chạy + kiểu khai báo + bộ chạy có gác quyền +…, Một tool: khai báo cho model (name/description/parameters) + hàm chạy thật…, ToolSpec, _apply_company(), _catalog_names(), _clean_number() (+33 more)

### Community 64 - "Community 64"
Cohesion: 0.08
Nodes (32): call(), cleanup_old_orders(), ensure_suppliers(), main(), Tạo 3 đơn mua hàng NHẬP KHẨU mẫu để thử bao-CR-319 (chỉ dùng LOCAL). Đi qua…, Dựng NCC nước ngoài + NCC chi phí thẳng qua ORM. Cố ý KHÔNG đi qua API như phần…, Xóa đơn mẫu của lần chạy trước để script chạy lại bao nhiêu lần cũng ra đúng 3…, record_deliveries() (+24 more)

### Community 65 - "Community 65"
Cohesion: 0.08
Nodes (41): direct_policy(), ext_of(), Đăng ký chính sách file đính kèm (P1). Mỗi entity đính kèm → (entity CHA để…, (tập đuôi cho phép, trần MB) của một cửa tải tệp trực tiếp. Khóa lạ → lỗi lập…, make_thumb(), BytesIO, Thu ảnh về cạnh dài `max_edge`, nén JPEG. Trả None khi không đáng làm (ảnh…, content_type_of() (+33 more)

### Community 66 - "Community 66"
Cohesion: 0.10
Nodes (36): production_overview(), Tổng quan phân hệ Sản xuất — danh mục NCC · Sản phẩm · ĐVT · Phân loại · Hợp…, bulk_delete_suppliers(), create_supplier(), delete_supplier(), export_suppliers_csv(), get_supplier(), list_suppliers() (+28 more)

### Community 67 - "Community 67"
Cohesion: 0.09
Nodes (41): add_article_slide(), add_help_home_item(), create_help_article(), delete_article_slide(), delete_help_article(), delete_help_home_item(), get_help_article(), get_help_home_sections() (+33 more)

### Community 68 - "Community 68"
Cohesion: 0.11
Nodes (42): get_approvers_for_entity(), Gets all active users who have approval permission for the given entity,…, _actor(), block_legacy_path(), _can_read_request(), _context_by_id(), _employee_id_of_user(), entity_context() (+34 more)

### Community 69 - "Community 69"
Cohesion: 0.09
Nodes (43): _add_rich(), bullet(), _cell_shade(), data_table(), footer(), h2(), header(), meta_table() (+35 more)

### Community 70 - "Community 70"
Cohesion: 0.08
Nodes (41): Kết quả báo cáo đã tính sẵn (precompute) — đọc nhanh, tính lại chạy nền. key =…, ReportSnapshot, _amt(), _blank_cell(), compute(), deliv_dim(), compute_dept_range(), ig_metric() (+33 more)

### Community 71 - "Community 71"
Cohesion: 0.11
Nodes (40): bulk_(), by_employee(), create_(), delete_(), get_(), list_(), _out(), delete (+32 more)

### Community 72 - "Community 72"
Cohesion: 0.08
Nodes (37): Phân hệ Công việc — cụm nhãn tùy biến của từng list. Quy ước chung của phân hệ…, Giá trị của một TRƯỜNG tùy biến trên một task (B-08 + B-13). Một dòng = một giá…, WorkTaskLabel, _as_date(), _as_decimal(), _as_int(), _build_rows(), Session (+29 more)

### Community 73 - "Community 73"
Cohesion: 0.11
Nodes (40): get_perm_profile(), Hồ sơ quyền (cache in-process) theo mô hình GRANT — mỗi vai trò của user là 1…, dashboard(), get, Session, Đủ số liệu cho cả trang trong MỘT lần gọi. Mọi câu đếm đi qua cùng bộ lọc phạm…, get_type_stats(), get (+32 more)

### Community 74 - "Community 74"
Cohesion: 0.09
Nodes (36): _grouped_out(), _match_company(), _payable_out(), Tool CÔNG NỢ PHẢI TRẢ + soạn nháp Yêu cầu thanh toán (YCTT) — chỉ đọc, không…, bao-CR-273 — tổng hợp NHÓM theo NCC/công ty trên TOÀN BỘ kết quả lọc. Trả lời…, Khớp tên/tên tắt/mã công ty (không phân biệt hoa thường) với danh mục đang hoạt…, Query khoản nợ đã gác phạm vi + các bộ lọc chung của cả hai tool. Trả (query,…, _run_draft() (+28 more)

### Community 75 - "Community 75"
Cohesion: 0.08
Nodes (18): check_extra_fields(), check_resign_after_hire(), Nghỉ việc không thể TRƯỚC ngày vào làm. Cho phép BẰNG nhau — vào làm rồi nghỉ…, Ràng buộc ô `extra_fields` — bốn chiều, thứ tự từ rẻ tới đắt., _check_code_value(), _check_extra_fields(), _check_gender_value(), EmployeeBase (+10 more)

### Community 76 - "Community 76"
Cohesion: 0.10
Nodes (39): _amt(), _can_see_ncc(), daily(), dept_range(), export_excel(), _id_list(), ig_range(), _import_landed_cost_data() (+31 more)

### Community 77 - "Community 77"
Cohesion: 0.12
Nodes (42): approve_seal(), _can_stamp(), complete_seal(), create_seal_request(), delete_seal_request(), get_seal_request(), list_approvers(), BackgroundTasks (+34 more)

### Community 78 - "Community 78"
Cohesion: 0.10
Nodes (40): resolve_actor(), _content_disposition(), download_export_file(), get_export(), _guard_view(), list_entities(), list_exports(), _log_out() (+32 more)

### Community 79 - "Community 79"
Cohesion: 0.10
Nodes (35): on_source_deleted(), on_source_saved(), Session, Móc nối nghiệp vụ -> chỉ mục vector. Service HDSD/FAQ gọi hai hàm này sau khi…, Gọi sau khi tạo/sửa một bài HDSD hoặc câu FAQ. `db` giữ cho khớp chữ ký cũ,…, Gọi sau khi xóa một bài HDSD hoặc câu FAQ., Tìm kiếm vector loại B cho trợ lý AI (HDSD + FAQ). Toàn bộ package nạp LƯỜI…, task (+27 more)

### Community 80 - "Community 80"
Cohesion: 0.11
Nodes (41): approve_request(), cancel_request(), create_request(), delete_request(), _dump(), _ensure_balance_in_scope(), estimate_days(), _get_or_404() (+33 more)

### Community 81 - "Community 81"
Cohesion: 0.11
Nodes (26): ChatMessage, ChatResult, Provider, ProviderError, Exception, ToolExecutor, Giao diện chung cho mọi nhà cung cấp model + kiểu dữ liệu trao đổi., Vòng lặp tool-calling (loại A): model chọn tool -> `execute` chạy dưới quyền… (+18 more)

### Community 82 - "Community 82"
Cohesion: 0.09
Nodes (40): build_template(), ImportValidationError, is_catalog_module(), Exception, Sinh file .xlsx mẫu: đúng bộ cột của adapter (một dòng tiêu đề)., File tải lên không khớp bảng đã chọn (sai phân hệ/bảng hoặc nhầm file mẫu)., _batch_out(), commit_import() (+32 more)

### Community 83 - "Community 83"
Cohesion: 0.10
Nodes (37): adjust_balance(), allocate(), apply_employee_search(), balance_summary(), close_year(), _dump(), _expire_then_commit(), get_balance() (+29 more)

### Community 84 - "Community 84"
Cohesion: 0.08
Nodes (38): _client(), dated_key(), download_bytes(), _eff(), is_remote_storage_ready(), presigned_url(), datetime, _r2_ready() (+30 more)

### Community 85 - "Community 85"
Cohesion: 0.11
Nodes (36): my_sessions(), Phiên của CHÍNH MÌNH, mới nhất trước; phiên đang gọi được đánh dấu…, _assert_user_in_scope(), _current_session_id(), list_sessions(), login_history(), logout_all(), get (+28 more)

### Community 86 - "Community 86"
Cohesion: 0.13
Nodes (37): DocumentNumberingRule, DocumentNumberingRuleBook, DocumentNumberingRuleDocType, Quy tắc đánh số văn bản theo chiều, loại văn bản và sổ áp dụng., Một quy tắc có một bộ đếm riêng cho từng pháp nhân. `pattern` dùng các token có…, create_rule(), delete_rule(), get_rule() (+29 more)

### Community 87 - "Community 87"
Cohesion: 0.12
Nodes (39): RoomBooking, attach_instance(), cancel(), check_capacity(), check_conflict(), check_editable(), check_ready_to_submit(), check_time_range() (+31 more)

### Community 88 - "Community 88"
Cohesion: 0.11
Nodes (35): I20 — bản in dấu vết duyệt. *"khi kiểm toán hoặc thanh tra hỏi «ai duyệt cái…, trail(), ApprovalAction, Dấu vết duyệt — **chỉ ghi thêm, không sửa, không xóa** (I20). Ba cột danh tính…, action_out(), actions_of(), _approver_names(), audit_sentence() (+27 more)

### Community 89 - "Community 89"
Cohesion: 0.09
Nodes (36): chat(), confirm_document_update(), delete_conversation(), download_report_file(), _guard(), list_conversations(), list_providers(), my_usage() (+28 more)

### Community 90 - "Community 90"
Cohesion: 0.10
Nodes (38): import_articles(), Nhập bài viết từ file HTML / Markdown — mỗi file thành 1 bài. Trả kết quả TỪNG…, HelpArticleSlide, Ảnh hướng dẫn từng bước gắn vào 1 bài viết., add_slide(), _branch_ids(), count_branch(), create_article() (+30 more)

### Community 91 - "Community 91"
Cohesion: 0.08
Nodes (35): HelpArticle, Bài viết hướng dẫn sử dụng. Tự tham chiếu parent_id để tạo cây thư mục., main(), di(), main(), Bốc nội dung bài HDSD / FAQ ra tệp HTML để sửa ngoài container. Cặp đôi với…, actor_id(), main() (+27 more)

### Community 92 - "Community 92"
Cohesion: 0.07
Nodes (34): _apply(), _dang_tam_ngung(), _doi_lo(), _doi_mot_cot(), downgrade(), _norm(), B-06 nhip 2: chuan hoa may trang thai tien do dong DMH sang ma tieng Anh…, Bo dau + thuong hoa + gom khoang trang. (+26 more)

### Community 93 - "Community 93"
Cohesion: 0.10
Nodes (36): is_enabled(), _after_submit(), apply_keyword_search(), approver_options(), _company_refs(), complete_seal(), count_attachments(), create_seal_request() (+28 more)

### Community 94 - "Community 94"
Cohesion: 0.11
Nodes (36): device_label(), Dấu 8 byte -> `chrome|windows|desktop`. Không tra được thì trả chuỗi rỗng. Trả…, Đổi sang chuỗi 36 ký tự có gạch — dạng người đọc, dạng API trả ra. ⚠️ Tra tay…, request_id_text(), AuditLog, Nhật ký thao tác: ai (created_by) làm gì (action) trên đối tượng nào, lúc nào…, ChangeLog, RequestLog (+28 more)

### Community 95 - "Community 95"
Cohesion: 0.09
Nodes (34): _as_list(), describe(), matches(), _one(), parse(), ĐIỀU KIỆN RẼ NHÁNH (I04). Điều kiện khai bằng JSON, đọc trên **bối cảnh phiếu**…, Câu tiếng Việt của điều kiện, cho bảng theo dõi và bản in dấu vết., Đọc chuỗi điều kiện. Hỏng thì coi như KHÔNG có điều kiện, không nổ. Nổ ở đây là… (+26 more)

### Community 96 - "Community 96"
Cohesion: 0.10
Nodes (36): block_legacy_path(), _can_read(), can_read_request(), cancel_request(), _context_by_id(), create_leave_document(), _document_lines(), entity_context() (+28 more)

### Community 97 - "Community 97"
Cohesion: 0.10
Nodes (36): block_legacy_path(), _can_read(), can_read_booking(), cancel_booking(), _context_by_id(), entity_context(), _get(), is_enabled() (+28 more)

### Community 98 - "Community 98"
Cohesion: 0.12
Nodes (30): create_rule(), delete_rule(), get_rule(), list_options(), list_rules(), delete, get, patch (+22 more)

### Community 99 - "Community 99"
Cohesion: 0.15
Nodes (30): create_template(), delete_template(), get_template(), list_templates(), delete, get, patch, Request (+22 more)

### Community 100 - "Community 100"
Cohesion: 0.07
Nodes (21): is_configured(), query_node(), Đọc Realtime Database của app đặt xe cũ. CHỈ ĐỌC, không bao giờ ghi. Chiều ghi…, Đọc một nhánh nhưng LỌC SẴN BÊN KIA: `orderBy` + `startAt` (+ `limitToFirst`).…, Đọc một nhánh, vd `read_node("vehicles/veh_04")`. Trả `None` khi chưa cấu hình,…, read_node(), _CatalogView, normalize_name() (+13 more)

### Community 101 - "Community 101"
Cohesion: 0.14
Nodes (34): Một HỒ SƠ cần hoàn thành trong báo cáo — đơn vị nhỏ nhất của khối., SurveyReportDoc, apply_template(), check_depends(), _check_refs(), create_doc(), create_item(), create_phase() (+26 more)

### Community 102 - "Community 102"
Cohesion: 0.09
Nodes (29): dispatch_booking(), Điều phối: gán xe + tài xế cho phiếu (điều phối viên = quyền write)., Driver, Vehicle, DispatchIn, Điều phối: gán 1 xe (+ 1 tài xế; tự lái thì bỏ trống, người yêu cầu là tài xế)., VehicleBookingCreate, dispatch_booking() (+21 more)

### Community 103 - "Community 103"
Cohesion: 0.12
Nodes (32): get_menu(), pos_dashboard(), Thực đơn đọc từ POS365 (tên/giá/ảnh theo dữ liệu quán đang bán)., Số liệu quầy đọc TRỰC TIẾP từ POS365 lúc mở màn: hôm nay + doanh thu theo ngày…, Chạy đồng bộ NGAY trong request (không cần worker) — quán nhỏ, mỗi vòng vài…, run_sync(), PosSyncKind, Năm vòng chạy nền. Đây là con số giao diện gửi lên khi bấm «Chạy ngay»; xuống… (+24 more)

### Community 104 - "Community 104"
Cohesion: 0.11
Nodes (32): resolve_actor(), Tạo task, hoặc VIỆC CON khi có `parent_id`. Việc con bỏ qua…, TaskCreate, _actor(), create_subtask(), create_task(), create_task_link(), delete_task() (+24 more)

### Community 105 - "Community 105"
Cohesion: 0.09
Nodes (31): _input_trace(), is_sensitive_key(), mask_error_detail(), mask_payload(), LUẬT GHI NHẬT KÝ — khai MỘT chỗ, dùng cho cả ba lớp (bao-CR-312, P1). Ba nhóm…, Có đệm thân trả về để đọc không. ⚠️ GET **thành công thì KHÔNG đệm**, và đây là…, Tên khóa (thân request) hay tên cột (P4) này có cấm ghi giá trị không., Chép sâu một cấu trúc JSON, thay giá trị của khóa nhạy cảm bằng `***`. Chép chứ… (+23 more)

### Community 106 - "Community 106"
Cohesion: 0.14
Nodes (30): block_edit_own_permissions(), L1. Gọi ở mọi cửa ghi phân quyền có tham số «tài khoản đích»., assign_roles(), _block_out_of_scope(), delete_user(), get_scope(), get_user(), list_users() (+22 more)

### Community 107 - "Community 107"
Cohesion: 0.09
Nodes (31): delete_key(), env_prefix(), Thư mục gốc tách môi trường trên storage (prod/dev...). Lấy từ .env…, delete_(), download(), list_(), _out(), delete (+23 more)

### Community 108 - "Community 108"
Cohesion: 0.14
Nodes (29): bulk_delete_companies(), _company_in_scope(), create_company(), delete_company(), _format_company(), get_company(), list_companies(), delete (+21 more)

### Community 109 - "Community 109"
Cohesion: 0.14
Nodes (29): create_department(), delete_department(), _department_in_scope(), export_departments_csv(), get_department(), import_departments_csv(), list_by_companies(), list_department_companies() (+21 more)

### Community 110 - "Community 110"
Cohesion: 0.12
Nodes (32): Hoàn tác batch danh mục: bản ghi MỚI -> xoá; bản ghi ĐÃ XÓA (was_new=2) -> tạo…, revert(), ImportBatch, ImportMode, ImportStatus, IntEnum, 1 lần import. created_by = người import; created_at = thời điểm upload., add_log() (+24 more)

### Community 111 - "Community 111"
Cohesion: 0.09
Nodes (30): _heading(), NỘI DUNG SOẠN THẢO của bộ văn bản mẫu — HTML cho trình soạn thảo. Tách riêng…, Khối đầu văn bản HAI CỘT + tên loại — thể thức chung ở `document_the_thuc`., Khối «Nơi nhận» — phần không ai được quên ở văn bản gửi ra ngoài., Khối chữ ký: chức vụ, khoảng trống ký tay, họ tên., Bảng có hàng tiêu đề — dùng cho biểu mẫu và phụ lục., _recipients_block(), _signature_block() (+22 more)

### Community 112 - "Community 112"
Cohesion: 0.11
Nodes (31): _add_aggregate(), _after_commit(), _after_flush(), _after_rollback(), _after_soft_rollback(), _before_flush(), _collect(), _detail_count() (+23 more)

### Community 113 - "Community 113"
Cohesion: 0.12
Nodes (31): placeholder_text(), Dòng thế chỗ cho tin CŨ khi nạp lại lịch sử — giữ ngữ cảnh 'từng gửi tệp gì' mà…, get_conversation(), Chi tiết hội thoại + toàn bộ tin (chỉ chủ hội thoại xem được)., _attachment_meta(), chat(), delete_conversation(), get_messages() (+23 more)

### Community 114 - "Community 114"
Cohesion: 0.15
Nodes (30): _alignment(), _char_style(), _color(), _css_number(), _font_info(), _image_html(), _ImageBlock, _line_content() (+22 more)

### Community 115 - "Community 115"
Cohesion: 0.11
Nodes (31): ForumPost, ForumPostStatus, Bài viết trên diễn đàn. Tác giả = `created_by` (user_id). `dept_id` /…, Trạng thái bài viết. `PENDING_REVIEW` chừa sẵn theo QĐ-D2: trước mắt KHÔNG…, _author_ids_subquery(), can_moderate(), can_view(), escape_like() (+23 more)

### Community 116 - "Community 116"
Cohesion: 0.08
Nodes (31): app_modules_user, _already_stamped(), _count_tickets_by_user(), create_one(), _index_departments_by_legacy(), _load_export(), main(), _make_password() (+23 more)

### Community 117 - "Community 117"
Cohesion: 0.10
Nodes (25): build_kwargs(), digits(), first_phone(), _int_or(), Lookups, loose(), parse_legacy_dt(), datetime (+17 more)

### Community 118 - "Community 118"
Cohesion: 0.11
Nodes (31): approve_booking(), cancel_booking(), check_availability(), create_booking(), delete_booking(), _dump_one(), get_booking(), _get_or_404() (+23 more)

### Community 119 - "Community 119"
Cohesion: 0.12
Nodes (30): _actor(), block_legacy_path(), _can_read_booking(), _context_by_id(), _employee_id_of_user(), entity_context(), is_enabled(), _on_approved() (+22 more)

### Community 120 - "Community 120"
Cohesion: 0.11
Nodes (28): _import_cost(), Một dòng chi phí nhập khẩu — trả cả SỐ lẫn NHÃN (R2/QĐ-11). `pay` là khoản nợ…, AllocationMethod, ImportCostStatus, ImportCostType, OrderType, IntEnum, Cách chia một khoản chi phí về các dòng hàng (bao-CR-319 P3/P4). Chỉ để XEM:… (+20 more)

### Community 121 - "Community 121"
Cohesion: 0.12
Nodes (27): bulk_delete_contracts(), create_(), delete_(), expiry_state(), _fill_party(), get_(), _in_scope(), list_contract_types() (+19 more)

### Community 122 - "Community 122"
Cohesion: 0.10
Nodes (21): RÀNG BUỘC KÍCH THƯỚC của hồ sơ nhân sự — chặn ở schema, không để MySQL nổ. Vì…, JobPositionCreate, JobPositionResponse, JobPositionUpdate, BaseModel, field_validator, Schema của DANH MỤC CHỨC VỤ — xem `position_model.py`. ⚠️ Mọi ô chuỗi khai…, Cắt khoảng trắng thừa và chặn ô rỗng. Một dòng tên rỗng thì ô chọn chức vụ hiện… (+13 more)

### Community 123 - "Community 123"
Cohesion: 0.10
Nodes (20): _body_only(), _Cleaner, _extract_title(), parse_file(), _pop_doc_title(), HTMLParser, Nhập bài viết Help Center từ file HTML / Markdown. Đầu vào là file NGOÀI hệ…, Chữ trần — dùng lấy tiêu đề / mô tả ngắn. (+12 more)

### Community 124 - "Community 124"
Cohesion: 0.13
Nodes (25): _authors(), create_comment(), delete_comment(), list_comments(), list_likes(), list_mentionable(), list_replies(), _notify_new() (+17 more)

### Community 125 - "Community 125"
Cohesion: 0.18
Nodes (26): Faq, Câu hỏi thường gặp — hiển thị ở trang người dùng của Trung tâm Hướng dẫn., add_home_item(), delete_home_item(), _get_home_item(), _get_home_section(), get_home_sections(), _has_duplicate() (+18 more)

### Community 126 - "Community 126"
Cohesion: 0.14
Nodes (25): _content_types(), _document_rels(), DocxPackage, EmbeddedImage, header_footer_paragraph(), mm_to_twips(), pack(), page_number_field() (+17 more)

### Community 127 - "Community 127"
Cohesion: 0.12
Nodes (25): _apply_range(), build_overview(), _by_company(), _by_driver(), _by_vehicle(), _month_range(), _month_starts(), _parse_day() (+17 more)

### Community 128 - "Community 128"
Cohesion: 0.09
Nodes (26): Quy trình thu mua DEGO, Phân hệ Văn thư, Bốn khung nhìn: Bảng, Danh sách, Gantt, Hoạt động, Bốn vai trò trong dự án (Khách xem, Thành viên, Quản trị, Chủ sở hữu), Phân hệ Dự án (ERP v2), Bốn khóa quyền nghỉ phép (leave_request, leave_balance, leave_type, holiday), Phân hệ Nghỉ phép (Nhân sự), Phân hệ Đặt phòng họp (Nhân sự) (+18 more)

### Community 129 - "Community 129"
Cohesion: 0.11
Nodes (14): Pos365Client, Session, `GET /api/orders?Includes=Partner` — danh sách mới nhất trước, phân trang…, Đọc lại MỘT đơn (soát void D-03). ĐÃ KIỂM 08/09/2026 (POC P4, cửa hàng…, Tra khách theo SĐT/tên phục vụ ghép B-02. Response đã lọc `Password`., B-03 — tạo khách mới (request GHI: không retry mù)., D-07 (soi gương số dư) — chỉ dùng khi POC P5 xác nhận ghi được., `GET /api/products` — thực đơn quán, kèm `Category` và… (+6 more)

### Community 130 - "Community 130"
Cohesion: 0.12
Nodes (23): _backfill_audit(), flush_changes(), Chép `changed_fields` / `change_count` lên dòng audit cùng `request_id`. Cố ý…, Ghi cả bộ đệm xuống `tab_change_log`. Trả về số dòng đã ghi. Mở phiên RIÊNG,…, _to_row(), bump_audit_count(), current_request_id(), current_request_id_text() (+15 more)

### Community 131 - "Community 131"
Cohesion: 0.12
Nodes (23): _fetch_datxe_bytes(), is_remote(), legacy_ready(), Đọc byte của tệp đính kèm CÒN NẰM Ở HỆ THỐNG KHÁC (`StoredFile.source`). Từ đợt…, Kéo byte thẳng từ bucket của app cũ bằng khóa CHỈ-ĐỌC., Xin app cũ một đường dẫn còn hạn rồi kéo byte về. Hai chặng chứ không một:…, Chữ ký máy-gọi-máy cho một lời gọi sang app cũ (mục 6 của bản mô tả). Ký lên…, Hỏi app cũ đường dẫn còn hạn của một tệp. ⚠️ Đường `GET… (+15 more)

### Community 132 - "Community 132"
Cohesion: 0.19
Nodes (23): CategoryAssignee, Phân công NSTM phụ trách theo phân loại VTBB: mỗi phân loại 1 người CHÍNH + 1…, auto_assign_by_category(), bulk_upsert(), create(), delete(), _find_pair(), get() (+15 more)

### Community 133 - "Community 133"
Cohesion: 0.12
Nodes (19): create_rule(), delete_rule(), get_rule(), list_rules(), delete, get, patch, Session (+11 more)

### Community 134 - "Community 134"
Cohesion: 0.15
Nodes (24): _date(), Nhận `YYYY-MM-DD`, trả lại đúng chuỗi đó. Ngày lưu dạng chuỗi trong JSON., expiry_date(), Ngày cuối cùng còn dùng được phần mang sang. `None` = không hết hạn. `year` là…, Số công khi nghỉ GỌN trong một ngày — hai ô buổi cùng nói về ngày đó. Tính bằng…, same_day_credit(), count_hourly_days(), is_workday() (+16 more)

### Community 135 - "Community 135"
Cohesion: 0.12
Nodes (23): _chan(), _dept_include_cond(), _dept_match(), _emp_match(), _explicit_cond(), _handler_dept_cond(), _parse_int_values(), _proc_status_cond() (+15 more)

### Community 136 - "Community 136"
Cohesion: 0.20
Nodes (23): _detail_url(), _cat(), _fetch_scoped(), _filter_mine(), _handler_dept_fields(), _label(), _limit(), _not_found() (+15 more)

### Community 137 - "Community 137"
Cohesion: 0.15
Nodes (19): BỘ MÃ CỦA PHÂN HỆ ĐẶT PHÒNG HỌP — số nguyên, theo R2/QĐ-11. Cột nào mang nghĩa…, API ĐẶT PHÒNG HỌP — `/api/room-bookings` và `/api/meeting-rooms`. Gác hai trục…, AttendeeItem, Config, MeetingRoomCreate, MeetingRoomResponse, MeetingRoomUpdate, BaseModel (+11 more)

### Community 138 - "Community 138"
Cohesion: 0.14
Nodes (22): EmailTemplate, get_effective(), list_effective(), Session, Mẫu email theo bước cho phân hệ Đặt xe — đọc/ghi + render + gửi. Nguồn mặc định…, Mẫu đang có hiệu lực cho một event: DB (nếu có) đè lên mặc định. Trả `None` nếu…, Toàn bộ mẫu theo thứ tự khai báo, đã đè DB lên mặc định., Lưu chỉnh sửa của người dùng cho một event (tạo dòng nếu chưa có). (+14 more)

### Community 139 - "Community 139"
Cohesion: 0.14
Nodes (23): POImportCost, Một khoản chi phí của lô hàng nhập khẩu (bao-CR-319 P3). Bảng PHẲNG, gắn thẳng…, compute(), _cost_dict(), _cost_type(), _cost_type_columns(), _empty_by_type(), _item_dict() (+15 more)

### Community 140 - "Community 140"
Cohesion: 0.23
Nodes (22): apply_template_(), create_doc_(), create_item_(), create_phase_(), delete_doc_(), delete_item_(), delete_phase_(), delete_report_() (+14 more)

### Community 141 - "Community 141"
Cohesion: 0.13
Nodes (15): BaseModel, field_validator, Schema của khối Báo cáo thực hiện (YCBG). ⚠️ Mọi trường chuỗi khai `max_length`…, Sửa một hồ sơ — chỉ gửi trường muốn đổi (nút ✓ chỉ gửi mỗi `status`)., Ô ngày đi bằng chuỗi `yyyy-mm-dd` (hoặc rỗng = chưa đặt) theo quy ước FE. Kiểm…, Thêm/sửa một nút dòng hàng., Thêm/sửa một giai đoạn., Đổ mẫu chung vào một nút dòng hàng (0 = Chung), tùy chọn chỉ một giai đoạn. (+7 more)

### Community 142 - "Community 142"
Cohesion: 0.17
Nodes (21): apply_sort(), Sắp xếp phía server theo cột — CHỈ nhận cột thật của bảng (whitelist chống SQL…, generate_code(), Session, Số chứng từ kế tiếp cho một tiền tố (`CTY001`, `NP027`…). ⚠️ **KHÓA HÀNG LỚN…, create_department(), delete_department(), departments_of_companies() (+13 more)

### Community 143 - "Community 143"
Cohesion: 0.14
Nodes (21): has_pending_task(), _instance_steps(), _names_of(), _one_step(), pending_assignees(), _planned_steps(), Session, LUỒNG DUYỆT DẠNG NGANG cho một DANH SÁCH chứng từ (CR-260). Màn danh sách muốn… (+13 more)

### Community 144 - "Community 144"
Cohesion: 0.14
Nodes (22): check_daily_limit(), count_today(), my_quota(), datetime, Exception, Session, _questions_sum(), QuotaExceeded (+14 more)

### Community 145 - "Community 145"
Cohesion: 0.11
Nodes (18): build_my_tasks(), dismiss_tasks(), my_tasks(), overview(), alert_ok(), can(), get, Request (+10 more)

### Community 146 - "Community 146"
Cohesion: 0.15
Nodes (22): check_enough(), consume(), ensure_balance(), get_balance(), Session, QUỸ PHÉP — cấp phát, tính thâm niên, giữ chỗ và trừ thật. Ràng buộc §6.1 của kế…, Số ngày còn nghỉ được. Chưa cấp phát thì trả `0.0`. `0.0` chứ không phải…, Chặn nếu nghỉ vượt quỹ — QĐ-NP2: **không cho ứng phép**. Vượt thì đổi sang loại… (+14 more)

### Community 147 - "Community 147"
Cohesion: 0.14
Nodes (20): action_options(), ActionCode, ActionFamily, _build(), group_of_action(), is_known_action(), label_of_action(), BỘ MÃ HÀNH ĐỘNG của nhật ký ba tầng — nơi khai DUY NHẤT (CR-312 P2 / NT-4). Cột… (+12 more)

### Community 148 - "Community 148"
Cohesion: 0.12
Nodes (21): answer_callback(), _call(), clear_buttons(), _clip(), esc(), fetch_updates(), is_allowed_chat(), is_enabled() (+13 more)

### Community 149 - "Community 149"
Cohesion: 0.15
Nodes (20): _before_create(), _before_update(), API HỒ SƠ — `/api/dossiers` (phân hệ Hồ sơ, 16/09/2026). Dựng bằng…, Bộ sinh trao SCHEMA (không phải dict) ở đường tạo — dựng dict rồi chép lại. ⚠️…, Đường sửa trao dict các ô ĐƯỢC GỬI (`exclude_unset`) — sửa tại chỗ. `obj` còn…, exists(), Dòng được trỏ tới còn tồn tại không? ⚠️ Kiểm thật chứ không tin máy khách, và…, apply_extra_fields() (+12 more)

### Community 150 - "Community 150"
Cohesion: 0.20
Nodes (18): create_(), delete_(), get_(), list_(), _out(), delete, get, patch (+10 more)

### Community 151 - "Community 151"
Cohesion: 0.15
Nodes (19): http_cookiejar, _detect(), _drive_download(), _file_id(), _plan(), Tải file hợp đồng từ Google Drive (cột 'Link HĐ' trong hợp đồng.xlsx) -> R2 ->…, Trả (bytes, content_type) hoặc (None, lý do) nếu không tải được (bị hạn chế…, Tái tạo thứ tự HĐ -> [(code, ncc, link_target, display)]. (+11 more)

### Community 152 - "Community 152"
Cohesion: 0.16
Nodes (19): _describe_step(), _document_flow(), _document_row(), _employee_names(), _entity_flow(), _find_doc_types(), _html_to_text(), _keyword_condition() (+11 more)

### Community 153 - "Community 153"
Cohesion: 0.19
Nodes (8): _color(), _Converter, _parse_style(), _px(), HTMLParser, Duyệt HTML một lượt, sinh thẳng XML của thân tài liệu., Số mục tự động cho tiêu đề — viết thẳng vào chữ (xem chú thích đầu tệp)., `#1a2b3c` hoặc `rgb(1,2,3)` → `1A2B3C`. Word không nhận dấu #.

### Community 154 - "Community 154"
Cohesion: 0.18
Nodes (9): Kiểm cả bộ trường của một loại hồ sơ. Trả về dạng đã chuẩn hoá để lưu. ⚠️ Trả…, validate_field_schema(), _check_status(), DossierCreate, DossierResponse, DossierUpdate, BaseModel, field_validator (+1 more)

### Community 155 - "Community 155"
Cohesion: 0.12
Nodes (20): _block_delete_position_in_use(), _propagate_rename(), Session, Chốt `before_update`: tên đổi thì nhãn trên hồ sơ phải đổi theo. Chạy TRƯỚC khi…, Chốt `before_delete`: còn người giữ chức vụ này thì không xóa. Xóa là để lại hồ…, check_assignable(), count_employees(), count_holders_by_department() (+12 more)

### Community 156 - "Community 156"
Cohesion: 0.18
Nodes (19): Đồng bộ mảng approval.history của phiếu app cũ sang tab_approval_instance,…, sync_legacy_approval_history(), backfill_trip(), build_actions(), build_instance(), build_snapshot(), build_tasks(), _existing_instances() (+11 more)

### Community 157 - "Community 157"
Cohesion: 0.17
Nodes (17): Danh mục Loại con dấu — CRUD đơn giản qua khung chung. Danh mục nền (entity…, CompanyRef, CompleteSealIn, Config, BaseModel, field_validator, AuditMixin trả datetime; API dùng chuỗi ISO. Không có validator này thì…, Văn thư HOÀN THÀNH (đã đóng dấu ngoài thực tế): ghi chú. (+9 more)

### Community 158 - "Community 158"
Cohesion: 0.18
Nodes (19): pil, api_login(), collect_rows(), compress(), drive_download(), drive_id(), find_product(), main() (+11 more)

### Community 159 - "Community 159"
Cohesion: 0.19
Nodes (19): Function naming rules (English verbs only), QĐ.HT.01 — Quy định hệ thống công việc, 10 hạng mục thiết kế công việc (định nghĩa → quy định → quy trình → hướng dẫn → tiêu chuẩn → biểu mẫu → báo cáo → kiểm soát → cải tiến → đào tạo), Phân loại A/B/C — điểm = tần suất × mức độ (6-9=A, 3-4=B, 1-2=C), HD.HT.01 — Hướng dẫn vận hành trợ lý AI, 6 giai đoạn hội thoại AI (G1 tiếp nhận → G2 phân tích thiếu → G3 phỏng vấn → G4 phân tích đề xuất → G5 tạo tài liệu → G6 tự kiểm tra), M1–M13 — 13 mẫu đầu ra bắt buộc của trợ lý AI, BM.01/QĐ.HT.01 — Bộ câu hỏi làm rõ công việc (100 câu) (+11 more)

### Community 160 - "Community 160"
Cohesion: 0.27
Nodes (18): Ghi một dòng nhật ký thao tác. Sáu tham số đầu **giữ nguyên thứ tự và ý nghĩa**…, record(), Phiếu hỗ trợ nội bộ. Mọi nhân viên đăng nhập đều mở được; nhóm 'Hỗ trợ' xử lý…, Một tin nhắn trong luồng trao đổi của phiếu hỗ trợ. created_by = tài khoản…, Ticket, TicketMessage, add_message(), assign() (+10 more)

### Community 161 - "Community 161"
Cohesion: 0.17
Nodes (18): _apply(), apply_operator_filters(), _blank(), build_condition(), _coerce(), collect_conditions(), collect_conditions_map(), _is_text_col() (+10 more)

### Community 162 - "Community 162"
Cohesion: 0.19
Nodes (18): _acting_employee_id(), create_delegation(), DelegationIn, delete_delegation(), list_delegations(), _load(), BaseModel, delete (+10 more)

### Community 163 - "Community 163"
Cohesion: 0.14
Nodes (19): close_year(), _moved_days(), Session, Số ngày dư được phép mang đi LƯỢT NÀY. `0` = không có gì để mang. ⚠️ **Vét thêm…, Loại nghỉ NHẬN. `None` = cấu hình hỏng, dòng đó phải bỏ qua chứ không đoán. Quy…, Kết sổ `year` cho các dòng quỹ đã lọc sẵn (phạm vi do nơi gọi lo). Trả về bảng…, _target_type(), LeaveType (+11 more)

### Community 164 - "Community 164"
Cohesion: 0.16
Nodes (18): Permission, Quyền chi tiết theo (vai trò x đối tượng) — các cờ hành động + phạm vi dòng., ensure_admin_role(), force_resync_roles(), Seed cho môi trường THẬT (prod + dev-UAT). Chạy: python -m app.seed_prod Chạy…, run(), E01 — bảy dòng quy tắc quan hệ mẫu. INSERT-ONLY. Không ghi đè dòng đã có: Hành…, Tạo các vai trò chuẩn + ma trận quyền. Không tạo user; gán cho nhân sự ở màn… (+10 more)

### Community 165 - "Community 165"
Cohesion: 0.19
Nodes (17): _build_query(), _can_read_changes(), _can_read_logs(), _guard(), list_logs(), get, Session, Ba cửa của màn NHẬT KÝ HỆ THỐNG `/system/logs` (bao-CR-407 / CR-312 P5). Xem… (+9 more)

### Community 166 - "Community 166"
Cohesion: 0.17
Nodes (18): _activity_out(), list_activities(), list_actors(), Session, Phân hệ Công việc — dòng hoạt động cấp DỰ ÁN (D-09, §8 của `05-giao-dien.md`).…, Những người TỪNG thao tác trên dự án — nguồn cho ô lọc «theo người». Lấy từ…, Id mọi việc thuộc dự án — KỂ CẢ việc đã xóa mềm. Không lọc `deleted_at IS…, Ba nguồn dòng hoạt động của MỘT dự án. `entity_id` chỉ so được trong phạm vi… (+10 more)

### Community 167 - "Community 167"
Cohesion: 0.19
Nodes (18): Một mũi tên phụ thuộc trên Gantt: việc TRƯỚC → việc SAU. Bốn luật, ba cái đầu…, WorkTaskLink, create_link(), creates_cycle(), delete_link(), list_links(), Session, Phân hệ Công việc — phụ thuộc việc trước–sau (B-15). Tệp này giữ MỘT luật mà… (+10 more)

### Community 168 - "Community 168"
Cohesion: 0.18
Nodes (18): commit_or_conflict(), make_crud_router(), create_item(), delete_item(), export_csv(), get_item(), import_csv(), list_items() (+10 more)

### Community 169 - "Community 169"
Cohesion: 0.16
Nodes (16): Sinh bản thumbnail cho ảnh lúc TẢI LÊN (Pillow). Hệ chưa có CDN resize, nên…, archive_audit_task(), _archive_table(), _column_names(), _jsonable(), _month_bounds(), datetime, task (+8 more)

### Community 170 - "Community 170"
Cohesion: 0.23
Nodes (17): _by_role(), _from_subject_field(), _heads_of_specified_departments(), _legal_representatives(), _len_n_cap(), _only_active_employees(), Session, BẢY CÁCH CHỌN NGƯỜI DUYỆT (I03). Trả về **danh sách employee_id**, đã bỏ trùng… (+9 more)

### Community 171 - "Community 171"
Cohesion: 0.15
Nodes (15): build_system(), load_pack(), Nạp GÓI TRI THỨC + dựng system prompt cho Trợ lý AI (AI-1, Phase 1). Cách làm…, Ghép nội dung mọi tệp .md trong packs/ (trừ README) theo thứ tự tên tệp., System prompt hoàn chỉnh = định nghĩa vai trò + gói tri thức (+ ghi đè tùy…, get_provider(), Lấy provider theo tên; None = nhà mặc định (config). Ưu tiên nhà đã cấu hình…, ask() (+7 more)

### Community 172 - "Community 172"
Cohesion: 0.16
Nodes (17): add_days(), _int(), norm_group(), Session, Số ngày quy định (QĐ) có hàng theo Phân loại VTBB/NL — dùng chung YCMH + ĐMH.…, Số ngày trong danh mục là chuỗi tự do ("10", "10 ngày") -> lấy phần chữ số., Khóa tra cứu phân loại: bỏ dấu cách thừa, KHÔNG phân biệt chữ hoa/thường…, {tên phân loại đã chuẩn hóa: số ngày QĐ} — luật "lấy mốc dài nhất, thiếu thì 15… (+9 more)

### Community 173 - "Community 173"
Cohesion: 0.22
Nodes (14): DepartmentCompany, Một phòng ban hiện diện tại một pháp nhân (A06). `Department.company_id` /…, Danh mục nền phân hệ Văn thư: loại văn bản, đơn vị gửi nhận bên ngoài., _check_code(), edit(), _has_book_entries(), _has_issued_numbers_for_company(), _has_issued_numbers_for_department() (+6 more)

### Community 174 - "Community 174"
Cohesion: 0.13
Nodes (17): Bộ phận Thu mua, Công nợ (Payables), Đơn mua hàng (ĐMH/PO), Nhận hàng (GR), Phiếu khảo sát giá, Yêu cầu báo giá (YCBG), Yêu cầu mua hàng (YCMH/PYC), Yêu cầu thanh toán (YCTT) (+9 more)

### Community 175 - "Community 175"
Cohesion: 0.23
Nodes (7): _accepts_budget_zero(), GeminiProvider, ToolExecutor, Đếm số dòng tool trả (để ghi vết audit). Không có thì None., Chỉ dòng Gemini 2.x nhận thinkingBudget=0; 3.x trả 400 nếu gửi 0., Content trung lập (chuỗi hoặc list block — xem ChatMessage) -> parts Gemini.…, _row_count()

### Community 176 - "Community 176"
Cohesion: 0.21
Nodes (16): _clean_changes(), confirm_update(), _editable_error(), _fernet(), _fetch_by_code(), _model_of(), _old_value(), Tool tầng GHI có xác nhận (CR-218): `propose_document_update` — CHỈ trả BẢN ĐỀ… (+8 more)

### Community 177 - "Community 177"
Cohesion: 0.26
Nodes (15): _breakdown_by_type(), DashboardFilters, _issued_12_months(), overview(), _priority_matrix(), Session, SỐ LIỆU TRANG TỔNG QUAN VĂN THƯ. Mọi câu đếm ở đây đều đi qua **cùng một bộ lọc…, Số văn bản ban hành theo tháng, 12 tháng gần nhất kể cả tháng rỗng. Dựng đủ 12… (+7 more)

### Community 178 - "Community 178"
Cohesion: 0.16
Nodes (14): _block_delete_type_in_use(), _propagate_rename(), Session, Chốt `before_update`: tên đổi thì nhãn trên hồ sơ phải đổi theo. Chạy TRƯỚC khi…, Chốt `before_delete`: còn hồ sơ mang loại này thì không xóa., DossierType, `field_schema` luôn đọc ra một danh sách, kể cả khi cột đang `NULL`., Số ô tùy biến — bày trên bảng danh mục để biết loại nào đã khai khuôn. (+6 more)

### Community 179 - "Community 179"
Cohesion: 0.20
Nodes (17): export_xlsx(), _filtered(), s(), list_payables(), offset_prepay_(), _out(), get, Request (+9 more)

### Community 180 - "Community 180"
Cohesion: 0.14
Nodes (16): build_overview(), scoped(), _by_company(), _has_grant(), _month_range(), _month_starts(), _parse_day(), datetime (+8 more)

### Community 181 - "Community 181"
Cohesion: 0.18
Nodes (15): clean_merged_duplicates(), _count_department_references(), _load_export(), main(), _next_department_code(), _node_name(), Đóng dấu `legacy_id` lên công ty + phòng ban, và tạo các phòng ban còn thiếu.…, Đóng dấu `legacy_id` lên 11 công ty đã có sẵn bên ERP. (+7 more)

### Community 182 - "Community 182"
Cohesion: 0.21
Nodes (14): _ensure_document(), ensure_in_scope(), _ensure_task_member(), parent_records(), Session, Phạm vi dữ liệu cho tệp đính kèm — B-08, trả nợ N-13. `FILE_POLICY`…, Đính kèm văn bản: hỏi `access_service`, không hỏi `apply_scope`.…, Đính kèm công việc: hỏi TƯ CÁCH THÀNH VIÊN, không hỏi `apply_scope`.… (+6 more)

### Community 183 - "Community 183"
Cohesion: 0.19
Nodes (15): _actor_permissions(), block_edit_own_role(), block_missing_roles(), block_privilege_escalation(), block_role_escalation(), permissions_in_matrix(), permissions_of_roles(), Session (+7 more)

### Community 184 - "Community 184"
Cohesion: 0.33
Nodes (14): BrandBase, BrandCreate, BrandOut, BrandUpdate, ItemGroupCreate, ItemGroupOut, ItemGroupUpdate, BaseModel (+6 more)

### Community 185 - "Community 185"
Cohesion: 0.23
Nodes (11): DocTypeCreate, DocTypeOut, DocTypeUpdate, ExternalPartyCreate, ExternalPartyOut, ExternalPartyUpdate, BaseModel, field_validator (+3 more)

### Community 186 - "Community 186"
Cohesion: 0.26
Nodes (15): EmployeeContact, EmployeeFamily, Người báo tin trong trường hợp cần thiết. Phiếu ghi rõ **bắt buộc** — đây là số…, Thành viên hộ gia đình — phục vụ kê khai BHXH khi ký hợp đồng chính thức. Ghi…, delete_all_of(), list_contacts(), list_families(), Session (+7 more)

### Community 187 - "Community 187"
Cohesion: 0.22
Nodes (13): _add_pivot(), _add_shipping(), build_import_landed_cost_workbook(), build_report_workbook(), BytesIO, Điều phối dựng workbook Excel báo cáo mua hàng — khớp form thumua1 sheet 12–16.…, Workbook báo cáo giá vốn lô hàng nhập khẩu (bao-CR-347) — hai sheet, hai cách…, Xuất Excel báo cáo mua hàng (khớp form thumua1 sheet 12–16). (+5 more)

### Community 188 - "Community 188"
Cohesion: 0.17
Nodes (13): Bộ mã của KHỐI BÁO CÁO THỰC HIỆN trên phiếu YCBG — số nguyên, theo R2/QĐ-11.…, Ba bảng của KHỐI BÁO CÁO THỰC HIỆN trên phiếu Yêu cầu báo giá (YCBG). NS Thu…, Một NÚT lọc theo dòng hàng trên khối báo cáo (vd «K₂SO₄», «KNO₃»). Là bảng chứ…, Một GIAI ĐOẠN của báo cáo (vd «Pháp lý & Giấy phép»). Hồ sơ xếp theo nó., SurveyReportItem, SurveyReportPhase, init_report(), _line_item_name() (+5 more)

### Community 189 - "Community 189"
Cohesion: 0.15
Nodes (15): _booking_query(), export_bookings_xlsx(), list_bookings(), Request, Xuất Excel danh sách phiếu theo ĐÚNG bộ lọc đang hiển thị (danh sách + Chuyến…, Query danh sách phiếu theo ĐÚNG bộ lọc đang đặt (lọc + tìm + phạm vi + mine).…, Danh sách phiếu trong phạm vi người xem ("Yêu cầu của tôi" khi phạm vi = own)., apply_keyword_search() (+7 more)

### Community 190 - "Community 190"
Cohesion: 0.23
Nodes (14): clean_text(), load_rows(), _ma_duyet(), main(), match_supplier(), _max_seq(), nfc(), parse_date() (+6 more)

### Community 191 - "Community 191"
Cohesion: 0.24
Nodes (14): _department_has_issued_document(), ensure_company_issue_code_free(), ensure_department_company_issue_code_free(), ensure_department_issue_code_free(), ensure_department_kind_free(), ensure_doc_type_code_free(), _has_sequence(), Session (+6 more)

### Community 192 - "Community 192"
Cohesion: 0.22
Nodes (9): DossierTypeCreate, DossierTypeResponse, DossierTypeUpdate, BaseModel, field_validator, Schema của DANH MỤC LOẠI HỒ SƠ — xem `type_model.py`. ⚠️ Mọi ô chuỗi khai…, Cắt khoảng trắng thừa và chặn ô rỗng. Một dòng tên rỗng thì ô chọn loại hồ sơ…, Mã loại hồ sơ luôn CHỮ HOA. Ép ở tầng schema chứ không ở giao diện, vì mã còn… (+1 more)

### Community 193 - "Community 193"
Cohesion: 0.18
Nodes (15): _dump_many(), handled(), _latest_per_booking(), get, Session, Phiếu ĐANG chờ chính tôi ký, kèm đủ thông tin để quyết ngay trên dòng., Phiếu chính tôi vừa duyệt / trả về / từ chối gần đây — MỖI PHIẾU MỘT DÒNG. ⚠️…, Giữ đúng MỘT việc cho mỗi phiếu — việc gần nhất. `handled_tasks` đã sắp mới… (+7 more)

### Community 194 - "Community 194"
Cohesion: 0.19
Nodes (13): build_import_landed_cost_item_sheet(), build_import_landed_cost_sheet(), _currency(), _goods_amount(), _label_col(), Hai sheet Excel của báo cáo giá vốn lô hàng nhập khẩu (bao-CR-347). * **GIA VON…, Sheet theo DÒNG HÀNG — chi phí của lô đã chia về từng mã hàng., Ba ô ký tay: người lập · kế toán · quản lý duyệt. (+5 more)

### Community 195 - "Community 195"
Cohesion: 0.15
Nodes (11): build(), scoped(), list_alerts(), get, Session, Cảnh báo cho CHUÔNG — chỉ hiện phần người xem CÓ QUYỀN đọc (không gửi email).…, Hồ sơ phân quyền (cache trong 1 lượt) — dùng cho `apply_scope`., get_position_stats() (+3 more)

### Community 196 - "Community 196"
Cohesion: 0.14
Nodes (14): 404 thay vì 403 cho văn bản không có quyền đọc, Ban hành văn bản (số hiệu vĩnh viễn), Bản riêng pháp nhân con (clone), Luồng duyệt văn bản, Phạm vi áp dụng văn bản, Vòng đời văn bản (11 trạng thái), Đơn nghỉ phép (NP-xxx), Giấy nghỉ phép (GNP) - văn bản tự sinh (+6 more)

### Community 197 - "Community 197"
Cohesion: 0.22
Nodes (13): docx_to_html(), _decode_text(), _doc_to_html(), _extension(), parse_document_file(), _plain_text_to_html(), Chuyển tệp tài liệu thành HTML an toàn để chèn vào trình soạn thảo.…, Tệp → HTML đã lọc; ném ``ValueError`` nếu không thể nhập. (+5 more)

### Community 198 - "Community 198"
Cohesion: 0.29
Nodes (13): EmailExclusion, add(), _excluded_sets(), filter_recipients(), list_all(), Session, Loại trừ email — đọc/ghi danh sách chặn + lọc người nhận trước khi gửi. Mỗi…, Tập id bị loại cho MỘT event = luật áp mọi mẫu ("") + luật riêng event đó. (+5 more)

### Community 199 - "Community 199"
Cohesion: 0.20
Nodes (13): get_my_preferences(), BaseModel, get, Session, save_my_preferences(), SavePreferencesIn, Tuỳ chọn CÁ NHÂN của một người dùng, dạng khoá-giá trị. Khác `tab_setting` ở…, UserPreference (+5 more)

### Community 200 - "Community 200"
Cohesion: 0.19
Nodes (10): device_hash(), _device_kind(), _match_family(), normalize_user_agent(), DẤU THIẾT BỊ — 8 byte cho câu hỏi "vẫn máy đó chứ?" (bao-CR-346). Vì sao cần,…, `User-Agent` thô -> chuỗi ba mảnh, ví dụ `chrome|windows|desktop`. Chuỗi rỗng…, 8 byte của chuỗi đã chuẩn hóa — thứ nằm ở mọi dòng nhật ký. Băm chứ không lưu…, Ghi một dòng. Hỏng thì nuốt lỗi — xem luật 1 ở đầu tệp. (+2 more)

### Community 201 - "Community 201"
Cohesion: 0.29
Nodes (12): _clean(), _clean_sections(), _clean_sheets(), Hai tool XUẤT FILE của Trợ lý AI: `export_report_file` (Word .docx chuẩn DEGO)…, Lưu file đã dựng lên storage + tạo StoredFile của NGƯỜI HỎI, trả khối kết quả…, Ô Excel: giữ số là SỐ (kể cả model gõ '40555800' dạng chuỗi) để cộng/lọc/pivot…, Dựng file .xlsx từ danh sách sheet ĐÃ chuẩn hóa. Tách riêng để test không cần…, render_xlsx() (+4 more)

### Community 202 - "Community 202"
Cohesion: 0.15
Nodes (4): Dossier, `extra_fields` luôn đọc ra một dict, kể cả khi cột đang `NULL`., `custom_fields` luôn đọc ra một danh sách, kể cả khi cột đang `NULL`. Hồ sơ lập…, Số ngày còn lại; âm = đã quá hạn; `None` = vô thời hạn.

### Community 203 - "Community 203"
Cohesion: 0.23
Nodes (12): app_modules_employee, count_refs(), _employee_line(), find_clusters(), main(), Gom tài khoản trùng email về MỘT bản ghi — luôn giữ id NHỎ NHẤT. Đại ca chốt…, Gom tài khoản theo email (bỏ hoa/thường). Chỉ đếm tài khoản ĐANG HOẠT ĐỘNG.…, Bỏ một tài khoản thừa. Trả về True nếu làm được (hoặc xem trước được). (+4 more)

### Community 204 - "Community 204"
Cohesion: 0.24
Nodes (12): ForumReaction, Cảm xúc của một người với một BÀI VIẾT — tối đa 1 dòng/(bài, người). Khuôn…, call_api(), collect_boxes(), login(), main(), parse_id_ranges(), Đi qua mọi dict trong cây board, gom {name: id} của BOX (parent_id > 0). (+4 more)

### Community 205 - "Community 205"
Cohesion: 0.28
Nodes (12): InventoryMove, Sổ phát sinh nhập/xuất kho. qty > 0 = nhập, < 0 = xuất/điều chỉnh giảm., adjust(), apply_delivery(), Session, Tồn kho: nhập từ phiếu nhận hàng (ngầm) + điều chỉnh tay. Phase 2 chỉ…, Tính lại tồn + giá BÌNH QUÂN GIA QUYỀN của (company, kho, sp). qty = Σ move.qty…, Upsert 1 phát sinh nhập kho cho 1 lần giao (idempotent theo delivery_id). Lưu… (+4 more)

### Community 206 - "Community 206"
Cohesion: 0.18
Nodes (13): delete_one(), delete_read(), list_notifications(), _out(), _prune_old(), delete, get, Request (+5 more)

### Community 207 - "Community 207"
Cohesion: 0.21
Nodes (10): get_client_ip(), is_trusted_proxy(), load_trusted_networks(), IP thật của người gọi khi đứng sau Cloudflare tunnel + nginx (bao-CR-313 /…, Đọc `TRUSTED_PROXY_CIDRS` một lần; dải hỏng thì bỏ qua thay vì làm sập app., Đầu TCP đối diện có phải proxy của mình không. `host` không phải IP (TestClient…, IP người gọi theo thứ tự tin cậy ở trên. Luôn trả chuỗi không rỗng (cho…, functools (+2 more)

### Community 208 - "Community 208"
Cohesion: 0.18
Nodes (10): Response, Đặt ngữ cảnh cho cả lượt gọi, rồi ghi lại lượt đó., Dập `last_seen_*` của phiên đang gọi (bao-CR-360, nửa dưới của QĐ-D).…, Đọc thân trả về nếu là JSON; thứ khác trả nguyên response cũ. Số thứ ba là **cỡ…, RequestContextMiddleware, Đã tới lúc dập `last_seen_at` chưa — kiểm TRƯỚC khi mở kết nối DB. Tách riêng…, Dập `last_seen_at` / `last_seen_ip`. Trả `True` nếu thật sự có ghi. Một câu…, touch_is_due() (+2 more)

### Community 209 - "Community 209"
Cohesion: 0.23
Nodes (11): _best_fuzzy(), _clean_acc(), _norm(), Nạp thông tin ngân hàng NCC (Số TK + Ngân hàng/CN) từ file mẫu vào…, Chuẩn hoá tên để so khớp: bỏ khoảng trắng thừa, hạ chữ thường., Số TK: bỏ dấu nháy, xuống dòng, khoảng trắng thừa (giữ nguyên chữ số + dấu cách…, Đọc dữ liệu: ưu tiên file seed_data; nếu có pipe stdin (không rỗng) thì dùng…, Tìm NCC gần đúng nhất (ratio >= ngưỡng), ưu tiên quan hệ chứa nhau. (+3 more)

### Community 210 - "Community 210"
Cohesion: 0.21
Nodes (12): handled(), _latest_per_request(), get, Session, Đơn ĐANG chờ chính tôi ký, kèm đủ thông tin để quyết ngay trên dòng. Mỗi dòng…, Đơn chính tôi vừa duyệt / trả về / từ chối gần đây — MỖI ĐƠN MỘT DÒNG. ⚠️…, Giữ đúng MỘT việc cho mỗi tờ đơn — việc gần nhất. `handled_tasks` đã sắp mới…, Ghép «việc của bộ máy» với «tờ đơn» thành một dòng đọc được. Việc nào trỏ tới… (+4 more)

### Community 211 - "Community 211"
Cohesion: 0.20
Nodes (10): _payload(), product_purchase_history(), get, Session, `hien_ncc=False` -> xóa tên/mã NCC khỏi payload (người xem không có quyền…, supplier_purchase_history(), PurchaseHistoryOut, BaseModel (+2 more)

### Community 212 - "Community 212"
Cohesion: 0.20
Nodes (12): get_report_(), get, Hoàn tác lần xóa gần nhất — dựng lại khối từ ảnh chụp trong sọt rác., restore_report_(), SỌT RÁC của khối báo cáo — cho phép HOÀN TÁC lần «Xóa báo cáo thực hiện». Xóa…, SurveyReportTrash, get_report_payload(), _latest_trash() (+4 more)

### Community 213 - "Community 213"
Cohesion: 0.29
Nodes (11): _dept(), _ensure_factory_assignee_rows(), main(), _make_payable(), _make_po(), _make_pr(), _make_sr(), _person() (+3 more)

### Community 214 - "Community 214"
Cohesion: 0.29
Nodes (10): Một dòng = một việc (task_key) mà một tài khoản đã đánh dấu xong. `task_key` do…, UserTaskDismiss, dismiss_keys(), load_dismissed_keys(), Session, Dịch vụ dùng chung cho Việc cần làm (CR-215). Đứng riêng để cả `/api/alerts`…, Mọi task_key mà tài khoản này đã đánh dấu xong., Đánh dấu xong một loạt việc; key đã có thì bỏ qua. Trả về số key mới ghi. (+2 more)

### Community 215 - "Community 215"
Cohesion: 0.20
Nodes (11): CloneCreate, ClonePlanSave, CloneStatusUpdate, BaseModel, patch, Session, Pháp nhân con cập nhật tình trạng xử lý bản clone của mình., Danh sách pháp nhân CUỐI CÙNG đang được tick — ghi đè, không cộng dồn. Cho phép… (+3 more)

### Community 216 - "Community 216"
Cohesion: 0.33
Nodes (10): list_signatures(), Request, Session, sign_document(), DocumentSignature, Session, Nghiệp vụ CHỮ KÝ (J02, J03). Ba chốt chặn, tất cả ở tầng dịch vụ: 1. **Chỉ ký…, serialize() (+2 more)

### Community 217 - "Community 217"
Cohesion: 0.24
Nodes (8): DossierFieldDef, BaseModel, field_validator, Khai báo MỘT ô nhập tùy biến., _coerce(), Kiểm + chuẩn hoá `extra_fields` của một hồ sơ theo bộ trường của loại., Ép một giá trị về đúng kiểu ô đã khai. Ném `ValueError` kèm tên ô., validate_extra_values()

### Community 218 - "Community 218"
Cohesion: 0.27
Nodes (10): _dem_dong(), _doi_lo(), _doi_mot_cot(), downgrade(), _norm(), B-06 nhip 1: chuan hoa 4 cot "phang" cua cum DMH + YCMH sang ma tieng Anh…, Bo dau + thuong hoa + gom khoang trang., Doi `cu` -> `moi` tren mot cot, cat theo khoang id. Tra so dong da doi. Moc lo… (+2 more)

### Community 219 - "Community 219"
Cohesion: 0.22
Nodes (9): model_of(), Entity (khóa phân quyền) → model SQLAlchemy, để soi phạm vi một bản ghi.…, Model của entity — `None` nếu entity khai `PUBLIC` hoặc không tồn tại. `None`…, _guard(), list_logs(), _format(), get, Session (+1 more)

### Community 220 - "Community 220"
Cohesion: 0.29
Nodes (5): EmbedError, GeminiEmbedder, RuntimeError, Lỗi khi gọi dịch vụ nhúng — tách riêng để tầng trên nuốt gọn, không lẫn lỗi…, Bản hiện thực gọi Gemini embedding API.

### Community 221 - "Community 221"
Cohesion: 0.27
Nodes (8): build_pivot_sheet(), write_row(), _fill_rates(), _finalize(), Dựng 1 sheet ma trận: rows = đối tượng, cols = 12 tháng × cột con + block Tổng…, Tính lại cột % cho dòng TỔNG CỘNG = (khoá phần) / (khoá tổng) * 100. Quy ước:…, subcols : list (header, key, fmt) — cột con lặp cho mỗi tháng year_cols : list…, _set()

### Community 222 - "Community 222"
Cohesion: 0.29
Nodes (9): collect_descendants(), delete_subtree(), insert_node(), main(), Seed nội dung Trung tâm trợ giúp cho phân hệ ĐẶT PHÒNG HỌP. Dựng cây bài viết:…, Sinh slug y hệt `slugify()` của help-center (help-slug.tsx). Portal tra ngược…, Trả [(id, độ sâu)] của cả cây, gồm chính gốc., ref() (+1 more)

### Community 223 - "Community 223"
Cohesion: 0.22
Nodes (7): Celery app dùng chung cho toàn bộ procurement-tool. Import ở mọi nơi: from…, ping(), task, Task kiểm tra hạ tầng Celery (smoke test). Không dùng trong logic nghiệp vụ., Trả lại message để xác nhận worker hoạt động., celery, celery_schedules

### Community 224 - "Community 224"
Cohesion: 0.28
Nodes (9): http_exception_handler(), Exception, Request, Lỗi KHÔNG lường trước — trả đúng phong bì kèm một MÃ SỰ CỐ tra được. Trước…, unhandled_exception_handler(), validation_exception_handler(), exception_handler, HTTPException (+1 more)

### Community 225 - "Community 225"
Cohesion: 0.22
Nodes (9): IssueCodeUpdate, list_issue_codes(), BaseModel, get, patch, Session, Sửa một mã. `kind` là một trong `issue_code_service.KIND_*`., Mọi mã đang đi vào số hiệu, gom theo bốn thẻ của mẫu. (+1 more)

### Community 226 - "Community 226"
Cohesion: 0.25
Nodes (7): parse_field_defs(), BỘ TRƯỜNG TÙY BIẾN của một loại hồ sơ — phần «metadata» của phân hệ Hồ sơ. Mỗi…, Đọc bộ trường ĐÃ LƯU thành đối tượng, bỏ qua dòng hỏng. ⚠️ Khoan dung ở ĐƯỜNG…, is_known(), model_of(), DANH MỤC mà một ô «Chọn từ danh mục» được phép trỏ tới. Trường tùy biến kiểu…, Model của một danh mục. `None` nếu khóa lạ.

### Community 227 - "Community 227"
Cohesion: 0.33
Nodes (8): _apply(), _doi_lo(), downgrade(), _norm(), B-04: chuan hoa tab_survey.approve_status sang ma tieng Anh Revision ID:…, Bo dau + thuong hoa + gom khoang trang., Doi `cu` -> `moi`, cat theo khoang id. Tra so dong da doi. Moc lo lay tu…, upgrade()

### Community 228 - "Community 228"
Cohesion: 0.36
Nodes (8): _grant_pur_staff(), main(), _make_pr(), Dựng dữ liệu DEMO để thử tay bao-CR-310 — gắn PHƯƠNG ÁN lên dòng Yêu cầu mua…, NSTM phải có vai trò thu mua thì mới ghi được YCMH được giao cho mình., _suggest_survey_lines(), _user(), _wipe_old()

### Community 229 - "Community 229"
Cohesion: 0.32
Nodes (6): _move_pos_runs_in(), _payload_type(), Sổ đồng bộ chung `tab_sync_log` — gộp luôn `tab_pos_sync_run` vào P0 của đồng…, Chuyển từng dòng `tab_pos_sync_run` thành một dòng RUN của nguồn `pos365`. Đi…, MEDIUMTEXT ở MySQL, TEXT ở nơi khác (SQLite của test không biết MEDIUMTEXT)., upgrade()

### Community 230 - "Community 230"
Cohesion: 0.29
Nodes (7): openpyxl, openpyxl_utils, openpyxl_worksheet_datavalidation, main(), Sinh tệp Excel RÀ SOÁT BỘ HỒ SƠ NHẬP KHẨU để gửi Phòng Thu mua nhập khẩu — MỘT…, Một khối = dòng hồ sơ + các dòng trường + EXTRA_ROWS dòng trống. Trả về dòng kế., write_block()

### Community 231 - "Community 231"
Cohesion: 0.36
Nodes (7): _check_table(), _load_export(), main(), Đóng dấu `legacy_id` lên `tab_vehicle` và `tab_driver`. Phiếu đặt xe bên app cũ…, Soi lệch giữa bảng tra và bản kết xuất. Trả về True nếu sạch., Gắn `legacy_id` theo bảng tra. Không bao giờ đè khóa khác đang có., stamp()

### Community 232 - "Community 232"
Cohesion: 0.36
Nodes (7): clean_text(), generate_sql_file(), parse_data_file(), Script cap nhat cot invoice_name (Ten tren hoa don) cho tab_product tu…, Doc va parse file datanhan.txt., Tao file SQL chua cac cau lenh UPDATE de nguoi dung luu tru hoac review., run()

### Community 234 - "Community 234"
Cohesion: 0.29
Nodes (7): BoardIn, ModerationIn, BaseModel, Tạo/sửa nhóm hoặc box chuyên mục (F13a) — chỉ `forum_admin` đi được.…, Bấm cảm xúc (CR-206) — `kind` theo `ForumReactionKind`; client cũ gửi `{}` thì…, Ẩn/xóa bài (F5) — `reason` bắt buộc ở service (QĐ-D1: không ẩn lặng lẽ); khôi…, ReactionIn

### Community 235 - "Community 235"
Cohesion: 0.33
Nodes (6): _block_delete_room_in_use(), Chốt `before_delete`: phòng đang có phiếu thì không xóa. Xóa là để lại phiếu mồ…, MeetingRoom, Một phòng họp — tài nguyên được đặt., SEED PHÒNG HỌP — chạy TAY, cố ý không nằm trong `app/seed.py`. docker compose…, seed_rooms()

### Community 236 - "Community 236"
Cohesion: 0.38
Nodes (6): build_rows(), _employee_names(), Session, CR-068 — xuất Excel màn Yêu cầu mua hàng (YCMH/PYC). Mỗi DÒNG HÀNG là một hàng…, Mã NV -> "NV0087 — Trần Minh Đức" cho cột NSTM phụ trách., Bung mỗi phiếu thành các hàng theo dòng hàng, kèm cụm đầu phiếu lặp lại.

### Community 237 - "Community 237"
Cohesion: 0.43
Nodes (6): _apply(), downgrade(), _norm(), CR-118: chuan hoa tab_contract.contract_type sang ma tieng Anh Revision ID:…, Bo dau + thuong hoa + gom khoang trang + bo tien to 'hop dong'., upgrade()

### Community 238 - "Community 238"
Cohesion: 0.38
Nodes (5): _as_date_str(), _backfill(), bao-CR-316 - tach Ngay tiep nhan ra cot rieng `received_date` Truoc CR nay chi…, Ngay cua dau vet: driver tra datetime hay chuoi deu quy ve YYYY-MM-DD., upgrade()

### Community 239 - "Community 239"
Cohesion: 0.43
Nodes (6): _apply(), downgrade(), _norm(), B-02: chuan hoa tab_contract.party_type + status sang ma tieng Anh Revision ID:…, Bo dau + thuong hoa + gom khoang trang., upgrade()

### Community 240 - "Community 240"
Cohesion: 0.38
Nodes (5): _backfill(), _backfill_nspt_qua_ycmh(), them nspt_id (DMH) + head_of_dept_id (YCBG) va dien lui theo ten — CR-087 Nối…, Lượt 3, CHỈ cho ĐMH: đơn còn kẹt vì TRÙNG TÊN thì hỏi YCMH nguồn. Dòng YCMH ghi…, upgrade()

### Community 242 - "Community 242"
Cohesion: 0.33
Nodes (4): BỘ MÃ SỐ CỦA HỒ SƠ — theo R2/QĐ-11 (phân hệ Hồ sơ, 16/09/2026). Cột…, expiry_state(), TÌNH TRẠNG HIỆU LỰC của một hồ sơ — suy ra từ ngày, không lưu cột nào. Tách…, (mã tình trạng hiệu lực, số ngày còn lại). `today` truyền vào được để bài kiểm…

### Community 243 - "Community 243"
Cohesion: 0.33
Nodes (6): assignable_departments(), block_out_of_scope_departments(), Bậc phạm vi rộng nhất mà người này có trên `(entity, action)`. `None` = không…, Những phòng người này được phép GÁN cho người khác. `None` = không giới hạn. ⚠️…, L2 — chỉ gán được phòng nằm trong tầm của chính người thao tác. Không có chốt…, _widest_scope()

### Community 244 - "Community 244"
Cohesion: 0.50
Nodes (3): _check_dates(), model_validator, Hạn hiệu lực không thể TRƯỚC ngày cấp. Cho phép BẰNG nhau — giấy cấp và hết…

### Community 246 - "Community 246"
Cohesion: 0.50
Nodes (3): _audit_columns(), Column, upgrade()

### Community 247 - "Community 247"
Cohesion: 0.50
Nodes (3): _audit_columns(), Column, upgrade()

### Community 248 - "Community 248"
Cohesion: 0.50
Nodes (3): _internal_key(), Suy ra file_key từ URL ảnh cũ, chỉ nhận ảnh nội bộ (đường dẫn có '/avatar/').…, upgrade()

### Community 249 - "Community 249"
Cohesion: 0.50
Nodes (3): _flags(), Cấp mặc định Nghỉ phép + Đặt phòng họp cho MỌI vai trò; cấp quản lý duyệt được…, upgrade()

### Community 250 - "Community 250"
Cohesion: 0.60
Nodes (4): downgrade(), CR-068 - bat quyen `export` (Xuat) cho cac vai tro chuan tren YCMH/YCBG/DMH Cac…, _set(), upgrade()

### Community 251 - "Community 251"
Cohesion: 0.60
Nodes (4): _alter(), downgrade(), Lich su mua hang: don gia len 4 so thap phan (Numeric(18,2) -> Numeric(18,4))…, upgrade()

### Community 252 - "Community 252"
Cohesion: 0.60
Nodes (4): _doi_bieu_thuc(), downgrade(), Van ban: tach trang thai Tra ve / Da tu choi khoi Nhap Revision ID:…, upgrade()

### Community 253 - "Community 253"
Cohesion: 0.50
Nodes (3): _audit_cols(), Bộ cột chuẩn của AuditMixin — mọi bảng trong hệ đều có., upgrade()

### Community 254 - "Community 254"
Cohesion: 0.60
Nodes (4): _alter(), downgrade(), Don gia cho phep 4 so thap phan (Numeric(18,2) -> Numeric(18,4)) Đơn giá nhập…, upgrade()

### Community 255 - "Community 255"
Cohesion: 0.50
Nodes (3): _audit_columns(), Column, upgrade()

### Community 256 - "Community 256"
Cohesion: 0.50
Nodes (3): Thêm NCC "Ngân sách nhà nước" nếu chưa có. Cột của `tab_supplier` đọc từ CHÍNH…, _seed_state_budget_supplier(), upgrade()

### Community 257 - "Community 257"
Cohesion: 0.40
Nodes (5): find_account(), link(), main(), Tra tài khoản theo tên tài xế. Trả về (tài khoản, lý do bỏ qua)., Nối tài khoản cho mọi tài xế nội bộ. Trả về (so noi moi, so bo qua).

### Community 258 - "Community 258"
Cohesion: 0.50
Nodes (3): estimate_cost_usd(), BỘ MÃ CỦA AGENT HUB — số nguyên, theo R2/QĐ-11. Phân hệ này MỚI và không thuộc…, Ước chi phí một lượt gọi. Model lạ -> 0.0 (xem ghi chú ở MODEL_PRICES_USD).…

### Community 259 - "Community 259"
Cohesion: 0.50
Nodes (4): dump_request(), Một dòng đơn để trả ra giao diện. `lines` là bản gom sẵn của…, Nhãn tiếng Việt kèm theo — R2: số ở cột, chữ ở tầng hiển thị., request_labels()

### Community 260 - "Community 260"
Cohesion: 0.83
Nodes (3): downgrade(), _set(), upgrade()

### Community 261 - "Community 261"
Cohesion: 0.83
Nodes (3): downgrade(), _set(), upgrade()

### Community 264 - "Community 264"
Cohesion: 0.83
Nodes (3): _audit_cols(), downgrade(), upgrade()

### Community 265 - "Community 265"
Cohesion: 0.83
Nodes (3): downgrade(), _has_column(), upgrade()

### Community 266 - "Community 266"
Cohesion: 0.83
Nodes (3): downgrade(), _has_col(), upgrade()

### Community 269 - "Community 269"
Cohesion: 0.83
Nodes (3): downgrade(), _has_col(), upgrade()

### Community 271 - "Community 271"
Cohesion: 0.67
Nodes (3): get, Ba loại chữ ký kèm CÂU GIÁ TRỊ PHÁP LÝ của từng loại. Câu đó do backend cấp,…, sign_kinds()

### Community 273 - "Community 273"
Cohesion: 0.67
Nodes (3): ClerkStatus, IntEnum, Trạng thái phân công văn thư (R2/QĐ-11 — cột trạng thái là SMALLINT + IntEnum).…

## Ambiguous Edges - Review These
- `Function naming rules (English verbs only)` → `Knowledge source README — raw files not loaded into bot`  [AMBIGUOUS]
  .claude/rules/naming.md · relation: conceptually_related_to

## Knowledge Gaps
- **33 isolated node(s):** `send_test_event.sh script`, `start.prod.sh script`, `start.sh script`, `Quy trình thu mua DEGO`, `Yêu cầu thanh toán (YCTT)` (+28 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 3810 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **154 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Function naming rules (English verbs only)` and `Knowledge source README — raw files not loaded into bot`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `success()` connect `Community 60` to `Document Access Control`, `Audit, Scoping & Notification`, `Document Controller & Sanitize`, `Legacy Dat Xe Integration`, `Auth Tokens & Permissions`, `Document Clone & Attachment Window`, `Survey Request Controller`, `Core Framework Utilities`, `App Settings & File Access Log`, `Work Controller (Kanban)`, `Attachment Upload Guard`, `Employee Controller`, `Product Catalog Controller`, `Doc Catalog Book Controller`, `Coffee Point POS Ledger`, `Forum Controller`, `Survey Progress Export`, `Community 32`, `Community 35`, `Community 38`, `Community 42`, `Community 44`, `Community 45`, `Community 46`, `Community 48`, `Community 51`, `Community 53`, `Community 54`, `Community 55`, `Community 56`, `Community 61`, `Community 66`, `Community 67`, `Community 71`, `Community 73`, `Community 76`, `Community 77`, `Community 78`, `Community 79`, `Community 80`, `Community 82`, `Community 83`, `Community 84`, `Community 85`, `Community 88`, `Community 89`, `Community 90`, `Community 98`, `Community 99`, `Community 102`, `Community 103`, `Community 104`, `Community 106`, `Community 107`, `Community 108`, `Community 109`, `Community 113`, `Community 118`, `Community 121`, `Community 122`, `Community 124`, `Community 133`, `Community 137`, `Community 140`, `Community 145`, `Community 150`, `Community 162`, `Community 165`, `Community 168`, `Community 179`, `Community 189`, `Community 193`, `Community 195`, `Community 199`, `Community 206`, `Community 210`, `Community 211`, `Community 212`, `Community 215`, `Community 216`, `Community 219`, `Community 225`, `Community 271`?**
  _High betweenness centrality (0.133) - this node is a cross-community bridge._
- **Why does `Employee` connect `Employee Assistant Tool` to `Core Models & Base Mixins`, `Document Access Control`, `Audit, Scoping & Notification`, `Doc Catalog Security Levels`, `Document Controller & Sanitize`, `Approval Flow & Delegation`, `Auth Tokens & Permissions`, `Document Clone & Attachment Window`, `Survey Request Controller`, `Purchase Order & Payable`, `Purchase Request Service`, `Core Framework Utilities`, `App Settings & File Access Log`, `Legacy Dat Xe Export Builder`, `Employee Controller`, `Work Group & Audit`, `Doc Catalog Book Controller`, `Forum Model & Announcement`, `Survey Request Model & Service`, `Coffee Point POS Ledger`, `Forum Controller`, `Work Label & List Config`, `Community 29`, `Survey Progress Export`, `Community 31`, `Community 32`, `Community 33`, `Community 34`, `Community 36`, `Community 37`, `Community 40`, `Community 41`, `Community 42`, `Community 43`, `Community 45`, `Community 57`, `Community 60`, `Community 62`, `Community 63`, `Community 68`, `Community 70`, `Community 71`, `Community 73`, `Community 78`, `Community 80`, `Community 83`, `Community 85`, `Community 87`, `Community 88`, `Community 93`, `Community 101`, `Community 102`, `Community 104`, `Community 106`, `Community 115`, `Community 116`, `Community 117`, `Community 124`, `Community 132`, `Community 137`, `Community 138`, `Community 142`, `Community 143`, `Community 144`, `Community 145`, `Community 150`, `Community 152`, `Community 155`, `Community 163`, `Community 164`, `Community 166`, `Community 170`, `Community 171`, `Community 188`, `Community 193`, `Community 195`, `Community 198`, `Community 203`, `Community 212`, `Community 213`, `Community 216`, `Community 228`, `Community 236`, `Community 257`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Why does `get_perm_profile()` connect `Community 73` to `Core Models & Base Mixins`, `Document Access Control`, `Audit, Scoping & Notification`, `Doc Catalog Security Levels`, `Document Controller & Sanitize`, `Community 135`, `Auth Tokens & Permissions`, `Community 137`, `Survey Request Controller`, `Purchase Request Service`, `Core Framework Utilities`, `App Settings & File Access Log`, `Attachment Upload Guard`, `Community 145`, `Employee Controller`, `Doc Catalog Book Controller`, `Forum Model & Announcement`, `Employee Assistant Tool`, `Forum Controller`, `Survey Progress Export`, `Community 31`, `Community 32`, `Community 33`, `Community 162`, `Community 164`, `Community 37`, `Community 36`, `Community 38`, `Community 168`, `Community 41`, `Community 42`, `Community 44`, `Community 45`, `Community 176`, `Community 48`, `Community 179`, `Community 180`, `Community 53`, `Community 182`, `Community 183`, `Community 56`, `Community 54`, `Community 60`, `Community 61`, `Community 189`, `Community 63`, `Community 66`, `Community 195`, `Community 68`, `Community 70`, `Community 76`, `Community 77`, `Community 78`, `Community 80`, `Community 83`, `Community 85`, `Community 219`, `Community 96`, `Community 97`, `Community 102`, `Community 106`, `Community 108`, `Community 109`, `Community 115`, `Community 118`, `Community 119`, `Community 121`, `Community 127`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 205 inferred relationships involving `Employee` (e.g. with `resolve_actor()` and `resolve_actor_profile()`) actually correct?**
  _`Employee` has 205 INFERRED edges - model-reasoned connections that need verification._
- **What connects `send_test_event.sh script`, `start.prod.sh script`, `start.sh script` to the rest of the system?**
  _33 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Core Models & Base Mixins` be split into smaller, more focused modules?**
  _Cohesion score 0.021658021658021658 - nodes in this community are weakly interconnected._