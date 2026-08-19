/**
 * CHIA NỘI DUNG THÀNH TỪNG TRANG A4 cho bản in.
 *
 * Vì sao phải tự chia thay vì để trình duyệt tự ngắt trang: **số trang**. Nghị
 * định 30 điều 8 bắt đánh số trang ở lề trên, canh giữa, từ trang 2 trở đi — mà
 * CSS `counter(page)` chỉ chạy trong ô lề của `@page`, thứ Chrome/Safari/Firefox
 * đều chưa dựng. Tự gom khối vào từng tờ thì mỗi tờ là một thẻ riêng, muốn in số
 * mấy lên đó cũng được, và người dùng thấy đúng số trang mà máy in sẽ nhả ra.
 *
 * Hàm này THUẦN: chiều cao do nơi gọi đo trên DOM thật rồi truyền vào.
 */

export interface PrintBlock {
  /** HTML của khối (`outerHTML` của một thẻ con trực tiếp trong thân bài). */
  html: string
  /** Chiều cao đo được (px). */
  height: number
  /** Khe cách với khối đứng trước (px) — rơi xuống đầu trang thì bỏ. */
  spaceBefore: number
}

/**
 * Gom khối vào từng trang theo đúng thứ tự.
 *
 * ⚠️ Khối CAO HƠN CẢ TRANG (bảng dài, ảnh lớn) được để đứng riêng một tờ và
 * **tràn tiếp sang tờ sau khi in** — hàm không cắt đôi một khối vì cắt sai chỗ
 * còn tệ hơn tràn. Nơi gọi đếm số khối như vậy để nói ra cho người dùng biết,
 * xem `oversizedCount`.
 */
export function splitBlocksIntoPages(blocks: PrintBlock[], pageHeight: number): PrintBlock[][] {
  if (pageHeight <= 0) return blocks.length ? [blocks] : []

  const pages: PrintBlock[][] = []
  let current: PrintBlock[] = []
  let used = 0

  for (const block of blocks) {
    //  Khe chỉ tính khi khối đứng giữa trang: đầu trang thì lề trên đã chừa rồi.
    const gap = current.length ? block.spaceBefore : 0

    if (current.length && used + gap + block.height > pageHeight) {
      pages.push(current)
      current = []
      used = 0
    }

    current.push(block)
    used += (current.length > 1 ? block.spaceBefore : 0) + block.height
  }

  if (current.length) pages.push(current)
  return pages
}

/** Số khối cao hơn cả một trang — những chỗ bản in sẽ tràn, cần nói ra. */
export function oversizedCount(blocks: PrintBlock[], pageHeight: number): number {
  if (pageHeight <= 0) return 0
  return blocks.filter((block) => block.height > pageHeight).length
}
