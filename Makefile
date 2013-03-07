DATA_DIR?=out/chromium-data-dir
CHROME_PATH?=/usr/local/google/home/binji/dev/chromium/src/out/Release/chrome
NEXE_ARGS+=--load-extension=${CURDIR}/out/package --user-data-dir=${DATA_DIR}

all: build.ninja
	@ninja package

build.ninja: build/make_ninja.py
	@python build/make_ninja.py

clean:
	@rm -rf out build.ninja

runclean: all
	@rm -rf ${DATA_DIR}
	@${CHROME_PATH} ${NEXE_ARGS}

run: all
	@${CHROME_PATH} ${NEXE_ARGS}

test: build.ninja
	@ninja out/gapi_test_host
	@cd src/test/data && ../../../out/gapi_test_host

debug_test: build.ninja
	@ninja out/gapi_test_host
	@cd src/test/data && gdb ../../../out/gapi_test_host

.PHONY: all clean runclean run test debug_test
