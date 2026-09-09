/**
 * Dải BA TAB của màn danh sách chuyển sang kiểu **GẠCH CHÂN** ở khổ điện thoại.
 *
 * Truyền vào `className` của `TabsList` / `TabsTrigger` (shadcn). Màn rộng giữ
 * nguyên dải phân đoạn nền xám — ở đó nó co theo nội dung nên không đụng ai.
 *
 * ⚠️ **Vì sao đổi kiểu chứ không chỉ chỉnh khoảng cách.** Trên điện thoại, ngay
 * TRÊN dải này là hàng chuyển màn của phân hệ (`RoomSectionTabs`), cũng ba mục,
 * cũng trải hết bề ngang, cũng chia đều. Hai hàng nút nền đặc xếp chồng nhau
 * thành **sáu ô giống hệt nhau thẳng cột**, sáu cụm chữ tiếng Việt dài xấp xỉ
 * nhau — mắt đọc ra MỘT lưới 2×3 chứ không ra hai cấp điều hướng (khách báo
 * 09/09/2026). Hàng trên giữ nút nền đặc vì nó trả lời câu *đang ở màn nào*;
 * hàng này hạ xuống gạch chân để nói *đang xem nhóm nào*. Cùng cách
 * `LeaveSectionTabs` tách hàng tab con của nó (`SubTabLink`).
 *
 * ⚠️ **CHIỀU CAO PHẢI GIỮ NGUYÊN 36px** (`h-9`), đó là lý do `LIST_TAB_LIST` vẫn
 * khai `max-md:h-9` dù kiểu gạch chân tự nó chỉ cần ~30px. Mốc `top` của thanh
 * công cụ ghim (`LIST_TOOLBAR_STICKY` = `top-11` = 44px) bằng đúng 36px của dải
 * này cộng 8px đệm dưới. Để nó co lại thì thanh công cụ ghim thấp hơn đáy dải
 * tab 6px, và nội dung chạy qua khe hở đó khi cuộn — lỗi chỉ lộ ra lúc cuộn,
 * không lộ lúc dựng màn. Xem `list-sticky.ts`.
 *
 * ⚠️ `-mb-px` để gạch chân của tab đang mở đè đúng lên đường viền dưới của dải,
 * không nằm cách nó một pixel.
 */

/** Dải bọc — bỏ nền xám, trải hết hàng, chỉ còn một đường kẻ chân. */
export const LIST_TAB_LIST =
  'max-md:h-9 max-md:w-full max-md:rounded-none max-md:border-b max-md:bg-transparent max-md:p-0'

/** Một tab — chữ + gạch chân thay cho ô nền trắng đổ bóng. */
export const LIST_TAB_TRIGGER =
  'max-md:-mb-px max-md:h-full max-md:min-w-0 max-md:rounded-none max-md:border-0 max-md:border-b-2 max-md:border-transparent max-md:px-1 max-md:text-xs max-md:data-[state=active]:border-primary max-md:data-[state=active]:bg-transparent max-md:data-[state=active]:font-semibold max-md:data-[state=active]:shadow-none'
