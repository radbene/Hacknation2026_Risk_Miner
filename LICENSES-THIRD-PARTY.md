# Licencje stron trzecich (SBOM)

Plik generowany: `cd backend && uv run riskminer licences --check` (źródła: `backend/uv.lock`, `frontend/package-lock.json`, `config/settings.example.yaml`). Kod projektu: **Apache-2.0**.

- zależności Python: 150, npm: 225
- **GPL/AGPL: 0** ✓
- wymagające uwagi (LGPL/MPL): 15 – certifi (Mozilla Public License 2.0 (MPL 2.0)), psycopg (LGPL-3.0-only), psycopg-binary (LGPL-3.0-only), lightningcss (MPL-2.0), lightningcss-android-arm64 (MPL-2.0), lightningcss-darwin-arm64 (MPL-2.0), lightningcss-darwin-x64 (MPL-2.0), lightningcss-freebsd-x64 (MPL-2.0), lightningcss-linux-arm-gnueabihf (MPL-2.0), lightningcss-linux-arm64-gnu (MPL-2.0), lightningcss-linux-arm64-musl (MPL-2.0), lightningcss-linux-x64-gnu (MPL-2.0), lightningcss-linux-x64-musl (MPL-2.0), lightningcss-win32-arm64-msvc (MPL-2.0), lightningcss-win32-x64-msvc (MPL-2.0)
- bez deklaracji licencji w metadanych: 0
- tylko w opcjonalnych dodatkach (`embeddings`, `litellm`; nie instalowane w obrazie): 64 – m.in. torch (BSD-3), sentence-transformers (Apache-2.0), transformers (Apache-2.0), biblioteki NVIDIA CUDA (licencja NVIDIA, redystrybucja dozwolona) – sprawdzić przed włączeniem

**psycopg (LGPL-3.0)** – sterownik PostgreSQL używany bez modyfikacji, ładowany dynamicznie jako osobny pakiet; LGPL nie obejmuje kodu aplikacji. Nie używamy PyMuPDF (AGPL), Ghostscript ani ocrmypdf.

## Źródła danych

| Źródło | Licencja / podstawa | URL |
|---|---|---|
| Biuletyn Zamówień Publicznych (e-Zamówienia API) | informacja publiczna (ustawa o dostępie do informacji publicznej, art. 1–2; ponowne wykorzystywanie – ustawa z 11.08.2021) | https://ezamowienia.gov.pl |
| Paczka ogłoszeń BZP 2021–2026 (lustro organizatora HackNation) | jak BZP – informacja publiczna; kopia udostępniona przez organizatora | https://bzp.cytr.us/paczka/risk_miner_bzp_kopia.zip |
| Biała lista podatników VAT (KAS) | rejestr publiczny (art. 96b ustawy o VAT), API bezpłatne | https://wl-api.mf.gov.pl |
| Raporty NIK (wod-kan) | dokumenty publiczne (informacja publiczna) | https://www.nik.gov.pl |
| TED – Tenders Electronic Daily | dane otwarte UE (decyzja Komisji 2011/833/UE – ponowne wykorzystanie) | https://ted.europa.eu |
| KRS – API Ministerstwa Sprawiedliwości | rejestr publiczny | https://api-krs.ms.gov.pl |
| Orzeczenia KIO (UZP) | dokumenty publiczne | https://orzeczenia.uzp.gov.pl |
| Baza Konkurencyjności 2021 | informacja publiczna | https://bazakonkurencyjnosci.funduszeeuropejskie.gov.pl |
| Lista 22 projektów i materiały eksperckie MFiPR (docx) | materiały organizatora udostępnione na potrzeby HackNation 2026 |  |

## Modele

