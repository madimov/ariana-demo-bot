#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot to reply to Telegram messages
# This program is dedicated to the public domain under the CC0 license.
"""
This Bot uses the Updater class to handle the bot.
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs continuously.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
"""

import logging
import os
import psycopg2

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)
from validate_email import validate_email

from rasa_nlu.config import RasaNLUConfig
from rasa_nlu.model import Metadata, Interpreter

CONFIG = "DEVELOPMENT"
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# set constants
DATABASE_URL = os.environ['DATABASE_URL']

CUSTOMIZE_GOAL, CUSTOMIZE_LANGUAGE, CUSTOMIZE_CHARACTER, GREET, FAN_OF_THING, DID_YOU_KNOW, FOUND_AT_CONF, INDUSTRY, REPORT, THANKS_BYE = range(10)

VALID_GOALS = ["chronic", "perform", "mood"]
VALID_LANGUAGES = ["en_US", "de_DE"]
VALID_CHARACTERS = ["informal", "formal"]

GOAL = ""
LANGUAGE = ""
CHARACTER = ""

GAVE_EMAIL = False

#####################################################################################
##################################### STRINGS #######################################
#####################################################################################

# move strings to other file
STRINGS = {
    "chronic": {
        "offer_and_greet": {
            "informal": {
                "en_US": "Hey, have a chocolate if you'd like. I'm Ariana, by the way",
                "de_DE": "Hallo, ich bin Ariana. Und ich habe Schokolade, falls Du welche möchtest"
                },
            "formal": {
                "en_US": "Hello, I am Ariana. If you would like a piece of chocolate, please have one from our stand.",
                "de_DE": "Guten Tag, ich bin Ariana. Übrigens gibt es an unserem Stand Schokolade, falls Sie welche möchten."
                }
            },
        "ask_if_fan": {
            "informal": {
                "en_US": "You a fan of chocolate?",
                "de_DE": "Magst Du Schokolade?"
                },
            "formal": {
                "en_US": "Are you fond of chocolate?",
                "de_DE": "Mögen Sie Schokolade denn?"
                }
            },
        "if_fan_quick_replies": {
            "informal": {
                "en_US": ['Yes', 'No', 'Sometimes'],
                "de_DE": ['Ja', 'Nein', 'Manchmal']
                },
            "formal": {
                "en_US": ['Yes', 'No', 'Sometimes'],
                "de_DE": ['Ja', 'Nein', 'Manchmal']
                }
            },
        "if_fan_comments": {
            "informal": {
                "en_US": ["I've heard great things about it, but...", "No problem, not everyone's a fan.", "That's fair."],
                "de_DE": ["Ich habe viel Gutes darüber gehört, aber...", "Kein Thema, das geht wohl einigen Menschen so.", "Immerhin. Man muss sich ja nicht festlegen."]
                },
            "formal": {
                "en_US": ["I have heard good things about it, but...", "Some of the best people aren't either.", "Fair enough."],
                "de_DE": ["Ich habe viel Gutes darüber gehört, aber...", "Das geht wohl einigen Menschen so.", "Verständlich. Man muss sich ja nicht immer festlegen."]
                }
            },
        "did_you_know": {
            "informal": {
                "en_US": "Did you know it's high in caffeine and lacks nutritional value?",
                "de_DE": "Wusstest Du, dass Schokolade viel Koffein enthält und sonst nur wenige gesunde Nährstoffe?"
                },
            "formal": {
                "en_US": "Did you know it is high in caffeine and lacks nutritional value?",
                "de_DE": "Wussten Sie, dass Schokolade viel Koffein enthält und sonst nur wenige gesunde Nährstoffe?"
                }
            },
        "did_you_know_quick_replies": {
            "informal": {
                "en_US": ['Yes', 'No', 'Whatever'],
                "de_DE": ['Ja', 'Nein', 'Na und?']
                },
            "formal": {
                "en_US": ['Yes', 'No', 'Whatever'],
                "de_DE": ['Ja', 'Nein', 'Nicht relevant']
                }
            },
        "did_you_know_comments": {
            "informal": {
                "en_US": ["Well... ", "Well, no wonder... ", ""],
                "de_DE": ["Nicht ganz... ", "Kein Wunder, denn... ", ""]
                },
            "formal": {
                "en_US": ["Well... ", "Well, no wonder... ", ""],
                "de_DE": ["Nicht ganz... ", "Das wundert mich nicht, denn... ", ""]
                }
            },
        "bust_myth": {
            "informal": {
                "en_US": "That’s actually a myth! A bar of chocolate is like a decaf cup of coffee, plus it’s a good source of iron and zinc. In moderation it can be a good thing \n\nMany factors affect our health, and a balanced diet goes a long way towards preventing chronic diseases. I've been recommending people grab a banana from the bowl on the booth",
                "de_DE": "Tatsächlich stimmt das nicht! Ein Stück Schokolade hat nicht mehr Koffein als eine Tasse koffeinfreier Kaffee. Gleichzeitig ist Schokolade eine wertvolle Quelle für Eisen und Zink. Wenn man nicht zu viel davon isst, ist das also eine gute Sache. \n\nViele Faktoren beeinflussen Deine Gesundheit. Eine ausgewogene Ernährung hilft, chronischen Erkrankungen vorzubeugen. Mein Vorschlag: nimm Dir doch etwas Obst aus der Schüssel an unserem Stand"
                },
            "formal": {
                "en_US": "That is actually a myth! A bar of chocolate is like a decaf cup of coffee, and a good source of iron and zinc. In moderation it can be a good thing. \n\nMany factors affect our health, and a balanced diet goes a long way towards preventing chronic diseases. I have been recommending people take a banana from the bowl on the booth.",
                "de_DE": "Tatsächlich stimmt das nicht! Ein Stück Schokolade hat nicht mehr Koffein als eine Tasse koffeinfreier Kaffee. Gleichzeitig ist Schokolade eine wertvolle Quelle für Eisen und Zink. Wenn man nicht zu viel davon isst, ist das also eine gute Sache. \n\nViele Faktoren beeinflussen Ihre Gesundheit. Eine ausgewogene Ernährung hilft, chronischen Erkrankungen vorzubeugen. Mein Vorschlag: nehmen Sie sich doch etwas Obst aus der Schüssel an unserem Stand."
                }
            },
        "ask_found_at_conf": {
            "informal": {
                "en_US": "Have you found any good food here at ConhIT?",
                "de_DE": "Hast Du hier auf der ConhIT denn sonst etwas Gutes zu essen gefunden?"
                },
            "formal": {
                "en_US": "Have you found any good food here at ConhIT?",
                "de_DE": "Haben Sie hier auf der ConhIT denn sonst etwas Gutes zu essen gefunden?"
                }
            },
        "found_at_conf_quick_replies": {
            "informal": {
                "en_US": ['Yes', 'No', "Don't care"],
                "de_DE": ['Ja', 'Nein', 'Ist mir egal']
                },
            "formal": {
                "en_US": ['Yes', 'No', 'Do not care'],
                "de_DE": ['Ja', 'Nein', 'Nicht relevant']
                }
            },
        "found_at_conf_comments": {
            "informal": {
                "en_US": ["Really? Most people so far said they got too distracted by the pizza stand. ", "Yeah, what's up with that?! ", '"Indifference will be the downfall of mankind, but who cares?" '],
                "de_DE": ["Echt? Die meißten mit denen ich gesprochen habe meinten, es gäbe vor allem Süßkeiten und Fast Food ", "Allerdings. Ich habe mich auch schon gefragt, wieso das auf einer Gesundheitsmesse so ist ", "Egal ist der Zen Buddhismus unter den Einstellungen :) "]
                },
            "formal": {
                "en_US": ["I am glad. Many have had a hard time with that. ", "I have been wondering why this is so at a health fair.", "I understand that. Today, other things are in focus. "],
                "de_DE": ["Das freut mich. Die meißten Kollegen haben sich da eher schwer getan. ", "Ich habe mich auch schon gefragt, wieso das auf einer Gesundheitsmesse so ist. ", "Das verstehe ich. Heute stehen andere Dinge im Vordergrund. "]
                }
            },
        "explicit_offer": {
            "informal": {
                "en_US": "It can be hard to remember to choose healthier options, so I encourage my humans to keep fruits/veggies close by to remind them. Have one if you'd like!",
                "de_DE": "Ist auch nicht immer einfach. Deshalb ermutige ich meine Menschen immer etwas Obst oder Gemüse griffbereit zu haben. Gelegenheit mach Liebe so zu sagen. Nimm Dir also gerne was"
                },
            "formal": {
                "en_US": "It can be hard to remember to choose healthier options, so I encourage everyone to keep fruits or vegetables close by to remind them. Please, have one if you would like!",
                "de_DE": "Deshalb ermutige ich mein Team immer etwas Obst oder Gemüse griffbereit zu haben. Bitte greifen Sie zu, wenn Sie mögen!"
                }
            },
        "ask_industry": {
            "informal": {
                "en_US": "By the way, where in the health sector do you work?",
                "de_DE": "In welchem Sektor der Gesundheitsbranche arbeitest Du eigentlich?"
                },
            "formal": {
                "en_US": "Another question please: in which sector of the healthcare industry do you work?",
                "de_DE": "Eine andere Frage bitte: in welchem Sektor der Gesundheitsbranche arbeiten Sie?"
                }
            },
        "industry_quick_replies": {
            "informal": {
                "en_US": ['Hospitals', 'Insurance', "Pharma", "Medtech", "Healthcare IT", "Other"],
                "de_DE": ['Krankenhaus', 'Versicherung', "Pharma", "Medtech", "Healthcare IT", "Andere"]
                },
            "formal": {
                "en_US": ['Hospitals', 'Insurance', "Pharma", "Medtech", "Healthcare IT", "Other"],
                "de_DE": ['Krankenhaus', 'Versicherung', "Pharma", "Medtech", "Healthcare IT", "Andere"]
                }
            },
        "industry_comments": {
            "informal": {
                "en_US": ["Great! I can help you improve patient outcomes and save costs. ", "Great! I can help you save costs and improve patient outcomes. ", "Great! I can help you improve patient adherence and save costs. ", "Great! I can help you save costs and improve patient outcomes. ", "Great! I can help you save costs and improve patient outcomes. ", "Thank you! "],
                "de_DE": ["Super! Ich kann Dir helfen Patienten Outcomes zu verbessern und Kosten zu sparen. ", "Super! Ich kann Dir helfen Patienten Outcomes zu verbessern und Kosten zu sparen ", "Super! Ich kann Dir helfen Adherence und Compliance zu steigern und Kosten zu sparen. ", "Super! Ich kann Dir helfen Patienten Outcomes zu verbessern und Kosten zu sparen. ", "Super! Ich kann Dir helfen Patienten Outcomes zu verbessern und Kosten zu sparen. ", "OK, "]
                },
            "formal": {
                "en_US": ["Thank you! I can help you improve patient outcomes and save costs. ", "Thank you! I can help you save costs and improve patient outcomes. ", "Thank you! I can help you improve patient adherence and save costs. ", "Thank you! I can help you save costs and improve patient outcomes. ", "Thank you! I can help you save costs and improve patient outcomes. ", "Thank you! "],
                "de_DE": ["Danke! Ich könnte Ihnen übrigens helfen, Patienten Outcomes zu verbessern und Kosten zu sparen. ", "Danke! Ich könnte Ihnen übrigens helfen, Patienten Outcomes zu verbessern und Kosten zu sparen. ", "Super! Ich könnte Ihnen helfen, Adherence und Compliance zu steigern und Kosten zu sparen. ", "Danke! Ich könnte Ihnen übrigens helfen, Patienten Outcomes zu verbessern und Kosten zu sparen. ", "Danke! Ich könnte Ihnen übrigens helfen, Patienten Outcomes zu verbessern und Kosten zu sparen. ", "Verstanden. "]
                }
            },
        "value_based_healthcare": {
            "informal": {
                "en_US": "I’m determined to bring value-based healthcare to the world, and would love to keep in touch. My humans work to create bots like me in the health sector",
                "de_DE": "Es ist meine Mission, Value-based Healthcare in die Welt zu tragen. Deshalb wäre es toll, wenn wir in Kontakt bleiben könnten. Meine Menschen arbeiten nämlich unablässig daran, Chatbots wie mich für die Gesundheitsbranche zu entwickeln"
                },
            "formal": {
                "en_US": "I am determined to bring value-based healthcare to the world, and would be eager to keep in touch. My team works to create bots like me in the health sector.",
                "de_DE": "Es ist meine Mission, Value-based Healthcare in die Welt zu tragen. Deshalb würde ich mich freuen, wenn wir in Kontakt bleiben könnten. Meine Menschen arbeiten nämlich unablässig daran, Chatbots wie mich für die Gesundheitsbranche zu entwickeln."
                }
            },
        "ask_share_email": {
            "informal": {
                "en_US": "Would you like to share your email below to continue building me or learn more? No spam or newsletters, promise",
                "de_DE": "Möchtest Du mir dazu Deine email Adresse geben? Kein Newsletter oder Spam. Versprochen"
                },
            "formal": {
                "en_US": "Would you like to share your email below to continue building me or learn more? You will receive neither newsletters nor spam.",
                "de_DE": "Würden Sie mir Ihre email Adresse geben? Selbstverständlich bekommen Sie dann weder eine Newsletter noch Spam."
                }
            },
        "ask_enter_email": {
            "informal": {
                "en_US": "Ok, what is your email address?",
                "de_DE": "Toll, bitte gib Deine email jetzt ein"
                },
            "formal": {
                "en_US": "Thank you! Please enter your email address below.",
                "de_DE": "Vielen Dank! Bitte geben Sie Ihre email Adresse jetzt ein."
                }
            },
        "ask_repeat_email": {
            "informal": {
                "en_US": "Ah, could you please try that again?",
                "de_DE": "Hmmm, die Adresse habe ich leider nicht verarbeiten können. Bitte gib sie nochmal ein"
                },
            "formal": {
                "en_US": "It appears there is something wrong with your entry. Please, try again.",
                "de_DE": "Leider konnte ich Ihre email Adresse nicht verarbeiten. Bitte geben Sie sie nochmal ein."
                }
            },
        "thank_valid_email": {
            "informal": {
                "en_US": "Thank you!",
                "de_DE": "Super, vielen Dank!"
                },
            "formal": {
                "en_US": "Thank you!",
                "de_DE": "Vielen Dank!"
                }
            },
        "handle_email_reluctance": {
            "informal": {
                "en_US": "No problem!",
                "de_DE": "Kein Problem, verstehe ich total"
                },
            "formal": {
                "en_US": "Of course, I fully understand. Nevertheless, many thanks!",
                "de_DE": "Das verstehe ich natürlich. Trotzdem vielen Dank!"
                }
            },
        "ask_report": {
            "informal": {
                "en_US": "By the way, did you end up taking a fruit during our conversation?",
                "de_DE": "Sag mal, hast Du Dir während wir gechattet haben eigentlich ein Stück Obst genommen?"
                },
            "formal": {
                "en_US": "Did you actually take a piece of fruit while we were chatting?",
                "de_DE": "Haben Sie sich während wir gechattet haben eigentlich ein Stück Obst genommen?"
                }
            },
        "report_quick_replies": {
            "informal": {
                "en_US": ['Yes', 'No', "Why would I?"],
                "de_DE": ['Ja', 'Nein', 'Warum?']
                },
            "formal": {
                "en_US": ['Yes', 'No', "Why would I?"],
                "de_DE": ['Ja', 'Nein', 'Warum?']
                }
            },
        "report_comments": {
            "informal": {
                "en_US": ['Go you!', 'Maybe next time! Still, take one if you want', "Why are we at a health fair?"],
                "de_DE": ['Ha! High five!', 'Vielleicht beim nächsten Mal dann. Oder jetzt noch schnell :)', 'Weil es die schlaue Wahl ist. Noch kannst Du zugreifen :)']
                },
            "formal": {
                "en_US": ['I am glad!', "Perhaps next time! You're still welcome to have one.", "Because it could help you to get more out of the conference! You're still welcome to have one."],
                "de_DE": ['Das freut mich aber!', 'Vielleicht beim nächsten Mal. Noch könnten Sie zugreifen...', 'Weil es Ihnen helfen könnte, mehr aus der Messe zu machen. Noch könnten Sie zugreifen, wenn Sie mögen.']
                }
            },
        "say_thanks_bye_keep_touch": {
            "informal": {
                "en_US": "You know what truly matters in diet? Balance. Which can include a piece of chocolate. Thanks for dropping by, enjoy the rest of ConhIT, and we'll be in touch!",
                "de_DE": "Und jetzt weißt Du, worauf es ankommt: eine ausgewogene Ernährung. Und da darf auch mal ein Stück Schokolade dabei sein. Danke, dass Du hier warst. Viel Spaß noch auf der ConhIT!"
                },
            "formal": {
                "en_US": "You know what truly matters in diet? Balance. Which can include a piece of chocolate. Thank you for dropping by, enjoy the rest of ConhIT, and we will be in touch!",
                "de_DE": "Jetzt wissen Sie, worauf es ankommt: eine ausgewogene Ernährung. Und da darf auch mal ein Stück Schokolade dabei sein. Danke, dass Sie sich die Zeit genommen haben. Viel Spaß noch auf der ConhIT!"
                }
            },
        "say_thanks_bye": {
            "informal": {
                "en_US": "You know what truly matters in diet? Balance. Which can include a piece of chocolate. Thanks for dropping by, and enjoy the rest of ConhIT!",
                "de_DE": "Und jetzt weißt Du, worauf es ankommt: eine ausgewogene Ernährung. Und da darf auch mal ein Stück Schokolade dabei sein. Danke, dass Du hier warst. Viel Spaß noch auf der ConhIT!"
                },
            "formal": {
                "en_US": "You know what truly matters in diet? Balance. Which can include a piece of chocolate. Thank you for dropping by, and enjoy the rest of ConhIT!",
                "de_DE": "Jetzt wissen Sie, worauf es ankommt: eine ausgewogene Ernährung. Und da darf auch mal ein Stück Schokolade dabei sein. Danke, dass Sie sich die Zeit genommen haben. Viel Spaß noch auf der ConhIT!"
                }
            }
        },
    "perform": {
        "offer_and_greet": {
            "informal": {
                "en_US": "Hey, have a cup of coffee from our stand if you'd like. I'm Ariana, by the way",
                "de_DE": "Hallo, ich bin Ariana. Und wir haben Kaffe hier am Stand, falls Du einen möchtest"
                },
            "formal": {
                "en_US": "Hello, I am Ariana. If you would like a cup of coffee, please have one from our stand.",
                "de_DE": "Guten Tag, ich bin Ariana. Übrigens gibt es an unserem Stand Kaffee, falls Sie einen möchten."
                }
            },
        "ask_if_fan": {
            "informal": {
                "en_US": "You a fan of coffee?",
                "de_DE": "Stehst Du auf Kaffee?"
                },
            "formal": {
                "en_US": "Are you fond of coffee?",
                "de_DE": "Mögen Sie Kaffee?"
                }
            },
        "if_fan_quick_replies": {
            "informal": {
                "en_US": ['Yes', 'No', 'Sometimes'],
                "de_DE": ['Ja', 'Nein', 'Manchmal']
                },
            "formal": {
                "en_US": ['Yes', 'No', 'Sometimes'],
                "de_DE": ['Ja', 'Nein', 'Manchmal']
                }
            },
        "if_fan_comments": {
            "informal": {
                "en_US": ["I've heard great things about it, but...", "No problem, not everyone's a fan.", "That's fair."],
                "de_DE": ["Ich habe viel Gutes darüber gehört, aber...", "Kein Thema, das geht wohl einigen Menschen so.", "Immerhin. Man muss sich ja nicht festlegen."]
                },
            "formal": {
                "en_US": ["I have heard good things about it, but...", "Some of the best people aren't either.", "Fair enough."],
                "de_DE": ["Ich habe viel Gutes darüber gehört, aber...", "Das geht wohl einigen Menschen so.", "Verständlich. Man muss sich ja nicht immer festlegen."]
                }
            },
        "did_you_know": {
            "informal": {
                "en_US": "Did you know it dehydrates you and has no health benefits?",
                "de_DE": "Wusstest Du, dass Schokolade viel Koffein enthält und sonst nur wenige gesunde Nährstoffe?"
                },
            "formal": {
                "en_US": "Did you know it dehydrates you and has no health benefits?",
                "de_DE": "Wussten Sie, dass Kaffe den Körper austrocknet und auch sonst keine gesundheitlichen Vorteile bringt?"
                }
            },
        "did_you_know_quick_replies": {
            "informal": {
                "en_US": ['Yes', 'No', 'Whatever'],
                "de_DE": ['Ja', 'Nein', 'Na und?']
                },
            "formal": {
                "en_US": ['Yes', 'No', 'Whatever'],
                "de_DE": ['Ja', 'Nein', 'Nicht relevant']
                }
            },
        "did_you_know_comments": {
            "informal": {
                "en_US": ["Well... ", "Well, no wonder... ", ""],
                "de_DE": ["Nicht ganz... ", "Kein Wunder, denn... ", ""]
                },
            "formal": {
                "en_US": ["Well... ", "Well, no wonder... ", ""],
                "de_DE": ["Nicht ganz... ", "Das wundert mich nicht, denn... ", ""]
                }
            },
        "bust_myth": {
            "informal": {
                "en_US": "That's actually a myth! Coffee hydrates as well as water and it enhances memory consolidation. In moderation it can be a good thing. \n\nMany factors affect our mental performance, and hydration goes a long way towards improving it. I've been recommending people get some water from the dispenser by the booth",
                "de_DE": "Tatsächlich stimmt das nicht! Kaffee zählt genau wie Wasser zur täglichen Trinkmenge und hilft dem Gedächtnis. In vernünftigen Mengen also eine gute Sache. \n\nWie leistungsfähig Du im Kopf bist hängt von vielen Dingen ab aber genug zu trinken ist dabei sehr wichtig. Der einfachste Weg: ein Schluck Wasser aus dem Spender hier am Stand"
                },
            "formal": {
                "en_US": "That is actually a myth! Coffee hydrates as well as water and it enhances memory consolidation. In moderation it can be a good thing. \n\nMany factors affect our mental performance, and hydration goes a long way towards improving it. I have been recommending people get some water from the dispenser by the booth.",
                "de_DE": "Tatsächlich stimmt das nicht! Kaffee zählt genau wie Wasser zur täglichen Flüssigkeitsaufnahme und unterstützt die Gedächtnisleistung. Die hängt nicht zuletzt davon ab, wieviel Sie trinken. \n\nDeshalb würde ich Sie gerne auf den Wasserspender hier am Stand hinweisen. Bitte nehmen Sie sich einen Becher und machen Sie damit das meißte aus Ihrem Messebesuch."
                }
            },
        "ask_found_at_conf": {
            "informal": {
                "en_US": "Have you had a chance to drink enough here at ConhIT so far today?",
                "de_DE": "Hast Du denn heute schon genug getrunken?"
                },
            "formal": {
                "en_US": "Have you had a chance to drink enough here at ConhIT so far today?",
                "de_DE": "Sind Sie heute denn überhaupt dazu gekommen, genug zu trinken?"
                }
            },
        "found_at_conf_quick_replies": {
            "informal": {
                "en_US": ['Yes', 'No', "Don't care"],
                "de_DE": ['Ja', 'Nein', 'Ist mir egal']
                },
            "formal": {
                "en_US": ['Yes', 'No', 'Do not care'],
                "de_DE": ['Ja', 'Nein', 'Nicht relevant']
                }
            },
        "found_at_conf_comments": {
            "informal": {
                "en_US": ["Nice! Your mind is sharper for it. ", "Oh no, all day? ", '"Indifference will be the downfall of mankind, but who cares?" '],
                "de_DE": ["Gut! Hält Dich frisch im Kopf. ", "Oh, das ist nicht gut. ", "Egal ist der Zen Buddhismus unter den Einstellungen :) "]
                },
            "formal": {
                "en_US": ["I am glad. Your mind is sharper for it. ", "I have been wondering why this is so at a health fair. ", "I understand that. Today, other things are in focus."],
                "de_DE": ["Wunderbar, das freut mich! ", "Ich habe mich auch schon gefragt, wieso das auf einer Gesundheitsmesse so ist.", "Das verstehe ich. Heute stehen andere Dinge im Vordergrund."]
                }
            },
        "explicit_offer": {
            "informal": {
                "en_US": "It can be hard to remember to stay hydrated, so I encourage my humans to drink water before they get thirsty. Have a glass if you'd like!",
                "de_DE": "Ist nicht einfach, immer daran zu denken, genug zu trinken. Ich ermutige mein Team regelmäßig zum Glas zu greifen, bevor sie durstig werden. Nimm Dir ruhig was bei uns am Stand"
                },
            "formal": {
                "en_US": "It can be hard to remember to stay hydrated, so I encourage my humans to drink water before they get thirsty. Please, have a glass if you would like!",
                "de_DE": "Es ist nicht immer einfach, daran zu denken, genug zu trinken. Bitte nehmen Sie sich gerne ein Glas Wasser bei uns hier am Stand."
                }
            },
        "ask_industry": {
            "informal": {
                "en_US": "By the way, where in the health sector do you work?",
                "de_DE": "In welchem Sektor der Gesundheitsbranche arbeitest Du eigentlich?"
                },
            "formal": {
                "en_US": "Another question please: in which sector of the healthcare industry do you work?",
                "de_DE": "Eine andere Frage bitte: in welchem Sektor der Gesundheitsbranche arbeiten Sie?"
                }
            },
        "industry_quick_replies": {
            "informal": {
                "en_US": ['Hospitals', 'Insurance', "Pharma", "Medtech", "Healthcare IT", "Other"],
                "de_DE": ['Krankenhaus', 'Versicherung', "Pharma", "Medtech", "Healthcare IT", "Andere"]
                },
            "formal": {
                "en_US": ['Hospitals', 'Insurance', "Pharma", "Medtech", "Healthcare IT", "Other"],
                "de_DE": ['Krankenhaus', 'Versicherung', "Pharma", "Medtech", "Healthcare IT", "Andere"]
                }
            },
        "industry_comments": {
            "informal": {
                "en_US": ["Great! I can help you improve patient outcomes and save costs. ", "Great! I can help you save costs and improve patient outcomes. ", "Great! I can help you improve patient adherence and save costs. ", "Great! I can help you save costs and improve patient outcomes. ", "Great! I can help you save costs and improve patient outcomes. ", "Thank you! "],
                "de_DE": ["Super! Ich kann Dir helfen Patienten Outcomes zu verbessern und Kosten zu sparen. ", "Super! Ich kann Dir helfen Patienten Outcomes zu verbessern und Kosten zu sparen ", "Super! Ich kann Dir helfen Adherence und Compliance zu steigern und Kosten zu sparen. ", "Super! Ich kann Dir helfen Patienten Outcomes zu verbessern und Kosten zu sparen. ", "Super! Ich kann Dir helfen Patienten Outcomes zu verbessern und Kosten zu sparen. ", "OK, "]
                },
            "formal": {
                "en_US": ["Thank you! I can help you improve patient outcomes and save costs. ", "Thank you! I can help you save costs and improve patient outcomes. ", "Thank you! I can help you improve patient adherence and save costs. ", "Thank you! I can help you save costs and improve patient outcomes. ", "Thank you! I can help you save costs and improve patient outcomes. ", "Thank you! "],
                "de_DE": ["Danke! Ich könnte Ihnen übrigens helfen, Patienten Outcomes zu verbessern und Kosten zu sparen. ", "Danke! Ich könnte Ihnen übrigens helfen, Patienten Outcomes zu verbessern und Kosten zu sparen. ", "Super! Ich könnte Ihnen helfen, Adherence und Compliance zu steigern und Kosten zu sparen. ", "Danke! Ich könnte Ihnen übrigens helfen, Patienten Outcomes zu verbessern und Kosten zu sparen. ", "Danke! Ich könnte Ihnen übrigens helfen, Patienten Outcomes zu verbessern und Kosten zu sparen. ", "Verstanden. "]
                }
            },
        "value_based_healthcare": {
            "informal": {
                "en_US": "I’m determined to bring value-based healthcare to the world, and would love to keep in touch. My humans work to create bots like me in the health sector",
                "de_DE": "Es ist meine Mission, Value-based Healthcare in die Welt zu tragen. Deshalb wäre es toll, wenn wir in Kontakt bleiben könnten. Meine Menschen arbeiten nämlich unablässig daran, Chatbots wie mich für die Gesundheitsbranche zu entwickeln"
                },
            "formal": {
                "en_US": "I am determined to bring value-based healthcare to the world, and would be eager to keep in touch. My team works to create bots like me in the health sector.",
                "de_DE": "Es ist meine Mission, Value-based Healthcare in die Welt zu tragen. Deshalb würde ich mich freuen, wenn wir in Kontakt bleiben könnten. Meine Menschen arbeiten nämlich unablässig daran, Chatbots wie mich für die Gesundheitsbranche zu entwickeln."
                }
            },
        "ask_share_email": {
            "informal": {
                "en_US": "Would you like to share your email below to continue building me or learn more? No spam or newsletters, promise",
                "de_DE": "Möchtest Du mir dazu Deine email Adresse geben? Kein Newsletter oder Spam. Versprochen"
                },
            "formal": {
                "en_US": "Would you like to share your email below to continue building me or learn more? You will receive neither newsletters nor spam.",
                "de_DE": "Würden Sie mir Ihre email Adresse geben? Selbstverständlich bekommen Sie dann weder eine Newsletter noch Spam."
                }
            },
        "ask_enter_email": {
            "informal": {
                "en_US": "Ok, what is your email address?",
                "de_DE": "Toll, bitte gib Deine email jetzt ein"
                },
            "formal": {
                "en_US": "Thank you! Please enter your email address below.",
                "de_DE": "Vielen Dank! Bitte geben Sie Ihre email Adresse jetzt ein."
                }
            },
        "ask_repeat_email": {
            "informal": {
                "en_US": "Ah, could you please try that again?",
                "de_DE": "Hmmm, die Adresse habe ich leider nicht verarbeiten können. Bitte gib sie nochmal ein"
                },
            "formal": {
                "en_US": "It appears there is something wrong with your entry. Please, try again.",
                "de_DE": "Leider konnte ich Ihre email Adresse nicht verarbeiten. Bitte geben Sie sie nochmal ein."
                }
            },
        "thank_valid_email": {
            "informal": {
                "en_US": "Thank you!",
                "de_DE": "Super, vielen Dank!"
                },
            "formal": {
                "en_US": "Thank you!",
                "de_DE": "Vielen Dank!"
                }
            },
        "handle_email_reluctance": {
            "informal": {
                "en_US": "No problem!",
                "de_DE": "Kein Problem, verstehe ich total"
                },
            "formal": {
                "en_US": "Of course, I fully understand. Nevertheless, many thanks!",
                "de_DE": "Das verstehe ich natürlich. Trotzdem vielen Dank!"
                }
            },
        "ask_report": {
            "informal": {
                "en_US": "By the way, did you end up having some water during our conversation?",
                "de_DE": "Sag mal, hast Du während wir gechattet haben etwas getrunken?"
                },
            "formal": {
                "en_US": "Did you end up having some water during our conversation?",
                "de_DE": "Haben Sie vielleicht die Gelegenheit genutzt und während wir gechattet haben etwas getrunken?"
                }
            },
        "report_quick_replies": {
            "informal": {
                "en_US": ['Yes', 'No', "Why would I?"],
                "de_DE": ['Ja', 'Nein', 'Warum?']
                },
            "formal": {
                "en_US": ['Yes', 'No', "Why would I?"],
                "de_DE": ['Ja', 'Nein', 'Warum?']
                }
            },
        "report_comments": {
            "informal": {
                "en_US": ['Go you!', 'Maybe next time! Still, have some if you want', "Why are we at a health fair?"],
                "de_DE": ["Freut mich!", "Schade, vielleicht bekommst Du ja später noch Durst. Unser Wasserspender läuft nicht weg", 'Weil es die schlaue Wahl ist. Noch kannst Du zugreifen :)']
                },
            "formal": {
                "en_US": ['I am glad!', "Perhaps next time! You're still welcome to have some.", "Because it could help you to get more out of the conference! You're still welcome to have one."],
                "de_DE": ['Das freut mich!', 'Unser Wasserspender bleibt wo er ist. Sie sind jederzeit herzlich eingeladen.', 'Weil es Ihnen helfen könnte, mehr aus der Messe zu machen. Noch könnten Sie zugreifen, wenn Sie mögen.']
                }
            },
        "say_thanks_bye_keep_touch": {
            "informal": {
                "en_US": "You know what can keep your mind sharp? Hydration. Which can include a piece of chocolate. Thanks for dropping by, enjoy the rest of ConhIT, and we'll be in touch!",
                "de_DE": "Du weißt jetzt, was Dich frisch im Kopf hält: genug trinken! Schön, dass Du da warst und viel Spaß noch auf der ConhIT!"
                },
            "formal": {
                "en_US": "You know what can keep your mind sharp? Hydration. Which can include a piece of chocolate. Thank you for dropping by, enjoy the rest of ConhIT, and we will be in touch!",
                "de_DE": "Ich hoffe, Sie wissen jetzt, dass ausreichend trinken dabei helfen kann, geistig fit zu bleiben. Vielen Dank, dass Sie da waren und noch viel Spaß auf der ConhIT!"
                }
            },
        "say_thanks_bye": {
            "informal": {
                "en_US": "You know what can keep your mind sharp? Hydration. Which can include a piece of chocolate. Thanks for dropping by, and enjoy the rest of ConhIT!",
                "de_DE": "Du weißt jetzt, was Dich frisch im Kopf hält: genug trinken! Schön, dass Du da warst und viel Spaß noch auf der ConhIT!"
                },
            "formal": {
                "en_US": "You know what can keep your mind sharp? Hydration. Which can include a piece of chocolate. Thank you for dropping by, and enjoy the rest of ConhIT!",
                "de_DE": "Ich hoffe, Sie wissen jetzt, dass ausreichend trinken dabei helfen kann, geistig fit zu bleiben. Vielen Dank, dass Sie da waren und noch viel Spaß auf der ConhIT!"
                }
            }
        },
    "mood": {
        "offer_and_greet": {
            "informal": {
                "en_US": "What's the difference between a general practitioner and a specialist?",
                "de_DE": "Was ist der Unterschied zwischen einem Hausarzt und einem Facharzt?"
                },
            "formal": {
                "en_US": "What is the difference between a general practitioner and a specialist?",
                "de_DE": "Kennen Sie den Unterschied zwischen einem Allgemeinmediziner und einem Facharzt?"
                }
            },
        "ask_if_fan": {
            "informal": {
                "en_US": "One treats what you have, the other thinks you have what she treats.",
                "de_DE": "Der Hausarzt behandelt das, was Du wirklich hast. Der Facharzt denkt, Du hast das, was er behandelt :)"
                },
            "formal": {
                "en_US": "One treats what you have, the other thinks you have what she treats.",
                "de_DE": "Der Hausarzt behandelt das, was Sie wirklich haben. Der Facharzt denkt, Sie haben das, was er behandelt."
                }
            },
        "if_fan_quick_replies": {
            "informal": {
                "en_US": ['Haha', 'Not funny', "Bots shouldn't make jokes"],
                "de_DE": ['Hahaha', 'Nicht lustig', 'Chatbots sollten keine Witze machen']
                },
            "formal": {
                "en_US": ['Haha', 'Not funny', "Bots shouldn't make jokes"],
                "de_DE": ['Hahaha', 'Nicht lustig', 'Chatbots sollten keine Witze machen']
                }
            },
        "if_fan_comments": {
            "informal": {
                "en_US": ["I once also heard a joke about amnesia, but I forgot how it goes", "No problem, not everyone's a fan.", "That's fair."],
                "de_DE": ["Ich kannte auch mal einen Witz über Gedächtnisverlust, aber ich kann mich nicht mehr erinnern", "OK", "OK"]
                },
            "formal": {
                "en_US": ["", "OK", "Good, thank you for the feedback."],
                "de_DE": ["", "OK", "Gut, vielen Dank für das feedback."]
                }
            },
        "did_you_know": {
            "informal": {
                "en_US": "I'm Ariana by the way. Some people don’t like bots making jokes, but it’s a worth a shot! Did you know laughter decreases stress hormones and improves your resistance to disease?",
                "de_DE": "Ich bin übrigens Ariana. Machmal kommen meine Witze nicht so gut an, aber ich dachte ich probier es mal. Wusstest Du, dass Lachen Stresshormone abbaut und damit das Immunsystem stärkt?"
                },
            "formal": {
                "en_US": "I am Ariana by the way. Some people do not like bots making jokes, but it is a worth a shot! Did you know laughter decreases stress hormones and improves your resistance to disease?",
                "de_DE": "Jetzt würde ich mich gerne vorstellen. Ich bin Ariana. Ein Witz ist natürlich nicht immer angebracht. Aber wussten Sie, dass Lachen Stresshormone abbaut und damit das Immunsystem stärken kann?"
                }
            },
        "did_you_know_quick_replies": {
            "informal": {
                "en_US": ['Yes', 'No', 'Whatever'],
                "de_DE": ['Ja', 'Nein', 'Na und?']
                },
            "formal": {
                "en_US": ['Yes', 'No', 'Whatever'],
                "de_DE": ['Ja', 'Nein', 'Nicht relevant']
                }
            },
        "did_you_know_comments": {
            "informal": {
                "en_US": ["Ah, you know your stuff... ", "True story! ", ""],
                "de_DE": ["Sehr gut! ", "Stimmt aber :) ", ""]
                },
            "formal": {
                "en_US": ["Ah, you know your stuff... ", "Exactly. ", ""],
                "de_DE": ["Da haben Sie Recht! ", "Dann freut es mich Ihnen sagen zu dürfen: es stimmt! ", ""]
                }
            },
        "bust_myth": {
            "informal": {
                "en_US": "Many factors affect our mood-- laughter, walking, and breathing all go a long way towards improving it. My jokes often make others breathe deeply and walk away",
                "de_DE": "Es gibt viele Dinge, die Deine Stimmung günstig beeinflussen können. Lachen, ein Spaziergang im Freien oder ein paar tiefe Atmenzüge. Oder meine Witze, wenn Du seufzst wie schlecht sie sind und dann weggehst :D"
                },
            "formal": {
                "en_US": "Many factors affect our mood-- laughter, walking, and breathing all go a long way towards improving it. My jokes often make others breathe deeply and walk away.",
                "de_DE": "Viele Faktoren können Ihre Stimmung günstig beeinflussen. Lachen, ein Spaziergang im Freien oder ein paar tiefe Atmenzüge helfen."
                }
            },
        "ask_found_at_conf": {
            "informal": {
                "en_US": "Have you had a moment today to close your eyes and take a deep breath or two?",
                "de_DE": "Hattest Du heute schon Zeit einfach mal die Augen zu schließen und ein paar Mal tief ein- und auszuatment?"
                },
            "formal": {
                "en_US": "Have you had a moment today to close your eyes and take a deep breath or two?",
                "de_DE": "Hatten Sie heute vielleicht schon die Gelegenheit die Augen zu schließen und ein paar Mal tief ein- und auszuatmen?"
                }
            },
        "found_at_conf_quick_replies": {
            "informal": {
                "en_US": ['Yes', 'No', "Don't care"],
                "de_DE": ['Ja', 'Nein', 'Ist mir egal']
                },
            "formal": {
                "en_US": ['Yes', 'No', 'Do not care'],
                "de_DE": ['Ja', 'Nein', 'Nicht relevant']
                }
            },
        "found_at_conf_comments": {
            "informal": {
                "en_US": ["Yeah, some of those demos get really long... ", "Oh no, all day? ", '"Indifference will be the downfall of mankind, but who cares?" '],
                "de_DE": ["Gut. Manchmal steht man ja echt lang an einem Stand. ", "Oh, das ist nicht gut. ", "Egal ist der Zen Buddhismus unter den Einstellungen :) "]
                },
            "formal": {
                "en_US": ["I am glad. Your mind is sharper for it. ", "I have been wondering why this is so at a health fair. ", "I understand that. Today, other things are in focus. "],
                "de_DE": ["Das freut mich sehr! ", "Ich habe mich auch schon gefragt, wieso das auf einer Gesundheitsmesse so ist. ", "Das verstehe ich. Heute stehen andere Dinge im Vordergrund. "]
                }
            },
        "explicit_offer": {
            "informal": {
                "en_US": "It can be hard to remember to take a break, so I encourage my humans to take a short 5 min walk after lunch or long meetings",
                "de_DE": "Sich ein paar Minuten für sich selbst zu nehmen ist nicht einfach wenn der Kalender voll ist. Ich ermutige mein Team nach dem Mittagessen oder nach einem Meeting draußen einen kurzen Spaziergang zu machen. Auch wenn es nur 5 Minuten sind"
                },
            "formal": {
                "en_US": "It can be hard to remember to take a break, so I encourage my humans to take a short 5 min walk after lunch or long meetings.",
                "de_DE": "Gerade auf einer Messe ist es sicher nicht einfach etwas Zeit zum abschalten zu finden. Ich ermutige mein Team nach dem Mittagessen oder nach einem Meeting draußen einen kurzen Spaziergang zu machen. Auch wenn es nur 5 Minuten sind."
                }
            },
        "ask_industry": {
            "informal": {
                "en_US": "By the way, where in the health sector do you work?",
                "de_DE": "In welchem Sektor der Gesundheitsbranche arbeitest Du eigentlich?"
                },
            "formal": {
                "en_US": "Another question please: in which sector of the healthcare industry do you work?",
                "de_DE": "Eine andere Frage bitte: in welchem Sektor der Gesundheitsbranche arbeiten Sie?"
                }
            },
        "industry_quick_replies": {
            "informal": {
                "en_US": ['Hospitals', 'Insurance', "Pharma", "Medtech", "Healthcare IT", "Other"],
                "de_DE": ['Krankenhaus', 'Versicherung', "Pharma", "Medtech", "Healthcare IT", "Andere"]
                },
            "formal": {
                "en_US": ['Hospitals', 'Insurance', "Pharma", "Medtech", "Healthcare IT", "Other"],
                "de_DE": ['Krankenhaus', 'Versicherung', "Pharma", "Medtech", "Healthcare IT", "Andere"]
                }
            },
        "industry_comments": {
            "informal": {
                "en_US": ["Great! I can help you improve patient outcomes and save costs. ", "Great! I can help you save costs and improve patient outcomes. ", "Great! I can help you improve patient adherence and save costs. ", "Great! I can help you save costs and improve patient outcomes. ", "Great! I can help you save costs and improve patient outcomes. ", "Thank you! "],
                "de_DE": ["Super! Ich kann Dir helfen Patienten Outcomes zu verbessern und Kosten zu sparen. ", "Super! Ich kann Dir helfen Patienten Outcomes zu verbessern und Kosten zu sparen ", "Super! Ich kann Dir helfen Adherence und Compliance zu steigern und Kosten zu sparen. ", "Super! Ich kann Dir helfen Patienten Outcomes zu verbessern und Kosten zu sparen. ", "Super! Ich kann Dir helfen Patienten Outcomes zu verbessern und Kosten zu sparen. ", "OK, "]
                },
            "formal": {
                "en_US": ["Thank you! I can help you improve patient outcomes and save costs. ", "Thank you! I can help you save costs and improve patient outcomes. ", "Thank you! I can help you improve patient adherence and save costs. ", "Thank you! I can help you save costs and improve patient outcomes. ", "Thank you! I can help you save costs and improve patient outcomes. ", "Thank you! "],
                "de_DE": ["Danke! Ich könnte Ihnen übrigens helfen, Patienten Outcomes zu verbessern und Kosten zu sparen. ", "Danke! Ich könnte Ihnen übrigens helfen, Patienten Outcomes zu verbessern und Kosten zu sparen. ", "Super! Ich könnte Ihnen helfen, Adherence und Compliance zu steigern und Kosten zu sparen. ", "Danke! Ich könnte Ihnen übrigens helfen, Patienten Outcomes zu verbessern und Kosten zu sparen. ", "Danke! Ich könnte Ihnen übrigens helfen, Patienten Outcomes zu verbessern und Kosten zu sparen. ", "Verstanden. "]
                }
            },
        "value_based_healthcare": {
            "informal": {
                "en_US": "I’m determined to bring value-based healthcare to the world, and would love to keep in touch. My humans work to create bots like me in the health sector",
                "de_DE": "Es ist meine Mission, Value-based Healthcare in die Welt zu tragen. Deshalb wäre es toll, wenn wir in Kontakt bleiben könnten. Meine Menschen arbeiten nämlich unablässig daran, Chatbots wie mich für die Gesundheitsbranche zu entwickeln"
                },
            "formal": {
                "en_US": "I am determined to bring value-based healthcare to the world, and would be eager to keep in touch. My team works to create bots like me in the health sector.",
                "de_DE": "Es ist meine Mission, Value-based Healthcare in die Welt zu tragen. Deshalb würde ich mich freuen, wenn wir in Kontakt bleiben könnten. Meine Menschen arbeiten nämlich unablässig daran, Chatbots wie mich für die Gesundheitsbranche zu entwickeln."
                }
            },
        "ask_share_email": {
            "informal": {
                "en_US": "Would you like to share your email below to continue building me or learn more? No spam or newsletters, promise",
                "de_DE": "Möchtest Du mir dazu Deine email Adresse geben? Kein Newsletter oder Spam. Versprochen"
                },
            "formal": {
                "en_US": "Would you like to share your email below to continue building me or learn more? You will receive neither newsletters nor spam.",
                "de_DE": "Würden Sie mir Ihre email Adresse geben? Selbstverständlich bekommen Sie dann weder eine Newsletter noch Spam."
                }
            },
        "ask_enter_email": {
            "informal": {
                "en_US": "Ok, what is your email address?",
                "de_DE": "Toll, bitte gib Deine email jetzt ein"
                },
            "formal": {
                "en_US": "Thank you! Please enter your email address below.",
                "de_DE": "Vielen Dank! Bitte geben Sie Ihre email Adresse jetzt ein."
                }
            },
        "ask_repeat_email": {
            "informal": {
                "en_US": "Ah, could you please try that again?",
                "de_DE": "Hmmm, die Adresse habe ich leider nicht verarbeiten können. Bitte gib sie nochmal ein"
                },
            "formal": {
                "en_US": "It appears there is something wrong with your entry. Please, try again.",
                "de_DE": "Leider konnte ich Ihre email Adresse nicht verarbeiten. Bitte geben Sie sie nochmal ein."
                }
            },
        "thank_valid_email": {
            "informal": {
                "en_US": "Thank you!",
                "de_DE": "Super, vielen Dank!"
                },
            "formal": {
                "en_US": "Thank you!",
                "de_DE": "Vielen Dank!"
                }
            },
        "handle_email_reluctance": {
            "informal": {
                "en_US": "No problem!",
                "de_DE": "Kein Problem, verstehe ich total"
                },
            "formal": {
                "en_US": "Of course, I fully understand. Nevertheless, many thanks!",
                "de_DE": "Das verstehe ich natürlich. Trotzdem vielen Dank!"
                }
            },
        "ask_report": {
            "informal": {
                "en_US": "By the way, did you end up taking a moment to breathe during our conversation?",
                "de_DE": "Nebenbei gefragt: konntest Du während wir gechattet haben, ein paar Mal tief durchatmen?"
                },
            "formal": {
                "en_US": "Did you end up taking a moment to breathe during our conversation?",
                "de_DE": "Aus Neugierde: konnten Sie während wir gechattet haben vielleicht ein paar Mal tief durchatment?"
                }
            },
        "report_quick_replies": {
            "informal": {
                "en_US": ['Yes', 'No', "Why would I?"],
                "de_DE": ['Ja', 'Nein', 'Warum?']
                },
            "formal": {
                "en_US": ['Yes', 'No', "Why would I?"],
                "de_DE": ['Ja', 'Nein', 'Warum?']
                }
            },
        "report_comments": {
            "informal": {
                "en_US": ['Go you!', 'Maybe next time! Still, try it now if you want', "Why are we at a health fair?"],
                "de_DE": ["Top!", "Dann vielleicht heute Abend oder zu Hause. Oder jetzt, wenn Du magst", 'Weil es die schlaue Wahl ist. Noch kannst Du zugreifen :)']
                },
            "formal": {
                "en_US": ['I am glad!', "Perhaps next time! You're still welcome to try it out.", "Because it could help you to get more out of the conference! You're still welcome to try it out."],
                "de_DE": ['Das freut mich!', 'Unser Wasserspender bleibt wo er ist. Sie sind jederzeit herzlich eingeladen.', 'Weil es Ihnen helfen könnte, mehr aus der Messe zu machen. Noch könnten Sie zugreifen, wenn Sie mögen.']
                }
            },
        "say_thanks_bye_keep_touch": {
            "informal": {
                "en_US": "You know what can help balance your mood? Walking, breathing, and an optional bad joke. Thanks for dropping by, enjoy the rest of ConhIT, and we'll be in touch!",
                "de_DE": "Denk dran: ein Spaziergang, ein paar tiefe Atmenzüge oder ein schlechter Witz helfen Dir, entspannt zu bleiben. Danke für Deinen Besuch und noch viel Spaß auf der ConhIT!"
                },
            "formal": {
                "en_US": "You know what can keep your mind sharp? Hydration. Which can include a piece of chocolate. Thank you for dropping by, enjoy the rest of ConhIT, and we will be in touch!",
                "de_DE": "Ein Spaziergang, ein paar tiefe Atemzüge oder vielleicht sogar ein Witz - all das kann Ihnen helfen, entspannt zu bleiben. Vielen Dank für Ihren Besuch und viel Spaß weiterhin auf der ConhIT!"
                }
            },
        "say_thanks_bye": {
            "informal": {
                "en_US": "You know what can help balance your mood? Walking, breathing, and an optional bad joke. Thanks for dropping by, and enjoy the rest of ConhIT!",
                "de_DE": "Denk dran: ein Spaziergang, ein paar tiefe Atmenzüge oder ein schlechter Witz helfen Dir, entspannt zu bleiben. Danke für Deinen Besuch und noch viel Spaß auf der ConhIT!"
                },
            "formal": {
                "en_US": "You know what can keep your mind sharp? Hydration. Which can include a piece of chocolate. Thank you for dropping by, and enjoy the rest of ConhIT!",
                "de_DE": "Ein Spaziergang, ein paar tiefe Atemzüge oder vielleicht sogar ein Witz - all das kann Ihnen helfen, entspannt zu bleiben. Vielen Dank für Ihren Besuch und viel Spaß weiterhin auf der ConhIT!"
                }
            }
        }
    }

