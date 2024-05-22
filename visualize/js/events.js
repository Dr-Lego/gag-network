
function createEvents() {
    network.on("stabilizationProgress", function (params) {
        document.getElementById('loading').innerText = `${Math.round((params.iterations / params.total) * 100).toString()}%`
    });

    network.on("stabilizationIterationsDone", function () {
        document.body.removeAttribute("style")
        document.getElementById('loading-container').classList.toggle("fade-out", true) //style.display = "none"
    });

    network.on('click', function (params) {
        document.activeElement.blur()
        let node = nodesDataset.get(params.nodes[0]);
        let edge = edgesDataset.get(params.edges[0]);
        if (node.id) {
            dom.intro.style.display = "none"
            showNodeInfo(node);
        } else if (edge.id) {
            dom.intro.style.display = "none"
            showNodeInfo(nodesDataset.get(edge.from));
            showEdgeInfo(edge.from, edge.to);
        } else {
            dom.intro.style.display = "block"
            dom.title.innerHTML = ""
            dom.title_en.innerHTML = ""
            dom.description.innerHTML = ""
            dom.episodes.innerHTML = ""
            dom.thumbnail.src = "assets/gag-logo.webp"
            dom.sidebar_data.style.display = "none";
            dom.info.style.opacity = 0
            currentNode = ""
        };
        //neighbourhoodHighlight(properties)
    });
}
