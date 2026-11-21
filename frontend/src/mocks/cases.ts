/** Deep case mocks: Nowogard RM-2026-020 (2 changes art. 455 ust. 1 pkt 4 → R03, R02) and
 * Wolin RM-2026-022 (number in xlsx not in BZP → uncertain link with a decoy). Values from the real notices. */
import type { Schemas } from '@/api/client'
import { evCalc, evSec, evVat, evXlsx, noticeId, RAW_NOTICES } from './evidence'
import { NOTICE_PAGE, NOTICE_PDF, MIRROR, uid } from './ids'
import { mockProjectItems, ORGANIZER_ROWS, projectId } from './projects'

type S = Schemas
const NOW = '2026-11-21T16:30:00Z'

export function noticeOut(no: string, procId?: string): S['NoticeDetail'] {
  const n = RAW_NOTICES[no]
  return {
    id: noticeId(no), object_id: n.object_id, notice_number: no, notice_type: n.notice_type, ocid: n.ocid,
    procedure_id: procId ?? null, published_at: n.published_at, title: n.title, org_name: n.org_name, org_nip: n.org_nip,
    url: NOTICE_PAGE(n.object_id), pdf_url: NOTICE_PDF(n.object_id), retrieved_from: MIRROR(n.object_id),
    retrieved_at: '2026-11-21T15:40:00Z', contractors: n.contractors, xrefs: [], parsed: {},
    canonical_text: n.sections.map((s) => `${s.section}.) ${s.label}: ${s.value}`).join('\n'),
    sections: n.sections.map((s) => ({ ...s, offset: null, part_no: null })),
  }
}

function rowIndex(code: string) { return ORGANIZER_ROWS.findIndex((r) => r[0] === code) + 2 }

export interface CaseBundle {
  detail: S['ProjectDetail']
  procedures: S['ProcedureOut'][]
  contracts: S['ContractOut'][]
  notices: S['NoticeDetail'][]
  links: S['LinkOut'][]
  candidates: S['LinkCandidate'][]
  timeline: S['TimelineOut']
  graph: S['GraphOut']
  events: S['EventOut'][]
  issues: S['DataIssueOut'][]
  history: S['ReviewOut'][]
}

/* ------------------------------------------------------------------ Nowogard RM-2026-020 */
const NG = 'RM-2026-020'
const ngPid = projectId(NG)
const ngProc = uid('procedure', 'ocds-148610-740158c8-9281-4fe9-9f58-59edc56af25c')
const ngContract = uid('contract', ngProc, 1)
const NG_CN = '2025/BZP 00113651/01', NG_TR = '2025/BZP 00206455/01', NG_AU1 = '2025/BZP 00558908/01',
  NG_AU2 = '2026/BZP 00280220/01', NG_CP = '2026/BZP 00291637/01'

const ngEv = {
  kpo: evXlsx(rowIndex(NG), 'Identyfikator publiczny', 'KPOD.03.15-IW.28-0003/24', NG),
  title: evXlsx(rowIndex(NG), 'Nazwa przedsięwzięcia', 'Budowa kanalizacji sanitarnej wraz z oczyszczalnią ścieków na terenie gminy Nowogard w m. Konarzewo', NG),
  nip: evXlsx(rowIndex(NG), 'Identyfikator odbiorcy', '8590012007', NG),
  annot: evXlsx(rowIndex(NG), 'Adnotacja instytucji', 'Wartość przedsięwzięcia: 1 749 991,33 zł; dofinansowanie: 1 414 257,17 zł', NG),
  cnTitle: evSec(NG_CN, '2.3'), cnCpv: evSec(NG_CN, '4.2.6'), cnPeriod: evSec(NG_CN, '4.2.10'), cnEu: evSec(NG_CN, '2.14'),
  cnMode: evSec(NG_CN, '2.16'), cnOffersDate: evSec(NG_CN, '8.1'), cnChanges: evSec(NG_CN, '7.4'),
  trEst: evSec(NG_TR, '4.3'), trOffers: evSec(NG_TR, '6.1'), trLow: evSec(NG_TR, '6.2'), trHigh: evSec(NG_TR, '6.3'),
  trSigned: evSec(NG_TR, '8.1'), trValue: evSec(NG_TR, '8.2'), trPeriod: evSec(NG_TR, '8.3'), trXref: evSec(NG_TR, '2.14'),
  au1Basis: evSec(NG_AU1, '5.2'), au1Reason: evSec(NG_AU1, '5.3'), au1Desc: evSec(NG_AU1, '5.4'), au1Date: evSec(NG_AU1, '5.1'),
  au2Basis: evSec(NG_AU2, '5.2'), au2Reason: evSec(NG_AU2, '5.3'), au2Desc: evSec(NG_AU2, '5.4'), au2Date: evSec(NG_AU2, '5.1'),
  cpEnd: evSec(NG_CP, '5.2'), cpOnTime: evSec(NG_CP, '5.3'), cpPaid: evSec(NG_CP, '5.5'), cpProper: evSec(NG_CP, '5.6'),
  cpChanges: evSec(NG_CP, '5.4.1'), cpXref: evSec(NG_CP, '4.5'),
  vat: evVat('8590012007', 'GMINA NOWOGARD'),
}
const ngPlannedEnd = evCalc('ng-planned-end', 'planned_end = signed_at (8.1) + okres realizacji (8.3)', [ngEv.trSigned, ngEv.trPeriod], '2025-10-24',
  { signed_at: '2025-04-24', months: 6 })
const ngDelay = evCalc('ng-delay', 'delay_days = actual_end (5.2) − planned_end', [ngEv.cpEnd, ngPlannedEnd], '185 dni',
  { actual_end: '2026-04-27', planned_end: '2025-10-24' })
const ngDelayAmended = evCalc('ng-delay-amended', 'delay_vs_amended = actual_end (5.2) − new_end ostatniej zmiany (AU2 5.4)', [ngEv.cpEnd, ngEv.au2Desc], '117 dni',
  { actual_end: '2026-04-27', new_end: '2025-12-31' })
const ngPaidRatio = evCalc('ng-paid-ratio', 'paid_ratio = wypłacono (5.5) / wartość umowy (8.2)', [ngEv.cpPaid, ngEv.trValue], '0,873',
  { paid: 1719611.3, value: 1969611.3 })
