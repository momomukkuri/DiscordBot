import discord
from discord.ext import commands
from discord import app_commands
import json
import os

print("automod =", load_json("automod.json"))
print("xsave =", load_json("xsave.json"))
print("xembed =", load_json("xembed.json"))
print("welcome =", load_json("welcome.json"))
print("verify =", load_json("verify.json"))

# ------------------------
# JSON
# ------------------------

def load_json(file):

    if not os.path.exists(file):
        return {}

    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(file, data):

    with open(file, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


# ------------------------
# ON / OFF表示
# ------------------------

def status(value):

    return "🟢 ON" if value else "🔴 OFF"


# ------------------------
# メイン画面Embed
# ------------------------

def settings_embed(guild_id):

    automod = load_json("automod.json")
    xsave = load_json("xsave.json")
    xembed = load_json("xembed.json")

    auto = automod.get(str(guild_id), {})

    embed = discord.Embed(
        title="⚙️ サーバー設定",
        description="変更したいカテゴリを選択してください。",
        color=discord.Color.green()
    )

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

    embed.add_field(
        name="🎥 X機能",
        value=(
            f"動画変換：{status(xsave.get(str(guild_id), {}).get('enabled', False))}"
            f"リンク展開：{status(xembed.get(str(guild_id), {}).get('enabled', False))}"
        ),
        inline=False
    )
    welcome = load_json("welcome.json")
    verify = load_json("verify.json")

    embed.add_field(
        name="👋 Welcome",
        value=(
            f"Welcome：{status(welcome.get(str(guild_id), {}).get("enabled", False))}\n"
            f"認証：{status(verify.get(str(guild_id), {}).get('enabled', False))}",
        ),
        inline=False
    )

    return embed
# ------------------------
# 設定メニュー
# ------------------------

class SettingsSelect(discord.ui.Select):

    def __init__(self):

        options = [

            discord.SelectOption(
                label="AutoMod",
                emoji="🛡",
                description="AutoModを設定"
            ),

            discord.SelectOption(
                label="X機能",
                emoji="🎥",
                description="X関連機能を設定"
            ),

            discord.SelectOption(
                label="Welcome",
                emoji="👋",
                description="Welcomeを設定"
            ),

            discord.SelectOption(
                label="ログ",
                emoji="📋",
                description="ログを設定"
            ),

            discord.SelectOption(
                label="その他",
                emoji="⚙️",
                description="その他"
            )

        ]

        super().__init__(
            placeholder="設定項目を選択",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        value = self.values[0]

        if value == "AutoMod":

            await interaction.response.edit_message(
                embed=automod_embed(interaction.guild.id),
                view=AutoModView()
            )

        elif value == "X機能":

            await interaction.response.edit_message(
                embed=x_embed(interaction.guild.id),
                view=XView()
            )

        elif value == "Welcome":

            await interaction.response.edit_message(
                embed=welcome_embed(interaction.guild.id),
                view=WelcomeView()
            )

        elif value == "ログ":

            await interaction.response.edit_message(
                embed=log_embed(interaction.guild.id),
                view=LogView()
            )

        elif value == "その他":

            await interaction.response.edit_message(
                embed=simple_embed("⚙️ その他設定"),
                view=SimpleView()
            )


class SettingsView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(SettingsSelect())
# ------------------------
# AutoMod
# ------------------------

def automod_embed(guild_id):

    data = load_json("automod.json")

    auto = data.get(str(guild_id), {})

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

        self.add_item(AutoModSelect())


class AutoModSelect(discord.ui.Select):

    def __init__(self):

        super().__init__(
            placeholder="変更する機能",
            options=[
                discord.SelectOption(label="spam"),
                discord.SelectOption(label="invite"),
                discord.SelectOption(label="ngword"),
                discord.SelectOption(label="mention")
            ]
        )

    async def callback(self, interaction: discord.Interaction):

        await interaction.response.edit_message(
            embed=automod_embed(interaction.guild.id),
            view=AutoModToggleView(self.values[0])
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

        guild = str(interaction.guild.id)

        if guild not in data:
            data[guild] = {}

        data[guild][self.feature] = True

        save_json("automod.json", data)

        await interaction.response.edit_message(
            embed=automod_embed(interaction.guild.id),
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

        guild = str(interaction.guild.id)

        if guild not in data:
            data[guild] = {}

        data[guild][self.feature] = False

        save_json("automod.json", data)

        await interaction.response.edit_message(
            embed=automod_embed(interaction.guild.id),
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
            embed=settings_embed(interaction.guild.id),
            view=SettingsView()
        )
# ------------------------
# X機能
# ------------------------

def x_embed(guild_id):

    xsave = load_json("xsave.json")
    xembed = load_json("xembed.json")

    embed = discord.Embed(
        title="🎥 X機能",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="現在の状態",
        value=(
            f"X動画変換：{status(xsave.get(str(guild_id), False))}\n"
            f"Xリンク展開：{status(xembed.get(str(guild_id), False))}"
        ),
        inline=False
    )

    return embed
# ------------------------
# Welcome
# ------------------------

def welcome_embed(guild_id):

    welcome = load_json("welcome.json")
    verify = load_json("verify.json")

    embed = discord.Embed(
        title="👋 Welcome設定",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="現在の状態",
        value=(
            f"Welcome：{status(welcome.get(str(guild_id), {}).get('enabled', False))}\n"
            f"認証：{status(verify.get(str(guild_id), {}).get('enabled', False))}"
        ),
        inline=False
    )

    return embed
# ------------------------
# ログ
# ------------------------

def log_embed(guild_id):

    logs = load_json("logtoggle.json")

    data = logs.get(str(guild_id), {})

    embed = discord.Embed(
        title="📋 ログ設定",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="現在の状態",
        value=(
            f"メッセージ：{status(data.get('message', False))}\n"
            f"参加退出：{status(data.get('joinleave', False))}\n"
            f"監視ログ：{status(data.get('monitor', False))}"
        ),
        inline=False
    )

    return embed

class LogView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(LogSelect())


class LogSelect(discord.ui.Select):

    def __init__(self):

        super().__init__(
            placeholder="変更する機能",
            options=[
                discord.SelectOption(label="message"),
                discord.SelectOption(label="joinleave"),
                discord.SelectOption(label="monitor")
            ]
        )

    async def callback(self, interaction: discord.Interaction):

        await interaction.response.edit_message(
            embed=log_embed(interaction.guild.id),
            view=LogToggleView(self.values[0])
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

        data = load_json("logtoggle.json")

        guild = str(interaction.guild.id)

        if guild not in data:
            data[guild] = {}

        data[guild][self.feature] = True

        save_json("logtoggle.json", data)

        await interaction.response.edit_message(
            embed=log_embed(interaction.guild.id),
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

        data = load_json("logtoggle.json")

        guild = str(interaction.guild.id)

        if guild not in data:
            data[guild] = {}

        data[guild][self.feature] = False

        save_json("logtoggle.json", data)

        await interaction.response.edit_message(
            embed=log_embed(interaction.guild.id),
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
            embed=settings_embed(interaction.guild.id),
            view=SettingsView()
        )

class WelcomeView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(WelcomeSelect())


class WelcomeSelect(discord.ui.Select):

    def __init__(self):

        super().__init__(
            placeholder="変更する機能",
            options=[
                discord.SelectOption(label="Welcome"),
                discord.SelectOption(label="認証")
            ]
        )

    async def callback(self, interaction: discord.Interaction):

        await interaction.response.edit_message(
            embed=welcome_embed(interaction.guild.id),
            view=WelcomeToggleView(self.values[0])
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

        file = "welcome.json" if self.feature == "Welcome" else "verify.json"

        data = load_json(file)

        guild = str(interaction.guild.id)

        if guild not in data:
            data[guild] = {}

        data[guild]["enabled"] = True

        save_json(file, data)

        await interaction.response.edit_message(
            embed=welcome_embed(interaction.guild.id),
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

        file = "welcome.json" if self.feature == "Welcome" else "verify.json"

        data = load_json(file)

        guild = str(interaction.guild.id)

        if guild not in data:
            data[guild] = {}

        data[guild]["enabled"] = False

        save_json(file, data)

        await interaction.response.edit_message(
            embed=welcome_embed(interaction.guild.id),
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
            embed=settings_embed(interaction.guild.id),
            view=SettingsView()
        )

class XView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(XSelect())


class XSelect(discord.ui.Select):

    def __init__(self):

        super().__init__(
            placeholder="変更する機能",
            options=[
                discord.SelectOption(label="X動画変換"),
                discord.SelectOption(label="Xリンク展開")
            ]
        )

    async def callback(self, interaction: discord.Interaction):

        await interaction.response.edit_message(
            embed=x_embed(interaction.guild.id),
            view=XToggleView(self.values[0])
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

        file = "xsave.json" if self.feature == "X動画変換" else "xembed.json"

        data = load_json(file)

        guild = str(interaction.guild.id)

        if guild not in data:
            data[guild] = {}

        data[guild]["enabled"] = True

        save_json(file, data)

        await interaction.response.edit_message(
            embed=x_embed(interaction.guild.id),
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

        file = "xsave.json" if self.feature == "X動画変換" else "xembed.json"

        data = load_json(file)

        guild = str(interaction.guild.id)

        if guild not in data:
            data[guild] = {}

        data[guild]["enabled"] = False

        save_json(file, data)

        await interaction.response.edit_message(
            embed=x_embed(interaction.guild.id),
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
            embed=settings_embed(interaction.guild.id),
            view=SettingsView()
        )
# ------------------------
# 仮画面
# ------------------------

def simple_embed(title: str):

    embed = discord.Embed(
        title=title,
        description="この機能は現在作成中です。",
        color=discord.Color.blurple()
    )

    return embed


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
            embed=settings_embed(interaction.guild.id),
            view=SettingsView()
        )

# ------------------------
# Cog
# ------------------------


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
            embed=settings_embed(interaction.guild.id),
            view=SettingsView(),
            ephemeral=True
        )



async def setup(bot):

    await bot.add_cog(
        Settings(bot)
    )