# Distributed PBFT Consensus System

An interactive PBFT (Practical Byzantine Fault Tolerance) demo system where **real users can join as replicas** and participate in the consensus process. The project also includes a **communication reliability experiment** that compares Monte‑Carlo results with theoretical success rates under a point‑to‑point independent link model.

## Highlights

- **Interactive consensus demo**: users join via QR code/link and act as specific replicas
- **Real-time messaging**: Socket.IO based real-time communication
- **Visualization**: node states, message flows, and consensus progress
- **Mobile friendly**: works well on phones for multi-user participation
- **Reliability experiment**: batch Monte‑Carlo runs + theoretical (dashed) curve on the same chart

## Architecture

### Frontend (Vue 3 + Element Plus)
- **Home page**: configure parameters, create session, generate QR code
- **Node page**: user participates as a replica (simplified UI)
- **Realtime**: Socket.IO client

### Backend (FastAPI + Socket.IO)
- **Session management**: create/manage sessions
- **WebSocket service**: real-time transport
- **PBFT engine**: three-phase consensus + experiment endpoints

## Quick Start

### 1) Install dependencies

```bash
# frontend
npm install

# backend
cd backend
pip install -r requirements.txt
cd ..
```

### 2) Start services

#### Option A: start script (recommended)

```bash
chmod +x start.sh
./start.sh
```

#### Option B: start manually

```bash
# backend
cd backend
python main.py

# frontend (new terminal)
npm run dev
```

Frontend runs at `http://localhost:3000`, backend runs at `http://localhost:8000`.

### 3) Smoke test

```bash
python test_backend.py
```

## Two experiment modes

This project supports **two complementary modes**:

### A) Interactive consensus demo (human-in-the-loop)

Use this mode when you want multiple users to join and manually trigger actions.

- **Create a session**: open `http://localhost:3000` and create a session on the home page
- **Invite users**: share the generated QR code / link
- **Participate**: users join as replicas and send prepare/commit at the appropriate time

PBFT phases:
- **Pre-prepare**: primary (node 0) proposes a value
- **Prepare**: replicas broadcast prepare messages
- **Commit**: replicas broadcast commit messages

Fault model:
- replicas can be configured as Byzantine
- optional malicious primary and message tampering (for demonstration)

### B) Reliability experiment (p–success-rate curve)

This mode measures how link reliability \(p\) impacts PBFT success probability under a **point-to-point independent link model** and compares:
- **Experimental**: backend Monte‑Carlo batch runs
- **Theoretical**: backend enumeration derived from Theorem 1 (Eq. (1)–(6)) (shown as a dashed line)

#### Definition (aligned with backend implementation)

- **Link model**: each message on each directed link succeeds independently with probability \(p\) (`messageDeliveryRate` in 0–100%)
- **Per-node threshold**: in prepare/commit, a node requires \(\ge 2f\) successful messages **from other nodes**
- **Success criterion (Metric A)**: number of commit-success nodes \(N_c \ge N - f\)
- **Fault bound**: \(f=\lfloor (N-1)/3 \rfloor\)

#### How to run

1. Start backend + frontend, open `http://localhost:3000`
2. Switch to the **Experiment** page (side navigation)
3. Configure:
   - `nodeCount`
   - `messageDeliveryRate` (p as a percentage)
   - `rounds` (Monte‑Carlo rounds per p)
4. Start the experiment; the frontend calls the backend batch endpoint and plots results

#### Batch API

- **Endpoint**: `POST /api/sessions/{session_id}/run-batch-experiment?rounds=30`
- **Key fields**:
  - `experimentalSuccessRate` (percentage)
  - `theoreticalSuccessRate` (percentage)
  - `results` (per-round success/failure + message stats)

> Note: if you change backend experiment/decision logic, **restart the backend**, otherwise the UI may still connect to an old running process and the curves will look “misaligned”.

## Simplified node UI

The node page is intentionally simplified for non-expert users:

- **Kept**: progress, received messages, topology visualization, final result/stats
- **Term mapping**:
  - “node” → “participant”
  - “pre-prepare/prepare/commit” → “propose/prepare/confirm”
  - “proposal value” → “proposal content”

## Tech stack

- **Frontend**: Vue 3, Vue Router, Element Plus, ECharts, Socket.IO client
- **Backend**: FastAPI, python-socketio, Pydantic, Uvicorn

## Project structure

```text
distributed-pbft/
├── src/
│   ├── views/
│   │   ├── HomePage.vue      # controller + experiment UI
│   │   ├── JoinPage.vue      # join page
│   │   └── NodePage.vue      # simplified node UI
├── backend/
│   ├── main.py               # backend server
│   └── requirements.txt      # python deps
├── package.json
├── vite.config.js
└── README.md
```

## Use cases

- **Teaching demo**: distributed systems / blockchain courses
- **Team collaboration**: multi-user consensus decision making
- **Research**: PBFT behavior under message loss
- **PoC**: prototype for interactive distributed systems

## Roadmap

- [ ] Support more consensus algorithms (Raft, Paxos, ...)
- [ ] Add network delay + richer network fault models
- [ ] Add replay/history viewer
- [ ] Extend Byzantine behaviors

## Contributing

Issues and pull requests are welcome.

## License

MIT License