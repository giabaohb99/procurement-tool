/**
 * Gỡ khóa `pointer-events: none` mà Radix đặt lên <body> khi mở modal.
 *
 * Radix tự gỡ khi đóng đúng quy trình, nhưng chỉ cần một lần unmount lệch nhịp
 * (điều hướng ngay lúc đang đóng, HMR, component cha biến mất...) là khóa ở lại
 * và TOÀN BỘ trang mất click — biểu hiện hay gặp là menu "..." bấm không mở.
 *
 * Gọi sau mỗi lần đóng hộp thoại. Chỉ gỡ khi thực sự không còn lớp phủ nào đang mở.
 */
export function releaseBodyLock(delay = 320) {
  setTimeout(() => {
    const stillOpen = document.querySelector(
      '[role="dialog"][data-state="open"], [role="alertdialog"][data-state="open"], [role="menu"][data-state="open"]',
    )
    if (!stillOpen && document.body.style.pointerEvents === 'none') {
      document.body.style.removeProperty('pointer-events')
    }
  }, delay)
}
