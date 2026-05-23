const samples = {
  bell: {
    num_qubits: 2,
    basis: "z",
    rdms: [{
      qubits: [0, 1],
      rho: [
        [0.5, 0, 0, 0.5],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0.5, 0, 0, 0.5],
      ],
    }],
  },
  product: {
    num_qubits: 2,
    basis: "z",
    rdms: [{
      qubits: [0, 1],
      rho: [
        [1, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
      ],
    }],
  },
  wPair: {
    num_qubits: 2,
    basis: "z",
    rdms: [{
      qubits: [0, 1],
      rho: [
        [0.3333333333, 0, 0, 0],
        [0, 0.3333333333, 0.3333333333, 0],
        [0, 0.3333333333, 0.3333333333, 0],
        [0, 0, 0, 0],
      ],
    }],
  },
};

const requestBody = document.querySelector("#request-body");
const responseBody = document.querySelector("#response-body");
const statusText = document.querySelector("#status");

function showSample(name) {
  requestBody.value = JSON.stringify(samples[name], null, 2);
}

async function runDemo() {
  statusText.textContent = "Running";
  responseBody.textContent = "";

  try {
    const payload = JSON.parse(requestBody.value);
    const response = await fetch("/v0/k-matrix", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    responseBody.textContent = JSON.stringify(body, null, 2);
    statusText.textContent = response.ok ? "OK" : `HTTP ${response.status}`;
  } catch (error) {
    responseBody.textContent = JSON.stringify({error: error.message}, null, 2);
    statusText.textContent = "Error";
  }
}

document.querySelectorAll("[data-sample]").forEach((button) => {
  button.addEventListener("click", () => showSample(button.dataset.sample));
});
document.querySelector("#run-button").addEventListener("click", runDemo);

showSample("bell");
runDemo();
