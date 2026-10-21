import os, random, asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

verified_users = set()
captcha_answers = {}

def create_math_captcha(user_id: int):
    a, b = random.randint(1, 9), random.randint(1, 9)
    ans = a + b
    captcha_answers[user_id] = ans
    options = {ans}
    while len(options) < 4:
        options.add(random.randint(2, 18))
    opts = list(options)
    random.shuffle(opts)

    builder = InlineKeyboardBuilder()
    for opt in opts:
        builder.button(text=str(opt), callback_data=f"verify_{opt}")
    builder.adjust(4)

    text = f"🛡️ **人机安全验证**\n\n为防范垃圾广告，请点击正确答案：\n👉 **{a} + {b} = ?**"
    return text, builder.as_markup()

@dp.callback_query(F.data.startswith("verify_"))
async def handle_captcha_click(query: types.CallbackQuery):
    user_id = query.from_user.id
    selected = int(query.data.split("_")[1])
    if selected == captcha_answers.get(user_id):
        verified_users.add(user_id)
        captcha_answers.pop(user_id, None)
        await query.message.edit_text("✅ 验证通过！现在您可以发送留言，管理员将收到传话。")
        await query.answer("验证成功！")
    else:
        text, kb = create_math_captcha(user_id)
        await query.message.edit_text(f"❌ 计算错误，请重试：\n\n{text}", reply_markup=kb, parse_mode="Markdown")
        await query.answer("答案错误", show_alert=True)

@dp.message(F.chat.type == "private")
async def forward_router(message: types.Message):
    user_id = message.from_user.id

    if user_id == ADMIN_ID:
        if message.reply_to_message and message.reply_to_message.forward_from:
            await message.copy_to(chat_id=message.reply_to_message.forward_from.id)
            await message.reply("✅ 已回传对方")
        return

    if user_id not in verified_users:
        text, kb = create_math_captcha(user_id)
        await message.reply(text, reply_markup=kb, parse_mode="Markdown")
        return

    await message.forward(chat_id=ADMIN_ID)
    await message.reply("📨 消息已转交管理员。")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
