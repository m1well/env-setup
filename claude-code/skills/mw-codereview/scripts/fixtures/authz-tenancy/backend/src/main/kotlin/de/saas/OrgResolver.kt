package de.saas

import org.springframework.security.oauth2.jwt.Jwt

class OrgResolver {
    fun tenant(jwt: Jwt): String = jwt.getClaimAsStringList("organization").first()
}
