/**
 * DẢI MỜ ngay sau ô tên ghim của lưới trái Gantt — đặt BÊN TRONG ô ghim.
 *
 * Cột ghim thì các cột khác trượt vào phía sau nó, và mép ghim cắt ngang bất cứ
 * thứ gì đang ở đó: hay gặp nhất là viên chip trạng thái bị xẻ đôi («…g mở»,
 * «…ã hủy») — khách chê đúng chỗ này ba lần. Vạch dọc và bóng đổ
 * (`PINNED_TITLE_CELL`) nói được "nội dung chạy vào phía sau ô tên" nhưng không
 * làm nửa viên chip kia biến mất. Dải này thì làm: 16px cuối cùng của thứ đang
 * chui vào **tan dần** thay vì đứt ngang.
 *
 * ⚠️ Nền lấy `bg-inherit`, KHÔNG gõ màu: ba nơi ghim có ba nền khác nhau (dòng
 * việc `bg-canvas`, hàng tiêu đề `bg-muted`, dòng nháp `bg-accent/30`), gõ cứng
 * một màu là hai chỗ còn lại lòi ra một vệt lạ. Kế thừa thì nó luôn đúng, kể cả
 * khi bảng màu đổi.
 *
 * Hình mờ vẽ bằng `mask` chứ không phải `linear-gradient` làm nền: gradient thì
 * phải biết màu ĐẦU là gì (tức lại gõ cứng), còn mask chỉ cắt độ đục của cái nền
 * đã kế thừa được.
 *
 * Chỉ hiện khi lưới ĐÃ cuộn ngang (`data-scrolled-x`, xem `gantt-view.tsx`) —
 * chưa cuộn thì sau ô tên chẳng có gì để mà làm mờ, để dải ở đó chỉ tổ vẽ một
 * vệt loang vô cớ lên cột kế bên.
 */
export function PinnedColumnFade() {
  return (
    <span
      aria-hidden
      className="pointer-events-none absolute inset-y-0 left-full w-4 bg-inherit opacity-0 transition-opacity [-webkit-mask-image:linear-gradient(to_right,black,transparent)] [mask-image:linear-gradient(to_right,black,transparent)] [[data-scrolled-x]_&]:opacity-100"
    />
  )
}
