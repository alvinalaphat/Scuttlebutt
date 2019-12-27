import requests
from bs4 import BeautifulSoup
import re
from multiprocessing import Pool
import flask
from flask import Flask, render_template, request
import pandas as pd
from time import sleep
from random import randint
# import pymongo
# from pymongo import MongoClient
from flask import json
from werkzeug.exceptions import HTTPException
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/', methods=['POST'])
def scrape():

    player_or_team = str(request.form['words'])

    # urls
    url_guardian = "https://www.theguardian.com/football/series/rumourmill"
    url_bbc = "https://www.bbc.com/sport/football/gossip"

    # pages
    page = requests.get(url_guardian)
    bbc_page = requests.get(url_bbc)

    # instances
    soup = BeautifulSoup(page.content, 'html.parser')
    souper = BeautifulSoup(bbc_page.content, 'html.parser')

    # functions
    def drop_reporters_in_rumors(rumor):
        for i in rumor:
            if(len(i) < 15):
                rumor.remove(i)

    # Guardian
    rumors = [entry.get_text().split(':')[1] for entry in soup.find_all(attrs={"class":"js-headline-text","data-link-name":"article"})]
    links = [link.get('href') for link in soup.find_all(attrs={"class":"js-headline-text","data-link-name":"article"})]
    dates = [date.get_text() for date in soup.find_all('time')[::2]]
    players = pd.DataFrame({'rumors':rumors,'links':links,'date_posted':dates})

    # BBC Sports
    bbc_rumors = [entry.text for entry in souper.select('div#story-body p')]
    bbc_links = [entry.get('href') for entry in souper.select('div#story-body a')[:(len(bbc_rumors))]]
    bbc_dates = [date.get('title') for date in souper.find_all('abbr')[::2]]
    bbc_dates = list(bbc_dates * (len(bbc_links)))
    bbc_players = pd.DataFrame({'rumors':bbc_rumors,'links':bbc_links,'date_posted':bbc_dates})
    players = players.append(bbc_players,ignore_index=True)

    # Telegraph
    telegraph1 = requests.get('https://www.telegraph.co.uk/football-transfers/')
    soapy = BeautifulSoup(telegraph1.content, 'html.parser')
    link1 = [('https://www.telegraph.co.uk' + link.get('href')) for link in soapy.select('h3 a')]
    rumor1 = [entry.get_text().strip() for entry in soapy.select('span.list-headline__text')]
    drop_reporters_in_rumors(rumor1)
    date1 = [date.get_text().split(',')[0] for date in soapy.select('div time')]

    telegraph1_data = pd.DataFrame({'rumors':rumor1,'links':link1,'date_posted':date1})
    players = players.append(telegraph1_data,ignore_index=True)

    # Telegraph pages 2-5
    pages = [str(i) for i in range(2,6)]

    for page in pages:
        response = requests.get('https://www.telegraph.co.uk/football-transfers/page-' + page)
        soupy = BeautifulSoup(response.content, 'html.parser')
        link = [('https://www.telegraph.co.uk' + link.get('href')) for link in soupy.select('h3 a')]
        rumor = [entry.get_text().strip() for entry in soupy.select('span.list-headline__text')]
        drop_reporters_in_rumors(rumor);
        date = [date.get_text().split(',')[0] for date in soupy.select('div time')]

        telegraph_players = pd.DataFrame({'rumors':rumor,'links':link,'date_posted':date})
        players = players.append(telegraph_players,ignore_index=True)

    final = []
    class Rumor:
        def __init__(self, rumor, link, date):
            self.rumor = rumor
            self.link = link
            self.date = date

    for row in players.iterrows():
        if player_or_team in row[1]['rumors'].lower():
            r1 = Rumor(row[1]['rumors'],row[1]['links'],row[1]['date_posted'])
            final.append(r1)
    if len(final)==0:
        final = 'There are no existing rumors about ' + player_or_team + '! Try typing in a keyword'
    return render_template('scraped.html', data=final)

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response
        
if __name__ == '__main__':
    app.run(debug=True)

# MfleMoXbUMfijHQd
# client = MongoClient('mongodb+srv://alvinalaphat:MfleMoXbUMfijHQd@cluster0-8bal1.mongodb.net/test?retryWrites=true')
# col = client['Rumors']['transfers']
# data = players.to_dict(orient='records')
# col.insert_many(data)
