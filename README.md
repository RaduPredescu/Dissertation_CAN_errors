
# CAN Lab — AI-Assisted Automotive Diagnostics

### Volkswagen Tiguan III (2025) · 2.0 TDI · 7-speed DSG · 4MOTION

An experimental platform developed for a master's dissertation on **multi-agent AI orchestration in Azure Kubernetes Service (AKS) for automotive CAN error analysis**.

The project simulates vehicle telemetry and faults, encodes selected signals into CAN/CAN-FD payloads using a Volkswagen MQBevo reference DBC subset, applies deterministic diagnostic rules, and presents the results in an interactive web dashboard.

The planned research extension introduces Model Context Protocol (MCP) servers, LLM-powered diagnostic agents, LiteLLM, LangGraph, and deployment on AKS.

> **Research prototype — not a vehicle diagnostic tool.**
> No traffic has been captured from an actual 2025 Tiguan. Vehicle behavior, fault scenarios, diagnostic trouble codes (DTCs), and measurements are simulated. The public DBC definitions are reference layouts; compatibility with this exact model has not been verified.


## Features (#IN PROGRESS)

- **Nine reproducible scenarios** covering normal vehicle operation, ABS wheel-speed faults, DPF, EGR, DSG, 4MOTION, low voltage, and correlated anomalies.
- **CAN frame inspector** displaying CAN IDs, hexadecimal payloads, message names, and decoded signal values.
- **Interactive vehicle visualization** highlighting affected components, including individual wheels.
- **Diagnostic explanation panel** showing observed symptoms, probable causes, alternative explanations, numerical evidence, and recommended checks.
- **Telemetry timeline** displaying vehicle speed, engine RPM, wheel speeds, battery voltage, and selected powertrain parameters.
- **Separate evaluation data** containing injected fault labels, deliberately excluded from dashboard API responses.

---

## System Architecture

### Current Implementation (v0.5)

```text
        Volkswagen Tiguan Simulator
                    |
          +---------+---------+
          |                   |
      CAN Encoder        Vehicle Telemetry
      (DBC-based)             |
          |             Fault Injection
          |                   |
     CAN/CAN-FD         Anomaly Detector
      HEX Frames              |
          |                   |
          +---------+---------+
                    |
              Observations
              Events / DTCs
                    |
               FastAPI
                    |
             React Dashboard
                    |
         Interactive Diagnostics
```

Injected fault labels are stored separately in the evaluation dataset and are not exposed through the application API.

### Target Dissertation Architecture

```text
          CAN Simulator
                |
        CAN Preprocessing
                |
          MCP Servers
        /      |      \
       /       |       \
  CAN Data  Diagnostic  Knowledge
       \       |       /
        \      |      /
         AI Orchestrator
           (LangGraph)
                |
      +---------+---------+
      |         |         |
    Triage   Specialist  Validation
    Agent      Agents      Agent
      |         |         |
      +---------+---------+
                |
             LiteLLM
                |
             LLM API
                |
       Structured Diagnosis
                |
             FastAPI
                |
         React Dashboard
```

The complete system is intended to run in **Azure Kubernetes Service (AKS)**.

Kubernetes manages container deployment, scaling, and availability, while LangGraph coordinates the reasoning workflow between AI agents.

MCP provides access to diagnostic tools and vehicle data. LiteLLM provides a unified interface for accessing language models.

---

## Technology Stack

| Layer | Technology |
| --- | --- |
| Simulation | Python |
| CAN definitions | OpenDBC MQBevo |
| CAN decoding | DBC-based decoder |
| Backend | FastAPI |
| Frontend | React |
| Frontend tooling | Vite |
| AI agents | LLM-based agents (planned) |
| Agent orchestration | LangGraph (planned) |
| Tool integration | MCP (planned) |
| LLM gateway | LiteLLM (planned) |
| Containerization | Docker (planned) |
| Cloud orchestration | Azure Kubernetes Service (planned) |

---

## Installation

### Requirements

- Python 3.11+
- Node.js 20.19+ or 22.12+
- npm
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/RaduPredescu/Dissertation_CAN_errors.git

cd Dissertation_CAN_errors
```

All following backend commands must be executed from the directory containing `tiguan_sim/`, `dashboard_api/`, and `requirements.txt`.

### 2. Create a Python Virtual Environment

```bash
python3 -m venv .venv

