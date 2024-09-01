function findMaxDegreeOfSeparation(network) {
    const nodeIds = network.body.data.nodes.getIds();
    let maxDegree = 0;
    let longestPaths = [];
  
    // Floyd-Warshall algorithm for all-pairs shortest paths
    function floydWarshall() {
      const dist = {};
      const next = {};
      nodeIds.forEach(i => {
        dist[i] = {};
        next[i] = {};
        nodeIds.forEach(j => {
          dist[i][j] = i === j ? 0 : Infinity;
          next[i][j] = null;
        });
      });
  
      nodeIds.forEach(i => {
        network.getConnectedNodes(i).forEach(j => {
          dist[i][j] = 1;
          next[i][j] = j;
        });
      });
  
      nodeIds.forEach(k => {
        nodeIds.forEach(i => {
          nodeIds.forEach(j => {
            if (dist[i][k] + dist[k][j] < dist[i][j]) {
              dist[i][j] = dist[i][k] + dist[k][j];
              next[i][j] = next[i][k];
            }
          });
        });
      });
  
      return { dist, next };
    }
  
    // Reconstruct path from Floyd-Warshall result
    function getPath(next, start, end) {
      if (next[start][end] === null) return null;
      const path = [start];
      while (start !== end) {
        start = next[start][end];
        path.push(start);
      }
      return path;
    }
  
    // Main algorithm
    const { dist, next } = floydWarshall();
  
    for (let i = 0; i < nodeIds.length; i++) {
      for (let j = i + 1; j < nodeIds.length; j++) {
        const distance = dist[nodeIds[i]][nodeIds[j]];
        if (distance > maxDegree && distance !== Infinity) {
          maxDegree = distance;
          longestPaths = [getPath(next, nodeIds[i], nodeIds[j])];
        } else if (distance === maxDegree) {
          longestPaths.push(getPath(next, nodeIds[i], nodeIds[j]));
        }
      }
    }
  
    return { maxDegree, longestPaths };
  }