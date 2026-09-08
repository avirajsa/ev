// EV Pitch Black Minimal Editorial Documentation Engine

document.addEventListener("DOMContentLoaded", () => {
    initCodeTabs();
    initFailoverSimulator();
    initScrollSpy();
});

function initCodeTabs() {
    const boxes = document.querySelectorAll(".code-tab-box");
    boxes.forEach(box => {
        const btns = box.querySelectorAll(".tab-btn");
        const panels = box.querySelectorAll(".code-panel");

        btns.forEach(btn => {
            btn.addEventListener("click", () => {
                const target = btn.getAttribute("data-target");

                btns.forEach(b => b.classList.remove("active"));
                panels.forEach(p => p.classList.remove("active"));

                btn.classList.add("active");
                const panel = box.querySelector(`#${target}`);
                if (panel) panel.classList.add("active");
            });
        });
    });
}

function initFailoverSimulator() {
    const btn429 = document.getElementById("btn-trigger-429");
    const btnReset = document.getElementById("btn-trigger-reset");
    const consoleBox = document.getElementById("sim-console");

    const steps = [
        { el: document.getElementById("m-claude"), name: "anthropic/claude-3.5-sonnet" },
        { el: document.getElementById("m-gpt"), name: "openai/gpt-4o" },
        { el: document.getElementById("m-gemini"), name: "google/gemini-2.0-flash" },
        { el: document.getElementById("m-llama"), name: "meta-llama/llama-3.3-70b" }
    ];

    let activeIdx = 0;

    function log(msg) {
        if (consoleBox) {
            consoleBox.textContent += "\n" + msg;
            consoleBox.scrollTop = consoleBox.scrollHeight;
        }
    }

    function updateState() {
        steps.forEach((step, idx) => {
            if (!step.el) return;
            step.el.classList.remove("active", "failed");
            if (idx < activeIdx) {
                step.el.classList.add("failed");
            } else if (idx === activeIdx) {
                step.el.classList.add("active");
            }
        });
    }

    if (btn429) {
        btn429.addEventListener("click", () => {
            if (activeIdx >= steps.length - 1) {
                log("[ROUTER] All fallback models in chain exhausted.");
                return;
            }
            const failedModel = steps[activeIdx].name;
            activeIdx++;
            const newModel = steps[activeIdx].name;

            log(`[ROUTER WARN] ${failedModel} returned HTTP 429 (Rate Limit).`);
            log(`[ROUTER FAILOVER] Switched traffic to: ${newModel}`);
            updateState();
        });
    }

    if (btnReset) {
        btnReset.addEventListener("click", () => {
            activeIdx = 0;
            updateState();
            if (consoleBox) {
                consoleBox.textContent = "[ROUTER] Primary model: anthropic/claude-3.5-sonnet. Ready.";
            }
        });
    }
}

function initScrollSpy() {
    const sections = document.querySelectorAll(".doc-section");
    const navLinks = document.querySelectorAll(".nav-menu .nav-link");

    window.addEventListener("scroll", () => {
        let current = "overview";
        sections.forEach(section => {
            const top = section.offsetTop - 100;
            if (window.scrollY >= top) {
                current = section.getAttribute("id");
            }
        });

        navLinks.forEach(link => {
            link.classList.remove("active");
            if (link.getAttribute("href") === `#${current}`) {
                link.classList.add("active");
            }
        });
    });
}
