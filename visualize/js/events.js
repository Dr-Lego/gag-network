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
        //document.getElementById('loading').innerText = `${Math.round((params.iterations / params.total) * 100).toString()}%`
    });

    network.on("stabilizationIterationsDone", function () {
       document.body.removeAttribute("style")
       // document.getElementById('loading-container').classList.toggle("fade-out", true) //style.display = "none"
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
        neighbourhoodHighlight(params)
    });
}

var highlightActive = false;
const nodeColor = "RGB(230, 145, 0)"
const edgeColor = "RGBA(211, 170, 126, 0.8)"
const secondNodeColor = "RGB(211, 126, 35)"


function neighbourhoodHighlight(params) {
    allNodes = nodesDataset.get({ returnType: "Object" });
    let allEdges = edgesDataset.get({ returnType: "Object" });

    // if something is selected:
    if (params.nodes.length > 0) {
        highlightActive = true;
        var i;
        var selectedNode = params.nodes[0];

        // make all nodes and edges gray.
        for (var nodeId in allNodes) {
            allNodes[nodeId].color = "rgb(230,230,230)";
            allNodes[nodeId].font = { face: "Poppins", strokeWidth: 5, color: "grey" };
        };
        for (var edgeId in allEdges) {
            allEdges[edgeId].color = { color: "rgb(230,230,230)" };
        };

        var connectedNodes = network.getConnectedNodes(selectedNode);
        var connectedEdges = network.getConnectedEdges(selectedNode);

        // all first degree nodes get their own color and their label back
        for (i = 0; i < connectedNodes.length; i++) {
            allNodes[connectedNodes[i]].color = nodeColor;
            allNodes[connectedNodes[i]].font = { face: "Poppins", strokeWidth: 5, color: "black" };
        };
        for (i = 0; i < connectedEdges.length; i++) {
            allEdges[connectedEdges[i]].color = edgeColor;
        };

        // the main node gets its own color and its label back.
        allNodes[selectedNode].color = nodeColor;
        allNodes[selectedNode].font = { face: "Poppins", strokeWidth: 5, color: "black" };

    } else if (params.edges.length > 0) {
        highlightActive = true;
        var i;
        var selectedEdge = params.edges[0];

        // make all nodes and edges gray.
        for (var nodeId in allNodes) {
            allNodes[nodeId].color = "rgb(230,230,230)";
            allNodes[nodeId].font = { face: "Poppins", strokeWidth: 5, color: "grey" };
        };
        for (var edgeId in allEdges) {
            allEdges[edgeId].color = { color: "rgb(230,230,230)" };
        };

        var connectedNodes = network.getConnectedNodes(selectedEdge);

        // all first degree nodes get their own color and their label back
        for (i = 0; i < connectedNodes.length; i++) {
            allNodes[connectedNodes[i]].color = nodeColor;
            allNodes[connectedNodes[i]].font = { face: "Poppins", strokeWidth: 5, color: "black" };
        };

        // the main node gets its own color and its label back.
        allEdges[selectedEdge].color = edgeColor;

    } else if (highlightActive === true) {
        // reset all nodes
        for (var nodeId in allNodes) {
            allNodes[nodeId].color = nodeColor;
        };
        // reset all edges nodes
        for (var edgeId in allEdges) {
            allEdges[edgeId].color = { color: edgeColor };
        };
        highlightActive = false;
    }

    // transform the object into an array
    var nodeUpdateArray = [];
    var edgeUpdateArray = [];
    for (nodeId in allNodes) {
        if (allNodes.hasOwnProperty(nodeId)) {
            nodeUpdateArray.push(allNodes[nodeId]);
        }
    }
    for (edgeId in allEdges) {
        if (allEdges.hasOwnProperty(edgeId)) {
            edgeUpdateArray.push(allEdges[edgeId]);
        }
    }
    nodesDataset.update(nodeUpdateArray);
    edgesDataset.update(edgeUpdateArray);
}