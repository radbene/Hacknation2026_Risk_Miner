# Uruchomienie i wdrożenie

## 1. Lokalnie (programista)

```bash
cp .env.example .env
cp config/settings.example.yaml config/settings.yaml
make up migrate        # Postgres 16 + pgvector w dockerze (port 55432), schemat
make api               # API :8040 – dokumentacja http://localhost:8040/api/docs
make worker            # kolejka zadań
make web               # interfejs :5180 (proxy /api → :8040)
make demo              # pełny przebieg: wiedza → import → wzbogacenie → zdarzenia → analizy → eksport → raport
make test
```

## 2. Pełny stos produkcyjny lokalnie (test przed wdrożeniem)

Osobny projekt compose (`rmtest`) z innymi portami – nie dotyka deweloperskiej bazy na 55432:

```bash
deploy/local-prod-test.sh up      # build + start db, api, worker, web, caddy; test /api/health i BZP
deploy/local-prod-test.sh demo    # riskminer demo w kontenerze api
deploy/local-prod-test.sh down
```

Interfejs: http://localhost:8088 (Caddy z `DOMAIN=:80`, czyli bez TLS).

## 3. Serwer (Hetzner Cloud)

**Zalecany serwer:** CX32 lub CPX31 (4 vCPU, 8 GB RAM, 80 GB dysku), lokalizacja **Falkenstein/Norymberga (DE)
lub Helsinki (FI)**, czyli wszystko działa w UE. Obraz: Ubuntu 24.04.

1. Załóż serwer w konsoli Hetzner i dodaj swój klucz SSH. Zapisz adres IPv4, np. `1.2.3.4`.
2. Domena: bez kupowania – `1.2.3.4.sslip.io` (wildcard DNS wskazuje na IP). Caddy sam pobiera certyfikat
   Let's Encrypt.
3. Pierwsze wdrożenie (instaluje docker i ufw z portami 22/80/443 oraz swap 4 GB):

   ```bash
   deploy/deploy.sh root@1.2.3.4 --bootstrap --with-data --demo
   ```

   Skrypt:
   - synchronizuje kod (`rsync`, bez `.git`, `.env`, `data/`);
   - tworzy na serwerze `.env` z losowym hasłem bazy i `SECRET_KEY` oraz ustawia `DOMAIN=<ip>.sslip.io` i `CORS_ORIGINS`;
   - kopiuje `config/settings.example.yaml` → `config/settings.yaml` (tylko za pierwszym razem);
   - uruchamia `docker compose --profile prod up -d --build`;
   - robi test dymny: `https://<domena>/api/health`, strona główna, `riskminer monitor probe`
     (dostęp do lustra BZP i do ezamowienia.gov.pl z własnym User-Agent);
   - z `--with-data` wysyła `data/` (paczka BZP, raw store, cache odpowiedzi LLM do trybu replay);
   - z `--demo` uruchamia `riskminer demo` w kontenerze.
4. Klucze API (opcjonalnie): `ssh root@1.2.3.4 nano /opt/riskminer/.env` (`ANTHROPIC_API_KEY=…`), potem
   `docker compose --profile prod up -d`. Bez kluczy działa profil `rules` (bez LLM) oraz odtwarzanie z cache.
5. Kolejne wdrożenia: `deploy/deploy.sh root@1.2.3.4` (albo `make deploy HOST=root@1.2.3.4`).

## 4. Usługi i dane

| Usługa | Obraz | Rola |
|---|---|---|
| db | pgvector/pgvector:pg16 | Postgres + pgvector, wolumen `pgdata` |
| api | riskminer-backend | `alembic upgrade head` + uvicorn :8040 (2 workery) |
| worker | riskminer-backend | kolejka zadań (`job`) + APScheduler: monitoring co `MONITOR_INTERVAL_MIN` min (domyślnie 360) |
| web | riskminer-web | statyczny build React (Caddy :80 w kontenerze) |
| caddy | caddy:2 | HTTPS, `/api/*` → api, reszta → web; wolumeny `caddy_data`, `caddy_config` |

Trwałość danych między restartami: baza w wolumenie `pgdata`; pliki w katalogach hosta `data/` (raw store,
wgrane dokumenty, paczka BZP, cache LLM, złoty zrzut `data/snapshots/golden`) i `exports/`. Konfiguracja:
`config/` (tylko do odczytu w kontenerze) i `knowledge/`.

## 5. Gdzie przetwarzane są dane

- Baza, pliki, embeddingi: na serwerze w UE (Hetzner DE/FI).
- Modele językowe: zgodnie z profilem w `config/settings.yaml` (`data_location`: `local` | `eu` | `non_eu` | `none`).
  Interfejs pokazuje to na pasku „Miejsce przetwarzania danych”.
- Do modeli trafiają wyłącznie fragmenty publicznych ogłoszeń BZP, fragmenty wgranych dokumentów i opis nowej
  inwestycji, po usunięciu danych osobowych.

## 6. Operacje

```bash
docker compose --profile prod logs -f api worker
docker compose exec api riskminer monitor run --as-of 2026-05-01     # odtworzenie stanu na dzień
docker compose exec api riskminer snapshot save                      # złoty zrzut (reset piaskownicy)
docker compose exec api riskminer report                             # docs/raport_z_testu.md
docker compose exec api riskminer embed                              # wektory opisów (model ~220 MB przy 1. uruchomieniu)
docker compose exec api riskminer ocr                                # OCR zapisanych skanów bez warstwy tekstowej
docker compose exec db pg_dump -U riskminer riskminer | gzip > backup.sql.gz
```
