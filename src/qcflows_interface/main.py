from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from qiskit import QuantumCircuit
import sys

sys.path.append("./qcircuit-relayer")
from qcircuit_relayer import PlatformLibrary, JobType

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your Netlify domain in prod
    allow_methods=["*"],
    allow_headers=["*"],
)

library = PlatformLibrary()


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
