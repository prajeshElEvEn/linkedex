from flask import render_template, request
from flask import Blueprint
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import warnings
warnings.filterwarnings("ignore")

bp = Blueprint('base', __name__)


@bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        search_query = request.form['searchItem']
        li_at = request.form['linkedinCookie']
        print(f"Scraping links for {search_query} with cookie {li_at}")
        links = scrape_links(search_query, li_at)
        return render_template('base.html', links=links)
    return render_template('base.html', links=[])


def scrape_links(search_query, li_at):
    links = []
    page = 1
    total_pages = 1  # Set the total pages to 4

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

    # Pass total_pages as an argument
    total_page(driver, search_query, total_pages)

    for i in tqdm(range(total_pages)):
        soup = fetch(driver, page, search_query)
        lists = soup.findAll(
            'li', class_='reusable-search__result-container')
        for list in lists:
            image_src = list.find(
                'img', class_='presence-entity__image')['src']
            name = list.find('img', class_='presence-entity__image')['alt']
            link = list.find('a', class_='app-aware-link')['href']
            links.append((image_src, name, link))
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


def total_page(driver, search_query, total_pages):
    print(f"Getting total pages for {search_query}")

    soup = fetch(driver, 1, search_query)
    last_li = soup.find_all(
        'li', attrs={"data-test-pagination-page-btn": True})
    if last_li:
        last_page = last_li[-1]
        attribute_value = last_page.get('data-test-pagination-page-btn')
        total_pages = min(int(attribute_value), total_pages)
