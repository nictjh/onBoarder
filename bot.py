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
submit_word = [] ## Global variable to store the word
update_userID = "" ## Global variable to store the userid
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
    global submit_word
    userId = str(update.callback_query.from_user.id)
    userName = str(update.callback_query.from_user.username)
    query = update.callback_query
    query.answer() ## All callback queries need to be answered
    if query.data == "wordCap":
        query.edit_message_text(
            text= "Please type the word you want the full form for: \nTo cancel word search type /cancel"
        )
        print("################## Button pressed wordCapture!")
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
    elif query.data ==  "acceptWord":
        print("############### Accepted word into database!")
        addWord(submit_word["submit"])
        updateTicket(True)
        query.edit_message_text("Word: {} is successfully added into the database!".format(submit_word["submit"].upper()))
        submit_word = [] ## reset it back to null, after addition
    elif query.data == "rejectWord":
        print("############### rejecting word phase")
        keyboard = [
            [
                InlineKeyboardButton("Yes", callback_data="rejected"),
                InlineKeyboardButton("Cancel", callback_data="cancelLast")
            ]
        ]
        query.edit_message_text("Do you want to reject the word?", reply_markup= InlineKeyboardMarkup(keyboard))
    elif query.data == "rejected":
        ## this is working too
        print("Word is rejected")
        removeWord(submit_word["submit"], "pending")
        updateTicket(False)
        query.edit_message_text("{} ticket is successfully deleted!".format(submit_word["submit"]))
    elif query.data == "cancelLast":
        query.edit_message_text((
            "Action has been cancelled."
            "Please do /start for the chatbot services or /help for more information on what the bot can do"
        ))

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
        update.message.reply_text(f'{short_value.upper()}: {long_value.capitalize()}')
    else:
        update.message.reply_text((
            'Sorry, I do not have the full form for that word. Do submit a ticket to request adding it into our database.'
            'Please type or press /ticket to do so.'
        ))

    return typing_State

def cancel(update: Update, context: CallbackContext) -> int:
    print("running Cancel now")
    update.message.reply_text("Dictionary search cancelled. Thank you for using it!. \n/start to access the main function and /help for more information")
    ## start(update, context)  # Maybe i shouldnt restart the start as it will reload the state in the db
    return ConversationHandler.END

def approveFirst(update: Update, context: CallbackContext) -> None:
    print("##### Approving first word in pending database")
    # broadcast_tix()
    global submit_word
    submit_word = broadcast_tix() ##double check this returns a list
    print(submit_word["submit"])

def test_command(update: Update, context: CallbackContext) -> None:
    print("##### Testing new command")

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
                data, count = supabase.table("tele-user").update({
                    "submit": text,
                    "status": "start"
                }).eq("user_id", userId).execute()

                update.message.reply_text("Successfully updated your submission.\nThank you for your contributions!")
                moveToPending(userId, username, text)
                # I can broadcast once it move to pending...
                # Broadcast by ID

            except Exception as e:
                update.message.reply_text("An error occurred: {}".format(e))
                print("An error occurred: Failed to add word into pending!!!", e)
        else:
            update.message.reply_text("The text inputted did not match the format given, try again: \n<Acronym>:<Long format>")
    else:
        update.message.reply_text(f"Sorry, '{update.message.text}' is not a recognized command or input. Please do /start or /help for more information.")


def broadcast_tix():
    ## Working!
    ## I need to save the user_id too for this so i can update the individual
    print("Function call: broadcast_tix!!!")
    ## I should change the logic to just get the first submission, count to be updated constantly...
    try:
        data, count = supabase.table("pending").select("*").execute()
        print(data)
        print(len(data[1])) ## This is the total number of things called
        detailFull = data[1][0] ## This will ensure that the first row will always be called
        print(detailFull) ## This is a list, which i should return instead so i can access all the values
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
        return detailFull ## used to be submittedWord
    except Exception as e:
        ## Data not found, throw error
        print("No data found, ", e)

def addWord(word):
    ## Process the word
    listOfWord =  word.split(":")
    shortForm = listOfWord[0].lower()
    longForm = listOfWord[1].lower()

    # add into main dictionary table
    try:
        data, count = supabase.table('dictionary').insert({
            'short': shortForm,
            'long': longForm
        }).execute()
        print("Added new word into dictionary", data)
    except Exception as e:
        print(f"An exception occurred when adding into dictionary: {e}")

    ## remove word in pending
    removeWord(word, "pending")

def updateTicket(flag):
    global submit_word ##declare to use the global variable
    ## Retrieve the user_id
    user_id = submit_word["user_id"]
    ticket = submit_word["submit"]
    if (flag):
        message_text = "Your submission of {} has been successfully reviewed and accepted in the database".format(ticket.upper())
    else:
        message_text = "Your submission of {} has been successfully reviewed but rejected. For more information, please find @nictjh".format(ticket.upper())

    url = "https://api.telegram.org/bot" + TOKEN + "/sendMessage?" + "chat_id=" + user_id + "&parse_mode=html" + "&text=" + message_text
    print(url)
    request_returns = requests.get(url).json()
    print(request_returns)
    print("update message has been sent out to specific users")


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
    ## Checks word in dictionary table
    try:
        print("Checking for {}".format(word))
        response = supabase.table("dictionary").select("short, long").eq("short", word).execute()
        print(response)
        return response.data
    except Exception as e:
        print("Failed to find word in dictionary or failed to connect: ", e)


def check_User(userId):
    ## Checks users in tele-user table
    response = supabase.table("tele-user").select("*").eq("user_id", userId).execute()
    if response.data:
        return True
    else:
        return False


def save_User(userId, username, chatid, status):
    ## saves user in  tele-user table
    ## also updates status if user exits
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
            print(f"An exception occurred, failed to save info into database: {e}")


def updateUserstatus(status, userId):
    ## second function to update user status
    try:
        data, count = supabase.table("tele-user").update({
            "status" : status
        }).eq("user_id", userId).execute()
        print("Successfully updated: ", data)
    except Exception as e:
        print("An exception occured, failed to update userStatus: ", e)


def getUserStatus(userId):
    try:
        data, count = supabase.table("tele-user").select("status").eq("user_id", userId).execute()
        result = data[1][0]
        status = result["status"]
        print(status)
        return status
    except Exception as e:
        print("An exception occured, failed to get userStatus: ", e)

def deleteInfo(userId, table):
    ## Delete row function for userid
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

def removeWord(word, table):
    ## Removing word function from a table
    if (table == "pending"):
        try:
            data, count = supabase.table(table).delete().eq('submit', word).execute()
            print("Deleted row from pending table: ", data)
        except Exception as e:
            print("Failed to delete row: ", e)
    else:
        ## if table is dictionary.delete by short
        try:
            data, count = supabase.table(table).delete().eq('short', word).execute()
            print("Deleted row from pending table: ", data)
        except Exception as e:
            print("Failed to delete row: ", e)


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
    dispatcher.add_handler(CommandHandler("check", approveFirst))
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