const ngOfferVsEst = evCalc('ng-offer-est', 'offer_vs_estimate = cena wybranej oferty brutto (6.4) / wartość zamówienia netto (4.3) – UWAGA: różna podstawa VAT', [ngEv.trLow, ngEv.trEst], '0,892 (netto vs brutto – nieporównywalne)',
  { offer_gross: 1969611.3, estimate_net: 2207285.7 })

const ngChanges: S['ContractChangeOut'][] = [
  { id: uid('change', ngContract, 1), contract_id: ngContract, notice_id: noticeId(NG_AU1), change_no: 1, change_date: '2025-11-03',
    legal_basis: 'art. 455 ust. 1 pkt 4 ustawy', legal_basis_code: '455.1.4',
    reason: 'konieczność ustanowienia służebności przesyłu na działce nr 3/39 obręb Konarzewo',
    description: 'Termin wykonania przedmiotu umowy : 30 listopada 2025 r.', change_kind: ['termin'], value_delta: 0, new_value: null, new_end: '2025-11-30',
    status: 'approved', method: 'rule:au_5x', confidence: 1, evidence_ids: [ngEv.au1Basis, ngEv.au1Reason, ngEv.au1Desc, ngEv.au1Date], reviewed_by: 'ekspert', reviewed_at: '2026-11-21T17:02:00Z' },
  { id: uid('change', ngContract, 2), contract_id: ngContract, notice_id: noticeId(NG_AU2), change_no: 2, change_date: '2025-12-01',
    legal_basis: 'art. 455 ust. 1 pkt 4 ustawy', legal_basis_code: '455.1.4',
    reason: 'W trakcie realizacji prac ziemnych ujawniono niekorzystne warunki gruntowe oraz miejscowy wysoki poziom wód gruntowych. W celu prawidłowego wykonania zamówienia konieczne było wydłużenie terminu realizacji umowy.',
    description: 'Termin wykonania przedmiotu umowy: 31.12.2025 r.', change_kind: ['termin'], value_delta: 0, new_value: null, new_end: '2025-12-31',
    status: 'proposed', method: 'rule:au_5x', confidence: 1, evidence_ids: [ngEv.au2Basis, ngEv.au2Reason, ngEv.au2Desc, ngEv.au2Date] },
]

const starkan: S['EntityOut'] = { id: uid('entity', '369467516'), name: 'Konsorcjum firm: "Starkan" Sp. z o.o. (lider), Przedsiębiorstwo Usługowe "Starkan" Marcin Pardus',
  regon: '369467516', role: 'contractor', city: 'Stargard', province: 'zachodniopomorskie', verified_by: ['BZP'], natural_person_flag: true }
const nowogardEntity: S['EntityOut'] = { id: uid('entity', '8590012007'), name: 'Gmina Nowogard', nip: '8590012007', regon: '811684278', role: 'beneficiary',
  city: 'Nowogard', province: 'zachodniopomorskie', verified_by: ['BZP', 'VAT'], vat_status: 'Czynny', natural_person_flag: false }

const ngEvents: S['EventOut'][] = [
  { id: uid('event', NG, 'ch1'), project_id: ngPid, project_code: NG, procedure_id: ngProc, contract_id: ngContract, change_id: ngChanges[0].id, notice_id: noticeId(NG_AU1),
    event_type: 'zmiana_terminu', event_date: '2025-11-03', risk_codes: ['R03'], title: 'Zmiana nr 1 – przedłużenie terminu (służebność przesyłu)',
    cause: 'Brak ustanowionej służebności przesyłu na działce nr 3/39 obręb Konarzewo', signal: 'Trasa przez grunt bez uregulowanego prawa do dysponowania',
    effect: 'Przedłużenie terminu wykonania do 30.11.2025', effect_days: 37, effect_pln: 0, mitigation: 'Aneks terminowy na podstawie art. 455 ust. 1 pkt 4',
    mitigation_effect: 'nieskuteczne – umowę wykonano 27.04.2026, po terminie z aneksu', mitigation_rule: 'finished_by_amended_date',
    quote: 'konieczność ustanowienia służebności przesyłu na działce nr 3/39 obręb Konarzewo', status: 'approved', method: 'rule:reasons', confidence: 0.95,
    evidence_ids: [ngEv.au1Reason, ngEv.au1Desc, ngEv.au1Basis], exemplary: true, tier: 'deep', reviewed_by: 'ekspert', reviewed_at: '2026-11-21T17:05:00Z' },
  { id: uid('event', NG, 'ch2'), project_id: ngPid, project_code: NG, procedure_id: ngProc, contract_id: ngContract, change_id: ngChanges[1].id, notice_id: noticeId(NG_AU2),
    event_type: 'zmiana_terminu', event_date: '2025-12-01', risk_codes: ['R02'], title: 'Zmiana nr 2 – przedłużenie terminu (warunki gruntowe, wody gruntowe)',
    cause: 'Niekorzystne warunki gruntowe i wysoki poziom wód gruntowych ujawnione podczas prac ziemnych', signal: 'Brak lub niepełne rozpoznanie geotechniczne przed przetargiem (PFU)',
    effect: 'Przedłużenie terminu do 31.12.2025', effect_days: 31, effect_pln: 0, mitigation: 'Aneks terminowy na podstawie art. 455 ust. 1 pkt 4',
    mitigation_effect: 'nieskuteczne – przekroczenie terminu z aneksu o 117 dni', mitigation_rule: 'finished_by_amended_date',
    quote: 'ujawniono niekorzystne warunki gruntowe oraz miejscowy wysoki poziom wód gruntowych', status: 'proposed', method: 'rule:reasons', confidence: 0.92,
    evidence_ids: [ngEv.au2Reason, ngEv.au2Desc, ngEv.au2Basis], exemplary: false, tier: 'deep' },
  { id: uid('event', NG, 'late'), project_id: ngPid, project_code: NG, procedure_id: ngProc, contract_id: ngContract, notice_id: noticeId(NG_CP),
    event_type: 'opoznienie', event_date: '2026-04-27', risk_codes: ['R06', 'R02'], title: 'Wykonanie po terminie: 185 dni po pierwotnym, 117 dni po terminie z aneksu',
    cause: 'Skumulowane skutki R03 i R02; terminy z aneksów niewystarczające', effect: 'Opóźnienie zakończenia o 185 dni', effect_days: 185,
    mitigation: 'Dwa aneksy terminowe', mitigation_effect: 'nieskuteczne', mitigation_rule: 'finished_by_amended_date',
    quote: 'Nie', status: 'proposed', method: 'rule:late_5_3', confidence: 1, evidence_ids: [ngEv.cpOnTime, ngEv.cpEnd, ngDelay, ngDelayAmended], exemplary: false, tier: 'deep' },
  { id: uid('event', NG, 'model'), project_id: ngPid, project_code: NG, procedure_id: ngProc, notice_id: noticeId(NG_CN),
    event_type: 'fragment_ryzykowny', event_date: '2025-02-20', risk_codes: ['R08', 'R02'], title: 'Ryczałt na podstawie PFU przy nierozpoznanych warunkach gruntowych',
    cause: 'Cena ryczałtowa liczona z Programu Funkcjonalno-Użytkowego', signal: '„Cena oferty stanowi wynagrodzenie ryczałtowe. Podstawą do obliczenia ceny jest Program Funkcjonalno-Użytkowy.”',
    effect: 'Ryzyko sporów o roboty nieprzewidziane i aneksów terminowych', mitigation: 'Klauzula waloryzacyjna / mechanizm zmiany dla warunków gruntowych (art. 455 ust. 1 pkt 1)',
    quote: 'Cena oferty stanowi wynagrodzenie ryczałtowe', model_label: 'Wniosek modelu', status: 'proposed', method: 'llm:doc_fragments', confidence: 0.68,
    evidence_ids: [evSec(NG_CN, '4.3.1', 'Cena oferty stanowi wynagrodzenie ryczałtowe')], exemplary: false, tier: 'deep',
    proposal: { risk_codes: ['R08'], cause: 'Wynagrodzenie ryczałtowe przy niepewnym zakresie (PFU)', _rerun_at: '2026-11-21T18:10:00Z' } },
]

