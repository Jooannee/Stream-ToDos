document.addEventListener('DOMContentLoaded', () => {
    const listContainer = document.getElementById("list-container");
    const $listView = $("#list-view");
    const widgetCount = document.getElementById("widget-count");

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
        setTimeout(scrollToTop, pauseDuration)
        });
    }

    function updateCounter() {
        const emptyDiv = document.getElementById("empty-state")
        if (emptyDiv!==null){currCount=0}
        else{currCount = listContainer.childElementCount}
        widgetCount.innerHTML = currCount
    }

    //Start scrolling cycle on page load
    scrollToBottom()
    //Update todo counter on page load
    updateCounter()
})