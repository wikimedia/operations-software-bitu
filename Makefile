DEFAULT_GOAL := build

ci:
	npm ci
	npm audit fix

build: ci
	npm run build

dev: ci
	npm run dev

pre_release:
	git rm src/bitu/static/bundler/assets/*.css
	git rm src/bitu/static/bundler/assets/*.js

release: ci build
	git add src/bitu/static/bundler/assets/*.css
	git add src/bitu/static/bundler/assets/*.js
	git add src/bitu/static/bundler/manifest.json