const ngIssues: S['DataIssueOut'][] = [
  { id: uid('issue', NG, 'docs'), project_id: ngPid, kind: 'missing_document', field: 'umowa / aneksy', state: 'brak', status: 'proposed',
    message: 'Brak treści umowy i aneksów (PPU) – warunki kontraktowe odtworzone z ogłoszeń 7.3–7.4.', what_to_add: 'Wgraj umowę i aneksy nr 1–2 (PDF) z BIP gminy lub od beneficjenta.',
    impact: 'Nie można zweryfikować kar umownych ani mechanizmu waloryzacji.', evidence_ids: [ngEv.cnChanges] },
  { id: uid('issue', NG, 'basis'), project_id: ngPid, kind: 'legal_basis', field: 'podstawa zmian', state: 'potwierdzone', status: 'approved',
    message: 'Obie zmiany: art. 455 ust. 1 pkt 4 – potwierdzone w ogłoszeniach o zmianie umowy.', evidence_ids: [ngEv.au1Basis, ngEv.au2Basis] },
  { id: uid('issue', NG, 'period'), project_id: ngPid, kind: 'contradiction', field: 'okres realizacji', state: 'sprzeczne', status: 'proposed',
    message: 'Okres realizacji: ogłoszenie o zamówieniu 4.2.10 = „8 miesiące”, ogłoszenie o wyniku 8.3 = „6 miesiące”.',
    what_to_add: 'Potwierdź termin z umowy (§ termin wykonania).', impact: 'Opóźnienie liczone od 6 mies. (185 dni); przy 8 mies. = 124 dni.', evidence_ids: [ngEv.cnPeriod, ngEv.trPeriod] },
  { id: uid('issue', NG, 'value'), project_id: ngPid, kind: 'contradiction', field: 'wartość', state: 'sprzeczne', status: 'proposed',
    message: 'Wartość przedsięwzięcia KPO (1 749 991,33 zł) niższa niż wartość umowy (1 969 611,30 zł brutto).',
    what_to_add: 'Ustal, czy wartość KPO jest netto lub obejmuje tylko koszty kwalifikowalne.', impact: 'Porównanie budżetu wymaga ustalenia podstawy VAT.', evidence_ids: [ngEv.annot, ngEv.trValue] },
  { id: uid('issue', NG, 'paid'), project_id: ngPid, kind: 'paid', field: 'wypłata', state: 'częściowe', status: 'proposed',
    message: 'Wypłacono 1 719 611,30 zł, tj. 250 000,00 zł mniej niż wartość umowy, przy braku wzrostu ceny w zmianach.',
    what_to_add: 'Sprawdź, czy potrącono kary umowne za opóźnienie.', impact: 'Możliwe kary umowne – efekt kosztowy opóźnienia nieznany.', evidence_ids: [ngEv.cpPaid, ngEv.trValue, ngPaidRatio] },
  { id: uid('issue', NG, 'geo'), project_id: ngPid, kind: 'missing_document', field: 'badania geotechniczne', state: 'brak', status: 'proposed',
    message: 'Brak dokumentacji geotechnicznej w materiałach postępowania.', what_to_add: 'Dodaj opinię geotechniczną / PFU z załącznikami.', impact: 'Nie można ocenić, czy R02 był przewidywalny.' },
]

