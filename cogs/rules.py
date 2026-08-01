import discord
from discord.ext import commands
from discord import app_commands
import json
import os

VERIFY_FILE = "verify.json"
def load_data():
    if not os.path.exists(VERIFY_FILE):
        return {}

    with open(VERIFY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(VERIFY_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )
class Rules(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(RuleView())
    @app_commands.command(
        name="setverifiedrole",
        description="認証済みロールを設定します"
    )
    @app_commands.default_permissions(administrator=True)
    async def setverifiedrole(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):
        data = load_data()

        guild_id = str(interaction.guild.id)

        if guild_id not in data:
            data[guild_id] = {}

        data[guild_id]["verified"] = role.id

        save_data(data)

        await interaction.response.send_message(
            f"✅ 認証済みロールを {role.mention} に設定しました。",
            ephemeral=True
        )


    @app_commands.command(
        name="setunverifiedrole",
        description="未認証ロールを設定します"
    )
    @app_commands.default_permissions(administrator=True)
    async def setunverifiedrole(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):
        data = load_data()

        guild_id = str(interaction.guild.id)

        if guild_id not in data:
            data[guild_id] = {}

        data[guild_id]["unverified"] = role.id

        save_data(data)

        await interaction.response.send_message(
            f"✅ 未認証ロールを {role.mention} に設定しました。",
            ephemeral=True
        )
    @app_commands.command(
        name="rulepanel",
        description="ルール認証パネルを送信します"
    )
    @app_commands.default_permissions(administrator=True)
    async def rulepanel(
        self,
        interaction: discord.Interaction
    ):
        embed = discord.Embed(
            title="📜 サーバールール",
            description=(
                "ここにサーバールールを書いてください。\n\n"
                "内容を確認したら下のボタンを押してください。"
            ),
            color=0x5865F2
        )

        await interaction.channel.send(
            embed=embed,
            view=RuleView()
        )

        await interaction.response.send_message(
            "✅ 認証パネルを送信しました。",
            ephemeral=True
        )
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        data = load_data()

        guild_id = str(member.guild.id)

        if guild_id not in data:
            return

        if "unverified" not in data[guild_id]:
            return

        role = member.guild.get_role(
            data[guild_id]["unverified"]
        )

        if role is None:
            return

        try:
            await member.add_roles(role, reason="未認証ロール自動付与")
        except discord.Forbidden:
            print("Botにロールを付与する権限がありません。")
class RuleView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="✅ 認証する",
        style=discord.ButtonStyle.success,
        custom_id="rule_verify"
    )
    
    async def verify(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ サーバー内で使用してください。",
                ephemeral=True
            )
            return
        data = load_data()

        guild_id = str(interaction.guild.id)

        if guild_id not in data:
            await interaction.response.send_message(
                "❌ このサーバーはまだ設定されていません。",
                ephemeral=True
            )
            return

        member = interaction.guild.get_member(interaction.user.id)

        if member is None:
            await interaction.response.send_message(
                "❌ メンバーを取得できませんでした。",
                ephemeral=True
            )
            return
        verified_role = interaction.guild.get_role(
            data[guild_id].get("verified")
        ) if "verified" in data[guild_id] else None

        unverified_role = interaction.guild.get_role(
            data[guild_id].get("unverified")
        ) if "unverified" in data[guild_id] else None


        if verified_role is None:
            await interaction.response.send_message(
                "❌ 認証済みロールが見つかりません。",
                ephemeral=True
            )
            return

        if verified_role in member.roles:
            await interaction.response.send_message(
                "❌ あなたは既に認証済みです。",
                ephemeral=True
            )
            return

        if unverified_role:
            await member.remove_roles(unverified_role)
        try:
            print("① ロール付与開始")
            await member.add_roles(verified_role)
            print("② ロール付与成功")
        except discord.Forbidden:
            print("ロール付与失敗")
            await interaction.response.send_message(
                "❌ Botにロール管理権限がありません。",
                ephemeral=True
            )
            return

    


async def setup(bot):
    await bot.add_cog(
        Rules(bot)
    )