
import os
from huggingface_hub import InferenceClient
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
import random
from datetime import datetime
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "ByteBuddy is alive!"

def run_web():
    app.run(host='0.0.0.0', port=8080)


from PIL import Image #for images#

user_memory = {}


TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
os.environ["HF_TOKEN"] = os.environ["HF_TOKEN"]


chat_client = InferenceClient(
    provider="fireworks-ai",
    api_key=os.environ["HF_TOKEN"]
)
image_client = InferenceClient(
    provider="nebius",
    api_key=os.environ["HF_TOKEN"],
)

system_prompt = {
    "role": "system",
    "content": "You are a friendly and concise AI assistant. Keep your answers short and helpful."
}

def menu(update, context):
    keyboard = [
        [
            InlineKeyboardButton("🃏 Tell a Joke", callback_data='joke'),
            InlineKeyboardButton("🕒 Show Time", callback_data='time'),
        ],
        [
            InlineKeyboardButton("🧹 Clear Chat", callback_data='clear'),
            InlineKeyboardButton("ℹ️ Help", callback_data='help'),
        ],
        [
            InlineKeyboardButton("🖼️ Generate Image", callback_data='image'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('🧠 Choose an option:', reply_markup=reply_markup)


def chat_with_huggingface(prompt, user_id):
    if user_id not in user_memory:
        user_memory[user_id] = []

    user_memory[user_id].append({"role": "user", "content": prompt})

    try:
        completion = chat_client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages= [system_prompt] + user_memory[user_id],
            max_tokens = 200,
            temperature=0.3,
            top_p=0.8
        )
        reply = completion.choices[0].message.content
        user_memory[user_id].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        return f"⚠️ Hugging Face Error: {str(e)}"

def button_handler(update, context):
    query = update.callback_query
    query.answer()

    if query.data == 'joke':
        joke = random.choice([
            "💾 Why did the computer get cold? It left its Windows open.",
            "🧠 Parallel lines have so much in common… it’s a shame they’ll never meet.",
            "🤖 Why did the robot go on a diet? It had too many bytes.",
            "🧃 I told my AI a joke about recursion... it laughed and told it again.",
            "📟 Why did the Java developer wear glasses? Because they couldn't C#.",
            "💡 How does a computer get drunk? It takes screenshots.",
            "🎤 Siri and Alexa had a rap battle. Nobody won — but Google took notes."
        ])
        query.edit_message_text(f"😂 {joke}")

    elif query.data == 'time':
        now = datetime.datetime.now().strftime("%A, %d %B %Y | %I:%M %p")
        query.edit_message_text(f"🕒 Today is: *{now}*", parse_mode='Markdown')

    elif query.data == 'clear':
        user_id = query.from_user.id
        if user_id in user_memory:
            user_memory[user_id] = []
        query.edit_message_text("🧹 Chat memory cleared! ByteBuddy is refreshed. ✨")
        print("Memory after clear:", user_memory.get(user_id))

    elif query.data == 'help':
        help_text = (
            "📖 *Available Commands:*\n"
            "/start - Welcome message\n"
            "/help - Show this help menu\n"
            "/about - Learn about ByteBuddy\n"
            "/clear - Clear chat memory\n"
            "/time - Show current time\n"
            "/8ball - Ask something fun\n"
            "/menu - Show buttons\n"
            "/image <prompt> - Generate an AI image"
        )
        query.edit_message_text(help_text, parse_mode='Markdown')
    elif query.data == 'image':
        query.edit_message_text("🖼️ To generate an image, type:\n`/image your_prompt_here`", parse_mode='Markdown')


def handle_message(update, context):
    user_message = update.message.text
    update.message.chat.send_action(action="typing")
    user_id = update.message.chat_id
    greetings = ["hi", "hello", "hey", "good morning"]
    if user_message.lower().strip() in greetings:
        update.message.reply_text(f"Hey {update.effective_user.first_name}! 👋 I'm ByteBuddy, your AI buddy. How can I help you today?")
        return

    reply = chat_with_huggingface(user_message, user_id)
    update.message.reply_text(reply, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("📷 Generate Image", callback_data='image')],
        [InlineKeyboardButton("🆘 Help", callback_data='help')]
    ]))
    

def start(update, context):
    update.message.reply_text(f"Hey {update.effective_user.first_name}! 👋 I'm ByteBuddy, your classy AI chat friend. Ask me anything!")


def about_command(update, context):
    update.message.reply_text("🤖 I'm ByteBuddy — your AI-powered assistant, built with love using LLaMA 3 and Hugging Face!")
def clear_command(update, context):
    user_id = update.effective_chat.id
    if user_id in user_memory:
      user_memory[user_id] = []
    update.message.reply_text("🧹 Your chat memory has been cleared!")
    print("Memory after clear:", user_memory.get(user_id))



def time_command(update, context):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    update.message.reply_text(f"🕒 Current time: {now}")


def eightball_command(update, context):
    responses = [
        "🎱 Yes, definitely!",
        "🎱 No way!",
        "🎱 Ask again later...",
        "🎱 It is certain.",
        "🎱 I have my doubts.",
        "🎱 Without a doubt.",
        "🎱 Don't count on it.",
        "🎱 Signs point to yes!"
    ]
    update.message.reply_text(random.choice(responses))
def help_command(update, context):
    update.message.reply_text(
        "/start - Welcome message\n"
        "/help - Show this help menu\n"
        "/about - Learn more about ByteBuddy\n"
        "/clear - Clear our chat memory 🧹\n"
        "/time - Show current time 🕒\n"
        "/8ball - Ask me anything fun 🎱"
    )

from io import BytesIO
import requests


def image_command(update, context):
    prompt = " ".join(context.args)
    if not prompt:
        update.message.reply_text("🖼️ Please provide a prompt. Example:\n/image astronaut with samosa")
        return

    update.message.reply_text("🎨 Generating image, please wait...")

    try:
        # Get PIL image from Hugging Face
        image = image_client.text_to_image(
            prompt,
            model="black-forest-labs/FLUX.1-dev"
        )

        bio = BytesIO()
        image.save(bio, format="PNG")
        bio.seek(0)

        update.message.reply_photo(photo=bio, caption=f"🖼️ Prompt: {prompt}")
    except Exception as e:
        update.message.reply_text(f"❌ Failed to generate image:\n{str(e)}")


updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher


dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(CommandHandler("about", about_command))
dispatcher.add_handler(CommandHandler("clear", clear_command))
dispatcher.add_handler(CommandHandler("time", time_command))
dispatcher.add_handler(CommandHandler("8ball", eightball_command))
dispatcher.add_handler(CommandHandler("menu", menu))
dispatcher.add_handler(CallbackQueryHandler(button_handler))
dispatcher.add_handler(CommandHandler("image", image_command))



dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))


def run_bot():
    updater.start_polling()
    updater.idle()
from flask import request, jsonify

@app.route('/chat', methods=['POST'])
def chat_api():
    data = request.get_json()
    prompt = data.get("prompt")
    user_id = "web-user"
    reply = chat_with_huggingface(prompt, user_id)
    return jsonify({"reply": reply})



if __name__ == '__main__':
    Thread(target=run_web).start()
    thread = threading.Thread(target=run_bot)
    thread.start()



