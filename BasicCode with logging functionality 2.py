import logging
from playwright.sync_api import sync_playwright
import imapclient
import pyzmail
import smtplib

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Step 1: Start Playwright and launch browser
logging.info("Starting Playwright and launching browser.")
playwright = sync_playwright().start()
browser = playwright.chromium.launch(headless=False)  # Set to True for headless mode
page = browser.new_page()

# Step 2: Navigate to the website
logging.info("Navigating to https://prenotami.esteri.it/UserArea.")
page.goto('https://prenotami.esteri.it/UserArea')

# Step 3: Enter email and request OTP
logging.info("Filling in email and requesting OTP.")
page.fill('#login-email', 'your_email@example.com')
page.click('#request_otp')

# Step 4: Fetch OTP from email
logging.info("Connecting to email to retrieve OTP.")
client = imapclient.IMAPClient('imap.gmail.com')
client.login('your_email@example.com', 'your_password')
client.select_folder('INBOX')

logging.info("Searching for OTP email.")
messages = client.search(['UNSEEN'])
otp_code = None
for msgid, data in client.fetch(messages, 'RFC822').items():
    email_message = pyzmail.PyzMessage.factory(data[b'RFC822'])
    if 'Your OTP' in email_message.get_subject():
        logging.info("OTP email found.")
        email_content = email_message.text_part.get_payload().decode('utf-8')
        otp_code = email_content.strip()  # Simplistic, refine as needed
        logging.info(f"Extracted OTP: {otp_code}")
        break

if not otp_code:
    logging.error("OTP code not found in emails.")
    browser.close()
    playwright.stop()
    exit()

# Step 5: Enter OTP and submit
logging.info("Entering OTP on the website.")
page.fill('#otp', otp_code)
page.click('#submit')

# Step 6: Navigate to the reservation section
logging.info("Navigating to reservation section.")
page.click('a[href="/ReservationLink"]')

logging.info("Selecting the third option from the list.")
page.click('a:has-text("Third Option")')

# Step 7: Check for availability
logging.info("Checking for availability.")
if page.is_visible('.no-availability-popup'):
    logging.info("No availability found.")
else:
    logging.info("Availability found, selecting date.")
    available_date = page.query_selector('.calendar-green')
    if available_date:
        available_date.click()
        logging.info("Date selected successfully.")
    else:
        logging.warning("No available dates found in the calendar.")

# Step 8: Send notification (example)
logging.info("Sending notification email.")
from_email = 'your_email@example.com'
to_email = 'your_email@example.com'
message = f'Subject: Appointment Booking Status\n\nBooking process completed.'

with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
    server.login(from_email, 'your_password')
    server.sendmail(from_email, to_email, message)

logging.info("Notification email sent successfully.")

# Step 9: Close browser and stop Playwright
logging.info("Closing browser and stopping Playwright.")
browser.close()
playwright.stop()
