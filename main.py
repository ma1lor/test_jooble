import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
import logging
import time 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



url_website = 'https://realtylink.org/en/properties~for-rent'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
}



data = []


def load_to_json() -> None:
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)


async def get_photo_urls(url) -> list:
    response = await send_request(url)
    soup = BeautifulSoup(response, 'lxml')
    photo_urls = []
    script_tag = soup.find('script', string=lambda text: 'window.MosaicPhotoUrls' in text)
    if script_tag:
        script_content = script_tag.string
        start_index = script_content.find('["') + 2
        end_index = script_content.find('"]', start_index)
        photo_urls = script_content[start_index:end_index].split('","')
    return photo_urls


async def get_info_from_page(url):
    response = await send_request(url)
    soup = BeautifulSoup(response, 'lxml')
    content = soup.find('div', class_='region-content')


    
    try:
        title = content.find('h1', itemprop='category').text.strip()

    except:
        title = 'No title found'
    try:
        address = content.find('div', class_='d-flex mt-1').text.strip()
    except:
        address = 'No address found'
        
    try:
        region = f"{address.split(',')[1].strip()}, {address.split(',')[2].strip()}"
    except:
        region = 'No region found'
    try:
        description = content.find('div', itemprop='description').text.strip()
    except:
        description = 'No description found'
    
    try:
        price = f"{content.find_all('span', class_='text-nowrap')[1].text.strip().split(' ')[0]}/month"
    except:
        price = 'No price information found'

    try:
        bedrooms = content.find('div', class_='col-lg-3 col-sm-6 cac').text.strip()
    except:
        bedrooms = '0 badrooms '

    try:
        bathrooms = content.find('div', class_="col-lg-3 col-sm-6 sdb").text.strip()
    except:
        bathrooms = '0 bathrooms'
    try:
        property_area = content.find('div', class_='carac-value').text.strip()
    except:
        property_area = 'No property area information found'
    photos_urls = await get_photo_urls(url)

    data.append({
        "url" : url,
        "title": title,
        "address": address,
        "region": region,
        "description": description,
        "price": price,
        "rooms": bedrooms + ' and ' + bathrooms,
        "property_area": property_area,
        "photos_urls": photos_urls
    })

    logger.info(f"Processed apartment: {title}")


async def gather_urls_of_aparts(number) -> list:
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    driver = webdriver.Chrome(options=options)
    driver.get(url_website)
    apartment_links = []
    time.sleep(5)
    for i in range(number):
        apartments = driver.find_elements(By.CSS_SELECTOR, 'div.property-thumbnail-item')
        for apartment in apartments:
            apartment_link = apartment.find_element(By.CSS_SELECTOR, 'a.property-thumbnail-summary-link').get_attribute('href')
            apartment_links.append(apartment_link)

        if i != number - 1:
            next_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'next')))
            next_button.click()
            time.sleep(2)
        else:
            driver.close()
            driver.quit()
        
    return apartment_links






async def send_request(url) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as resp:
            return await resp.text(encoding="utf-8")



async def main(number) -> None:

    apartment_links = await gather_urls_of_aparts(number)
    tasks = [get_info_from_page(link) for link in apartment_links]
    await asyncio.gather(*tasks)
 

if __name__ == "__main__":
    #NUMBER OF PAGES TO SCRAPE
    #1 PAGE = 20 ELEMENTS
    number = 3
    asyncio.run(main(number))
    load_to_json()
