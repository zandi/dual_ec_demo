#!/usr/bin/bash
# this attempts to automate testing the challenges.
# this requires the server.py and attack.py files,
# as well as the prng_{1,2,3,4}.py and attack_{1,2,3,4}.py
# files

if ! pgrep -f 'python server.py'; then
	echo "starting server"
	python server.py &
else
	echo "it appears the server is already started"
fi

# BUG: if server.py crashes out immediately, the following will fail.
# pay attention!
if test $(python attack.py | grep 'key:' | wc -l) == 4; then
	echo "success!"
else
	echo "something appears to be wrong..."
	echo "Please try running manually, getting full output to debug:"
	echo "    python server.py &; python attack.py"
	echo "piping both stdout and stderr to a file with '&>' may be handy"
fi

# hardcoded kill based on our invocation above.
pkill -f 'python server.py'
