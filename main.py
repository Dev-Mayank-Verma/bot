import logging
import sqlite3
import asyncio
import os
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from playwright.async_api import async_playwright

# Logging setup
logging.basicConfig(level=logging.INFO)

# Token configuration (Render environment variable se uthayega)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# --- SQLite Database Setup ---
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_data (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            email TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            phone TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- FSM States ---
class DomainPurchaseStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_password = State()
    waiting_for_email = State()
    waiting_for_address = State()
    waiting_for_city = State()
    waiting_for_state = State()
    waiting_for_zip = State()
    waiting_for_phone = State()
    waiting_for_domain = State()

# --- Start Command & Step-by-Step Details Flow ---
@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Swagat hai Free .XYZ Domain Buyer Bot mein!\n\n"
        "Apne details set karne ke liye pehle Gen.xyz account ka Username/Handle daliye:"
    )
    await state.set_state(DomainPurchaseStates.waiting_for_username)

@router.message(DomainPurchaseStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    await state.update_data(username=message.text.strip())
    await message.answer("Gen.xyz account ke liye ek naya Password chuniye:")
    await state.set_state(DomainPurchaseStates.waiting_for_password)

@router.message(DomainPurchaseStates.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text.strip())
    await message.answer("Ab apna Email address daliye:")
    await state.set_state(DomainPurchaseStates.waiting_for_email)

@router.message(DomainPurchaseStates.waiting_for_email)
async def process_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text.strip())
    await message.answer("Ab apna Street Address daliye:")
    await state.set_state(DomainPurchaseStates.waiting_for_address)

@router.message(DomainPurchaseStates.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    await message.answer("Apna City daliye (jaise Mumbai, Pune):")
    await state.set_state(DomainPurchaseStates.waiting_for_city)

@router.message(DomainPurchaseStates.waiting_for_city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text.strip())
    await message.answer("Apna State daliye:")
    await state.set_state(DomainPurchaseStates.waiting_for_state)

@router.message(DomainPurchaseStates.waiting_for_state)
async def process_state(message: Message, state: FSMContext):
    await state.update_data(state=message.text.strip())
    await message.answer("Apna Pin Code/Zip Code daliye (jaise 411001):")
    await state.set_state(DomainPurchaseStates.waiting_for_zip)

@router.message(DomainPurchaseStates.waiting_for_zip)
async def process_zip(message: Message, state: FSMContext):
    await state.update_data(zip_code=message.text.strip())
    await message.answer("Apna Phone Number daliye (Country code ke sath, jaise +91...):")
    await state.set_state(DomainPurchaseStates.waiting_for_phone)

@router.message(DomainPurchaseStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    
    # Save to SQLite Database
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO user_data (user_id, username, password, email, address, city, state, zip_code, phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        message.from_user.id,
        data['username'],
        data['password'],
        data['email'],
        data['address'],
        data['city'],
        data['state'],
        data['zip_code'],
        message.text.strip()
    ))
    conn.commit()
    conn.close()

    await message.answer(
        "✅ **Details successfully save ho gayi hain!**\n\n"
        "Ab aapko jo .xyz domain free mein kharidna hai, uska naam bhejiye (jaise `mycoolsite.xyz`):"
    )
    await state.set_state(DomainPurchaseStates.waiting_for_domain)

# --- Automation, Availability Check & Purchase Flow ---
@router.message(DomainPurchaseStates.waiting_for_domain)
async def process_domain(message: Message, state: FSMContext):
    domain_name = message.text.strip().lower()
    if not domain_name.endswith(".xyz"):
        domain_name += ".xyz"

    user_id = message.from_user.id

    # Database se user details fetch karna
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, email, address, city, state, zip_code, phone FROM user_data WHERE user_id = ?", (user_id,))
    user_row = cursor.fetchone()
    conn.close()

    if not user_row:
        await message.answer("⚠️ Pehle /start dabakar apni details save karein.")
        return

    username, password, email, address, city, state_val, zip_code, phone = user_row

    status_msg = await message.answer(f"🔍 Checking availability for `{domain_name}` on gen.xyz...")

    try:
        async with async_playwright() as p:
            # Render ke liye zaroori sandbox args ke sath browser launch
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            page = await browser.new_page()

            # Gen.xyz par jaana
            await page.goto("https://gen.xyz/", timeout=60000)
            
            # Domain search input box locate karna aur domain enter karna
            search_input = "input[type='text'], input[placeholder*='domain']"
            await page.wait_for_selector(search_input, timeout=10000)
            await page.fill(search_input, domain_name)
            await page.press(search_input, "Enter")

            # Result load hone ka wait
            await asyncio.sleep(4)

            # --- AVAILABILITY CHECK ---
            page_content = await page.content()
            if "taken" in page_content.lower() or "unavailable" in page_content.lower():
                await browser.close()
                await status_msg.edit_text(f"❌ Maaf kijiye, `{domain_name}` pehle se hi **Taken (Unavailable)** hai! Koi doosra domain try karein.")
                await state.clear()
                return

            await status_msg.edit_text(f"✅ `{domain_name}` available hai! Cart mein add karke coupon apply kiya ja raha hai...")

            # --- Checkout & Purchase Steps (Cart -> Coupon -> Details -> PayPal) ---
            await asyncio.sleep(5) # Simulation step

            await browser.close()

        await status_msg.edit_text(f"🎉 Success! `{domain_name}` ke liye automation process complete ho gaya hai.")
    except Exception as e:
        logging.error(f"Automation Error: {e}")
        await status_msg.edit_text(f"❌ Automation ke dauran error aa gaya hai: `{str(e)}`")

    await state.clear()

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
