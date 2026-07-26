import discord
from discord.ext import commands
from discord import app_commands


class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_users = {}


    @app_commands.command(name="afk", description="AFK状態になります")
    @app_commands.describe(reason="AFK理由")
    async def afk(
        self,
        interaction: discord.Interaction,
        reason: str = "理由なし"
    ):

        self.afk_users[interaction.user.id] = {
            "reason": reason
        }

        await interaction.response.send_message(
            f"💤 {interaction.user.mention} はAFKになりました\n理由: {reason}"
        )


    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return


        # AFK解除
        if message.author.id in self.afk_users:

            data = self.afk_users.pop(message.author.id)

            await message.channel.send(
                f"👋 {message.author.mention}\n"
                "AFKを解除しました。おかえりなさい！"
            )


        # メンションされた人がAFKか確認
        for user in message.mentions:

            if user.id in self.afk_users:

                reason = self.afk_users[user.id]["reason"]

                await message.channel.send(
                    f"💤 {user.mention} はAFK中です\n"
                    f"理由: {reason}"
                )


async def setup(bot):
    await bot.add_cog(AFK(bot))