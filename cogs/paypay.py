import discord
from discord.ext import commands
from discord import app_commands

import json
import os


# =========================================================
# 設定
# =========================================================

DATA_DIR = "data"
PAYPAY_FILE = os.path.join(DATA_DIR, "paypay.json")


# =========================================================
# JSON
# =========================================================

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_paypay():
    ensure_data_dir()

    if not os.path.exists(PAYPAY_FILE):
        return {}

    try:
        with open(
            PAYPAY_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    except (json.JSONDecodeError, OSError):
        return {}


def save_paypay(data):
    ensure_data_dir()

    with open(
        PAYPAY_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


# =========================================================
# PayPay Cog
# =========================================================

class PayPay(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # =====================================================
    # PayPay URL登録
    # =====================================================

    @app_commands.command(
        name="setpaypay",
        description="自分のPayPay送金URLを登録します"
    )
    @app_commands.describe(
        url="PayPayの送金URL"
    )
    async def setpaypay(
        self,
        interaction: discord.Interaction,
        url: str
    ):

        # =================================================
        # URLチェック
        # =================================================

        if not url.startswith(
            "https://pay.paypay.ne.jp/"
        ):
            await interaction.response.send_message(
                "❌ 正しいPayPay送金URLを入力してください。\n\n"
                "例:\n"
                "`https://pay.paypay.ne.jp/xxxxxxxx`",
                ephemeral=True
            )
            return

        # =================================================
        # 保存
        # =================================================

        data = load_paypay()

        user_id = str(
            interaction.user.id
        )

        data[user_id] = {
            "url": url
        }

        save_paypay(data)

        await interaction.response.send_message(
            "✅ PayPay送金URLを登録しました。\n\n"
            f"💰 送金先:\n{url}",
            ephemeral=True
        )

    # =====================================================
    # PayPay URL確認
    # =====================================================

    @app_commands.command(
        name="mypaypay",
        description="登録しているPayPay送金URLを確認します"
    )
    async def mypaypay(
        self,
        interaction: discord.Interaction
    ):

        data = load_paypay()

        user_id = str(
            interaction.user.id
        )

        seller = data.get(user_id)

        if not seller:
            await interaction.response.send_message(
                "❌ PayPay送金URLが登録されていません。\n\n"
                "先に `/setpaypay` を使用してください。",
                ephemeral=True
            )
            return

        url = seller.get("url")

        if not url:
            await interaction.response.send_message(
                "❌ PayPay送金URLが見つかりません。",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "💰 **登録中のPayPay送金URL**\n\n"
            f"{url}",
            ephemeral=True
        )

    # =====================================================
    # PayPay URL削除
    # =====================================================

    @app_commands.command(
        name="delpaypay",
        description="登録しているPayPay送金URLを削除します"
    )
    async def delpaypay(
        self,
        interaction: discord.Interaction
    ):

        data = load_paypay()

        user_id = str(
            interaction.user.id
        )

        if user_id not in data:
            await interaction.response.send_message(
                "❌ PayPay送金URLが登録されていません。",
                ephemeral=True
            )
            return

        del data[user_id]

        save_paypay(data)

        await interaction.response.send_message(
            "✅ PayPay送金URLを削除しました。",
            ephemeral=True
        )


# =========================================================
# Setup
# =========================================================

async def setup(bot):
    await bot.add_cog(
        PayPay(bot)
    )