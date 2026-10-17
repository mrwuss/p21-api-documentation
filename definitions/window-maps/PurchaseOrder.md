# Purchase Order Entry (`PurchaseOrder`)

- Window class: `w_purchase_order_entry_sheet`; menu class: `m_purchaseorderentry`
- Tabs: 37; datawindows mapped: 29; unreachable entries: 17

## Tab overview

| Tab | Caption | Datawindows mapped | Tables in the SELECT |
|---|---|---|---|
| `TABPAGE_1` | Purchase Order | `tp_1_dw_1` | address, carrier_info, carrier_priority, carrier_ship_method, company, contacts, po_hdr, purchase_transfer_group, supplier |
| `TABPAGE_2` | Vendor | `tp_2_dw_2` | address, carrier_info, carrier_priority, carrier_ship_method, company, contacts, po_hdr, purchase_transfer_group, supplier |
| `TABPAGE_3` | Supplier | `tp_3_dw_3` | address, carrier_info, carrier_priority, carrier_ship_method, company, contacts, po_hdr, purchase_transfer_group, supplier |
| `TABPAGE_4` | Pricing | `tp_4_dw_4` | supplier_pricing |
| `TABPAGE_5` | Division | `tp_5_dw_5` | address, carrier_info, carrier_priority, carrier_ship_method, company, contacts, po_hdr, purchase_transfer_group, supplier |
| `TABPAGE_6` | Classes | `tp_6_dw_6` | address, carrier_info, carrier_priority, carrier_ship_method, company, contacts, po_hdr, purchase_transfer_group, supplier |
| `TABPAGE_7` | PO Notes | `tp_7_dw_7` | note_area, notepad_class, po_hdr_notepad |
| `SHIP_TO` | Ship To | `ship_to` | address, carrier_info, carrier_priority, carrier_ship_method, company, contacts, po_hdr, purchase_transfer_group, supplier |
| `TOTALS` | Totals | `totals` | location_supplier, supplier |
| `TABPAGE_LANDED_COST` | Landed Cost | `tabpage_landed_cost` | company, currency_line, landed_cost_category, landed_cost_driver, landed_cost_driver_tax, lc_driver_x_tran, po_hdr |
| `SCHEDULE` | Schedule | `po_schedule_rule`, `po_schedule` | po_schedule, po_schedule_rule |
| `DOCUMENT_LINK` | Document Links | `document_link`, `document_link_forms` | document_link, document_link_area, document_link_entity_req, inv_mast |
| `TABPAGE_CONTACT` | Contacts | `contacts` | address, contacts, salutation |
| `TIMESTAMP` | Audit Trail | `timestamp`, `audit_trail` | p21_view_audit_trail_po_hdr_<id> |
| `TABPAGE_17` | Items | `tp_17_dw_17` | inv_loc, inv_mast, inventory_supplier, item_revision, item_uom, oe_line, oe_line_po, p21_view_total_qty_on_po_per_order_line, po_hdr, po_line, revision_transaction, tpcx_dead_stock, vendor_rfq_line, vessel_receipts_line |
| `TABPAGE_18` | Extended Info  | `extended_info` | inv_loc, inv_mast, inventory_supplier, item_revision, item_uom, oe_line, oe_line_po, p21_view_total_qty_on_po_per_order_line, po_hdr, po_line, revision_transaction, tpcx_dead_stock, vendor_rfq_line, vessel_receipts_line |
| `TABPAGE_19` | Price | `price` | inv_loc, inv_mast, inventory_supplier, item_revision, item_uom, oe_line, oe_line_po, p21_view_total_qty_on_po_per_order_line, po_hdr, po_line, revision_transaction, tpcx_dead_stock, vendor_rfq_line, vessel_receipts_line |
| `TABPAGE_21` | PO Line Notes | `tp_21_dw_21` | note_area, notepad_class, po_line_notepad |
| `COMMITMENT_SCHEDULE` | Commitment Schedule | `commitment_schedule_detail`, `commitment_schedule_header` | inv_loc, inv_loc_stock_status, inv_mast, location, p21_view_supplier_purchasing_info |
| `RELEASE_SCHEDULE` | Release Schedule | `po_line_schedule_item`, `po_line_schedule` | inv_mast, po_line, po_line_schedule |
| `TABPAGE_LANDED_COST_DETAIL` | Landed Cost | `tabpage_landed_cost_detail` | currency_line, inv_mast, landed_cost_category, landed_cost_driver, landed_cost_driver_tax, lc_driver_x_tran, lc_driver_x_tran_detail, po_line |
| `DOCUMENT_LINK_DETAIL` | Document Links | `document_link_detail_detail` | document_link, document_link_area, document_link_entity_req, inv_mast |
| `PURCHASEHISTORY` | Purchase History | `po_history` | inv_mast, po_hdr, po_line, supplier, vendor_rfq_hdr, vessel_receipts_hdr, vessel_receipts_line |
| `TIMESTAMPDETAIL` | Timestamp | `timestampdetail` |  |

## Datawindows

### `TABPAGE_1.tp_1_dw_1` (Purchase Order)

- Update table: `po_hdr`
- Tables in the SELECT: `po_hdr`, `address`, `company`, `contacts`, `supplier`, `purchase_transfer_group`, `carrier_info`, `carrier_ship_method`, `carrier_priority`

