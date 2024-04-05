from flask import Flask, jsonify, request, render_template, url_for, flash, redirect, json
import time
import sql_functions
from datetime import date
import time

app = Flask(__name__)
app.config['SECRET_KEY']    = '1hhyjufosaip9fcids09if09ds8vuodsijfdious0d9f'
url_timestamp               = {}
url_viewtime                = {}
prev_url                    = ""
db                          = sql_functions.DB()
flask_port                  = 9000

def url_strip(url):
    if "http://" in url or "https://" in url:
        url = url.replace("https://", '').replace("http://", '').replace('\"', '')
    if "/" in url:
        url = url.split('/', 1)[0]
    return url

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/limits', methods=['GET', 'POST'])
def limits():
    if request.method == 'POST':
        limit   = int(request.form['limit'])

        if not limit:
            flash('A new limit is required')
        else:
            db.update_db_data()
            flash('Limit saved succesfully', 'info')

    limits      = db.get_db_data('SELECT * from Limits')

    return render_template('limits.html', limits=limits)

@app.route('/history', methods=['GET', 'POST'])
def history():
    if request.method == 'POST':
        limit   = request.form['limit']
        url     = request.form['url']

        if not limit:
            flash('A new limit is required')
        elif int(limit) < 5:
            flash('Limit should be greater than 5 minutes')
        elif not url:
            flash('An url is required')
        else:
            db.add_db_entry('Limits', "'url', 'limit'", "'" + url + "'," + limit)
            flash('Limit saved succesfully', 'info')

    data        = db.get_db_data('SELECT * from History')

    # first sort the data on date
    newData     = {}
    for d in data:
        if not d['date'] in newData:
            newData[d['date']]  = {}

        if not d['time'] in newData[d['date']]:
            newData[d['date']][d['time']]  = []

        
        newData[d['date']][d['time']].append({
            'url':  d['url'],
            'time': round(d['time_spent']/60), #show time in minutes
        })

    # than only keep the last time for each date
    newData2    = []
    for d in newData:
        latest_time = list(newData[d])[-1]
        total_time  = 0

        for t in newData[d][latest_time]:
            total_time = total_time + t['time']

        newData2.append({
            'date':     d,
            'total':    total_time,
            'data':     newData[d][latest_time],
            'rows':     len(newData[d][latest_time])
        })

    limits      = db.get_db_data('SELECT * from Limits')

    # create a limits dict
    newlimits   = {}
    for limit in limits:
        newlimits[limit['url']] = limit['limit']

    return render_template('history.html', data=newData2, limits=newlimits)

@app.route('/update_history', methods=['POST'])
def update_history():
    tabtimes         = request.form['tabtimes']
    
    if not tabtimes:
        flash('Tabtimes is required')
    else:
        tabtimes    = json.loads(tabtimes)
        print(tabtimes)
        for url, spent in tabtimes.items():
            if url == 'undefined':
                continue

            db.add_db_entry('History', "'url', 'date', 'time', time_spent", "'" + url + "','"+ str(date.today()) + "','" + time.strftime("%H:%M", time.localtime()) + "'," + str(spent))
    
    return jsonify({'message': 'success!'})

@app.route('/get_limits', methods=['POST', "GET"])
def get_limits():
    limits      = db.get_db_data('SELECT * from Limits')

    newlimits   = {}
    for limit in limits:
        newlimits[limit['url']] = limit['limit']
    
    return jsonify(newlimits)

app.run(host='0.0.0.0', port=flask_port)