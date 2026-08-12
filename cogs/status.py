import discord
from discord.ext import commands
from discord import app_commands
import json
import os


class StatusView(discord.ui.View):

    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    async def update_status(
        self,
        interaction: discord.Interaction,
        status_text: str,
        emoji: str,
        color: discord.Color
    ):

        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        allowed_role_ids = self.cog.status_roles.get(
            guild_id,
            []
        )

        if not allowed_role_ids:

            await interaction.response.send_message(
                "❌ 対応状況を操作できるロールが設定されていません。",
                ephemeral=True
            )

            return

        user_role_ids = {
            role.id
            for role in interaction.user.roles
        }

        has_permission = any(
            role_id in user_role_ids
            for role_id in allowed_role_ids
        )

        if not has_permission:

            await interaction.response.send_message(
                "❌ 対応状況を操作できるロールを持っていません。",
                ephemeral=True
            )

            return

        required_role = interaction.guild.get_role(
            int(required_role_id)
        )

        if required_role is None:

            await interaction.response.send_message(
                "❌ 設定されているロールが存在しません。",
                ephemeral=True
            )

            return

        if required_role not in interaction.user.roles:

            await interaction.response.send_message(
                f"❌ {required_role.mention} ロールを持っている人だけ操作できます。",
                ephemeral=True
            )

            return

        # =========================
        # サーバーのデータがなければ作成
        # =========================

        if guild_id not in self.cog.statuses:
            self.cog.statuses[guild_id] = {}

        # =========================
        # ユーザーの状態を更新
        # =========================

        self.cog.statuses[guild_id][user_id] = {
            "name": interaction.user.display_name,
            "mention": interaction.user.mention,
            "status": status_text,
            "emoji": emoji,
            "color": color.value
        }

        # =========================
        # JSON保存
        # =========================

        self.cog.save_statuses()

        # =========================
        # 最新のEmbedを作成
        # =========================

        embed = self.cog.create_status_embed(guild_id)

        # =========================
        # 設置済みパネルを更新
        # =========================

        if guild_id in self.cog.panels:

            panel = self.cog.panels[guild_id]

            try:

                channel = self.cog.bot.get_channel(
                    panel["channel_id"]
                )

                if channel is not None:

                    message = await channel.fetch_message(
                        panel["message_id"]
                    )

                    await message.edit(
                        embed=embed,
                        view=StatusView(self.cog)
                    )

            except discord.NotFound:

                print(
                    f"対応状況パネルが見つかりません: {guild_id}"
                )

            except discord.Forbidden:

                print(
                    f"対応状況パネルへのアクセス権限がありません: {guild_id}"
                )

            except Exception as e:

                print(
                    f"対応状況パネル更新失敗: {guild_id} {e}"
                )

        # =========================
        # ボタンを押した本人の画面も更新
        # =========================

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    # =========================
    # 対応可能
    # =========================

    @discord.ui.button(
        label="対応可能",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="status_available"
    )
    async def available(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await self.update_status(
            interaction,
            "対応可能です。",
            "✅",
            discord.Color.green()
        )

    # =========================
    # 対応遅延
    # =========================

    @discord.ui.button(
        label="対応遅延",
        emoji="⚠️",
        style=discord.ButtonStyle.primary,
        custom_id="status_delayed"
    )
    async def delayed(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await self.update_status(
            interaction,
            "対応が遅延しています。",
            "⚠️",
            discord.Color.gold()
        )

    # =========================
    # 対応不可
    # =========================

    @discord.ui.button(
        label="対応不可",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="status_unavailable"
    )
    async def unavailable(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await self.update_status(
            interaction,
            "現在対応できません。",
            "❌",
            discord.Color.red()
        )
    
    # =========================
    # 状態解除
    # =========================

    @discord.ui.button(
        label="状態を解除",
        emoji="🗑️",
        style=discord.ButtonStyle.secondary,
        custom_id="status_clear"
    )
    async def clear_status(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        # =========================
        # 登録されているか確認
        # =========================

        if guild_id not in self.cog.statuses:

            await interaction.response.send_message(
                "ℹ️ 現在、対応状況は登録されていません。",
                ephemeral=True
            )
            return

        if user_id not in self.cog.statuses[guild_id]:

            await interaction.response.send_message(
                "ℹ️ あなたの対応状況は登録されていません。",
                ephemeral=True
            )
            return

        # =========================
        # 状態を削除
        # =========================

        del self.cog.statuses[guild_id][user_id]

        # =========================
        # サーバーに誰もいなければ削除
        # =========================

        if not self.cog.statuses[guild_id]:

            del self.cog.statuses[guild_id]

        # =========================
        # JSON保存
        # =========================

        self.cog.save_statuses()

        # =========================
        # Embed更新
        # =========================

        embed = self.cog.create_status_embed(guild_id)

        # =========================
        # パネル更新
        # =========================

        if guild_id in self.cog.panels:

            panel = self.cog.panels[guild_id]

            try:

                channel = self.cog.bot.get_channel(
                    panel["channel_id"]
                )

                if channel is not None:

                    message = await channel.fetch_message(
                        panel["message_id"]
                    )

                    await message.edit(
                        embed=embed,
                        view=StatusView(self.cog)
                    )

            except discord.NotFound:

                print(
                    f"対応状況パネルが見つかりません: {guild_id}"
                )

            except discord.Forbidden:

                print(
                    f"対応状況パネルへのアクセス権限がありません: {guild_id}"
                )

            except Exception as e:

                print(
                    f"対応状況パネル更新失敗: {guild_id} {e}"
                )

        # =========================
        # 押した本人の画面を更新
        # =========================

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )




class StatusRoleSelect(discord.ui.RoleSelect):

    def __init__(self, cog):

        super().__init__(
            placeholder="対応状況を操作できるロールを選択",
            min_values=1,
            max_values=10,
            custom_id="status_role_select"
        )

        self.cog = cog

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        if not interaction.user.guild_permissions.manage_guild:

            await interaction.response.send_message(
                "❌ サーバー管理権限が必要です。",
                ephemeral=True
            )

            return

        roles = self.values

        guild_id = str(interaction.guild.id)

        self.cog.status_roles[guild_id] = [
            role.id
            for role in roles
        ]

        self.cog.save_status_roles()

        role_text = "\n".join(
            f"・{role.mention}"
            for role in roles
        )

        await interaction.response.send_message(
            f"✅ 対応状況を操作できるロールを設定しました。\n\n"
            f"{role_text}",
            ephemeral=True
        )




class StatusRoleView(discord.ui.View):

    def __init__(self, cog):

        super().__init__(timeout=60)

        self.add_item(
            StatusRoleSelect(cog)
        )        
    
    


class Status(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.status_file = "status.json"
        self.statuses = self.load_statuses()

        self.panel_file = "status_panel.json"
        self.panels = self.load_panels()

        self.role_file = "status_role.json"
        self.status_roles = self.load_status_roles()

        bot.add_view(StatusView(self))

    def load_statuses(self):

        if not os.path.exists(self.status_file):
            return {}

        with open(
            self.status_file,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)


    def save_statuses(self):

        with open(
            self.status_file,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                self.statuses,
                f,
                ensure_ascii=False,
                indent=4
            )

    def load_panels(self):

        if not os.path.exists(self.panel_file):
            return {}

        try:

            with open(
                self.panel_file,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        except json.JSONDecodeError:

            print("status_panel.json が空または壊れています。")

            return {}


    def save_panels(self):

        with open(
            self.panel_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.panels,
                f,
                ensure_ascii=False,
                indent=4
            )
    
    def load_status_roles(self):

        if not os.path.exists(self.role_file):
            return {}

        try:

            with open(
                self.role_file,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        except json.JSONDecodeError:

            print(
                "status_role.json が空または壊れています。"
            )

            return {}


    def save_status_roles(self):

        with open(
            self.role_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.status_roles,
                f,
                ensure_ascii=False,
                indent=4
            )
    
    @app_commands.command(
        name="statusrole",
        description="対応状況を操作できるロールを設定します"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def statusrole(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.send_message(
            "対応状況を操作できるロールを選択してください。",
            view=StatusRoleView(self),
            ephemeral=True
        )

    # =========================
    # /status
    # =========================

    @app_commands.command(
        name="status",
        description="対応状況パネルを設置します"
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def status(
        self,
        interaction: discord.Interaction
    ):

        guild_id = str(interaction.guild.id)

        embed = discord.Embed(
            title="対応状況",
            description="ボタンを押して現在の対応状況を設定してください。",
            color=discord.Color.blurple()
        )

        message = await interaction.channel.send(
            embed=embed,
            view=StatusView(self)
        )

        # パネル情報を保存
        self.panels[guild_id] = {
            "channel_id": interaction.channel.id,
            "message_id": message.id
        }

        self.save_panels()

        await interaction.response.send_message(
            "✅ 対応状況パネルを設置しました。",
            ephemeral=True
        )
    
    async def restore_panels(self):

        for guild_id, panel in self.panels.items():

            try:
                channel = self.bot.get_channel(
                    panel["channel_id"]
                )

                if channel is None:
                    continue

                message = await channel.fetch_message(
                    panel["message_id"]
                )

                embed = self.create_status_embed(guild_id)

                await message.edit(
                    embed=embed,
                    view=StatusView(self)
                )

                print(
                    f"対応状況パネル復元: {guild_id}"
                )

            except discord.NotFound:

                print(
                    f"対応状況パネルが見つかりません: {guild_id}"
                )

            except discord.Forbidden:

                print(
                    f"対応状況パネルへのアクセス権限がありません: {guild_id}"
                )

            except Exception as e:

                print(
                    f"対応状況パネル復元失敗: {guild_id} {e}"
                )

    def create_status_embed(self, guild_id):

        guild_id = str(guild_id)

        users = self.statuses.get(guild_id, {})

        # =========================
        # 誰も設定していない場合
        # =========================

        if not users:

            return discord.Embed(
                title="📊 対応状況",
                description="現在、対応状況を設定しているユーザーはいません。",
                color=discord.Color.blurple()
            )

        available_users = []
        delayed_users = []
        unavailable_users = []

        # =========================
        # 状態ごとに分類
        # =========================

        for user in users.values():

            if user["emoji"] == "✅":

                available_users.append(
                    f'{user["mention"]}'
                )

            elif user["emoji"] == "⚠️":

                delayed_users.append(
                    f'{user["mention"]}'
                )

            elif user["emoji"] == "❌":

                unavailable_users.append(
                    f'{user["mention"]}'
                )

        # =========================
        # Embed本文
        # =========================

        description = ""

        # 対応可能
        description += "🟢 **対応可能**\n"

        if available_users:

            description += "\n".join(
                f"・{user}"
                for user in available_users
            )

        else:

            description += "・なし"

        description += "\n\n"

        # 対応遅延
        description += "🟡 **対応遅延**\n"

        if delayed_users:

            description += "\n".join(
                f"・{user}"
                for user in delayed_users
            )

        else:

            description += "・なし"

        description += "\n\n"

        # 対応不可
        description += "🔴 **対応不可**\n"

        if unavailable_users:

            description += "\n".join(
                f"・{user}"
                for user in unavailable_users
            )

        else:

            description += "・なし"

        # =========================
        # 集計
        # =========================

        total = len(users)

        available_count = len(available_users)
        delayed_count = len(delayed_users)
        unavailable_count = len(unavailable_users)

        description += (
            "\n\n"
            "━━━━━━━━━━━━━━\n"
            f"👥 **登録人数:** {total}人\n"
            f"🟢 **対応可能:** {available_count}人\n"
            f"🟡 **対応遅延:** {delayed_count}人\n"
            f"🔴 **対応不可:** {unavailable_count}人"
        )

        # =========================
        # Embed
        # =========================

        return discord.Embed(
            title="📊 対応状況",
            description=description,
            color=discord.Color.blurple()
        )


async def setup(bot):

    cog = Status(bot)

    await bot.add_cog(cog)

    await cog.restore_panels()