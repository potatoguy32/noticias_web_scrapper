import time
import json
import re
import concurrent.futures

from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup

import requests

from retry import retry

import pandas as pd
import numpy as np

import utils


def extract_links_from_infobae(browser, grupos):
    extracted_entries = dict()
    for grupo in grupos:
        browser.get(f'https://www.infobae.com/america/buscador/?query={grupo}%20mexico')
        time.sleep(2)
        mexico_button = browser.find_element(by=By.XPATH, value='//*[@id="section_filter"]/div[2]/div[1]/a')
        if mexico_button.text.startswith('México'):
            print("Mexico button found")
            mexico_button.click()
            time.sleep(2)
            
        resultados = browser.find_element(by=By.XPATH, value='//*[@id="resultdata"]/div[1]/div')
        if len(re.findall(r'\d+', resultados.text)) > 0:
            total = int(re.findall(r'\d+', resultados.text)[0])
            
        target = total // 20 + min(1, total % 20)
        print(f"Extracting {total} entries for {grupo}")
        time.sleep(2)
        counter = 0
        extracted_entries[grupo] = list()
        while counter <= target:
            try:
                extracted_entries[grupo].extend(utils.extract_news(browser=browser))
                next_page_button = browser.find_element(by=By.XPATH, value='//*[@id="resultdata"]/a[1]')
                if next_page_button.text.lower() != 'siguiente':
                    break
                
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                next_page_button.click()
                time.sleep(2)
                counter += 1
            except Exception as e:
                print(e)
                break
    
    return extracted_entries


def extract_links_from_universal(browser, grupos):
    palabras = [palabra.replace(' ', '+') for palabra in grupos]
    collected_entries = {}
    for grupo in palabras:
        browser.get(f'https://www.eluniversal.com.mx/buscador/?query={grupo}')
        running_entries = []
        results_text = browser.find_element(by=By.XPATH, value='//*[@id="resultdata"]/div[1]').text
        total_items = int(re.search('(?<!\S)(?=.)(0|([1-9](\d*|\d{0,2}(,\d{3})*)))?(\.\d*[1-9])?(?!\S)', results_text).group())
        target = total_items // 20 + min(1, total_items % 20)
        for _ in range(target):
            results = browser.find_element(by=By.ID, value='resultdata')
            anchores = [element.get_attribute("href") for element in results.find_elements(by=By.TAG_NAME, value='a')[:-1] if (len(element.text.split('\n')) > 2) and (int(re.search('\d{4}', element.text.split('\n')[1]).group()) >= 2020)]
            running_entries.extend(anchores)
            next_page_button = browser.find_element(by=By.XPATH, value='//*[@id="resultdata"]/a[1]')    
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:
                next_page_button.click()
            except Exception as e:
                print(f"Error tratando de clickear el boton de siguiente \n{e}")
            time.sleep(3)
        
        collected_entries[grupo] = list(set(running_entries))
    
    return collected_entries