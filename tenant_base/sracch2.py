module issuerJwtBase


class JwtIssuerController():
    def sign_in(self):

        self._verify_credentials()
        self._generate_token_payload()
        return token

module consumerJwtBase

class AbstractJwtConsumer():
    def consume_token(self):
        self._consume_token()
        return true or Raise BadToken





module ShopinvaderJwt

    surcharge verify_credentials
    surcharge generat_etoken_payload

    @route
    def ...maRoute(auth=jwtToken)
