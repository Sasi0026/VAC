"""Built-in mock exams for the three starter levels.

These are original practice questions written to the official format (same sections, item types
and pass rules as the real tests) at reduced length. They are not past papers.

Question fields: sec (score section id), part (official item type), q, sub (passage shown),
say (script read aloud by text-to-speech and never shown), o (options, correct one FIRST), type.
"""
from .base import Q


def M(sec, part, q, options, sub="", say=""):
    d = Q(q, options, 0, sub)
    d.update(sec=sec, part=part)
    if say:
        d["say"] = say
    return d


def TXT(sec, part, q, accept, sub="", say=""):
    d = {"type": "text", "sec": sec, "part": part, "q": q, "accept": accept, "sub": sub}
    if say:
        d["say"] = say
    return d


def OPEN(kind, sec, part, q, rubric, model, max_pts, sub="", min_words=0):
    return {"type": kind, "sec": sec, "part": part, "q": q, "rubric": rubric, "model": model, "max": max_pts,
            "sub": sub, "min_words": min_words}


# ----------------------------------------------------------------------------- JLPT N5
_KR = "＿＿の ことばは ひらがなで どう かきますか。"
_OR = "＿＿の ことばは どう かきますか。"
_CX = "（　）に なにを いれますか。"
_PA = "つぎの ぶんと だいたい おなじ いみの ぶんは どれですか。"
_ST = "★に はいる ものは どれですか。"
_PASS_A = ("やまださんへ\nきょうの ごご、3じに えきの まえで あいましょう。えいがは 3じはんに はじまります。"
           "チケットは わたしが もって いきます。\nリー")
_PASS_B = ("わたしの へやには つくえと ベッドが あります。テレビは ありません。つくえの うえに パソコンが あります。"
           "まいばん パソコンで おんがくを ききます。")
_PASS_C = ("きのうは にちようびでした。あさ、ともだちの キムさんと こうえんで テニスを しました。そのあと、ふたりで "
           "レストランへ いきました。わたしは カレーを たべました。キムさんは さかなが すきですから、さかなの りょうりを "
           "たべました。ごご、わたしは うちで しゅくだいを しました。キムさんは としょかんへ いきました。")
_INFO = ("にほんごクラスの おしらせ\nAクラス：げつようび・すいようび 10:00〜12:00　3,000円\n"
         "Bクラス：かようび・もくようび 18:00〜20:00　3,500円\nCクラス：どようび 9:00〜12:00　2,500円")
_TEXT_G = "わたしは まいあさ 6じに おきます。（ 1 ）、こうえんを さんぽします。こうえんは しずかで、とても（ 2 ）。"