source .venv/bin/activate
```

Install the Python dependencies:

```bash
python -m pip install -r requirements.txt
```

### 3. Generate CAN Simulation Data

Run all available scenarios:

```bash
python -m tiguan_sim --scenario all --backend offline
```

Run an individual scenario:

```bash
python -m tiguan_sim --scenario abs_fr_sensor --backend offline
```

### 4. Start the FastAPI Backend

```bash
python -m uvicorn dashboard_api.app:app \
  --reload \
  --host 127.0.0.1 \
  --port 8000
```

API documentation:

http://127.0.0.1:8000/docs

### 5. Start the React Frontend

Open another terminal:

```bash
cd dashboard_web

npm install

npm run dev
```

Open the dashboard:

http://127.0.0.1:5173

The Vite development server proxies API requests to the FastAPI backend.

---

## Available Simulation Scenarios

| Scenario | Description |
| --- | --- |
| `healthy` | Normal vehicle operation |
| `abs_fr_sensor` | Front-right ABS wheel-speed sensor failure |
| `abs_fr_encoder` | Intermittent or implausible wheel-speed signal |
| `dpf_restriction` | Diesel particulate filter restriction |
| `egr_flow` | EGR flow deviation |
| `dsg_overheat` | DSG transmission overheating |
| `awd_clutch` | 4MOTION rear coupling malfunction |
| `low_voltage` | Low 12 V electrical system voltage |
| `compound` | Low voltage followed by ABS communication failure |

Each scenario follows a deterministic 55-second simulated driving cycle.

Faults are introduced at predefined timestamps, making the scenarios reproducible and suitable for experimental evaluation.

---

## CAN Data Processing

The simulator generates hexadecimal CAN frames using selected message definitions from the Volkswagen MQBevo reference DBC.

A typical decoding process follows:

```text
CAN ID + HEX Payload
         |
         v
  DBC Message Lookup
         |
         v
    Signal Extraction
         |
         v
  Physical Value Conversion
         |
         v
    Anomaly Detection
         |
         v
   Diagnostic Analysis
```

A DBC definition describes:

- CAN message identifiers
- Signal positions and bit lengths
- Byte order
- Scaling factors
- Offsets
- Physical units

The general decoding formula is:

```text
Physical Value = Raw Value * Factor + Offset
```

The decoder converts hexadecimal payloads into interpretable vehicle parameters.

**Important:** The DBC reference does not establish full compatibility with the Volkswagen Tiguan III 2025. The generated payloads are simulated and must not be treated as actual traffic captured from the vehicle.

---

## Diagnostic Processing

The current implementation uses deterministic rules to detect abnormal vehicle behavior.

For example, an ABS wheel-speed sensor fault can be detected by comparing the reported speed of each wheel.

If three wheels report similar speeds while the front-right wheel reports zero, the system identifies an anomalous wheel-speed signal.

The diagnostic explanation includes:

- Affected component
- Observed abnormal behavior
- Supporting measurements
- Probable causes
- Alternative explanations
- Recommended verification procedures

A detected anomaly does not automatically prove that a specific physical component is defective.

Possible causes may include sensors, wiring, connectors, encoders, or electronic control units.

---

## Output Files

Simulation results are stored in:

```text
output/
├── observations/
│   └── abs_fr_sensor/
│       ├── frames.jsonl
│       ├── candump.log
│       ├── telemetry.jsonl
│       ├── events.jsonl
│       ├── dtcs.jsonl
│       └── summary.json
│
└── evaluation/
    └── abs_fr_sensor/
        └── ground_truth.json
```

### File Descriptions

| File | Purpose |
| --- | --- |
| `frames.jsonl` | Generated CAN frames and decoded signals |
| `candump.log` | CAN traffic in hexadecimal dump format |
| `telemetry.jsonl` | Time-series vehicle measurements |
| `events.jsonl` | Detected anomalies |
| `dtcs.jsonl` | Simulated diagnostic trouble codes |
| `summary.json` | Simulation results and metadata |
| `ground_truth.json` | Known injected faults for evaluation |

The `ground_truth.json` files must remain inaccessible to AI diagnostic agents.

This separation prevents the models from directly accessing the expected answers during experimental evaluation.

---

## REST API

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/health` | Application health status |
| GET | `/api/scenarios` | List simulation scenarios |
| GET | `/api/scenarios/{scenario}` | Retrieve scenario observations |
| GET | `/api/scenarios/{scenario}/frames?at=30` | Retrieve CAN frames near a timestamp |
| POST | `/api/runs/{scenario}` | Execute a simulation scenario |

