const runTestsBtn = document.querySelector("#run-tests-btn");
const testRunnerStatus = document.querySelector("#test-runner-status");
const testSummaryText = document.querySelector("#test-summary-text");
const testDurationBadge = document.querySelector("#test-duration-badge");
const testResultsList = document.querySelector("#test-results-list");
const probesContainer = document.querySelector("#probes-container");
const statServices = document.querySelector("#stat-services");
const statTests = document.querySelector("#stat-tests");

const API_BASE =
  window.location.protocol === "file:" || (window.location.port && window.location.port !== "5001")
    ? "http://127.0.0.1:5001"
    : "";

async function request(url, options = {}) {
  const fullUrl = url.startsWith("http") ? url : `${API_BASE}${url}`;
  let response;
  try {
    response = await fetch(fullUrl, options);
  } catch (err) {
    throw new Error("Unable to connect to TrackHub gateway. Ensure app.py is running on port 5001.");
  }
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}

async function loadSystemOverview() {
  try {
    const data = await request("/api/presentation/system-overview");
    if (statServices) {
      statServices.textContent = `${data.total_services} / ${data.total_services} Online`;
    }

    if (probesContainer && data.services) {
      probesContainer.replaceChildren();
      data.services.forEach((s) => {
        const card = document.createElement("div");
        card.className = "probe-card";

        const h3 = document.createElement("h3");
        h3.innerHTML = `<span>${s.service}</span> <span class="status-pill">${s.status}</span>`;

        const p1 = document.createElement("p");
        p1.textContent = `Endpoint: ${s.health_endpoint}`;

        const p2 = document.createElement("p");
        p2.style.marginTop = "4px";
        p2.textContent = s.db_file ? `DB: ${s.db_file} (${s.db_size_kb} KB)` : "Stateless gateway service";

        card.append(h3, p1, p2);
        probesContainer.appendChild(card);
      });
    }
  } catch (err) {
    if (probesContainer) {
      probesContainer.innerHTML = `<p style="color: #a33624; font-size: 0.85rem;">Error loading service probes: ${err.message}</p>`;
    }
  }
}

if (runTestsBtn) {
  runTestsBtn.addEventListener("click", async () => {
    runTestsBtn.disabled = true;
    runTestsBtn.textContent = "⏳ Executing Pytest Suite…";
    testRunnerStatus.style.display = "block";
    testSummaryText.textContent = "Running 24 automated unit & integration tests…";
    testDurationBadge.textContent = "In progress…";
    testResultsList.innerHTML = `<p style="color: var(--ink-soft); font-size: 0.82rem; margin: 8px;">Spawning pytest worker subprocess…</p>`;

    try {
      const result = await request("/api/presentation/run-tests", { method: "POST" });
      testSummaryText.textContent = `✅ ${result.passed} / ${result.total_tests} Tests Passed (${result.summary})`;
      testDurationBadge.textContent = `${result.duration_seconds}s execution`;

      if (statTests) {
        statTests.textContent = `${result.passed} Verified`;
      }

      testResultsList.replaceChildren();
      result.tests.forEach((t) => {
        const row = document.createElement("div");
        row.className = "test-row";

        const testName = document.createElement("span");
        testName.innerHTML = `<span style="color: var(--ink-soft);">[${t.module}]</span> ${t.test}`;

        const statusBadge = document.createElement("span");
        statusBadge.className = t.status === "PASSED" ? "badge-pass" : "badge badge-streak";
        statusBadge.textContent = t.status;

        row.append(testName, statusBadge);
        testResultsList.appendChild(row);
      });
    } catch (err) {
      testSummaryText.textContent = "❌ Test execution encountered an error";
      testDurationBadge.textContent = "Error";
      testResultsList.innerHTML = `<p style="color: #a33624; font-size: 0.82rem; margin: 8px;">${err.message}</p>`;
    } finally {
      runTestsBtn.disabled = false;
      runTestsBtn.textContent = "⚡ Run Automated Tests Again";
    }
  });
}

loadSystemOverview();
