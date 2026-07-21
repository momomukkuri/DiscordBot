import discord
from discord.ext import commands
from discord import app_commands
import json
import os


class VerifyView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

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

        verify_file = "verify.json"

        if not os.path.exists(verify_file):

            await interaction.response.send_message(
                "❌ 認証設定がありません。",
                ephemeral=True
            )
            return

        with open(
            verify_file,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        guild_id = str(interaction.guild.id)

        if guild_id not in data:

            await interaction.response.send_message(
                "❌ 認証ロールが設定されていません。",
                ephemeral=True
            )
            return

        role_id = data[guild_id]["role"]

        role = interaction.guild.get_role(role_id)

        if role is None:

            await interaction.response.send_message(
                "❌ 認証ロールが見つかりません。",
                ephemeral=True
            )
            return

        if role in interaction.user.roles:

            await interaction.response.send_message(
                "✅ あなたは既に認証済みです。",
                ephemeral=True
            )
            return

        try:

            await interaction.user.add_roles(
                role,
                reason="認証完了"
            )

            # 未認証ロールを外す
            unverified_id = data[guild_id].get("unverified")

            if unverified_id:

                unverified_role = interaction.guild.get_role(unverified_id)

                if (
                    unverified_role
                    and unverified_role in interaction.user.roles
                ):
                    await interaction.user.remove_roles(
                        unverified_role,
                        reason="認証完了"
                    )
            # 認証ログ
            if os.path.exists("logs.json"):

                with open(
                    "logs.json",
                    "r",
                    encoding="utf-8"
                ) as f:
                    logs = json.load(f)

                guild_logs = logs.get(
                    str(interaction.guild.id),
                    {}
                )

                channel_id = guild_logs.get("monitor")

                if channel_id:

                    log_channel = interaction.guild.get_channel(
                        channel_id
                    )

                    if log_channel:

                        log_embed = discord.Embed(
                            title="✅ 認証完了",
                            color=discord.Color.green()
                        )

                        log_embed.add_field(
                            name="ユーザー",
                            value=f"{interaction.user.mention}\n`{interaction.user.id}`",
                            inline=False
                        )

                        log_embed.add_field(
                            name="認証ロール",
                            value=role.mention,
                            inline=False
                        )

                        if unverified_id:
                            log_embed.add_field(
                                name="未認証ロール",
                                value=unverified_role.mention,
                                inline=False
                            )

                        await log_channel.send(
                            embed=log_embed
                        )
            embed = discord.Embed(
                title="✅ 認証完了",
                description=f"{role.mention} を付与しました！",
                color=discord.Color.green()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ Botにロールを付与する権限がありません。",
                ephemeral=True
            )


class Verify(commands.Cog):

    def __init__(self, bot):

        self.bot = bot
        self.verify_file = "verify.json"

        # 永続ボタン
        self.bot.add_view(
            VerifyView()
        )

    # ------------------------
    # 認証ロール設定
    # ------------------------
    @app_commands.command(
        name="setverifyrole",
        description="認証後に付与するロールを設定します"
    )
    @app_commands.default_permissions(
        administrator=True
    )
    async def setverifyrole(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):

        data = {}

        if os.path.exists(self.verify_file):

            with open(
                self.verify_file,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

        guild_id = str(interaction.guild.id)

        if guild_id not in data:

            data[guild_id] = {}

        data[guild_id]["role"] = role.id

        with open(
            self.verify_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )

        embed = discord.Embed(
            title="✅ 認証ロール設定",
            description=f"{role.mention} を認証ロールに設定しました。",
            color=discord.Color.green()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
    # ------------------------
    # 認証パネル設置
    # ------------------------
    @app_commands.command(
        name="verifysetup",
        description="認証パネルを設置します"
    )
    @app_commands.default_permissions(
        administrator=True
    )
    async def verifysetup(
        self,
        interaction: discord.Interaction
    ):

        if not os.path.exists(self.verify_file):

            await interaction.response.send_message(
                "❌ 先に /setverifyrole を実行してください。",
                ephemeral=True
            )
            return

        with open(
            self.verify_file,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        guild_id = str(interaction.guild.id)

        if guild_id not in data:

            await interaction.response.send_message(
                "❌ 先に /setverifyrole を実行してください。",
                ephemeral=True
            )
            return

        role_id = data[guild_id].get("role")

        if role_id is None:

            await interaction.response.send_message(
                "❌ 認証ロールが設定されていません。",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(role_id)

        if role is None:

            await interaction.response.send_message(
                "❌ 設定されたロールが見つかりません。",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🔐 サーバー認証",
            description=(
                "サーバーへようこそ！\n\n"
                "ルールを確認したら\n"
                "**下のボタンを押して認証してください。**"
            ),
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="認証後",
            value=f"{role.mention} が付与されます。",
            inline=False
        )
        image_url = data[guild_id].get("image")

        if image_url:
            embed.set_image(
                url=image_url
            )
        embed.set_footer(
            text="MOMON 鯖管理Bot"
        )

        await interaction.channel.send(
            embed=embed,
            view=VerifyView()
        )

        await interaction.response.send_message(
            "✅ 認証パネルを設置しました。",
            ephemeral=True
        )
    # ------------------------
    # 未認証ロール設定
    # ------------------------
    @app_commands.command(
        name="setunverifiedrole",
        description="参加時に付与する未認証ロールを設定します"
    )
    @app_commands.default_permissions(
        administrator=True
    )
    async def setunverifiedrole(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):

        data = {}

        if os.path.exists(self.verify_file):

            with open(
                self.verify_file,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

        guild_id = str(interaction.guild.id)

        if guild_id not in data:

            data[guild_id] = {}

        data[guild_id]["unverified"] = role.id

        with open(
            self.verify_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )

        embed = discord.Embed(
            title="🔒 未認証ロール設定",
            description=f"{role.mention} を未認証ロールに設定しました。",
            color=discord.Color.orange()
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
    @app_commands.command(
    name="setverifyimage",
    description="認証パネルの画像・GIFを設定します"
    )
    @app_commands.default_permissions(
        administrator=True
    )
    async def setverifyimage(
        self,
        interaction: discord.Interaction,
        url: str
    ):

        data = {}

        if os.path.exists(self.verify_file):
            with open(
                self.verify_file,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)

        guild_id = str(interaction.guild.id)

        if guild_id not in data:
            data[guild_id] = {}

        data[guild_id]["image"] = url

        with open(
            self.verify_file,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )

        embed = discord.Embed(
            title="🖼️ 認証画像設定",
            description="認証パネルの画像を設定しました。",
            color=discord.Color.green()
        )

        embed.add_field(
            name="URL",
            value=url,
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(
        Verify(bot)
    )