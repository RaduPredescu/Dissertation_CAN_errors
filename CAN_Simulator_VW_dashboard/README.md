# CAN Lab v0.5 — Volkswagen Tiguan III 2025 · 2.0 TDI DSG 4MOTION

**Proiect funcțional offline**: simulator CAN/DBC de referință + scenarii controlate + analiză deterministă a cauzelor probabile + FastAPI + dashboard React, cu mașină SVG interactivă, roți individuale, telemetrie și inspector de payload HEX.

Profil auto: 2025 Tiguan CT, **2.0 TDI 142 kW (193 CP), DSG cu 7 trepte, 4MOTION**, pe baza specificațiilor VW. Nivelul de echipare nu este modelat.

> **Important:** nu este o diagnoză de service autentică, nu comunică cu un automobil și nu trebuie folosit pentru reparații. *Niciun cadru CAN nu este capturat din Tiguan 2025*. Modelul fizic, DTC-urile și valorile efective sunt simulate. Nu există încă agenți AI/MCP/LiteLLM/AKS.

## Ce este nou față de versiunea Ford

- Am păstrat designul dashboard-ului React (sidebar, hartă vehicul, timeline, carduri, inspector HEX).
- SVG nou cu patru roți clicabile, plus TDI, EGR, DPF, DSG, 12 V, ABS și tracțiunea 4MOTION.
- Panou **Cauze**: componenta, ipoteza principală, *de ce* a apărut alerta, dovezi numerice, cauze alternative, verificări recomandate și incertitudini.
- 9 scenarii reexecutabile offline; DTC-uri **ilustrative**, separate de simptome. Pentru DSG/AWD nu atribuim coduri OEM neverificate.
- Cadre HEX cu CAN ID, lungime, decodare și marcaj de checksum neimplementat.
- `ground_truth.json` separat de API și de datele observate.

## Rulare pe Ubuntu / Debian

Dezarhivează proiectul și asigură-te că terminalul se află în directorul ce conține `tiguan_sim/`, `dashboard_api/`, `dashboard_web/` și `requirements.txt`.

Terminal 1 — backend:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m tiguan_sim --scenario all --backend offline
python -m uvicorn dashboard_api.app:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2 — frontend (Node.js 20.19+ sau 22.12+):

```bash
cd dashboard_web
npm install
npm run dev
```

Apoi deschide **http://127.0.0.1:5173**. La primul start, cele 9 scenarii sunt deja incluse în `output/observations/` și nu trebuie regenerate.

API interactiv: **http://127.0.0.1:8000/docs**.

Dacă ai deja proiectul Ford, **nu suprascrie folderul acestuia**. Deschide Tiguan ca proiect separat.

## Primul experiment recomandat

1. Selectează **ABS sensor FR**. La începutul simulării nu există anomalie.
2. Mută timeline-ul la **30 s**. Roata **FR** (față dreapta) este marcată și există alerta `ABS_FR_SIGNAL_LOSS`.
3. Apasă **Cauze**: vei vedea diferența dintre viteza FR, celelalte roți și verificările posibile. Codul `C101B` este demonstrativ, nu citit dintr-un Tiguan real.
4. Compară cu scenariul **ABS encoder FR**, unde semnalul cade intermitent, nu rămâne zero.
5. Testează **Compound**: scăderea tensiunii 12 V precede pierderea mesajelor ESP; interpretează corelația temporală, fără a o confunda cu demonstrarea cauzei fizice.
6. Deschide **CAN frame inspector** și apasă pe mesajul `ESP_NEW_1` pentru a vedea valorile celor patru roți codificate în payload-ul HEX.

## Scenarii

| ID | Ce simulează | Observația diagnostică |
|---|---|---|
| `healthy` | Comportament normal | Nicio eroare |
| `abs_fr_sensor` | Pierdere semnal FR | Roată FR aproape 0 în mers |
| `abs_fr_encoder` | Căderi intermitente FR | Valori FR implauzibile |
| `dpf_restriction` | Restricție DPF | Presiune diferențială și soot estimate ridicate |
| `egr_flow` | Răspuns EGR prea mic | EGR comandat vs feedback |
| `dsg_overheat` | Creștere temperatură transmisie | DSG temp peste pragul demo |
| `awd_clutch` | Cuplare spate sub cerere | Requested vs actual AWD |
| `low_voltage` | Tensiune 12 V în scădere | Prag de alimentare |
| `compound` | Tensiune 12 V + pierdere ECU ABS | Corelație temporală, nu dovadă de cauzalitate |

## CAN, DBC și LIMITĂRI (foarte important pentru disertație)

### Ce este derivat dintr-o definiție OpenDBC

