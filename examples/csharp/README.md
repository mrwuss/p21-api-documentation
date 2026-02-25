# P21 API C# Examples

C# console application examples demonstrating all P21 APIs using raw `HttpClient`.

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
```

## Project Structure

```
P21Examples.sln
Common/                     # Shared library (netstandard2.0)
  P21Config.cs              # Environment variable loading
  P21Auth.cs                # Token V1/V2, XML/JSON dual parsing
  P21Client.cs              # HttpClient wrapper for all 4 APIs
  Models/
    InteractiveResult.cs    # Interactive API response model
    TransactionResult.cs    # Transaction API response model
OData/                      # OData API examples (net8.0)
Transaction/                # Transaction API examples (net8.0)
Interactive/                # Interactive API examples (net8.0)
Entity/                     # Entity API examples (net8.0)
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
