import discord
from discord.ext import commands
from discord import app_commands

import json
import os
import re


# =========================================================
# 設定
# =========================================================

COLDWORDS_FILE = "coldwords.json"

# 冷笑判定の最低スコア
COLD_SARCASM_THRESHOLD = 3


# =========================================================
# JSON
# =========================================================

def load_json(file):

    if not os.path.exists(file):
        return {}

    try:
        with open(
            file,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    except (json.JSONDecodeError, OSError):
        return {}


def save_json(file, data):

    with open(
        file,
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
# 冷笑設定
# =========================================================

def get_cold_config(guild_id):

    data = load_json(
        COLDWORDS_FILE
    )

    guild = str(guild_id)

    config = data.get(
        guild,
        {}
    )

    if not isinstance(config, dict):
        config = {}

    if "enabled" not in config:
        config["enabled"] = False

    if "words" not in config:
        config["words"] = []

    if not isinstance(config["words"], list):
        config["words"] = []

    return config


def save_cold_config(
    guild_id,
    config
):

    data = load_json(
        COLDWORDS_FILE
    )

    guild = str(guild_id)

    data[guild] = config

    save_json(
        COLDWORDS_FILE,
        data
    )


# =========================================================
# 冷笑パターン
# =========================================================

LAUGH_PATTERNS = [
    r"ｗ",
    r"w",
    r"笑",
    r"草",
]


PHRASE_PATTERNS = {

    "はいはい": 2,

    "へぇ": 1,
    "へえ": 1,
    "へー": 1,

    "それ本気で言ってる": 2,
    "それ本気で言ってんの": 2,

    "そうなんだ笑": 2,
    "そうなんだｗ": 2,
    "そうなんだw": 2,

}


# =========================================================
# 冷笑スコア計算
# =========================================================

def calculate_cold_score(
    content,
    words
):

    if not content:
        return 0

    content_lower = content.lower()

    score = 0

    detected_word = False


    # -----------------------------------------------------
    # 登録用語
    # -----------------------------------------------------

    for word in words:

        if not isinstance(word, str):
            continue

        word = word.strip()

        if not word:
            continue

        if word.lower() in content_lower:

            score += 2

            detected_word = True

            break


    # -----------------------------------------------------
    # 登録用語がない場合は冷笑扱いしない
    # -----------------------------------------------------

    if not detected_word:
        return 0


    # -----------------------------------------------------
    # 笑い表現
    # -----------------------------------------------------

    for pattern in LAUGH_PATTERNS:

        if re.search(
            pattern,
            content,
            re.IGNORECASE
        ):

            score += 1

            break


    # -----------------------------------------------------
    # 冷笑フレーズ
    # -----------------------------------------------------

    for phrase, points in PHRASE_PATTERNS.items():

        if phrase.lower() in content_lower:

            score += points


    return score


# =========================================================
# Cold Sarcasm Cog
# =========================================================

class ColdSarcasm(commands.Cog):

    def __init__(self, bot):

        self.bot = bot


    # =====================================================
    # メッセージ監視
    # =====================================================

    @commands.Cog.listener()
    async def on_message(
        self,
        message: discord.Message
    ):

        # -------------------------------------------------
        # Bot無視
        # -------------------------------------------------

        if message.author.bot:
            return


        # -------------------------------------------------
        # DM無視
        # -------------------------------------------------

        if message.guild is None:
            return


        # -------------------------------------------------
        # settings.py と同じ coldwords.json を読む
        # -------------------------------------------------

        config = get_cold_config(
            message.guild.id
        )


        # -------------------------------------------------
        # settingsでOFFなら反応しない
        # -------------------------------------------------

        if not config.get(
            "enabled",
            False
        ):
            return


        # -------------------------------------------------
        # 登録用語
        # -------------------------------------------------

        words = config.get(
            "words",
            []
        )

        if not words:
            return


        # -------------------------------------------------
        # メッセージ
        # -------------------------------------------------

        content = message.content

        if not content:
            return


        # -------------------------------------------------
        # 冷笑判定
        # -------------------------------------------------

        score = calculate_cold_score(
            content,
            words
        )

        if score < COLD_SARCASM_THRESHOLD:
            return


        # -------------------------------------------------
        # 冷笑を検知
        # -------------------------------------------------

        print(
            f"[冷笑感知] "
            f"Guild={message.guild.id} "
            f"User={message.author} "
            f"Score={score}"
        )


        # -------------------------------------------------
        # 1回だけ返信
        # -------------------------------------------------

        try:

            await message.reply(
                "冷笑を感知しました"
            )

        except discord.Forbidden:

            pass

        except discord.HTTPException:

            pass


    # =====================================================
    # /coldword_add
    # =====================================================

    @app_commands.command(
        name="coldword_add",
        description="冷笑感知用語を追加します"
    )
    @app_commands.describe(
        word="追加する冷笑用語"
    )
    @app_commands.default_permissions(
        administrator=True
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def coldword_add(
        self,
        interaction: discord.Interaction,
        word: str
    ):

        word = word.strip()

        if not word:

            await interaction.response.send_message(
                "用語を入力してください。",
                ephemeral=True
            )

            return


        config = get_cold_config(
            interaction.guild.id
        )


        words = config.get(
            "words",
            []
        )


        # -------------------------------------------------
        # 重複チェック
        # -------------------------------------------------

        for registered_word in words:

            if str(
                registered_word
            ).lower() == word.lower():

                await interaction.response.send_message(
                    f"すでに登録されています。\n`{word}`",
                    ephemeral=True
                )

                return


        # -------------------------------------------------
        # 登録
        # -------------------------------------------------

        words.append(word)

        config["words"] = words


        save_cold_config(
            interaction.guild.id,
            config
        )


        await interaction.response.send_message(
            f"冷笑用語を追加しました。\n\n`{word}`",
            ephemeral=True
        )


    # =====================================================
    # /coldword_remove
    # =====================================================

    @app_commands.command(
        name="coldword_remove",
        description="冷笑感知用語を削除します"
    )
    @app_commands.describe(
        word="削除する冷笑用語"
    )
    @app_commands.default_permissions(
        administrator=True
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def coldword_remove(
        self,
        interaction: discord.Interaction,
        word: str
    ):

        word = word.strip()


        config = get_cold_config(
            interaction.guild.id
        )


        words = config.get(
            "words",
            []
        )


        target = None


        for registered_word in words:

            if str(
                registered_word
            ).lower() == word.lower():

                target = registered_word

                break


        if target is None:

            await interaction.response.send_message(
                f"登録されていません。\n`{word}`",
                ephemeral=True
            )

            return


        words.remove(target)

        config["words"] = words


        save_cold_config(
            interaction.guild.id,
            config
        )


        await interaction.response.send_message(
            f"冷笑用語を削除しました。\n\n`{target}`",
            ephemeral=True
        )


    # =====================================================
    # /coldword_list
    # =====================================================

    @app_commands.command(
        name="coldword_list",
        description="登録されている冷笑用語を表示します"
    )
    @app_commands.default_permissions(
        administrator=True
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def coldword_list(
        self,
        interaction: discord.Interaction
    ):

        config = get_cold_config(
            interaction.guild.id
        )


        words = config.get(
            "words",
            []
        )


        if not words:

            await interaction.response.send_message(
                "冷笑用語は登録されていません。",
                ephemeral=True
            )

            return


        text = "\n".join(
            f"`{index + 1}.` {word}"
            for index, word in enumerate(words)
        )


        embed = discord.Embed(
            title="冷笑用語一覧",
            description=text,
            color=discord.Color.blurple()
        )


        embed.add_field(
            name="状態",
            value=(
                "ON"
                if config.get(
                    "enabled",
                    False
                )
                else "OFF"
            ),
            inline=False
        )


        embed.add_field(
            name="判定方式",
            value=(
                f"スコア方式\n"
                f"検知ライン："
                f"{COLD_SARCASM_THRESHOLD}点以上"
            ),
            inline=False
        )


        embed.set_footer(
            text=f"登録数：{len(words)}"
        )


        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# =========================================================
# Setup
# =========================================================

async def setup(bot):

    await bot.add_cog(
        ColdSarcasm(bot)
    )