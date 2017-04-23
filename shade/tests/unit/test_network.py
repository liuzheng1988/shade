# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock
import testtools

import shade
from shade.tests.unit import base


class TestNetwork(base.RequestsMockTestCase):

    def test_list_networks(self):
        net1 = {'id': '1', 'name': 'net1'}
        net2 = {'id': '2', 'name': 'net2'}
        self.register_uris([
            dict(method='GET',
                 uri=self.get_mock_url(
                     'network', 'public', append=['v2.0', 'networks.json']),
                 json={'networks': [net1, net2]})
        ])
        nets = self.cloud.list_networks()
        self.assertEqual([net1, net2], nets)
        self.assert_calls()

    def test_list_networks_filtered(self):
        self.register_uris([
            dict(method='GET',
                 uri=self.get_mock_url(
                     'network', 'public', append=['v2.0', 'networks.json'],
                     qs_elements=["name=test"]),
                 json={'networks': []})
        ])
        self.cloud.list_networks(filters={'name': 'test'})
        self.assert_calls()

    @mock.patch.object(shade.OpenStackCloud, 'neutron_client')
    def test_create_network(self, mock_neutron):
        self.cloud.create_network("netname")
        mock_neutron.create_network.assert_called_with(
            body=dict(
                network=dict(
                    name='netname',
                    admin_state_up=True
                )
            )
        )

    @mock.patch.object(shade.OpenStackCloud, 'neutron_client')
    def test_create_network_specific_tenant(self, mock_neutron):
        self.cloud.create_network("netname", project_id="project_id_value")
        mock_neutron.create_network.assert_called_with(
            body=dict(
                network=dict(
                    name='netname',
                    admin_state_up=True,
                    tenant_id="project_id_value",
                )
            )
        )

    @mock.patch.object(shade.OpenStackCloud, 'neutron_client')
    def test_create_network_external(self, mock_neutron):
        self.cloud.create_network("netname", external=True)
        mock_neutron.create_network.assert_called_with(
            body=dict(
                network={
                    'name': 'netname',
                    'admin_state_up': True,
                    'router:external': True
                }
            )
        )

    @mock.patch.object(shade.OpenStackCloud, 'neutron_client')
    def test_create_network_provider(self, mock_neutron):
        provider_opts = {'physical_network': 'mynet',
                         'network_type': 'vlan',
                         'segmentation_id': 'vlan1'}
        self.cloud.create_network("netname", provider=provider_opts)
        mock_neutron.create_network.assert_called_once_with(
            body=dict(
                network={
                    'name': 'netname',
                    'admin_state_up': True,
                    'provider:physical_network':
                        provider_opts['physical_network'],
                    'provider:network_type':
                        provider_opts['network_type'],
                    'provider:segmentation_id':
                        provider_opts['segmentation_id'],
                }
            )
        )

    @mock.patch.object(shade.OpenStackCloud, 'neutron_client')
    def test_create_network_provider_ignored_value(self, mock_neutron):
        provider_opts = {'physical_network': 'mynet',
                         'network_type': 'vlan',
                         'segmentation_id': 'vlan1',
                         'should_not_be_passed': 1}
        self.cloud.create_network("netname", provider=provider_opts)
        mock_neutron.create_network.assert_called_once_with(
            body=dict(
                network={
                    'name': 'netname',
                    'admin_state_up': True,
                    'provider:physical_network':
                        provider_opts['physical_network'],
                    'provider:network_type':
                        provider_opts['network_type'],
                    'provider:segmentation_id':
                        provider_opts['segmentation_id'],
                }
            )
        )

    def test_create_network_provider_wrong_type(self):
        provider_opts = "invalid"
        with testtools.ExpectedException(
            shade.OpenStackCloudException,
            "Parameter 'provider' must be a dict"
        ):
            self.cloud.create_network("netname", provider=provider_opts)

    def test_delete_network(self):
        network_id = "test-net-id"
        network_name = "network"
        network = {'id': network_id, 'name': network_name}
        self.register_uris([
            dict(method='GET',
                 uri=self.get_mock_url(
                     'network', 'public', append=['v2.0', 'networks.json']),
                 json={'networks': [network]}),
            dict(method='DELETE',
                 uri=self.get_mock_url(
                     'network', 'public',
                     append=['v2.0', 'networks', "%s.json" % network_id]),
                 json={})
        ])
        self.assertTrue(self.cloud.delete_network(network_name))
        self.assert_calls()

    def test_delete_network_not_found(self):
        self.register_uris([
            dict(method='GET',
                 uri=self.get_mock_url(
                     'network', 'public', append=['v2.0', 'networks.json']),
                 json={'networks': []}),
        ])
        self.assertFalse(self.cloud.delete_network('test-net'))
        self.assert_calls()

    def test_delete_network_exception(self):
        network_id = "test-net-id"
        network_name = "network"
        network = {'id': network_id, 'name': network_name}
        self.register_uris([
            dict(method='GET',
                 uri=self.get_mock_url(
                     'network', 'public', append=['v2.0', 'networks.json']),
                 json={'networks': [network]}),
            dict(method='DELETE',
                 uri=self.get_mock_url(
                     'network', 'public',
                     append=['v2.0', 'networks', "%s.json" % network_id]),
                 status_code=503)
        ])
        self.assertRaises(shade.OpenStackCloudException,
                          self.cloud.delete_network, network_name)
        self.assert_calls()
