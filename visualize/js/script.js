var highlightActive = false;
var allNodes;
var network;
var currentNode = "";
nodesDataset = new vis.DataSet();
nodesDataset.add(DATA["nodes"]);
edges = new vis.DataSet();
edges.add(DATA["edges"]);
console.log("test")

const dom = {
  "title": document.getElementById("title"),
  "description": document.getElementById("description"),
  "episodes": document.getElementById("episodes"),
  "thumbnail": document.getElementById("thumbnail"),
  "cropped_image": document.getElementById("cropped-image"),
  "connections_to": document.getElementById("connections-to-wrapper"),
  "connections_from": document.getElementById("connections-from-wrapper"),
  "connections_to_section": document.getElementById("connections-to-section"),
  "connections_from_section": document.getElementById("connections-from-section"),
  "sidebar_data": document.getElementById("sidebar-data"),
  "connections_number": document.getElementById("connections-number"),
  "episodes_number": document.getElementById("episodes-number"),
  "search": document.getElementById("search"),
  "search_suggestions": document.getElementById("search-suggestions")
}


function draw() {
  // create a network
  var container = document.getElementById("network");
  var data = {
    nodes: nodesDataset,
    edges: edges,
  };
  //var data = { nodes: getNodeData(SAVE), edges: getEdgeData(SAVE) };
  //data = importNetwork(SAVE)
  console.log("imported")
  network = new vis.Network(container, data, options);

  network.stabilize(1000)

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
      dom.description.innerHTML = ""
      dom.episodes.innerHTML = ""
      dom.thumbnail.src = "assets/gag-logo.webp"
      dom.sidebar_data.style.display = "none";
      currentNode = ""
    } else {
      showInfo(node)
    };
  });

  // search
  Object.keys(nodesDataset._data).sort().forEach(function (item) {
    const option = document.createElement('option');
    option.setAttribute('value', item);
    dom.search_suggestions.appendChild(option);
  });
}

function showInfo(node) {
  currentNode = node.id;
  dom.title.innerHTML = `<a href="https://de.wikipedia.org/wiki/${encodeURIComponent(node.id.replaceAll(" ", "_"))}" target="_blank">${node.id}</a>`
  dom.description.innerHTML = DATA.meta.summary[node.id]
  dom.thumbnail.src = DATA.meta.thumbnail[node.id];

  if (DATA.meta.thumbnail[node.id] == "") {
    dom.cropped_image.style.display = "none"
  } else {
    dom.cropped_image.style.display = "block"
  }
  dom.cropped_image.style.maxHeight = '25%'
  dom.connections_to.innerHTML = ""
  dom.connections_from.innerHTML = ""
  dom.sidebar_data.style.display = "block"
  episode_display = []
  for (let i = 0; i < DATA.meta.episodes[node.id].length; i++) {
    const episode = DATA.meta.episodes[node.id][i];
    episode_display.push(`<a class="episode-link" href=${JSON.parse(episode.links.replaceAll("'", '"'))[0]} target="_blank"><span class="episode-index">${episode.nr}</span>${episode.title}</a>`)
  };
  dom.episodes.innerHTML = episode_display.join("");
  dom.episodes_number.innerText = `(${episode_display.length})`

  dom.connections_to_section.style.display = "block"
  dom.connections_from_section.style.display = "block"

  // connections to
  let connections_to = DATA["edges"].filter(
    edge => edge.from === node.id || (edge.to === node.id && edge.arrows == "to, from")
  ).map(
    function (edge) { if (edge.to === node.id) { return edge.from } else { return edge.to } }
  );

  for (let i = 0; i < connections_to.length; i++) {
    const conn = document.createElement("span")
    conn.className = "connection";
    conn.innerText = connections_to[i];
    dom.connections_to.appendChild(conn)
  };

  if (connections_to.length == 0) { dom.connections_to_section.style.display = "none" }

  // connections from
  let connections_from = DATA["edges"].filter(
    edge => edge.to === node.id || (edge.from === node.id && edge.arrows == "to, from")
  ).map(
    function (edge) { if (edge.from === node.id) { return edge.to } else { return edge.from } }
  );

  for (let i = 0; i < connections_from.length; i++) {
    const conn = document.createElement("span")
    conn.className = "connection";
    conn.innerText = connections_from[i];
    dom.connections_from.appendChild(conn)
  };

  if (connections_from.length == 0) { dom.connections_from_section.style.display = "none" }

  dom.connections_number.innerText = `(${Array.from(new Set(connections_to.concat(connections_from))).length})`

  // edge event listener
  $(".connection").click(function () {
    console.log("test");
    focus_edge(currentNode, this.innerText)
  })
}

function search(elem) {
  if (event.key === 'Enter') {
    document.activeElement.blur()
    showInfo(nodesDataset.get(elem.value));
    network.selectNodes([elem.value])
    focus_node(elem.value);
  }
}

function imageAnimate() {
  if (dom.cropped_image.style.maxHeight == '25%') {
    dom.cropped_image.style.maxHeight = '100%';
  } else {
    dom.cropped_image.style.maxHeight = '25%'
  }
}


function exportNetwork() {
  var _nodes = objectToarrows_to(network.getPositions());
  var _edges = Object.values(edges._data)
  console.log(JSON.stringify({ "nodes": _nodes, "edges": _edges }, undefined, 2))
}

function importNetwork(save) {
  return {
    nodes: getNodeData(save.nodes),
    edges: new vis.DataSet(save.edges),
  }
}

function objectToarrows_to(obj) {
  return Object.keys(obj).map(function (key) { obj[key].id = key; return obj[key] });
}


function getNodeData(data) {
  var networkNodes = [];

  data.forEach(function (elem, index) {
    networkNodes.push({
      id: elem.id,
      label: elem.id,
      x: elem.x,
      y: elem.y,
    });
  });

  return new vis.DataSet(networkNodes);
}

function focus_node(node) {
  network.moveTo({
    position: network.getPositions()[node],
    scale: 1.5,
    animation: {
      duration: 400,
      easingFunction: "easeInOutQuad"
    }
  });
}

function averagePos(a, b) {
  positions = network.getPositions()
  a = positions[a]
  b = positions[b]
  return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 }
}

function nodeDistance(a, b) {
  positions = network.getPositions()
  a = positions[a]
  b = positions[b]
  return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
}

function focus_edge(a, b) {
  edge = DATA["edges"].filter(
    edge => [a, b].sort().toString() == [edge.to, edge.from].sort().toString()
  )[0].id;
  network.selectEdges([edge])

  scale = -0.000366703337 * nodeDistance(a, b) + 1.383498349835

  network.moveTo({
    position: averagePos(a, b),
    scale: scale,
    animation: {
      duration: 400,
      easingFunction: "easeInOutQuad"
    }
  });
}


draw()