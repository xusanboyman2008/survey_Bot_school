import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.types import Message, CallbackQuery

from database import init, create_survey, create_user, get_survey
from word import  create_survey_docx

dp = Dispatcher()
bot = Bot(token=os.environ['TOKEN'])


class Survey(StatesGroup):
    first_name = State()
    last_name = State()
    subjects = State()
    place = State()
    date = State()
    weekdays = State()
    education_name = State()
    classroom = State()
    test = State()


def keyboard_subject(subject):
    subjects = ['Ingilis tili', 'Rus tili', 'Arab tili', 'Kikboksing/box', 'Sport zal', 'Musiqa', 'Informatika','Kores tili','Matimatika','Ona tili/adabiyot','Tarix','Oromgoh']
    keyboard = []

    row = []
    for i in subjects:
        if i not in subject:
            button_text = i
            callback = f"s_{i}_add"
        else:
            button_text = f'✅ {i}'
            callback = f"s_{i}_remove"

        row.append(InlineKeyboardButton(text=button_text, callback_data=callback))

        if len(row) == 3:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)
    if not subject:
        keyboard.append([InlineKeyboardButton(text='Yozgi ta`tilda xech qayerga bormayman', callback_data='Done_none')])
    keyboard.append([InlineKeyboardButton(text='Qolda fanni qoshish', callback_data='add_subject')])
    if subject:
        keyboard.append([InlineKeyboardButton(text='✅ Tasdiqlash', callback_data='Done')])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def classroom_keyboard(page=1, grade=''):
    letters = ['A', 'B', 'V']
    # Set number based on page
    number = 3 if page == 1 else 6 if page == 2 else 11
    keyboard = []
    row = []

    # Loop through letters and numbers, building buttons
    for i in letters:
        for j in range(number - 2, number + 1):
            grade_str = f"{j}{i}"
            if grade_str == grade:
                btn = InlineKeyboardButton(text=f'✅ {grade_str}', callback_data=f'g_{grade_str}_{page}')
            else:
                btn = InlineKeyboardButton(text=grade_str, callback_data=f'g_{grade_str}_{page}')
            row.append(btn)
            if len(row) == 3:
                keyboard.append(row)
                row = []

    # Add any remaining buttons
    if row:
        keyboard.append(row)

    # Navigation buttons
    keyboard.append([
        InlineKeyboardButton(text='⬅️', callback_data=f'g_back_{3 if page == 1 else page - 1}_{grade}'),
        InlineKeyboardButton(text='➡️', callback_data=f'g_next_{1 if page == 3 else page + 1}_{grade}')
    ])

    # Confirm button if grade selected (wrapped in a list)
    if grade:
        keyboard.append([InlineKeyboardButton(text='✅ Tastiqlash', callback_data=f'Grade_{grade}')])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def weekends(weekend_days):
    keyboard = []
    row = []
    week_days = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba']

    for i in week_days:
        if i in weekend_days:
            row.append(InlineKeyboardButton(text=f"✅ {i}", callback_data=f'weekend_{i}_remove'))
        else:
            row.append(InlineKeyboardButton(text=f"{i}", callback_data=f'weekend_{i}_add'))

        if len(row) == 3:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    if not weekend_days:
        keyboard.append([InlineKeyboardButton(text='Bilmayman', callback_data='w_unknown')])
    else:
        keyboard.append([InlineKeyboardButton(text='✅ Tastiqlash', callback_data='w_done')])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def confirm():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='✅ Tastiqlsh', callback_data=f'a_done'),
                                                  InlineKeyboardButton(text='♻️ qaytatan yozish',
                                                                       callback_data=f'a_fail')], ])


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    login = await create_user(message.from_user.id)

    if login:
        await message.reply(
            text='⚠️ Siz allaqachon so‘rovnomani to‘ldirib bo‘lgansiz.'
        )
        return

    await message.answer(
        text="📋 14-maktabning so‘rovnomasiga xush kelibsiz!\n"
             "✍️ Iltimos, ismingizni kiriting (masalan: *Xusanboy*)",
        parse_mode="Markdown"
    )
    await state.set_state(Survey.first_name)



@dp.message(Survey.first_name)
async def first(message: Message, state: FSMContext):
    text = message.text.strip().capitalize()

    if any(char.isdigit() for char in text):
        await message.reply('⚠️ Ismingizda raqam bo‘lishi mumkin emas!')
        return

    await state.update_data(first_name=text)
    await message.answer('👤 Endi familiyangizni kiriting (masalan: *Abdulxayev*)', parse_mode="Markdown")
    await state.set_state(Survey.last_name)



@dp.message(Survey.last_name)
async def last(message: Message, state: FSMContext):
    text = message.text.strip().capitalize()
    if any(char.isdigit() for char in text):
        await message.reply('⚠️ Familyangizda raqam bo‘lishi mumkin emas!')
        return
    await state.update_data(last_name=text)
    await message.answer(text='📚 Sinfingizni tanlang:👇', reply_markup=classroom_keyboard())