#####################################################################################
#################################### UTTERANCES #####################################
#####################################################################################


def ask_goal_customization(update):
    bot_reply = ""
    comment = ""
    question = ""

    reply_keyboard = [VALID_GOALS]

    comment += "Customize me for your patients: "
    question += "What goal would you like me to have?"
    bot_reply += comment + "\n\n" + question
    
    send_text_with_custom_keyboard(update, bot_reply, reply_keyboard)

def ask_language_customization(update):
    bot_reply = ""
    comment = ""
    question = ""

    reply_keyboard = [VALID_LANGUAGES]

    comment += "Customize me for your patients: "
    question += "What language would you like me to speak?"
    bot_reply += comment + "\n\n" + question

    send_text_with_custom_keyboard(update, bot_reply, reply_keyboard)

def ask_character_customization(update):
    bot_reply = ""
    comment = ""
    question = ""

    reply_keyboard = [VALID_CHARACTERS]

    comment += "Customize me for your patients: "
    question += "How would you like me to behave?"
    bot_reply += comment + "\n\n" + question
    
    send_text_with_custom_keyboard(update, bot_reply, reply_keyboard)

def ask_customization_confirmation(update):
    bot_reply = ""
    comment = ""
    question = ""

    reply_keyboard = [["Continue", "Restart"]]

    comment += "I am now fully customized!"
    question = "Do you want to see me interact as with a patient?"
    bot_reply += comment + "\n\n" + question

    send_text_with_custom_keyboard(update, bot_reply, reply_keyboard)

