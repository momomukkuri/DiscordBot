import discord
from discord.ext import commands
from discord import app_commands
import json
import os


ROLE_FILE = "roles.json"


class RoleButton(discord.ui.Button):

    def __init__(self, role_id, label, emoji):
        super().__init__(
            label=label,
            emoji=emoji,
            style=discord.ButtonStyle.primary
        )
        self.role_id = role_id


    async def callback(self, interaction: discord.Interaction):

        role = interaction.guild.get_role(self.role_id)

        if role is None:
            await interaction.response.send_message(
                "❌ ロールが見つかりません",
                ephemeral=True
            )
            return


        if role in interaction.user.roles:

            await interaction.user.remove_roles(role)

            await interaction.response.send_message(
                f"❌ {role.name} を解除しました",
                ephemeral=True
            )

        else:

            await interaction.user.add_roles(role)

            await interaction.response.send_message(
                f"✅ {role.name} を付与しました",
                ephemeral=True
            )



class RolePanelView(discord.ui.View):

    def __init__(self, roles):
        super().__init__(timeout=None)

        for role in roles:
            self.add_item(
                RoleButton(
                    role["id"],
                    role["name"],
                    role["emoji"]
                )
            )



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
            {
                "id": 123456789012345678,
                "name": "ゲーム",
                "emoji": "🎮"
            },
            {
                "id": 123456789012345679,
                "name": "開発者",
                "emoji": "💻"
            }
        ]


        embed = discord.Embed(
            title="🎭 ロール選択",
            description="ボタンを押してロールを取得できます",
            color=discord.Color.blue()
        )


        await interaction.channel.send(
            embed=embed,
            view=RolePanelView(roles)
        )


        await interaction.response.send_message(
            "✅ ロールパネルを作成しました",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(RolePanel(bot))