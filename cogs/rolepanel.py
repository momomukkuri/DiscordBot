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
                    value=str(role.id),
                    description=f"{role.name} を取得"
                )
            )

        super().__init__(
            placeholder="取得したいロールを選択",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="role_select"
        )


    async def callback(self, interaction: discord.Interaction):

        role_id = int(self.values[0])

        role = interaction.guild.get_role(role_id)

        if role is None:
            await interaction.response.send_message(
                "❌ ロールが見つかりません",
                ephemeral=True
            )
            return


        member = interaction.user


        if role in member.roles:

            await member.remove_roles(role)

            await interaction.response.send_message(
                f"❌ {role.name} を解除しました",
                ephemeral=True
            )

        else:

            await member.add_roles(role)

            await interaction.response.send_message(
                f"✅ {role.name} を取得しました",
                ephemeral=True
            )



class RoleView(discord.ui.View):

    def __init__(self, roles):

        super().__init__(timeout=None)

        if roles:
            self.add_item(
                RoleSelect(roles)
            )



class RolePanel(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        # 再起動後もViewを有効化
        bot.add_view(
            RoleView([])
        )


    @app_commands.command(
        name="rolepanel",
        description="ロール選択パネルを作成します"
    )
    @app_commands.default_permissions(administrator=True)
    async def rolepanel(
        self,
        interaction: discord.Interaction
    ):


        roles = [
            role
            for role in interaction.guild.roles
            if role != interaction.guild.default_role
            and role < interaction.guild.me.top_role
        ][:25]


        if not roles:

            await interaction.response.send_message(
                "❌ 付与可能なロールがありません。\nBotのロール位置を確認してください。",
                ephemeral=True
            )
            return



        embed = discord.Embed(
            title="🎭 ロール選択",
            description=(
                "取得したいロールを選択してください。\n\n"
                "同じロールをもう一度選択すると解除されます。"
            ),
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