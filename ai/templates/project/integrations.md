<!-- TEMPLATE: <project>/.ai/context/integrations.md — contracts between repos -->
<!-- Every row must cite the real contract path (OpenAPI, proto, DTO, event schema) -->

# Integrations

> Changing a contract in this table = cross-repo breaking change — `/spec` / `/change` must flag every consumer repo

| Provider | Consumer | Channel | Contract | Notes |
|---|---|---|---|---|
| `{repo}` | `{repo}` | {REST / gRPC / queue / DB / file} | `{repo}/{path}` | {auth, versioning} |

## Breaking-change Rules

- {e.g. adding fields is fine; removing/changing types requires versioning}
