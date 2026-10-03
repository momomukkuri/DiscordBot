import discord
from discord.ext import commands
from discord import app_commands

import json
import os


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
# ON / OFF
# =========================================================

def status(value):

    return "🟢 ON" if value else "🔴 OFF"


# =========================================================
# 冷笑感知のデフォルト設定
# =========================================================

DEFAULT_COLD_CONFIG = {
    "enabled": False,
    "words": [],
    "action": "none",
    "timeout_minutes": 10
}


def get_cold_config(guild_id):

    data = load_json("coldwords.json")

    guild = str(guild_id)

    config = data.get(guild, {})

    if not isinstance(config, dict):
        config = {}

    result = DEFAULT_COLD_CONFIG.copy()

    result["words"] = []

    result.update(config)

    if not isinstance(result.get("words"), list):
        result["words"] = []

    if result.get("action") not in [
        "none",
        "warn",
        "timeout",
        "kick",
        "ban"
    ]:
        result["action"] = "none"

    try:
        result["timeout_minutes"] = int(
            result.get("timeout_minutes", 10)
        )
    except (TypeError, ValueError):
        result["timeout_minutes"] = 10

    if result["timeout_minutes"] < 1:
        result["timeout_minutes"] = 10

    return result


def save_cold_config(guild_id, config):

    data = load_json("coldwords.json")

    guild = str(guild_id)

    if not isinstance(config, dict):
        config = {}

    data[guild] = config

    save_json(
        "coldwords.json",
        data
    )


# =========================================================
# 冷笑処理の表示名
# =========================================================

def cold_action_name(action):

    names = {
        "none": "何もしない",
        "warn": "⚠️ Warn",
        "timeout": "🔇 Timeout",
        "kick": "👢 Kick",
        "ban": "🔨 BAN"
    }

    return names.get(
        action,
        "何もしない"
    )


# =========================================================
# メイン設定画面
# =========================================================

def settings_embed(guild_id):

    automod = load_json("automod.json")
    xsave = load_json("xsave.json")
    xembed = load_json("xembed.json")
    welcome = load_json("welcome.json")
    verify = load_json("verify.json")
    coldwords = load_json("coldwords.json")
    logs = load_json("logtoggle.json")

    guild = str(guild_id)

    auto = automod.get(guild, {})

    if not isinstance(auto, dict):
        auto = {}

    xsave_data = xsave.get(guild, {})

    if isinstance(xsave_data, dict):
        xsave_enabled = xsave_data.get(
            "enabled",
            False
        )
    else:
        xsave_enabled = bool(xsave_data)

    xembed_data = xembed.get(guild, {})

    if isinstance(xembed_data, dict):
        xembed_enabled = xembed_data.get(
            "enabled",
            False
        )
    else:
        xembed_enabled = bool(xembed_data)

    welcome_data = welcome.get(guild, {})

    if not isinstance(welcome_data, dict):
        welcome_data = {}

    verify_data = verify.get(guild, {})

    if not isinstance(verify_data, dict):
        verify_data = {}

    cold = get_cold_config(guild_id)

    log = logs.get(guild, {})

    if not isinstance(log, dict):
        log = {}

    embed = discord.Embed(
        title="⚙️ サーバー設定",
        description="変更したいカテゴリを選択してください。",
        color=discord.Color.green()
    )

    # -----------------------------------------------------
    # AutoMod
    # -----------------------------------------------------

    embed.add_field(
        name="🛡 AutoMod",
        value=(
            f"Spam：{status(auto.get('spam', False))}\n"
            f"Invite：{status(auto.get('invite', False))}\n"
            f"NGWord：{status(auto.get('ngword', False))}\n"
            f"Mention：{status(auto.get('mention', False))}"
        ),
        inline=False
    )

    # -----------------------------------------------------
    # X
    # -----------------------------------------------------

    embed.add_field(
        name="🎥 X機能",
        value=(
            f"動画変換：{status(xsave_enabled)}\n"
            f"リンク展開：{status(xembed_enabled)}"
        ),
        inline=False
    )

    # -----------------------------------------------------
    # Welcome
    # -----------------------------------------------------

    embed.add_field(
        name="👋 Welcome",
        value=(
            f"Welcome：{status(welcome_data.get('enabled', False))}\n"
            f"認証：{status(verify_data.get('enabled', False))}"
        ),
        inline=False
    )

    # -----------------------------------------------------
    # 冷笑感知
    # -----------------------------------------------------

    embed.add_field(
        name="😏 冷笑感知",
        value=(
            f"冷笑感知：{status(cold.get('enabled', False))}\n"
            f"登録用語：{len(cold.get('words', []))}個\n"
            f"検知時：{cold_action_name(cold.get('action'))}\n"
            f"Timeout：{cold.get('timeout_minutes', 10)}分"
        ),
        inline=False
    )

    # -----------------------------------------------------
    # ログ
    # -----------------------------------------------------

    embed.add_field(
        name="📋 ログ",
        value=(
            f"メッセージ：{status(log.get('message', False))}\n"
            f"参加退出：{status(log.get('joinleave', False))}\n"
            f"監視：{status(log.get('monitor', False))}\n"
            f"管理：{status(log.get('moderation', False))}"
        ),
        inline=False
    )

    return embed


