from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler, Filters, MessageHandler
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import random
import sys 


# Creating a state to handle query
typing_State = 1 
user_states = {}
load_dotenv()
TOKEN = os.getenv("TOKEN")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
# Establishing supabase client
supabase = create_client(url, key)

def start(update: Update, context: CallbackContext) -> None:
    print("*****Start is called*****")
    userId = str(update.message.from_user.id)
    username = str(update.message.from_user.username)
    chatId = str(update.message.chat.id)
    chat_type = str(update.message.chat.type)
    print(userId,username,chatId)
    save_User(userId, username, chatId)
    if chat_type == "private":

        keyboard = [
            [
                InlineKeyboardButton("Decipher a word", callback_data="wordCap"),
                InlineKeyboardButton("Familiarising urself", callback_data="tree")
            ]
        ]
        update.message.reply_text("Hello! Welcome to CAG. Please write /help to see the commands available or navigate with the buttons below", 
                                reply_markup=InlineKeyboardMarkup(keyboard))
    else: 
        print("User is trying to start commands in group chat, NO GO")

def help(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        (
            "These are the list of available functions at the moment\n" 
            "/start : Bring you to the main menu page to access the main function of deciphering words\n"
            "/help :  Shows you available commands that can be performed\n"
        )
    )

def button(update: Update, context: CallbackContext) -> None:
    userId = str(update.callback_query.from_user.id)
    userName = str(update.callback_query.from_user.username)
    query = update.callback_query
    query.answer()
    if query.data == "wordCap":
        query.edit_message_text(
            text= "Please type the word you want the full form for: \nTo cancel word search type /cancel"
        )
        print("Button pressed wordCapture!")
        return typing_State
    elif query.data == "tixStart":
        query.edit_message_text(text = (
            "Key in the acronym and long text in the format below: \n"
            "<Acronym>:<Long format>"
        ))
        user_states[userId] = "tixStart"
        updateUserstatus("tixStart", userId)

    elif query.data == "tree":
        query.edit_message_text(text= "Testing")
        print("Button pressed learning is wanted!")


def receive_word(update: Update, context: CallbackContext) -> int:
    # Pre-process the word 
    word = update.message.text.lower()
    definition = check_word(word) # Returning response.data
    
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


# Ticketing 
def send_ticket(update: Update, context: CallbackContext) -> None:
    print("Starting ticket send")
    action = "tixStart"
    keyboard = [
        [
            InlineKeyboardButton("Begin", callback_data=action)
        ]
    ]
    update.message.reply_text("Main menu to submit words into Database", reply_markup=InlineKeyboardMarkup(keyboard))

def unknown(update: Update, context: CallbackContext) -> None:
    userId = update.message.from_user.id
    userStatus = getUserStatus(userId)  # Retrieve the user's state from the database
    print("THE USER STATUS IS: ", userStatus)
    if userStatus == "tixStart":
        text = update.message.text
        try:
            # Assuming 'supabase' is properly configured and imported
            data, count = supabase.table("tele-user").update({
                "submit": text,
                "status": "start"
            }).eq("user_id", userId).execute()
            update.message.reply_text("Successfully updated your submission.")
        except Exception as e:
            update.message.reply_text("An error occurred: {}".format(e))
            print("An error occurred:", e)
    else:
        update.message.reply_text(f"Sorry, '{update.message.text}' is not a recognized command or input.")



## Database related functions
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


def check_User(userId):
    response = supabase.table("tele-user").select("*").eq("user_id", userId).execute()
    if response.data:
        return True
    else: 
        return False


def save_User(userId, username, chatid):
    if check_User(userId):
        pass
    else:
    # This assumes that user has not been added
        try:
            # Generate a unique ID for each entry
            unique_id = random.randint(0, sys.maxsize)

            # Save info into Supabase
            data, count = supabase.table("tele-user").insert({
                "id": unique_id,
                "user_id": userId,
                "chat_id": chatid,
                "userName": username,
                "status": "start"
            }).execute()
            print("Added: ", data)
            print("Table count: ", count)
        except Exception as e:
            print(f"An exception occurred: {e}")


def updateUserstatus(status, userId):
    try: 
        data, count = supabase.table("tele-user").update({
            "status" : status
        }).eq("user_id", userId).execute()
        print("Successfully updated: ", data)
    except Exception as e:
        print("An exception occured: ", e)

def getUserStatus(userId):
    try: 
        data, count = supabase.table("tele-user").select("status").eq("user_id", userId).execute()
        result = data[1][0]
        status = result["status"]
        print(status)
        return status
    except Exception as e:
        print("An exception occured: ", e)




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
    dispatcher.add_handler(CommandHandler("ticket", send_ticket))
    dispatcher.add_handler(CommandHandler('help', help))
    # dispatcher.add_handler(CommandHandler('dict', dict_command, pass_args=True))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(MessageHandler(Filters.text, unknown))
    # Start the Bot (Test DB connection first)
    if test_database_connection():
        print("Database connection success!, starting bot")
        updater.start_polling()
        updater.idle()
    else:
        print("Database connection failed")

if __name__ == '__main__':
    main()