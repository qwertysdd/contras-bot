import telebot
from telebot import types
from telebot.types import Message
import yadisk
import calendar
import time as time_module
import re
from datetime import datetime, date, time as datetime_time
import os

from telebot import apihelper

apihelper.API_TIMEOUT = 60
apihelper.CONNECT_TIMEOUT = 30
apihelper.READ_TIMEOUT = 60
apihelper.RETRY_ON_ERROR = True
apihelper.RETRY_ATTEMPTS = 5

BOT_TOKEN = '8517851908:AAHe-Ynao2YqwV49m7cvk1VbIbDsrEvv4wE'
YANDEX_TOKEN = 'y0__xDNjJXLARisnT4g84q_xhbytwlTUZfqPlPbTcoln1J-W5kjnA'
CHANNEL_USERNAME = 'contras_go'
CHANNEL_ID = -1001708721955
DISK_ROOT_PATH = '/ИГРЫ/'

CALENDAR_PREFIX = "calendar_"
TIME_PREFIX = "time_"

PLATFORMS = {
    "DOOM_LAB": {"prefix": "D", "name": "DOOM_LAB"},
    "CS_MANSION": {"prefix": "M", "name": "CS_MANSION"}
}

bot = telebot.TeleBot(BOT_TOKEN)
y = yadisk.YaDisk(token=YANDEX_TOKEN)

states = {}

# Русские названия месяцев
RUS_MONTHS = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]


def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator', 'restricted']
    except:
        return False


