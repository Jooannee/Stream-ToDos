const wsScheme = window.location.protocol === "https:" ? "wss://" : "ws://";
const wsUrl = wsScheme+window.location.host+"/ws/dash/"
var socket = null;

function socketConnect() {
    socket = new WebSocket(wsUrl);
    console.log("Socket connected")
}

function itemMarkDone(listName, itemName) {
    socket.send(JSON.stringify({
        type: "mark_done",
        list: listName,
        item: itemName
    }));
}

document.addEventListener('DOMContentLoaded', () => {
    socketConnect();

    socket.onmessage = function(e) {
        try {
            const data = JSON.parse(e.data);
            listDiv = document.getElementById(`todolist-${data.list}`)
            switch (data.type) {
                case "list_delete":
                    listDiv.remove()
                case "list_update":
                    listDiv.innerHTML = data.html

        }
        } catch (err) {
            console.error("Error processing websocket message: ", err);
        }
    };

    socket.onclose = function(e) {
        console.warn("Websocket closed. Attempting reconnect in 3 Seconds: ", e.reason);
        setTimeout(socketConnect, 3000);
    };
    socket.onerror = function(err) {
        console.error("Websocket error: ", err);
    }
})