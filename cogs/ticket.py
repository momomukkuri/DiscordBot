import asyncio
import html
import io
import json
import os

import discord
from discord.ext import commands
from discord import app_commands

CONFIG_FILE = "ticket.json"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {
            "category": None,
            "log_channel": None,

            "ticket_number": 0,

            "panel_title": "🎫 サポートセンター",

            "panel_description":
                "サポートが必要な場合は\n"
                "下のボタンを押してください。",

            "panel_image": None,

            "mention_role": None,

            "first_message":
                "スタッフがお伺いします。"
        }

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    defaults = {

        "category": None,
        "log_channel": None,

        "ticket_number": 0,

        "panel_title": "🎫 サポートセンター",

        "panel_description":
            "サポートが必要な場合は\n"
            "下のボタンを押してください。",

        "panel_image": None,

        "mention_role": None,

        "first_message":
            "スタッフがお伺いします。"

    }

    for key, value in defaults.items():
        data.setdefault(key, value)

    return data


def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


config = load_config()


def create_panel_embed():

    embed = discord.Embed(
        title=config["panel_title"],
        description=config["panel_description"],
        color=discord.Color.blurple(),
        timestamp=discord.utils.utcnow()
    )

    if config["panel_image"]:
        embed.set_image(url=config["panel_image"])

    embed.set_footer(
        text="Ticket System"
    )

    return embed


async def create_transcript(channel: discord.TextChannel):

    html_data = f"""
<html>
<head>
<meta charset="utf-8">
<title>{channel.name}</title>

<style>

body{{
background:#36393f;
color:white;
font-family:Arial;
padding:20px;
}}

.message{{
margin-bottom:20px;
padding:10px;
background:#2f3136;
border-radius:8px;
}}

.author{{
font-weight:bold;
color:#57F287;
}}

.time{{
font-size:12px;
color:gray;
}}

.content{{
margin-top:5px;
white-space:pre-wrap;
}}

</style>
</head>
<body>

<h2>{channel.guild.name}</h2>
<h3>{channel.name}</h3>

"""

    async for message in channel.history(limit=None, oldest_first=True):

        content = html.escape(message.content)

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

        if message.attachments:

            html_data += "<br><b>Attachments</b><br>"

            for attachment in message.attachments:

                # 画像なら表示
                if (
                    attachment.content_type
                    and attachment.content_type.startswith("image")
                ):
                    html_data += (
                        f'<img src="{attachment.url}" '
                        f'style="max-width:600px;border-radius:8px;"><br>'
                    )

                # 動画ならリンク
                elif (
                    attachment.content_type
                    and attachment.content_type.startswith("video")
                ):
                    html_data += (
                        f'<a href="{attachment.url}">'
                        f'🎥 {attachment.filename}'
                        '</a><br>'
                    )

                # その他
                else:
                    html_data += (
                        f'<a href="{attachment.url}">'
                        f'📄 {attachment.filename}'
                        '</a><br>'
                    )

        if message.embeds:

            html_data += "<br><b>Embed</b><br>"

            for embed in message.embeds:

                if embed.title:
                    html_data += (
                        f"<b>{html.escape(embed.title)}</b><br>"
                    )

                if embed.description:
                    html_data += (
                        html.escape(embed.description)
                        + "<br>"
                    )

        html_data += """
        </div>
        </div>
        """

    html_data += "</body></html>"

    return discord.File(
        io.BytesIO(html_data.encode("utf-8")),
        filename=f"{channel.name}.html"
    )

