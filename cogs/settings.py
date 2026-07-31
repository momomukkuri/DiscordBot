import discord
from discord.ext import commands
from discord import app_commands
import json
import os


class SettingsSelect(discord.ui.Select):

    def __init__(self):

        options = [

            discord.SelectOption(
                label="AutoMod",
                emoji="🛡",
                description="AutoModの設定"
            ),

            discord.SelectOption(
                label="X機能",
                emoji="🎥",
                description="X動画変換・リンク展開"
            ),

            discord.SelectOption(
                label="Welcome",
                emoji="👋",
                description="Welcome・認証"
            ),

            discord.SelectOption(
                label="ログ",
                emoji="📋",
                description="ログ設定"
            ),

            discord.SelectOption(
                label="その他",
                emoji="⚙️",
                description="その他の設定"
            )

        ]

        super().__init__(
            placeholder="設定を選択してください",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        if self.values[0] == "AutoMod":

            await interaction.response.edit_message(
                embed=automod_embed(interaction.guild.id),
                view=AutoModView()
            )

        else:

            await interaction.response.send_message(
                "この項目は次回作成します。",
                ephemeral=True
            )

class SettingsView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(SettingsSelect())

    def load_json(file):

        if not os.path.exists(file):
            return {}

        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)


    def status(value):

        return "🟢 ON" if value else "🔴 OFF"


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

        with open(
            "automod.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=4
            )

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

        with open(
            "automod.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=4
            )

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
            embed=discord.Embed(
                title="⚙️ サーバー設定",
                description="カテゴリを選択してください。",
                color=discord.Color.green()
            ),
            view=SettingsView()
        )

class Settings(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # -----------------
    # json読み込み
    # -----------------
    def load_json(self, file):

        if not os.path.exists(file):
            return {}

        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)

    # -----------------
    # ON/OFF表示
    # -----------------
    def status(self, value):

        return "🟢 ON" if value else "🔴 OFF"

    # -----------------
    # /settings
    # -----------------
    @app_commands.command(
        name="settings",
        description="サーバー設定を表示します"
    )
    async def settings(
        self,
        interaction: discord.Interaction
    ):

        guild = str(interaction.guild.id)

        automod = self.load_json("automod.json")
        xsave = self.load_json("xsave.json")
        xembed = self.load_json("xembed.json")

        embed = discord.Embed(
            title="⚙️ サーバー設定",
            color=discord.Color.green()
        )

        auto = automod.get(guild, {})

        embed.add_field(
            name="🛡 AutoMod",
            value=(
                f"アンチスパム：{self.status(auto.get('spam', False))}\n"
                f"招待リンク：{self.status(auto.get('invite', False))}\n"
                f"禁止ワード：{self.status(auto.get('ngword', False))}\n"
                f"メンション：{self.status(auto.get('mention', False))}"
            ),
            inline=False
        )

        embed.add_field(
            name="🎥 X機能",
            value=(
                f"X動画変換：{self.status(xsave.get(guild, False))}\n"
                f"Xリンク展開：{self.status(xembed.get(guild, False))}"
            ),
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            view=SettingsView()
        )


async def setup(bot):

    await bot.add_cog(
        Settings(bot)
    )