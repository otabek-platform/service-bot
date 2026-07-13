from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database import (
    get_config, set_config, get_orders,
    update_order_status, get_api_usage, get_total_usage_today,
    is_admin,
)
from keyboards import admin_menu, order_actions

router = Router()


class AdminStates(StatesGroup):
    waiting_api_key = State()
    waiting_max_tokens = State()
    waiting_max_requests = State()
    waiting_broadcast = State()


def admin_filter(func):
    async def wrapper(message: Message, *args, **kwargs):
        if not await is_admin(message.from_user.id):
            await message.answer("❌ У вас нет доступа к админ-панели.")
            return
        return await func(message, *args, **kwargs)
    return wrapper


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    await message.answer(
        "👑 *Панель администратора*\n\nВыберите действие:",
        reply_markup=admin_menu(),
    )


@router.callback_query(F.data == "admin_orders")
async def admin_orders(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    orders = await get_orders(10)
    if not orders:
        await callback.message.edit_text("📦 Заказов пока нет.")
        return
    for order in orders:
        status_emoji = {
            "new": "🆕",
            "in_progress": "🔄",
            "completed": "✅",
            "cancelled": "❌",
        }.get(order["status"], "❓")
        text = (
            f"{status_emoji} *Заказ #{order['id']}*\n"
            f"Клиент: {order['full_name']} (@{order['username']})\n"
            f"Тип: {order['order_type']}\n"
            f"Дата: {order['created_at']}\n"
            f"Статус: {order['status']}\n"
            f"Детали: {order['details'][:300]}"
        )
        await callback.message.answer(
            text,
            reply_markup=order_actions(order["id"]),
        )
    await callback.message.delete()


@router.callback_query(F.data.startswith("order_status_"))
async def order_status_change(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    parts = callback.data.split("_")
    order_id = int(parts[2])
    new_status = parts[3]
    await update_order_status(order_id, new_status)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.edit_text(
        f"{callback.message.text}\n\n✅ Статус обновлён на: {new_status}"
    )
    await callback.answer(f"Статус заказа #{order_id} изменён на {new_status}")


@router.callback_query(F.data == "admin_set_api_key")
async def admin_set_api_key_prompt(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    current = await get_config("groq_api_key")
    masked = current[:8] + "..." + current[-4:] if current and len(current) > 12 else "не установлен"
    await callback.message.edit_text(
        f"🔑 *Текущий API ключ Groq:* {masked}\n\n"
        "Отправьте новый Groq API ключ (или /cancel для отмены):"
    )
    await state.set_state(AdminStates.waiting_api_key)


@router.message(AdminStates.waiting_api_key, Command("cancel"))
async def cancel_api_key(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено.", reply_markup=admin_menu())


@router.message(AdminStates.waiting_api_key, F.text)
async def admin_save_api_key(message: Message, state: FSMContext):
    await set_config("groq_api_key", message.text.strip())
    await state.clear()
    await message.answer("✅ Groq API ключ сохранён!", reply_markup=admin_menu())


@router.callback_query(F.data == "admin_limits")
async def admin_limits(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    max_tokens = await get_config("max_daily_tokens") or "100000"
    max_requests = await get_config("max_daily_requests") or "500"
    usage = await get_total_usage_today()

    text = (
        f"⚙️ *Лимиты на сегодня:*\n\n"
        f"📊 Токенов: {usage['tokens']} / {max_tokens}\n"
        f"📊 Запросов: {usage['requests']} / {max_requests}\n\n"
        f"1. Установить лимит токенов в день\n"
        f"2. Установить лимит запросов в день"
    )
    btn = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Лимит токенов", callback_data="admin_set_max_tokens"),
                InlineKeyboardButton(text="📝 Лимит запросов", callback_data="admin_set_max_requests"),
            ]
        ]
    )
    await callback.message.edit_text(text, reply_markup=btn)


@router.callback_query(F.data == "admin_set_max_tokens")
async def admin_set_max_tokens_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите максимальное количество токенов в день (например 100000):"
    )
    await state.set_state(AdminStates.waiting_max_tokens)


@router.message(AdminStates.waiting_max_tokens, F.text)
async def admin_save_max_tokens(message: Message, state: FSMContext):
    try:
        val = int(message.text.strip())
        await set_config("max_daily_tokens", str(val))
        await state.clear()
        await message.answer(f"✅ Лимит токенов установлен: {val}", reply_markup=admin_menu())
    except ValueError:
        await message.answer("❌ Введите число.")


@router.callback_query(F.data == "admin_set_max_requests")
async def admin_set_max_requests_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите максимальное количество запросов в день (например 500):"
    )
    await state.set_state(AdminStates.waiting_max_requests)


@router.message(AdminStates.waiting_max_requests, F.text)
async def admin_save_max_requests(message: Message, state: FSMContext):
    try:
        val = int(message.text.strip())
        await set_config("max_daily_requests", str(val))
        await state.clear()
        await message.answer(f"✅ Лимит запросов установлен: {val}", reply_markup=admin_menu())
    except ValueError:
        await message.answer("❌ Введите число.")


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    usage = await get_api_usage(7)
    if not usage:
        await callback.message.edit_text("📊 Статистика пока пуста.")
        return

    lines = ["📊 *Статистика API (последние 7 дней):*\n"]
    total_tokens = 0
    total_requests = 0
    for row in usage:
        lines.append(f"  {row['date']}: {row['tokens_used']} токенов, {row['requests_count']} запросов")
        total_tokens += row["tokens_used"]
        total_requests += row["requests_count"]
    lines.append(f"\n📈 *Итого:* {total_tokens} токенов, {total_requests} запросов")
    await callback.message.edit_text("\n".join(lines))


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_prompt(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(
        "📨 Отправьте сообщение для рассылки всем пользователям (или /cancel для отмены):"
    )
    await state.set_state(AdminStates.waiting_broadcast)


@router.message(AdminStates.waiting_broadcast, Command("cancel"))
async def cancel_broadcast(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено.", reply_markup=admin_menu())


@router.message(AdminStates.waiting_broadcast)
async def admin_send_broadcast(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ Рассылка отправлена!")
