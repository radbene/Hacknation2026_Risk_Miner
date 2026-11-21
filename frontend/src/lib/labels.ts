/** Polish UI labels for contract enums. */
export const STATUS_LABEL: Record<string, string> = {
  proposed: 'Propozycja', approved: 'Zatwierdzone', edited: 'Poprawione', rejected: 'Odrzucone',
}
export const LINK_STATUS_LABEL: Record<string, string> = {
  linked: 'Powiązany', uncertain: 'Niepewny', unlinked: 'Niepowiązany', rejected: 'Odrzucony',
}
export const METHOD_LABEL: Record<string, string> = {
  kpo_ref: 'numer KPO', notice_no: 'numer ogłoszenia', ocid: 'OCID', xref: 'łańcuch ogłoszeń', fuzzy: 'dopasowanie rozmyte',
  expert: 'ekspert', 'title+nip': 'tytuł + NIP', xlsx: 'plik xlsx',
}
export function methodLabel(m?: string | null) {
  if (!m) return '—'
  if (METHOD_LABEL[m]) return METHOD_LABEL[m]
  if (m.startsWith('rule:')) return `reguła ${m.slice(5)}`
  if (m.startsWith('llm:')) return `model (${m.slice(4)})`
  return m
}
export const RISK_NAMES: Record<string, string> = {
  R01: 'Niepełny lub niespójny zakres', R02: 'Niedostateczne rozpoznanie stanu istniejącego',
  R03: 'Kolizje, dostęp do terenu i prawa do nieruchomości', R04: 'Decyzje, pozwolenia i uzgodnienia zależne od podmiotów trzecich',
  R05: 'Niejasny lub nieadekwatny podział odpowiedzialności', R06: 'Nierealistyczny harmonogram i nieuwzględnione zależności',
  R07: 'Nieprzewidziane zmiany i roboty dodatkowe', R08: 'Model wynagrodzenia niedopasowany do niepewności zakresu',
  R09: 'Niejednoznaczne lub niemierzalne wymagania techniczne', R10: 'Niedookreślone próby, rozruch i odbiór',
  R11: 'Postępowanie podatne na odwołanie lub ograniczenie konkurencji', R12: 'Niewystarczająca zdolność wykonawcy lub łańcucha dostaw',
  R13: 'Ryzyko finansowania, budżetu i płatności', R14: 'Nadmierne koszty eksploatacji i utrzymania',
  R15: 'Nieosiągnięcie efektu technologicznego, użytkowego lub środowiskowego',
}
export const SUBSECTORS = ['Sieć wodociągowa', 'Kanalizacja sanitarna', 'Oczyszczalnia ścieków', 'Uzdatnianie i zaopatrzenie w wodę',
  'Kanalizacja deszczowa i retencja', 'Inne obiekty wod-kan']
export const ISSUE_STATES = ['potwierdzone', 'częściowe', 'brak', 'sprzeczne'] as const
export const OBJECT_TYPE_LABEL: Record<string, string> = {
  project: 'Projekt', project_procedure: 'Powiązanie', contract: 'Umowa', contract_change: 'Zmiana umowy', fact: 'Fakt', document: 'Dokument',
  risk_category: 'Kategoria ryzyka', lesson: 'Lekcja', clause: 'Klauzula', event: 'Zdarzenie', data_issue: 'Brak danych', analysis: 'Analiza',
  analysis_item: 'Element analizy',
}
export const EVENT_TYPE_LABEL: Record<string, string> = {
  zmiana_terminu: 'Zmiana terminu', zmiana_wynagrodzenia: 'Zmiana wynagrodzenia', roboty_dodatkowe: 'Roboty dodatkowe', opoznienie: 'Opóźnienie',
  wyplata_powyzej_wartosci: 'Wypłata powyżej wartości', fragment_ryzykowny: 'Ryzykowny fragment dokumentu', uniewaznienie: 'Unieważnienie',
  jedna_oferta: 'Jedna oferta', nienalezyte_wykonanie: 'Nienależyte wykonanie', odwolanie_kio: 'Odwołanie do KIO',
}
export const ACTION_LABEL: Record<string, string> = {
  accept: 'zatwierdzenie', edit: 'poprawka', reject: 'odrzucenie', exemplary: 'oznaczenie jako wzorcowe', unexemplary: 'zdjęcie wzorca',
  reopen: 'ponowne otwarcie', relink: 'zmiana powiązania', import: 'import', propose: 'propozycja systemu',
}
export const SOURCE_LABEL: Record<string, string> = {
  bzp: 'BZP (e-Zamówienia)', organizer_xlsx: 'Plik organizatora (xlsx)', riskminer: 'Obliczenie RISK MINER', vat_whitelist: 'Biała lista VAT',
  upload: 'Dokument wgrany', nik: 'Raport NIK', ted: 'TED', kio: 'KIO', knowledge: 'Wiedza ekspercka',
}
