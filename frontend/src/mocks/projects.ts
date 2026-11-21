/** The 22 organizer rows (Risk_Miner_dane_projekty.xlsx, sheet "Projekty"), as list items. */
import type { Schemas } from '@/api/client'
import { uid } from './ids'

type Row = [code: string, nip: string, name: string, teryt: string, voiv: string, city: string, title: string,
  scope: string, idType: 'Ogłoszenie BZP' | 'Projekt KPO', idValue: string, subsector: string, value?: number, grant?: number]

export const ORGANIZER_ROWS: Row[] = [
  ['RM-2026-001', '9121715754', 'Gmina Oława', '02', 'dolnośląskie', 'Oława', 'Budowa rurociągu tłocznego kanalizacji sanitarnej Godzikowice – Jaczkowice, gmina Oława', 'całe postępowanie', 'Ogłoszenie BZP', '2022/BZP 00058537/01', 'Kanalizacja sanitarna'],
  ['RM-2026-002', '6941566139', 'Gmina Zagrodno', '02', 'dolnośląskie', 'Zagrodno', 'Budowa kanalizacji sanitarnej na terenie Gminy Zagrodno w miejscowości Modlikowice', 'całe postępowanie', 'Projekt KPO', 'KPOD.03.15-IW.13-0004/25', 'Kanalizacja sanitarna', 5350782.65, 4333677.17],
  ['RM-2026-003', '8792466869', 'Gmina Czernikowo', '04', 'kujawsko-pomorskie', 'Czernikowo', 'Budowa oczyszczalni ścieków w miejscowości Steklin w formule zaprojektuj i wybuduj', 'całe postępowanie', 'Ogłoszenie BZP', '2024/BZP 00349631/01', 'Oczyszczalnia ścieków'],
  ['RM-2026-004', '8792466869', 'Gmina Czernikowo', '04', 'kujawsko-pomorskie', 'Czernikowo', 'Modernizacja Stacji Uzdatniania Wody w Czernikowie', 'całe postępowanie', 'Ogłoszenie BZP', '2025/BZP 00569258/01', 'Uzdatnianie i zaopatrzenie w wodę'],
  ['RM-2026-005', '8792469951', 'Gmina Zławieś Wielka', '04', 'kujawsko-pomorskie', 'Zławieś Wielka', 'Budowa sieci kanalizacji sanitarnej w miejscowości Zławieś Wielka i Zławieś Mała wraz z modernizacją stacji uzdatniania wody w miejscowości Pędzewo', 'całe postępowanie', 'Projekt KPO', 'KPOD.03.15-IW.14-0032/25', 'Kanalizacja sanitarna', 3087491.54, 2349408.96],
  ['RM-2026-006', '7151863553', 'Gmina Gościeradów', '06', 'lubelskie', 'Gościeradów Ukazowy', 'Przebudowa (modernizacja) oczyszczalni ścieków w m. Gościeradów Folwark', 'całe postępowanie', 'Ogłoszenie BZP', '2024/BZP 00067908/01', 'Oczyszczalnia ścieków'],
  ['RM-2026-007', '7141896261', 'Gmina Kamionka', '06', 'lubelskie', 'Kamionka', 'Rozbudowa sieci wodociągowej w gminie Kamionka', 'całe postępowanie', 'Projekt KPO', 'KPOD.03.15-IW.15-0081/25', 'Sieć wodociągowa', 3096863.9, 2517775.52],
  ['RM-2026-008', '7381973883', 'Gmina Biecz', '12', 'małopolskie', 'Biecz', 'Budowa sieci kanalizacji sanitarnej na terenie Gminy Biecz', 'część 1', 'Ogłoszenie BZP', '2026/BZP 00084760/01', 'Kanalizacja sanitarna', 6188345.13, 5000000],
  ['RM-2026-009', '7962959318', 'Gmina Zakrzew', '14', 'mazowieckie', 'Zakrzew', 'Budowa sieci wodociągowej na terenie gminy Zakrzew', 'część 2', 'Ogłoszenie BZP', '2025/BZP 00307948/01', 'Sieć wodociągowa', 2329043.45, 1894503.63],
  ['RM-2026-010', '8161570014', 'Gmina Grodzisko Dolne', '18', 'podkarpackie', 'Grodzisko Dolne', 'Budowa kanalizacji sanitarnej w miejscowości Zmysłówka i Grodzisko Dolne, gmina Grodzisko Dolne', 'całe postępowanie', 'Projekt KPO', 'KPOD.03.15-IW.21-0025/25', 'Kanalizacja sanitarna', 3373482.44, 2742668.65],
  ['RM-2026-011', '6871783356', 'Gmina Sanok', '18', 'podkarpackie', 'Sanok', 'Budowa sieci wodociągowej w miejscowości Czerteż, Zabłotce oraz w części miejscowości Sanoczek', 'całe postępowanie', 'Ogłoszenie BZP', '2023/BZP 00271948/01', 'Sieć wodociągowa'],
  ['RM-2026-012', '5890010583', 'Gmina Kartuzy – Urząd Miejski w Kartuzach', '22', 'pomorskie', 'Kartuzy', 'Budowa tranzytu przesyłowego sieci kanalizacji sanitarnej ze Smętowa Chmieleńskiego do Kos', 'całe postępowanie', 'Ogłoszenie BZP', '2025/BZP 00119683/01', 'Kanalizacja sanitarna'],
  ['RM-2026-013', '6521708710', 'Gmina Bestwina', '24', 'śląskie', 'Bestwina', 'Budowa sieci kanalizacji sanitarnej w Gminie Bestwina – sołectwo Kaniów', 'całe postępowanie', 'Ogłoszenie BZP', '2023/BZP 00206497/01', 'Kanalizacja sanitarna'],
  ['RM-2026-014', '6252446477', 'Gmina Bobrowniki', '24', 'śląskie', 'Bobrowniki', 'Budowa sieci kanalizacji sanitarnej ul. Słoneczna w Siemoni', 'całe postępowanie', 'Ogłoszenie BZP', '2026/BZP 00130634/01', 'Kanalizacja sanitarna', 1714989, 1394300],
  ['RM-2026-015', '5783105254', 'Gmina Elbląg', '28', 'warmińsko-mazurskie', 'Elbląg', 'Przebudowa sieci wodociągowej oraz kanalizacji sanitarnej i deszczowej wraz z przyłączami i modernizacją oczyszczalni ścieków w miejscowości Janów w formule zaprojektuj i wybuduj', 'całe postępowanie', 'Ogłoszenie BZP', '2023/BZP 00135041/01', 'Inne obiekty wod-kan'],
  ['RM-2026-016', '7412025674', 'Gmina Miłakowo', '28', 'warmińsko-mazurskie', 'Miłakowo', 'Budowa sieci wodociągowej o długości 22,616 km i sieci kanalizacji sanitarnej na odcinku 18,09 km na obszarach wiejskich Gminy Miłakowo', 'całe postępowanie', 'Ogłoszenie BZP', '2022/BZP 00308854/01', 'Sieć wodociągowa'],
  ['RM-2026-017', '7773157115', 'Gmina Kleszczewo', '30', 'wielkopolskie', 'Kleszczewo', 'Budowa sieci kanalizacji sanitarnej wraz z przyłączami w miejscowości Tanibórz, Gmina Kleszczewo', 'całe postępowanie', 'Projekt KPO', 'KPOD.03.15-IW.27-0013/25', 'Kanalizacja sanitarna', 4052494.96, 3294711.35],
  ['RM-2026-018', '6211694095', 'Gmina Zduny', '30', 'wielkopolskie', 'Zduny', 'Budowa kanalizacji sanitarnej w miejscowości Baszków Gmina Zduny – etap II', 'całe postępowanie', 'Projekt KPO', 'KPOD.03.15-IW.27-0107/25', 'Kanalizacja sanitarna', 3847757.34, 3128258],
  ['RM-2026-019', '9720914891', 'Wielkopolski Zarząd Dróg Wojewódzkich w Poznaniu', '30', 'wielkopolskie', 'Poznań', 'Budowa kanalizacji deszczowej w ciągu drogi wojewódzkiej nr 444 w miejscowości Sulmierzyce', 'całe postępowanie', 'Ogłoszenie BZP', '2024/BZP 00354928/01', 'Kanalizacja deszczowa i retencja'],
  ['RM-2026-020', '8590012007', 'Gmina Nowogard', '32', 'zachodniopomorskie', 'Nowogard', 'Budowa kanalizacji sanitarnej wraz z oczyszczalnią ścieków na terenie gminy Nowogard w m. Konarzewo', 'całe postępowanie', 'Projekt KPO', 'KPOD.03.15-IW.28-0003/24', 'Kanalizacja sanitarna', 1749991.33, 1414257.17],
  ['RM-2026-021', '8590012007', 'Gmina Nowogard', '32', 'zachodniopomorskie', 'Nowogard', 'Zwiększenie odporności hydrologicznej Aglomeracji Nowogard poprzez rozdział kanalizacji sanitarnej na ul. 700-lecia', 'całe postępowanie', 'Ogłoszenie BZP', '2025/BZP 00364116/01', 'Kanalizacja sanitarna'],
  ['RM-2026-022', '9860164852', 'Gmina Wolin', '32', 'zachodniopomorskie', 'Wolin', 'Budowa sieci wodociągowych i kanalizacji sanitarnej w Gminie Wolin', 'całe postępowanie', 'Ogłoszenie BZP', '2023/BZP 00110672/01', 'Sieć wodociągowa'],
]