class CloseConfirmView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(
        label="✅ はい",
        style=discord.ButtonStyle.red
    )
    async def yes(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.defer(ephemeral=True)

        channel = interaction.channel

        transcript = await create_transcript(channel)

        if config["log_channel"]:

            log = interaction.guild.get_channel(
                config["log_channel"]
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

                try:
                    member = interaction.guild.get_member(int(channel.topic))

                    owner = member.mention if member else f"ID: {channel.topic}"
                except (TypeError, ValueError):
                    owner = "不明"

                embed.add_field(
                    name="Owner",
                    value=owner,
                    inline=False
                )

                await log.send(
                    embed=embed,
                    file=transcript
                )

        await asyncio.sleep(1)

        await channel.delete()

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


class CloseView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

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

        try:
            owner_id = int(interaction.channel.topic)
        except (TypeError, ValueError):
            await interaction.response.send_message(
                "❌ このチャンネルはチケットではありません。",
                ephemeral=True
            )
            return

        if (
            interaction.user.id != owner_id
            and not interaction.user.guild_permissions.manage_channels
        ):
            await interaction.response.send_message(
                "❌ チケット作成者またはスタッフのみ閉じられます。",
                ephemeral=True
            )
            return


        await interaction.response.send_message(
            "本当に閉じますか？",
            view=CloseConfirmView(),
            ephemeral=True
        )


class TicketPanel(discord.ui.View):

    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="🎫 チケットを作成",
        style=discord.ButtonStyle.green,
        custom_id="ticket_create"
    )
    async def create(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        guild = interaction.guild

        category = None

        if config["category"]:
            category = guild.get_channel(
                config["category"]
            )

        if category is None:

            category = discord.utils.get(
                guild.categories,
                name="🎫 Tickets"
            )

        if category is None:

            category = await guild.create_category(
                "🎫 Tickets"
            )

            config["category"] = category.id
            save_config(config)

        for ch in category.text_channels:

            if ch.topic == str(interaction.user.id):

                await interaction.response.send_message(
                    "❌ 既にチケットがあります。",
                    ephemeral=True
                )
                return

        config["ticket_number"] += 1
        save_config(config)

        number = str(
            config["ticket_number"]
        ).zfill(4)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),

            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
                read_message_history=True
            )
        }

        # スタッフロールにも権限を付与
        if config["mention_role"]:
            role = guild.get_role(config["mention_role"])

            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    attach_files=True,
                    embed_links=True,
                    read_message_history=True
                )

        # Botの権限
        bot_member = guild.get_member(self.bot.user.id)

        if bot_member:
            overwrites[bot_member] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True,
                read_message_history=True
            )

        ticket = await guild.create_text_channel(

            name=f"ticket-{number}",

            category=category,

            overwrites=overwrites,

            topic=str(interaction.user.id)

        )

        embed = discord.Embed(
            title=f"🎫 Ticket #{number}",
            description=(
                f"{interaction.user.mention}\n\n"
                "終了時は下のボタンから閉じてください。"
            ),
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="作成者",
            value=interaction.user.mention,
            inline=True
        )

        embed.add_field(
            name="チケット番号",
            value=f"#{number}",
            inline=True
        )

        embed.set_footer(
            text=f"User ID : {interaction.user.id}"
        )


        content = config["first_message"]

        if config["mention_role"]:
            content = f"<@&{config['mention_role']}>\n{config['first_message']}"

        await ticket.send(
            content=content,
            embed=embed,
            view=CloseView()
        )

        if config["log_channel"]:

            log = guild.get_channel(
                config["log_channel"]
            )

            if log:

                log_embed = discord.Embed(
                    title="📂 Ticket Created",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )

                log_embed.add_field(
                    name="チケット",
                    value=ticket.mention,
                    inline=False
                )

                log_embed.add_field(
                    name="作成者",
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


class Ticket(commands.Cog):

    def __init__(self, bot: commands.Bot):

        self.bot = bot

        bot.add_view(
            TicketPanel(bot)
        )

        bot.add_view(
            CloseView()
        )

    @app_commands.command(
        name="ticket",
        description="チケットパネルを設置します"
    )
    @app_commands.default_permissions(administrator=True)
    async def ticket(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        category: discord.CategoryChannel,
        log_channel: discord.TextChannel,
        staff_role: discord.Role = None,
        first_message: str = "スタッフがお伺いします。",
        image: discord.Attachment = None
    ):

        config["category"] = category.id
        config["log_channel"] = log_channel.id

        config["panel_title"] = title
        config["panel_description"] = description
        config["first_message"] = first_message

        if staff_role:
            config["mention_role"] = staff_role.id
        else:
            config["mention_role"] = None

        if image:
            config["panel_image"] = image.url
        else:
            config["panel_image"] = None

        save_config(config)

        embed = create_panel_embed()

        await interaction.channel.send(
            embed=embed,
            view=TicketPanel(self.bot)
        )

        await interaction.response.send_message(
            "✅ チケットパネルを設置しました。",
            ephemeral=True
        )

    @app_commands.command(
        name="ticketadd",
        description="チケットにユーザーを追加します"
    )
    @app_commands.default_permissions(manage_channels=True)
    async def ticketadd(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        try:
            int(interaction.channel.topic)
        except (TypeError, ValueError):
            await interaction.response.send_message(
                "❌ このコマンドはチケットでのみ使用できます。",
                ephemeral=True
            )
            return

        await interaction.channel.set_permissions(
            member,
            view_channel=True,
            send_messages=True,
            attach_files=True,
            read_message_history=True
        )

        await interaction.response.send_message(
            f"✅ {member.mention} を追加しました。",
            ephemeral=True
        )
    @app_commands.command(
        name="ticketremove",
        description="チケットからユーザーを削除します"
    )
    @app_commands.default_permissions(manage_channels=True)
    async def ticketremove(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        try:
            int(interaction.channel.topic)
        except (TypeError, ValueError):
            await interaction.response.send_message(
                "❌ このコマンドはチケットでのみ使用できます。",
                ephemeral=True
            )
            return

        await interaction.channel.set_permissions(
            member,
            overwrite=None
        )

        await interaction.response.send_message(
            f"✅ {member.mention} を削除しました。",
            ephemeral=True
        )

    @app_commands.command(
        name="ticketrename",
        description="チケット名を変更します"
    )
    @app_commands.default_permissions(manage_channels=True)
    async def ticketrename(
        self,
        interaction: discord.Interaction,
        name: str
    ):

        try:
            int(interaction.channel.topic)
        except (TypeError, ValueError):
            await interaction.response.send_message(
                "❌ このコマンドはチケットでのみ使用できます。",
                ephemeral=True
            )
            return

        await interaction.channel.edit(
            name=name
        )

        await interaction.response.send_message(
            f"✅ チケット名を **{name}** に変更しました。",
            ephemeral=True
        )

    @app_commands.command(
        name="ticketclaim",
        description="チケットを担当します"
    )
    @app_commands.default_permissions(manage_channels=True)
    async def ticketclaim(
        self,
        interaction: discord.Interaction
    ):

        try:
            int(interaction.channel.topic)
        except (TypeError, ValueError):
            await interaction.response.send_message(
                "❌ このコマンドはチケットでのみ使用できます。",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="👤 チケット担当",
            description=f"{interaction.user.mention} が担当しました。",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )

        await interaction.channel.send(
            embed=embed
        )

        await interaction.response.send_message(
            "✅ 担当しました。",
            ephemeral=True
        )


async def setup(bot: commands.Bot):

    await bot.add_cog(
        Ticket(bot)
    )