const ngTimeline: S['TimelineOut'] = {
  project_id: ngPid,
  items: [
    { date: '2025-02-20', kind: 'budget', label: 'Wartość przedsięwzięcia KPO', value: 1749991.33, planned: true, evidence_ids: [ngEv.annot] },
    { date: '2025-02-20', kind: 'published', label: 'Ogłoszenie o zamówieniu 2025/BZP 00113651/01', notice_id: noticeId(NG_CN), evidence_ids: [ngEv.cnTitle], planned: false },
    { date: '2025-02-20', kind: 'estimate', label: 'Wartość zamówienia (netto)', value: 2207285.7, planned: true, evidence_ids: [ngEv.trEst] },
    { date: '2025-03-03', kind: 'offers', label: '10 ofert: 1 969 611,30 – 3 479 874,18 zł', value: 1969611.3, notice_id: noticeId(NG_TR), evidence_ids: [ngEv.trOffers, ngEv.trLow, ngEv.trHigh], planned: false },
    { date: '2025-04-24', kind: 'contract', label: 'Umowa: Konsorcjum „Starkan”', value: 1969611.3, notice_id: noticeId(NG_TR), evidence_ids: [ngEv.trSigned, ngEv.trValue], planned: false },
    { date: '2025-10-24', kind: 'planned_end', label: 'Planowany termin (umowa + 6 mies.)', planned: true, evidence_ids: [ngPlannedEnd] },
    { date: '2025-11-03', kind: 'change', label: 'Zmiana 1 → 30.11.2025 (R03 służebność)', value: 0, notice_id: noticeId(NG_AU1), evidence_ids: [ngEv.au1Reason], planned: false },
    { date: '2025-12-01', kind: 'change', label: 'Zmiana 2 → 31.12.2025 (R02 warunki gruntowe)', value: 0, notice_id: noticeId(NG_AU2), evidence_ids: [ngEv.au2Reason], planned: false },
    { date: '2026-04-27', kind: 'actual_end', label: 'Faktyczne wykonanie', notice_id: noticeId(NG_CP), evidence_ids: [ngEv.cpEnd, ngEv.cpOnTime], planned: false },
    { date: '2026-06-16', kind: 'paid', label: 'Wypłacono', value: 1719611.3, notice_id: noticeId(NG_CP), evidence_ids: [ngEv.cpPaid], planned: false },
  ],
  planned_vs_actual: { planned_end: '2025-10-24', amended_end: '2025-12-31', actual_end: '2026-04-27', delay_days: 185, delay_vs_amended_days: 117,
    value: 1969611.3, paid: 1719611.3, paid_ratio: 0.873, estimate_net: 2207285.7, budget: 1749991.33, evidence: { delay_days: ngDelay, paid_ratio: ngPaidRatio, offer_vs_estimate: ngOfferVsEst } },
}

const ngLink: S['LinkOut'] = {
  id: uid('link', ngPid, ngProc), project_id: ngPid, project_code: NG, procedure_id: ngProc, ocid: 'ocds-148610-740158c8-9281-4fe9-9f58-59edc56af25c',
  bzp_number: NG_CN, procedure_title: RAW_NOTICES[NG_CN].title, part_no: null, status: 'proposed', method: 'title+nip', confidence: 0.97,
  evidence_ids: [ngEv.title, ngEv.cnTitle],
  components: [
    { name: 'nip', score: 1, weight: 0.3, detail: 'NIP zamawiającego = NIP odbiorcy (8590012007)', evidence_id: ngEv.nip },
    { name: 'title', score: 1, weight: 0.3, detail: 'Tytuł identyczny z nazwą przedsięwzięcia', evidence_id: ngEv.cnTitle },
    { name: 'location', score: 1, weight: 0.1, detail: 'Konarzewo w tytule i opisie KPO', evidence_id: ngEv.annot },
    { name: 'cpv', score: 1, weight: 0.1, detail: '45232421-9 – wod-kan', evidence_id: ngEv.cnCpv },
    { name: 'kpo_ref', score: 0, weight: 0.15, detail: 'Ogłoszenie 2.14 = „Nie” (brak numeru KPO w BZP)', evidence_id: ngEv.cnEu },
    { name: 'date', score: 0.9, weight: 0.05, detail: 'Ogłoszenie 2025-02 – w oknie realizacji KPO', evidence_id: ngEv.cnOffersDate },
  ],
  alternatives: [], is_override: false, rank: 1,
}

const ngProcedure: S['ProcedureOut'] = {
  id: ngProc, ocid: ngLink.ocid, bzp_number: NG_CN, title: RAW_NOTICES[NG_CN].title, cpv_main: '45232421-9', cpv_extra: ['45252127-4', '45262640-9', '45111200-0', '45232400-6', '45231300-8'],
  mode: 'tryb podstawowy, art. 275 pkt 2', buyer_nip: '8590012007', est_value_net: 2207285.7, planned_period_text: '8 miesiące', planned_days: 243, parts: 1,
  eu_funded: false, offers_count: 10, cancelled: false, first_published_at: '2025-02-20T00:00:00Z', subsector_main: 'Kanalizacja sanitarna', tier: 'deep',
  evidence_ids: [ngEv.cnTitle, ngEv.trEst, ngEv.trOffers],
}

const ngContractOut: S['ContractOut'] = {
  id: ngContract, procedure_id: ngProc, part_no: null, contractor: starkan, signed_at: '2025-04-24', value_gross: 1969611.3, offers_count: 10,
  planned_end: '2025-10-24', planned_days: 183, actual_end: '2026-04-27', paid_gross: 1719611.3, on_time: false, performed: true, proper: true,
  n_changes: 2, terms_source: 'ogłoszenie 7.3–7.4 (warunki kontraktowe odtworzone)', changes: ngChanges,
  status: 'proposed', method: 'rule:result+performing', confidence: 1, evidence_ids: [ngEv.trSigned, ngEv.trValue, ngEv.cpEnd, ngEv.cpPaid, ngEv.cpOnTime, ngEv.cpProper],
}

/* ------------------------------------------------------------------ Wolin RM-2026-022 */
const WL = 'RM-2026-022'
const wlPid = projectId(WL)
const wlOcid = 'ocds-148610-f193152b-b443-11ed-9236-36fed59ea7dd'
const wlProc = uid('procedure', wlOcid)
const decoyOcid = 'ocds-148610-?-06954b8c6cb9'
const decoyProc = uid('procedure', 'decoy-wolin-wodociagi')
const roadsProc = uid('procedure', 'wolin-drogi')
const wlContract = uid('contract', wlProc, 1)
const WL_AU = '2023/BZP 00396503/01', WL_CP = '2023/BZP 00580488/01', WL_CP2 = '2024/BZP 00621519/01', DEC_TR = '2023/BZP 00232972/01', DEC_CP = '2023/BZP 00464559/01'

