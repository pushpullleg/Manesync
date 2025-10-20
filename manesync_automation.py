"""
Manesync Automation - Standalone Executable Script
Save this as: manesync_automation.py
Run with: python manesync_automation.py
"""

import time
import random
from datetime import datetime
import json
import subprocess
import sys

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("❌ Selenium not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
    print("✅ Selenium installed. Please run the script again.")
    sys.exit(0)


class ManesyncAutomation:
    def __init__(self, iterations):
        self.iterations = iterations
        self.login_url = "https://manesync.tamuc.edu/login_only"
        self.evidence_log = []
        self.driver = None
        
    def setup_driver(self, profile_path=None):
        """Initialize Chrome WebDriver with user profile"""
        print("🌐 Launching Chrome browser...")
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        
        # Use user's Chrome profile to maintain login sessions
        if profile_path:
            print(f"📂 Using Chrome profile: {profile_path}")
            options.add_argument(f"--user-data-dir={profile_path}")
            # Optional: specify profile directory name (usually "Default" or "Profile 1")
            # options.add_argument("--profile-directory=Default")
        else:
            print("⚠️  No profile specified, using default")
            
        # Keep browser open
        options.add_experimental_option("detach", True)
        
        # Disable automation flags to avoid detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        try:
            self.driver = webdriver.Chrome(options=options)
            print("✅ Browser launched successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to launch browser: {e}")
            print("\n💡 Make sure ChromeDriver is installed:")
            print("   pip install webdriver-manager")
            return False
            
    def random_delay(self, min_seconds=0.5, max_seconds=2):
        """Add random delay"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        
    def calculate_points(self, completed):
        """Calculate points: 5 iterations = 2 points"""
        return (completed / 5) * 2
        
    def log_evidence(self, iteration, status, message=""):
        """Log iteration evidence"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        completed = len([e for e in self.evidence_log if e['status'] == 'SUCCESS'])
        points = self.calculate_points(completed)
        
        evidence = {
            "iteration": iteration,
            "timestamp": timestamp,
            "status": status,
            "points": round(points, 2),
            "message": message
        }
        
        self.evidence_log.append(evidence)
        icon = "✓" if status == "SUCCESS" else "✗"
        print(f"[{timestamp}] {icon} Iteration {iteration}/{self.iterations} - {status}")
        if message:
            print(f"  └─ {message}")
            
    def save_evidence(self):
        """Save evidence to JSON"""
        successful = len([e for e in self.evidence_log if e['status'] == 'SUCCESS'])
        filename = f"manesync_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        summary = {
            "run_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_iterations": self.iterations,
            "completed_successfully": successful,
            "failed_iterations": self.iterations - successful,
            "total_points": round(self.calculate_points(successful), 2),
            "success_rate": f"{(successful/self.iterations)*100:.1f}%",
            "detailed_log": self.evidence_log
        }
        
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"\n📄 Evidence saved to: {filename}")
        
    def wait_for_element(self, by, value, timeout=10):
        """Wait for element to be clickable"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except TimeoutException:
            return None
            
    def login_sequence(self, iteration):
        """Execute login"""
        try:
            print("\n🔐 LOGIN PHASE")
            
            # Step 1: Open login page
            print("→ Step 1: Opening login page")
            self.driver.get(self.login_url)
            time.sleep(3)
            
            # Step 2: Click SSO button
            print("→ Step 2: Finding ETAMU SSO button")
            
            # Try multiple strategies to find SSO button
            sso_clicked = False
            
            # Strategy 1: Link with text containing ETAMU or SSO
            try:
                links = self.driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    text = link.text.upper()
                    if "ETAMU" in text or "SSO" in text:
                        print(f"  └─ Found button: {link.text}")
                        link.click()
                        sso_clicked = True
                        break
            except:
                pass
                
            # Strategy 2: Link with href containing /cas/tamuc
            if not sso_clicked:
                try:
                    sso_link = self.driver.find_element(By.CSS_SELECTOR, 'a[href*="/cas/tamuc"]')
                    print(f"  └─ Found SSO link via href")
                    sso_link.click()
                    sso_clicked = True
                except:
                    pass
                    
            if not sso_clicked:
                raise Exception("Could not find SSO button")
                
            print("  ✓ SSO button clicked")
            time.sleep(4)
            
            # Step 3: Handle MFA on first iteration
            if iteration == 1:
                print("\n⚠️  MANUAL MFA REQUIRED")
                print("   Complete authentication in the browser")
                print("   Press ENTER when you see the logged-in dashboard...")
                input()
            else:
                time.sleep(3)
                
            # Step 4: Verify login
            print("→ Step 3: Verifying login")
            current_url = self.driver.current_url
            if 'web_app' in current_url:
                print("  ✓ Login successful!")
                return True
            else:
                raise Exception(f"Not on logged-in page. URL: {current_url}")
                
        except Exception as e:
            print(f"  ✗ Login failed: {e}")
            return False
            
    def logout_sequence(self):
        """Execute logout"""
        try:
            print("\n🚪 LOGOUT PHASE")
            
            # Step 1: Find and click account dropdown
            print("→ Step 1: Finding account dropdown")
            
            # Try to find dropdown in top right
            dropdown_clicked = False
            
            # Strategy 1: Look for common selectors
            selectors = [
                '[class*="account"]',
                '[class*="user"]',
                '[class*="profile"]',
                '[class*="dropdown"]'
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        # Check if in top-right area
                        location = el.location
                        size = self.driver.get_window_size()
                        if location['x'] > size['width'] * 0.7 and location['y'] < 100:
                            el.click()
                            dropdown_clicked = True
                            print(f"  └─ Clicked dropdown via {selector}")
                            break
                    if dropdown_clicked:
                        break
                except:
                    continue
                    
            if not dropdown_clicked:
                print("  ⚠️  Trying JavaScript click...")
                self.driver.execute_script("""
                    const elements = document.querySelectorAll('[class*="account"], [class*="user"], [class*="dropdown"]');
                    for (let el of elements) {
                        const rect = el.getBoundingClientRect();
                        if (rect.right > window.innerWidth * 0.7 && rect.top < 100) {
                            el.click();
                            return true;
                        }
                    }
                """)
                dropdown_clicked = True
                
            time.sleep(1.5)
            
            # Step 2: Click logout
            print("→ Step 2: Clicking Logout")
            
            logout_clicked = False
            
            # Strategy 1: Find by text
            try:
                links = self.driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    text = link.text.lower().strip()
                    if text in ['logout', 'log out', 'sign out']:
                        link.click()
                        logout_clicked = True
                        print(f"  └─ Clicked logout link")
                        break
            except:
                pass
                
            # Strategy 2: Find by href
            if not logout_clicked:
                try:
                    logout_link = self.driver.find_element(By.CSS_SELECTOR, 'a[href*="/logout"]')
                    logout_link.click()
                    logout_clicked = True
                    print(f"  └─ Clicked logout via href")
                except:
                    pass
                    
            if not logout_clicked:
                raise Exception("Could not find logout button")
                
            time.sleep(3)
            
            # Step 3: Verify logout
            print("→ Step 3: Verifying logout")
            current_url = self.driver.current_url
            if 'login_only' in current_url or 'logout' in current_url:
                print("  ✓ Logout successful!")
                return True
            else:
                raise Exception(f"Not on login page. URL: {current_url}")
                
        except Exception as e:
            print(f"  ✗ Logout failed: {e}")
            return False
            
    def run_iteration(self, iteration):
        """Run single iteration"""
        print(f"\n{'='*60}")
        print(f"🔄 ITERATION {iteration}/{self.iterations}")
        print(f"{'='*60}")
        
        try:
            # Login
            if not self.login_sequence(iteration):
                self.log_evidence(iteration, "FAILED", "Login failed")
                return False
                
            # Delay
            self.random_delay(1, 2)
            
            # Logout
            if not self.logout_sequence():
                self.log_evidence(iteration, "FAILED", "Logout failed")
                return False
                
            # Success
            self.log_evidence(iteration, "SUCCESS", "Complete cycle")
            return True
            
        except Exception as e:
            self.log_evidence(iteration, "ERROR", str(e))
            return False
            
    def run(self, profile_path=None):
        """Main execution"""
        if not self.setup_driver(profile_path):
            return
            
        print("\n" + "="*60)
        print("🤖 MANESYNC AUTOMATION")
        print("="*60)
        print(f"Iterations: {self.iterations}")
        print(f"Target points: {self.calculate_points(self.iterations):.2f}")
        print("="*60)
        
        successful = 0
        
        try:
            for i in range(1, self.iterations + 1):
                if self.run_iteration(i):
                    successful += 1
                    
                if i < self.iterations:
                    delay = random.uniform(0.5, 2)
                    print(f"\n⏸️  Waiting {delay:.1f}s...")
                    time.sleep(delay)
                    
        finally:
            # Summary
            print("\n" + "="*60)
            print("✅ AUTOMATION COMPLETE")
            print("="*60)
            print(f"✓ Successful: {successful}/{self.iterations}")
            print(f"✗ Failed: {self.iterations - successful}")
            print(f"📊 Success rate: {(successful/self.iterations)*100:.1f}%")
            print(f"🏆 Points: {self.calculate_points(successful):.2f}")
            print("="*60)
            
            self.save_evidence()
            
            # Keep browser open
            print("\n💡 Browser will remain open")
            print("   Close it manually when done")


def get_chrome_profile_path():
    """
    Get Chrome profile path from user or use default
    """
    import os
    import platform
    
    # Default Chrome profile locations
    system = platform.system()
    if system == "Windows":
        default_path = os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data")
    elif system == "Darwin":  # macOS
        default_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    else:  # Linux
        default_path = os.path.expanduser("~/.config/google-chrome")
    
    print("\n" + "="*60)
    print("🔧 CHROME PROFILE SETUP")
    print("="*60)
    print("\nUsing your Chrome profile will:")
    print("  ✓ Keep you logged in (no MFA every time)")
    print("  ✓ Use your saved passwords")
    print("  ✓ Keep your browsing history")
    print("\n💡 Default Chrome profile location:")
    print(f"   {default_path}")
    print("\nOptions:")
    print("  1. Press ENTER to use default location")
    print("  2. Type 'none' to use a fresh profile")
    print("  3. Paste your custom profile path")
    
    choice = input("\nYour choice: ").strip()
    
    if choice.lower() == 'none':
        print("✅ Using fresh profile (will need MFA)")
        return None
    elif choice == '':
        if os.path.exists(default_path):
            print(f"✅ Using default profile: {default_path}")
            return default_path
        else:
            print(f"⚠️  Default path not found: {default_path}")
            print("   Using fresh profile instead")
            return None
    else:
        if os.path.exists(choice):
            print(f"✅ Using custom profile: {choice}")
            return choice
        else:
            print(f"⚠️  Path not found: {choice}")
            print("   Using fresh profile instead")
            return None


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("🤖 MANESYNC AUTOMATION SCRIPT")
    print("="*60)
    
    # Get Chrome profile
    profile_path = get_chrome_profile_path()
    
    # Get iterations
    while True:
        try:
            iterations = input("\nEnter number of iterations: ").strip()
            iterations = int(iterations)
            if iterations > 0:
                break
            print("❌ Please enter a positive number")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\n❌ Cancelled")
            return
            
    automation = ManesyncAutomation(iterations)
    automation.run(profile_path)


if __name__ == "__main__":
    main()