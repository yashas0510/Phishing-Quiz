/* Phishing Awareness Quiz — form progress, submission, and results.
   No innerHTML, no eval, no inline handlers: all DOM is built with
   createElement/textContent so server data can never execute as markup. */
(function () {
    'use strict';

    function el(tag, cls, text) {
        const node = document.createElement(tag);
        if (cls) node.className = cls;
        if (text !== undefined && text !== null) node.textContent = text;
        return node;
    }

    function asText(value) {
        if (typeof value !== 'string') return '';
        return value;
    }

    function init() {
        const form = document.getElementById('quiz-form');
        const submitBtn = document.getElementById('submit-btn');
        const resetBtn = document.getElementById('reset-btn');
        const hint = document.getElementById('form-hint');
        if (!form || !submitBtn || !resetBtn || !hint) return;

        submitBtn.addEventListener('click', submitQuiz);
        resetBtn.addEventListener('click', resetQuiz);
        form.addEventListener('change', updateProgress);
        updateProgress();
    }

    function totalQuestions() {
        return document.querySelectorAll('.question-card').length;
    }

    function collectAnswers() {
        const form = document.getElementById('quiz-form');
        const answers = {};
        const checked = form.querySelectorAll('input[type="radio"]:checked');
        for (const input of checked) {
            if (input.name.charAt(0) !== 'q') continue;
            const qid = input.name.slice(1);
            if (!/^\d+$/.test(qid)) continue;
            answers[qid] = input.value;
        }
        return answers;
    }

    function updateProgress() {
        const total = totalQuestions();
        const answered = Object.keys(collectAnswers()).length;
        const pct = total ? Math.round((answered / total) * 100) : 0;
        document.getElementById('progress-text').textContent =
            answered + ' of ' + total + ' answered';
        document.getElementById('progress-pct').textContent = pct + '%';
        document.getElementById('progress-fill').style.width = pct + '%';
        document.getElementById('form-hint').textContent =
            answered === total ? 'All scenarios answered. Ready to check your score.' : '';
    }

    function resetQuiz() {
        document.getElementById('quiz-form').reset();
        const results = document.getElementById('results');
        while (results.firstChild) results.removeChild(results.firstChild);
        updateProgress();
        document.getElementById('form-hint').textContent = 'Answers cleared.';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function submitQuiz() {
        const submitBtn = document.getElementById('submit-btn');
        const hint = document.getElementById('form-hint');
        const answers = collectAnswers();
        const total = totalQuestions();
        const unanswered = total - Object.keys(answers).length;
        if (unanswered > 0) {
            const proceed = window.confirm(
                'You have ' + unanswered + ' unanswered scenario(s). ' +
                'Submit anyway? Unanswered scenarios count as incorrect.'
            );
            if (!proceed) return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = 'Checking…';
        hint.textContent = '';

        window.fetch('/check', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ answers: answers })
        }).then(function (response) {
            if (!response.ok) {
                throw new Error('Server returned status ' + response.status);
            }
            return response.json();
        }).then(function (data) {
            renderResults(data);
        }).catch(function (err) {
            const results = document.getElementById('results');
            while (results.firstChild) results.removeChild(results.firstChild);
            const box = el('div', 'feedback-item incorrect');
            const p = el('p', null, 'Could not check your answers (' + err.message + '). Please try again.');
            box.appendChild(p);
            results.appendChild(box);
        }).then(function () {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Check my score';
        });
    }

    function gradeFor(score, total) {
        const pct = total ? score / total : 0;
        if (pct >= 0.86) {
            return {
                cls: 'grade-great',
                label: 'Excellent result',
                tip: 'You judged each scenario on its evidence. Keep verifying senders through a separate channel and navigating to sites yourself.'
            };
        }
        if (pct >= 0.64) {
            return {
                cls: 'grade-ok',
                label: 'Developing judgment',
                tip: 'Review the red flags below. Slow down whenever urgency and authority appear together, such as payment orders or account warnings.'
            };
        }
        return {
            cls: 'grade-risk',
            label: 'Needs improvement',
            tip: 'Attackers rely on rushing you. Re-read each explanation, then retake the quiz. Treat unexpected links, codes, attachments, and sign-in prompts as hostile until verified.'
        };
    }

    function renderResults(data) {
        const results = document.getElementById('results');
        while (results.firstChild) results.removeChild(results.firstChild);

        const score = typeof data.score === 'number' ? data.score : 0;
        const total = typeof data.total === 'number' ? data.total : 0;
        const items = Array.isArray(data.feedback) ? data.feedback : [];

        const g = gradeFor(score, total);
        const scoreCard = el('div', 'score-card');
        scoreCard.appendChild(el('div', 'score-grade ' + g.cls, g.label));
        scoreCard.appendChild(el('div', 'score-num', 'Score: ' + score + ' / ' + total));
        scoreCard.appendChild(el('p', 'score-tip', g.tip));
        results.appendChild(scoreCard);

        for (const item of items) {
            results.appendChild(feedbackCard(item));
        }

        const actions = el('div', 'actions');
        const retry = el('button', null, 'Retake quiz');
        retry.setAttribute('type', 'button');
        retry.addEventListener('click', function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
        actions.appendChild(retry);
        results.appendChild(actions);

        results.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function feedbackCard(item) {
        const correct = item.is_correct === true;
        const box = el('div', 'feedback-item ' + (correct ? 'correct' : 'incorrect'));

        const head = el('div', 'fb-head');
        head.appendChild(el('span', 'fb-verdict', correct ? 'Correct' : 'Incorrect'));
        const meta = 'Scenario ' + asText(String(item.id)) +
            (item.category ? ' · ' + asText(item.category) : '');
        head.appendChild(el('span', 'fb-cat', meta));
        box.appendChild(head);

        box.appendChild(labeledLine('Scenario: ', asText(item.question), 'fb-q'));

        const your = asText(item.your_answer) || 'No answer';
        box.appendChild(labeledLine('Your answer: ', your + '  |  Correct: ' + asText(item.correct_answer), 'fb-answers'));

        if (item.explanation) {
            box.appendChild(el('p', 'fb-explain', asText(item.explanation)));
        }

        const flags = Array.isArray(item.red_flags) ? item.red_flags : [];
        if (flags.length > 0) {
            box.appendChild(el('p', 'fb-flags-label', 'Warning signs:'));
            const list = el('ul', 'fb-flags');
            for (const flag of flags) {
                list.appendChild(el('li', null, asText(flag)));
            }
            box.appendChild(list);
        }

        if (item.action) {
            const action = el('div', 'fb-action');
            action.appendChild(el('span', 'fb-action-title', 'Recommended action: '));
            action.appendChild(document.createTextNode(asText(item.action)));
            box.appendChild(action);
        }

        return box;
    }

    function labeledLine(label, value, cls) {
        const p = el('p', cls);
        const strong = el('strong', null, label);
        p.appendChild(strong);
        p.appendChild(document.createTextNode(value));
        return p;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