const wlEv = {
  bzp: evXlsx(rowIndex(WL), 'Identyfikator publiczny', '2023/BZP 00110672/01', WL),
  title: evXlsx(rowIndex(WL), 'Nazwa przedsięwzięcia', 'Budowa sieci wodociągowych i kanalizacji sanitarnej w Gminie Wolin', WL),
  nip: evXlsx(rowIndex(WL), 'Identyfikator odbiorcy', '9860164852', WL),
  auTitle: evSec(WL_AU, '3.6'), auXref: evSec(WL_AU, '3.1.1'), auBasis: evSec(WL_AU, '5.2'), auReason: evSec(WL_AU, '5.3'), auDesc: evSec(WL_AU, '5.4'), auValue: evSec(WL_AU, '5.5.1'),
  auSigned: evSec(WL_AU, '4.1'), auContractValue: evSec(WL_AU, '4.4'), auContractor: evSec(WL_AU, '4.3.1'),
  cpTitle: evSec(WL_CP, '3.7'), cpEnd: evSec(WL_CP, '5.2'), cpOnTime: evSec(WL_CP, '5.3'), cpPaid: evSec(WL_CP, '5.5'), cpNChanges: evSec(WL_CP, '5.4.1'), cpXref: evSec(WL_CP, '4.5'),
  cp2Title: evSec(WL_CP2, '3.7'),
  decTitle: evSec(DEC_TR, '4.5.1'), decContractor: evSec(DEC_TR, '7.3.1'),
}
const wlPaidRatio = evCalc('wl-paid', 'paid_ratio = wypłacono (5.5) / wartość umowy (4.4)', [wlEv.cpPaid, wlEv.auContractValue], '1,267',
  { paid: 2827552.39, value: 2230851 })
const wlCheck = evCalc('wl-sum', 'wartość + Σ zmian = 2 230 851,00 + 319 316,59 + 277 384,80', [wlEv.auContractValue, wlEv.auValue, wlEv.cpPaid], '2 827 552,39 = wypłacono ✔')

const wlComponentsMain: S['LinkComponent'][] = [
  { name: 'notice_no', score: 0, weight: 0.35, detail: 'Numer 2023/BZP 00110672/01 z xlsx nie istnieje w BZP', evidence_id: wlEv.bzp },
  { name: 'nip', score: 1, weight: 0.2, detail: 'NIP zamawiającego 9860164852', evidence_id: wlEv.nip },
  { name: 'title', score: 1, weight: 0.2, detail: 'Tytuł identyczny (ogłoszenie o zmianie 3.6 i 2× o wykonaniu)', evidence_id: wlEv.auTitle },
  { name: 'xref', score: 0.9, weight: 0.15, detail: 'Łańcuch: zmiana 2023/BZP 00396503/01 → 3.1.1 ogł. 2023/BZP 00178669', evidence_id: wlEv.auXref },
  { name: 'date', score: 0.8, weight: 0.1, detail: 'Umowa 2023-04-11 – zgodna z rokiem numeru z xlsx', evidence_id: wlEv.auSigned },
]
const wlCandidates: S['LinkCandidate'][] = [
  { procedure_id: wlProc, ocid: wlOcid, bzp_number: '2023/BZP 00178669/01', title: 'Budowa sieci wodociągowych i kanalizacji sanitarnej w Gminie Wolin', score: 0.64, components: wlComponentsMain },
  { procedure_id: decoyProc, ocid: decoyOcid, bzp_number: DEC_TR, title: 'BUDOWA SIECI WODOCIĄGOWYCH W GMINIE WOLIN,', score: 0.58,
    components: [
      { name: 'notice_no', score: 0, weight: 0.35, detail: 'brak klucza' },
      { name: 'nip', score: 1, weight: 0.2, detail: 'NIP zamawiającego 9860164852', evidence_id: wlEv.nip },
      { name: 'title', score: 0.78, weight: 0.2, detail: 'Brak „kanalizacji sanitarnej” w tytule', evidence_id: wlEv.decTitle },
      { name: 'date', score: 0.9, weight: 0.1, detail: 'Wynik 2023-05-25' },
      { name: 'value', score: 0.4, weight: 0.15, detail: 'Inny wykonawca (MPGK Wolin) niż w zmianie umowy', evidence_id: wlEv.decContractor },
    ],
    why_not: 'Wabik: prawie identyczny tytuł, ale zakres tylko wodociągowy i inny wykonawca (MPGK Wolin) niż w ogłoszeniach o zmianie/wykonaniu (PPH Artex).' },
  { procedure_id: roadsProc, ocid: 'ocds-148610-…-bea871b78b5b', bzp_number: '2023/BZP 00407868/01', title: 'Przebudowa dróg w Wolinie wraz z rozbudową i przebudową infrastruktury w zakresie odprowadzenia wód…', score: 0.31,
    components: [{ name: 'nip', score: 1, weight: 0.2 }, { name: 'title', score: 0.35, weight: 0.2 }, { name: 'cpv', score: 0.5, weight: 0.1, detail: 'roboty drogowe + deszczówka' }],
    why_not: 'Inny przedmiot (drogi, kanalizacja deszczowa).' },
]

const wlLink: S['LinkOut'] = {
  id: uid('link', wlPid, wlProc), project_id: wlPid, project_code: WL, procedure_id: wlProc, ocid: wlOcid, bzp_number: '2023/BZP 00178669/01',
  procedure_title: 'Budowa sieci wodociągowych i kanalizacji sanitarnej w Gminie Wolin', part_no: null, status: 'proposed', method: 'xref', confidence: 0.64,
  evidence_ids: [wlEv.bzp, wlEv.auXref, wlEv.auTitle], components: wlComponentsMain, alternatives: wlCandidates.slice(1), is_override: false, rank: 1,
}

const artex: S['EntityOut'] = { id: uid('entity', '6690503086'), name: 'PPH Artex sp. z o.o.', nip: '6690503086', role: 'contractor', city: 'Koszalin',
  province: 'zachodniopomorskie', verified_by: ['BZP', 'VAT'], vat_status: 'Czynny', natural_person_flag: false }
const wolinEntity: S['EntityOut'] = { id: uid('entity', '9860164852'), name: 'Gmina Wolin', nip: '9860164852', role: 'beneficiary', city: 'Wolin',
  province: 'zachodniopomorskie', verified_by: ['BZP', 'VAT'], vat_status: 'Czynny', natural_person_flag: false }

