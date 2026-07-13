from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.types import Message, CallbackQuery

from database import get_config, save_conversation, track_api_usage, add_order, get_total_usage_today
from keyboards import (
    main_menu, exit_ai_keyboard,
    cancel_kb, web_purpose_kb, bot_purpose_kb, gps_type_kb,
    design_kb, need_integrations_kb, budget_kb, gps_budget_kb, confirm_kb,
)
from services.groq import chat_completion

router = Router()


PRICE_TABLE = {
    "web_landing":     {"label": "Лендинг", "min": 150, "max": 350},
    "web_shop":        {"label": "Интернет-магазин", "min": 400, "max": 1200},
    "web_catalog":     {"label": "Сайт-каталог", "min": 250, "max": 600},
    "web_corporate":   {"label": "Корпоративный сайт", "min": 300, "max": 800},
    "bot_info":        {"label": "Информационный / FAQ", "min": 80, "max": 200},
    "bot_catalog":     {"label": "Каталог товаров", "min": 150, "max": 400},
    "bot_shop":        {"label": "Магазин с оплатой", "min": 250, "max": 700},
    "bot_ai":          {"label": "AI-ассистент", "min": 400, "max": 1200},
    "gps_personal":    {"label": "Личный автомобиль (аренда)", "min": 10, "max": 30},
    "gps_fleet_small": {"label": "Автопарк (2-5 машин)", "min": 30, "max": 80},
    "gps_fleet_big":   {"label": "Автопарк (5-10 машин)", "min": 50, "max": 150},
    "gps_equipment":   {"label": "Оборудование / Активы", "min": 15, "max": 50},
}

DESIGN_PRICES = {
    "scratch": {"label": "Дизайн с нуля", "min": 80, "max": 200},
    "refs":    {"label": "По референсам", "min": 0, "max": 50},
}

INTEGRATION_PRICES = {
    "payment":  {"label": "Приём платежей", "min": 100, "max": 300},
    "crm":      {"label": "CRM система", "min": 100, "max": 250},
    "database": {"label": "База данных", "min": 50, "max": 150},
    "ai":       {"label": "AI / ChatGPT", "min": 200, "max": 500},
    "mailing":  {"label": "Рассылки / Email", "min": 50, "max": 150},
    "none":     {"label": "Без доп. интеграций", "min": 0, "max": 0},
}

LABEL_MAP = {
    "obudget_30": "$10-30",
    "obudget_80": "$30-80",
    "obudget_100": "до $100",
    "obudget_150": "$80+",
    "obudget_300": "до $300",
    "obudget_600": "$300-600",
    "obudget_1000": "$600-1000",
    "obudget_2000": "$1000+",
    "obudget_unknown": "Не знаю / Обсудить",
}

INT_LABEL_MAP = {
    "payment": "💳 Оплата",
    "crm": "📊 CRM",
    "database": "🗄️ БД",
    "ai": "🤖 AI",
    "mailing": "📨 Рассылки",
    "none": "—",
}


def calc_price(data: dict) -> tuple:
    purpose = data.get("purpose", "")
    base = PRICE_TABLE.get(purpose, {"label": "—", "min": 0, "max": 0})
    min_p = base["min"]
    max_p = base["max"]
    items = [f"• {base['label']}: ${base['min']} – ${base['max']}"]

    design = data.get("design", "")
    if design:
        d = DESIGN_PRICES.get(design, {"label": "", "min": 0, "max": 0})
        min_p += d["min"]
        max_p += d["max"]
        items.append(f"• {d['label']}: +${d['min']} – ${d['max']}")

    integration = data.get("integration", "")
    if integration:
        i = INTEGRATION_PRICES.get(integration, {"label": "", "min": 0, "max": 0})
        min_p += i["min"]
        max_p += i["max"]
        items.append(f"• {i['label']}: +${i['min']} – ${i['max']}")

    return min_p, max_p, items


class AIAssistState(StatesGroup):
    chatting = State()


class OrderState(StatesGroup):
    purpose = State()
    design = State()
    integration = State()
    budget = State()
    confirm = State()


# ── Start ────────────────────────────────────────────────────────────

