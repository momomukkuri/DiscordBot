import os
import asyncio
import traceback

import discord
from discord.ext import commands
from dotenv import load_dotenv


# =========================================================
# .envを読み込む
# =========================================================

load_dotenv()

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise RuntimeError("TOKENが設定されていません")


# =========================================================
# サーバーID
# =========================================================
# Discordで対象サーバーを右クリック
# →「サーバーIDをコピー」
# → 下の数字を入れる
#
# 例：
# GUILD_ID = 123456789012345678
# =========================================================

GUILD_ID = 1538575152114303036


# =========================================================
# Intents
# =========================================================

intents = discord.Intents.default()

intents.message_content = True
intents.members = True
intents.messages = True
intents.moderation = True
intents.guilds = True


# =========================================================
# Bot作成
# =========================================================

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================================================
# スラッシュコマンドエラー
# =========================================================

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error
):

    print("===== スラッシュコマンドエラー =====")

    traceback.print_exception(
        type(error),
        error,
        error.__traceback__
    )

    try:

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

    except Exception as e:

        print(
            "エラー通知にも失敗しました:",
            e
        )


# =========================================================
# 起動時
# =========================================================

@bot.event
async def on_ready():

    print("================================")
    print(f"{bot.user} が起動しました！")
    print("================================")

    try:

        guild = discord.Object(
            id=GUILD_ID
        )

        # グローバルに登録されているコマンドを
        # このサーバーへコピー
        bot.tree.copy_global_to(
            guild=guild
        )

        # サーバーへ同期
        synced = await bot.tree.sync(
            guild=guild
        )

        print(
            f"スラッシュコマンドを {len(synced)} 個同期しました"
        )

        for cmd in synced:
            print(
                f"  /{cmd.name}"
            )

        print("================================")

    except Exception as e:

        print("同期エラー:")
        traceback.print_exc()


# =========================================================
# Cog読み込み
# =========================================================

async def load_extensions():

    await bot.load_extension(
        "cogs.utility"
    )
    print("✅ cogs.utility 読み込み完了")

    await bot.load_extension(
        "cogs.info"
    )
    print("✅ cogs.info 読み込み完了")

    await bot.load_extension(
        "cogs.moderation"
    )
    print("✅ cogs.moderation 読み込み完了")

    await bot.load_extension(
        "cogs.events"
    )
    print("✅ cogs.events 読み込み完了")

    await bot.load_extension(
        "cogs.logs"
    )
    print("✅ cogs.logs 読み込み完了")

    await bot.load_extension(
        "cogs.verify"
    )
    print("✅ cogs.verify 読み込み完了")

    await bot.load_extension(
        "cogs.ticket"
    )
    print("✅ cogs.ticket 読み込み完了")

    await bot.load_extension(
        "cogs.giveaway"
    )
    print("✅ cogs.giveaway 読み込み完了")

    await bot.load_extension(
        "cogs.afk"
    )
    print("✅ cogs.afk 読み込み完了")

    await bot.load_extension(
        "cogs.rolepanel"
    )
    print("✅ cogs.rolepanel 読み込み完了")

    await bot.load_extension(
        "cogs.survey"
    )
    print("✅ cogs.survey 読み込み完了")

    await bot.load_extension(
        "cogs.settings"
    )
    print("✅ cogs.settings 読み込み完了")

    await bot.load_extension(
        "cogs.status"
    )
    print("✅ cogs.status 読み込み完了")

    await bot.load_extension(
        "cogs.shop"
    )
    print("✅ cogs.shop 読み込み完了")

    await bot.load_extension(
        "cogs.paypay"
    )
    print("✅ cogs.paypay 読み込み完了")

    print("================================")
    print("Cog読み込み完了")
    print("================================")


# =========================================================
# Bot起動
# =========================================================

async def main():

    async with bot:

        await load_extensions()

        await bot.start(
            TOKEN
        )


# =========================================================
# 実行
# =========================================================

asyncio.run(
    main()
)