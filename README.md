# snap-store-proxy

## Description

The Snap Store Proxy provides an on-premise edge proxy to the general Snap Store for your devices. Devices are registered with the proxy, and all communication with the Store will flow through the proxy.

**Note:** In order to serve its client devices, a Snap Store Proxy needs to be online and connected to the general Snap Store. This is a requirement, even though Snap Store Proxy caches downloaded snap files, which substantially reduces internet traffic. There's currently no generally available offline mode for the Snap Store Proxy itself. See Network Connectivity for the snap-proxy check-connections command and the up-to-date Network requirements for Snappy post for a list of domains Snap Store Proxy needs access to.

## Usage

This charm can be deployed using juju:
```
    juju deploy snap-store-proxy snap-store-proxy
    juju add-relation postgresql:db-admin snap-store-proxy:db
```
Note that Snap Store Proxy requires administrative privileges on the database. 

After the installation completes, proxy needs to be [registered](https://docs.ubuntu.com/snap-store-proxy/en/register):
```
juju ssh snap-store-proxy/0
sudo snap-proxy generate-keys
sudo snap-proxy register
```

More details can be found in Snap Store Proxy installation [documentation](https://docs.ubuntu.com/snap-store-proxy/en/install).

## Developing

Create and activate a virtualenv,
and install the development requirements,

    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements-dev.txt

## Testing

Just run `run_tests`:

    ./run_tests
