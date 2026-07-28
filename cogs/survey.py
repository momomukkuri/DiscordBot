import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import datetime

SURVEY_FILE = "surveys.json"


def load_surveys():
    if not os.path.exists(SURVEY_FILE):
        return {}

    with open(
        SURVEY_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def save_surveys(data):
    with open(
        SURVEY_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )
class SurveyModal(discord.ui.Modal):

    def __init__(self, message_id):
        super().__init__(title="アンケート回答")

        self.message_id = str(message_id)

        self.answer = discord.ui.TextInput(
            label="回答",
            style=discord.TextStyle.paragraph,
            placeholder="回答を入力してください",
            required=True,
            max_length=1000
        )

        self.add_item(self.answer)

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        data = load_surveys()

        survey = data[self.message_id]

        user_id = str(interaction.user.id)

        editing = user_id in survey["answers"]

        survey["answers"][user_id] = self.answer.value

        save_surveys(data)

        survey["answers"][user_id] = self.answer.value

        save_surveys(data)

        channel = interaction.guild.get_channel(
            survey["channel"]
        )

        message = await channel.fetch_message(
            int(self.message_id)
        )

        embed = message.embeds[0]

        embed.set_field_at(
            0,
            name="回答数",
            value=str(len(survey["answers"])),
            inline=True
        )

        await message.edit(
            embed=embed,
            view=SurveyView(self.message_id)
        )

        if editing:

            text = "✏️ 回答を更新しました！"

        else:

            text = "✅ 回答ありがとうございました！"

        await interaction.response.send_message(
            text,
            ephemeral=True
        )

class SurveyView(discord.ui.View):

    def __init__(self, message_id):
        super().__init__(timeout=None)

        self.message_id = message_id

    @discord.ui.button(
        label="回答する",
        emoji="📝",
        style=discord.ButtonStyle.primary
    )
    async def answer(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_modal(
            SurveyModal(
                self.message_id
            )
        )
    def disable_all(self):
        for item in self.children:
            item.disabled = True
    @discord.ui.button(
        label="結果を見る",
        emoji="📊",
        style=discord.ButtonStyle.secondary
    )
    async def result(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not interaction.user.guild_permissions.manage_guild:

            await interaction.response.send_message(
                "❌ 管理者のみ閲覧できます。",
                ephemeral=True
            )
            return

        data = load_surveys()

        survey = data[str(self.message_id)]

        embed = discord.Embed(
            title="📊 アンケート結果",
            description=survey["question"],
            color=discord.Color.green()
        )

        if survey["answers"]:

            text = ""

            for user_id, answer in survey["answers"].items():
                text += f"<@{user_id}>\n{answer}\n\n"

            embed.add_field(
                name=f"回答 ({len(survey['answers'])}件)",
                value=text[:1024],
                inline=False
            )

        else:

            embed.add_field(
                name="回答",
                value="まだありません",
                inline=False
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
    @discord.ui.button(
        label="回答を削除",
        emoji="❌",
        style=discord.ButtonStyle.danger
    )
    async def delete_answer(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        data = load_surveys()

        survey = data[str(self.message_id)]

        user_id = str(interaction.user.id)

        if user_id not in survey["answers"]:

            await interaction.response.send_message(
                "❌ あなたはまだ回答していません。",
                ephemeral=True
            )
            return

        del survey["answers"][user_id]

        save_surveys(data)

        channel = interaction.guild.get_channel(
            survey["channel"]
        )

        message = await channel.fetch_message(
            int(self.message_id)
        )

        embed = message.embeds[0]

        embed.set_field_at(
            0,
            name="回答数",
            value=str(len(survey["answers"])),
            inline=True
        )

        await message.edit(
            embed=embed,
            view=SurveyView(self.message_id)
        )

        await interaction.response.send_message(
            "🗑 回答を削除しました。",
            ephemeral=True
        )


class Survey(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name="survey_result",
        description="アンケート結果"
    )
    async def survey_result(
        self,
        interaction: discord.Interaction,
        message_id: str
    ):

        data = load_surveys()

        if message_id not in data:

            await interaction.response.send_message(
                "アンケートが見つかりません。",
                ephemeral=True
            )
            return

        survey = data[message_id]

        embed = discord.Embed(
            title="📝 アンケート結果",
            description=survey["question"],
            color=discord.Color.green()
        )

        if survey["answers"]:

            text = ""

            for user_id, answer in survey["answers"].items():

                text += f"<@{user_id}>\n{answer}\n\n"

            embed.add_field(
                name=f"回答 ({len(survey['answers'])}件)",
                value=text[:1024],
                inline=False
            )

        else:

            embed.add_field(
                name="回答",
                value="まだありません",
                inline=False
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
    @app_commands.command(
        name="survey_close",
        description="アンケートを終了します"
    )
    @app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def survey_close(
        self,
        interaction: discord.Interaction,
        message_id: str
    ):

        data = load_surveys()

        if message_id not in data:

            await interaction.response.send_message(
                "アンケートが見つかりません。",
                ephemeral=True
            )
            return

        survey = data[message_id]

        channel = interaction.guild.get_channel(
            survey["channel"]
        )

        message = await channel.fetch_message(
            int(message_id)
        )

        embed = message.embeds[0]

        embed.color = discord.Color.red()

        embed.set_field_at(
            2,
            name="状態",
            value="🔒 終了",
            inline=False
        )

        view = SurveyView(message_id)
        view.disable_all()

        await message.edit(
            embed=embed,
            view=view
        )

        await interaction.response.send_message(
            "✅ アンケートを終了しました。",
            ephemeral=True
        )
    @app_commands.command(
        name="survey",
        description="アンケートを作成します"
    )
    @app_commands.describe(
        question="質問",
        hours="締切(時間)"
    )
    async def survey(
        self,
        interaction: discord.Interaction,
        question: str,
        hours: int
    ):

        end_time = (
            datetime.datetime.now()
            + datetime.timedelta(hours=hours)
        )

        embed = discord.Embed(
            title="📝 アンケート",
            description=question,
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="回答数",
            value="0",
            inline=True
        )

        embed.add_field(
            name="締切",
            value=f"<t:{int(end_time.timestamp())}:F>",
            inline=False
        )

        embed.add_field(
            name="状態",
            value="🟢 募集中",
            inline=False
        )

        message = await interaction.channel.send(
            embed=embed
        )

        await message.edit(
            view=SurveyView(message.id)
        )

        data = load_surveys()

        data[str(message.id)] = {
            "guild": interaction.guild.id,
            "channel": interaction.channel.id,
            "question": question,
            "answers": {},
            "end": int(end_time.timestamp())
        }

        save_surveys(data)

        await interaction.response.send_message(
            "✅ アンケートを作成しました。",
            ephemeral=True
        )



async def setup(bot):

    await bot.add_cog(
        Survey(bot)
    )