| Profil / model | Licencja | Uwagi |
|---|---|---|
| rules: none/- | brak modelu (reguły deterministyczne) | przetwarzanie: none |
| claude: anthropic/claude-opus-5-5 | usługa API (Anthropic Commercial Terms) – brak trenowania na danych API | przetwarzanie: non_eu |
| claude_fast: anthropic/claude-haiku-5-5 | usługa API (Anthropic Commercial Terms) – brak trenowania na danych API | przetwarzanie: non_eu |
| openai: openai/- | usługa API (OpenAI Services Agreement) | przetwarzanie: non_eu |
| azure_eu: openai/- | usługa API (OpenAI Services Agreement) | przetwarzanie: eu |
| gemini: gemini/- | usługa API (Google Gemini API Terms) | przetwarzanie: non_eu |
| gemini_vertex_eu: gemini/- | usługa API (Google Gemini API Terms) | przetwarzanie: eu |
| local_bielik: openai_compatible/riskminer-bielik | Apache-2.0 (SpeakLeash Bielik 11B v2.x) | przetwarzanie: local |
| sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 | Apache-2.0 | embeddingi, lokalnie (opcjonalnie) |

## Python (backend/uv.lock)

| Pakiet | Wersja | Licencja | Ocena |
|---|---|---|---|
| alembic | 1.20.1 | MIT | ok |
| annotated-doc | 0.0.7 | MIT | ok |
| annotated-types | 0.8.0 | MIT | ok |
| anthropic | 2.12.0 | Apache Software License | ok |
| anyio | 4.16.0 | MIT | ok |
| apscheduler | 3.11.3 | MIT License | ok |
| certifi | 2026.11.20 | Mozilla Public License 2.0 (MPL 2.0) | note |
| cffi | 2.1.1 | MIT-0 | ok |
| charset-normalizer | 3.5.2 | MIT | ok |
| click | 8.5.1 | BSD-3-Clause | ok |
| cloudpickle | 3.1.3 | BSD-3-Clause | ok |
| coverage | 7.17.4 | Apache-2.0 | ok |
| cryptography | 50.0.2 | Apache-2.0 OR BSD-3-Clause | ok |
| distro | 1.9.0 | Apache Software License | ok |
| docstring-parser | 0.18.0 | MIT License | ok |
| et-xmlfile | 2.0.0 | MIT License | ok |
| fastapi | 0.165.0 | MIT | ok |
| google-auth | 2.63.0 | Apache Software License | ok |
| google-genai | 3.6.1 | Apache-2.0 | ok |
| h11 | 0.16.0 | MIT License | ok |
| httpcore | 1.0.9 | BSD-3-Clause | ok |
| httpcore2 | 2.16.2 | BSD-3-Clause | ok |
| httptools | 0.9.0 | MIT | ok |
| httpx | 0.28.1 | BSD License | ok |
| httpx2 | 2.16.2 | BSD-3-Clause | ok |
| idna | 3.20 | BSD-3-Clause | ok |
| iniconfig | 2.3.1 | MIT | ok |
| jiter | 0.19.0 | MIT | ok |
| joblib | 1.6.0 | BSD-3-Clause | ok |
| lxml | 6.1.3 | BSD-3-Clause | ok |
| mako | 1.4.3 | MIT | ok |
| markdown-it-py | 4.3.0 | MIT License | ok |
| markupsafe | 3.0.4 | BSD-3-Clause | ok |
| mdurl | 0.1.2 | MIT License | ok |
| narwhals | 2.29.0 | MIT | ok |
| numpy | 2.5.5 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | ok |
| openai | 3.57.0 | Apache-2.0 | ok |
| openpyxl | 3.1.5 | MIT License | ok |
| opentelemetry-api | 1.45.2 | Apache-2.0 | ok |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | ok |
| pdfminer-six | 20260107 | MIT | ok |
| pdfplumber | 0.11.11 | MIT License | ok |
| pgvector | 0.5.1 | MIT | ok |
| pillow | 13.0.0 | MIT-CMU | ok |
| pluggy | 1.7.0 | MIT License | ok |
| psycopg | 3.3.9 | LGPL-3.0-only | note |
| psycopg-binary | 3.3.9 | LGPL-3.0-only | note |
| pyasn1 | 0.6.5 | BSD-2-Clause | ok |
| pyasn1-modules | 0.4.2 | BSD License | ok |
| pycparser | 3.12 | BSD-3-Clause | ok |
| pydantic | 2.14.4 | MIT | ok |
| pydantic-core | 2.50.5 | MIT | ok |
| pydantic-settings | 2.16.3 | MIT | ok |
| pygments | 2.21.0 | BSD-2-Clause | ok |
| pypdf | 7.1.1 | BSD-3-Clause | ok |
| pypdfium2 | 5.15.2 | BSD-3-Clause, Apache-2.0, dependency licenses | ok |
| pytest | 9.2.0 | MIT | ok |
| pytest-cov | 7.1.0 | MIT | ok |
| python-docx | 1.2.0 | MIT License | ok |
| python-dotenv | 1.2.4 | BSD-3-Clause | ok |
| python-multipart | 0.0.34 | Apache-2.0 | ok |
| pyyaml | 6.0.4 | MIT License | ok |
| rapidfuzz | 3.14.6 | MIT | ok |
| requests | 2.34.2 | Apache Software License | ok |
| rich | 15.0.0 | MIT License | ok |
| ruff | 0.17.6 | MIT | ok |
| scikit-learn | 1.9.1 | BSD-3-Clause | ok |
| scipy | 1.18.1 | BSD License | ok |
| selectolax | 1.0.2 | MIT | ok |
| shellingham | 1.5.4 | ISC License (ISCL) | ok |
| sniffio | 1.3.1 | MIT License / Apache Software License | ok |
| sqlalchemy | 2.1.9 | MIT | ok |
| starlette | 1.10.0 | BSD-3-Clause | ok |
| tenacity | 9.1.4 | Apache Software License | ok |
| threadpoolctl | 3.8.0 | BSD-3-Clause | ok |
| truststore | 0.10.5 | MIT | ok |
| typer | 0.29.2 | MIT | ok |
| typing-extensions | 4.16.0 | PSF-2.0 | ok |
| typing-inspection | 0.4.5 | MIT | ok |
| tzlocal | 5.4.5 | MIT | ok |
| urllib3 | 2.8.0 | MIT | ok |
| uvicorn | 0.54.0 | BSD-3-Clause | ok |
| uvloop | 0.23.0 | Apache Software License / MIT License | ok |
| watchfiles | 1.3.0 | MIT License | ok |
| websockets | 17.4 | BSD-3-Clause | ok |
| xlrd | 2.0.2 | BSD License | ok |

