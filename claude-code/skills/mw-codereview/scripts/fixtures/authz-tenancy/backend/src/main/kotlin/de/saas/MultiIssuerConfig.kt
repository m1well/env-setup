package de.saas

import com.nimbusds.jwt.JWTParser
import org.springframework.security.authentication.AuthenticationManagerResolver
import org.springframework.security.oauth2.jwt.JwtDecoders
import org.springframework.security.oauth2.server.resource.authentication.JwtIssuerAuthenticationManagerResolver
import jakarta.servlet.http.HttpServletRequest

class MultiIssuerConfig {
    fun resolver(): AuthenticationManagerResolver<HttpServletRequest> =
        JwtIssuerAuthenticationManagerResolver.fromTrustedIssuers { true }

    fun decoderFor(token: String) = JwtDecoders.fromIssuerLocation<org.springframework.security.oauth2.jwt.JwtDecoder>(
        JWTParser.parse(token).jwtClaimsSet.issuer)
}