# =========================================================
# メイン設定メニュー
# =========================================================

class SettingsSelect(discord.ui.Select):

    def __init__(self):

        options = [

            discord.SelectOption(
                label="AutoMod",
                value="AutoMod",
                emoji="🛡",
                description="AutoModを設定"
            ),

            discord.SelectOption(
                label="X機能",
                value="X機能",
                emoji="🎥",
                description="X関連機能を設定"
            ),

            discord.SelectOption(
                label="Welcome",
                value="Welcome",
                emoji="👋",
                description="Welcome・認証を設定"
            ),

            discord.SelectOption(
                label="ログ",
                value="ログ",
                emoji="📋",
                description="ログ機能を設定"
            ),

            discord.SelectOption(
                label="冷笑感知",
                value="冷笑感知",
                emoji="😏",
                description="冷笑感知と処分方法を設定"
            ),

            discord.SelectOption(
                label="その他",
                value="その他",
                emoji="⚙️",
                description="その他設定"
            )
        ]

        super().__init__(
            placeholder="設定項目を選択",
            options=options
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        value = self.values[0]

        if value == "AutoMod":

            await interaction.response.edit_message(
                embed=automod_embed(
                    interaction.guild.id
                ),
                view=AutoModView()
            )

        elif value == "X機能":

            await interaction.response.edit_message(
                embed=x_embed(
                    interaction.guild.id
                ),
                view=XView()
            )

        elif value == "Welcome":

            await interaction.response.edit_message(
                embed=welcome_embed(
                    interaction.guild.id
                ),
                view=WelcomeView()
            )

        elif value == "ログ":

            await interaction.response.edit_message(
                embed=log_embed(
                    interaction.guild.id
                ),
                view=LogView()
            )

        elif value == "冷笑感知":

            await interaction.response.edit_message(
                embed=cold_sarcasm_embed(
                    interaction.guild.id
                ),
                view=ColdSarcasmView()
            )

        elif value == "その他":

            await interaction.response.edit_message(
                embed=simple_embed(
                    "⚙️ その他設定"
                ),
                view=SimpleView()
            )


class SettingsView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(
            SettingsSelect()
        )


# =========================================================
# AutoMod
# =========================================================

def automod_embed(guild_id):

    data = load_json("automod.json")

    auto = data.get(
        str(guild_id),
        {}
    )

    if not isinstance(auto, dict):
        auto = {}

    embed = discord.Embed(
        title="🛡 AutoMod設定",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="現在の状態",
        value=(
            f"アンチスパム：{status(auto.get('spam', False))}\n"
            f"招待リンク：{status(auto.get('invite', False))}\n"
            f"禁止ワード：{status(auto.get('ngword', False))}\n"
            f"メンション：{status(auto.get('mention', False))}"
        ),
        inline=False
    )

    return embed


class AutoModView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(
            AutoModSelect()
        )


class AutoModSelect(discord.ui.Select):

    def __init__(self):

        super().__init__(
            placeholder="変更する機能",
            options=[
                discord.SelectOption(
                    label="spam"
                ),
                discord.SelectOption(
                    label="invite"
                ),
                discord.SelectOption(
                    label="ngword"
                ),
                discord.SelectOption(
                    label="mention"
                )
            ]
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.edit_message(
            embed=automod_embed(
                interaction.guild.id
            ),
            view=AutoModToggleView(
                self.values[0]
            )
        )


class AutoModToggleView(discord.ui.View):

    def __init__(self, feature):

        super().__init__(timeout=None)

        self.feature = feature

    @discord.ui.button(
        label="🟢 ON",
        style=discord.ButtonStyle.green
    )
    async def on_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        data = load_json("automod.json")

        guild = str(
            interaction.guild.id
        )

        if guild not in data:
            data[guild] = {}

        if not isinstance(data[guild], dict):
            data[guild] = {}

        data[guild][self.feature] = True

        save_json(
            "automod.json",
            data
        )

        await interaction.response.edit_message(
            embed=automod_embed(
                interaction.guild.id
            ),
            view=AutoModView()
        )

    @discord.ui.button(
        label="🔴 OFF",
        style=discord.ButtonStyle.red
    )
    async def off_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        data = load_json("automod.json")

        guild = str(
            interaction.guild.id
        )

        if guild not in data:
            data[guild] = {}

        if not isinstance(data[guild], dict):
            data[guild] = {}

        data[guild][self.feature] = False

        save_json(
            "automod.json",
            data
        )

        await interaction.response.edit_message(
            embed=automod_embed(
                interaction.guild.id
            ),
            view=AutoModView()
        )

    @discord.ui.button(
        label="⬅ 戻る",
        style=discord.ButtonStyle.gray
    )
    async def back_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            embed=settings_embed(
                interaction.guild.id
            ),
            view=SettingsView()
        )


# =========================================================
# X機能
# =========================================================

def x_embed(guild_id):

    xsave = load_json("xsave.json")
    xembed = load_json("xembed.json")

    xsave_data = xsave.get(
        str(guild_id),
        {}
    )

    xembed_data = xembed.get(
        str(guild_id),
        {}
    )

    if isinstance(xsave_data, dict):
        xsave_enabled = xsave_data.get(
            "enabled",
            False
        )
    else:
        xsave_enabled = bool(xsave_data)

    if isinstance(xembed_data, dict):
        xembed_enabled = xembed_data.get(
            "enabled",
            False
        )
    else:
        xembed_enabled = bool(xembed_data)

    embed = discord.Embed(
        title="🎥 X機能",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="現在の状態",
        value=(
            f"X動画変換：{status(xsave_enabled)}\n"
            f"Xリンク展開：{status(xembed_enabled)}"
        ),
        inline=False
    )

    return embed


class XView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(
            XSelect()
        )


class XSelect(discord.ui.Select):

    def __init__(self):

        super().__init__(
            placeholder="変更する機能",
            options=[
                discord.SelectOption(
                    label="X動画変換"
                ),
                discord.SelectOption(
                    label="Xリンク展開"
                )
            ]
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.edit_message(
            embed=x_embed(
                interaction.guild.id
            ),
            view=XToggleView(
                self.values[0]
            )
        )


class XToggleView(discord.ui.View):

    def __init__(self, feature):

        super().__init__(timeout=None)

        self.feature = feature

    @discord.ui.button(
        label="🟢 ON",
        style=discord.ButtonStyle.green
    )
    async def on_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        file = (
            "xsave.json"
            if self.feature == "X動画変換"
            else "xembed.json"
        )

        data = load_json(file)

        guild = str(
            interaction.guild.id
        )

        if guild not in data:
            data[guild] = {}

        if not isinstance(data[guild], dict):
            data[guild] = {}

        data[guild]["enabled"] = True

        save_json(
            file,
            data
        )

        await interaction.response.edit_message(
            embed=x_embed(
                interaction.guild.id
            ),
            view=XView()
        )

    @discord.ui.button(
        label="🔴 OFF",
        style=discord.ButtonStyle.red
    )
    async def off_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        file = (
            "xsave.json"
            if self.feature == "X動画変換"
            else "xembed.json"
        )

        data = load_json(file)

        guild = str(
            interaction.guild.id
        )

        if guild not in data:
            data[guild] = {}

        if not isinstance(data[guild], dict):
            data[guild] = {}

        data[guild]["enabled"] = False

        save_json(
            file,
            data
        )

        await interaction.response.edit_message(
            embed=x_embed(
                interaction.guild.id
            ),
            view=XView()
        )

    @discord.ui.button(
        label="⬅ 戻る",
        style=discord.ButtonStyle.gray
    )
    async def back_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            embed=settings_embed(
                interaction.guild.id
            ),
            view=SettingsView()
        )


# =========================================================
# Welcome
# =========================================================

def welcome_embed(guild_id):

    welcome = load_json("welcome.json")
    verify = load_json("verify.json")

    welcome_data = welcome.get(
        str(guild_id),
        {}
    )

    verify_data = verify.get(
        str(guild_id),
        {}
    )

    if not isinstance(welcome_data, dict):
        welcome_data = {}

    if not isinstance(verify_data, dict):
        verify_data = {}

    embed = discord.Embed(
        title="👋 Welcome設定",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="現在の状態",
        value=(
            f"Welcome：{status(welcome_data.get('enabled', False))}\n"
            f"認証：{status(verify_data.get('enabled', False))}"
        ),
        inline=False
    )

    return embed


class WelcomeView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(
            WelcomeSelect()
        )


class WelcomeSelect(discord.ui.Select):

    def __init__(self):

        super().__init__(
            placeholder="変更する機能",
            options=[
                discord.SelectOption(
                    label="Welcome"
                ),
                discord.SelectOption(
                    label="認証"
                )
            ]
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.edit_message(
            embed=welcome_embed(
                interaction.guild.id
            ),
            view=WelcomeToggleView(
                self.values[0]
            )
        )


class WelcomeToggleView(discord.ui.View):

    def __init__(self, feature):

        super().__init__(timeout=None)

        self.feature = feature

    @discord.ui.button(
        label="🟢 ON",
        style=discord.ButtonStyle.green
    )
    async def on_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        file = (
            "welcome.json"
            if self.feature == "Welcome"
            else "verify.json"
        )

        data = load_json(file)

        guild = str(
            interaction.guild.id
        )

        if guild not in data:
            data[guild] = {}

        if not isinstance(data[guild], dict):
            data[guild] = {}

        data[guild]["enabled"] = True

        save_json(
            file,
            data
        )

        await interaction.response.edit_message(
            embed=welcome_embed(
                interaction.guild.id
            ),
            view=WelcomeView()
        )

    @discord.ui.button(
        label="🔴 OFF",
        style=discord.ButtonStyle.red
    )
    async def off_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        file = (
            "welcome.json"
            if self.feature == "Welcome"
            else "verify.json"
        )

        data = load_json(file)

        guild = str(
            interaction.guild.id
        )

        if guild not in data:
            data[guild] = {}

        if not isinstance(data[guild], dict):
            data[guild] = {}

        data[guild]["enabled"] = False

        save_json(
            file,
            data
        )

        await interaction.response.edit_message(
            embed=welcome_embed(
                interaction.guild.id
            ),
            view=WelcomeView()
        )

    @discord.ui.button(
        label="⬅ 戻る",
        style=discord.ButtonStyle.gray
    )
    async def back_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            embed=settings_embed(
                interaction.guild.id
            ),
            view=SettingsView()
        )


# =========================================================
# ログ
# =========================================================

def log_embed(guild_id):

    logs = load_json("logtoggle.json")

    data = logs.get(
        str(guild_id),
        {}
    )

    if not isinstance(data, dict):
        data = {}

    embed = discord.Embed(
        title="📋 ログ設定",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="現在の状態",
        value=(
            f"メッセージ：{status(data.get('message', False))}\n"
            f"参加退出：{status(data.get('joinleave', False))}\n"
            f"監視ログ：{status(data.get('monitor', False))}\n"
            f"管理ログ：{status(data.get('moderation', False))}"
        ),
        inline=False
    )

    return embed


class LogView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(
            LogSelect()
        )


class LogSelect(discord.ui.Select):

    def __init__(self):

        super().__init__(
            placeholder="変更する機能",
            options=[
                discord.SelectOption(
                    label="message"
                ),
                discord.SelectOption(
                    label="joinleave"
                ),
                discord.SelectOption(
                    label="monitor"
                ),
                discord.SelectOption(
                    label="moderation"
                )
            ]
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.edit_message(
            embed=log_embed(
                interaction.guild.id
            ),
            view=LogToggleView(
                self.values[0]
            )
        )


class LogToggleView(discord.ui.View):

    def __init__(self, feature):

        super().__init__(timeout=None)

        self.feature = feature

    @discord.ui.button(
        label="🟢 ON",
        style=discord.ButtonStyle.green
    )
    async def on_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        data = load_json(
            "logtoggle.json"
        )

        guild = str(
            interaction.guild.id
        )

        if guild not in data:
            data[guild] = {}

        if not isinstance(data[guild], dict):
            data[guild] = {}

        data[guild][self.feature] = True

        save_json(
            "logtoggle.json",
            data
        )

        await interaction.response.edit_message(
            embed=log_embed(
                interaction.guild.id
            ),
            view=LogView()
        )

    @discord.ui.button(
        label="🔴 OFF",
        style=discord.ButtonStyle.red
    )
    async def off_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        data = load_json(
            "logtoggle.json"
        )

        guild = str(
            interaction.guild.id
        )

        if guild not in data:
            data[guild] = {}

        if not isinstance(data[guild], dict):
            data[guild] = {}

        data[guild][self.feature] = False

        save_json(
            "logtoggle.json",
            data
        )

        await interaction.response.edit_message(
            embed=log_embed(
                interaction.guild.id
            ),
            view=LogView()
        )

    @discord.ui.button(
        label="⬅ 戻る",
        style=discord.ButtonStyle.gray
    )
    async def back_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            embed=settings_embed(
                interaction.guild.id
            ),
            view=SettingsView()
        )


# =========================================================
# 冷笑感知
# =========================================================

def cold_sarcasm_embed(guild_id):

    config = get_cold_config(
        guild_id
    )

    action = config.get(
        "action",
        "none"
    )

    timeout_minutes = config.get(
        "timeout_minutes",
        10
    )

    embed = discord.Embed(
        title="😏 冷笑感知設定",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="現在の状態",
        value=(
            f"冷笑感知：{status(config.get('enabled', False))}\n"
            f"登録用語：{len(config.get('words', []))}個\n"
            f"検知時の処理：{cold_action_name(action)}\n"
            f"Timeout時間：{timeout_minutes}分"
        ),
        inline=False
    )

    embed.add_field(
        name="用語の管理",
        value=(
            "`/coldword_add` → 用語を追加\n"
            "`/coldword_remove` → 用語を削除\n"
            "`/coldword_list` → 登録用語を確認"
        ),
        inline=False
    )

    return embed


class ColdSarcasmView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(
            ColdActionSelect()
        )

    @discord.ui.button(
        label="🟢 ON",
        style=discord.ButtonStyle.green,
        row=1
    )
    async def on_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        config = get_cold_config(
            interaction.guild.id
        )

        config["enabled"] = True

        save_cold_config(
            interaction.guild.id,
            config
        )

        await interaction.response.edit_message(
            embed=cold_sarcasm_embed(
                interaction.guild.id
            ),
            view=ColdSarcasmView()
        )

    @discord.ui.button(
        label="🔴 OFF",
        style=discord.ButtonStyle.red,
        row=1
    )
    async def off_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        config = get_cold_config(
            interaction.guild.id
        )

        config["enabled"] = False

        save_cold_config(
            interaction.guild.id,
            config
        )

        await interaction.response.edit_message(
            embed=cold_sarcasm_embed(
                interaction.guild.id
            ),
            view=ColdSarcasmView()
        )

    @discord.ui.button(
        label="⏱ Timeout時間",
        style=discord.ButtonStyle.secondary,
        row=2
    )
    async def timeout_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_modal(
            ColdTimeoutModal()
        )

    @discord.ui.button(
        label="⬅ 戻る",
        style=discord.ButtonStyle.gray,
        row=2
    )
    async def back_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            embed=settings_embed(
                interaction.guild.id
            ),
            view=SettingsView()
        )


