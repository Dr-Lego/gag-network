/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			fontFamily: {
				sans: ['Poppins', 'Arial', 'Helvetica', 'sans-serif']
			},
			boxShadow: {
				default: '0 0 15px -5px rgba(128, 128, 128, 1)'
			},
			colors: {
				primary: '#d34823',
				light: '#f0f0f0',
				grey: 'grey',
				lightgrey: 'lightgrey'
			},
			fontSize: {
				default: '11pt',
				larger: 'larger',
				semilarge: 'large',
				large: 'xx-large'
			}
		}
	},
	plugins: []
};
