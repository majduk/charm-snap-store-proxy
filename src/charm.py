#!/usr/bin/env python3
# Copyright 2020 Ubuntu
# See LICENSE file for licensing details.

import logging

from ops.charm import CharmBase
from ops.main import main
from ops.framework import StoredState
from ops.model import ActiveStatus, BlockedStatus

import subprocess

logger = logging.getLogger(__name__)


class SnapStoreProxyCharm(CharmBase):
    _stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.install, self._on_install)
        self.framework.observe(self.on.update_status, self._on_update_status)
        self.framework.observe(self.on.db_relation_changed, self._on_db_relation_changed)
        self._stored.set_default(config={},
                                 db_connected=False,
                                 store_id=None
                                 )

    def _on_install(self, _):
        subprocess.check_output(["snap", "install", "snap-store-proxy"])
        subprocess.check_output(["apt", "install", "-y", "postgresql-client-10"])

    def _on_update_status(self, _):
        if not self._stored.db_connected:
            self.model.unit.status = BlockedStatus("Database not connected")
            return
        try:
            status = subprocess.check_output(["snap-proxy", "status"])
        except subprocess.CalledProcessError as e:
            status = e.output
        logger.info("Status: {}".format(status))
        srv_down = []
        for line in status.decode("utf-8").splitlines():
            if 'Store ID' in line:
                sid = line.split(":")[1].strip()
                if sid != 'not registered':
                    self._stored.store_id = sid
            if 'not running' in line:
                srv = line.split(":")[0].strip()
                srv_down.append(srv)
        if srv_down:
            s = "Services not running: " + ", ".join(srv_down)
            self.model.unit.status = BlockedStatus(s)
            return
        if not self._stored.store_id:
            self.model.unit.status = BlockedStatus("Not registered")
            return
        self.model.unit.status = ActiveStatus()

    def _on_db_relation_changed(self, event):
        data = event.relation.data[event.unit]
        if 'password' not in data:
            self.model.unit.status = BlockedStatus("Database relation not ready")
            return
        db_url = "postgresql://{user}:{password}@{host}:{port}/{database}".format(**data)
        subprocess.check_output(["psql", "-x", db_url, "-c", "CREATE EXTENSION \"btree_gist\""])
        subprocess.check_output(["snap-proxy", "config", "proxy.db.connection={}".format(db_url)])
        self._stored.db_connected = True

    def _on_config_changed(self, _):
        for key in self.model.config:
            if key not in self._stored.config or \
               self.model.config[key] != self._stored.config[key]:
                value = self.model.config[key]
                logger.info("Setting {} to: {}".format(key, value))
                handle = getattr(self, "_set_{}".format(key.replace("-", "_")))
                handle(value)
                self._stored.config[key] = value

    def _set_proxy_domain(self, domain):
        subprocess.check_output(["snap-proxy", "config", "proxy.domain={}".format(domain)])


if __name__ == "__main__":
    main(SnapStoreProxyCharm)