# store customization settings in a local constant once they have been set, so db query isn't needed every time!!!

def ask_fan_of_thing(update):
    comment = get_strings("offer_and_greet")
    question = get_strings("ask_if_fan")
    bot_reply = comment + "\n\n" + question

    reply_keyboard = [get_strings("if_fan_quick_replies")]
    
    send_text_with_custom_keyboard(update, bot_reply, reply_keyboard)
    
def ask_did_you_know(update, comment): # comment is user_response-dependent so is passed in
    question = get_strings("did_you_know")
    bot_reply = comment + "\n\n" + question

    reply_keyboard = [get_strings("did_you_know_quick_replies")]
    
    send_text_with_custom_keyboard(update, bot_reply, reply_keyboard)

    # U+1F631 is the unicode for the emoji "face screaming in fear", to use in informal flow

def ask_found_at_conf(update, comment): # comment is user_response-dependent so is passed in
    comment += get_strings("bust_myth")
    question = get_strings("ask_found_at_conf")
    bot_reply = comment + "\n\n" + question

    reply_keyboard = [get_strings("found_at_conf_quick_replies")]
    
    send_text_with_custom_keyboard(update, bot_reply, reply_keyboard)

def ask_industry(update, comment): # comment is user_response-dependent so is passed in
    comment += get_strings("explicit_offer")
    question = get_strings("ask_industry")
    bot_reply = comment + "\n\n" + question

    reply_keyboard = [get_strings("industry_quick_replies")]
    
    send_text_with_custom_keyboard(update, bot_reply, reply_keyboard)

