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

        # Botが付与できないロール
        if self.role >= interaction.guild.me.top_role:
            await interaction.response.send_message(
                "❌ このロールはBotが管理できません。",
                ephemeral=True
            )
            return

        if self.role in member.roles:

            await member.remove_roles(self.role)

            await interaction.response.send_message(
                f"❌ **{self.role.name}** を解除しました。",
                ephemeral=True
            )

        else:

            await member.add_roles(self.role)

            await interaction.response.send_message(
                f"✅ **{self.role.name}** を取得しました。",
                ephemeral=True
            )


class RoleView(discord.ui.View):

    def __init__(self, roles):

        super().__init__(timeout=None)

        for role in roles[:25]:   # Discordのボタン上限
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
        interaction: discord.Interaction
    ):

        roles = [
            role
            for role in reversed(interaction.guild.roles)
            if role != interaction.guild.default_role
            and role < interaction.guild.me.top_role
            and not role.managed
        ][:25]

        if not roles:
            await interaction.response.send_message(
                "❌ 配布できるロールがありません。\nBotのロールを一番上にしてください。",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🎭 ロールパネル",
            description="**下のボタンを押してロールを受け取れます。**\n\nもう一度押すとロールを解除できます。",
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


async def setup(bot):
    await bot.add_cog(RolePanel(bot))