from telegram.ext import ConversationHandler
from Notion import *
from imports import *

client = OpenAI()
BOT_TOKEN = "BOT_TOKEN"
CHOOSING, SAVING_PHOTO, SAVING_VOICE, ANALYZING = range(4)
spending_categories = [
    "Groceries",
    "Rent",
    "Transportation",
    "Utilities",
    "Dining Out",
    "Clothing",
    "Health",
    "Entertainment",
    "Subscriptions",
    "Travel"
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Budget Buddy! 🎉\n\n"
        "I'm here to help you track and categorize your expenses automatically from your receipts.\n\n"
        "For detailed info press /menu")
    return CHOOSING


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 Available Actions:\n\n"
        "/save_photo – Extract and save invoice details from a photo\n"
        "/save_voice – Extract and save invoice details from a voice message\n"
        "/analyze_invoices – Analyze your spending's with the help of AI\n")
    return CHOOSING


async def save_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me please your invoice.", parse_mode='Markdown')
    return SAVING_PHOTO


async def process_invoice_photo(update: Update, context):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_path = await file.download_to_drive()

    with Image.open(file_path) as img:
        buffer = BytesIO()
        img.convert("RGB").save(buffer, format="JPEG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": f"Extract the following from the image: Invoice Number, Date, Category (pick the closest from {spending_categories}), and Total Amount in JSON format. If no invoice is found in the image, respond with 'No invoice detected' line."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        },
                    },
                ],
            }
        ],
        max_tokens=100,
    )
    os.remove(file_path)

    reply = response.choices[0].message.content

    if "No invoice detected" in reply:
        await update.message.reply_text("No invoice detected in the image.", parse_mode='Markdown')
    else:
        match = re.search(r'\{[\s\S]*\}', reply)
        data = json.loads(match.group())

        number = data['Invoice Number']
        amount = data.get("Total Amount", "0").replace('€', '').replace('$', '').replace('грн', '').strip()
        amount_cleaned = amount.replace(',', '.')
        amount = float(amount_cleaned)
        date = data['Date']
        category = data['Category']

        invoice = Invoice(number, amount, date, category)

        write_data_to_notion(invoice)
        await update.message.reply_text("Successfully saved!", parse_mode='Markdown')

    return CHOOSING


async def save_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me the voice message.", parse_mode='Markdown')
    return SAVING_VOICE


async def process_invoice_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as f:
        await file.download_to_drive(f.name)
        voice_path = f.name

    audio = AudioSegment.from_ogg(voice_path)
    wav_path = voice_path.replace(".ogg", ".wav")
    audio.export(wav_path, format="wav")

    with open(wav_path, "rb") as voice_file:
        transcription = openai.audio.transcriptions.create(
            model="whisper-1",
            file=voice_file
        )

        text = transcription.text


    prompt = (
        f"Extract the following from the text: Invoice Number (if missed leave '-'), "
        f"Date (if missed leave '-'), Category (choose the closest from {spending_categories}, you have to fill this field), "
        f"and Total Amount you should write as a 'number' (if missed leave '0') in JSON format. If no invoice is found in the text, "
        f"respond with 'No invoice detected'."
    )

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": prompt},
            {"role": "user", "content": text}
        ],
        max_tokens=200,
    )

    reply = response.choices[0].message.content

    if "No invoice detected" in reply:
        await update.message.reply_text("No invoice detected in the voice message.")
    else:
        match = re.search(r'\{[\s\S]*\}', reply)
        if match:
            data = json.loads(match.group())

            number = data.get('Invoice Number', '-')
            amount = data.get("Total Amount", "0").replace('€', '').replace('$', '').strip()
            amount_cleaned = amount.replace(',', '.')
            amount = float(amount_cleaned)
            date = data.get('Date', '-')
            category = data.get('Category', 'Uncategorized')

            invoice = Invoice(number, amount, date, category)
            write_data_to_notion(invoice)

            await update.message.reply_text("Invoice successfully saved!", parse_mode='Markdown')
        else:
            await update.message.reply_text("Couldn't parse the invoice data.")

    os.remove(voice_path)
    os.remove(wav_path)

    return CHOOSING


async def analyze_invoice_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("How you wanna analyze your invoices? If you want to finish conversation use /menu", parse_mode='Markdown')
    return ANALYZING


async def analyze_invoices(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_input = update.message.text
    invoices = get_all_data()

    if len(invoices) == 0:
        if user_input == "/menu":
            return await menu(update, context)
        await update.message.reply_text("You have not uploaded any invoices yet", parse_mode='Markdown')
    else:
        if user_input == "/menu":
            return await menu(update, context)
        else:
            prompt = (
                f"You are an intelligent financial assistant. A user asked: '{user_input}'. "
                f"Here are the invoice records: {', '.join(invoices)}. "
                f"Do NOT list the invoices unless the user explicitly asks for them. "
                f"If you do show them, format each invoice clearly like this:\n"
                f"- Number: <number>\n"
                f"- Date: DD/MM/YY\n"
                f"- Category: <category>\n"
                f"- Price: <price>$\n"
                f"Always be helpful and concise in your responses."
            )

            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )

            reply = response.choices[0].message.content
            await update.message.reply_text(reply, parse_mode='Markdown')

    return ANALYZING


if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('menu', menu),
        ],
        states={
            CHOOSING: [
                CommandHandler('save_photo', save_photo),
                CommandHandler('save_voice', save_voice),
                CommandHandler('analyze_invoices', analyze_invoice_start),
            ],
            SAVING_PHOTO: [
                MessageHandler(filters.PHOTO, process_invoice_photo)
            ],
            SAVING_VOICE: [
                MessageHandler(filters.VOICE, process_invoice_voice)
            ],
            ANALYZING: [
                MessageHandler(filters.TEXT, analyze_invoices),
                CommandHandler('menu', menu),
            ]
        },
        fallbacks=[
            CommandHandler('start', start),
            CommandHandler('menu', menu)
        ]
    )

    app.add_handler(conversation_handler)
    app.add_handler(MessageHandler(filters.ALL, menu))

    print("Bot is running...")

    app.run_polling()
