# Импорт необходимых модулей из библиотеки python-telegram-bot
from telegram import Update  # Для работы с входящими обновлениями (сообщениями)
from telegram.ext import (
    Application,  # Основной класс для создания бота
    CommandHandler,  # Обработчик команд (начинающихся с /)
    MessageHandler,  # Обработчик текстовых сообщений
    filters,  # Фильтры для обработки сообщений
    ContextTypes,  # Типы для работы с контекстом
    ConversationHandler,  # Для создания многоэтапных диалогов
)
from gigachat import GigaChat  # Для работы с API GigaChat

# Конфигурационные константы
BOT_TOKEN = "7961345416:AAGtoJgv38bkrJ6NBP1JB_JRlDmrF-Pye4Y"  # Токен вашего Telegram бота
GIGA_API_KEY = "NDE5YjEyZTgtZGM4MC00YTg4LWI4MzQtZWI1MTg0Y2JmODE5OmYyNGQ2YzFiLWQ3OTMtNDc5MC04ZmIwLWZjOTk3NTdlZjJlYQ=="  # API-ключ GigaChat

# Определение состояний для ConversationHandler
# Каждое состояние соответствует этапу диалога
(
    WAITING_FOR_PRODUCT,  # Ожидание названия товара для отзыва
    WAITING_FOR_FILTER_CATEGORY,  # Ожидание категории товара для фильтра
    WAITING_FOR_FILTER_PREFERENCES,  # Ожидание предпочтений для фильтра
    WAITING_FOR_FILTER_PRICE,  # Ожидание ценового диапазона
) = range(4)  # Присваиваем числа 0-3 для каждого состояния

