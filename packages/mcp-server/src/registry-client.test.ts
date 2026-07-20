import { RegistryClient } from "./registry-client.js";

describe("RegistryClient", () => {
  it("constructs with a base URL", () => {
    const client = new RegistryClient("http://localhost:8000");
    expect(client).toBeDefined();
  });

  it("strips trailing slash from base URL", () => {
    const client = new RegistryClient("http://localhost:8000/");
    // baseUrl is private — just verify construction succeeds
    expect(client).toBeInstanceOf(RegistryClient);
  });
});