N5 = {
    "id": "ja-n5", "title": "JLPT N5 mock test", "minutes": 35,
    "note": "Compact mock: every official N5 item type, about 40% of full length. Listening is read by your "
            "phone's Japanese voice.",
    "questions": [
        M("lk", "Kanji reading", _KR, ["てんき", "でんき", "てんぎ", "でんぎ"], "きょうは 【天気】が いいです。"),
        M("lk", "Kanji reading", _KR, ["みず", "みす", "みづ", "すい"], "【水】を のみます。"),
        M("lk", "Kanji reading", _KR, ["ひゃく", "びゃく", "ひやく", "はく"], "【百】円の ペンを かいました。"),
        M("lk", "Kanji reading", _KR, ["せんせい", "せんせ", "せいせん", "せんせえ"], "あの 人は 【先生】です。"),
        M("lk", "Orthography", _OR, ["学生", "字生", "学先", "字先"], "わたしは 【がくせい】です。"),
        M("lk", "Orthography", _OR, ["テレビ", "テルビ", "チレビ", "テレヒ"], "【てれび】を みます。"),
        M("lk", "Orthography", _OR, ["山", "川", "出", "上"], "【やま】に のぼります。"),
        M("lk", "Contextually-defined expressions", _CX, ["のって", "はいって", "あがって", "あるいて"],
          "バスに（　）、がっこうへ いきます。"),
        M("lk", "Contextually-defined expressions", _CX, ["おいしい", "おもしろい", "いそがしい", "わかい"],
          "この りんごは とても（　）です。"),
        M("lk", "Contextually-defined expressions", _CX, ["かります", "うります", "あらいます", "きります"],
          "としょかんで ほんを（　）。"),
        M("lk", "Contextually-defined expressions", _CX, ["コート", "プール", "ノート", "テーブル"],
          "さむいですから、（　）を きます。"),
        M("lk", "Paraphrases", _PA,
          ["この へやは きれいじゃ ありません。", "この へやは ひろく ありません。", "この へやは あかるいです。",
           "この へやは しずかです。"], "この へやは きたないです。"),
        M("lk", "Paraphrases", _PA,
          ["あには びょういんで はたらいて います。", "あには がっこうで おしえて います。", "あには みせで うって います。",
           "あには ぎんこうで はたらいて います。"], "あには いしゃです。"),
        M("lk", "Sentential grammar 1", _CX, ["で", "に", "を", "が"], "わたしは まいにち バス（　）かいしゃへ いきます。"),
        M("lk", "Sentential grammar 1", _CX, ["で", "に", "へ", "が"], "きのう デパート（　）くつを かいました。"),
        M("lk", "Sentential grammar 1", _CX, ["の", "が", "を", "に"], "これは だれ（　）かさですか。"),
        M("lk", "Sentential grammar 1", _CX, ["が", "を", "で", "へ"], "へやに いす（　）ふたつ あります。"),
        M("lk", "Sentential grammar 1", _CX, ["ませんか", "ました", "ませんでした", "ですか"],
          "A「いっしょに ひるごはんを たべ（　）。」\nB「いいですね。」"),
        M("lk", "Sentential grammar 1", _CX, ["ですが", "ですから", "でした", "ですね"],
          "にほんごは むずかしい（　）、おもしろいです。"),
        M("lk", "Sentential grammar 2", _ST, ["いる", "めがねを", "人", "かけて"],
          "あの ＿＿ ＿＿ ★ ＿＿ は たなかさんです。\n（めがねを ／ 人 ／ かけて ／ いる）"),
        M("lk", "Sentential grammar 2", _ST, ["えいがは", "みた", "とても", "ともだちと"],
          "きのう ＿＿ ＿＿ ★ ＿＿ おもしろかったです。\n（えいがは ／ みた ／ とても ／ ともだちと）"),
        M("lk", "Text grammar", "（ 1 ）に なにを いれますか。", ["それから", "でも", "しかし", "だから"], _TEXT_G),
        M("lk", "Text grammar", "（ 2 ）に なにを いれますか。", ["きれいです", "きれいだです", "きれいなです", "きれいくです"],
          _TEXT_G),
        M("lk", "Comprehension (short passages)", "リーさんと やまださんは どこで あいますか。",
          ["えきの まえ", "えいがかん", "やまださんの うち", "がっこう"], _PASS_A),
        M("lk", "Comprehension (short passages)", "この ひとは まいばん なにを しますか。",
          ["おんがくを ききます", "テレビを みます", "ほんを よみます", "べんきょうします"], _PASS_B),
        M("lk", "Comprehension (mid-size passages)", "ふたりは テニスの あとで なにを しましたか。",
          ["レストランで ごはんを たべました", "としょかんへ いきました", "しゅくだいを しました", "こうえんを さんぽしました"],
          _PASS_C),
        M("lk", "Comprehension (mid-size passages)", "キムさんは レストランで なにを たべましたか。",
          ["さかなの りょうり", "カレー", "にく", "パン"], _PASS_C),
        M("lk", "Information retrieval",
          "マリアさんは げつようびから きんようびまで、あさ 9じから ごご 5じまで はたらきます。どようびと にちようびは "
          "やすみたいです。どの クラスが いいですか。", ["Bクラス", "Aクラス", "Cクラス", "Aクラスと Cクラス"], _INFO),
        M("li", "Task-based comprehension", "おんなの ひとは なにを かいますか。",
          ["ぎゅうにゅうと たまご", "ぎゅうにゅうと パン", "パンと たまご", "ぎゅうにゅうだけ"],
          say="男の人と女の人が話しています。女の人は何を買いますか。男の人、すみません、牛乳を買ってきてください。"
              "女の人、はい。パンも買いますか。男の人、パンはまだあります。あ、卵をお願いします。女の人、わかりました。"),
        M("li", "Task-based comprehension", "がくせいは あした なんじに がっこうへ きますか。",
          ["9じはん", "9じ", "10じ", "10じはん"],
          say="学生が先生と話しています。学生は明日、何時に学校へ来ますか。学生、先生、明日のテストは九時からですか。"
              "先生、いいえ、十時からです。でも、九時半に教室に来てください。学生、はい、わかりました。"),
        M("li", "Task-based comprehension", "おんなの ひとは どの かばんを かいますか。",
          ["ちいさくて しろい かばん", "おおきくて しろい かばん", "ちいさくて くろい かばん", "おおきくて くろい かばん"],
          say="女の人が店の人と話しています。女の人はどのかばんを買いますか。店の人、いらっしゃいませ。この大きいかばんは"
              "どうですか。女の人、ちょっと大きいですね。小さいのはありますか。店の人、はい。黒いのと白いのがあります。"
              "女の人、じゃあ、白いのをください。"),
        M("li", "Comprehension of key points", "おとこの ひとは どようびに なにを しましたか。",
          ["うちで ほんを よみました", "へやの そうじを しました", "でかけました", "えいがを みました"],
          say="男の人と女の人が話しています。男の人は土曜日に何をしましたか。女の人、週末はどこかへ行きましたか。"
              "男の人、いいえ。土曜日は雨でしたから、家で本を読みました。日曜日は部屋の掃除をしました。"),
        M("li", "Comprehension of key points", "おんなの ひとの かぞくは なんにんですか。",
          ["5にん", "4にん", "3にん", "6にん"],
          say="女の人が話しています。女の人の家族は何人ですか。私の家族は、父と母と兄と妹と私です。兄は東京に住んでいます。"),
        M("li", "Comprehension of key points", "ふたりは なにで いきますか。",
          ["タクシー", "バス", "あるいて いきます", "でんしゃ"],
          say="男の人と女の人が話しています。二人は何で行きますか。男の人、駅まで歩いて行きますか。女の人、ちょっと遠い"
              "ですね。バスはどうですか。男の人、バスは今出ました。タクシーで行きましょう。女の人、そうですね。"),
        M("li", "Verbal expressions", "ともだちの うちに はいります。なんと いいますか。",
          ["おじゃまします。", "いってきます。", "ただいま。", "ごちそうさま。"]),
        M("li", "Verbal expressions", "レストランで みずが ほしいです。みせの ひとに なんと いいますか。",
          ["すみません、みずを ください。", "みずを のみましょうか。", "みずは どうですか。", "みずを どうぞ。"]),
        M("li", "Quick response", "へんじを えらんで ください。",
          ["はい、げんきです。", "はい、そうです。", "いいえ、ちがいます。", "どういたしまして。"], say="お元気ですか。"),
        M("li", "Quick response", "へんじを えらんで ください。",
          ["わたしのです。", "ほんです。", "はい、そうです。", "つくえの うえです。"], say="これは誰の本ですか。"),
        M("li", "Quick response", "へんじを えらんで ください。",
          ["ありがとうございます。いただきます。", "はい、コーヒーです。", "いいえ、のみました。", "どうぞ。"],
          say="コーヒーはいかがですか。"),
    ],
}

