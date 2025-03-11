import os
import logging
import time
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext


# Menggunakan variabel lingkungan untuk menyimpan token dan admin ID
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # ID Telegram admin (pastikan diisi)
CS_ID = os.getenv("CS_ID")  # ID Telegram CS
ADMIN_REKENING = os.getenv("ADMIN_REKENING", "1234567890 (Bank XYZ)")  # Rekening admin

# Konfigurasi logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.info(f"ADMIN_ID: {ADMIN_ID}")  # Cek apakah ID admin valid


# Database sementara untuk menyimpan saldo pengguna
user_data = {}

# Fungsi untuk menampilkan menu utama
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id  # Menggunakan effective_user.id agar tetap berfungsi di callback query
    message_text = update.message.text if update.message else ""  # Ambil teks jika ada

    # Cek apakah pengguna datang dari link referral
    if message_text.startswith("/start "):  
        referrer_id = message_text.split(" ")[1]  # Ambil ID pengundang
        try:
            referrer_id = int(referrer_id)
            if referrer_id != user_id:  # Pastikan user tidak mengundang diri sendiri
                if referrer_id in user_data:
                    user_data[referrer_id]["saldo"] += 1000  # Tambahkan saldo referral
                else:
                    user_data[referrer_id] = {"saldo": 1000}  # Inisialisasi saldo pengundang

                # Kirim pemberitahuan ke pengundang
                await context.bot.send_message(
                    chat_id=referrer_id,
                    text="🎉 Selamat! Anda mendapatkan 1000 IDR karena berhasil mengundang teman!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 Cek Saldo", callback_data="cek_saldo")]])
                )
        except ValueError:
            pass  # Abaikan jika tidak valid

    # Inisialisasi saldo user jika belum ada
    if user_id not in user_data:
        user_data[user_id] = {"saldo": 0}  

    keyboard = [
        [InlineKeyboardButton("📥 Depo", callback_data="depo"), InlineKeyboardButton("💰 Menarik", callback_data="menarik")],
        [InlineKeyboardButton("🔥 Pertandingan", callback_data="pertandingan"), InlineKeyboardButton("🎁 Tugas check-in", callback_data="checkin")],
        [InlineKeyboardButton("👤 Pribadi", callback_data="pribadi"), InlineKeyboardButton("👥 Teman-teman", callback_data="teman")],
        [InlineKeyboardButton("🌍 Bahasa", callback_data="bahasa"), InlineKeyboardButton("🎉 Aktivitas", callback_data="aktivitas")],
        [InlineKeyboardButton("💰 Cek Saldo", callback_data="cek_saldo")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("🔷 Selamat datang di TELE Dompet! Pilih menu di bawah:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text("🔷 Selamat datang di TELE Dompet! Pilih menu di bawah:", reply_markup=reply_markup)

# Fungsi untuk menangani tombol menu
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "start":  # ✅ Jika tombol kembali ditekan, panggil menu utama
        await start(update, context)
        return
    if query.data == "teman":  # ✅ Jika user memilih "Teman-teman"
        keyboard = [
            [InlineKeyboardButton("📨 Undang Teman", callback_data="undang_teman")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("👥 Pilih opsi di bawah:", reply_markup=reply_markup)
        return
    
    if user_id not in user_data:
        user_data[user_id] = {"saldo": 0, "bet": 0}  # Saldo default 0

    saldo = user_data[user_id]["saldo"]  # Ambil saldo utama

    if query.data == "pertandingan":
        if saldo <= 0:
            await query.message.edit_text(
                "⚠️ Anda tidak memiliki saldo yang cukup untuk bermain.\n\n"
                "Silakan lakukan deposit terlebih dahulu.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Kembali", callback_data="start")]
                ])
            )
            return

        # Jika saldo cukup, tampilkan pilihan taruhan
        keyboard = [
            [InlineKeyboardButton("100 IDR", callback_data="bet_100")],
            [InlineKeyboardButton("500 IDR", callback_data="bet_500")],
            [InlineKeyboardButton("1000 IDR", callback_data="bet_1000")],
            [InlineKeyboardButton("2000 IDR", callback_data="bet_2000")],
            [InlineKeyboardButton("5000 IDR", callback_data="bet_5000")],
            [InlineKeyboardButton("10000 IDR", callback_data="bet_10000")],
            [InlineKeyboardButton("50000 IDR", callback_data="bet_50000")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="start")]
        ]

        await query.message.edit_text(
            f"💰 Saldo Anda: {saldo} IDR\n\nPilih jumlah taruhan:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data.startswith("bet_"):  # Menangani pilihan taruhan
        bet_amount = int(query.data.split("_")[1])  # Ambil jumlah taruhan
        if saldo < bet_amount:
            await query.answer("⚠️ Saldo tidak mencukupi!", show_alert=True)
            return

        user_data[user_id]["bet"] = bet_amount  # Simpan taruhan sementara

        # Tampilkan pilihan suit
        suit_keyboard = [
            [InlineKeyboardButton("🪨 Batu", callback_data="suit_batu")],
            [InlineKeyboardButton("✂️ Gunting", callback_data="suit_gunting")],
            [InlineKeyboardButton("📜 Kertas", callback_data="suit_kertas")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="pertandingan")]
        ]

        await query.message.edit_text(
            f"✅ Anda bertaruh {bet_amount} IDR.\n\nPilih tangan Anda:",
            reply_markup=InlineKeyboardMarkup(suit_keyboard)
        )

    elif query.data.startswith("suit_"):  # Menangani permainan suit
        pilihan_user = query.data.split("_")[1]
        pilihan_bot = random.choice(["batu", "gunting", "kertas"])

        hasil = ""
        bet_amount = user_data[user_id]["bet"]

        # Logika permainan suit
        if pilihan_user == pilihan_bot:
            hasil = "🤝 Seri!"
        elif (pilihan_user == "batu" and pilihan_bot == "gunting") or \
             (pilihan_user == "gunting" and pilihan_bot == "kertas") or \
             (pilihan_user == "kertas" and pilihan_bot == "batu"):
            hasil = f"🎉 Anda menang! +{bet_amount * 1.8} IDR"
            user_data[user_id]["saldo"] += int(bet_amount * 1.8)
        else:
            hasil = f"😢 Anda kalah! -{bet_amount} IDR"
            user_data[user_id]["saldo"] -= bet_amount

        # Tampilkan hasil permainan
        await query.message.edit_text(
            f"🤖 Bot memilih: {pilihan_bot.capitalize()}\n"
            f"👤 Anda memilih: {pilihan_user.capitalize()}\n\n"
            f"{hasil}\n\n"
            f"💰 Saldo Anda sekarang: {user_data[user_id]['saldo']} IDR",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Main lagi", callback_data="pertandingan")],
                [InlineKeyboardButton("🏠 Kembali ke Menu", callback_data="start")]
            ])
        )

    
    if query.data == "undang_teman":  # ✅ Jika user memilih "Undang Teman"
        referral_link = f"https://t.me/duittele16625_bot?start={user_id}"  # Ganti YOUR_BOT_USERNAME dengan username bot kamu
        await query.message.edit_text(
            f"📨 Bagikan link ini kepada temanmu untuk mengundang mereka:\n\n"
            f"[Salin Link Undangan Mu]({referral_link})",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="start")]])
        )
        return
    if query.data == "depo":
        user_data[user_id] = {"status": "waiting_for_deposit"}
        keyboard_back = [[InlineKeyboardButton("🔙 Kembali", callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard_back)
        await query.message.edit_text("💰 Masukkan jumlah deposit (minimal 5000):", reply_markup=reply_markup)
        return
    
    
    
    if query.data == "kirim_bukti":
        user_data[user_id] = {"status": "waiting_for_bukti"}
        await query.message.edit_text("📸 Kirim foto bukti transfer Anda.")
        return

    if query.data == "cek_saldo":
        saldo = user_data.get(user_id, {}).get("saldo", 0)
        await query.message.edit_text(f"💰 Saldo Anda saat ini: {saldo} IDR", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="start")]]))
        return
     
    if query.data == "menarik":
        user = user_data.get(user_id, {"saldo": 0, "has_deposited": False})
        saldo = user.get("saldo", 0)
        has_deposited = user.get("has_deposited", False)

        if not has_deposited:
            await query.message.edit_text(
                "⚠️ Anda harus melakukan deposit minimal 5000 sebelum bisa menarik saldo!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="start")]])
            )
            return

        if saldo < 10000:
            await query.message.edit_text(
                f"⚠️ Saldo Anda kurang! Minimal penarikan adalah 10000.\nSaldo saat ini: {saldo} IDR",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="start")]])
            )
            return

        user_data[user_id]["status"] = "waiting_for_rekening"

        await query.message.edit_text(
            "🏦 Silakan masukkan nomor rekening Anda dalam format:\n\n"
            "`Nomor Rekening : Nama Bank`\n\n"
            "Contoh: 081234000000 : Dana",
            parse_mode="Markdown"
        )
        return
        
        

    menu_response = {
        "menarik": "💰 Anda memilih menu *Menarik*",
        "checkin": "🎁 Dalam Pengembangan *Tugas Check-in*",
         "pertandingan": "🔥 Dalam Pengembangan *Pertandingan*",
        "pribadi": "👤 @azey_king *Contact*",
        "teman": "👥 Anda memilih menu *Teman-teman*",
        "bahasa": "🌍 Dalam Pengembangan *Bahasa*",
        "aktivitas": "🎉 Dalam Pengembangan *Aktivitas*"
    }
    
    response_text = menu_response.get(query.data, "❌ Menu tidak ditemukan!")
    keyboard_back = [[InlineKeyboardButton("🔙 Kembali", callback_data="start")]]
    reply_markup = InlineKeyboardMarkup(keyboard_back)
    await query.message.edit_text(response_text, reply_markup=reply_markup)
    


 
