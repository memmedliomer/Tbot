import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# --- Sabit Dəyərlər ---
TOKEN = "7981599020:AAGRhaJZbvMQ1n9Y7qrnBDKWYZcsVX3FV88"

# ConversationHandler üçün vəziyyətlər (states)
(
    SELECTING_EXAM_TYPE,
    AWAITING_INPUT,
    CONFIRMING_INPUT,
    SELECTING_GRID_SCORES,
) = range(4)

# Bütün imtahan modelləri üçün mərkəzi konfiqurasiya
STEPS = {
    '9_kohne': {
        'ingilis_qapali': {'prompt': "İngilis dili fənnindən qapalı suallara verdiyiniz doğru cavabların sayını daxil edin.", 'max_val': 26, 'validation': 'int', 'data_key': 'ingilis_qapali', 'next_step': 'ingilis_grid'},
        'ingilis_grid': {'prompt': "İngilis dili fənnindən yazılı düz cavablarınızı seçin:", 'questions': ['6', '28', '29', '30'], 'data_key': 'ingilis_grid_selections', 'next_step': 'az_dili_qapali'},
        'az_dili_qapali': {'prompt': "Azərbaycan dili fənnindən qapalı suallara verdiyiniz doğru cavabların sayını daxil edin.", 'max_val': 26, 'validation': 'int', 'data_key': 'az_dili_qapali', 'next_step': 'az_dili_grid'},
        'az_dili_grid': {'prompt': "Azərbaycan dili fənnindən yazılı düz cavablarınızı seçin:", 'questions': ['49', '50', '59', '60'], 'data_key': 'az_dili_grid_selections', 'next_step': 'riyaziyyat_qapali'},
        'riyaziyyat_qapali': {'prompt': "Riyaziyyat fənnindən qapalı düz cavabların sayını daxil edin.", 'max_val': 15, 'validation': 'int', 'data_key': 'riyaziyyat_qapali', 'next_step': 'riyaziyyat_kodlash'},
        'riyaziyyat_kodlash': {'prompt': "Riyaziyyat fənnindən açıq kodlaşdırılabilən düz cavabların sayını qeyd edin.", 'max_val': 6, 'validation': 'int', 'data_key': 'riyaziyyat_kodlash', 'next_step': 'riyaziyyat_grid'},
        'riyaziyyat_grid': {'prompt': "Riyaziyyat fənnindən yazılı düz cavablarınızı seçin:", 'questions': ['82', '83', '84', '85'], 'data_key': 'riyaziyyat_grid_selections', 'next_step': 'son_hesablama'},
    },
    '9_2025': {
        'ingilis_qapali': {'prompt': "Xarici dil fənnindən qapalı tipli düzgün cavabların sayını daxil edin.", 'max_val': 22, 'validation': 'int', 'data_key': 'ingilis_qapali', 'next_step': 'ingilis_kodlash'},
        'ingilis_kodlash': {'prompt': "Xarici dil fənnindən açıq kodlaşdırılabilən düz cavabların sayını qeyd edin.\n*Qeyd: 0.5 aralıqla daxil edə bilərsiniz.*", 'max_val': 3, 'validation': 'float', 'data_key': 'ingilis_kodlash', 'next_step': 'ingilis_esse'},
        'ingilis_esse': {'prompt': "Xarici dil fənnindən esse dəyərini qeyd edin.\n*Qeyd: Esse 0.5 aralıqla maksimum 5 bal kimi dəyərləndirilə bilər.*", 'max_val': 5, 'validation': 'float', 'data_key': 'ingilis_esse', 'next_step': 'az_dili_qapali'},
        'az_dili_qapali': {'prompt': "Ana dili fənnindən düzgün cavabların sayını daxil edin.", 'max_val': 26, 'validation': 'int', 'data_key': 'az_dili_qapali', 'next_step': 'az_dili_grid'},
        'az_dili_grid': {'prompt': "Ana dili fənnindən yazılı düz cavablarınızı seçin:", 'questions': ['45', '46', '55', '56'], 'data_key': 'az_dili_grid_selections', 'next_step': 'riyaziyyat_qapali'},
        'riyaziyyat_qapali': {'prompt': "Riyaziyyat fənnindən qapalı düz cavabların sayını daxil edin.", 'max_val': 15, 'validation': 'int', 'data_key': 'riyaziyyat_qapali', 'next_step': 'riyaziyyat_kodlash'},
        'riyaziyyat_kodlash': {'prompt': "Riyaziyyat fənnindən açıq kodlaşdırıla bilən düz cavabların sayını qeyd edin.", 'max_val': 6, 'validation': 'int', 'data_key': 'riyaziyyat_kodlash', 'next_step': 'riyaziyyat_grid'},
        'riyaziyyat_grid': {'prompt': "Riyaziyyat fənnindən yazılı düz cavablarınızı seçin:", 'questions': ['78', '79', '80', '81'], 'data_key': 'riyaziyyat_grid_selections', 'next_step': 'son_hesablama'},
    },
    '11': {
        'ingilis_qapali': {'prompt': "Xarici dil fənnindən düzgün cavabların sayını daxil edin.", 'max_val': 23, 'validation': 'int', 'data_key': 'ingilis_qapali', 'next_step': 'ingilis_grid'},
        'ingilis_grid': {'prompt': "Xarici dil fənnindən yazılı düz cavablarınızı seçin:", 'questions': ['4', '5', '6', '27', '28', '29', '30'], 'data_key': 'ingilis_grid_selections', 'next_step': 'az_dili_qapali'},
        'az_dili_qapali': {'prompt': "Azərbaycan dili fənnindən düzgün cavabların sayını daxil edin.", 'max_val': 20, 'validation': 'int', 'data_key': 'az_dili_qapali', 'next_step': 'az_dili_grid'},
        'az_dili_grid': {'prompt': "Azərbaycan dili fənnindən yazılı düz cavablarınızı seçin:", 'questions': ['46', '47', '48', '49', '50', '56', '57', '58', '59', '60'], 'data_key': 'az_dili_grid_selections', 'next_step': 'riyaziyyat_qapali'},
        'riyaziyyat_qapali': {'prompt': "Riyaziyyat fənnindən qapalı düz cavabların sayını daxil edin.", 'max_val': 13, 'validation': 'int', 'data_key': 'riyaziyyat_qapali', 'next_step': 'riyaziyyat_kodlash'},
        'riyaziyyat_kodlash': {'prompt': "Riyaziyyat fənnindən açıq kodlaşdırıla bilən düz cavabların sayını qeyd edin.", 'max_val': 5, 'validation': 'int', 'data_key': 'riyaziyyat_kodlash', 'next_step': 'riyaziyyat_grid'},
        'riyaziyyat_grid': {'prompt': "Riyaziyyat fənnindən yazılı düz cavablarınızı seçin:", 'questions': ['79', '80', '81', '82', '83', '84', '85'], 'data_key': 'riyaziyyat_grid_selections', 'next_step': 'son_hesablama'},
    }
}