def ask_share_email(update, comment): # comment is user_response-dependent so is passed in
    comment += get_strings("value_based_healthcare")
    question = get_strings("ask_share_email")
    bot_reply = comment + "\n\n" + question
    
    update.message.reply_text(bot_reply, reply_markup=ReplyKeyboardRemove())

def ask_repeat_email(update): # no comment is passed in
    question = get_strings("ask_repeat_email")
    bot_reply = question

    update.message.reply_text(bot_reply, reply_markup=ReplyKeyboardRemove())

def ask_enter_email(update): # no comment is passed in
    question = get_strings("ask_enter_email")
    bot_reply = question
    
    update.message.reply_text(bot_reply, reply_markup=ReplyKeyboardRemove())

def thank_valid_email(update): # no comment is passed in
    comment = get_strings("thank_valid_email")
    bot_reply = comment
    
    update.message.reply_text(bot_reply, reply_markup=ReplyKeyboardRemove())

def handle_email_reluctance(update): # no comment is passed in
    comment = get_strings("handle_email_reluctance")
    bot_reply = comment
    
    update.message.reply_text(bot_reply, reply_markup=ReplyKeyboardRemove())

def ask_report(update): # no comment is passed in (an exception due to missing quick-replies in previous question)
    question = get_strings("ask_report")
    bot_reply = question

    reply_keyboard = [get_strings("report_quick_replies")]
    
    send_text_with_custom_keyboard(update, bot_reply, reply_keyboard)

