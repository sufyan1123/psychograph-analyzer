"""
DSM-5 Diagnostic Assessment Module
Analyzes chat conversations against DSM-5 diagnostic criteria
and provides evidence-based diagnosis recommendations.
"""

import re
from typing import Dict, List, Tuple

# ── DSM-5 Diagnostic Criteria Database ────────────────────────────────────────
# This contains the major diagnostic criteria from DSM-5
# Each entry includes: criteria text, DSM-5 page reference, and indicators to look for

DSM5_CRITERIA = {
    "Panic Disorder": {
        "dsm_page": 208,
        "pdf_page": 250,
        "section": "Anxiety Disorders",
        "criteria_count_required": 4,
        "duration": "At least 1 month of concern or behavioral change following at least one attack",
        "criteria": {
            "A": {
                "text": "Recurrent unexpected panic attacks. A panic attack is an abrupt surge of intense fear or intense discomfort that reaches a peak within minutes, and during which time four (or more) of the following symptoms occur:",
                "indicators": ["came out of nowhere", "hit me out of the blue", "happened for no reason", "wasn't even stressed when it started", "random attack", "just happened suddenly", "no warning"]
            },
            "A1": {
                "text": "Palpitations, pounding heart, or accelerated heart rate",
                "indicators": ["heart was racing", "felt like my heart was gonna explode", "heart pounding out of my chest", "heart beating so fast", "heart was going crazy", "could feel my heartbeat in my throat", "heart skipping beats", "heart wouldn't slow down"]
            },
            "A2": {
                "text": "Sweating",
                "indicators": ["drenched in sweat", "sweating like crazy", "palms were so sweaty", "broke out in a cold sweat", "sweating for no reason", "soaked through my shirt", "sweating bullets"]
            },
            "A3": {
                "text": "Trembling or shaking",
                "indicators": ["couldn't stop shaking", "my hands were trembling", "whole body was shaking", "legs were like jelly", "shaky af", "trembling so bad", "couldn't hold anything steady", "vibrating inside"]
            },
            "A4": {
                "text": "Sensations of shortness of breath or smothering",
                "indicators": ["couldn't breathe", "felt like i was suffocating", "couldn't catch my breath", "felt like something was on my chest", "gasping for air", "couldn't get enough air", "felt like i was choking", "breathing felt impossible", "air wouldn't go in"]
            },
            "A5": {
                "text": "Feelings of choking",
                "indicators": ["throat was closing up", "felt like i was being strangled", "something stuck in my throat", "couldn't swallow", "throat felt tight", "like hands around my neck", "choking feeling"]
            },
            "A6": {
                "text": "Chest pain or discomfort",
                "indicators": ["chest was hurting", "thought i was having a heart attack", "pressure in my chest", "chest felt tight", "pain in my chest", "chest was crushing", "felt like an elephant on my chest", "stabbing pain in my heart"]
            },
            "A7": {
                "text": "Nausea or abdominal distress",
                "indicators": ["felt like i was gonna throw up", "stomach was in knots", "felt sick to my stomach", "nauseous af", "stomach dropped", "felt like i was gonna puke", "gut was churning", "butterflies on steroids"]
            },
            "A8": {
                "text": "Feeling dizzy, unsteady, light-headed, or faint",
                "indicators": ["felt like i was gonna pass out", "room was spinning", "so dizzy", "lightheaded", "everything went fuzzy", "felt faint", "legs were gonna give out", "head was swimming", "almost blacked out"]
            },
            "A9": {
                "text": "Chills or heat sensations",
                "indicators": ["got so hot suddenly", "chills all over", "felt like i was on fire", "hot flash out of nowhere", "freezing and sweating at the same time", "waves of heat", "body went cold", "burning up"]
            },
            "A10": {
                "text": "Paresthesias (numbness or tingling sensations)",
                "indicators": ["hands went numb", "tingling all over", "pins and needles", "face went numb", "couldn't feel my fingers", "weird tingling feeling", "arms felt dead", "numbness spreading"]
            },
            "A11": {
                "text": "Derealization (feelings of unreality) or depersonalization (being detached from oneself)",
                "indicators": ["felt like i wasn't real", "everything seemed fake", "felt like i was in a dream", "watching myself from outside", "nothing felt real", "felt disconnected from my body", "like i was floating away", "world looked weird", "felt like a movie", "out of body experience"]
            },
            "A12": {
                "text": "Fear of losing control or 'going crazy'",
                "indicators": ["thought i was losing my mind", "felt like i was going crazy", "scared i was gonna lose it", "thought i was going insane", "felt like i was gonna snap", "losing my grip on reality", "thought i was having a breakdown", "scared i'd do something crazy"]
            },
            "A13": {
                "text": "Fear of dying",
                "indicators": ["thought i was dying", "was sure i was gonna die", "felt like this was the end", "thought i was having a heart attack", "convinced i was dying", "texted goodbye to everyone", "called 911 cause i thought i was dying", "made peace with death", "this is it im dying"]
            },
            "B1": {
                "text": "Persistent concern or worry about additional panic attacks or their consequences (e.g., losing control, having a heart attack, 'going crazy')",
                "indicators": ["keep waiting for the next one", "scared its gonna happen again", "what if i have another one", "always worried itll come back", "cant stop thinking about when the next attack will hit", "living in fear of another episode", "constantly on edge waiting", "dreading having another one", "obsessing over when itll happen again"]
            },
            "B2": {
                "text": "Significant maladaptive change in behavior related to the attacks (e.g., behaviors designed to avoid having panic attacks, such as avoidance of exercise or unfamiliar situations)",
                "indicators": ["stopped going out", "wont go anywhere alone anymore", "avoid places where it happened", "cant drive anymore", "stopped exercising cause it triggers it", "wont go to the mall", "stay home all the time now", "need someone with me always", "cant take the subway anymore", "planning escape routes everywhere", "always sit near exits", "stopped drinking coffee"]
            },
            "C": {
                "text": "The disturbance is not attributable to the physiological effects of a substance (e.g., a drug of abuse, a medication) or another medical condition (e.g., hyperthyroidism, cardiopulmonary disorders)",
                "indicators": ["not on any drugs", "wasnt drinking or anything", "docs say my heart is fine", "all my tests came back normal", "its not medical", "thyroid is fine", "not from caffeine"]
            },
            "D": {
                "text": "The disturbance is not better explained by another mental disorder (e.g., the panic attacks do not occur only in response to feared social situations, as in social anxiety disorder; in response to circumscribed phobic objects or situations, as in specific phobia; in response to obsessions, as in obsessive-compulsive disorder; in response to reminders of traumatic events, as in posttraumatic stress disorder; or in response to separation from attachment figures, as in separation anxiety disorder)",
                "indicators": ["happens randomly not just in social situations", "not triggered by anything specific", "comes out of nowhere", "not related to my trauma", "not just when im away from home", "no pattern to when it happens"]
            },
        }
    },
    "Social Anxiety Disorder": {
        "dsm_page": 202,
        "pdf_page": 244,
        "section": "Anxiety Disorders",
        "criteria_count_required": 10,
        "duration": "6 months or more",
        "criteria": {
            "A": {
                "text": "Marked fear or anxiety about one or more social situations in which the individual is exposed to possible scrutiny by others. Examples include social interactions (e.g., having a conversation, meeting unfamiliar people), being observed (e.g., eating or drinking), and performing in front of others (e.g., giving a speech).",
                "indicators": ["hate being around people", "scared to talk to new people", "can't eat in front of others", "terrified of presentations", "freak out meeting strangers", "don't want anyone watching me", "can't handle parties", "avoid eye contact", "dread small talk", "panic when i have to speak up"]
            },
            "B": {
                "text": "The individual fears that he or she will act in a way or show anxiety symptoms that will be negatively evaluated (i.e., will be humiliating or embarrassing; will lead to rejection or offend others).",
                "indicators": ["everyone will think im weird", "they'll see me shaking", "scared ill embarrass myself", "what if i say something stupid", "they'll notice im nervous", "people will judge me", "afraid ill blush", "dont want to look like an idiot", "they'll think im a freak", "scared of being rejected"]
            },
            "C": {
                "text": "The social situations almost always provoke fear or anxiety.",
                "indicators": ["every single time i panic", "always get anxious around people", "never get used to it", "happens literally every time", "cant remember not being scared", "its always like this", "without fail i freak out", "social stuff always triggers me", "every party same thing", "always been this way"]
            },
            "D": {
                "text": "The social situations are avoided or endured with intense fear or anxiety.",
                "indicators": ["i just dont go anymore", "skip everything social", "forced myself but died inside", "make excuses to stay home", "ghosted the party", "had to leave early", "white knuckled through it", "couldnt make myself go", "ditched plans again", "survived but barely"]
            },
            "E": {
                "text": "The fear or anxiety is out of proportion to the actual threat posed by the social situation and to the sociocultural context.",
                "indicators": ["i know its dumb but", "logically it makes no sense", "its just coffee but i cant", "people do this every day", "shouldnt be this hard", "its not even a big deal but", "normal people dont stress this", "i overreact i know", "my brain makes it worse than it is", "rationally i get it but still"]
            },
            "F": {
                "text": "The fear, anxiety, or avoidance is persistent, typically lasting for 6 months or more.",
                "indicators": ["been like this for years", "since high school", "as long as i can remember", "its been months now", "not getting any better", "always been shy like this", "struggled with this forever", "never goes away", "whole life basically", "at least a year now"]
            },
            "G": {
                "text": "The fear, anxiety, or avoidance causes clinically significant distress or impairment in social, occupational, or other important areas of functioning.",
                "indicators": ["ruining my life", "cant make friends", "failing classes cuz presentations", "turned down the job", "have no social life", "missing out on everything", "relationship problems from this", "cant network for work", "grades suffering", "so lonely because of this"]
            },
            "H": {
                "text": "The fear, anxiety, or avoidance is not attributable to the physiological effects of a substance (e.g., a drug of abuse, a medication) or another medical condition.",
                "indicators": ["not on anything", "sober and still anxious", "happens without caffeine too", "not my meds causing it", "was like this before i started anything", "even when im clean", "no substances involved", "its just me not drugs", "doctor ruled out medical stuff", "not a side effect"]
            },
            "I": {
                "text": "The fear, anxiety, or avoidance is not better explained by the symptoms of another mental disorder, such as panic disorder, body dysmorphic disorder, or autism spectrum disorder.",
                "indicators": ["its specifically social stuff", "only around people", "not random panic attacks", "its about being judged", "not about how i look exactly", "fine when im alone", "only triggered by social situations", "people are the problem", "not general anxiety just social", "specifically about others watching"]
            },
            "J": {
                "text": "If another medical condition (e.g., Parkinson's disease, obesity, disfigurement from burns or injury) is present, the fear, anxiety, or avoidance is clearly unrelated or is excessive.",
                "indicators": ["its not about my condition", "even before the accident", "way more than makes sense", "others with same thing are fine", "excessive for what i have", "not just about that", "goes beyond whats normal", "disproportionate to my situation", "started before any health stuff", "cant blame it on that"]
            },
        }
    },
    "Specific Phobia": {
        "dsm_page": 197,
        "pdf_page": 239,
        "section": "Anxiety Disorders",
        "criteria_count_required": 7,
        "duration": "6 months or more",
        "criteria": {
            "A": {
                "text": "Marked fear or anxiety about a specific object or situation (e.g., flying, heights, animals, receiving an injection, seeing blood).",
                "indicators": ["i'm terrified of", "can't even look at", "freaks me out so bad", "i literally cannot handle", "makes me want to scream", "i have this thing about", "scared to death of", "gives me the creeps", "i panic when i see", "absolutely horrified by"]
            },
            "B": {
                "text": "The phobic object or situation almost always provokes immediate fear or anxiety.",
                "indicators": ["every single time i see one", "always makes me freak out", "instant panic mode", "the second i see it", "immediately start sweating", "my heart races right away", "can't help it it just happens", "without fail i lose it", "triggers me every time", "never fails to scare me"]
            },
            "C": {
                "text": "The phobic object or situation is actively avoided or endured with intense fear or anxiety.",
                "indicators": ["i go out of my way to avoid", "won't go anywhere near", "had to leave because", "i just can't be around", "refuse to go if there's", "i'll take the long way to avoid", "white knuckled through it", "forced myself but dying inside", "literally ran away from", "i'd rather die than"]
            },
            "D": {
                "text": "The fear or anxiety is out of proportion to the actual danger posed by the specific object or situation and to the sociocultural context.",
                "indicators": ["i know it's dumb but", "people think i'm crazy", "it's irrational i know", "logically i know it won't hurt me", "everyone says i'm overreacting", "i feel so stupid about it", "makes no sense but still", "sounds ridiculous but", "i know it's not that serious but", "even tiny ones freak me out"]
            },
            "E": {
                "text": "The fear, anxiety, or avoidance is persistent, typically lasting for 6 months or more.",
                "indicators": ["been like this forever", "ever since i was a kid", "had this fear for years", "it's always been this way", "never gotten over it", "been dealing with this so long", "for as long as i can remember", "it's not going away", "still just as bad as before", "years later and still can't"]
            },
            "F": {
                "text": "The fear, anxiety, or avoidance causes clinically significant distress or impairment in social, occupational, or other important areas of functioning.",
                "indicators": ["it's ruining my life", "can't take that job because", "missed out on so much", "it's affecting my relationship", "had to cancel plans again", "can't live normally because", "holding me back from", "feel like such a burden", "embarrassed to tell people", "limits everything i do"]
            },
            "G": {
                "text": "The disturbance is not better explained by the symptoms of another mental disorder, including fear, anxiety, and avoidance of situations associated with panic-like symptoms or other incapacitating symptoms; objects or situations related to obsessions; reminders of traumatic events; separation from home or attachment figures; or social situations.",
                "indicators": ["it's just this one thing", "only happens with", "everything else is fine", "specifically about", "not anxious about other stuff", "only when it comes to", "this is my only issue", "nothing else bothers me like this"]
            },
        }
    },
    "Separation Anxiety Disorder": {
        "dsm_page": 190,
        "pdf_page": 232,
        "section": "Anxiety Disorders",
        "criteria_count_required": 3,
        "duration": "at least 4 weeks in children/adolescents, typically 6 months or more in adults",
        "criteria": {
            "A1": {
                "text": "Recurrent excessive distress when anticipating or experiencing separation from home or from major attachment figures.",
                "indicators": ["freaking out because they're leaving", "can't stop crying when he goes", "panic when she has to go", "losing it every time they leave", "sobbing before they even left", "felt sick knowing he was going away", "couldn't handle saying goodbye", "meltdown when mom left for work", "chest gets tight when they mention leaving"]
            },
            "A2": {
                "text": "Persistent and excessive worry about losing major attachment figures or about possible harm to them, such as illness, injury, disasters, or death.",
                "indicators": ["what if something happens to them", "keep thinking they'll die", "scared they'll get in an accident", "can't stop worrying about mom", "terrified something bad will happen", "checking if they're okay constantly", "nightmare about losing them", "what if they don't come back", "obsessing over their safety", "afraid they'll get sick and die"]
            },
            "A3": {
                "text": "Persistent and excessive worry about experiencing an untoward event (e.g., getting lost, being kidnapped, having an accident, becoming ill) that causes separation from a major attachment figure.",
                "indicators": ["scared i'll get kidnapped", "what if i get lost", "afraid something will happen to me", "worried i'll get sick and be alone", "terrified of being taken away", "what if there's an accident and we're separated", "can't stop thinking about bad things happening to me", "fear of getting hurt when they're not here"]
            },
            "A4": {
                "text": "Persistent reluctance or refusal to go out, away from home, to school, to work, or elsewhere because of fear of separation.",
                "indicators": ["can't make myself go to school", "won't leave the house", "refuse to go anywhere without them", "skipping work to stay home", "can't do things alone anymore", "haven't left home in days", "won't go out unless they come", "staying home again today", "too scared to go anywhere by myself", "ditching plans because i can't leave"]
            },
            "A5": {
                "text": "Persistent and excessive fear of or reluctance about being alone or without major attachment figures at home or in other settings.",
                "indicators": ["hate being home alone", "can't be by myself", "terrified when they're not here", "need someone with me always", "follow them room to room", "panic when i'm alone", "can't handle being left alone", "freak out in empty house", "need them near me constantly", "scared to be without them"]
            },
            "A6": {
                "text": "Persistent reluctance or refusal to sleep away from home or to go to sleep without being near a major attachment figure.",
                "indicators": ["can't sleep unless they're here", "won't do sleepovers anymore", "need them in the room to sleep", "can't fall asleep alone", "sleeping in their bed again", "refuse to stay overnight anywhere", "have to sleep with door open to hear them", "can't sleep when they're out", "won't sleep at friend's house", "need to know they're home to sleep"]
            },
            "A7": {
                "text": "Repeated nightmares involving the theme of separation.",
                "indicators": ["keep having dreams they die", "nightmare about losing them again", "woke up crying from bad dream", "dreamed they abandoned me", "same scary dream about them leaving", "can't sleep because of the nightmares", "dream they disappeared", "having separation dreams every night", "nightmare they never came back"]
            },
            "A8": {
                "text": "Repeated complaints of physical symptoms (e.g., headaches, stomachaches, nausea, vomiting) when separation from major attachment figures occurs or is anticipated.",
                "indicators": ["stomach hurts when they leave", "get headaches before they go", "feel sick when they're gone", "threw up before school", "body aches when we're apart", "feel nauseous every morning", "tummy hurts don't wanna go", "get physically sick thinking about it", "head pounding when they left", "feel awful in my body when separated"]
            },
            "B": {
                "text": "The fear, anxiety, or avoidance is persistent, lasting at least 4 weeks in children and adolescents and typically 6 months or more in adults.",
                "indicators": ["been like this for months", "hasn't gotten better", "going on for weeks now", "this has been happening forever", "same thing every day for months", "been struggling with this all semester", "it's been this way since summer"]
            },
            "C": {
                "text": "The disturbance causes clinically significant distress or impairment in social, academic, occupational, or other important areas of functioning.",
                "indicators": ["failing classes because of this", "lost my job over it", "friends gave up on me", "can't function anymore", "ruining my relationship", "life is falling apart", "grades are tanking", "can't do normal stuff", "missing everything important", "it's affecting everything"]
            },
            "D": {
                "text": "The disturbance is not better explained by another mental disorder.",
                "indicators": []
            },
        }
    },
    "Agoraphobia": {
        "dsm_page": 217,
        "pdf_page": 259,
        "section": "Anxiety Disorders",
        "criteria_count_required": 12,
        "duration": "6 months or more",
        "criteria": {
            "A": {
                "text": "Marked fear or anxiety about two (or more) of the following five situations:",
                "indicators": []
            },
            "A1": {
                "text": "Using public transportation (e.g., automobiles, buses, trains, ships, planes)",
                "indicators": ["can't do buses anymore", "trains freak me out", "haven't been on a plane in years", "uber is the only way i can travel", "subway gives me panic attacks", "i avoid the metro completely", "can't handle public transit", "being stuck on a bus terrifies me", "flying is impossible for me now", "i need someone to drive me everywhere"]
            },
            "A2": {
                "text": "Being in open spaces (e.g., parking lots, marketplaces, bridges)",
                "indicators": ["parking lots are the worst", "can't cross bridges anymore", "open areas make me panic", "farmers markets are too much", "i hate big empty spaces", "stadiums terrify me", "walking across that plaza freaks me out", "fields make me feel so exposed", "beach is too open for me", "i avoid outdoor malls"]
            },
            "A3": {
                "text": "Being in enclosed places (e.g., shops, theaters, cinemas)",
                "indicators": ["can't go to movies anymore", "stores make me feel trapped", "malls are suffocating", "elevators are a no go", "i avoid theaters completely", "small shops freak me out", "can't handle crowded stores", "being inside buildings is hard", "restaurants feel too closed in", "i need to sit near the exit"]
            },
            "A4": {
                "text": "Standing in line or being in a crowd",
                "indicators": ["can't do lines anymore", "crowds make me lose it", "waiting in line is torture", "concerts are impossible now", "i avoid busy places", "standing in queues gives me anxiety", "crowded places are my nightmare", "i leave if there's a line", "festivals are way too much", "grocery store lines freak me out"]
            },
            "A5": {
                "text": "Being outside of the home alone",
                "indicators": ["can't leave the house alone", "need someone with me to go out", "going out by myself is terrifying", "i haven't left alone in months", "being outside alone triggers me", "i only go out if someone comes with", "walking alone is too scary", "i need a buddy to go anywhere", "can't even check the mail alone", "venturing out solo is impossible"]
            },
            "B": {
                "text": "The individual fears or avoids these situations because of thoughts that escape might be difficult or help might not be available in the event of developing panic-like symptoms or other incapacitating or embarrassing symptoms (e.g., fear of falling in the elderly; fear of incontinence)",
                "indicators": ["what if i can't get out", "no one would help me", "i'd be trapped", "what if i panic and can't escape", "i might pass out and no one would notice", "scared i'll embarrass myself", "what if i lose control", "i could faint and be stuck", "afraid i'll have an accident", "there's no quick exit", "what if something happens and i can't leave", "i'd be helpless"]
            },
            "C": {
                "text": "The agoraphobic situations almost always provoke fear or anxiety",
                "indicators": ["it happens every single time", "i always panic in those places", "without fail i freak out", "guaranteed anxiety attack", "100% of the time i get scared", "it never fails to trigger me", "always the same reaction", "can't remember not being scared there", "every time no exceptions", "consistently terrifying"]
            },
            "D": {
                "text": "The agoraphobic situations are actively avoided, require the presence of a companion, or are endured with intense fear or anxiety",
                "indicators": ["i just don't go anymore", "my friend has to come with me", "i white knuckle through it", "completely avoiding those places now", "only if someone holds my hand", "i suffer through it but barely", "i've stopped going altogether", "need my partner there or forget it", "i push through but i'm dying inside", "haven't been there in forever"]
            },
            "E": {
                "text": "The fear or anxiety is out of proportion to the actual danger posed by the agoraphobic situations and to the sociocultural context",
                "indicators": ["i know it's irrational but", "logically nothing bad would happen", "it makes no sense but i'm terrified", "everyone else is fine there", "i know it's safe but still", "my brain knows better but my body doesn't", "objectively there's no danger", "it's dumb but i can't help it", "rationally i get it but emotionally nope", "seems crazy but it feels real"]
            },
            "F": {
                "text": "The fear, anxiety, or avoidance is persistent, typically lasting for 6 months or more",
                "indicators": ["been like this for years", "it's been months of this", "this isn't new", "i've struggled with this forever", "going on almost a year now", "hasn't gotten better in ages", "been dealing with this since last year", "it's a long term thing", "this has been my life for a while", "not a recent thing at all"]
            },
            "G": {
                "text": "The fear, anxiety, or avoidance causes clinically significant distress or impairment in social, occupational, or other important areas of functioning",
                "indicators": ["i lost my job because of this", "my relationships are suffering", "can't live a normal life", "it's ruining everything", "i'm basically housebound", "missing out on so much", "my life has gotten so small", "can't work anymore", "friends stopped inviting me", "i've missed so many events", "it's destroying my marriage", "quality of life is garbage"]
            },
        }
    },
    "Bipolar I Disorder": {
        "dsm_page": 123,
        "pdf_page": 165,
        "section": "Bipolar and Related Disorders",
        "criteria_count_required": 3,
        "duration": "Manic episode lasting at least 7 days (or any duration if hospitalization required)",
        "criteria": {
            "A": {
                "text": "A distinct period of abnormally and persistently elevated, expansive, or irritable mood and abnormally and persistently increased goal-directed activity or energy, lasting at least 7 days and present most of the day, nearly every day (or any duration if hospitalization is necessary).",
                "indicators": ["i feel like i can do anything", "on top of the world rn", "never felt this good in my life", "so hyped up lately", "everything is irritating me", "can't stop moving gotta stay busy", "feel like im vibrating with energy", "literally unstoppable", "been going nonstop for days", "i feel amazing but everyone says im being weird"]
            },
            "B1": {
                "text": "Inflated self-esteem or grandiosity",
                "indicators": ["im literally a genius", "i could be famous if i wanted", "no one understands how talented i am", "i have special powers", "im meant for great things", "people are jealous of me", "i could run this company better than anyone", "god chose me for something big", "im basically untouchable", "everyone else is so basic compared to me"]
            },
            "B2": {
                "text": "Decreased need for sleep (e.g., feels rested after only 3 hours of sleep)",
                "indicators": ["slept like 2 hours and feel amazing", "who needs sleep anyway", "havent slept in days but im fine", "sleep is for the weak lol", "so much energy dont need rest", "been up for 3 days straight", "cant sleep too many ideas", "why would i waste time sleeping", "4am and still going strong", "my body doesnt need sleep anymore"]
            },
            "B3": {
                "text": "More talkative than usual or pressure to keep talking",
                "indicators": ["sorry for all the texts lol", "cant stop talking rn", "i have so much to say", "everyone keeps telling me to shut up", "my thoughts are just flowing", "sorry im talking so much", "i keep interrupting people i cant help it", "words just keep coming out", "ive been going off all day", "nobody can keep up with me in conversation"]
            },
            "B4": {
                "text": "Flight of ideas or subjective experience that thoughts are racing",
                "indicators": ["my brain wont slow down", "thoughts going a million miles an hour", "cant keep track of all my ideas", "jumping from thought to thought", "my mind is racing", "so many ideas at once", "brain is on overdrive", "cant focus on one thing too many thoughts", "its like my head is spinning with ideas", "thoughts are all over the place rn"]
            },
            "B5": {
                "text": "Distractibility (i.e., attention too easily drawn to unimportant or irrelevant external stimuli), as reported or observed",
                "indicators": ["sorry what were we talking about", "keep getting distracted", "cant focus on anything for long", "every little thing catches my attention", "started 10 things finished nothing", "squirrel lol", "wait what was i saying", "my attention is everywhere", "cant sit still or concentrate", "everything is interesting rn"]
            },
            "B6": {
                "text": "Increase in goal-directed activity (either socially, at work or school, or sexually) or psychomotor agitation (i.e., purposeless non-goal-directed activity)",
                "indicators": ["started like 5 new projects today", "been cleaning the whole house at 3am", "cant stop doing stuff", "signed up for everything", "been so productive lately", "started a business today", "hooking up with everyone lol", "my sex drive is crazy high", "reorganized my entire life this week", "pacing around cant sit still"]
            },
            "B7": {
                "text": "Excessive involvement in activities that have a high potential for painful consequences (e.g., engaging in unrestrained buying sprees, sexual indiscretions, or foolish business investments)",
                "indicators": ["just spent my whole paycheck", "maxed out my credit cards oops", "bought a car on impulse", "made some risky decisions last night", "yolo spent everything", "slept with someone i shouldnt have", "quit my job because i dont need it", "invested everything in crypto", "drove way too fast felt amazing", "gonna regret this but dont care rn"]
            },
            "C": {
                "text": "The mood disturbance is sufficiently severe to cause marked impairment in social or occupational functioning or to necessitate hospitalization to prevent harm to self or others, or there are psychotic features.",
                "indicators": ["got fired because of how ive been acting", "my family wants me hospitalized", "people are scared of me rn", "ruined all my relationships this week", "seeing things that arent there", "hearing voices telling me im special", "friends staged an intervention", "everyone says im out of control", "almost got arrested", "people think im losing it"]
            },
            "D": {
                "text": "The episode is not attributable to the physiological effects of a substance (e.g., a drug of abuse, a medication, other treatment) or to another medical condition.",
                "indicators": ["havent taken anything i swear", "this isnt from drugs", "im completely sober", "not on any new meds", "this is just me", "doctor checked me out im healthy", "no substances involved", "been clean for months", "this came out of nowhere naturally", "nothing has changed except my mood"]
            },
        }
    },
    "Persistent Depressive Disorder (Dysthymia)": {
        "dsm_page": 168,
        "pdf_page": 210,
        "section": "Depressive Disorders",
        "criteria_count_required": 2,
        "duration": "2 years (1 year for children/adolescents)",
        "criteria": {
            "A": {
                "text": "Depressed mood for most of the day, for more days than not, as indicated by either subjective account or observation by others, for at least 2 years. Note: In children and adolescents, mood can be irritable and duration must be at least 1 year.",
                "indicators": ["always feel down", "never really happy", "been sad forever", "can't remember feeling good", "always in a bad mood", "constantly bummed out", "life's just gray", "haven't been happy in years", "always feeling blah", "perpetually sad"]
            },
            "B1": {
                "text": "Poor appetite or overeating",
                "indicators": ["never hungry anymore", "always stress eating", "food doesn't interest me", "eat my feelings", "can't stop snacking", "haven't had an appetite in forever", "either starving or stuffed", "eating is a chore", "comfort eating again", "no desire to eat"]
            },
            "B2": {
                "text": "Insomnia or hypersomnia",
                "indicators": ["sleep all the time", "can never sleep right", "always tired but can't sleep", "sleeping 12 hours and still exhausted", "up all night every night", "sleep is my escape", "haven't slept well in ages", "either can't sleep or sleep too much", "my sleep schedule is wrecked", "just want to stay in bed forever"]
            },
            "B3": {
                "text": "Low energy or fatigue",
                "indicators": ["always exhausted", "no energy ever", "constantly drained", "running on empty", "tired all the time for years", "zero motivation", "everything takes so much effort", "perpetually wiped out", "never have energy for anything", "exhausted just existing"]
            },
            "B4": {
                "text": "Low self-esteem",
                "indicators": ["i'm such a loser", "never good enough", "hate myself", "i'm worthless", "everyone's better than me", "can't do anything right", "i'm a failure", "don't deserve good things", "always been a disappointment", "what's wrong with me"]
            },
            "B5": {
                "text": "Poor concentration or difficulty making decisions",
                "indicators": ["can't focus on anything", "brain fog all the time", "can't make simple decisions", "mind always wandering", "can't think straight", "takes forever to decide anything", "concentration is shot", "spacing out constantly", "can't commit to choices", "my head's not in it"]
            },
            "B6": {
                "text": "Feelings of hopelessness",
                "indicators": ["what's the point", "nothing ever gets better", "this is just my life now", "given up hoping", "things won't change", "no light at the end", "accepted this is how it is", "stopped expecting good things", "why bother trying", "it's always gonna be like this"]
            },
            "C": {
                "text": "During the 2-year period (1 year for children or adolescents) of the disturbance, the individual has never been without the symptoms in Criteria A and B for more than 2 months at a time.",
                "indicators": ["it's been like this for years", "can't remember feeling different", "maybe a few good weeks here and there", "always comes back", "never fully goes away", "brief breaks but always returns", "this has been going on forever", "as long as i can remember", "persistent thing with me", "it's just how i am now"]
            },
            "D": {
                "text": "Criteria for a major depressive disorder may be continuously present for 2 years.",
                "indicators": ["sometimes it gets really bad", "have my really dark periods", "goes from bad to worse", "low is my baseline", "sometimes hit rock bottom", "worse episodes on top of this", "the bad times within the bad times", "depression on top of depression", "some months are unbearable", "dips even lower sometimes"]
            },
            "E": {
                "text": "There has never been a manic episode or a hypomanic episode, and criteria have never been met for cyclothymic disorder.",
                "indicators": ["never felt super high", "don't have up periods", "no manic phases", "just always down", "never feel amazing either", "no extreme highs", "consistently low not up and down", "don't cycle through moods", "steady state of blah", "no euphoric times"]
            },
            "F": {
                "text": "The disturbance is not better explained by a persistent schizoaffective disorder, schizophrenia, delusional disorder, or other specified or unspecified schizophrenia spectrum and other psychotic disorder.",
                "indicators": []
            },
            "G": {
                "text": "The symptoms are not attributable to the physiological effects of a substance (e.g., a drug of abuse, a medication) or another medical condition (e.g., hypothyroidism).",
                "indicators": []
            },
            "H": {
                "text": "The symptoms cause clinically significant distress or impairment in social, occupational, or other important areas of functioning.",
                "indicators": ["affecting my relationships", "can't keep up at work", "struggling to function", "hard to maintain friendships", "impacts everything i do", "can barely get through the day", "affecting my whole life", "can't be the friend i want to be", "work is suffering", "just getting by"]
            },
        }
    },
    "Cyclothymic Disorder": {
        "dsm_page": 139,
        "pdf_page": 181,
        "section": "Bipolar and Related Disorders",
        "criteria_count_required": 7,
        "duration": "At least 2 years (1 year for children/adolescents)",
        "criteria": {
            "A": {
                "text": "For at least 2 years (at least 1 year in children and adolescents) there have been numerous periods with hypomanic symptoms that do not meet criteria for a hypomanic episode and numerous periods with depressive symptoms that do not meet criteria for a major depressive episode.",
                "indicators": ["my moods are always up and down", "i cycle between feeling great and feeling low", "one week im on top of the world next week im sad", "my mood never stays the same for long", "im either really productive or cant do anything", "always been moody my whole life", "i swing between happy and depressed constantly", "some days i feel unstoppable other days i cant get out of bed", "my friends say im unpredictable", "been dealing with mood swings for years"]
            },
            "B": {
                "text": "During the above 2-year period (1 year in children and adolescents), the hypomanic and depressive periods have been present for at least half the time and the individual has not been without the symptoms for more than 2 months at a time.",
                "indicators": ["i cant remember the last time i felt normal", "theres never a break from this", "its been like this forever", "i dont know what stable even feels like", "maybe a few weeks of calm then it starts again", "its constant honestly", "i never get a real break from the ups and downs", "this has been going on nonstop", "cant catch a break from my moods"]
            },
            "C": {
                "text": "Criteria for a major depressive, manic, or hypomanic episode have never been met.",
                "indicators": ["its not like full on depression", "i dont think its bipolar bipolar", "never been hospitalized or anything", "its bad but not THAT bad", "i can still function mostly", "never had a complete breakdown", "its like bipolar lite or something", "not severe enough to be diagnosed with anything major"]
            },
            "D": {
                "text": "The symptoms in Criterion A are not better explained by schizoaffective disorder, schizophrenia, schizophreniform disorder, delusional disorder, or other specified or unspecified schizophrenia spectrum and other psychotic disorder.",
                "indicators": ["i dont hear voices or anything", "im not psychotic just moody", "no hallucinations just mood stuff", "its purely my mood not like seeing things", "i know whats real its just my emotions"]
            },
            "E": {
                "text": "The symptoms are not attributable to the physiological effects of a substance (e.g., a drug of abuse, a medication) or another medical condition (e.g., hyperthyroidism).",
                "indicators": ["this happens whether im drinking or not", "been like this before i started any meds", "not on anything that would cause this", "my thyroid is fine they checked", "this isnt from partying its just me", "sober or not im still like this"]
            },
            "hypomanic_indicators": {
                "text": "Periods of hypomanic symptoms (elevated mood, decreased need for sleep, increased energy, inflated self-esteem, talkativeness, racing thoughts, increased goal-directed activity)",
                "indicators": ["feeling myself lately", "dont need much sleep and im fine", "got so much energy rn", "started like 5 new projects this week", "feeling like i can do anything", "talking everyones ear off", "my mind is going a million miles an hour", "been super social and outgoing", "spending money like crazy but whatever", "everything feels possible rn"]
            },
            "depressive_indicators": {
                "text": "Periods of depressive symptoms (depressed mood, loss of interest, fatigue, feelings of worthlessness, difficulty concentrating)",
                "indicators": ["dont feel like doing anything", "whats the point", "so tired all the time now", "cant focus on anything", "feeling worthless again", "back to feeling low", "dont want to see anyone", "everything feels hard", "the sad phase is back", "just want to stay in bed"]
            },
        }
    },
    "Adjustment Disorders": {
        "dsm_page": 286,
        "pdf_page": 328,
        "section": "Trauma- and Stressor-Related Disorders",
        "criteria_count_required": 6,
        "duration": "Symptoms must occur within 3 months of stressor onset and not persist more than 6 months after stressor/consequences have terminated",
        "criteria": {
            "A": {
                "text": "The development of emotional or behavioral symptoms in response to an identifiable stressor(s) occurring within 3 months of the onset of the stressor(s).",
                "indicators": ["ever since the breakup i've been a mess", "after i got fired everything fell apart", "haven't been the same since we moved", "since my parents divorced i can't cope", "losing my job changed everything", "after the diagnosis i just shut down", "since the accident i'm not myself", "ever since they left me", "when i failed that class everything went downhill", "after the miscarriage nothing feels right"]
            },
            "B1": {
                "text": "Marked distress that is out of proportion to the severity or intensity of the stressor, taking into account the external context and the cultural factors that might influence symptom severity and presentation.",
                "indicators": ["i know it's dumb but i can't stop crying over it", "everyone says i'm overreacting but i can't help it", "it shouldn't affect me this much but it does", "i feel like i'm falling apart over something small", "people think i should be over it by now", "i know it's not that serious but i'm devastated", "why am i this messed up over something so minor", "i feel crazy for being this upset", "it's not like someone died but i feel like they did", "everyone else handled it fine but i'm a wreck"]
            },
            "B2": {
                "text": "Significant impairment in social, occupational, or other important areas of functioning.",
                "indicators": ["can't focus at work anymore", "i've been calling in sick constantly", "haven't seen my friends in weeks", "my grades are tanking", "i keep canceling plans with everyone", "can't even do basic stuff anymore", "i'm gonna get fired at this rate", "stopped going to class", "my relationships are falling apart", "can't function like a normal person"]
            },
            "C": {
                "text": "The stress-related disturbance does not meet the criteria for another mental disorder and is not merely an exacerbation of a preexisting mental disorder.",
                "indicators": ["i've never felt like this before", "this isn't my usual anxiety", "i was fine before this happened", "this is different from my normal stuff", "never had mental health issues until now", "this isn't like my regular depression", "i was doing great before all this", "something new is wrong with me", "this feels different than before"]
            },
            "D": {
                "text": "The symptoms do not represent normal bereavement.",
                "indicators": ["it's not like someone died", "this isn't grief exactly", "nobody passed away but i feel like mourning", "it's not a death thing", "i didn't lose anyone to death", "this is different from when grandma died", "not grieving a death just everything else"]
            },
            "E": {
                "text": "Once the stressor or its consequences have terminated, the symptoms do not persist for more than an additional 6 months.",
                "indicators": ["it's been a few months and still struggling", "thought i'd be better by now", "when will this end", "still not over it", "how long is this gonna last", "it's getting a little better slowly", "some days are easier now", "starting to feel more normal again"]
            },
        }
    },
    "Obsessive-Compulsive Disorder": {
        "dsm_page": 237,
        "pdf_page": 279,
        "section": "Obsessive-Compulsive and Related Disorders",
        "criteria_count_required": 1,
        "duration": "Not specified, but symptoms must be time-consuming (more than 1 hour per day)",
        "criteria": {
            "A1": {
                "text": "Obsessions as defined by: (1) Recurrent and persistent thoughts, urges, or images that are experienced, at some time during the disturbance, as intrusive and unwanted, and that in most individuals cause marked anxiety or distress. (2) The individual attempts to ignore or suppress such thoughts, urges, or images, or to neutralize them with some other thought or action (i.e., by performing a compulsion).",
                "indicators": ["can't stop thinking about it", "these thoughts won't go away", "my brain won't shut up", "keeps popping into my head", "i know it's irrational but", "the thought keeps coming back", "intrusive thoughts are killing me", "can't get it out of my mind", "my mind is torturing me", "horrible thoughts i can't control"]
            },
            "A2": {
                "text": "Compulsions as defined by: (1) Repetitive behaviors (e.g., hand washing, ordering, checking) or mental acts (e.g., praying, counting, repeating words silently) that the individual feels driven to perform in response to an obsession or according to rules that must be applied rigidly. (2) The behaviors or mental acts are aimed at preventing or reducing anxiety or distress, or preventing some dreaded event or situation; however, these behaviors or mental acts are not connected in a realistic way with what they are designed to neutralize or prevent, or are clearly excessive.",
                "indicators": ["had to check the door like 10 times", "can't stop washing my hands", "have to do it a certain number of times", "doesn't feel right unless i do it", "stuck in a loop doing the same thing", "spent an hour just checking stuff", "have to count everything", "can't leave until everything is perfect", "keep going back to make sure", "if i don't do it something bad will happen"]
            },
            "B": {
                "text": "The obsessions or compulsions are time-consuming (e.g., take more than 1 hour per day) or cause clinically significant distress or impairment in social, occupational, or other important areas of functioning.",
                "indicators": ["this is taking over my life", "i was late again because of my rituals", "spent hours on this stupid thing", "can't function normally anymore", "it's ruining my relationships", "missed work because of this", "takes me forever to get ready", "can't do normal things like everyone else", "losing so much time to this", "my whole day revolves around it"]
            },
            "C": {
                "text": "The obsessive-compulsive symptoms are not attributable to the physiological effects of a substance (e.g., a drug of abuse, a medication) or another medical condition.",
                "indicators": ["not on anything that would cause this", "been like this even when i'm sober", "no meds or drugs involved", "this started on its own", "doctors ruled out medical stuff"]
            },
            "D": {
                "text": "The disturbance is not better explained by the symptoms of another mental disorder (e.g., excessive worries, as in generalized anxiety disorder; preoccupation with appearance, as in body dysmorphic disorder; difficulty discarding or parting with possessions, as in hoarding disorder; hair pulling, as in trichotillomania; skin picking, as in excoriation disorder; stereotypies, as in stereotypic movement disorder; ritualized eating behavior, as in eating disorders; preoccupation with substances or gambling, as in substance-related and addictive disorders; preoccupation with having an illness, as in illness anxiety disorder; sexual urges or fantasies, as in paraphilic disorders; impulses, as in disruptive, impulse-control, and conduct disorders; guilty ruminations, as in major depressive disorder; thought insertion or delusional preoccupations, as in schizophrenia spectrum and other psychotic disorders; or repetitive patterns of behavior, as in autism spectrum disorder).",
                "indicators": ["it's not just worry it's specific thoughts", "not about my looks or weight", "different from regular anxiety", "it's the rituals that are the problem", "not about hoarding or collecting", "specific obsessions not general stress"]
            },
        }
    },
    "Body Dysmorphic Disorder": {
        "dsm_page": 242,
        "pdf_page": 284,
        "section": "Obsessive-Compulsive and Related Disorders",
        "criteria_count_required": 4,
        "duration": "none specified",
        "criteria": {
            "A": {
                "text": "Preoccupation with one or more perceived defects or flaws in physical appearance that are not observable or appear slight to others.",
                "indicators": ["i look so ugly", "my nose is huge", "can't stop staring at my face in the mirror", "everyone can see how gross i look", "my skin is disgusting", "i hate my face so much", "why do i look like this", "my [body part] is deformed", "i look like a monster", "nobody else has a face this ugly"]
            },
            "B": {
                "text": "At some point during the course of the disorder, the individual has performed repetitive behaviors (e.g., mirror checking, excessive grooming, skin picking, reassurance seeking) or mental acts (e.g., comparing his or her appearance with that of others) in response to the appearance concerns.",
                "indicators": ["spent hours doing my makeup and still look bad", "keep checking myself in every mirror", "do i look okay be honest", "comparing myself to everyone on ig", "picked at my skin again", "changed my outfit like ten times", "need you to tell me if this looks weird", "can't leave until my hair is perfect", "always looking at other people's faces", "took 200 selfies and deleted all of them"]
            },
            "C": {
                "text": "The preoccupation causes clinically significant distress or impairment in social, occupational, or other important areas of functioning.",
                "indicators": ["can't go out looking like this", "called in sick bc i look too ugly today", "cancelled plans again", "haven't left my room in days", "can't focus on anything except how i look", "i don't want anyone to see me", "skipped class bc of my face", "crying over how ugly i am", "this is ruining my life", "too embarrassed to show my face"]
            },
            "D": {
                "text": "The appearance preoccupation is not better explained by concerns with body fat or weight in an individual whose symptoms meet diagnostic criteria for an eating disorder.",
                "indicators": ["it's not about my weight", "i don't care about being thin", "it's my actual face that's the problem", "this isn't about food or eating", "my features are wrong not my size", "it's my bone structure", "being skinny won't fix my face", "this is about how deformed i look"]
            },
        }
    },
    "Hoarding Disorder": {
        "dsm_page": 247,
        "pdf_page": 289,
        "section": "Obsessive-Compulsive and Related Disorders",
        "criteria_count_required": 4,
        "duration": "persistent",
        "criteria": {
            "A": {
                "text": "Persistent difficulty discarding or parting with possessions, regardless of their actual value.",
                "indicators": ["i can't throw anything away", "might need it someday", "i just can't get rid of stuff", "everything has sentimental value", "what if i need it later", "it feels wrong to throw things out", "i keep everything just in case", "can't bring myself to toss it", "feels like losing a part of me", "i've had this forever can't let go"]
            },
            "B": {
                "text": "This difficulty is due to a perceived need to save the items and to distress associated with discarding them.",
                "indicators": ["it stresses me out to throw stuff away", "i feel anxious when i try to clean out", "what if i regret getting rid of it", "i get so upset thinking about tossing things", "it feels wasteful to throw away", "i panic when someone touches my stuff", "i need to keep it safe", "gets me really worked up to declutter", "feels like i'm abandoning it", "my heart races when i try to purge"]
            },
            "C": {
                "text": "The difficulty discarding possessions results in the accumulation of possessions that congest and clutter active living areas and substantially compromises their intended use. If living areas are uncluttered, it is only because of the interventions of third parties (e.g., family members, cleaners, authorities).",
                "indicators": ["my place is so full i can barely walk", "can't use my kitchen table anymore", "stuff is piled everywhere", "no room to sit on the couch", "my bedroom is basically storage now", "can't have anyone over it's embarrassing", "paths through my apartment lol", "my parents came and cleaned it out", "landlord threatened me about the mess", "sleeping on a tiny corner of my bed"]
            },
            "D": {
                "text": "The hoarding causes clinically significant distress or impairment in social, occupational, or other important areas of functioning (including maintaining a safe environment for self and others).",
                "indicators": ["i'm so ashamed of how i live", "haven't had friends over in years", "my family won't visit anymore", "it's affecting my relationship", "i'm scared of a fire hazard", "can't find important stuff when i need it", "lost my deposit because of the mess", "too embarrassed to date anyone", "my kids can't play in their room", "constantly stressed about the clutter"]
            },
            "E": {
                "text": "The hoarding is not attributable to another medical condition (e.g., brain injury, cerebrovascular disease, Prader-Willi syndrome).",
                "indicators": ["been like this my whole life", "no head injuries or anything", "doctors say nothing's wrong with my brain", "always been a collector type", "runs in my family honestly", "not a medical thing just how i am"]
            },
            "F": {
                "text": "The hoarding is not better explained by the symptoms of another mental disorder (e.g., obsessions in obsessive-compulsive disorder, decreased energy in major depressive disorder, delusions in schizophrenia or another psychotic disorder, cognitive deficits in major neurocognitive disorder, restricted interests in autism spectrum disorder).",
                "indicators": ["it's not about contamination or anything", "i actually want the stuff not just keeping it", "not too depressed to clean just can't let go", "i know the stuff isn't special to anyone else", "it's not a compulsion thing", "i genuinely love my collections"]
            },
        }
    },
    "Anorexia Nervosa": {
        "dsm_page": 338,
        "pdf_page": 380,
        "section": "Feeding and Eating Disorders",
        "criteria_count_required": 3,
        "duration": "No specific duration required, but pattern of behavior must be persistent",
        "criteria": {
            "A": {
                "text": "Restriction of energy intake relative to requirements, leading to a significantly low body weight in the context of age, sex, developmental trajectory, and physical health. Significantly low weight is defined as a weight that is less than minimally normal or, for children and adolescents, less than that minimally expected.",
                "indicators": ["barely eating anything", "skipped lunch again", "not hungry lately", "just had coffee for breakfast", "i'll eat later", "already ate earlier", "too full to eat", "cutting back on food", "only having a salad", "don't need that much food"]
            },
            "B": {
                "text": "Intense fear of gaining weight or of becoming fat, or persistent behavior that interferes with weight gain, even though at a significantly low weight.",
                "indicators": ["terrified of getting fat", "can't gain any weight", "freaking out about the scale", "scared to eat carbs", "if i eat that i'll blow up", "weighed myself like 5 times today", "panicking about weight", "cant stop thinking about calories", "feel disgusting when i eat", "one bite and i feel huge"]
            },
            "C": {
                "text": "Disturbance in the way in which one's body weight or shape is experienced, undue influence of body weight or shape on self-evaluation, or persistent lack of recognition of the seriousness of the current low body weight.",
                "indicators": ["still look so fat", "my thighs are huge", "need a thigh gap", "i'm fine i'm not that skinny", "everyone says i'm thin but i don't see it", "hate how my body looks", "feel enormous today", "my stomach is disgusting", "won't be happy until i'm smaller", "people are overreacting about my weight"]
            },
        }
    },
    "Bulimia Nervosa": {
        "dsm_page": 345,
        "pdf_page": 387,
        "section": "Feeding and Eating Disorders",
        "criteria_count_required": 5,
        "duration": "at least once a week for 3 months",
        "criteria": {
            "A": {
                "text": "Recurrent episodes of binge eating. An episode of binge eating is characterized by both of the following: (1) Eating, in a discrete period of time (e.g., within any 2-hour period), an amount of food that is definitely larger than what most individuals would eat in a similar period of time under similar circumstances. (2) A sense of lack of control over eating during the episode (e.g., a feeling that one cannot stop eating or control what or how much one is eating).",
                "indicators": ["i ate so much i feel sick", "couldn't stop eating", "ate the whole thing in like an hour", "i blacked out and ate everything", "lost control with food again", "ate until i was in pain", "finished an entire box of cookies", "went through the drive thru twice", "i literally can't stop once i start", "had another binge last night"]
            },
            "B": {
                "text": "Recurrent inappropriate compensatory behaviors in order to prevent weight gain, such as self-induced vomiting; misuse of laxatives, diuretics, or other medications; fasting; or excessive exercise.",
                "indicators": ["had to get rid of it after", "took some laxatives", "made myself throw up", "purged again", "ran for 2 hours to burn it off", "not eating tomorrow to make up for it", "need to work out extra hard now", "i just had to get it out", "took water pills", "fasting for the next few days"]
            },
            "C": {
                "text": "The binge eating and inappropriate compensatory behaviors both occur, on average, at least once a week for 3 months.",
                "indicators": ["this happens every week", "been doing this for months", "it's like a cycle i can't break", "this is my routine now", "i do this almost every day", "been stuck in this pattern", "can't remember when this started", "this has been going on forever", "same thing different week"]
            },
            "D": {
                "text": "Self-evaluation is unduly influenced by body shape and weight.",
                "indicators": ["i feel worthless when i gain weight", "the scale controls my mood", "if i'm not thin i'm nothing", "my weight is all i think about", "i hate how my body looks", "can't wear that until i lose weight", "feeling fat today so staying home", "my thighs are disgusting", "body checking constantly", "i only feel good when i'm skinny"]
            },
            "E": {
                "text": "The disturbance does not occur exclusively during episodes of anorexia nervosa.",
                "indicators": ["i eat sometimes but then...", "my weight goes up and down", "i'm not that underweight", "i don't starve i just binge and purge", "i actually eat a lot just get rid of it"]
            },
        }
    },
    "Binge-Eating Disorder": {
        "dsm_page": 350,
        "pdf_page": 392,
        "section": "Feeding and Eating Disorders",
        "criteria_count_required": 1,
        "duration": "At least once a week for 3 months",
        "criteria": {
            "A1": {
                "text": "Recurrent episodes of binge eating. An episode of binge eating is characterized by eating, in a discrete period of time (e.g., within any 2-hour period), an amount of food that is definitely larger than what most people would eat in a similar period of time under similar circumstances.",
                "indicators": ["i ate so much food", "couldn't stop eating", "finished the whole thing", "ate everything in sight", "went through the entire bag", "ate way too much again", "demolished all the food", "binged so hard", "ate enough for like 5 people", "consumed an insane amount"]
            },
            "A2": {
                "text": "A sense of lack of control over eating during the episode (e.g., a feeling that one cannot stop eating or control what or how much one is eating).",
                "indicators": ["couldn't stop myself", "no control over eating", "can't help it once i start", "like i was on autopilot", "just kept going", "something takes over", "hands have a mind of their own", "felt possessed", "couldn't put it down", "it's like i black out"]
            },
            "B1": {
                "text": "Eating much more rapidly than normal.",
                "indicators": ["inhaled my food", "ate so fast", "barely even chewed", "scarfed it down", "wolfed it all down", "didn't even taste it", "ate in like 5 minutes", "speed eating again"]
            },
            "B2": {
                "text": "Eating until feeling uncomfortably full.",
                "indicators": ["so stuffed i can't move", "feel like i'm gonna burst", "ate until it hurt", "stomach is killing me", "so full i feel sick", "physically uncomfortable", "can barely breathe ate so much", "pants won't even button now", "feel like a balloon"]
            },
            "B3": {
                "text": "Eating large amounts of food when not feeling physically hungry.",
                "indicators": ["wasn't even hungry", "not hungry but eating anyway", "just ate but eating more", "i don't eat because i'm hungry", "full but still eating", "ate for no reason", "don't know why i ate that", "emotional eating again"]
            },
            "B4": {
                "text": "Eating alone because of feeling embarrassed by how much one is eating.",
                "indicators": ["eat alone so no one sees", "hide when i eat", "can't eat like this around people", "wait til everyone's asleep to eat", "embarrassed to eat in front of others", "eat in my car alone", "don't want anyone to know how much", "secret eating", "hide the evidence"]
            },
            "B5": {
                "text": "Feeling disgusted with oneself, depressed, or very guilty afterward.",
                "indicators": ["hate myself after", "feel so disgusting", "why did i do that again", "so much regret", "feel like a failure", "crying after eating", "feel so ashamed", "depressed after i eat", "can't believe i did that again", "what's wrong with me"]
            },
            "C": {
                "text": "Marked distress regarding binge eating is present.",
                "indicators": ["this is ruining my life", "so stressed about my eating", "can't keep living like this", "eating is destroying me", "i'm so upset about this", "it's taking over my life", "constantly thinking about food", "feel trapped by food", "don't know what to do anymore"]
            },
            "D": {
                "text": "The binge eating occurs, on average, at least once a week for 3 months.",
                "indicators": ["happens every week", "been doing this for months", "this is a regular thing now", "can't remember when it started", "been going on forever", "at least once a week", "it's constant", "never ending cycle"]
            },
            "E": {
                "text": "The binge eating is not associated with the recurrent use of inappropriate compensatory behavior as in bulimia nervosa and does not occur exclusively during the course of bulimia nervosa or anorexia nervosa.",
                "indicators": ["don't throw up after", "don't purge", "just eat and feel bad", "don't do anything to make up for it", "the food just stays", "wish i could undo it but i don't", "not bulimic just binge"]
            },
        }
    },
    "Avoidant Personality Disorder": {
        "dsm_page": 672,
        "pdf_page": 714,
        "section": "Personality Disorders",
        "criteria_count_required": 4,
        "duration": "stable pattern since adolescence or early adulthood",
        "criteria": {
            "A1": {
                "text": "Avoids occupational activities that involve significant interpersonal contact, because of fears of criticism, disapproval, or rejection.",
                "indicators": ["turned down the promotion", "can't handle working with people", "stayed in my dead end job bc no customers", "rather work alone", "hate jobs where i have to talk to people", "applied for the back office position", "can't do customer service", "scared they'll judge my work", "avoid meetings at all costs", "called in sick bc of the presentation"]
            },
            "A2": {
                "text": "Is unwilling to get involved with people unless certain of being liked.",
                "indicators": ["need to know they actually like me first", "can't make the first move", "wait for them to reach out", "what if they're just being nice", "don't want to bother anyone", "they probably don't actually want me there", "i only talk to people who approach me", "need reassurance they want me around", "too scared to message first", "what if they secretly hate me"]
            },
            "A3": {
                "text": "Shows restraint within intimate relationships because of the fear of being shamed or ridiculed.",
                "indicators": ["scared to be myself around them", "can't open up even to my partner", "what if they think i'm weird", "hide parts of myself", "too embarrassed to share that", "they'd laugh at me", "keep my guard up even with bae", "can't be vulnerable", "afraid they'll make fun of me", "don't tell them the real stuff"]
            },
            "A4": {
                "text": "Is preoccupied with being criticized or rejected in social situations.",
                "indicators": ["everyone's judging me", "they're probably talking about me", "what if i say something stupid", "can't stop thinking about what they think", "replaying everything i said", "they definitely think i'm annoying", "waiting for them to reject me", "know they'll criticize me eventually", "assume people don't like me", "obsessing over that awkward moment"]
            },
            "A5": {
                "text": "Is inhibited in new interpersonal situations because of feelings of inadequacy.",
                "indicators": ["freeze around new people", "don't know what to say to strangers", "feel like i'm not good enough to talk to them", "too awkward for new situations", "clam up when meeting people", "they're way out of my league socially", "feel so small around new people", "can't be myself with people i just met", "i'm so boring compared to them", "not interesting enough to make friends"]
            },
            "A6": {
                "text": "Views self as socially inept, personally unappealing, or inferior to others.",
                "indicators": ["i'm so awkward", "nobody would want to be my friend", "i'm literally the worst at socializing", "such a loser", "everyone's better than me", "i'm so unlikeable", "no personality", "boring af", "who would even want to hang out with me", "i'm the weird one in every group"]
            },
            "A7": {
                "text": "Is unusually reluctant to take personal risks or to engage in any new activities because they may prove embarrassing.",
                "indicators": ["what if i embarrass myself", "too scared to try new things", "rather stay home than risk it", "can't handle looking stupid", "never trying that again", "too risky what if i fail", "staying in my comfort zone", "nope not worth the humiliation", "imagine if i mess up in front of everyone", "playing it safe forever"]
            },
        }
    },
    "Dependent Personality Disorder": {
        "dsm_page": 675,
        "pdf_page": 717,
        "section": "Personality Disorders",
        "criteria_count_required": 5,
        "duration": "persistent pattern from early adulthood",
        "criteria": {
            "A1": {
                "text": "Has difficulty making everyday decisions without an excessive amount of advice and reassurance from others.",
                "indicators": ["what do you think i should do", "i can't decide without you", "just tell me what to pick", "i need your opinion first", "should i do this or that", "i can't make up my mind alone", "what would you do if you were me", "i'm scared to choose wrong", "please help me decide", "i don't trust my own judgment"]
            },
            "A2": {
                "text": "Needs others to assume responsibility for most major areas of his or her life.",
                "indicators": ["can you handle this for me", "i need someone to take care of things", "i can't do adult stuff alone", "you're better at this than me", "i need you to deal with it", "can you just do it for me", "i'm useless at managing my life", "someone else should be in charge", "i can't handle responsibility", "please take over for me"]
            },
            "A3": {
                "text": "Has difficulty expressing disagreement with others because of fear of loss of support or approval.",
                "indicators": ["i didn't want to upset them", "i just agreed to keep the peace", "i can't say no to people", "what if they leave me", "i'm scared they'll be mad", "i never speak up", "i just go along with everything", "i can't risk losing them", "i hate conflict so i stay quiet", "i'll just do what they want"]
            },
            "A4": {
                "text": "Has difficulty initiating projects or doing things on his or her own (because of a lack of self-confidence in judgment or abilities rather than a lack of motivation or energy).",
                "indicators": ["i can't start things alone", "i need someone with me to do stuff", "i don't trust myself to do it right", "i'm too scared to try on my own", "i need backup before i start", "what if i mess it up", "i can't do anything by myself", "i wait for someone to help me begin", "i'm not capable on my own", "i need hand holding"]
            },
            "A5": {
                "text": "Goes to excessive lengths to obtain nurturance and support from others, to the point of volunteering to do things that are unpleasant.",
                "indicators": ["i'll do anything for them to stay", "i do stuff i hate so they like me", "i'll be their doormat if it means they stay", "i volunteer for everything so they need me", "i do all the gross tasks so they appreciate me", "i'll put up with anything", "i bend over backwards for everyone", "i let them walk all over me", "i do whatever it takes to keep them", "i sacrifice everything for their approval"]
            },
            "A6": {
                "text": "Feels uncomfortable or helpless when alone because of exaggerated fears of being unable to care for himself or herself.",
                "indicators": ["i hate being alone", "i feel helpless by myself", "i can't survive on my own", "being alone terrifies me", "i don't know how to function alone", "i panic when no one's around", "i need someone here always", "i feel lost without people", "i can't take care of myself", "what if something happens and i'm alone"]
            },
            "A7": {
                "text": "Urgently seeks another relationship as a source of care and support when a close relationship ends.",
                "indicators": ["i jumped into a new relationship right away", "i can't be single", "i found someone new immediately", "i need to be with someone", "i went back to my ex because i couldn't be alone", "i'll date anyone just to not be single", "i hooked up with someone new already", "i can't do the single life", "i rebounded fast", "i need a relationship to function"]
            },
            "A8": {
                "text": "Is unrealistically preoccupied with fears of being left to take care of himself or herself.",
                "indicators": ["what if everyone abandons me", "i'm terrified of being left alone", "i worry they'll all leave", "i can't stop thinking about them leaving", "what happens when i'm on my own", "i'm scared i'll end up alone forever", "i obsess over them leaving me", "i have nightmares about being abandoned", "i can't handle the thought of being alone", "what if no one wants me"]
            },
        }
    },
    "Obsessive-Compulsive Personality Disorder": {
        "dsm_page": 678,
        "pdf_page": 720,
        "section": "Personality Disorders",
        "criteria_count_required": 4,
        "duration": "Stable pattern from early adulthood",
        "criteria": {
            "A1": {
                "text": "Is preoccupied with details, rules, lists, order, organization, or schedules to the extent that the major point of the activity is lost.",
                "indicators": ["i spent 3 hours making the perfect spreadsheet", "can't start until everything is organized", "i need to make another list first", "the formatting has to be exactly right", "i keep rewriting my to-do list", "got so caught up in planning i never actually did it", "i need everything color coded", "can't focus on the actual project until my desk is perfect", "spent all day organizing instead of working"]
            },
            "A2": {
                "text": "Shows perfectionism that interferes with task completion (e.g., is unable to complete a project because his or her own overly strict standards are not met).",
                "indicators": ["it's not good enough yet", "i can't turn this in it's not perfect", "been working on this forever but it's still not right", "i'd rather not submit it than submit something mediocre", "redid the whole thing five times", "if i can't do it perfectly why bother", "my standards are too high i know", "i'll never finish this project", "kept editing until i missed the deadline", "nothing i do is ever good enough"]
            },
            "A3": {
                "text": "Is excessively devoted to work and productivity to the exclusion of leisure activities and friendships (not accounted for by obvious economic necessity).",
                "indicators": ["i don't have time for fun", "can't remember my last vacation", "weekends are for catching up on work", "i'll relax when the work is done", "friends stopped inviting me out", "hobbies feel like a waste of time", "i feel guilty when i'm not productive", "haven't seen my friends in months too busy", "taking a break feels wrong", "work comes first always"]
            },
            "A4": {
                "text": "Is overconscientious, scrupulous, and inflexible about matters of morality, ethics, or values (not accounted for by cultural or religious identification).",
                "indicators": ["there's a right way and a wrong way", "i can't bend the rules ever", "it's the principle of the matter", "how can people be so unethical", "i could never do that it's wrong", "rules exist for a reason", "i don't care if everyone does it it's still wrong", "my integrity is everything", "i can't look the other way", "some things are just black and white"]
            },
            "A5": {
                "text": "Is unable to discard worn-out or worthless objects even when they have no sentimental value.",
                "indicators": ["i might need it someday", "can't throw this away what if", "i have boxes of old stuff just in case", "it still works why trash it", "i keep everything you never know", "my closet is full of stuff i never use but can't toss", "throwing things away feels wasteful", "i have receipts from like 5 years ago", "what if i need this later"]
            },
            "A6": {
                "text": "Is reluctant to delegate tasks or to work with others unless they submit to exactly his or her way of doing things.",
                "indicators": ["i'll just do it myself", "nobody does it right except me", "if you want something done right", "they won't do it the way i need", "i can't trust anyone else with this", "it's easier to do it alone", "they never follow my instructions exactly", "i'm such a control freak i know", "group projects are my nightmare", "i have to supervise everything or it's wrong"]
            },
            "A7": {
                "text": "Adopts a miserly spending style toward both self and others; money is viewed as something to be hoarded for future catastrophes.",
                "indicators": ["i never spend money on myself", "saving for a rainy day", "what if something bad happens and i need it", "i can't justify that purchase", "that's too expensive even though i can afford it", "i feel guilty spending money", "you never know when you'll need savings", "i'm not cheap i'm careful", "buying things feels wasteful", "i'd rather save than enjoy life honestly"]
            },
            "A8": {
                "text": "Shows rigidity and stubbornness.",
                "indicators": ["i'm not changing my mind", "this is how i've always done it", "i know i'm stubborn", "why fix what isn't broken", "i don't do well with change", "my way works fine", "i hate when people try to change my routine", "i'm set in my ways", "don't try to convince me otherwise", "i know i'm inflexible but whatever"]
            },
        }
    },
    "Paranoid Personality Disorder": {
        "dsm_page": 649,
        "pdf_page": 691,
        "section": "Personality Disorders",
        "criteria_count_required": 4,
        "duration": "Stable pattern since early adulthood",
        "criteria": {
            "A": {
                "text": "A pervasive distrust and suspiciousness of others such that their motives are interpreted as malevolent, beginning by early adulthood and present in a variety of contexts, as indicated by four (or more) of the following:",
                "indicators": []
            },
            "A1": {
                "text": "Suspects, without sufficient basis, that others are exploiting, harming, or deceiving him or her.",
                "indicators": ["everyone's out to get me", "they're using me", "people always have hidden agendas", "i know they're lying to me", "nobody tells the truth", "they're just pretending to be nice", "something's off about them", "i can tell they're fake", "they're definitely hiding something", "people only want something from me"]
            },
            "A2": {
                "text": "Is preoccupied with unjustified doubts about the loyalty or trustworthiness of friends or associates.",
                "indicators": ["i can't trust anyone", "my friends talk behind my back", "they'll turn on me eventually", "are you really my friend tho", "nobody's actually loyal", "i know they're secretly against me", "even my best friend would betray me", "people always switch up on you", "i'm always testing people's loyalty", "can't rely on anybody these days"]
            },
            "A3": {
                "text": "Is reluctant to confide in others because of unwarranted fear that the information will be used maliciously against him or her.",
                "indicators": ["i can't tell anyone anything", "they'll use it against me later", "anything i say will come back to bite me", "i keep everything to myself", "people weaponize your secrets", "never let them know your business", "i don't open up to anyone", "they'll spread my stuff around", "information is power over you", "told someone once and they used it against me"]
            },
            "A4": {
                "text": "Reads hidden demeaning or threatening meanings into benign remarks or events.",
                "indicators": ["what did they mean by that", "that was definitely a dig at me", "i know what they're really saying", "that comment was shady af", "they're lowkey insulting me", "there's a hidden message there", "why would they say it like that", "that was a threat disguised as a joke", "i caught that subliminal", "they're mocking me but trying to hide it"]
            },
            "A5": {
                "text": "Persistently bears grudges (i.e., is unforgiving of insults, injuries, or slights).",
                "indicators": ["i never forget what people did to me", "still haven't forgiven them", "i remember every wrong", "they hurt me 5 years ago and i still think about it", "i keep receipts on everyone", "forgive and forget isn't for me", "they'll pay for what they did", "i hold onto things forever", "once you cross me it's done", "i've got a mental list of everyone who wronged me"]
            },
            "A6": {
                "text": "Perceives attacks on his or her character or reputation that are not apparent to others and is quick to react angrily or to counterattack.",
                "indicators": ["they're trying to ruin my reputation", "everyone's attacking me", "i had to defend myself", "they started it first", "people are always coming for me", "i'm not gonna let them disrespect me", "they're trying to make me look bad", "i snapped because they were attacking me", "why is everyone against me", "i had to set the record straight"]
            },
            "A7": {
                "text": "Has recurrent suspicions, without justification, regarding fidelity of spouse or sexual partner.",
                "indicators": ["i know they're cheating", "checked their phone again", "who were you really with", "why did you take so long to reply", "i saw how they looked at you", "they're definitely talking to someone else", "why are you being so secretive", "i don't believe them when they say nothing happened", "something feels off with us", "i need to know where you are at all times"]
            },
            "B": {
                "text": "Does not occur exclusively during the course of schizophrenia, a bipolar disorder or depressive disorder with psychotic features, or another psychotic disorder and is not attributable to the physiological effects of another medical condition.",
                "indicators": []
            },
        }
    },
    "Schizoid Personality Disorder": {
        "dsm_page": 653,
        "pdf_page": 695,
        "section": "Personality Disorders",
        "criteria_count_required": 4,
        "duration": "stable pattern since early adulthood",
        "criteria": {
            "A1": {
                "text": "Neither desires nor enjoys close relationships, including being part of a family.",
                "indicators": ["i don't really need people", "relationships are too much work", "i'm fine being alone", "don't really want a partner", "family stuff isn't for me", "i don't get why people need to be so close", "rather just do my own thing", "never wanted that whole family life", "being close to people feels pointless", "i'm not into the whole relationship thing"]
            },
            "A2": {
                "text": "Almost always chooses solitary activities.",
                "indicators": ["i always do stuff alone", "prefer solo activities", "don't like group things", "i'd rather stay in by myself", "never really hang out with people", "i do everything on my own", "groups aren't my thing", "i like hobbies i can do alone", "don't need company to have fun", "team stuff isn't for me"]
            },
            "A3": {
                "text": "Has little, if any, interest in having sexual experiences with another person.",
                "indicators": ["not really into that stuff", "sex doesn't interest me much", "i don't really think about that", "physical stuff isn't my thing", "never been that into hooking up", "could take it or leave it honestly", "don't get why everyone's obsessed with it", "that side of relationships doesn't appeal to me", "i'm not really a sexual person", "intimacy like that feels weird to me"]
            },
            "A4": {
                "text": "Takes pleasure in few, if any, activities.",
                "indicators": ["nothing really excites me", "i don't enjoy much tbh", "can't think of anything i love doing", "stuff just feels meh", "i'm not passionate about anything", "things don't make me happy like other people", "hobbies feel pointless", "i don't really have fun", "nothing sounds appealing", "idk what i even like anymore"]
            },
            "A5": {
                "text": "Lacks close friends or confidants other than first-degree relatives.",
                "indicators": ["don't really have friends", "no one i'd call close", "just have family i guess", "never had a best friend", "i don't do the whole friend group thing", "no one really knows me", "don't have anyone to talk to besides family", "i keep to myself mostly", "never been good at making friends", "wouldn't say i have real friends"]
            },
            "A6": {
                "text": "Appears indifferent to the praise or criticism of others.",
                "indicators": ["don't care what people think", "compliments don't do anything for me", "criticism doesn't bother me", "people's opinions are whatever", "doesn't matter if they like me", "i'm unbothered by what others say", "praise feels empty", "i don't need validation", "their judgment means nothing", "couldn't care less about approval"]
            },
            "A7": {
                "text": "Shows emotional coldness, detachment, or flattened affectivity.",
                "indicators": ["people say i'm cold", "i don't really feel emotions", "i'm pretty detached from everything", "not an emotional person", "feelings aren't really my thing", "i come off distant apparently", "don't really react to stuff", "emotions just aren't there for me", "people think i don't care", "i'm kinda numb to everything"]
            },
        }
    },
    "Schizotypal Personality Disorder": {
        "dsm_page": 655,
        "pdf_page": 697,
        "section": "Personality Disorders",
        "criteria_count_required": 5,
        "duration": "Pervasive pattern beginning by early adulthood",
        "criteria": {
            "A1": {
                "text": "Ideas of reference (excluding delusions of reference)",
                "indicators": ["people were talking about me", "that song was meant for me", "saw a sign meant just for me", "the tv was sending me a message", "everyone keeps looking at me", "that post was definitely about me", "its not a coincidence", "the universe is trying to tell me something", "they were laughing at me i know it", "everything feels connected to me somehow"]
            },
            "A2": {
                "text": "Odd beliefs or magical thinking that influences behavior and is inconsistent with subcultural norms (e.g., superstitiousness, belief in clairvoyance, telepathy, or 'sixth sense'; in children and adolescents, bizarre fantasies or preoccupations)",
                "indicators": ["i can sense things before they happen", "im pretty sure im psychic", "i knew you were gonna text me", "i can read peoples energy", "we have a telepathic connection", "i just know things without knowing how", "i can feel when something bad is coming", "my dreams predict the future", "i put a protection spell on myself", "the crystals are working i can feel it"]
            },
            "A3": {
                "text": "Unusual perceptual experiences, including bodily illusions",
                "indicators": ["i felt a presence in the room", "sometimes i hear someone call my name", "my body feels like its not mine", "i saw something out of the corner of my eye", "i feel like someones watching me", "felt like i was floating outside myself", "shadows keep moving weird", "i swear i felt someone touch me", "everything looks different sometimes", "my hands dont feel like my hands"]
            },
            "A4": {
                "text": "Odd thinking and speech (e.g., vague, circumstantial, metaphorical, overelaborate, or stereotyped)",
                "indicators": ["sorry i know im not making sense", "wait what was i even talking about", "its hard to explain what i mean", "people say i talk weird", "my thoughts are all jumbled", "i cant find the right words", "everything connects to everything you know", "sorry im rambling again", "people never understand what i mean", "my brain works differently than others"]
            },
            "A5": {
                "text": "Suspiciousness or paranoid ideation",
                "indicators": ["i dont trust anyone tbh", "people always have hidden motives", "theyre plotting something i can tell", "cant tell anyone my secrets", "everyone is out for themselves", "i know theyre talking behind my back", "something feels off about them", "i dont believe anything anyone says", "people pretend to be nice", "trust no one fr"]
            },
            "A6": {
                "text": "Inappropriate or constricted affect",
                "indicators": ["people say i react wrong", "i laughed at the wrong time again", "i dont feel things like others do", "my face doesnt match my feelings", "i cant show emotions right", "people think im cold but im not", "i felt nothing when i should have cried", "my reactions are always off", "i smiled when i shouldnt have", "everyone thinks im weird for not reacting"]
            },
            "A7": {
                "text": "Behavior or appearance that is odd, eccentric, or peculiar",
                "indicators": ["people stare at me a lot", "i dress different and idc", "everyone thinks im weird", "i do things my own way", "people say im eccentric", "i dont fit in anywhere", "my style is unique lets say", "people call me strange", "i know i come off as odd", "normal is boring anyway"]
            },
            "A8": {
                "text": "Lack of close friends or confidants other than first-degree relatives",
                "indicators": ["i only really talk to my family", "dont have any real friends", "nobody gets me", "i keep to myself mostly", "people drift away from me", "cant connect with anyone", "i have no one to talk to", "friendships never work out for me", "im always on the outside", "i prefer being alone anyway"]
            },
            "A9": {
                "text": "Excessive social anxiety that does not diminish with familiarity and tends to be associated with paranoid fears rather than negative judgments about self",
                "indicators": ["even around people i know i feel anxious", "the anxiety never goes away with anyone", "i get nervous cause i dont know what theyre thinking", "social stuff never gets easier for me", "cant relax around anyone", "always on edge around people", "i watch everyone carefully", "being around people drains me cause i cant trust them", "never feel comfortable no matter how long i know someone", "the more i know someone the more suspicious i get"]
            },
        }
    },
    "Antisocial Personality Disorder": {
        "dsm_page": 659,
        "pdf_page": 701,
        "section": "Personality Disorders",
        "criteria_count_required": 3,
        "duration": "Pattern since age 15, individual must be at least 18 years old",
        "criteria": {
            "A": {
                "text": "A pervasive pattern of disregard for and violation of the rights of others, occurring since age 15 years, as indicated by three (or more) of the following:",
                "indicators": []
            },
            "A1": {
                "text": "Failure to conform to social norms with respect to lawful behaviors, as indicated by repeatedly performing acts that are grounds for arrest.",
                "indicators": ["got arrested again", "cops are after me", "broke the law but whatever", "they can't catch me", "rules don't apply to me", "got away with it", "who cares if it's illegal", "did some sketchy stuff", "been in trouble with the law", "might go to jail lol"]
            },
            "A2": {
                "text": "Deceitfulness, as indicated by repeated lying, use of aliases, or conning others for personal profit or pleasure.",
                "indicators": ["told them what they wanted to hear", "made up a whole story", "they believed everything i said", "scammed this guy", "used a fake name", "lied my way out of it", "people are so easy to fool", "finessed them", "played them so hard", "they had no idea i was lying"]
            },
            "A3": {
                "text": "Impulsivity or failure to plan ahead.",
                "indicators": ["just did it without thinking", "yolo", "don't think about tomorrow", "who needs a plan", "just winging it", "acted on impulse", "didn't think about consequences", "live in the moment", "planning is boring", "i do what i want when i want"]
            },
            "A4": {
                "text": "Irritability and aggressiveness, as indicated by repeated physical fights or assaults.",
                "indicators": ["got in another fight", "punched him in the face", "he had it coming", "beat someone up", "they made me hit them", "i'll fight anyone", "threw hands", "messed him up pretty bad", "people know not to cross me", "violence solves problems"]
            },
            "A5": {
                "text": "Reckless disregard for safety of self or others.",
                "indicators": ["drove 100mph it was fun", "who cares if it's dangerous", "i don't wear seatbelts", "risked it all", "living on the edge", "safety is for losers", "almost died but whatever", "did something crazy last night", "they could've gotten hurt but oh well", "danger makes me feel alive"]
            },
            "A6": {
                "text": "Consistent irresponsibility, as indicated by repeated failure to sustain consistent work behavior or honor financial obligations.",
                "indicators": ["got fired again", "not paying that back", "ghosted my job", "bills can wait", "not my problem", "they'll figure it out", "can't hold down a job", "money comes and goes", "work is for suckers", "borrowed money and forgot about it"]
            },
            "A7": {
                "text": "Lack of remorse, as indicated by being indifferent to or rationalizing having hurt, mistreated, or stolen from another.",
                "indicators": ["they deserved it", "don't feel bad at all", "not my fault they got hurt", "i'd do it again", "why would i feel guilty", "they had it coming", "no regrets", "sucks for them", "not losing sleep over it", "whatever happened to them isn't my problem"]
            },
            "B": {
                "text": "The individual is at least age 18 years.",
                "indicators": ["i'm an adult", "over 18", "grown", "legal age"]
            },
            "C": {
                "text": "There is evidence of conduct disorder with onset before age 15 years.",
                "indicators": ["been like this since i was a kid", "always been in trouble", "got expelled in middle school", "started young", "was a problem child", "been this way forever", "did worse stuff as a teenager", "juvenile record", "always been a troublemaker"]
            },
            "D": {
                "text": "The occurrence of antisocial behavior is not exclusively during the course of schizophrenia or bipolar disorder.",
                "indicators": []
            },
        }
    },
    "Histrionic Personality Disorder": {
        "dsm_page": 667,
        "pdf_page": 709,
        "section": "Personality Disorders",
        "criteria_count_required": 5,
        "duration": "persistent pattern from early adulthood",
        "criteria": {
            "A1": {
                "text": "Is uncomfortable in situations in which he or she is not the center of attention",
                "indicators": ["everyone was ignoring me", "nobody even noticed me", "felt invisible at the party", "why wasn't anyone paying attention to me", "i hate when people don't notice me", "felt like i didn't even exist there", "nobody was looking at me", "i need to be seen", "can't stand being ignored", "felt so left out when they weren't focused on me"]
            },
            "A2": {
                "text": "Interaction with others is often characterized by inappropriate sexually seductive or provocative behavior",
                "indicators": ["i was just being flirty", "everyone says i'm too much", "i can't help being sexy", "just wanted them to want me", "wore something super hot to get attention", "was being a little provocative lol", "flirted with everyone there", "i like making people want me", "being seductive is just who i am", "turned on the charm big time"]
            },
            "A3": {
                "text": "Displays rapidly shifting and shallow expression of emotions",
                "indicators": ["i was crying then laughing in like 2 seconds", "my mood changes so fast", "went from furious to totally fine", "i feel everything so intensely but it passes quick", "was sobbing then completely over it", "my emotions are all over the place today", "literally went from rage to happy in a minute", "i switch moods super fast", "one second i'm devastated next i'm fine", "my feelings change constantly"]
            },
            "A4": {
                "text": "Consistently uses physical appearance to draw attention to self",
                "indicators": ["spent 3 hours getting ready", "need to look perfect so people notice", "always have to be the best dressed", "my outfit has to stand out", "can't go out without full glam", "i dress to turn heads", "looking hot is everything", "my appearance is so important to me", "always need to look amazing", "gotta make sure all eyes on me"]
            },
            "A5": {
                "text": "Has a style of speech that is excessively impressionistic and lacking in detail",
                "indicators": ["it was just like the most amazing thing ever", "literally the worst thing that's ever happened", "you wouldn't even believe how incredible it was", "it was just so so so good", "i can't even describe it it was everything", "the vibes were just immaculate", "it was literally perfect in every way", "so unbelievably crazy", "the whole thing was just wow", "i can't explain it was just everything"]
            },
            "A6": {
                "text": "Shows self-dramatization, theatricality, and exaggerated expression of emotion",
                "indicators": ["i literally wanted to die", "it was the most traumatic thing ever", "i'm completely destroyed", "this is the worst day of my entire life", "i'm absolutely devastated beyond words", "i've never been this upset ever", "my heart is literally shattered", "i can't even function i'm so upset", "this ruined my whole life", "i'm having a complete breakdown rn"]
            },
            "A7": {
                "text": "Is suggestible (i.e., easily influenced by others or circumstances)",
                "indicators": ["she said i should so i did", "everyone was doing it so", "they convinced me so easily", "i just go along with whatever", "i change my mind based on who i'm with", "totally got talked into it", "i'm so easily influenced lol", "whatever you think i should do", "i just agree with everyone", "someone told me this was better so now i think that"]
            },
            "A8": {
                "text": "Considers relationships to be more intimate than they actually are",
                "indicators": ["we're literally best friends after meeting once", "i feel like we've known each other forever", "they're basically my soulmate already", "we have such a deep connection", "i've never felt this close to anyone", "we're so intimate even though we just met", "they totally get me on another level", "we're practically family now", "i feel like we're meant to be together", "never had a bond this strong this fast"]
            },
        }
    },
    "Alcohol Use Disorder": {
        "dsm_page": 490,
        "pdf_page": 532,
        "section": "Substance-Related and Addictive Disorders",
        "criteria_count_required": 2,
        "duration": "12 months",
        "criteria": {
            "A1": {
                "text": "Alcohol is often taken in larger amounts or over a longer period than was intended.",
                "indicators": ["only meant to have one drink", "didn't plan on drinking that much", "went way harder than i planned", "blacked out again", "said i'd stop at 2 but", "kept going til the bottle was empty", "one drink turned into ten", "lost count of how many i had", "woke up still drunk"]
            },
            "A2": {
                "text": "There is a persistent desire or unsuccessful efforts to cut down or control alcohol use.",
                "indicators": ["trying to cut back on drinking", "i keep saying i'll quit but", "told myself no more drinking", "failed dry january again", "can't seem to stop", "swore off alcohol last week", "deleted my bar apps but still went", "promised myself i'd take a break", "keep falling off the wagon"]
            },
            "A3": {
                "text": "A great deal of time is spent in activities necessary to obtain alcohol, use alcohol, or recover from its effects.",
                "indicators": ["whole weekend was just drinking", "spent all day hungover", "recovering from last night", "wasted my whole sunday in bed", "too hungover to function", "needed the whole day to recover", "spent hours at the bar again", "my life revolves around drinking", "always planning the next drink"]
            },
            "A4": {
                "text": "Craving, or a strong desire or urge to use alcohol.",
                "indicators": ["really need a drink rn", "dying for a beer", "can't stop thinking about drinking", "i need alcohol to get through this", "counting down til happy hour", "all i want is wine", "would kill for a shot", "the urge is so strong", "obsessing over getting drunk"]
            },
            "A5": {
                "text": "Recurrent alcohol use resulting in a failure to fulfill major role obligations at work, school, or home.",
                "indicators": ["called in sick bc hungover", "missed class from drinking", "got written up at work", "too wasted to pick up my kids", "forgot about the meeting", "bombed my exam bc i was drinking", "my boss noticed i was off", "couldn't make it to work again", "flunking out bc of partying"]
            },
            "A6": {
                "text": "Continued alcohol use despite having persistent or recurrent social or interpersonal problems caused or exacerbated by the effects of alcohol.",
                "indicators": ["we fight every time i drink", "my friends are over my drinking", "gf threatened to leave if i keep drinking", "lost another friendship over it", "family won't talk to me anymore", "drunk texted and ruined everything", "people avoid me when i'm drinking", "caused another scene at the party", "keep hurting people when i'm wasted"]
            },
            "A7": {
                "text": "Important social, occupational, or recreational activities are given up or reduced because of alcohol use.",
                "indicators": ["stopped going to the gym", "don't do anything but drink anymore", "quit all my hobbies", "never see my friends unless drinking", "missed my kid's game again", "used to love hiking but now", "gave up everything for alcohol", "don't have energy for anything else", "stopped caring about stuff i used to love"]
            },
            "A8": {
                "text": "Recurrent alcohol use in situations in which it is physically hazardous.",
                "indicators": ["drove home drunk last night", "drinking and driving again", "went swimming wasted", "got behind the wheel after shots", "blacked out walking home alone", "mixed alcohol with my meds", "drunk at work with machinery", "ubered bc too drunk to drive finally", "woke up somewhere random"]
            },
            "A9": {
                "text": "Alcohol use is continued despite knowledge of having a persistent or recurrent physical or psychological problem that is likely to have been caused or exacerbated by alcohol.",
                "indicators": ["doctor told me to stop drinking but", "my liver is messed up and i still drink", "makes my depression worse but whatever", "know it's killing me but can't stop", "anxiety is worse when i drink but", "stomach problems from drinking", "meds don't work bc of alcohol", "therapist says i need to quit", "health is getting worse but still drinking"]
            },
            "A10": {
                "text": "Tolerance, as defined by either of the following: (a) a need for markedly increased amounts of alcohol to achieve intoxication or desired effect, or (b) a markedly diminished effect with continued use of the same amount of alcohol.",
                "indicators": ["takes so much more to feel it now", "used to get drunk off 2 beers", "can drink anyone under the table", "barely feel buzzed anymore", "need way more than i used to", "my tolerance is insane", "a bottle doesn't even touch me", "can handle my liquor too well", "nothing gets me drunk anymore"]
            },
            "A11": {
                "text": "Withdrawal, as manifested by either of the following: (a) the characteristic withdrawal syndrome for alcohol, or (b) alcohol (or a closely related substance, such as a benzodiazepine) is taken to relieve or avoid withdrawal symptoms.",
                "indicators": ["hands won't stop shaking", "need a drink to stop the shakes", "feel sick until i have a drink", "sweating and can't sleep without alcohol", "hair of the dog to feel normal", "get the sweats when i don't drink", "anxiety is insane until i drink", "heart racing without alcohol", "need morning drinks to function"]
            },
        }
    },
}



