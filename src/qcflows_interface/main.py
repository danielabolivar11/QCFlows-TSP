from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from pydantic import BaseModel
from bridge import simulate_marker
from qiskit import QuantumCircuit
import sys

sys.path.append("./qcircuit-relayer")
from qcircuit_relayer import PlatformLibrary, JobType

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your Netlify for prod
    allow_methods=["*"],
    allow_headers=["*"],
)

library = PlatformLibrary()


class _Op(BaseModel):
    gate: str
    qubits: list[int]
    params: dict[str, float] = {}

class RDMRequest(BaseModel):
    num_qubits: int
    operations: list[_Op]
    markers: list[int] | None = None

@app.post("/rdms")
def rdms(req: RDMRequest):
    ops = [op.model_dump() for op in req.operations]
    total = len(ops)
    markers = req.markers if req.markers is not None else list(range(total + 1))
    results = []
    for m in markers:
        if m < 0 or m > total:
            raise HTTPException(status_code=422, detail=f"Marker {m} is out of range 0..{total}")
        results.append({"marker": m, **simulate_marker(req.num_qubits, ops[:m])})
    return {"num_qubits": req.num_qubits, "results": results}


def make_bell() -> QuantumCircuit:
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    return qc


@app.post("/run-bell")
def run_bell(shots: int = 1024):
    platform = library.get("aer")
    platform.connect()
    backend = platform.get_backend()
    engine = platform.engine(backend)

    circuit = make_bell()
    job = engine.submit(circuit, JobType.SAMPLER, shots=shots)
    result = job.result()

    counts = result[0].data.meas.get_counts()
    return {"job_id": job.id, "counts": counts}
