/** Document mocks: a print of the real Nowogard contract notice (public/mock/*.pdf) as an uploaded PDF. */
import type { Schemas } from '@/api/client'
import { evDoc } from './evidence'
import { uid } from './ids'
import { projectId } from './projects'

export const NG_DOC_ID = uid('document', 'nowogard-cn-pdf')
export const MOCK_DOC_FILES: Record<string, string> = { [NG_DOC_ID]: '/mock/ogloszenie-2025-BZP-00113651.pdf' }

export const mockDocuments: Schemas['DocumentOut'][] = [
  { id: NG_DOC_ID, project_id: projectId('RM-2026-020'), doc_type: 'Ogłoszenie o zamówieniu', phase: 'postępowanie', title: 'Ogłoszenie o zamówieniu 2025/BZP 00113651/01 (PDF)',
    url: 'https://ezamowienia.gov.pl/mo-board/api/v1/Board/GetNoticePdfById?noticeId=08dd51ab-134e-2276-8f1b-b600017c84ad', file_name: 'ogloszenie-2025-BZP-00113651.pdf',
    mime: 'application/pdf', sha256: 'demo', version: 1, pages: 7, source_code: 'upload', retrieved_at: '2026-11-21T16:44:00Z', text_status: 'text_layer',
    created_at: '2026-11-21T16:44:00Z', status: 'approved', method: 'upload', confidence: 1, evidence_ids: [] },
]

export const NG_DOC_EV = {
  lump: evDoc(NG_DOC_ID, 3, 'Cena oferty stanowi wynagrodzenie ryczałtowe', { section: '4.3.1' }),
  period: evDoc(NG_DOC_ID, 3, 'Okres realizacji zamówienia albo umowy ramowej', { section: '4.2.10' }),
  changes: evDoc(NG_DOC_ID, 6, 'Rodzaj i zakres zmian umowy', { section: '7.4' }),
}

export const mockChunks: Record<string, Schemas['ChunkOut'][]> = {
  [NG_DOC_ID]: [
    { id: uid('chunk', NG_DOC_ID, 1), document_id: NG_DOC_ID, ord: 1, page: 3, section: '4.3.1', locator: { page: 3 },
      text: '1. Wykonawca poda cenę oferty w Formularzu ofertowym … 2. Cena oferty stanowi wynagrodzenie ryczałtowe. 3. Podstawą do obliczenia ceny jest Program Funkcjonalno-Użytkowy.' },
    { id: uid('chunk', NG_DOC_ID, 2), document_id: NG_DOC_ID, ord: 2, page: 6, section: '7.4', locator: { page: 6 },
      text: 'Rodzaj i zakres zmian umowy oraz warunki ich wprowadzenia: 1. Wszelkie zmiany niniejszej umowy wymagają aneksu …' },
  ],
}
