const options = {
    physics: {
        enabled: false,
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {
            gravitationalConstant: -400,
            springLength: 70,
            avoidOverlap: 1
        }
    },
    nodes: {
        shape: "dot",
        size: 10,
        color: "RGB(211, 126, 35)",
        font: {
            face: "Poppins"
        }
    },
    layout: {
        improvedLayout: false,
    },
    edges: {
        arrows: { to: { scaleFactor: 0.8 }, from: { scaleFactor: 0.8 } },
        color: {
            color: "RGBA(211, 126, 35, 0.5)",
            hover: "RGBA(211, 170, 126, 1)",
            highlight: "RGBA(211, 170, 126, 1)",
            inherit: false,
        },
        smooth: {
            type: "continuous",
        },
        hoverWidth: 4,
        selectionWidth: 4,
        font: {
            size: 8
        }
    },
    interaction: {
        hoverConnectedEdges: true,
        dragNodes: false
    }
};