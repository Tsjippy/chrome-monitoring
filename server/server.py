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

    data  = [
        {
            'date': '2024-04-05',
            'total': 19,
            'data':
                [
                    {
                        'url': 'nas',
                        'time': 4,
                    },
                    {
                        'url': 'youtube.com',
                        'time': 4,
                    },
                    {
                        'url': '192.168.0.200',
                        'time': 4,
                    },
                    {
                        'url': 'nu.nl',
                        'time': 5,
                    },
                ],
            'rows': 4
        },
    ]

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
            'time': d['time_spent'],
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
        flash('A new limit is required')
    else:
        tabtimes    = json.loads(tabtimes)
        print(tabtimes)
        for url, spent in tabtimes.items():
            if url == 'undefined':
                continue

            db.add_db_entry('History', "'url', 'date', 'time', time_spent", "'" + url + "','"+ str(date.today()) + "','" + time.strftime("%H:%M", time.localtime()) + "'," + str(spent))
    
    return jsonify({'message': 'success!'})

@app.route('/send_url', methods=['POST'])
def send_url():
    url         = request.form['url']
    print("currently viewing: " + url_strip(url))
    parent_url  = url_strip(url)

    global url_timestamp
    global url_viewtime
    global prev_url

    print("initial db prev tab: ", prev_url)
    print("initial db timestamp: ", url_timestamp)
    print("initial db viewtime: ", url_viewtime)

    if parent_url not in url_timestamp.keys():
        url_viewtime[parent_url] = 0

    if prev_url != '':
        time_spent = int(time.time() - url_timestamp[prev_url])
        url_viewtime[prev_url] = url_viewtime[prev_url] + time_spent

    x = int(time.time())
    url_timestamp[parent_url] = x
    prev_url = parent_url
    print("final timestamps: ", url_timestamp)
    print("final viewtime: ", url_viewtime[prev_url])

    return jsonify({'message': 'success!'})

@app.route('/get_limits', methods=['POST', "GET"])
def get_limits():
    limits      = db.get_db_data('SELECT * from Limits')

    newlimits   = {}
    for limit in limits:
        newlimits[limit['url']] = limit['limit']

    limits           = {
        "nas": 40,
        "youtube.com": 40,
        "192.168.0.200": 40,
        "total": 120,
        "default": 11,
    }
    
    return jsonify(newlimits)

@app.route('/quit_url', methods=['POST'])
def quit_url():
    resp_json = request.get_data()
    print("Url closed: " + resp_json.decode())
    return jsonify({'message': 'quit success!'})



app.run(host='0.0.0.0', port=5000)