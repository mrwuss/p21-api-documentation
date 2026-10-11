// Recipe: Purchasing Runbook — Stock PO -> Receipt -> Voucher, and Drop Ship
// Docs:   docs/recipes/purchase-receive-vouch.md
//
// Runs both buy-side paths one step at a time, reading each step back
// before the next one starts:
//
//   Path A (stock):     A1 PurchaseOrder -> A2 PurchaseOrderReceipt
//                       -> A3 ConvertPOToVoucher                (Transaction API)
//   Path B (drop ship): B1 Order with a disposition-D line      (Interactive)
//                       B2 re-open, c_create_po ON, PO wizard   (Interactive)
//                       B3 DirectShipConfirmation               (Interactive)
//                       B4 ConvertPOToVoucher on that receipt   (Transaction API)
//
// Path A needs an item whose primary bin at the location is usable (not a
// put-locked bin such as '0'). Path B needs an API user with a Buyer ID —
// answer "y" to the consumer-key prompt when that user is the one with it.

using Newtonsoft.Json.Linq;
using static P21Examples.Recipes.RunbookSteps;

namespace P21Examples.Recipes;

public static class PurchaseReceiveVouch
{
    public static async Task RunAsync()
    {
        Console.WriteLine("Runbook - Purchasing: Stock PO -> Receipt -> Voucher, and Drop Ship");
        Console.WriteLine(new string('=', 60));
        Console.WriteLine("Values (Enter keeps the placeholder):");
        var path = Ask("Path (A, B or both)", "both").ToUpperInvariant();
        var location = Ask("Location", "10");
        var tag = Ask("Tag for the PO / order", "RUNBOOK-001");
        string vendor = "", buyer = "", item = "", qty = "", price = "";
        if (path is "A" or "BOTH")
        {
            vendor = Ask("Vendor ID", "SUP-100");
            buyer = Ask("Buyer ID (employee number)", "100");
            item = Ask("Stock item (usable primary bin)", "ITEM-001");
            qty = Ask("Quantity", "2");
            price = Ask("PO price (unit_price_display)", "6.55");
        }
        string customer = "", shipTo = "", contact = "", taker = "", dsItem = "", dsQty = "",
            dsPrice = "", dsPoCost = "";
        var consumer = false;
        if (path is "B" or "BOTH")
        {
            customer = Ask("Customer ID", "CUST-100");
            shipTo = Ask("Ship-to ID", "CUST-100");
            contact = Ask("Contact ID", "300");
            taker = Ask("Taker", "JSMITH");
            dsItem = Ask("Direct-ship item", "ITEM-002");
            dsQty = Ask("Quantity", "3");
            dsPrice = Ask("Sell price", "4.00");
            dsPoCost = Ask("PO cost", "2.50");
            consumer = Ask("Write as the consumer-key user (needs a Buyer ID)? y/n", "n") == "y";
        }

        if (path is "A" or "BOTH")
        {
            RecipeHelpers.PrintPayload("A1 PurchaseOrder payload",
                BuildPoPayload(location, vendor, buyer, item, qty, price, $"{tag}-A"));
            RecipeHelpers.PrintPayload("A2 PurchaseOrderReceipt payload (po_no from A1)",
                BuildReceiptPayload("{po_no}", $"{tag}-A"));
            RecipeHelpers.PrintPayload("A3 ConvertPOToVoucher payload (one row per receipt line)",
                BuildVoucherPayload("{po_no}", "{receipt_number}", vendor, $"{tag}-A",
                    new List<(string, string, string)> { ("1", qty, price) }));
        }
        if (path is "B" or "BOTH")
        {
            Console.WriteLine($@"
Path B call plan (Interactive API, ResponseWindowHandlingEnabled):
  B1 Order: quote=OFF, sales/source_loc_id={location}, customer_id={customer}, ship_to_id={shipTo},
     contact_id={contact}, dates (cb_ok), po_no={tag}-B, taker={taker}; TP_ITEMS:
     oe_order_item_id={dsItem}, unit_quantity={dsQty}, disposition=D, unit_price={dsPrice},
     po_cost={dsPoCost}; save.
  B2 Order: order_no=<B1>, c_create_po=ON, save -> wizard (cb_finish in its tools):
     cb_next (PO committed), cb_finish.
  B3 DirectShipConfirmation: tp_1_dw_po.po_no=<B2>, receive_all=ON, save.
  B4 ConvertPOToVoucher against the B3 receipt (payload as A3).");
        }

        if (!RecipeHelpers.ConfirmExecute())
            return;

        using var rb = await Runbook.CreateAsync(consumer);
        if (path is "A" or "BOTH")
        {
            Console.WriteLine("\nA1 - Create the PO (Transaction PurchaseOrder)");
            var result = await rb.TransactionAsync(
                BuildPoPayload(location, vendor, buyer, item, qty, price, $"{tag}-A"), "PurchaseOrder");
            var poNo = ResultValue(result, "TABPAGE_1.tp_1_dw_1", "po_no")!;
            var hdr = await rb.OneAsync("po_hdr", $"po_no eq {poNo}", "po_no,po_type,approved");
            Console.WriteLine($"    po_no = {poNo}, po_type = {hdr["po_type"]}, approved = {hdr["approved"]}");
            var line = await rb.OneAsync("po_line", $"po_no eq {poNo}", "line_no,unit_price");
            Check("po_line.unit_price", Fmt(Num(line["unit_price"])), Fmt(Num(price)));

            Console.WriteLine("\nA2 - Receive it (Transaction PurchaseOrderReceipt)");
            result = await rb.TransactionAsync(BuildReceiptPayload(poNo, $"{tag}-A"), "PurchaseOrderReceipt");
            var receiptNo = ResultValue(result, "TABPAGE_1.tp_1_dw_po", "receipt_number")
                ?? (await rb.OneAsync("inventory_receipts_hdr", $"po_number eq {poNo}",
                    "receipt_number", "receipt_number desc"))["receipt_number"]!.ToString();
            Console.WriteLine($"    receipt_number = {receiptNo}");
            foreach (var l in await rb.ODataAsync("po_line", $"po_no eq {poNo}", "line_no,qty_ordered,qty_received"))
                Check($"po_line {l["line_no"]} qty_received", Fmt(Num(l["qty_received"])), Fmt(Num(l["qty_ordered"])));

            Console.WriteLine("\nA3 - Vouch the vendor invoice (Transaction ConvertPOToVoucher)");
            await VouchAsync(rb, poNo, receiptNo, vendor, $"{tag}-A");
        }

        if (path is "B" or "BOTH")
        {
            Console.WriteLine("\nB1 - Sales order with a direct-ship line (Interactive Order)");
            var orderNo = await EnterOrderAsync(rb,
                new[]
                {
                    ("sales_loc_id", location), ("source_loc_id", location),
                    ("customer_id", customer), ("ship_to_id", shipTo), ("contact_id", contact),
                    ("order_date", Today), ("requested_date", DaysFromToday(2)),
                    ("po_no", $"{tag}-B"), ("taker", taker),
                },
                new[]
                {
                    new[]
                    {
                        ("oe_order_item_id", dsItem), ("unit_quantity", dsQty),
                        ("disposition", "D"),          // only accepted while the line is entered
                        ("unit_price", dsPrice),
                        ("po_cost", dsPoCost),         // flows to the PO line's price
                    },
                });
            var ol = await rb.OneAsync("oe_line", $"order_no eq '{orderNo}'", "line_no,disposition");
            Check("oe_line.disposition", ol["disposition"], "D");

            Console.WriteLine("\nB2 - Re-open, c_create_po = ON, save, PO wizard (Interactive Order)");
            var poNo = await CreatePoFromOrderAsync(rb, orderNo);

            Console.WriteLine("\nB3 - Confirm the direct ship (Interactive DirectShipConfirmation)");
            var receiptNo = await ConfirmDirectShipAsync(rb, poNo, orderNo);

            Console.WriteLine("\nB4 - Vouch the vendor invoice against the B3 receipt (ConvertPOToVoucher)");
            var poVendor = (await rb.OneAsync("po_hdr", $"po_no eq {poNo}", "vendor_id"))["vendor_id"]!.ToString();
            await VouchAsync(rb, poNo, receiptNo, poVendor, $"{tag}-B");
        }
        Console.WriteLine("\nRunbook complete.");
    }

    /// <summary>A1: PurchaseOrder header + one line. Omit division_id/company_id; they default.</summary>
    private static JObject BuildPoPayload(
        string location, string vendor, string buyer, string item, string qty, string price, string tag) =>
        Payload("PurchaseOrder", false,
            Element("TABPAGE_1.tp_1_dw_1", "Form", Array.Empty<string>(), new[]
            {
                Edit("location_id", location), Edit("vendor_id", vendor),
                Edit("buyer_id", buyer),                       // employee NUMBER -> po_hdr.requested_by
                Edit("order_date", Today), Edit("required_date", DaysFromToday(5)),
                Edit("external_po_no", tag),
            }),
            Element("TABPAGE_17.tp_17_dw_17", "List", new[] { "item_id" }, new[]
            {
                Edit("item_id", item), Edit("unit_quantity", qty),
                Edit("unit_of_measure", "EA"), Edit("pricing_unit", "EA"),
                Edit("unit_price_display", price),             // "PO Price" — NOT unit_price
            }));

    /// <summary>A2: receive every line at its remaining quantity — the whole payload.</summary>
    private static JObject BuildReceiptPayload(string poNo, string tag) =>
        Payload("PurchaseOrderReceipt", false,
            Element("TABPAGE_1.tp_1_dw_po", "Form", Array.Empty<string>(),
                new[] { Edit("po_no", poNo), Edit("receive_all", "Y") }),
            Element("TABPAGE_1.tp_1_dw_1", "Form", Array.Empty<string>(),
                new[] { Edit("external_reference_no", tag) }));

    /// <summary>
    /// A3/B4: voucher header + one row per receipt line. Send these five header
    /// fields and nothing else — company_id, branch_id, period and
    /// year_for_period are marked required AND are disabled columns.
    /// invoice_amount must equal the vouched lines.
    /// </summary>
    private static JObject BuildVoucherPayload(
        string poNo, string receiptNo, string vendor, string invoiceNo,
        List<(string Line, string Qty, string Cost)> lines)
    {
        var amount = lines.Sum(l => Num(l.Qty) * Num(l.Cost));
        return Payload("ConvertPOToVoucher", false,
            Element("TABPAGE_1.tp_1_dw_1", "Form", new[] { "voucher_no" }, new[]  // voucher_no empty = create
            {
                Edit("po_no", poNo), Edit("invoice_no", invoiceNo), Edit("invoice_date", Today),
                Edit("invoice_amount", amount.ToString("0.00", System.Globalization.CultureInfo.InvariantCulture)),
                Edit("vendor_id", vendor),
            }),
            Element("TABPAGE_17.tp_17_dw_17", "List", new[] { "receipt_number", "line_number", "po_no" },
                lines.Select(l => new[]
                {
                    Edit("receipt_number", receiptNo), Edit("line_number", l.Line), Edit("po_no", poNo),
                    Edit("unit_qty_invoiced", l.Qty), Edit("unit_cost_display", l.Cost),
                }).ToArray()));
    }

    /// <summary>A3/B4: vouch the receipt's lines and read the voucher back.</summary>
    private static async Task VouchAsync(Runbook rb, string poNo, string receiptNo, string vendor, string invoiceNo)
    {
        // inventory_receipts_line uses line_number, not line_no
        var lines = (await rb.ODataAsync("inventory_receipts_line", $"receipt_number eq {receiptNo}",
                "line_number,qty_received,unit_cost"))
            .Select(r => (r["line_number"]!.ToString(), Fmt(Num(r["qty_received"])), Fmt(Num(r["unit_cost"]))))
            .ToList();
        var result = await rb.TransactionAsync(
            BuildVoucherPayload(poNo, receiptNo, vendor, invoiceNo, lines), "ConvertPOToVoucher");
        var voucherNo = ResultValue(result, "TABPAGE_1.tp_1_dw_1", "voucher_no")!;
        var hdr = await rb.OneAsync("apinv_hdr", $"voucher_no eq '{voucherNo}'",
            "voucher_no,invoice_amount,approved");
        Console.WriteLine($"    voucher_no = {voucherNo}, invoice_amount = {hdr["invoice_amount"]}, " +
                          $"approved = {hdr["approved"]}");
        foreach (var l in await rb.ODataAsync("inventory_receipts_line", $"receipt_number eq {receiptNo}",
                     "line_number,vouch_complete"))
            Check($"receipt line {l["line_number"]} vouch_complete", l["vouch_complete"], "Y");
    }

    /// <summary>
    /// B2: re-open the saved order, c_create_po ON, save, drive the wizard.
    /// The wizard is identified by its buttons (cb_finish) before anything is
    /// pressed; the PO is committed at cb_next, before cb_finish.
    /// </summary>
    private static async Task<string> CreatePoFromOrderAsync(Runbook rb, string orderNo)
    {
        var session = await rb.SessionAsync();
        var windowId = await session.OpenAsync("Order");
        string? wizardPo = null;
        try
        {
            await session.ChangeAsync(windowId, "TABPAGE_1", "order", "order_no", orderNo);
            await session.ChangeAsync(windowId, "TABPAGE_1", "order", "c_create_po", "ON"); // needs a Buyer ID
            var result = await session.SaveRawAsync(windowId);
            for (var i = 0; i < 10 && RunbookSession.IsBlocked(result); i++)
            {
                foreach (var popupId in RunbookSession.PopupIds(result))
                {
                    var tools = await session.ToolsAsync(popupId);
                    if (!tools.Contains("cb_finish"))       // some other prompt: proceed
                    {
                        result = await session.ClickAsync(popupId,
                            new[] { "cb_ok", "cb_1", "cb_yes" }.First(tools.Contains));
                        continue;
                    }
                    foreach (var row in await session.RowsAsync(popupId, "items"))
                        Console.WriteLine($"    wizard page 1: {row["item_id"]} qty {row["qty_to_purchase"]} " +
                                          $"supplier {row["supplier_id"]} quote_item={row["quote_item"]}");
                    await session.ClickAsync(popupId, "cb_next");   // <-- the PO is committed HERE
                    foreach (var row in await session.RowsAsync(popupId, "po_print"))
                    {
                        wizardPo = row["po_no"];
                        Console.WriteLine($"    wizard page 2: po_no {wizardPo}, po_type {row["po_type"]}");
                    }
                    result = await session.ClickAsync(popupId, "cb_finish");
                }
            }
        }
        finally
        {
            await session.CloseAsync(windowId);
        }

        var link = await rb.OneAsync("oe_line_po", $"order_number eq '{orderNo}'",
            "order_number,line_number,po_no,connection_type");
        Check("oe_line_po.connection_type", link["connection_type"], "P");
        var poNo = link["po_no"]!.ToString();
        var hdr = await rb.OneAsync("po_hdr", $"po_no eq {poNo}", "po_no,po_type");
        Check("po_hdr.po_type", hdr["po_type"], "D");
        if (wizardPo != null && wizardPo != poNo)
            throw new InvalidOperationException($"Wizard showed PO {wizardPo}, oe_line_po links {poNo}");
        return poNo;
    }

    /// <summary>
    /// B3: Interactive DirectShipConfirmation — receipt AND customer invoice in
    /// one save. Never send c_email_invoice. The save writes shipment_date onto
    /// every po_line.supplier_ship_date.
    /// </summary>
    private static async Task<string> ConfirmDirectShipAsync(Runbook rb, string poNo, string orderNo)
    {
        var session = await rb.SessionAsync();
        var windowId = await session.OpenAsync("DirectShipConfirmation");
        try
        {
            await session.ChangeAsync(windowId, "TABPAGE_1", "tp_1_dw_po", "po_no", poNo);
            await session.ChangeAsync(windowId, "TABPAGE_1", "tp_1_dw_po", "receive_all", "ON");
            await session.SaveAsync(windowId);
        }
        finally
        {
            await session.CloseAsync(windowId);
        }
        var receipt = await rb.OneAsync("inventory_receipts_hdr", $"po_number eq {poNo}",
            "receipt_number,receipt_type,shipment_date", "receipt_number desc");
        Console.WriteLine($"    receipt_number = {receipt["receipt_number"]} (type {receipt["receipt_type"]}, " +
                          $"shipment_date {receipt["shipment_date"]})");
        foreach (var l in await rb.ODataAsync("po_line", $"po_no eq {poNo}", "line_no,complete"))
            Check($"po_line {l["line_no"]} complete", l["complete"], "Y");
        foreach (var l in await rb.ODataAsync("oe_line", $"order_no eq '{orderNo}'", "line_no,qty_ordered,qty_invoiced"))
            Check($"oe_line {l["line_no"]} qty_invoiced", Fmt(Num(l["qty_invoiced"])), Fmt(Num(l["qty_ordered"])));
        var inv = await rb.OneAsync("invoice_hdr", $"order_no eq '{orderNo}'", "invoice_no,total_amount");
        Console.WriteLine($"    customer invoice {inv["invoice_no"]}, total {inv["total_amount"]}");
        return receipt["receipt_number"]!.ToString();
    }
}
