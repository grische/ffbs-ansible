#!/bin/sh
SIGN_PUB_KEY=/vagrant/files/node-config-pub.key
CONFIG_SERVER=concentrator1
DEFAULT_SLEEP=20

tmpdir=/tmp/ff-Ohb0ba0u/
mkdir -p $tmpdir

pubkey=$(cat /etc/ffbs/wg-pubkey | sed 's/+/%2B/g')

while true; do
		rm -f "${tmpdir}config.json" "${tmpdir}config.json.sig"
		nonce=$(head /dev/urandom | tr -dc "0123456789abcdefghijklmnopqrstuvwxyz" | head -c20)
		wget http://${CONFIG_SERVER}/config?pubkey=${pubkey}\&nonce=${nonce} -O "${tmpdir}config.json" -q
		wget http://${CONFIG_SERVER}/config.sig?pubkey=${pubkey}\&nonce=${nonce} -O "${tmpdir}config.json.sig" -q
		usign -V -m "${tmpdir}config.json" -p $SIGN_PUB_KEY -q
		if [ "$?" == 0 ]; then
			outp=$(lua /usr/share/lua/nodeconfig.lua "${tmpdir}config.json" $nonce)
			if [ "$?" == 0 ]; then
				echo "$outp"
			    slp=$(echo "$outp" | tail -n1)
			    sleep $slp
			else
				echo "$outp"
			    sleep $DEFAULT_SLEEP
			fi
		else
			sleep $DEFAULT_SLEEP
		fi
done