# =========================================================
# 冷笑感知 - 処理選択
# =========================================================

class ColdActionSelect(discord.ui.Select):

    def __init__(self):

        super().__init__(
            placeholder="検知したときの処理を選択",
            row=0,
            options=[
                discord.SelectOption(
                    label="何もしない",
                    value="none",
                    emoji="⚪",
                    description="検知するだけで処分しません"
                ),
                discord.SelectOption(
                    label="Warn",
                    value="warn",
                    emoji="⚠️",
                    description="警告を追加します"
                ),
                discord.SelectOption(
                    label="Timeout",
                    value="timeout",
                    emoji="🔇",
                    description="ユーザーをタイムアウトします"
                ),
                discord.SelectOption(
                    label="Kick",
                    value="kick",
                    emoji="👢",
                    description="ユーザーをKickします"
                ),
                discord.SelectOption(
                    label="BAN",
                    value="ban",
                    emoji="🔨",
                    description="ユーザーをBANします"
                )
            ]
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        action = self.values[0]

        config = get_cold_config(
            interaction.guild.id
        )

        config["action"] = action

        save_cold_config(
            interaction.guild.id,
            config
        )

        await interaction.response.edit_message(
            embed=cold_sarcasm_embed(
                interaction.guild.id
            ),
            view=ColdSarcasmView()
        )


# =========================================================
# 冷笑感知 - Timeout時間Modal
# =========================================================

class ColdTimeoutModal(discord.ui.Modal):

    def __init__(self):

        super().__init__(
            title="⏱ Timeout時間設定"
        )

        self.minutes = discord.ui.TextInput(
            label="Timeout時間（分）",
            placeholder="例：10",
            required=True,
            min_length=1,
            max_length=5
        )

        self.add_item(
            self.minutes
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        try:

            minutes = int(
                self.minutes.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ 数字で入力してください。",
                ephemeral=True
            )
            return

        if minutes < 1:

            await interaction.response.send_message(
                "❌ 1分以上を指定してください。",
                ephemeral=True
            )
            return

        if minutes > 40320:

            await interaction.response.send_message(
                "❌ Timeoutは最大40320分までです。",
                ephemeral=True
            )
            return

        config = get_cold_config(
            interaction.guild.id
        )

        config["timeout_minutes"] = minutes

        save_cold_config(
            interaction.guild.id,
            config
        )

        await interaction.response.edit_message(
            embed=cold_sarcasm_embed(
                interaction.guild.id
            ),
            view=ColdSarcasmView()
        )


# =========================================================
# その他
# =========================================================

def simple_embed(title: str):

    return discord.Embed(
        title=title,
        description="この機能は現在作成中です。",
        color=discord.Color.blurple()
    )


class SimpleView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

    @discord.ui.button(
        label="⬅ 戻る",
        style=discord.ButtonStyle.gray
    )
    async def back_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            embed=settings_embed(
                interaction.guild.id
            ),
            view=SettingsView()
        )


# =========================================================
# Settings Cog
# =========================================================

class Settings(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

    @app_commands.command(
        name="settings",
        description="サーバー設定を開きます"
    )
    @app_commands.default_permissions(
        administrator=True
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def settings(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.send_message(
            embed=settings_embed(
                interaction.guild.id
            ),
            view=SettingsView(),
            ephemeral=True
        )


# =========================================================
# Setup
# =========================================================

async def setup(bot):

    await bot.add_cog(
        Settings(bot)
    )