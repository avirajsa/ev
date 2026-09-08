// EV System Editorial Documentation Interactive Logic

document.addEventListener("DOMContentLoaded", () => {
    initCodeTabs();
    initFailoverSimulator();
    initDocSearch();
    initScrollSpy();
});

/* Code Tabs Switching */
function initCodeTabs() {
    const containers = document.querySelectorAll(".code-tab-container");
    containers.forEach(container => {
        const tabs = container.querySelectorAll(".code-tab");
        const contents = container.querySelectorAll(".code-content");

        tabs.forEach(tab => {
            tab.addEventListener("click", () => {
                const targetId = tab.getAttribute("data-target");

                tabs.forEach(t => t.classList.remove("active"));
                contents.forEach(c => c.classList.remove("active"));

                tab.classList.add("active");
                const targetContent = container.querySelector(`#${targetId}`);
                if (targetContent) {
                    targetContent.classList.add("active");
                }
            });
        });
    });
}

/* OpenRouter LLM Dynamic Failover Interactive Simulator */
function initFailoverSimulator() {
    const btnRateLimit = document.getElementById("btn-sim-ratelimit");
    const btnQuota = document.getElementById("btn-sim-quota");
    const btnReset = document.getElementById("btn-sim-reset");
    const logOutput = document.getElementById("sim-log");

    const nodeClaude = document.getElementById("node-claude");
    const nodeGpt = document.getElementById("node-gpt");
    const nodeGemini = document.getElementById("node-gemini");
    const nodeLlama = document.getElementById("node-llama");

    const nodes = [nodeClaude, nodeGpt, nodeGemini, nodeLlama];
    const modelNames = [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o",
        "google/gemini-2.0-flash-001",
        "meta-llama/llama-3.3-70b"
    ];

    let currentActiveIndex = 0;

    function appendLog(text) {
        if (logOutput) {
            logOutput.textContent += "\n" + text;
            logOutput.scrollTop = logOutput.scrollHeight;
        }
    }

    function updateNodeStates() {
        nodes.forEach((node, idx) => {
            if (!node) return;
            node.classList.remove("active", "failed");
            const statusEl = node.querySelector(".node-status");

            if (idx < currentActiveIndex) {
                node.classList.add("failed");
                if (statusEl) statusEl.textContent = "Failed / Skipped";
            } else if (idx === currentActiveIndex) {
                node.classList.add("active");
                if (statusEl) statusEl.textContent = idx === 0 ? "Active / Primary" : "Active / Fallback";
            } else {
                if (statusEl) statusEl.textContent = "Standby";
            }
        });
    }

    if (btnRateLimit) {
        btnRateLimit.addEventListener("click", () => {
            if (currentActiveIndex >= nodes.length - 1) {
                appendLog(`[LLMRouter WARN] All models exhausted! Reset required.`);
                return;
            }
            const currentModel = modelNames[currentActiveIndex];
            currentActiveIndex++;
            const nextModel = modelNames[currentActiveIndex];

            appendLog(`[LLMRouter WARN] Model ${currentModel} returned HTTP 429 (Rate Limit Exceeded).`);
            appendLog(`[LLMRouter FAILOVER] Seamlessly switching traffic to next fallback model: ${nextModel}`);
            updateNodeStates();
        });
    }

    if (btnQuota) {
        btnQuota.addEventListener("click", () => {
            if (currentActiveIndex >= nodes.length - 1) {
                appendLog(`[LLMRouter WARN] All models exhausted! Reset required.`);
                return;
            }
            const currentModel = modelNames[currentActiveIndex];
            currentActiveIndex++;
            const nextModel = modelNames[currentActiveIndex];

            appendLog(`[LLMRouter WARN] Model ${currentModel} returned HTTP 402 (Insufficient Credits / Quota Exceeded).`);
            appendLog(`[LLMRouter FAILOVER] Rerouting request to fallback model: ${nextModel}`);
            updateNodeStates();
        });
    }

    if (btnReset) {
        btnReset.addEventListener("click", () => {
            currentActiveIndex = 0;
            updateNodeStates();
            if (logOutput) {
                logOutput.textContent = "[LLMRouter] Router reset. Primary model set to anthropic/claude-3.5-sonnet.";
            }
        });
    }
}

/* Documentation Search Filtering */
function initDocSearch() {
    const searchInput = document.getElementById("doc-search");
    if (!searchInput) return;

    searchInput.addEventListener("input", (e) => {
        const query = e.target.value.toLowerCase().trim();
        const navLinks = document.querySelectorAll(".nav-menu .nav-link");

        navLinks.forEach(link => {
            const text = link.textContent.toLowerCase();
            if (text.includes(query) || query === "") {
                link.style.display = "flex";
            } else {
                link.style.display = "none";
            }
        });
    });

    // Keyboard shortcut '/' to focus search
    document.addEventListener("keydown", (e) => {
        if (e.key === "/" && document.activeElement !== searchInput) {
            e.preventDefault();
            searchInput.focus();
        }
    });
}

/* ScrollSpy for Sidebar Links & Breadcrumb Update */
function initScrollSpy() {
    const sections = document.querySelectorAll(".doc-section");
    const navLinks = document.querySelectorAll(".nav-menu .nav-link");
    const crumbCurrent = document.getElementById("current-crumb");

    window.addEventListener("scroll", () => {
        let currentSectionId = "overview";
        let currentSectionName = "Overview";

        sections.forEach(section => {
            const sectionTop = section.offsetTop - 120;
            if (window.scrollY >= sectionTop) {
                currentSectionId = section.getAttribute("id");
                const heading = section.querySelector("h1, h2");
                if (heading) {
                    currentSectionName = heading.textContent.trim();
                }
            }
        });

        navLinks.forEach(link => {
            link.classList.remove("active");
            if (link.getAttribute("href") === `#${currentSectionId}`) {
                link.classList.add("active");
            }
        });

        if (crumbCurrent) {
            crumbCurrent.textContent = currentSectionName;
        }
    });
}
