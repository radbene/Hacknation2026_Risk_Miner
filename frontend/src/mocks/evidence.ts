/** Evidence registry for mocks: every quote is a verbatim value of a real BZP notice section or xlsx cell. */
import type { Schemas } from '@/api/client'
import { MIRROR, NOTICE_PAGE, uid } from './ids'
import noticesJson from './notices.json'

export type RawNotice = {
  object_id: string; notice_type: string; ocid: string; published_at: string; title: string | null
  org_name: string | null; org_nip: string | null; contractors: Record<string, unknown>[]
  sections: { section: string; label: string; value: string }[]
}
export const RAW_NOTICES = noticesJson as unknown as Record<string, RawNotice>

export const EVIDENCE = new Map<string, Schemas['EvidenceOut']>()
const RETRIEVED = '2026-11-21T15:40:00Z'
export const XLSX_SHA = '4b1f0c3a9e2d7c51f0b8a6e3d2c1b0a9f8e7d6c5b4a3928170615243342516a7'

export const noticeId = (no: string) => uid('notice', no)

/** Evidence pointing at one numbered section of a notice (quote = the section value, or a substring of it). */
export function evSec(no: string, section: string, quote?: string): string {
  const n = RAW_NOTICES[no]
  const s = n?.sections.find((x) => x.section === section)
  const id = uid('ev', no, section, quote ?? '')
  if (!EVIDENCE.has(id)) {
    EVIDENCE.set(id, {
      id, source_code: 'bzp', kind: 'notice_section',
      url: n ? NOTICE_PAGE(n.object_id) : null, retrieved_from: n ? MIRROR(n.object_id) : null, retrieved_at: RETRIEVED,
      locator: { notice_number: no, notice_type: n?.notice_type, section, label: s?.label },
      quote: quote ?? s?.value ?? null, quote_verified: true, notice_id: noticeId(no),
    })
  }
  return id
}

/** Evidence pointing at a cell of the organizer xlsx. */
export function evXlsx(row: number, column: string, value: string, code: string): string {
  const id = uid('ev', 'xlsx', code, column)
  if (!EVIDENCE.has(id)) {
    EVIDENCE.set(id, {
      id, source_code: 'organizer_xlsx', kind: 'xlsx_cell', url: null, retrieved_from: 'Risk_Miner_dane_projekty.xlsx',
      retrieved_at: '2026-11-21T14:05:00Z', locator: { file: 'Risk_Miner_dane_projekty.xlsx', sheet: 'Projekty', row, column },
      quote: value, quote_verified: true, import_sha256: XLSX_SHA,
    })
  }
  return id
}

/** Calculation evidence: inputs (evidence ids) + formula + result. */
export function evCalc(key: string, formula: string, inputs: string[], result: string, values?: Record<string, unknown>): string {
  const id = uid('ev', 'calc', key)
  if (!EVIDENCE.has(id)) {
    EVIDENCE.set(id, {
      id, source_code: 'riskminer', kind: 'derivation', url: null, retrieved_at: RETRIEVED, locator: {},
      quote: null, derivation: { formula, inputs, result, values: values ?? {} },
    })
  }
  return id
}

/** External register (Biała lista VAT). */
export function evVat(nip: string, name: string): string {
  const id = uid('ev', 'vat', nip)
  if (!EVIDENCE.has(id)) {
    EVIDENCE.set(id, {
      id, source_code: 'vat_whitelist', kind: 'register', url: `https://wl-api.mf.gov.pl/api/search/nip/${nip}?date=2026-11-21`,
      retrieved_from: null, retrieved_at: RETRIEVED, locator: { field: 'name' }, quote: name, quote_verified: true,
    })
  }
  return id
}

/** Fragment of an uploaded document (PDF page / DOCX paragraph). */
export function evDoc(docId: string, page: number, quote: string, extra: Record<string, unknown> = {}): string {
  const id = uid('ev', 'doc', docId, page, quote.slice(0, 30))
  if (!EVIDENCE.has(id)) {
    EVIDENCE.set(id, {
      id, source_code: 'upload', kind: 'document_chunk', url: `/api/documents/${docId}/file`, retrieved_at: RETRIEVED,
      locator: { page, ...extra }, quote, quote_verified: true, document_id: docId,
    })
  }
  return id
}
