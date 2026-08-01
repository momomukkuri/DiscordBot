import discord
from discord.ext import commands
from discord import app_commands


class RoleButton(discord.ui.Button):
    def __init__(self, role: discord.Role):
        super().__init__(
            label=role.name,
            style=discord.ButtonStyle.secondary,
            custom_id=f"role_{role.id}"
        )
        self.role = role

    async def callback(self, interaction: discord.Interaction):

        member = interaction.user

        if self.role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "❌ このロールはBotが管理できません。",
                ephemeral=True
            )
            return

        if self.role in member.roles:
            await member.remove_roles(self.role)
            await interaction.response.send_message(
                f"❌ {self.role.name} を解除しました。",
                ephemeral=True
            )
        else:
            await member.add_roles(self.role)
            await interaction.response.send_message(
                f"✅ {self.role.name} を取得しました。",
                ephemeral=True
            )
    


class RoleView(discord.ui.View):

    def __init__(self, roles):
        super().__init__(timeout=None)

        for role in roles:
            self.add_item(RoleButton(role))


class RolePanel(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="rolepanel",
        description="ロールパネルを作成します"
    )
    @app_commands.default_permissions(administrator=True)
    async def rolepanel(
        self,
        interaction: discord.Interaction,

        role1: discord.Role,
        role2: discord.Role = None,
        role3: discord.Role = None,
        role4: discord.Role = None,
        role5: discord.Role = None,
        role6: discord.Role = None,
        role7: discord.Role = None,
        role8: discord.Role = None,
        role9: discord.Role = None,
        role10: discord.Role = None,
    ):

        roles = []

        for role in [
            role1, role2, role3, role4, role5,
            role6, role7, role8, role9, role10
        ]:

            if role is None:
                continue

            if role == interaction.guild.default_role:
                continue

            if role.managed:
                continue

            if role >= interaction.guild.me.top_role:
                continue

            roles.append(role)

        if len(roles) == 0:

            await interaction.response.send_message(
                "❌ 配布できるロールがありません。",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🎭 ロールパネル",
            description=(
                "下のボタンを押してロールを受け取れます。\n"
                "もう一度押すと解除できます。"
            ),
            color=discord.Color.blurple()
        )

        await interaction.channel.send(
            embed=embed,
            view=RoleView(roles)
        )

        await interaction.response.send_message(
            "✅ ロールパネルを作成しました。",
            ephemeral=True
        )
# ==========================
# Cog登録
# ==========================

async def setup(bot: commands.Bot):

    await bot.add_cog(RolePanel(bot))