# Fungsi untuk menangani input deposit
async def handle_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_data.get(user_id, {}).get("status") == "waiting_for_deposit":
        try:
            deposit_amount = int(update.message.text)
            if deposit_amount < 5000:
                await update.message.reply_text("⚠️ Minimal deposit adalah 5000. Masukkan jumlah yang benar.")
                return
            
            # Tandai bahwa user sudah pernah deposit
            if user_id not in user_data:
                user_data[user_id] = {"saldo": 0, "has_deposited": True}
            else:
                user_data[user_id]["has_deposited"] = True

            # Kirim notifikasi ke admin
            if ADMIN_ID:
                admin_message = f"📩 Pengguna @{update.message.from_user.username} ({user_id}) melakukan deposit sebesar {deposit_amount}"
                await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)
                
            keyboard = [[InlineKeyboardButton("📩 Kirim Bukti Transfer ke CS", callback_data="kirim_bukti")],
                        [InlineKeyboardButton("🔙 Kembali", callback_data="start")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            rekening_message = f"✅ Deposit berhasil dikirim ke admin.\n\n💳 Transfer ke rekening:\n*{ADMIN_REKENING}*\n\nKlik tombol di bawah untuk mengirim bukti ke CS."
            await update.message.reply_text(rekening_message, reply_markup=reply_markup, parse_mode="Markdown")

            user_data[user_id]["status"] = None
        except ValueError:
            await update.message.reply_text("⚠️ Masukkan angka yang valid.")
            

async def pertandingan(update: Update, context: CallbackContext, user_choice):
    query = update.callback_query
    user_id = query.from_user.id
    bet_amount = user_data[user_id].get("bet", 0)

    choices = ["batu", "gunting", "kertas"]
    bot_choice = random.choice(choices)

    result_text = f"👤 Anda: {user_choice.capitalize()}\n🤖 Bot: {bot_choice.capitalize()}\n\n"

    if user_choice == bot_choice:
        result_text += "⚖️ Hasil: Seri! Saldo tetap."
    elif (user_choice == "batu" and bot_choice == "gunting") or \
         (user_choice == "gunting" and bot_choice == "kertas") or \
         (user_choice == "kertas" and bot_choice == "batu"):
        winnings = int(bet_amount * 1.8)
        user_data[user_id]["saldo"] += winnings
        result_text += f"✅ Anda menang! +{winnings} IDR"
    else:
        user_data[user_id]["saldo"] -= bet_amount
        result_text += f"❌ Anda kalah! -{bet_amount} IDR"

    await query.message.edit_text(result_text, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Main Lagi", callback_data="pertandingan")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="start")]
    ]))


