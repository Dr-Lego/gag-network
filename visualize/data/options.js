const options = {
    physics: {
        enabled: false,
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {
            gravitationalConstant: -400,
            damping: 0.5,
            springConstant: 0.2,
            avoidOverlap: 1
        },
    },
    nodes: {
        shape: "dot",
        size: 10,
        color: "RGB(230, 145, 0)",
        borderWidth: 0,
        font: {
            face: "Poppins",
            strokeWidth: 5,
            color: "black"
        }
    },
    layout: {
        improvedLayout: false,
    },
    edges: {
        arrows: { to: { scaleFactor: 0.8 }, from: { scaleFactor: 0.8 } },
        color: {
            color: "RGBA(211, 170, 126, 0.8)",//"RGBA(232, 139, 39, 0.5)",
            highlight: "RGBA(211, 170, 126, 1)",
            inherit: false,
        },
        smooth: {
            type: "discrete",
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
    },
    configure: {
        enabled: false,
        showButton: true
    }
};