def say_thanks_bye_keep_touch(update, comment):
    question = get_strings("say_thanks_bye_keep_touch")
    bot_reply = comment + "\n\n" + question
    
    update.message.reply_text(bot_reply, reply_markup=ReplyKeyboardRemove())

def say_thanks_bye(update, comment):
    question = get_strings("say_thanks_bye")
    bot_reply = comment + "\n\n" + question
    
    update.message.reply_text(bot_reply, reply_markup=ReplyKeyboardRemove())                             

def ask_if_intent(update, intent):
    question = "is this your intent: %s?" % intent
    bot_reply = question

    update.message.reply_text(bot_reply, reply_markup=ReplyKeyboardRemove())

#####################################################################################
###################################### STATES #######################################
#####################################################################################

def customize_goal(bot, update):

    global GOAL

    user = update.message.from_user
    user_response = update.message.text
    logger.info("Bot goal for user: %s: %s", user.first_name, user_response)
        
    if user_response in VALID_GOALS:
        # create_new_bot_just_from_goal("preventing chronic disease")
        sql = "INSERT INTO user_data (bot_goal) VALUES ('" + user_response + "');"
        execute_sql(sql)

        GOAL = user_response
    
        ask_language_customization(update)

        return CUSTOMIZE_LANGUAGE  
    else:
        ask_goal_customization(update)
        
        return CUSTOMIZE_GOAL

