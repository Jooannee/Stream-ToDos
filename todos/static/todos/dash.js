const wsScheme = window.location.protocol === "https:" ? "wss://" : "ws://";
const wsUrl = wsScheme+window.location.host+"/ws/dash/"
var socket = null;

function socketConnect() {
    socket = new WebSocket(wsUrl);
    console.log("Socket connected")
}

function itemMarkDone(listName, itemIndex) {
    socket.send(JSON.stringify({
        type: "mark_done",
        list: listName,
        item: itemIndex
    }));
}
function createItem(listName, itemName) {
    socket.send(JSON.stringify({
        type: "new_item",
        list_name: listName,
        item_name: itemName
    }))
}
function createList(listName) {
    socket.send(JSON.stringify({
        type: "new_list",
        list_name: listName,
    }))
}
function deleteList(listName) {
    socket.send(JSON.stringify({
        type: "delete_list",
        list_name: listName
    }))
}
function setChatList(listName) {
    socket.send(JSON.stringify({
        type: "set_chat_list",
        list_name: listName
    }))
}
function setStreamerList(listName) {
    socket.send(JSON.stringify({
        type: "set_streamer_list",
        list_name: listName
    }))
}

function handleFormSubmit(event) {
    event.preventDefault();

    const element = event.currentTarget;
    const data = new FormData(element);
    const listName = data.get("listname");
    const itemName = data.get("itemName");
    
    createItem(listName, itemName);
}
function formListenersCreateItem() {
    const elements = document.getElementsByClassName("form-newitem");
    
    Array.from(elements).forEach((element) => {
        element.removeEventListener("submit", handleFormSubmit);
        element.addEventListener("submit", handleFormSubmit);
    });
}


document.addEventListener('DOMContentLoaded', () => {
    socketConnect();

    socket.onmessage = function(e) {
        try {
            const data = JSON.parse(e.data);
            listDiv = document.getElementById(`todolist-${data.list}`)
            switch (data.type) {
                case "list_delete":
                    listDiv.remove();
                    break;
                case "list_update":
                    listDiv.innerHTML = data.html;
                    formListenersCreateItem();
                    break;
                case "list_create":
                    listsContainer = document.getElementById("todolists-container")
                    newDiv = listsContainer.appendChild(document.createElement("div"))
                    newDiv.id = `todolist-${data.list}`
                    newDiv.innerHTML = data.html
                    formListenersCreateItem();
                case "success":
                    console.log(`Successful task: ${data.message}`);
                    break;
                case "error":
                    console.error(`Error while executing Task: ${data.message}`);
                    break;

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


    $("#form-newlist").submit(function(event) {
        event.preventDefault();
        createList($("#newlist-title").val());
    })
    formListenersCreateItem();
})