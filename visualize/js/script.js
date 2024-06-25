var allNodes;
var network;
var currentNode = "";
var highlightActive = false;
var edges;
var data;
var nodesDataset
var edgesDataset;

const dom = {
  "intro": document.getElementById("intro"),
  "stats": document.getElementById("stats"),
  "title": document.getElementById("title"),
  "title_en": document.getElementById("title_en"),
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
  "search_suggestions": document.getElementById("search-suggestions"),
  "context": document.getElementById("context"),
  "context_title": document.getElementById("context-title"),
  "info": document.getElementById("info"),
  "to_exclude": document.getElementById("to-exclude"),
  "exclude_container": document.getElementById("exclude-container")
}

// .visualize/js/events.js


function draw() {
  [nodesDataset, edgesDataset] = Object.values(importNetwork(data))
  edges = Object.values(edgesDataset._data)

  // create a network
  var container = document.getElementById("network");

  var _data = {
    nodes: nodesDataset,
    edges: edgesDataset,
  };

  network = new vis.Network(container, _data, options);
  document.body.removeAttribute("style")

  stats.innerHTML = `<b>Themen:</b><nobr>   ${data.nodes.length}<br><b>Verbindungen:</b>  ${data.edges.length}`

  createEvents()

  // prepare search autocompletion
  Object.keys(nodesDataset._data).sort().forEach(function (item) {
    const option = document.createElement('option');
    option.setAttribute('value', item);
    dom.search_suggestions.appendChild(option);
  });

}

function showNodeInfo(node) {
  dom.intro.style.display = "none"
  currentNode = node.id;
  dom.title.innerHTML = `<a href="https://de.wikipedia.org/wiki/${encodeURIComponent(node.id.replaceAll(" ", "_"))}" target="_blank">${node.id}</a>`
  dom.title_en.innerHTML = `<a href="https://en.wikipedia.org/wiki/${encodeURIComponent(META.translations[node.id].replaceAll(" ", "_"))}" target="_blank">${META.translations[node.id]}</a>`
  dom.description.innerHTML = META.summary[node.id]
  dom.thumbnail.src = META.thumbnail[node.id];

  if (META.thumbnail[node.id] == "") {
    dom.cropped_image.style.display = "none"
  } else {
    dom.cropped_image.style.display = "block"
  }
  dom.cropped_image.style.maxHeight = '25%'
  dom.connections_to.innerHTML = ""
  dom.connections_from.innerHTML = ""
  dom.sidebar_data.style.display = "block"
  episode_display = []
  for (let i = 0; i < META.episodes[node.id].length; i++) {
    const episode = META.episodes[node.id][i];
    episode_display.push(
      `<a class="episode-link" href=${episode.link} target="_blank" style="background-image: url(${META.episode_covers[episode.link.split("/")[episode.link.split("/").length - 2]]})">
      <span><span class="episode-index">${episode.nr}</span>${episode.title}</span>
      </a>`)
      //      <img src="${META.episode_covers[episode.link.split("/")[episode.link.split("/").length - 2]]}">
  };
  dom.episodes.innerHTML = episode_display.join("");
  dom.episodes_number.innerText = `(${episode_display.length})`

  dom.connections_to_section.style.display = "block"
  dom.connections_from_section.style.display = "block"

  dom.info.style.opacity = 0

  // connections to
  let connections_to = edges.filter(
    edge => edge.from === node.id || (edge.to === node.id && edge.arrows == "to, from")
  ).map(
    function (edge) { if (edge.to === node.id) { return edge.from } else { return edge.to } }
  ).sort();

  for (let i = 0; i < connections_to.length; i++) {
    const conn = document.createElement("span")
    conn.className = "connection";
    conn.innerText = connections_to[i];
    dom.connections_to.appendChild(conn)
  };

  if (connections_to.length == 0) { dom.connections_to_section.style.display = "none" }

  // connections from
  let connections_from = edges.filter(
    edge => edge.to === node.id || (edge.from === node.id && edge.arrows == "to, from")
  ).map(
    function (edge) { if (edge.from === node.id) { return edge.to } else { return edge.from } }
  ).sort();

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
    let a; let b;
    $(".connection").removeAttr("style");
    $(this).attr("style", "color:#d34823 !important");
    if (this.parentElement.id.includes("to")) {
      a = currentNode; b = this.innerText;
    } else {
      a = this.innerText; b = currentNode;
    }
    focus_edge(a, b);
    showEdgeInfo(a, b);
  })
}