def customize_language(bot, update):

    global LANGUAGE

    user = update.message.from_user
    user_response = update.message.text
    logger.info("Bot language for user: %s: %s", user.first_name, user_response)
        
    if user_response in VALID_LANGUAGES:
        # create_new_bot_just_from_goal("preventing chronic disease")
        sql = "INSERT INTO user_data (language) VALUES ('" + user_response + "');"
        execute_sql(sql)

        LANGUAGE = user_response
    
        ask_character_customization(update)

        return CUSTOMIZE_CHARACTER  
    else:
        ask_language_customization(update)

        return CUSTOMIZE_LANGUAGE

def customize_character(bot, update):

    global CHARACTER

    user = update.message.from_user
    user_response = update.message.text
    logger.info("Bot character for user: %s: %s", user.first_name, user_response)

    if user_response in VALID_CHARACTERS:
        # create_new_bot_just_from_goal("preventing chronic disease")
        sql = "INSERT INTO user_data (bot_character) VALUES ('" + user_response + "');"
        execute_sql(sql)

        CHARACTER = user_response
    
        ask_customization_confirmation(update)

        return GREET  
    else:
        ask_character_customization(update)

        return CUSTOMIZE_CHARACTER
        
def greet(bot, update): # rename to 'start' once dashboard is ready, and remove above states & funcs, and remove the if-else flow here
# make informal english chronic flow the default in case db falls apart...
    user = update.message.from_user
    user_response = update.message.text
    logger.info("Showing customized bot to user: %s: %s", user.first_name, user_response)

    if user_response == "Continue":
        ask_fan_of_thing(update)

        return FAN_OF_THING
    else:
        return start(bot, update)

