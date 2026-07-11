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
Recipes/                    # End-to-end recipe programs (net8.0), one class per docs/recipes page
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `P21_BASE_URL` | Yes | P21 server URL (e.g., `https://play.p21server.com`) |
| `P21_USERNAME` | Yes* | P21 API username |
| `P21_PASSWORD` | Yes* | P21 API password |
| `P21_CONSUMER_KEY` | No | Consumer key (alternative to username/password) |
| `P21_VERIFY_SSL` | No | Set to `true` to verify SSL certificates |

*Required unless using `P21_CONSUMER_KEY`.