# ----------------------------------------------------------------------------- Goethe A1
_RF = ["Richtig", "Falsch"]
_FR = ["Falsch", "Richtig"]
_MAIL = ("Liebe Maria,\nvielen Dank für deine Einladung. Ich komme gern zu deiner Party am Samstag. Leider kann ich "
         "erst um 20 Uhr kommen, weil ich bis 19 Uhr arbeiten muss. Ich bringe einen Salat mit.\nBis Samstag!\nDeine Julia")
_FORM = ("Ihre Freundin Eva Kadavy möchte einen Deutschkurs machen. Sie ist 28 Jahre alt, kommt aus Prag und wohnt "
         "jetzt in Hamburg, Bergstraße 5. Sie möchte am Abend lernen und bar bezahlen.\nHelfen Sie Eva und füllen Sie "
         "das Formular aus.")

A1 = {
    "id": "de-a1", "title": "Goethe-Zertifikat A1 mock test", "minutes": 30,
    "note": "Compact mock with all four modules: Hören, Lesen, Schreiben, Sprechen. Listening is read by your "
            "phone's German voice. Writing and speaking are marked by the Examiner agent.",
    "questions": [
        M("ho", "Hören Teil 1", "Was kostet der Pullover?", ["29,50 Euro", "25,90 Euro", "92,50 Euro"],
          say="Entschuldigung, wie viel kostet dieser Pullover? Der kostet neunundzwanzig Euro fünfzig. Gut, den nehme ich."),
        M("ho", "Hören Teil 1", "Wann fährt der Zug nach Köln?", ["Um 14.20 Uhr", "Um 14.02 Uhr", "Um 4.20 Uhr"],
          say="Guten Tag, ich möchte nach Köln fahren. Wann fährt der nächste Zug? Der nächste Zug fährt um vierzehn Uhr "
              "zwanzig von Gleis sieben."),
        M("ho", "Hören Teil 1", "Wo treffen sich Anna und Peter?", ["Vor dem Kino", "Im Café", "Am Bahnhof"],
          say="Hallo Anna, hier ist Peter. Wir treffen uns heute nicht im Café, sondern vor dem Kino. Der Film beginnt um acht."),
        M("ho", "Hören Teil 2", "Richtig oder falsch? „Die Äpfel sind im ersten Stock.“", _FR,
          say="Liebe Kunden, heute im Angebot: frische Äpfel, das Kilo nur ein Euro neunundneunzig. Sie finden die Äpfel "
              "in der Obstabteilung im Erdgeschoss."),
        M("ho", "Hören Teil 2", "Richtig oder falsch? „Der Zug nach München kommt später.“", _RF,
          say="Achtung, eine Durchsage: Der Zug nach München hat heute zwanzig Minuten Verspätung."),
        M("ho", "Hören Teil 3", "Wann ist der neue Termin?", ["Am Mittwoch um 10 Uhr", "Am Montag um 10 Uhr",
                                                             "Am Mittwoch um 12 Uhr"],
          say="Guten Tag, hier ist die Praxis Doktor Weber. Ihr Termin am Montag fällt leider aus. Bitte kommen Sie am "
              "Mittwoch um zehn Uhr."),
        M("le", "Lesen Teil 1", "Richtig oder falsch? „Julia kommt zur Party.“", _RF, _MAIL),
        M("le", "Lesen Teil 1", "Richtig oder falsch? „Julia arbeitet am Samstag nicht.“", _FR, _MAIL),
        M("le", "Lesen Teil 1", "Was bringt Julia mit?", ["Einen Salat", "Einen Kuchen", "Getränke"], _MAIL),
        M("le", "Lesen Teil 2", "Sie suchen ein Zimmer in Berlin. Welche Anzeige passt?", ["Anzeige a", "Anzeige b"],
          "a) Zimmer frei! 20 m², Berlin-Mitte, 450 Euro im Monat. Tel. 030 123456\n"
          "b) Ferienwohnung in München, 80 Euro pro Nacht, mit Balkon."),
        M("le", "Lesen Teil 3", "Richtig oder falsch? „Am Sonntag kann man hier Brot kaufen.“", _FR,
          "Bäckerei Schmidt\nÖffnungszeiten: Mo-Fr 6.30-18.00 Uhr, Sa 7.00-13.00 Uhr, So geschlossen"),
        M("le", "Lesen Teil 3", "Richtig oder falsch? „Das Büro ist jetzt im zweiten Stock.“", _RF,
          "Sprachschule Lingua\nDas Büro ist umgezogen. Sie finden uns jetzt im 2. Stock, Zimmer 204."),
        M("sc", "Schreiben Teil 1", "Formular: Alter", ["28", "5", "20"], _FORM),
        M("sc", "Schreiben Teil 1", "Formular: Wohnort", ["Hamburg", "Prag", "Bergstraße"], _FORM),
        M("sc", "Schreiben Teil 1", "Formular: Kurszeit", ["abends", "vormittags", "am Wochenende"], _FORM),
        OPEN("write", "sc", "Schreiben Teil 2",
             "Sie möchten nächsten Monat einen Deutschkurs in Leipzig machen. Schreiben Sie an die Sprachschule:\n"
             "- Warum schreiben Sie?\n- Wann möchten Sie den Kurs machen?\n- Fragen Sie nach dem Preis.\n"
             "Schreiben Sie circa 30 Wörter. Vergessen Sie Anrede und Gruß nicht.",
             "Goethe A1 Schreiben Teil 2: all three points covered (most weight), formal greeting and closing, text is "
             "understandable despite errors.",
             "Sehr geehrte Damen und Herren,\nich möchte einen Deutschkurs in Leipzig machen. Ich möchte den Kurs im "
             "Mai besuchen. Was kostet der Kurs? Vielen Dank für Ihre Antwort.\nMit freundlichen Grüßen\nRavi Kumar",
             5, min_words=20),
        OPEN("speak", "sp", "Sprechen Teil 1",
             "Stellen Sie sich vor: Name, Alter, Land, Wohnort, Sprachen, Beruf, Hobby.",
             "Goethe A1 Sprechen Teil 1: gives most of the seven details in simple, understandable sentences.",
             "Ich heiße Ravi Kumar. Ich bin 26 Jahre alt. Ich komme aus Indien und wohne in Berlin. Ich spreche Hindi, "
             "Englisch und ein bisschen Deutsch. Ich bin Ingenieur von Beruf. Mein Hobby ist Fußball.", 3),
        OPEN("speak", "sp", "Sprechen Teil 2",
             "Thema: Essen und Trinken. Stellen Sie eine Frage mit dem Wort „Frühstück“. Antworten Sie dann auf die "
             "Frage: „Was trinken Sie gern?“",
             "Goethe A1 Sprechen Teil 2: one correct question using the word, one fitting answer.",
             "Was essen Sie zum Frühstück? - Ich trinke gern Kaffee mit Milch.", 3),
        OPEN("speak", "sp", "Sprechen Teil 3",
             "Sie sind im Café und möchten die Speisekarte: bitten Sie höflich. Antworten Sie dann auf die Bitte: "
             "„Können Sie bitte das Fenster öffnen?“",
             "Goethe A1 Sprechen Teil 3: one polite request, one fitting reply to a request.",
             "Entschuldigung, kann ich bitte die Speisekarte haben? - Ja, gern. Einen Moment, bitte.", 3),
    ],
}