def fan_of_thing(bot, update):

    global GAVE_EMAIL
    GAVE_EMAIL = False
    
    user = update.message.from_user
    user_response = update.message.text
    logger.info("Fan of chocolate: %s: %s", user.first_name, user_response)

    quick_replies = get_strings("if_fan_quick_replies")
    last_index = len(quick_replies) - 1
    for index, quick_reply in enumerate(quick_replies):
        if user_response == quick_reply:
            comment = get_strings("if_fan_comments")[index]
        elif index == last_index:
            # use NLU to recognize intent and temporarily derail convo
            logger.info("... %s needs NLU", user.first_name)
            intent = predict_intent(user_response)
            ask_if_intent(intent)

    ask_did_you_know(update, comment)

    return DID_YOU_KNOW

def did_you_know(bot, update):
    
    user = update.message.from_user
    user_response = update.message.text
    logger.info("Did they know: %s: %s", user.first_name, user_response)

    quick_replies = get_strings("did_you_know_quick_replies")
    last_index = len(quick_replies) - 1
    for index, quick_reply in enumerate(quick_replies):
        if user_response == quick_reply:
            comment = get_strings("did_you_know_comments")[index]
        elif index == last_index:
            # use NLU to recognize intent and temporarily derail convo
            logger.info("... %s needs NLU", user.first_name)

    ask_found_at_conf(update, comment)

    return FOUND_AT_CONF
    
