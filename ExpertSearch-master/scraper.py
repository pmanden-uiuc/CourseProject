from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
from urllib.request import urlopen
from urllib.parse import urlparse, urljoin
import requests


#uses webdriver object to execute javascript code and get dynamically loaded webcontent
def get_js_soup(url,driver):
    driver.get(url)
    res_html = driver.execute_script('return document.body.innerHTML')
    soup = BeautifulSoup(res_html,'html.parser') #beautiful soup object to be used for parsing html content
    return soup

# Returns list of URLs of universities from http://doors.stanford.edu/~sr/universities.html
def scrape_list_of_universities(dir_url,driver):
    print('-'*20,'Scraping {}'.format(dir_url),'-'*20)
    faculty_links = []
    soup = get_js_soup(dir_url,driver)
    for link_holder in soup.find_all('a'):
        rel_link = link_holder.get('href')
        if rel_link != None and 'http' in rel_link:
            faculty_links.append(rel_link)
    print ('-'*20,'Found {} Universities'.format(len(faculty_links)),'-'*20)
    return faculty_links

# Returns specified number of links found on the url provided
def get_all_website_links(url, driver, no_links_to_scrape):
    # initialize the set of links (unique links)
    internal_urls = []
    external_urls = []

    urls = []

    domain_name = urlparse(url).netloc
    soup = get_js_soup(url, driver)

    no_links = 0
    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None or '/' not in href:
            # href empty tag
            continue

        # join the URL if it's relative (not absolute link)
        href = urljoin(url, href)

        parsed_href = urlparse(href)
        # remove URL GET parameters, URL fragments, etc.
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path

        if not is_valid(href):
            continue
        if href in internal_urls:
            continue
        if domain_name not in href:
            # external link
            if href not in external_urls:
                print(f"External link: {href}")
                external_urls.append(href)
            continue

        print(f"Internal link: {href}")
        urls.append(href)
        internal_urls.append(href)
        no_links += 1
        if no_links > no_links_to_scrape:
            break

    return urls

# Checks whether `url` is a valid URL
def is_valid(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def write_lst(lst,file_):
    with open(file_,'w') as f:
        for l in lst:
            f.write(l)
            f.write('\n')

if __name__ == '__main__':
    # create a webdriver object and set options for headless browsing
    options = Options()
    options.headless = True
    driver = webdriver.Chrome('./chromedriver', options=options)

    faculty_links = scrape_list_of_universities('http://doors.stanford.edu/~sr/universities.html', driver)

    # Scrape homepages of all urls
    tot_urls = len(faculty_links)
    all_urls = []
    for i, link in enumerate(faculty_links):
        print('-'*20, 'University faculty url {}/{}'.format(i+1,tot_urls), '-'*20)
        try:
            urls = get_all_website_links(link, driver, 10)
            all_urls += urls
        except:
            print('Exception')
    driver.close()
    write_lst(all_urls,"all_urls.txt")

    print( 'Done')
