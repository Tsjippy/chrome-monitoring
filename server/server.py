from flask import Flask, jsonify, request, render_template, url_for, flash, redirect, json
import time
import sql_functions
from datetime import datetime, date
import time

app = Flask(__name__)
app.config['SECRET_KEY']    = '1hhyjufosaip9fcids09if09ds8vuodsijfdious0d9f'
db                          = sql_functions.DB()
flask_port                  = 9000
settings                    = ''

def url_strip(url):
    if "http://" in url or "https://" in url:
        url = url.replace("https://", '').replace("http://", '').replace('\"', '')
    if "/" in url:
        url = url.split('/', 1)[0]
    return url

@app.route('/', methods=['GET'])
def index():
    users = db.get_db_data('SELECT DISTINCT user FROM History ORDER BY user')

    return render_template('index.html', users=users)

@app.route('/limits', methods=['GET', 'POST'])
def limits():
    if request.method == 'POST':
        limit   = int(request.form['limit'])

        if not limit:
            flash('A new limit is required')
        else:
            db.update_db_data()
            flash('Limit saved succesfully', 'info')

    user   = request.form['username']

    limits = db.get_db_data('SELECT * from Limits WHERE user="'+user+'"')

    return render_template('limits.html', limits=limits)

@app.route('/history', methods=['GET', 'POST'])
def history():
    if request.method == 'POST':
        limit   = request.form['limit']
        url     = request.form['url']
        user    = request.form['username']

        if not limit:
            flash('A new limit is required')
        elif int(limit) < 5:
            flash('Limit should be greater than 5 minutes')
        elif not url:
            flash('An url is required')
        else:
            db.add_db_entry('Limits', "'user','url', 'limit'", "'" + user + "','" + limit + "', '" + url + "'," + limit)
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
    newData2    = {}
    for d in newData:
        latest_time = list(newData[d])[-1]
        total_time  = 0

        for t in newData[d][latest_time]:
            total_time = total_time + t['time']

        year    = int(datetime.strptime(d, '%Y-%m-%d').strftime('%Y'))
        if not year in newData2:
            newData2[year]  = {}

        month   = datetime.strptime(d, '%Y-%m-%d').strftime('%B')
        if not month in newData2[year]:
            newData2[year][month]  = []

        newData2[year][month].append({
            'date':     datetime.strptime(d, '%Y-%m-%d').strftime('%d-%m-%Y'),
            'total':    total_time,
            'data':     newData[d][latest_time],
            'rows':     len(newData[d][latest_time])
        })

    limits      = db.get_db_data('SELECT * from Limits')

    # create a limits dict
    newlimits   = {}
    for limit in limits:
        newlimits[limit['url']] = limit['limit']

    return render_template('history.html', data=newData2, limits=newlimits, curyear=datetime.now().year, curmonth=datetime.now().strftime('%B'))

@app.route('/update_history', methods=['POST'])
def update_history():
    tabtimes    = request.form['tabtimes']
    user        = request.form['username']
    
    if not tabtimes:
        flash('Tabtimes is required')
    elif not user:
        flash('Username is required')
    else:
        tabtimes    = json.loads(tabtimes)
        print(tabtimes)
        for url, spent in tabtimes.items():
            if url == 'undefined':
                continue

            db.add_db_entry('History', "'user', 'url', 'date', 'time', time_spent", "'"+user+"','" + url + "','"+ str(date.today()) + "','" + time.strftime("%H:%M", time.localtime()) + "'," + str(spent))
    
    return jsonify({'message': 'success!'})

@app.route('/get_limits', methods=['POST', "GET"])
def get_limits():
    global settings
    try:
     user        = request.form['username']
    except Exception as e:
        print('exception!')
        print(e)

    limits      = db.get_db_data('SELECT * from Limits WHERE user="'+user+'"')

    print(limits)

    newlimits   = {}
    for limit in limits:
        newlimits[limit['url']] = limit['limit']

    for setting in settings:
        newlimits[setting['key']] = setting['value']

    print(newlimits)
    
    return jsonify(newlimits)

settings      = db.get_db_data('SELECT * from Settings')

app.run(host='0.0.0.0', port=flask_port)