# ----------------------------------------------------------------------------- IELTS
_L1 = ("Good morning, City Library, how can I help? Hi, I'd like to join the library. Of course. Can I take your "
       "surname? It's Marlowe. M, A, R, L, O, W, E. Thank you. Membership is free for residents, but there is a charge "
       "of two pounds fifty if you lose your card. You can borrow up to twelve books at a time, for three weeks.")
_L2 = ("Welcome to Greenfield Sports Centre. The swimming pool is on the ground floor, next to the cafe. The gym is "
       "upstairs and opens at six thirty every morning. Yoga classes take place on Tuesday and Thursday evenings, and "
       "you must book them online at least one day in advance. Please note that the car park behind the building is "
       "closed this month for repairs, so use the street parking on Mill Road.")
_READ = ("Urban beekeeping has grown rapidly over the past two decades. In London alone, the number of registered hives "
         "more than doubled between 2008 and 2018. Supporters argue that cities can be surprisingly good places for "
         "honeybees: parks, gardens and railway embankments offer a wide variety of flowering plants, and urban areas "
         "are often warmer than the surrounding countryside, which lengthens the foraging season.\n\n"
         "However, some ecologists have begun to question whether more hives are always better. Honeybees are only one "
         "of several hundred bee species found in Britain, and most of the others are wild, solitary bees that do not "
         "live in hives. When too many honeybee colonies are placed in a small area, they may compete with these wild "
         "species for nectar and pollen. A study of city sites found fewer wild bees in places where hive numbers were "
         "highest, although the researchers noted that other factors, such as the amount of green space, could also "
         "explain the pattern.\n\n"
         "For this reason, several conservation groups now advise people who want to help pollinators to plant flowers "
         "rather than buy a hive. Beekeeping associations, meanwhile, stress that well-trained keepers remain "
         "valuable, because they monitor bee health and can report diseases early.")
