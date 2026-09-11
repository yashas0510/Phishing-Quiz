from flask import Flask, render_template, request, jsonify

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)

# ---------------------------------------------------------------------------
# Question bank: modern, scenario-based, requires careful judgment.
# Mix of phishing (11) and legitimate (3) so "always say phishing" fails.
# Each question carries a detailed explanation, red flags, and safe action.
# ---------------------------------------------------------------------------
questions = [
    {
        "id": 1,
        "category": "QR phishing (quishing)",
        "difficulty": 2,
        "sender": "facilities@company-mail-support.com",
        "subject": "Action needed: claim your staff parking refund",
        "body": (
            "Hi team,\n\nFinance has approved Q3 parking refunds. Scan the QR code "
            "in the attached flyer (or tap the image on mobile) to verify your "
            "employee ID and bank details for the refund transfer.\n\n"
            "This offer expires in 24 hours. The QR code is the only way to claim — "
            "do not contact Finance directly as the team is offsite."
        ),
        "prompt": "You did not expect any parking refund. The flyer QR code points to a login page asking for your company password and bank OTP. Is this message phishing or legitimate?",
        "options": ["Phishing", "Legitimate"],
        "answer": "Phishing",
        "explanation": (
            "This is quishing — phishing via QR code. QR codes hide the destination URL, "
            "so victims cannot hover-to-inspect the link. A refund you never expected, a "
            "24-hour deadline, a request for password + bank OTP, and 'do not contact "
            "Finance' (which blocks verification) are all classic lures."
        ),
        "red_flags": [
            "Unexpected refund you never applied for",
            "QR code hides the real URL — cannot be inspected at a glance",
            "Asks for company password + bank OTP together",
            "Artificial 24-hour urgency",
            "'Do not contact Finance' blocks out-of-band verification",
            "Sender domain company-mail-support.com is not the real company domain",
        ],
        "action": "Do not scan. Verify via a known channel (Finance intranet page or phone number from the directory), then report the email as phishing.",
    },
    {
        "id": 2,
        "category": "MFA fatigue",
        "difficulty": 3,
        "sender": "System push notification (Microsoft Authenticator)",
        "subject": "MFA approval requests — 14 requests at 3:12 AM",
        "body": (
            "You receive 14 MFA push approvals in 10 minutes at 3 AM while asleep. "
            "Then an SMS arrives: 'Hi, this is IT Support. We're fixing an auth outage — "
            "please approve the next prompt so we can close your ticket. Ticket #IT-8841.' "
            "You never opened any ticket."
        ),
        "prompt": "The SMS pressures you to approve one prompt. Is approving the MFA request the safe, legitimate thing to do?",
        "options": ["Phishing", "Legitimate"],
        "answer": "Phishing",
        "explanation": (
            "This is an MFA-fatigue (push-bombing) attack: the attacker already has your "
            "password and spams MFA prompts hoping you approve one out of annoyance or "
            "confusion. The follow-up 'IT Support' SMS is part of the attack — real IT "
            "never asks you to approve an MFA prompt you did not initiate."
        ),
        "red_flags": [
            "Burst of MFA prompts you did not trigger, at an odd hour",
            "Unsolicited SMS claiming to be IT Support",
            "References a ticket you never opened",
            "Pressure to approve — urgency + authority combo",
        ],
        "action": "Approve NOTHING. Open the authenticator app and deny/report the requests, change your password from a known-good device, and call IT on the published number.",
    },
    {
        "id": 3,
        "category": "OAuth consent scam",
        "difficulty": 3,
        "sender": "Productivity Suite (via Microsoft 365 consent screen)",
        "subject": "Acme Analytics wants to access your account",
        "body": (
            "A calendar-invite add-in asks you to click 'Accept' on a REAL Microsoft "
            "consent screen. The app 'Acme Analytics' requests: read all emails and files, "
            "send mail as you, read contacts, and 'maintain access even if you change your "
            "password'. The publisher is unverified."
        ),
        "prompt": "The consent screen is genuinely from Microsoft, so accepting must be safe. Phishing or legitimate?",
        "options": ["Phishing", "Legitimate"],
        "answer": "Phishing",
        "explanation": (
            "Tricky but malicious: the consent screen is real, the APP is not. OAuth-consent "
            "phishing abuses legitimate consent flows to get persistent access (including "
            "'maintain access after password change') without ever stealing your password. "
            "A calendar widget has no need to read all email or send mail as you."
        ),
        "red_flags": [
            "Wildly excessive permissions for a simple add-in",
            "'Maintain access even if you change your password' = persistence",
            "Unverified publisher",
            "Consent arrives out of context (via invite, not the official store)",
        ],
        "action": "Decline. Install add-ins only from the official store with minimal scopes, and review/revoke consented apps at account.microsoft.com > Privacy > Apps.",
    },
    {
        "id": 4,
        "category": "Fake tech support",
        "difficulty": 1,
        "sender": "Phone call + follow-up email from 'Microsoft Refund Dept'",
        "subject": "You are owed a $499 refund — confirm remote access",
        "body": (
            "'Hello, I am calling from Microsoft Refund Department about your expired "
            "antivirus subscription. We will refund $499. Please install AnyDesk so I can "
            "connect, then log in to your bank to 'verify' the refund. Do not tell anyone — "
            "this is a confidential finance process.'"
        ),
        "prompt": "They knew your name and old order number. Is this phishing or legitimate?",
        "options": ["Phishing", "Legitimate"],
        "answer": "Phishing",
        "explanation": (
            "Classic refund scam. Microsoft never calls about refunds or asks for remote "
            "access to your bank. Scammers buy leaked personal details (name, old orders) "
            "to sound credible, then use remote-access tools to drain accounts or plant malware. "
            "The 'keep it secret' instruction is there to stop you getting advice."
        ),
        "red_flags": [
            "Unsolicited call about money you were not expecting",
            "Asks to install remote-access software (AnyDesk)",
            "Asks you to log in to your bank while they watch",
            "'Do not tell anyone' secrecy pressure",
            "Microsoft does not do refund calls like this",
        ],
        "action": "Hang up, do not install anything. If you already did, disconnect from the internet, uninstall the tool, and call your bank + real support from official numbers.",
    },
    {
        "id": 5,
        "category": "AI-generated spear phishing",
        "difficulty": 3,
        "sender": "sarah.chen@yourcompany.com (display name matches your manager)",
        "subject": "Quick favor while I'm in back-to-back interviews",
        "body": (
            "Hi! I'm stuck in interviews all day (saw on LinkedIn I'm hiring — true). "
            "Could you grab 4x $100 gift cards for new-hire welcome kits and send me the "
            "codes? Finance will reimburse today. Flawless grammar, correct signature, "
            "references your current project by name. Reply-To header (hidden) points to "
            "sarah.chen.hr.help@gmail.com."
        ),
        "prompt": "Everything looks perfect — tone, signature, project name. Is this phishing or legitimate?",
        "options": ["Phishing", "Legitimate"],
        "answer": "Phishing",
        "explanation": (
            "AI makes phishing flawless now — grammar mistakes are no longer the tell. The "
            "real signals are behavioral: a gift-card request, secrecy/urgency, and the "
            "hidden Reply-To to a Gmail address. Attackers scrape LinkedIn and project names "
            "to personalize lures. Always verify the SENDER ADDRESS, not the display name."
        ),
        "red_flags": [
            "Gift cards / codes as payment — almost always fraud",
            "Display name matches your manager but actual address is Gmail",
            "Hidden Reply-To mismatch",
            "Urgency + 'in meetings, can't talk' blocks voice verification",
            "Personalization (project name) is now cheap with AI + LinkedIn scraping",
        ],
        "action": "Do not reply or buy anything. Message your manager through a known channel (Teams/Slack or known number) to verify. Report the email.",
    },
    {
        "id": 6,
        "category": "Business email compromise (BEC)",
        "difficulty": 2,
        "sender": "CEO (display name) <ceo-office-urgent@company-finance-portal.com>",
        "subject": "Confidential acquisition — wire needed before 2 PM",
        "body": (
            "I'm in a board meeting, phone off. We are closing an acquisition today and need "
            "a $48,000 wire to the attached new vendor account before 2 PM. Keep this strictly "
            "between us until the announcement. Our finance head is CC'd (another external "
            "address). Reply only to this email."
        ),
        "prompt": "The tone sounds exactly like your CEO under pressure. Phishing or legitimate?",
        "options": ["Phishing", "Legitimate"],
        "answer": "Phishing",
        "explanation": (
            "Textbook BEC: authority (CEO) + urgency (before 2 PM) + secrecy (keep it between "
            "us) + a payment-method change to a 'new account'. Note there is no malware or link "
            "to scan — the fraud is pure social engineering. Real executives never order secret "
            "wires by email alone."
        ),
        "red_flags": [
            "Secret payment bypassing normal approval process",
            "New vendor account details via email",
            "External sender domain impersonating the CEO",
            "CC'd 'finance head' is also an external address",
            "'Reply only to this email' prevents verification",
        ],
        "action": "Stop and verify out-of-band: call the CEO/finance on known numbers and follow the vendor-change verification process. Do not reply to the suspect email.",
    },
    {
        "id": 7,
        "category": "Malicious attachment",
        "difficulty": 2,
        "sender": "billing@trusted-supplier-invoices.net",
        "subject": "Overdue invoice INV-2291 — payment required within 48h",
        "body": (
            "Attached: Invoice_Payment_Oct.docm. Your payment of $7,240 is 30 days overdue. "
            "Late fees apply after 48 hours. To view the invoice, open the attachment and click "
            "'Enable Content / Enable Macros'. The document shows a blurred preview saying "
            "'This document is protected. Enable editing to view.'"
        ),
        "prompt": "It looks like a real supplier invoice and you do buy from suppliers. Phishing or legitimate?",
        "options": ["Phishing", "Legitimate"],
        "answer": "Phishing",
        "explanation": (
            "'Enable Macros / Enable Content' on an unexpected Office attachment is one of the "
            "most dangerous clicks in phishing — it runs malware (often .docm macro malware). "
            "Real invoices come as PDFs or viewable documents, never blurred files demanding "
            "macro execution. Urgency (48h, late fees) pushes you to click before verifying."
        ),
        "red_flags": [
            ".docm attachment (macro-capable) instead of PDF",
            "Blurred preview demanding 'Enable Content' — hallmark of macro malware",
            "Unexpected overdue claim + fee threat creates urgency",
            "Sender domain trusted-supplier-invoices.net may not be your real supplier",
        ],
        "action": "Do not enable macros. Verify the invoice in your procurement system or by calling the supplier on a known number. Scan/upload suspicious files in a sandbox, never on your work machine.",
    },
    {
        "id": 8,
        "category": "Shortened URL",
        "difficulty": 1,
        "sender": "SMS from +1 (555) 01X-XXXX: 'POST-Express'",
        "subject": "Your parcel could not be delivered",
        "body": (
            "'POST-Express: Your parcel #PX8812 could not be delivered. Pay $1.95 redelivery "
            "fee within 12h or it will be returned: http://bit.ly/3xP-delivery-PX8812'. You "
            "are vaguely expecting a package but never used POST-Express."
        ),
        "prompt": "It's only $1.95 and bit.ly links are used by real companies too. Phishing or legitimate?",
        "options": ["Phishing", "Legitimate"],
        "answer": "Phishing",
        "explanation": (
            "Parcel-fee smishing. URL shorteners hide the true domain — bit.ly links are cheap "
            "camouflage for credential-harvesting pages that ask for card details over a tiny "
            "fee. Real carriers track via their own domain/app and never threaten return over "
            "a $1.95 link in an unsolicited SMS."
        ),
        "red_flags": [
            "Unsolicited SMS from an unknown number",
            "Shortened URL hides the real destination",
            "Tiny fee = card-harvesting pretext, not real postage",
            "12-hour threat + return scare",
            "Carrier you never used",
        ],
        "action": "Do not tap. Track the parcel only in the retailer's official app/site, or paste the short link into an expander/preview on a safe device if you must inspect it.",
    },
    {
        "id": 9,
        "category": "Typosquatting",
        "difficulty": 2,
        "sender": "IT Security <no-reply@micorsoft-secure-auth.com>",
        "subject": "Your password expires in 24 hours",
        "body": (
            "Dear user, your mailbox password expires in 24 hours. Renew now to avoid losing "
            "access: https://micorsoft-secure-auth.com/renew?user=you. The page looks identical "
            "to the real login, with full company branding."
        ),
        "prompt": "The login page looks pixel-perfect with your company branding. Phishing or legitimate?",
        "options": ["Phishing", "Legitimate"],
        "answer": "Phishing",
        "explanation": (
            "Look closely: 'micorsoft' (missing an 'r') is typosquatting — a lookalike domain. "
            "Cloned login pages with perfect branding cost attackers minutes to build with "
            "phishing kits. Real password-expiry notices never come from a misspelled external "
            "domain with a countdown link."
        ),
        "red_flags": [
            "Domain micorsoft-secure-auth.com is misspelled (micorsoft ≠ microsoft)",
            "External domain for an 'IT Security' notice",
            "Generic 'Dear user' greeting",
            "Countdown pressure + link to 'renew' (passwords renew in settings, not via email links)",
        ],
        "action": "Do not click or enter credentials. Type the portal address manually or use your password manager (it will refuse to autofill on the fake domain — a great detector).",
    },
    {
        "id": 10,
        "category": "Smishing (bank impersonation)",
        "difficulty": 1,
        "sender": "SMS from 'BANK-Alert' (alphanumeric sender ID)",
        "subject": "Suspicious transaction blocked",
        "body": (
            "'BANK-Alert: A $2,499 transaction was blocked on your card ending 4412. If this "
            "was NOT you, verify immediately: https://secure-bank-verification-support.com/login. "
            "Failure to verify within 2 hours will suspend your account.'"
        ),
        "prompt": "It mentions your card's last digits and threatens suspension. Phishing or legitimate?",
        "options": ["Phishing", "Legitimate"],
        "answer": "Phishing",
        "explanation": (
            "Banks never send login links by SMS or threaten suspension for not clicking. "
            "Sender IDs like 'BANK-Alert' are trivially spoofed, and partial card digits often "
            "come from past breaches. The link domain (secure-bank-verification-support.com) is "
            "not the bank's real domain."
        ),
        "red_flags": [
            "Login link delivered by SMS — banks don't do this",
            "Threat of suspension within 2 hours",
            "Spoofable alphanumeric sender ID proves nothing",
            "Link domain is not the bank's official domain",
        ],
        "action": "Do not tap the link. Open the bank's official app (or call the number on your card) and check for alerts there.",
    },
    {
        "id": 11,
        "category": "DocuSign / file-share lure",
        "difficulty": 3,
        "sender": "DocuSign <dse_notification@docusign-mgr-securefiles.com>",
        "subject": "Please review and sign: Updated payroll details",
        "body": (
            "You received an unexpected DocuSign envelope 'Updated payroll details' from an "
            "unknown sender. The 'Review Document' button links to a page that first asks for "
            "your email password 'to verify your identity before showing the document'."
        ),
        "prompt": "The email formatting looks exactly like real DocuSign. Phishing or legitimate?",
        "options": ["Phishing", "Legitimate"],
        "answer": "Phishing",
        "explanation": (
            "Real DocuSign envelopes never ask for your EMAIL password to view a document — "
            "that credential request is the theft. Attackers abuse trusted brands (DocuSign, "
            "SharePoint, Dropbox) because victims trust the logo. An unexpected payroll "
            "document from an unknown sender plus an off-domain link seals it."
        ),
        "red_flags": [
            "Unexpected payroll/HR document from unknown sender",
            "Asks for email password before showing content — never legitimate",
            "Sender domain docusign-mgr-securefiles.com is not docusign.net",
            "Abuses a trusted brand to borrow credibility",
        ],
        "action": "Do not enter credentials. Confirm with HR/payroll through a known channel, and preview envelopes only by logging in to docusign.net directly.",
    },
    {
        "id": 12,
        "category": "Legitimate password reset (control)",
        "difficulty": 3,
        "sender": "Google <no-reply@accounts.google.com> (SPF/DKIM pass, correct domain)",
        "subject": "Password reset request",
        "body": (
            "You requested a password reset 5 minutes ago from a known device. The email "
            "contains no threats or attachments — just 'Reset your password' linking to "
            "https://accounts.google.com/signin/recovery (the domain you typed yourself to "
            "check), expiring in 1 hour. No personal details are requested in the email."
        ),
        "prompt": "It links to a login page and asks you to set a new password. Phishing or legitimate?",
        "options": ["Phishing", "Legitimate"],
        "answer": "Legitimate",
        "explanation": (
            "This one is REAL — included so you judge instead of auto-answering 'phishing'. "
            "You initiated it minutes ago, the sender domain is exactly accounts.google.com "
            "with passing authentication, the link matches the official domain you verified "
            "by typing, and there is no urgency theater or credential request inside the email."
        ),
        "red_flags": [],
        "action": "Still best practice: ignore the link and navigate to the site yourself (or use your password manager), then complete the reset. That habit protects you even when an email is genuine.",
    },
    {
        "id": 13,
        "category": "Legitimate IT notice (control)",
        "difficulty": 2,
        "sender": "IT Department (internal address, announced last week in town hall)",
        "subject": "VPN migration window this Saturday — no action via email",
        "body": (
            "Reminder of the VPN migration announced in last week's town hall and on the "
            "intranet. The email contains NO links, NO attachments, and asks for NO "
            "credentials — it says: 'On Saturday the VPN will be down 2–4 AM. Instructions are "
            "on the intranet (open it yourself, do not reply to this email).'"
        ),
        "prompt": "An IT email about a service change. Phishing or legitimate?",
        "options": ["Phishing", "Legitimate"],
        "answer": "Legitimate",
        "explanation": (
            "Legitimate. It corroborates a pre-announced change (town hall + intranet), and — "
            "critically — demands NOTHING clickable: no links, no attachments, no credentials, "
            "explicitly telling you to navigate yourself. That is exactly how trustworthy "
            "operational notices are written."
        ),
        "red_flags": [],
        "action": "Follow the intranet instructions by navigating there yourself. Keep this pattern as your baseline: real IT notices minimize clickable actions.",
    },
    {
        "id": 14,
        "category": "Legitimate recruiter outreach (control)",
        "difficulty": 3,
        "sender": "LinkedIn InMail from a verified employee of a real company",
        "subject": "Role that matches your profile",
        "body": (
            "A recruiter with a multi-year LinkedIn history, mutual connections, and a company "
            "email domain matching the real firm's site writes: a short role pitch, salary band, "
            "and an invite to book via the company's official careers page (link matches the "
            "firm's domain). No attachments, no request for bank details, ID scans, fees, or "
            "'download this offer file'."
        ),
        "prompt": "Out-of-the-blue job offer with a link. Phishing or legitimate?",
        "options": ["Phishing", "Legitimate"],
        "answer": "Legitimate",
        "explanation": (
            "Legitimate outreach. The differentiators from job scams: verifiable identity "
            "(history + mutuals + matching corporate domain), process runs on the official "
            "careers site, and zero premature sensitive requests. Job SCAMS instead demand "
            "fees, ID scans, or .exe/.docm 'offer files' and often pay above market with no interview."
        ),
        "red_flags": [],
        "action": "Still verify: open the careers page manually, confirm the recruiter's profile + email domain, and never send ID/bank details or pay fees before a signed offer and verified onboarding.",
    },
]


@app.route("/")
def index():
    return render_template("quiz.html", questions=questions)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "questions": len(questions)})


@app.route("/check", methods=["POST"])
def check():
    data = request.get_json(silent=True) or {}
    user_answers = data.get("answers", {})
    if not isinstance(user_answers, dict):
        user_answers = {}

    results = {}
    feedback = []
    for question in questions:
        qid = str(question["id"])
        correct = question["answer"]
        user_response = str(user_answers.get(qid, "") or "")
        is_correct = user_response == correct
        results[qid] = is_correct
        feedback.append(
            {
                "id": qid,
                "category": question["category"],
                "difficulty": question["difficulty"],
                "question": question["prompt"],
                "your_answer": user_response,
                "correct_answer": correct,
                "is_correct": is_correct,
                "explanation": question["explanation"],
                "red_flags": question.get("red_flags", []),
                "action": question.get("action", ""),
            }
        )
    score = sum(1 for v in results.values() if v)
    return jsonify({"feedback": feedback, "score": score, "total": len(questions)})
