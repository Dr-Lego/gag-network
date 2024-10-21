<script>
	import Intro from '../lib/components/Intro.svelte';
	import Exclude from '../lib/components/Exclude.svelte';
	import { SAVE } from '$lib/data/save.js';
	import { META } from '$lib/data/meta.js';
	import { options } from '$lib/data/options.js';
	import distance from 'jaro-winkler';
	import vis from 'vis-network/dist/vis-network.min.js';
	import MagnifyingGlass from '$lib/assets/search.svg';
	import Network from '$lib/network.js';

	let network;
	let currentNode = '';
	let highlightActive = false;
	let edges;
	let data;
	let nodesDataset;
	let edgesDataset;
	let exclude;
	let stats = {
		nodes: 0,
		edges: 0
	};
	let introActive = true;
	let infoActive = false;
	let title = {
		en: '',
		de: ''
	};
	let context = {
		text: '',
		title: ''
	};
	let enlargedImage = false;
	let activeConnection = { name: '', type: '' };
	let description = '';
	let thumbnail = false;
	let connectionsTo = [];
	let connectionsFrom = [];
	let episodes = [];
	let searchSuggestions = [];
	let searchTerm = '';

	let connectionCounts = Object.fromEntries(
		SAVE.full.nodes.map(([id, connections]) => [id, (connections - 10) * 2])
	);

	let fiftyplus = Object.entries(connectionCounts)
		.filter(([, count]) => count > 80)
		.map(([id]) => id);

	function createEvents() {
		network.on('click', (params) => {
			document.activeElement.blur();
			let clickedNode = nodesDataset.get(params.nodes[0]);
			let clickedEdge = edgesDataset.get(params.edges[0]);

			if (clickedNode?.id) {
				introActive = false;
				showNodeInfo(clickedNode);
			} else if (clickedEdge?.id) {
				introActive = false;
				let { from, to } = clickedEdge;
				showNodeInfo(nodesDataset.get(from));
				showEdgeInfo(from, to);
			} else {
				resetInterface();
			}

			network.neighbourhoodHighlight(params);
		});
	}

	function resetInterface() {
		introActive = true;
		title = { en: '', de: '' };
		description = '';
		episodes = [];
		thumbnail = false;
		infoActive = false;
		currentNode = '';
	}

	function showEdgeInfo(a, b) {
		introActive = false;
		let link = META.links[`${a} -> ${b}`];

		context.text = link.context.replaceAll(
			link.text,
			`<span class="highlighted">${link.text}</span>`
		);
		context.title = [a, b];
		infoActive = true;
	}

	function showNodeInfo(node) {
		introActive = false;
		infoActive = false;
		enlargedImage = false;
		activeConnection = { name: '', type: '' };

		currentNode = node.id;
		title = {
			en: META.translations[node.id],
			de: node.id
		};
		description = META.summary[node.id];
		thumbnail = META.thumbnail[node.id];

		episodes = [];
		for (let i = 0; i < META.episodes[node.id].length; i++) {
			const episode = META.episodes[node.id][i];
			episodes.push({
				nr: episode.nr,
				title: episode.title,
				link: episode.link,
				cover: META.episode_covers[episode.link.split('/')[episode.link.split('/').length - 2]]
			});
		}

		connectionsTo = edges
			.filter((edge) => edge.from === node.id || (edge.to === node.id && edge.arrows == 'to, from'))
			.map(function (edge) {
				if (edge.to === node.id) {
					return edge.from;
				} else {
					return edge.to;
				}
			})
			.sort();

		connectionsFrom = edges
			.filter((edge) => edge.to === node.id || (edge.from === node.id && edge.arrows == 'to, from'))
			.map(function (edge) {
				if (edge.from === node.id) {
					return edge.to;
				} else {
					return edge.from;
				}
			})
			.sort();
	}

	function search(term) {
		term = term.toLowerCase();
		const suggestionsWithSimilarity = searchSuggestions.map((suggestion) => [
			suggestion,
			distance(term, suggestion)
		]);
		const sortedSuggestions = suggestionsWithSimilarity.sort((a, b) => b[1] - a[1]);
		const bestMatch = sortedSuggestions[0][0];

		document.activeElement.blur();
		showNodeInfo(nodesDataset.get(bestMatch));
		network.selectNodes([bestMatch]);
		network.neighbourhoodHighlight({
			nodes: [bestMatch],
			edges: network.getConnectedEdges(bestMatch)
		});
		network.focusNode(bestMatch);
		searchTerm = '';
	}

	function connectionClicked(connection, type) {
		let a;
		let b;

		activeConnection.name = connection;
		activeConnection.type = type;

		if (type == 'to') {
			a = currentNode;
			b = connection;
		} else {
			a = connection;
			b = currentNode;
		}

		const edgeId = edges.find(
			(edge) => [a, b].sort().toString() === [edge.to, edge.from].sort().toString()
		)?.id;
		network.focusEdge(a, b, edgeId);
		showEdgeInfo(a, b);
	}

	function themeLinkClicked(theme) {
		let node = nodesDataset.get(theme);
		network.selectNodes([theme]);
		document.activeElement.blur();

		showNodeInfo(node);
		network.neighbourhoodHighlight({ nodes: [theme], edges: network.getConnectedEdges(theme) });
		network.focusNode(theme);
	}

	function importNetwork(save) {
		let nodes = [];
		let ids = {};

		edges = [];

		for (let i = 0; i < save.nodes.length; i++) {
			const node = save.nodes[i];
			let _node = { id: node[0], label: node[0], size: node[1], x: node[2], y: node[3] };
			if (node.length == 5) {
				_node['image'] = save.icons[node[4]];
				_node['shape'] = 'circularImage';
			}
			nodes.push(_node);
			ids[i + 1] = node[0];
		}

		for (let i = 0; i < save.edges.length; i++) {
			const edge = save.edges[i];
			if (edge.length == 2) {
				edge.push(0);
			}
			edges.push({
				arrows: [edge[2]] ? 'to' : 'to, from',
				from: ids[edge[0]],
				to: ids[edge[1]],
				id: `${ids[edge[0]]}-${ids[edge[1]]}`
			});
		}

		return {
			nodes: new vis.DataSet(nodes),
			edges: new vis.DataSet(edges)
		};
	}

	function draw() {
		[nodesDataset, edgesDataset] = Object.values(importNetwork(data));

		// create a network
		var container = document.getElementById('network');

		var _data = {
			nodes: nodesDataset,
			edges: edgesDataset
		};

		network = new Network(container, _data, options, edges);

		console.log()

		stats = {
			nodes: nodesDataset.length,
			edges: edgesDataset.length
		};

		createEvents();

		// prepare search autocompletion
		searchSuggestions = data.nodes.map((node) => node[0]);
	}

	function main(e) {
		data = SAVE[e.detail.size];
		setTimeout(() => {
			exclude.$destroy();
		}, 1000);

		draw();
	}
