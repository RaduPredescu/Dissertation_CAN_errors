# CAN Lab v0.6 — Dynamic DBC Engine

**Volkswagen Tiguan III (2025) · 2.0 TDI · DSG · 4MOTION**  
Master's dissertation prototype: CAN error simulation and the future orchestration of diagnostic AI agents in AKS.

The dashboard and nine fault scenarios from v0.5 are preserved. **New in v0.6:** a DBC-driven generator that discovers CAN messages and signals automatically, plus a searchable **DBC Explorer** in the React dashboard.

> **Important:** Traffic and faults are synthetic. Public VW MQBevo DBC layouts are not verified for this exact Tiguan 2025. An unknown signal can be encoded with a neutral synthetic value; it is **not** a measurement from the real vehicle. OEM checksums, bus timing, UDS and physical behavior are not automatically deduced from DBC. Never inject generated frames onto a real vehicle CAN bus.

## Quick start (Ubuntu)

Open a terminal **inside the project root** (the folder with `tiguan_sim/` and `dashboard_web/`):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m tiguan_sim --scenario all --backend offline
python -m uvicorn dashboard_api.app:app --reload --host 127.0.0.1 --port 8000
```

Open a **second** terminal:

```bash
cd dashboard_web
npm install
npm run dev
```

Open **http://127.0.0.1:5173**. Expand **DBC Explorer** below the signal charts to search CAN IDs, messages and individual signals, including bit positions, factors, offsets and how test values are generated.

The bundled `vw_mqbevo_reference_subset.dbc` contains **3 sample message definitions** and runs even without `cantools`, using the limited built-in parser. For Intel/Motorola signals, signed values, multiplexing and a full DBC, install `cantools` (included in `requirements.txt`).

## Using the entire public MQBevo DBC

While your virtual environment is active, download the upstream DBC:

```bash
bash scripts/fetch_vw_dbc.sh
```

Run the **complete DBC** structurally (no fixed list of CAN IDs):

```bash
python -m tiguan_sim \
  --scenario abs_fr_sensor \
  --backend offline \
  --engine dynamic \
  --dbc dbc/upstream/vw_mqbevo.dbc
```

To use the same DBC in the dashboard and for its **Run scenario** button, restart the backend with:

```bash
CAN_LAB_DBC_PATH=dbc/upstream/vw_mqbevo.dbc \
  python -m uvicorn dashboard_api.app:app --reload --host 127.0.0.1 --port 8000
```

The dashboard's DBC Explorer shows every message the parser can load. Generation attempts every message; unsupported encodings are recorded in `summary.json → messages_skipped` rather than silently claimed as valid.

**The complete upstream DBC is not bundled**; download it yourself. The file SHA-256 is logged with generated results. The default sampled rate is **at most 2 frames/s per message**, to keep the demo manageable, not the OEM frame frequency.

To reduce test volume:

```bash
python -m tiguan_sim --scenario healthy --engine dynamic \
  --dbc dbc/upstream/vw_mqbevo.dbc --max-messages 30
```

To run the original v0.5 hard-coded subset generator for comparison:

```bash
python -m tiguan_sim --scenario healthy --engine legacy
```

## What is generated automatically?

| DBC field | From DBC automatically? |
| --- | --- |
| Message name, CAN ID, payload length | Yes |
| Signal bit positions and byte order | Yes |
| Signed values, scaling, offset, choices, multiplexing | With `cantools` (where supported) |
| Generic hexadecimal frame generation | Attempted for each message |
| Realistic speed/RPM/ABS values | Only where mapped to the vehicle model |
| Other, unmapped signals | Neutral **synthetic** placeholders |
| OEM CRC and accurate counters | **No**, placeholder / not validated |
| UDS diagnostic sessions and DTC semantics | Separate future implementation |

See [`config/signal_sources.json`](config/signal_sources.json) for **declarative signal-to-state mappings**. Add mappings here to connect additional DBC signals to physical models, without changing the frame generator. `tiguan_sim/scenarios.py` still provides the existing simplified driving-cycle and fault models.

## API

- `GET /api/scenarios` — scenarios
- `GET /api/scenarios/{id}` — observations, simulated DTCs and rules
- `GET /api/scenarios/{id}/frames?at=30` — hexadecimal CAN frames and their origin tags
- `POST /api/runs/{id}` — run a scenario with the configured DBC
- `GET /api/dbc/messages?search=RPM&offset=0&limit=40` — searchable DBC catalog
- `GET /api/dbc/messages/{name}` — definitions for one message

Injected fault ground truth is stored separately in `output/evaluation/` and is **never served through the API**.

## Tests

```bash
python -m unittest discover -s tests -v
cd dashboard_web && npm run build
```

## Roadmap

- Higher-fidelity physical behavior models and documented CAN timing
- Virtual UDS/ISO-TP ECU diagnostic interfaces
- Read-only MCP servers and LLM agents via LiteLLM
- LangGraph multi-agent orchestration and deployment in AKS

**Status:** The simulator, deterministic diagnostics, FastAPI and React dashboard work locally; MCP/AI/AKS are future work.
