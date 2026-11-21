/** Deterministic fake UUIDs for mocks (FNV-1a over the key → 32 hex chars). */
export function uid(...key: (string | number)[]): string {
  const s = key.join(':')
  let hex = ''
  for (let round = 0; hex.length < 32; round++) {
    let h = 0x811c9dc5 ^ round
    for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0 }
    hex += h.toString(16).padStart(8, '0')
  }
  hex = hex.slice(0, 32)
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-5${hex.slice(13, 16)}-a${hex.slice(17, 20)}-${hex.slice(20, 32)}`
}

export const NOTICE_PAGE = (objectId: string) => `https://ezamowienia.gov.pl/mo-client-board/bzp/notice-details/id/${objectId}`
export const NOTICE_PDF = (objectId: string) => `https://ezamowienia.gov.pl/mo-board/api/v1/Board/GetNoticePdfById?noticeId=${objectId}`
export const MIRROR = (objectId: string) => `https://bzp.cytr.us/mo-board/api/v1/notice?ObjectId=${objectId}`
