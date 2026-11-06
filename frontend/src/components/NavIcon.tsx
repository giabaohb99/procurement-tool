/**
 * Biểu tượng của một mục menu trái, kèm BÓNG ĐỎ đếm phiếu chờ duyệt ở góc trên bên phải (duoc-CR-723).
 *
 * Bóng chỉ vẽ khi số > 0 — số 0 trên menu là nhiễu. Quá 99 thì ghi "99+" cho bóng không phình ra che chữ.
 * `aria-label` đọc thành câu cho trình đọc màn hình, vì một con số trần cạnh tên mục không nói nó đếm gì.
 */
export default function NavIcon({ icon, count = 0 }: { icon: string; count?: number }) {
  return (
    <span className="nav-icon">
      <i className={'ti ' + icon} />
      {count > 0 && (
        <span className="nav-badge" aria-label={`${count} phiếu đang chờ duyệt`}>
          {count > 99 ? '99+' : count}
        </span>
      )}
    </span>
  )
}
