import discord
from discord import app_commands
from discord.ext import commands
from collections import Counter

SKELETON_ROLE_ID: int = 0
SIREN_ROLE_ID: int = 0

FACTION_QUESTIONS = [
  {
        "question": "A stranger offers you power in exchange for betraying someone who trusts you.",
        "answers": [
            ("Accept immediately", "Skeleton"),
            ("Pretend to agree while planning around it", "Siren"),
            ("Refuse", "Abyss Watcher"),
            ("Learn why they made the offer first", "Abyss Watcher"),
        ],
    },
    {
        "question": "What is more dangerous?",
        "answers": [
            ("Love", "Siren"),
            ("Hunger", "Skeleton"),
            ("Knowledge", "Abyss Watcher"),
            ("Desperation", "Skeleton"),
        ],
    },
    {
        "question": "Your enemy falls into the sea during the battle. What do you do?",
        "answers": [
            ("Save them", "Siren"),
            ("Watch them drown", "Skeleton"),
            ("Use them as bait", "Skeleton"),
            ("Ask what they know first", "Abyss Watcher"),
        ],
    },
    {
        "question": "Which matters most?",
        "answers": [
            ("Freedom", "Skeleton"),
            ("Loyalty", "Siren"),
            ("Survival", "Skeleton"),
            ("Truth", "Abyss Watcher"),
        ],
    },
    {
        "question": "A secret could destroy your faction. What do you do?",
        "answers": [
            ("Bury it forever.", "Siren"),
            ("Sell it.", "Skeleton"),
            ("Reveal it publicly.", "Abyss Watcher"),
            ("Study it before deciding.", "Abyss Watcher"),
        ],
    },
    {
        "question": "What creates the strongest ruler?",
        "answers": [
            ("Fear", "Skeleton"),
            ("Devotion", "Siren"),
            ("Intelligence", "Abyss Watcher"),
            ("Mystery", "Siren"),
        ],
    },
    {
        "question": "You discover someone has been spying on your allies. What do you do?",
        "answers": [
            ("Kill them.", "Skeleton"),
            ("Recruit them.", "Siren"),
            ("Expose them", "Abyss Watcher"),
            ("Follow them to their source.", "Abyss Watcher"),
        ],
    },
    {
        "question": "What kind of story do you respect the most?",
        "answers": [
            ("Tragedy", "Siren"),
            ("Revenge", "Skeleton"),
            ("Sacrifice", "Siren"),
            ("Discovery", "Abyss Watcher"),
        ],
    },
    {
        "question": "A powerful relic whispers your name. What do you do?",
        "answers": [
            ("Take it.", "Skeleton"),
            ("Destroy it.", "Abyss Watcher"),
            ("Hide it.", "Siren"),
            ("Listen first.", "Abyss Watcher"),
        ],
    },
    {
        "question": "Which is worse?",
        "answers": [
            ("Being forgotten.", "Siren"),
            ("Being powerless.", "Skeleton"),
            ("Being betrayed.", "Siren"),
            ("Never knowing the truth.", "Abyss Watcher"),
        ],
    },
    {
        "question": "A city burns in the distance. What do you do?",
        "answers": [
            ("Loot what remains.", "Skeleton"),
            ("Rescue survivors.", "Siren"),
            ("Hunt the one responsible.", "Skeleton"),
            ("Watch, and learn why it happened.", "Abyss Watcher"),
        ],
    },
    {
        "question": "What makes someone truly dangerous?",
        "answers": [
            ("Charm", "Siren"),
            ("Patience", "Abyss Watcher"),
            ("Brutality", "Skeleton"),
            ("Intelligence", "Abyss Watcher"),
        ],
    },
    {
        "question": "If given the chance, which would you rather do?",
        "answers": [
            ("Rule the seas.", "Skeleton"),
            ("Control information.", "Abyss Watcher"),
            ("Become untouchable.", "Skeleton"),
            ("Be remembered forever.", "Siren"),
        ],
    },
    {
        "question": "Someone offers you forbidden knowledge. What do you do?",
        "answers": [
            ("Take it without hesitation.", "Skeleton"),
            ("Take it cautiously.", "Abyss Watcher"),
            ("Refuse it.", "Siren"),
            ("Ask what it costs.", "Abyss Watcher"),
        ],
    },
    {
        "question": "What is your greatest weapon?",
        "answers": [
            ("Words", "Siren"),
            ("Strategy", "Abyss Watcher"),
            ("Fearlessness", "Skeleton"),
            ("Perception", "Abyss Watcher"),
        ],
    },
    {
        "question": "The sea remembers one thing most clearly. What is it?",
        "answers": [
            ("Betrayal", "Siren"),
            ("Blood", "Skeleton"),
            ("Secrets", "Abyss Watcher"),
            ("Ambition", "Skeleton"),
        ],
    },
    {
        "question": "Choose a path.",
        "answers": [
            ("The Siren Song", "Siren"),
            ("The Storm", "Skeleton"),
            ("The Abyss", "Abyss Watcher"),
            ("The Crown", "Skeleton"),
        ],
    },
    {
        "question": "When cornered, what do you do?",
        "answers": [
            ("Manipulate", "Siren"),
            ("Fight", "Skeleton"),
            ("Disappear", "Abyss Watcher"),
            ("Observe", "Abyss Watcher"),
        ],
    },
    {
        "question": "Which would tempt you the most?",
        "answers": [
            ("Forbidden love", "Siren"),
            ("Absolute power", "Skeleton"),
            ("Hidden truth", "Abyss Watcher"),
            ("Endless wealth", "Skeleton"),
        ],
    },
    {
        "question": "At the end of all things, what matters most?",
        "answers": [
            ("Who feared you.", "Skeleton"),
            ("Who loved you.", "Siren"),
            ("What you uncovered.", "Abyss Watcher"),
            ("What survived you.", "Skeleton"),
        ],
    },
]
