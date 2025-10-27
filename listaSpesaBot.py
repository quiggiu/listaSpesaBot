import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Configurazione logging per debug
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Dizionario per memorizzare le liste di ogni utente
# Struttura: {user_id: [elemento1, elemento2, ...]}
user_lists = {}


def get_user_list(user_id):
    """Ottiene la lista dell'utente, creandola se non esiste"""
    if user_id not in user_lists:
        user_lists[user_id] = []
    return user_lists[user_id]


def create_main_keyboard():
    """Crea la tastiera con i pulsanti delle azioni"""
    keyboard = [
        [InlineKeyboardButton("➕ Aggiungi elemento", callback_data='add')],
        [InlineKeyboardButton("❌ Elimina elemento", callback_data='delete')],
        [InlineKeyboardButton("📋 Mostra lista completa", callback_data='show')]
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /start e mostra il menu principale"""
    user_id = update.effective_user.id
    user_list = get_user_list(user_id)

    message = "🤖 *Benvenuto nel Bot Lista!*\n\n"

    if user_list:
        message += f"📝 La tua lista contiene {len(user_list)} elementi:\n"
        for i, item in enumerate(user_list, 1):
            message += f"{i}. {item}\n"
    else:
        message += "📝 La tua lista è vuota.\n"

    message += "\n*Cosa vuoi fare?*"

    await update.message.reply_text(
        message,
        reply_markup=create_main_keyboard(),
        parse_mode='Markdown'
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce tutti i messaggi di testo (diversi dai comandi)"""
    user_id = update.effective_user.id

    # Controlla se l'utente sta aggiungendo un elemento
    if context.user_data.get('waiting_for_item'):
        item = update.message.text
        user_lists[user_id].append(item)
        context.user_data['waiting_for_item'] = False

        await update.message.reply_text(
            f"✅ Elemento '*{item}*' aggiunto alla lista!",
            reply_markup=create_main_keyboard(),
            parse_mode='Markdown'
        )

    # Controlla se l'utente sta eliminando un elemento
    elif context.user_data.get('waiting_for_delete'):
        try:
            index = int(update.message.text) - 1
            user_list = get_user_list(user_id)

            if 0 <= index < len(user_list):
                deleted_item = user_list.pop(index)
                context.user_data['waiting_for_delete'] = False

                await update.message.reply_text(
                    f"🗑️ Elemento '*{deleted_item}*' eliminato!",
                    reply_markup=create_main_keyboard(),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ Numero non valido. Riprova:",
                    parse_mode='Markdown'
                )
        except ValueError:
            await update.message.reply_text(
                "❌ Per favore invia un numero valido:",
                parse_mode='Markdown'
            )

    # Se non sta facendo nessuna azione, mostra il menu
    else:
        user_list = get_user_list(user_id)

        message = "📋 *La tua lista:*\n\n"

        if user_list:
            for i, item in enumerate(user_list, 1):
                message += f"{i}. {item}\n"
        else:
            message += "_Lista vuota_\n"

        message += "\n*Scegli un'azione:*"

        await update.message.reply_text(
            message,
            reply_markup=create_main_keyboard(),
            parse_mode='Markdown'
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce i click sui pulsanti"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_list = get_user_list(user_id)

    if query.data == 'add':
        context.user_data['waiting_for_item'] = True
        await query.edit_message_text(
            "✏️ *Aggiungi elemento*\n\nInvia il testo dell'elemento che vuoi aggiungere:",
            parse_mode='Markdown'
        )

    elif query.data == 'delete':
        if not user_list:
            await query.edit_message_text(
                "❌ La lista è vuota! Non c'è nulla da eliminare.",
                reply_markup=create_main_keyboard(),
                parse_mode='Markdown'
            )
        else:
            context.user_data['waiting_for_delete'] = True
            message = "🗑️ *Elimina elemento*\n\n📝 Lista attuale:\n"
            for i, item in enumerate(user_list, 1):
                message += f"{i}. {item}\n"
            message += "\n*Invia il numero dell'elemento da eliminare:*"

            await query.edit_message_text(
                message,
                parse_mode='Markdown'
            )

    elif query.data == 'show':
        message = "📋 *La tua lista completa:*\n\n"

        if user_list:
            for i, item in enumerate(user_list, 1):
                message += f"{i}. {item}\n"
        else:
            message += "_Lista vuota_\n"

        await query.edit_message_text(
            message,
            reply_markup=create_main_keyboard(),
            parse_mode='Markdown'
        )


def main():
    """Funzione principale che avvia il bot"""

    # Legge il token dalla variabile d'ambiente (impostata su Render)
    TOKEN = os.environ.get('TELEGRAM_TOKEN')

    if not TOKEN:
        print("❌ ERRORE: Token non trovato!")
        print("Assicurati di aver impostato la variabile d'ambiente TELEGRAM_TOKEN")
        return

    print("🤖 Avvio del bot...")

    # Crea l'applicazione
    application = Application.builder().token(TOKEN).build()

    # Aggiungi i gestori dei comandi e messaggi
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Avvia il bot
    print("✅ Bot avviato correttamente!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()