function showEdgeInfo(a, b) {
  dom.intro.style.display = "none"
  let link = META.links[`${a} -> ${b}`];

  context = link.context;
  context = context.replaceAll(link.text, `<span class="highlighted">${link.text}</span>`)
  dom.context.innerHTML = context
  dom.context_title.innerHTML = `<span class='theme-link'>${a}</span> > <span class='theme-link'>${b}</span>`
  dom.info.style.opacity = 1

  //event listener for theme link
  $(".theme-link").click(
    function () {
      showNodeInfo(nodesDataset.get($(this).text()));
      network.selectNodes([$(this).text()])
    }
  )
}


function search(elem) {
  if (event.key === 'Enter') {
    // remove focus
    document.activeElement.blur()
    showNodeInfo(nodesDataset.get(elem.value));
    network.selectNodes([elem.value]);
    neighbourhoodHighlight({ 'nodes': [elem.value] });
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
  var _nodes = objectToArray(network.getPositions());
  var _edgesDataset = Object.values(edgesDataset._data)
  console.log(JSON.stringify({ "nodes": _nodes, "edgesDataset": _edgesDataset }, undefined, 2))
}

function importNetwork(save) {
  let nodes = []
  let edges = []
  let ids = {}
  const arrows = {
    0: "to, from",
    1: "to"
  }

  for (let i = 0; i < save.nodes.length; i++) {
    const node = save.nodes[i];
    let _node = { "id": node[0], "label": node[0], "size": node[1], "x": node[2], "y": node[3] }
    if (node.length == 5) {
      _node["image"] = save.icons[node[4]]
      _node["shape"] = "circularImage"
    }
    nodes.push(_node)
    ids[i + 1] = node[0]
  }

  for (let i = 0; i < save.edges.length; i++) {
    const edge = save.edges[i];
    if (edge.length == 2) {
      edge.push(0)
    }
    edges.push(
      { "arrows": arrows[edge[2]], "from": ids[edge[0]], "to": ids[edge[1]], "id": `${ids[edge[0]]}-${ids[edge[1]]}` }
    )
  }

  return {
    nodes: new vis.DataSet(nodes),
    edges: new vis.DataSet(edges),
  }
}

function objectToArray(obj) {
  return Object.keys(obj).map(function (key) { obj[key].id = key; return obj[key] });
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
  // center of two nodes
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
  edge = edges.filter(
    edge => [a, b].sort().toString() == [edge.to, edge.from].sort().toString()
  )[0].id;
  network.selectEdges([edge])

  // linear scaling function found using two fixed points
  scale = Math.max(0.25, -0.000366703337 * nodeDistance(a, b) + 1.383498349835)

  network.moveTo({
    position: averagePos(a, b),
    scale: scale,
    animation: {
      duration: 400,
      easingFunction: "easeInOutQuad"
    }
  });
}


var connections_count = Object.assign({}, ...SAVE.full.nodes.map(
  node => ({ [node[0]]: (node[1] - 10) * 2 })
));
var fiftyplus = Object.keys(connections_count).filter(node => connections_count[node] > 80).map(node => node)
dom.to_exclude.innerHTML = fiftyplus.join(", ")


$(".button").click(function (event) {
  data = SAVE[{ "yes": "small", "no": "full" }[event.target.id]];
  delete SAVE;
  draw();
  dom.exclude_container.style.opacity = 0;
  dom.exclude_container.style.pointerEvents = "none";
  setTimeout(function () { dom.exclude_container.remove() }, 1000)
})
