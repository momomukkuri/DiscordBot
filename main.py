import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
import traceback

@bot.tree.error
async def on_app_command_error(interaction, error):
    print("===== スラッシュコマンドエラー =====")
    traceback.print_exception(
        type(error),
        error,
        error.__traceback__
    )

# .envを読み込む
load_dotenv()

TOKEN = os.getenv("TOKEN")

print("TOKEN:", TOKEN)
print("長さ:", len(TOKEN) if TOKEN else None)


# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.messages = True
intents.moderation = True
intents.guilds = True


# Bot作成
bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# 起動時
@bot.event
async def on_ready():

    print(f"{bot.user} が起動しました！")

    try:
        synced = await bot.tree.sync()

        print(f"{len(synced)}個のコマンドを同期しました")

        for cmd in synced:
            print(cmd.name)

    except Exception as e:
        print("同期エラー:", e)



# スラッシュコマンドエラー
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

    await bot.load_extension("cogs.ticket")
    print("ticket 読み込み完了")

    await bot.load_extension("cogs.giveaway")
    print("giveaway 読み込み完了")

    await bot.load_extension("cogs.afk")
    print("afk 読み込み完了")

    await bot.load_extension("cogs.rolepanel")
    print("rolepanel 読み込み完了")
    await bot.load_extension("cogs.survey")
    print("survey 読み込み完了")
    await bot.load_extension("cogs.settings")
    print("settings 読み込み完了")



# Bot起動
async def main():

    async with bot:

        await load_extensions()

        await bot.start(TOKEN)



# 実行
asyncio.run(main())