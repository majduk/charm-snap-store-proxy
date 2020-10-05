# Copyright 2020 Ubuntu
# See LICENSE file for licensing details.

import unittest
from unittest.mock import (
    Mock,
    patch,
    call
)
from uuid import uuid4
import random

from ops.testing import Harness
from charm import SnapStoreProxyCharm


class TestCharm(unittest.TestCase):

    def default_config(self):
        return {
            'proxy-domain': uuid4(),
        }

    @patch('subprocess.check_output')
    def test_install(self, mock_subproc):
        process_mock = Mock()
        mock_subproc.return_value = process_mock
        harness = Harness(SnapStoreProxyCharm)
        harness.begin()
        action_event = Mock()
        harness.charm._on_install(action_event)
        self.assertTrue(mock_subproc.called)
        assert mock_subproc.call_args_list[0] == call(["snap", "install", "snap-store-proxy"])
        assert mock_subproc.call_args_list[1] == call(["apt", "install", "-y",
                                                       "postgresql-client-10"])

    def test_config_changed(self):
        harness = Harness(SnapStoreProxyCharm)
        self.addCleanup(harness.cleanup)
        harness.begin()
        harness.charm._set_proxy_domain = Mock()
        default_config = self.default_config()
        self.assertEqual(harness.charm._stored.config, {})
        harness.update_config(default_config)
        self.assertEqual(harness.charm._stored.config, default_config)
        self.assertTrue(harness.charm._set_proxy_domain.called)

    @patch('subprocess.check_output')
    def test_db_relation_changed(self, mock_subproc):
        harness = Harness(SnapStoreProxyCharm)
        self.addCleanup(harness.cleanup)
        harness.begin()
        app_name = str(uuid4())
        peer = "{}/{}".format(app_name, random.randint(0, 100))
        relation_id = harness.add_relation('db', 'pgsql')
        harness.add_relation_unit(relation_id, peer)
        relation_data = {
            'user': str(uuid4()),
            'password': str(uuid4()),
            'host': str(uuid4()),
            'port': str(uuid4()),
            'database': str(uuid4()),
        }
        db_url = "postgresql://{user}:{password}@{host}:{port}/{database}".format(**relation_data)
        harness.update_relation_data(relation_id, peer, relation_data)
        assert harness.get_relation_data(relation_id, peer) == relation_data
        assert mock_subproc.call_args_list[0] == call(['psql', '-x', db_url, '-c',
                                                       'CREATE EXTENSION "btree_gist"'])
        assert mock_subproc.call_args_list[1] == call(["snap-proxy", "config",
                                                       "proxy.db.connection={}".format(db_url)])
