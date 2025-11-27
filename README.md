# Installation Guide - Shopify Contact Scraper

Simple step-by-step installation guide for Windows users.

---

## What You Need

- **Windows 10 or Windows 11**
- **Internet Connection**
- **About 10 minutes**

---

## Step 1: Install Python

1. **Download Python:**
   - Go to: https://www.python.org/downloads/
   - Click the big yellow "Download Python" button
   - Save the file to your computer

2. **Install Python:**
   - Double-click the downloaded file
   - ⚠️ **IMPORTANT**: Check the box that says "Add Python to PATH"
   - Click "Install Now"
   - Wait for installation to finish (2-3 minutes)
   - Click "Close" when done

3. **Verify Python Installed:**
   - Press `Windows + R` keys together
   - Type `cmd` and press Enter
   - In the black window, type:
   ```cmd
   python --version
   ```
   - Press Enter
   - You should see something like: `Python 3.12.4`

---

## Step 2: Install Google Chrome

1. **Download Chrome:**
   - Go to: https://www.google.com/chrome/
   - Click "Download Chrome"
   - Save and run the installer

2. **Install Chrome:**
   - Follow the installation prompts
   - Chrome should open automatically when done

---

## Step 3: Download the Scraper Files

1. **Create a Folder:**
   - Open File Explorer
   - Go to your desired location (e.g., `C:\Users\YourName\Documents`)
   - Right-click → New → Folder
   - Name it: `ShopifyScraper`

2. **Copy the Files:**
   - Copy all project files into this folder:
     - `shopify_contact_scraper.py`
     - `requirements.txt`
     - Other files

---

## Step 4: (Optional) Create Virtual Environment

**Note:** Virtual environment keeps packages separate from your system Python. This is optional but recommended.

1. **Open Command Prompt in Your Folder:**
   - Open the `ShopifyScraper` folder in File Explorer
   - Click in the address bar at the top
   - Type `cmd` and press Enter

2. **Create Virtual Environment:**
   ```cmd
   python -m venv .venv
   ```
   - Wait for it to finish (about 30 seconds)

3. **Activate Virtual Environment:**
   ```cmd
   .venv\Scripts\activate
   ```
   - You should see `(.venv)` appear before your prompt
   - This means the virtual environment is active

**Important:** Whenever you open a new command prompt to use the scraper, run the activate command again:
```cmd
.venv\Scripts\activate.bat
```

---

## Step 5: Install Required Packages

1. **Open Command Prompt (if not already open):**
   - If you created a virtual environment in Step 4, make sure it's activated
   - You should see `(.venv)` before your prompt
   - If not, run: `.venv\Scripts\activate.bat`

2. **Install Packages:**
   - In the command window, type:
   ```cmd
   pip install selenium beautifulsoup4 pandas openpyxl
   ```
   or

    ```cmd
    pip install -r requirements.txt
    ```

   - Press Enter
   - Wait for installation (1-2 minutes)
   - You'll see "Successfully installed..." messages

---

## Step 5: Test Everything Works

1. **Test the Script:**
   - In the same command window, type:
   ```cmd
   python shopify_contact_scraper.py --help
   ```
   - Press Enter
   - You should see usage information (how to use the script)

2. **If You See Errors:**
   - Close the command window
   - Repeat Step 4 (install packages again)

---

## You're Done! 🎉

Installation complete! The scraper is ready to use.

---

## How to Use the Scraper

### Open Command Prompt in Your Folder

1. Open File Explorer to your `ShopifyScraper` folder
2. Click in the address bar
3. Type `cmd` and press Enter
4. **If you used virtual environment:** Activate it first:
   ```cmd
   .venv\Scripts\activate.bat
   ```

### Basic Usage

**Search for stores in a country:**
```cmd
python shopify_contact_scraper.py --country "USA" --no-headless
```

**Search with more results:**
```cmd
python shopify_contact_scraper.py --country "Canada" --max-results 20 --no-headless
```

**Add Delay if blocked**
 ```cmd
python shopify_contact_scraper.py --country "Canada" --max-results 20 --delay 1.0 --no-headless
```

### View Results

- After scraping, check your folder for `shopify_contacts.csv`
- Open it with Excel or any spreadsheet program
- All contact information will be there!

---