Fișierul **`dbc/vw_mqbevo_reference_subset.dbc`** conține un subset al unor mesaje din proiectul public [commaai/OpenDBC – `vw_mqbevo.dbc`](https://github.com/commaai/opendbc/blob/master/opendbc/dbc/vw_mqbevo.dbc):

- `Motor_04`, CAN ID `0x107` — include turație motor și trepte;
- `Getriebe_11`, CAN ID `0x0AD` — include selecție treaptă și unele stări de transmisie;
- `ESP_NEW_1`, CAN ID `0x0FC` — include câmpuri numite `WHEEL_SPEED_FL/FR/RL/RR` într-un mesaj exploratoriu CAN-FD.

**Acestea sunt layout-uri de referință, NU validări că Tiguan CT 2025 le transmite identic.** Unitatea și interpretarea exactă a semnalelor de roată pe mașina 2025 nu sunt stabilite; în UI sunt valori demonstrative. Semnalele din DPF, EGR, DSG oil temperature, 12 V și AWD sunt modelate în `telemetry.jsonl` ca senzori virtuali, **nu sunt prezentate ca DIDs/semnale OEM decodate din CAN**.

`ESP_NEW_1` și `Getriebe_11` conțin câmpuri de checksum în DBC, dar simulatorul **NU implementează checksum-ul VW**, folosind 0 pentru aceste câmpuri. Aceste cadre sunt pentru **inspecție offline, nu injectare într-un bus de vehicul**. În inspector este afișat `checksum_validated: false`.

### Verificarea cu fișierul original DBC

Opțional (necesită Internet și `curl`):

```bash
sudo apt install -y curl
bash scripts/fetch_vw_dbc.sh
```

Scriptul descarcă un DBC public upstream, afișează SHA-256 și compară layout-urile subsetului cu cele din versiunea descărcată. **O potrivire de definiții între două fișiere nu confirmă compatibilitatea pe un Tiguan 2025**. Pentru reproducibilitate academică, arhivează commit-ul și SHA-ul efectiv utilizat.

### DTC-uri

C101B, P0401, P2463 și P0562 sunt coduri **exemplificative** asociate unor simptome simulate; nu avem citiri autentice din ECU-ul Tiguan 2025. Un cod DTC nu demonstrează singur piesa defectă. Pentru DSG și AWD nu inventăm DTC-uri OEM.

Acest MVP **nu implementează încă un server UDS 0x19** și nici o sesiune ISO-TP reală. Vizualizările DTC reprezintă memoria *virtuală* de erori, nu cadre de răspuns UDS capturate.

## API-uri

| Metodă | Endpoint | Rol |
|---|---|---|
| GET | `/api/health` | Sănătate + limite de integrare |
| GET | `/api/scenarios` | 9 scenarii |
| GET | `/api/scenarios/abs_fr_sensor` | Evenimente, ipoteze, DTC și telemetrie |
| GET | `/api/scenarios/abs_fr_sensor/frames?at=30` | CAN ID și HEX în jurul timpului selectat |
| POST | `/api/runs/abs_fr_sensor` | Regenerează offline un scenariu cunoscut |

Nu există API pentru `output/evaluation/ground_truth.json`, nicio integrare AI și nicio transmisie către hardware real.

## Teste

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
```

Backend-ul și simulatorul au fost testate. **Build-ul frontend Vite nu a fost executat în mediul de generare** deoarece pachetele npm nu au fost disponibile offline; sintaxa JSX a fost verificată cu parserul TypeScript. Rulează `npm install` și `npm run build` local dacă vrei validarea completă.

## Organizare

```text
tiguan_sim/                  # dinamică, DBC codec, detector, generator offline
dbc/vw_mqbevo_reference_subset.dbc
scripts/fetch_vw_dbc.sh     # verificare opțională cu OpenDBC
dashboard_api/              # FastAPI read-only
 dashboard_web/             # React/Vite, hartă SVG
output/observations/        # cadre, telemetrie, anomalii și DTC simulate
output/evaluation/          # ground truth, NUMAI pentru evaluare
tests/                       # teste de regresie
```

## Referințe

- [Volkswagen Tiguan — specificații tehnice](https://www.volkswagen.de/de/modelle/tiguan.html/__ui/technische-daten.app)
- [OpenDBC – MQBevo DBC](https://github.com/commaai/opendbc/blob/master/opendbc/dbc/vw_mqbevo.dbc)
- [VIS4VAG — Tiguan CT 2024+, inclusiv Brake Electronics](https://diagnostics.vis4vag.com/en/vw/tiguan-ct-mqb-2024/)
- [Licență OpenDBC (MIT)](https://github.com/commaai/opendbc/blob/master/LICENSE)

## Dezvoltarea ulterioară

Primul pas ulterior: ECU virtual ABS cu diagnoză UDS/ISO-TP pe vcan, apoi MCP read-only, LiteLLM și orchestratorul multi-agent în AKS. **Nu pretindem că sistemul actual este deja un tester OEM.**
