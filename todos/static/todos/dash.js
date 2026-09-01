const wsScheme = window.location.protocol === "https:" ? "wss://" : "ws://";
const wsUrl = wsScheme + window.location.host + "/ws/dash/";
var socket = null;

function socketConnect() {
    socket = new WebSocket(wsUrl);
    
    socket.onmessage = function(e) {
        try {
            const data = JSON.parse(e.data);
            const listDiv = document.getElementById(`todolist-${data.list}`);
            
            switch (data.type) {
                case "list_delete":
                    if (listDiv) {
                        listDiv.classList.add('opacity-0', 'scale-95');
                        setTimeout(() => {
                            listDiv.remove();
                            updateListCount(-1);
                        }, 300);
                    }
                    break;
                case "list_update":
                    if (listDiv) {
                        listDiv.innerHTML = data.html;
                        formListenersCreateItem();
                    }
                    break;
                case "list_create":
                    const listsContainer = document.getElementById("todolists-container");
                    if (listsContainer) {
                        const newDiv = document.createElement("div");
                        newDiv.id = `todolist-${data.list}`;
                        newDiv.className = "bg-dreamy-deep border border-dreamy-lavender/10 rounded-2xl shadow-xl flex flex-col h-full hover:border-dreamy-lavender/30 hover:shadow-purple-950/20 transition-all opacity-0 scale-95 duration-300";
                        newDiv.innerHTML = data.html;
                        listsContainer.appendChild(newDiv);
                        
                        setTimeout(() => {
                            newDiv.classList.remove('opacity-0', 'scale-95');
                        }, 50);
                        
                        formListenersCreateItem();
                        updateListCount(1);
                    }
                    break;
                case "success":
                    console.log(`Success: ${data.message}`);
                    showToast(data.message, "success");
                    break;
                case "error":
                    console.error(`Error: ${data.message}`);
                    showToast(data.message, "error");
                    break;
            }
        } catch (err) {
            console.error("Error processing websocket message: ", err);
        }
    };

    socket.onclose = function(e) {
        console.warn("Websocket closed. Attempting reconnect in 3 seconds...", e.reason);
        setTimeout(socketConnect, 3000);
    };

    socket.onerror = function(err) {
        console.error("Websocket error: ", err);
    };
}

function itemMarkDone(listName, itemIndex) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: "mark_done",
            list: listName,
            item: itemIndex
        }));
    }
}

function createItem(listName, itemName) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: "new_item",
            list_name: listName,
            item_name: itemName
        }));
    }
}

function createList(listName) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: "new_list",
            list_name: listName
        }));
    }
}

function deleteList(listName) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: "delete_list",
            list_name: listName
        }));
    }
}

function setChatList(listName) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: "set_chat_list",
            list_name: listName
        }));
    }
}

function setStreamerList(listName) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
            type: "set_streamer_list",
            list_name: listName
        }));
    }
}

function handleFormSubmit(event) {
    event.preventDefault();
    const element = event.currentTarget;
    const data = new FormData(element);
    const listName = data.get("listname");
    const itemName = data.get("itemName");
    
    createItem(listName, itemName);
    element.reset();
}

function formListenersCreateItem() {
    const elements = document.getElementsByClassName("form-newitem");
    Array.from(elements).forEach((element) => {
        element.removeEventListener("submit", handleFormSubmit);
        element.addEventListener("submit", handleFormSubmit);
    });
}

function updateListCount(diff) {
    const countEl = document.getElementById("lists-count");
    if (countEl) {
        let currentCount = parseInt(countEl.innerText) || 0;
        countEl.innerText = Math.max(0, currentCount + diff);
    }
}

window.showToast = function(message, type = "success") {
    const container = document.getElementById("toast-container");
    if (!container) return;
    
    const toast = document.createElement("div");
    toast.className = `px-4 py-3 rounded-xl shadow-2xl text-white ${type === 'success' ? 'bg-green-600' : 'bg-red-600'} flex items-center gap-3 border border-white/10 min-w-[280px] max-w-sm transition-all duration-300 transform translate-y-2 opacity-0 shadow-lg`;
    
    const icon = type === "success" ? "fa-circle-check" : "fa-circle-exclamation";
    toast.innerHTML = `
        <i class="fa-solid ${icon} text-base"></i>
        <span class="text-xs font-semibold">${message}</span>
        <button class="ml-auto text-white/70 hover:text-white transition-opacity">
            <i class="fa-solid fa-xmark"></i>
        </button>
    `;
    
    toast.querySelector("button").addEventListener("click", () => {
        toast.classList.remove('translate-y-0', 'opacity-100');
        toast.classList.add('translate-y-2', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    });
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
        toast.classList.add('translate-y-0', 'opacity-100');
    }, 50);
    
    setTimeout(() => {
        if (toast.parentNode) {
            toast.classList.remove('translate-y-0', 'opacity-100');
            toast.classList.add('translate-y-2', 'opacity-0');
            setTimeout(() => toast.remove(), 300);
        }
    }, 3500);
};

document.addEventListener('DOMContentLoaded', () => {
    socketConnect();

    $("#form-newlist").submit(function(event) {
        event.preventDefault();
        const input = $("#newlist-title");
        createList(input.val());
        input.val("");
    });
    
    formListenersCreateItem();
});