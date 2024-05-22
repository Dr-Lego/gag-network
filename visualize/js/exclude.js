const searchParams = new URLSearchParams(window.location.search)

var connections_count = Object.assign({}, ...DATA.nodes.map(
    node => ({ [node.id]: (node.size - 10) * 2 })
));

var fiftyplus = Object.keys(connections_count).filter(node => connections_count[node] > 50).map(node => node)
var exclude = []

if (searchParams.has("exclude")) {
//if (confirm(`Folgende Themen haben jeweils mehr als 50 Verbingugen, manche sogar mehr als 150, und können die Darstellung erheblich verlangsamen. Willst du sie ausblenden?\n\n${fiftyplus.join(", ")}`)) {
    exclude = fiftyplus;
}