# Fungsi untuk menangani bukti transfer
async def handle_bukti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_data.get(user_id, {}).get("status") == "waiting_for_bukti":
        if update.message.photo:
            if CS_ID:
                await context.bot.send_photo(chat_id=CS_ID, photo=update.message.photo[-1].file_id, caption=f"📩 Bukti transfer dari @{update.message.from_user.username} ({user_id})")
                await update.message.reply_text("✅ Bukti transfer telah dikirim ke CS. Tunggu konfirmasi.")
            else:
                await update.message.reply_text("⚠️ CS belum dikonfigurasi. Hubungi admin.")
        else:
            await update.message.reply_text("⚠️ Harap kirim foto bukti transfer.")
        
        user_data[user_id] = {"status": None}

# Fungsi untuk menambah saldo pengguna (hanya admin)
async def add_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("⚠️ Anda tidak memiliki izin untuk menambahkan saldo.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("⚠️ Gunakan format: /addsaldo <user_id> <jumlah>")
        return
    
    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])

        # **Pastikan user_id ada di database dan memiliki saldo**
        if target_user_id not in user_data:
            user_data[target_user_id] = {"saldo": 0, "has_deposited": True}  # Inisialisasi dan set sudah deposit

        if "saldo" not in user_data[target_user_id]:
            user_data[target_user_id]["saldo"] = 0  # Inisialisasi saldo

        user_data[target_user_id]["saldo"] += amount
        user_data[target_user_id]["has_deposited"] = True  # ✅ Tandai user sebagai sudah deposit

        total_saldo = user_data[target_user_id]["saldo"]

        # **Kirim konfirmasi ke admin yang melakukan top-up**
        await update.message.reply_text(
            f"✅ Saldo pengguna {target_user_id} berhasil ditambahkan sebesar {amount}.\n"
            f"Total saldo sekarang: {total_saldo}"
        )

        # **Kirim notifikasi ke user yang menerima saldo**
        keyboard = [[InlineKeyboardButton("💰 Cek Saldo", callback_data="cek_saldo")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎉 Selamat! Saldo sebesar {amount} telah berhasil ditambahkan ke akun Anda.\n"
                     f"Total saldo saat ini: {total_saldo}",
                reply_markup=reply_markup
            )
        except Exception:
            await update.message.reply_text(f"⚠️ Tidak bisa mengirim pesan ke {target_user_id}. User mungkin belum memulai bot.")

    except ValueError:
        await update.message.reply_text("⚠️ Masukkan angka yang valid.")

       # Tambahkan fungsi handle_withdraw sebelum main()
async def handle_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_status = user_data.get(user_id, {}).get("status", "")

    logging.info(f"User {user_id} mengirim nomor rekening. Status: {user_status}")

    if user_status != "waiting_for_rekening":
        await update.message.reply_text("⚠️ Anda belum memilih menu tarik saldo.")
        return

    rekening_info = update.message.text.strip()
    
    if ":" not in rekening_info:
        await update.message.reply_text(
            "⚠️ Format tidak valid! Gunakan format:\n\n"
            "`Nomor Rekening : Nama Bank`\n\n"
            "Contoh: `081234567890 : Dana`",
            parse_mode="Markdown"
        )
        return

    saldo = user_data[user_id].get("saldo", 0)

    if saldo < 10000:
        await update.message.reply_text("⚠️ Saldo Anda tidak mencukupi untuk melakukan penarikan.")
        return

    # Kurangi saldo setelah permintaan dikirim
    user_data[user_id]["saldo"] -= 10000
    user_data[user_id]["status"] = None
    user_data[user_id]["withdraw_time"] = time.time()

    # Kirim notifikasi ke admin
    if ADMIN_ID:
        logging.info(f"Mengirim permintaan penarikan dari {user_id} ke ADMIN_ID {ADMIN_ID}")
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 Permintaan penarikan dari @{update.message.from_user.username} ({user_id})\n\n"
                 f"🏦 Rekening: {rekening_info}\n"
                 f"💰 Jumlah: 10000 IDR\n\nSilakan proses."
        )
        keyboard = [[InlineKeyboardButton("🔙 Kembali ke Menu", callback_data="start")]] 
        reply_markup = InlineKeyboardMarkup(keyboard)
    
    
    await update.message.reply_text(
        "✅ Permintaan Anda telah dikirim ke admin. Saldo Anda telah dikurangi. Penarikan Hanya bisa 10000 sekali penarikan \n\n"
        "⏳ Proses bisa memakan waktu hingga *24 jam*.\n"
        "Jika lebih dari *24 jam* belum diproses, silakan hubungi admin.",
        parse_mode="Markdown",
        reply_markup=reply_markup
        
    )
