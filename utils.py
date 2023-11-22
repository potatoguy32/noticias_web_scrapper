import re
import time

import requests
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from retry import retry


@retry(tries=3, delay=2)
def extract_news(browser):
    entries = list()
    for element in browser.find_elements(by=By.TAG_NAME, value='a'):
        if (element.get_attribute("href") is not None) and (element.get_attribute("class") == '') and (len(element.text) > 10):
            entries.append(element.get_attribute("href"))
    
    return entries

def words_in_string(criterios, complete_text):
    patterns = [re.compile(re.escape(sentence), re.IGNORECASE) for sentence in criterios]
    words_found = []
    for index, pattern in enumerate(patterns):
        if pattern.search(complete_text):
            words_found.append(criterios[index])
            
    if len(words_found) > 0:
        return words_found

    return None

def append_matching_words(grupo, word_list, a_string, url, filtered_entries):
    words_found = set(word_list).intersection(a_string.replace(',', '').replace('.', '').split())
    if len(words_found) > 0:
        filtered_entries[grupo].append((url, list(words_found)))
    
    return


def get_matches(collector, grupo, url, criterios, municipios, actividades, carteles):
    if url in [x[-1] for l in collector.values() for x in l]:
        return None
    
    r = requests.request(method='GET', url=url)
    time.sleep(3)
    soup = BeautifulSoup(r.content, 'html.parser')
    titulo = soup.find('h1').text
    matching_years = [re.search('\d{4}', span.text).group() for span in soup.find_all('span') if re.search('\d{4}', span.text)]
    if int(matching_years[0]) < 2019:
        return None
    
    complete_text = " ".join([paragraph.text.lower() for paragraph in soup.find_all('p')])
    matching_criterios = words_in_string(criterios, complete_text)
    matching_estados = words_in_string(municipios['ESTADO'].unique(), complete_text)
    matching_municipios = words_in_string(municipios['MUNICIPIO'].unique(), complete_text)
    matching_carteles = [re.compile(re.escape(text), re.IGNORECASE).search(complete_text) is not None for text in carteles]
    matching_actividades = [re.compile(re.escape(text), re.IGNORECASE).search(complete_text) is not None for text in actividades]
    if matching_criterios and (matching_estados or matching_municipios):
        collector[grupo].append((titulo,
                                 matching_years[0],
                                 matching_criterios,
                                 matching_estados,
                                 matching_municipios,
                                 matching_carteles,
                                 matching_actividades,
                                 url
                                 ))
    
    return None

