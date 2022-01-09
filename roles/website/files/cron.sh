#!/bin/bash
cat /srv/yanic/pub/nodes.json | jq '[.nodes[].statistics.clients] | add' > /tmp/clientcount
nodecount=$(cat /srv/yanic/pub/nodes.json | jq '.nodes | map(select(.flags.online)) | length')
echo "$nodecount" > /tmp/nodecount
sed -e "s/%nodecount%/${nodecount}/" -e "s/%lastchange%/$(date -Iseconds)/" /var/www/website-extras/api.json.template > /tmp/api.json
mkdir -p /var/www/website-extras/pub
mv /tmp/clientcount /tmp/nodecount /tmp/api.json /var/www/website-extras/pub/
