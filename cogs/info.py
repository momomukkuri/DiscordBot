import discord
from discord.ext import commands
from discord import app_commands


class Info(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    # =========================
    # Userinfo
    # =========================
    @app_commands.command(
        name="userinfo",
        description="ユーザー情報を表示します"
    )
    @app_commands.describe(
        member="情報を表示したいユーザー"
    )
    async def userinfo(
        self,
        interaction: discord.Interaction,
        member: discord.Member = None
    ):

        await interaction.response.defer()


        try:

            if member is None:
                member = interaction.user


            embed = discord.Embed(
                title="👤 ユーザー情報",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )


            embed.set_thumbnail(
                url=member.display_avatar.url
            )


            # ロール取得
            roles = [
                role.mention
                for role in member.roles
                if role.name != "@everyone"
            ]


            if roles:

                role_text = " ".join(roles)

                # 長すぎ防止
                if len(role_text) > 1024:
                    role_text = role_text[:1000] + "..."

            else:

                role_text = "なし"



            embed.add_field(
                name="👤 ユーザー名",
                value=f"{member.mention}\n`{member}`",
                inline=False
            )


            embed.add_field(
                name="🆔 ユーザーID",
                value=f"`{member.id}`",
                inline=False
            )


            embed.add_field(
                name="📅 アカウント作成日",
                value=discord.utils.format_dt(
                    member.created_at,
                    style="F"
                ),
                inline=False
            )


            if member.joined_at:

                embed.add_field(
                    name="📥 サーバー参加日",
                    value=discord.utils.format_dt(
                        member.joined_at,
                        style="F"
                    ),
                    inline=False
                )

            else:

                embed.add_field(
                    name="📥 サーバー参加日",
                    value="取得できません",
                    inline=False
                )


            embed.add_field(
                name="🎭 ロール",
                value=role_text,
                inline=False
            )


            embed.add_field(
                name="🤖 Bot",
                value="はい" if member.bot else "いいえ",
                inline=True
            )


            embed.add_field(
                name="🏷️ ニックネーム",
                value=member.nick or "なし",
                inline=True
            )


            embed.set_footer(
                text=f"実行者: {interaction.user}"
            )


            await interaction.followup.send(
                embed=embed
            )


        except Exception as e:

            print(
                "Userinfo Error:",
                e
            )


            await interaction.followup.send(
                "❌ ユーザー情報取得に失敗しました",
                ephemeral=True
            )
    # =========================
    # Server Info
    # =========================
    @app_commands.command(
        name="serverinfo",
        description="サーバー情報を表示します"
    )
    async def serverinfo(
        self,
        interaction: discord.Interaction
    ):

        guild = interaction.guild


        embed = discord.Embed(
            title="🏠 サーバー情報",
            color=discord.Color.blue()
        )


        if guild.icon:

            embed.set_thumbnail(
                url=guild.icon.url
            )


        embed.add_field(
            name="📛 サーバー名",
            value=guild.name,
            inline=False
        )


        embed.add_field(
            name="🆔 サーバーID",
            value=f"`{guild.id}`",
            inline=False
        )


        embed.add_field(
            name="👑 オーナー",
            value=f"<@{guild.owner_id}>",
            inline=False
        )


        embed.add_field(
            name="👥 メンバー数",
            value=f"{guild.member_count}人",
            inline=True
        )


        embed.add_field(
            name="💬 チャンネル数",
            value=f"{len(guild.channels)}個",
            inline=True
        )


        embed.add_field(
            name="🎭 ロール数",
            value=f"{len(guild.roles)}個",
            inline=True
        )


        embed.add_field(
            name="📅 作成日",
            value=discord.utils.format_dt(
                guild.created_at,
                style="F"
            ),
            inline=False
        )


        embed.add_field(
            name="🚀 ブースト",
            value=f"Lv{guild.premium_tier} ({guild.premium_subscription_count}回)",
            inline=True
        )


        embed.set_footer(
            text=f"実行者: {interaction.user}"
        )


        await interaction.response.send_message(
            embed=embed
        )
    @app_commands.command(
        name="avatar",
        description="ユーザーのアイコンを表示します"
    )
    async def avatar(
        self,
        interaction: discord.Interaction,
        user: discord.Member = None
    ):

        if user is None:
            user = interaction.user

        embed = discord.Embed(
            title=f"🖼️ {user.display_name} のアイコン",
            color=discord.Color.blurple()
        )

        embed.set_image(
            url=user.display_avatar.url
        )

        embed.set_footer(
            text=f"ID: {user.id}"
        )

        await interaction.response.send_message(
            embed=embed
        )
    @app_commands.command(
        name="servericon",
        description="サーバーのアイコンを表示します"
    )
    async def servericon(
        self,
        interaction: discord.Interaction
    ):

        if interaction.guild.icon is None:
            await interaction.response.send_message(
                "❌ このサーバーにはアイコンが設定されていません。",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"🖼️ {interaction.guild.name} のサーバーアイコン",
            color=discord.Color.blurple()
        )

        embed.set_image(
            url=interaction.guild.icon.url
        )

        await interaction.response.send_message(
            embed=embed
        )
    @app_commands.command(
        name="roleinfo",
        description="ロールの情報を表示します"
    )
    async def roleinfo(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):

        members = sum(1 for m in interaction.guild.members if role in m.roles)

        embed = discord.Embed(
            title=f"🎭 {role.name}",
            color=role.color if role.color.value != 0 else discord.Color.blurple()
        )

        embed.add_field(
            name="🆔 ロールID",
            value=f"`{role.id}`",
            inline=False
        )

        embed.add_field(
            name="👥 メンバー数",
            value=f"{members}人",
            inline=True
        )

        embed.add_field(
            name="📍 位置",
            value=str(role.position),
            inline=True
        )

        embed.add_field(
            name="🎨 カラー",
            value=str(role.color),
            inline=True
        )

        embed.add_field(
            name="📅 作成日",
            value=discord.utils.format_dt(
                role.created_at,
                style="F"
            ),
            inline=False
        )

        embed.add_field(
            name="📢 メンション可能",
            value="✅ はい" if role.mentionable else "❌ いいえ",
            inline=True
        )

        embed.add_field(
            name="👑 管理者権限",
            value="✅ はい" if role.permissions.administrator else "❌ いいえ",
            inline=True
        )

        embed.add_field(
            name="🤖 Botロール",
            value="✅ はい" if role.is_bot_managed() else "❌ いいえ",
            inline=True
        )

        await interaction.response.send_message(
            embed=embed
        )
    @app_commands.command(
        name="channelinfo",
        description="チャンネル情報を表示します"
    )
    async def channelinfo(
        self,
        interaction: discord.Interaction,
        channel: discord.abc.GuildChannel = None
    ):

        if channel is None:
            channel = interaction.channel

        embed = discord.Embed(
            title=f"📁 {channel.name}",
            color=discord.Color.blurple()
        )

        embed.add_field(
            name="🆔 チャンネルID",
            value=f"`{channel.id}`",
            inline=False
        )

        embed.add_field(
            name="📂 種類",
            value=str(channel.type).replace("_", " ").title(),
            inline=True
        )

        embed.add_field(
            name="📍 位置",
            value=str(channel.position),
            inline=True
        )

        if channel.category:
            embed.add_field(
                name="🗂️ カテゴリ",
                value=channel.category.name,
                inline=False
            )

        if isinstance(channel, discord.TextChannel):

            embed.add_field(
                name="🐢 スローモード",
                value=f"{channel.slowmode_delay}秒",
                inline=True
            )

            embed.add_field(
                name="🔞 NSFW",
                alue="✅ はい" if channel.nsfw else "❌ いいえ",
                inline=True
            )

        embed.add_field(
            name="📅 作成日",
            value=discord.utils.format_dt(
                channel.created_at,
                style="F"
            ),
            inline=False
        )

        await interaction.response.send_message(
            embed=embed
        )

async def setup(bot):

    await bot.add_cog(
        Info(bot)
    )