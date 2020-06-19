import os
import re
import time
import lxml
import requests
import urllib.request

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

from pytube import YouTube


def soft_log(cntr):
    SOFT_USER = os.environ.get('SOFT_USER')
    SOFT_PASS = os.environ.get('SOFT_PASS')

    try:
        present_user = sub_driver.find_element_by_xpath("//input[@id='username']")
        present_user.send_keys(SOFT_USER)

        present_pass = sub_driver.find_element_by_xpath("//input[@id='password']")
        present_pass.send_keys(SOFT_PASS)

        sub_driver.find_element_by_xpath("//input[@type='submit']").click()
        print('Logged in successfully!')
        cntr += 1
    except:
        pass


def make_dir(name):
    try:
        # Check if the folder already exists
        if os.path.isdir(name):
            pass
        # Else create a new one
        os.mkdir(name)
    except OSError:
        print(f"Creation of the directory {name} failed")
    else:
        print(f"Successfully created the directory {name}")


def download_resource(drive, link, folders_dictionary, file_extention, counter):
    drive.get(link)
    soft_log(counter)

    sub_source = drive.page_source
    sub_soup = BeautifulSoup(sub_source, 'lxml')

    sub_name = re.findall(r'Документ за урок \'(.*)\' от курса', sub_soup.prettify())[0]
    sub_name = re.sub(r':', '', sub_name)
    name_folder_check = re.sub(r'\W', '', sub_name).replace('_', '').lower()
    name_folder_touse = folders_dictionary[name_folder_check] + '\\' + sub_name + file_extention
    # print(name_folder_touse)

    sub_links = sub_soup.find_all('a', href=True)
    sub_links = [a['href'] for a in sub_links if 'downloads' in a['href']]
    # print(sub_links[0])

    container = requests.get(sub_links[0], allow_redirects=True)
    try:
        with open(name_folder_touse, 'wb') as f:
            f.write(container.content)
    except:
        print('File exists.')


def youtube_download(drive, lnk, folders_dictionary, counter):
    drive.get(lnk)
    soft_log(counter)

    sub_name = drive.find_element_by_xpath("//p[@class='lecture-topic lighter truncate']").text
    sub_name = re.sub(r':', '', sub_name)
    name_folder_check = re.sub(r'\W', '', sub_name).replace('_', '').lower()
    name_folder_touse = folders_dictionary[name_folder_check] + '\\'

    video_block = drive.find_element_by_xpath("//div[@class='col-md-12 col-xs-12 stream-wrapper bottom-buffer "
                                              "no-padding']")
    video_source = video_block.get_attribute('innerHTML')
    video_soup = BeautifulSoup(video_source, 'lxml')

    v_link = video_soup.find_all('iframe')[0]['src']
    nav = requests.get(v_link)

    nav_soup = BeautifulSoup(nav.text, 'lxml')
    # print(nav_soup.prettify())

    nav_link = nav_soup.find_all('a', href=True)[0]
    youtube_link = nav_link["href"]
    # print(f'The YouTube link is: {youtube_link}')

    ytd = YouTube(youtube_link)
    title = ytd.title

    while title == 'YouTube':
        ytd = YouTube(youtube_link)
        title = ytd.title

    ytd.streams.get_highest_resolution().download(output_path=name_folder_touse)


# Time for some Selenium
options = Options()
options.headless = True
options.add_argument("--mute-audio")
options.add_argument("--window-size=1920,1200")

sub_options = Options()
sub_options.headless = True
sub_options.add_argument("--mute-audio")
sub_options.add_argument("--window-size=1920,1200")

driver = webdriver.Chrome(options=options)
driver.implicitly_wait(1)

sub_driver = webdriver.Chrome(options=sub_options)
sub_driver.implicitly_wait(1)

count = 0

main_dir = 'E:\\SoftUni\\SoftUni - Program'

url = input('Please enter a MODULE link from SoftUni: ')
response = requests.get(url)

