import Keycloak from 'keycloak-js';

export class Session {
  private readonly keycloak = new Keycloak({ url: 'https://id.example.com', realm: 'shop', clientId: 'shop' });

  async token(): Promise<string | undefined> {
    try {
      await this.keycloak.updateToken(30);
    } catch (error) {
      if (!this.keycloak.token) {
        void this.keycloak.login();
      } else if (this.keycloak.isTokenExpired()) {
        throw error;
      }
    }
    return this.keycloak.token;
  }

  async guardedToken(): Promise<string | undefined> {
    try {
      await this.keycloak.updateToken(30);
    } catch (error) {
      if (!this.keycloak.refreshToken) {
        void this.keycloak.login();
        return undefined;
      }
      if (this.keycloak.isTokenExpired()) throw error;
    }
    return this.keycloak.token;
  }
}
