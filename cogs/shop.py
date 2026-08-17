import asyncio
import discord

from discord.ext import commands
from discord import app_commands

import json
import os
import uuid
from datetime import datetime


# =========================================================
# 設定
# =========================================================

DATA_DIR = "data"

SHOPS_FILE = os.path.join(DATA_DIR, "shops.json")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
PAYPAY_FILE = os.path.join(DATA_DIR, "paypay.json")


# =========================================================
# JSON
# =========================================================

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_json(path):
    ensure_data_dir()

    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except (json.JSONDecodeError, OSError):
        return {}


def save_json(path, data):
    ensure_data_dir()

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4
        )


# =========================================================
# 商品選択
# =========================================================

class ProductSelect(discord.ui.Select):

    def __init__(self, cog, products):

        self.cog = cog

        options = []

        for product in products[:25]:

            options.append(
                discord.SelectOption(
                    label=product["name"][:100],
                    description=(
                        f"¥{product['price']:,}"
                    )[:100],
                    value=product["id"]
                )
            )

        super().__init__(
            placeholder="📦 購入する商品を選択してください",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        product_id = self.values[0]

        product = self.cog.products.get(product_id)

        if not product:

            await interaction.response.send_message(
                "❌ 商品が見つかりません。",
                ephemeral=True
            )
            return

        if not product.get("enabled", True):

            await interaction.response.send_message(
                "❌ この商品は現在販売停止中です。",
                ephemeral=True
            )
            return

        # 自分の商品チェック
        if product["seller_id"] == interaction.user.id:

            await interaction.response.send_message(
                "❌ 自分の商品は購入できません。",
                ephemeral=True
            )
            return

        # PayPay登録確認
        seller_paypay = self.cog.paypay_data.get(
            str(product["seller_id"])
        )

        if not seller_paypay:

            await interaction.response.send_message(
                "❌ この販売者はPayPay送金先を登録していません。",
                ephemeral=True
            )
            return

        if not seller_paypay.get("url"):

            await interaction.response.send_message(
                "❌ 販売者のPayPay送金先URLが設定されていません。",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"📦 {product['name']}",
            description=product["description"],
            color=discord.Color.green()
        )

        embed.add_field(
            name="💰 価格",
            value=f"¥{product['price']:,} / 個",
            inline=True
        )

        embed.add_field(
            name="🆔 商品ID",
            value=f"`{product['id']}`",
            inline=True
        )

        embed.add_field(
            name="🏪 販売者",
            value=f"<@{product['seller_id']}>",
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            view=ProductView(
                self.cog,
                product_id
            ),
            ephemeral=True
        )


# =========================================================
# ショップパネル
# =========================================================

class ShopPanelView(discord.ui.View):

    def __init__(self, cog, products):

        super().__init__(
            timeout=None
        )

        self.add_item(
            ProductSelect(
                cog,
                products
            )
        )


# =========================================================
# 商品購入View
# =========================================================

class ProductView(discord.ui.View):

    def __init__(self, cog, product_id):

        super().__init__(
            timeout=300
        )

        self.cog = cog
        self.product_id = product_id

    @discord.ui.button(
        label="🛒 購入する",
        style=discord.ButtonStyle.green
    )
    async def purchase(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        product = self.cog.products.get(
            self.product_id
        )

        if not product:

            await interaction.response.send_message(
                "❌ 商品が存在しません。",
                ephemeral=True
            )
            return

        if not product.get("enabled", True):

            await interaction.response.send_message(
                "❌ この商品は現在販売停止中です。",
                ephemeral=True
            )
            return

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ サーバー内で使用してください。",
                ephemeral=True
            )
            return

        if product["seller_id"] == interaction.user.id:

            await interaction.response.send_message(
                "❌ 自分の商品は購入できません。",
                ephemeral=True
            )
            return

        seller_paypay = self.cog.paypay_data.get(
            str(product["seller_id"])
        )

        if not seller_paypay:

            await interaction.response.send_message(
                "❌ この販売者はPayPay送金先を登録していません。",
                ephemeral=True
            )
            return

        if not seller_paypay.get("url"):

            await interaction.response.send_message(
                "❌ 販売者のPayPay送金先URLが設定されていません。",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(
            QuantityModal(
                self.cog,
                self.product_id
            )
        )


# =========================================================
# 個数入力Modal
# =========================================================

class QuantityModal(discord.ui.Modal):

    def __init__(
        self,
        cog,
        product_id
    ):

        super().__init__(
            title="購入個数"
        )

        self.cog = cog
        self.product_id = product_id

        self.quantity = discord.ui.TextInput(
            label="購入する個数",
            placeholder="例：1",
            required=True,
            min_length=1,
            max_length=4
        )

        self.add_item(
            self.quantity
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        product = self.cog.products.get(
            self.product_id
        )

        if not product:

            await interaction.response.send_message(
                "❌ 商品が見つかりません。",
                ephemeral=True
            )
            return

        try:

            quantity = int(
                self.quantity.value
            )

        except ValueError:

            await interaction.response.send_message(
                "❌ 個数は数字で入力してください。",
                ephemeral=True
            )
            return

        if quantity <= 0:

            await interaction.response.send_message(
                "❌ 個数は1個以上にしてください。",
                ephemeral=True
            )
            return

        if quantity > 9999:

            await interaction.response.send_message(
                "❌ 個数は9999個以下にしてください。",
                ephemeral=True
            )
            return

        total_price = product["price"] * quantity

        embed = discord.Embed(
            title="🛒 購入確認",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📦 商品",
            value=product["name"],
            inline=False
        )

        embed.add_field(
            name="🔢 個数",
            value=f"{quantity}個",
            inline=True
        )

        embed.add_field(
            name="💰 1個あたり",
            value=f"¥{product['price']:,}",
            inline=True
        )

        embed.add_field(
            name="💰 合計金額",
            value=f"¥{total_price:,}",
            inline=False
        )

        embed.set_footer(
            text="この内容で購入しますか？"
        )

        await interaction.response.send_message(
            embed=embed,
            view=QuantityConfirmView(
                self.cog,
                self.product_id,
                quantity
            ),
            ephemeral=True
        )


# =========================================================
# 個数購入確認View
# =========================================================

class QuantityConfirmView(discord.ui.View):

    def __init__(
        self,
        cog,
        product_id,
        quantity
    ):

        super().__init__(
            timeout=60
        )

        self.cog = cog
        self.product_id = product_id
        self.quantity = quantity

    # =====================================================
    # 購入確定
    # =====================================================

    @discord.ui.button(
        label="✅ 購入する",
        style=discord.ButtonStyle.green
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        product = self.cog.products.get(
            self.product_id
        )

        if not product:

            await interaction.response.edit_message(
                content="❌ 商品が見つかりません。",
                embed=None,
                view=None
            )
            return

        if not product.get("enabled", True):

            await interaction.response.edit_message(
                content="❌ この商品は販売停止中です。",
                embed=None,
                view=None
            )
            return

        if product["seller_id"] == interaction.user.id:

            await interaction.response.edit_message(
                content="❌ 自分の商品は購入できません。",
                embed=None,
                view=None
            )
            return

        seller_paypay = self.cog.paypay_data.get(
            str(product["seller_id"])
        )

        if not seller_paypay:

            await interaction.response.edit_message(
                content="❌ 販売者のPayPay送金先が登録されていません。",
                embed=None,
                view=None
            )
            return

        paypay_url = seller_paypay.get("url")

        if not paypay_url:

            await interaction.response.edit_message(
                content="❌ PayPay送金先URLが設定されていません。",
                embed=None,
                view=None
            )
            return

        total_price = (
            product["price"] * self.quantity
        )

        buyer = interaction.guild.get_member(
            interaction.user.id
        )

        seller = interaction.guild.get_member(
            product["seller_id"]
        )

        if not buyer or not seller:

            await interaction.response.edit_message(
                content="❌ 購入者または販売者を取得できませんでした。",
                embed=None,
                view=None
            )
            return

        # =================================================
        # 注文を1回だけ作成
        # =================================================

        order_id = self.cog.create_order(
            guild_id=interaction.guild.id,
            buyer_id=interaction.user.id,
            seller_id=product["seller_id"],
            product_id=self.product_id,
            quantity=self.quantity
        )

        if not order_id:

            await interaction.response.edit_message(
                content="❌ 注文の作成に失敗しました。",
                embed=None,
                view=None
            )
            return

        # =================================================
        # Ticket作成
        # =================================================

        ticket = None

        try:

            from .ticket import create_sale_ticket

            ticket = await create_sale_ticket(
                self.cog.bot,
                interaction.guild,
                buyer,
                seller,
                order_id,
                product["name"],
                total_price
            )

        except Exception as e:

            print(
                f"[Shop] 販売Ticket作成エラー: {e}"
            )

        if not ticket:

            order = self.cog.orders.get(order_id)

            if order:

                order["status"] = "ticket_error"
                order["ticket_error_at"] = (
                    datetime.now().isoformat()
                )

                self.cog.save_orders()

            await interaction.response.edit_message(
                content=(
                    "❌ 販売Ticketの作成に失敗しました。\n"
                    "Botの権限を確認してください。"
                ),
                embed=None,
                view=None
            )
            return

        # =================================================
        # Ticket情報保存
        # =================================================

        order = self.cog.orders.get(order_id)

        if order:

            order["ticket_id"] = ticket.id
            order["ticket_channel_id"] = ticket.id
            order["ticket_created_at"] = (
                datetime.now().isoformat()
            )

            self.cog.save_orders()

        # =================================================
        # 支払いEmbed
        # =================================================

        payment_embed = discord.Embed(
            title="💰 お支払い",
            description=(
                f"{buyer.mention} さん\n\n"
                "下のボタンから販売者のPayPayへ直接支払ってください。\n\n"
                "⚠️ **Botが代金を預かることはありません。**\n"
                "PayPayアプリで販売者への送金を行ってください。\n\n"
                "支払いが完了したら\n"
                "「✅ 支払い完了」を押してください。"
            ),
            color=discord.Color.orange()
        )

        payment_embed.add_field(
            name="📦 商品",
            value=product["name"],
            inline=False
        )

        payment_embed.add_field(
            name="🔢 個数",
            value=f"{self.quantity}個",
            inline=True
        )

        payment_embed.add_field(
            name="💰 1個あたり",
            value=f"¥{product['price']:,}",
            inline=True
        )

        payment_embed.add_field(
            name="💰 合計金額",
            value=f"¥{total_price:,}",
            inline=False
        )

        payment_embed.add_field(
            name="🏪 支払先",
            value=f"<@{product['seller_id']}>",
            inline=False
        )

        payment_embed.add_field(
            name="🆔 注文ID",
            value=f"`{order_id}`",
            inline=False
        )

        await ticket.send(
            embed=payment_embed,
            view=PaymentView(
                self.cog,
                order_id,
                paypay_url
            )
        )

        # =================================================
        # 購入開始完了
        # =================================================

        await interaction.response.edit_message(
            content=(
                "✅ **購入手続きを開始しました！**\n\n"
                f"📦 商品：**{product['name']}**\n"
                f"🔢 個数：**{self.quantity}個**\n"
                f"💰 合計：**¥{total_price:,}**\n"
                f"🆔 注文ID：`{order_id}`\n\n"
                f"🎫 {ticket.mention}\n\n"
                "Ticket内から販売者へPayPayで直接支払ってください。"
            ),
            embed=None,
            view=None
        )

    # =====================================================
    # キャンセル
    # =====================================================

    @discord.ui.button(
        label="❌ キャンセル",
        style=discord.ButtonStyle.red
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            content="❌ 購入をキャンセルしました。",
            embed=None,
            view=None
        )


# =========================================================
# 支払いView
# =========================================================

class PaymentView(discord.ui.View):

    def __init__(
        self,
        cog,
        order_id,
        paypay_url
    ):

        super().__init__(
            timeout=None
        )

        self.cog = cog
        self.order_id = order_id
        self.paypay_url = paypay_url

        # PayPayリンク
        if paypay_url:

            self.add_item(
                discord.ui.Button(
                    label="💰 PayPayで支払う",
                    style=discord.ButtonStyle.link,
                    url=paypay_url
                )
            )

    # =====================================================
    # 支払い完了
    # =====================================================

    @discord.ui.button(
        label="✅ 支払い完了",
        style=discord.ButtonStyle.green,
        custom_id="shop_payment_completed"
    )
    async def payment_completed(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        order = self.cog.orders.get(
            self.order_id
        )

        if not order:

            await interaction.response.send_message(
                "❌ 注文が見つかりません。",
                ephemeral=True
            )
            return

        if interaction.user.id != order["buyer_id"]:

            await interaction.response.send_message(
                "❌ この注文の購入者ではありません。",
                ephemeral=True
            )
            return

        if order["payment_status"] == "paid":

            await interaction.response.send_message(
                "❌ すでに支払い確認済みです。",
                ephemeral=True
            )
            return

        if order["payment_status"] == "checking":

            await interaction.response.send_message(
                "⏳ すでに支払い確認待ちです。",
                ephemeral=True
            )
            return

        # 支払い申告
        order["payment_status"] = "checking"
        order["status"] = "payment_checking"
        order["payment_submitted_at"] = (
            datetime.now().isoformat()
        )

        self.cog.save_orders()

        button.disabled = True

        await interaction.response.edit_message(
            embed=self.cog.create_payment_check_embed(
                self.order_id
            ),
            view=self
        )

        await self.cog.notify_seller_payment(
            self.order_id
        )

    # =====================================================
    # 誤購入
    # =====================================================

    @discord.ui.button(
        label="❌ 誤購入",
        style=discord.ButtonStyle.red,
        custom_id="shop_cancel_order"
    )
    async def cancel_order(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        order = self.cog.orders.get(
            self.order_id
        )

        if not order:

            await interaction.response.send_message(
                "❌ 注文が見つかりません。",
                ephemeral=True
            )
            return

        if interaction.user.id != order["buyer_id"]:

            await interaction.response.send_message(
                "❌ この注文の購入者ではありません。",
                ephemeral=True
            )
            return

        if order["payment_status"] == "paid":

            await interaction.response.send_message(
                "❌ すでに支払い確認済みのため、誤購入キャンセルはできません。",
                ephemeral=True
            )
            return

        if order["payment_status"] == "checking":

            await interaction.response.send_message(
                "❌ すでに「支払い完了」が押されているため、誤購入キャンセルはできません。",
                ephemeral=True
            )
            return

        if order["status"] == "cancelled":

            await interaction.response.send_message(
                "❌ この注文はすでにキャンセルされています。",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            (
                "⚠️ **本当にこの注文をキャンセルしますか？**\n\n"
                "誤購入として処理され、Ticketが削除されます。"
            ),
            ephemeral=True,
            view=CancelOrderConfirmView(
                self.cog,
                self.order_id
            )
        )


# =========================================================
# 誤購入確認View
# =========================================================

class CancelOrderConfirmView(discord.ui.View):

    def __init__(
        self,
        cog,
        order_id
    ):

        super().__init__(
            timeout=60
        )

        self.cog = cog
        self.order_id = order_id

    @discord.ui.button(
        label="✅ はい、キャンセルする",
        style=discord.ButtonStyle.red
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        order = self.cog.orders.get(
            self.order_id
        )

        if not order:

            await interaction.response.edit_message(
                content="❌ 注文が見つかりません。",
                view=None
            )
            return

        if interaction.user.id != order["buyer_id"]:

            await interaction.response.edit_message(
                content="❌ この注文の購入者ではありません。",
                view=None
            )
            return

        if order["payment_status"] == "paid":

            await interaction.response.edit_message(
                content=(
                    "❌ すでに支払い確認済みのため、"
                    "キャンセルできません。"
                ),
                view=None
            )
            return

        if order["payment_status"] == "checking":

            await interaction.response.edit_message(
                content=(
                    "❌ すでに「支払い完了」が押されているため、"
                    "誤購入キャンセルはできません。"
                ),
                view=None
            )
            return

        if order["status"] == "cancelled":

            await interaction.response.edit_message(
                content="❌ この注文はすでにキャンセルされています。",
                view=None
            )
            return

        # キャンセル
        order["payment_status"] = "cancelled"
        order["delivery_status"] = "cancelled"
        order["status"] = "cancelled"
        order["cancelled_at"] = (
            datetime.now().isoformat()
        )
        order["cancelled_by"] = interaction.user.id

        self.cog.save_orders()

        await interaction.response.edit_message(
            content=(
                "✅ **誤購入としてキャンセルしました。**\n\n"
                "このTicketを削除します。"
            ),
            view=None
        )

        channel = interaction.channel

        if isinstance(channel, discord.TextChannel):

            await asyncio.sleep(2)

            try:

                await channel.delete(
                    reason=f"誤購入キャンセル Order: {self.order_id}"
                )

            except discord.Forbidden:

                print(
                    "[Shop] Ticket削除権限がありません。"
                )

            except discord.HTTPException as e:

                print(
                    f"[Shop] Ticket削除エラー: {e}"
                )

    @discord.ui.button(
        label="❌ いいえ",
        style=discord.ButtonStyle.gray
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            content="✅ キャンセル操作を取り消しました。",
            view=None
        )


# =========================================================
# 販売者用 注文View
# =========================================================

class OrderView(discord.ui.View):

    def __init__(
        self,
        cog,
        order_id
    ):

        super().__init__(
            timeout=None
        )

        self.cog = cog
        self.order_id = order_id

    # =====================================================
    # 支払い確認
    # =====================================================

    @discord.ui.button(
        label="💰 支払い確認",
        style=discord.ButtonStyle.green,
        custom_id="shop_confirm_payment"
    )
    async def confirm_payment(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        order = self.cog.orders.get(
            self.order_id
        )

        if not order:

            await interaction.response.send_message(
                "❌ 注文が見つかりません。",
                ephemeral=True
            )
            return

        if interaction.user.id != order["seller_id"]:

            await interaction.response.send_message(
                "❌ この注文の販売者ではありません。",
                ephemeral=True
            )
            return

        if order["payment_status"] == "paid":

            await interaction.response.send_message(
                "❌ すでに支払い確認済みです。",
                ephemeral=True
            )
            return

        if order["payment_status"] != "checking":

            await interaction.response.send_message(
                "❌ 購入者がまだ支払い完了を押していません。",
                ephemeral=True
            )
            return

        success = await self.cog.payment_completed(
            self.order_id
        )

        if not success:

            await interaction.response.send_message(
                "❌ 支払い確認処理に失敗しました。",
                ephemeral=True
            )
            return

        button.disabled = True

        await interaction.response.edit_message(
            embed=self.cog.create_order_embed(
                self.order_id
            ),
            view=self
        )

    # =====================================================
    # 商品を渡した
    # =====================================================

    @discord.ui.button(
        label="📦 商品を渡した",
        style=discord.ButtonStyle.blurple,
        custom_id="shop_delivered"
    )
    async def delivered(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        order = self.cog.orders.get(
            self.order_id
        )

        if not order:

            await interaction.response.send_message(
                "❌ 注文が見つかりません。",
                ephemeral=True
            )
            return

        if interaction.user.id != order["seller_id"]:

            await interaction.response.send_message(
                "❌ この注文の販売者ではありません。",
                ephemeral=True
            )
            return

        if order["payment_status"] != "paid":

            await interaction.response.send_message(
                "❌ まだ支払い確認されていません。",
                ephemeral=True
            )
            return

        if order["status"] == "completed":

            await interaction.response.send_message(
                "❌ この注文はすでに完了しています。",
                ephemeral=True
            )
            return

        order["delivery_status"] = "delivered"
        order["status"] = "completed"
        order["completed_at"] = (
            datetime.now().isoformat()
        )

        self.cog.save_orders()

        button.disabled = True

        await interaction.response.edit_message(
            embed=self.cog.create_order_embed(
                self.order_id
            ),
            view=self
        )

        buyer = self.cog.bot.get_user(
            order["buyer_id"]
        )

        if buyer:

            try:

                embed = discord.Embed(
                    title="✅ 商品の受け渡しが完了しました",
                    color=discord.Color.green()
                )

                embed.add_field(
                    name="📦 商品",
                    value=order["product_name"],
                    inline=False
                )

                embed.add_field(
                    name="🔢 個数",
                    value=f"{order['quantity']}個",
                    inline=True
                )

                embed.add_field(
                    name="💰 金額",
                    value=f"¥{order['total_price']:,}",
                    inline=True
                )

                embed.add_field(
                    name="🆔 注文ID",
                    value=f"`{self.order_id}`",
                    inline=False
                )

                await buyer.send(
                    embed=embed
                )

            except discord.Forbidden:
                pass


# =========================================================
# Shop Cog
# =========================================================

class Shop(commands.Cog):

    def __init__(
        self,
        bot
    ):

        self.bot = bot

        self.shops = load_json(
            SHOPS_FILE
        )

        self.products = load_json(
            PRODUCTS_FILE
        )

        self.orders = load_json(
            ORDERS_FILE
        )

        self.paypay_data = load_json(
            PAYPAY_FILE
        )

    # =====================================================
    # 保存
    # =====================================================

    def save_shops(self):

        save_json(
            SHOPS_FILE,
            self.shops
        )

    def save_products(self):

        save_json(
            PRODUCTS_FILE,
            self.products
        )

    def save_orders(self):

        save_json(
            ORDERS_FILE,
            self.orders
        )

    def save_paypay(self):

        save_json(
            PAYPAY_FILE,
            self.paypay_data
        )

    # =====================================================
    # ショップ作成
    # =====================================================

    @app_commands.command(
        name="shop_create",
        description="ショップを作成します"
    )
    @app_commands.describe(
        name="ショップ名"
    )
    async def shop_create(
        self,
        interaction: discord.Interaction,
        name: str
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ サーバー内で使用してください。",
                ephemeral=True
            )
            return

        guild_id = str(
            interaction.guild.id
        )

        name = name.strip()

        if not name:

            await interaction.response.send_message(
                "❌ ショップ名を入力してください。",
                ephemeral=True
            )
            return

        if len(name) > 50:

            await interaction.response.send_message(
                "❌ ショップ名は50文字以内にしてください。",
                ephemeral=True
            )
            return

        if guild_id in self.shops:

            await interaction.response.send_message(
                "❌ このサーバーにはすでにショップがあります。",
                ephemeral=True
            )
            return

        self.shops[guild_id] = {
            "owner_id": interaction.user.id,
            "name": name,
            "created_at": datetime.now().isoformat()
        }

        self.save_shops()

        await interaction.response.send_message(
            f"✅ **{name}** を作成しました。",
            ephemeral=True
        )

    # =====================================================
    # 商品追加
    # =====================================================

    @app_commands.command(
        name="shop_product_add",
        description="商品を追加します"
    )
    @app_commands.describe(
        name="商品名",
        price="価格",
        description="商品説明"
    )
    async def shop_product_add(
        self,
        interaction: discord.Interaction,
        name: str,
        price: int,
        description: str
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ サーバー内で使用してください。",
                ephemeral=True
            )
            return

        guild_id = str(
            interaction.guild.id
        )

        shop = self.shops.get(
            guild_id
        )

        if not shop:

            await interaction.response.send_message(
                "❌ 先に `/shop_create` をしてください。",
                ephemeral=True
            )
            return

        if shop["owner_id"] != interaction.user.id:

            await interaction.response.send_message(
                "❌ ショップオーナーのみ使用できます。",
                ephemeral=True
            )
            return

        name = name.strip()
        description = description.strip()

        if not name:

            await interaction.response.send_message(
                "❌ 商品名を入力してください。",
                ephemeral=True
            )
            return

        if price <= 0:

            await interaction.response.send_message(
                "❌ 価格は1円以上にしてください。",
                ephemeral=True
            )
            return

        product_id = uuid.uuid4().hex[:12]

        self.products[product_id] = {
            "id": product_id,
            "guild_id": interaction.guild.id,
            "seller_id": interaction.user.id,
            "name": name,
            "price": price,
            "description": description,
            "enabled": True,
            "created_at": datetime.now().isoformat()
        }

        self.save_products()

        await interaction.response.send_message(
            (
                "✅ 商品を追加しました。\n"
                f"📦 {name}\n"
                f"💰 ¥{price:,} / 個\n"
                f"🆔 `{product_id}`"
            ),
            ephemeral=True
        )

    # =====================================================
    # 商品一覧
    # =====================================================

    @app_commands.command(
        name="shop_products",
        description="商品一覧を表示します"
    )
    async def shop_products(
        self,
        interaction: discord.Interaction
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ サーバー内で使用してください。",
                ephemeral=True
            )
            return

        guild_id = interaction.guild.id

        products = [
            p
            for p in self.products.values()
            if p.get("guild_id") == guild_id
        ]

        if not products:

            await interaction.response.send_message(
                "❌ 商品がありません。",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="📦 商品一覧",
            color=discord.Color.blue()
        )

        for product in products[:25]:

            status = (
                "🟢 販売中"
                if product.get("enabled", True)
                else "🔴 販売停止"
            )

            embed.add_field(
                name=(
                    f"{product['name']}"
                    f" — ¥{product['price']:,}"
                ),
                value=(
                    f"{product['description']}\n"
                    f"🆔 `{product['id']}`\n"
                    f"{status}"
                ),
                inline=False
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    # =====================================================
    # 商品削除
    # =====================================================

    @app_commands.command(
        name="shop_product_delete",
        description="商品を削除します"
    )
    @app_commands.describe(
        product_id="商品ID"
    )
    async def shop_product_delete(
        self,
        interaction: discord.Interaction,
        product_id: str
    ):

        product = self.products.get(
            product_id
        )

        if not product:

            await interaction.response.send_message(
                "❌ 商品が見つかりません。",
                ephemeral=True
            )
            return

        if product["seller_id"] != interaction.user.id:

            await interaction.response.send_message(
                "❌ この商品の販売者ではありません。",
                ephemeral=True
            )
            return

        del self.products[product_id]

        self.save_products()

        await interaction.response.send_message(
            "✅ 商品を削除しました。",
            ephemeral=True
        )

    # =====================================================
    # ショップパネル
    # =====================================================

    @app_commands.command(
        name="shop_panel",
        description="ショップパネルを設置します"
    )
    async def shop_panel(
        self,
        interaction: discord.Interaction
    ):

        if interaction.guild is None:

            await interaction.response.send_message(
                "❌ サーバー内で使用してください。",
                ephemeral=True
            )
            return

        guild_id = str(
            interaction.guild.id
        )

        shop = self.shops.get(
            guild_id
        )

        if not shop:

            await interaction.response.send_message(
                "❌ 先に `/shop_create` をしてください。",
                ephemeral=True
            )
            return

        if shop["owner_id"] != interaction.user.id:

            await interaction.response.send_message(
                "❌ ショップオーナーのみ使用できます。",
                ephemeral=True
            )
            return

        products = [
            p
            for p in self.products.values()
            if p.get("guild_id") == interaction.guild.id
            and p.get("enabled", True)
        ]

        if not products:

            await interaction.response.send_message(
                "❌ 販売中の商品がありません。",
                ephemeral=True
            )
            return

        products = products[:25]

        embed = discord.Embed(
            title=f"🛒 {shop['name']}",
            description=(
                "購入したい商品を下のメニューから選択してください。"
            ),
            color=discord.Color.blue()
        )

        for product in products:

            embed.add_field(
                name=f"📦 {product['name']}",
                value=(
                    f"💰 ¥{product['price']:,} / 個\n"
                    f"{product['description']}"
                ),
                inline=False
            )

        embed.set_footer(
            text="商品を選択すると購入画面が表示されます。"
        )

        await interaction.channel.send(
            embed=embed,
            view=ShopPanelView(
                self,
                products
            )
        )

        await interaction.response.send_message(
            "✅ ショップパネルを設置しました。",
            ephemeral=True
        )

    # =====================================================
    # 注文作成
    # =====================================================

    def create_order(
        self,
        guild_id,
        buyer_id,
        seller_id,
        product_id,
        quantity=1
    ):

        product = self.products.get(
            product_id
        )

        if not product:
            return None

        if quantity <= 0:
            return None

        order_id = uuid.uuid4().hex[:10]

        total_price = (
            product["price"] * quantity
        )

        self.orders[order_id] = {

            "id": order_id,

            "guild_id": guild_id,

            "buyer_id": buyer_id,

            "seller_id": seller_id,

            "product_id": product_id,

            "product_name": product["name"],

            "price": product["price"],

            "quantity": quantity,

            "total_price": total_price,

            "payment_status": "pending",

            "delivery_status": "pending",

            "status": "pending",

            "ticket_id": None,

            "ticket_channel_id": None,

            "created_at": datetime.now().isoformat()
        }

        self.save_orders()

        return order_id

    # =====================================================
    # 支払い確認待ちEmbed
    # =====================================================

    def create_payment_check_embed(
        self,
        order_id
    ):

        order = self.orders.get(
            order_id
        )

        if not order:

            return discord.Embed(
                title="❌ 注文が見つかりません。",
                color=discord.Color.red()
            )

        embed = discord.Embed(
            title=f"💰 入金確認待ち #{order_id}",
            description=(
                "購入者が支払い完了を申告しました。\n\n"
                "販売者はPayPayアプリを確認し、"
                "実際に入金されていることを確認してください。\n\n"
                "確認できた場合のみ「💰 支払い確認」を押してください。"
            ),
            color=discord.Color.orange()
        )

        embed.add_field(
            name="📦 商品",
            value=order["product_name"],
            inline=False
        )

        embed.add_field(
            name="🔢 個数",
            value=f"{order['quantity']}個",
            inline=True
        )

        embed.add_field(
            name="💰 合計金額",
            value=f"¥{order['total_price']:,}",
            inline=True
        )

        embed.add_field(
            name="🆔 注文ID",
            value=f"`{order_id}`",
            inline=False
        )

        return embed

    # =====================================================
    # 注文Embed
    # =====================================================

    def create_order_embed(
        self,
        order_id
    ):

        order = self.orders.get(
            order_id
        )

        if not order:

            return discord.Embed(
                title="❌ 注文が見つかりません。",
                color=discord.Color.red()
            )

        payment = order.get(
            "payment_status",
            "pending"
        )

        delivery = order.get(
            "delivery_status",
            "pending"
        )

        status = order.get(
            "status",
            "pending"
        )

        payment_text = {
            "pending": "⏳ 支払い待ち",
            "checking": "⏳ 入金確認待ち",
            "paid": "✅ 支払い確認済み",
            "cancelled": "❌ キャンセル"
        }.get(
            payment,
            "⏳ 不明"
        )

        delivery_text = {
            "pending": "📦 未受け渡し",
            "delivered": "✅ 商品受け渡し済み",
            "cancelled": "❌ キャンセル"
        }.get(
            delivery,
            "📦 未受け渡し"
        )

        status_text = {
            "pending": "⏳ 処理中",
            "payment_checking": "💰 入金確認待ち",
            "paid": "📦 商品受け渡し待ち",
            "completed": "✅ 完了",
            "cancelled": "❌ キャンセル"
        }.get(
            status,
            "⏳ 処理中"
        )

        embed = discord.Embed(
            title=f"🛒 注文 #{order_id}",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="📦 商品",
            value=order["product_name"],
            inline=False
        )

        embed.add_field(
            name="🔢 個数",
            value=f"{order['quantity']}個",
            inline=True
        )

        embed.add_field(
            name="💰 合計金額",
            value=f"¥{order['total_price']:,}",
            inline=True
        )

        embed.add_field(
            name="👤 購入者",
            value=f"<@{order['buyer_id']}>",
            inline=True
        )

        embed.add_field(
            name="💳 支払い",
            value=payment_text,
            inline=False
        )

        embed.add_field(
            name="📦 商品受け渡し",
            value=delivery_text,
            inline=False
        )

        embed.add_field(
            name="📋 状態",
            value=status_text,
            inline=False
        )

        ticket_id = order.get(
            "ticket_channel_id"
        )

        if ticket_id:

            embed.add_field(
                name="🎫 Ticket",
                value=f"<#{ticket_id}>",
                inline=False
            )

        return embed

    # =====================================================
    # 販売者通知
    # =====================================================

    async def notify_seller_payment(
        self,
        order_id
    ):

        order = self.orders.get(
            order_id
        )

        if not order:
            return

        seller = self.bot.get_user(
            order["seller_id"]
        )

        if not seller:
            return

        embed = discord.Embed(
            title="💰 支払い確認が必要です",
            description=(
                "購入者が支払い完了を申告しました。\n\n"
                "⚠️ 購入者の申告だけでは支払い確認済みにはなりません。\n"
                "必ずPayPayアプリで実際の入金を確認してください。"
            ),
            color=discord.Color.orange()
        )

        embed.add_field(
            name="🆔 注文ID",
            value=f"`{order_id}`",
            inline=False
        )

        embed.add_field(
            name="📦 商品",
            value=order["product_name"],
            inline=True
        )

        embed.add_field(
            name="🔢 個数",
            value=f"{order['quantity']}個",
            inline=True
        )

        embed.add_field(
            name="💰 合計金額",
            value=f"¥{order['total_price']:,}",
            inline=False
        )

        try:

            await seller.send(
                embed=embed,
                view=OrderView(
                    self,
                    order_id
                )
            )

        except discord.Forbidden:

            print(
                f"[Shop] {seller.id} にDMを送信できませんでした。"
            )

    # =====================================================
    # 支払い確認
    # =====================================================

    async def payment_completed(
        self,
        order_id
    ):

        order = self.orders.get(
            order_id
        )

        if not order:
            return False

        if order["payment_status"] != "checking":
            return False

        # =================================================
        # Bot内の残高は一切増やさない
        # =================================================

        order["payment_status"] = "paid"
        order["status"] = "paid"

        order["paid_at"] = (
            datetime.now().isoformat()
        )

        self.save_orders()

        return True

    # =====================================================
    # 注文一覧
    # =====================================================

    @app_commands.command(
        name="shop_orders",
        description="自分の注文一覧を表示します"
    )
    async def shop_orders(
        self,
        interaction: discord.Interaction
    ):

        orders = [
            order
            for order in self.orders.values()
            if (
                order["seller_id"] == interaction.user.id
                or order["buyer_id"] == interaction.user.id
            )
        ]

        if not orders:

            await interaction.response.send_message(
                "📦 注文はありません。",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="📦 注文一覧",
            color=discord.Color.blue()
        )

        for order in orders[-10:]:

            embed.add_field(
                name=(
                    f"#{order['id']} "
                    f"{order['product_name']}"
                ),
                value=(
                    f"🔢 {order['quantity']}個\n"
                    f"💰 ¥{order['total_price']:,}\n"
                    f"💳 {order['payment_status']}\n"
                    f"📦 {order['delivery_status']}\n"
                    f"📋 {order['status']}"
                ),
                inline=False
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# =========================================================
# Setup
# =========================================================

async def setup(
    bot: commands.Bot
):

    await bot.add_cog(
        Shop(bot)
    )