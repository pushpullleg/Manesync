from playwright.sync_api import sync_playwright
import time

# Simple automation: Open Google, search, close tab
class SimpleBot:
    def __init__(self):
        self.search_term = "Python automation"
    
    def run(self):
        with sync_playwright() as p:
            # Launch Google Chrome (set headless=False to see the browser)
            browser = p.chromium.launch(
                headless=False,
                channel="chrome"  # Use Google Chrome instead of Chromium
            )
            page = browser.new_page()
            
            # 1. Open Google
            print("Opening Google...")
            page.goto("https://google.com")
            time.sleep(2)
            
            # 2. Type in search box
            print("Typing search term...")
            page.fill('textarea[name="q"]', self.search_term)
            
            # 3. Submit
            print("Submitting search...")
            page.press('textarea[name="q"]', 'Enter')
            
            # Wait to see results
            time.sleep(3)
            
            print("Done!")
            
            # Keep browser open - user will close manually
            input("Press Enter to close the browser...")
            
            # Close browser
            browser.close()

# Run it
if __name__ == "__main__":
    bot = SimpleBot()
    bot.run()