def build_calendar(year, month):
    markup = types.InlineKeyboardMarkup(row_width=7)
    markup.row(types.InlineKeyboardButton(
        f"{RUS_MONTHS[month - 1]} {year}", callback_data="ignore"))

    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    markup.row(*[types.InlineKeyboardButton(d, callback_data="ignore") for d in days])

    cal = calendar.monthcalendar(year, month)
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(types.InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                row.append(types.InlineKeyboardButton(str(day), callback_data=f"{CALENDAR_PREFIX}{year}_{month}_{day}"))
        markup.row(*row)

    prev_m = month - 1 if month > 1 else 12
    prev_y = year if month > 1 else year - 1
    next_m = month + 1 if month < 12 else 1
    next_y = year if month < 12 else year + 1

    markup.row(
        types.InlineKeyboardButton("<< Пред. месяц", callback_data=f"{CALENDAR_PREFIX}{prev_y}_{prev_m}_0"),
        types.InlineKeyboardButton("След. месяц >>", callback_data=f"{CALENDAR_PREFIX}{next_y}_{next_m}_0")
    )
    return markup


@bot.message_handler(commands=['start'])
def start(message: Message):
    user_id = message.from_user.id
    states.pop(user_id, None)

    photo_path = "platforms.jpg"

    inline_markup = types.InlineKeyboardMarkup(row_width=2)
    inline_markup.add(
        types.InlineKeyboardButton("CS_MANSION (Пейнтбол)", callback_data="platform_CS_MANSION"),
        types.InlineKeyboardButton("DOOM_LAB (Лазертаг)", callback_data="platform_DOOM_LAB")
    )

    if not check_subscription(user_id):
        caption = "Чтобы получить фотографии, сначала подпишитесь на канал 👇\n\nЗатем выберите площадку:"
    else:
        caption = "Выберите площадку:"

    if os.path.exists(photo_path):
        try:
            with open(photo_path, 'rb') as photo:
                bot.send_photo(
                    message.chat.id,
                    photo,
                    caption=caption,
                    reply_markup=inline_markup
                )
        except Exception as e:
            print(f"[ERROR] Ошибка отправки фото: {e}")
            bot.send_message(
                message.chat.id,
                caption + "\n(Фото не загрузилось, но можно выбрать площадку)",
                reply_markup=inline_markup
            )
    else:
        bot.send_message(
            message.chat.id,
            caption,
            reply_markup=inline_markup
        )


@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    user_id = call.from_user.id
    if check_subscription(user_id):
        bot.answer_callback_query(call.id, "Подписка подтверждена! ✅")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        photo_path = "platforms.jpg"

        inline_markup = types.InlineKeyboardMarkup(row_width=2)
        inline_markup.add(
            types.InlineKeyboardButton("CS_MANSION (Пейнтбол)", callback_data="platform_CS_MANSION"),
            types.InlineKeyboardButton("DOOM_LAB (Лазертаг)", callback_data="platform_DOOM_LAB")
        )

        caption = "Выберите площадку:"

        if os.path.exists(photo_path):
            try:
                with open(photo_path, 'rb') as photo:
                    bot.send_photo(
                        call.message.chat.id,
                        photo,
                        caption=caption,
                        reply_markup=inline_markup
                    )
            except Exception as e:
                print(f"[ERROR] Ошибка отправки фото после подписки: {e}")
                bot.send_message(
                    call.message.chat.id,
                    caption + "\n(Фото не загрузилось, но можно выбрать площадку)",
                    reply_markup=inline_markup
                )
        else:
            bot.send_message(
                call.message.chat.id,
                caption,
                reply_markup=inline_markup
            )
    else:
        bot.answer_callback_query(call.id, "Вы ещё не подписаны.", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith("platform_"))
def platform_callback(call):
    user_id = call.from_user.id
    platform_key = call.data.replace("platform_", "")

    if platform_key not in PLATFORMS:
        bot.answer_callback_query(call.id, "Неизвестная площадка", show_alert=True)
        return

    states[user_id] = {'platform': platform_key}

    today = date.today()
    markup = build_calendar(today.year, today.month)
    bot.send_message(
        call.message.chat.id,
        f"Выбрана площадка: {PLATFORMS[platform_key]['name']}\n"
        f"Выберите день в {RUS_MONTHS[today.month - 1]} {today.year}:",
        reply_markup=markup
    )
    bot.answer_callback_query(call.id, f"Выбрано: {PLATFORMS[platform_key]['name']}")


@bot.callback_query_handler(func=lambda call: call.data.startswith(CALENDAR_PREFIX))
def calendar_callback(call):
    user_id = call.from_user.id
    if user_id not in states or 'platform' not in states[user_id]:
        bot.answer_callback_query(call.id, "Сначала выберите площадку", show_alert=True)
        return

    parts = call.data.split("_")
    if len(parts) != 4:
        bot.answer_callback_query(call.id, "Ошибка календаря", show_alert=True)
        return

    year = int(parts[1])
    month = int(parts[2])
    day = int(parts[3])

    if day == 0:
        # Переход на другой месяц
        try:
            bot.edit_message_text(
                text=f"Выберите день в {RUS_MONTHS[month - 1]} {year}:",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=build_calendar(year, month)
            )
        except Exception:
            pass  # если сообщение уже было удалено или не редактируемо — просто игнорируем
        bot.answer_callback_query(call.id)
        return

    try:
        selected_date = date(year, month, day)
    except ValueError:
        bot.answer_callback_query(call.id, "Неверная дата", show_alert=True)
        return

    states[user_id]['date'] = selected_date

    bot.send_message(
        call.message.chat.id,
        f"Выбрана площадка: {PLATFORMS[states[user_id]['platform']]['name']}\n"
        f"Вы выбрали: {selected_date.strftime('%d.%m.%Y')}\n"
        "Ищем доступные времена..."
    )

    times = get_available_times(year, month, day, states[user_id]['platform'])

    if not times:
        bot.send_message(call.message.chat.id, "За этот день игр не найдено.\nПопробуйте другую дату.")
        return

    markup = types.InlineKeyboardMarkup(row_width=4)
    for i in range(0, len(times), 4):
        row = times[i:i + 4]
        markup.row(*[types.InlineKeyboardButton(t, callback_data=f"{TIME_PREFIX}{t}") for t in row])

    bot.send_message(
        call.message.chat.id,
        f"Доступные времена на {selected_date.strftime('%d.%m.%Y')}:",
        reply_markup=markup
    )

    bot.answer_callback_query(call.id)


# Остальные функции (get_available_times, time_callback, find_and_share_folder) остаются без изменений
# Копировать их из твоего кода без изменений

def get_available_times(year: int, month: int, day: int, platform_key: str):
    yy = str(year)[-2:]
    mm = f"{month:02d}"
    dd = f"{day:02d}"

    prefix = PLATFORMS[platform_key]["prefix"]
    year_path = f"{DISK_ROOT_PATH}{platform_key}/{year}/"

    print(f"[DEBUG] get_available_times: площадка={platform_key}, путь к году={year_path}")

    if not y.exists(year_path):
        print(f"[DEBUG] Путь {year_path} не найден")
        return []

    pattern = re.compile(rf'^{prefix}(\d{{2}})(\d{{2}})(\d{{2}})(\d{{2}})(\d{{2}})_(\d{{1,3}})$')

    times = set()

    try:
        year_items = list(y.listdir(year_path))
        print(f"[DEBUG] В году найдено элементов: {len(year_items)}")
        print(f"[DEBUG] Имена папок в году: {[item.name for item in year_items]}")

        for item in year_items:
            if item.type != 'dir':
                continue

            month_folder_name = item.name
            month_path = f"{year_path}{month_folder_name}/"
            print(f"[DEBUG] Заходим в месяц: {month_folder_name} → путь={month_path}")

            try:
                month_items = list(y.listdir(month_path))
                print(f"[DEBUG] В месяце '{month_folder_name}' найдено элементов: {len(month_items)}")
                print(f"[DEBUG] Имена игр в месяце: {[sub.name for sub in month_items if sub.type == 'dir']}")

                for game_item in month_items:
                    if game_item.type != 'dir':
                        continue

                    game_name = game_item.name
                    print(f"[DEBUG] Проверяем игру: {game_name}")

                    match = pattern.match(game_name)
                    if match:
                        f_yy, f_mm, f_dd, f_hh, f_mm_time, f_n = match.groups()
                        print(f"[DEBUG] Разбор игры {game_name}: {f_yy}-{f_mm}-{f_dd} {f_hh}:{f_mm_time}, №={f_n}")

                        if f_yy == yy and f_mm == mm and f_dd == dd:
                            time_str = f"{f_hh}:{f_mm_time}"
                            times.add(time_str)
                            print(f"[DEBUG] Добавлено время: {time_str}")
                    else:
                        print(f"[DEBUG] Игра {game_name} не подошла под регулярку")

            except Exception as e:
                print(f"[ERROR] Ошибка чтения месяца '{month_folder_name}': {e}")
                continue

    except Exception as e:
        print(f"[ERROR] Ошибка чтения года {year} ({platform_key}): {e}")

    print(f"[DEBUG] Найденные времена за день: {sorted(times)}")
    return sorted(times)


@bot.callback_query_handler(func=lambda call: call.data.startswith(TIME_PREFIX))
def time_callback(call):
    user_id = call.from_user.id
    if user_id not in states or 'platform' not in states[user_id] or 'date' not in states[user_id]:
        bot.answer_callback_query(call.id, "Сессия истекла. Нажмите /start")
        return

    time_str = call.data[len(TIME_PREFIX):]
    try:
        h_str, m_str = time_str.split(":")
        h = int(h_str)
        m = int(m_str)
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError("Неверный диапазон времени")
    except Exception as e:
        print(f"[ERROR] Ошибка парсинга времени '{time_str}': {e}")
        bot.answer_callback_query(call.id, "Ошибка времени")
        return

    selected_date = states[user_id]['date']
    platform_key = states[user_id]['platform']

    try:
        game_time = datetime_time(h, m)
        game_dt = datetime.combine(selected_date, game_time)
        print(f"[DEBUG] Время успешно создано: {game_time}, дата+время: {game_dt}")
    except Exception as e:
        print(f"[ERROR] Ошибка создания времени h={h}, m={m}: {e}")
        bot.answer_callback_query(call.id, "Ошибка даты/времени")
        return

    data = {
        'year': selected_date.year,
        'month': selected_date.month,
        'day': selected_date.day,
        'hours': h,
        'minutes': m,
        'game_dt': game_dt,
        'platform': platform_key,
        'date': selected_date
    }

    find_and_share_folder(call.message, data)
    states.pop(user_id, None)

    try:
        bot.edit_message_text("Ищем вашу папку...", call.message.chat.id, call.message.message_id)
    except:
        pass


def find_and_share_folder(message: Message, data):
    selected_date = data['date']

    input_datetime = datetime(
        selected_date.year,
        selected_date.month,
        selected_date.day,
        data['hours'],
        data['minutes']
    )

    year_str = str(data['year'])
    yy = year_str[-2:]
    mm = f"{data['month']:02d}"
    dd = f"{data['day']:02d}"

    platform_key = data['platform']
    prefix = PLATFORMS[platform_key]["prefix"]

    year_path = f"{DISK_ROOT_PATH}{platform_key}/{year_str}/"

    print(f"[DEBUG] find_and_share_folder: площадка={platform_key}, путь к году={year_path}")

    if not y.exists(year_path):
        print(f"[DEBUG] Путь {year_path} не найден")
        bot.send_message(message.chat.id, f"За {year_str} год на {PLATFORMS[platform_key]['name']} игр не найдено.")
        return

    pattern = re.compile(rf'^{prefix}(\d{{2}})(\d{{2}})(\d{{2}})(\d{{2}})(\d{{2}})_(\d{{1,3}})$')

    candidates = []

    try:
        year_items = list(y.listdir(year_path))
        print(f"[DEBUG] В году найдено элементов: {len(year_items)}")
        print(f"[DEBUG] Имена папок в году: {[item.name for item in year_items]}")

        for item in year_items:
            if item.type != 'dir':
                continue

            month_folder_name = item.name
            month_path = f"{year_path}{month_folder_name}/"
            print(f"[DEBUG] Заходим в месяц: {month_folder_name} → путь={month_path}")

            try:
                month_items = list(y.listdir(month_path))
                print(f"[DEBUG] В месяце '{month_folder_name}' найдено элементов: {len(month_items)}")
                print(f"[DEBUG] Имена игр в месяце: {[sub.name for sub in month_items if sub.type == 'dir']}")

                for game_item in month_items:
                    if game_item.type != 'dir':
                        continue

                    game_name = game_item.name
                    print(f"[DEBUG] Проверяем игру: {game_name}")

                    match = pattern.match(game_name)
                    if match:
                        f_yy, f_mm, f_dd, f_hh, f_mm_time, f_n = match.groups()
                        print(f"[DEBUG] Разбор игры {game_name}: {f_yy}-{f_mm}-{f_dd} {f_hh}:{f_mm_time}, №={f_n}")

                        if f_yy == yy and f_mm == mm and f_dd == dd:
                            try:
                                hh = int(f_hh)
                                mm_time = int(f_mm_time)

                                game_datetime = datetime(
                                    selected_date.year,
                                    selected_date.month,
                                    selected_date.day,
                                    hh,
                                    mm_time
                                )

                                delta = abs((input_datetime - game_datetime).total_seconds() / 60)
                                print(f"[DEBUG] Совпадение! Δ={delta} мин (hh={hh}, mm={mm_time})")

                                if delta <= 30:
                                    full_path = f"{month_path}{game_name}"
                                    candidates.append((game_name, delta, full_path))
                                    print(f"[DEBUG] Добавлена кандидат: {full_path}")
                            except ValueError as ve:
                                print(f"[DEBUG] Ошибка преобразования времени в {game_name}: {ve}")
                    else:
                        print(f"[DEBUG] Игра {game_name} не подошла под регулярку")

            except Exception as e:
                print(f"[ERROR] Ошибка чтения месяца '{month_folder_name}': {e}")
                continue

    except Exception as e:
        print(f"[ERROR] Ошибка года {year_str} ({platform_key}): {e}")
        bot.send_message(message.chat.id,
                         f"Ошибка доступа к папке {PLATFORMS[platform_key]['name']} за {year_str} год.")
        return

    if not candidates:
        bot.send_message(message.chat.id,
                         f"Игра в указанное время (±30 минут) на {PLATFORMS[platform_key]['name']} не найдена.")
        return

    closest = min(candidates, key=lambda x: x[1])
    full_path = closest[2]

    try:
        print(f"[DEBUG] Публикация: {full_path}")
        y.publish(full_path)
        time_module.sleep(3)

        meta = y.get_meta(full_path, fields=['public_url', 'public_key'])

        url = (
            meta.public_url if hasattr(meta, 'public_url') and meta.public_url else
            (f"https://disk.yandex.ru/d/{meta.public_key}" if hasattr(meta, 'public_key') and meta.public_key else
             f"https://disk.yandex.ru/client/disk{full_path}")
        )

        bot.send_message(message.chat.id,
                         f"Вот ваша папка с фотографиями ({PLATFORMS[platform_key]['name']}):\n\n{url}")
    except Exception as e:
        print(f"[ERROR] Ошибка публикации: {e}")
        bot.send_message(message.chat.id, "Не удалось получить ссылку. Опубликуйте папку вручную.")


if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)