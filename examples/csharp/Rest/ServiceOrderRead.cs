// Other REST Families - Read a Service Order (service/serviceorders)
// Docs: docs/15-Other-REST-Families.md#serviceserviceorders
// Mirrors: examples/python/rest/service_order_read.py
//
// The finding: this route resolves against ANY oe_hdr.order_no, not just
// orders specially flagged as "service" -- its shape is an ordinary
// sales order header. PUT against the same order was refused with
// "Unable to find Order Header using Order No" -- see docs/15.

using Newtonsoft.Json.Linq;

namespace P21Examples.Rest;

public static class ServiceOrderRead
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Other REST Families - Service Order Read (service/serviceorders)");
        Console.WriteLine(new string('=', 60));

        var (http, baseUrl) = await RestHelpers.CreateRawClientAsync();
        using var _ = http;
        Console.WriteLine($"Server: {baseUrl}");

        Console.Write("Order number (any oe_hdr.order_no) [999991]: ");
        var orderNo = Console.ReadLine()?.Trim();
        orderNo = string.IsNullOrEmpty(orderNo) ? "999991" : orderNo;

        var response = await http.GetAsync($"{baseUrl}/api/service/serviceorders/{orderNo}");
        response.EnsureSuccessStatusCode();
        var order = JObject.Parse(await response.Content.ReadAsStringAsync());

        Console.WriteLine($"\nOrder {order["OrderNo"]}  customer={order["CustomerId"]}  " +
                          $"location={order["LocationId"]}  po_no={order["PoNo"]}");
        Console.WriteLine($"Ship to: {order["Ship2Name"]}");
        Console.WriteLine($"\nLines={RestHelpers.JsonDisplay(order["Lines"])}  " +
                          $"Salesreps={RestHelpers.JsonDisplay(order["Salesreps"])}  " +
                          $"Notes={RestHelpers.JsonDisplay(order["Notes"])}");
        Console.WriteLine("\nThis is an ordinary sales order read through a differently-shaped " +
                          "view -- the same order also answers on sales/tasks' LinkId lookups " +
                          "and the Transaction API Order service.");
    }
}
