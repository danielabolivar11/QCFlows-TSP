# Local Install

This is the backend/API setup for QCFlows.
It lets you compute pairwise metrics directly from density matrices, list stored experiments, and run local circuit simulations.

## Requirements

- Python 3.11+
- `uv`

Install dependencies from the repository root:

```bash
uv sync
```

## Run the API

For direct metric endpoints and stored experiments:

```bash
uv run uvicorn qcflows_api.main:app --host 127.0.0.1 --port 8000
```

Check it:

```bash
curl http://127.0.0.1:8000/health
```

Open the small built-in API demo:

```text
http://127.0.0.1:8000/
```

## Calculate Metrics From RDMs

The `/v0/metric-matrix` endpoint does not need the circuit simulation worker.
It accepts 2-qubit reduced density matrices and returns a pairwise metric matrix.

Example Bell-pair RDM:

```bash
curl -sS http://127.0.0.1:8000/v0/metric-matrix \
  -H 'content-type: application/json' \
  --data '{
    "num_qubits": 2,
    "basis": "z",
    "metric": "k",
    "rdms": [
      {
        "qubits": [0, 1],
        "rho": [
          [0.5, 0.0, 0.0, 0.5],
          [0.0, 0.0, 0.0, 0.0],
          [0.0, 0.0, 0.0, 0.0],
          [0.5, 0.0, 0.0, 0.5]
        ]
      }
    ]
  }'
```

Set `"metric"` to `"k"`, `"eof"`, or `"mi"`.

## Stored Experiments

List stored experiments:

```bash
curl http://127.0.0.1:8000/experiments
```

Load one experiment:

```bash
curl http://127.0.0.1:8000/experiments/qft-5
```

The experiment files live in:

```text
src/qcflows_api/data/experiments/
```

## Run Local Circuit Simulation

The `/simulate` endpoint calls a separate local interface worker. Start it in one terminal:

```bash
cd src/qcflows_interface
uv run uvicorn main:app --host 127.0.0.1 --port 8003
```

Then start the API in another terminal:

```bash
INTERFACE_URL=http://127.0.0.1:8003 \
  uv run uvicorn qcflows_api.main:app --host 127.0.0.1 --port 8000
```

Run a Bell circuit through the simulator:

```bash
curl -sS http://127.0.0.1:8000/simulate \
  -H 'content-type: application/json' \
  --data '{
    "num_qubits": 2,
    "all_metrics": true,
    "operations": [
      {"gate": "h", "qubits": [0], "params": {}},
      {"gate": "cx", "qubits": [0, 1], "params": {}}
    ]
  }'
```