The current backend operates on locally generated simulation files.

It does not communicate with a physical vehicle, LLM, or Azure cluster.

---

## Repository Structure

```text
.
├── tiguan_sim/
│   ├── scenarios/
│   ├── codec/
│   ├── detector/
│   └── runner/
│
├── dbc/
│
├── dashboard_api/
│
├── dashboard_web/
│
├── scripts/
│
├── tests/
│
├── output/
│   ├── observations/
│   └── evaluation/
│
├── requirements.txt
│
└── README.md
```

The diagram above illustrates the logical project organization. Internal Python modules may be organized differently in the current implementation.

---

## Testing

Run the Python tests:

```bash
python -m unittest discover -s tests -v
```

Build the React frontend:

```bash
cd dashboard_web

npm run build
```

For a functional dashboard test:

1. Start the FastAPI backend.
2. Start the React frontend.
3. Select the `abs_fr_sensor` scenario.
4. Move the simulation timeline to approximately 30 seconds.
5. Inspect the highlighted front-right wheel.
6. Review the diagnostic explanation and supporting CAN frames.

---

## Planned AI Agent Architecture

The next development phase will introduce specialized AI agents for vehicle diagnostics.

### Triage Agent

Receives detected anomalies, determines the affected automotive subsystem, and selects the appropriate diagnostic workflow.

### Specialist Agents

Analyze faults within specific subsystems, including:

- ABS and braking systems
- Diesel engine and emissions systems
- DSG transmission
- 4MOTION all-wheel-drive system
- Electrical systems and CAN communication

Specialist agents will use MCP tools to retrieve relevant vehicle observations and technical information.

### Diagnostic Agent

Correlates symptoms, evaluates possible failure mechanisms, and generates evidence-based diagnostic hypotheses.

### Validation Agent

Reviews the proposed diagnosis, checks supporting measurements, identifies contradictions, and requests additional investigation when necessary.

### Orchestrator

The LangGraph orchestrator will manage:

- Agent execution order
- Conditional workflow routing
- Shared investigation state
- Parallel specialist execution
- Tool access
- Validation and retry decisions
- Final diagnostic report generation

---

## Model Context Protocol (MCP)

MCP servers will provide standardized access to vehicle telemetry, diagnostic information, and technical knowledge.

Planned tools include:

```python
get_vehicle_status()

get_active_dtcs()

get_wheel_speeds()

get_signal_history(signal, start_time, end_time)

get_can_frames(start_time, end_time)

get_detected_anomalies()

get_component_information(component)
```

Agents will access these tools through MCP rather than reading simulator files directly.

The initial MCP implementation will be read-only.

---

## LiteLLM Integration

LiteLLM will provide a unified interface between the AI agents and external language model APIs.

Planned capabilities include:

- Model routing
- Centralized API configuration
- Authentication
- Token usage monitoring
- Request logging
- Latency measurements
- Error handling
- Model comparison

The model provider will remain configurable.

This separation allows the AI orchestration architecture to be evaluated independently of a specific LLM provider.

---

## Azure Kubernetes Service (AKS)

The target infrastructure will deploy the application as containerized services in Azure Kubernetes Service.

Planned services include:

```text
Azure Kubernetes Service
|
├── React Dashboard
├── FastAPI Backend
├── CAN Simulator
├── MCP Servers
├── AI Agent Runtime
├── LangGraph Orchestrator
├── LiteLLM Gateway
└── Observability Services
```

Container images will be stored in Azure Container Registry.

Kubernetes will manage service deployment, communication, scaling, and recovery.

The AI orchestration workflow will be managed independently by LangGraph.

---

## Research Objectives

The dissertation aims to investigate the effectiveness of multi-agent AI orchestration for automotive diagnostic analysis.

The experimental evaluation will compare:

1. Deterministic rule-based diagnosis
2. Single-agent LLM diagnosis
3. Multi-agent LLM