<script>
	import { createEventDispatcher } from 'svelte';

	export let to_exclude = '';
	export let hidden = false;

	const dispatcher = createEventDispatcher();

	function hide(e) {
		dispatcher('start', {
			size: { yes: 'small', no: 'full' }[e.target.id]
		});
		hidden = true;
	}
</script>

<div
	id="exclude-container"
	class="absolute {hidden
		? 'pointer-events-none opacity-0'
		: ''} left-0 top-0 z-50 m-0 h-full w-full bg-white bg-cover bg-no-repeat p-0 text-center text-lg text-gray-500 transition-all duration-200 ease-in-out"
	style="background-image: url('/assets/preview_blurred.png');"
>
	<div id="exclude-flex" class="flex h-full w-full items-center justify-center">
		<section
			id="exclude-box"
			class="w-[40%] rounded-3xl border-2 border-light bg-white p-14 text-semilarge"
		>
			<h3 class="mb-5 font-bold">
				Möchtest du folgende Themen mit jeweils mehr als 80 Verbindungen ausblenden?
			</h3>
			<p class="mb-5">
				Dies kann die Anzeige erheblich beschleunigen und wird für ältere Computer dringend
				empfohlen.
			</p>
			<p class="italic">{to_exclude}</p>
			<div class="mx-auto mb-0 mt-12 w-[95%] leading-normal">
				<button
					id="no"
					on:click={hide}
					class="inline-block w-[15%] cursor-pointer rounded-l-md rounded-r-none bg-primary p-2 text-white"
				>
					nein
				</button>
				<button
					id="yes"
					on:click={hide}
					class="inline-block w-[15%] cursor-pointer rounded-l-none rounded-r-md bg-lime-500 p-2 text-black"
				>
					ja
				</button>
			</div>
		</section>
	</div>
</div>

<style>
	button {
		transition: width 0.2s ease-in-out;
	}

	button:hover {
		width: 20%;
	}
</style>
