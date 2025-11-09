from flask import Flask, render_template, request, jsonify

app = Flask(
    __name__,
    template_folder="templates",    # Tells Flask to look in /api/templates/
    static_folder="static"         # Tells Flask to look in /api/static/
)

# Sample phishing data
questions = [
    {
        "id": 1,
        "text": "An email claims to be from PayPal and asks you to 'log in to confirm your account' by clicking on a link. The email has grammatical errors. Is this phishing?",
        "options": ["Yes", "No"],
        "answer": "Yes",
    },
    # ... (your other questions here; unchanged)
]

@app.route("/")
def index():
    return render_template("quiz.html", questions=questions)

@app.route("/check", methods=["POST"])
def check():
    user_answers = request.json.get("answers", {})
    results = {}
    feedback = []
    for question in questions:
        qid = str(question["id"])
        correct = question["answer"]
        user_response = user_answers.get(qid, "")
        is_correct = (user_response == correct)
        results[qid] = is_correct
        feedback.append({
            "id": qid,
            "question": question["text"],
            "your_answer": user_response,
            "correct_answer": correct,
            "is_correct": is_correct,
            "explanation": "Correct!" if is_correct else f"The correct answer is '{correct}'."
        })
    return jsonify({"feedback": feedback, "score": sum(1 for v in results.values() if v), "total": len(questions)})

# DO NOT include an 'if __name__ == "__main__": app.run(debug=True)' block.