def analyze_dsm5_diagnosis(conversation_text: str, participant_name: str) -> Dict:
    """Analyze conversation against DSM-5 criteria and return diagnosis."""
    
    messages = conversation_text.split('\n')
    patient_messages = [m for m in messages if m.startswith('[PATIENT]:')]
    
    diagnoses_assessed = []
    
    for disorder_name, disorder_info in DSM5_CRITERIA.items():
        assessment = assess_disorder(
            disorder_name,
            disorder_info,
            patient_messages
        )
        diagnoses_assessed.append(assessment)
    
    diagnoses_assessed.sort(key=lambda x: x['criteria_met_percentage'], reverse=True)
    
    primary_diagnosis = None
    for diagnosis in diagnoses_assessed:
        if diagnosis['meets_diagnostic_threshold']:
            primary_diagnosis = diagnosis
            break
    
    return {
        "primary_diagnosis": primary_diagnosis,
        "all_assessments": diagnoses_assessed,
        "disclaimer": "AI-assisted screening tool. Clinical diagnosis requires comprehensive evaluation by licensed professional."
    }


def assess_disorder(disorder_name: str, disorder_info: Dict, patient_messages: List[str]) -> Dict:
    """Assess specific disorder against conversation."""
    
    criteria_results = {}
    criteria_met_count = 0
    evidence_collection = []
    
    for criterion_id, criterion_data in disorder_info['criteria'].items():
        evidence_found = []
        
        for message in patient_messages:
            message_lower = message.lower()
            
            for indicator in criterion_data['indicators']:
                if indicator.lower() in message_lower:
                    evidence_found.append({
                        "message": message.replace('[PATIENT]:', '').strip(),
                        "indicator_matched": indicator,
                        "criterion_id": criterion_id
                    })
        
        is_met = len(evidence_found) > 0
        
        criteria_results[criterion_id] = {
            "criterion_text": criterion_data['text'],
            "is_met": is_met,
            "evidence": evidence_found[:3],
            "evidence_count": len(evidence_found)
        }
        
        if is_met:
            criteria_met_count += 1
            evidence_collection.extend(evidence_found[:2])
    
    total_criteria = len(disorder_info['criteria'])
    required_count = disorder_info.get('criteria_count_required', total_criteria)
    meets_threshold = criteria_met_count >= required_count
    percentage = (criteria_met_count / total_criteria) * 100
    
    if percentage >= 80:
        confidence = "High"
    elif percentage >= 60:
        confidence = "Moderate"
    elif percentage >= 40:
        confidence = "Low"
    else:
        confidence = "Very Low"
    
    return {
        "disorder_name": disorder_name,
        "dsm5_page": disorder_info['dsm_page'],
        "pdf_page": disorder_info.get('pdf_page', disorder_info['dsm_page']),
        "section": disorder_info['section'],
        "criteria_met": criteria_met_count,
        "total_criteria": total_criteria,
        "criteria_required": required_count,
        "criteria_met_percentage": round(percentage, 1),
        "meets_diagnostic_threshold": meets_threshold,
        "confidence_level": confidence,
        "criteria_breakdown": criteria_results,
        "key_evidence": evidence_collection[:5],
        "duration_note": disorder_info.get('duration', 'Not specified'),
        "clinical_interpretation": f"{'Meets' if meets_threshold else 'Does not meet'} diagnostic criteria ({criteria_met_count}/{required_count} criteria). {confidence} confidence."
    }


def get_dsm5_diagnosis(conversation_text: str, participant_name: str) -> Dict:
    """Main entry point for DSM-5 diagnosis analysis."""
    return analyze_dsm5_diagnosis(conversation_text, participant_name)