| Field | Stored in | Basis |
|---|---|---|
| `po_no` | `po_hdr.po_no` | probed |
| `company_id` | `po_hdr.company_no` | probed |
| `location_id` | `po_hdr.location_id` | probed |
| `vendor_id` | `po_hdr.vendor_id` | probed |
| `vendor_supplier_id` | `po_hdr.supplier_id` | probed |
| `division_id` | `po_hdr.division_id` | probed |
| `buyer_id` | `po_hdr.requested_by` | probed |
| `purchase_transfer_group_id` | `po_hdr.purchase_group_id` | probed |
| `c_vendor_rfq` | computed: `(CASE WHEN po_hdr.po_type = 'Q' THEN 'Y' ELSE 'N' END)` | probed |
| `external_po_no` | `po_hdr.external_po_no` | probed |
| `contact_id` | `po_hdr.contact_id` | probed |
| `order_date` | `po_hdr.order_date` | probed |
| `required_date` | `po_hdr.date_due` | probed |
| `expected_date` | `po_hdr.expected_date` | probed |
| `expected_ship_date` | `po_hdr.expected_ship_date` | probed |
| `supplier_release_no` | `po_hdr.supplier_release_no` | probed |
| `print_canadian_b3_forms_flag` | `po_hdr.print_canadian_b3_forms_flag` | probed |
| `canadian_b3_forms_date` | `po_hdr.canadian_b3_forms_date` | probed |
| `print_po_form` | computed: `' '` | probed |
| `fax_po_form` | computed: `' '` | probed |
| `email` | computed: `'N'` | probed |
| `edi_form` | computed: `'N'` | probed |
| `resend_edi_form` | computed: `'N'` | probed |
| `process_doclinks` | computed: `'N'` | probed |
| `exclude_from_lead_time` | `po_hdr.exclude_from_lead_time` | probed |
| `approved` | `po_hdr.approved` | probed |
| `delete_flag` | `po_hdr.delete_flag` | probed |
| `net_billing_flag` | `po_hdr.net_billing_flag` | probed |
| `do_not_export_carrier_po_flag` | `po_hdr.do_not_export_carrier_po_flag` | probed |
| `auto_vouch_except_flag` | `po_hdr.auto_vouch_except_flag` | probed |
| `excl_send_info_to_rfnav` | computed: `(the tool names po_hdr.excl_send_linked_info_to_rfnav_flag; the SELECT does not read it)` | probed |
| `direct_through_stock_flag` | `po_hdr.direct_through_stock_flag` | probed |
| `vendor_supplier_name` | `address.name` | probed |
| `vendor_name` | `address.name` | probed |
| `location_name` | `address.name` | probed |
| `purchase_transfer_group_desc` | `purchase_transfer_group.purchase_transfer_group_desc` | probed |
| `division_name` | `address.name` | probed |
| `company_name` | `company.company_name` | probed |
| `buyer_name` | computed: `contacts.last_name + ', ' + contacts.first_name + ' ' + contacts.mi` | probed |
| `sales_order_number` | `po_hdr.sales_order_number` | probed |
| `source_type` | `po_hdr.source_type` | probed |
| `po_hdr_po_type` | `po_hdr.po_type` | probed |
| `contact_name` | computed: `' '` | probed |
| `complete` | `po_hdr.complete` | probed |
| `supplier_id` | computed: `(computed in the datawindow)` | probed |
| `cf_ship_to_address_id` | computed: `(computed in the datawindow)` | probed |
| `cf_ship_to_state` | computed: `(computed in the datawindow)` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Purchase Order Number: | `po_hdr.po_no` |
| 2 | Vendor ID: | `po_hdr.vendor_id` |
| 3 | Vendor Name | `address.name` |
| 4 | Supplier ID: | `po_hdr.supplier_id` |
| 5 | Vendor Supplier Name | `address.name` |
| 6 | Division ID: | `po_hdr.division_id` |
| 7 | Division Name | `address.name` |
| 8 | Company ID: | `po_hdr.company_no` |
| 9 | Company Name | `company.company_name` |
| 10 | Purchase Location ID: | `po_hdr.location_id` |
| 11 | Location Name | `address.name` |
| 12 | Buyer ID: | `po_hdr.requested_by` |
| 16 | Purchase Order Date: | `po_hdr.order_date` |
| 17 | Required Date: | `po_hdr.date_due` |
| 18 | Approved | `po_hdr.approved` |
| 19 | Complete | `po_hdr.complete` |
| 20 | Delete Flag | `po_hdr.delete_flag` |
| 51 | Purchase Group ID: | `po_hdr.purchase_group_id` |
| 58 | Purchase Transfer Group Desc | `purchase_transfer_group.purchase_transfer_group_desc` |
| 59 | Currency ID: | `po_hdr.currency_id` |
| 62 | SO Number: | `po_hdr.sales_order_number` |
| 71 | Buyer Name | `compute_0071` |
| 73 | Print Po Form | `compute_0073` |
| 74 | Purchase Order Type: | `po_hdr.po_type` |
| 76 | Fax Po Form | `compute_0074` |
| 77 | 'External PO Number:if ( (c_vendor_rfq = 'N' OR IsNull(c_vendor_rfq)), 'External PO Number:', 'Supplier Quote Number:')' | `po_hdr.external_po_no` |
| 78 | Exclude From Lead Time | `po_hdr.exclude_from_lead_time` |
| 79 | Purchase Order Source: | `po_hdr.source_type` |
| 83 | Edi Form | `edi_form` |
| 85 | Email | `address_b.email` |
| 86 | Contact ID: | `po_hdr.contact_id` |
| 87 | Contact Name | `contact_name` |
| 88 | C Vendor Rfq | `c_vendor_rfq` |
| 95 | Process Doclinks | `process_doclinks` |
| 96 | Expected Date: | `po_hdr.expected_date` |
| 122 | Expected Ship Date: | `po_hdr.expected_ship_date` |
| 123 | Auto Vouch Except Flag | `po_hdr.auto_vouch_except_flag` |
| 127 | Resend Edi Form | `resend_edi_form` |
| calc | Status: | `if (delete_flag = 'Y' ,'Deleted',if(complete = 'Y','Completed',if(printed='Y','Printed',if(approved='Y','Approved',''))))` |

### `TABPAGE_2.tp_2_dw_2` (Vendor)

- Update table: `po_hdr`
- Tables in the SELECT: `po_hdr`, `address`, `company`, `contacts`, `supplier`, `purchase_transfer_group`, `carrier_info`, `carrier_ship_method`, `carrier_priority`

| Field | Stored in | Basis |
|---|---|---|
| `terms` | `po_hdr.terms` | column |
| `vendor_id` | `po_hdr.vendor_id` | column |
| `city` | `address.mail_city` | probed |
| `address2` | `address.mail_address2` | probed |
| `address1` | `address.mail_address1` | probed |
| `vendor_name` | `address.name` | probed |
| `state` | `address.mail_state` | probed |
| `postal_code` | `address.mail_postal_code` | probed |
| `phone_number` | `address.central_phone_number` | probed |
| `fax_number` | `address.central_fax_number` | probed |
| `country` | `address.mail_country` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 2 | Vendor ID: | `po_hdr.vendor_id` |
| 3 | Vendor Name | `address.name` |
| 21 | Mail Address1: | `address.mail_address1` |
| 22 | Mail Address2: | `address.mail_address2` |
| 23 | Mail City: | `address.mail_city` |
| 24 | State | `address.mail_state` |
| 25 | Postal Code | `address.mail_postal_code` |
| 26 | Mail Country: | `address.mail_country` |
| 27 | Central Phone Number: | `address.central_phone_number` |
| 28 | Central Fax Number: | `address.central_fax_number` |
| 29 | Terms: | `po_hdr.terms` |

### `TABPAGE_3.tp_3_dw_3` (Supplier)

- Update table: `po_hdr`
- Tables in the SELECT: `po_hdr`, `address`, `company`, `contacts`, `supplier`, `purchase_transfer_group`, `carrier_info`, `carrier_ship_method`, `carrier_priority`

| Field | Stored in | Basis |
|---|---|---|
| `carrier_id` | `po_hdr.carrier_id` | column |
| `packing_basis` | `po_hdr.packing_basis` | column |
| `po_desc` | `po_hdr.po_desc` | column |
| `address1` | `address.mail_address1` | probed |
| `supplier_id` | `po_hdr.supplier_id` | column |
| `address2` | `address.mail_address2` | probed |
| `city` | `address.mail_city` | probed |
| `supplier_name` | `address.name` | probed |
| `state` | `address.mail_state` | probed |
| `postal_code` | `address.mail_postal_code` | probed |
| `country` | `address.mail_country` | probed |
| `fax_number` | `address.central_fax_number` | probed |
| `phone_number` | `address.central_phone_number` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 4 | Supplier ID: | `po_hdr.supplier_id` |
| 5 | Supplier Name | `address.name` |
| 30 | Mail Address1: | `address.mail_address1` |
| 31 | Mail Address2: | `address.mail_address2` |
| 32 | Mail City: | `address.mail_city` |
| 33 | State | `address.mail_state` |
| 34 | Postal Code | `address.mail_postal_code` |
| 35 | Mail Country: | `address.mail_country` |
| 36 | Central Phone Number: | `address.central_phone_number` |
| 37 | Central Fax Number: | `address.central_fax_number` |
| 38 | Shipping Instructions: | `po_hdr.po_desc` |
| 39 | Carrier ID: | `po_hdr.carrier_id` |

### `TABPAGE_4.tp_4_dw_4` (Pricing)

- Update table: `supplier_pricing`
- Tables in the SELECT: `supplier_pricing`

| Field | Stored in | Basis |
|---|---|---|
| `company_id` | `supplier_pricing.company_id` | column |
| `multiplier` | `supplier_pricing.multiplier` | column |
| `pricing_method` | `supplier_pricing.pricing_method` | column |
| `source_price` | `supplier_pricing.source_price` | column |
| `supplier_id` | `supplier_pricing.supplier_id` | column |
| `address_name` | `address.name` | probed |
| `company_name` | `company.company_name` | column |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Company ID: | `supplier_pricing.company_id` |
| 2 | Supplier ID: | `supplier_pricing.supplier_id` |
| 3 | Pricing Method: | `supplier_pricing.pricing_method` |
| 4 | Source Price: | `supplier_pricing.source_price` |
| 5 | Multiplier: | `supplier_pricing.multiplier` |
| 6 | Address Name | `address.name` |
| 7 | Company Name | `company.company_name` |

### `TABPAGE_5.tp_5_dw_5` (Division)

- Update table: `po_hdr`
- Tables in the SELECT: `po_hdr`, `address`, `company`, `contacts`, `supplier`, `purchase_transfer_group`, `carrier_info`, `carrier_ship_method`, `carrier_priority`

