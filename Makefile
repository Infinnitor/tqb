env:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt


runner:
	mkdir -p build/cache/
	gcc runner.c -o build/runner;\
	cp runner.c build/cache/
	# ./build/runner ls --where Priority=High

tests:
	pytest -v --no-header test/


release:
	# rm -rf build/*
	mkdir -p build
	gcc runner.c -o build/tqb
	cp src/ build/ -r
	python3 -m venv build/venv
	./build/venv/bin/pip install -r requirements.txt --quiet


clean:
	rm -rf build/*


install:
	make release
	sudo cp build /opt/tqb -r
	sudo ln -s /opt/tqb/tqb /usr/bin/tqb

uninstall:
	sudo rm -rf /opt/tqb/
	sudo rm /usr/bin/tqb
