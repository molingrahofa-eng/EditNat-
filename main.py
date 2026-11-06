import requests
import json
import time
import threading
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

TELEGRAM_BOT_TOKEN = "6241875863:AAHaY4dyL86Si42IV-plN6WU0BC3ecxokF4"
ADMIN_USER_ID = 5952132218  # ضع معرف التيليجرام الخاص بك هنا

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

accounts = {}
# قاموس مؤقت لتتبع حالة المستخدم إذا كان بصدد إرسال حساب جديد
user_state = {}

def faucet_worker(bot_app, chat_id, email):
    headers = {
        'authority': 'faucetearner.org',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'origin': 'https://faucetearner.org',
        'referer': 'https://faucetearner.org/faucet.php',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    params = {'act': 'faucet'}

    while email in accounts and accounts[email]["running"]:
        time.sleep(5)
        cookies = accounts[email].get("cookies")
        if not cookies:
            continue
        try:
            rr = requests.post('https://faucetearner.org/api.php', params=params, cookies=cookies, headers=headers, timeout=15)
            response_text = rr.text
        except Exception:
            continue
        
        if 'Congratulations on receiving' in response_text:
            accounts[email]["good"] += 1
            try:
                json_data = json.loads(response_text)
                message = json_data.get("message", "")
                start_index = message.find(">") + 1
                end_index = message.find(" ", start_index)
                balance = message[start_index:end_index]
                accounts[email]["total_money"] += float(balance)
                msg = f"🔔 [تنبيه حساب: {email}]\n[+] تم المطالبة: {balance}\nالمجموع: {accounts[email]['total_money']:.4f}"
                bot_app.bot.send_message(chat_id=chat_id, text=msg)
            except Exception:
                pass
        elif 'You have already claimed, please wait for the next wave!' in response_text:
            accounts[email]["bad"] += 1
        else:
            pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
    
    # أزرار شفافة أسفل الرسالة تماماً مثل الصورة المطلوبة
    keyboard = [
        [InlineKeyboardButton("〈 اضف حساب 〉", callback_data="btn_add_account")],
        [InlineKeyboardButton("〈 حساباتي 〉", callback_data="btn_list_accounts"), InlineKeyboardButton("〈 الإحصائيات العامة 〉", callback_data="btn_global_status")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        " أهلاً بك في لوحة تحكم FaucetEarner.\n"
        "اختر من الأزرار أدناه للتحكم بالخدمات:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "btn_add_account":
        user_state[update.effective_user.id] = "waiting_for_account"
        await query.message.reply_text(
            "📩 ارسل بيانات الحساب الآن بالشكل التالي:\n\n"
            "`email password`\n\n"
            "مثال:\n`user@gmail.com mypassword123`",
            parse_mode="Markdown"
        )
    elif data == "btn_list_accounts":
        if not accounts:
            await query.message.reply_text("لا توجد أي حسابات مضافة حتى الآن.")
            return
        for email, acc_data in accounts.items():
            status_text = "يعمل 🟢" if acc_data["running"] else "متوقف 🔴"
            kb = [
                [InlineKeyboardButton("إيقاف ⏹", callback_data=f"stop_{email}"), InlineKeyboardButton("تشغيل ▶️", callback_data=f"start_{email}")],
                [InlineKeyboardButton("حذف ❌", callback_data=f"del_{email}")]
            ]
            await query.message.reply_text(
                f"📧 البريد: `{email}`\nالحالة: {status_text}\n✅ الناجحة: {acc_data['good']}\n💰 المجموع: {acc_data['total_money']:.4f}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(kb)
            )
    elif data == "btn_global_status":
        if not accounts:
            await query.message.reply_text("لا توجد حسابات قيد المراقبة.")
            return
        total_all_money = sum(acc["total_money"] for acc in accounts.values())
        total_good_all = sum(acc["good"] for acc in accounts.values())
        active_count = sum(1 for acc in accounts.values() if acc["running"])
        await query.message.reply_text(
            f"📊 **الإحصائيات الشاملة:**\n\n🔹 الحسابات: {len(accounts)}\n🟢 النشطة: {active_count}\n✅ المطالبات: {total_good_all}\n💰 الأرباح: {total_all_money:.4f}",
            parse_mode="Markdown"
        )
    elif "_" in data:
        action, email = data.split("_", 1)
        if email not in accounts:
            await query.edit_message_text("[-] هذا الحساب لم يعد موجوداً.")
            return
        if action == "stop":
            accounts[email]["running"] = False
            await query.edit_message_text(f"🛑 تم إيقاف الحساب:\n`{email}`", parse_mode="Markdown")
        elif action == "start":
            if not accounts[email]["running"]:
                accounts[email]["running"] = True
                threading.Thread(target=faucet_worker, args=(context.application, query.message.chat_id, email), daemon=True).start()
                await query.edit_message_text(f"▶️ تم تشغيل الحساب:\n`{email}`", parse_mode="Markdown")
            else:
                await query.edit_message_text(f"ℹ️ الحساب يعمل بالفعل:\n`{email}`", parse_mode="Markdown")
        elif action == "del":
            accounts[email]["running"] = False
            del accounts[email]
            await query.edit_message_text(f"🗑 تم حذف الحساب:\n`{email}`", parse_mode="Markdown")

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
    
    user_id = update.effective_user.id
    if user_state.get(user_id) == "waiting_for_account":
        text = update.message.text.strip()
        parts = text.split()
        if len(parts) < 2:
            await update.message.reply_text("[-] الصيغة غير صحيحة. يرجى إرسال البريد وكلمة المرور هكذا:\n`email password`", parse_mode="Markdown")
            return
        
        email = parts[0]
        password = parts[1]
        user_state[user_id] = None  # إزالة الحالة
        
        await update.message.reply_text("[*] جاري التحقق وتسجيل الدخول...")
        
        headers = {
            'authority': 'faucetearner.org',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'content-type': 'application/json',
            'origin': 'https://faucetearner.org',
            'referer': 'https://faucetearner.org/login.php',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        params = {'act': 'login'}
        json_data = {'email': email, 'password': password}

        try:
            response = requests.post('https://faucetearner.org/api.php', params=params, headers=headers, json=json_data, timeout=15)
            if "Login successful" in response.text:
                accounts[email] = {
                    "password": password,
                    "cookies": response.cookies.get_dict(),
                    "running": True,
                    "total_money": 0.0,
                    "good": 0,
                    "bad": 0
                }
                threading.Thread(target=faucet_worker, args=(context.application, update.effective_chat.id, email), daemon=True).start()
                await update.message.reply_text(f"[+] تمت إضافة الحساب وتشغيله بنجاح:\n`{email}`", parse_mode="Markdown")
            else:
                await update.message.reply_text("[-] فشل تسجيل الدخول: البريد أو كلمة المرور خطأ.")
        except Exception as e:
            await update.message.reply_text(f"[!] خطأ في الاتصال: {e}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    print("[*] Inline Buttons Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
