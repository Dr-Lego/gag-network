import vis from 'vis-network/dist/vis-network.min.js';

class Network extends vis.Network {
	NODE_COLOR = 'rgb(230,145,0)';
	EDGE_COLOR = 'RGBA(211, 170, 126, 0.8)';

	constructor(container, data, options, edges) {
		super(container, data, options);
		this.nodesDataset = data.nodes;
		this.edgesDataset = data.edges;
		this.highlightActive = false;
		this.edges = edges;
	}

	nodeDistance = (a, b) => {
		let positions = this.getPositions();
		a = positions[a];
		b = positions[b];
		return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);
	};

	averagePos = (a, b) => {
		// center of two nodes
		let positions = this.getPositions();
		a = positions[a];
		b = positions[b];
		return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
	};

	focusNode = (node) => {
		this.moveTo({
			position: this.getPositions()[node],
			scale: 1.5,
			animation: {
				duration: 400,
				easingFunction: 'easeInOutQuad'
			}
		});
	};

	focusEdge = (from, to, id) => {
		if (id) {
			this.selectEdges([id]);
			const distance = this.nodeDistance(from, to);
			const scale = (Math.min(window.innerHeight, window.innerWidth)-50) / distance;
			this.moveTo({
				position: this.averagePos(from, to),
				scale,
				animation: {
					duration: 400,
					easingFunction: 'easeInOutQuad'
				}
			});
		}
	};

	neighbourhoodHighlight = (params) => {
		// Get all nodes and edges from the network
		const allNodes = this.nodesDataset.get({ returnType: 'Object' });
		const allEdges = this.edgesDataset.get({ returnType: 'Object' });

		// If something is selected
		if (params.nodes.length > 0) {
			// Set the highlight flag to true
			this.highlightActive = true;

			// Get the selected node
			const selectedNode = params.nodes[0];

			// Make all nodes and edges gray
			for (const nodeId in allNodes) {
				allNodes[nodeId].color = 'rgb(230,230,230)';
				allNodes[nodeId].font = { face: 'Poppins', strokeWidth: 5, color: 'grey' };
			}
			for (const edgeId in allEdges) {
				allEdges[edgeId].color = { color: 'rgb(230,230,230)' };
			}

			// Get the connected nodes of the selected node
			const connectedNodes = this.getConnectedNodes(selectedNode);

			// All first degree nodes get their own color and their label back
			for (let i = 0; i < connectedNodes.length; i++) {
				allNodes[connectedNodes[i]].color = this.NODE_COLOR;
				allNodes[connectedNodes[i]].font = { face: 'Poppins', strokeWidth: 5, color: 'black' };
			}
			for (let i = 0; i < params.edges.length; i++) {
				allEdges[params.edges[i]].color = this.EDGE_COLOR;
			}

			// The main node gets its own color and its label back
			allNodes[selectedNode].color = this.NODE_COLOR;
			allNodes[selectedNode].font = { face: 'Poppins', strokeWidth: 5, color: 'black' };
		} else if (params.edges.length > 0) {
			// Set the highlight flag to true
			this.highlightActive = true;

			// Get the selected edge
			const selectedEdge = params.edges[0];

			// Make all nodes and edges gray
			for (const nodeId in allNodes) {
				allNodes[nodeId].color = 'rgb(230,230,230)';
				allNodes[nodeId].font = { face: 'Poppins', strokeWidth: 5, color: 'grey' };
			}
			for (const edgeId in allEdges) {
				allEdges[edgeId].color = { color: 'rgb(230,230,230)' };
			}

			// Get the connected nodes of the selected edge
			const connectedNodes = this.getConnectedNodes(selectedEdge);

			// All first degree nodes get their own color and their label back
			for (let i = 0; i < connectedNodes.length; i++) {
				allNodes[connectedNodes[i]].color = this.NODE_COLOR;
				allNodes[connectedNodes[i]].font = { face: 'Poppins', strokeWidth: 5, color: 'black' };
			}

			// The main edge gets its own color and its label back
			allEdges[selectedEdge].color = this.EDGE_COLOR;
		} else if (this.highlightActive === true) {
			// Reset all nodes
			for (const nodeId in allNodes) {
				allNodes[nodeId].color = this.NODE_COLOR;
			}
			// Reset all edges nodes
			for (const edgeId in allEdges) {
				allEdges[edgeId].color = { color: this.EDGE_COLOR };
			}
			// Set the highlight flag to false
			this.highlightActive = false;
		}

		// Transform the object into an array
		const nodeUpdateArray = [];
		const edgeUpdateArray = [];

		// Push all nodes and edges to the arrays
		for (const nodeId in allNodes) {
			if (allNodes.hasOwnProperty(nodeId)) {
				nodeUpdateArray.push(allNodes[nodeId]);
			}
		}
		for (const edgeId in allEdges) {
			if (allEdges.hasOwnProperty(edgeId)) {
				edgeUpdateArray.push(allEdges[edgeId]);
			}
		}

		// Update the nodes and edges in the network
		this.nodesDataset.update(nodeUpdateArray);
		this.edgesDataset.update(edgeUpdateArray);
	};
}

export default Network;