| Field | Stored in | Basis |
|---|---|---|
| `address1` | `address.mail_address1` | probed |
| `address2` | `address.mail_address2` | probed |
| `city` | `address.mail_city` | probed |
| `division_id` | `po_hdr.division_id` | column |
| `division_name` | `address.name` | probed |
| `state` | `address.mail_state` | probed |
| `postal_code` | `address.mail_postal_code` | probed |
| `phone_number` | `address.central_phone_number` | probed |
| `fax_number` | `address.central_fax_number` | probed |
| `country` | `address.mail_country` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 6 | Division ID: | `po_hdr.division_id` |
| 7 | Division Name | `address.name` |
| 40 | Mail Address1: | `address.mail_address1` |
| 41 | Mail Address2: | `address.mail_address2` |
| 42 | Mail City/State/Zip: | `address.mail_city` |
| 43 | State | `address.mail_state` |
| 44 | Postal Code | `address.mail_postal_code` |
| 45 | Mail Country: | `address.mail_country` |
| 46 | Central Phone Number: | `address.central_phone_number` |
| 47 | Central Fax Number: | `address.central_fax_number` |

### `TABPAGE_6.tp_6_dw_6` (Classes)

- Update table: `po_hdr`
- Tables in the SELECT: `po_hdr`, `address`, `company`, `contacts`, `supplier`, `purchase_transfer_group`, `carrier_info`, `carrier_ship_method`, `carrier_priority`

| Field | Stored in | Basis |
|---|---|---|
| `po_class1` | `po_hdr.po_class1` | column |
| `po_class2` | `po_hdr.po_class2` | column |
| `po_class3` | `po_hdr.po_class3` | column |
| `po_class4` | `po_hdr.po_class4` | column |
| `po_class5` | `po_hdr.po_class5` | column |

| # | Label | table.column / expression |
|---|---|---|
| 52 | Class 1: | `po_hdr.po_class1` |
| 53 | Class 2: | `po_hdr.po_class2` |
| 54 | Class 3: | `po_hdr.po_class3` |
| 55 | Class 4: | `po_hdr.po_class4` |
| 56 | Class 5: | `po_hdr.po_class5` |

### `TABPAGE_7.tp_7_dw_7` (PO Notes)

- Update table: `po_hdr_notepad`
- Tables in the SELECT: `po_hdr_notepad`, `note_area`, `notepad_class`

| Field | Stored in | Basis |
|---|---|---|
| `note` | `po_hdr_notepad.note` | column |
| `note_id` | `po_hdr_notepad.note_id` | column |
| `topic` | `po_hdr_notepad.topic` | column |
| `notepad_class_desc` | `notepad_class.notepad_class_desc` | column |

| # | Label | table.column / expression |
|---|---|---|
| 2 | Note ID | `po_hdr_notepad.note_id` |
| 3 | Topic | `po_hdr_notepad.topic` |
| 4 | Note | `po_hdr_notepad.note` |
| 14 | Class | `notepad_class.notepad_class_desc` |

### `SHIP_TO.ship_to` (Ship To)

- Update table: `po_hdr`
- Tables in the SELECT: `po_hdr`, `address`, `company`, `contacts`, `supplier`, `purchase_transfer_group`, `carrier_info`, `carrier_ship_method`, `carrier_priority`

| Field | Stored in | Basis |
|---|---|---|
| `ship2_name` | `po_hdr.ship2_name` | column |
| `ship2_add1` | `po_hdr.ship2_add1` | column |
| `ship2_add2` | `po_hdr.ship2_add2` | probed |
| `ship2_city` | `po_hdr.ship2_city` | column |
| `ship2_state` | `po_hdr.ship2_state` | column |
| `ship2_zip` | `po_hdr.ship2_zip` | column |
| `ship2_country` | `po_hdr.ship2_country` | column |

| # | Label | table.column / expression |
|---|---|---|
| 63 | Ship To Name: | `po_hdr.ship2_name` |
| 65 | Ship To Address1: | `po_hdr.ship2_add1` |
| 66 | Ship To Address2: | `po_hdr.ship2_add2` |
| 67 | Ship To City/State/Zip: | `po_hdr.ship2_city` |
| 68 | Ship2 State | `po_hdr.ship2_state` |
| 69 | Ship To Country: | `po_hdr.ship2_country` |
| 70 | Ship2 Zip | `po_hdr.ship2_zip` |

### `TOTALS.totals` (Totals)

- Update table: `supplier`
- Tables in the SELECT: `supplier`, `location_supplier`

| Field | Stored in | Basis |
|---|---|---|
| `total_volume` | computed: `0.0000` | alias |
| `total_units_purchased` | computed: `0.0000` | alias |
| `total_no_of_pieces` | computed: `0.0000` | probed |
| `total_iva_tax_amount` | computed: `0.0000` | alias |
| `total_amount` | computed: `0.0000` | alias |
| `target_value` | computed: `CASE WHEN COALESCE(location_supplier.target_value, 0) = 0 THEN supplier.target_value ELSE location_supplier.target_value END` | alias |
| `no_of_line_items` | computed: `0` | alias |
| `total_weight` | computed: `0.0000` | alias |
| `control_value` | computed: `CASE WHEN COALESCE(location_supplier.target_value, 0) = 0 THEN supplier.control_value ELSE location_supplier.control_value END` | alias |
| `cf_containers_filled` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 2 | Control Value: | `supplier.control_value` |
| 3 | Target Value: | `location_supplier.target_value` |
| 4 | Number of Line Items: | `no_of_line_items` |
| 5 | Total Number of Pieces: | `total_no_of_pieces` |
| 6 | Total Weight: | `total_weight` |
| 7 | Total Amount: | `total_amount` |
| 8 | Total Units Purchased: | `cf_total_units_purchased` |
| 9 | Total Volume: | `cf_total_volume` |
| calc | Containers Filled: | `IF( container_volume = 0, 0, total_volume /  container_volume )` |

### `TABPAGE_LANDED_COST.tabpage_landed_cost` (Landed Cost)

- Update table: `lc_driver_x_tran`
- Tables in the SELECT: `lc_driver_x_tran`, `po_hdr`, `landed_cost_driver`, `landed_cost_category`, `company`, `landed_cost_driver_tax`, `currency_line`

| Field | Stored in | Basis |
|---|---|---|
| `landed_cost_driver_cd` | `landed_cost_driver.landed_cost_driver_cd` | column |
| `application_point_cd` | `lc_driver_x_tran.application_point_cd` | column |
| `payable_to` | `lc_driver_x_tran.payable_to` | column |
| `multiplier` | `lc_driver_x_tran.multiplier` | column |
| `calculation_method` | `lc_driver_x_tran.calculation_method_code_no` | probed |
| `dollar_amount` | `lc_driver_x_tran.dollar_amount` | column |
| `landed_cost_driver_desc` | `landed_cost_driver.landed_cost_driver_desc` | column |
| `tax_driver_flag` | `landed_cost_driver_tax.tax_driver_flag` | column |
| `landed_cost_amt` | `lc_driver_x_tran.landed_cost_amt` | column |
| `spaces` | computed: `(computed in the datawindow)` | dw_name |
| `cf_duty_amount_home` | computed: `(computed in the datawindow)` | dw_name |
| `cf_duty_amount` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_landed_cost_amount` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_landedcost` | computed: `(computed in the datawindow)` | dw_name |
| `cf_sum_duty_amount` | computed: `(computed in the datawindow)` | dw_name |
| `cf_sum_total_landed_cost_amount` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |
| `cf_zero` | computed: `(computed in the datawindow)` | dw_name |
| `cf_n` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 5 | Calculation Method | `lc_driver_x_tran.calculation_method_code_no` |
| 6 | Multiplier | `lc_driver_x_tran.multiplier` |
| 7 | Dollar Amount | `lc_driver_x_tran.dollar_amount` |
| 8 | Landed CostAmount | `lc_driver_x_tran.landed_cost_amt` |
| 13 | Landed Cost Driver | `landed_cost_driver.landed_cost_driver_cd` |
| 14 | Landed Cost Driver Description | `landed_cost_driver.landed_cost_driver_desc` |
| 20 | Application Point | `lc_driver_x_tran.application_point_cd` |
| 26 | Payable To: | `lc_driver_x_tran.payable_to` |
| 27 | Tax | `landed_cost_driver_tax.tax_driver_flag` |
| calc | Cf Duty Amount Home | `IF ( duty_flag = 'Y' AND  duty_percentage >= 0, landed_cost_amt_home * (duty_percentage / 100), 0)` |

### `SCHEDULE.po_schedule_rule` (Schedule)

