import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
import json
import os
import time
import asyncio
import random

GIVEAWAY_FILE = "giveaway.json"


class GiveawayView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)


    @discord.ui.button(
        label="🎉 参加する",
        style=discord.ButtonStyle.success,
        custom_id="giveaway_join"
    )
    async def join(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        data = load_data()

        message_id = str(interaction.message.id)

        if message_id not in data:
            data[message_id] = {
                "participants": []
            }

        participants = data[message_id]["participants"]

        if interaction.user.id in participants:

            await interaction.response.send_message(
                "❌ あなたは既に参加しています！",
                ephemeral=True
            )
            return

        participants.append(interaction.user.id)

        save_data(data)


        embed = interaction.message.embeds[0]

        embed.set_field_at(
            3,
            name="👥 参加人数",
            value=f"{len(participants)}人",
            inline=False
        )

        await interaction.message.edit(
            embed=embed,
            view=self
        )

        await interaction.response.send_message(
            "🎉 抽選に参加しました！",
            ephemeral=True
        )
    @discord.ui.button(
        label="❌ 参加取消",
        style=discord.ButtonStyle.danger,
        custom_id="giveaway_leave"
    )
    async def leave(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        data = load_data()

        message_id = str(interaction.message.id)

        if message_id not in data:
            await interaction.response.send_message(
                "❌ このGiveawayは存在しません。",
                ephemeral=True
            )
            return

        participants = data[message_id]["participants"]

        if interaction.user.id not in participants:
            await interaction.response.send_message(
                "❌ あなたは参加していません。",
                ephemeral=True
            )
            return

        participants.remove(interaction.user.id)

        save_data(data)

        embed = interaction.message.embeds[0]

        embed.set_field_at(
            3,
            name="👥 参加人数",
            value=f"{len(participants)}人",
            inline=False
        )

        await interaction.message.edit(
            embed=embed,
            view=self
        )

        await interaction.response.send_message(
            "✅ 抽選への参加を取り消しました。",
            ephemeral=True
        )



def load_data():
    if not os.path.exists(GIVEAWAY_FILE):
        return {}

    with open(GIVEAWAY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(GIVEAWAY_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


class Giveaway(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(GiveawayView())
    @app_commands.command(
        name="giveawaycreate",
        description="抽選を作成します"
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(
        color=[
            Choice(name="🔵 Discord Blue", value="5865F2"),
            Choice(name="🟢 Green", value="57F287"),
            Choice(name="🔴 Red", value="ED4245"),
            Choice(name="🟡 Yellow", value="FEE75C"),
            Choice(name="🟣 Purple", value="9B59B6"),
            Choice(name="🩷 Pink", value="FF69B4"),
            Choice(name="🩵 Sky Blue", value="87CEEB"),
            Choice(name="🟧 Orange", value="FFA500"),
        ]
    )
    async def giveawaycreate(
        self,
        interaction: discord.Interaction,
        景品: str,
        説明: str,
        時間: str,
        当選人数: app_commands.Range[int, 1, 20],
        color: Choice[str] | None = None,
        image: discord.Attachment | None = None
    ):

        try:
            seconds = self.parse_time(時間)
        except ValueError:

            await interaction.response.send_message(
                "❌ 時間は `30s` `10m` `2h` `1d` の形式で入力してください。",
                ephemeral=True
            )
            return
        color_value = int(color.value, 16) if color else 0x5865F2

        embed = discord.Embed(
            title="🎉 Giveaway",
            description=説明,
            color=color_value
        )

        embed.add_field(
            name="🎁 景品",
            value=景品,
            inline=False
        )

        embed.add_field(
            name="👑 当選人数",
            value=f"{当選人数}人",
            inline=True
        )

        embed.add_field(
            name="⏰ 終了",
            value=時間,
            inline=True
        )

        embed.add_field(
            name="👥 参加人数",
            value="0人",
            inline=False
        )

        if image:
            embed.set_image(url=image.url)

        embed.set_footer(
            text="Giveaway System"
        )

        message = await interaction.channel.send(
            embed=embed,
            view=GiveawayView()
        )
        await interaction.response.send_message(
            "✅ Giveawayを作成しました。",
            ephemeral=True
        )

        data = load_data()

        data[str(message.id)] = {
            "participants": [],
            "winners": 当選人数,
            "prize": 景品,
            "channel": interaction.channel.id,
            "end": time.time() + seconds
        }

        save_data(data)

        await asyncio.sleep(seconds)

        await self.finish_giveaway(
            message,
        当選人数
        )
    def parse_time(self, text: str):

        text = text.lower()

        if text.endswith("s"):
            return int(text[:-1])

        if text.endswith("m"):
            return int(text[:-1]) * 60

        if text.endswith("h"):
            return int(text[:-1]) * 3600

        if text.endswith("d"):
            return int(text[:-1]) * 86400

        raise ValueError

    async def finish_giveaway(
        self,
        message,
        winners
    ):

        data = load_data()

        giveaway = data.get(str(message.id))

        if giveaway is None:
            return

        participants = giveaway["participants"]

        if len(participants) == 0:

            await message.channel.send(
                "❌ 参加者がいませんでした。"
            )

            return

        winners = min(winners, len(participants))

        result = random.sample(
            participants,
            winners
        )

        mentions = []

        for uid in result:
            mentions.append(f"<@{uid}>")

        await message.channel.send(
            f"🎉 当選者\n{', '.join(mentions)}"
        )

        await message.edit(view=None)

        del data[str(message.id)]

        save_data(data)




async def setup(bot):
    await bot.add_cog(
        Giveaway(bot)
    )