soup = BeautifulSoup(response.text, 'lxml')

# Get the TOPIC name
topic_name = soup.find('h1', class_='text-center').text.strip()
topic_dir_name = f'{main_dir}\\{topic_name}'

try:
    # Check if the folder already exists
    if os.path.isdir(topic_dir_name):
        pass
    # Else create a new one
    os.mkdir(topic_dir_name)
except OSError:
    print(f"Creation of the directory {topic_dir_name} failed")
else:
    print(f"Successfully created the directory {topic_dir_name}")

# Begin page scraping
lectures_list = soup.find_all('li', class_='lecture col-md-6 col-sm-12 visible-lg visible-md')

for lecture in lectures_list:
    # Get the lecture number and name
    lecture_number = lecture.find('span', class_='lecture-number').text
    lecture_name = lecture.find('span', class_='lecture-name').text

    # Inner scraping cycle: Get the resources links from the expandable menu
    lecture_hash = lecture.find_all('a', href=True)
    lecture_hash = [a['href'] for a in lecture_hash][0]

    lec_suburl = f'{url}{lecture_hash}'
    # print(lec_suburl)

    lecture_name = re.sub(r':', '_', lecture_name)
    lecture_name = re.sub(r'\W ', '', lecture_name)

    dir_name = f'{topic_dir_name}\\{lecture_number}_{lecture_name.upper()}'
    make_dir(dir_name)

print()

# Create a dictionary with folder names
folders = [x[0] for x in os.walk(topic_dir_name)]
short_dict = dict()
for folder in folders:
    if folder != topic_dir_name:
        short_name = re.findall(r'\d+_(.*)', folder)[0]
        short_name = re.sub(r'\W', '', short_name).replace('_', '').lower()
        short_dict[short_name] = folder

driver.get(url)
try:
    table = driver.find_element_by_xpath("//div[@class='grey-container lectures-section text-center']")
    list_of_lectures = table.find_elements_by_xpath("//li[@class='lecture col-md-6 col-sm-12 visible-lg "
                                                    "visible-md']")
    for each in list_of_lectures:
        print(each.text)
        each.click()
        time.sleep(1)

        # Wait for DROP-DOWN menu to appear
        WebDriverWait(driver, 100).until(EC.presence_of_element_located(
            (By.XPATH, "//ul[@class='lecture-resources-list top-buffer-lg']")))

        # Each lecture info
        lecture_html = each.get_attribute('innerHTML')
        lecture_soup = BeautifulSoup(lecture_html, 'lxml')

        lecture_id = lecture_soup.find_all('a', href=True)
        lecture_id = [a['href'] for a in lecture_id][0].replace('#', '')

        resources_table = driver.find_element_by_id(lecture_id)
        resources_table_html = resources_table.get_attribute('innerHTML')
        resources_soup = BeautifulSoup(resources_table_html, 'lxml')

        resources_urls = resources_soup.find_all('a', href=True)
        print(f'Links for the lecture: {len(resources_urls)}')

        for link in resources_urls:
            resource_name = link.text
            resource_link = link['href']
            resource_initial = resource_link
            if 'https' not in resource_link:
                resource_link = f'https://softuni.bg{resource_link}'
            if 'Presentation' in resource_name:
                download_resource(sub_driver, resource_link, short_dict, '.pptx', count)
            if 'Lab' in resource_name:
                download_resource(sub_driver, resource_link, short_dict, '.docx', count)
            if resource_name == 'Exercise':
                download_resource(sub_driver, resource_link, short_dict, '.docx', count)
            if 'More Exercise' in resource_name:
                download_resource(sub_driver, resource_link, short_dict, '_MORE.docx', count)
            if 'Видео' in resource_name and 'youtu.be' not in resource_initial:
                youtube_download(sub_driver, resource_link, short_dict, count)

            print(resource_name, resource_link)
        print()

    driver.quit()
    sub_driver.quit()
except Exception as ex:
    print(ex)
    driver.quit()
    sub_driver.quit()