- Update table: `po_schedule_rule`
- Tables in the SELECT: `po_schedule_rule`

| Field | Stored in | Basis |
|---|---|---|
| `release_type` | `po_schedule_rule.release_type` | column |
| `round_type` | `po_schedule_rule.round_type` | column |
| `first_date` | `po_schedule_rule.first_date` | column |
| `total_releases` | `po_schedule_rule.total_releases` | probed |
| `frequency_value` | `po_schedule_rule.frequency_value` | column |
| `frequency_type` | `po_schedule_rule.frequency_type` | column |
| `default_to_all` | `po_schedule_rule.default_to_all` | column |

| # | Label | table.column / expression |
|---|---|---|
| 2 | Release By: | `po_schedule_rule.release_type` |
| 3 | Round Quantity On: | `po_schedule_rule.round_type` |
| 4 | First Release Date: | `po_schedule_rule.first_date` |
| 5 | Total Releases: | `po_schedule_rule.total_releases` |
| 6 | Occurs Every: | `po_schedule_rule.frequency_value` |
| 7 | Frequency Type | `po_schedule_rule.frequency_type` |
| 8 | Default To All | `po_schedule_rule.default_to_all` |

### `SCHEDULE.po_schedule` (Schedule)

- Update table: `po_schedule`
- Tables in the SELECT: `po_schedule`

| Field | Stored in | Basis |
|---|---|---|
| `release_date` | `po_schedule.release_date` | column |
| `row_no` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 4 | Release Date | `po_schedule.release_date` |
| calc | Release Number | `getrow()` |

### `DOCUMENT_LINK.document_link` (Document Links)

- Update table: `document_link`
- Tables in the SELECT: `document_link`, `document_link_area`, `inv_mast`, `document_link_entity_req`

| Field | Stored in | Basis |
|---|---|---|
| `link_name` | `document_link.link_name` | column |
| `link_path` | `document_link.link_path` | column |
| `row_status_flag` | `document_link.row_status_flag` | probed |
| `mandatory_flag` | `document_link.mandatory_flag` | column |
| `user_print_flag` | computed: `'N'` | alias |
| `user_fax_flag` | computed: `'N'` | alias |
| `user_email_flag` | computed: `'N'` | alias |
| `outside_use_flag` | `document_link.outside_use_flag` | column |
| `send_outside_use_print_flag` | `document_link_entity_req.send_outside_use_print_flag` | alias |
| `document_link_uid` | `document_link.document_link_uid` | probed |
| `send_outside_use_email_flag` | `document_link_entity_req.send_outside_use_email_flag` | alias |
| `send_outside_use_fax_flag` | `document_link_entity_req.send_outside_use_fax_flag` | alias |
| `source_area_cd` | `document_link.source_area_cd` | column |
| `cf_rowind` | computed: `(computed in the datawindow)` | dw_name |
| `cf_keylist` | computed: `(computed in the datawindow)` | dw_name |
| `display_area` | computed: `(computed in the datawindow)` | probed |
| `cf_firstind` | computed: `(computed in the datawindow)` | dw_name |
| `cf_rowno` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Document Link Uid | `document_link.document_link_uid` |
| 2 | Source Area | `document_link.source_area_cd` |
| 9 | Link Name | `document_link.link_name` |
| 10 | Link Path | `document_link.link_path` |
| 11 | Status | `document_link.row_status_flag` |
| 24 | Outside Use | `document_link.outside_use_flag` |
| 25 | Mandatory | `document_link.mandatory_flag` |
| 26 | Print | `user_print_flag` |
| 27 | Fax | `user_fax_flag` |
| 28 | E-mail | `user_email_flag` |
| 36 | OU-Print | `document_link_entity_req.send_outside_use_print_flag` |
| 37 | OU-Fax | `document_link_entity_req.send_outside_use_fax_flag` |
| 38 | OU-Email | `document_link_entity_req.send_outside_use_email_flag` |
| calc | Document Linked to | `IF ( key2_cd = 'lot_cd', if(isnull(key2_value),'',key2_value), IF ( key1_cd = 'inv_mast_uid', if(isnull(item_id),'',item_id), if(isnull(key1_value),'',key1_value) ) + IF ( IsNull(key2_value), '', '/' + key2_value + IF ( IsNull(key3_value), '', '/' + key3_value)) )` |
| calc | Form | `if( display_area_cd = 2284, 'RFQ', '') + if(display_area_cd = 2285, 'PO','')  + if(display_area_cd = 709, 'Quote','') + if(display_area_cd = 999, 'Packing List','') + if(display_area_cd = 998, 'Order Acknowledgment','') + if(display_area_cd = 2750, 'Production Order','') + if(display_area_cd = 995, 'Invoice', '') + if(display_area_cd = 3376, 'Builder Selection Sheet', '') + if(display_area_cd = 3451, 'Service Order Parts Pick Tickets', '') + if(display_area_cd = 3452, 'Service Order Pick Tickets', '') + if(display_area_cd = 3453, 'Sales Order Pick Ticket', '')  + if(display_area_cd = 1319, 'Order Entry/RMA', '')` |

### `DOCUMENT_LINK.document_link_forms` (Document Links)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `display_area_cd` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Form: | `document_link_area.display_area_cd` |

### `TABPAGE_CONTACT.contacts` (Contacts)

- Update table: `contacts`
- Tables in the SELECT: `contacts`, `address`, `salutation`

| Field | Stored in | Basis |
|---|---|---|
| `id` | `contacts.id` | column |
| `salutation` | `contacts.salutation` | column |
| `first_name` | `contacts.first_name` | column |
| `mi` | `contacts.mi` | column |
| `last_name` | `contacts.last_name` | column |
| `title` | `contacts.title` | column |
| `address_id` | `contacts.address_id` | column |
| `use_supplier_address` | computed: `' '` | alias |
| `address_name` | `contacts.address_name` | column |
| `mail_address1` | `address.mail_address1` | column |
| `mail_address2` | `address.mail_address2` | column |
| `mail_city` | `address.mail_city` | column |
| `mail_state` | `address.mail_state` | column |
| `mail_postal_code` | `address.mail_postal_code` | column |
| `mail_country` | `address.mail_country` | column |
| `direct_phone` | `contacts.direct_phone` | column |
| `phone_ext` | `contacts.phone_ext` | column |
| `direct_fax` | `contacts.direct_fax` | column |
| `fax_ext` | `contacts.fax_ext` | column |
| `central_phone_number` | `address.central_phone_number` | column |
| `central_fax_number` | `address.central_fax_number` | column |
| `email_address` | `contacts.email_address` | column |
| `url` | `contacts.url` | column |
| `vendor_supplier_id` | computed: `0` | alias |
| `vendor_supplier_name` | computed: `' '` | alias |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Contact ID: | `contacts.id` |
| 2 | Address ID: | `contacts.address_id` |
| 3 | Salutation | `contacts.salutation` |
| 4 | First Name | `contacts.first_name` |
| 5 | Mi | `contacts.mi` |
| 6 | Last Name | `contacts.last_name` |
| 7 | Direct Phone: | `contacts.direct_phone` |
| 8 | Job Title: | `contacts.title` |
| 9 | Direct Fax: | `contacts.direct_fax` |
| 17 | Contact URL: | `contacts.url` |
| 18 | Contact Email: | `contacts.email_address` |
| 19 | Name: | `address.name` |
| 20 | Address: | `address.mail_address1` |
| 21 | Mail Address2 | `address.mail_address2` |
| 22 | City/State/Zip/Country: | `address.mail_city` |
| 23 | Mail State | `address.mail_state` |
| 24 | Mail Postal Code | `address.mail_postal_code` |
| 25 | Mail Country | `address.mail_country` |
| 26 | Central Phone: | `address.central_phone_number` |
| 27 | Fax: | `address.central_fax_number` |
| 29 | Use Supplier Address | `use_supplier_address` |
| 31 | Supplier ID: | `supplier.id` |
| 32 | Vendor Supplier Name | `address.name` |
| 39 | Phone Extension: | `contacts.phone_ext` |
| 40 | Fax Extension: | `contacts.fax_ext` |

### `TIMESTAMP.timestamp` (Audit Trail)

- Update table: `none (external source)`
- Mapped off-tab: the API could not select this tab (HTTP 400: Multiple tabs have a name or display text of TIMESTAMP.); SQL Information reads an instantiated datawindow whichever tab is active

