/**
 * Returns valid week numbers for a given year/month.
 * Week 1 = days 1-7, Week 2 = days 8-14, etc.
 */
export function validWeeksForMonth(year: number, month: number): number[] {
  const daysInMonth = new Date(year, month, 0).getDate()
  const weeks: number[] = []
  let day = 1
  let weekNo = 1
  while (day <= daysInMonth) {
    weeks.push(weekNo)
    day += 7
    weekNo++
  }
  return weeks
}

/**
 * Returns a human-readable label for the week period.
 * e.g. "2026년 3월 2주 (3/8~3/14)"
 */
export function weekLabel(year: number, month: number, weekNo: number): string {
  const start = (weekNo - 1) * 7 + 1
  const daysInMonth = new Date(year, month, 0).getDate()
  const end = Math.min(start + 6, daysInMonth)
  return `${year}년 ${month}월 ${weekNo}주 (${month}/${start}~${month}/${end})`
}

/**
 * Returns start/end date strings for the week period.
 */
export function weekDateRange(year: number, month: number, weekNo: number): { start: string; end: string } {
  const startDay = (weekNo - 1) * 7 + 1
  const daysInMonth = new Date(year, month, 0).getDate()
  const endDay = Math.min(startDay + 6, daysInMonth)

  const pad = (n: number) => String(n).padStart(2, "0")
  const start = `${year}-${pad(month)}-${pad(startDay)}`
  const end = `${year}-${pad(month)}-${pad(endDay)}`
  return { start, end }
}
