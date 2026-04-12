"""
Synthetic email dataset — 35 realistic emails across all categories.
Used as the environment's email corpus.
"""

from .models import EmailCategory, EmailItem, Sentiment

EMAIL_CORPUS: list[EmailItem] = [
    # ─── COMPLAINTS ──────────────────────────────────────────────────────────
    EmailItem(
        id="email_001",
        subject="My order is completely wrong!",
        body=(
            "I placed order #78432 three days ago and received the completely wrong items. "
            "I ordered a blue jacket in size L but received a green dress in size S. "
            "This is absolutely unacceptable. I need this resolved immediately. "
            "Please send the correct items or issue a full refund."
        ),
        sender="sarah.miller@gmail.com",
        sender_name="Sarah Miller",
        category=EmailCategory.complaint,
        urgency_score=0.7,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T08:12:00Z",
    ),
    EmailItem(
        id="email_002",
        subject="Terrible customer service experience",
        body=(
            "I called your support line yesterday and was on hold for 2 hours before being "
            "disconnected. Nobody called me back. This is the third time I have experienced "
            "this issue. I am extremely frustrated and considering cancelling my subscription. "
            "I demand an explanation and compensation for my wasted time."
        ),
        sender="james.h.walker@outlook.com",
        sender_name="James Walker",
        category=EmailCategory.complaint,
        urgency_score=0.65,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T09:05:00Z",
    ),
    EmailItem(
        id="email_003",
        subject="Defective product received",
        body=(
            "The laptop stand I purchased from your store arrived with a broken hinge. "
            "I paid $89 for what appears to be a factory defect. I have taken photos. "
            "Please advise on how to proceed with a replacement or refund. "
            "Order number: ORD-99812."
        ),
        sender="priya.sharma@techmail.com",
        sender_name="Priya Sharma",
        category=EmailCategory.complaint,
        urgency_score=0.5,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T10:30:00Z",
    ),
    EmailItem(
        id="email_004",
        subject="Wrong charges on my bill",
        body=(
            "I noticed that I was charged twice for my monthly subscription in March. "
            "My bank statement shows two charges of $49.99 on March 3rd and March 5th. "
            "I only authorized one payment. Please investigate and refund the duplicate charge."
        ),
        sender="carlos.ruiz@fastnet.io",
        sender_name="Carlos Ruiz",
        category=EmailCategory.complaint,
        urgency_score=0.6,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T11:00:00Z",
    ),
    # ─── REFUNDS ─────────────────────────────────────────────────────────────
    EmailItem(
        id="email_005",
        subject="Refund request for order #45823",
        body=(
            "I would like to request a refund for order #45823. "
            "The product description did not match what was delivered. "
            "I am returning the item unopened. Could you please process the refund "
            "to my original payment method within 5-7 business days?"
        ),
        sender="lisa.fontaine@email.fr",
        sender_name="Lisa Fontaine",
        category=EmailCategory.refund,
        urgency_score=0.4,
        sentiment=Sentiment.neutral,
        timestamp="2026-04-07T08:45:00Z",
    ),
    EmailItem(
        id="email_006",
        subject="Requesting refund — cancelled subscription",
        body=(
            "Hi, I cancelled my annual subscription on April 1st, which was within the "
            "30-day money-back guarantee window. I have not yet received my refund of $199. "
            "My cancellation confirmation number is CAN-20394. Please process this urgently."
        ),
        sender="tom.baker@protonmail.com",
        sender_name="Tom Baker",
        category=EmailCategory.refund,
        urgency_score=0.5,
        sentiment=Sentiment.neutral,
        timestamp="2026-04-07T12:00:00Z",
    ),
    EmailItem(
        id="email_007",
        subject="Double charged — need refund ASAP",
        body=(
            "I was charged $149 twice for the same order. This is causing issues with my bank. "
            "Please refund one of the charges immediately. My card is already near its limit "
            "and this is causing me real financial stress. Order ID: ORD-88721."
        ),
        sender="mike.okafor@yahoo.com",
        sender_name="Mike Okafor",
        category=EmailCategory.refund,
        urgency_score=0.85,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T07:30:00Z",
    ),
    EmailItem(
        id="email_008",
        subject="Refund for incomplete service",
        body=(
            "I hired your cleaning service for a deep clean of my apartment but the team "
            "only cleaned two rooms and left. I paid $250 for the full apartment. "
            "I am requesting a partial refund of $175 for the work not completed."
        ),
        sender="anna.kowalski@wp.pl",
        sender_name="Anna Kowalski",
        category=EmailCategory.refund,
        urgency_score=0.45,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T14:00:00Z",
    ),
    # ─── INQUIRIES ───────────────────────────────────────────────────────────
    EmailItem(
        id="email_009",
        subject="What are your current shipping rates?",
        body=(
            "Hello, I am interested in placing a bulk order of around 500 units of your "
            "product line for my retail store. Could you please share your current shipping "
            "rates and any bulk discount pricing that may be available? Thank you."
        ),
        sender="retailstore.buyer@mybiz.net",
        sender_name="Diana Chen",
        category=EmailCategory.inquiry,
        urgency_score=0.2,
        sentiment=Sentiment.positive,
        timestamp="2026-04-07T09:30:00Z",
    ),
    EmailItem(
        id="email_010",
        subject="Do you offer corporate accounts?",
        body=(
            "I represent a mid-size tech company of 200 employees. We are looking to "
            "set up a corporate account for regular purchases. I would like to know "
            "about your B2B pricing, net-30 payment terms, and a dedicated account manager. "
            "Please get back to me at your earliest convenience."
        ),
        sender="procurement@techsolutions.com",
        sender_name="Robert Kim",
        category=EmailCategory.inquiry,
        urgency_score=0.25,
        sentiment=Sentiment.neutral,
        timestamp="2026-04-07T10:00:00Z",
    ),
    EmailItem(
        id="email_011",
        subject="Question about warranty coverage",
        body=(
            "I purchased a blender from your store 14 months ago and it has stopped working. "
            "The warranty card says 24-month coverage. Does this issue fall under the warranty? "
            "The motor simply stopped spinning and I have not dropped or misused the product."
        ),
        sender="helen.murphy@irishmail.ie",
        sender_name="Helen Murphy",
        category=EmailCategory.inquiry,
        urgency_score=0.3,
        sentiment=Sentiment.neutral,
        timestamp="2026-04-07T11:30:00Z",
    ),
    EmailItem(
        id="email_012",
        subject="Is your product compatible with Mac?",
        body=(
            "Hi! I was wondering if your USB-C hub is compatible with the latest MacBook Pro M3. "
            "The listing mentions Windows compatibility but does not mention macOS. "
            "Please let me know before I place my order."
        ),
        sender="felix.nguyen@gmail.com",
        sender_name="Felix Nguyen",
        category=EmailCategory.inquiry,
        urgency_score=0.1,
        sentiment=Sentiment.positive,
        timestamp="2026-04-07T13:00:00Z",
    ),
    EmailItem(
        id="email_013",
        subject="Looking for product recommendations",
        body=(
            "Good afternoon! I am setting up a home office and need ergonomic furniture. "
            "My budget is around $800 and I work about 10 hours a day. "
            "Can you recommend the best combination of desk, chair, and monitor stand?"
        ),
        sender="workspace@newstart.co",
        sender_name="Amara Osei",
        category=EmailCategory.inquiry,
        urgency_score=0.15,
        sentiment=Sentiment.positive,
        timestamp="2026-04-07T15:00:00Z",
    ),
    # ─── SPAM ────────────────────────────────────────────────────────────────
    EmailItem(
        id="email_014",
        subject="CONGRATULATIONS! You've won $5,000,000!",
        body=(
            "DEAR VALUED CUSTOMER! You have been selected as the WINNER of our international "
            "lottery draw! You have WON $5,000,000 USD! Click the link below to claim your "
            "prize NOW! Offer expires in 24 hours! www.totally-legit-prize.ru/claim?id=99"
        ),
        sender="noreply@prize-claim-now.xyz",
        sender_name="International Lottery Board",
        category=EmailCategory.spam,
        urgency_score=0.0,
        sentiment=Sentiment.positive,
        timestamp="2026-04-07T08:00:00Z",
    ),
    EmailItem(
        id="email_015",
        subject="Exclusive offer just for you — act now!",
        body=(
            "Hi there! We noticed you visited our site. For the next 2 hours, you can get "
            "90% off everything in our store! This deal is ONLY available to you. "
            "No purchase history required! Just click: www.amazing-deals-today.biz"
        ),
        sender="deals@amazing-discount-site.biz",
        sender_name="Deals Team",
        category=EmailCategory.spam,
        urgency_score=0.0,
        sentiment=Sentiment.positive,
        timestamp="2026-04-07T07:00:00Z",
    ),
    EmailItem(
        id="email_016",
        subject="Your account has suspicious activity — verify now",
        body=(
            "We have detected unusual login to your account from Russia. "
            "Your account will be SUSPENDED in 24 hours unless you verify your email and password "
            "at: www.account-verify-now.net/secure-login — Do not ignore this urgent message!"
        ),
        sender="security@account-verify-now.net",
        sender_name="Security Team",
        category=EmailCategory.spam,
        urgency_score=0.0,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T06:30:00Z",
    ),
    EmailItem(
        id="email_017",
        subject="Make $10,000 a week working from home!",
        body=(
            "Are you tired of your 9-to-5 job? Our proven system lets you earn $10,000 "
            "every week from the comfort of your home! No experience needed! Sign up today "
            "at www.easy-money-system.info and start earning IMMEDIATELY!"
        ),
        sender="info@easy-money-system.info",
        sender_name="Work From Home Team",
        category=EmailCategory.spam,
        urgency_score=0.0,
        sentiment=Sentiment.positive,
        timestamp="2026-04-07T05:00:00Z",
    ),
    # ─── URGENT ──────────────────────────────────────────────────────────────
    EmailItem(
        id="email_018",
        subject="CRITICAL: Payment system down — losing revenue RIGHT NOW",
        body=(
            "This is an emergency. Our payment gateway has been returning error code 503 "
            "for the past 45 minutes. We are an e-commerce business processing thousands "
            "of transactions per hour. We are losing approximately $12,000 per minute. "
            "We need a senior engineer on this call IMMEDIATELY. My number: +1-555-0192. "
            "Escalation contact: CTO Mark Davis at mark.davis@ourbusiness.com."
        ),
        sender="ops-director@ourbusiness.com",
        sender_name="Jennifer Torres",
        category=EmailCategory.urgent,
        urgency_score=1.0,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T16:00:00Z",
        sla_deadline_steps=3,  # must act within 3 steps or SLA breach
    ),
    EmailItem(
        id="email_019",
        subject="Security breach detected in our account",
        body=(
            "We believe our company account with your service has been compromised. "
            "We are seeing unauthorized API calls that began at 3:15 AM today. "
            "We need you to immediately suspend all API access and issue new credentials. "
            "This may be a data breach affecting our 50,000 users."
        ),
        sender="ciso@securecorp.io",
        sender_name="David Park",
        category=EmailCategory.urgent,
        urgency_score=0.98,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T04:30:00Z",
    ),
    EmailItem(
        id="email_020",
        subject="Hospital system integration failure — patient data at risk",
        body=(
            "URGENT: Our hospital's patient management system integration with your API "
            "has failed. We are unable to access critical patient records. "
            "This is causing delays in patient care. Multiple departments affected. "
            "Please escalate to your highest engineering tier immediately. "
            "Contact: Dr. Sarah Chen, IT Director, +1-555-0847."
        ),
        sender="it-emergency@regionalhospital.org",
        sender_name="Hospital IT Emergency",
        category=EmailCategory.urgent,
        urgency_score=0.99,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T06:00:00Z",
    ),
    EmailItem(
        id="email_021",
        subject="Account suspended without warning — affecting business operations",
        body=(
            "Our enterprise account was suspended at 9 AM today with no warning or explanation. "
            "We have 3,000 active users who cannot access the service. "
            "We have a major product launch happening in 6 hours. "
            "We need our account reinstated NOW. We have been a paying customer for 4 years."
        ),
        sender="operations@startup-unicorn.com",
        sender_name="Alex Reynolds",
        category=EmailCategory.urgent,
        urgency_score=0.92,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T09:15:00Z",
    ),
    # ─── ABUSE ───────────────────────────────────────────────────────────────
    EmailItem(
        id="email_022",
        subject="I WILL SUE YOUR COMPANY",
        body=(
            "You absolute idiots have ruined my life. I am going to sue every single one of you "
            "personally. My lawyer will be contacting you tomorrow. You are all incompetent fools "
            "and deserve to be shut down. I have posted on every review site about your pathetic "
            "excuse for a company. Go to hell!"
        ),
        sender="angry.guy@hotmail.com",
        sender_name="Unknown Sender",
        category=EmailCategory.abuse,
        urgency_score=0.6,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T13:30:00Z",
    ),
    EmailItem(
        id="email_023",
        subject="Your employee is a scammer and a liar",
        body=(
            "Your employee John in sales is a complete fraud. He told me I would get free shipping "
            "for life and now you people are charging me. I am going to report this to the BBB, "
            "FTC, and every consumer protection agency. I am also filing a chargeback "
            "for every purchase I have ever made. You are all crooks."
        ),
        sender="disgruntled2024@anon.mail",
        sender_name="Anonymous",
        category=EmailCategory.abuse,
        urgency_score=0.55,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T14:45:00Z",
    ),
    # ─── ADDITIONAL MIXED ────────────────────────────────────────────────────
    EmailItem(
        id="email_024",
        subject="Feedback: Great product, small issue",
        body=(
            "Hey team! I love the new product update, the UI is much cleaner now. "
            "One small issue: the dark mode toggle doesn't save between sessions. "
            "Every time I log in it reverts to light mode. Not a big deal but thought "
            "you should know. Keep up the great work!"
        ),
        sender="happyuser@digitallife.com",
        sender_name="Marcus Green",
        category=EmailCategory.inquiry,
        urgency_score=0.1,
        sentiment=Sentiment.positive,
        timestamp="2026-04-07T10:15:00Z",
    ),
    EmailItem(
        id="email_025",
        subject="Need immediate refund — medical emergency",
        body=(
            "I am in the hospital right now and desperately need the $300 refund "
            "for my cancelled order to pay for medical expenses. I cancelled within the "
            "return window. My cancellation ID is RET-40921. Please process this as fast "
            "as humanly possible. I cannot wait the standard 5-7 days."
        ),
        sender="emergency.request@family.net",
        sender_name="Laura Kim",
        category=EmailCategory.refund,
        urgency_score=0.9,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T07:45:00Z",
        sla_deadline_steps=4,  # medical urgency - must act within 4 steps
    ),
    EmailItem(
        id="email_026",
        subject="Partnership opportunity — AI integration",
        body=(
            "Hello, I am the CEO of DataFlow AI, a Series B startup. "
            "We believe there is a significant opportunity to integrate our AI pipeline "
            "with your platform. I would love to schedule a call with your business "
            "development team this week. Please let me know your availability."
        ),
        sender="ceo@dataflow-ai.io",
        sender_name="Nathaniel Brooks",
        category=EmailCategory.inquiry,
        urgency_score=0.3,
        sentiment=Sentiment.positive,
        timestamp="2026-04-07T11:00:00Z",
    ),
    EmailItem(
        id="email_027",
        subject="Order not received — 3 weeks late",
        body=(
            "I placed order #92034 three weeks ago and it still has not arrived. "
            "The tracking number you provided shows 'in transit' for 18 days. "
            "This is completely unacceptable. I need to know where my package is "
            "or I will be disputing the charge with my credit card company."
        ),
        sender="waiting.customer@mailbox.org",
        sender_name="Yuki Tanaka",
        category=EmailCategory.complaint,
        urgency_score=0.75,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T09:00:00Z",
    ),
    EmailItem(
        id="email_028",
        subject="Re: Support ticket #1234 — still not resolved after 2 weeks",
        body=(
            "This is my fourth email about ticket #1234. I submitted this two weeks ago "
            "and keep getting automated replies saying 'we are looking into it.' "
            "Nothing has been done. What is going on? I need a human to actually "
            "read this and take action. I am losing patience."
        ),
        sender="frustrated.user@email.co",
        sender_name="Patrick O'Brien",
        category=EmailCategory.complaint,
        urgency_score=0.7,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T12:30:00Z",
        thread_id="thread_support_1234",
        thread_position=1,
    ),
    EmailItem(
        id="email_029",
        subject="Re: Re: Support ticket #1234 — escalation requested",
        body=(
            "Following up on my previous emails. I have spoken with two agents already. "
            "Both promised resolution within 24 hours — now 72 hours later, nothing. "
            "I am formally requesting escalation to a supervisor or manager. "
            "Please acknowledge this email within 2 hours."
        ),
        sender="frustrated.user@email.co",
        sender_name="Patrick O'Brien",
        category=EmailCategory.urgent,
        urgency_score=0.88,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T14:00:00Z",
        thread_id="thread_support_1234",
        thread_position=2,
    ),
    EmailItem(
        id="email_030",
        subject="Free crypto — just share your wallet address!",
        body=(
            "Hello! We are giving away 5 Bitcoin to random users today! "
            "Just send your wallet address and we will send you 0.5 BTC for free! "
            "This is a promotional campaign by CryptoGiftclub. Offer limited — act now!"
        ),
        sender="gifts@cryptogiftclub.money",
        sender_name="Crypto Gift Club",
        category=EmailCategory.spam,
        urgency_score=0.0,
        sentiment=Sentiment.positive,
        timestamp="2026-04-07T06:00:00Z",
    ),
    EmailItem(
        id="email_031",
        subject="Software license expired — team cannot work",
        body=(
            "Our enterprise software license for your platform expired at midnight. "
            "My entire development team of 25 people is locked out and cannot work. "
            "We paid for the annual renewal on March 28th — you can verify this. "
            "Please restore access immediately. We are losing €5,000 per hour."
        ),
        sender="it-admin@devhouse.eu",
        sender_name="Sophie Weber",
        category=EmailCategory.urgent,
        urgency_score=0.95,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T08:30:00Z",
    ),
    EmailItem(
        id="email_032",
        subject="Thank you for the excellent support!",
        body=(
            "Hi! I just wanted to say thank you to your support team, especially agent Maya, "
            "for resolving my billing issue so quickly yesterday. She was professional, "
            "empathetic, and efficient. This kind of service keeps me as a loyal customer. "
            "Please pass along my appreciation to her and the team!"
        ),
        sender="satisfied.customer@personalbox.com",
        sender_name="Grace Thompson",
        category=EmailCategory.inquiry,
        urgency_score=0.05,
        sentiment=Sentiment.positive,
        timestamp="2026-04-07T16:30:00Z",
    ),
    EmailItem(
        id="email_033",
        subject="Inquiry about enterprise pricing tiers",
        body=(
            "Hello, we are a 500-person financial services firm evaluating your platform. "
            "We need to understand your enterprise pricing, SLA guarantees, and data "
            "residency options (we require EU data centers). Could you schedule a call "
            "with your enterprise sales team? Best time is Tuesday or Wednesday afternoon."
        ),
        sender="it-procurement@finservgroup.com",
        sender_name="Benjamin Hoffman",
        category=EmailCategory.inquiry,
        urgency_score=0.35,
        sentiment=Sentiment.neutral,
        timestamp="2026-04-07T10:45:00Z",
    ),
    EmailItem(
        id="email_034",
        subject="Account hacked — unauthorized purchases made",
        body=(
            "I believe my account has been hacked. I received two order confirmation emails "
            "for items I never ordered — total value $847. I did not make these purchases. "
            "Please freeze my account immediately and reverse the fraudulent charges. "
            "I have already changed my password and enabled 2FA."
        ),
        sender="victim.user@safemail.com",
        sender_name="Chidi Okonkwo",
        category=EmailCategory.urgent,
        urgency_score=0.93,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T05:30:00Z",
    ),
    EmailItem(
        id="email_035",
        subject="Product arrived damaged — photos attached",
        body=(
            "I received my order today and the item was badly damaged — the packaging was crushed "
            "and the glass panel is completely shattered. I have documentation of the damage. "
            "I am requesting a replacement to be expedited. Order: ORD-77612. "
            "Please advise on the return shipping process."
        ),
        sender="product.buyer@webshop.de",
        sender_name="Klaus Bauer",
        category=EmailCategory.complaint,
        urgency_score=0.55,
        sentiment=Sentiment.negative,
        timestamp="2026-04-07T15:30:00Z",
    ),
]

# Indexed lookup for O(1) access
EMAIL_BY_ID: dict[str, EmailItem] = {e.id: e for e in EMAIL_CORPUS}


def get_email(email_id: str) -> EmailItem | None:
    """Return a fresh copy of an email by ID."""
    email = EMAIL_BY_ID.get(email_id)
    if email:
        return email.model_copy(deep=True)
    return None


def get_emails_by_category(category: EmailCategory) -> list[EmailItem]:
    return [e.model_copy(deep=True) for e in EMAIL_CORPUS if e.category == category]