| Field | Stored in | Basis |
|---|---|---|
| `date_created` | ? | no_sql |
| `date_last_modified` | ? | no_sql |
| `created_by` | ? | no_sql |
| `last_maintained_by` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Date Created: | `date_created` |
| 2 | Created By: | `created_by` |
| 3 | Date Last Modified: | `date_last_modified` |
| 4 | Last Maintained By: | `last_maintained_by` |
| 5 | Last Pricing Service Date: | `last_pricing_service_date` |

### `TIMESTAMP.audit_trail` (Audit Trail)

- Update table: `p21_view_audit_trail_po_hdr_<id>`
- Tables in the SELECT: `p21_view_audit_trail_po_hdr_<id>`
- Mapped off-tab: the API could not select this tab (HTTP 400: Multiple tabs have a name or display text of TIMESTAMP.); SQL Information reads an instantiated datawindow whichever tab is active

| Field | Stored in | Basis |
|---|---|---|
| `line_no` | `p21_view_audit_trail_po_hdr_<id>.line_no` | probed |
| `item_id` | `p21_view_audit_trail_po_hdr_<id>.item_id` | probed |
| `column_description` | `p21_view_audit_trail_po_hdr_<id>.column_description` | probed |
| `old_value` | `p21_view_audit_trail_po_hdr_<id>.old_value` | probed |
| `new_value` | `p21_view_audit_trail_po_hdr_<id>.new_value` | probed |
| `date_created` | `p21_view_audit_trail_po_hdr_<id>.date_created` | probed |
| `created_by` | `p21_view_audit_trail_po_hdr_<id>.created_by` | probed |
| `cf_display_key` | computed: `(computed in the datawindow)` | dw_name |
| `cf_sub_line_no` | computed: `(computed in the datawindow)` | dw_name |
| `cf_line_no_visible` | computed: `(computed in the datawindow)` | dw_name |
| `cf_item_id_visible` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 5 | Column Changed | `column_description` |
| 12 | Line No | `line_no` |
| 14 | Old Value | `old_value` |
| 15 | New Value | `new_value` |
| 18 | Date Created | `date_created` |
| 19 | Created By | `created_by` |
| 21 | 'Item IDIF (source_area_cd = 950, 'Process', IF(source_area_cd = 1302, 'Component ID', 'Item ID'))' | `item_id` |
| calc | Purchase Order No | `"IF ((source_area_cd = 1763 and key1_cd = 'service_labor_uid'), item_id,  IF (source_area_cd = 950, key1_value,  IF (key2_cd = 'item_service_uid',  Item_id + ' / ALL / ALL',  IF ( key2_cd = 'lot_cd', key2_value,   IF ( Len(auxiliary_value) > 0 AND source_area_cd IN (1544, 1250, 2531), auxiliary_value,  IF (source_area_cd = 1314 and table_changed = 'inv_mast_strategic_pricing', item_id + '/' + key3_value + IF (IsNull(key2_value), '', '/' + auxiliary_value),  IF ( key1_cd = 'inv_mast_uid', item_id, key1_value ) + IF ( IsNull ( key2_value) AND source_area_cd <> 1314, '', ' / ' + IF ( key2_cd = 'inv_mast_uid', item_id, IF ( IsNull ( key2_value ), 'ALL', key2_value ) )  + IF ( IsNull (key3_value) AND source_area_cd <> 1314, '', ' / ' + IF ( key3_cd = 'inv_mast_uid', item_id, IF ( IsNull ( key3_value ), 'ALL', key3_value ) ) ) )  ) ) ) ) ) )"` |
| calc | 'Sub Line No | `` |

### `TABPAGE_17.tp_17_dw_17` (Items)

- Update table: `po_line`
- Tables in the SELECT: `po_line`, `po_hdr`, `oe_line_po`, `oe_line`, `inv_mast`, `item_uom`, `inventory_supplier`, `vendor_rfq_line`, `tpcx_dead_stock`, `p21_view_total_qty_on_po_per_order_line`, `vessel_receipts_line`, `revision_transaction`, `item_revision`, `inv_loc`

| Field | Stored in | Basis |
|---|---|---|
| `line_no` | `po_line.line_no` | probed |
| `item_id` | `inv_mast.item_id` | probed |
| `unit_of_measure` | `po_line.unit_of_measure` | probed |
| `unit_quantity` | `po_line.unit_quantity` | probed |
| `pricing_unit` | `po_line.pricing_unit` | probed |
| `unit_price_display` | `po_line.unit_price_display` | probed |
| `extended_price` | computed: `CAST((po_line.unit_quantity * po_line.unit_size) * (po_line.unit_price_display / po_line.pricing_unit_size) AS Decimal(19,9))` | probed |
| `cancel_flag` | `po_line.cancel_flag` | probed |
| `delete_flag` | `po_line.delete_flag` | probed |
| `exclude_from_lead_time` | `po_line.exclude_from_lead_time` | probed |
| `trans_revision_level` | `item_revision.revision_level` | probed |
| `country_of_origin` | `po_line.country_of_origin` | probed |
| `b3_qty` | `po_line.b3_qty` | probed |
| `qty_ready_uom` | `po_line.qty_ready_uom` | probed |
| `unit_qty_ready` | `po_line.unit_qty_ready` | probed |
| `qty_break_sequence_no` | computed: `COALESCE(po_line.parent_po_line_no, po_line.line_no)` | probed |
| `parent_po_line_no` | `po_line.parent_po_line_no` | probed |
| `item_desc` | computed: `(CASE WHEN COALESCE(po_line.parent_po_line_no, po_line.line_no) = po_line.line_no THEN po_line.item_description ELSE 'Quantity Break' END)` | probed |
| `c_shipped_flag` | computed: `CASE WHEN supplier_ship_date IS NULL THEN 'N' ELSE 'Y' END` | probed |
| `supplier_ship_date` | `po_line.supplier_ship_date` | probed |
| `supplier_part_no` | `inventory_supplier.supplier_part_no` | probed |
| `complete` | `po_line.complete` | probed |
| `contract_number` | `po_line.contract_number` | probed |
| `total_pieces` | computed: `(computed in the datawindow)` | probed |
| `compute_extended_price` | computed: `(computed in the datawindow)` | probed |
| `item_total_weight` | computed: `(computed in the datawindow)` | probed |
| `last_line_no` | computed: `(computed in the datawindow)` | probed |
| `cf_total_units_purchased` | computed: `(computed in the datawindow)` | probed |
| `cf_skuprice` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | probed |
| `total_rows` | computed: `(computed in the datawindow)` | probed |
| `total_amount` | computed: `(computed in the datawindow)` | probed |
| `po_total_weight` | computed: `(computed in the datawindow)` | probed |
| `cf_total_volume` | computed: `(computed in the datawindow)` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Item ID | `inv_mast.item_id` |
| 3 | OrderUOM | `po_line.unit_of_measure` |
| 4 | Unit Price | `po_line.unit_price` |
| 10 | Delete | `po_line.delete_flag` |
| 11 | Complete | `po_line.complete` |
| 13 | Order Qty | `po_line.unit_quantity` |
| 14 | Line Number | `po_line.line_no` |
| 27 | Extended Price | `compute_0027` |
| 33 | Item Description | `po_line.item_description` |
| 35 | Cancel | `po_line.cancel_flag` |
| 38 | PriceUOM | `po_line.pricing_unit` |
| 40 | PO Price | `po_line.unit_price_display` |
| 50 | Exclude From Lead Time | `po_line.exclude_from_lead_time` |
| 61 | Supplier Part No | `inventory_supplier.supplier_part_no` |
| 63 | Contract Number | `po_line.contract_number` |
| 74 | Ack Ship Date | `po_line.supplier_ship_date` |
| 75 | Ack'd | `c_shipped_flag` |

### `TABPAGE_18.extended_info` (Extended Info )

- Update table: `po_line`
- Tables in the SELECT: `po_line`, `po_hdr`, `oe_line_po`, `oe_line`, `inv_mast`, `item_uom`, `inventory_supplier`, `vendor_rfq_line`, `tpcx_dead_stock`, `p21_view_total_qty_on_po_per_order_line`, `vessel_receipts_line`, `revision_transaction`, `item_revision`, `inv_loc`

