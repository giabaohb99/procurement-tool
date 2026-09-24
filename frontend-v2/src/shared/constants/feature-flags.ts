/**
 * CÔNG TẮC TÍNH NĂNG — bật/tắt một phần giao diện bằng đúng một dòng.
 *
 * Chỉ dùng cho thứ đã dựng xong nhưng tạm **chưa cho người dùng thấy**. Tính
 * năng chưa làm thì đừng khai ở đây: một cái cờ luôn `false` từ ngày ra đời là
 * mã chết mang hình dạng cấu hình.
 */

/**
 * Phân hệ **HỒ SƠ** — tạm ẩn khỏi giao diện (21/09/2026, đại ca yêu cầu).
 *
 * Tắt cờ này giấu phân hệ ở **cả hai chỗ nó xuất hiện**, và phải giấu cả hai
 * cùng lúc — giấu mỗi thẻ ngoài màn chọn phân hệ thì thẻ «Hồ sơ cần kèm» vẫn
 * nằm giữa bốn trang chứng từ Thu mua, còn người dùng thì không có màn nào để
 * đi quản lý đống hồ sơ mà nó đang đòi:
 *
 * 1. **Bản thân phân hệ** — `module-registry.ts` không đăng ký `dossierModule`
 *    nữa, nên không có thẻ trên màn chọn phân hệ, không có mục thanh bên, và gõ
 *    thẳng `/dossier/...` lên URL cũng ra 404 (route không tồn tại).
 * 2. **Bốn thẻ cắm trong phân hệ THU MUA** — «Hồ sơ cần kèm»
 *    (`RequiredDossiersCard`) ở chi tiết YCMH · ĐMH · Phiếu khảo sát, và «Hồ sơ
 *    cần hoàn thành» (`DossierChecklistCard`) ở chi tiết YCBG.
 *
 * ⚠️ **Backend KHÔNG tắt theo.** Bảng `tab_dossier`, các đường `/api/dossiers/*`
 * và hai khóa quyền `dossier` · `dossier_type` vẫn còn nguyên — đây là công tắc
 * của giao diện, không phải của dữ liệu. Dữ liệu ai đã nhập vẫn nằm đó và hiện
 * lại đầy đủ khi bật cờ.
 *
 * Bật lại: đổi `false` thành `true`, không cần sửa chỗ nào khác.
 *
 * Khai kiểu `boolean` chứ không để TypeScript suy ra kiểu `false`: để kiểu chữ
 * thì mọi nhánh dùng nó thành "không bao giờ chạy" dưới mắt công cụ, và trình
 * soạn thảo tô xám cả bốn thẻ như mã chết.
 */
export const DOSSIER_UI_ENABLED: boolean = false