@router.message(StateFilter(default_state), Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Добро пожаловать в IT-сервис Otabek (Джумаев Отабек)!\n\n"
        "🚀 Senior Full Stack Developer & Software Architect\n"
        "📍 Душанбе, Таджикистан\n\n"
        "Я помогаю с заказами:\n"
        "📱 Сайты (лендинги, интернет-магазины, каталоги)\n"
        "🤖 Telegram боты (магазины, ассистенты, с оплатой)\n"
        "📡 Установка GPS трекеров в Таджикистане\n"
        "💬 AI решения и интеграции\n\n"
        "🌟 Нажмите «Портфолио» чтобы увидеть мои проекты\n\n"
        "Выберите нужный пункт в меню ниже:",
        reply_markup=main_menu(),
    )


@router.message(StateFilter(default_state), F.text == "🌟 Портфолио")
async def portfolio(message: Message):
    await message.answer(
        "🌟 *Портфолио Otabek*\n\n"
        "👨‍💻 Senior Full Stack Developer | 5+ лет | 50+ проектов\n"
        "📍 Душанбе, Таджикистан\n\n"
        "🔧 *Технический стек:*\n"
        "Frontend: React, Next.js, TypeScript, Tailwind CSS\n"
        "Backend: Go, Python, Node.js, PostgreSQL, Redis, GraphQL\n"
        "DevOps: Docker, Kubernetes, AWS, Terraform, CI/CD\n"
        "AI: OpenAI, LangChain, TensorFlow, RAG, Vector DB\n\n"
        "🏆 *Избранные проекты:*\n\n"
        "1️⃣ *HighLoad E-Commerce Platform*\n"
        "   Микросервисный маркетплейс (100K+ RPS)\n"
        "   Go, Kafka, PostgreSQL, K8s, gRPC\n\n"
        "2️⃣ *AI Code Assistant*\n"
        "   VS Code extension с RAG-архитектурой\n"
        "   TypeScript, LangChain, Vector DB, OpenAI\n\n"
        "3️⃣ *Real-time Analytics Dashboard*\n"
        "   Дашборд для мониторинга метрик в реальном времени\n"
        "   React, D3.js, Node.js, ClickHouse, WebSocket\n\n"
        "📜 Сертификаты: AWS SA, Google Cloud Dev, TensorFlow\n\n"
        "💼 Открыт для сложных проектов и консультаций!\n"
        "📧 otabek.platform@gmail.com\n"
        "💬 @extayle\n"
        "📱 +992 02 880 7776\n"
        "🔗 GitHub: github.com/otabek-platform",
        reply_markup=main_menu(),
    )


@router.message(StateFilter(default_state), F.text == "📞 Контакты")
async def contacts(message: Message):
    await message.answer(
        "📞 *Свяжитесь со мной напрямую:*\n\n"
        "Otabek (Джумаев Отабек)\n"
        "Senior Full Stack Developer\n\n"
        "📧 Email: otabek.platform@gmail.com\n"
        "💬 Telegram: @extayle\n"
        "📱 WhatsApp/Phone: +992 02 880 7776\n"
        "🔗 GitHub: github.com/otabek-platform\n\n"
        "🌟 Портфолио: otabekportfolio.vercel.app",
        reply_markup=main_menu(),
    )


# ── Order flow: start ────────────────────────────────────────────────

@router.message(StateFilter(default_state), F.text == "📱 Заказать сайт")
async def order_website_start(message: Message, state: FSMContext):
    await state.update_data(project_type="website")
    await state.set_state(OrderState.purpose)
    await message.answer(
        "📱 *Заказ сайта*\n\n"
        "Для каких целей вам нужен сайт?",
        reply_markup=web_purpose_kb(),
    )


@router.message(StateFilter(default_state), F.text == "🤖 Заказать Telegram бота")
async def order_bot_start(message: Message, state: FSMContext):
    await state.update_data(project_type="bot")
    await state.set_state(OrderState.purpose)
    await message.answer(
        "🤖 *Заказ Telegram бота*\n\n"
        "Какой тип бота вам нужен?",
        reply_markup=bot_purpose_kb(),
    )


@router.message(StateFilter(default_state), F.text == "📡 Установка GPS трекера")
async def order_gps_start(message: Message, state: FSMContext):
    await state.update_data(project_type="gps")
    await state.set_state(OrderState.purpose)
    await message.answer(
        "📡 *GPS трекер (аренда)*\n\n"
        "Аренда GPS трекера от **$10/100 сомони** в месяц.\n"
        "Выберите тип:",
        reply_markup=gps_type_kb(),
    )


# ── Order flow: cancel / restart ────────────────────────────────────

