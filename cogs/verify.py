import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
import json
import os

VERIFY_FILE = "verify.json"


def load_verify():
    if not os.path.exists(VERIFY_FILE):
        return {}

    with open(
        VERIFY_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def save_verify(data):
    with open(
        VERIFY_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def get_guild_data(guild_id: int):
    data = load_verify()

    gid = str(guild_id)

    if gid not in data:
        data[gid] = {
            "enabled": True,
            "role": None,
            "unverified": None,

            "title": "🔐 サーバー認証",

            "description":
                "サーバーへようこそ！\n\n"
                "下のボタンを押して認証してください。",

            "rules": "",
            
            "button": "✅ 認証する",

            "color": 0x5865F2,

            "image": None
        }

        save_verify(data)

    return data
class RuleModal(discord.ui.Modal):

    def __init__(self, guild_id: int):
        super().__init__(title="サーバールール設定")

        data = get_guild_data(guild_id)
        gid = str(guild_id)

        self.rules = discord.ui.TextInput(
            label="ルール",
            style=discord.TextStyle.paragraph,
            placeholder=(
                "① 荒らし禁止\n"
                "② スパム禁止\n"
                "③ 暴言禁止"
            ),
            default=data[gid].get("rules", ""),
            required=True,
            max_length=4000
        )

        self.add_item(self.rules)


    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        data = get_guild_data(interaction.guild.id)

        gid = str(interaction.guild.id)

        data[gid]["rules"] = self.rules.value

        save_verify(data)

        await interaction.response.send_message(
            "✅ ルールを保存しました。",
            ephemeral=True
        )
class VerifyView(discord.ui.View):

    def __init__(self, label="✅ 認証する"):
        super().__init__(timeout=None)

        self.verify_button.label = label

    @discord.ui.button(
        label="✅ 認証する",
        style=discord.ButtonStyle.success,
        custom_id="verify_button"
    )
    async def verify_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        data = load_verify()

        guild = data.get(str(interaction.guild.id))

        if guild is None:
            await interaction.response.send_message(
                "❌ 認証設定がありません。",
                ephemeral=True
            )
            return
        
        if not guild.get("enabled", True):
            await interaction.response.send_message(
                "❌ 認証機能は現在OFFです。",
                ephemeral=True
            )
            return

        role_id = guild.get("role")

        if role_id is None:
            await interaction.response.send_message(
                "❌ 認証ロールが設定されていません。",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(role_id)

        if role is None:
            await interaction.response.send_message(
                "❌ 認証ロールが見つかりません。",
                ephemeral=True
            )
            return

        if role in interaction.user.roles:
            await interaction.response.send_message(
                "✅ 既に認証済みです。",
                ephemeral=True
            )
            return

        try:
            await interaction.user.add_roles(
                role,
                reason="認証完了"
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Botにロールを付与する権限がありません。",
                ephemeral=True
            )
            return

        # 未認証ロールを外す
        unverified_id = guild.get("unverified")

        if unverified_id:
            unverified = interaction.guild.get_role(unverified_id)

            if (
                unverified
                and unverified in interaction.user.roles
            ):
                try:
                    await interaction.user.remove_roles(
                        unverified,
                        reason="認証完了"
                    )
                except discord.Forbidden:
                    pass

        embed = discord.Embed(
            title="✅ 認証完了",
            description=f"{role.mention} を付与しました！",
            color=discord.Color.green()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

        # DM送信
        try:
            dm = discord.Embed(
                title="✅ 認証完了",
                description=(
                    f"**{interaction.guild.name}** の認証が完了しました！\n\n"
                    "サーバーをお楽しみください。"
                ),
                color=discord.Color.green()
            )

            if interaction.guild.icon:
                dm.set_thumbnail(url=interaction.guild.icon.url)

            await interaction.user.send(embed=dm)

        except discord.Forbidden:
            pass

        # サーバー内のメッセージ
        embed = discord.Embed(
            title="✅ 認証完了",
            description=f"{role.mention} を付与しました！",
            color=discord.Color.green()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
class Verify(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        data = load_verify()

        if not data:
            self.bot.add_view(VerifyView())
        else:
            for guild in data.values():
                self.bot.add_view(
                    VerifyView(
                        guild.get("button", "✅ 認証する")
                    )
                )

    @app_commands.command(
        name="verifysetup",
        description="認証パネルを作成します"
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(
        color=[
            Choice(name="🔵 Discord Blue", value="5865F2"),
            Choice(name="🟢 Green", value="57F287"),
            Choice(name="🔴 Red", value="ED4245"),
            Choice(name="🟡 Yellow", value="FEE75C"),
            Choice(name="🟣 Purple", value="9B59B6"),
            Choice(name="🩷 Pink", value="FF69B4"),
            Choice(name="🩵 Sky Blue", value="87CEEB"),
            Choice(name="🟧 Orange", value="FFA500"),
            Choice(name="⚫ Black", value="2B2D31"),
            Choice(name="⚪ White", value="FFFFFF"),
        ]
    )
    async def verifysetup(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        title: str,
        description: str,
        button: str,
        color: Choice[str] | None = None,
        unverified: discord.Role | None = None,
        image: discord.Attachment | None = None
    ):

        if color is None:
            color_value = 0x5865F2  # デフォルト色（Discord Blue）
        else:
            color_value = int(color.value, 16)
            

        data = get_guild_data(interaction.guild.id)

        gid = str(interaction.guild.id)

        data[gid]["role"] = role.id
        data[gid]["unverified"] = unverified.id if unverified else None
        data[gid]["title"] = title
        data[gid]["description"] = description
        data[gid]["button"] = button
        data[gid]["color"] = color_value
        data[gid]["image"] = image.url if image else None

        save_verify(data)


        rules = data[gid].get("rules", "ルールは設定されていません。")
        rules = rules.replace("\r\n", "\n")

        embed = discord.Embed(
            title=title,
            color=color_value
        )

        embed.description = (
            f"{description}\n\n"
            "📜 **サーバールール**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"{rules}\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "✅ **下のボタンを押すとルールに同意したものとみなします。**"
        )

        if image:
            embed.set_image(url=image.url)

        embed.add_field(
            name="認証後",
            value=role.mention,
            inline=False
        )

        if unverified:
            embed.add_field(
                name="未認証ロール",
                value=unverified.mention,
                inline=False
            )

        embed.set_footer(
            text="Verification System"
        )

        await interaction.channel.send(
            embed=embed,
            view=VerifyView(button)
        )

        await interaction.response.send_message(
            "✅ 認証パネルを設置しました。",
            ephemeral=True
        )
    @app_commands.command(
        name="setrules",
        description="認証パネルのルールを設定します"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def setrules(
        self,
        interaction: discord.Interaction
    ):
        await interaction.response.send_modal(
            RuleModal(interaction.guild.id)
        )
    @app_commands.command(
        name="verifytoggle",
        description="認証機能をON/OFFします"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.choices(
        state=[
            app_commands.Choice(name="ON", value="on"),
            app_commands.Choice(name="OFF", value="off"),
        ]
    )
    async def verifytoggle(
        self,
        interaction: discord.Interaction,
        state: Choice[str]
    ):
        data = get_guild_data(interaction.guild.id)

        gid = str(interaction.guild.id)

        data[gid]["enabled"] = (state.value == "on")

        save_verify(data)

        await interaction.response.send_message(
            f"✅ 認証を **{state.value.upper()}** にしました。",
            ephemeral=True
        )

    
    


async def setup(bot):
    await bot.add_cog(
        Verify(bot)
    )