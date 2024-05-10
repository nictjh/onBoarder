from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler, Filters, MessageHandler
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Creating a state to handle query
typing_State = 1 
load_dotenv()
TOKEN = os.getenv("TOKEN")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
# Establishing supabase client
supabase = create_client(url, key)

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton("Decipher a word", callback_data="wordCap"),
            InlineKeyboardButton("Familiarising urself", callback_data="tree")
        ]
    ]
    update.message.reply_text("Hello! Welcome to CAG. Please write /help to see the commands available or navigate with the buttons below", 
                              reply_markup=InlineKeyboardMarkup(keyboard))

def help(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        (
            "These are the list of available functions at the moment\n" 
            "/start : Bring you to the main menu page to access the main function of deciphering words\n"
            "/help :  Shows you available commands that can be performed\n"
        )
    )

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    if query.data == "wordCap":
        query.edit_message_text(
            text= "Please type the word you want the full form for: \nTo cancel word search type /cancel"
        )
        print("Button pressed wordCapture!")
        return typing_State
    elif query.data == "tree":
        query.edit_message_text(text= "Testing")
        print("Button pressed learning is wanted!")


def receive_word(update: Update, context: CallbackContext) -> int:
    # Pre-process the word 
    word = update.message.text.lower()
    definition = check_word(word) ##Returning response.data
    
    if definition:
        #Take the first row
        result = definition[0]
        short_value = result["short"]
        long_value = result["long"]
        update.message.reply_text(f'{short_value.capitalize()}: {long_value}')
    else:
        update.message.reply_text(
            'Sorry, I do not have the full form for that word. Do submit a ticket to request adding it into our database'
        )

    return typing_State

def cancel(update: Update, context: CallbackContext) -> int:
    print("running Cancel now")
    update.message.reply_text("Dictionary search cancelled. Restarting...")
    start(update, context)  # Restart by calling start
    return ConversationHandler.END


def test_database_connection():
    try:
        data = supabase.table("dictionary").select("*").execute()
        print(data)
        return True
    except Exception as e:
        print("An error occured:", e)
        return False


def check_word(word): 
    try: 
        print("Checking for {}".format(word))
        response = supabase.table("dictionary").select("short, long").eq("short", word).execute()
        print(response)
        return response.data
    except Exception as e:
        print("An error occured: ", e)


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


    # Routing 
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', help))
    # dispatcher.add_handler(CommandHandler('dict', dict_command, pass_args=True))

    # Start the Bot (Test DB connection first)
    if test_database_connection():
        print("Database connection success!, starting bot")
        updater.start_polling()
        updater.idle()
    else:
        print("Database connection failed")

if __name__ == '__main__':
    main()