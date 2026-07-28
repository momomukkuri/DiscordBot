import discord
from discord.ext import commands
from discord import app_commands

import asyncio
import datetime
import json
import os

XEMBED_FILE = "xembed.json"


def load_xembed():

    if not os.path.exists(XEMBED_FILE):
        return {}

    with open(
        XEMBED_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def save_xembed(data):

    with open(
        XEMBED_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )

class PollEndView(discord.ui.View):

    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.ended = False

    @discord.ui.button(
        label="🔒 投票終了",
        style=discord.ButtonStyle.danger
    )
    async def end_poll(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if (
            interaction.user.id != self.author_id
            and not interaction.user.guild_permissions.administrator
        ):
            await interaction.response.send_message(
                "❌ この投票を終了できません。",
                ephemeral=True
            )
            return

        message = interaction.message

        emojis = ["🇦", "🇧", "🇨", "🇩", "🇪"]

        results = []

        for reaction in message.reactions:
            if reaction.emoji in emojis:
                results.append((reaction.emoji, reaction.count - 1))

        embed = message.embeds[0]

        result = discord.Embed(
            title="📊 投票終了",
            description=embed.description,
            color=discord.Color.green()
        )

        winner = max(v for _, v in results) if results else 0

        for i, (emoji, votes) in enumerate(results):

            choice = embed.fields[i].value

            mark = " 🏆" if votes == winner and winner > 0 else ""

            result.add_field(
                name=f"{emoji} {choice}",
                value=f"{votes}票{mark}",
                inline=False
            )

        button.disabled = True

        await interaction.response.edit_message(
            embed=result,
            view=self
        )
class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.warning_file = "warnings.json"
        self.history_file = "history.json"


    # =========================
    # Log送信
    # =========================
    async def send_log(self, guild, embed):

        if not os.path.exists("logs.json"):
            return

        with open(
            "logs.json",
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)


        guild_data = data.get(
            str(guild.id),
            {}
        )


        channel_id = guild_data.get(
            "moderation"
        )


        if not channel_id:
            return


        channel = guild.get_channel(
            channel_id
        )


        if channel:
            await channel.send(
                embed=embed
            )

    def add_history(self, user_id, action, reason, moderator):

        if os.path.exists(self.history_file):
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        user_id = str(user_id)

        if user_id not in data:
            data[user_id] = []

        data[user_id].append({
            "action": action,
            "reason": reason,
            "moderator": moderator,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        })

        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


    # =========================
    # Timeout
    # =========================
    @app_commands.command(
        name="timeout",
        description="ユーザーをタイムアウトします"
    )
    @app_commands.describe(
        member="対象ユーザー",
        minutes="時間(分)",
        reason="理由"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        minutes: int,
        reason: str = "理由なし"
    ):

        await interaction.response.defer()

        try:
            await member.timeout(
                datetime.timedelta(minutes=minutes),
                reason=reason
            )

            embed = discord.Embed(
                title="🔇 Timeout",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.now()
            )

            embed.add_field(
                name="対象",
                value=f"{member.mention}\n`{member.id}`",
                inline=False
            )

            embed.add_field(
                name="時間",
                value=f"{minutes}分",
                inline=False
            )

            embed.add_field(
                name="理由",
                value=reason,
                inline=False
            )

            embed.set_footer(
                text=f"実行者: {interaction.user}"
            )

            await interaction.followup.send(embed=embed)

            await self.send_log(
                interaction.guild,
                embed
            )

            self.add_history(
                member.id,
                "Timeout",
                reason,
                str(interaction.user)
            )

        except Exception as e:
            print("Timeout Error:", e)

            await interaction.followup.send(
                "❌ Timeout失敗",
                ephemeral=True
            )




    # =========================
    # Untimeout
    # =========================
    @app_commands.command(
        name="untimeout",
        description="Timeoutを解除します"
    )
    @app_commands.checks.has_permissions(
        moderate_members=True
    )
    async def untimeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        await interaction.response.defer()

        try:

            await member.timeout(None)

            embed = discord.Embed(
                title="🔊 Timeout解除",
                color=discord.Color.green()
            )

            embed.add_field(
                name="対象",
                value=member.mention,
                inline=False
            )

            embed.set_footer(
                text=f"実行者: {interaction.user}"
            )

            await interaction.followup.send(
                embed=embed
            )

            await self.send_log(
                interaction.guild,
                embed
            )

            self.add_history(
                member.id,
                "Untimeout",
                "理由なし",
                str(interaction.user)
            )

        except Exception as e:

            print("Untimeout Error:", e)

            await interaction.followup.send(
                "❌ Timeout解除に失敗しました。",
                ephemeral=True
            )



    # =========================
    # Kick
    # =========================
    @app_commands.command(
        name="kick",
        description="ユーザーをKickします"
    )
    @app_commands.checks.has_permissions(
        kick_members=True
    )
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "理由なし"
    ):

        await interaction.response.defer()


        try:

            await member.kick(
                reason=reason
            )


            embed = discord.Embed(
                title="👢 Kick",
                color=discord.Color.red()
            )


            embed.add_field(
                name="対象",
                value=f"{member}\n`{member.id}`",
                inline=False
            )


            embed.add_field(
                name="理由",
                value=reason,
                inline=False
            )


            embed.set_footer(
                text=f"実行者: {interaction.user}"
            )


            await interaction.followup.send(
                embed=embed
            )


            await self.send_log(
                interaction.guild,
                embed
            )

            self.add_history(
                member.id,
                "Kick",
                reason,
                str(interaction.user)
            )


        except Exception as e:

            print(
                "Kick Error:",
                e
            )



    # =========================
    # BAN
    # =========================
    @app_commands.command(
        name="ban",
        description="ユーザーをBANします"
    )
    @app_commands.checks.has_permissions(
        ban_members=True
    )
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str="理由なし"
    ):

        await interaction.response.defer()


        try:

            await member.ban(
                reason=reason
            )


            embed = discord.Embed(
                title="🔨 BAN",
                color=discord.Color.dark_red()
            )


            embed.add_field(
                name="対象",
                value=f"{member}\n`{member.id}`",
                inline=False
            )


            embed.add_field(
                name="理由",
                value=reason,
                inline=False
            )


            embed.set_footer(
                text=f"実行者: {interaction.user}"
            )


            await interaction.followup.send(
                embed=embed
            )


            await self.send_log(
                interaction.guild,
                embed
            )

            self.add_history(
                member.id,
                "BAN",
                reason,
                str(interaction.user)
            )


        except Exception as e:

            print(
                "BAN Error:",
                e
            )
    @app_commands.command(
        name="banlist",
        description="BANされているユーザー一覧を表示します"
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def banlist(
        self,
        interaction: discord.Interaction
    ):

        bans = [entry async for entry in interaction.guild.bans()]

        if not bans:
            await interaction.response.send_message(
                "✅ BANされているユーザーはいません。",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🔨 BANリスト",
            color=discord.Color.red()
        )

        description = ""

        for i, entry in enumerate(bans, start=1):
            user = entry.user
            reason = entry.reason or "理由なし"

            description += (
                f"**{i}.** {user} (`{user.id}`)\n"
                f"理由: {reason}\n\n"
            )

            # Embedの文字数制限対策
            if len(description) > 3500:
                break

        embed.description = description

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
    # =========================
    # Unban
    # =========================
    @app_commands.command(
        name="unban",
        description="BAN解除します"
    )
    @app_commands.checks.has_permissions(
        ban_members=True
    )
    async def unban(
        self,
        interaction: discord.Interaction,
        user_id: str,
        reason: str="理由なし"
    ):

        await interaction.response.defer()

        try:

            user_id = user_id.replace(
                "<@",
                ""
            ).replace(
                ">",
                ""
            ).replace(
                "!",
                ""
            )


            await interaction.guild.unban(
                discord.Object(
                    id=int(user_id)
                ),
                reason=reason
            )


            embed = discord.Embed(
                title="🔓 BAN解除",
                color=discord.Color.green()
            )


            embed.add_field(
                name="ID",
                value=user_id,
                inline=False
            )

            embed.add_field(
                name="理由",
                value=reason,
                inline=False
            )

            embed.set_footer(
                text=f"実行者: {interaction.user}"
            )


            await interaction.followup.send(
                embed=embed
            )


            await self.send_log(
                interaction.guild,
                embed
            )

            self.add_history(
                int(user_id),
                "Unban",
                reason,
                str(interaction.user)
            )


        except Exception as e:

            print(
                "Unban Error:",
                e
            )


    # =========================
    # SoftBAN
    # =========================
    @app_commands.command(
        name="softban",
        description="SoftBANします"
    )
    @app_commands.checks.has_permissions(
        ban_members=True
    )
    async def softban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason:str="理由なし"
    ):

        await interaction.response.defer()


        try:

            await interaction.guild.ban(
                member,
                delete_message_days=7,
                reason=reason
            )


            await interaction.guild.unban(
                discord.Object(
                    id=member.id
                ),
                reason="SoftBAN解除"
            )


            embed = discord.Embed(
                title="🧹 SoftBAN",
                color=discord.Color.orange()
            )


            embed.add_field(
                name="対象",
                value=member.mention,
                inline=False
            )

            embed.add_field(
                name="削除",
                value="7日分のメッセージ",
                inline=False
            )

            embed.add_field(
                name="理由",
                value=reason,
                inline=False
            )


            await interaction.followup.send(
                embed=embed
            )


            await self.send_log(
                interaction.guild,
                embed
            )

            self.add_history(
                member.id,
                "SoftBAN",
                reason,
                str(interaction.user)
            )


        except Exception as e:

            print(
                "SoftBAN Error:",
                e
            )



    # =========================
    # Warn
    # =========================
    @app_commands.command(
        name="warn",
        description="警告を追加します"
    )
    @app_commands.checks.has_permissions(
        moderate_members=True
    )
    async def warn(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason:str="理由なし"
    ):

        await interaction.response.defer()


        data={}


        if os.path.exists(
            self.warning_file
        ):

            with open(
                self.warning_file,
                "r",
                encoding="utf-8"
            ) as f:
                data=json.load(f)


        uid=str(member.id)


        if uid not in data:
            data[uid]=[]


        data[uid].append(
            {
                "reason":reason,
                "by":str(interaction.user),
                "date":str(datetime.datetime.now())
            }
        )


        with open(
            self.warning_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=4
            )


        embed=discord.Embed(
            title="⚠️ Warn",
            color=discord.Color.gold()
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


        await interaction.followup.send(
            embed=embed
        )


        await self.send_log(
            interaction.guild,
            embed
        )

        self.add_history(
            member.id,
            "Warn",
            reason,
            str(interaction.user)
        )



    # =========================
    # Warnings
    # =========================
    @app_commands.command(
        name="warnings",
        description="警告履歴を見る"
    )
    @app_commands.checks.has_permissions(
        moderate_members=True
    )
    async def warnings(
        self,
        interaction: discord.Interaction,
        member:discord.Member
    ):

        if not os.path.exists(
            self.warning_file
        ):

            await interaction.response.send_message(
                "履歴なし"
            )
            return


        with open(
            self.warning_file,
            "r",
            encoding="utf-8"
        ) as f:

            data=json.load(f)


        warns=data.get(
            str(member.id),
            []
        )


        embed=discord.Embed(
            title="⚠️ 警告履歴",
            color=discord.Color.gold()
        )


        if warns:

            text=""

            for i,w in enumerate(
                warns,
                1
            ):

                text+=(
                    f"#{i}\n"
                    f"{w['reason']}\n"
                    f"{w['by']}\n\n"
                )

            embed.description=text[:4000]

        else:

            embed.description="履歴なし"


        await interaction.response.send_message(
            embed=embed
        )
    
    # =========================
    # History
    # =========================
    @app_commands.command(
        name="history",
        description="ユーザーの処分履歴を表示します"
    )
    @app_commands.checks.has_permissions(
        moderate_members=True
    )
    async def history(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        if not os.path.exists(self.history_file):
            await interaction.response.send_message(
                "履歴はありません。",
                ephemeral=True
            )
            return

        with open(
            self.history_file,
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

        history = data.get(str(member.id), [])

        if not history:
            await interaction.response.send_message(
                f"{member.mention} の履歴はありません。",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"📜 {member} の処分履歴",
            color=discord.Color.orange()
        )

        text = ""

        for i, h in enumerate(history, 1):
            text += (
                f"**#{i} {h['action']}**\n"
                f"理由: {h['reason']}\n"
                f"実行者: {h['moderator']}\n"
                f"日時: {h['date']}\n\n"
            )

        embed.description = text[:4000]

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    # =========================
    # Nuke
    # =========================
    @app_commands.command(
        name="nuke",
        description="チャンネル内のメッセージを全削除します"
    )
    @app_commands.default_permissions(
        administrator=True
    )
    async def nuke(
        self,
        interaction: discord.Interaction
    ):

        channel = interaction.channel

        await interaction.response.send_message(
            "💣 チャンネルを初期化しています...",
            ephemeral=True
        )

        # チャンネルを複製
        new_channel = await channel.clone(
            reason=f"Nuke実行者: {interaction.user}"
        )

        # 元の位置へ移動
        await new_channel.edit(
            position=channel.position
        )

        # 元チャンネル削除
        await channel.delete(
            reason=f"Nuke実行者: {interaction.user}"
        )

        embed = discord.Embed(
            title="💣 Nuke Complete",
            description=(
                f"👤 実行者: {interaction.user.mention}\n"
                "🧹 うおｗ　nukeしたンゴ"
            ),
            color=discord.Color.red()
        )

        embed.set_image(
            url="https://i.pinimg.com/originals/36/55/45/36554586166d20f8fd62daefda51fd24.gif"
        )

        await new_channel.send(embed=embed)

        # 管理ログ
        embed = discord.Embed(
            title="💣 チャンネル初期化",
            color=discord.Color.red()
        )

        embed.add_field(
            name="実行者",
            value=f"{interaction.user.mention}\n`{interaction.user.id}`",
            inline=False
        )

        embed.add_field(
            name="チャンネル",
            value=new_channel.mention,
            inline=False
        )

        await self.send_log(
            new_channel.guild,
            embed,
        )



    # =========================
    # Clear
    # =========================
    @app_commands.command(
        name="clear",
        description="メッセージ削除"
    )
    @app_commands.checks.has_permissions(
        manage_messages=True
    )
    async def clear(
        self,
        interaction:discord.Interaction,
        amount:int
    ):

        await interaction.response.defer(
            ephemeral=True
        )


        deleted=await interaction.channel.purge(
            limit=amount
        )


        embed=discord.Embed(
            title="🧹 Clear",
            description=f"{len(deleted)}件削除",
            color=discord.Color.blue()
        )


        await interaction.followup.send(
            embed=embed
        )


        await self.send_log(
            interaction.guild,
            embed
        )
    # =========================
    # Lockdown
    # =========================
    @app_commands.command(
        name="lockdown",
        description="チャンネルをロックします"
    )
    @app_commands.checks.has_permissions(
        manage_channels=True
    )
    async def lockdown(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.defer()

        channel = interaction.channel

        await channel.set_permissions(
            interaction.guild.default_role,
            send_messages=False
        )


        embed = discord.Embed(
            title="🔒 Lockdown",
            description=f"{channel.mention}をロックしました",
            color=discord.Color.red()
        )

        embed.set_footer(
            text=f"実行者: {interaction.user}"
        )


        await interaction.followup.send(
            embed=embed
        )

        await self.send_log(
            interaction.guild,
            embed
        )



    # =========================
    # Unlock
    # =========================
    @app_commands.command(
        name="unlock",
        description="ロック解除"
    )
    @app_commands.checks.has_permissions(
        manage_channels=True
    )
    async def unlock(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.defer()

        channel=interaction.channel


        await channel.set_permissions(
            interaction.guild.default_role,
            send_messages=None
        )


        embed=discord.Embed(
            title="🔓 Unlock",
            description=f"{channel.mention}を解除しました",
            color=discord.Color.green()
        )


        await interaction.followup.send(
            embed=embed
        )


        await self.send_log(
            interaction.guild,
            embed
        )



    # =========================
    # Server Lock
    # =========================
    @app_commands.command(
        name="serverlock",
        description="サーバー全体をロック"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def serverlock(
        self,
        interaction:discord.Interaction
    ):

        await interaction.response.defer()


        count=0

        for channel in interaction.guild.text_channels:

            await channel.set_permissions(
                interaction.guild.default_role,
                send_messages=False
            )

            count+=1


        embed=discord.Embed(
            title="🔒 Server Lock",
            description=f"{count}チャンネルをロック",
            color=discord.Color.red()
        )


        await interaction.followup.send(
            embed=embed
        )


        await self.send_log(
            interaction.guild,
            embed
        )



    # =========================
    # Server Unlock
    # =========================
    @app_commands.command(
        name="serverunlock",
        description="サーバーロック解除"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def serverunlock(
        self,
        interaction:discord.Interaction
    ):

        await interaction.response.defer()


        count=0


        for channel in interaction.guild.text_channels:

            await channel.set_permissions(
                interaction.guild.default_role,
                send_messages=None
            )

            count+=1


        embed=discord.Embed(
            title="🔓 Server Unlock",
            description=f"{count}チャンネル解除",
            color=discord.Color.green()
        )


        await interaction.followup.send(
            embed=embed
        )


        await self.send_log(
            interaction.guild,
            embed
        )



    # =========================
    # Announce
    # =========================
    @app_commands.command(
        name="announce",
        description="告知送信"
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def announce(
        self,
        interaction:discord.Interaction,
        channel:discord.TextChannel,
        message:str
    ):

        await interaction.response.defer(
            ephemeral=True
        )


        embed=discord.Embed(
            title="📢 お知らせ",
            description=message,
            color=discord.Color.blue()
        )


        embed.set_footer(
            text=f"投稿者:{interaction.user}"
        )


        await channel.send(
            embed=embed
        )


        await interaction.followup.send(
            "✅送信しました",
            ephemeral=True
        )


        await self.send_log(
            interaction.guild,
            embed
        )



    # =========================
    # Add Role
    # =========================
    @app_commands.command(
        name="addrole",
        description="ロール付与"
    )
    @app_commands.checks.has_permissions(
        manage_roles=True
    )
    async def addrole(
        self,
        interaction:discord.Interaction,
        member:discord.Member,
        role:discord.Role
    ):


        await member.add_roles(
            role
        )


        embed=discord.Embed(
            title="✅ ロール付与",
            color=discord.Color.green()
        )


        embed.add_field(
            name="対象",
            value=member.mention
        )

        embed.add_field(
            name="ロール",
            value=role.mention
        )


        await interaction.response.send_message(
            embed=embed
        )


        await self.send_log(
            interaction.guild,
            embed
        )



    # =========================
    # Remove Role
    # =========================
    @app_commands.command(
        name="removerole",
        description="ロール削除"
    )
    @app_commands.checks.has_permissions(
        manage_roles=True
    )
    async def removerole(
        self,
        interaction:discord.Interaction,
        member:discord.Member,
        role:discord.Role
    ):

        await member.remove_roles(
            role
        )


        embed=discord.Embed(
            title="🗑 ロール削除",
            color=discord.Color.red()
        )


        embed.add_field(
            name="対象",
            value=member.mention
        )


        embed.add_field(
            name="ロール",
            value=role.mention
        )


        await interaction.response.send_message(
            embed=embed
        )


        await self.send_log(
            interaction.guild,
            embed
        )
    @app_commands.command(
        name="poll",
        description="投票を作成します"
    )
    
    async def poll(
        self,
        interaction: discord.Interaction,
        質問: str,
        時間: app_commands.Range[int, 1, 10080],
        選択肢1: str,
        選択肢2: str,
        選択肢3: str = None,
        選択肢4: str = None,
        選択肢5: str = None
    ):

        choices = [
            選択肢1,
            選択肢2,
            選択肢3,
            選択肢4,
            選択肢5
        ]

        emojis = ["🇦", "🇧", "🇨", "🇩", "🇪"]

        embed = discord.Embed(
            title="📊 投票",
            description=質問,
            color=discord.Color.blurple()
        )

        for emoji, choice in zip(emojis, choices):
            if choice:
                embed.add_field(
                    name=emoji,
                    value=choice,
                    inline=False
                )

        embed.set_footer(
            text=f"⏰ {時間}分後に締め切られます"
        )

        await interaction.response.defer(ephemeral=True)

        view = PollEndView(interaction.user.id)

        msg = await interaction.channel.send(
            embed=embed,
            view=view
        )
        for emoji, choice in zip(emojis, choices):
            if choice:
                await msg.add_reaction(emoji)
        await interaction.followup.send(
            "✅ 投票を作成しました。",
            ephemeral=True
        )
        asyncio.create_task(
            self.finish_poll(
                interaction.channel,
                msg,
                質問,
                choices,
                emojis,
                view,
                時間
            )
        )

    async def finish_poll(
        self,
        channel,
        msg,
        質問,
        choices,
        emojis,
        view,
        時間
    ):
        await asyncio.sleep(時間 * 60)

        if view.ended:
            return

        view.ended = True

        msg = await channel.fetch_message(msg.id)

        results = []

        valid_choices = [c for c in choices if c]

        for emoji in emojis[:len(valid_choices)]:
            reaction = discord.utils.get(
                msg.reactions,
                emoji=emoji
            )

            votes = reaction.count - 1 if reaction else 0
            results.append(votes)

        winner = max(results) if results else 0

        result_embed = discord.Embed(
            title="📊 投票終了",
            description=質問,
            color=discord.Color.green()
        )

        for emoji, choice, vote in zip(
            emojis,
            valid_choices,
            results
        ):
            mark = " 🏆" if vote == winner and winner > 0 else ""

            result_embed.add_field(
                name=f"{emoji} {choice}",
                value=f"**{vote}票**{mark}",
                inline=False
            )

        await channel.send(
            embed=result_embed
        )
    @app_commands.command(
        name="prohibited",
        description="禁止ワードを管理します"
    )
    @app_commands.describe(
        action="add / remove / list / clear",
        word="禁止ワード"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def prohibited(
        self,
        interaction: discord.Interaction,
        action: str,
        word: str = None
    ):
        if not os.path.exists("prohibited.json"):
            with open("prohibited.json", "w", encoding="utf-8") as f:
                json.dump({}, f)

        with open("prohibited.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        guild_id = str(interaction.guild.id)

        if guild_id not in data:
            data[guild_id] = []

        if action == "add":

            if not word:
                await interaction.response.send_message(
                    "ワードを入力してください。",
                    ephemeral=True
                )
                return

            if word in data[guild_id]:
                await interaction.response.send_message(
                    "既に登録されています。",
                    ephemeral=True
                )
                return

            data[guild_id].append(word)

            with open("prohibited.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            await interaction.response.send_message(
                f"✅ `{word}` を追加しました。"
            )

        elif action == "remove":

            if word not in data[guild_id]:
                await interaction.response.send_message(
                    "そのワードはありません。",
                    ephemeral=True
                )
                return

            data[guild_id].remove(word)

            with open("prohibited.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            await interaction.response.send_message(
                f"🗑 `{word}` を削除しました。"
            )

        elif action == "list":

            if not data[guild_id]:
                await interaction.response.send_message("禁止ワードはありません。")
                return

            text = "\n".join(
                f"{i+1}. {w}"
                for i, w in enumerate(data[guild_id])
            )

            await interaction.response.send_message(
                f"## 禁止ワード一覧\n{text}"
            )

        elif action == "clear":

            data[guild_id] = []

            with open("prohibited.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            await interaction.response.send_message(
                "🗑 全て削除しました。"
            )

        else:
            await interaction.response.send_message(
                "actionは add / remove / list / clear を指定してください。",
                ephemeral=True
            )
    @app_commands.command(
        name="指定メッセージ削除",
        description="入力した内容と一致するメッセージをすべて削除します"
    )
    @app_commands.describe(content="削除するメッセージの内容")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def delete_message(
        self,
        interaction: discord.Interaction,
        content: str
    ):

        await interaction.response.defer(ephemeral=True)

        deleted = 0

        async for message in interaction.channel.history(limit=1000):

            if message.content == content:
                await message.delete()
                deleted += 1

        if deleted == 0:
            await interaction.followup.send(
                "❌ 一致するメッセージは見つかりませんでした。",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                f"✅ {deleted}件のメッセージを削除しました。",
                ephemeral=True
            )

    @app_commands.command(
        name="xembed",
        description="X埋め込み機能のON/OFF"
    )
    @app_commands.describe(
        mode="on または off"
    )
    @app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def xembed(
        self,
        interaction: discord.Interaction,
        mode: str
    ):

        mode = mode.lower()

        if mode not in ["on", "off"]:

            await interaction.response.send_message(
                "使い方: `/xembed on` または `/xembed off`",
                ephemeral=True
            )
            return

        data = load_xembed()

        data[str(interaction.guild.id)] = (
            mode == "on"
        )

        save_xembed(data)

        await interaction.response.send_message(
            f"✅ X埋め込みを **{mode.upper()}** にしました。",
            ephemeral=True
        )


# =========================
# Setup
# =========================
async def setup(bot):

    await bot.add_cog(
        Moderation(bot)
    )