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


def get_links_from_infobae(browser, word):
    links = []
    try:
        browser.get(f'https://www.infobae.com/mexico/')
        time.sleep(3)
        try:
            sub_button = browser.find_element(By.XPATH, '//*[@id="onesignal-slidedown-cancel-button"]')
            sub_button.click()
            print("subscribe section found. Skipping...")
        except:
            pass
        
        time.sleep(3)
        button = browser.find_element(By.XPATH, '//*[@id="hamburger-icon"]')
        button.click()
        time.sleep(3)
        search_button = browser.find_element(By.XPATH, '//*[@id="queryly-label"]/button')
        search_button.click()
        time.sleep(3)
        text_bar = browser.find_element(By.XPATH, '//*[@id="queryly_query"]')
        text_bar.send_keys(word)
        time.sleep(3)
        resultados_texto = browser.find_element(By.XPATH, '//*[@id="queryly_searchresultscounter"]').text
        resultados = int(re.search(r'(?<!\S)(?=.)(0|([1-9](\d*|\d{0,2}(,\d{3})*)))?(\.\d*[1-9])?(?!\S)', resultados_texto).group())
        n_links_to_get = min(200, resultados)
        target = (n_links_to_get // 10) + (min(n_links_to_get % 10, 1))
        for _ in range(target):
            browser.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            time.sleep(2)

        noticias_container = browser.find_element(By.XPATH, '//*[@id="queryly_resultscontainer"]')
        noticias = noticias_container.find_elements(By.TAG_NAME, 'div')
        for noticia in noticias:
            try:
                current_noticia = noticia.find_element(By.CLASS_NAME, 'queryly_item_contentcontainer')
            except:
                continue
            
            pubdate = current_noticia.find_element(By.CLASS_NAME, 'queryly_item_pubdate')
            pub_year = int(re.search('\d{4}', pubdate.text).group())
            if pub_year >= 2019:
                link = current_noticia.find_element(By.TAG_NAME, 'a').get_attribute('href')
                links.append(link)
            
    
    except:
        print("Something went wrong with infobae")
        return list(set(links))
    
    return list(set(links))


def extract_links_from_universal(browser, word):
    running_entries = []
    try:
        palabra = word.replace(' ', '+')
        browser.get(f'https://www.eluniversal.com.mx/buscador/?query={palabra}')
        results_text = browser.find_element(by=By.XPATH, value='//*[@id="resultdata"]/div[1]').text
        total_items = int(re.search('(?<!\S)(?=.)(0|([1-9](\d*|\d{0,2}(,\d{3})*)))?(\.\d*[1-9])?(?!\S)', results_text).group())
        target = total_items // 20 + min(1, total_items % 20)
        for _ in range(target):
            results = browser.find_element(by=By.ID, value='resultdata')
            anchores = [element.get_attribute("href") for element in results.find_elements(by=By.TAG_NAME, value='a')[:-1] if (len(element.text.split('\n')) > 2) and (int(re.search('\d{4}', element.text.split('\n')[1]).group()) >= 2019)]
            running_entries.extend(anchores)
            next_page_button = browser.find_element(by=By.XPATH, value='//*[@id="resultdata"]/a[1]')    
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:
                next_page_button.click()
            except Exception as e:
                print(f"Error tratando de clickear el boton de siguiente")
            time.sleep(3)
    
    except:
        print("Something went wrong with el universal")
        return list(set(running_entries))
    
    return list(set(running_entries))


def get_links_from_sinembargo(browser, word):
    links = []
    try:
        search_words = [word.replace(' ', '+'), word.replace(' ', '%20')]
        browser.get(f'https://www.sinembargo.mx/resultados?q={search_words[0]}#gsc.tab=0&gsc.q={search_words[1]}&gsc.page=1')
        page_index = browser.find_element(By.XPATH, '//*[@id="___gcse_0"]/div/div/div/div[5]/div[2]/div[1]/div/div[2]/div')
        pages = [page for page in page_index.find_elements(By.TAG_NAME, 'div')]
        total_pages = len(pages)
        for i in range(1, total_pages):
            notes = browser.find_element(By.XPATH, '//*[@id="___gcse_0"]/div/div/div/div[5]/div[2]/div[1]/div/div[1]')
            for element in notes.find_elements(By.CLASS_NAME, 'gsc-webResult'):
                fecha = element.text.split('\n')[-1].split('...')[0]
                fecha_year_re = re.search('\d{4}', fecha)
                if ('hace ' in fecha) or (fecha and (int(fecha_year_re.group()) >= 2019)):
                    links.append(element.find_element(By.TAG_NAME, 'a').get_attribute('href'))
            
            page_index = browser.find_element(By.XPATH, '//*[@id="___gcse_0"]/div/div/div/div[5]/div[2]/div[1]/div/div[2]/div')
            pages = [page for page in page_index.find_elements(By.TAG_NAME, 'div')]
            pages[i].click()
            time.sleep(3)
    
    except:
        print("Something went wrong with sin embargo")
        return list(set(links))
    
    return list(set(links))


def get_articulos_from_elsoldemexico(browser, word):
    links = []
    try:
        palabra = word.replace(' ', '+')
        browser.get(f'https://www.elsoldemexico.com.mx/buscar/?q={palabra}')
        time.sleep(3)
        browser.find_element(By.XPATH, '//*[@id="tab-story"]/div[1]/select/option[2]').click()
        time.sleep(1)
        articulos_text = browser.find_element(By.XPATH, '/html/body/div[3]/section/section/div[2]/div[3]/div/ul/li[1]/a').text
        total_articulos = int(re.search('\d{0,3}(,\d{3})|\d{1,3}', articulos_text).group().replace(',', ''))
        target_articulos = (total_articulos // 10) + min(total_articulos % 10, 1)
        for _ in range(1, target_articulos):
            results = browser.find_element(By.XPATH, '//*[@id="tab-story"]/div[2]/div/div/div/div')
            for result in results.find_elements(By.TAG_NAME, 'div'):
                try:
                    fecha_texto = result.find_element(By.TAG_NAME, 'strong').text
                except:
                    continue
                
                if len(fecha_texto) < 8:
                    continue
                
                year = int(re.search('\d{4}', fecha_texto).group())
                if year >= 2019:
                    link = result.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    links.append(link)
                else:
                    return list(set(links))
            
            browser.find_element(By.XPATH, f'//*[@id="tab-story"]/div[3]/ul/li[{target_articulos + 3}]/span').click()
            time.sleep(2)
    
    except:
        print('Something went wrong with el sol de mx (articulos)')
        return list(set(links))
    
    return list(set(links))


def get_columnas_from_elsoldemexico(browser, word):
    links = []
    try:
        palabra = word.replace(' ', '+')
        browser.get(f'https://www.elsoldemexico.com.mx/buscar/?q={palabra}')
        time.sleep(2)
        browser.find_element(By.XPATH, '/html/body/div[3]/section/section/div[2]/div[3]/div/ul/li[3]/a').click()
        time.sleep(2)
        browser.find_element(By.XPATH, '//*[@id="tab-column"]/div[1]/select/option[2]').click()
        time.sleep(1)
        columnas_text = browser.find_element(By.XPATH, '/html/body/div[3]/section/section/div[2]/div[3]/div/ul/li[3]/a/p').text
        total_columnas = int(re.search('\d{0,3}(,\d{3})|\d{1,3}', columnas_text).group().replace(',', ''))
        target_columnas = (total_columnas // 10) + min(total_columnas % 10, 1)
        for _ in range(1, target_columnas):
            results = browser.find_element(By.XPATH, '//*[@id="tab-column"]/div[2]')
            for result in results.find_elements(By.TAG_NAME, 'div'):
                try:
                    fecha_texto = result.find_element(By.TAG_NAME, 'strong').text
                except:
                    continue
                
                if len(fecha_texto) < 8:
                    continue
                
                year = int(re.search('\d{4}', fecha_texto).group())
                if year >= 2019:
                    link = result.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    links.append(link)
                else:
                    return list(set(links))

            browser.find_element(By.XPATH, f'//*[@id="tab-column"]/div[3]/ul/li[{target_columnas + 3}]/span').click()
            time.sleep(2)
    except:
        print('Something went wrong with el sol de mx (columnas)')
        return list(set(links))
    
    return list(set(links))
