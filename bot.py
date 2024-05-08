from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler, Filters, MessageHandler
import os
from dotenv import load_dotenv


typing_State = 1 #defining a state to handle the dictionary query

load_dotenv()
TOKEN = os.getenv("TOKEN")

# This will be replaced by an PostgreSQL
word_db = {
    "h": "hello",
    "w": "World"
}

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton("Decipher a word", callback_data="wordCap"),
            InlineKeyboardButton("Familiarising urself", callback_data="tree")
        ]
    ]
    update.message.reply_text("Hello! Welcome to CAG. Please write /help to see the commands available or navigate with the buttons below", 
                              reply_markup=InlineKeyboardMarkup(keyboard))

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    if query.data == "wordCap":
        query.edit_message_text(text= "Please type the word you want the full form for: ")
        print("Button pressed wordCapture!")
        return typing_State
    elif query.data == "tree":
        query.edit_message_text(text= "Testing")
        print("Button pressed learning is wanted!")



def dict_command(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Please type the word you want the definition for:')
    return typing_State


def receive_word(update: Update, context: CallbackContext) -> int:
    word = update.message.text.lower()
    definition = word_db.get(word)
    
    if definition:
        update.message.reply_text(f'{word.capitalize()}: {definition}')
    else:
        update.message.reply_text('Sorry, I do not have the definition for that word.')

    return typing_State


def cancel(update: Update, context: CallbackContext) -> int:
    print("running Cancel now")
    update.message.reply_text("Dictionary search canceled. Restarting...")
    start(update, context)  # Restart by calling start
    return ConversationHandler.END





def main() -> None:
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern='^' + "wordCap" + '$')],
        states={
            typing_State: [
                MessageHandler(Filters.text & ~Filters.command, receive_word),
                CommandHandler('cancel', cancel)  
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)

    dispatcher.add_handler(CommandHandler('start', start))
    # dispatcher.add_handler(CommandHandler('dict', dict_command, pass_args=True))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
