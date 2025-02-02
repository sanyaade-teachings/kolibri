import json

from morango.api.serializers import CertificateSerializer
from morango.constants.api_urls import NONCE
from morango.models import Certificate

from kolibri.core.auth.constants.morango_sync import ScopeDefinitions
from kolibri.core.discovery.utils.network.client import NetworkClient
from kolibri.utils import conf


def registerfacility(token, facility):

    # request the server for a one-time-use nonce
    PORTAL_URL = conf.OPTIONS["Urls"]["DATA_PORTAL_SYNCING_BASE_URL"]
    client = NetworkClient(PORTAL_URL)
    response = client.post(NONCE)
    server_nonce = response.json()["id"]

    # get owned certificate for this facility
    client_cert = (
        facility.dataset.get_owned_certificates()
        .filter(scope_definition_id=ScopeDefinitions.FULL_FACILITY)
        .first()
    )

    if client_cert is None:
        raise Certificate.DoesNotExist

    # build up data for request
    data = {
        "facility_id": facility.id,
        "server_nonce": server_nonce,
        "client_certificate_id": client_cert.id,
        "certificate_chain": json.dumps(
            CertificateSerializer(
                client_cert.get_ancestors(include_self=True), many=True
            ).data
        ),
        "token": token,
    }

    # sign the server nonce to attach to the request
    message = "{server_nonce}".format(**data)
    data["signature"] = client_cert.sign(message)

    # attempt to claim the facility
    response = client.post("portal/api/public/v1/registerfacility/", data=data)
    return response
