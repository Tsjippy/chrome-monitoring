let activeTab       = null;
let tabTimes        = {};
let warningTime     = 5; // minutes
let counter         = 0;
let limits          = {};
let serverAddress   = ''
let username        = '';

const keepAlive = () => setInterval(chrome.runtime.getPlatformInfo, 20e3);
chrome.runtime.onStartup.addListener(keepAlive);
keepAlive();

async function initialize(){
    chrome.notifications.create('', {
        title:      'Starting Extension',
        message:    `Starting the url monitoring extension`,
        iconUrl:    '/icon.png',
        type:       'basic'
    });

    console.log('Notification send')

    // get extension settings from sync
    syncStorage     = await chrome.storage.sync.get();

    username        = syncStorage.name;
    serverAddress   = syncStorage.server;
    warningTime     = syncStorage.warning;

    if(syncStorage.name == undefined || syncStorage.server == undefined || syncStorage.warning == undefined || username == '' || serverAddress == ''){
        // redirect to options page if needed
        if (chrome.runtime.openOptionsPage) {
            chrome.runtime.openOptionsPage();
        } else {
            window.open(chrome.runtime.getURL('options.html'));
        }
    }

    // get stored usage from today
    let d       = new Date();
    let dateStr = d.toLocaleDateString("fr-CA", {
        year:   "numeric",
        month:  "2-digit",
        day:    "2-digit",
    });

    let result      = await chrome.storage.local.get([dateStr]);
    
    if(result[dateStr] != undefined){
        console.log(await chrome.storage.local.get());
        tabTimes    = result[dateStr];
    }
    console.log(tabTimes);

    // Clean up local storage
    result      = await chrome.storage.local.get();

    for (const [key, data] of Object.entries(result)) {
        if( key == 'history' || key == dateStr){
            continue;
        }
        chrome.storage.local.remove([key]);
    }

    // get website limits from the server
    let formData    = new FormData();
    formData.append('username', username)

    result          = await request(`get_limits`, formData);

    if(result ){
        limits  = result;
        
        // store for offline usage
        await chrome.storage.sync.set({'limits': limits });
    }else{
        console.log('Getting offline limits');

        // use offline limits
        chrome.storage.sync.get(["limits"]).then((result) => {
            limits  = result.limits;

            if(limits == undefined){
                limits  = {};

                chrome.notifications.create('serverurl', {
                    title:              'Do you have the right server url?',
                    message:            `I cannot reach your server at ${serverAddress} are you sure it is correct?<br>Change it by clicking on this message`,
                    iconUrl:            '/icon.png',
                    type:               'basic',
                    requireInteraction: true,
                });
            
                chrome.notifications.onClicked.addListener(
                    function(notificationId){
                        if(notificationId == 'serverurl'){
                            // redirect to options page if needed
                            if (chrome.runtime.openOptionsPage) {
                                chrome.runtime.openOptionsPage();
                            } else {
                                window.open(chrome.runtime.getURL('options.html'));
                            }
                        }
                    },
                );
            }

            console.log('Limits fetched: '+JSON.stringify(limits));
        });
    }
}

initialize();

// check active tab each second
setInterval(async () => {
    counter++;

    const d         = new Date();

    let dateStr     = d.toLocaleDateString("fr-CA", {
        year:   "numeric",
        month:  "2-digit",
        day:    "2-digit",
    });

    // store tabtimes locally to use when rebooting extension or chrome
    chrome.storage.local.set({ [dateStr] : tabTimes });

    if((counter / 300 )  % 1 === 0 && username != ''){
        sendUsage();
    }

    let currentWindow   = await chrome.windows.getCurrent();

    // check if we are actually seeing the tab
    if(!currentWindow.focused){
        return;
    }
    
    tabs        = await chrome.tabs.query({ currentWindow: true, active: true });
    if(tabs.length < 1){
        return;
    }
    
    activeTab = {
        'url':  stripUrl(tabs[0].url),
        'id':   tabs[0].id
    }

    if(activeTab.url == 'newtab'){
        return;
    }

    if (activeTab) {
        enforceLimits();
    }
    
    self.serviceWorker.postMessage('test')
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
        console.log(serverAddress+url);
		console.log(error);
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

async function sendUsage(){
    let formData    = new FormData();
    const d         = new Date();

    let dateStr     = d.toLocaleDateString("fr-CA", {
        year:   "numeric",
        month:  "2-digit",
        day:    "2-digit",
    });

    let timeStr     = d.toLocaleTimeString("nl-NL", {
        hour:   '2-digit', 
        minute: '2-digit'
    });

    // get offline history
    result      = await chrome.storage.local.get(["history"]);

    let history     = result.history;

    formData.append('username', username);
    formData.append('date', dateStr);
    formData.append('time', timeStr);
    formData.append('tabtimes', JSON.stringify(tabTimes));

    result      = await request('update_history', formData);

    if(!result){
        console.log('Storing data in local storage');
        if ( history == undefined ){
            history = {};
        }

        if ( history[dateStr] == undefined ){
            history[dateStr] = {};
        }

        history[dateStr][timeStr] = tabTimes;
        
        // store history locally to upload it later
        await chrome.storage.local.set({'history': history });
        chrome.storage.local.get().then(res=>console.log(res));
    }else{
        console.log('Uploading data succesfull');

        // upload previously stored data
        if( history != undefined){
            let succes  = true;

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

                        console.error(`Uploading data for ${dateStr} ${time} failed`);
                        break;
                    }

                    console.log(`Uploaded data for ${dateStr} ${time} succesfully`);
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
}

async function enforceLimits(){
    if (!tabTimes[activeTab.url]) {
        tabTimes[activeTab.url] = 0;
    }

    tabTimes[activeTab.url]++;

    console.log(`${activeTab.url}: ${tabTimes[activeTab.url]} seconds`)

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
        console.log(`Closing the tab with url ${activeTab.url}`);
        
        await chrome.notifications.create('', {
            title:      'Je schermtijd zit er op',
            message:    `De website ${activeTab.url} is afgesloten. ${limit} minuten is genoeg!`,
            iconUrl:    '/icon.png',
            type:       'basic'
        });

        let tabs = await chrome.tabs.query({});
        tabs.forEach(tab => {
            if(tab.url != undefined && stripUrl(tab.url) == activeTab.url){
                console.log(tab);
                chrome.tabs.remove(tab.id);
            }
        });
    }
}

function stripUrl(orgUrl){
    url = orgUrl.split( '/' )[2];

    if(url == undefined){
        return orgUrl;
    }

    if(url.split('.').length - 1 < 2){
        return url;
    }

    return url.split(/\.(.*)/s)[1];
}