| Field | Stored in | Basis |
|---|---|---|
| `supplier_part_no` | `inventory_supplier.supplier_part_no` | probed |
| `unit_quantity` | `po_line.unit_quantity` | probed |
| `unit_of_measure` | `po_line.unit_of_measure` | probed |
| `pricing_unit` | `po_line.pricing_unit` | probed |
| `unit_price_display` | `po_line.unit_price_display` | probed |
| `required_date` | `po_line.required_date` | probed |
| `cc_rfq_lead_time` | computed: `0` | probed |
| `date_due` | `po_line.date_due` | probed |
| `expected_ship_date` | `po_line.expected_ship_date` | probed |
| `supplier_ship_date` | `po_line.supplier_ship_date` | probed |
| `c_shipped_flag` | computed: `CASE WHEN supplier_ship_date IS NULL THEN 'N' ELSE 'Y' END` | probed |
| `extended_desc` | `po_line.extended_desc` | probed |
| `expedite_notes` | `po_line.expedite_notes` | probed |
| `computedummytosetfocus` | computed: `''` | probed |
| `acknowledged_date` | `po_line.acknowledged_date` | probed |
| `acknowledged` | `po_line.acknowledged` | probed |
| `item_id` | `inv_mast.item_id` | probed |
| `date_due_edited` | computed: `CASE WHEN po_line.date_due_last_modified IS NOT NULL THEN 'Y' ELSE 'N' END` | probed |
| `item_description` | computed: `(CASE WHEN COALESCE(po_line.parent_po_line_no, po_line.line_no) = po_line.line_no THEN po_line.item_description ELSE 'Quantity Break' END)` | probed |
| `source_type` | `po_line.source_type` | probed |
| `pricing_unit_size` | `po_line.pricing_unit_size` | probed |
| `unit_size` | `po_line.unit_size` | probed |
| `contract_number` | `po_line.contract_number` | probed |
| `cf_rowinfo` | computed: `(computed in the datawindow)` | probed |
| `c_unit_qty_received` | computed: `(computed in the datawindow)` | probed |
| `cf_has_mult_containers` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Item ID: | `inv_mast.item_id` |
| 3 | Order UOM: | `po_line.unit_of_measure` |
| 5 | Unit Size: | `po_line.unit_size` |
| 13 | Order Quantity: | `po_line.unit_quantity` |
| 15 | Extended Description: | `po_line.extended_desc` |
| 33 | Item Description | `po_line.item_description` |
| 38 | Pricing Unit: | `po_line.pricing_unit` |
| 39 | Unit Size: | `po_line.pricing_unit_size` |
| 40 | Unit Price: | `po_line.unit_price_display` |
| 45 | Expected Date: | `po_line.date_due` |
| 46 | Required Date: | `po_line.required_date` |
| 51 | Source: | `po_line.source_type` |
| 56 | Computedummytosetfocus | `ComputeDummyToSetFocus` |
| 60 | RFQ Lead Time: | `cc_rfq_lead_time` |
| 61 | Supplier Part Number: | `inventory_supplier.supplier_part_no` |
| 63 | Contract Number: | `po_line.contract_number` |
| 74 | Ack Ship Date: | `po_line.supplier_ship_date` |
| 75 | C Shipped Flag | `c_shipped_flag` |
| 88 | Expedite Notes: | `po_line.expedite_notes` |
| 89 | Acknowledged Date: | `po_line.acknowledged_date` |
| 99 | Date Due Edited | `date_due_edited` |
| 100 | Expected Ship Date: | `po_line.expected_ship_date` |
| 101 | Acknowledged | `po_line.acknowledged` |
| calc | Cf Rowinfo | `'Row ' + string(getrow()) + ' of ' + String(rowcount())` |
| calc | Quantity Received: | `"/* c_unit_qty_received */  qty_received / unit_size"` |

### `TABPAGE_19.price` (Price)

- Update table: `po_line`
- Tables in the SELECT: `po_line`, `po_hdr`, `oe_line_po`, `oe_line`, `inv_mast`, `item_uom`, `inventory_supplier`, `vendor_rfq_line`, `tpcx_dead_stock`, `p21_view_total_qty_on_po_per_order_line`, `vessel_receipts_line`, `revision_transaction`, `item_revision`, `inv_loc`

| Field | Stored in | Basis |
|---|---|---|
| `unit_quantity` | `po_line.unit_quantity` | column |
| `unit_of_measure` | `po_line.unit_of_measure` | column |
| `unit_price_display` | `po_line.unit_price_display` | column |
| `pricing_unit` | `po_line.pricing_unit` | column |
| `extended_price` | computed: `CAST((po_line.unit_quantity * po_line.unit_size) * (po_line.unit_price_display / po_line.pricing_unit_size) AS Decimal(19,9))` | probed |
| `contract_number` | `po_line.contract_number` | column |
| `computedummytosetfocus` | computed: `''` | probed |
| `base_unit_price_display` | computed: `0.0000` | probed |
| `calc_type` | `po_line.calc_type` | column |
| `calc_value` | `po_line.calc_value` | column |
| `item_id` | `inv_mast.item_id` | column |
| `pricing_book_supplier_id` | `po_line.pricing_book_supplier_id` | column |
| `combinable` | `po_line.combinable` | probed |
| `next_unit_price_display` | computed: `0.0000` | probed |
| `pricing_book_disc_grp_id` | `po_line.pricing_book_disc_grp_id` | column |
| `pricing_book_effective_date` | `po_line.pricing_book_effective_date` | column |
| `next_break` | `po_line.next_break` | column |
| `item_description` | computed: `(CASE WHEN COALESCE(po_line.parent_po_line_no, po_line.line_no) = po_line.line_no THEN po_line.item_description ELSE 'Quantity Break' END)` | alias |
| `unit_size` | `po_line.unit_size` | column |
| `pricing_unit_size` | `po_line.pricing_unit_size` | column |
| `price_edit` | `po_line.price_edit` | column |
| `cf_rowinfo` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Item ID: | `inv_mast.item_id` |
| 3 | Order UOM: | `po_line.unit_of_measure` |
| 5 | Unit Size: | `po_line.unit_size` |
| 13 | Order Quantity: | `po_line.unit_quantity` |
| 19 | Calculation Type: | `po_line.calc_type` |
| 20 | Calculation Value: | `po_line.calc_value` |
| 21 | Combinable | `po_line.combinable` |
| 22 | Supplier ID: | `po_line.pricing_book_supplier_id` |
| 23 | Discount Group ID: | `po_line.pricing_book_disc_grp_id` |
| 24 | Effective Date: | `po_line.pricing_book_effective_date` |
| 27 | Extended Price: | `compute_0027` |
| 29 | Next Break: | `po_line.next_break` |
| 32 | Price Edit | `po_line.price_edit` |
| 33 | Item Description | `po_line.item_description` |
| 38 | Pricing UOM: | `po_line.pricing_unit` |
| 39 | Unit Size: | `po_line.pricing_unit_size` |
| 40 | Net Unit Price: | `po_line.unit_price_display` |
| 42 | Base Unit Price: | `compute_0043` |
| 43 | Next Unit Price: | `compute_0044` |
| 63 | Contract Number: | `po_line.contract_number` |
| calc | Cf Rowinfo | `'Row ' + string(GetRow(),"#,##0") + ' of ' + string(RowCount(),"#,##0")` |

### `TABPAGE_21.tp_21_dw_21` (PO Line Notes)

- Update table: `po_line_notepad`
- Tables in the SELECT: `po_line_notepad`, `note_area`, `notepad_class`

| Field | Stored in | Basis |
|---|---|---|
| `note` | `po_line_notepad.note` | probed |
| `note_id` | `po_line_notepad.note_id` | column |
| `topic` | `po_line_notepad.topic` | probed |
| `notepad_class_desc` | `notepad_class.notepad_class_desc` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Note ID | `po_line_notepad.note_id` |
| 5 | Topic | `po_line_notepad.topic` |
| 6 | Note | `po_line_notepad.note` |
| 15 | Class | `notepad_class.notepad_class_desc` |