const wlChanges: S['ContractChangeOut'][] = [
  { id: uid('change', wlContract, 1), contract_id: wlContract, notice_id: noticeId(WL_CP), change_no: 1, legal_basis: null, reason: null,
    description: 'Zmiana nr 1 wykazana w ogłoszeniu o wykonaniu umowy (5.4.2–5.4.8) bez ogłoszenia o zmianie', change_kind: ['wynagrodzenie'],
    value_delta: 319316.59, status: 'proposed', method: 'rule:cp_5_4', confidence: 1, evidence_ids: [evSec(WL_CP, '5.4.6')] },
  { id: uid('change', wlContract, 2), contract_id: wlContract, notice_id: noticeId(WL_AU), change_no: 2, change_date: '2023-08-16', legal_basis: 'art. 455 ust. 1 pkt 3 ustawy', legal_basis_code: '455.1.3',
    reason: RAW_NOTICES[WL_AU].sections.find((s) => s.section === '5.3')?.value ?? null,
    description: RAW_NOTICES[WL_AU].sections.find((s) => s.section === '5.4')?.value ?? null, change_kind: ['zakres', 'wynagrodzenie'],
    value_delta: 277384.8, status: 'proposed', method: 'rule:au_5x', confidence: 1, evidence_ids: [wlEv.auBasis, wlEv.auReason, wlEv.auDesc, wlEv.auValue] },
]

const wlEvents: S['EventOut'][] = [
  { id: uid('event', WL, 'ch2'), project_id: wlPid, project_code: WL, procedure_id: wlProc, contract_id: wlContract, change_id: wlChanges[1].id, notice_id: noticeId(WL_AU),
    event_type: 'roboty_dodatkowe', event_date: '2023-08-16', risk_codes: ['R07', 'R01'], title: 'Roboty dodatkowe: 593,61 m przyłączy i 3 hydranty (+277 384,80 zł)',
    cause: 'Konieczność rozbudowy infrastruktury wodociągowej o dodatkowe przyłącza (protokół konieczności nr 2/2023)', effect: 'Wzrost wynagrodzenia o 12,4%',
    effect_pln: 277384.8, effect_pct: 0.124, mitigation: 'Zamówienie dodatkowe u dotychczasowego wykonawcy (art. 455 ust. 1 pkt 3)', mitigation_effect: 'skuteczne – termin dotrzymany (5.3 = Tak)', mitigation_rule: 'finished_by_amended_date',
    quote: 'polegających na rozbudowie infrastruktury wodociągowej o dodatkowe przyłącza', status: 'proposed', method: 'rule:reasons', confidence: 0.88,
    evidence_ids: [wlEv.auReason, wlEv.auValue, wlEv.cpOnTime], exemplary: false, tier: 'deep' },
  { id: uid('event', WL, 'paid'), project_id: wlPid, project_code: WL, procedure_id: wlProc, contract_id: wlContract, notice_id: noticeId(WL_CP),
    event_type: 'wyplata_powyzej_wartosci', event_date: '2023-12-29', risk_codes: ['R07', 'R13'], title: 'Wypłata 26,7% powyżej wartości umowy',
    cause: 'Dwie zmiany zwiększające wynagrodzenie', effect: 'Wypłacono 2 827 552,39 zł przy umowie 2 230 851,00 zł', effect_pln: 596701.39, effect_pct: 0.267,
    quote: '2827552,39 PLN', status: 'proposed', method: 'rule:paid_5_5', confidence: 1, evidence_ids: [wlEv.cpPaid, wlEv.auContractValue, wlPaidRatio, wlCheck], exemplary: false, tier: 'deep' },
  { id: uid('event', WL, 'ch1'), project_id: wlPid, project_code: WL, procedure_id: wlProc, contract_id: wlContract, change_id: wlChanges[0].id, notice_id: noticeId(WL_CP),
    event_type: 'zmiana_wynagrodzenia', risk_codes: ['R01'], title: 'Zmiana nr 1 (+319 316,59 zł) – przyczyna nieznana',
    cause: 'Prawdopodobnie niepełny zakres w dokumentacji (brak opisu w ogłoszeniu)', effect: 'Wzrost wynagrodzenia o 14,3%', effect_pln: 319316.59, effect_pct: 0.143,
    model_label: 'Wniosek modelu', quote: '319316,59', status: 'proposed', method: 'llm:causes', confidence: 0.45, evidence_ids: [evSec(WL_CP, '5.4.6')], exemplary: false, tier: 'deep' },
]

const wlIssues: S['DataIssueOut'][] = [
  { id: uid('issue', WL, 'bzp'), project_id: wlPid, kind: 'organizer_error', field: 'Identyfikator publiczny', state: 'sprzeczne', status: 'proposed',
    message: 'Numer 2023/BZP 00110672/01 z pliku organizatora nie istnieje w BZP (zapytanie NoticeNumber: 0 wyników).',
    what_to_add: 'Potwierdź właściwy numer ogłoszenia lub zaakceptuj powiązanie przez łańcuch ogłoszeń.', impact: 'Powiązanie niepewne (0,64) – wymaga decyzji eksperta.', evidence_ids: [wlEv.bzp] },
  { id: uid('issue', WL, 'ch1'), project_id: wlPid, kind: 'missing_field', field: 'podstawa zmiany nr 1', state: 'brak', status: 'proposed',
    message: 'Zmiana nr 1 (+319 316,59 zł) bez podstawy prawnej i przyczyn – brak ogłoszenia o zmianie.', what_to_add: 'Wgraj aneks nr 1.', impact: 'Przyczyna przypisana tylko przez model.' },
  { id: uid('issue', WL, 'cp2'), project_id: wlPid, kind: 'contradiction', field: 'ogłoszenia o wykonaniu', state: 'częściowe', status: 'proposed',
    message: 'Dwa ogłoszenia o wykonaniu z tym samym tytułem (2023/BZP 00580488/01 i 2024/BZP 00621519/01).', what_to_add: 'Sprawdź, czy drugie dotyczy innej umowy/części.', evidence_ids: [wlEv.cpTitle, wlEv.cp2Title] },
]

const wlContractOut: S['ContractOut'] = {
  id: wlContract, procedure_id: wlProc, contractor: artex, signed_at: '2023-04-11', value_gross: 2230851, actual_end: '2023-08-31', planned_end: '2023-08-31',
  paid_gross: 2827552.39, on_time: true, performed: true, proper: true, n_changes: 2, terms_source: 'ogłoszenia o zmianie/wykonaniu', changes: wlChanges,
  status: 'proposed', method: 'rule:performing', confidence: 1, evidence_ids: [wlEv.auSigned, wlEv.auContractValue, wlEv.cpEnd, wlEv.cpPaid],
}

