from flask import Flask, jsonify, request, render_template, flash, json
import sql_functions
from datetime import datetime
import mqtt_to_ha

app = Flask(__name__)
app.config['SECRET_KEY']    = '1hhyjufosaip9fcids09if09ds8vuodsijfdious0d9f'
db                          = sql_functions.DB()
flask_port                  = 9000
settings                    = db.get_db_data('SELECT * from Settings')
page_password               = 'moeilijk'
users_ha                    = {}

def url_strip(url):
    if "http://" in url or "https://" in url:
        url = url.replace("https://", '').replace("http://", '').replace('\"', '')

    if "/" in url:
        url = url.split('/', 1)[0]

    if url.count('.') > 1:
        if not url.split('.', 1)[0].isdigit():
            url = url.split('.', 1)[-1]

    return url

def getVar(request, key):
    if request.method == 'POST':
        return request.form.get(key)
    else:
        return request.args.get(key) 

@app.route('/', methods=['GET'])
def index():
    users = db.get_db_data('SELECT DISTINCT user FROM History ORDER BY user')

    return render_template('index.html', users=users)
    
@app.route('/limits/', methods=['GET', 'POST'])
def limits():
    pwd             = None
    new_limits      = {}
    authenticated   = False

    if request.method == 'POST':
        password    = getVar(request, 'password')

        if(password == page_password):
            pwd             = page_password
            authenticated   = True

            limit       = getVar(request, 'limit')

            if limit:
                url         = getVar(request, 'url')
                till        = getVar(request, 'till')
                temp_limit  = getVar(request, 'temp_limit')
                user        = getVar(request, 'user')
                if not user:
                    flash('An user is required', 'error')
                elif not url:
                    flash('An url is required', 'error')
                else:
                    user    = user.lower()
                    limit   = int(limit)

                    # Update the temporary limit
                    if till:
                        temp_limit   = int(temp_limit)

                        # Store the end date and time
                        query   = f"UPDATE Limits SET 'till' = '{till}' WHERE user='{user}' AND url='{url}'"
                        db.update_db_data(query)

                        # Store the temp limit
                        query   = f"UPDATE Limits SET 'temp_limit' = {temp_limit} WHERE user='{user}' AND url='{url}'"
                        db.update_db_data(query)
                    
                    # Up date the normal limit
                    query   = f"UPDATE Limits SET 'limit' = {limit} WHERE user='{user}' AND url='{url}'"

                    print(query)
                    db.update_db_data(query)

                    flash('Limit saved succesfully', 'success')
            else:
                flash('Succesfully logged in', 'success')
        else:
            flash('Invalid Password', 'danger')

    if pwd != None:
        limits      = db.get_db_data(f"SELECT * from Limits")

        new_limits  = {}
        unique_urls = {}

        for limit in limits:
            if not limit['user'] in unique_urls:
                unique_urls[limit['user']]  = []
                
            if not limit['user'] in new_limits:
                new_limits[limit['user']]  = []

            # Skip duplicates
            if limit['url'] in unique_urls[limit['user']]:
                continue

            unique_urls[limit['user']].append(limit['url'])

            date_string = ''
            temp_limit  = None
            if limit['till'] != None:
                x           = datetime.strptime(limit['till'], '%Y-%m-%dT%H:%M')

                # check if the date is in the future
                if datetime.now() < x:           
                    date_string = x.strftime('%d-%m-%Y %H:%M')
                    temp_limit  = limit['temp_limit']
                    date_string = limit['till']

            new_limits[limit['user']].append({
                'url':          limit['url'],
                'limit':        limit['limit'], #show time in minutes
                'till':         date_string,
                'temp_limit':   temp_limit
            })
        
        print(new_limits)

    return render_template('limits.html', limits=new_limits, usercount=len(new_limits), authenticated=authenticated, password=pwd)

