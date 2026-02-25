using System;

namespace P21Examples.Common
{
    /// <summary>
    /// P21 API configuration loaded from environment variables.
    /// Mirrors Python scripts/common/config.py.
    /// </summary>
    public class P21Config
    {
        public string BaseUrl { get; }
        public string Username { get; }
        public string Password { get; }
        public string? ConsumerKey { get; }
        public bool VerifySsl { get; }

        public string TokenUrl => $"{BaseUrl}/api/security/token";
        public string TokenUrlV2 => $"{BaseUrl}/api/security/token/v2";
        public string ODataUrl => $"{BaseUrl}/odataservice/odata";
        public string EntityUrl => $"{BaseUrl}/api/entity";

        public P21Config(
            string baseUrl,
            string username = "",
            string password = "",
            string? consumerKey = null,
            bool verifySsl = false)
        {
            BaseUrl = baseUrl.TrimEnd('/');
            Username = username;
            Password = password;
            ConsumerKey = consumerKey;
            VerifySsl = verifySsl;
        }

        /// <summary>
        /// Load configuration from environment variables.
        /// Looks for a .env file in the project root directory.
        /// </summary>
        public static P21Config FromEnvironment()
        {
            // Load .env file if present (simple key=value parsing)
            LoadDotEnv();

            var baseUrl = Environment.GetEnvironmentVariable("P21_BASE_URL");
            var username = Environment.GetEnvironmentVariable("P21_USERNAME") ?? "";
            var password = Environment.GetEnvironmentVariable("P21_PASSWORD") ?? "";
            var consumerKey = Environment.GetEnvironmentVariable("P21_CONSUMER_KEY");
            var verifySsl = string.Equals(
                Environment.GetEnvironmentVariable("P21_VERIFY_SSL"),
                "true",
                StringComparison.OrdinalIgnoreCase);

            if (string.IsNullOrEmpty(baseUrl))
                throw new InvalidOperationException("P21_BASE_URL environment variable is required");

            if (string.IsNullOrEmpty(consumerKey) && string.IsNullOrEmpty(username))
                throw new InvalidOperationException(
                    "P21_USERNAME (or P21_CONSUMER_KEY) environment variable is required");

            if (string.IsNullOrEmpty(consumerKey) && string.IsNullOrEmpty(password))
                throw new InvalidOperationException(
                    "P21_PASSWORD (or P21_CONSUMER_KEY) environment variable is required");

            return new P21Config(baseUrl, username, password, consumerKey, verifySsl);
        }

        private static void LoadDotEnv()
        {
            // Walk up from current directory to find .env
            var dir = AppContext.BaseDirectory;
            for (var i = 0; i < 6; i++)
            {
                var envFile = System.IO.Path.Combine(dir, ".env");
                if (System.IO.File.Exists(envFile))
                {
                    foreach (var line in System.IO.File.ReadAllLines(envFile))
                    {
                        var trimmed = line.Trim();
                        if (string.IsNullOrEmpty(trimmed) || trimmed.StartsWith("#"))
                            continue;

                        var eqIndex = trimmed.IndexOf('=');
                        if (eqIndex <= 0) continue;

                        var key = trimmed.Substring(0, eqIndex).Trim();
                        var value = trimmed.Substring(eqIndex + 1).Trim();

                        // Strip surrounding quotes
                        if (value.Length >= 2 &&
                            ((value.StartsWith("\"") && value.EndsWith("\"")) ||
                             (value.StartsWith("'") && value.EndsWith("'"))))
                        {
                            value = value.Substring(1, value.Length - 2);
                        }

                        if (string.IsNullOrEmpty(Environment.GetEnvironmentVariable(key)))
                            Environment.SetEnvironmentVariable(key, value);
                    }
                    return;
                }

                var parent = System.IO.Directory.GetParent(dir);
                if (parent == null) break;
                dir = parent.FullName;
            }
        }
    }
}