# Инициализация клиента GigaChat с переданными учетными данными
# verify_ssl_certs=False отключает проверку SSL-сертификатов (не рекомендуется для продакшена)
giga = GigaChat(credentials=GIGA_API_KEY, verify_ssl_certs=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start - первое сообщение при запуске бота"""
    await update.message.reply_text(
        "👋 Привет! Я твой помощник по выбору и анализу товаров!\n\n"
        "Я могу:\n"
        "🔍 1. Анализировать товары (/otziv)\n"
        "🛒 2. Подбирать товары по фильтрам (/filter)\n\n"
        "Выбери нужную команду и я с радостью помогу! 😊"
    )

async def otziv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /otziv - начинает процесс создания отзыва"""
    await update.message.reply_text(
        "📝 Хочешь проанализировать товар? Отлично!\n"
        "Пришли мне название товара, например:\n"
        "'iPhone 15' или 'Xiaomi Redmi Note 12'\n\n"
        "Я подготовлю подробный обзор! 🔍✨"
    )
    return WAITING_FOR_PRODUCT  # Переводим бота в состояние ожидания товара

async def filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /filter - начинает процесс фильтрации товаров"""
    await update.message.reply_text(
        "🛍️ Давай подберем идеальный товар специально для тебя!\n\n"
        "Для начала укажи категорию товара, например:\n"
        "'смартфоны', 'ноутбуки', 'наушники' или 'фотоаппараты'\n\n"
        "Я готов помочь с выбором! 😊"
    )
    return WAITING_FOR_FILTER_CATEGORY  # Ожидаем категорию товара

async def handle_filter_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик введенной категории товара для фильтра"""
    # Сохраняем категорию в user_data для использования на следующих этапах
    context.user_data['category'] = update.message.text
    await update.message.reply_text(
        "👍 Отличный выбор! Теперь расскажи, каким должен быть твой идеальный товар?\n\n"
        "Например:\n"
        "'с хорошей камерой 📷', 'игровой 🎮', 'для работы 💼', 'с долгим аккумулятором 🔋'\n\n"
        "Чем подробнее опишешь, тем точнее будет подбор! 😉"
    )
    return WAITING_FOR_FILTER_PREFERENCES  # Переходим к ожиданию предпочтений

async def handle_filter_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик пожеланий к товару"""
    # Сохраняем предпочтения в user_data
    context.user_data['preferences'] = update.message.text
    await update.message.reply_text(
        "💵 Теперь укажи бюджет, который готов выделить на покупку.\n\n"
        "Напиши в формате:\n"
        "'10000-50000' или '20000-30000'\n\n"
        "Это поможет найти лучшие варианты в твоей ценовой категории! 💰"
    )
    return WAITING_FOR_FILTER_PRICE  # Ожидаем ввод ценового диапазона

async def handle_filter_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ценового диапазона и генерация результатов"""
    try:
        # Парсим введенный диапазон цен
        price_range = update.message.text.split('-')
        min_price = int(price_range[0].strip())  # Минимальная цена
        max_price = int(price_range[1].strip())  # Максимальная цена
        
        # Получаем сохраненные данные из контекста
        category = context.user_data.get('category', '')
        preferences = context.user_data.get('preferences', '')
        
        # Формируем подробный запрос к GigaChat
        prompt = (
            f"Подбери 3-5 конкретных моделей товаров в категории '{category}' "
            f"со следующими характеристиками: {preferences} "
            f"и в ценовом диапазоне {min_price}-{max_price} рублей.\n\n"
            "Предоставь результат в формате:\n"
            "1. 🏷️ Название модели\n"
            "2. 📋 Основные характеристики\n"
            "3. 💰 Средняя цена\n"
            "4. 🛒 Где можно купить (маркетплейсы)\n"
            "5. ⭐ Рейтинг (если есть)\n\n"
            "Будь максимально конкретным и предоставляй актуальную информацию."
            "В этом сообщении должно быть меньше 2500 символов"
        )
        
        # Отправляем запрос к GigaChat API
        response = giga.chat(prompt)
        # Отправляем пользователю ответ от GigaChat с приветственным сообщением
        await update.message.reply_text(
            "🎉 Вот что я нашел специально для тебя!\n\n"
            "🔍 Результаты подбора по твоим критериям:\n\n" +
            response.choices[0].message.content +
            "\n\nЕсли хочешь уточнить параметры - просто начни заново (/filter) 😊"
        )
        
    except (ValueError, IndexError):
        # Обработка ошибки неверного формата цены
        await update.message.reply_text(
            "❌ Ой, кажется, ты ввел цену в неправильном формате.\n\n"
            "Пожалуйста, укажи диапазон так:\n"
            "'10000-50000' или '20000-30000'\n\n"
            "Давай попробуем еще раз! 💪"
        )
        return WAITING_FOR_FILTER_PRICE  # Повторно запрашиваем цену
    except Exception as e:
        # Обработка всех остальных ошибок
        await update.message.reply_text(
            "😔 Упс! Что-то пошло не так...\n"
            f"Ошибка: {e}\n\n"
            "Попробуй начать заново (/filter) или напиши разработчику!"
        )
    
    return ConversationHandler.END  # Завершаем диалог

async def handle_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик названия товара для генерации отзыва"""
    tovar = update.message.text  # Получаем текст сообщения (название товара)
    
    try:
        # Формируем запрос к GigaChat на генерацию отзыва
        response = giga.chat(
            f"Напиши подробный отзыв на товар '{tovar}'. Включи следующие разделы:\n"
            "🔹 Основные преимущества\n"
            "🔹 Недостатки и слабые стороны\n"
            "🔹 Лучшие аналоги с сравнением\n"
            "🔹 Итоговую оценку в формате '⭐⭐⭐⭐☆ (4.5/5)'\n\n"
            "Отзыв должен быть полезным, объективным и хорошо структурированным,а так же в нем должно быть меньше 2500 символов"
        )
        # Отправляем сгенерированный отзыв пользователю с приветственным сообщением
        await update.message.reply_text(
            "📊 Вот мой подробный анализ товара:\n\n" +
            response.choices[0].message.content +
            "\n\nНадеюсь, эта информация была полезной! 😊\n"
            "Если хочешь проанализировать другой товар - просто введи его название или нажми /otziv"
        )
    except Exception as e:
        # Обработка ошибок
        await update.message.reply_text(
            "😕 Упс! При анализе товара произошла ошибка.\n"
            f"Техническая информация: {e}\n\n"
            "Попробуй еще раз или обратись к разработчику!"
        )
    
    return ConversationHandler.END  # Завершаем диалог

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды отмены (/cancel)"""
    await update.message.reply_text(
        "🚫 Операция отменена.\n\n"
        "Если хочешь начать заново, просто выбери одну из команд:\n"
        "/otziv - для анализа товара\n"
        "/filter - для подбора товаров\n\n"
        "Я всегда готов помочь! 😊"
    )
    return ConversationHandler.END  # Завершаем текущий диалог

if __name__ == "__main__":
    # Создаем экземпляр Application с нашим токеном
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Настраиваем ConversationHandler для команды /otziv
    otziv_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("otziv", otziv_command)],  # Точка входа - команда /otziv
        states={
            WAITING_FOR_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product)],
        },  # Состояние ожидания товара
        fallbacks=[CommandHandler("cancel", cancel)],  # Команда для отмены
    )
    
    # Настраиваем ConversationHandler для команды /filter
    filter_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("filter", filter_command)],  # Точка входа - команда /filter
        states={
            WAITING_FOR_FILTER_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_filter_category)],
            WAITING_FOR_FILTER_PREFERENCES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_filter_preferences)],
            WAITING_FOR_FILTER_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_filter_price)],
        },  # Все состояния для фильтра
        fallbacks=[CommandHandler("cancel", cancel)],  # Команда для отмены
    )
    
    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))  # Обработчик /start
    app.add_handler(otziv_conv_handler)  # Обработчик цепочки /otziv
    app.add_handler(filter_conv_handler)  # Обработчик цепочки /filter
    
    print("🤖 Бот успешно запущен и готов к работе!")  # Сообщение в консоль при запуске
    app.run_polling()  # Запускаем бота в режиме polling