### `COMMITMENT_SCHEDULE.commitment_schedule_detail` (Commitment Schedule)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `transaction_date` | ? | no_sql |
| `transaction_number` | ? | no_sql |
| `trans_type` | ? | no_sql |
| `release_qty` | ? | no_sql |
| `allocated_qty` | ? | no_sql |
| `duein_qty` | ? | no_sql |
| `promise_date` | ? | no_sql |
| `rowfocusindicatorcol` | ? | no_sql |
| `net_stock` | ? | no_sql |
| `c_netstockadd` | ? | no_sql |
| `cf_dfflag` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 3 | Exp/Rel Date | `transaction_date` |
| 4 | Transaction Number | `transaction_number` |
| 5 | Trans Type | `trans_type` |
| 6 | Release Qty | `release_qty` |
| 7 | Allocated Qty | `allocated_qty` |
| 8 | Due In Qty | `DueIn_Qty` |
| 19 | Promise Date | `promise_date` |
| calc | Net Stock | `qty_on_hand - qty_allocated + cumulativeSum( duein_qty - release_qty + allocated_qty) - qty_quarantined` |

### `COMMITMENT_SCHEDULE.commitment_schedule_header` (Commitment Schedule)

- Update table: `inv_loc`
- Tables in the SELECT: `inv_loc`, `inv_mast`, `location`, `p21_view_supplier_purchasing_info`, `inv_loc_stock_status`

| Field | Stored in | Basis |
|---|---|---|
| `location_id` | `inv_loc.location_id` | column |
| `apply_look_ahead_days` | computed: `'N'` | alias |
| `item_id` | `inv_mast.item_id` | column |
| `location_name` | `location.location_name` | column |
| `item_desc` | `inv_mast.item_desc` | column |
| `lead_time_source` | `p21_view_supplier_purchasing_info.lead_time_source` | probed |
| `lead_time` | computed: `COALESCE(CAST(p21_view_supplier_purchasing_info.average_lead_time AS char), 'N/A')` | probed |
| `qty_available` | computed: `(computed in the datawindow)` | probed |
| `c_net_stock_total` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Item ID: | `inv_mast.item_id` |
| 2 | Item Desc | `inv_mast.item_desc` |
| 3 | Location ID: | `inv_loc.location_id` |
| 4 | Location Name | `location.location_name` |
| 12 | Lead Time Source: | `p21_view_supplier_purchasing_info.lead_time_source` |
| 14 | Lead Time: | `p21_view_supplier_purchasing_info.lead_time` |
| calc | Qty Available: | `qty_on_hand -  qty_allocated - qty_non_pickable - qty_quarantined - qty_frozen` |
| calc | Net Stock: | `"qty_on_hand -  qty_allocated - qty_quarantined - qty_backordered +  qty_in_transit +  order_quantity + c_netstockadd  // Net stock = Qty on Hand - Qty Allocated - Qty Unallocated + Transfers + Qty on PO  // Qty Unallocated == qty_backordered  // Qty on PO == inv_loc.order_quantity + unapproved po qty (which is zero, since we automatically don't include unapproved pos)  // c_netstockadd - the qty coming in from production orders isn't included in the above equation, but is included in the d_dw_commitment_schedule.  So, this will be added in manually.  // Sc 926402: subtract quantined quantity from net stock calc"` |

### `RELEASE_SCHEDULE.po_line_schedule_item` (Release Schedule)

- Update table: `po_line_schedule`
- Tables in the SELECT: `po_line_schedule`, `po_line`, `inv_mast`

| Field | Stored in | Basis |
|---|---|---|
| `item_id` | `inv_mast.item_id` | column |
| `item_desc` | `inv_mast.item_desc` | column |
| `unit_qty_ordered` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 22 | Item ID: | `inv_mast.item_id` |
| 23 | Item Desc | `inv_mast.item_desc` |
| calc | Quantity Ordered: | `unit_quantity` |

### `RELEASE_SCHEDULE.po_line_schedule` (Release Schedule)

- Update table: `po_line_schedule`
- Tables in the SELECT: `po_line_schedule`, `po_line`, `inv_mast`

| Field | Stored in | Basis |
|---|---|---|
| `release_date` | `po_line_schedule.release_date` | column |
| `unit_release_qty` | computed: `CAST(po_line_schedule.release_qty/po_line.unit_size AS Decimal(19,9))` | alias |
| `row_status_flag` | `po_line_schedule.row_status_flag` | column |
| `unit_qty_ready` | computed: `po_line_schedule.qty_ready/po_line.unit_size` | alias |
| `unit_of_measure` | `po_line.unit_of_measure` | column |
| `rowind` | computed: `(computed in the datawindow)` | dw_name |
| `row_no` | computed: `(computed in the datawindow)` | dw_name |
| `unit_received` | computed: `(computed in the datawindow)` | probed |
| `unit_qty_due` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |
| `compute_1` | computed: `(computed in the datawindow)` | dw_name |
| `compute_4` | computed: `(computed in the datawindow)` | dw_name |
| `compute_2` | computed: `(computed in the datawindow)` | dw_name |
| `compute_3` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 4 | Release Date | `po_line_schedule.release_date` |
| 5 | Unit Release Qty | `unit_release_qty` |
| 10 | Release Status | `po_line_schedule.row_status_flag` |
| 20 | Unit Of Measure | `po_line.unit_of_measure` |
| calc | Release Number | `getrow()` |
| calc | Quantity Received | `qty_received /  unit_size` |
| calc | Quantity Due | `if( IsNull(unit_release_qty -  unit_received) or unit_release_qty -  unit_received < 0, 0, unit_release_qty -  unit_received)` |

### `TABPAGE_LANDED_COST_DETAIL.tabpage_landed_cost_detail` (Landed Cost)

- Update table: `lc_driver_x_tran_detail`
- Tables in the SELECT: `lc_driver_x_tran_detail`, `lc_driver_x_tran`, `po_line`, `inv_mast`, `landed_cost_driver`, `landed_cost_category`, `currency_line`, `landed_cost_driver_tax`

