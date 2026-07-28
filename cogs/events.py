import discord
from discord.ext import commands
from discord import app_commands
from typing import Literal, Optional
import json
import os
import datetime
import asyncio
import re



class Events(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        self.welcome_file = "welcome.json"
        self.ngword_file = "ngwords.json"
        self.automod_file = "automod.json"
        self.ban_count = {}
        self.channel_delete_count = {}
        self.role_delete_count = {}
        self.antiraid = {}
        self.spam_count = {}

    async def send_log(
        self,
        guild,
        embed,
        log_type="joinleave"
    ):
        if not os.path.exists("logs.json"):
            return

        with open("logs.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        guild_data = data.get(str(guild.id), {})
        channel_id = guild_data.get(log_type)

        if not channel_id:
            return

        channel = guild.get_channel(channel_id)

        if channel:
            await channel.send(embed=embed)

    # =========================
    # NGワード読み込み
    # =========================
    def load_ngwords(self):

        if not os.path.exists(self.ngword_file):
            return {}

        with open(self.ngword_file, "r", encoding="utf-8") as f:
            return json.load(f)
    

    # =========================
    # NGワード検知
    # =========================
    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return

        # スパム検知
        await self.check_spam(message)

        # メンションスパム検知
        await self.check_mention_spam(message)

        # 管理者は無視
        if message.author.guild_permissions.manage_guild:
            return

        # 招待リンクブロック
        automod = self.load_automod()
        guild_id = str(message.guild.id)

        if automod.get(guild_id, {}).get("invite", False):

            if re.search(
                r"(discord\.gg/|discord\.com/invite/)",
                message.content,
                re.IGNORECASE
            ):

                try:
                    await message.delete()

                    embed = discord.Embed(
                        title="🚫 招待リンクを削除しました",
                        color=discord.Color.red(),
                        timestamp=datetime.datetime.now()
                    )

                    embed.add_field(
                        name="ユーザー",
                        value=message.author.mention,
                        inline=False
                    )

                    embed.add_field(
                        name="チャンネル",
                        value=message.channel.mention,
                        inline=False
                    )

                    embed.add_field(
                        name="内容",
                        value=message.content,
                        inline=False
                    )

                    await self.send_log(
                        message.guild,
                        embed,
                        "monitor"
                    )

                except discord.Forbidden:
                    pass

                return

        data = self.load_ngwords()

        automod = self.load_automod()

        guild_id = str(message.guild.id)

        # NGワード機能がOFFなら処理しない
        if not automod.get(guild_id, {}).get("ngword", False):
            return

        if guild_id not in data:
            return

        for word in data[guild_id]:

            if word.lower() in message.content.lower():

                try:
                    await message.delete()

                    embed = discord.Embed(
                        title="🚫 禁止ワード検知",
                        color=discord.Color.red(),
                        timestamp=datetime.datetime.now()
                    )

                    embed.add_field(
                        name="ユーザー",
                        value=message.author.mention,
                        inline=False
                    )

                    embed.add_field(
                        name="禁止ワード",
                        value=f"`{word}`",
                        inline=False
                    )

                    embed.add_field(
                        name="チャンネル",
                        value=message.channel.mention,
                        inline=False
                    )

                    await self.send_log(
                        message.guild,
                        embed,
                        "monitor"
                    )

                except discord.Forbidden:
                    pass

                break

    # =========================
    # NGワード管理
    # =========================
    @app_commands.command(
        name="ngword",
        description="禁止ワードを管理します"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ngword(
        self,
        interaction: discord.Interaction,
        action: Literal["add", "remove", "list"],
        word: Optional[str] = None
    ):

        data = self.load_ngwords()

        guild_id = str(interaction.guild.id)

        if guild_id not in data:
            data[guild_id] = []

        # 追加
        if action == "add":

            if not word:
                await interaction.response.send_message(
                    "追加する単語を入力してください。",
                    ephemeral=True
                )
                return

            if word in data[guild_id]:
                await interaction.response.send_message(
                    "その禁止ワードは既に登録されています。",
                    ephemeral=True
                )
                return

            data[guild_id].append(word)

        # 削除
        elif action == "remove":

            if not word:
                await interaction.response.send_message(
                    "削除する単語を入力してください。",
                    ephemeral=True
                )
                return

            if word not in data[guild_id]:
                await interaction.response.send_message(
                    "その禁止ワードは登録されていません。",
                    ephemeral=True
                )
                return

            data[guild_id].remove(word)

        # 一覧
        elif action == "list":

            if not data[guild_id]:
                await interaction.response.send_message(
                    "禁止ワードは登録されていません。",
                    ephemeral=True
                )
                return

            embed = discord.Embed(
                title="🚫 禁止ワード一覧",
                description="\n".join(f"• {w}" for w in data[guild_id]),
                color=discord.Color.red()
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
            return

        else:
            await interaction.response.send_message(
                "actionは add / remove / list のどれかです。",
                ephemeral=True
            )
            return

        with open(self.ngword_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        await interaction.response.send_message(
            "更新しました。",
            ephemeral=True
        )

    # =========================
    # AutoMod設定読み込み
    # =========================
    def load_automod(self):

        if not os.path.exists(self.automod_file):
            return {}

        with open(self.automod_file, "r", encoding="utf-8") as f:
            return json.load(f)
 
    # =========================
    # スパム検知
    # =========================
    async def check_spam(self, message):

        automod = self.load_automod()

        guild_id = str(message.guild.id)

        if not automod.get(guild_id, {}).get("spam", False):
            return

        now = datetime.datetime.now().timestamp()

        user_id = message.author.id

        if user_id not in self.spam_count:
            self.spam_count[user_id] = []

        self.spam_count[user_id].append(now)

        # 5秒以内のメッセージだけ残す
        self.spam_count[user_id] = [
            t for t in self.spam_count[user_id]
            if now - t < 5
        ]

        # 5秒で5回送信したら
        if len(self.spam_count[user_id]) >= 5:

            try:
                await message.channel.purge(
                    limit=20,
                    check=lambda m: m.author.id == user_id
                )

                await message.author.timeout(
                    datetime.timedelta(minutes=10),
                    reason="スパム送信"
                )

                embed = discord.Embed(
                    title="🚨 スパム検知",
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.now()
                )

                embed.add_field(
                    name="ユーザー",
                    value=message.author.mention,
                    inline=False
                )

                embed.add_field(
                    name="内容",
                    value="5秒以内に5回以上送信",
                    inline=False
                )

                embed.add_field(
                    name="処罰",
                    value="10分タイムアウト",
                    inline=False
                )

                await self.send_log(
                    message.guild,
                    embed,
                    "monitor"
                )

            except discord.Forbidden:
                pass

            self.spam_count[user_id].clear()
    # =========================
    # メンションスパム検知
    # =========================
    async def check_mention_spam(self, message):

        automod = self.load_automod()

        guild_id = str(message.guild.id)

        # OFFなら何もしない
        if not automod.get(guild_id, {}).get("mention", False):
            return

        # 5人以上メンション
        if len(message.mentions) < 5:
            return

        try:
            await message.delete()

            await message.author.timeout(
                datetime.timedelta(minutes=10),
                reason="メンションスパム"
            )

            embed = discord.Embed(
                title="🚨 メンションスパム検知",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )

            embed.add_field(
                name="ユーザー",
                value=message.author.mention,
                inline=False
            )

            embed.add_field(
                name="メンション数",
                value=str(len(message.mentions)),
                inline=False
            )

            embed.add_field(
                name="処罰",
                value="10分タイムアウト",
                inline=False
            )

            await self.send_log(
                message.guild,
                embed,
                "monitor"
            )

        except discord.Forbidden:
            pass
    # =========================
    # AutoMod設定
    # =========================
    @app_commands.command(
        name="automod",
        description="AutoModのON/OFFを設定します"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def automod(
        self,
        interaction: discord.Interaction,
        feature: Literal["spam", "invite", "ngword", "mention"],
        state: Literal["on", "off"]
    ):

        data = self.load_automod()

        guild_id = str(interaction.guild.id)

        if guild_id not in data:
            data[guild_id] = {}

        data[guild_id][feature] = (state == "on")

        with open(self.automod_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        await interaction.response.send_message(
            f"✅ **{feature}** を **{state.upper()}** にしました。",
            ephemeral=True
        )



    # =========================
    # Punish User
    # =========================
    async def punish_user(
        self,
        guild,
        user,
        reason
    ):

        try:

            member = guild.get_member(user.id)

            if member:

                await member.timeout(
                    datetime.timedelta(minutes=10),
                    reason=reason
                )


                embed = discord.Embed(
                    title="🚨 Anti Raid処罰",
                    color=discord.Color.red(),
                    timestamp=datetime.datetime.now()
                )


                embed.add_field(
                    name="対象",
                    value=member.mention,
                    inline=False
                )


                embed.add_field(
                    name="理由",
                    value=reason,
                    inline=False
                )


                await self.send_log(
                    guild,
                    embed,
                    "monitor"
                )


        except Exception as e:

            print(
                "Punish Error:",
                e
            )


    # =========================
    # UNBAN検知
    # =========================
    @commands.Cog.listener()
    async def on_member_unban(
        self,
        guild,
        user
    ):

        await asyncio.sleep(1)


        executor="不明"
        reason="理由なし"


        async for entry in guild.audit_logs(
            limit=5,
            action=discord.AuditLogAction.unban
        ):

            if entry.target.id == user.id:

                executor=entry.user.mention
                reason=entry.reason or "理由なし"
                break



        embed=discord.Embed(
            title="🔓 BAN解除検知",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )


        embed.add_field(
            name="対象",
            value=f"{user}\n`{user.id}`",
            inline=False
        )


        embed.add_field(
            name="実行者",
            value=executor,
            inline=False
        )


        embed.add_field(
            name="理由",
            value=reason,
            inline=False
        )


        await self.send_log(
            guild,
            embed,
            "monitor"
        )
    # =========================
    # BAN検知
    # =========================

    @commands.Cog.listener()
    async def on_member_ban(
        self,
        guild,
        user
    ):

        await asyncio.sleep(1)

        executor = "不明"
        reason = "理由なし"


        async for entry in guild.audit_logs(
            limit=5,
            action=discord.AuditLogAction.ban
        ):

            if entry.target.id == user.id:

                executor = entry.user.mention
                reason = entry.reason or "理由なし"
                break



        embed = discord.Embed(
            title="🔨 BAN検知",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now()
        )


        embed.add_field(
            name="対象",
            value=f"{user}\n`{user.id}`",
            inline=False
        )


        embed.add_field(
            name="実行者",
            value=executor,
            inline=False
        )


        embed.add_field(
            name="理由",
            value=reason,
            inline=False
        )


        await self.send_log(
            guild,
            embed,
            "monitor"
        )


        # Anti Raid BAN

        now = datetime.datetime.now().timestamp()

        guild_id = guild.id


        if guild_id not in self.ban_count:
            self.ban_count[guild_id] = []


        self.ban_count[guild_id].append(now)


        self.ban_count[guild_id] = [
            x for x in self.ban_count[guild_id]
            if now - x < 10
        ]


        if len(self.ban_count[guild_id]) >= 5:

            entry_user = None


            async for entry in guild.audit_logs(
                limit=1,
                action=discord.AuditLogAction.ban
            ):

                entry_user = entry.user
                break


            if entry_user:

                await self.punish_user(
                    guild,
                    entry_user,
                    "短時間大量BANによるAnti Raid"
                )
    
    # =========================
    # Kick / Leave
    # =========================
    @commands.Cog.listener()
    async def on_member_remove(self, member):

        print(f"退出イベント発生: {member}")

        print("退出イベント発生")

        await asyncio.sleep(1)

        executor = "不明"
        reason = "理由なし"

        async for entry in member.guild.audit_logs(
            limit=5,
            action=discord.AuditLogAction.kick
        ):
            now = datetime.datetime.now(datetime.timezone.utc)

            async for entry in member.guild.audit_logs(
                limit=5,
                action=discord.AuditLogAction.kick
            ):
                if entry.target.id != member.id:
                    continue

                if (now - entry.created_at).total_seconds() > 5:
                    continue

                executor = entry.user.mention
                reason = entry.reason or "理由なし"
                break


        # Kickの場合

        if executor != "不明":

            embed = discord.Embed(
                title="👢 Kick検知",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.now()
            )

            embed.add_field(
                name="対象",
                value=f"{member}\n`{member.id}`",
                inline=False
            )

            embed.add_field(
                name="実行者",
                value=executor,
                inline=False
            )

            embed.add_field(
                name="理由",
                value=reason,
                inline=False
            )


            await self.send_log(
                member.guild,
                embed,
                "monitor"
            )

            return


        # 普通の退出

        embed = discord.Embed(
            description=f"**{member.display_name}** がサーバーを退出しました",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )

        embed.set_author(
            name=str(member),
            icon_url=member.display_avatar.url
        )

        embed.set_thumbnail(
            url=member.display_avatar.url
        )

        created = member.created_at
        now = discord.utils.utcnow()
        delta = now - created

        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        embed.add_field(
            name="📅 アカウント作成",
            value=(
                f"<t:{int(created.timestamp())}:F>\n"
                f"経過: **{days}日 {hours}時間 {minutes}分**"
            ),
            inline=False
        )

        if member.joined_at:
            joined = member.joined_at
            stay = now - joined

            d = stay.days
            h = stay.seconds // 3600
            m = (stay.seconds % 3600) // 60

            embed.add_field(
                name="📥 サーバー滞在期間",
                value=(
                    f"<t:{int(joined.timestamp())}:F>\n"
                    f"滞在: **{d}日 {h}時間 {m}分**"
                ),
                inline=False
            )

        embed.add_field(
            name="👥 退出後の人数",
            value=f"{member.guild.member_count}人",
            inline=False
        )

        if member.bot:
            embed.add_field(
                name="🤖 アカウント",
                value="Bot",
                inline=True
            )

        await self.send_log(
            member.guild,
            embed,
            "joinleave"
        )
    # =========================
    # Join
    # =========================
    @commands.Cog.listener()
    async def on_member_join(self, member):

        print(f"参加イベント発生: {member} ({member.id})")

        now = discord.utils.utcnow()

        created = member.created_at

        delta = now - created

        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60

        embed = discord.Embed(
            description=f"**{member.display_name}** がサーバーに参加しました",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )

        embed.set_author(
            name=str(member),
            icon_url=member.display_avatar.url
        )

        embed.set_thumbnail(
            url=member.display_avatar.url
        )

        embed.add_field(
            name="📅 アカウント作成",
            value=(
                f"<t:{int(created.timestamp())}:F>\n"
                f"経過: **{days}日 {hours}時間 {minutes}分**"
            ),
            inline=False
        )

        embed.add_field(
            name="👥 現在のサーバー人数",
            value=f"{member.guild.member_count}人",
            inline=False
        )

        if member.bot:
            embed.add_field(
                name="🤖 アカウント",
                value="Bot",
                inline=True
            )

        if days < 7:
            embed.add_field(
                name="⚠ 注意",
                value="作成から7日以内のアカウントです。",
                inline=False
            )

        await self.send_log(
            member.guild,
            embed,
            "joinleave"
        )

        try:

            # =========================
            # 未認証ロール付与
            # =========================
            if os.path.exists("verify.json"):

                with open(
                    "verify.json",
                    "r",
                    encoding="utf-8"
                ) as f:

                    verify_data = json.load(f)

                guild_verify = verify_data.get(
                    str(member.guild.id),
                    {}
                )

                role_id = guild_verify.get("unverified")

                if role_id:

                    role = member.guild.get_role(role_id)

                    if role:

                        await member.add_roles(
                            role,
                            reason="未認証ロール付与"
                        )

            # =========================
            # Welcome
            # =========================
            if os.path.exists(self.welcome_file):

                with open(
                    self.welcome_file,
                    "r",
                    encoding="utf-8"
                ) as f:

                    welcome_data = json.load(f)

                guild_data = welcome_data.get(
                    str(member.guild.id),
                    {}
                )

                channel_id = guild_data.get("channel")

                if channel_id:

                    channel = member.guild.get_channel(channel_id)

                    if channel:

                        welcome = discord.Embed(
                            title="🎉 新しいメンバー",
                            description=f"{member.mention} さんようこそ！",
                            color=discord.Color.green()
                        )

                        await channel.send(embed=welcome)

            # =========================
            # DM送信
            # =========================
            dm_embed = discord.Embed(
                title="🎉 サーバーへようこそ！",
                description=(
                    f"**{member.guild.name}** に参加していただきありがとうございます！\n\n"
                    "認証したあと\n"
                    "📜 ルールを確認して楽しく過ごしてください！"
                ),
                color=discord.Color.blue()
            )

            try:

                await member.send(embed=dm_embed)

            except discord.Forbidden:
                pass

        except Exception as e:

            print(
                "Welcome Error:",
                repr(e)
            )
    # =========================
    # Role Create
    # =========================
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):

        executor = "不明"

        try:
            now = datetime.datetime.now(datetime.timezone.utc)

            async for entry in role.guild.audit_logs(
                limit=5,
                action=discord.AuditLogAction.role_create
            ):

                if entry.target.id != role.id:
                    continue

                if (now - entry.created_at).total_seconds() > 5:
                    continue

                executor = entry.user.mention
                break

        except Exception as e:
            print("Role Create Audit Error:", e)

        embed = discord.Embed(
            title="🎭 ロール作成",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )

        embed.add_field(
            name="ロール",
            value=f"{role.name}\n`{role.id}`",
            inline=False
        )

        embed.add_field(
            name="実行者",
            value=executor,
            inline=False
        )

        await self.send_log(
            role.guild,
            embed,
            "monitor"
        )


    # =========================
    # Role Delete
    # =========================
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):

        executor = "不明"

        try:
            async for entry in role.guild.audit_logs(
                limit=5,
                action=discord.AuditLogAction.role_delete
            ):
                executor = entry.user.mention
                break

        except Exception as e:
            print("Role Delete Audit Error:", e)

        embed = discord.Embed(
            title="🗑 ロール削除",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now()
        )

        embed.add_field(
            name="ロール",
            value=f"{role.name}\n`{role.id}`",
            inline=False
        )

        embed.add_field(
            name="実行者",
            value=executor,
            inline=False
        )

        await self.send_log(
            role.guild,
            embed,
            "monitor"
        )

        now = datetime.datetime.now().timestamp()
        guild_id = role.guild.id

        if guild_id not in self.role_delete_count:
            self.role_delete_count[guild_id] = []

        self.role_delete_count[guild_id].append(now)

        self.role_delete_count[guild_id] = [
            x for x in self.role_delete_count[guild_id]
            if now - x < 10
        ]

        if len(self.role_delete_count[guild_id]) >= 5:

            embed = discord.Embed(
                title="🚨 ロール削除荒らし検知",
                description="10秒以内に5個以上ロール削除",
                color=discord.Color.red()
            )

            await self.send_log(
                role.guild,
                embed,
                "monitor"
            )

            self.role_delete_count[guild_id].clear()
    # =========================
    # Channel Create
    # =========================
    @commands.Cog.listener()
    async def on_guild_channel_create(
        self,
        channel
    ):

        executor = "不明"


        try:

            async for entry in channel.guild.audit_logs(
                limit=5,
                action=discord.AuditLogAction.channel_create
            ):

                if entry.target.id == channel.id:

                    executor = entry.user.mention
                    break


        except Exception as e:

            print(
                "Channel Create Audit Error:",
                e
            )


        embed = discord.Embed(
            title="📁 チャンネル作成",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )


        embed.add_field(
            name="チャンネル",
            value=f"{channel.name}\n`{channel.id}`",
            inline=False
        )


        embed.add_field(
            name="実行者",
            value=executor,
            inline=False
        )


        await self.send_log(
            channel.guild,
            embed,
            "monitor"
        )
    # =========================
    # Channel Delete
    # =========================
    @commands.Cog.listener()
    async def on_guild_channel_delete(
        self,
        channel
    ):

        executor = "不明"


        try:

            async for entry in channel.guild.audit_logs(
                limit=5,
                action=discord.AuditLogAction.channel_delete
            ):

                if entry.target.id == channel.id:

                    executor = entry.user.mention
                    break


        except Exception as e:

            print(
                "Channel Delete Audit Error:",
                e
            )


        embed = discord.Embed(
            title="🗑 チャンネル削除",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now()
        )


        embed.add_field(
            name="チャンネル",
            value=f"{channel.name}\n`{channel.id}`",
            inline=False
        )


        embed.add_field(
            name="実行者",
            value=executor,
            inline=False
        )


        await self.send_log(
            channel.guild,
            embed,
            "monitor"
        )
    # =========================
    # Anti Channel Delete Raid
    # =========================

        now = datetime.datetime.now().timestamp()


        guild_id = channel.guild.id


        if guild_id not in self.channel_delete_count:

            self.channel_delete_count[guild_id] = []


        self.channel_delete_count[guild_id].append(
            now
        )


        self.channel_delete_count[guild_id] = [
            x for x in self.channel_delete_count[guild_id]
            if now - x < 10
        ]


        if len(self.channel_delete_count[guild_id]) >= 3:


            embed = discord.Embed(
                title="🚨 チャンネル削除荒らし検知",
                description="10秒以内に3個以上削除されました",
                color=discord.Color.red()
            )


            await self.send_log(
                channel.guild,
                embed,
                "monitor"
            )
   

            self.channel_delete_count[guild_id].clear()
    # =========================
    # Channel Update
    # =========================
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):

        embed = discord.Embed(
            title="⚙️ チャンネル変更",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.now()
        )

        changed = False

        embed.add_field(
            name="チャンネル",
            value=after.mention,
            inline=False
        )

        if before.name != after.name:
            changed = True
            embed.add_field(
                name="名前変更",
                value=f"{before.name} → {after.name}",
                inline=False
            )

        if before.topic != after.topic:
            changed = True
            embed.add_field(
                name="トピック変更",
                value="変更あり",
                inline=False
            )
        if before.overwrites != after.overwrites:
            changed = True
            embed.add_field(
                name="権限変更",
                value="権限設定が変更されました",
                inline=False
            )

        if changed:
            await self.send_log(
                after.guild,
                embed,
                "monitor"
            )

    # =========================
    # Voice State Update
    # =========================
    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member,
        before,
        after
    ):

        if member.bot:
            return


        embed = None



        # VC参加
        if before.channel is None and after.channel is not None:


            embed = discord.Embed(
                title="🔊 VC参加",
                color=discord.Color.green(),
                timestamp=datetime.datetime.now()
            )


            embed.add_field(
                name="ユーザー",
                value=member.mention,
                inline=False
            )


            embed.add_field(
                name="参加先",
                value=after.channel.mention,
                inline=False
            )



        # VC退出
        elif before.channel is not None and after.channel is None:


            embed = discord.Embed(
                title="🔇 VC退出",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )


            embed.add_field(
                name="ユーザー",
                value=member.mention,
                inline=False
            )


            embed.add_field(
                name="退出元",
                value=before.channel.mention,
                inline=False
            )



        # VC移動
        elif (
            before.channel is not None
            and after.channel is not None
            and before.channel.id != after.channel.id
        ):


            embed = discord.Embed(
                title="🔀 VC移動",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.now()
            )


            embed.add_field(
                name="ユーザー",
                value=member.mention,
                inline=False
            )


            embed.add_field(
                name="移動前",
                value=before.channel.mention,
                inline=False
            )


            embed.add_field(
                name="移動後",
                value=after.channel.mention,
                inline=False
            )



        if embed:


            await self.send_log(
                member.guild,
                embed,
                "monitor"
            ) 
    # =========================
    # Guild Update
    # =========================
    @commands.Cog.listener()
    async def on_guild_update(
        self,
        before,
        after
    ):

        changes = []


        if before.name != after.name:

            changes.append(
                f"名前変更\n`{before.name}` → `{after.name}`"
            )


        if before.icon != after.icon:

            changes.append(
                "サーバーアイコン変更"
            )


        if before.description != after.description:

            changes.append(
                "サーバー説明変更"
            )


        if not changes:
            return



        embed = discord.Embed(
            title="⚙️ サーバー設定変更",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.now()
        )


        embed.add_field(
            name="変更内容",
            value="\n\n".join(changes),
            inline=False
        )


        await self.send_log(
            after,
            embed,
            "monitor"
        ) 
    # =========================
    # Invite Create
    # =========================
    @commands.Cog.listener()
    async def on_invite_create(
        self,
        invite
    ):


        embed = discord.Embed(
            title="🔗 招待作成",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )


        embed.add_field(
            name="作成者",
            value=invite.inviter.mention if invite.inviter else "不明",
            inline=False
        )


        embed.add_field(
            name="チャンネル",
            value=invite.channel.mention if invite.channel else "不明",
            inline=False
        )


        embed.add_field(
            name="コード",
            value=f"`{invite.code}`",
            inline=False
        )


        if invite.max_age:

            embed.add_field(
                name="期限",
                value=f"{invite.max_age}秒",
                inline=False
            )

        else:

            embed.add_field(
                name="期限",
                value="無期限",
                inline=False
            )


        await self.send_log(
            invite.guild,
            embed,
            "monitor"
        )  
    # =========================
    # Invite Delete
    # =========================
    @commands.Cog.listener()
    async def on_invite_delete(
        self,
        invite
    ):


        embed = discord.Embed(
            title="🗑 招待削除",
            color=discord.Color.red(),
            timestamp=datetime.datetime.now()
        )


        embed.add_field(
            name="コード",
            value=f"`{invite.code}`",
            inline=False
        )


        if invite.channel:

            embed.add_field(
                name="チャンネル",
                value=invite.channel.mention,
                inline=False
            )


        await self.send_log(
            invite.guild,
            embed,
            "monitor"
        )
    # =========================
    # Role Update
    # =========================
    @commands.Cog.listener()
    async def on_guild_role_update(
        self,
        before,
        after
    ):

        changes = []


        if before.name != after.name:

            changes.append(
                f"名前変更\n`{before.name}` → `{after.name}`"
            )


        if before.permissions != after.permissions:

            changes.append(
                "権限変更"
            )


        if before.color != after.color:

            changes.append(
                "色変更"
            )


        if not changes:
            return



        embed = discord.Embed(
            title="🎭 ロール変更",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.now()
        )


        embed.add_field(
            name="ロール",
            value=f"{after.name}\n`{after.id}`",
            inline=False
        )


        embed.add_field(
            name="変更内容",
            value="\n".join(changes),
            inline=False
        )


        await self.send_log(
            after.guild,
            embed,
            "monitor"
        )
    
    async def cog_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ このコマンドを使う権限がありません。",
                ephemeral=True
            )
    
    @commands.Cog.listener()
    async def on_message(
        self,
        message
    ):

        if message.author.bot:
            return

        if not message.guild:
            return

        data = {}

        if os.path.exists("xembed.json"):

            with open(
                "xembed.json",
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

        if not data.get(
            str(message.guild.id),
            False
        ):
            return

        match = re.search(
            r"https?://(?:x|twitter)\.com/\S+",
            message.content
        )

        if not match:
            return

        url = match.group()
        fx_url = (
            url
            .replace(
                "https://x.com/",
                "https://fxtwitter.com/"
            )
            .replace(
                "https://twitter.com/",
                "https://fxtwitter.com/"
            )
        )

        await message.channel.send(fx_url)


# =========================
# Setup
# =========================

async def setup(bot):

    await bot.add_cog(
        Events(bot)
    )