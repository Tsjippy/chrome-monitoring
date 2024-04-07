let activeTab       = null;
let tabTimes        = {};
let warningTime     = 5; // minutes
let counter         = 0;
let limits          = {};
let serverAddress   = ''
let username        = '';

async function getLimits(){
    result          = await chrome.storage.sync.get();

    username        = result.name;
    serverAddress   = result.server;
    warningTime     = result.warning;

    if(username == '' || serverAddress == '' || result.warning == undefined){
        if (chrome.runtime.openOptionsPage) {
            chrome.runtime.openOptionsPage();
        } else {
            window.open(chrome.runtime.getURL('options.html'));
        }
    }

    if(serverAddress[serverAddress.length-1] != '/'){
        serverAddress += '/';
    }

    let formData    = new FormData();
    formData.append('username', username)

    result          = await request(`get_limits`, formData);

    if(result ){
        limits  = result;
        // store for offline usage
        await chrome.storage.sync.set({'limits': limits });
    }else{
        console.log('getting offline limits');

        // use offline limits
        await chrome.storage.sync.get(["limits"]).then((result) => {
            limits  = result.limits;

            console.log('Limits fetched: '+JSON.stringify(limits));
        });
    }
}

getLimits();

// check active tab each second
setInterval(async () => {
    counter++;

    if((counter / 300)  % 1 === 0 && username != ''){
        let formData    = new FormData();
        const date      = new Date();
        // use offline limits
        let result      = await chrome.storage.local.get(["history"]);

        let history     = result.history;

        let dateStr     = date.toLocaleDateString("nl-NL", {
            year:   "numeric",
            month:  "2-digit",
            day:    "2-digit",
        });

        let timeStr     = date.toLocaleTimeString("nl-NL", {
            hour:   '2-digit', 
            minute: '2-digit'
        });

        formData.append('username', username);
        formData.append('date', dateStr);
        formData.append('time', timeStr);
        formData.append('tabtimes', JSON.stringify(tabTimes));

        result  = await request('update_history', formData);

        if(!result){
            if ( history == undefined ){
                history = {};
            }

            if ( history[dateStr] == undefined ){
                history[dateStr] = {};
            }

            history[dateStr][timeStr] = tabTimes;

            for (const [dateStr, times] of Object.entries(history)) {
                console.log(`${dateStr}: ${times}`);
                for (const [time, tabtimes] of Object.entries(times)) {
                    console.log(`${time}: ${tabtimes}`);
                }
            }
            
            // store history locally
            await chrome.storage.local.set({'history': history });
        }else if( history != undefined){
            let succes  = true;
            // Upload offline data

            // loop over all dates
            for (const [dateStr, times] of Object.entries(history)) {
                //loop over all times
                for (const [time, tabtimes] of Object.entries(times)) {
                    formData    = new FormData();
                    formData.append('username', username);
                    formData.append('date', dateStr);
                    formData.append('time', time);
                    formData.append('tabtimes', JSON.stringify(tabtimes));

                    result  = await request('update_history', formData);

                    if(!result){
                        succes = false;
                        break;
                    }
                }

                if(!succes){
                    break;
                }
            }

            // all data succesfully uploaded, remove from storage
            if(succes){
                chrome.storage.local.remove(['history']);
            }
        }
    }

    let currentWindow   = await chrome.windows.getCurrent();

    // check if we are actually seeing the tab
    if(!currentWindow.focused || !navigator.onLine){
        return;
    }
    
    tabs        = await chrome.tabs.query({ currentWindow: true, active: true });
    if(tabs.length < 1){
        return;
    }
    
    activeTab = {
        'url':  tabs[0].url.split( '/' )[2],
        'id':   tabs[0].id
    }

    if(activeTab.url == 'newtab'){
        return;
    }

    if (activeTab) {
        if (!tabTimes[activeTab.url]) {
            tabTimes[activeTab.url] = 0;
        }

        tabTimes[activeTab.url]++;

        let limit   = limits[activeTab.url];
        if(limit == undefined){
            limit   = limits['default'];
        }

        if(parseInt(tabTimes[activeTab.url]) / 60 == ( limit - warningTime) ){
            console.log(activeTab)

            await chrome.notifications.create('', {
                title:      'Je schermtijd zit er bijna op',
                message:    `De website ${activeTab.url} wordt over ${warningTime} minuten afgesloten`,
                iconUrl:    '/icon.png',
                type:       'basic'
            });
        }

        let total   = 0;
        Object.entries(tabTimes).forEach(s => total = total + parseInt(s));
        if(total >= limits.total * 60){
            total   = total / 3600;

            await chrome.notifications.create('', {
                title:      'Je schermtijd zit er op',
                message:    `Je zit al ${total.toFixed(1)} uur achter je computer!`,
                iconUrl:    '/icon.png',
                type:       'basic'
            });
        }


        // close the tab
        if(tabTimes[activeTab.url] / 60 > limit){
            console.log(`closing the tab with url ${activeTab.url}`);
            
            await chrome.notifications.create('', {
                title:      'Je schermtijd zit er op',
                message:    `De website ${activeTab.url} wordt nu afgesloten. ${limit} minuten is genoeg!`,
                iconUrl:    '/icon.png',
                type:       'basic'
            });

            let tabs = await chrome.tabs.query({});
            tabs.forEach(tab => {
                if(tab.url != undefined && tab.url.split( '/' )[2] == activeTab.url){
                    console.log(tab.url);
                    chrome.tabs.remove(tab.id);
                }
            });
        }
    }
}, 1000);

async function request(url, formData=''){
    let response;
    let result;

    if(serverAddress == ''){
        console.error('no server address set')
        return false;
    }

    try{
        result = await fetch(
            serverAddress+url,
            {
                method: 'POST',
                credentials: 'same-origin',
                body: formData
            }
        );
    }catch (error){
        console.error(url);
		console.error(error);
		return false;
	}

	try{
        response	= await result.json();
	}catch (error){
		console.error(result);
		console.error(error);
		return false;
	}

	if(result.ok){
		return response;
	}else{
		console.error(result);
		console.error(`/login/${url}`);
		return false;
	}
}