# --- Loglama ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Başlanğıc və Menyu Funksiyaları ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton("🎓 Buraxılış", callback_data='buraxilish')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = "Salam! 👋 DİM imtahan nəticələrini hesablamaq üçün imtahan növünü seçin:"
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text=message_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=message_text, reply_markup=reply_markup)
    return SELECTING_EXAM_TYPE

async def select_exam_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("11-ci sinif", callback_data='class_11')],
        [InlineKeyboardButton("9-cu sinif (2025 modeli)", callback_data='class_9_2025')],
        [InlineKeyboardButton("9-cu sinif (Köhnə model)", callback_data='class_9_kohne')],
        [InlineKeyboardButton("↩️ Ana Səhifə", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Zəhmət olmasa, buraxılış imtahanı üçün sinif və modeli seçin:", reply_markup=reply_markup)
    return SELECTING_EXAM_TYPE

async def start_exam_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['exam_type'] = query.data.split('class_')[1]
    return await prompt_for_input(update, context, step_name='ingilis_qapali')


# --- Ümumi Məlumat Daxiletmə Funksiyaları ---
async def prompt_for_input(update: Update, context: ContextTypes.DEFAULT_TYPE, step_name: str | None = None) -> int:
    query = update.callback_query
    if not step_name:
        await query.answer()
        step_name = query.data

    context.user_data['current_step'] = step_name
    exam_type = context.user_data['exam_type']
    step_info = STEPS[exam_type][step_name]
    
    keyboard = [[InlineKeyboardButton("❌ Ləğv et", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = f"{step_info['prompt']}\n(Maksimum dəyər: {step_info['max_val']})"
    
    if query and query.message:
        await query.edit_message_text(text=message_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message_text, reply_markup=reply_markup, parse_mode='Markdown')
    return AWAITING_INPUT

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text.replace(',', '.')
    step_name = context.user_data['current_step']
    exam_type = context.user_data['exam_type']
    step_info = STEPS[exam_type][step_name]
    max_val = step_info['max_val']
    validation_type = step_info['validation']
    
    is_valid = False
    try:
        value = float(user_input)
        if 0 <= value <= max_val:
            if validation_type == 'int' and value.is_integer():
                is_valid = True
            elif validation_type == 'float' and (value * 2).is_integer():
                is_valid = True
    except ValueError:
        is_valid = False

    if not is_valid:
        error_msg = f"Daxil etdiyiniz məlumat düzgün deyil. Zəhmət olmasa, 0 və {max_val} arasında "
        error_msg += "tam bir rəqəm yazın." if validation_type == 'int' else "0.5 aralıqlı bir rəqəm yazın."
        await update.message.reply_text(error_msg)
        return AWAITING_INPUT
    
    context.user_data['temp_value'] = int(value) if validation_type == 'int' else value
    
    keyboard = [
        [InlineKeyboardButton("✅ Təsdiq et", callback_data=f"confirm_{step_name}")],
        [InlineKeyboardButton("✏️ Düzəliş et", callback_data=step_name), InlineKeyboardButton("❌ Ləğv et", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Daxil etdiyiniz məlumat: *{context.user_data['temp_value']}*\nBu məlumat doğrudurmu?", reply_markup=reply_markup, parse_mode='Markdown')
    return CONFIRMING_INPUT

async def confirm_input_and_proceed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    step_name = query.data.replace('confirm_', '')
    exam_type = context.user_data['exam_type']
    step_info = STEPS[exam_type][step_name]
    context.user_data[step_info['data_key']] = context.user_data.pop('temp_value')
    next_step_name = step_info['next_step']
    
    if 'grid' in next_step_name:
        context.user_data['current_step'] = next_step_name
        return await show_grid_selection(update, context)
    else:
        return await prompt_for_input(update, context, step_name=next_step_name)


# --- Grid (Cədvəl) Seçimi Funksiyaları ---
async def show_grid_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()

    step_name = context.user_data['current_step']
    exam_type = context.user_data['exam_type']
    step_info = STEPS[exam_type][step_name]
    selections = context.user_data.get(step_info['data_key'], {})
    
    keyboard = []
    header_text = f"{step_info['prompt']}\n\n*Qeyd:* Səhv seçimi sualın nömrəsinə toxunaraq sıfırlaya bilərsiniz."
    
    for q_num in step_info['questions']:
        row = [InlineKeyboardButton(f"{q_num}. 👉", callback_data=f"grid_reset_{q_num}")]
        for val_str, val_data in [('0', '0'), ('1/3', '0.33'), ('1/2', '0.5'), ('2/3', '0.67'), ('1', '1')]:
            text = f"✅ {val_str}" if selections.get(q_num) == val_data else val_str
            row.append(InlineKeyboardButton(text, callback_data=f"grid_select_{q_num}_{val_data}"))
        keyboard.append(row)
    
    keyboard.append([
        InlineKeyboardButton("❌ Ləğv et", callback_data='cancel'),
        InlineKeyboardButton("✅ Təsdiq et", callback_data='confirm_grid')
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query and query.message:
         await query.edit_message_text(text=header_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=header_text, reply_markup=reply_markup, parse_mode='Markdown')
    return SELECTING_GRID_SCORES

async def handle_grid_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    step_name = context.user_data['current_step']
    exam_type = context.user_data['exam_type']
    step_info = STEPS[exam_type][step_name]
    data_key = step_info['data_key']
    parts = query.data.split('_')
    action, q_num = parts[1], parts[2]
    selections = context.user_data.get(data_key, {})
    
    if action == 'select':
        selections[q_num] = parts[3]
    elif action == 'reset' and q_num in selections:
        del selections[q_num]
    context.user_data[data_key] = selections
    return await show_grid_selection(update, context)
    
async def confirm_grid_and_proceed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    current_step_name = context.user_data['current_step']
    exam_type = context.user_data['exam_type']
    step_info = STEPS[exam_type][current_step_name]
    next_step_name = step_info['next_step']

    if next_step_name == 'son_hesablama':
        return await calculate_and_show_results(update, context)
    else:
        return await prompt_for_input(update, context, step_name=next_step_name)


# --- Hesablama və Sonlandırma Funksiyaları ---
async def calculate_and_show_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    data = context.user_data
    exam_type = data['exam_type']
    bal_az = bal_ingilis = bal_riyaziyyat = 0.0

    try:
        # 9-cu sinif modelləri
        if exam_type == '9_2025' or exam_type == '9_kohne':
            # PDF-ə əsasən düsturlar
            # Tədris dili
            n_az_qapali = data.get('az_dili_qapali', 0)
            sum_az_grid = sum(float(v) for v in data.get('az_dili_grid_selections', {}).values())
            bal_az = ((2 * sum_az_grid + n_az_qapali) * 100) / 34

            # Riyaziyyat
            n_riyaziyyat_qapali = data.get('riyaziyyat_qapali', 0)
            n_riyaziyyat_kodlash = data.get('riyaziyyat_kodlash', 0)
            sum_riyaziyyat_grid = sum(float(v) for v in data.get('riyaziyyat_grid_selections', {}).values())
            bal_riyaziyyat = ((2 * sum_riyaziyyat_grid + n_riyaziyyat_kodlash + n_riyaziyyat_qapali) * 100) / 29

            # Xarici dil (modellərə görə fərqli)
            if exam_type == '9_2025':
                n_ingilis_qapali = data.get('ingilis_qapali', 0)
                n_ingilis_kodlash = data.get('ingilis_kodlash', 0)
                n_ingilis_esse = data.get('ingilis_esse', 0)
                bal_ingilis = ((n_ingilis_esse + 0 + n_ingilis_kodlash + n_ingilis_qapali) * 100) / 30 # n_d/y = 0
            else: # 9_kohne
                n_ingilis_qapali = data.get('ingilis_qapali', 0)
                sum_ingilis_grid = sum(float(v) for v in data.get('ingilis_grid_selections', {}).values())
                bal_ingilis = ((2 * sum_ingilis_grid + n_ingilis_qapali) * 100) / 34 # Köhnə düstur
        
        # 11-ci sinif modeli
        elif exam_type == '11':
            n_az_qapali = data.get('az_dili_qapali', 0)
            sum_az_grid = sum(float(v) for v in data.get('az_dili_grid_selections', {}).values())
            bal_az = ((2 * sum_az_grid + n_az_qapali) * 5) / 2
            
            n_ingilis_qapali = data.get('ingilis_qapali', 0)
            sum_ingilis_grid = sum(float(v) for v in data.get('ingilis_grid_selections', {}).values())
            bal_ingilis = (100 / 37) * (2 * sum_ingilis_grid + n_ingilis_qapali)
            
            n_riyaziyyat_qapali = data.get('riyaziyyat_qapali', 0)
            n_riyaziyyat_kodlash = data.get('riyaziyyat_kodlash', 0)
            sum_riyaziyyat_grid = sum(float(v) for v in data.get('riyaziyyat_grid_selections', {}).values())
            bal_riyaziyyat = (25 / 8) * (2 * sum_riyaziyyat_grid + n_riyaziyyat_qapali + n_riyaziyyat_kodlash)

        total_bal = bal_az + bal_ingilis + bal_riyaziyyat
        
        exam_title = exam_type.replace('_', ' ').title()
        result_text = (f"🎉 *Nəticəniz ({exam_title})* 🎉\n\n"
                       f"🇦🇿 *Ana dili:* {bal_az:.1f} bal\n"
                       f"🇬🇧 *Xarici dil:* {bal_ingilis:.1f} bal\n"
                       f"🧮 *Riyaziyyat:* {bal_riyaziyyat:.1f} bal\n"
                       "-------------------------------------\n"
                       f"🏆 *ÜMUMİ BAL:* {total_bal:.1f}")
    except Exception as e:
        logger.error(f"Hesablama zamanı xəta baş verdi: {e}")
        result_text = "Nəticələri hesablayarkən xəta baş verdi. Zəhmət olmasa, /start ilə yenidən cəhd edin."
    
    keyboard = [[InlineKeyboardButton("🏠 Ana Səhifə", callback_data='start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=result_text, parse_mode='Markdown', reply_markup=reply_markup)
    context.user_data.clear()
    return SELECTING_EXAM_TYPE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(text="Proses ləğv edildi.")
    return await start(update, context)


# --- Əsas Bot Qurulumu ---
def main() -> None:
    application = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING_EXAM_TYPE: [
                CallbackQueryHandler(select_exam_class, pattern='^buraxilish$'),
                CallbackQueryHandler(start_exam_flow, pattern='^class_'),
                CallbackQueryHandler(start, pattern='^start$')
            ],
            AWAITING_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            CONFIRMING_INPUT: [
                CallbackQueryHandler(confirm_input_and_proceed, pattern='^confirm_'),
                CallbackQueryHandler(prompt_for_input, pattern='^(ingilis|az_dili|riyaziyyat)')
            ],
            SELECTING_GRID_SCORES: [
                CallbackQueryHandler(handle_grid_selection, pattern='^grid_'),
                CallbackQueryHandler(confirm_grid_and_proceed, pattern='^confirm_grid$'),
            ],
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern='^cancel$'), CommandHandler('start', start)],
        persistent=False, name="exam_conversation"
    )
    application.add_handler(conv_handler)
    print("Bot işə düşdü...")
    application.run_polling()

if __name__ == "__main__":
    main()