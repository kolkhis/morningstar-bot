import discord
from discord import app_commands
from discord.ext import commands
from collections import Counter

SKELETON_ROLE_ID: int = 1504521227979456662
SIREN_ROLE_ID: int = 1504521401099354162

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

def get_existing_faction(member: discord.Member) -> str | None:
    """Return the member's current faction name, or None if unassigned."""
    has_skeleton = any(role.id == SKELETON_ROLE_ID for role in member.roles)
    has_siren = any(role.id == SIREN_ROLE_ID for role in member.roles)
    if has_skeleton:
        return "Skeleton"
    if has_siren:
        return "Siren"
    return None

def already_bound_embed(faction: str) -> discord.Embed:
    embed = discord.Embed(
        title="The Pact Has Already Been Sealed",
        description=(
            f"The tide has already claimed you.\n\n"
            f"You are bound to **{faction}**, and the sea does not forget its oaths.\n\n"
            "If you believe this was a mistake, contact an administrator."
        ),
        color=discord.Color.dark_purple(),
    )
    return embed


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

        # Disallow faction changes if they already have a faction role
        if role in member.roles or opposite_role in member.roles:
            await interaction.response.edit_message(
                content="You have already been assigned a faction role. You may not change factions after taking the quiz. If you believe this is an error, please contact an administrator.",
                embed=None,
                view=None
            )
            return

        # If allowing faction changes, removes opposite role if they have it
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

class QuizQuestionView(discord.ui.View):
    def __init__(self, user: discord.Member, question_index: int, scores: Counter):
        super().__init__(timeout=300)
        self.user = user
        self.question_index = question_index
        self.scores = scores
    
        question = FACTION_QUESTIONS[question_index]
        for answer_text, faction in question["answers"]:
            self.add_item(AnswerButton(answer_text, faction))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id
    async def handle_answer(self, interaction: discord.Interaction, faction: str):
        self.scores[faction] += 1
        next_index = self.question_index + 1

        if next_index >= len(FACTION_QUESTIONS):
            await self.finish_quiz(interaction)
            return

        question = FACTION_QUESTIONS[next_index]
        embed = discord.Embed(
            title=f"Faction Quiz - Question {next_index + 1}/{len(FACTION_QUESTIONS)}",
            description=question["question"],
            color=discord.Color.dark_purple(),
        )
        view = QuizQuestionView(
            user = self.user,
            question_index=next_index,
            scores=self.scores,
        )
        await interaction.response.edit_message(embed=embed, view=view)

    async def finish_quiz(self, interaction: discord.Interaction):
        skeleton = self.scores["Skeleton"]
        siren = self.scores["Siren"]
        abyss = self.scores["Abyss Watcher"]

        if skeleton > siren and skeleton > abyss:
            view = FactionChoiceView(self.user)
            await view.assign_role(interaction, "Skeleton")
            return

        if siren > skeleton and siren > abyss:
            view = FactionChoiceView(self.user)
            await view.assign_role(interaction, "Siren")
            return

        embed = discord.Embed(
            title="The Abyss Watches You",
            description=(
                "Your answers leaned toward **Abyss Watcher**.\n\n"
                "You may now choose which faction to join:"
            ),
            color=discord.Color.dark_teal(),
        )

        embed.add_field(name="Skeleton", value="Power, survival, ambition.", inline=False)
        embed.add_field(name="Siren", value="Loyalty, charm, devotion.", inline=False)

        await interaction.response.edit_message(
            embed=embed,
            view=FactionChoiceView(self.user),
        )

class AnswerButton(discord.ui.Button):
    def __init__(self, label: str, faction: str):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.faction = faction
    async def callback(self, interaction: discord.Interaction):
        view: QuizQuestionView = self.view  # type: ignore
        await view.handle_answer(interaction, self.faction)

class FactionQuizCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="faction_quiz", description="Take the faction assignment quiz")
    async def faction_quiz(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("This command must be used in the server.", ephemeral=True)
            return

        member = interaction.guild.get_member(interaction.user.id)
        if member is None:
            member = await interaction.guild.fetch_member(interaction.user.id)

        question = FACTION_QUESTIONS[0]

        existing_faction = get_existing_faction(member)
        if existing_faction is not None:
            await interaction.response.send_message(
                embed=already_bound_embed(existing_faction),
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"Faction Quiz — Question 1/{len(FACTION_QUESTIONS)}",
            description=question["question"],
            color=discord.Color.dark_purple(),
        )

        view = QuizQuestionView(user=member, question_index=0, scores=Counter())

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(FactionQuizCog(bot))