</script>

<div id="network" class="w-full h-full"></div>

<Exclude bind:this={exclude} on:start={main} to_exclude={fiftyplus.join(', ')} />

<section class="w-1/4 h-full overflow-hidden shadow-default">
	<input
		type="text"
		id="search"
		class="relative w-full py-4 pl-4 font-sans text-xl text-center bg-center bg-no-repeat border-b-2 outline-none border-light"
		style='background: url("{MagnifyingGlass}") 12px 50% / 20pt no-repeat white;'
		list="search-suggestions"
		spellcheck="false"
		placeholder="Finde ein Thema..."
		bind:value={searchTerm}
		on:keydown={(e) => e.key === 'Enter' && search(e.target.value)}
	/>
	<datalist id="search-suggestions">
		{#each searchSuggestions as suggestion}
			<option class="absolute right-5" value={suggestion}>{suggestion}</option>
		{/each}
	</datalist>

	<!-- Sidebar -->
	<div class="overflow-x-hidde z-10 h-[calc(100%-58px)] w-full overflow-y-auto bg-white px-5">
		{#if thumbnail}
			<button
				class="-mx-5 {enlargedImage
					? 'max-h-full'
					: 'max-h-[25%]'} w-[calc(100%+2.5rem)] overflow-hidden"
				on:click={() => (enlargedImage = !enlargedImage)}
			>
				<img id="thumbnail" class="w-full" src={thumbnail} alt="Logo" />
			</button>
		{/if}
		{#if introActive}
			<Intro {stats} />
		{/if}

		<!-- Title -->
		<h1 class="mt-3 font-bold text-large">
			<a
				href="https://de.wikipedia.org/wiki/{encodeURIComponent(title.de.replaceAll(' ', '_'))}"
				target="_blank">{title.de}</a
			>
		</h1>
		<h2 class="mb-2.5 text-semilarge font-bold text-grey">
			<a
				href="https://en.wikipedia.org/wiki/{encodeURIComponent(title.en.replaceAll(' ', '_'))}"
				target="_blank">{title.en}</a
			>
		</h2>

		<!-- Description -->
		<p class="mb-8 text-grey">{description}</p>
		{#if !introActive}
			<div>
				<h2 class="font-bold text-semilarge">
					Episoden<span class=" ml-2.5 text-[80%] font-normal text-lightgrey"
						>({episodes.length})</span
					>
				</h2>
				<div class="mt-2 mb-8">
					<!-- Episodes -->
					<div>
						{#each episodes as episode}
							<a
								class="mb-2.5 flex h-fit items-center rounded-lg bg-[rgb(245,245,245)] bg-contain bg-no-repeat bg-blend-overlay"
								href={episode.link}
								target="_blank"
							>
								<div class="relative flex-shrink-0 w-24 h-24">
									<img
										class="object-cover w-full h-full rounded-l-lg"
										src={episode.cover}
										alt={episode.title}
									/>
									<span
										class="absolute w-full px-2 py-1 font-bold text-center text-white transform -translate-x-1/2 -translate-y-1/2 bg-black bg-opacity-50 left-1/2 top-1/2"
									>
										{episode.nr}
									</span>
								</div>
								<span class="flex-grow p-2.5 text-black hover:text-primary hover:underline">
									{episode.title}
								</span>
							</a>
						{/each}
					</div>
				</div>

				<!-- Connections -->
				<h2 class="mb-5 font-bold text-semilarge">
					Verbindungen<span class="ml-2.5 text-[80%] font-normal text-lightgrey"
						>({Array.from(new Set(connectionsTo.concat(connectionsFrom))).length})</span
					>
				</h2>
				{#each ['to', 'from'] as connectionType}
					<div>
						{#if { to: connectionsTo, from: connectionsFrom }[connectionType].length > 0}
							<h3 class="font-bold text-medium">
								...{connectionType == 'to' ? 'zu' : 'von'} anderen Themen:
							</h3>
						{/if}
						<div
							class="flex flex-row flex-wrap items-center content-between justify-start mt-2 mb-5"
						>
							{#each { to: connectionsTo, from: connectionsFrom }[connectionType] as connection}
								<button
									class="my-1 mr-2.5 w-fit cursor-pointer text-nowrap rounded-md bg-[rgb(245,245,245)] p-2 {activeConnection.name ==
										connection && activeConnection.type == connectionType
										? 'text-primary'
										: ''} text-black no-underline transition-all ease-in-out hover:text-primary"
									on:click={() => {
										connectionClicked(connection, connectionType);
									}}
									>{connection}
								</button>
							{/each}
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</section>

<!-- Context Info -->
<div
	class="absolute {infoActive
		? 'pointer-events-auto opacity-100'
		: 'pointer-events-none opacity-0'} bottom-0 left-0 h-fit w-1/5 cursor-default overflow-y-auto rounded-tr-2xl bg-white p-4 shadow-default transition-all ease-in-out"
>
	<h3 class="mb-2.5 text-semilarge font-bold">
		<button
			class="hover:text-primary hover:underline"
			on:click={() => themeLinkClicked(context.title[0])}>{context.title[0]}</button
		>
		&gt;
		<button
			class="hover:text-primary hover:underline"
			on:click={() => themeLinkClicked(context.title[1])}>{context.title[1]}</button
		>
	</h3>
	<p>{@html context.text}</p>
</div>

<style>
	:global(.highlighted) {
		background: yellow;
	}
</style>
