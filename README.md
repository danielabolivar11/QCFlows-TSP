# QCFlows
Quantum Correlation Flows

Run `uv run uvicorn qcflows_api.main:app --reload` and open `http://127.0.0.1:8000` for a small live K-matrix demo using `/v0/k-matrix`.

The API also exposes `/v0/metric-matrix` for pairwise K, EoF, and MI matrices from 2-qubit RDM inputs. The `/graph_data` route accepts `metric=k`, `metric=eof`, or `metric=mi` for frontend graph rendering.
