/**
 * Dải TAB chuyển sang kiểu **GẠCH CHÂN** ở khổ điện thoại.
 *
 * Truyền vào `className` của `TabsList` / `TabsTrigger` (shadcn). Màn rộng giữ
 * nguyên dải phân đoạn nền xám — ở đó nó co theo nội dung nên không đụng ai.
 *
 * ⚠️ **Vì sao đổi kiểu chứ không chỉ chỉnh khoảng cách.** Rãnh xám của
 * `TabsList` là `bg-muted`, mà trong bảng màu này `--muted` **trùng đúng nền
 * trang** (`rgb(246 248 251)`, đo 10/09/2026). Nghĩa là thứ lẽ ra gom các tab
 * lại thành MỘT bộ điều khiển thì vô hình: người dùng chỉ thấy một viên trắng
 * nổi cạnh một dòng chữ xám, hai thứ trông như hai loại phần tử khác nhau chứ
 * không như hai lựa chọn của cùng một chỗ (khách báo *"nhìn nó rời rạc quá"*).
 * Kiểu gạch chân không cần rãnh: đường kẻ chân trải hết bề ngang là cái neo,
 * và vạch màu chính nói tab nào đang mở.
 *
 * Dùng ở **hai chỗ, hai lý do khác nhau**:
 *
 * - **Trang chi tiết CRUD** (`CrudDetailPage`) — lý do ở trên.
 * - **Màn Phiếu đặt phòng** — ở đó còn một lý do riêng: ngay TRÊN dải này là
 *   hàng chuyển màn của phân hệ (`RoomSectionTabs`), cũng ba mục, cũng trải hết
 *   bề ngang, cũng chia đều. Hai hàng nút nền đặc xếp chồng thành **sáu ô giống
 *   hệt nhau thẳng cột**, mắt đọc ra MỘT lưới 2×3 chứ không ra hai cấp điều
 *   hướng (khách báo 09/09/2026). Hàng trên giữ nút nền đặc vì nó trả lời câu
 *   *đang ở màn nào*; hàng dưới hạ xuống gạch chân để nói *đang xem nhóm nào*.
 *
 * ⚠️ **CHIỀU CAO PHẢI GIỮ NGUYÊN 36px** (`h-9`) — đó là lý do `TAB_LIST_UNDERLINE`
 * vẫn khai `max-md:h-9` dù kiểu gạch chân tự nó chỉ cần ~30px. Ở màn Phiếu đặt
 * phòng, mốc `top` của thanh công cụ ghim (`LIST_TOOLBAR_STICKY` = `top-11` =
 * 44px) bằng đúng 36px của dải này cộng 8px đệm dưới. Để nó co lại thì thanh
 * công cụ ghim thấp hơn đáy dải tab 6px và nội dung chạy qua khe hở đó khi cuộn
 * — lỗi chỉ lộ ra lúc cuộn, không lộ lúc dựng màn. Xem `hr/utils/list-sticky.ts`.
 *
 * ⚠️ `-mb-px` để gạch chân của tab đang mở đè đúng lên đường viền dưới của dải,
 * không nằm cách nó một pixel.
 */

/** Dải bọc — bỏ nền xám, trải hết hàng, chỉ còn một đường kẻ chân. */
export const TAB_LIST_UNDERLINE =
  'max-md:h-9 max-md:w-full max-md:rounded-none max-md:border-b max-md:bg-transparent max-md:p-0'

/** Một tab — chữ + gạch chân thay cho ô nền trắng đổ bóng. */
export const TAB_TRIGGER_UNDERLINE =
  'max-md:-mb-px max-md:h-full max-md:min-w-0 max-md:rounded-none max-md:border-0 max-md:border-b-2 max-md:border-transparent max-md:px-1 max-md:text-xs max-md:data-[state=active]:border-primary max-md:data-[state=active]:bg-transparent max-md:data-[state=active]:font-semibold max-md:data-[state=active]:shadow-none'

/**
 * Bản gạch chân ở **MỌI khổ màn hình** (01/10/2026) — cho chỗ mà ngay cả màn rộng cũng đã có một
 * điều khiển phân đoạn nền đặc khác ở gần (vd trang chi tiết thuốc BVTV: tab thân trang + bộ chọn
 * «Cùng công ty / Cùng hoạt chất» bên trong). Hai dải nền đặc chồng nhau đọc ra MỘT lưới, không ra
 * hai cấp — cùng lý do màn Phiếu đặt phòng ở trên, chỉ là xảy ra cả ở màn rộng.
 */
export const TAB_LIST_UNDERLINE_ALWAYS =
  'h-auto w-full justify-start gap-6 rounded-none border-b bg-transparent p-0'

export const TAB_TRIGGER_UNDERLINE_ALWAYS =
  '-mb-px h-10 flex-none rounded-none border-0 border-b-2 border-transparent bg-transparent px-0 text-muted-foreground shadow-none data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:font-semibold data-[state=active]:text-foreground data-[state=active]:shadow-none dark:data-[state=active]:bg-transparent'
