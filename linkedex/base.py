from flask import render_template, request
from flask import Blueprint
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import os
import csv
from flask import send_file
import warnings
warnings.filterwarnings("ignore")

bp = Blueprint('base', __name__)


@bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search_query = request.form['searchItem']
        li_at = request.form['linkedinCookie']
        pages_to_scrape = int(request.form['pagesToScrape'])
        print(f"Scraping links for {search_query} with cookie {li_at}")
        links = scrape_links(search_query, li_at, pages_to_scrape)
        filename = f'linkedin-links_{search_query}.csv'
        write_to_csv(links, filename)
        return render_template('base.html', links=links, filename=filename)
    return render_template('base.html', links=[])


@bp.route('/download/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    base_dir = os.getcwd()
    upload_dir = os.path.join(base_dir, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    return send_file(file_path, as_attachment=True)


def scrape_links(search_query, li_at, pages_to_scrape):
    links = []
    page = 1

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)

    cookies = {
        'name': 'li_at',
        'value': li_at,
        'domain': '.linkedin.com',
    }

    driver.get("https://www.linkedin.com")
    driver.add_cookie(cookies)

    # Pass pages_to_scrape as an argument
    total_page(driver, search_query, pages_to_scrape)

    for i in tqdm(range(pages_to_scrape)):
        soup = fetch(driver, page, search_query)
        lists = soup.findAll('li', class_='reusable-search__result-container')
        for list in lists:
            try:
                image = list.find(
                    'img', class_='presence-entity__image')['src']
            except (AttributeError, TypeError):
                image = ""
            try:
                alt_tag = list.find('img', class_='presence-entity__image')
                alt = alt_tag.get('alt') if alt_tag else ""
            except (AttributeError, TypeError):
                alt = ""
            try:
                href_tag = list.find('a', class_='app-aware-link')
                href = href_tag.get('href') if href_tag else ""
            except (AttributeError, TypeError):
                href = ""
            if image and alt and href:
                link_item = (image, alt, href)
                links.append(link_item)
            page += 1

    driver.quit()
    return links


def fetch(driver, page, search_query):
    print(f"Fetching page {page} for {search_query}")
    searchkey_url = f"https://www.linkedin.com/search/results/people/?geoUrn=[\"104305776\"]&keywords={search_query}&origin=SWITCH_SEARCH_VERTICAL&page={page}"
    driver.get(searchkey_url)
    time.sleep(15)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    html = driver.page_source
    return BeautifulSoup(html, "lxml")


def total_page(driver, search_query, pages_to_scrape):
    print(f"Getting total pages for {search_query}")

    soup = fetch(driver, 1, search_query)
    last_li = soup.find_all(
        'li', attrs={"data-test-pagination-page-btn": True})
    if last_li:
        last_page = last_li[-1]
        attribute_value = last_page.get('data-test-pagination-page-btn')
        pages_to_scrape = min(int(attribute_value), pages_to_scrape)


def write_to_csv(links, filename):
    base_dir = os.getcwd()
    upload_dir = os.path.join(base_dir, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Image Source', 'Name', 'Link'])
        for link in links:
            writer.writerow(link)
