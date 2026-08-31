/**
 * Lớp CSS của ô GHIM trái — cột «Tên công việc» ở lưới trái của khung nhìn Gantt.
 *
 * Các cột trượt ngang chui xuống dưới ô tên, nên phải có gì đó nói được "nội
 * dung đang chạy VÀO PHÍA SAU ô này" — nếu không thì cạnh cột tên chỉ là một mớ
 * nửa chữ, nhìn như lỗi vẽ. Ở đây thứ ấy là **bóng đổ, và CHỈ bóng đổ**.
 *
 * ⚠️ **KHÔNG vẽ vạch dọc.** Bản đầu có `inset -1px` làm vạch ngăn (đúng lối cột
 * ghim của `DataTable` dùng chung); khách bỏ ngay 31/08/2026 — *"cột tên công
 * việc ko có border như này nha, bỏ đi"*. Lưới này theo lối Lark: chỉ có vạch
 * NGANG mảnh giữa các dòng, tuyệt đối không kẻ dọc. Đừng thêm lại.
 *
 * **Bóng chỉ hiện khi đã cuộn ngang** — chưa cuộn thì chẳng có gì ở sau, đổ bóng
 * lên nền trơn là tự bịa ra một tầng lớp không có thật, và lúc ấy mép ô tên lại
 * thành một đường kẻ dọc đúng thứ vừa bỏ. Trạng thái ấy đánh dấu bằng
 * `data-scrolled-x` trên chính KHUNG CUỘN của lưới (`gantt-view.tsx`), nhờ vậy
 * khỏi luồn thêm một prop qua bốn tầng component chỉ để bật một cái bóng.
 *
 * Nền để NGOÀI: mỗi chỗ dùng một nền khác nhau (dòng việc `bg-canvas`, hàng tiêu
 * đề `bg-muted`, dòng đang soạn `bg-accent/30`) nhưng nền phải ĐỤC — nền trong
 * là chữ chồng lên chữ.
 */
export const PINNED_TITLE_CELL =
  'sticky left-0 z-10 [[data-scrolled-x]_&]:shadow-[6px_0_8px_-6px_rgb(0_0_0/0.18)]'

/**
 * Kéo ô ghim CAO BẰNG CẢ DÒNG — dán kèm `PINNED_TITLE_CELL` ở **dòng việc** và
 * **dòng nháp** (hàng tiêu đề thì không, xem bên dưới).
 *
 * ⚠️ Đây là gốc của lỗi "chip đè lên cột tên" mà khách báo ba lần. Dòng để
 * `items-center` nên ô tên chỉ cao bằng NỘI DUNG của nó — đo thật: dòng cao
 * 44px, ô tên **24px**, mà viên chip trạng thái cao **32px**. Ô tên vì thế chỉ
 * che được khúc giữa; 4px trên và 4px dưới của viên chip vẫn ló ra hai bên khối
 * nền, đúng cái vệt bo tròn nhìn như chip nằm ĐÈ lên tên việc. Không phải lỗi
 * `z-index`, cũng không phải nền trong suốt — nền có đủ, chỉ là **thiếu chiều
 * cao**.
 *
 * `self-stretch` kéo ô cao bằng hộp NỘI DUNG của dòng, nhưng thế vẫn hụt: dòng
 * có `py-1.5` nên hộp nội dung chỉ 31px, còn thiếu 1px so với viên chip. `-my-1.5`
 * ăn nốt hai vạt đệm ấy → ô ghim cao đúng cả dòng (trừ `border-b`, thứ nằm ngoài
 * hộp nội dung nên vạch kẻ ngang KHÔNG bị nền của ô ghim nuốt mất).
 *
 * Hàng TIÊU ĐỀ cố ý không dùng: nó xếp `items-end` để nhãn cột nằm sát đáy, kéo
 * cao ra là nhãn nhảy lên đỉnh; mà hàng ấy cũng không có gì để che — các ô tiêu
 * đề đều là chữ trơn cùng một đường chân, không có viên chip nào cao hơn.
 */
export const PINNED_TITLE_FULL_HEIGHT = 'self-stretch -my-1.5'
