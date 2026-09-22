import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from playwright.async_api import async_playwright
from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)
router = Router()

def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            user_id INTEGER,
            domain TEXT,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            phone TEXT,
            password TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class DomainPurchaseStates(StatesGroup):
    waiting_for_domain = State()
    waiting_for_firstname = State()
    waiting_for_lastname = State()
    waiting_for_email = State()
    waiting_for_address = State()
    waiting_for_city = State()
    waiting_for_state = State()
    waiting_for_zip = State()
    waiting_for_phone = State()
    waiting_for_password = State()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Welcome! Apna desired .xyz domain name bhejiye (jaise example.xyz):")
    await state.set_state(DomainPurchaseStates.waiting_for_domain)

@router.message(DomainPurchaseStates.waiting_for_domain)
async def process_domain(message: Message, state: FSMContext):
    await state.update_data(domain=message.text.strip())
    await message.answer("Ab apna First Name daliye:")
    await state.set_state(DomainPurchaseStates.waiting_for_firstname)

@router.message(DomainPurchaseStates.waiting_for_firstname)
async def process_firstname(message: Message, state: FSMContext):
    await state.update_data(first_name=message.text.strip())
    await message.answer("Ab apna Last Name daliye:")
    await state.set_state(DomainPurchaseStates.waiting_for_lastname)

@router.message(DomainPurchaseStates.waiting_for_lastname)
async def process_lastname(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text.strip())
    await message.answer("Ab apna Email Address daliye (jis par verification aayegi)[span_2](start_span)[span_2](end_span):")
    await state.set_state(DomainPurchaseStates.waiting_for_email)

@router.message(DomainPurchaseStates.waiting_for_email)
async def process_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text.strip())
    await message.answer("Ab apna Street Address daliye:")
    await state.set_state(DomainPurchaseStates.waiting_for_address)


@router.message(DomainPurchaseStates.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    await message.answer("City ka naam daliye:")
    await state.set_state(DomainPurchaseStates.waiting_for_city)

@router.message(DomainPurchaseStates.waiting_for_city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text.strip())
    await message.answer("State ka naam daliye:")
    await state.set_state(DomainPurchaseStates.waiting_for_state)

@router.message(DomainPurchaseStates.waiting_for_state)
async def process_state(message: Message, state: FSMContext):
    await state.update_data(state=message.text.strip())
    await message.answer("Zip/Postal Code daliye:")
    await state.set_state(DomainPurchaseStates.waiting_for_zip)

@router.message(DomainPurchaseStates.waiting_for_zip)
async def process_zip(message: Message, state: FSMContext):
    await state.update_data(zip_code=message.text.strip())
    await message.answer("Phone Number daliye (country code ke sath, jaise +1...):")
    await state.set_state(DomainPurchaseStates.waiting_for_phone)

@router.message(DomainPurchaseStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    await message.answer("Gen.xyz account ke liye ek naya Password chuniye:")
    await state.set_state(DomainPurchaseStates.waiting_for_password)

@router.message(DomainPurchaseStates.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text.strip())
    data = await state.get_data()
    
    await message.answer("Details mil gayi hain! Automation shuru ho raha hai, kripya intezaar karein...")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True) # Set headless=False karke aap screen par dekh sakte hain kya ho raha hai
            page = await browser.new_page()
            
            # 1. Open Gen.xyz
            await page.goto("https://gen.xyz/")
            
            # 2. Search Domain
            await page.fill("input[placeholder*='Enter the domain']", data['domain'])
            await page.click("button:has-text('Register')")
            await page.wait_for_selector("text=It's available", timeout=10000)
            
            # 3. Add to cart & Go to checkout
            await page.click("text=Added")
            await page.click("text=Go to checkout")
            
            # 4. Change Term from 3 Years to 1 Year (Jaise video mein 1-year select kiya tha)[span_3](start_span)[span_3](end_span)
            await page.select_option("select", label="1 year") # Dropdown se 1 year select karna
            
            # 5. Handle Add-ons (Click No Thanks)[span_4](start_span)[span_4](end_span)
            await page.click("text=No Thanks")
            await page.click("text=Next: Information & Checkout")
            
            # 6. Apply Coupon Code HFY26 to make it $0[span_5](start_span)[span_5](end_span)
            await page.fill("input[placeholder*='Promotional Code']", "HFY26")
            await page.click("text=Apply Code")
            
            # 7. Fill User Information (New Customer)[span_6](start_span)[span_6](end_span)
            await page.click("text=New Customer")
            await page.fill("input[name='firstname']", data['first_name'])
            await page.fill("input[name='lastname']", data['last_name'])
            await page.fill("input[name='email']", data['email'])
            await page.fill("input[name='address1']", data['address'])
            await page.fill("input[name='city']", data['city'])
            await page.fill("input[name='state']", data['state'])
            await page.fill("input[name='postcode']", data['zip_code'])
            await page.fill("input[name='phonenumber']", data['phone'])
            await page.fill("input[name='password']", data['password'])
            
            # 8. Select PayPal as Payment Method[span_7](start_span)[span_7](end_span)
            await page.click("text=PayPal")
            
            # 9. Agree to Terms & Conditions checkbox and Submit Order[span_8](start_span)[span_8](end_span)
            await page.check("input[type='checkbox']")
            await page.click("text=Submit Order")
            
            # 10. Wait for confirmation[span_9](start_span)[span_9](end_span)
            await page.wait_for_selector("text=Order Confirmation", timeout=15000)
            
            await browser.close()
            
        await message.answer("Order successfully place ho gaya hai! Kripya apna email check karein aur verification complete karein[span_10](start_span)[span_10](end_span).")
    
    except Exception as e:
        logging.error(f"Automation Error: {e}")
        await message.answer("Automation ke dauran koi error aa gaya hai. Kripya baad mein dobara koshish karein.")
        
    await state.clear()

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
