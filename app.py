import streamlit as st
import asyncio
from playwright.async_api import async_playwright
import os
from twilio.rest import Client

st.set_page_config(page_title="UK Driving Test Bot", page_icon="🚗", layout="centered")

# Initialize session state variables
if "running" not in st.session_state:
    st.session_state.running = False
if "slots_found" not in st.session_state:
    st.session_state.slots_found = 0

st.title("🚗 UK Driving Test Bot Dashboard")
st.markdown("Fast, local automation tool to monitor slots and send instant WhatsApp alerts.")

# Configuration Form
with st.form("bot_config_form"):
    st.subheader("Bot Settings & Credentials")
    license_number = st.text_input("Driving License Number", placeholder="e.g. ABCDE123456789")
    reference_number = st.text_input("Booking Reference Number", placeholder="e.g. 12345678")
    proxy_url = st.text_input("Proxy URL (optional)", placeholder="http://username:password@ip:port")
    whatsapp_to = st.text_input("WhatsApp Number (with country code)", placeholder="447123456789")
    
    col1, col2 = st.columns(2)
    with col1:
        start_btn = st.form_submit_button("🚀 Start Bot", use_container_width=True)
    with col2:
        stop_btn = st.form_submit_button("🛑 Stop Bot", use_container_width=True)

# Twilio WhatsApp Alert Function
def send_whatsapp_alert(to_number, message):
    try:
        twilio_sid = os.getenv("TWILIO_SID", "your_twilio_sid")
        twilio_auth = os.getenv("TWILIO_AUTH_TOKEN", "your_auth_token")
        client = Client(twilio_sid, twilio_auth)
        client.messages.create(
            body=message,
            from_="whatsapp:+14155238886",
            to=f"whatsapp:{to_number}"
        )
    except Exception as e:
        st.error(f"Failed to send WhatsApp alert: {e}")

# Core Playwright Automation Loop
async def run_booking_bot(license, ref, proxy, phone):
    st.session_state.running = True
    browser_args = {}
    if proxy:
        browser_args["proxy"] = {"server": proxy}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, **browser_args)
        context = await browser.new_context()
        page = await context.new_page()

        status_placeholder = st.empty()
        status_placeholder.info("Bot is active and running background checks...")

        try:
            while st.session_state.running:
                # --- INSERT DVSA AUTOMATION LOGIC HERE ---
                # Example: await page.goto("https://www.gov.uk/book-driving-test")
                
                # Simulated delay between checking cycles to avoid blocks
                await asyncio.sleep(10)
                
                # Mock check result
                slot_found = False # Change to True when criteria match
                
                if slot_found:
                    st.session_state.slots_found += 1
                    msg = f"🚨 Driving Test Slot Found for License {license}!"
                    send_whatsapp_alert(phone, msg)
                    st.success(msg)
                    break
                    
        except Exception as e:
            st.error(f"Bot encountered an error: {e}")
        finally:
            await browser.close()
            st.session_state.running = False
            status_placeholder.empty()

# Handle Button Interactions
if start_btn:
    if not license_number or not whatsapp_to:
        st.warning("Please enter at least your License Number and WhatsApp Number.")
    else:
        st.success("Initialization signal sent. Starting bot...")
        asyncio.run(run_booking_bot(license_number, reference_number, proxy_url, whatsapp_to))

if stop_btn:
    st.session_state.running = False
    st.warning("Stop signal sent to the background worker.")

# Live Status Metrics Dashboard
st.divider()
metric_col1, metric_col2 = st.columns(2)
with metric_col1:
    if st.session_state.running:
        st.metric(label="System Status", value="Running 🟢")
    else:
        st.metric(label="System Status", value="Stopped 🔴")
with metric_col2:
    st.metric(label="Slots Found", value=st.session_state.slots_found)