| Field | Stored in | Basis |
|---|---|---|
| `item_id` | `inv_mast.item_id` | column |
| `item_desc` | `inv_mast.item_desc` | probed |
| `landed_cost_driver_cd` | `landed_cost_driver.landed_cost_driver_cd` | column |
| `landed_cost_driver_desc` | `landed_cost_driver.landed_cost_driver_desc` | column |
| `line_no` | `lc_driver_x_tran_detail.line_no` | column |
| `tax_driver_flag` | `landed_cost_driver_tax.tax_driver_flag` | column |
| `multiplier` | `lc_driver_x_tran.multiplier` | column |
| `calculation_method` | `lc_driver_x_tran.calculation_method_code_no` | probed |
| `dollar_amount` | `lc_driver_x_tran.dollar_amount` | column |
| `landed_cost_amt` | `lc_driver_x_tran_detail.landed_cost_amt` | column |
| `cf_duty_amount_home` | computed: `(computed in the datawindow)` | dw_name |
| `cf_duty_amount` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_landed_cost_amount` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_itemlandedcost_display` | computed: `(computed in the datawindow)` | dw_name |
| `cf_sum_duty_amount` | computed: `(computed in the datawindow)` | dw_name |
| `cf_sum_total_landed_cost_amount` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_landedcost_display` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |
| `cf_zero` | computed: `(computed in the datawindow)` | dw_name |
| `cf_fisrtofgroupflag` | computed: `(computed in the datawindow)` | dw_name |
| `cf_visibleflag` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_landedcost` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_itemlandedcost` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 6 | Landed CostAmount | `lc_driver_x_tran_detail.landed_cost_amt` |
| 12 | Calculation Method | `lc_driver_x_tran.calculation_method_code_no` |
| 13 | Multiplier | `lc_driver_x_tran.multiplier` |
| 14 | Dollar Amount | `lc_driver_x_tran.dollar_amount` |
| 15 | Landed CostDriver | `landed_cost_driver.landed_cost_driver_cd` |
| 16 | Landed Cost Driver Description | `landed_cost_driver.landed_cost_driver_desc` |
| 18 | Item ID | `inv_mast.item_id` |
| 19 | Item Description | `inv_mast.item_desc` |
| 21 | Tax | `landed_cost_driver_tax.tax_driver_flag` |
| calc | Cf Duty Amount Home | `IF ( duty_flag = 'Y' AND  duty_percentage >= 0, landed_cost_amt_home * (duty_percentage / 100), 0)` |

### `DOCUMENT_LINK_DETAIL.document_link_detail_detail` (Document Links)

- Update table: `document_link`
- Tables in the SELECT: `document_link`, `document_link_area`, `inv_mast`, `document_link_entity_req`

| Field | Stored in | Basis |
|---|---|---|
| `link_name` | `document_link.link_name` | column |
| `link_path` | `document_link.link_path` | column |
| `row_status_flag` | `document_link.row_status_flag` | column |
| `mandatory_flag` | `document_link.mandatory_flag` | column |
| `user_print_flag` | computed: `'N'` | alias |
| `user_fax_flag` | computed: `'N'` | alias |
| `user_email_flag` | computed: `'N'` | probed |
| `outside_use_flag` | `document_link.outside_use_flag` | column |
| `send_outside_use_print_flag` | `document_link_entity_req.send_outside_use_print_flag` | probed |
| `document_link_uid` | `document_link.document_link_uid` | probed |
| `send_outside_use_email_flag` | `document_link_entity_req.send_outside_use_email_flag` | alias |
| `send_outside_use_fax_flag` | `document_link_entity_req.send_outside_use_fax_flag` | alias |
| `source_area_cd` | `document_link.source_area_cd` | probed |
| `cf_rowind` | computed: `(computed in the datawindow)` | dw_name |
| `cf_keylist` | computed: `(computed in the datawindow)` | dw_name |
| `display_area` | computed: `(computed in the datawindow)` | probed |
| `cf_firstind` | computed: `(computed in the datawindow)` | dw_name |
| `cf_rowno` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Document Link Uid | `document_link.document_link_uid` |
| 2 | Source Area | `document_link.source_area_cd` |
| 9 | Link Name | `document_link.link_name` |
| 10 | Link Path | `document_link.link_path` |
| 11 | Status | `document_link.row_status_flag` |
| 24 | Outside Use | `document_link.outside_use_flag` |
| 25 | Mandatory | `document_link.mandatory_flag` |
| 26 | Print | `user_print_flag` |
| 27 | Fax | `user_fax_flag` |
| 28 | E-mail | `user_email_flag` |
| 36 | OU-Print | `document_link_entity_req.send_outside_use_print_flag` |
| 37 | OU-Fax | `document_link_entity_req.send_outside_use_fax_flag` |
| 38 | OU-Email | `document_link_entity_req.send_outside_use_email_flag` |
| calc | Document Linked to | `IF ( key2_cd = 'lot_cd', if(isnull(key2_value),'',key2_value), IF ( key1_cd = 'inv_mast_uid', if(isnull(item_id),'',item_id), if(isnull(key1_value),'',key1_value) ) + IF ( IsNull(key2_value), '', '/' + key2_value + IF ( IsNull(key3_value), '', '/' + key3_value)) )` |
| calc | Form | `if( display_area_cd = 2284, 'RFQ', '') + if(display_area_cd = 2285, 'PO','')  + if(display_area_cd = 709, 'Quote','') + if(display_area_cd = 999, 'Packing List','') + if(display_area_cd = 998, 'Order Acknowledgment','') + if(display_area_cd = 2750, 'Production Order','') + if(display_area_cd = 995, 'Invoice', '') + if(display_area_cd = 3376, 'Builder Selection Sheet', '') + if(display_area_cd = 3451, 'Service Order Parts Pick Tickets', '') + if(display_area_cd = 3452, 'Service Order Pick Tickets', '') + if(display_area_cd = 3453, 'Sales Order Pick Ticket', '')  + if(display_area_cd = 1319, 'Order Entry/RMA', '')` |

### `PURCHASEHISTORY.po_history` (Purchase History)

- Update table: `none reported` (tool reported 'clause*/' (misparse of SQL comments; treat as unknown))
- Tables in the SELECT: `po_hdr`, `po_line`, `supplier`, `vendor_rfq_hdr`, `inv_mast`, `vessel_receipts_line`, `vessel_receipts_hdr`

| Field | Stored in | Basis |
|---|---|---|
| `supplier_id` | `po_hdr.supplier_id` | probed |
| `supplier_name` | `supplier.supplier_name` | column |
| `po_no` | `po_hdr.po_no` | column |
| `order_date` | `po_hdr.order_date` | column |
| `qty_ordered` | computed: `CAST(po_line.qty_ordered / po_line.unit_size AS Decimal(19,9))` | alias |
| `qty_on_vessel` | computed: `COALESCE(vessel_receipts.sum_qty_on_vessel, 0) / po_line.unit_size` | alias |
| `qty_received` | computed: `CAST(po_line.qty_received / po_line.unit_size AS Decimal(19,9))` | alias |
| `unit_of_measure` | `po_line.unit_of_measure` | column |
| `unit_price_display` | `po_line.unit_price_display` | column |
| `received_date` | `po_line.received_date` | column |
| `cancel_flag` | `po_line.cancel_flag` | column |
| `complete` | `po_line.complete` | column |
| `location_id` | `po_hdr.location_id` | column |
| `po_hdr_po_type` | computed: `COALESCE(po_line.line_type, po_hdr.po_type)` | probed |
| `space` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 2 | Supplier ID | `po_hdr.supplier_id` |
| 3 | Supplier Name | `supplier.supplier_name` |
| 4 | PurchaseOrder | `po_hdr.po_no` |
| 5 | OrderDate | `po_hdr.order_date` |
| 6 | QuantityOrdered | `po_line.qty_ordered` |
| 7 | QuantityReceived | `po_line.qty_received` |
| 8 | Unit ofMeasure | `po_line.unit_of_measure` |
| 10 | ReceivedDate | `po_line.received_date` |
| 11 | Cancel | `po_line.cancel_flag` |
| 12 | Complete | `po_line.complete` |
| 13 | LocationID | `po_hdr.location_id` |
| 14 | PurchaseOrder Type | `po_hdr.po_type` |
| 16 | Qty InVessel | `qty_on_vessel` |
| 17 | UnitPrice | `po_line.unit_price_display` |

### `TIMESTAMPDETAIL.timestampdetail` (Timestamp)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `date_created` | ? | no_sql |
| `date_last_modified` | ? | no_sql |
| `created_by` | ? | no_sql |
| `last_maintained_by` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Date Created: | `date_created` |
| 2 | Created By: | `created_by` |
| 3 | Date Last Modified: | `date_last_modified` |
| 4 | Last Maintained By: | `last_maintained_by` |
| 5 | Last Pricing Service Date: | `last_pricing_service_date` |

## Unreachable

| Tab | Caption | Datawindow | Reason |
|---|---|---|---|
| `TABPAGE_4` | Pricing | `tp_4_dw_library` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_8` | Supplier Notes | `tp_8_dw_8` | datawindow never instantiated (tab not enabled) |
| `VENDOR_RFQ_HDR` | Vendor RFQ | `vendor_rfq_hdr` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_ORDER_NOTES` | Order Notes | `order notes` | datawindow never instantiated (tab not enabled) |
| `PROD_ORDER_HDR_NOTE_TAB` | Production Order Notes | `prod_order_hdr_note_tab` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_20` | Item Notes | `tp_20_dw_20` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_22` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_23` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_24` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `DOCUMENT_LINK_DETAIL` | Document Links | `document_link_forms` | datawindow never instantiated (tab not enabled) |
| `BACKORDERS` | Backorders | `links_for_po_hdr` | datawindow never instantiated (tab not enabled) |
| `BACKORDERS` | Backorders | `links_for_po` | datawindow never instantiated (tab not enabled) |
| `VENDOR_RFQ_LINE` | Vendor RFQ Line | `vendor_rfq_line` | datawindow never instantiated (tab not enabled) |
| `ORDER_LINE_NOTES` | Order Line Note | `order_line_notes` | datawindow never instantiated (tab not enabled) |
| `PROD_ORDER_LINE_NOTE_TAB` | Production Order Line Notes | `prod_order_line_note_tab` | datawindow never instantiated (tab not enabled) |
| `PROCESS_INFO` | Process Info | `process_info` | datawindow never instantiated (tab not enabled) |
| `TIMESTAMPDETAIL` | Timestamp | `timestampdetail_dw_audittrail` | datawindow never instantiated (tab not enabled) |