/** Per-project demo state (link status, counts); other rows get neutral defaults. */
const STATE: Record<string, Partial<Schemas['ProjectListItem']>> = {
  'RM-2026-001': { link_status: 'linked', status: 'approved', n_procedures: 1, n_events: 2, n_issues: 0, n_pending_review: 0, completeness: 0.92, method: 'notice_no', confidence: 1 },
  'RM-2026-008': { link_status: 'linked', status: 'proposed', n_procedures: 1, n_events: 3, n_issues: 1, n_pending_review: 2, completeness: 0.74, method: 'notice_no', confidence: 1 },
  'RM-2026-014': { link_status: 'linked', n_procedures: 1, n_events: 0, n_issues: 2, n_pending_review: 1, completeness: 0.48, method: 'notice_no', confidence: 1 },
  'RM-2026-018': { link_status: 'uncertain', n_procedures: 1, n_events: 1, n_issues: 2, n_pending_review: 2, completeness: 0.55, method: 'fuzzy', confidence: 0.71 },
  'RM-2026-020': { link_status: 'linked', status: 'proposed', n_procedures: 1, n_events: 3, n_issues: 2, n_pending_review: 4, completeness: 0.81, method: 'kpo_ref', confidence: 0.97 },
  'RM-2026-022': { link_status: 'uncertain', status: 'proposed', n_procedures: 1, n_events: 2, n_issues: 3, n_pending_review: 3, completeness: 0.62, method: 'xref', confidence: 0.64 },
}

export const projectId = (code: string) => uid('project', code)

export const mockProjectItems: Schemas['ProjectListItem'][] = ORGANIZER_ROWS.map((r, i) => {
  const [code, nip, name, teryt, voiv, , title, scope, idType, idValue, subsector] = r
  const st = STATE[code] ?? {}
  return {
    id: projectId(code), code, title, beneficiary_name: name, beneficiary_nip: nip, voivodeship: voiv, teryt,
    subsector_main: subsector, subsector_extra: [], public_id_type: idType, public_id_value: idValue,
    record_scope: scope, part_no: scope.startsWith('część') ? Number(scope.split(' ')[1]) : null,
    project_status: 'Zakończone', tier: 'deep', status: 'proposed', method: idType === 'Projekt KPO' ? 'kpo_ref' : 'notice_no',
    confidence: idType === 'Projekt KPO' ? 0.9 : 1, evidence_ids: [uid('ev', 'xlsx', code)],
    link_status: 'linked', n_procedures: 1, n_events: i % 3, n_issues: i % 2, n_pending_review: 1, completeness: 0.6 + (i % 4) * 0.08,
    ...st,
  }
})
