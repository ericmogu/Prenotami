from playwright.sync_api import sync_playwright
import imapclient
import pyzmail


# Set up Playwright and launch the browser
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://prenotami.esteri.it/UserArea')

    # Step 1: Enter email and request OTP
    page.fill('#email', 'your_email@example.com')
    page.click('#request_otp')

    # Step 2: Fetch OTP from email using IMAPClient for users and more
    with imapclient.IMAPClient('imap.gmail.com') as client:
        client.login('your_email@example.com', 'your_password')
        client.select_folder('INBOX')
        messages = client.search(['UNSEEN'])
        otp_code = None
        for msgid, data in client.fetch(messages, 'RFC822').items():
            email_message = pyzmail.PyzMessage.factory(data[b'RFC822'])
            if 'Your OTP' in email_message.get_subject():
                email_content = email_message.text_part.get_payload().decode('utf-8')
                otp_code = email_content.strip()  # Simplistic OTP extraction, refine as needed
                break

    # Ensure OTP was found
    if otp_code:
        # Step 3: Enter OTP and submit
        page.fill('#otp', otp_code)
        page.click('#submit')

        # Step 4: Navigate to reservation section
        page.click('a[href="/ReservationLink"]')
        page.click('a:has-text("Third Option")')

        # Step 5: Check for availability
        if page.is_visible('.no-availability-popup'):
            print("No availability found.")
        else:
            print("Availability found, selecting date.")
            available_date = page.query_selector('.calendar-green')
            if available_date:
                available_date.click()
            else:
                print("No green dates available.")

    else:
        print("OTP not found in email.")

    # Close the browser
    browser.close()
