from typing import Union, List
import requests
import ujson

from visionapp.shared.singleton import Singleton
from visionapp.shared.stream_capture import StreamReader
from visionapp.client.api.codecs import StreamConfiguration, \
    Zone, Alert, Codec, ZoneStatus, EngineConfiguration
from visionapp.client.api.streaming import StreamManager


class API(metaclass=Singleton):
    # For testing purposes
    get = staticmethod(requests.get)
    put = staticmethod(requests.put)


    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self._base_url = self.hostname + ":" + str(self.port)

        self._stream_manager = StreamManager()

    # Stream Configuration Stuff
    def get_stream_configurations(self, only_get_active=False) \
            -> List[StreamConfiguration]:
        """Get all StreamConfigurations that currently exist.
        :param only_get_active: If True, It will get StreamConfigurations that
        are currently active, AKA being streamed
        :return: [StreamConfiguration, StreamConfiguration, ...]
        """
        req = "/api/streams/"
        data = self._get(req)
        configs = [StreamConfiguration.from_dict(d) for d in data]
        if only_get_active:
            configs = [c for c in configs if c.is_active]
        return configs

    def set_stream_configuration(self, stream_configuration) \
            -> StreamConfiguration:
        """Update an existing stream configuration or create a new one
        If creating a new one, the stream_configuration.id will be None
        :param stream_configuration: StreamConfiguration
        :return: StreamConfiguration, initialized with an ID
        """
        req = "/api/streams/"
        data = self._put_codec(req, stream_configuration)
        config = StreamConfiguration.from_dict(data)
        return config

    def delete_stream_configuration(self, stream_id):
        """Deletes a stream configuration with the given ID

        :param stream_id: The ID of the stream to delete
        """
        # TODO: Implement this in April

    # Setting server analysis tasks
    def start_analyzing(self, stream_id) -> bool:
        """
        Tell the server to set this stream config to active, and start analysis
        :param stream_id:
        :return: True or False if the server was able to start analysis on that
        stream. It could fail because: unable to start stream, or license
        restrictions.
        """
        req = "/api/streams/{stream_id}/analyze".format(
            stream_id=stream_id)
        resp = self._put_json(req, 'true')
        return resp

    def stop_analyzing(self, stream_id):
        """Tell the server to stop analyzing a particular stream
        :param stream_id:
        :return:
        """
        req = "/api/streams/{stream_id}/analyze".format(
            stream_id=stream_id)
        self._put_json(req, 'false')

    # Stream Specific stuff
    def get_stream(self, stream_id) -> Union[None, StreamReader]:
        """Get the StreamReader for the given stream_id.
        :param stream_id: The ID of the stream configuration to open.
        :return: A StreamReader object OR None, if the server was unable to
        open a stream
        """
        req = "/api/streams/{stream_id}/url".format(stream_id=stream_id)
        url = self._get(req)
        if url is None:
            return None
        return self._stream_manager.get_stream(url)

    # Get Analysis
    def get_latest_zone_statuses(self) -> List[ZoneStatus]:
        """Get all ZoneStatuses

        :return:
        {“stream_id1”: [ZoneStatus, ZoneStatus], “stream_id2”: [ZoneStatus]}
        """

    # Alerts
    def get_unverified_alerts(self, stream_id) -> List[Alert]:
        """Gets all alerts that have not been verified or rejected

        :param stream_id:
        :return:
        """
        req = "/api/alerts/unverified".format(
            stream_id=stream_id)
        data = self._get(req, params={"stream_id": str(stream_id)})
        alerts = [Alert.from_dict(a) for a in data]
        return alerts

    def set_alert_verification(self, alert_id, verified_as: bool):
        """Sets an alert verified as True or False
        :param stream_id: The stream that the alert is part of
        :param alert_id: The
        :param verified_as: Set verification to True or False
        :return: The modified Alert
        """
        req = "/api/alerts/{alert_id}".format(alert_id=alert_id)
        resp = self._put_json(req, ujson.dumps(verified_as))

    # Backend Capabilities
    def get_engine_configuration(self) -> EngineConfiguration:
        """Returns the capabilities of the machine learning engine on the server.
        Currently, it can tell you:
            The types of objects that can be detected
            The types of attributes that can be detected for each object.

        :return: EngineConfiguration
        """

    # Zone specific stuff
    def get_zones(self, stream_id) -> List[Zone]:
        """Returns a list of Zone's associated with that stream"""
        req = "/api/streams/{stream_id}/zones".format(stream_id=str(stream_id))
        data = self._get(req)
        zones = [Zone.from_dict(j) for j in data]
        return zones

    def get_zone(self, stream_id, zone_id) -> Zone:
        """Get a specific zone"""
        data = self.get_zones(stream_id)
        zones = [zone for zone in data if zone.id == zone_id]
        assert len(zones) != 0, ("A zone with that stream_id and zone_id could"
                                 " not be found!")
        return zones[0]

    def set_zone(self, stream_id, zone):
        """Update or create a zone. If the Zone doesn't exist, the zone.id
        must be None. An initialized Zone with an ID will be returned.
        :param stream_id: The stream_id that this zone exists in
        :param zone: A Zone object
        :return: Zone, initialized with an ID
        """
        req = "/api/streams/{stream_id}/zones".format(stream_id=stream_id)
        data = self._put_codec(req, zone)
        new_zone = Zone.from_dict(data)
        return new_zone

    def close(self):
        """Clean up the API. It may no longer be used after this call."""
        self._stream_manager.close()

    def _get(self, api_url, params=None):
        """
        :param api_url: The /api/blah/blah to append to the base_url
        :param params: The "query_string" to add to the url. In the format
        of a dict, {"key": "value", ...} key and val must be a string
        :return:
        """
        response = self.get(self._full_url(api_url), params=params)
        return ujson.loads(response.content)

    def _put_codec(self, api_url, codec: Codec):
        data = codec.to_json()
        resp = self.put(self._full_url(api_url), data=data)
        return ujson.loads(resp.content)

    def _put_json(self, api_url, json):
        resp = self.put(self._full_url(api_url), data=json)
        if resp.content:
            return ujson.loads(resp.content)

    def _full_url(self, api_url):
        url = "{base_url}{api_url}".format(
            base_url=self._base_url,
            api_url=api_url)
        return url
