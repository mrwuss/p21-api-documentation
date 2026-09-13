# P21 API C# Examples

C# console application examples demonstrating all P21 APIs using raw `HttpClient`, plus end-to-end recipe programs mirroring the [recipes cookbook](../../docs/recipes/README.md).

## Prerequisites

- [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0)
- P21 API credentials (set in `.env` file at project root)

## Setup

```bash
# From the repository root
cp .env.example .env
# Edit .env with your P21 credentials

# Build all examples
cd examples/csharp
dotnet build
```

## Running Examples

```bash
# Run a specific example (from examples/csharp/)
dotnet run --project OData
dotnet run --project Transaction
dotnet run --project Interactive
dotnet run --project Entity
dotnet run --project Production
dotnet run --project Recipes      # end-to-end tasks; writes gated behind typing EXECUTE
dotnet run --project Rest         # other REST families (docs/15); task create gated behind typing EXECUTE
```

## Project Structure

```
P21Examples.sln
Common/                     # Shared library (net8.0)
  P21Config.cs              # Environment variable loading
  P21Auth.cs                # Token auth (V2 for credentials; V1 only for consumer keys), XML/JSON dual parsing
  P21Client.cs              # HttpClient wrapper for all 4 APIs
  Models/
    InteractiveResult.cs    # Interactive API response model
    TransactionResult.cs    # Transaction API response model
OData/                      # OData API examples (net8.0)
Transaction/                # Transaction API examples (net8.0)
Interactive/                # Interactive API examples (net8.0)
Entity/                     # Entity API examples (net8.0)
Production/                 # Production & Labor examples (net8.0)
Rest/                       # Other REST families (net8.0) -- docs/15-Other-REST-Families.md
                            #   (menu-driven; task create gated behind typing EXECUTE)
Recipes/                    # End-to-end recipe programs (net8.0), one class per docs/recipes page
                            #   (menu-driven; writes gated behind typing EXECUTE)
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `P21_BASE_URL` | Yes | P21 server URL (e.g., `https://play.p21server.com`) |
| `P21_USERNAME` | Yes* | P21 API username |
| `P21_PASSWORD` | Yes* | P21 API password |
| `P21_CONSUMER_KEY` | No | Consumer key (used only if username/password are not set) |
| `P21_VERIFY_SSL` | No | Set to `true` to verify SSL certificates |

*Required unless using `P21_CONSUMER_KEY`.

> **If both are set, username/password wins.** `P21Auth.GetTokenV2Async` prefers `P21_USERNAME`/`P21_PASSWORD` and only falls back to `P21_CONSUMER_KEY` when they are empty — matching `examples/python/common/auth.py`'s `get_token()`, which never uses `config.consumer_key` unless a caller explicitly passes it. This was a real bug until 2026-09: it used to prefer the consumer key whenever one was present at all, so **every example in this solution** silently authenticated with whatever key happened to be in `.env` the moment one was added, with no error and no indication anything had changed. A key scoped to a restricted table list (its JWT `aud` claim names specific tables) made REST-family calls (`/api/{family}/...`) keep working while OData calls (`/odataservice/odata/table/...`) against any table outside that list failed with a generic `401 "You are not authorized to access API."` — which reads exactly like a permissions problem and is not one. If you see that error from a C# example that otherwise looks right, decode the bearer token's `aud` claim before assuming your P21 user lacks OData permission.
