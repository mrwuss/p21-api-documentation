// Other REST Families - User-Defined Field Inventory
// Docs: docs/15-Other-REST-Families.md#extensibilityuserdefinedfields
// Mirrors: examples/python/rest/udf_inventory.py
//
// Enumerates every user-defined field, grouped by the *_ud table it
// extends, separating real UDFs from the table's own key plumbing.
//
// The convention (verified live, 26.1.5950.0):
//   - ColumnOrder 1 is always the *_ud table's surrogate key.
//   - The NOT NULL columns after it are the join key back to the base
//     table (composite on some tables, e.g. ship_to_ud).
//   - The nullable columns are the real user-defined fields.
//   - One exception: customer_ud.autoorder_flag is NOT NULL and is a
//     genuine UDF (it has a default) -- a strong convention, not a
//     guarantee. Read the names.

using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class UdfInventory
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - User-Defined Field Inventory");
        Console.WriteLine(new string('=', 60));

        var (http, baseUrl) = await RestHelpers.CreateRawClientAsync();
        using var _ = http;
        Console.WriteLine($"Server: {baseUrl}");

        var response = await http.GetAsync($"{baseUrl}/api/extensibility/userdefinedfields/tables");
        response.EnsureSuccessStatusCode();
        var tables = JObject.Parse(await response.Content.ReadAsStringAsync())["list"] as JArray
                     ?? new JArray();

        int totalReal = 0;
        foreach (var table in tables)
        {
            var fields = (table["UserDefinedFields"]?["list"] as JArray ?? new JArray())
                .OrderBy(f => (int)f["ColumnOrder"]!)
                .ToList();

            var udfs = RealUdfs(fields);
            totalReal += udfs.Count;

            Console.WriteLine($"\n{table["TableName"]}  (extends {table["BaseTableName"]})");
            Console.WriteLine(new string('-', 50));
            if (udfs.Count == 0)
            {
                Console.WriteLine("  (no user-defined fields beyond the join key)");
                continue;
            }
            foreach (var f in udfs)
                Console.WriteLine($"  {(string)f["ColumnName"]!,-32} {f["DataType"]}({f["Length"]})  " +
                                  $"null={f["IsNullable"]}");
        }

        Console.WriteLine("\n" + new string('=', 60));
        Console.WriteLine($"{tables.Count} table(s), {totalReal} user-defined field(s)");
    }

    /// <summary>
    /// Split plumbing from genuine UDFs. Drops the surrogate key (position
    /// 1), then keeps every nullable column plus any NOT NULL column that
    /// appears after the first nullable one (the customer_ud.autoorder_flag
    /// shape).
    /// </summary>
    private static List<JToken> RealUdfs(List<JToken> orderedFields)
    {
        var tail = orderedFields.Skip(1).ToList();
        var seenNullable = false;
        var result = new List<JToken>();
        foreach (var f in tail)
        {
            var nullable = (string)f["IsNullable"]! == "Y";
            if (nullable)
            {
                seenNullable = true;
                result.Add(f);
            }
            else if (seenNullable)
            {
                result.Add(f);
            }
        }
        return result;
    }
}
