# Hosting – rekomendacja (21.11.2026)

## Wymagania
- **Aplikacja** (db + api + worker + web + Caddy): 4–8 vCPU, 16 GB RAM, ≥ 80 GB dysku. Baza po załadowaniu warstwy
  automatycznej (113 tys. ogłoszeń BZP) ma ok. 4 GB; z kopią BZP, surowymi danymi i pamięcią LLM – ok. 10 GB.
- **Bielik 11B v3.0** (Q4_K_M, 6,7 GB) z kontekstem 8k: ≥ 10 GB VRAM, żeby cały model był na GPU. Na laptopowej
  RTX 4060 8 GB działa w 70% na GPU: ~15 tokenów/s, cechy inwestycji ~1–1,5 min, przyczyna zdarzenia ~12 s.
  Na samym CPU – kilka minut na wywołanie (nieużywalne na żywo).
- **Lokalizacja danych:** dane są publiczne (BZP), ale dokumenty wgrywane przez instytucję mogą nie być – preferujemy
  UE, najlepiej Polskę; model lokalny = dane nie opuszczają serwera (baner „Przetwarzanie LLM: lokalnie”).

## Porównanie (ceny netto; sprawdzić na stronie dostawcy przed zakupem – źródła poniżej podają różne wartości)

| Opcja | Co dostajemy | Koszt | Lokalizacja | Uwagi |
|---|---|---|---|---|
| **A. Scaleway L4-1-24G, Warszawa (WAW2)** | 1× NVIDIA L4 24 GB, 8 vCPU, 48 GB RAM – aplikacja **i** Bielik na jednej maszynie | ~0,75–0,79 €/h, rozliczane co minutę (~550 €/mies.; **~40 € za 48 h oceny**) | **Polska** | Cały Bielik w VRAM (zmieści też Q8); dostępność L4 w WAW2 zmienna – sprawdzić w konsoli |
| **B. Hetzner Cloud CX43/CX53 + Bielik z pamięci (replay)** | 8–16 vCPU, 16–32 GB RAM, bez GPU | ~16–29,5 €/mies. | Niemcy/Finlandia | Najtańsze; odpowiedzi Bielika policzone na naszym GPU, serwowane z `data/llm_cache` (`LLM_MODE=replay`), nowe zapytania → reguły. CX bywa niedostępny do zamówienia |
| C. Hetzner GEX44 (dedykowany) | RTX 4000 Ada 20 GB, 64 GB RAM | ~184–234 €/mies. + opłata startowa | Niemcy | Umowa miesięczna, sens przy wdrożeniu produkcyjnym, nie na 2 dni |
| D. Google Cloud g2-standard-8, Warszawa | 1× L4 24 GB, 8 vCPU, 32 GB RAM | ~1,08 $/h (~786 $/mies.) | Polska | Droższe od A, więcej konfiguracji (IAM, VPC) |
| E. OVHcloud L4 | 1× L4 | ~0,75 €/h (≈1 $/h) | Francja (GRA) | GPU OVH nie są dostępne w Warszawie |

## Rekomendacja
1. **Na hackathon (ocena 22.11): opcja A – Scaleway L4 w Warszawie.** Jedna maszyna, dane w Polsce, Bielik na żywo
   na GPU (jury widzi „Wniosek modelu” liczony lokalnie), płacimy tylko za godziny działania; po ocenie wyłączamy.
   Wdrożenie: obraz „Ubuntu GPU OS” (sterowniki NVIDIA + docker + nvidia-container-toolkit), potem
   `deploy/deploy.sh root@<ip> --bootstrap --with-data --bielik`.
2. **Zapas / gdy L4 w WAW2 niedostępne: opcja B** – Hetzner CX43 z `LLM_MODE=replay` i pamięcią odpowiedzi Bielika
   (wszystkie wywołania demo – 3 analizy, przyczyny zdarzeń 22 projektów – policzone wcześniej na naszym GPU).
   Uczciwie opisane w `docs/status.md`: na serwerze bez GPU nowe zapytania LLM spadają do reguł.
3. **Docelowo (instytucja):** serwer z GPU w kraju lub on-premise (opcja A/C albo infrastruktura resortu) –
   konfiguracja się nie zmienia (profil `local_bielik` = dowolny serwer zgodny z OpenAI API: Ollama, vLLM).

## Konfiguracja Bielika w aplikacji
- Profil `local_bielik` w `config/settings.yaml`: `provider: openai`, `base_url: http://localhost:11434/v1`
  (w dockerze: `http://ollama:11434/v1` – ustawia `deploy.sh --bielik`), model `riskminer-bielik`
  = `SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M` + `num_ctx 8192` (`deploy/ollama/Modelfile`; domyślne 4096 ucinałoby
  dokument + schemat JSON).
- Routing: wszystkie zadania `[local_bielik, claude, rules]` – najpierw model lokalny, Claude tylko gdy jest klucz
  i Bielik niedostępny, na końcu zawsze reguły. Zmiana w UI: Źródła i operacje → Modele językowe.
- Każda odpowiedź modelu przechodzi bramkę cytatu (cytat musi występować dosłownie w źródle), inaczej zostaje wynik
  reguł; zapis w `llm_call` (zadanie, profil, czas, tokeny, miejsce przetwarzania).
- Lokalnie: `ollama pull SpeakLeash/bielik-11b-v3.0-instruct:Q4_K_M && ollama create riskminer-bielik -f deploy/ollama/Modelfile`,
  test: `riskminer llm test local_bielik`.

## Źródła (ceny z 21.11.2026, wyszukiwanie)
- Scaleway L4: [cennik GPU](https://scaleway.com/en/pricing/gpu), [L4 – FAQ/WAW2](https://scaleway.com/en/docs/faq/instances), [dostępność w regionach](https://scaleway.com/en/docs/account/reference-content/products-availability), [GPU docs (waw-2)](https://www.scaleway.com/en/docs/compute/gpu)
- Hetzner: [zmiana cen (oficjalnie)](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/), [ceny 2026 – cloudtally](https://cloudtally.eu/hetzner-cloud-prices), [CX dostępność – bitdoze](https://www.bitdoze.com/hetzner-cloud-cost-optimized-plans/), [GEX44 – bex.co](https://bex.co/blog/2026/07/13/hetzner-gex44-gpu-pricing-break-even), [GEX44 – hosting.gallery](https://hosting.gallery/companies/hetzner-com/dedicated-servers/gex44-nvidia-rtx-4000)
- Google Cloud: [ceny akceleratorów](https://cloud.google.com/products/compute/pricing/accelerator-optimized?hl=en), [g2-standard-8 europe-central2 – Holori](https://calculator.holori.com/gcp/vm/g2-standard-8/europe-central2)
- OVHcloud: [Cloud GPU](https://www.ovhcloud.com/en/public-cloud/gpu/), [L4 – computeprices](https://computeprices.com/providers/ovhcloud/gpus/l4)
- Bielik: [bielik.ai](https://www.bielik.ai/en), [Bielik-11B-v3.0-Instruct (HF)](https://huggingface.co/speakleash/Bielik-11B-v3.0-Instruct) – brak polskiego hostowanego API; zalecane uruchomienie własne (Ollama / vLLM)
