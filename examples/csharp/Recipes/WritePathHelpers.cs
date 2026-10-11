// Helpers for the Transaction API write-path recipes (bins, vendor,
// contract ship-to/line_no, assembly edits, order append/hold/cancel,
// item/customer merge).
//
// - Ask(): every record ID is asked for at run time, with a generic
//   placeholder as the default, so no tenant data lives in the source.
// - Rows(): OData read-back as a JArray of rows.
// - ResultValue(): read a field from a passed transaction's echoed rows
//   (for example a generated vendor ID or order number).

using Newtonsoft.Json.Linq;
using P21Examples.Common;
using P21Examples.Common.Models;

namespace P21Examples.Recipes;

internal static class WritePathHelpers
{
    /// <summary>Ask for a value; an empty answer keeps the default.</summary>
    public static string Ask(string label, string defaultValue)
    {
        Console.Write($"{label} [{defaultValue}]: ");
        var answer = Console.ReadLine()?.Trim();
        return string.IsNullOrEmpty(answer) ? defaultValue : answer;
    }

    /// <summary>Quote a string literal for an OData $filter.</summary>
    public static string Q(string value) => "'" + value.Replace("'", "''") + "'";

    /// <summary>Query an OData table (or view) and return its rows.</summary>
    public static async Task<JArray> Rows(
        P21Client client, string name, string filter, string? select = null, bool view = false)
    {
        var json = view
            ? await client.OData.QueryViewAsync(name, select: select, filter: filter)
            : await client.OData.QueryAsync(name, select: select, filter: filter);
        return (JArray)json["value"]!;
    }

    /// <summary>Read a field from the first passed transaction's echoed rows.</summary>
    public static string? ResultValue(TransactionResult result, string element, string field)
    {
        foreach (var txn in result.Results?["Transactions"] ?? new JArray())
        {
            if ((string?)txn["Status"] != "Passed")
                continue;
            foreach (var de in txn["DataElements"] ?? new JArray())
            {
                if ((string?)de["Name"] != element)
                    continue;
                foreach (var row in de["Rows"] ?? new JArray())
                    foreach (var e in row["Edits"] ?? new JArray())
                        if ((string?)e["Name"] == field && !string.IsNullOrEmpty((string?)e["Value"]))
                            return (string?)e["Value"];
            }
        }
        return null;
    }

    /// <summary>One Transaction API DataElement with a single row.</summary>
    public static JObject Element(string name, string type, string[] keys, params JObject[] edits) =>
        new JObject
        {
            ["Name"] = name, ["Type"] = type, ["Keys"] = new JArray(keys),
            ["Rows"] = new JArray { new JObject {
                ["Edits"] = new JArray(edits), ["RelativeDateEdits"] = new JArray() } }
        };

    /// <summary>A payload with one Status "New" transaction.</summary>
    public static JObject Payload(string service, params JObject[] elements) =>
        new JObject
        {
            ["Name"] = service, ["UseCodeValues"] = false,
            ["Transactions"] = new JArray {
                new JObject { ["Status"] = "New", ["DataElements"] = new JArray(elements) } }
        };
}
