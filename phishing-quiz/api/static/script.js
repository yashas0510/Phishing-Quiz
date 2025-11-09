document.addEventListener("DOMContentLoaded", function () {
    const submitBtn = document.getElementById("submit-btn");
    submitBtn.addEventListener("click", submitQuiz);
});

function submitQuiz() {
    const form = document.getElementById("quiz-form");
    const formData = new FormData(form);
    const answers = {};

    // FormData only contains checked radio inputs, names are like "q1", so strip the leading 'q'
    for (const [name, value] of formData.entries()) {
        if (name.startsWith("q")) {
            const qid = name.slice(1); // "q1" -> "1"
            answers[qid] = value;
        }
    }

    fetch("/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers: answers })
    })
    .then(response => {
        if (!response.ok) throw new Error("Network response was not OK");
        return response.json();
    })
    .then(data => {
        renderResults(data);
    })
    .catch(err => {
        const resultsDiv = document.getElementById("results");
        resultsDiv.innerHTML = `<p style="color: red;">Error: ${err.message}</p>`;
    });
}

function renderResults(data) {
    const resultsDiv = document.getElementById("results");
    resultsDiv.innerHTML = ""; // clear

    const scoreP = document.createElement("p");
    scoreP.innerHTML = `Score: ${data.score} / ${data.total}`;
    scoreP.style.fontSize = "1.1rem";
    scoreP.style.marginBottom = "1rem";
    resultsDiv.appendChild(scoreP);

    const list = document.createElement("div");

    data.feedback.forEach(item => {
        const container = document.createElement("div");
        container.className = "feedback-item";
        container.style.border = "1px solid #e0e0e0";
        container.style.padding = "10px";
        container.style.margin = "8px auto";
        container.style.borderRadius = "6px";
        container.style.textAlign = "left";
        container.style.maxWidth = "800px";

        const qElem = document.createElement("p");
        qElem.innerHTML = `<strong>Q:</strong> ${item.question}`;
        container.appendChild(qElem);

        const yourAns = document.createElement("p");
        yourAns.innerHTML = `<strong>Your answer:</strong> ${item.your_answer || "<em>No answer</em>"}`;
        container.appendChild(yourAns);

        const correctAns = document.createElement("p");
        correctAns.innerHTML = `<strong>Correct answer:</strong> ${item.correct_answer}`;
        container.appendChild(correctAns);

        const explanation = document.createElement("p");
        explanation.innerHTML = `<strong>${item.is_correct ? "Correct ✓" : "Incorrect ✗"}</strong> — ${item.explanation}`;
        explanation.style.color = item.is_correct ? "green" : "red";
        container.appendChild(explanation);

        list.appendChild(container);
    });

    resultsDiv.appendChild(list);
    // scroll to results for convenience
    resultsDiv.scrollIntoView({ behavior: "smooth" });
}
