import discord
from discord.ext import commands
from discord import app_commands
import json
import os


class Logs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    # =========================
    # ログ送信
    # =========================
    async def send_log(
        self,
        guild,
        embed,
        log_type="moderation"
    ):

        # ON/OFF確認
        if os.path.exists("logtoggle.json"):
            with open("logtoggle.json", "r", encoding="utf-8") as f:
                toggle = json.load(f)

            if not toggle.get(str(guild.id), {}).get(log_type, False):
                return

        # ログチャンネル確認
        if not os.path.exists("logs.json"):
            return

        with open("logs.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        guild_data = data.get(str(guild.id), {})
        channel_id = guild_data.get(log_type)

        if channel_id is None:
            return

        channel = guild.get_channel(channel_id)

        if channel:
            await channel.send(embed=embed)

    # =========================
    # 管理ログ設定
    # =========================
    @app_commands.command(
        name="setmoderationlog",
        description="管理ログチャンネルを設定します"
    )
    @app_commands.default_permissions(administrator=True)
    async def setmoderationlog(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        data = {}

        if os.path.exists("logs.json"):
            with open("logs.json", "r", encoding="utf-8") as f:
                data = json.load(f)

        guild = str(interaction.guild.id)

        if guild not in data:
            data[guild] = {}

        data[guild]["moderation"] = channel.id

        with open("logs.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        await interaction.response.send_message(
            f"✅ 管理ログを {channel.mention} に設定しました。",
            ephemeral=True
        )


    # =========================
    # 入退室ログ設定
    # =========================
    @app_commands.command(
        name="setjoinleavelog",
        description="入退室ログチャンネルを設定します"
    )
    @app_commands.default_permissions(administrator=True)
    async def setjoinleavelog(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        data = {}

        if os.path.exists("logs.json"):
            with open("logs.json", "r", encoding="utf-8") as f:
                data = json.load(f)

        guild = str(interaction.guild.id)

        if guild not in data:
            data[guild] = {}

        data[guild]["joinleave"] = channel.id

        with open("logs.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        await interaction.response.send_message(
            f"✅ 入退室ログを {channel.mention} に設定しました。",
            ephemeral=True
        )


    # =========================
    # メッセージログ設定
    # =========================
    @app_commands.command(
        name="setmessagelog",
        description="メッセージログチャンネルを設定します"
    )
    @app_commands.default_permissions(administrator=True)
    async def setmessagelog(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        data = {}

        if os.path.exists("logs.json"):
            with open("logs.json", "r", encoding="utf-8") as f:
                data = json.load(f)

        guild = str(interaction.guild.id)

        if guild not in data:
            data[guild] = {}

        data[guild]["message"] = channel.id

        with open("logs.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        await interaction.response.send_message(
            f"✅ メッセージログを {channel.mention} に設定しました。",
            ephemeral=True
        )


    # =========================
    # 監視ログ設定
    # =========================
    @app_commands.command(
        name="setmonitorlog",
        description="監視ログチャンネルを設定します"
    )
    @app_commands.default_permissions(administrator=True)
    async def setmonitorlog(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        data = {}

        if os.path.exists("logs.json"):
            with open("logs.json", "r", encoding="utf-8") as f:
                data = json.load(f)

        guild = str(interaction.guild.id)

        if guild not in data:
            data[guild] = {}

        data[guild]["monitor"] = channel.id

        with open("logs.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        await interaction.response.send_message(
            f"✅ 監視ログを {channel.mention} に設定しました。",
            ephemeral=True
        )


    # =========================
    # メッセージ削除
    # =========================
    @commands.Cog.listener()
    async def on_message_delete(
        self,
        message
    ):

        if message.author.bot:
            return

        if message.guild is None:
            return


        embed = discord.Embed(
            title="🗑️ メッセージ削除",
            color=discord.Color.red()
        )


        embed.add_field(
            name="ユーザー",
            value=f"{message.author.mention}\n`{message.author.id}`",
            inline=False
        )


        embed.add_field(
            name="チャンネル",
            value=message.channel.mention,
            inline=False
        )


        embed.add_field(
            name="内容",
            value=message.content[:1024] or "なし",
            inline=False
        )


        await self.send_log(
            message.guild,
            embed,
            "message"
        )



    # =========================
    # メッセージ編集
    # =========================
    @commands.Cog.listener()
    async def on_message_edit(
        self,
        before,
        after
    ):

        if before.author.bot:
            return


        if before.guild is None:
            return


        if before.content == after.content:
            return


        embed = discord.Embed(
            title="✏️ メッセージ編集",
            color=discord.Color.orange()
        )


        embed.add_field(
            name="ユーザー",
            value=f"{before.author.mention}\n`{before.author.id}`",
            inline=False
        )


        embed.add_field(
            name="チャンネル",
            value=before.channel.mention,
            inline=False
        )


        embed.add_field(
            name="変更前",
            value=before.content[:1024] or "なし",
            inline=False
        )


        embed.add_field(
            name="変更後",
            value=after.content[:1024] or "なし",
            inline=False
        )


        await self.send_log(
            before.guild,
            embed,
            "message"
        )
    # =========================
    # 入室ログ
    # =========================
    @commands.Cog.listener()
    async def on_member_join(self, member):

        embed = discord.Embed(
            title="📥 メンバー参加",
            color=discord.Color.green()
        )

        embed.add_field(
            name="ユーザー",
            value=f"{member.mention}\n`{member.id}`",
            inline=False
        )

        await self.send_log(
            member.guild,
            embed,
            "joinleave"
        )


    # =========================
    # 退出ログ
    # =========================
    @commands.Cog.listener()
    async def on_member_remove(self, member):

        embed = discord.Embed(
            title="📤 メンバー退出",
            color=discord.Color.red()
        )

        embed.add_field(
            name="ユーザー",
            value=f"{member}\n`{member.id}`",
            inline=False
        )

        await self.send_log(
            member.guild,
            embed,
            "joinleave"
        )



async def setup(bot):

    await bot.add_cog(
        Logs(bot)
    )