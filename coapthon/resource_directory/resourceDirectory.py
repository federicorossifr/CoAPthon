from coap import CoAP
from registration import Registration
from lookup import Lookup
from lookupRes import LookupRes
from lookupEp import LookupEp
from subprocess import Popen
from coapthon.defines import MONGO_CONFIG_FILE

__author__ = 'Carmelo Aparo'


class ResourceDirectory(CoAP):
    """
    Implementation of the resource directory server.
    """
    def __init__(self, host, port):
        """
        Initializes a resource directory and creates registration, lookup resources.
        :param host: the host where the resource directory is.
        :param port: the port where the resource directory listens.
        """
        CoAP.__init__(self, (host, port))
        self.add_resource('rd/', Registration())
        self.add_resource('rd-lookup/', Lookup())
        self.add_resource('rd-lookup/res', LookupRes())
        self.add_resource('rd-lookup/ep', LookupEp())
        self.mongodb = Popen(['mongod', '--config', MONGO_CONFIG_FILE, '--auth'])

    def __del__(self):
        self.mongodb.terminate()
