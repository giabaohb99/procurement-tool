/** Hai chữ cái cuối của tên ("Nguyễn Văn An" → "VA") cho AvatarFallback. */
export function authorInitials(name: string): string {
  return (
    name
      .trim()
      .split(/\s+/)
      .slice(-2)
      .map((part) => part[0]?.toUpperCase())
      .join('') || '?'
  )
}