@dp.callback_query(F.data.startswith('g_'))
async def classroom(call: CallbackQuery, state: FSMContext):
    data = call.data.split('_')
    gr = await state.get_data()

    # Determine grade from state or callback data
    grade_s = gr.get('classroom') or (data[3] if len(data) == 4 else data[1])
    print(f"Selected grade: {grade_s}")

    if len(data) == 4:
        await call.message.edit_text(
            text='📚 Sinifingizni tanlang:👇',
            reply_markup=classroom_keyboard(page=int(data[2]), grade=grade_s or '')
        )
        return

    await call.message.edit_reply_markup(
        reply_markup=classroom_keyboard(page=int(data[2]), grade=grade_s or '')
    )
    await state.update_data(classroom=grade_s)



@dp.callback_query(F.data.startswith('Grade_'))
async def grade(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        '📚 Qaysi fanlar bo‘yicha repetitorga qatnashmoqdasiz? '
        'Fanlaringizni tanlang (1 dan ortiq fan tanlash mumkin) 👇',
        reply_markup=keyboard_subject([])
    )
    print(f"Selected grade: {call.data}")
    await state.update_data(classroom=call.data.split('Grade_')[1])
    await state.update_data(subjects=[])



@dp.callback_query(F.data.startswith('add_subject'))
async def add_subject(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer('✍️ Iltimos, fan nomini kiriting:')
    await state.set_state(Survey.test)
    return

@dp.message(Survey.test)
async def test(message: Message, state: FSMContext):
    data = await state.get_data()
    subjects = data.get('subjects')

    # Ensure subjects is a list
    if not isinstance(subjects, list):
        subjects = []

    subjects.append(message.text)
    await state.update_data(subjects=subjects)

    await message.answer('🏫 O‘quv markazining nomini yozing (masalan: Smart English):')
    await state.set_state(Survey.education_name)




@dp.callback_query(F.data.startswith('s_'))
async def subjects(call: CallbackQuery, state: FSMContext):
    data = call.data.split('_')
    action = data[2]
    added_subject = data[1]

    user_data = await state.get_data()
    subjects_all = user_data.get('subjects', [])

    # Ensure subjects_all is a list
    if not isinstance(subjects_all, list):
        subjects_all = []

    if action == 'remove':
        if added_subject in subjects_all:
            subjects_all.remove(added_subject)
    elif action == 'add':
        if added_subject not in subjects_all:
            subjects_all.append(added_subject)

    await call.message.edit_text(
        '📚 Qaysi fanlar bo‘yicha repetitorga qatnamoqdasiz? '
        'Fanlaringizni tanlang (1 dan ortiq fan tanlash mumkin) 👇',
        reply_markup=keyboard_subject(subjects_all)
    )
    await state.update_data(subjects=subjects_all)



@dp.callback_query(F.data.startswith('Done'))
async def done(call: CallbackQuery, state: FSMContext):
    callback = call.data.split('_')
    print(f"Callback parts count: {len(callback)}")

    await call.message.delete()

    if len(callback) == 2:
        await state.update_data(subjects=['Hech qayerga bormiman'])
        all_data = await state.get_data()

        first_name = all_data.get('first_name', 'Noma\'lum')
        last_name = all_data.get('last_name', 'Noma\'lum')
        classroom = all_data.get('classroom', 'Noma\'lum')

        text = (
            "Iltimos, quyidagi ma'lumotlaringizni tekshiring:\n\n"
            f"📛 Ismi: {first_name}\n"
            f"👤 Familiyasi: {last_name}\n"
            f"🏫 Sinf: {classroom}\n"
            f"📚 Fanlar: Yozda uyda dam olaman\n\n"
            "Ushbu ma'lumotlar to‘g‘rimi?\n\n"
            "✅ Tasdiqlash uchun \"Tasdiqlash\" tugmasini bosing."
        )

        await call.message.answer(text=text, reply_markup=confirm())
        return

    await call.message.answer(
        text="🏫 O‘quv markazining nomini yozing (masalan: Smart English):"
    )
    await state.set_state(Survey.education_name)



@dp.message(Survey.education_name)
async def education(message: Message, state: FSMContext):
    education_name = message.text.strip().capitalize()
    await state.update_data(education_name=education_name)

    await message.reply(
        text=f"🏢 '{education_name}' o‘quv markazi qayerda joylashgan? "
             "(Masalan: Marhamat markazida, MIBdan keyin yoki 47-udum oldida)"
    )
    await state.set_state(Survey.place)
    return



@dp.message(Survey.place)
async def place(message: Message, state: FSMContext):
    data = await state.get_data()
    education_name = data.get('education_name', 'Noma\'lum o‘quv markazi')
    subjects = data.get('subjects', [])

    subjects_str = ', '.join(subjects) if subjects else "Fanlar ro‘yxati mavjud emas"

    await message.answer(
        f"📅 '{education_name}' o‘quv markazida \n{subjects_str} fanlarini qachon boshlamoqchisiz? "
        "(Agar o‘qishni boshlagan bo‘lsangiz, boshlagan sanangizni kiriting.)\n"
        "Sanani kiriting: kun.oy.yil formatida (masalan: 25.05.2025)"
    )
    await state.update_data(place=message.text.strip())
    await state.set_state(Survey.date)



@dp.message(Survey.date)
async def date(message: Message, state: FSMContext):
    parts = message.text.split('.')

    if len(parts) != 3:
        await message.reply('❌ Iltimos, sanani to‘g‘ri formatda kiriting: kun.oy.yil (masalan: 25.05.2025)')
        return

    if not all(part.isdigit() for part in parts):
        await message.reply('❌ Iltimos, faqat raqamlardan foydalaning: kun.oy.yil (masalan: 25.05.2025)')
        return

    day, month, year = map(int, parts)
    if not (1 <= day <= 31) or not (1 <= month <= 12) or not (2010 <= year <= 2025):
        await message.reply('❌ Sana noto‘g‘ri kiritilgan yoki diapazondan tashqarida. Iltimos, formatga mos yozing: kun.oy.yil (masalan: 25.05.2025)')
        return

    await state.update_data(date=message.text)
    await state.update_data(weekdays=[])

    await message.answer(
        '📅 Haftaning qaysi kunlarida repetitoringiz bo‘ladi? '
        'Quyidagi tugmalardan tanlang 👇',
        reply_markup=weekends(weekend_days=[])
    )



@dp.callback_query(F.data.startswith('weekend_'))
async def weekend(call: CallbackQuery, state: FSMContext):
    callback_data = call.data.split('_')
    action = callback_data[2]
    day = callback_data[1]

    data = await state.get_data()
    weekdays = data.get('weekdays', [])

    # Ensure weekdays is a list
    if not isinstance(weekdays, list):
        weekdays = []

    if action == 'remove':
        if day in weekdays:
            weekdays.remove(day)
    elif action == 'add':
        if day not in weekdays:
            weekdays.append(day)

    await call.message.edit_text(
        '📅 Haftaning qaysi kunlarida repetitoringiz bo‘ladi? '
        'Pastdagi tugmalardan tanlang 👇',
        reply_markup=weekends(weekend_days=weekdays)
    )
    await state.update_data(weekdays=weekdays)



@dp.callback_query(F.data.startswith('w_'))
async def week(call: CallbackQuery, state: FSMContext):
    data = call.data.split('_')
    await call.message.delete()

    if data[1] == 'unknown':
        await state.update_data(weekdays=['Noma\'lum'])

    all_data = await state.get_data()
    weekdays = all_data.get('weekdays', [])
    first_name = all_data.get('first_name', 'Noma\'lum')
    last_name = all_data.get('last_name', 'Noma\'lum')
    place = all_data.get('place', 'Noma\'lum')
    subjects = all_data.get('subjects', [])
    education_name = all_data.get('education_name', 'Noma\'lum')
    classroom = all_data.get('classroom', 'Noma\'lum')
    date = all_data.get('date', 'Noma\'lum')

    text = f"""Iltimos, quyidagi ma'lumotlaringizni tekshiring:

📛 Ismi: {first_name}
👤 Familiyasi: {last_name}
🏫 Ta'lim muassasasi: {education_name}
🏢 Joylashuvi: {place}
📅 Sana: {date}
🏫 Sinf: {classroom}
📚 Fanlar: {', '.join(subjects) if subjects else 'Noma`lum'}
🗓 Haftaning kunlari: {', '.join(weekdays) if weekdays else 'Noma`lum'}

Ushbu ma'lumotlar to‘g‘rimi?

✅ Tasdiqlash uchun "Tasdiqlash" tugmasini bosing.
"""

    await call.message.answer(text=text, reply_markup=confirm())



@dp.callback_query(F.data.startswith('a_'))
async def ask(call: CallbackQuery, state: FSMContext):
    data = call.data.split('_')

    if data[1] == 'done':
        await call.message.delete()
        await call.message.answer('✅ Siz ma`lumotnomani muvaffaqiyatli tugatdingiz, rahmat! 🙏')

        all_data = await state.get_data()
        weekdays = all_data.get('weekdays', [])
        first_name = all_data.get('first_name', '')
        last_name = all_data.get('last_name', '')
        place = all_data.get('place', '')
        subjects = all_data.get('subjects', [])
        education_name = all_data.get('education_name', '')
        classroom = all_data.get('classroom', '')
        date = all_data.get('date', '')

        await create_survey(
            tg_id=call.from_user.id,
            first_name=first_name,
            last_name=last_name,
            classroom=classroom,
            subjects=subjects,
            date=date,
            place=place,
            weekdays=weekdays,
            education_name=education_name
        )
        return

    if data[1] == 'fail':
        await state.clear()
        await call.message.answer(
            '❌ Jarayon bekor qilindi. Iltimos, qayta boshlang.\n\nIsmingizni kiriting: (Xusanboy) Misol uchun'
        )
        await state.set_state(Survey.first_name)
        return


@dp.message(F.text=='/yuklash')
async def download(message:Message):
    print('downloading')
    file_path = await create_survey_docx(await get_survey())
    await message.answer_document(document=FSInputFile(file_path), caption="Sizning so'rovingiz hujjati")



async def main():
    await init()
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bye')
