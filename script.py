# -*- coding: utf-8 -*-

import requests
from lxml import html
import random
import time
import json
import pymysql
from pymysql.cursors import DictCursor
from contextlib import closing

s = requests.Session()

data = {'user': 'YOUR_LOGIN', 'password': 'YOUR_PASSWORD', 'la': 'login'}
#Данные для входа

headers = {'authority': 'rus-oge.sdamgia.ru',
            'method': 'POST',
            'path': '/',
            'scheme': 'https',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9,ru;q=0.8',
            'cache-control': 'max-age=0',
            'content-length': 62,
            'content-type': 'application/x-www-form-urlencoded',
            'cookie': 'YOUR_COOKIE',
            'origin': 'https://rus-oge.sdamgia.ru',
            'referer': 'https://rus-oge.sdamgia.ru/',
            'upgrade-insecure-requests': 1,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36 OPR/62.0.3331.99'}

#Заголовки для успешного соединения

r = s.post('https://sdamgia.ru', data=data, headers=headers)
#Отправляет POST-запрос на авторизацию

url = 'https://rus-oge.sdamgia.ru'
#Основная ссылка

def get_parsed_page(url):
    #Возвращает контент вебсайта по выбранному url и парсит в lxml-формате
    response = s.get(url)
    parsed_page = html.fromstring(response.content)
    return parsed_page

parsed_page = get_parsed_page(url)
#Сохраняет "запарсенную" страницу в переменную
variantHrefs = parsed_page.xpath('//span[@class="our_test pinkmark"]/a/@href')
#Получаем ссылки на все варианты
variantHref = 'https://rus-oge.sdamgia.ru/test'
#Общая ссылка на варианты

for variant in variantHrefs:
    headers = {'cookie': 'YOUR_COOKIE'}
    
    params = {'id': int(variant.split("=")[-1])}
    #Передаём ID варианта в параметрах
    
    response = s.get(variantHref, params = params, headers = headers)
    parsed_page = html.fromstring(response.content)
    exercise_urls = parsed_page.xpath('//div[@class="prob_maindiv"]/div/span[@class="prob_nums"]/a/@href')
    #Получаем ссылки на упражнения
    
    for exe in exercise_urls:
        if exercise_urls.index(exe) in (0, 14):
            pass
        else:
            params = {'id': int(exe.split("=")[-1])}
            headers = {'cookie': 'YOUR_COOKIE'}
            task_resp = s.get('https://rus-oge.sdamgia.ru/problem', headers = headers, params = params)
            parsed_page = html.fromstring(task_resp.content)
            task = ""
            taskLines = parsed_page.xpath('//div[@class="pbody"]/p/text()')
            #Получаем строки текста задания
            for i in taskLines:
                lmn = i.split("\xad")
                for u in lmn:
                    task += u
                task += "\n"
            #Циклом восстанавливаем текст из строк
            
            textLines = parsed_page.xpath('//div[@class="probtext"]/div/div/p/text()')
            text = ""
            for strTextOf in textLines:
                plm = strTextOf.split("\xad")
                for l in plm:
                    text += l
            
            exerciseTaskText = task + "\n" + text
            #Соединяем текст задания и приведённый текст
            
            answer = parsed_page.xpath('//div[@class="answer"]/span/text()')[0].split(": ")[-1]
            #Скрапим ответ
            
            with closing(pymysql.connect(host='localhost', user='root', password='', db='exams', charset='utf8mb4', cursorclass=DictCursor)) as conn:
                with conn.cursor() as cursor:
                    data = [(exerciseTaskText, (exercise_urls.index(exe)+1), answer, "ОГЭ")]
                    query = 'INSERT INTO tasks (exerciseText, exercise_number, answer, work_type) VALUES (%s, %s, %s, %s)'
                    cursor.executemany(query, data)
                    conn.commit()
                    
            #Сохраняем результат в таблицу exams в БД MySQL
            
            time.sleep(10)

    time.sleep(10) 