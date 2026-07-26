import discord
from discord.ext import commands
from discord import app_commands


class RoleSelect(discord.ui.Select):

    def __init__(self, roles):

        options = []

        for role in roles:
            options.append(
                discord.SelectOption(
                    label=role.name,
                    value=str(role.id)
                )
            )

        super().__init__(
            placeholder="取得するロールを選択",
            options=options
        )


    async def callback(self, interaction: discord.Interaction):

        role_id = int(self.values[0])

        role = interaction.guild.get_role(role_id)

        if role in interaction.user.roles:

            await interaction.user.remove_roles(role)

            await interaction.response.send_message(
                f"❌ {role.name} を外しました",
                ephemeral=True
            )

        else:

            await interaction.user.add_roles(role)

            await interaction.response.send_message(
                f"✅ {role.name} を取得しました",
                ephemeral=True
            )



class RoleView(discord.ui.View):

    def __init__(self, roles):

        super().__init__(timeout=None)

        self.add_item(
            RoleSelect(roles)
        )



class RolePanel(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @app_commands.command(
        name="rolepanel",
        description="ロールパネル作成"
    )
    @app_commands.default_permissions(administrator=True)
    async def rolepanel(
        self,
        interaction: discord.Interaction
    ):


        roles = [
            role for role in interaction.guild.roles
            if role.name != "@everyone"
        ][:25]


        embed = discord.Embed(
            title="🎭 ロール選択",
            description="取得したいロールを選択してください",
            color=discord.Color.blue()
        )


        await interaction.channel.send(
            embed=embed,
            view=RoleView(roles)
        )


        await interaction.response.send_message(
            "✅ ロールパネルを作成しました",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(RolePanel(bot))