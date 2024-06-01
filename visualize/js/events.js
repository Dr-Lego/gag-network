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
        neighbourhoodHighlight(params)
    });
}

var highlightActive = false;


function neighbourhoodHighlight(params) {
    // if something is selected:
    if (params.nodes.length > 0) {
      highlightActive = true;
      var i, j;
      var selectedNode = params.nodes[0];
      var degrees = 2;
  
      // mark all nodes as hard to read.
      for (var nodeId in allNodes) {
        allNodes[nodeId].color = "rgb(230,230,230)";
        if (allNodes[nodeId].hiddenLabel === undefined) {
          allNodes[nodeId].hiddenLabel = allNodes[nodeId].label;
          allNodes[nodeId].label = "";
        }
      }
      var connectedNodes = network.getConnectedNodes(selectedNode);
      var allConnectedNodes = [];
  
      // get the second degree nodes
      for (i = 1; i < degrees; i++) {
        for (j = 0; j < connectedNodes.length; j++) {
          allConnectedNodes = allConnectedNodes.concat(
            network.getConnectedNodes(connectedNodes[j])
          );
        }
      }
  
      // all second degree nodes get a different color and their label back
      for (i = 0; i < allConnectedNodes.length; i++) {
        allNodes[allConnectedNodes[i]].color = secondNodeColor;
        if (allNodes[allConnectedNodes[i]].hiddenLabel !== undefined) {
          allNodes[allConnectedNodes[i]].label =
            allNodes[allConnectedNodes[i]].hiddenLabel;
          allNodes[allConnectedNodes[i]].hiddenLabel = undefined;
        }
      }
  
      // all first degree nodes get their own color and their label back
      for (i = 0; i < connectedNodes.length; i++) {
        allNodes[connectedNodes[i]].color = nodeColor;
        if (allNodes[connectedNodes[i]].hiddenLabel !== undefined) {
          allNodes[connectedNodes[i]].label =
            allNodes[connectedNodes[i]].hiddenLabel;
          allNodes[connectedNodes[i]].hiddenLabel = undefined;
        }
      }
  
      // the main node gets its own color and its label back.
      allNodes[selectedNode].color = nodeColor;
      if (allNodes[selectedNode].hiddenLabel !== undefined) {
        allNodes[selectedNode].label = allNodes[selectedNode].hiddenLabel;
        allNodes[selectedNode].hiddenLabel = undefined;
      }
    } else if (highlightActive === true) {
      // reset all nodes
      for (var nodeId in allNodes) {
        allNodes[nodeId].color = nodeColor;
        if (allNodes[nodeId].hiddenLabel !== "") {
          allNodes[nodeId].label = allNodes[nodeId].hiddenLabel;
          allNodes[nodeId].hiddenLabel = undefined;
        }
      }
      highlightActive = false;
    }
  
    // transform the object into an array
    var updateArray = [];
    for (nodeId in allNodes) {
      if (allNodes.hasOwnProperty(nodeId)) {
        updateArray.push(allNodes[nodeId]);
      }
    }
    nodesDataset.update(updateArray);
  }