/* ------------------------------------------------------------------ graph builder */
function graphFor(p: S['ProjectListItem'], beneficiary: S['EntityOut'], proc: S['ProcedureOut'], link: S['LinkOut'], notices: string[],
  contract?: S['ContractOut'], events: S['EventOut'][] = [], decoys: S['LinkCandidate'][] = []): S['GraphOut'] {
  const nodes: S['GraphNode'][] = [
    { id: p.id, type: 'project', label: `${p.code}\n${p.title.slice(0, 50)}…`, data: { code: p.code } },
    { id: beneficiary.id, type: 'entity', label: `${beneficiary.name}\nNIP ${beneficiary.nip}`, data: { role: 'beneficiary' } },
    { id: proc.id, type: 'procedure', label: `Postępowanie\n${proc.ocid?.slice(-12)}`, data: { ocid: proc.ocid } },
  ]
  const edges: S['GraphEdge'][] = [
    { source: beneficiary.id, target: p.id, label: 'odbiorca', method: 'xlsx', confidence: 1, status: 'approved' },
    { source: p.id, target: proc.id, label: 'powiązanie', method: link.method, confidence: link.confidence, status: link.status },
  ]
  for (const no of notices) {
    const n = RAW_NOTICES[no]
    nodes.push({ id: noticeId(no), type: 'notice', label: `${typeLabel(n.notice_type)}\n${no}`, data: { notice_number: no, notice_type: n.notice_type } })
    edges.push({ source: proc.id, target: noticeId(no), label: 'ogłoszenie', method: 'ocid', confidence: 1, status: 'approved' })
  }
  if (contract) {
    nodes.push({ id: contract.id, type: 'contract', label: `Umowa\n${contract.value_gross?.toLocaleString('pl-PL')} zł`, data: {} })
    edges.push({ source: proc.id, target: contract.id, label: 'umowa', method: 'xref 4.5', confidence: 1, status: 'approved' })
    if (contract.contractor) {
      nodes.push({ id: contract.contractor.id, type: 'entity', label: contract.contractor.name.slice(0, 40), data: { role: 'contractor' } })
      edges.push({ source: contract.id, target: contract.contractor.id, label: 'wykonawca', method: 'BZP 4.3', confidence: 1, status: 'approved' })
    }
    for (const ch of contract.changes ?? []) {
      nodes.push({ id: ch.id, type: 'change', label: `Zmiana ${ch.change_no}\n${ch.legal_basis ?? 'podstawa: brak'}`, data: {} })
      edges.push({ source: contract.id, target: ch.id, label: 'zmiana', method: ch.method, confidence: ch.confidence, status: ch.status })
    }
  }
  for (const e of events) {
    nodes.push({ id: e.id, type: 'event', label: `${(e.risk_codes ?? []).join(', ')}\n${(e.title ?? '').slice(0, 36)}…`, data: { status: e.status } })
    edges.push({ source: e.change_id ?? contract?.id ?? proc.id, target: e.id, label: 'zdarzenie', method: e.method, confidence: e.confidence, status: e.status })
  }
  for (const d of decoys) {
    const id = d.procedure_id ?? uid('decoy', d.title ?? '')
    nodes.push({ id, type: 'procedure', label: `Kandydat (odrzucony)\n${d.bzp_number}`, data: { decoy: true, why_not: d.why_not } })
    edges.push({ source: p.id, target: id, label: 'kandydat', method: 'fuzzy', confidence: d.score, status: 'rejected' })
  }
  return { nodes, edges }
}

export function typeLabel(t: string) {
  return ({ ContractNotice: 'Ogłoszenie o zamówieniu', TenderResultNotice: 'Ogłoszenie o wyniku', AgreementUpdateNotice: 'Ogłoszenie o zmianie umowy',
    ContractPerformingNotice: 'Ogłoszenie o wykonaniu umowy' } as Record<string, string>)[t] ?? t
}

/* ------------------------------------------------------------------ history */
function hist(objectType: string, objectId: string, action: string, at: string, reviewer: string, comment?: string, before?: object, after?: object): S['ReviewOut'] {
  return { id: uid('review', objectId, action, at), object_type: objectType, object_id: objectId, action, at, reviewer, comment: comment ?? null,
    before: (before as Record<string, unknown>) ?? null, after: (after as Record<string, unknown>) ?? null }
}

/* ------------------------------------------------------------------ bundles */
const item = (code: string) => mockProjectItems.find((p) => p.code === code)!

function detailOf(code: string, extra: Partial<S['ProjectDetail']>): S['ProjectDetail'] {
  const p = item(code)
  const row = ORGANIZER_ROWS.find((r) => r[0] === code)!
  return {
    ...p, city: row[5], description: null, work_type: 'Roboty budowlane', formula: null, funding: row[8] === 'Projekt KPO' ? 'KPO B3.1.1' : null,
    project_value: row[11] ?? null, grant_value: row[12] ?? null, annotation: null, features: {}, beneficiary: null, exemplary: false,
    import_row: { 'Lp.': rowIndex(code) - 1, 'Identyfikator rekordu': code, 'Identyfikator odbiorcy': row[1], 'Nazwa odbiorcy': row[2],
      'Kod województwa (TERYT)': row[3], 'Województwo': row[4], 'Siedziba odbiorcy': row[5], 'Nazwa przedsięwzięcia': row[6], 'Zakres rekordu': row[7],
      'Rodzaj identyfikatora publicznego': row[8], 'Identyfikator publiczny': row[9], 'Status przedsięwzięcia': 'Zakończone', 'Wersja rekordu': '2.0' },
    ...extra,
  }
}

