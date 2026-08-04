const wsScheme = window.location.protocol === "https:" ? "wss://" : "ws://";
const wsUrl = wsScheme+window.location.host+"/ws/dash/"

function connectSocket() {
    const socket = new WebSocket(wsUrl);
    console.log("Websocket connected")

    socket.onmessage = function(e) {
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


function itemMarkDone(listName, itemName) {
    const socket = new WebSocket(wsUrl);
    socket.onopen = function(e) {
    socket.send(JSON.stringify({
        type: "mark_done",
        list: listName,
        item: itemName
    }));
    socket.close();
    }
}