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

@app.route('/limits/', methods=['GET', 'POST'])
def limits():
    if request.method == 'POST':
        user    = request.form['user']
        limit   = int(request.form['limit'])
        url     = request.form['url']

        if not limit:
            flash('A new limit is required')
        elif not user:
            flash('An user is required')
        elif not url:
            flash('An url is required')
        else:
            query   = f"UPDATE Limits SET 'limit' = {limit} WHERE user='{user}' AND url='{url}'"
            print(query)
            db.update_db_data(query)
            flash('Limit saved succesfully', 'info')
    
    limits      = db.get_db_data(f"SELECT * from Limits")
    newLimits  = {}

    for limit in limits:
        if not limit['user'] in newLimits:
            newLimits[limit['user']]  = []

        newLimits[limit['user']].append({
            'url':      limit['url'],
            'limit':    limit['limit'], #show time in minutes
        })
    
    print(newLimits)

    return render_template('limits.html', limits=newLimits, usercount=len(newLimits))

@app.route('/history', methods=['GET', 'POST'])
def history():
    if request.method == 'POST':
        limit   = request.form['limit']
        url     = request.form['url']
        user    = request.form['user']

        if int(limit) < 5:
            flash('Limit should be greater than 5 minutes')
        else:
            values   = f"'{user}', '{url}', {limit}"
            db.add_db_entry('Limits', "'user','url', 'limit'", values)
            flash('Limit saved succesfully', 'info')
    elif request.method == 'GET':
        user = request.args.get('user')

    data        = db.get_db_data('SELECT * from History')

    # first sort the data on date
    newData     = {}
    for d in data:
        if not d['user'] in newData:
            newData[d['user']]  = {}

        if not d['date'] in newData[d['user']]:
            newData[d['user']][d['date']]  = {}

        if not d['time'] in newData[d['user']][d['date']]:
            newData[d['user']][d['date']][d['time']]  = []

        seconds   = d['time_spent']
        hour      = seconds // 3600
        seconds    %= 3600
        minutes   = seconds // 60
        seconds    %= 60

        if hour == 0 and minutes == 0:
            spent = str(seconds) + ' (s)'
        elif hour == 0 :
            spent = str(minutes)
        else:
            spent = f"{hour}:{minutes}"
        
        newData[d['user']][d['date']][d['time']].append({
            'url':      d['url'],
            'time':     spent, #show time in minutes
            'seconds':  d['time_spent']
        })

    # than only keep the last time for each date
    newData2    = {}

    # loop over the users
    for u in newData:
        if not u in newData2:
            newData2[u]  = {}

        # loop over the dates
        for d in newData[u]:
            # get the last timestamp
            latest_time = list(newData[u][d])[-1]
            total_time  = 0

            # calculate the total of all visited websites together
            for t in newData[u][d][latest_time]:
                total_time = total_time + t['seconds']
            
            total_time = total_time // 60 # convert to minutes

            year    = int(datetime.strptime(d, '%Y-%m-%d').strftime('%Y'))
            if not year in newData2[u]:
                newData2[u][year]  = {}

            month   = datetime.strptime(d, '%Y-%m-%d').strftime('%B')
            if not month in newData2[u][year]:
                newData2[u][year][month]  = []

            newData2[u][year][month].append({
                'date':     datetime.strptime(d, '%Y-%m-%d').strftime('%d-%m-%Y'),
                'total':    total_time,
                'data':     newData[u][d][latest_time],
                'rows':     len(newData[u][d][latest_time])
            })

    limits      = db.get_db_data('SELECT * from Limits')

    # create a limits dict
    newlimits   = {}
    for limit in limits:
        newlimits[limit['url']] = limit['limit']

    return render_template('history.html', data=newData2, limits=newlimits, curyear=datetime.now().year, curmonth=datetime.now().strftime('%B'), curuser=user)

@app.route('/update_history', methods=['POST'])
def update_history():
    tabtimes    = request.form['tabtimes']
    user        = request.form['username'].lower()
    dateStr     = request.form['date']
    timeStr     = request.form['time']

    limitsSet   = db.get_db_data(f"SELECT * from Limits WHERE user='{user}'")

    # add default limits
    if not limitsSet:
        settings   = db.get_db_data(f"SELECT * from Settings")

        for limit in settings:
            values   = f"'{user}', '{limit['key']}', {limit['value']}"
            db.add_db_entry('Limits', "'user','url', 'limit'", values)
    
    tabtimes    = json.loads(tabtimes)
    print(tabtimes)
    for url, spent in tabtimes.items():
        if url == 'undefined':
            continue

        values  = f"'{user}', '{url}', '{dateStr}', '{timeStr}', {spent}"
        db.add_db_entry('History', "'user', 'url', 'date', 'time', time_spent", values)
        
    return jsonify({'message': 'success!'})

@app.route('/get_limits', methods=['POST', "GET"])
def get_limits():
    global settings
    try:
        user        = request.form['username']
    except Exception as e:
        print('exception!')
        print(e)

    limits      = db.get_db_data(f"SELECT * from Limits WHERE user='{user}'")

    print(limits)

    newlimits   = {}
    for limit in limits:
        newlimits[limit['url']] = limit['limit']
    
    return jsonify(newlimits)

settings      = db.get_db_data('SELECT * from Settings')

app.run(host='0.0.0.0', port=flask_port)