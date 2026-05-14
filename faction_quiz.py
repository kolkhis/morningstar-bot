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

class FactionChoiceView(discord.ui.View):
    def __init__(self, user: discord.Member, target_faction: str | None = None):
        super().__init__(timeout=300)
        self.user = user
        self.target_faction = target_faction
        self.responses = {}

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def assign_role(self, interaction: discord.Interaction, faction: str):
        if interaction.guild is None:
            await interaction.response.send_message("Guild not found. User must be in a server.", ephemeral=True)
            return

        role_id = SKELETON_ROLE_ID if faction == "Skeleton" \
            else SIREN_ROLE_ID if faction == "Siren" \
            else None
        opposite_role_id = SIREN_ROLE_ID if faction == "Skeleton" \
            else SKELETON_ROLE_ID if faction == "Siren" \
            else None

        if role_id is None or opposite_role_id is None:
            await interaction.response.send_message("Invalid faction.", ephemeral=True)
            return
        role = interaction.guild.get_role(role_id)
        opposite_role = interaction.guild.get_role(opposite_role_id)

        if role is None:
            await interaction.response.send_message(f"Role for {faction} not found. Please contact an administrator.", ephemeral=True)
            return
        member = interaction.guild.get_member(interaction.user.id)        
        if member is None:
            await interaction.response.send_message(f"Member {interaction.user.name} not found in guild (server).", ephemeral=True)
            return
        roles_to_remove = []
        if opposite_role and opposite_role in member.roles:
            roles_to_remove.append(opposite_role)
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason="Faction change")

        if role not in member.roles:
            await member.add_roles(role, reason="Faction quiz result")

        await interaction.response.edit_message(
            content=f"You have been assigned to the {faction} faction!",
            embed=None,
            view=None
        )

    @discord.ui.button(label="Skeleton", style=discord.ButtonStyle.success)
    async def skeleton_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_role(interaction, "Skeleton")

    @discord.ui.button(label="Siren", style=discord.ButtonStyle.success)
    async def siren_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_role(interaction, "Siren")


    # @discord.ui.select(
    #     placeholder="Choose your answer...",
    #     options=[
    #         discord.SelectOption(label=answer[0], value=answer[1])
    #         for question in FACTION_QUESTIONS
    #         for answer in question["answers"]
    #     ],
    # )
    # async def select_answer(self, interaction: discord.Interaction, select: discord.ui.Select):
    #     if interaction.user.id != self.user_id:
    #         await interaction.response.send_message("This is not your quiz!", ephemeral=True)
    #         return

    #     question_index = len(self.responses) // 4
    #     if question_index >= len(FACTION_QUESTIONS):
    #         await interaction.response.send_message("You have already completed the quiz!", ephemeral=True)
    #         return

    #     selected_faction = select.values[0]
    #     self.responses[question_index] = selected_faction

    #     if len(self.responses) == len(FACTION_QUESTIONS) * 4:
    #         faction_counts = Counter(self.responses.values())
    #         most_common_faction = faction_counts.most_common(1)[0][0]
    #         await interaction.response.send_message(f"You belong to the {most_common_faction} faction!", ephemeral=True)
    #         # Here you would add role assignment logic based on
    #         # most_common_faction
