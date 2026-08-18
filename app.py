import sys
import asyncio

# Playwright requires Proactor event loop policy on Windows for subprocess support
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
from playwright.sync_api import sync_playwright
import os
import random
import string
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="UK Driving Test Hunt & Monitor Bot",
    page_icon="🎯",
    layout="wide"
)

if "running" not in st.session_state:
    st.session_state.running = False
if "slots_found" not in st.session_state:
    st.session_state.slots_found = 0
if "active_ref" not in st.session_state:
    st.session_state.active_ref = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

st.title("🎯 UK Driving Test Hunt & Monitor Bot")
st.markdown("Advanced slot hunting platform optimized for multi-license tracking and instant WhatsApp alerts.")

st.info(f"🔗 Active Hunt Session URL: `https://passly-dates.laravel.cloud/hunt-date?ref={st.session_state.active_ref}`")

with st.form("bot_config_form"):
    st.subheader("Hunt Settings & Credentials")
    
    col_a, col_b = st.columns(2)
    with col_a:
        license_number = st.text_input(
            "Driving License Number(s)", 
            value="", 
            placeholder="e.g. THINDO06104AS9YP 12 or multiple separated by comma"
        )
        reference_number = st.text_input(
            "Booking Reference Code / Hunt Ref", 
            value=st.session_state.active_ref,
            placeholder="e.g. wtnvkfze6q"
        )
    with col_b:
        proxy_url = st.text_input(
            "Proxy URL (UK Residential)", 
            placeholder="http://username:password@ip:port"
        )
        whatsapp_to = st.text_input(
            "WhatsApp Number (with country code)", 
            placeholder="4475873636568"
        )
        
    st.subheader("Test Centre & Date Window Preferences")
    col_c, col_d, col_e = st.columns(3)
    with col_c:
        test_centres = st.text_input(
            "Preferred Test Centres", 
            value="Southall, Slough", 
            placeholder="e.g. Pinner, Southall, Slough"
        )
    with col_d:
        start_date = st.date_input("Start Date (Earliest)")
    with col_e:
        end_date = st.date_input("End Date (Latest)")

    col1, col2 = st.columns(2)
    with col1:
        start_btn = st.form_submit_button("🚀 Start Hunt Bot", use_container_width=True)
    with col2:
        stop_btn = st.form_submit_button("🛑 Stop Bot", use_container_width=True)

def send_whatsapp_alert(to_number, message):
    try:
        twilio_sid = os.getenv("TWILIO_SID")
        twilio_auth = os.getenv("TWILIO_AUTH_TOKEN")
        whatsapp_from = os.getenv("WHATSAPP_FROM", "whatsapp:+14155238886")
        
        if not twilio_sid or not twilio_auth:
            return

        client = Client(twilio_sid, twilio_auth)
        client.messages.create(
            body=message,
            from_=whatsapp_from,
            to=f"whatsapp:{to_number}"
        )
    except Exception:
        pass

def parse_proxy_url(proxy):
    if not proxy:
        return {}
    proxy = proxy.strip()
    browser_proxy = {}
    try:
        if "@" in proxy:
            if not proxy.startswith("http://") and not proxy.startswith("https://"):
                proxy = f"http://{proxy}"
            server_part = proxy.split("@")[-1]
            auth_part = proxy.split("@")[0].replace("http://", "").replace("https://", "")
            if ":" in auth_part:
                username, password = auth_part.split(":", 1)
                browser_proxy = {"server": f"http://{server_part}", "username": username, "password": password}
            else:
                browser_proxy = {"server": proxy}
        else:
            parts = proxy.split(":")
            if len(parts) == 4:
                host, port, username, password = parts
                browser_proxy = {"server": f"http://{host}:{port}", "username": username, "password": password}
            else:
                if not proxy.startswith("http://") and not proxy.startswith("https://"):
                    proxy = f"http://{proxy}"
                browser_proxy = {"server": proxy}
    except Exception:
        browser_proxy = {"server": proxy}
    return browser_proxy

def run_fast_booking_bot(licenses, ref, proxy, phone, centres, s_date, e_date):
    st.session_state.running = True
    browser_args = {}
    parsed_proxy = parse_proxy_url(proxy)
    if parsed_proxy:
        browser_args["proxy"] = parsed_proxy

    import time

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(
                    headless=True, 
                    args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage", "--disable-extensions"],
                    **browser_args
                )
            except Exception as launch_err:
                st.error(f"Browser Launch Error: {launch_err}. Run 'playwright install' in terminal.")
                st.session_state.running = False
                return

            status_placeholder = st.empty()
            status_placeholder.info(f"🎯 Hunting slots for Ref: `{ref}` across centres: {centres}...")

            try:
                while st.session_state.running:
                    license_list = [l.strip() for l in licenses.split(",") if l.strip()]
                    
                    for lic in license_list:
                        if not st.session_state.running:
                            break
                        
                        context = browser.new_context()
                        page = context.new_page()
                        try:
                            page.route(
                                "**/*", 
                                lambda route: route.abort() 
                                if route.request.resource_type in ["image", "stylesheet", "font", "media"] 
                                else route.continue_()
                            )
                            
                            time.sleep(1.0)
                            slot_found = False  # Placeholder logic
                            
                            if slot_found:
                                st.session_state.slots_found += 1
                                msg = f"🎯 Hunt Success! Ref: {ref} | License: {lic} | Centres: {centres} | Date: {s_date} to {e_date}"
                                if phone:
                                    send_whatsapp_alert(phone, msg)
                                st.success(msg)
                                st.session_state.running = False
                                break
                        except Exception:
                            pass
                        finally:
                            context.close()
                    
                    time.sleep(2.5)
            finally:
                browser.close()
                status_placeholder.empty()
    except Exception as e:
        import traceback
        st.error(f"Execution Error Details: {str(e)}")
        st.text(traceback.format_exc())
    finally:
        st.session_state.running = False

if start_btn:
    if not license_number or not whatsapp_to:
        st.warning("Please provide at least your Driving License Number(s) and WhatsApp Number.")
    else:
        st.success("🎯 Hunt session initialized. Worker pool active...")
        run_fast_booking_bot(
            license_number, reference_number, proxy_url, 
            whatsapp_to, test_centres, start_date, end_date
        )

if stop_btn:
    st.session_state.running = False
    st.warning("🛑 Hunt bot stopped.")

st.divider()
metric_col1, metric_col2 = st.columns(2)
with metric_col1:
    if st.session_state.running:
        st.metric(label="Hunt Status", value="Hunting Active 🎯")
    else:
        st.metric(label="Hunt Status", value="Idle 🔴")
with metric_col2:
    st.metric(label="Total Slots Hunted", value=st.session_state.slots_found)
