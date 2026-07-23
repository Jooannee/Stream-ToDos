document.addEventListener('DOMContentLoaded', () => {
    const listContainer = document.getElementById("list-container");
    const $listView = $("#list-view");
    const widgetCount = document.getElementById("widget-count");
    const widgetTitle = document.getElementById("widget-title");

    const scrollSpeed = 0.1; //Pixels per ms
    const pauseDuration = 10000; //in ms

    function getScrollDuration(targetScrolltop) {
        const currentScrolltop = $listView.scrollTop();
        const distance = Math.abs(currentScrolltop-targetScrolltop);
        return distance/scrollSpeed;
    }
    function scrollToTop(){
        $listView.stop().animate({scrollTop:0}, getScrollDuration(0), 'linear', () => { 
        setTimeout(scrollToBottom, pauseDuration);
        });
    }
    function scrollToBottom(){
        var maxScroll = $listView[0].scrollHeight-$listView[0].clientHeight;
        $listView.stop().animate({scrollTop:maxScroll}, getScrollDuration(maxScroll), 'linear', ()=> { 
        setTimeout(scrollToTop, pauseDuration);
        });
    }

    function updateCounter() {
        const emptyDiv = document.getElementById("empty-state");
        if (emptyDiv){currCount=0}
        else{currCount = document.getElementsByClassName("item-pending").length}
        widgetCount.innerHTML = currCount;
    }

    //Websocket Things c:
    const wsScheme = window.location.protocol === "https:" ? "wss://" : "ws://";
    const urlArgs = window.location.pathname.split("/");
    const wsUrl = wsScheme+window.location.host+"/ws/todo/"+urlArgs[2]+"/"+urlArgs[3]+"/";

    function connectSocket() {
        const socket = new WebSocket(wsUrl);
        console.log("Websocket connected")

        socket.onmessage = function(e) {
            try {
                const data = JSON.parse(e.data);
                if (data.type === "todo_update" && data.html !== undefined) {
                    listContainer.innerHTML = data.html;
                    widgetTitle.innerHTML = data.todo_title;
                    
                    updateCounter()
                }
            } catch (err) {
                console.error("Error processing websocket message: ", err);
            }
        };

        socket.onclose = function(e) {
            console.warn("Websocket closed. Attempting reconnect in 3 Seconds: ", e.reason);
            setTimeout(connectSocket, 3000);
        };

        socket.onerror = function(err) {
            console.error("Websocket error: ", err);
        }
    }
    connectSocket();


    //Start scrolling cycle on page load
    scrollToBottom()
    //Update todo counter on page load
    updateCounter()
})