import asyncio
import html
import io
import json
import os

import discord
from discord.ext import commands
from discord import app_commands


# =========================================================
# 設定
# =========================================================

CONFIG_FILE = "ticket.json"


# =========================================================
# Config 読み込み
# =========================================================

def load_config():

    defaults = {

        # =========================
        # 通常Ticket
        # =========================

        "normal_category": None,
        "normal_log_channel": None,
        "normal_staff_role": None,

        # =========================
        # 販売Ticket
        # =========================

        "sale_category": None,
        "sale_log_channel": None,
        "sale_staff_role": None,

        # =========================
        # 共通
        # =========================

        "ticket_number": 0,

        "panel_title": "🎫 サポートセンター",

        "panel_description": (
            "サポートが必要な場合は\n"
            "下のボタンを押してください。"
        ),

        "panel_image": None,

        "first_message": "スタッフがお伺いします。"
    }

    # ファイルがない場合
    if not os.path.exists(CONFIG_FILE):

        save_config(defaults)

        return defaults

    try:

        with open(
            CONFIG_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

    except (
        json.JSONDecodeError,
        OSError
    ):

        data = {}

    # 足りない設定を追加
    for key, value in defaults.items():

        data.setdefault(
            key,
            value
        )

    return data


# =========================================================
# Config 保存
# =========================================================

def save_config(data):

    with open(
        CONFIG_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


config = load_config()


# =========================================================
# パネルEmbed
# =========================================================

def create_panel_embed():

    embed = discord.Embed(
        title=config["panel_title"],
        description=config["panel_description"],
        color=discord.Color.blurple(),
        timestamp=discord.utils.utcnow()
    )

    if config["panel_image"]:

        embed.set_image(
            url=config["panel_image"]
        )

    embed.set_footer(
        text="Ticket System"
    )

    return embed


# =========================================================
# Ticket判定
# =========================================================

def get_ticket_data(channel):

    if not isinstance(
        channel,
        discord.TextChannel
    ):
        return None

    topic = channel.topic

    if not topic:
        return None

    # 新形式
    try:

        data = json.loads(topic)

        if isinstance(data, dict):

            if data.get("type") in (
                "normal",
                "sale"
            ):

                return data

    except (
        json.JSONDecodeError,
        TypeError
    ):
        pass

    # 旧形式
    try:

        owner_id = int(topic)

        return {
            "type": "normal",
            "owner_id": owner_id
        }

    except (
        TypeError,
        ValueError
    ):
        return None


# =========================================================
# Ticket所有者取得
# =========================================================

def get_ticket_users(channel):

    data = get_ticket_data(channel)

    if not data:
        return []

    # =========================
    # 通常Ticket
    # =========================

    if data.get("type") == "normal":

        owner_id = data.get(
            "owner_id"
        )

        if owner_id:

            return [
                int(owner_id)
            ]

    # =========================
    # 販売Ticket
    # =========================

    if data.get("type") == "sale":

        users = []

        buyer_id = data.get(
            "buyer_id"
        )

        seller_id = data.get(
            "seller_id"
        )

        if buyer_id:
            users.append(
                int(buyer_id)
            )

        if seller_id:
            users.append(
                int(seller_id)
            )

        return users

    return []


# =========================================================
# Ticket種類取得
# =========================================================

def get_ticket_type(channel):

    data = get_ticket_data(channel)

    if not data:
        return None

    return data.get("type")


# =========================================================
# Transcript
# =========================================================

async def create_transcript(
    channel: discord.TextChannel
):

    html_data = f"""
<html>

<head>

<meta charset="utf-8">

<title>
{html.escape(channel.name)}
</title>

<style>

body {{
    background:#36393f;
    color:white;
    font-family:Arial;
    padding:20px;
}}

.message {{
    margin-bottom:20px;
    padding:10px;
    background:#2f3136;
    border-radius:8px;
}}

.author {{
    font-weight:bold;
    color:#57F287;
}}

.time {{
    font-size:12px;
    color:gray;
}}

.content {{
    margin-top:5px;
    white-space:pre-wrap;
}}

img {{
    max-width:600px;
    border-radius:8px;
}}

</style>

</head>

<body>

<h2>
{html.escape(channel.guild.name)}
</h2>

<h3>
{html.escape(channel.name)}
</h3>

"""

    # =====================================================
    # メッセージ取得
    # =====================================================

    async for message in channel.history(
        limit=None,
        oldest_first=True
    ):

        content = html.escape(
            message.content
        )

        html_data += f"""

<div class="message">

<div class="author">
{html.escape(str(message.author))}
</div>

<div class="time">
{message.created_at.strftime("%Y/%m/%d %H:%M:%S")}
</div>

<div class="content">
{content}
</div>

"""

        # =================================================
        # 添付ファイル
        # =================================================

        if message.attachments:

            html_data += (
                "<br><b>Attachments</b><br>"
            )

            for attachment in message.attachments:

                content_type = (
                    attachment.content_type
                    or ""
                )

                # -----------------------------
                # 画像
                # -----------------------------

                if content_type.startswith(
                    "image"
                ):

                    html_data += (
                        f'<img src="{html.escape(attachment.url)}" '
                        f'style="max-width:600px;'
                        f'border-radius:8px;"><br>'
                    )

                # -----------------------------
                # 動画
                # -----------------------------

                elif content_type.startswith(
                    "video"
                ):

                    html_data += (
                        f'<a href="{html.escape(attachment.url)}">'
                        f'🎥 '
                        f'{html.escape(attachment.filename)}'
                        f'</a><br>'
                    )

                # -----------------------------
                # その他
                # -----------------------------

                else:

                    html_data += (
                        f'<a href="{html.escape(attachment.url)}">'
                        f'📄 '
                        f'{html.escape(attachment.filename)}'
                        f'</a><br>'
                    )

        # =================================================
        # Embed
        # =================================================

        if message.embeds:

            html_data += (
                "<br><b>Embed</b><br>"
            )

            for embed in message.embeds:

                if embed.title:

                    html_data += (
                        f"<b>"
                        f"{html.escape(embed.title)}"
                        f"</b><br>"
                    )

                if embed.description:

                    html_data += (
                        html.escape(
                            embed.description
                        )
                        + "<br>"
                    )

        html_data += """

</div>

"""

    html_data += """

</body>

</html>

"""

    return discord.File(
        io.BytesIO(
            html_data.encode("utf-8")
        ),
        filename=f"{channel.name}.html"
    )


# =========================================================
# Ticket閉じる確認View
# =========================================================

class CloseConfirmView(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=60
        )

    # =====================================================
    # はい
    # =====================================================

    @discord.ui.button(
        label="✅ はい",
        style=discord.ButtonStyle.red
    )
    async def yes(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.defer(
            ephemeral=True
        )

        channel = interaction.channel

        # Transcript
        transcript = await create_transcript(
            channel
        )

        # Ticket情報
        ticket_data = get_ticket_data(
            channel
        )

        ticket_type = get_ticket_type(
            channel
        )

        # =================================================
        # ログ先
        # =================================================

        log_channel_id = None

        if ticket_type == "sale":

            log_channel_id = config[
                "sale_log_channel"
            ]

        elif ticket_type == "normal":

            log_channel_id = config[
                "normal_log_channel"
            ]

        # =================================================
        # ログ送信
        # =================================================

        if log_channel_id:

            log = interaction.guild.get_channel(
                log_channel_id
            )

            if log:

                embed = discord.Embed(
                    title="📁 Ticket Closed",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )

                embed.add_field(
                    name="Channel",
                    value=channel.name,
                    inline=False
                )

                embed.add_field(
                    name="Closed By",
                    value=interaction.user.mention,
                    inline=False
                )

                # =========================================
                # 通常Ticket
                # =========================================

                if (
                    ticket_data
                    and ticket_type == "normal"
                ):

                    owner_id = ticket_data.get(
                        "owner_id"
                    )

                    if owner_id:

                        embed.add_field(
                            name="Owner",
                            value=f"<@{owner_id}>",
                            inline=False
                        )

                               # =========================================
                # 販売Ticket
                # =========================================

                elif (
                    ticket_data
                    and ticket_type == "sale"
                ):

                    buyer_id = ticket_data.get(
                        "buyer_id"
                    )

                    seller_id = ticket_data.get(
                        "seller_id"
                    )

                    order_id = ticket_data.get(
                        "order_id"
                    )

                    # -----------------------------
                    # 購入者
                    # -----------------------------

                    if buyer_id:

                        embed.add_field(
                            name="👤 購入者",
                            value=f"<@{buyer_id}>",
                            inline=True
                        )

                    # -----------------------------
                    # 販売者
                    # -----------------------------

                    if seller_id:

                        embed.add_field(
                            name="🏪 販売者",
                            value=f"<@{seller_id}>",
                            inline=True
                        )

                    # -----------------------------
                    # 注文ID
                    # -----------------------------

                    if order_id:

                        embed.add_field(
                            name="🆔 注文ID",
                            value=f"`{order_id}`",
                            inline=False
                        )

                    # -----------------------------
                    # 販売Ticketであることを明示
                    # -----------------------------

                    embed.title = "🛒 販売Ticket Closed"

                    embed.color = discord.Color.orange()

                await log.send(
                    embed=embed,
                    file=transcript
                )

        # =================================================
        # 少し待って削除
        # =================================================

        await asyncio.sleep(1)

        await channel.delete()

    # =====================================================
    # いいえ
    # =====================================================

    @discord.ui.button(
        label="❌ いいえ",
        style=discord.ButtonStyle.gray
    )
    async def no(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            content="キャンセルしました。",
            view=None
        )

# =========================================================
# Ticket閉じるボタン
# =========================================================

class CloseView(discord.ui.View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="🔒 チケットを閉じる",
        style=discord.ButtonStyle.red,
        custom_id="ticket_close"
    )
    async def close(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        channel = interaction.channel

        # =====================================================
        # Ticket情報取得
        # =====================================================

        ticket_data = get_ticket_data(
            channel
        )

        if not ticket_data:

            await interaction.response.send_message(
                "❌ このチャンネルはTicketではありません。",
                ephemeral=True
            )

            return

        # =====================================================
        # Ticket参加者
        # =====================================================

        allowed_users = get_ticket_users(
            channel
        )

        # =====================================================
        # スタッフ / 管理者判定
        # =====================================================

        is_staff = (
            interaction.user.guild_permissions.manage_channels
        )

        # =====================================================
        # 権限確認
        # =====================================================

        if (
            interaction.user.id not in allowed_users
            and not is_staff
        ):

            await interaction.response.send_message(
                "❌ チケット作成者・購入者・販売者・スタッフのみ閉じられます。",
                ephemeral=True
            )

            return

        # =====================================================
        # 確認
        # =====================================================

        await interaction.response.send_message(
            "⚠️ 本当にこのTicketを閉じますか？",
            view=CloseConfirmView(),
            ephemeral=True
        )


# =========================================================
# Ticketパネル
# =========================================================

class TicketPanel(discord.ui.View):

    def __init__(self, bot):
        super().__init__(timeout=None)

        self.bot = bot

    # =====================================================
    # 通常Ticket
    # =====================================================

    @discord.ui.button(
        label="🎫 通常Ticket",
        style=discord.ButtonStyle.green,
        custom_id="ticket_create_normal"
    )
    async def create_normal(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "❌ サーバー内でのみ使用できます。",
                ephemeral=True
            )
            return

        # =================================================
        # カテゴリ取得
        # =================================================

        category = None

        if config["normal_category"]:
            category = guild.get_channel(
                config["normal_category"]
            )

        if not isinstance(
            category,
            discord.CategoryChannel
        ):
            category = discord.utils.get(
                guild.categories,
                name="🎫 Tickets"
            )

        # =================================================
        # カテゴリ自動作成
        # =================================================

        if category is None:

            category = await guild.create_category(
                "🎫 Tickets"
            )

            config["normal_category"] = category.id
            save_config(config)

        # =================================================
        # 既存Ticket確認
        # =================================================

        for channel in category.text_channels:

            ticket_data = get_ticket_data(channel)

            if not ticket_data:
                continue

            if ticket_data.get("type") != "normal":
                continue

            if ticket_data.get("owner_id") == interaction.user.id:

                await interaction.response.send_message(
                    "❌ 既に通常Ticketがあります。",
                    ephemeral=True
                )
                return

        # =================================================
        # Ticket番号
        # =================================================

        config["ticket_number"] += 1
        save_config(config)

        number = str(
            config["ticket_number"]
        ).zfill(4)

        # =================================================
        # 権限
        # =================================================

        overwrites = {

            guild.default_role:
                discord.PermissionOverwrite(
                    view_channel=False
                ),

            interaction.user:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    attach_files=True,
                    embed_links=True,
                    read_message_history=True
                )
        }

        # =================================================
        # スタッフ
        # =================================================

        if config["normal_staff_role"]:

            role = guild.get_role(
                config["normal_staff_role"]
            )

            if role:

                overwrites[role] = (
                    discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        attach_files=True,
                        embed_links=True,
                        read_message_history=True
                    )
                )

        # =================================================
        # Bot
        # =================================================

        bot_member = guild.get_member(
            self.bot.user.id
        )

        if bot_member:

            overwrites[bot_member] = (
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    manage_channels=True,
                    manage_messages=True,
                    read_message_history=True
                )
            )

        # =================================================
        # Topic
        # =================================================

        topic = json.dumps(
            {
                "type": "normal",
                "owner_id": interaction.user.id
            },
            ensure_ascii=False
        )

        # =================================================
        # 作成
        # =================================================

        try:

            ticket = await guild.create_text_channel(
                name=f"ticket-{number}",
                category=category,
                overwrites=overwrites,
                topic=topic
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ Botにチャンネル作成権限がありません。",
                ephemeral=True
            )
            return

        except discord.HTTPException:

            await interaction.response.send_message(
                "❌ Ticketの作成に失敗しました。",
                ephemeral=True
            )
            return

        # =================================================
        # Embed
        # =================================================

        embed = discord.Embed(
            title=f"🎫 Ticket #{number}",
            description=(
                f"{interaction.user.mention}\n\n"
                f"{config['first_message']}\n\n"
                "終了するときは下のボタンを押してください。"
            ),
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="👤 作成者",
            value=interaction.user.mention,
            inline=True
        )

        embed.add_field(
            name="🎫 Ticket番号",
            value=f"#{number}",
            inline=True
        )

        content = config["first_message"]

        if config["normal_staff_role"]:

            content = (
                f"<@&{config['normal_staff_role']}>\n"
                f"{config['first_message']}"
            )

        await ticket.send(
            content=content,
            embed=embed,
            view=CloseView()
        )

        # =================================================
        # ログ
        # =================================================

        if config["normal_log_channel"]:

            log = guild.get_channel(
                config["normal_log_channel"]
            )

            if log:

                log_embed = discord.Embed(
                    title="📂 Ticket Created",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )

                log_embed.add_field(
                    name="🎫 チケット",
                    value=ticket.mention,
                    inline=False
                )

                log_embed.add_field(
                    name="👤 作成者",
                    value=interaction.user.mention,
                    inline=False
                )

                await log.send(
                    embed=log_embed
                )

        await interaction.response.send_message(
            f"✅ {ticket.mention} を作成しました。",
            ephemeral=True
        )

    # =====================================================
    # 販売Ticket
    # =====================================================

    @discord.ui.button(
        label="🛒 販売Ticket",
        style=discord.ButtonStyle.blurple,
        custom_id="ticket_create_sale"
    )
    async def create_sale(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_message(
            "🛒 販売Ticketはショップの商品購入時に自動作成されます。\n\n"
            "商品を購入すると、購入者・販売者・商品・価格・注文IDが設定された販売Ticketが自動で作成されます。",
            ephemeral=True
        )


# =========================================================
# Ticket Cog
# =========================================================

class Ticket(commands.Cog):

    def __init__(
        self,
        bot: commands.Bot
    ):

        self.bot = bot

        # ================================================
        # 永続View
        # ================================================

        bot.add_view(
            TicketPanel(bot)
        )

        bot.add_view(
            CloseView()
        )

    # =====================================================
    # /ticket
    # =====================================================

    @app_commands.command(
        name="ticket",
        description="Ticketパネルを設置します"
    )
    @app_commands.default_permissions(
        administrator=True
    )
    async def ticket(
        self,
        interaction: discord.Interaction,

        title: str,
        description: str,

        category: discord.CategoryChannel,
        log_channel: discord.TextChannel,

        staff_role: discord.Role = None,

        first_message: str = "スタッフがお伺いします。",

        image: discord.Attachment = None,

        # =================================================
        # 販売Ticket設定
        # =================================================

        sale_category: discord.CategoryChannel = None,

        sale_log_channel: discord.TextChannel = None,

        sale_staff_role: discord.Role = None
    ):

        # =================================================
        # 通常Ticket設定
        # =================================================

        config["normal_category"] = category.id

        config["normal_log_channel"] = (
            log_channel.id
        )

        if staff_role:

            config["normal_staff_role"] = (
                staff_role.id
            )

        else:

            config["normal_staff_role"] = None

        # =================================================
        # 販売Ticket設定
        # =================================================

        if sale_category:

            config["sale_category"] = (
                sale_category.id
            )

        else:

            config["sale_category"] = None

        if sale_log_channel:

            config["sale_log_channel"] = (
                sale_log_channel.id
            )

        else:

            config["sale_log_channel"] = None

        if sale_staff_role:

            config["sale_staff_role"] = (
                sale_staff_role.id
            )

        else:

            config["sale_staff_role"] = None

        # =================================================
        # パネル設定
        # =================================================

        config["panel_title"] = title

        config["panel_description"] = description

        config["first_message"] = first_message

        if image:

            config["panel_image"] = image.url

        else:

            config["panel_image"] = None

        # =================================================
        # 保存
        # =================================================

        save_config(config)

        # =================================================
        # パネルEmbed
        # =================================================

        embed = create_panel_embed()

        await interaction.channel.send(
            embed=embed,
            view=TicketPanel(self.bot)
        )

        # =================================================
        # 完了メッセージ
        # =================================================

        sale_status = (
            "✅ 設定済み"
            if sale_log_channel
            else "⚪ 未設定"
        )

        await interaction.response.send_message(
            (
                "✅ チケットパネルを設置しました。\n\n"
                f"🎫 通常Ticketログ：{log_channel.mention}\n"
                f"🛒 販売Ticketログ：{sale_status}"
            ),
            ephemeral=True
        )

    # =====================================================
    # /ticketadd
    # =====================================================

    @app_commands.command(
        name="ticketadd",
        description="チケットにユーザーを追加します"
    )
    @app_commands.default_permissions(
        manage_channels=True
    )
    async def ticketadd(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        # =================================================
        # Ticket確認
        # =================================================

        ticket_data = get_ticket_data(
            interaction.channel
        )

        if not ticket_data:

            await interaction.response.send_message(
                "❌ このコマンドはTicketでのみ使用できます。",
                ephemeral=True
            )

            return

        # =================================================
        # 権限追加
        # =================================================

        await interaction.channel.set_permissions(
            member,
            view_channel=True,
            send_messages=True,
            attach_files=True,
            embed_links=True,
            read_message_history=True
        )

        await interaction.response.send_message(
            f"✅ {member.mention} をTicketに追加しました。",
            ephemeral=True
        )

    # =====================================================
    # /ticketremove
    # =====================================================

    @app_commands.command(
        name="ticketremove",
        description="チケットからユーザーを削除します"
    )
    @app_commands.default_permissions(
        manage_channels=True
    )
    async def ticketremove(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        # =================================================
        # Ticket確認
        # =================================================

        ticket_data = get_ticket_data(
            interaction.channel
        )

        if not ticket_data:

            await interaction.response.send_message(
                "❌ このコマンドはTicketでのみ使用できます。",
                ephemeral=True
            )

            return

        # =================================================
        # 権限削除
        # =================================================

        await interaction.channel.set_permissions(
            member,
            overwrite=None
        )

        await interaction.response.send_message(
            f"✅ {member.mention} をTicketから削除しました。",
            ephemeral=True
        )

    # =====================================================
    # /ticketrename
    # =====================================================

    @app_commands.command(
        name="ticketrename",
        description="チケット名を変更します"
    )
    @app_commands.default_permissions(
        manage_channels=True
    )
    async def ticketrename(
        self,
        interaction: discord.Interaction,
        name: str
    ):

        # =================================================
        # Ticket確認
        # =================================================

        ticket_data = get_ticket_data(
            interaction.channel
        )

        if not ticket_data:

            await interaction.response.send_message(
                "❌ このコマンドはTicketでのみ使用できます。",
                ephemeral=True
            )

            return

        # =================================================
        # 名前変更
        # =================================================

        try:

            await interaction.channel.edit(
                name=name
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ Botにチャンネル名を変更する権限がありません。",
                ephemeral=True
            )

            return

        except discord.HTTPException:

            await interaction.response.send_message(
                "❌ チャンネル名の変更に失敗しました。",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            f"✅ チケット名を **{name}** に変更しました。",
            ephemeral=True
        )

    # =====================================================
    # /ticketclaim
    # =====================================================

    @app_commands.command(
        name="ticketclaim",
        description="チケットを担当します"
    )
    @app_commands.default_permissions(
        manage_channels=True
    )
    async def ticketclaim(
        self,
        interaction: discord.Interaction
    ):

        # =================================================
        # Ticket確認
        # =================================================

        ticket_data = get_ticket_data(
            interaction.channel
        )

        if not ticket_data:

            await interaction.response.send_message(
                "❌ このコマンドはTicketでのみ使用できます。",
                ephemeral=True
            )

            return

        # =================================================
        # 担当Embed
        # =================================================

        embed = discord.Embed(
            title="👤 チケット担当",
            description=(
                f"{interaction.user.mention} が担当しました。"
            ),
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="担当者",
            value=interaction.user.mention,
            inline=True
        )

        await interaction.channel.send(
            embed=embed
        )

        await interaction.response.send_message(
            "✅ このTicketを担当しました。",
            ephemeral=True
        )



# =========================================================
# 販売Ticket作成
# =========================================================

async def create_sale_ticket(
    bot,
    guild,
    buyer,
    seller,
    order_id,
    product_name,
    price
):

    # =====================================================
    # カテゴリ
    # =====================================================

    category = None

    if config["sale_category"]:

        category = guild.get_channel(
            config["sale_category"]
        )

    # =====================================================
    # カテゴリが存在しない場合
    # =====================================================

    if not isinstance(
        category,
        discord.CategoryChannel
    ):

        category = discord.utils.get(
            guild.categories,
            name="🛒 Sales"
        )

    # =====================================================
    # カテゴリ自動作成
    # =====================================================

    if category is None:

        category = await guild.create_category(
            "🛒 Sales"
        )

        config["sale_category"] = (
            category.id
        )

        save_config(
            config
        )

    # =====================================================
    # Ticket番号
    # =====================================================

    config["ticket_number"] += 1

    save_config(
        config
    )

    number = str(
        config["ticket_number"]
    ).zfill(4)

    # =====================================================
    # 権限
    # =====================================================

    overwrites = {

        guild.default_role:
            discord.PermissionOverwrite(
                view_channel=False
            ),

        buyer:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
                read_message_history=True
            ),

        seller:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
                read_message_history=True
            )
    }

    # =====================================================
    # 販売スタッフ
    # =====================================================

    if config["sale_staff_role"]:

        role = guild.get_role(
            config["sale_staff_role"]
        )

        if role:

            overwrites[role] = (
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    attach_files=True,
                    embed_links=True,
                    read_message_history=True
                )
            )

    # =====================================================
    # Bot
    # =====================================================

    bot_member = guild.get_member(
        bot.user.id
    )

    if bot_member:

        overwrites[bot_member] = (
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
                read_message_history=True,
                manage_channels=True,
                manage_messages=True
            )
        )

    # =====================================================
    # Topic
    # =====================================================

    topic = json.dumps(
        {
            "type": "sale",
            "buyer_id": buyer.id,
            "seller_id": seller.id,
            "order_id": str(order_id)
        },
        ensure_ascii=False
    )

    # =====================================================
    # Ticket作成
    # =====================================================

    try:

        ticket = await guild.create_text_channel(

            name=f"sale-{number}",

            category=category,

            overwrites=overwrites,

            topic=topic
        )

    except discord.Forbidden:

        return None

    except discord.HTTPException:

        return None

    # =====================================================
    # Embed
    # =====================================================

    embed = discord.Embed(
        title=f"🛒 販売Ticket #{number}",
        description=(
            "商品購入用のTicketです。\n\n"
            f"購入者：{buyer.mention}\n"
            f"販売者：{seller.mention}\n\n"
            "このTicket内で購入者と販売者が"
            "やり取りできます。\n\n"
            "終了するときは下のボタンを押してください。"
        ),
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name="📦 商品",
        value=str(product_name),
        inline=False
    )

    embed.add_field(
        name="💰 価格",
        value=f"¥{price:,}",
        inline=True
    )

    embed.add_field(
        name="🆔 注文ID",
        value=f"`{order_id}`",
        inline=True
    )

    embed.add_field(
        name="👤 購入者",
        value=buyer.mention,
        inline=True
    )

    embed.add_field(
        name="🏪 販売者",
        value=seller.mention,
        inline=True
    )

    # =====================================================
    # メッセージ
    # =====================================================

    await ticket.send(
        content=(
            f"{buyer.mention} {seller.mention}"
        ),
        embed=embed,
        view=CloseView()
    )

    # =====================================================
    # ログ
    # =====================================================

    if config["sale_log_channel"]:

        log = guild.get_channel(
            config["sale_log_channel"]
        )

        if log:

            log_embed = discord.Embed(
                title="🛒 販売Ticket Created",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )

            log_embed.add_field(
                name="Ticket",
                value=ticket.mention,
                inline=False
            )

            log_embed.add_field(
                name="購入者",
                value=buyer.mention,
                inline=True
            )

            log_embed.add_field(
                name="販売者",
                value=seller.mention,
                inline=True
            )

            log_embed.add_field(
                name="商品",
                value=str(product_name),
                inline=False
            )

            log_embed.add_field(
                name="価格",
                value=f"¥{price:,}",
                inline=True
            )

            log_embed.add_field(
                name="注文ID",
                value=f"`{order_id}`",
                inline=True
            )

            await log.send(
                embed=log_embed
            )

    return ticket


# =========================================================
# Cog Setup
# =========================================================

async def setup(
    bot: commands.Bot
):

    await bot.add_cog(
        Ticket(bot)
    )