
function createEvents(params) {
    network.on("stabilizationProgress", function (params) {
        document.getElementById('loading').innerText = `${Math.round((params.iterations / params.total) * 100).toString()}%`
    });

    network.on("stabilizationIterationsDone", function () {
        document.body.removeAttribute("style")
        document.getElementById('loading-container').classList.toggle("fade-out", true) //style.display = "none"
    });

    network.on('click', function (properties) {
        document.activeElement.blur()
        let node = nodesDataset.get(properties.nodes[0]);
        if (node.id == undefined) {
            dom.title.innerHTML = "Geschichten aus der Geschichten<br>»Flickenteppich«"
            dom.title_en.innerHTML = ""
            dom.description.innerHTML = ""
            dom.episodes.innerHTML = ""
            dom.thumbnail.src = "assets/gag-logo.webp"
            dom.sidebar_data.style.display = "none";
            dom.info.style.opacity = 0
            currentNode = ""
        } else {
            showNodeInfo(node)
        };
    });
}
