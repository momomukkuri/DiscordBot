import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ping",
        description="Botの応答速度を確認します"
    )
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green()
        )

        embed.add_field(
            name="レイテンシ",
            value=f"{latency} ms",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="help",
        description="コマンド一覧を表示します"
    )
    async def help(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="🛠️ MOMON 鯖管理Bot",
            description="利用できるコマンド一覧です。",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="🏓 ユーティリティ",
            value=(
                "`/ping` - Botの応答速度を確認\n"
                "`/help` - このヘルプを表示\n"
                "`/poll` - 投票を作成"
            ),
            inline=False
        )

        embed.add_field(
            name="👤 情報コマンド",
            value=(
                "`/userinfo` - ユーザー情報\n"
                "`/serverinfo` - サーバー情報\n"
                "`/avatar` - アイコン表示\n"
                "`/servericon` - サーバーアイコン表示"
            ),
            inline=False
        )

        embed.add_field(
            name="🛡️ 管理コマンド",
            value=(
                "`/clear` - メッセージ削除\n"
                "`/warn` - 警告\n"
                "`/warnings` - 警告履歴\n"
                "`/timeout` - タイムアウト\n"
                "`/untimeout` - タイムアウト解除\n"
                "`/kick` - キック\n"
                "`/ban` - BAN\n"
                "`/lock` - チャンネルをロック\n"
                "`/unlock` - チャンネルを解除\n"
                "`/nuke` - チャンネルを初期化"
            ),
            inline=False
        )

        embed.add_field(
            name="🔐 認証",
            value=(
                "`/verifysetup` - 認証パネル設置\n"
                "`/setverifyrole` - 認証ロール設定\n"
                "`/setunverifiedrole` - 未認証ロール設定\n"
                "`/setverifyimage` - 認証画像/GIF設定"
            ),
            inline=False
        )

        embed.add_field(
            name="📝 ログ",
            value=(
                "`/setmoderationlog` - 管理ログ\n"
                "`/setjoinleavelog` - 入退室ログ\n"
                "`/setmessagelog` - メッセージログ\n"
                "`/setmonitorlog` - 監視ログ"
            ),
            inline=False
        )

        embed.set_footer(text="MOMON 鯖管理Bot")

        await interaction.response.send_message(
            embed=embed
        )
    @app_commands.command(
        name="setwelcome",
        description="Welcomeチャンネルを設定します"
    )
    @app_commands.describe(
        channel="Welcomeメッセージを送信するチャンネル"
    )
    @app_commands.default_permissions(administrator=True)
    async def setwelcome(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        welcome_file = "welcome.json"

        if os.path.exists(welcome_file):
            with open(
                welcome_file,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)
        else:
            data = {}

        guild_id = str(interaction.guild.id)

        if guild_id not in data:
            data[guild_id] = {}

        data[guild_id]["channel"] = channel.id

        with open(
            welcome_file,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )

        embed = discord.Embed(
            title="✅ Welcomeチャンネルを設定しました",
            description=f"{channel.mention} をWelcomeチャンネルに設定しました。",
            color=discord.Color.green()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    @app_commands.command(
        name="flood",
        description="指定した内容を連続送信します"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def flood(
        self,
        interaction: discord.Interaction,
        message: str,
        count: app_commands.Range[int, 1, 100],
        delay: app_commands.Range[float, 0.5, 10.0]
    ):
        await interaction.response.send_message(
            f"🚀 {count}回送信を開始します。",
            ephemeral=True
        )

        channel = interaction.channel

        for i in range(count):
            await channel.send(message)
            await asyncio.sleep(delay)

async def setup(bot):
    await bot.add_cog(Utility(bot))