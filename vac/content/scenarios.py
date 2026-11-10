"""Interests, goals and the role-play simulations built from them."""

INTERESTS = [
    ("gaming", "Gaming", "game-controller"),
    ("job", "Job and career", "briefcase"),
    ("tech", "Tech", "cpu"),
    ("family", "Family", "users"),
    ("travel", "Travel", "airplane-tilt"),
    ("study", "Study abroad", "graduation-cap"),
    ("food", "Food", "fork-knife"),
    ("music", "Music and film", "music-notes"),
    ("sports", "Sports", "soccer-ball"),
]

GOALS = [
    ("job", "Get a job", "briefcase"),
    ("visa", "Visa or residency", "airplane-tilt"),
    ("scholarship", "Scholarship or university", "graduation-cap"),
    ("life", "Everyday life", "house"),
]

# Each scenario: the situation, who the AI plays, what the learner must get done, and a writing task
# the Examiner can set from it. `open` is the AI's first line when there is no connection.
SCENARIOS = [
    {"id": "cafe", "interest": "food", "title": "Order at a cafe", "icon": "coffee", "sketch": "cafe",
     "role": "a friendly cafe waiter", "situation": "You walk into a small cafe and want a drink and something to eat.",
     "tasks": ["Greet and ask for the menu", "Order a drink and one food item", "Ask for the bill"],
     "write": "Write a short review of a cafe you visited: what you ordered and whether you liked it.",
     "open": {"ja": "いらっしゃいませ。ごちゅうもんは？", "de": "Guten Tag! Was möchten Sie?",
              "en": "Hi there! What can I get you today?"}},
    {"id": "interview", "interest": "job", "title": "Job interview", "icon": "briefcase", "sketch": "interview",
     "role": "a hiring manager interviewing you for a junior role",
     "situation": "You are in a first interview for a job you want.",
     "tasks": ["Introduce yourself", "Describe your experience or studies", "Say why you want the job",
               "Ask one question about the company"],
     "write": "Write a short self-introduction for a job application: who you are, what you can do, why this job.",
     "open": {"ja": "こんにちは。どうぞ すわって ください。じこしょうかいを おねがいします。",
              "de": "Guten Tag, nehmen Sie bitte Platz. Stellen Sie sich bitte kurz vor.",
              "en": "Good morning, please take a seat. Could you start by telling me about yourself?"}},
    {"id": "standup", "interest": "tech", "title": "Team stand-up", "icon": "cpu", "sketch": "study",
     "role": "your team lead running the daily stand-up meeting",
     "situation": "It is the morning stand-up. You report on your work.",
     "tasks": ["Say what you did yesterday", "Say what you will do today", "Mention one problem and ask for help"],
     "write": "Write a short message to your team explaining a bug you found and what you need from them.",
     "open": {"ja": "おはようございます。きのうは なにを しましたか。",
              "de": "Guten Morgen! Was haben Sie gestern gemacht?",
              "en": "Morning! Let's start with you. What did you get done yesterday?"}},
    {"id": "voicechat", "interest": "gaming", "title": "Game voice chat", "icon": "game-controller", "sketch": "gaming",
     "role": "a teammate in an online co-op game, casual and friendly",
     "situation": "You join a voice channel before a match and plan with a teammate.",
     "tasks": ["Greet your teammate", "Say which role you will play", "Suggest a plan", "React to how the match went"],
     "write": "Write a short post for a game forum: introduce yourself and say what kind of teammates you are looking for.",
     "open": {"ja": "やあ！いっしょに ゲームを しましょう。どの キャラクターが すきですか。",
              "de": "Hey! Bist du bereit? Welche Rolle spielst du heute?",
              "en": "Hey! You ready? Which role are you playing this round?"}},
    {"id": "hostfamily", "interest": "family", "title": "Dinner with a host family", "icon": "users",
     "sketch": "family", "role": "a kind host parent at the dinner table",
     "situation": "It is your first dinner with your host family.",
     "tasks": ["Thank them for the meal", "Talk about your own family", "Say what food you like",
               "Offer to help after dinner"],
     "write": "Write a thank-you note to your host family after your first week.",
     "open": {"ja": "どうぞ、たくさん たべて ください。ごかぞくは なんにんですか。",
              "de": "Guten Appetit! Erzählen Sie doch ein bisschen von Ihrer Familie.",
              "en": "Help yourself! So, tell us a little about your family back home."}},
    {"id": "airport", "interest": "travel", "title": "Airport immigration", "icon": "airplane-tilt",
     "sketch": "airport", "role": "an immigration officer, polite and brief",
     "situation": "You have just landed and reach the immigration desk.",
     "tasks": ["Say why you are visiting", "Say how long you will stay", "Say where you will stay"],
     "write": "Write an email to a hotel: book a room, give your dates and ask about airport transport.",
     "open": {"ja": "パスポートを みせて ください。にほんへ なにを しに きましたか。",
              "de": "Guten Tag, Ihren Pass bitte. Was ist der Grund für Ihre Reise?",
              "en": "Good afternoon. Passport, please. What is the purpose of your visit?"}},
    {"id": "station", "interest": "travel", "title": "Buy a train ticket", "icon": "train", "sketch": "station",
     "role": "a ticket office clerk", "situation": "You need a ticket to another city today.",
     "tasks": ["Say where you want to go", "Ask the price and the time", "Ask which platform"],
     "write": "Write a message to a friend: say which train you are taking and when you arrive.",
     "open": {"ja": "いらっしゃいませ。どちらまで いきますか。", "de": "Guten Tag! Wohin möchten Sie fahren?",
              "en": "Hello! Where are you travelling to today?"}},
    {"id": "campus", "interest": "study", "title": "University admissions office", "icon": "graduation-cap",
     "sketch": "classroom", "role": "an admissions officer at a university",
     "situation": "You visit the admissions office to ask about a course and a scholarship.",
     "tasks": ["Say which course interests you", "Ask about entry requirements", "Ask about scholarships and deadlines"],
     "write": "Write a short statement: why you want to study this subject in this country.",
     "open": {"ja": "こんにちは。どの コースに きょうみが ありますか。",
              "de": "Guten Tag! Für welchen Studiengang interessieren Sie sich?",
              "en": "Hello, welcome. Which course are you interested in applying for?"}},
    {"id": "doctor", "interest": "family", "title": "At the doctor", "icon": "first-aid", "sketch": "doctor",
     "role": "a calm family doctor", "situation": "You feel unwell and see a doctor.",
     "tasks": ["Describe your symptoms", "Say since when", "Ask what you should do"],
     "write": "Write a message to your manager or teacher: you are ill and cannot come today.",
     "open": {"ja": "こんにちは。どう しましたか。", "de": "Guten Tag. Was fehlt Ihnen denn?",
              "en": "Hello, come in. What seems to be the problem?"}},
    {"id": "concert", "interest": "music", "title": "Plan a night out", "icon": "music-notes", "sketch": "greeting",
     "role": "a friend who loves music and films",
     "situation": "You and a friend decide what to do this weekend.",
     "tasks": ["Suggest a concert or a film", "Agree a day and time", "Decide where to meet"],
     "write": "Write an invitation to a friend for a concert or a film this weekend.",
     "open": {"ja": "しゅうまつ、なにを しますか。えいがは どうですか。",
              "de": "Hast du am Wochenende Zeit? Wollen wir etwas zusammen machen?",
              "en": "Any plans this weekend? Fancy seeing a film or a gig?"}},
    {"id": "gym", "interest": "sports", "title": "Join a sports club", "icon": "soccer-ball", "sketch": "transport",
     "role": "the receptionist at a sports club", "situation": "You want to join a local sports club.",
     "tasks": ["Say which sport you want to do", "Ask about days, times and price", "Give your name and contact"],
     "write": "Write a short message asking to join a local sports team: your experience and when you are free.",
     "open": {"ja": "こんにちは。どの スポーツを したいですか。",
              "de": "Hallo! Für welchen Sport interessieren Sie sich?",
              "en": "Hi! Welcome to the club. Which sport are you interested in?"}},
    {"id": "shop", "interest": "food", "title": "Shopping at the market", "icon": "shopping-cart", "sketch": "market",
     "role": "a cheerful market stall owner", "situation": "You are buying fruit and bread at a market.",
     "tasks": ["Ask what something costs", "Buy two different things", "Pay and say goodbye"],
     "write": "Write a shopping list with quantities, then a note asking a flatmate to buy the items.",
     "open": {"ja": "いらっしゃい！きょうは りんごが やすいですよ。", "de": "Guten Morgen! Was darf es sein?",
              "en": "Morning! Lovely fresh apples today. What can I get you?"}},
]


def scenario(sid):
    for s in SCENARIOS:
        if s["id"] == sid:
            return s
    return None


def for_interests(interests):
    """Scenarios ordered so the learner's interests come first."""
    mine = [s for s in SCENARIOS if s["interest"] in interests]
    rest = [s for s in SCENARIOS if s["interest"] not in interests]
    return mine + rest
