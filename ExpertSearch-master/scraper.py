from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
from urllib.request import urlopen
from urllib.parse import urlparse, urljoin
import requests

#
# uses webdriver object to execute javascript code and get dynamically loaded webcontent
#
def get_js_soup(url,driver):
    driver.get(url)
    res_html = driver.execute_script('return document.body.innerHTML')
    soup = BeautifulSoup(res_html,'html.parser') #beautiful soup object to be used for parsing html content
    return soup

#
# Returns list of URLs of universities from http://doors.stanford.edu/~sr/universities.html
#
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

#
# Returns specified number of links found on the url provided
#
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

#
# Checks whether `url` is a valid URL
#
def is_valid(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

#
# writes specified list to specified file
#
def write_lst(lst,file_):
    with open(file_,'w') as f:
        for l in lst:
            f.write(l)
            f.write('\n')

#
# Cleans up the specified url list to remove urls with keywords such as 'faculty', 'staff', etc. and
# writes to the specified output file. Also excludes all external links in the list.
#
def cleanup_urls(url_list, file_out):

    # open file in write mode
    f_out = open(file_out, "w")

    count = 0
    internal_count = 0
    for line in url_list:
        count += 1
        if 'faculty' in line or 'staff' in line or 'people' in line or 'directory' in line:
            continue

        # Exclude base urls
        if line.endswith('.edu/') == False:
            f_out.writelines(line+'\n')
            internal_count += 1

    f_out.close()

    print('Total urls {}, urls written {}'.format(count, internal_count))


if __name__ == '__main__':
    # create a webdriver object and set options for headless browsing
    options = Options()
    options.headless = True
    driver = webdriver.Chrome('./chromedriver', options=options)

    university_list = scrape_list_of_universities('http://doors.stanford.edu/~sr/universities.html', driver)

    # Scrape homepages of all urls
    no_universities = len(university_list)

    # Scraping all universities takes a long time. Set the value below to a small
    # number to test the functionality
    no_universities_to_scrape = 3

    all_urls = []
    for i, link in enumerate(university_list):
        try:
            # Get a maximum of 10 links from the home page
            urls = get_all_website_links(link, driver, 10)

            print('-' * 20, 'Scraped [{}] {}/{}'.format(link, i + 1, no_universities), '-' * 20)
            all_urls += urls
        except:
            #print('Exception')
            continue

        if i > no_universities_to_scrape:
            break

    driver.close()

    # Clean up urls and write to a file
    cleanup_urls(all_urls, "urls_clean.txt")

    print('Done')