_TFN = "True, False or Not Given?"
_W_RUB = ("IELTS Writing band descriptors: Task Achievement/Response, Coherence and Cohesion, Lexical Resource, "
          "Grammatical Range and Accuracy. Give a band from 0 to 9. Penalise answers under the word minimum.")
_S_RUB = ("IELTS Speaking band descriptors applied to a transcript: Fluency and Coherence, Lexical Resource, "
          "Grammatical Range and Accuracy (pronunciation cannot be judged from text). Give a band from 0 to 9.")

IELTS = {
    "id": "en-ielts", "title": "IELTS mock test", "minutes": 60,
    "note": "Compact mock with all four sections. Listening is read by your phone's English voice. Writing uses "
            "the General Training letter for Task 1. Writing and Speaking are given a band by the Examiner agent.",
    "questions": [
        TXT("li", "Listening Part 1", "Complete the form. Surname:", ["marlowe"], say=_L1),
        M("li", "Listening Part 1", "The charge for a lost card is", ["£2.50", "£2.15", "£12.50"], say=_L1),
        TXT("li", "Listening Part 1", "Maximum number of books (write a number):", ["12", "twelve"], say=_L1),
        M("li", "Listening Part 1", "Books can be borrowed for", ["three weeks", "two weeks", "twelve days"], say=_L1),
        M("li", "Listening Part 2", "Where is the swimming pool?",
          ["On the ground floor, next to the cafe", "Upstairs", "Behind the building"], say=_L2),
        TXT("li", "Listening Part 2", "The gym opens at (time):",
            ["6.30", "6:30", "630", "six thirty", "half past six", "6.30 am", "6:30 am", "6.30am", "6:30am"], say=_L2),
        M("li", "Listening Part 2", "Yoga classes must be booked",
          ["online, at least a day ahead", "at reception on the day", "by phone"], say=_L2),
        M("li", "Listening Part 2", "Why can't visitors use the car park?",
          ["It is closed for repairs", "It is full", "It is for members only"], say=_L2),
        M("rd", "Reading: True / False / Not Given",
          _TFN + "\n'The number of registered hives in London fell between 2008 and 2018.'",
          ["False", "True", "Not Given"], _READ),
        M("rd", "Reading: True / False / Not Given", _TFN + "\n'Cities are often warmer than nearby rural areas.'",
          ["True", "False", "Not Given"], _READ),
        M("rd", "Reading: True / False / Not Given", _TFN + "\n'Most British bee species live in hives.'",
          ["False", "True", "Not Given"], _READ),
        M("rd", "Reading: True / False / Not Given",
          _TFN + "\n'Urban honey sells for a higher price than rural honey.'", ["Not Given", "True", "False"], _READ),
        M("rd", "Reading: multiple choice", "According to some ecologists, too many hives in a small area may",
          ["leave wild bees with less food", "spread into the countryside", "reduce the number of flowers",
           "make cities warmer"], _READ),
        M("rd", "Reading: multiple choice", "Conservation groups advise people who want to help pollinators to",
          ["plant flowers", "buy a hive", "join a beekeeping association", "report bee diseases"], _READ),
        TXT("rd", "Reading: sentence completion",
            "Complete with ONE WORD from the passage:\nUrban warmth lengthens the ______ season.", ["foraging"], _READ),
        TXT("rd", "Reading: sentence completion",
            "Complete with ONE WORD from the passage:\nTrained keepers can report ______ early.", ["diseases", "disease"],
            _READ),
        OPEN("write", "wr", "Writing Task 1 (General Training)",
             "You recently bought a laptop online, but it arrived damaged. Write a letter to the company. In your "
             "letter:\n- give details of your order\n- explain what is wrong with the laptop\n- say what you would "
             "like the company to do\nWrite at least 150 words.", _W_RUB,
             "Dear Sir or Madam,\nI am writing to complain about a laptop that I ordered from your website on 3 March "
             "(order number 48213). The laptop was delivered yesterday, but unfortunately it arrived damaged. When I "
             "opened the box, I found a large crack across the screen, and the device will not switch on. The outer "
             "packaging was also torn, which suggests it was handled carelessly in transit. I need this laptop for my "
             "work, so this has caused me considerable inconvenience. I would be grateful if you could send a "
             "replacement as soon as possible and arrange for the damaged laptop to be collected at no cost to me. If "
             "a replacement is not available within a week, I would like a full refund. I have attached photographs "
             "of the damage and a copy of my receipt. I look forward to hearing from you soon.\nYours faithfully,\n"
             "R. Kumar", 9, min_words=150),
        OPEN("write", "wr", "Writing Task 2",
             "Some people think that young people should spend their free time doing organised activities such as "
             "sports clubs. Others believe they should be free to choose how they spend it. Discuss both views and "
             "give your own opinion. Write at least 250 words.", _W_RUB,
             "A strong answer has four paragraphs: an introduction that paraphrases the question and states a "
             "position; one paragraph on the benefits of organised activities (teamwork, discipline, health) with an "
             "example; one paragraph on free choice (creativity, independence, rest) with an example; and a "
             "conclusion that repeats the position, for example that a balance of both is best.", 18, min_words=250),
        OPEN("speak", "sp", "Speaking Part 1",
             "Let's talk about where you live. Do you live in a house or a flat? What do you like about the area?",
             _S_RUB, "I live in a small flat near the city centre. What I like most is that everything is close: I "
                     "can walk to work in ten minutes, and there is a park nearby where I go running.", 9),
        OPEN("speak", "sp", "Speaking Part 2",
             "Describe a skill you would like to learn. You should say: what the skill is, why you want to learn it, "
             "how you would learn it, and explain how it would change your life. Speak for one to two minutes.",
             _S_RUB, "I'd like to talk about learning to cook properly. The reason I chose this is that I eat out too "
                     "often, which is expensive and not very healthy. I would start with online videos and then take "
                     "a weekend class. Looking back in a year, I think it would save me money and make me more "
                     "independent.", 9),
        OPEN("speak", "sp", "Speaking Part 3",
             "Do you think schools should teach practical skills such as cooking and managing money? Why or why not?",
             _S_RUB, "I tend to think they should. One reason is that many young people leave home without knowing "
                     "how to budget. Having said that, schools already have a full timetable, so it may need to "
                     "replace something else.", 9),
    ],
}

MOCKS = {"ja-n5": N5, "de-a1": A1, "en-ielts": IELTS}
