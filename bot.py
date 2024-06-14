from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler, Filters, MessageHandler
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import random
import sys
import re
import requests


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
    save_User(userId, username, chatId, "start")
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
    query.answer() ## All callback queries need to be answered
    if query.data == "wordCap":
        query.edit_message_text(
            text= "Please type the word you want the full form for: \nTo cancel word search type /cancel"
        )
        print("Button pressed wordCapture!")
        updateUserstatus("wordCap", userId) ## Update my database status
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
    # userId = str(update.message.from_user.id)
    # Pre-process the word
    word = update.message.text.lower()
    definition = check_word(word) # Returning response.data

    if definition:
        #Take the first row
        result = definition[0]
        short_value = result["short"]
        long_value = result["long"]
        update.message.reply_text(f'{short_value.upper()}: {long_value}')
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

def test_command(update: Update, context: CallbackContext) -> None:
    print("##### Testing new command")
    broadcast_tix()

# Ticketing
def send_ticket(update: Update, context: CallbackContext) -> None:
    ## I should do a user init here too
    userId = str(update.message.from_user.id)
    username = str(update.message.from_user.username)
    chatId = str(update.message.chat.id)
    chat_type = str(update.message.chat.type)
    print(userId,username,chatId)
    save_User(userId, username, chatId, "await")
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
    username = update.message.from_user.username
    userStatus = getUserStatus(userId)  # Retrieve the user's state from the database
    # Check userStatus
    print("THE USER STATUS IS: ", userStatus)

    if userStatus == "tixStart":
        # When enter "tixStart" state, handle in here:
        # Validate text given by users to ensure correct data input
        pattern = re.compile(r"^([^:]+):([^:]+)$")
        text = update.message.text
        text_check = pattern.match(text)
        if text_check:
            text = text.lower()
            try:
                # Assuming 'supabase' is properly configured and imported
                data, count = supabase.table("tele-user").update({
                    "submit": text,
                    "status": "start"
                }).eq("user_id", userId).execute()

                update.message.reply_text("Successfully updated your submission.")
                moveToPending(userId, username, text)
                # I can broadcast once it move to pending...
                # Broadcast by ID

            except Exception as e:
                update.message.reply_text("An error occurred: {}".format(e))
                print("An error occurred:", e)
        else:
            update.message.reply_text("The text inputted did not match the format given, try again: \n<Acronym>:<Long format>")
    else:
        update.message.reply_text(f"Sorry, '{update.message.text}' is not a recognized command or input.")


def broadcast_tix():
    ## Not tested yet
    print("Function call: broadcast_tix!!!")
    ## I should change the logic to just get the first submission, count to be updated constantly...
    try:
        data, count = supabase.table("pending").select("*").execute()
        print(data)
        print(len(data[1])) ## This is the total number of things called
        detailFull = data[1][0] ## This will ensure that the first row will always be called
        print(detailFull)
        #chat_id = detailFull["user_id"]
        chat_id = os.getenv("admin") #To send to admins

        ## Formatting message
        submittedWord = detailFull["submit"]
        keyboard = [
            [
                InlineKeyboardButton("Add", callback_data="acceptWord"),
                InlineKeyboardButton("Reject", callback_data="rejectWord")
            ]
        ]
        message_text = "<b>Word Submission into database</b>\n\n" + submittedWord.upper()
        reply_markup = InlineKeyboardMarkup(keyboard)
        keyboard_string = str(reply_markup).replace("'", '"') #Double apostrofy is needed for the url to work

        url = "https://api.telegram.org/bot" + TOKEN + "/sendMessage?" + "chat_id=" + chat_id + "&parse_mode=html" + "&text=" + message_text + "&reply_markup=" + keyboard_string
        print(url)
        request_returns = requests.get(url).json()
        print(request_returns)
        print("Sent message to admin")
    except Exception as e:
        ## Data not found, throw error
        print("No data found, ", e)


## Database related functions
def test_database_connection(table):
    try:
        data = supabase.table(table).select("*").execute()
        print(data)
        return True
    except Exception as e:
        print("Database connection failed:", e)
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


def save_User(userId, username, chatid, status):
    if check_User(userId):
        #pass
        data, count = supabase.table("tele-user").update({
            "status" : status
        }).eq("user_id", userId).execute()
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
                "status": status
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

def deleteInfo(userId, table):
    ## Delete row function
    try:
        test_database_connection(table)
        data, count = supabase.table(table).delete().eq("user_id", userId).execute()
        print("Deleted row from: ", userId)
    except Exception as e:
        print("Failed to delete row: ", e)


def moveToPending(user_id, userName, submit):
    try:
        data, count = supabase.table("pending").insert({
            "user_id" : user_id,
            "userName" : userName,
            "submit" : submit
        }).execute()
        print("Added: ", data)
    except Exception as e:
        print("Failed to move to pending, ", e)
    # Delete row entry in tele-user after moving to pending
    deleteInfo(user_id, "tele-user")


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
    dispatcher.add_handler(CommandHandler("test", test_command))
    # dispatcher.add_handler(CommandHandler('dict', dict_command, pass_args=True))

    dispatcher.add_handler(CallbackQueryHandler(button)) # Handles Callback query buttons
    dispatcher.add_handler(MessageHandler(Filters.text, unknown)) ## Handles random commands / Text
    # Start the Bot (Test DB connection first)
    if test_database_connection("dictionary"):
        print("Database connection success!, starting bot")
        updater.start_polling()
        updater.idle()
    else:
        print("Database connection failed")

if __name__ == '__main__':
    main()