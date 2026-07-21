import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

# .envを読み込む
load_dotenv()

TOKEN = os.getenv("TOKEN")


# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.messages = True
intents.moderation = True
intents.guilds=True

# Bot作成
bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# 起動時
@bot.event
async def on_ready():
    print("Bot名:", bot.user.name)
    print("Bot ID:", bot.user.id)
    print(f"{bot.user} が起動しました！")

    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)}個のスラッシュコマンドを同期しました！")

    except Exception as e:
        print(f"同期エラー: {e}")


# スラッシュコマンドエラー表示
@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error
):

    print("===== スラッシュコマンドエラー =====")
    print(error)

    if interaction.response.is_done():

        await interaction.followup.send(
            "❌ コマンド実行中にエラーが発生しました",
            ephemeral=True
        )

    else:

        await interaction.response.send_message(
            "❌ コマンド実行中にエラーが発生しました",
            ephemeral=True
        )


# Cog読み込み
async def load_extensions():

    await bot.load_extension("cogs.utility")
    print("utility 読み込み完了")

    await bot.load_extension("cogs.info")
    print("info 読み込み完了")

    await bot.load_extension("cogs.moderation")
    print("moderation 読み込み完了")

    await bot.load_extension("cogs.events")
    print("events 読み込み完了")
    
    await bot.load_extension("cogs.logs")
    print("logs 読み込み完了")
    await bot.load_extension("cogs.verify")
    print("verify 読み込み完了")


# Bot起動
async def main():

    async with bot:

        await load_extensions()

        await bot.start(TOKEN)


# 実行
asyncio.run(main())