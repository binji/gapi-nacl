DATA_DIR?=out/chromium-data-dir
CHROME_PATH?=/usr/local/google/home/binji/dev/chromium/src/out/Release/chrome
NEXE_ARGS+=--load-extension=${CURDIR}/out/package --user-data-dir=${DATA_DIR}

all: build.ninja
	@ninja

build.ninja: build/ninja-wrap/ninja_wrap.py build/build.nw
	@python build/ninja-wrap/ninja_wrap.py build/build.nw -o build.ninja -D nacl_sdk_root=nacl_sdk/pepper_canary

clean:
	@rm -rf out build.ninja

runclean: all
	@rm -rf ${DATA_DIR}
	@${CHROME_PATH} ${NEXE_ARGS}

run: all
	@${CHROME_PATH} ${NEXE_ARGS}

test: build.ninja
	@ninja out/gapi_test_host_release
	@cd src/test/data && ../../../out/gapi_test_host_release

debug_test: build.ninja
	@ninja out/gapi_test_host_debug
	@cd src/test/data && gdb ../../../out/gapi_test_host_debug

.PHONY: all clean runclean run test debug_test