## npm (frontend/package-lock.json)

| Pakiet | Wersja | Licencja | Ocena |
|---|---|---|---|
| @babel/code-frame | 7.29.7 | MIT | ok (dev) |
| @babel/helper-validator-identifier | 7.29.7 | MIT | ok (dev) |
| @emnapi/core | 2.0.0-beta.2 | MIT | ok (dev) |
| @emnapi/core | 1.11.3 | MIT | ok (dev) |
| @emnapi/runtime | 2.0.0-beta.2 | MIT | ok (dev) |
| @emnapi/runtime | 1.11.3 | MIT | ok (dev) |
| @emnapi/wasi-threads | 2.2.0 | MIT | ok (dev) |
| @emnapi/wasi-threads | 1.2.3 | MIT | ok (dev) |
| @fontsource-variable/inter | 5.3.0 | OFL-1.1 | ok |
| @jridgewell/gen-mapping | 0.3.13 | MIT | ok (dev) |
| @jridgewell/remapping | 2.3.5 | MIT | ok (dev) |
| @jridgewell/resolve-uri | 3.1.3 | MIT | ok (dev) |
| @jridgewell/sourcemap-codec | 1.6.0 | MIT | ok (dev) |
| @jridgewell/trace-mapping | 0.3.31 | MIT | ok (dev) |
| @napi-rs/canvas | 1.2.0 | MIT | ok |
| @napi-rs/canvas-android-arm64 | 1.2.0 | MIT | ok |
| @napi-rs/canvas-darwin-arm64 | 1.2.0 | MIT | ok |
| @napi-rs/canvas-darwin-x64 | 1.2.0 | MIT | ok |
| @napi-rs/canvas-linux-arm-gnueabihf | 1.2.0 | MIT | ok |
| @napi-rs/canvas-linux-arm64-gnu | 1.2.0 | MIT | ok |
| @napi-rs/canvas-linux-arm64-musl | 1.2.0 | MIT | ok |
| @napi-rs/canvas-linux-riscv64-gnu | 1.2.0 | MIT | ok |
| @napi-rs/canvas-linux-x64-gnu | 1.2.0 | MIT | ok |
| @napi-rs/canvas-linux-x64-musl | 1.2.0 | MIT | ok |
| @napi-rs/canvas-win32-arm64-msvc | 1.2.0 | MIT | ok |
| @napi-rs/canvas-win32-x64-msvc | 1.2.0 | MIT | ok |
| @napi-rs/wasm-runtime | 1.2.6 | MIT | ok (dev) |
| @napi-rs/wasm-runtime | 1.2.2 | MIT | ok (dev) |
| @oxc-project/types | 0.156.0 | MIT | ok (dev) |
| @oxlint/binding-android-arm-eabi | 1.94.0 | MIT | ok (dev) |
| @oxlint/binding-android-arm64 | 1.94.0 | MIT | ok (dev) |
| @oxlint/binding-darwin-arm64 | 1.94.0 | MIT | ok (dev) |
| @oxlint/binding-darwin-x64 | 1.94.0 | MIT | ok (dev) |
| @oxlint/binding-freebsd-x64 | 1.94.0 | MIT | ok (dev) |
| @oxlint/binding-linux-arm-gnueabihf | 1.94.0 | MIT | ok (dev) |
| @oxlint/binding-linux-arm-musleabihf | 1.94.0 | MIT | ok (dev) |
| @oxlint/binding-linux-arm64-gnu | 1.94.0 | MIT | ok (dev) |
| @oxlint/binding-linux-arm64-musl | 1.94.0 | MIT | ok (dev) |
| @oxlint/binding-linux-ppc64-gnu | 1.94.0 | MIT | ok (dev) |
| @oxlint/binding-linux-riscv64-gnu | 1.94.0 | MIT | ok (dev) |
| @oxlint/binding-linux-riscv64-musl | 1.94.0 | MIT | ok (dev) |
| @oxlint/binding-linux-s390x-gnu | 1.94.0 | MIT | ok (dev) |
| @oxlint/binding-linux-x64-gnu | 1.94.0 | MIT | ok (dev) |
| @oxlint/binding-linux-x64-musl | 1.94.0 | MIT | ok (dev) |
| @oxlint/binding-openharmony-arm64 | 1.94.0 | MIT | ok (dev) |
| @oxlint/binding-win32-arm64-msvc | 1.94.0 | MIT | ok (dev) |
| @oxlint/binding-win32-ia32-msvc | 1.94.0 | MIT | ok (dev) |
| @oxlint/binding-win32-x64-msvc | 1.94.0 | MIT | ok (dev) |
| @redocly/ajv | 8.11.2 | MIT | ok (dev) |
| @redocly/config | 0.22.0 | MIT | ok (dev) |
| @redocly/openapi-core | 1.34.24 | MIT | ok (dev) |
| @reduxjs/toolkit | 2.15.0 | MIT | ok |
| @rolldown/binding-android-arm-eabi | 1.2.19 | MIT | ok (dev) |
| @rolldown/binding-android-arm64 | 1.2.19 | MIT | ok (dev) |
| @rolldown/binding-darwin-arm64 | 1.2.19 | MIT | ok (dev) |
| @rolldown/binding-darwin-x64 | 1.2.19 | MIT | ok (dev) |
| @rolldown/binding-freebsd-x64 | 1.2.19 | MIT | ok (dev) |
| @rolldown/binding-linux-arm-gnueabihf | 1.2.19 | MIT | ok (dev) |
| @rolldown/binding-linux-arm64-gnu | 1.2.19 | MIT | ok (dev) |
| @rolldown/binding-linux-arm64-musl | 1.2.19 | MIT | ok (dev) |
| @rolldown/binding-linux-ppc64-gnu | 1.2.19 | MIT | ok (dev) |
| @rolldown/binding-linux-s390x-gnu | 1.2.19 | MIT | ok (dev) |
| @rolldown/binding-linux-x64-gnu | 1.2.19 | MIT | ok (dev) |
| @rolldown/binding-linux-x64-musl | 1.2.19 | MIT | ok (dev) |
| @rolldown/binding-openharmony-arm64 | 1.2.19 | MIT | ok (dev) |
| @rolldown/binding-wasm32-wasi | 1.2.19 | MIT | ok (dev) |
| @rolldown/binding-win32-arm64-msvc | 1.2.19 | MIT | ok (dev) |
| @rolldown/binding-win32-x64-msvc | 1.2.19 | MIT | ok (dev) |
| @rolldown/pluginutils | 1.1.1 | MIT | ok (dev) |
| @standard-schema/spec | 1.1.0 | MIT | ok |
| @standard-schema/utils | 0.3.0 | MIT | ok |
| @tailwindcss/node | 4.3.5 | MIT | ok (dev) |
| @tailwindcss/oxide | 4.3.5 | MIT | ok (dev) |
| @tailwindcss/oxide-android-arm64 | 4.3.5 | MIT | ok (dev) |
| @tailwindcss/oxide-darwin-arm64 | 4.3.5 | MIT | ok (dev) |
| @tailwindcss/oxide-darwin-x64 | 4.3.5 | MIT | ok (dev) |
| @tailwindcss/oxide-freebsd-x64 | 4.3.5 | MIT | ok (dev) |
| @tailwindcss/oxide-linux-arm-gnueabihf | 4.3.5 | MIT | ok (dev) |
| @tailwindcss/oxide-linux-arm64-gnu | 4.3.5 | MIT | ok (dev) |
| @tailwindcss/oxide-linux-arm64-musl | 4.3.5 | MIT | ok (dev) |
| @tailwindcss/oxide-linux-x64-gnu | 4.3.5 | MIT | ok (dev) |
| @tailwindcss/oxide-linux-x64-musl | 4.3.5 | MIT | ok (dev) |
| @tailwindcss/oxide-wasm32-wasi | 4.3.5 | MIT | ok (dev) |
| @tailwindcss/oxide-win32-arm64-msvc | 4.3.5 | MIT | ok (dev) |
| @tailwindcss/oxide-win32-x64-msvc | 4.3.5 | MIT | ok (dev) |
| @tailwindcss/vite | 4.3.5 | MIT | ok (dev) |
| @tanstack/history | 1.162.5 | MIT | ok |
| @tanstack/query-core | 5.108.2 | MIT | ok |
| @tanstack/react-query | 5.108.2 | MIT | ok |
| @tanstack/react-router | 1.170.46 | MIT | ok |
| @tanstack/react-store | 0.11.2 | MIT | ok |
| @tanstack/react-table | 9.3.1 | MIT | ok |
| @tanstack/router-core | 1.171.39 | MIT | ok |
| @tanstack/store | 0.11.2 | MIT | ok |
| @tanstack/table-core | 9.3.1 | MIT | ok |
| @tybys/wasm-util | 0.10.3 | MIT | ok (dev) |
| @tybys/wasm-util | 0.10.5 | MIT | ok (dev) |
| @types/d3-array | 3.2.2 | MIT | ok |
| @types/d3-color | 3.1.3 | MIT | ok |
| @types/d3-drag | 3.0.7 | MIT | ok |
| @types/d3-ease | 3.0.2 | MIT | ok |
| @types/d3-interpolate | 3.0.4 | MIT | ok |
| @types/d3-path | 3.1.1 | MIT | ok |
| @types/d3-scale | 4.0.9 | MIT | ok |
| @types/d3-selection | 3.0.12 | MIT | ok |
| @types/d3-shape | 3.2.0 | MIT | ok |
| @types/d3-time | 3.0.4 | MIT | ok |
| @types/d3-timer | 3.0.2 | MIT | ok |
| @types/d3-transition | 3.0.9 | MIT | ok |
| @types/d3-zoom | 3.0.9 | MIT | ok |
| @types/node | 24.19.2 | MIT | ok (dev) |
| @types/react | 19.3.0 | MIT | ok (dev) |
| @types/react-dom | 19.3.0 | MIT | ok (dev) |
| @types/use-sync-external-store | 0.0.6 | MIT | ok |
| @vitejs/plugin-react | 6.3.0 | MIT | ok (dev) |
| @xyflow/react | 13.0.2 | MIT | ok |
| @xyflow/system | 1.0.0 | MIT | ok |
| agent-base | 7.1.4 | MIT | ok (dev) |
| ansi-colors | 4.1.3 | MIT | ok (dev) |
| argparse | 2.0.1 | Python-2.0 | ok (dev) |
| balanced-match | 1.0.2 | MIT | ok (dev) |
| brace-expansion | 2.1.8 | MIT | ok (dev) |
| change-case | 5.4.4 | MIT | ok (dev) |
| class-variance-authority | 0.7.1 | Apache-2.0 | ok |
| classcat | 5.0.5 | MIT | ok |
| clsx | 2.1.1 | MIT | ok |
| colorette | 1.4.0 | MIT | ok (dev) |
| cookie-es | 3.1.1 | MIT | ok |
| csstype | 3.2.4 | MIT | ok (dev) |
| d3-array | 3.2.5 | ISC | ok |
| d3-color | 3.1.1 | ISC | ok |
| d3-dispatch | 3.0.2 | ISC | ok |
| d3-drag | 3.0.1 | ISC | ok |
| d3-ease | 3.0.2 | BSD-3-Clause | ok |
| d3-format | 3.1.3 | ISC | ok |
| d3-interpolate | 3.0.2 | ISC | ok |
| d3-path | 3.1.1 | ISC | ok |
| d3-scale | 4.0.3 | ISC | ok |
| d3-selection | 3.0.1 | ISC | ok |
| d3-shape | 3.2.1 | ISC | ok |
| d3-time | 3.1.1 | ISC | ok |
| d3-time-format | 4.1.1 | ISC | ok |
| d3-timer | 3.0.2 | ISC | ok |
| d3-transition | 3.0.2 | ISC | ok |
| d3-zoom | 3.0.1 | ISC | ok |
| debug | 4.4.3 | MIT | ok (dev) |
| decimal.js-light | 2.5.1 | MIT | ok |
| detect-libc | 2.1.2 | Apache-2.0 | ok (dev) |
| enhanced-resolve | 5.27.0 | MIT | ok (dev) |
| es-toolkit | 1.53.2 | MIT | ok |
| eventemitter3 | 5.0.4 | MIT | ok |
| fast-deep-equal | 3.1.3 | MIT | ok (dev) |
| fdir | 6.5.0 | MIT | ok (dev) |
| fsevents | 2.3.3 | MIT | ok (dev) |
| graceful-fs | 4.2.12 | BlueOak-1.0.0 | ok (dev) |
| https-proxy-agent | 7.0.6 | MIT | ok (dev) |
| immer | 11.2.10 | MIT | ok |
| index-to-position | 1.2.0 | MIT | ok (dev) |
| internmap | 2.0.3 | ISC | ok |
| isbot | 5.2.3 | Unlicense | ok |
| jiti | 2.7.0 | MIT | ok (dev) |
| js-levenshtein | 1.1.6 | MIT | ok (dev) |
| js-tokens | 4.0.0 | MIT | ok (dev) |
| js-yaml | 4.3.2 | MIT | ok (dev) |
| json-schema-traverse | 1.0.0 | MIT | ok (dev) |
| lightningcss | 1.33.0 | MPL-2.0 | note (dev) |
| lightningcss-android-arm64 | 1.33.0 | MPL-2.0 | note (dev) |
| lightningcss-darwin-arm64 | 1.33.0 | MPL-2.0 | note (dev) |
| lightningcss-darwin-x64 | 1.33.0 | MPL-2.0 | note (dev) |
| lightningcss-freebsd-x64 | 1.33.0 | MPL-2.0 | note (dev) |
| lightningcss-linux-arm-gnueabihf | 1.33.0 | MPL-2.0 | note (dev) |
| lightningcss-linux-arm64-gnu | 1.33.0 | MPL-2.0 | note (dev) |
| lightningcss-linux-arm64-musl | 1.33.0 | MPL-2.0 | note (dev) |
| lightningcss-linux-x64-gnu | 1.33.0 | MPL-2.0 | note (dev) |
| lightningcss-linux-x64-musl | 1.33.0 | MPL-2.0 | note (dev) |
| lightningcss-win32-arm64-msvc | 1.33.0 | MPL-2.0 | note (dev) |
| lightningcss-win32-x64-msvc | 1.33.0 | MPL-2.0 | note (dev) |
| lucide-react | 1.77.0 | ISC | ok |
| magic-string | 1.4.5 | MIT | ok (dev) |
| minimatch | 5.1.9 | ISC | ok (dev) |
| ms | 2.1.3 | MIT | ok (dev) |
| nanoid | 3.3.20 | MIT | ok (dev) |
| openapi-fetch | 0.17.0 | MIT | ok |
| openapi-typescript | 7.13.0 | MIT | ok (dev) |
| openapi-typescript-helpers | 0.1.0 | MIT | ok |
| oxlint | 1.94.0 | MIT | ok (dev) |
| parse-json | 8.3.0 | MIT | ok (dev) |
| pdfjs-dist | 6.5.438 | Apache-2.0 | ok |
| picocolors | 1.1.1 | ISC | ok (dev) |
| picomatch | 4.0.7 | MIT | ok (dev) |
| pluralize | 8.0.0 | MIT | ok (dev) |
| postcss | 8.5.33 | MIT | ok (dev) |
| react | 19.3.1 | MIT | ok |
| react-compiler-runtime | 1.0.0 | MIT | ok |
| react-dom | 19.3.1 | MIT | ok |
| react-is | 19.3.1 | MIT | ok |
| react-redux | 9.3.1 | MIT | ok |
| recharts | 3.11.0 | MIT | ok |
| redux | 5.0.1 | MIT | ok |
| redux-thunk | 3.1.0 | MIT | ok |
| require-from-string | 2.0.2 | MIT | ok (dev) |
| reselect | 5.2.0 | MIT | ok |
| rolldown | 1.2.19 | MIT | ok (dev) |
| scheduler | 0.28.0 | MIT | ok |
| seroval | 1.8.2 | MIT | ok |
| seroval-plugins | 1.8.0 | MIT | ok |
| source-map-js | 1.2.4 | BSD-3-Clause | ok (dev) |
| supports-color | 10.2.2 | MIT | ok (dev) |
| tailwind-merge | 3.7.1 | MIT | ok |
| tailwindcss | 4.3.5 | MIT | ok (dev) |
| tapable | 2.3.4 | MIT | ok (dev) |
| tiny-invariant | 1.3.3 | MIT | ok |
| tinyglobby | 0.2.17 | MIT | ok (dev) |
| tslib | 2.8.1 | 0BSD | ok (dev) |
| tslib | 2.9.1 | 0BSD | ok (dev) |
| type-fest | 4.41.0 | (MIT OR CC0-1.0) | ok (dev) |
| typescript | 5.9.3 | Apache-2.0 | ok (dev) |
| undici-types | 7.24.6 | MIT | ok (dev) |
| uri-js-replace | 1.0.3 | MIT | ok (dev) |
| use-sync-external-store | 1.7.0 | MIT | ok |
| victory-vendor | 37.4.1 | MIT AND ISC AND BSD-3-Clause | ok |
| vite | 8.3.8 | MIT | ok (dev) |
| yaml-ast-parser | 0.0.43 | Apache-2.0 | ok (dev) |
| yargs-parser | 21.1.1 | ISC | ok (dev) |
| zustand | 5.1.0 | MIT | ok |
