let activeTab    = null;
let tabTimes     = {};
let warningTime  = 5; // minutes
let counter      = 0;
let limits       = {
    "nas": 40,
    "youtube.com": 40,
    "192.168.0.200": 40,
    "total": 120,
    "default": 11,
}

async function getLimits(){
    result  = await request("get_limits");

    if(result ){
        limits  = result;
    }
}

getLimits();

// check active tab each second
setInterval(async () => {
    counter++;

    console.log(counter)
    if((counter / 300)  % 1 === 0){
        console.log('test')
        let formData    = new FormData();
        formData.append('tabtimes', JSON.stringify(tabTimes));
        request('update_history', formData)
    }

    let currentWindow   = await chrome.windows.getCurrent();

    // check if we are actually seeing the tab
    if(!currentWindow.focused || !navigator.onLine){
        return;
    }
    
    tabs        = await chrome.tabs.query({ currentWindow: true, active: true });

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

    try{
        result = await fetch(
            'http://127.0.0.1:5000/'+url,
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