@router.callback_query(F.data == "order_cancel")
async def order_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Заказ отменён.")
    await callback.message.answer(
        "Возвращайтесь, когда будете готовы!",
        reply_markup=main_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "order_restart")
async def order_restart(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    proj_type = data.get("project_type", "")
    await state.clear()

    prompts = {
        "website": ("📱 *Заказ сайта*\n\nДля каких целей?", web_purpose_kb()),
        "bot": ("🤖 *Заказ бота*\n\nКакой тип бота?", bot_purpose_kb()),
        "gps": ("📡 *GPS трекер*\n\nДля каких целей?", gps_type_kb()),
    }
    text, kb = prompts.get(proj_type, ("Выберите тип заказа из меню:", main_menu()))
    await state.update_data(project_type=proj_type)
    await state.set_state(OrderState.purpose)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# ── Order flow: purpose ─────────────────────────────────────────────

@router.callback_query(OrderState.purpose, F.data.startswith("opurpose_"))
async def purpose_chosen(callback: CallbackQuery, state: FSMContext):
    purpose = callback.data[len("opurpose_"):]
    await state.update_data(purpose=purpose)
    proj_type = purpose.split("_", 1)[0]

    if proj_type == "gps":
        await state.set_state(OrderState.budget)
        await callback.message.edit_text(
            "💰 *Бюджет*\n\nКакой бюджет рассматриваете?",
            reply_markup=gps_budget_kb(),
        )
    else:
        await state.set_state(OrderState.design)
        await callback.message.edit_text(
            "🎨 *Дизайн*\n\nУ вас есть готовый дизайн / макеты / референсы?",
            reply_markup=design_kb(),
        )
    await callback.answer()


# ── Order flow: design ──────────────────────────────────────────────

@router.callback_query(OrderState.design, F.data.startswith("odesign_"))
async def design_chosen(callback: CallbackQuery, state: FSMContext):
    design = callback.data[len("odesign_"):]
    await state.update_data(design=design)
    await state.set_state(OrderState.integration)
    await callback.message.edit_text(
        "🔌 *Интеграции*\n\n"
        "Какая интеграция нужна в первую очередь?\n"
        "(можно выбрать одну основную, остальное обсудите с Otabek)",
        reply_markup=need_integrations_kb(),
    )
    await callback.answer()


# ── Order flow: integration ─────────────────────────────────────────

@router.callback_query(OrderState.integration, F.data.startswith("oint_"))
async def integration_chosen(callback: CallbackQuery, state: FSMContext):
    integration = callback.data[len("oint_"):]
    await state.update_data(integration=integration)
    await state.set_state(OrderState.budget)
    await callback.message.edit_text(
        "💰 *Бюджет*\n\nКакой бюджет рассматриваете?",
        reply_markup=budget_kb(),
    )
    await callback.answer()


# ── Order flow: budget → summary ───────────────────────────────────

@router.callback_query(OrderState.budget, F.data.startswith("obudget_"))
async def budget_chosen(callback: CallbackQuery, state: FSMContext):
    budget = callback.data[len("obudget_"):]
    await state.update_data(budget=budget)
    data = await state.get_data()

    min_p, max_p, price_items = calc_price(data)
    budget_label = LABEL_MAP.get(f"obudget_{budget}", budget)

    parts = data.get("purpose", "").split("_", 1)
    proj_type = parts[0] if len(parts) > 1 else ""
    type_labels = {"web": "📱 Сайт", "bot": "🤖 Бот", "gps": "📡 GPS"}
    proj_label = type_labels.get(proj_type, "📋 Проект")

    int_key = data.get("integration", "")
    int_label = INT_LABEL_MAP.get(int_key, "—")

    design_key = data.get("design", "")
    design_label = {"scratch": "🎨 С нуля", "refs": "📐 По референсам"}.get(design_key, "—")

    summary = (
        f"📋 *Сводка заказа*\n\n"
        f"┌───────────────────\n"
        f"{proj_label}\n"
        f"{'─' * 20}\n"
    )
    for item in price_items:
        summary += f"  {item}\n"
    summary += (
        f"└───────────────────\n\n"
        f"🎨 Дизайн: {design_label if proj_type != 'gps' else '—'}\n"
        f"🔌 Интеграция: {int_label if proj_type != 'gps' else '—'}\n"
        f"💰 Ваш бюджет: {budget_label}\n\n"
        f"📊 *Примерная стоимость проекта:* ⬇️\n\n"
    )

    if min_p == 0 and max_p == 0:
        summary += "Точную оценку даст Otabek после обсуждения.\n"
    else:
        summary += f"  💵 **${min_p} – ${max_p}**\n\n"
        client_budget = {"30": 30, "80": 80, "100": 100, "150": 150,
                         "300": 300, "600": 600,
                         "1000": 1000, "2000": 2000}.get(budget, 0)
        if client_budget and client_budget < min_p:
            summary += (
                f"⚠️ Ваш бюджет (${client_budget}) ниже минимальной "
                f"оценки (${min_p}).\n"
                f"Otabek предложит оптимальное решение под ваш бюджет.\n"
            )
        elif client_budget and client_budget >= max_p:
            summary += f"✅ Ваш бюджет соответствует оценке. Otabek подтвердит финальную цену.\n"
        elif client_budget:
            summary += f"Otabek подберёт лучшее решение в рамках вашего бюджета.\n"

    summary += (
        "\n*Подтвердите заказ*, чтобы Otabek связался с вами."
    )

    await state.set_state(OrderState.confirm)
    await callback.message.edit_text(summary, reply_markup=confirm_kb())
    await callback.answer()


# ── Order flow: confirm ─────────────────────────────────────────────

@router.callback_query(OrderState.confirm, F.data == "order_confirm")
async def order_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    purpose = data.get("purpose", "")
    parts = purpose.split("_", 1)
    proj_type = parts[0] if len(parts) > 1 else "other"
    purpose_name = PRICE_TABLE.get(purpose, {}).get("label", purpose)

    design_key = data.get("design", "")
    design_label = {"scratch": "С нуля", "refs": "По референсам"}.get(design_key, "—")
    int_key = data.get("integration", "")
    int_label = INT_LABEL_MAP.get(int_key, "—")
    budget = data.get("budget", "unknown")
    budget_label = LABEL_MAP.get(f"obudget_{budget}", "Не указан")
    min_p, max_p, _ = calc_price(data)

    details = (
        f"Тип: {purpose_name}\n"
        f"Дизайн: {design_label}\n"
        f"Интеграция: {int_label}\n"
        f"Бюджет: {budget_label}\n"
        f"Оценка: ${min_p} – ${max_p}\n"
        f"Клиент: @{callback.from_user.username or '—'}\n"
        f"Имя: {callback.from_user.full_name}"
    )

    order_id = await add_order(
        user_id=callback.from_user.id,
        username=callback.from_user.username or "",
        full_name=callback.from_user.full_name,
        order_type=proj_type,
        details=details,
    )

    await state.clear()
    await callback.message.edit_text(
        f"✅ *Заказ #{order_id} создан!*\n\n"
        "Otabek свяжется с вами в ближайшее время "
        "для обсуждения деталей и старта работы.\n\n"
        "📧 otabek.platform@gmail.com\n"
        "💬 @extayle\n"
        "📱 +992 02 880 7776"
    )
    await callback.message.answer(
        "Спасибо за заказ! 🙌",
        reply_markup=main_menu(),
    )
    await _notify_admin(callback.bot, order_id, details)
    await callback.answer()


# ── AI Assistant ─────────────────────────────────────────────────────

@router.message(StateFilter(default_state), F.text == "💬 AI Ассистент")
async def ai_assist_start(message: Message, state: FSMContext):
    api_key = await get_config("groq_api_key")
    if not api_key:
        await message.answer(
            "❌ AI ассистент временно недоступен. Попробуйте позже или свяжитесь напрямую:\n"
            "📧 otabek.platform@gmail.com\n💬 @extayle",
            reply_markup=main_menu(),
        )
        return

    limits = await _check_limits()
    if limits["blocked"]:
        await message.answer(
            "❌ Лимит использования AI ассистента на сегодня исчерпан. "
            "Свяжитесь напрямую:\n📧 otabek.platform@gmail.com\n💬 @extayle",
            reply_markup=main_menu(),
        )
        return

    await state.set_state(AIAssistState.chatting)
    await state.update_data(messages=[])
    await message.answer(
        "🤖 Привет! Я AI-ассистент Otabek.\n\n"
        "Расскажите, что вам нужно:\n"
        "• Сайт\n• Telegram бот\n• GPS трекер\n• Другое IT-решение\n\n"
        "Я соберу все детали и передам заказ.\n"
        "Напишите /exit чтобы выйти из режима ассистента.",
        reply_markup=exit_ai_keyboard(),
    )


@router.message(AIAssistState.chatting, Command("exit"))
async def ai_assist_exit(message: Message, state: FSMContext):
    data = await state.get_data()
    msgs = data.get("messages", [])
    if msgs:
        await save_conversation(message.from_user.id, msgs)
    await state.clear()
    await message.answer(
        "Вы вышли из режима AI ассистента. Если хотите сделать заказ позже — просто напишите!",
        reply_markup=main_menu(),
    )


@router.message(AIAssistState.chatting, F.text == "🚪 Выйти из AI чата")
async def ai_assist_exit_button(message: Message, state: FSMContext):
    data = await state.get_data()
    msgs = data.get("messages", [])
    if msgs:
        await save_conversation(message.from_user.id, msgs)
    await state.clear()
    await message.answer(
        "Вы вышли из режима AI ассистента.",
        reply_markup=main_menu(),
    )


@router.message(AIAssistState.chatting)
async def ai_assist_chat(message: Message, state: FSMContext):
    api_key = await get_config("groq_api_key")
    if not api_key:
        await message.answer("❌ AI ассистент недоступен. Используйте /exit.")
        return

    limits = await _check_limits()
    if limits["blocked"]:
        await message.answer(
            "❌ Дневной лимит исчерпан. Ваш запрос сохранён. Свяжитесь напрямую:\n"
            "📧 otabek.platform@gmail.com\n💬 @extayle"
        )
        await state.clear()
        return

    data = await state.get_data()
    msgs: list = data.get("messages", [])
    msgs.append({"role": "user", "content": message.text})

    try:
        await message.answer("⏳ Думаю...")
        reply, tokens = await chat_completion(api_key, msgs)
    except Exception as e:
        await message.answer(
            f"⚠️ Ошибка: {e}\n\nПопробуйте позже или свяжитесь напрямую:\n"
            "📧 otabek.platform@gmail.com\n💬 @extayle"
        )
        return

    msgs.append({"role": "assistant", "content": reply})
    await state.update_data(messages=msgs)
    await track_api_usage(tokens)
    await message.answer(reply, reply_markup=exit_ai_keyboard())

    if "otabek.platform@gmail.com" in reply and "@extayle" in reply:
        details = (
            f"Клиент: @{message.from_user.username or 'нет'}\n"
            f"Имя: {message.from_user.full_name}\n"
            f"История:\n" + "\n".join(
                f"{'🤖' if m['role'] == 'assistant' else '👤'}: {m['content'][:200]}"
                for m in msgs
            )
        )
        order_id = await add_order(
            user_id=message.from_user.id,
            username=message.from_user.username or "",
            full_name=message.from_user.full_name,
            order_type="ai_assist",
            details=details,
        )
        await save_conversation(message.from_user.id, msgs)
        await state.clear()
        await message.answer(
            f"✅ Заказ #{order_id} передан Otabek! Он свяжется с вами в ближайшее время.",
            reply_markup=main_menu(),
        )
        await _notify_admin(message.bot, order_id, details)

    limits = await _check_limits()
    from config import ADMIN_IDS
    if limits["warning"] and message.from_user.id in ADMIN_IDS:
        await message.answer(f"⚠️ Внимание: {limits['warning']}")


# ── helpers ──────────────────────────────────────────────────────────

async def _check_limits() -> dict:
    max_daily_tokens_str = await get_config("max_daily_tokens")
    max_daily_requests_str = await get_config("max_daily_requests")
    max_daily_tokens = int(max_daily_tokens_str) if max_daily_tokens_str else 100000
    max_daily_requests = int(max_daily_requests_str) if max_daily_requests_str else 500
    usage = await get_total_usage_today()

    result = {"blocked": False, "warning": None}
    if usage["tokens"] >= max_daily_tokens or usage["requests"] >= max_daily_requests:
        result["blocked"] = True
    elif usage["tokens"] >= max_daily_tokens * 0.8:
        result["warning"] = f"Использовано {usage['tokens']}/{max_daily_tokens} токенов сегодня"
    elif usage["requests"] >= max_daily_requests * 0.8:
        result["warning"] = f"Использовано {usage['requests']}/{max_daily_requests} запросов сегодня"
    return result


async def _notify_admin(bot, order_id: int, details: str):
    from config import ADMIN_IDS
    text = (
        f"🆕 *Новый заказ!* #{order_id}\n\n"
        f"{details}\n\n"
        f"Используйте /admin для управления."
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text)
        except Exception:
            pass