@app.route('/history', methods=['GET', 'POST'])
def history():
    if request.method == 'POST':
        limit   = getVar(request,'limit')
        url     = getVar(request,'url')
        user    = getVar(request,'user').lower()

        if int(limit) < 5:
            flash('Limit should be greater than 5 minutes', 'info')
        else:
            values   = f"'{user}', '{url}', {limit}"
            db.add_db_entry('Limits', "'user','url', 'limit'", values)
            flash('Limit saved succesfully', 'success')
    elif request.method == 'GET':
        user = getVar(request,"user")
        if user is None:
            print("Argument not provided")
        else:
            user    = user.lower()

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

        time   = seconds_to_time(d['time_spent'])
        
        newData[d['user']][d['date']][d['time']].append({
            'url':      d['url'],
            'time':     time, #show time in minutes
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
            
            total_time = seconds_to_time(total_time)

            try:
                year    = int(datetime.strptime(d, '%Y-%m-%d').strftime('%Y'))
            except Exception as e:
                print(e)
                continue
            
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
    tabtimes    = getVar(request,'tabtimes')
    user        = getVar(request,'username').lower()
    dateStr     = getVar(request,'date')
    timeStr     = getVar(request,'time')

    limitsSet   = db.get_db_data(f"SELECT * from Limits WHERE user='{user}'")

    # add default limits
    if not limitsSet:
        settings   = db.get_db_data(f"SELECT * from Settings")

        for limit in settings:
            values   = f"'{user}', '{limit['key']}', {limit['value']}"
            db.add_db_entry('Limits', "'user','url', 'limit'", values)
    
    tabtimes    = json.loads(tabtimes)
    print(tabtimes)

    # check if there are duplicate urls for which should total the times spent
    totals      = {}
    for url, spent in tabtimes.items():
        if url == 'undefined':
            continue
        
        url = url_strip(url)

        if url in totals:
            totals[url] = totals[url] + int(spent)
        else:
            totals[url] = int(spent)

    total   = 0
    today   = datetime.now().strftime("%Y-%m-%d")
    for url, spent in totals.items():
        if url == '':
            continue

        values  = f"'{user}', '{url}', '{dateStr}', '{timeStr}', {spent}"
        db.add_db_entry('History', "'user', 'url', 'date', 'time', time_spent", values)

        # Do not run for historical data
        if dateStr == today:
            # Send to HA
            update_ha_sensors(user, url, spent)

            total += spent

    # Update total time
    update_ha_sensors(user, 'Total Screen Time', total, False)
        
    return jsonify({
        'message': 'success!',
        'limits':   get_limits(False)
    })

@app.route('/get_limits', methods=['POST', "GET"])
def get_limits(json=True):
    global settings
    try:
        user        = getVar(request,'username')
        if user == None:
            print("No user given")
            flash('An user is required', 'error')

            return "Please select an user"
        else:
            user=user.lower()
    except Exception as e:
        print('exception!')
        print(e)
        return e

    limits      = db.get_db_data(f"SELECT * from Limits WHERE user='{user}'")

    newlimits   = {}
    for limit in limits:
        minutes = limit['limit']

        # Send the temporary limit
        if limit['till'] != None and limit['temp_limit'] != None:
            x           = datetime.strptime(limit['till'], '%Y-%m-%dT%H:%M')

            # check if the date is in the future
            if datetime.now() < x:           
                minutes = limit['temp_limit']            

        newlimits[limit['url']] = minutes
    
    if json:
        return jsonify(newlimits)
    
    return newlimits

def seconds_to_time(seconds):
    hour    = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    
    if hour != 0 and  minutes < 10:
        minutes = '0' + str(minutes)

    if hour == 0 and minutes == 0:
        time = str(seconds) + ' (s)'
    elif hour == 0 :
        time = str(minutes) + ' (min)'
    else:
        time = f"{hour}:{minutes}"

    return time

def setup_ha_devices(user):
    # Create user if it does not exist
    if not user in users_ha:
        users_ha[user]  = {}

        # Device
        users_ha[user]['device']   = {
            "identifiers": [
                f"chrome_monitoring_{user}"
            ],
            "name": f"Chrome Monitoring {user.title()}",
            "model": "1",
            "manufacturer": "Ewald Harmsen"
        }

        #To Ha Instance
        users_ha[user]['mqtt_to_ha']   = mqtt_to_ha.MqqtToHa(users_ha[user]['device'])

def create_ha_sensor(user, url):
    # Create device if needed
    setup_ha_devices(user)

    index   = url.replace('.', '_').replace(':', '__')

    # Only create if needed
    if not index in users_ha[user]['mqtt_to_ha'].sensors:
        users_ha[user]['mqtt_to_ha'].sensors[index] = {
            "name":     url,
            "state":    "TOTAL_INCREASING",
            "unit":     "s",
            "type":     "DURATION"
        }
        
        users_ha[user]['mqtt_to_ha'].create_sensors( { index: users_ha[user]['mqtt_to_ha'].sensors[index]} )

    # Return the Sensor 
    return users_ha[user]['mqtt_to_ha'].sensors[index]

def update_ha_sensors(user, url, time, use_json=True):
    # Create sensor if needed
    sensor  = create_ha_sensor(user, url)

    users_ha[user]['mqtt_to_ha'].send_value(sensor, time, use_json)

app.run(host='0.0.0.0', port=flask_port)