document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("quiz-form");
    const submitBtn = document.getElementById("submit-btn");
    const resetBtn = document.getElementById("reset-btn");
    const hint = document.getElementById("form-hint");

    submitBtn.addEventListener("click", submitQuiz);
    resetBtn.addEventListener("click", resetQuiz);
    form.addEventListener("change", updateProgress);
    updateProgress();

    function totalQuestions() {
        return document.querySelectorAll(".question-card").length;
    }

    function collectAnswers() {
        const formData = new FormData(form);
        const answers = {};
        // FormData only contains checked radios; names are like "q1" -> strip "q"
        for (const [name, value] of formData.entries()) {
            if (name.startsWith("q")) {
                answers[name.slice(1)] = value;
            }
        }
        return answers;
    }

    function updateProgress() {
        const total = totalQuestions();
        const answered = Object.keys(collectAnswers()).length;
        const pct = total ? Math.round((answered / total) * 100) : 0;
        document.getElementById("progress-text").textContent = `${answered} of ${total} answered`;
        document.getElementById("progress-pct").textContent = `${pct}%`;
        document.getElementById("progress-fill").style.width = `${pct}%`;
        if (answered === total) {
            hint.textContent = "All scenarios answered — ready to check your score.";
        } else {
            hint.textContent = "";
        }
    }

    function resetQuiz() {
        form.reset();
        document.getElementById("results").innerHTML = "";
        updateProgress();
        hint.textContent = "Answers cleared. Good luck on the retake.";
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    function submitQuiz() {
        const answers = collectAnswers();
        const total = totalQuestions();
        const unanswered = total - Object.keys(answers).length;
        if (unanswered > 0) {
            const proceed = confirm(
                `You have ${unanswered} unanswered scenario(s). Submit anyway? (Unanswered counts as incorrect.)`
            );
            if (!proceed) return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = "Checking…";
        hint.textContent = "";

        fetch("/check", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ answers: answers })
        })
            .then((response) => {
                if (!response.ok) throw new Error(`Server returned ${response.status}`);
                return response.json();
            })
            .then((data) => renderResults(data))
            .catch((err) => {
                const resultsDiv = document.getElementById("results");
                resultsDiv.innerHTML = `<div class="feedback-item incorrect"><p><strong>Error:</strong> ${escapeHtml(err.message)}. Is the server running?</p></div>`;
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = "Check my score";
            });
    }

    function grade(score, total) {
        const pct = total ? score / total : 0;
        if (pct >= 0.86) return { cls: "grade-great", label: "Excellent — sharp eye", tip: "You judge instead of guessing. Keep verifying senders out-of-band and navigating to sites yourself." };
        if (pct >= 0.64) return { cls: "grade-ok", label: "Getting there — stay skeptical", tip: "Review the red flags below. Slow down on urgency + authority combos (CEO wires, gift cards, expiring passwords)." };
        return { cls: "grade-risk", label: "At risk — review carefully", tip: "Attackers rely on rushing you. Re-read each explanation, then retake the quiz — assume unexpected links, QR codes, attachments and MFA prompts are hostile until proven otherwise." };
    }

    function renderResults(data) {
        const resultsDiv = document.getElementById("results");
        resultsDiv.innerHTML = "";

        const g = grade(data.score, data.total);
        const scoreCard = document.createElement("div");
        scoreCard.className = "score-card";
        scoreCard.innerHTML =
            `<div class="score-grade ${g.cls}">${escapeHtml(g.label)}</div>` +
            `<div class="score-num">Score: ${data.score} / ${data.total}</div>` +
            `<p class="score-tip">${escapeHtml(g.tip)}</p>`;
        resultsDiv.appendChild(scoreCard);

        const list = document.createElement("div");
        data.feedback.forEach((item) => {
            const container = document.createElement("div");
            container.className = "feedback-item " + (item.is_correct ? "correct" : "incorrect");

            const flags = (item.red_flags || []).map((f) => `<li>${escapeHtml(f)}</li>`).join("");
            container.innerHTML =
                `<div class="fb-head"><span class="fb-verdict">${item.is_correct ? "✓ Correct" : "✗ Incorrect"}</span>` +
                `<span class="fb-cat">Scenario ${escapeHtml(String(item.id))} · ${escapeHtml(item.category || "")}</span></div>` +
                `<p class="fb-q"><strong>Scenario:</strong> ${escapeHtml(item.question)}</p>` +
                `<p class="fb-answers"><strong>Your answer:</strong> ${escapeHtml(item.your_answer || "No answer")} &nbsp;|&nbsp; <strong>Correct:</strong> ${escapeHtml(item.correct_answer)}</p>` +
                `<p class="fb-explain">${escapeHtml(item.explanation || "")}</p>` +
                (flags ? `<ul class="fb-flags">${flags}</ul>` : "") +
                (item.action ? `<div class="fb-action"><strong>Safe habit:</strong> ${escapeHtml(item.action)}</div>` : "");
            list.appendChild(container);
        });
        resultsDiv.appendChild(list);

        const retry = document.createElement("div");
        retry.className = "actions";
        retry.innerHTML = `<button type="button" id="retry-btn">Retake quiz</button>`;
        resultsDiv.appendChild(retry);
        document.getElementById("retry-btn").addEventListener("click", () => {
            resultsDiv.scrollIntoView({ behavior: "smooth", block: "start" });
            window.scrollTo({ top: 0, behavior: "smooth" });
        });

        resultsDiv.scrollIntoView({ behavior: "smooth" });
    }

    function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, (c) => ({
            "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
        })[c]);
    }
});
