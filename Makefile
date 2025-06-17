runner:
	mkdir -p build/cache/
	@if [ "$(shell diff -q runner.c build/cache/runner.c)" != "" ]; then\
		echo "gcc runner.c -o build.runner";\
		gcc runner.c -o build/runner;\
	fi
	cp runner.c build/cache/
	# ./build/runner ls --where Priority=High

tests:
	pytest -v --no-header test/


release:
	mkdir -p build
	gcc runner.c -o build/runner
	cp src/ build/ -r
	cp logo-clr.txt
	python3 -m venv build/venv
	./build/venv/bin/pip install -r requirements.txt
