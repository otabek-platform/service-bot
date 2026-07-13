from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 Заказать сайт")
    builder.button(text="🤖 Заказать Telegram бота")
    builder.button(text="📡 Установка GPS трекера")
    builder.button(text="💬 AI Ассистент")
    builder.button(text="🌟 Портфолио")
    builder.button(text="📞 Контакты")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def exit_ai_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🚪 Выйти из AI чата")
    return builder.as_markup(resize_keyboard=True)


def admin_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📦 Заказы", callback_data="admin_orders")
    builder.button(text="🔑 Установить Groq API ключ", callback_data="admin_set_api_key")
    builder.button(text="📊 Статистика API", callback_data="admin_stats")
    builder.button(text="⚙️ Лимиты", callback_data="admin_limits")
    builder.button(text="📨 Рассылка", callback_data="admin_broadcast")
    builder.adjust(1)
    return builder.as_markup()


def order_actions(order_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ В работе", callback_data=f"order_status_{order_id}_in_progress")
    builder.button(text="✔️ Завершён", callback_data=f"order_status_{order_id}_completed")
    builder.button(text="❌ Отменён", callback_data=f"order_status_{order_id}_cancelled")
    builder.adjust(1)
    return builder.as_markup()


def cancel_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отменить заказ", callback_data="order_cancel")
    return builder.as_markup()


def web_purpose_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Лендинг", callback_data="opurpose_web_landing")
    builder.button(text="🛒 Интернет-магазин", callback_data="opurpose_web_shop")
    builder.button(text="📋 Сайт-каталог", callback_data="opurpose_web_catalog")
    builder.button(text="🏢 Корпоративный сайт", callback_data="opurpose_web_corporate")
    builder.button(text="❌ Отменить", callback_data="order_cancel")
    builder.adjust(1)
    return builder.as_markup()


def bot_purpose_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="ℹ️ Информационный / FAQ", callback_data="opurpose_bot_info")
    builder.button(text="📦 Каталог товаров", callback_data="opurpose_bot_catalog")
    builder.button(text="🛍️ Магазин с оплатой", callback_data="opurpose_bot_shop")
    builder.button(text="🤖 AI-ассистент", callback_data="opurpose_bot_ai")
    builder.button(text="❌ Отменить", callback_data="order_cancel")
    builder.adjust(1)
    return builder.as_markup()


def gps_type_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🚗 Личный автомобиль", callback_data="opurpose_gps_personal")
    builder.button(text="🚛 Автопарк (2-5 машин)", callback_data="opurpose_gps_fleet_small")
    builder.button(text="🚛🚛 Автопарк (5-10 машин)", callback_data="opurpose_gps_fleet_big")
    builder.button(text="📡 Оборудование / Активы", callback_data="opurpose_gps_equipment")
    builder.button(text="❌ Отменить", callback_data="order_cancel")
    builder.adjust(1)
    return builder.as_markup()


def design_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="🎨 С нуля (нужен дизайн)", callback_data="odesign_scratch")
    builder.button(text="📐 Есть макеты / референсы", callback_data="odesign_refs")
    builder.button(text="❌ Отменить", callback_data="order_cancel")
    builder.adjust(1)
    return builder.as_markup()


def need_integrations_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Приём платежей", callback_data="oint_payment")
    builder.button(text="📊 CRM система", callback_data="oint_crm")
    builder.button(text="🗄️ База данных", callback_data="oint_database")
    builder.button(text="🤖 AI / ChatGPT", callback_data="oint_ai")
    builder.button(text="📨 Рассылки / Email", callback_data="oint_mailing")
    builder.button(text="⏭️ Ничего / Позже решу", callback_data="oint_none")
    builder.button(text="❌ Отменить", callback_data="order_cancel")
    builder.adjust(1)
    return builder.as_markup()


def budget_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="до $300", callback_data="obudget_300")
    builder.button(text="$300-600", callback_data="obudget_600")
    builder.button(text="$600-1000", callback_data="obudget_1000")
    builder.button(text="$1000+", callback_data="obudget_2000")
    builder.button(text="Не знаю / Обсудить", callback_data="obudget_unknown")
    builder.button(text="❌ Отменить", callback_data="order_cancel")
    builder.adjust(2)
    return builder.as_markup()


def gps_budget_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="до $100", callback_data="obudget_100")
    builder.button(text="$100-300", callback_data="obudget_300")
    builder.button(text="$300+", callback_data="obudget_1000")
    builder.button(text="Не знаю / Обсудить", callback_data="obudget_unknown")
    builder.button(text="❌ Отменить", callback_data="order_cancel")
    builder.adjust(2)
    return builder.as_markup()


def confirm_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить заказ", callback_data="order_confirm")
    builder.button(text="🔄 Начать заново", callback_data="order_restart")
    builder.button(text="❌ Отменить", callback_data="order_cancel")
    builder.adjust(1)
    return builder.as_markup()