const nowogard: CaseBundle = {
  detail: detailOf(NG, {
    description: 'Projekt obejmuje przebudowę i budowę oczyszczalni ścieków w m. Konarzewo, gm. Nowogard oraz budowę sieci kanalizacji sanitarnej z 17 przyłączami i rozgałęzieniami sieci wraz z niezbędną infrastrukturą techniczną.',
    formula: 'zaprojektuj i wybuduj (PFU)', subsector_extra: ['Oczyszczalnia ścieków'], beneficiary: nowogardEntity, exemplary: true,
    annotation: 'KPO, inwestycja B3.1.1. Wartość przedsięwzięcia: 1 749 991,33 zł; dofinansowanie: 1 414 257,17 zł.',
    features: { connections: 17, value_gross: 1969611.3, duration_months: 6 }, evidence_ids: [ngEv.kpo, ngEv.title, ngEv.annot, ngEv.vat],
  }),
  procedures: [ngProcedure], contracts: [ngContractOut],
  notices: [NG_CN, NG_TR, NG_AU1, NG_AU2, NG_CP].map((n) => noticeOut(n, ngProc)), links: [ngLink],
  candidates: [{ procedure_id: ngProc, ocid: ngLink.ocid, bzp_number: NG_CN, title: ngProcedure.title, score: 0.97, components: ngLink.components }],
  timeline: ngTimeline, events: ngEvents, issues: ngIssues,
  graph: graphFor(item(NG), nowogardEntity, ngProcedure, ngLink, [NG_CN, NG_TR, NG_AU1, NG_AU2, NG_CP], ngContractOut, ngEvents.slice(0, 3)),
  history: [
    hist('project', ngPid, 'import', '2026-11-21T14:05:00Z', 'system', 'Import xlsx organizatora (wiersz 21)'),
    hist('project_procedure', ngLink.id, 'propose', '2026-11-21T15:41:00Z', 'system', 'Powiązanie title+nip (0,97)'),
    hist('contract_change', ngChanges[0].id, 'accept', '2026-11-21T17:02:00Z', 'ekspert', 'Podstawa i przyczyna zgodne z ogłoszeniem.'),
    hist('event', ngEvents[0].id, 'edit', '2026-11-21T17:04:00Z', 'ekspert', 'Doprecyzowano kod: R03 zamiast R04.', { risk_codes: ['R04'] }, { risk_codes: ['R03'] }),
    hist('event', ngEvents[0].id, 'exemplary', '2026-11-21T17:05:00Z', 'ekspert', 'Wzorcowy przykład dla few-shot.'),
  ],
}

const wolinProcedure: S['ProcedureOut'] = { id: wlProc, ocid: wlOcid, bzp_number: '2023/BZP 00178669/01', title: 'Budowa sieci wodociągowych i kanalizacji sanitarnej w Gminie Wolin',
  cpv_main: '45231300-8', buyer_nip: '9860164852', parts: 1, offers_count: null, tier: 'deep', subsector_main: 'Sieć wodociągowa', evidence_ids: [wlEv.auTitle, wlEv.auXref] }

const wolin: CaseBundle = {
  detail: detailOf(WL, { beneficiary: wolinEntity, evidence_ids: [wlEv.bzp, wlEv.title], subsector_extra: ['Kanalizacja sanitarna'] }),
  procedures: [wolinProcedure], contracts: [wlContractOut], notices: [WL_AU, WL_CP, WL_CP2, DEC_TR, DEC_CP].map((n) => noticeOut(n, n.startsWith('2023/BZP 0023') || n === DEC_CP ? decoyProc : wlProc)),
  links: [wlLink], candidates: wlCandidates,
  timeline: {
    project_id: wlPid,
    items: [
      { date: '2023-04-11', kind: 'contract', label: 'Umowa: PPH Artex sp. z o.o.', value: 2230851, notice_id: noticeId(WL_AU), evidence_ids: [wlEv.auSigned, wlEv.auContractValue], planned: false },
      { date: '2023-08-16', kind: 'change', label: 'Zmiana 2: roboty dodatkowe (+277 384,80 zł)', value: 2827552.39 - 319316.59, notice_id: noticeId(WL_AU), evidence_ids: [wlEv.auValue], planned: false },
      { date: '2023-08-31', kind: 'planned_end', label: 'Termin wykonania', planned: true, evidence_ids: [wlEv.cpEnd] },
      { date: '2023-08-31', kind: 'actual_end', label: 'Wykonano w terminie', evidence_ids: [wlEv.cpOnTime], planned: false },
      { date: '2023-12-29', kind: 'paid', label: 'Wypłacono', value: 2827552.39, notice_id: noticeId(WL_CP), evidence_ids: [wlEv.cpPaid], planned: false },
    ],
    planned_vs_actual: { planned_end: '2023-08-31', actual_end: '2023-08-31', delay_days: 0, value: 2230851, paid: 2827552.39, paid_ratio: 1.267, evidence: { paid_ratio: wlPaidRatio } },
  },
  events: wlEvents, issues: wlIssues,
  graph: graphFor(item(WL), wolinEntity, wolinProcedure, wlLink, [WL_AU, WL_CP, WL_CP2], wlContractOut, wlEvents.slice(0, 2), wlCandidates.slice(1, 2)),
  history: [
    hist('project', wlPid, 'import', '2026-11-21T14:05:00Z', 'system', 'Import xlsx organizatora (wiersz 23)'),
    hist('project_procedure', wlLink.id, 'propose', '2026-11-21T15:44:00Z', 'system', 'Klucz BZP nie znaleziony → łańcuch ogłoszeń (xref) 0,64; wabik 0,58'),
  ],
}

/** Minimal bundle for rows without a hand-made mock (only xlsx evidence). */
function genericBundle(p: S['ProjectListItem']): CaseBundle {
  const row = ORGANIZER_ROWS.find((r) => r[0] === p.code)!
  const ev = evXlsx(rowIndex(p.code), 'Identyfikator publiczny', row[9], p.code)
  return {
    detail: detailOf(p.code, { evidence_ids: [ev] }), procedures: [], contracts: [], notices: [], links: [], candidates: [],
    timeline: { project_id: p.id, items: [], planned_vs_actual: {} }, graph: { nodes: [{ id: p.id, type: 'project', label: p.code, data: {} }], edges: [] },
    events: [], issues: [], history: [hist('project', p.id, 'import', '2026-11-21T14:05:00Z', 'system', `Import xlsx organizatora (wiersz ${rowIndex(p.code)})`)],
  }
}

const BUNDLES: Record<string, CaseBundle> = { [ngPid]: nowogard, [wlPid]: wolin }
export function caseBundle(projectIdOrCode: string): CaseBundle | undefined {
  const p = mockProjectItems.find((x) => x.id === projectIdOrCode || x.code === projectIdOrCode)
  if (!p) return undefined
  return (BUNDLES[p.id] ??= genericBundle(p))
}
export const NOWOGARD_ID = ngPid
export const WOLIN_ID = wlPid
export const allBundles = () => mockProjectItems.map((p) => caseBundle(p.id)!)
export { NOW }