async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    if query.data == "pertandingan":
        # Tampilkan pilihan bet
        bet_buttons = [
            [InlineKeyboardButton(f"{amount} IDR", callback_data=f"bet_{amount}")]
            for amount in [100, 500, 1000, 2000, 5000, 10000, 50000]
        ]
        await query.message.edit_text(
            f"💰 Saldo Anda: {saldo} IDR\n\nPilih jumlah taruhan:",
            reply_markup=InlineKeyboardMarkup(bet_buttons)
        )

    elif query.data.startswith("bet_"):
        # Ambil jumlah bet
        bet = int(query.data.split("_")[1])

        # Pastikan saldo cukup
        if saldo < bet:
            await query.answer("Saldo tidak cukup!", show_alert=True)
            return

        # Simpan jumlah bet sementara
        context.user_data["bet"] = bet

        # Pilihan suit
        suit_buttons = [
            [InlineKeyboardButton("🪨 Batu", callback_data="suit_Batu")],
            [InlineKeyboardButton("✂️ Gunting", callback_data="suit_Gunting")],
            [InlineKeyboardButton("📜 Kertas", callback_data="suit_Kertas")]
        ]
        await query.message.edit_text(
            f"✅ Anda bertaruh {bet} IDR.\n\nPilih tangan Anda:",
            reply_markup=InlineKeyboardMarkup(suit_buttons)
        )

    elif query.data.startswith("suit_"):
        # Ambil pilihan user
        user_choice = query.data.split("_")[1]
        bot_choice = random.choice(["Batu", "Gunting", "Kertas"])

        # Logika menang/kalah
        suit_rules = {"Batu": "Gunting", "Gunting": "Kertas", "Kertas": "Batu"}

        if user_choice == bot_choice:
            result = "🤝 Seri!"
            new_saldo = saldo
        elif suit_rules[user_choice] == bot_choice:
            result = "🎉 Anda menang!"
            winnings = int(context.user_data["bet"] * 1.8)  # Menang 180%
            new_saldo = saldo + winnings
        else:
            result = "😢 Anda kalah!"
            new_saldo = saldo - context.user_data["bet"]

        # Update saldo
        user_data[user_id]["saldo"] = new_saldo

        # Kirim hasil pertandingan
        await query.message.edit_text(
            f"👤 Anda: {user_choice}\n🤖 Bot: {bot_choice}\n\n{result}\n\n💰 Saldo Anda sekarang: {new_saldo} IDR",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="start")]])
        )



# Fungsi utama untuk menjalankan bot
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addsaldo", add_saldo))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_bukti))
    

    # Pisahkan handler deposit dan withdraw agar tidak bentrok
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_withdraw))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_deposit))

    logging.info("🚀 Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
