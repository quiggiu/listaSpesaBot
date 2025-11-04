import logging
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Configurazione logging per debug
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# File JSON per salvare la lista
DATA_FILE = 'shared_list.json'

# Lista condivisa globale - visibile a TUTTI gli utenti
shared_list = []


def load_list():
    """Carica la lista dal file JSON"""
    global shared_list
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                shared_list = json.load(f)
            print(f"✅ Lista caricata: {len(shared_list)} elementi")
        else:
            shared_list = []
            print("📝 Nessun file trovato, lista vuota inizializzata")
    except Exception as e:
        print(f"⚠️ Errore nel caricamento della lista: {e}")
        shared_list = []


def save_list():
    """Salva la lista nel file JSON"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(shared_list, f, ensure_ascii=False, indent=2)
        print(f"💾 Lista salvata: {len(shared_list)} elementi")
    except Exception as e:
        print(f"⚠️ Errore nel salvataggio della lista: {e}")


def create_main_keyboard():
    """Crea la tastiera con i pulsanti delle azioni"""
    keyboard = [
        [InlineKeyboardButton("➕ Aggiungi elemento", callback_data='add')],
        [InlineKeyboardButton("❌ Elimina elemento", callback_data='delete')],
        [InlineKeyboardButton("📋 Mostra lista completa", callback_data='show')],
        [InlineKeyboardButton("🗑️ Svuota lista", callback_data='clear')]
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce il comando /start e mostra il menu principale"""
    username = update.effective_user.first_name

    message = f"🤖 *Benvenuto {username}!*\n\n"
    message += "📋 Questa è una *lista condivisa* visibile a tutti gli utenti del bot.\n\n"

    if shared_list:
        message += f"📝 La lista contiene {len(shared_list)} elementi:\n"
        for i, item in enumerate(shared_list, 1):
            message += f"{i}. {item}\n"
    else:
        message += "📝 La lista è vuota.\n"

    message += "\n*Cosa vuoi fare?*"

    await update.message.reply_text(
        message,
        reply_markup=create_main_keyboard(),
        parse_mode='Markdown'
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce tutti i messaggi di testo (diversi dai comandi)"""
    username = update.effective_user.first_name

    # Controlla se l'utente sta aggiungendo un elemento
    if context.user_data.get('waiting_for_item'):
        item = update.message.text
        shared_list.append(item)
        context.user_data['waiting_for_item'] = False

        await update.message.reply_text(
            f"✅ *{username}* ha aggiunto '*{item}*' alla lista condivisa!",
            reply_markup=create_main_keyboard(),
            parse_mode='Markdown'
        )

    # Controlla se l'utente sta eliminando un elemento
    elif context.user_data.get('waiting_for_delete'):
        try:
            index = int(update.message.text) - 1

            if 0 <= index < len(shared_list):
                deleted_item = shared_list.pop(index)
                context.user_data['waiting_for_delete'] = False

                await update.message.reply_text(
                    f"🗑️ *{username}* ha eliminato '*{deleted_item}*'!",
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
        message = "📋 *Lista condivisa:*\n\n"

        if shared_list:
            for i, item in enumerate(shared_list, 1):
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

    username = update.effective_user.first_name

    if query.data == 'add':
        context.user_data['waiting_for_item'] = True
        await query.edit_message_text(
            "✏️ *Aggiungi elemento alla lista condivisa*\n\nInvia il testo dell'elemento che vuoi aggiungere:",
            parse_mode='Markdown'
        )

    elif query.data == 'delete':
        if not shared_list:
            await query.edit_message_text(
                "❌ La lista è vuota! Non c'è nulla da eliminare.",
                reply_markup=create_main_keyboard(),
                parse_mode='Markdown'
            )
        else:
            context.user_data['waiting_for_delete'] = True
            message = "🗑️ *Elimina elemento*\n\n📝 Lista condivisa attuale:\n"
            for i, item in enumerate(shared_list, 1):
                message += f"{i}. {item}\n"
            message += "\n*Invia il numero dell'elemento da eliminare:*"

            await query.edit_message_text(
                message,
                parse_mode='Markdown'
            )

    elif query.data == 'show':
        message = "📋 *Lista condivisa completa:*\n\n"

        if shared_list:
            for i, item in enumerate(shared_list, 1):
                message += f"{i}. {item}\n"
            message += f"\n_Totale: {len(shared_list)} elementi_"
        else:
            message += "_Lista vuota_\n"

        await query.edit_message_text(
            message,
            reply_markup=create_main_keyboard(),
            parse_mode='Markdown'
        )

    elif query.data == 'clear':
        if not shared_list:
            await query.edit_message_text(
                "❌ La lista è già vuota!",
                reply_markup=create_main_keyboard(),
                parse_mode='Markdown'
            )
        else:
            # Crea tastiera di conferma
            keyboard = [
                [
                    InlineKeyboardButton("✅ Sì, svuota", callback_data='confirm_clear'),
                    InlineKeyboardButton("❌ No, annulla", callback_data='cancel_clear')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"⚠️ *Attenzione!*\n\nSei sicuro di voler svuotare la lista condivisa?\n\n"
                f"Verranno eliminati *{len(shared_list)} elementi*.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    elif query.data == 'confirm_clear':
        items_count = len(shared_list)
        shared_list.clear()
        
        await query.edit_message_text(
            f"🗑️ *{username}* ha svuotato la lista condivisa!\n\n"
            f"Eliminati {items_count} elementi.",
            reply_markup=create_main_keyboard(),
            parse_mode='Markdown'
        )

    elif query.data == 'cancel_clear':
        await query.edit_message_text(
            "❌ Operazione annullata.\n\nLa lista non è stata modificata.",
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

    print("🤖 Avvio del bot con lista condivisa...")

    # Crea l'applicazione
    application = Application.builder().token(TOKEN).build()

    # Aggiungi i gestori dei comandi e messaggi
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Avvia il bot
    print("✅ Bot avviato correttamente!")
    print("📋 Lista condivisa attiva - tutti gli utenti vedranno gli stessi elementi")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
