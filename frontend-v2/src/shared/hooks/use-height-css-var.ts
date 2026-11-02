import { useCallback } from 'react'

/**
 * Ghi CHIỀU CAO của một phần tử vào biến CSS `name` trên phần tử CHA của nó, cập nhật
 * mỗi khi phần tử đổi cỡ. Trả về một callback ref để gắn vào phần tử cần đo.
 *
 * Sinh ra cho màn chi tiết nhân sự (duoc-CR-708): thanh bên phải phải dính ngay DƯỚI cụm
 * tiêu đề + dải tab đang dính, mà cụm đó cao bao nhiêu thì tùy khổ màn (dải tab xuống
 * một hay hai hàng, tên dài xuống dòng) — gán cứng `top-[101px]` là lệch ở khổ khác.
 *
 * ⚠️ Ghi thẳng vào `style` chứ không qua state: đổi cỡ bắn liên tục khi kéo cửa sổ, đi
 * qua React là vẽ lại cả trang mỗi lần. Callback ref (không phải `useRef` + effect) vì
 * phần tử thường chỉ xuất hiện SAU khi dữ liệu tải xong — effect chạy lúc mount sẽ gặp
 * `null` và không bao giờ chạy lại. Hàm dọn trả về từ ref là tính năng của React 19.
 */
export function useHeightCssVar(name: string) {
  return useCallback(
    (el: HTMLElement | null) => {
      const target = el?.parentElement
      if (!el || !target) return
      const write = () => target.style.setProperty(name, `${el.offsetHeight}px`)
      write()
      const observer = new ResizeObserver(write)
      observer.observe(el)
      return () => {
        observer.disconnect()
        target.style.removeProperty(name)
      }
    },
    [name],
  )
}
