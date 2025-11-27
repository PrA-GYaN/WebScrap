"""
Shopify Contact Information Scraper

This script searches Google for Shopify stores, then extracts contact information 
including emails, phone numbers, social media links, and physical addresses using 
Selenium WebDriver for JavaScript-rendered content.

Requirements:
- Chrome browser installed
- ChromeDriver (automatically managed by Selenium 4.15+)
"""

import os
import re
import time
import pandas as pd
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Set, Optional
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ShopifyContactScraper:
    """Main scraper class for extracting contact information from Shopify stores."""
    
    def __init__(self, headless: bool = True):
        """
        Initialize the scraper.
        
        Args:
            headless: Run browser in headless mode (default: True)
        """
        self.headless = headless
        self.driver = None
        self._init_driver()
        self._init_driver()
        
        # Regex patterns
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        # Enhanced phone pattern - matches various international formats
        self.phone_pattern = re.compile(
            r'(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(?\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)?\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?)|'
            r'(?:\+\d{1,3}[\s.-]?)?\(?\d{2,4}\)?[\s.-]?\d{2,4}[\s.-]?\d{2,4}[\s.-]?\d{0,4}'
        )
        
        # Social media domains
        self.social_media_domains = {
            'facebook': ['facebook.com', 'fb.com'],
            'instagram': ['instagram.com'],
            'twitter_x': ['twitter.com', 'x.com'],
            'tiktok': ['tiktok.com'],
            'youtube': ['youtube.com', 'youtu.be'],
            'linkedin': ['linkedin.com']
        }
    
    def search_google(self, query: str, max_results: int = 10) -> List[str]:
        """
        Search Google and extract result URLs using Selenium with pagination support.
        
        Args:
            query: Search query (e.g., 'site:myshopify.com "USA" intitle:"contact"')
            max_results: Maximum number of results to return
            
        Returns:
            List of URLs found
        """
        logger.info(f"Searching Google for: {query} (max {max_results} results)")
        
        if not self.driver:
            logger.error("WebDriver not initialized. Cannot search.")
            return []
        
        urls = []
        seen = set()
        page = 1
        max_pages = (max_results + 9) // 10  # Calculate pages needed (10 results per page)
        
        try:
            # Navigate to Google
            self.driver.get('https://www.google.com')
            time.sleep(2)
            
            # Find search box and enter query
            try:
                search_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "q"))
                )
                search_box.send_keys(query)
                search_box.submit()
            except TimeoutException:
                # Try alternative selectors
                search_box = self.driver.find_element(By.NAME, "q")
                search_box.send_keys(query)
                search_box.submit()
            
            # Wait for results to load
            time.sleep(3)
            
            # Loop through pages until we have enough results
            while len(urls) < max_results and page <= max_pages:
                logger.info(f"Extracting results from page {page}...")
                
                try:
                    # Wait for search results
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "search"))
                    )
                    
                    # Parse the page
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    
                    # Find all result links
                    result_links = []
                    
                    # Method 1: Find divs with class containing 'g' (common for results)
                    for result in soup.select('div.g, div[data-hveid]'):
                        link = result.find('a', href=True)
                        if link and link['href'].startswith('http'):
                            url = link['href']
                            # Filter out Google's own links
                            if not any(x in url for x in ['google.com', 'youtube.com/results']):
                                result_links.append(url)
                    
                    # Method 2: Find all links in search results area (fallback)
                    if not result_links:
                        search_div = soup.find('div', {'id': 'search'})
                        if search_div:
                            for link in search_div.find_all('a', href=True):
                                href = link['href']
                                if href.startswith('http') and 'google.com' not in href:
                                    result_links.append(href)
                    
                    # Add unique URLs to results
                    page_urls_added = 0
                    for url in result_links:
                        if url not in seen and len(urls) < max_results:
                            urls.append(url)
                            seen.add(url)
                            page_urls_added += 1
                    
                    logger.info(f"Page {page}: Found {page_urls_added} new results (total: {len(urls)}/{max_results})")
                    
                    # Check if we have enough results
                    if len(urls) >= max_results:
                        break
                    
                    # Try to go to next page
                    if page < max_pages:
                        next_button_found = False
                        
                        # Try multiple methods to find and click the "Next" button
                        try:
                            # Method 1: Find by ID
                            next_button = self.driver.find_element(By.ID, "pnnext")
                            if next_button.is_displayed():
                                next_button.click()
                                next_button_found = True
                                time.sleep(3)  # Wait for next page to load
                        except:
                            pass
                        
                        if not next_button_found:
                            try:
                                # Method 2: Find by aria-label
                                next_button = self.driver.find_element(By.CSS_SELECTOR, "a[aria-label*='Next']")
                                if next_button.is_displayed():
                                    next_button.click()
                                    next_button_found = True
                                    time.sleep(3)
                            except:
                                pass
                        
                        if not next_button_found:
                            try:
                                # Method 3: Find span with "Next" text
                                next_spans = self.driver.find_elements(By.XPATH, "//span[text()='Next']")
                                for span in next_spans:
                                    parent = span.find_element(By.XPATH, "..")
                                    if parent.tag_name == 'a':
                                        parent.click()
                                        next_button_found = True
                                        time.sleep(3)
                                        break
                            except:
                                pass
                        
                        if not next_button_found:
                            logger.warning(f"Could not find 'Next' button on page {page}, stopping pagination")
                            break
                        
                        page += 1
                    else:
                        break
                        
                except TimeoutException:
                    logger.warning(f"Timeout waiting for search results on page {page}")
                    break
                except Exception as e:
                    logger.warning(f"Error on page {page}: {e}")
                    break
            
        except WebDriverException as e:
            logger.error(f"WebDriver error during search: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
        
        logger.info(f"Search completed: Found {len(urls)} total results")
        return urls
    
    def _init_driver(self):
        """Initialize Selenium WebDriver with Chrome."""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless=new')
            
            # Common arguments for stable operation
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Suppress logging
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            logger.info("Selenium WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            logger.error("Make sure Chrome and ChromeDriver are installed")
            self.driver = None
    
    def __del__(self):
        """Cleanup: Close the browser when scraper is destroyed."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def close_popups(self):
        """Attempt to close any popups, modals, or cookie banners."""
        try:
            # Common selectors for close buttons
            close_selectors = [
                "button[aria-label*='Close']",
                "button[class*='close']",
                "button[class*='dismiss']",
                "button[id*='close']",
                "a[class*='close']",
                "div[class*='modal'] button",
                ".modal-close",
                ".popup-close",
                "[data-dismiss='modal']",
                "button.cookie-accept",
                "button.cookie-consent",
                "#onetrust-accept-btn-handler",
                ".cookie-banner button"
            ]
            
            for selector in close_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            element.click()
                            time.sleep(0.5)
                            logger.debug(f"Closed popup with selector: {selector}")
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Error closing popups: {e}")
            pass
    

    
    def extract_emails(self, soup: BeautifulSoup, text: str) -> Set[str]:
        """
        Extract email addresses from page content with enhanced detection.
        
        Args:
            soup: BeautifulSoup object
            text: Raw text content
            
        Returns:
            Set of email addresses found
        """
        emails = set()
        
        # Find emails in mailto links first (most reliable)
        for link in soup.find_all('a', href=True):
            if link['href'].startswith('mailto:'):
                email = link['href'].replace('mailto:', '').split('?')[0].strip()
                if '@' in email and '.' in email:
                    emails.add(email.lower())
        
        # Search in text content
        found_emails = self.email_pattern.findall(text)
        for email in found_emails:
            email = email.lower().strip()
            # Filter out common false positives and invalid emails
            if email and not any(x in email for x in [
                'example.com', 'domain.com', 'email.com', 'test.com',
                'yoursite.com', 'website.com', 'yourdomain.com',
                'siteaddress.com', 'sample.com', '.png', '.jpg', '.gif'
            ]):
                # Validate email has proper structure
                if email.count('@') == 1 and '.' in email.split('@')[1]:
                    emails.add(email)
        
        # Search in meta tags
        for meta in soup.find_all('meta'):
            content = meta.get('content', '')
            if '@' in content:
                found = self.email_pattern.findall(content)
                for email in found:
                    email = email.lower().strip()
                    if email.count('@') == 1:
                        emails.add(email)
        
        return emails
    
    def extract_phone_numbers(self, soup: BeautifulSoup, text: str) -> Set[str]:
        """
        Extract phone numbers from page content with enhanced detection.
        
        Args:
            soup: BeautifulSoup object
            text: Raw text content
            
        Returns:
            Set of phone numbers found
        """
        phones = set()
        
        # Find phones in tel links first (most reliable)
        for link in soup.find_all('a', href=True):
            if link['href'].startswith('tel:'):
                phone = link['href'].replace('tel:', '').strip()
                # Clean the phone number
                phone = re.sub(r'[^0-9+()\s.-]', '', phone)
                if phone:
                    phones.add(phone)
        
        # Search in specific elements likely to contain contact info
        contact_elements = soup.find_all(['p', 'div', 'span', 'li', 'td'], 
            string=re.compile(r'phone|call|contact|tel', re.IGNORECASE))
        
        for elem in contact_elements:
            elem_text = elem.get_text(separator=' ', strip=True)
            potential_phones = self.phone_pattern.findall(elem_text)
            for match in potential_phones:
                phone = match if isinstance(match, str) else ''.join(match)
                phone = phone.strip()
                # Validate: should have at least 10 digits
                digit_count = len(re.sub(r'\D', '', phone))
                if digit_count >= 10 and digit_count <= 15:
                    phones.add(phone)
        
        # Search full text as fallback
        if len(phones) < 2:  # If we haven't found many phones yet
            potential_phones = self.phone_pattern.findall(text)
            for match in potential_phones:
                phone = match if isinstance(match, str) else ''.join(match)
                phone = phone.strip()
                # Clean and validate
                digit_count = len(re.sub(r'\D', '', phone))
                if digit_count >= 10 and digit_count <= 15:
                    # Filter out common false positives
                    if not any(x in phone for x in ['1234567890', '0000000000']):
                        phones.add(phone)
        
        return phones
    
    def extract_social_links(self, soup: BeautifulSoup, base_url: str) -> Dict[str, str]:
        """
        Extract social media links from page.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            
        Returns:
            Dictionary with social media platform names as keys
        """
        social_links = {
            'facebook': '',
            'instagram': '',
            'twitter_x': '',
            'tiktok': '',
            'youtube': '',
            'linkedin': ''
        }
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            
            # Check each social media platform
            for platform, domains in self.social_media_domains.items():
                if not social_links[platform]:  # Only store first occurrence
                    for domain in domains:
                        if domain in href:
                            # Get full URL
                            full_url = urljoin(base_url, link['href'])
                            social_links[platform] = full_url
                            break
        
        return social_links
    
    def extract_physical_address(self, soup: BeautifulSoup, text: str) -> str:
        """
        Attempt to extract physical address from page.
        
        Args:
            soup: BeautifulSoup object
            text: Raw text content
            
        Returns:
            Physical address if found, empty string otherwise
        """
        # Look for common address indicators
        address_keywords = ['address', 'location', 'visit us', 'our office', 'headquarters']
        
        # Check for schema.org markup
        for element in soup.find_all(attrs={"itemtype": re.compile(".*PostalAddress")}):
            address_parts = []
            for child in element.find_all(attrs={"itemprop": True}):
                address_parts.append(child.get_text(strip=True))
            if address_parts:
                return ', '.join(address_parts)
        
        # Look for address in specific HTML elements
        for element in soup.find_all(['address', 'div', 'p']):
            elem_text = element.get_text(strip=True).lower()
            if any(keyword in elem_text for keyword in address_keywords):
                # Return first reasonable address-like text
                full_text = element.get_text(strip=True)
                if len(full_text) > 20 and len(full_text) < 500:
                    return full_text[:200]  # Limit length
        
        return ''
    
    def find_contact_page(self, soup: BeautifulSoup, base_url: str) -> str:
        """
        Find the contact page URL if different from current page.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            
        Returns:
            Contact page URL if found
        """
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            text = link.get_text(strip=True).lower()
            
            # Check if link text or href suggests contact page
            if any(word in href or word in text for word in ['contact', 'get-in-touch', 'reach-us']):
                return urljoin(base_url, link['href'])
        
        return ''
    
    def scrape_site(self, url: str) -> Dict[str, str]:
        """
        Scrape a single website for contact information using Selenium with enhanced extraction.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary with extracted information
        """
        logger.info(f"Scraping {url}...")
        
        result = {
            'url': url,
            'emails': '',
            'phone_numbers': '',
            'facebook': '',
            'instagram': '',
            'twitter_x': '',
            'tiktok': '',
            'youtube': '',
            'linkedin': '',
            'physical_address': '',
            'contact_page_url': ''
        }
        
        if not self.driver:
            logger.error("WebDriver not initialized. Cannot scrape.")
            return result
        
        try:
            # Load the page with Selenium
            self.driver.get(url)
            
            # Wait for page to load (wait for body element)
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                logger.warning(f"Timeout waiting for {url} to load")
            
            # Close any popups or modals
            time.sleep(2)
            self.close_popups()
            time.sleep(1)
            
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            
            # Get current URL (in case of redirects)
            current_url = self.driver.current_url
            
            # Extract contact information from main page
            emails = self.extract_emails(soup, text)
            phones = self.extract_phone_numbers(soup, text)
            social = self.extract_social_links(soup, current_url)
            address = self.extract_physical_address(soup, text)
            contact_page = self.find_contact_page(soup, current_url)
            
            # If we didn't find much info and there's a contact page, visit it
            if contact_page and contact_page != current_url and (len(emails) == 0 or len(phones) == 0):
                logger.info(f"Visiting contact page: {contact_page}")
                try:
                    self.driver.get(contact_page)
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    time.sleep(2)
                    self.close_popups()
                    
                    # Parse contact page
                    contact_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    contact_text = contact_soup.get_text(separator=' ', strip=True)
                    
                    # Extract additional info from contact page
                    emails.update(self.extract_emails(contact_soup, contact_text))
                    phones.update(self.extract_phone_numbers(contact_soup, contact_text))
                    
                    # Update social links if not found on main page
                    contact_social = self.extract_social_links(contact_soup, contact_page)
                    for key, value in contact_social.items():
                        if value and not social.get(key):
                            social[key] = value
                    
                    # Update address if not found on main page
                    if not address:
                        address = self.extract_physical_address(contact_soup, contact_text)
                        
                except Exception as e:
                    logger.warning(f"Error visiting contact page: {e}")
            
            # Update result
            result['url'] = current_url  # Use final URL after redirects
            result['emails'] = ', '.join(sorted(emails))
            result['phone_numbers'] = ', '.join(sorted(phones))
            result['physical_address'] = address
            result['contact_page_url'] = contact_page
            result.update(social)
            
            logger.info(f"Successfully scraped {url} - Found {len(emails)} emails, {len(phones)} phones")
            
        except TimeoutException:
            logger.warning(f"Timeout while loading {url}")
        except WebDriverException as e:
            logger.warning(f"WebDriver error accessing {url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
        
        return result
    
    def scrape_multiple_sites(self, urls: List[str], delay: float = 2.0) -> List[Dict[str, str]]:
        """
        Scrape multiple websites with delay between requests.
        
        Args:
            urls: List of URLs to scrape
            delay: Delay in seconds between requests
            
        Returns:
            List of dictionaries with extracted information
        """
        results = []
        
        for i, url in enumerate(urls):
            logger.info(f"Processing {i+1}/{len(urls)}: {url}")
            result = self.scrape_site(url)
            results.append(result)
            
            # Add delay between requests to be respectful
            if i < len(urls) - 1:
                time.sleep(delay)
        
        return results
    
    def save_to_csv(self, data: List[Dict[str, str]], filename: str = 'shopify_contacts.csv'):
        """
        Save extracted data to CSV file.
        
        Args:
            data: List of dictionaries with contact information
            filename: Output filename
        """
        if not data:
            logger.warning("No data to save")
            return
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        logger.info(f"Data saved to {filename}")
    
    def save_to_excel(self, data: List[Dict[str, str]], filename: str = 'shopify_contacts.xlsx'):
        """
        Save extracted data to Excel file.
        
        Args:
            data: List of dictionaries with contact information
            filename: Output filename
        """
        if not data:
            logger.warning("No data to save")
            return
        
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False, engine='openpyxl')
        logger.info(f"Data saved to {filename}")


def main():
    """Main entry point for the script."""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Search Google and scrape contact information from Shopify stores using Selenium'
    )
    
    # Create mutually exclusive group for query vs URLs
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--query',
        type=str,
        help='Google search query (e.g., \'site:myshopify.com "USA" intitle:"contact"\')'
    )
    group.add_argument(
        '--country',
        type=str,
        help='Country name to search for (creates query: site:myshopify.com "<country>" intitle:"contact")'
    )
    group.add_argument(
        '--urls',
        type=str,
        nargs='+',
        help='One or more URLs to scrape directly (space-separated)'
    )
    
    parser.add_argument(
        '--max-results',
        type=int,
        default=10,
        help='Maximum number of search results to process (default: 10)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='shopify_contacts',
        help='Output filename without extension (default: shopify_contacts)'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['csv', 'excel', 'both'],
        default='csv',
        help='Output format (default: csv)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=2.0,
        help='Delay between requests in seconds (default: 2.0)'
    )
    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='Run browser in visible mode (default: headless)'
    )
    parser.add_argument(
        '--url-file',
        type=str,
        help='Path to text file containing URLs (one per line)'
    )
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = ShopifyContactScraper(headless=not args.no_headless)
    
    # Determine URLs to scrape
    urls = []
    
    if args.query:
        # Search Google with custom query
        urls = scraper.search_google(args.query, max_results=args.max_results)
    elif args.country:
        # Build query from country name
        query = f'site:myshopify.com "{args.country}" intitle:"contact"'
        urls = scraper.search_google(query, max_results=args.max_results)
    elif args.urls:
        # Use provided URLs
        urls = args.urls
    
    # Add URLs from file if provided
    if args.url_file:
        try:
            with open(args.url_file, 'r') as f:
                file_urls = [line.strip() for line in f if line.strip()]
                urls.extend(file_urls)
            logger.info(f"Loaded {len(file_urls)} URLs from {args.url_file}")
        except Exception as e:
            logger.error(f"Error reading URL file: {e}")
    
    if not urls:
        logger.error("No URLs found. Please check your search query or provide URLs.")
        if scraper.driver:
            scraper.driver.quit()
        return
    
    # Scrape contact information
    results = scraper.scrape_multiple_sites(urls, delay=args.delay)
    
    # Save results
    if args.format in ['csv', 'both']:
        scraper.save_to_csv(results, f'{args.output}.csv')
    
    if args.format in ['excel', 'both']:
        scraper.save_to_excel(results, f'{args.output}.xlsx')
    
    logger.info(f"Scraping completed! Processed {len(results)} sites.")
    
    # Cleanup
    if scraper.driver:
        scraper.driver.quit()


if __name__ == '__main__':
    main()
