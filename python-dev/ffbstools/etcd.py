import json
from aioetcd3.client import ssl_client


config = json.load(open('/etc/etcd-client.json'))

# Using multiple endpoints for load-balancing and fail-over seems to be
# currently unsupported, so we just use config['ENDPOINT'] instead of
# config['ENDPOINTS'].

etcd_client = ssl_client(
        endpoint='ipv4:///{}'.format(config['ENDPOINT']),
        ca_file=config['CACERT'],
        cert_file=config['CERT'],
        key_file=config['KEY'],
)
