from coapthon.messages.response import Response
from coapthon import defines

__author__ = 'Giacomo Tanganelli'


class RequestLayer(object):
    """
    Class to handle the Request/Response layer
    """
    def __init__(self, server):
        self._server = server

    def receive_request(self, transaction):
        """
        Handle request and execute the requested method

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction with the response to the request
        """
        method = transaction.request.code
        if method == defines.Codes.GET.number:
            transaction = self._handle_get(transaction)
        elif method == defines.Codes.POST.number:
            transaction = self._handle_post(transaction)
        elif method == defines.Codes.PUT.number:
            transaction = self._handle_put(transaction)
        elif method == defines.Codes.DELETE.number:
            transaction = self._handle_delete(transaction)
        else:
            transaction.response = None
        return transaction

    def send_request(self, request):
        """
         Dummy function. Used to do not broke the layered architecture.

        :type request: Request
        :param request: the request
        :return: the request unmodified
        """
        return request

    def _handle_get(self, transaction):
        """
        Handle GET requests

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction with the response to the request
        """
        path = str("/" + transaction.request.uri_path)
        transaction.response = Response()
        transaction.response.destination = transaction.request.source
        transaction.response.token = transaction.request.token
        if path == defines.DISCOVERY_URL:
            transaction = self._server.resourceLayer.discover(transaction)
        else:
            try:
                resource = self._server.root[path]
            except KeyError:
                resource = None
            if resource is None or path == '/':
                # Not Found
                transaction.response.code = defines.Codes.NOT_FOUND.number
            else:
                transaction.resource = resource
                transaction = self._server.resourceLayer.get_resource(transaction)
        return transaction

    def _handle_put(self, transaction):
        """
        Handle PUT requests

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction with the response to the request
        """
        path = str("/" + transaction.request.uri_path)
        transaction.response = Response()
        transaction.response.destination = transaction.request.source
        transaction.response.token = transaction.request.token
        try:
            resource = self._server.root[path]
        except KeyError:
            resource = None
        if resource is None and not path.startswith("/ps"):
            transaction.response.code = defines.Codes.NOT_FOUND.number
        elif resource is None and path.startswith("/ps"):
            #transaction = self._server.resourceLayer.create_resource(path, transaction)
            path_el = path.split("/");
            create_item = path_el[-1]
            del path_el[-1];
            new_path = '/'.join(path_el);
            parent_resource = self._server.root[new_path]
            print("[BROKER] Creating topic "+path+" on PUT request")
            payload = "<"+create_item+">;ct=0;";
            resource = parent_resource.createResFromPayload(payload,new_path)
            parent_resource.children.append(resource)
            parent_resource.cs.add_resource(resource.name,resource)
            print("[BROKER] Created")
            transaction.response.code = defines.Codes.CREATED.number
            transaction.resource = resource
            transaction = self._server.resourceLayer.update_resource(transaction)
        else:
            transaction.resource = resource
            # Update request
            transaction = self._server.resourceLayer.update_resource(transaction)
        return transaction

    def _handle_post(self, transaction):
        """
        Handle POST requests

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction with the response to the request
        """
        path = str("/" + transaction.request.uri_path)
        transaction.response = Response()
        transaction.response.destination = transaction.request.source
        transaction.response.token = transaction.request.token

        # Create request
        transaction = self._server.resourceLayer.create_resource(path, transaction)
        return transaction

    def _handle_delete(self, transaction):
        """
        Handle DELETE requests

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction with the response to the request
        """
        path = str("/" + transaction.request.uri_path)
        transaction.response = Response()
        transaction.response.destination = transaction.request.source
        transaction.response.token = transaction.request.token
        try:
            resource = self._server.root[path]
        except KeyError:
            resource = None
        print("Notifying resource:",resource,"\n")
        observers = self._server._observeLayer.notify(resource)
        print("Observers",observers)
        for transaction_ in observers:
            with transaction_:
                transaction_.response.code = defines.Codes.NOT_FOUND.number
                transaction_.response.observe = transaction_.resource.observe_count+1
                transaction_.response.type = defines.Types["NON"]
                if transaction_.response is not None:
                    self._server.send_datagram(transaction_.response)
        if resource is None:
            transaction.response.code = defines.Codes.NOT_FOUND.number
        else:
            # Delete
            transaction.resource = resource
            transaction = self._server.resourceLayer.delete_resource(transaction, path)
        return transaction