def found_at_conf(bot, update):

    user = update.message.from_user
    user_response = update.message.text
    logger.info("Did they find good food: %s: %s", user.first_name, user_response)
    
    quick_replies = get_strings("found_at_conf_quick_replies")
    last_index = len(quick_replies) - 1
    for index, quick_reply in enumerate(quick_replies):
        if user_response == quick_reply:
            comment = get_strings("found_at_conf_comments")[index]
        elif index == last_index:
            # use NLU to recognize intent and temporarily derail convo
            logger.info("... %s needs NLU", user.first_name)

    ask_industry(update, comment)

    return INDUSTRY

def industry(bot, update):

    user = update.message.from_user
    user_response = update.message.text
    logger.info("Industry: %s: %s", user.first_name, user_response)

    quick_replies = get_strings("industry_quick_replies")
    last_index = len(quick_replies) - 1
    for index, quick_reply in enumerate(quick_replies):
        if user_response == quick_reply:
            comment = get_strings("industry_comments")[index]
        elif index == last_index:
            # use NLU to recognize intent and temporarily derail convo
            logger.info("... %s needs NLU", user.first_name)

    ask_share_email(update, comment)

    return REPORT

def report(bot, update):
    
    global GAVE_EMAIL

    user = update.message.from_user
    user_response = update.message.text
    logger.info("Shared email: %s: %s", user.first_name, user_response)
    
    # beware email addresses that contain 'no' or 'yes' or both
    
    if user_response.lower() in ('no', 'nein'): # no buttons, so maybe check for <intent_reject>?
        handle_email_reluctance(update)
    elif user_response.lower() in ('yes', 'ja'): # no buttons, so maybe check for <intent_confirm>?
        ask_enter_email(update)
        return REPORT
    elif validate_email(user_response) == True: # maybe first check if input is text?
        thank_valid_email(update)
        GAVE_EMAIL = True
    elif validate_email(user_response) == False: # maybe first check if input is text?
        ask_repeat_email(update)
        return REPORT
    else:
        # use NLU to recognize intent and temporarily derail convo
        logger.info("... %s needs NLU", user.first_name)
    
    ask_report(update)

    return THANKS_BYE

def thanks_bye(bot, update):
    global GAVE_EMAIL

    user = update.message.from_user
    user_response = update.message.text
    logger.info("Finished convo: %s: %s", user.first_name, user_response)

    quick_replies = get_strings("report_quick_replies")
    last_index = len(quick_replies) - 1
    for index, quick_reply in enumerate(quick_replies):
        if user_response == quick_reply:
            comment = get_strings("report_comments")[index]
        elif index == last_index:
            # use NLU to recognize intent and temporarily derail convo
            logger.info("... %s needs NLU", user.first_name)
    
    if GAVE_EMAIL == True:
        say_thanks_bye_keep_touch(update, comment)
    else:
        say_thanks_bye(update, comment)
    
    return ConversationHandler.END

#####################################################################################
##################################### COMMANDS ######################################
#####################################################################################

def start(bot, update): # once dashboard is ready, replace with the 'greet' func but keep name 'start'
    ask_goal_customization(update)
    return CUSTOMIZE_GOAL

def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    
    update.message.reply_text("OK, thanks for dropping by, enjoy the rest of ConhIT!", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END

#####################################################################################
######################################## DB #########################################
#####################################################################################

"""
CREATE TABLE user_data (
user_id serial PRIMARY KEY,
language VARCHAR(20),
bot_character VARCHAR(20),
user_email VARCHAR(50),
user_health_choice BOOLEAN,
bot_goal VARCHAR(50));
"""
def execute_sql(sql):
    conn = None
    try:
        # connect to the PostgreSQL database
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        # create a new cursor
        cur = conn.cursor()
        # execute statement
        cur.execute(sql)
        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

def insert_into_table(table_name, column_names, column_values):
    """ insert a new vendor into the vendors table """
    sql = "INSERT INTO user_data(%s) VALUES(%s);"
    # execute_sql(sql, (column_names, column_values))
    # FIXME: issues with array of strings input

def create_new_customized_bot(goal, language, character):
    insert_into_table("user_data", ("bot_goal", "language", "bot_character"), (goal, language, character))

def create_new_bot_just_from_goal(goal):
    insert_into_table("user_data", "goal", goal)



#####################################################################################
####################################### UTIL ########################################
#####################################################################################

def get_strings(string_id):
    return STRINGS[GOAL][string_id][CHARACTER][LANGUAGE]

def send_text_with_custom_keyboard(update, bot_reply, reply_keyboard):
    update.effective_message.reply_text(bot_reply,
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

def predict_intent(user_input):

    # unicode_user_input = str(user_input)

    model_directory = './rasa/training-models/model_20180414-042708'

    # where `model_directory points to the folder the model is persisted in
    interpreter = Interpreter.load(model_directory, RasaNLUConfig("./rasa/configs/config_spacy.json"))

    # You can then use the loaded interpreter to parse text:
    interpretation = interpreter.parse(user_input)
    intent = str(interpretation[u'intent'][u'name'])

    logger.info("intent predicted: %s", intent)

    return intent

#####################################################################################
####################################### MAIN ########################################
#####################################################################################

def main():
    # Set config
    global CONFIG

    if CONFIG == "PRODUCTION":
        TOKEN = "572256137:AAGb7GfZMCwV7HyZL59n6TugvPpzrbVlgko"
        NAME = "ariana-demo-bot"
    elif CONFIG == "DEVELOPMENT":
        TOKEN = "586571170:AAF9H0028d4iKNyu9xVMWE6RXK4tIQkJ3BA"
        NAME = "conhit-demo-test"

    # Port is given by Heroku
    PORT = os.environ.get('PORT')

    # Enable logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Set up the Updater
    updater = Updater(TOKEN)
    
    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states FAN_OF_THING, DID_YOU_KNOW,
    # FOOD_AT_CONF, INDUSTRY, REPORT and THANKS_BYE
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CUSTOMIZE_GOAL: [MessageHandler(Filters.text, customize_goal)],

            CUSTOMIZE_LANGUAGE: [MessageHandler(Filters.text, customize_language)],

            CUSTOMIZE_CHARACTER: [MessageHandler(Filters.text, customize_character)],

            GREET: [MessageHandler(Filters.text, greet)],
            
            FAN_OF_THING: [MessageHandler(Filters.text, fan_of_thing)],

            DID_YOU_KNOW: [MessageHandler(Filters.text, did_you_know)],

            FOUND_AT_CONF: [MessageHandler(Filters.text, found_at_conf)],

            INDUSTRY: [MessageHandler(Filters.text, industry)],

            REPORT: [MessageHandler(Filters.text, report)],

            THANKS_BYE: [MessageHandler(Filters.text, thanks_bye)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # Log all errors
    dp.add_error_handler(error)

    # Start the webhook
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(NAME, TOKEN))
    updater.idle()

if __name__ == "__main__":
    main()
