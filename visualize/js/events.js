function createEvents() {
    const _dom = {
        "intro": document.getElementById("intro"),
        "title": document.getElementById("title"),
        "title_en": document.getElementById("title_en"),
        "sidebar_data": document.getElementById("sidebar-data"),
        "description": document.getElementById("description"),
        "episodes": document.getElementById("episodes"),
        "thumbnail": document.getElementById("thumbnail"),
        "info": document.getElementById("info")
    }
    
    
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
            _dom.intro.style.display = "none"
            showNodeInfo(node);
        } else if (edge.id) {
            _dom.intro.style.display = "none"
            showNodeInfo(nodesDataset.get(edge.from));
            showEdgeInfo(edge.from, edge.to);
        } else {
            _dom.intro.style.display = "block"
            _dom.title.innerHTML = ""
            _dom.title_en.innerHTML = ""
            _dom.description.innerHTML = ""
            _dom.episodes.innerHTML = ""
            _dom.thumbnail.src = "assets/gag-logo.webp"
            _dom.sidebar_data.style.display = "none";
            _dom.info.style.opacity = 0
            currentNode = ""
        };
        //neighbourhoodHighlight(properties)
    });
}
