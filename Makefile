install : requirements.txt
	test -d env || virtualenv -p python3 env; \
	. env/bin/activate; \
	pip install -r requirements.txt; \
	pip install git+https://github.com/htwangtw/tftb.git@spwv_fix
