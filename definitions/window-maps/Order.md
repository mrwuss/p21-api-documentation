# Order Entry (`Order`)

- Window class: `w_order_entry_sheet`; menu class: `m_orderentry`
- Tabs: 84; datawindows mapped: 75; unreachable entries: 41

## Tab overview

| Tab | Caption | Datawindows mapped | Tables in the SELECT |
|---|---|---|---|
| `TABPAGE_1` | Order | `order` | address, carrier_contract_hdr, company, country_subdivision, crm_contact_information, currency_line, customer, freight_code, invoice_batch, oe_hdr, oe_hdr_integration, oe_hdr_notepad, p21_view_oe_hdr_rfq_control_no, pegmost_oe_hdr, quote_hdr, ship_to, shipping_route, users |
| `TP_CUSTOMER` | Customer | `tp_customer` | address, corp_id, customer, lead_source |
| `TP_CONTACTS` | Contacts | `tp_contacts` | address, company, contacts, salutation |
| `TP_SHIPTO` | Ship To | `shipto` | address, carrier_contract_hdr, company, country_subdivision, crm_contact_information, currency_line, customer, freight_code, invoice_batch, oe_hdr, oe_hdr_integration, oe_hdr_notepad, p21_view_oe_hdr_rfq_control_no, pegmost_oe_hdr, quote_hdr, ship_to, shipping_route, users |
| `TP_REMITTANCES` | Remittances | `tp_remittances`, `remittances`, `remittotals` | address, ar_payment_details, carrier_contract_hdr, check_payment_details, company, country_subdivision, crm_contact_information, currency_hdr, currency_line, customer, epf_transaction_detail, freight_code, invoice_batch, oe_hdr, oe_hdr_integration, oe_hdr_notepad, oe_line, p21_view_ar_payment_details, p21_view_creditcard_payment_details, p21_view_oe_hdr_rfq_control_no, payment_account, payment_account_x_transaction, payment_types, pegmost_oe_hdr, quote_hdr, remittances, ship_to, shipping_route, users |
| `TP_TOTALS` | Totals | `tp_totals` | oe_line |
| `TP_FRONTCOUNTER` | Front Counter | `tp_frontcounter` |  |
| `HDR_NOTE` | Order Notes | `hdr_note` | note_area, notepad_class, oe_hdr_notepad |
| `TP_SHIPINFO` | Ship Info | `shipinfo` | address, carrier_contract_hdr, company, country_subdivision, crm_contact_information, currency_line, customer, freight_code, invoice_batch, oe_hdr, oe_hdr_integration, oe_hdr_notepad, p21_view_oe_hdr_rfq_control_no, pegmost_oe_hdr, quote_hdr, ship_to, shipping_route, users |
| `TP_TAX` | Tax | `tp_tax`, `tp_tax_dw_2` | address, carrier_contract_hdr, company, country_subdivision, crm_contact_information, currency_line, customer, freight_code, invoice_batch, oe_hdr, oe_hdr_integration, oe_hdr_notepad, oe_hdr_tax, p21_view_oe_hdr_rfq_control_no, pegmost_oe_hdr, quote_hdr, ship_to, shipping_route, tax_jurisdiction, users |
| `CUSTOMERNOTESTABPG` | Customer Notes | `customernotestabpg` | customer_notepad, note_area, notepad_class |
| `TP_WAREHOUSEACTIVITY` | Warehouse Activity | `warehouse_activity` | group_pick_ticket_detail, group_pick_ticket_hdr, location, oe_hdr, oe_pick_ticket |
| `TP_SALESREPS` | Salesreps | `tp_salesreps` | contacts, oe_hdr_salesrep, salesrep_commission_class, salutation |
| `TP_CREDIT` | Credit | `tp_credit` | address, corp_id, customer, lead_source |
| `TP_PRICING` | Pricing | `pricing_hdr`, `pricing_detail` | address, corp_id, customer, lead_source, price_library, price_library_x_cust_x_cmpy |
| `TP_TERMS` | Terms | `terms`, `tp_terms_dw_2` | address, carrier_contract_hdr, company, country_subdivision, crm_contact_information, currency_line, customer, freight_code, invoice_batch, oe_hdr, oe_hdr_integration, oe_hdr_notepad, p21_view_oe_hdr_rfq_control_no, pegmost_oe_hdr, quote_hdr, ship_to, shipping_route, terms, users |
| `TP_HDRPROMISEDATES` | Promise Dates | `tp_hdrpromisedates` | address, carrier_contract_hdr, company, country_subdivision, crm_contact_information, currency_line, customer, freight_code, invoice_batch, oe_hdr, oe_hdr_integration, oe_hdr_notepad, p21_view_oe_hdr_rfq_control_no, pegmost_oe_hdr, quote_hdr, ship_to, shipping_route, users |
| `TP_SHIPMENTS` | Shipments | `tp_shipments` | address, code_p21, company_strategic_pricing, contacts, freight_code, invoice_hdr, location, oe_hdr, oe_line, oe_line_lot_billing, oe_pick_ticket, oe_pick_ticket_detail, oe_pick_ticket_ups, p21_view_clippership_return_<id>, shipment, shipping_route, system_setting |
| `TP_CLASS` | Classes | `tp_class` | address, carrier_contract_hdr, company, country_subdivision, crm_contact_information, currency_line, customer, freight_code, invoice_batch, oe_hdr, oe_hdr_integration, oe_hdr_notepad, p21_view_oe_hdr_rfq_control_no, pegmost_oe_hdr, quote_hdr, ship_to, shipping_route, users |
| `TP_AGING` | Aging | `tp_aging` |  |
| `TP_CUSTSALESHISTORY` | Customer Sales History | `filter_components`, `start_date`, `customer_sales_history` | currency_line, customer, inv_mast, invoice_hdr, invoice_line, invoice_line_taxes, item_uom, job_price_hdr, job_price_line, oe_hdr, system_setting |
| `TP_SCHEDULE` | Release Schedule | `schedule_hdr`, `schedule_detail` | oe_schedule, oe_schedule_detail |
| `TP_STRATEGICPRICING` | Strategic Pricing | `tp_strategicpricing` | code_p21, customer_category, oe_hdr, price_library |
| `OPPORTUNITIES` | Opportunities | `opportunities` | opportunity, opportunity_x_order |
| `DOCUMENT_LINK` | Document Links | `document_link`, `document_link_forms` | document_link, document_link_area, document_link_entity_req, inv_mast |
| `TP_TASKS` | Tasks | `oe_hdr_tasks_access`, `oe_hdr_tasks` | activity, activity_trans, alarm_code, contacts, inv_mast, oe_hdr, problem_code, serial_number |
| `TP_TRANS_X_GL_DIMENSION` | GL Dimensions | `tp_trans_x_gl_dimension` | gl_dimen_type, trans_x_gl_dimension |
| `TP_SHIPTOPRICING` | Ship To Pricing | `ship_to_pricing_hdr`, `ship_to_pricing_detail` | price_library, price_library_x_ship_to, ship_to |
| `TIMESTAMP` | Audit Trail | `timestamp`, `audit_trail` | p21_view_audit_trail_oe_hdr_<id> |
| `TP_ITEMS` | Items | `items` | address, carrier_contract_line, carrier_contract_z_line, inv_loc, inv_loc_stock_status, inv_mast, inv_mast_assem_info, inventory_supplier, inventory_supplier_x_loc, invoice_line, item_revision, item_uom, job_price_line, oe_hdr, oe_line, oe_line_hose_assembly, oe_line_labor, oe_line_last_margin_price, oe_line_lot_billing, oe_line_notepad, oe_line_po, oe_line_promise_date, oe_line_rma, oe_line_room, operation, p21_view_getrevisionlotquantity, p21_view_oe_line_anticipated_allocation_summary, price_family, price_page, product_group, restricted_class, revision_transaction, room, room_area, service_labor, shipping_route, supplier, tpcx_dead_stock, transfer_hdr |
| `TP_EXTDINFO` | Ext'd Info | `extd_info` | address, carrier_contract_line, carrier_contract_z_line, inv_loc, inv_loc_stock_status, inv_mast, inv_mast_assem_info, inventory_supplier, inventory_supplier_x_loc, invoice_line, item_revision, item_uom, job_price_line, oe_hdr, oe_line, oe_line_hose_assembly, oe_line_labor, oe_line_last_margin_price, oe_line_lot_billing, oe_line_notepad, oe_line_po, oe_line_promise_date, oe_line_rma, oe_line_room, operation, p21_view_getrevisionlotquantity, p21_view_oe_line_anticipated_allocation_summary, price_family, price_page, product_group, restricted_class, revision_transaction, room, room_area, service_labor, shipping_route, supplier, tpcx_dead_stock, transfer_hdr |
| `TP_PRICES` | Prices | `prices`, `price_page`, `contract_info` | address, carrier_contract_line, carrier_contract_z_line, inv_loc, inv_loc_stock_status, inv_mast, inv_mast_assem_info, inventory_supplier, inventory_supplier_x_loc, invoice_line, item_revision, item_uom, job_price_line, oe_hdr, oe_line, oe_line_hose_assembly, oe_line_labor, oe_line_last_margin_price, oe_line_lot_billing, oe_line_notepad, oe_line_po, oe_line_promise_date, oe_line_rma, oe_line_room, operation, p21_view_getrevisionlotquantity, p21_view_oe_line_anticipated_allocation_summary, price_family, price_page, product_group, restricted_class, revision_transaction, room, room_area, service_labor, shipping_route, supplier, tpcx_dead_stock, transfer_hdr |
| `LINE_NOTE` | Order Line Notes | `line_note` | note_area, notepad_class, oe_line_notepad |
| `TABPAGE_LINE_TAX` | Taxes | `tabpage_line_tax` | inv_mast, invoice_line, invoice_line_taxes, oe_line, oe_line_rma, oe_line_tax, tax_jurisdiction |
| `TABPAGE_COST` | Costs | `costs` | address, carrier_contract_line, carrier_contract_z_line, inv_loc, inv_loc_stock_status, inv_mast, inv_mast_assem_info, inventory_supplier, inventory_supplier_x_loc, invoice_line, item_revision, item_uom, job_price_line, oe_hdr, oe_line, oe_line_hose_assembly, oe_line_labor, oe_line_last_margin_price, oe_line_lot_billing, oe_line_notepad, oe_line_po, oe_line_promise_date, oe_line_rma, oe_line_room, operation, p21_view_getrevisionlotquantity, p21_view_oe_line_anticipated_allocation_summary, price_family, price_page, product_group, restricted_class, revision_transaction, room, room_area, service_labor, shipping_route, supplier, tpcx_dead_stock, transfer_hdr |
| `TABPAGE_RELEASE` | Schedules | `tabpage_release` | inv_mast, oe_line, oe_line_schedule |
| `TABPAGE_LOT` | Lot | `tabpage_lot` | document_line_lot |
| `TP_ITEMNOTES` | Item Notes | `tp_itemnotes` | code_p21, note, note_area, notepad_class |
| `COMMITMENT_SCHEDULE` | Commitment Schedule | `commitment_schedule_detail`, `commitment_schedule_header` | inv_loc, inv_loc_stock_status, inv_mast, location, p21_view_supplier_purchasing_info |
| `TABPAGE_ASSMOPTIONS` | Assembly Options | `assmoptions` | assembly_hdr, inv_mast |
| `BUY_SELL_HISTORY` | Buy/Sell | `buy_sell_history_past_sell_prices_hdr`, `buy_sell_history_past_sell_prices`, `buy_sell_history_past_costs_hdr`, `buy_sell_history_past_costs` | currency_line, inv_mast, oe_hdr, oe_line |
| `TABPAGE_POS` | POs | `tabpage_pos`, `tabpage_pos_hdr` | address, inv_mast, inventory_supplier, inventory_supplier_x_loc, item_uom, oe_line_po, po_hdr, po_line, po_line_schedule, supplier, system_setting, vendor_rfq_hdr, vendor_rfq_hdr_x_po_hdr, vendor_rfq_line, vessel_receipts_container, vessel_receipts_hdr, vessel_receipts_line |
| `TP_LINEPROMISEDATE` | Promise Dates | `tp_linepromisedate` | inv_mast, oe_line, oe_line_promise_date |
| `TABPAGE_TRANSFERS` | Transfers | `tabpage_transfers` | inv_mast, location, oe_line_po, transfer_hdr, transfer_line |
| `TABPAGE_LINESHIPMENT` | Item Shipments | `tabpage_lineshipment` | clippership_return_<id>, code_p21, customer_terms, oe_hdr, oe_line, oe_pick_ticket, oe_pick_ticket_detail, p21_view_shipped_ups_package_details, product_group, shipment |
| `TABPAGE_STOCK` | Stock Avail | `stock_avail`, `checkbox` | address, inv_loc, inv_loc_stock_status, inv_mast, item_uom, location, po_hdr, po_line, transfer_days, vessel_receipts_hdr, vessel_receipts_line |
| `TABPAGE_POSXFERS` | POs/Xfers | `posxfers_hdr`, `posxfers` | address, company, inv_mast, inventory_supplier, inventory_supplier_x_loc, oe_line_po, po_hdr, po_line, po_line_schedule, supplier, transfer_hdr, transfer_line, vendor_rfq_hdr, vendor_rfq_hdr_x_po_hdr, vendor_rfq_line, vessel_receipts_container, vessel_receipts_hdr, vessel_receipts_line |
| `TABPAGE_ORDERS` | Orders | `open_orders_checkbox`, `open_orders` | address, inv_mast, item_uom, oe_hdr, oe_line, system_setting |
| `TABPAGE_SALESHISTORY` | Sales History | `tabpage_saleshistory`, `external` | currency_line, customer, inv_mast, invoice_hdr, invoice_line, invoice_line_taxes, item_uom, job_price_hdr, job_price_line, oe_hdr, rebill_invoice_reason, system_setting |
| `TABPAGE_PRODUCTIONORDER` | Production Order | `tabpage_productionorder` | oe_line, oe_line_schedule, prod_order_hdr, prod_order_line, prod_order_line_link |
| `DOCUMENT_LINK_DETAIL` | Document Links | `document_link_detail_detail` | document_link, document_link_area, document_link_entity_req, inv_mast, ship_to |
| `TIMESTAMPDETAIL` | Timestamp | `timestampdetail` |  |

## Datawindows

### `TABPAGE_1.order` (Order)

- Update table: `oe_hdr`
- Tables in the SELECT: `oe_hdr`, `company`, `users`, `address`, `ship_to`, `freight_code`, `shipping_route`, `p21_view_oe_hdr_rfq_control_no`, `invoice_batch`, `customer`, `currency_line`, `quote_hdr`, `crm_contact_information`, `pegmost_oe_hdr`, `carrier_contract_hdr`, `oe_hdr_notepad`, `oe_hdr_integration`, `country_subdivision`

| Field | Stored in | Basis |
|---|---|---|
| `quote` | `oe_hdr.projected_order` | probed |
| `order_no` | `oe_hdr.order_no` | column |
| `sales_loc_id` | `oe_hdr.location_id` | probed |
| `source_loc_id` | `oe_hdr.source_location_id` | probed |
| `ship_to_id` | `oe_hdr.address_id` | probed |
| `contact_id` | `oe_hdr.contact_id` | column |
| `po_no` | `oe_hdr.po_no` | column |
| `customer_id` | `oe_hdr.customer_id` | column |
| `c_create_transfer` | computed: `'N'` | alias |
| `c_create_po` | computed: `'N'` | alias |
| `order_date` | `oe_hdr.order_date` | column |
| `rma_expiration_date` | `oe_hdr.rma_expiration_date` | column |
| `quote_expiration_date` | `quote_hdr.expiration_date` | probed |
| `expedite_date` | `oe_hdr.expedite_date` | column |
| `company_id` | `oe_hdr.company_id` | column |
| `c_job_no` | computed: `' '` | alias |
| `job_name` | `oe_hdr.job_name` | column |
| `taker` | `oe_hdr.taker` | column |
| `email_address` | `oe_hdr.ship2_email_address` | probed |
| `requested_date` | `oe_hdr.requested_date` | column |
| `approved` | `oe_hdr.approved` | column |
| `oe_hdr_completed` | `oe_hdr.completed` | probed |
| `quote_complete` | computed: `'N'` | alias |
| `cancel_flag` | `oe_hdr.cancel_flag` | column |
| `currency_id` | `currency_line.to_currency_id` | probed |
| `route_override_date` | `oe_hdr.route_override_date` | column |
| `order_priority_uid` | `oe_hdr.order_priority_uid` | column |
| `electronic_order_flag` | `oe_hdr.electronic_order_flag` | probed |
| `supplier_order_no` | `oe_hdr.supplier_order_no` | column |
| `net_billing_flag` | `oe_hdr.net_billing_flag` | column |
| `supplier_release_no` | `oe_hdr.supplier_release_no` | column |
| `do_not_export_to_pts_flag` | `oe_hdr.do_not_export_to_pts_flag` | probed |
| `order_type` | `oe_hdr.order_type` | column |
| `quote_type` | `oe_hdr.quote_type` | column |
| `oe_hdr_terms` | `oe_hdr.terms` | probed |
| `pts_label_print_flag` | `oe_hdr.pts_label_print_flag` | column |
| `oe_hdr_ship2_add1` | `oe_hdr.ship2_add1` | probed |
| `advanced_billing_flag` | `oe_hdr.advanced_billing_flag` | column |
| `oe_hdr_ship2_add2` | `oe_hdr.ship2_add2` | probed |
| `rental_return_date` | `oe_hdr.rental_return_date` | column |
| `oe_hdr_ship2_city` | `oe_hdr.ship2_city` | probed |
| `oe_hdr_ship2_state` | `oe_hdr.ship2_state` | probed |
| `rental_billing_flag` | `oe_hdr.rental_billing_flag` | column |
| `fc_create_invoice` | computed: `'N'` | probed |
| `oe_hdr_ship2_zip` | `oe_hdr.ship2_zip` | probed |
| `fc_receipt_print` | computed: `'N'` | alias |
| `ship_route` | `shipping_route.route_code` | probed |
| `fc_receipt_email` | computed: `'N'` | alias |
| `oe_hdr_carrier_id` | `oe_hdr.carrier_id` | probed |
| `fc_receipt_unpriced` | computed: `'N'` | alias |
| `packing_basis` | `oe_hdr.packing_basis` | column |
| `fc_receipt_skinny` | computed: `'N'` | alias |
| `delivery_instructions` | `oe_hdr.delivery_instructions` | probed |
| `freight_cd` | `freight_code.freight_cd` | column |
| `rental_transaction_no` | `oe_hdr.rental_transaction_no` | column |
| `convert_to_order` | computed: `'N'` | alias |
| `source_code_no` | `oe_hdr.source_code_no` | column |
| `source_id` | `oe_hdr.source_id` | column |
| `suggested_order_no` | computed: `suggested_order_no` | probed |
| `customer_name` | `address.name` | probed |
| `contact_name` | computed: `' '` | probed |
| `sales_loc_name` | `address.name` | probed |
| `ship_to_name` | `oe_hdr.ship2_name` | probed |
| `taker_name` | `users.name` | probed |
| `source_loc_name` | `address.name` | probed |
| `validation_status` | `oe_hdr.validation_status` | column |
| `c_job_description` | computed: `' '` | alias |
| `ups_code` | `oe_hdr.ups_code` | column |
| `c_po_no_append` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Order Number: | `oe_hdr.order_no` |
| 2 | Customer ID: | `oe_hdr.customer_id` |
| 3 | Customer Name | `address.name` |
| 4 | Company ID: | `oe_hdr.company_id` |
| 6 | Sales/Source Loc: | `oe_hdr.location_id` |
| 7 | Sales Loc Name | `address.name` |
| 8 | Ship To ID: | `oe_hdr.address_id` |
| 11 | PO: | `oe_hdr.po_no` |
| 12 | Job: | `oe_hdr.job_name` |
| 13 | Contact ID: | `oe_hdr.contact_id` |
| 14 | Taker: | `oe_hdr.taker` |
| 15 | Taker Name | `users.name` |
| 16 | Order Date: | `oe_hdr.order_date` |
| 17 | Required Date: | `oe_hdr.requested_date` |
| 19 | Quote | `oe_hdr.projected_order` |
| 20 | Oe Hdr Completed | `oe_hdr.completed` |
| 22 | Approved | `oe_hdr.approved` |
| 31 | Ship To Name | `oe_hdr.ship2_name` |
| 32 | Address: | `oe_hdr.ship2_add1` |
| 33 | Address - Line 2: | `oe_hdr.ship2_add2` |
| 34 | City, State, Zip: | `oe_hdr.ship2_city` |
| 35 | State: | `oe_hdr.ship2_state` |
| 36 | Zip: | `oe_hdr.ship2_zip` |
| 38 | Carrier: | `oe_hdr.carrier_id` |
| 39 | Source Location ID: | `oe_hdr.source_location_id` |
| 40 | Packing Basis: | `oe_hdr.packing_basis` |
| 42 | Delivery Instructions: | `oe_hdr.delivery_instructions` |
| 43 | Source Location Name: | `address.name` |
| 44 | Terms: | `oe_hdr.terms` |
| 45 | Contact Name | `contact_name` |
| 55 | Cancel Flag | `oe_hdr.cancel_flag` |
| 59 | Validation Status: | `oe_hdr.validation_status` |
| 62 | Source Id | `oe_hdr.source_id` |
| 63 | Source Type/ID: | `oe_hdr.source_code_no` |
| 64 | Quote Complete | `quote_complete` |
| 73 | Freight Code: | `freight_code.freight_cd` |
| 75 | Payment Hold: | `oe_hdr.credit_card_hold` |
| 76 | E-mail: | `oe_hdr.ship2_email_address` |
| 79 | C Create Po | `c_create_po` |
| 84 | C Create Transfer | `c_create_transfer` |
| 89 | Contract: | `c_job_no` |
| 90 | C Job Description | `c_job_description` |
| 112 | Expedite Date: | `oe_hdr.expedite_date` |
| 115 | Quote Expiration Date: | `quote_expiration_date` |
| 130 | Ups Code: | `oe_hdr.ups_code` |
| calc | C Po No Append | `if((po_no_append = '-1'), ' ', po_no_append)` |

### `TP_CUSTOMER.tp_customer` (Customer)

- Update table: `customer`
- Tables in the SELECT: `customer`, `address`, `corp_id`, `lead_source`

| Field | Stored in | Basis |
|---|---|---|
| `customer_id` | `customer.customer_id` | column |
| `customer_type_cd` | `customer.customer_type_cd` | column |
| `ship_to` | computed: `'N'` | probed |
| `customer_name` | `address.name` | probed |
| `mail_address1` | `address.mail_address1` | column |
| `mail_address2` | `address.mail_address2` | probed |
| `mail_city` | `address.mail_city` | column |
| `mail_state` | `address.mail_state` | column |
| `mail_postal_code` | `address.mail_postal_code` | probed |
| `mail_country` | `address.mail_country` | column |
| `corp_address_id` | `address.corp_address_id` | column |
| `lead_source_id` | `customer.lead_source_id` | column |
| `currency_id` | `customer.currency_id` | column |
| `central_phone_number` | `address.central_phone_number` | column |
| `central_fax_number` | `address.central_fax_number` | column |
| `email_address` | `address.email_address` | column |
| `url` | `address.url` | column |
| `invoice_print_qty` | `customer.invoice_print_qty` | column |
| `tariff_enabled_flag` | computed: `NULL` | alias |
| `source_description` | `lead_source.source_description` | column |
| `default_disposition` | `customer.default_disposition` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Customer ID: | `customer.customer_id` |
| 2 | Name: | `address.name` |
| 3 | Address: | `address.mail_address1` |
| 4 | Mail Address2 | `address.mail_address2` |
| 5 | City/State/Zip/Country: | `address.mail_city` |
| 6 | Mail State | `address.mail_state` |
| 7 | Mail Postal Code | `address.mail_postal_code` |
| 8 | Mail Country | `address.mail_country` |
| 9 | Corp Address ID: | `address.corp_address_id` |
| 11 | Phone Number: | `address.central_phone_number` |
| 12 | Fax Number: | `address.central_fax_number` |
| 14 | Default Disposition: | `customer.default_disposition` |
| 31 | Ship To | `ship_to` |
| 52 | Invoice Print Quantity: | `customer.invoice_print_qty` |
| 67 | E-mail Address: | `address.email_address` |
| 68 | URL: | `address.url` |
| 71 | Currency ID: | `customer.currency_id` |
| 83 | Type: | `customer.customer_type_cd` |
| 84 | Lead Source ID: | `customer.lead_source_id` |
| 89 | Source Description | `lead_source.source_description` |
| 110 | Tariff Enabled Flag | `tariff_enabled_flag` |

### `TP_CONTACTS.tp_contacts` (Contacts)

- Update table: `contacts`
- Tables in the SELECT: `contacts`, `address`, `company`, `salutation`

| Field | Stored in | Basis |
|---|---|---|
| `contact_id` | `contacts.id` | probed |
| `salutation` | `contacts.salutation` | column |
| `first_name` | `contacts.first_name` | column |
| `mi` | `contacts.mi` | column |
| `last_name` | `contacts.last_name` | column |
| `contacts_title` | `contacts.title` | probed |
| `address_id` | `contacts.address_id` | column |
| `customer_address` | computed: `' '` | alias |
| `contact_association` | computed: `'Customer'` | probed |
| `phone_ext` | `contacts.phone_ext` | column |
| `address_name` | `address.name` | probed |
| `mail_address1` | `address.mail_address1` | column |
| `fax_ext` | `contacts.fax_ext` | probed |
| `mail_address2` | `address.mail_address2` | column |
| `mail_city` | `address.mail_city` | column |
| `mail_state` | `address.mail_state` | column |
| `mail_postal_code` | `address.mail_postal_code` | column |
| `mail_country` | `address.mail_country` | column |
| `contacts_direct_phone` | `contacts.direct_phone` | probed |
| `direct_fax` | `contacts.direct_fax` | column |
| `central_phone_number` | `address.central_phone_number` | probed |
| `central_fax_number` | `address.central_fax_number` | column |
| `email_address` | `contacts.email_address` | column |
| `url` | `contacts.url` | column |
| `contacts_cellular` | `contacts.cellular` | probed |
| `fsm_contact` | `contacts.fsm_contact` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Contact ID: | `contacts.id` |
| 2 | First Name | `contacts.first_name` |
| 3 | Mi | `contacts.mi` |
| 4 | Last Name | `contacts.last_name` |
| 5 | Job Title: | `contacts.title` |
| 6 | Address ID: | `contacts.address_id` |
| 7 | Name: | `address.name` |
| 8 | Address: | `address.mail_address1` |
| 9 | Mail Address2 | `address.mail_address2` |
| 10 | City/State/Zip/Country: | `address.mail_city` |
| 11 | Mail State | `address.mail_state` |
| 12 | Mail Postal Code | `address.mail_postal_code` |
| 13 | Mail Country | `address.mail_country` |
| 14 | Central Phone: | `address.central_phone_number` |
| 15 | Central Fax: | `address.central_fax_number` |
| 16 | Direct Phone: | `contacts.direct_phone` |
| 17 | Direct Fax: | `contacts.direct_fax` |
| 19 | Mobile: | `contacts.cellular` |
| 20 | Contact E-mail: | `contacts.email_address` |
| 23 | Salutation | `contacts.salutation` |
| 30 | Customer Address | `customer_address` |
| 32 | Contact URL: | `contacts.url` |
| 34 | Contact Association | `contact_association` |
| 35 | Phone Extension: | `contacts.phone_ext` |
| 36 | Fax Extension: | `contacts.fax_ext` |

### `TP_SHIPTO.shipto` (Ship To)

- Update table: `oe_hdr`
- Tables in the SELECT: `oe_hdr`, `company`, `users`, `address`, `ship_to`, `freight_code`, `shipping_route`, `p21_view_oe_hdr_rfq_control_no`, `invoice_batch`, `customer`, `currency_line`, `quote_hdr`, `crm_contact_information`, `pegmost_oe_hdr`, `carrier_contract_hdr`, `oe_hdr_notepad`, `oe_hdr_integration`, `country_subdivision`

| Field | Stored in | Basis |
|---|---|---|
| `ship_to_id` | `oe_hdr.address_id` | probed |
| `ship_to_name` | `oe_hdr.ship2_name` | probed |
| `phys_address1` | `oe_hdr.ship2_add1` | probed |
| `phys_address2` | `oe_hdr.ship2_add2` | probed |
| `phys_city` | `oe_hdr.ship2_city` | probed |
| `phys_state` | `oe_hdr.ship2_state` | probed |
| `phys_postal_code` | `oe_hdr.ship2_zip` | probed |
| `phys_country` | `oe_hdr.ship2_country` | probed |
| `source_loc_id` | `oe_hdr.source_location_id` | probed |
| `invoice_batch_number` | `invoice_batch.invoice_batch_number` | column |
| `central_phone_number` | `oe_hdr.ship_to_phone` | probed |
| `central_fax_number` | `address.central_fax_number` | column |
| `email_address` | `oe_hdr.ship2_email_address` | probed |
| `url` | `address.url` | column |
| `ship2_latitude` | `oe_hdr.ship2_latitude` | column |
| `ship2_longitude` | `oe_hdr.ship2_longitude` | column |
| `country_subdivision_uid` | `country_subdivision.country_subdivision_uid` | column |
| `convert_to_order` | computed: `'N'` | alias |
| `invoice_batch_desc` | `invoice_batch.invoice_batch_desc` | column |
| `source_loc_name` | `address.name` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 8 | Ship To ID: | `oe_hdr.address_id` |
| 9 | Phone Number: | `oe_hdr.ship_to_phone` |
| 10 | Fax Number: | `address.central_fax_number` |
| 31 | Name: | `oe_hdr.ship2_name` |
| 32 | Address: | `oe_hdr.ship2_add1` |
| 33 | Phys Address2 | `oe_hdr.ship2_add2` |
| 34 | City/State/Zip/Country: | `oe_hdr.ship2_city` |
| 35 | Phys State | `oe_hdr.ship2_state` |
| 36 | Phys Postal Code | `oe_hdr.ship2_zip` |
| 37 | Phys Country | `oe_hdr.ship2_country` |
| 39 | Source Location ID: | `oe_hdr.source_location_id` |
| 43 | Source Loc Name | `address.name` |
| 76 | E-mail address: | `oe_hdr.ship2_email_address` |
| 77 | URL: | `address.url` |
| 81 | Invoice Batch Number: | `invoice_batch.invoice_batch_number` |
| 82 | Invoice Batch Desc | `invoice_batch.invoice_batch_desc` |

### `TP_REMITTANCES.tp_remittances` (Remittances)

- Update table: `oe_hdr`
- Tables in the SELECT: `oe_hdr`, `company`, `users`, `address`, `ship_to`, `freight_code`, `shipping_route`, `p21_view_oe_hdr_rfq_control_no`, `invoice_batch`, `customer`, `currency_line`, `quote_hdr`, `crm_contact_information`, `pegmost_oe_hdr`, `carrier_contract_hdr`, `oe_hdr_notepad`, `oe_hdr_integration`, `country_subdivision`

| Field | Stored in | Basis |
|---|---|---|
| `req_pymt_upon_release_flag` | `oe_hdr.req_pymt_upon_release_flag` | column |
| `convert_to_order` | computed: `'N'` | alias |

| # | Label | table.column / expression |
|---|---|---|
| 108 | Req Pymt Upon Release Flag | `oe_hdr.req_pymt_upon_release_flag` |

### `TP_REMITTANCES.remittances` (Remittances)

- Update table: `ar_payment_details`
- Tables in the SELECT: `ar_payment_details`, `payment_types`, `remittances`, `currency_line`, `p21_view_ar_payment_details`, `check_payment_details`, `p21_view_creditcard_payment_details`, `epf_transaction_detail`, `payment_account_x_transaction`, `payment_account`, `currency_hdr`

| Field | Stored in | Basis |
|---|---|---|
| `payment_type_id` | `ar_payment_details.payment_type_id` | column |
| `payment_amount` | `ar_payment_details.payment_amount` | column |
| `c_cash_pymt_amt` | `ar_payment_details.payment_amount` | alias |
| `payment_desc` | `ar_payment_details.payment_desc` | column |
| `check_number` | `ar_payment_details.check_number` | column |
| `payment_date` | `ar_payment_details.payment_date` | column |
| `store_credit_number` | `ar_payment_details.store_credit_number` | column |
| `cf_pay_total` | computed: `' '` | alias |
| `cc_name` | `ar_payment_details.cc_name` | column |
| `cc_creditcard_number` | computed: `CASE WHEN payment_method_id IN ('CC', 'DE', 'EP') THEN '************' + RIGHT(ar_payment_details.cc_number, 4) ELSE NULL END` | alias |
| `customer_verification_value` | `p21_view_creditcard_payment_details.customer_verification_value` | column |
| `cc_expiration_date` | `ar_payment_details.cc_expiration_date` | column |
| `cc_authorized_date` | `ar_payment_details.cc_authorized_date` | column |
| `cc_authorized_number` | `ar_payment_details.cc_authorized_number` | column |
| `switch_issue_number` | `p21_view_creditcard_payment_details.switch_issue_number` | column |
| `multi_currency_id` | `ar_payment_details.multi_currency_id` | column |
| `multi_currency_payment_amount` | `ar_payment_details.multi_currency_payment_amount` | column |
| `rental_payment_amt` | computed: `0` | alias |
| `exchange_date` | computed: `COALESCE(ar_payment_details.exchange_rate_override_date, ar_payment_details.date_created)` | alias |
| `cc_swipe` | computed: `' '` | alias |
| `override_surcharge` | `ar_payment_details.override_surcharge` | column |
| `memo_amount` | `ar_payment_details.memo_amount` | probed |
| `sum_cc_payment` | computed: `(computed in the datawindow)` | dw_name |
| `sum_payment_amount` | computed: `(computed in the datawindow)` | dw_name |
| `cf_rowinfo` | computed: `(computed in the datawindow)` | dw_name |
| `sum_memo_amount` | computed: `(computed in the datawindow)` | dw_name |
| `cf_new_payment` | computed: `(computed in the datawindow)` | dw_name |
| `sum_new_payments` | computed: `(computed in the datawindow)` | dw_name |
| `sum_new_cc_payments` | computed: `(computed in the datawindow)` | dw_name |
| `sum_auth_amount` | computed: `(computed in the datawindow)` | dw_name |
| `cf_cash_pymt_chg` | computed: `(computed in the datawindow)` | dw_name |
| `cf_sum_new_pymts_not_cc_or_ca` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 2 | Pymt Type: | `ar_payment_details.payment_type_id` |
| 3 | Payment Desc: | `ar_payment_details.payment_desc` |
| 4 | Pymt Date: | `ar_payment_details.payment_date` |
| 5 | Payment Amount: | `ar_payment_details.payment_amount` |
| 8 | Check Number: | `ar_payment_details.check_number` |
| 9 | CC Name: | `ar_payment_details.cc_name` |
| 11 | CC Exp Dt: | `ar_payment_details.cc_expiration_date` |
| 12 | CC Auth Dt: | `ar_payment_details.cc_authorized_date` |
| 13 | CC Auth No: | `ar_payment_details.cc_authorized_number` |
| 24 | AP Credit Memo: | `ar_payment_details.memo_amount` |
| 25 | Cc Swipe | `cc_swipe` |
| 27 | Authorized Amount: | `p21_view_creditcard_payment_details.auth_amount` |
| 37 | Payment Amount Home | `p21_view_ar_payment_details.payment_amount_home` |
| 38 | Auth Amount Home | `p21_view_creditcard_payment_details.auth_amount_home` |
| 48 | Cash Pymt Amt: | `c_cash_pymt_amt` |
| 50 | CC Number: | `cc_creditcard_number` |
| 53 | Switch Issue Number | `p21_view_creditcard_payment_details.switch_issue_number` |
| 81 | Rental Amount: | `rental_payment_amt` |
| calc | Cf Rowinfo | `'Payment ' + string(getrow()) + ' of ' + String(rowcount())` |

### `TP_REMITTANCES.remittotals` (Remittances)

- Update table: `oe_line`
- Tables in the SELECT: `oe_line`

| Field | Stored in | Basis |
|---|---|---|
| `pay_current_invoice` | computed: `'N'` | alias |
| `c_dp_to_apply` | computed: `0.00` | alias |
| `c_dp_percentage` | computed: `0.00` | probed |
| `c_calculated_dp` | computed: `0.00` | alias |
| `c_create_add_dp_amt` | computed: `'N'` | alias |
| `c_dp_override_amt` | computed: `0.00` | alias |
| `c_dp_refund_amt` | computed: `0` | alias |
| `c_order_disc_type` | computed: `0.00` | alias |
| `c_order_disc_factor` | computed: `0.00` | alias |
| `invoice_total` | computed: `0.00` | alias |
| `c_prev_open_inv_total` | computed: `0.00` | alias |
| `c_open_dp_inv_amt` | computed: `0.00` | alias |
| `c_tag_n_hold_total` | computed: `0.00` | alias |
| `c_new_dp_amt` | computed: `0.00` | alias |
| `c_unapplied_dp` | computed: `0.00` | alias |
| `bo_total` | computed: `0.00` | alias |
| `total_paid` | computed: `0.000000000` | alias |
| `ship_total` | computed: `0.00` | alias |
| `amount_tendered` | computed: `0.00` | alias |
| `cf_total_sugg_amt` | computed: `(computed in the datawindow)` | dw_name |
| `cf_sugg_pymt` | computed: `(computed in the datawindow)` | dw_name |
| `cf_sugg_dp` | computed: `(computed in the datawindow)` | dw_name |
| `cf_balance_change` | computed: `(computed in the datawindow)` | dw_name |
| `cf_downpayment_remaining` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_due` | computed: `(computed in the datawindow)` | dw_name |
| `cf_balance` | computed: `(computed in the datawindow)` | dw_name |
| `cf_tax` | computed: `(computed in the datawindow)` | dw_name |
| `cf_rental_adjustment_amt` | computed: `(computed in the datawindow)` | dw_name |
| `cf_ship_total` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 12 | Total Paid: | `total_paid` |
| 35 | Sub Total | `sub_total` |
| 38 | Amt Tendered: | `amount_tendered` |
| 39 | Bo Balance | `bo_balance` |
| 45 | Order Total: | `ship_total` |
| 46 | Bo Tax | `bo_tax` |
| 47 | Curr Inv Total: | `invoice_total` |
| 48 | Non-Inv Total: | `bo_total` |
| 50 | Prev Open Inv Total: | `c_prev_open_inv_total` |
| 51 | Tag and Hold Total: | `c_tag_n_hold_total` |
| 52 | DP %: | `c_dp_percentage` |
| 53 | Calc / Req DP Amt: | `c_calculated_dp` |
| 54 | Pay Current Invoice | `pay_current_invoice` |
| 55 | Unapplied DP: | `c_unapplied_dp` |
| 56 | Amt To Maintain DP: | `c_new_dp_amt` |
| 57 | Open DP Inv Amt: | `c_open_dp_inv_amt` |
| 58 | C Create Add Dp Amt | `c_create_add_dp_amt` |
| 59 | DP To Apply: | `c_dp_to_apply` |
| 77 | DP Override Amt: | `c_dp_override_amt` |
| 89 | DP Refund Amt: | `c_dp_refund_amt` |
| calc | Total Sugg Pymt (A+B): | `"if ((cf_sugg_pymt +  cf_sugg_dp - bldr_allowance_remaining) < 0, 0,  (cf_sugg_pymt +  cf_sugg_dp - bldr_allowance_remaining))      /* if ((cf_sugg_pymt +  cf_sugg_dp -   c_prev_pymt_not_appd) < 0, 0,  (cf_sugg_pymt +  cf_sugg_dp -   c_prev_pymt_not_appd)) */"` |
| calc | Sugg Pymt For Inv's (A): | `if( pay_current_invoice = 'Y',  invoice_total  - c_dp_to_apply, (c_prev_open_inv_total  +  invoice_total)  -   c_dp_to_apply)` |
| calc | Sugg Pymt For DP (B): | `c_calculated_dp -  c_unapplied_dp` |
| calc | Cf Balance Change | `If (cf_balance >=0, "Balance:","Change:")` |
| calc | Total Due: | `ship_total + cf_tax + if( IsNull(total_wee_tax), 0, total_wee_tax) + if(IsNull(total_eco_fee), 0, total_eco_fee) + if(isNull(c_price_rounding_offset), 0, c_price_rounding_offset) - total_paid` |
| calc | Cf Balance | `cf_total_due - amount_tendered` |
| calc | Tax Due: | `total_tax_due - tax_paid` |

### `TP_TOTALS.tp_totals` (Totals)

- Update table: `oe_line`
- Tables in the SELECT: `oe_line`

| Field | Stored in | Basis |
|---|---|---|
| `sales_sub_total` | computed: `0.00` | alias |
| `tcost` | computed: `0` | alias |
| `total_profit` | computed: `0.000000000` | alias |
| `total_paid` | computed: `0.000000000` | alias |
| `total_other_charge` | computed: `0.00` | alias |
| `total_freight` | computed: `0.00` | alias |
| `line_items` | computed: `0.00` | alias |
| `sales_total` | computed: `0.00` | alias |
| `tax_total` | computed: `0.00` | alias |
| `total_pieces` | computed: `0.000000000` | alias |
| `total_sales_cost` | computed: `0.00` | alias |
| `total_weight` | computed: `0.00` | alias |
| `open_other_charge_total` | computed: `0.00` | alias |
| `open_sales_tax_total` | computed: `0.00` | alias |
| `open_sub_total` | computed: `0.00` | alias |
| `open_total` | computed: `0.00` | alias |
| `total_open_freight` | computed: `0.00` | alias |
| `open_sales_cost_total` | computed: `0.00` | alias |
| `open_profit_percent` | computed: `0.00` | alias |
| `open_pieces` | computed: `0.000000000` | alias |
| `open_weight_total` | computed: `0.00` | alias |

| # | Label | table.column / expression |
|---|---|---|
| 4 | Sales Cost | `oe_line.sales_cost` |
| 5 | Total Line Items: | `line_items` |
| 6 | Sub Total: | `sales_sub_total` |
| 7 | Estimated Tax: | `tax_total` |
| 8 | Total: | `sales_total` |
| 9 | Cost: | `total_sales_cost` |
| 10 | Profit Percent: | `total_profit` |
| 11 | Pieces: | `total_pieces` |
| 12 | Total Paid: | `total_paid` |
| 13 | Weight: | `total_weight` |
| 14 | Other Charge: | `total_other_charge` |
| 15 | Open Total: | `open_total` |
| 16 | Sub Total: | `open_sub_total` |
| 17 | Other Charge: | `open_other_charge_total` |
| 18 | Estimated Tax: | `open_sales_tax_total` |
| 19 | Sales Cost: | `open_sales_cost_total` |
| 20 | Profit Percent: | `open_profit_percent` |
| 21 | Weight: | `open_weight_total` |
| 22 | Total Amount On Invoices | `total_amount_on_invoices` |
| 23 | Estimated Freight: | `total_freight` |
| 24 | Estimated Freight: | `total_open_freight` |
| 29 | Order Cost Basis: | `tcost` |
| 34 | Open Pieces: | `open_pieces` |

### `TP_FRONTCOUNTER.tp_frontcounter` (Front Counter)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `print_tix` | ? | no_sql |
| `fax_tix` | ? | no_sql |
| `email_tix` | ? | no_sql |
| `print_orderack` | ? | no_sql |
| `fax_orderack` | ? | no_sql |
| `email_orderack` | ? | no_sql |
| `edi_843` | ? | no_sql |
| `ship` | ? | no_sql |
| `print_invoice` | ? | no_sql |
| `fax_invoice` | ? | no_sql |
| `email_invoice` | ? | no_sql |
| `print_downpayment` | ? | no_sql |
| `fax_downpayment` | ? | no_sql |
| `email_downpayment` | ? | no_sql |
| `print_advanced_bill` | ? | no_sql |
| `fax_advanced_bill` | ? | no_sql |
| `email_advanced_bill` | ? | no_sql |
| `print_pack_list` | ? | no_sql |
| `fax_pack_list` | ? | no_sql |
| `email_pack_list` | ? | no_sql |
| `period` | ? | no_sql |
| `year_for_period` | ? | no_sql |
| `will_call` | ? | no_sql |
| `signature_capture` | ? | no_sql |
| `receiver_name` | ? | no_sql |
| `print_bssheet` | ? | no_sql |
| `fax_bssheet` | ? | no_sql |
| `email_bssheet` | ? | no_sql |
| `bssheet_price_display_option` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Print Tix | `print_tix` |
| 4 | Print Orderack | `print_orderack` |
| 6 | Period: | `Period` |
| 7 | Year: | `year_for_period` |
| 8 | Will Call | `will_call` |
| 11 | Pay Current Invoice | `pay_current_invoice` |
| 12 | Fax Tix | `fax_tix` |
| 14 | Fax Orderack | `fax_orderack` |
| 19 | Email Orderack | `email_orderack` |
| 21 | Email Tix | `email_tix` |
| 31 | Print Pack List | `print_pack_list` |
| 32 | Fax Pack List | `fax_pack_list` |
| 33 | Email Pack List | `email_pack_list` |
| 34 | Print Bssheet | `print_bssheet` |
| 35 | Fax Bssheet | `fax_bssheet` |
| 36 | Email Bssheet | `email_bssheet` |
| 37 | Send Original Bssheet | `send_original_bssheet` |
| 39 | Bssheet Price Display Option | `bssheet_price_display_option` |
| 40 | Print Advanced Bill | `print_advanced_bill` |
| 41 | Fax Advanced Bill | `fax_advanced_bill` |
| 42 | Email Advanced Bill | `email_advanced_bill` |

### `HDR_NOTE.hdr_note` (Order Notes)

- Update table: `oe_hdr_notepad`
- Tables in the SELECT: `oe_hdr_notepad`, `note_area`, `notepad_class`

| Field | Stored in | Basis |
|---|---|---|
| `note` | `oe_hdr_notepad.note` | column |
| `note_id` | `oe_hdr_notepad.note_id` | column |
| `topic` | `oe_hdr_notepad.topic` | column |
| `notepad_class_desc` | `notepad_class.notepad_class_desc` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Note ID | `oe_hdr_notepad.note_id` |
| 4 | Topic | `oe_hdr_notepad.topic` |
| 5 | Note | `oe_hdr_notepad.note` |
| 15 | Class | `notepad_class.notepad_class_desc` |

### `TP_SHIPINFO.shipinfo` (Ship Info)

- Update table: `oe_hdr`
- Tables in the SELECT: `oe_hdr`, `company`, `users`, `address`, `ship_to`, `freight_code`, `shipping_route`, `p21_view_oe_hdr_rfq_control_no`, `invoice_batch`, `customer`, `currency_line`, `quote_hdr`, `crm_contact_information`, `pegmost_oe_hdr`, `carrier_contract_hdr`, `oe_hdr_notepad`, `oe_hdr_integration`, `country_subdivision`

| Field | Stored in | Basis |
|---|---|---|
| `delivery_instructions` | `oe_hdr.delivery_instructions` | column |
| `freight_cd` | `freight_code.freight_cd` | column |
| `freight_out` | `oe_hdr.freight_out` | column |
| `oe_hdr_carrier_id` | `oe_hdr.carrier_id` | probed |
| `ups_code` | `oe_hdr.ups_code` | column |
| `ship_route` | `shipping_route.route_code` | probed |
| `pick_ticket_type` | `oe_hdr.pick_ticket_type` | column |
| `packing_basis` | `oe_hdr.packing_basis` | column |
| `third_party_billing_flag` | `oe_hdr.third_party_billing_flag` | column |
| `oe_hdr_handling_charge_req_flag` | `oe_hdr.handling_charge_req_flag` | probed |
| `tag_hold_cancel_date` | `oe_hdr.tag_hold_cancel_date` | column |
| `transit_days` | `oe_hdr.transit_days` | column |
| `days_early` | `oe_hdr.days_early` | probed |
| `pegmost_delivery_notes` | `pegmost_oe_hdr.pegmost_delivery_notes` | column |
| `convert_to_order` | computed: `'N'` | alias |
| `freight_desc` | `freight_code.freight_desc` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 38 | Carrier: | `oe_hdr.carrier_id` |
| 40 | Packing Basis: | `oe_hdr.packing_basis` |
| 41 | Route: | `shipping_route.route_code` |
| 42 | Delivery Instructions: | `oe_hdr.delivery_instructions` |
| 56 | Pick Ticket Type | `oe_hdr.pick_ticket_type` |
| 71 | Outgoing Freight: | `oe_hdr.freight_out` |
| 73 | Freight Code: | `freight_code.freight_cd` |
| 74 | Freight Desc | `freight_code.freight_desc` |
| 130 | UPS Code: | `oe_hdr.ups_code` |
| 162 | Transit Days: | `oe_hdr.transit_days` |
| 163 | Days Early: | `oe_hdr.days_early` |

### `TP_TAX.tp_tax` (Tax)

- Update table: `oe_hdr_tax`
- Tables in the SELECT: `oe_hdr_tax`, `tax_jurisdiction`

| Field | Stored in | Basis |
|---|---|---|
| `jurisdiction_id` | `oe_hdr_tax.jurisdiction_id` | column |
| `taxable` | `oe_hdr_tax.taxable` | column |
| `jurisdiction_desc` | `tax_jurisdiction.jurisdiction_desc` | column |
| `flat_fee_amount` | `tax_jurisdiction.flat_fee_amount` | probed |
| `compute_1` | computed: `(computed in the datawindow)` | dw_name |
| `tax_in_hundred` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Jurisdiction ID | `oe_hdr_tax.jurisdiction_id` |
| 2 | Taxable | `oe_hdr_tax.taxable` |
| 6 | Jurisdiction Description | `tax_jurisdiction.jurisdiction_desc` |
| 16 | Flat Rate Amount | `tax_jurisdiction.flat_fee_amount` |
| calc | Tax Percentage | `tax_percentage` |

### `TP_TAX.tp_tax_dw_2` (Tax)

- Update table: `oe_hdr`
- Tables in the SELECT: `oe_hdr`, `company`, `users`, `address`, `ship_to`, `freight_code`, `shipping_route`, `p21_view_oe_hdr_rfq_control_no`, `invoice_batch`, `customer`, `currency_line`, `quote_hdr`, `crm_contact_information`, `pegmost_oe_hdr`, `carrier_contract_hdr`, `oe_hdr_notepad`, `oe_hdr_integration`, `country_subdivision`

| Field | Stored in | Basis |
|---|---|---|
| `taxable` | computed: `'Y'` | alias |
| `convert_to_order` | computed: `'N'` | alias |

| # | Label | table.column / expression |
|---|---|---|
| 83 | Taxable | `taxable` |

### `CUSTOMERNOTESTABPG.customernotestabpg` (Customer Notes)

- Update table: `customer_notepad`
- Tables in the SELECT: `customer_notepad`, `note_area`, `notepad_class`

| Field | Stored in | Basis |
|---|---|---|
| `note_id` | `customer_notepad.note_id` | column |
| `topic` | `customer_notepad.topic` | column |
| `notepad_class_desc` | `notepad_class.notepad_class_desc` | column |
| `note` | `customer_notepad.note` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Note ID | `customer_notepad.note_id` |
| 2 | Topic | `customer_notepad.topic` |
| 3 | Note | `customer_notepad.note` |
| 5 | Class | `notepad_class.notepad_class_desc` |

### `TP_WAREHOUSEACTIVITY.warehouse_activity` (Warehouse Activity)

- Update table: `oe_pick_ticket`
- Tables in the SELECT: `oe_pick_ticket`, `oe_hdr`, `location`, `group_pick_ticket_detail`, `group_pick_ticket_hdr`

| Field | Stored in | Basis |
|---|---|---|
| `pick_ticket_no` | `oe_pick_ticket.pick_ticket_no` | column |
| `print_date` | `oe_pick_ticket.print_date` | alias |
| `picking_status` | computed: `CASE WHEN COALESCE(oe_pick_ticket.invoice_no, 0)=0 THEN '' ELSE 'Shipped' END` | alias |
| `percent_picked` | computed: `CASE WHEN COALESCE(oe_pick_ticket.invoice_no, 0)=0 THEN 0 ELSE 100 END` | alias |
| `bin` | computed: `''` | alias |
| `group_pick_ticket_hdr_uid` | computed: `CASE WHEN group_pick_ticket_hdr.transaction_type_cd = 1881 THEN group_pick_ticket_hdr.group_pick_ticket_hdr_uid ELSE NULL END` | probed |
| `gpt_picking_status` | computed: `NULL` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Pick Ticket | `oe_pick_ticket.pick_ticket_no` |
| 2 | Print Date | `oe_pick_ticket.print_date` |
| 4 | Picking Status | `picking_status` |
| 5 | % Picked | `percent_picked` |
| 6 | Pick to Bin | `bin` |
| 9 | Group PT No | `group_pick_ticket_hdr.group_pick_ticket_hdr_uid` |
| 10 | Group PT Picking Status | `gpt_picking_status` |

### `TP_SALESREPS.tp_salesreps` (Salesreps)

- Update table: `oe_hdr_salesrep`
- Tables in the SELECT: `oe_hdr_salesrep`, `contacts`, `salutation`, `salesrep_commission_class`

| Field | Stored in | Basis |
|---|---|---|
| `salesrep_id` | `oe_hdr_salesrep.salesrep_id` | column |
| `commission_split` | `oe_hdr_salesrep.commission_split` | column |
| `primary_salesrep` | `oe_hdr_salesrep.primary_salesrep` | column |
| `delete_flag` | `oe_hdr_salesrep.delete_flag` | column |
| `exclude_split_validation_flag` | `oe_hdr_salesrep.exclude_split_validation_flag` | column |
| `commission_class_desc` | `salesrep_commission_class.commission_class_desc` | column |
| `display_salesrep_name` | computed: `(computed in the datawindow)` | probed |
| `salesrep_name_1` | computed: `(computed in the datawindow)` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Salesrep ID | `oe_hdr_salesrep.salesrep_id` |
| 6 | Percentage | `oe_hdr_salesrep.commission_split` |
| 8 | Delete | `oe_hdr_salesrep.delete_flag` |
| 9 | Commission Class | `salesrep_commission_class.commission_class_desc` |
| 15 | Primary Rep | `oe_hdr_salesrep.primary_salesrep` |
| 16 | Full Commission | `oe_hdr_salesrep.exclude_split_validation_flag` |
| calc | Name | `"IF ( salesrep_name <> ' ', salesrep_name, contacts_last_name + IF(IsNull(contacts_first_name ), ~"~", ~", ~" + contacts_first_name +  ~" ~") + IF(IsNull(contacts_mi), ~"~", ~" ~" + contacts_mi + ~".~")  )    "` |

### `TP_CREDIT.tp_credit` (Credit)

- Update table: `customer`
- Tables in the SELECT: `customer`, `address`, `corp_id`, `lead_source`

| Field | Stored in | Basis |
|---|---|---|
| `credit_status` | `customer.credit_status` | column |
| `open_ar` | computed: `0.000000000` | alias |
| `corp_id_credit_limit` | `corp_id.credit_limit` | probed |
| `credit_limit` | `customer.credit_limit` | probed |
| `credit_limit_used` | `customer.credit_limit_used` | probed |
| `corp_id_credit_limit_used` | `corp_id.credit_limit_used` | probed |
| `customer_credit_limit_per_order` | `customer.credit_limit_per_order` | probed |
| `customer_minimum_order_dollar_amount` | `customer.minimum_order_dollar_amount` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 35 | Credit Limit Used | `customer.credit_limit_used` |
| 38 | Credit Limit Per Order: | `customer.credit_limit_per_order` |
| 46 | Minimum Order Amount: | `customer.minimum_order_dollar_amount` |
| 55 | Corporate: | `corp_id.credit_limit` |
| 56 | Corp Id Credit Limit Used | `corp_id.credit_limit_used` |
| 57 | Credit Limit | `customer.credit_limit` |
| 58 | Credit Status: | `customer.credit_status` |
| 59 | Open Receivables: | `address.open_ar` |
| calc | Corp Credit Available | `if( corp_id_credit_limit = 0, 0, corp_id_credit_limit  -  corp_id_credit_limit_used )` |
| calc | Credit Limit Available | `if( credit_limit = 0, credit_limit, credit_limit  -  credit_limit_used  )` |

### `TP_PRICING.pricing_hdr` (Pricing)

- Update table: `customer`
- Tables in the SELECT: `customer`, `address`, `corp_id`, `lead_source`

| Field | Stored in | Basis |
|---|---|---|
| `customer_id` | `customer.customer_id` | column |
| `multiplier` | `customer.multiplier` | column |
| `pricing_method_cd` | `customer.pricing_method_cd` | column |
| `source_price_cd` | `customer.source_price_cd` | column |
| `customer_name` | `address.name` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Customer ID: | `customer.customer_id` |
| 2 | Customer Name | `address.name` |
| 60 | Pricing Method: | `customer.pricing_method_cd` |
| 61 | Source Price: | `customer.source_price_cd` |
| 62 | Multiplier: | `customer.multiplier` |

### `TP_PRICING.pricing_detail` (Pricing)

- Update table: `none reported` (tool reported 'clause*/' (misparse of SQL comments; treat as unknown))
- Tables in the SELECT: `customer`, `price_library_x_cust_x_cmpy`, `price_library`

| Field | Stored in | Basis |
|---|---|---|
| `price_library_id` | `price_library.price_library_id` | column |
| `description` | `price_library.description` | probed |
| `row_status_flag` | `price_library_x_cust_x_cmpy.row_status_flag` | column |

| # | Label | table.column / expression |
|---|---|---|
| 4 | Library ID | `price_library.price_library_id` |
| 5 | Library Description | `price_library.description` |
| 7 | Status | `price_library_x_cust_x_cmpy.row_status_flag` |

### `TP_TERMS.terms` (Terms)

- Update table: `oe_hdr`
- Tables in the SELECT: `oe_hdr`, `company`, `users`, `address`, `ship_to`, `freight_code`, `shipping_route`, `p21_view_oe_hdr_rfq_control_no`, `invoice_batch`, `customer`, `currency_line`, `quote_hdr`, `crm_contact_information`, `pegmost_oe_hdr`, `carrier_contract_hdr`, `oe_hdr_notepad`, `oe_hdr_integration`, `country_subdivision`

| Field | Stored in | Basis |
|---|---|---|
| `terms` | `oe_hdr.terms` | column |
| `convert_to_order` | computed: `'N'` | alias |

| # | Label | table.column / expression |
|---|---|---|
| 44 | Terms ID: | `oe_hdr.terms` |

### `TP_TERMS.tp_terms_dw_2` (Terms)

- Update table: `terms`
- Tables in the SELECT: `terms`

| Field | Stored in | Basis |
|---|---|---|
| `discount_days` | `terms.discount_days` | probed |
| `net_days` | `terms.net_days` | column |
| `terms_months` | `terms.terms_months` | column |
| `billing_cycle_cutoff_day` | `terms.billing_cycle_cutoff_day` | column |
| `terms_day_of_month` | `terms.terms_day_of_month` | column |
| `discount_pct` | `terms.discount_pct` | column |
| `net_day_of_month` | `terms.day_of_month` | probed |
| `net_months` | `terms.months` | probed |
| `terms_day_of_month_1` | `terms.terms_day_of_month` | probed |
| `terms_months_1` | `terms.terms_months` | probed |
| `terms_day_of_month2` | `terms.terms_day_of_month2` | column |
| `net_months_1` | `terms.months` | probed |
| `net_day_of_month_1` | `terms.day_of_month` | probed |
| `net_day_of_month2` | `terms.net_day_of_month2` | column |

| # | Label | table.column / expression |
|---|---|---|
| 3 | Terms Percent : | `terms.discount_pct` |
| 4 | Terms Days: | `terms.discount_days` |
| 5 | Net Days: | `terms.net_days` |
| 10 | Net Day Of Month | `terms.day_of_month` |
| 11 | Additional Net Months: | `terms.months` |
| 12 | Terms Day Of Month | `terms.terms_day_of_month` |
| 13 | Additional Terms Months: | `terms.terms_months` |
| 14 | (16 - End): | `terms.net_day_of_month2` |
| 15 | (16 - End): | `terms.terms_day_of_month2` |
| 17 | Billing Cycle Cutoff Day: | `terms.billing_cycle_cutoff_day` |

### `TP_HDRPROMISEDATES.tp_hdrpromisedates` (Promise Dates)

- Update table: `oe_hdr`
- Tables in the SELECT: `oe_hdr`, `company`, `users`, `address`, `ship_to`, `freight_code`, `shipping_route`, `p21_view_oe_hdr_rfq_control_no`, `invoice_batch`, `customer`, `currency_line`, `quote_hdr`, `crm_contact_information`, `pegmost_oe_hdr`, `carrier_contract_hdr`, `oe_hdr_notepad`, `oe_hdr_integration`, `country_subdivision`

| Field | Stored in | Basis |
|---|---|---|
| `original_promise_date` | `oe_hdr.original_promise_date` | column |
| `promise_date` | `oe_hdr.promise_date` | column |
| `promise_date_extended_desc` | `oe_hdr.promise_date_extended_desc` | column |
| `convert_to_order` | computed: `'N'` | probed |
| `promise_date_edited_date` | `oe_hdr.promise_date_edited_date` | column |

| # | Label | table.column / expression |
|---|---|---|
| 113 | Promise Date: | `oe_hdr.promise_date` |
| 114 | Original Promise Date: | `oe_hdr.original_promise_date` |
| 120 | Date Edited: | `oe_hdr.promise_date_edited_date` |
| 121 | Promise Date Notes: | `oe_hdr.promise_date_extended_desc` |

### `TP_SHIPMENTS.tp_shipments` (Shipments)

- Update table: `none reported` (tool reported 'clause*/' (misparse of SQL comments; treat as unknown))
- Tables in the SELECT: `oe_pick_ticket`, `oe_hdr`, `p21_view_clippership_return_<id>`, `freight_code`, `shipment`, `address`, `code_p21`, `company_strategic_pricing`, `location`, `invoice_hdr`, `oe_pick_ticket_detail`, `oe_line`, `oe_line_lot_billing`, `oe_pick_ticket_ups`, `shipping_route`, `contacts`, `system_setting`

| Field | Stored in | Basis |
|---|---|---|
| `c_tracking_no` | computed: `COALESCE( p21_view_clippership_return_<id>.tracking_no, ptshipment.shipment_id, oe_pick_ticket.tracking_no )` | alias |
| `shipment_transaction_no` | computed: `CASE ptshipment.transaction_type_cd WHEN 222 THEN oe_hdr.order_no ELSE oe_pick_ticket.pick_ticket_no END` | probed |
| `print_date` | `oe_pick_ticket.print_date` | probed |
| `c_carrier` | computed: `COALESCE( p21_view_clippership_return_<id>.carrier_name, address.name )` | alias |
| `freight_code` | `freight_code.freight_cd` | probed |
| `freight_in` | `oe_pick_ticket.freight_in` | alias |
| `c_freight_out` | computed: `COALESCE( p21_view_clippership_return_<id>.total_charge, oe_pick_ticket.freight_out, 0.00 )` | alias |
| `c_ship_date` | computed: `COALESCE( p21_view_clippership_return_<id>.shipped_date, oe_pick_ticket.ship_date )` | probed |
| `invoice_no` | `oe_pick_ticket.invoice_no` | column |
| `shipment_type_display` | computed: `CASE WHEN oe_pick_ticket_type_cd = 1921 THEN 'Parts Pick Ticket' WHEN oe_pick_ticket_type_cd = 1922 THEN 'Service Pick Ticket' WHEN oe_pick_ticket.direct_shipment = 'Y' THEN 'Direct Shipment' WHEN oe_pick_ticket.auxiliary = 'Y' THEN 'Auxiliary Pick Ticket' WHEN oe_pick_ticket.pick_and_hold = 'Y' THEN CASE WHEN oe_hdr.packing_basis = 'Tag and Hold' THEN 'Tag And Hold' ELSE 'Pick And Hold' END ELSE CASE ptshipment.transaction_type_cd WHEN 222 THEN 'Shipped via Order Entry' ELSE 'Regular Pick Ticket' END END + CASE WHEN COALESCE( p21_view_clippership_return_<id>.clippership_return_uid, 0 ) <> 0 THEN CASE system_setting.value WHEN 'Y' THEN ' (Quick Ship)' ELSE ' (Clippership)' END WHEN COALESCE( ptshipment.shipment_uid, 0 ) <> 0 THEN ' (' + carriertype.code_description + ')' ELSE '' END` | alias |
| `rowfocusindicatorcol` | computed: `(computed in the datawindow)` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 2 | Print Date | `oe_pick_ticket.print_date` |
| 3 | Carrier | `c_carrier` |
| 4 | Tracking Number/Shipment ID | `c_tracking_no` |
| 5 | Freight Out | `c_freight_out` |
| 6 | Freight In | `oe_pick_ticket.freight_in` |
| 8 | Ship Date | `c_ship_date` |
| 9 | Invoice No | `oe_pick_ticket.invoice_no` |
| 15 | Freight Code | `freight_code.freight_cd` |
| 21 | Shipment Type | `shipment_type_display` |
| 22 | Transaction Number | `transaction_no` |

### `TP_CLASS.tp_class` (Classes)

- Update table: `oe_hdr`
- Tables in the SELECT: `oe_hdr`, `company`, `users`, `address`, `ship_to`, `freight_code`, `shipping_route`, `p21_view_oe_hdr_rfq_control_no`, `invoice_batch`, `customer`, `currency_line`, `quote_hdr`, `crm_contact_information`, `pegmost_oe_hdr`, `carrier_contract_hdr`, `oe_hdr_notepad`, `oe_hdr_integration`, `country_subdivision`

| Field | Stored in | Basis |
|---|---|---|
| `oe_hdr_class_1id` | `oe_hdr.class_1id` | probed |
| `oe_hdr_class_2id` | `oe_hdr.class_2id` | probed |
| `oe_hdr_class_3id` | `oe_hdr.class_3id` | probed |
| `oe_hdr_class_4id` | `oe_hdr.class_4id` | probed |
| `oe_hdr_class_5id` | `oe_hdr.class_5id` | probed |
| `convert_to_order` | computed: `'N'` | alias |

| # | Label | table.column / expression |
|---|---|---|
| 23 | Class 1: | `oe_hdr.class_1id` |
| 24 | Class 2: | `oe_hdr.class_2id` |
| 25 | Class 3: | `oe_hdr.class_3id` |
| 26 | Class 4: | `oe_hdr.class_4id` |
| 27 | Class 5: | `oe_hdr.class_5id` |

### `TP_AGING.tp_aging` (Aging)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `age_by` | ? | no_sql |
| `period1` | ? | no_sql |
| `period2` | ? | no_sql |
| `period3` | ? | no_sql |
| `current_due` | ? | no_sql |
| `bucket4_total` | ? | no_sql |
| `bucket1_total` | ? | no_sql |
| `bucket3_total` | ? | no_sql |
| `bucket2_total` | ? | no_sql |
| `total` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Age By: | `age_by` |
| 2 | Period1: | `period1` |
| 3 | Period2: | `period2` |
| 4 | Period3: | `period3` |
| 5 | 1 - 30 Days | `bucket1_total` |
| 6 | 31 - 60 Days | `bucket2_total` |
| 7 | 61 - 90 Days | `bucket3_total` |
| 8 | OVER 90 Days | `bucket4_total` |
| 9 | Current Due | `current_due` |
| calc | Total: | `bucket1_total + bucket2_total + bucket3_total + bucket4_total + current_due` |

### `TP_CUSTSALESHISTORY.filter_components` (Customer Sales History)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `show_components` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Show Components | `filter_out_components` |

### `TP_CUSTSALESHISTORY.start_date` (Customer Sales History)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `start_date` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Start Date: | `start_date` |

### `TP_CUSTSALESHISTORY.customer_sales_history` (Customer Sales History)

- Update table: `system_setting` (tool reported system_setting, the first FROM table of a read-only grid; treat as read-only)
- Tables in the SELECT: `system_setting`, `invoice_line`, `invoice_hdr`, `inv_mast`, `job_price_line`, `job_price_hdr`, `oe_hdr`, `currency_line`, `invoice_line_taxes`, `customer`, `item_uom`

| Field | Stored in | Basis |
|---|---|---|
| `ship2_name` | `invoice_hdr.ship2_name` | column |
| `item_id` | computed: `COALESCE(inv_mast.item_id, invoice_line.item_id)` | alias |
| `item_desc` | computed: `COALESCE(inv_mast.item_desc, invoice_line.item_desc)` | alias |
| `order_no` | `invoice_hdr.order_no` | column |
| `order_date` | `invoice_hdr.order_date` | column |
| `invoice_date` | `invoice_hdr.invoice_date` | column |
| `cc_invoice_no_display` | `invoice_hdr.invoice_no` | probed |
| `credit_or_rebill` | computed: `CASE WHEN invoice_hdr.invoice_adjustment_type = 'C' AND invoice_hdr.source_type_cd = 2638 THEN 'Credit' WHEN invoice_hdr.record_type_cd = 2594 THEN 'Rebill' ELSE '' END` | alias |
| `location_id` | `invoice_hdr.sales_location_id` | probed |
| `unit_of_measure` | `invoice_line.unit_of_measure` | column |
| `pricing_unit` | `invoice_line.pricing_unit` | column |
| `unit_price` | `invoice_line.unit_price` | column |
| `extended_price` | `invoice_line.extended_price` | column |
| `c_comparison_cost` | computed: `CASE customer.invoice_comp_cost_cd_tier1 WHEN 2110 THEN CASE WHEN (invoice_line.commission_cost * invoice_line.pricing_unit_size <> 0) THEN invoice_line.commission_cost * invoice_line.pricing_unit_size ELSE CASE customer.invoice_comp_cost_cd_tier2 WHEN 2111 THEN CASE WHEN (CASE invoice_line.qty_shipped WHEN 0 THEN 0 ELSE CAST(invoice_line.cogs_amount / (invoice_line.qty_shipped / invoice_line.pricing_unit_size) AS Decimal(19,9)) END) <> 0 THEN invoice_line.cogs_amount / (invoice_line.qty_shipped / invoice_line.pricing_unit_size) ELSE invoice_line.other_cost * invoice_line.pricing_unit_size END WHEN 1195 THEN CASE WHEN (invoice_line.other_cost * invoice_line.pricing_unit_size <> 0) THEN invoice_line.other_cost * invoice_line.pricing_unit_size ELSE (CASE invoice_line.qty_shipped WHEN 0 THEN 0 ELSE CAST(invoice_line.cogs_amount / (invoice_line.qty_shipped / invoice_line.pricing_unit_size) AS Decimal(19,9)) END) END END END WHEN 2111 THEN CASE WHEN (CASE invoice_line.qty_shipped WHEN 0 THEN 0 ELSE CAST(invoice_line.cogs_amount / (invoice_line.qty_shipped / invoice_line.pricing_unit_size) AS Decimal(19,9)) END) <> 0 THEN invoice_line.cogs_amount / (invoice_line.qty_shipped / invoice_line.pricing_unit_size) ELSE CASE customer.invoice_comp_cost_cd_tier2 WHEN 2110 THEN CASE WHEN (invoice_line.commission_cost * invoice_line.pricing_unit_size <> 0) THEN invoice_line.commission_cost * invoice_line.pricing_unit_size ELSE invoice_line.other_cost * invoice_line.pricing_unit_size END WHEN 1195 THEN CASE WHEN (invoice_line.other_cost * invoice_line.pricing_unit_size <> 0) THEN invoice_line.other_cost * invoice_line.pricing_unit_size ELSE invoice_line.commission_cost * invoice_line.pricing_unit_size END END END WHEN 1195 THEN CASE WHEN (invoice_line.other_cost * invoice_line.pricing_unit_size <> 0) THEN invoice_line.other_cost * invoice_line.pricing_unit_size ELSE CASE customer.invoice_comp_cost_cd_tier2 WHEN 2110 THEN CASE WHEN (invoice_line.commission_cost * invoice_line.pricing_unit_size <> 0) THEN invoice_line.commission_cost * invoice_line.pricing_unit_size ELSE (CASE invoice_line.qty_shipped WHEN 0 THEN 0 ELSE CAST(invoice_line.cogs_amount / (invoice_line.qty_shipped / invoice_line.pricing_unit_size) AS Decimal(19,9)) END) END WHEN 2111 THEN CASE WHEN (CASE invoice_line.qty_shipped WHEN 0 THEN 0 ELSE CAST(invoice_line.cogs_amount / (invoice_line.qty_shipped / invoice_line.pricing_unit_size) AS Decimal(19,9)) END) <> 0 THEN invoice_line.cogs_amount / (invoice_line.qty_shipped / invoice_line.pricing_unit_size) ELSE invoice_line.commission_cost * invoice_line.pricing_unit_size END END END END` | alias |
| `c_extended_comparison_cost` | computed: `CASE customer.invoice_comp_cost_cd_tier1 WHEN 2110 THEN CASE WHEN (invoice_line.commission_cost * invoice_line.qty_shipped <> 0) THEN invoice_line.commission_cost * invoice_line.qty_shipped ELSE CASE customer.invoice_comp_cost_cd_tier2 WHEN 2111 THEN CASE WHEN (invoice_line.cogs_amount <> 0) THEN invoice_line.cogs_amount ELSE invoice_line.other_cost * invoice_line.qty_shipped END WHEN 1195 THEN CASE WHEN (invoice_line.other_cost * invoice_line.qty_shipped <> 0) THEN invoice_line.other_cost * invoice_line.qty_shipped ELSE invoice_line.cogs_amount END END END WHEN 2111 THEN CASE WHEN (invoice_line.cogs_amount <> 0) THEN invoice_line.cogs_amount ELSE CASE customer.invoice_comp_cost_cd_tier2 WHEN 2110 THEN CASE WHEN (invoice_line.commission_cost * invoice_line.qty_shipped <> 0) THEN invoice_line.commission_cost * invoice_line.qty_shipped ELSE invoice_line.other_cost * invoice_line.qty_shipped END WHEN 1195 THEN CASE WHEN (invoice_line.other_cost * invoice_line.qty_shipped <> 0) THEN invoice_line.other_cost * invoice_line.qty_shipped ELSE invoice_line.commission_cost * invoice_line.qty_shipped END END END WHEN 1195 THEN CASE WHEN (invoice_line.other_cost * invoice_line.qty_shipped <> 0) THEN invoice_line.other_cost * invoice_line.qty_shipped ELSE CASE customer.invoice_comp_cost_cd_tier2 WHEN 2110 THEN CASE WHEN (invoice_line.commission_cost * invoice_line.qty_shipped <> 0) THEN invoice_line.commission_cost * invoice_line.qty_shipped ELSE invoice_line.cogs_amount END WHEN 2111 THEN CASE WHEN (invoice_line.cogs_amount <> 0) THEN invoice_line.cogs_amount ELSE invoice_line.commission_cost * invoice_line.qty_shipped END END END END` | alias |
| `c_taxable` | `derv_taxable.taxable` | alias |
| `c_direct_ship` | computed: `CASE invoice_hdr.source_type_cd WHEN 1129 THEN 'Y' WHEN 1924 THEN 'Y' ELSE 'N' END` | alias |
| `c_unitcost` | computed: `CASE invoice_line.qty_shipped WHEN 0 THEN 0 ELSE (CASE :cost_type WHEN 2 THEN invoice_line.commission_cost * invoice_line.qty_shipped WHEN 3 THEN invoice_line.other_cost * invoice_line.qty_shipped ELSE invoice_line.cogs_amount END) / (qty_shipped / COALESCE(invoice_line.pricing_unit_size, 1)) END` | probed |
| `cogs_amount` | computed: `CASE :cost_type WHEN 2 THEN invoice_line.commission_cost * invoice_line.qty_shipped WHEN 3 THEN invoice_line.other_cost * invoice_line.qty_shipped ELSE invoice_line.cogs_amount END` | alias |
| `contract_no` | `job_price_hdr.contract_no` | column |
| `job_description` | `job_price_hdr.job_description` | column |
| `line_no` | `job_price_line.line_no` | probed |
| `ordered` | computed: `(computed in the datawindow)` | probed |
| `shipped` | computed: `(computed in the datawindow)` | probed |
| `profit` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Invoice Date | `invoice_hdr.invoice_date` |
| 5 | Unit Price | `invoice_line.unit_price` |
| 6 | OrderUOM | `invoice_line.unit_of_measure` |
| 7 | ExtendedPrice | `invoice_line.extended_price` |
| 9 | OrderNumber | `invoice_hdr.order_no` |
| 10 | Contract Ln # | `job_price_line.line_no` |
| 11 | Contract No | `job_price_hdr.contract_no` |
| 12 | Contract Description | `job_price_hdr.job_description` |
| 13 | Extended Cost | `invoice_line.cogs_amount` |
| 14 | UnitCost | `c_unitcost` |
| 15 | Ship To Name | `invoice_hdr.ship2_name` |
| 16 | Item ID | `inv_mast.item_id` |
| 17 | Item Description | `inv_mast.item_desc` |
| 19 | PrcUOM | `invoice_line.pricing_unit` |
| 21 | Location | `invoice_hdr.sales_location_id` |
| 22 | Order Date | `invoice_hdr.order_date` |
| 24 | ComparisonCost | `c_comparison_cost` |
| 25 | Ext ComparisonCost | `c_extended_comparison_cost` |
| 26 | Taxable | `c_taxable` |
| 27 | DS | `c_direct_ship` |
| 32 | Invoice Number | `cc_invoice_no_display` |
| 33 | Credit or Rebill | `credit_or_rebill` |
| calc | Quantity Ordered | `IF (IsNull(qty_requested), 0, qty_requested /  order_unit_size)` |
| calc | Quantity Shipped | `IF (IsNull(qty_shipped), 0, qty_shipped / order_unit_size)` |
| calc | Profit % | `(( extended_price -  cogs_amount ) /  extended_price ) * 100` |

### `TP_SCHEDULE.schedule_hdr` (Release Schedule)

- Update table: `oe_schedule`
- Tables in the SELECT: `oe_schedule`

| Field | Stored in | Basis |
|---|---|---|
| `release_type` | `oe_schedule.release_type` | column |
| `round_type` | `oe_schedule.round_type` | column |
| `default_to_all` | `oe_schedule.default_to_all` | column |
| `first_date` | `oe_schedule.first_date` | column |
| `total_releases` | `oe_schedule.total_releases` | column |
| `frequency_value` | `oe_schedule.frequency_value` | column |
| `frequency_type` | `oe_schedule.frequency_type` | column |
| `expedite_value` | `oe_schedule.expedite_value` | column |
| `expedite_type` | `oe_schedule.expedite_type` | column |
| `pick_value` | `oe_schedule.pick_value` | column |
| `pick_type` | `oe_schedule.pick_type` | column |

| # | Label | table.column / expression |
|---|---|---|
| 2 | Release By: | `oe_schedule.release_type` |
| 3 | Round Quantity On: | `oe_schedule.round_type` |
| 4 | First Date: | `oe_schedule.first_date` |
| 5 | Total Releases: | `oe_schedule.total_releases` |
| 6 | Every | `oe_schedule.frequency_value` |
| 7 | Frequency Type | `oe_schedule.frequency_type` |
| 8 | Expedite Before Release Date: | `oe_schedule.expedite_value` |
| 9 | Expedite Type | `oe_schedule.expedite_type` |
| 10 | Pick Before Release Date: | `oe_schedule.pick_value` |
| 11 | Pick Type | `oe_schedule.pick_type` |
| 15 | Default To All | `oe_schedule.default_to_all` |

### `TP_SCHEDULE.schedule_detail` (Release Schedule)

- Update table: `oe_schedule_detail`
- Tables in the SELECT: `oe_schedule_detail`

| Field | Stored in | Basis |
|---|---|---|
| `release_date` | `oe_schedule_detail.release_date` | column |
| `expedite_value` | `oe_schedule_detail.expedite_value` | column |
| `expedite_type` | `oe_schedule_detail.expedite_type` | column |
| `pick_value` | `oe_schedule_detail.pick_value` | column |
| `pick_type` | `oe_schedule_detail.pick_type` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Release Date | `oe_schedule_detail.release_date` |
| 4 | Expedite Value | `oe_schedule_detail.expedite_value` |
| 5 | Expedite Type | `oe_schedule_detail.expedite_type` |
| 6 | Pick Time | `oe_schedule_detail.pick_value` |
| 7 | Pick Type | `oe_schedule_detail.pick_type` |

### `TP_STRATEGICPRICING.tp_strategicpricing` (Strategic Pricing)

- Update table: `price_library`
- Tables in the SELECT: `price_library`, `customer_category`, `code_p21`, `oe_hdr`

| Field | Stored in | Basis |
|---|---|---|
| `customer_size_desc` | `code_p21.code_description` | alias |
| `customer_category_id` | `customer_category.customer_category_id` | column |
| `price_library_id` | `price_library.price_library_id` | probed |
| `original_price_library_id` | `price_library.price_library_id` | alias |

| # | Label | table.column / expression |
|---|---|---|
| 2 | Strategic Price Library | `price_library.price_library_id` |
| 19 | Customer Category | `customer_category.customer_category_id` |
| 23 | Customer Size | `customer_size_desc` |
| 24 | Original Strategic Price Library | `price_library_original.price_library_id` |

### `OPPORTUNITIES.opportunities` (Opportunities)

- Update table: `opportunity_x_order`
- Tables in the SELECT: `opportunity_x_order`, `opportunity`

| Field | Stored in | Basis |
|---|---|---|
| `opportunity_id` | `opportunity.opportunity_id` | column |
| `opportunity_name` | `opportunity.opportunity_name` | column |
| `opportunity_type_uid` | `opportunity.opportunity_type_uid` | column |
| `opportunity_status_uid` | `opportunity.opportunity_status_uid` | column |
| `opportunity_stage_uid` | `opportunity.opportunity_stage_uid` | column |
| `opportunity_size` | `opportunity.opportunity_size` | column |

| # | Label | table.column / expression |
|---|---|---|
| 4 | Opportunity ID | `opportunity.opportunity_id` |
| 5 | Opportunity Name | `opportunity.opportunity_name` |
| 6 | Opportunity Type | `opportunity.opportunity_type_uid` |
| 7 | Opportunity Status | `opportunity.opportunity_status_uid` |
| 8 | Opportunity Stage | `opportunity.opportunity_stage_uid` |
| 13 | Opportunity Size | `opportunity.opportunity_size` |

### `DOCUMENT_LINK.document_link` (Document Links)

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
| `user_email_flag` | computed: `'N'` | alias |
| `outside_use_flag` | `document_link.outside_use_flag` | column |
| `send_outside_use_print_flag` | `document_link_entity_req.send_outside_use_print_flag` | alias |
| `document_link_uid` | `document_link.document_link_uid` | column |
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

### `TP_TASKS.oe_hdr_tasks_access` (Tasks)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `task_access_flag` | ? | no_sql |
| `display_end_date` | ? | no_sql |
| `task_assignment_flag` | ? | no_sql |
| `filter_by` | ? | no_sql |
| `filter_value` | ? | no_sql |
| `filter_value_subject` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Task Access Flag | `task_access_flag` |
| 5 | Filter By: | `filter_by` |

### `TP_TASKS.oe_hdr_tasks` (Tasks)

- Update table: `activity_trans`
- Tables in the SELECT: `activity_trans`, `activity`, `oe_hdr`, `contacts`, `serial_number`, `inv_mast`, `problem_code`, `alarm_code`

| Field | Stored in | Basis |
|---|---|---|
| `comments` | `activity_trans.comments` | column |
| `activity_id` | `activity_trans.activity_id` | column |
| `activity_desc` | `activity.activity_desc` | column |
| `contact_name` | computed: `contacts.first_name + ' ' + COALESCE(contacts.mi + ' ', '') + contacts.last_name` | alias |
| `assigned_to_id` | `activity_trans.assigned_to_id` | probed |
| `target_complete_date` | `activity_trans.target_complete_date` | column |
| `completed_flag` | `activity_trans.completed_flag` | column |
| `subject` | `activity_trans.subject` | column |
| `compute_1` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Activity | `activity_trans.activity_id` |
| 2 | Activity Description | `activity.activity_desc` |
| 3 | Contact Name | `contact_name` |
| 4 | Assigned To | `activity_trans.assigned_to_id` |
| 5 | Target Complete Date | `activity_trans.target_complete_date` |
| 6 | Completed | `activity_trans.completed_flag` |
| 7 | Subject | `activity_trans.subject` |
| 8 | Comments | `activity_trans.comments` |

### `TP_TRANS_X_GL_DIMENSION.tp_trans_x_gl_dimension` (GL Dimensions)

- Update table: `trans_x_gl_dimension`
- Tables in the SELECT: `trans_x_gl_dimension`, `gl_dimen_type`

| Field | Stored in | Basis |
|---|---|---|
| `gl_dimen_type_id` | `gl_dimen_type.gl_dimen_type_id` | column |
| `gl_dimension_id` | `trans_x_gl_dimension.gl_dimension_id` | column |
| `delete_flag` | computed: `'N'` | alias |
| `gl_dimen_type_uid` | `trans_x_gl_dimension.gl_dimen_type_uid` | column |
| `gl_dimen_type_desc` | `gl_dimen_type.gl_dimen_type_desc` | column |
| `gl_dimension_desc` | `trans_x_gl_dimension.gl_dimension_desc` | column |
| `rowfocusindicator` | computed: `(computed in the datawindow)` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 3 | Value | `trans_x_gl_dimension.gl_dimension_id` |
| 4 | Value Name | `trans_x_gl_dimension.gl_dimension_desc` |
| 9 | Delete | `delete_flag` |
| 12 | Type ID | `gl_dimen_type.gl_dimen_type_id` |
| 13 | Type Desc | `gl_dimen_type.gl_dimen_type_desc` |

### `TP_SHIPTOPRICING.ship_to_pricing_hdr` (Ship To Pricing)

- Update table: `ship_to`
- Tables in the SELECT: `ship_to`

| Field | Stored in | Basis |
|---|---|---|
| `pricing_method_cd` | `ship_to.pricing_method_cd` | column |
| `ship_to_id` | `ship_to.ship_to_id` | column |

| # | Label | table.column / expression |
|---|---|---|
| 2 | Ship To ID: | `ship_to.ship_to_id` |
| 3 | Pricing Method: | `ship_to.pricing_method_cd` |

### `TP_SHIPTOPRICING.ship_to_pricing_detail` (Ship To Pricing)

- Update table: `price_library_x_ship_to`
- Tables in the SELECT: `price_library_x_ship_to`, `ship_to`, `price_library`

| Field | Stored in | Basis |
|---|---|---|
| `price_library_id` | `price_library.price_library_id` | column |
| `description` | `price_library.description` | column |
| `row_status_flag` | `price_library_x_ship_to.row_status_flag` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 4 | Library ID | `price_library.price_library_id` |
| 5 | Library Description | `price_library.description` |
| 6 | Status | `price_library_x_ship_to.row_status_flag` |

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

- Update table: `p21_view_audit_trail_oe_hdr_<id>`
- Tables in the SELECT: `p21_view_audit_trail_oe_hdr_<id>`
- Mapped off-tab: the API could not select this tab (HTTP 400: Multiple tabs have a name or display text of TIMESTAMP.); SQL Information reads an instantiated datawindow whichever tab is active

| Field | Stored in | Basis |
|---|---|---|
| `line_no` | `p21_view_audit_trail_oe_hdr_<id>.line_no` | probed |
| `item_id` | `p21_view_audit_trail_oe_hdr_<id>.item_id` | probed |
| `column_description` | `p21_view_audit_trail_oe_hdr_<id>.column_description` | probed |
| `old_value` | `p21_view_audit_trail_oe_hdr_<id>.old_value` | probed |
| `new_value` | `p21_view_audit_trail_oe_hdr_<id>.new_value` | probed |
| `date_created` | `p21_view_audit_trail_oe_hdr_<id>.date_created` | probed |
| `created_by` | `p21_view_audit_trail_oe_hdr_<id>.created_by` | probed |
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
| calc | Order No | `"IF ((source_area_cd = 1763 and key1_cd = 'service_labor_uid'), item_id,  IF (source_area_cd = 950, key1_value,  IF (key2_cd = 'item_service_uid',  Item_id + ' / ALL / ALL',  IF ( key2_cd = 'lot_cd', key2_value,   IF ( Len(auxiliary_value) > 0 AND source_area_cd IN (1544, 1250, 2531), auxiliary_value,  IF (source_area_cd = 1314 and table_changed = 'inv_mast_strategic_pricing', item_id + '/' + key3_value + IF (IsNull(key2_value), '', '/' + auxiliary_value),  IF ( key1_cd = 'inv_mast_uid', item_id, key1_value ) + IF ( IsNull ( key2_value) AND source_area_cd <> 1314, '', ' / ' + IF ( key2_cd = 'inv_mast_uid', item_id, IF ( IsNull ( key2_value ), 'ALL', key2_value ) )  + IF ( IsNull (key3_value) AND source_area_cd <> 1314, '', ' / ' + IF ( key3_cd = 'inv_mast_uid', item_id, IF ( IsNull ( key3_value ), 'ALL', key3_value ) ) ) )  ) ) ) ) ) )"` |
| calc | 'Sub Line No | `` |

### `TP_ITEMS.items` (Items)

- Update table: `oe_line`
- Tables in the SELECT: `oe_line`, `inv_loc`, `inv_mast`, `product_group`, `item_uom`, `inventory_supplier`, `inventory_supplier_x_loc`, `tpcx_dead_stock`, `supplier`, `inv_loc_stock_status`, `inv_mast_assem_info`, `oe_line_hose_assembly`, `oe_line_last_margin_price`, `address`, `oe_hdr`, `revision_transaction`, `p21_view_getrevisionlotquantity`, `item_revision`, `oe_line_po`, `job_price_line`, `oe_line_promise_date`, `oe_line_labor`, `operation`, `service_labor`, `carrier_contract_line`, `carrier_contract_z_line`, `oe_line_room`, `room`, `oe_line_notepad`, `room_area`, `p21_view_oe_line_anticipated_allocation_summary`, `oe_line_lot_billing`, `restricted_class`, `transfer_hdr`, `oe_line_rma`, `invoice_line`, `price_page`, `price_family`, `shipping_route`

| Field | Stored in | Basis |
|---|---|---|
| `oe_order_item_id` | `inv_mast.item_id` | probed |
| `item_desc` | `inv_mast.item_desc` | column |
| `unit_quantity` | `oe_line.unit_quantity` | column |
| `unit_of_measure` | `oe_line.unit_of_measure` | column |
| `disposition` | `oe_line.disposition` | column |
| `unit_price` | `oe_line.unit_price` | column |
| `extended_price` | `oe_line.extended_price` | column |
| `user_line_no` | `oe_line.user_line_no` | column |
| `sales_cost_profit` | computed: `CASE oe_line.extended_price WHEN 0 THEN 0 ELSE (oe_line.extended_price - (( oe_line.sales_cost / oe_line.pricing_unit_size ) * oe_line.qty_ordered)) / oe_line.extended_price * 100 END` | alias |
| `sales_cost` | `oe_line.sales_cost` | column |
| `trans_revision_level` | `item_revision.revision_level` | alias |
| `commission_cost` | `oe_line.commission_cost` | column |
| `commission_cost_profit` | computed: `CASE oe_line.extended_price WHEN 0 THEN 0 ELSE (oe_line.extended_price - (( oe_line.commission_cost / oe_line.pricing_unit_size ) * oe_line.qty_ordered)) / oe_line.extended_price * 100 END` | alias |
| `other_cost` | `oe_line.other_cost` | column |
| `other_cost_profit` | computed: `CASE oe_line.extended_price WHEN 0 THEN 0 ELSE (oe_line.extended_price - (( oe_line.other_cost / oe_line.pricing_unit_size ) * oe_line.qty_ordered)) / oe_line.extended_price * 100 END` | alias |
| `po_cost` | `oe_line.po_cost` | column |
| `po_cost_profit` | computed: `100.00` | alias |
| `export_parker_printer_name` | `oe_line.export_parker_printer_name` | column |
| `export_parker_label_copies` | `oe_line.export_parker_label_copies` | column |
| `extended_desc` | `oe_line.extended_desc` | probed |
| `create_trackabout_lease_flag` | `oe_line.create_trackabout_lease_flag` | column |
| `ship_loc_id` | `oe_line.ship_loc_id` | column |
| `source_loc_id` | `oe_line.source_loc_id` | column |
| `quote_price_disposition` | `oe_line.quote_price_disposition` | column |
| `customer_part_number` | `oe_line.customer_part_number` | column |
| `estimated_labor_cost` | `oe_line_labor.estimated_labor_cost` | column |
| `qty_available_to_make` | computed: `0.0000` | alias |
| `list_price` | computed: `CASE WHEN COALESCE(inventory_supplier_x_loc.loc_list_price, 0) <> 0 THEN inventory_supplier_x_loc.loc_list_price ELSE inventory_supplier.list_price END` | probed |
| `c_sum_comp_cost` | computed: `null` | alias |
| `prev_profit_percent` | `oe_line_last_margin_price.prev_profit_percent` | column |
| `cf_expandableindicator` | computed: `(computed in the datawindow)` | dw_name |
| `quantity_available` | computed: `(computed in the datawindow)` | probed |
| `cf_price_break_indicator` | computed: `(computed in the datawindow)` | dw_name |
| `cf_prev_unit_price` | computed: `(computed in the datawindow)` | dw_name |
| `cf_prev_unit_qty_ordered` | computed: `(computed in the datawindow)` | dw_name |
| `open_value` | computed: `(computed in the datawindow)` | probed |
| `compute_1` | computed: `(computed in the datawindow)` | dw_name |
| `bo_amount` | computed: `(computed in the datawindow)` | probed |
| `bo_tax_amount` | computed: `(computed in the datawindow)` | probed |
| `amt_cancelled` | computed: `(computed in the datawindow)` | probed |
| `sum_price` | computed: `(computed in the datawindow)` | dw_name |
| `bo_balance` | computed: `(computed in the datawindow)` | probed |
| `max_line_no` | computed: `(computed in the datawindow)` | probed |
| `sum_downpayment` | computed: `(computed in the datawindow)` | dw_name |
| `sum_tax` | computed: `(computed in the datawindow)` | dw_name |
| `canceled_qty` | computed: `(computed in the datawindow)` | probed |
| `total_amt_invoiced` | computed: `(computed in the datawindow)` | probed |
| `cf_cancelled_qty` | computed: `(computed in the datawindow)` | dw_name |
| `open_cost` | computed: `(computed in the datawindow)` | probed |
| `sum_bo_tax_amount` | computed: `(computed in the datawindow)` | dw_name |
| `total_amt_cancelled` | computed: `(computed in the datawindow)` | probed |
| `cf_total_amt_cancelled` | computed: `(computed in the datawindow)` | dw_name |
| `invoiced_qty` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |
| `total_lines` | computed: `(computed in the datawindow)` | probed |
| `open_line_total` | computed: `(computed in the datawindow)` | probed |
| `extended_price_total` | computed: `(computed in the datawindow)` | probed |
| `sum_open_value` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_profit` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Item ID | `inv_mast.item_id` |
| 3 | UOM | `oe_line.unit_of_measure` |
| 4 | Disp | `oe_line.disposition` |
| 5 | Unit Price | `oe_line.unit_price` |
| 6 | Extended Price | `oe_line.extended_price` |
| 7 | Description | `inv_mast.item_desc` |
| 10 | Order Cost | `oe_line.sales_cost` |
| 23 | Source Location ID | `oe_line.source_loc_id` |
| 24 | Ship Location ID | `oe_line.ship_loc_id` |
| 31 | Extended Desc | `oe_line.extended_desc` |
| 44 | Qty Ordered | `oe_line.unit_quantity` |
| 61 | Other Cost | `oe_line.other_cost` |
| 62 | Commission Cost | `oe_line.commission_cost` |
| 64 | Profit % | `sales_cost_profit` |
| 65 | Profit % | `commission_cost_profit` |
| 66 | Profit % | `other_cost_profit` |
| 81 | Customer Part Number | `oe_line.customer_part_number` |
| 82 | PO Cost | `oe_line.po_cost` |
| 84 | Profit % | `po_cost_profit` |
| 140 | Qty Avail To Make | `qty_available_to_make` |
| 153 | List Price | `inventory_supplier.list_price` |
| 162 | Prev Profit % | `oe_line_last_margin_price.prev_profit_percent` |
| 192 | Cust Line No | `oe_line.user_line_no` |
| 249 | Unit Labor Cost | `oe_line_labor.estimated_labor_cost` |
| 271 | Unit Matl Cost | `c_sum_comp_cost` |
| 530 | Price Disp | `oe_line.quote_price_disposition` |
| calc | = if(((oe_line_assembly in ('B', 'P')) and (qty_ordered > 0)) or (lot_bill | `'Y'), "+","")` |
| calc | Qty Available | `if( ( inv_loc_qty_on_hand  - if( inv_loc_qty_allocated < 0, 0,  inv_loc_qty_allocated) - qty_non_pickable - qty_quarantined - qty_frozen  - if(isNull(qty_reserved), 0, qty_reserved))   /  unit_size < 0, 0 ,   (inv_loc_qty_on_hand  - if( inv_loc_qty_allocated < 0, 0, inv_loc_qty_allocated )  - qty_non_pickable - qty_quarantined - qty_frozen  - if(isNull(qty_reserved), 0, qty_reserved))  /  unit_size)` |
| calc | Prev Unit Price | `if((isNull(unit_size) OR (unit_size = 0) OR IsNull(prev_sku_price)), 0, prev_sku_price * pricing_unit_size )` |
| calc | Prev Qty Ordered | `if((isNull(unit_size) OR (unit_size = 0) OR IsNull(prev_qty_ordered)), 0, prev_qty_ordered / unit_size )` |

### `TP_EXTDINFO.extd_info` (Ext'd Info)

- Update table: `oe_line`
- Tables in the SELECT: `oe_line`, `inv_loc`, `inv_mast`, `product_group`, `item_uom`, `inventory_supplier`, `inventory_supplier_x_loc`, `tpcx_dead_stock`, `supplier`, `inv_loc_stock_status`, `inv_mast_assem_info`, `oe_line_hose_assembly`, `oe_line_last_margin_price`, `address`, `oe_hdr`, `revision_transaction`, `p21_view_getrevisionlotquantity`, `item_revision`, `oe_line_po`, `job_price_line`, `oe_line_promise_date`, `oe_line_labor`, `operation`, `service_labor`, `carrier_contract_line`, `carrier_contract_z_line`, `oe_line_room`, `room`, `oe_line_notepad`, `room_area`, `p21_view_oe_line_anticipated_allocation_summary`, `oe_line_lot_billing`, `restricted_class`, `transfer_hdr`, `oe_line_rma`, `invoice_line`, `price_page`, `price_family`, `shipping_route`

| Field | Stored in | Basis |
|---|---|---|
| `oe_order_item_id` | `inv_mast.item_id` | probed |
| `item_desc` | `inv_mast.item_desc` | column |
| `extended_desc` | `oe_line.extended_desc` | probed |
| `source_loc_id` | `oe_line.source_loc_id` | column |
| `ship_loc_id` | `oe_line.ship_loc_id` | column |
| `product_group_id` | `oe_line.product_group_id` | column |
| `supplier_id_by_item` | `oe_line.supplier_id` | probed |
| `oe_division_id` | `inventory_supplier.division_id` | probed |
| `item_bill_to_id` | `oe_line.item_bill_to_id` | column |
| `routing_status_flag` | `oe_line.routing_status_flag` | probed |
| `tank_name` | `oe_line.tank_name` | column |
| `required_date` | `oe_line.required_date` | column |
| `expedite_date` | `oe_line.expedite_date` | column |
| `pick_date` | `oe_line.pick_date` | column |
| `use_strategic_freight` | computed: `''` | alias |
| `freight_in` | `oe_line.freight_in` | column |
| `item_terms_discount_pct` | `oe_line.item_terms_discount_pct` | column |
| `will_call` | `oe_line.will_call` | column |
| `tax_item` | `oe_line.tax_item` | column |
| `stockable` | `inv_loc.stockable` | probed |
| `lot_bill` | `oe_line.lot_bill` | column |
| `buy` | `inv_loc.buy` | column |
| `make` | `inv_loc.make` | column |
| `buyback_no` | `oe_line.buyback_no` | column |
| `loan_uid` | `oe_line.loan_uid` | column |
| `unit_of_measure` | `oe_line.unit_of_measure` | column |
| `disposition` | `oe_line.disposition` | column |
| `unit_quantity` | `oe_line.unit_quantity` | column |
| `allocated_qty` | computed: `CAST(oe_line.qty_allocated / oe_line.unit_size AS Decimal(19,9))` | alias |
| `direct_through_stock_flag` | `oe_line.direct_through_stock_flag` | alias |
| `dts_release_qty` | `oe_line.dts_release_qty` | probed |
| `product_group_desc` | `product_group.product_group_desc` | column |
| `ship_loc_name` | computed: `' '` | alias |
| `source_loc_name` | computed: `' '` | alias |
| `division_name` | computed: `' '` | alias |
| `supplier_name` | computed: `' '` | alias |
| `supplier_part_no` | `inventory_supplier.supplier_part_no` | column |
| `canceled_qty` | computed: `(computed in the datawindow)` | probed |
| `invoice_qty` | computed: `(computed in the datawindow)` | probed |
| `pick_qty` | computed: `(computed in the datawindow)` | probed |
| `quantity_available` | computed: `(computed in the datawindow)` | probed |
| `unit_picked` | computed: `(computed in the datawindow)` | probed |
| `units_staged` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Item ID: | `inv_mast.item_id` |
| 3 | UOM: | `oe_line.unit_of_measure` |
| 4 | Disposition: | `oe_line.disposition` |
| 7 | Item Desc | `inv_mast.item_desc` |
| 8 | Assembly Type: | `oe_line.assembly` |
| 16 | Lot Bill | `oe_line.lot_bill` |
| 23 | Source Location ID: | `oe_line.source_loc_id` |
| 24 | Ship Location ID: | `oe_line.ship_loc_id` |
| 31 | Extended Desc: | `oe_line.extended_desc` |
| 32 | Expedite Date: | `oe_line.expedite_date` |
| 33 | Required Date: | `oe_line.required_date` |
| 37 | Supplier ID: | `oe_line.supplier_id` |
| 38 | Product Group ID: | `oe_line.product_group_id` |
| 39 | Product Group Desc | `product_group.product_group_desc` |
| 40 | Supplier Name | `supplier_name` |
| 41 | Source Loc Name | `source_loc_name` |
| 42 | Ship Loc Name | `ship_loc_name` |
| 44 | Qty Ordered: | `oe_line.unit_quantity` |
| 45 | Qty Allocated: | `allocated_qty` |
| 53 | Division ID: | `inventory_supplier.division_id` |
| 54 | Division Name | `division_name` |
| 56 | Will Call | `oe_line.will_call` |
| 76 | Disp Retrieved | `oe_line.disposition` |
| 77 | Disp Saved On Fly | `oe_line.disposition` |
| 80 | Tax Item | `oe_line.tax_item` |
| 91 | Stockable | `inv_loc.stockable` |
| 110 | Incoming Freight: | `oe_line.freight_in` |
| 127 | Buy | `inv_loc.buy` |
| 128 | Make | `inv_loc.make` |
| 178 | Pick Date: | `oe_line.pick_date` |
| 277 | Supplier Part No: | `inventory_supplier.supplier_part_no` |
| 335 | Use Strategic Freight | `use_strategic_freight` |
| calc | Qty Canceled: | `if((disposition = "C"), (abs(unit_quantity) - abs(allocated_qty) - abs(pick_qty) - abs(invoice_qty)), abs(qty_canceled / unit_size))` |
| calc | Qty Invoiced: | `oe_line_qty_invoiced  /  unit_size` |
| calc | Qty Available: | `if( ( inv_loc_qty_on_hand  -  inv_loc_qty_allocated - qty_non_pickable - qty_quarantined - qty_frozen  - if(isNull(qty_reserved), 0, qty_reserved))   /  unit_size < 0, 0 ,   (inv_loc_qty_on_hand  -  inv_loc_qty_allocated - qty_non_pickable - qty_quarantined - qty_frozen  - if(isNull(qty_reserved), 0, qty_reserved))  /  unit_size)` |
| calc | Qty On Pick Tickets: | `qty_on_pick_tickets / unit_size` |
| calc | Qty Staged: | `qty_staged / unit_size` |

### `TP_PRICES.prices` (Prices)

- Update table: `oe_line`
- Tables in the SELECT: `oe_line`, `inv_loc`, `inv_mast`, `product_group`, `item_uom`, `inventory_supplier`, `inventory_supplier_x_loc`, `tpcx_dead_stock`, `supplier`, `inv_loc_stock_status`, `inv_mast_assem_info`, `oe_line_hose_assembly`, `oe_line_last_margin_price`, `address`, `oe_hdr`, `revision_transaction`, `p21_view_getrevisionlotquantity`, `item_revision`, `oe_line_po`, `job_price_line`, `oe_line_promise_date`, `oe_line_labor`, `operation`, `service_labor`, `carrier_contract_line`, `carrier_contract_z_line`, `oe_line_room`, `room`, `oe_line_notepad`, `room_area`, `p21_view_oe_line_anticipated_allocation_summary`, `oe_line_lot_billing`, `restricted_class`, `transfer_hdr`, `oe_line_rma`, `invoice_line`, `price_page`, `price_family`, `shipping_route`

| Field | Stored in | Basis |
|---|---|---|
| `calc_value` | `oe_line.calc_value` | probed |
| `unit_of_measure` | `oe_line.unit_of_measure` | column |
| `unit_size` | `oe_line.unit_size` | column |
| `unit_quantity` | `oe_line.unit_quantity` | column |
| `pricing_unit` | `oe_line.pricing_unit` | column |
| `pricing_unit_size` | `oe_line.pricing_unit_size` | column |
| `unit_price` | `oe_line.unit_price` | column |
| `extended_price` | `oe_line.extended_price` | column |
| `one_time_price` | `oe_line_last_margin_price.one_time_price` | probed |
| `manual_price_overide` | `oe_line.manual_price_overide` | column |
| `base_ut_price` | `oe_line.base_ut_price` | column |
| `combinable` | `oe_line.combinable` | column |
| `oe_order_item_id` | `inv_mast.item_id` | probed |
| `next_break` | `oe_line.next_break` | column |
| `next_ut_price` | `oe_line.next_ut_price` | column |
| `item_desc` | `inv_mast.item_desc` | column |
| `tariff_percent` | `oe_line.tariff_percent` | column |
| `used_strategic_pricing_flag` | `oe_line.used_strategic_pricing_flag` | column |
| `canceled_qty` | computed: `(computed in the datawindow)` | probed |
| `pricing_option_desc` | computed: `(computed in the datawindow)` | probed |
| `cf_tariff_unit_price` | computed: `(computed in the datawindow)` | dw_name |
| `quantity_available` | computed: `(computed in the datawindow)` | probed |
| `pricing_qty` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Item ID: | `inv_mast.item_id` |
| 3 | Order UOM: | `oe_line.unit_of_measure` |
| 5 | Net Unit Price: | `oe_line.unit_price` |
| 6 | Extended Price: | `oe_line.extended_price` |
| 7 | Item Desc | `inv_mast.item_desc` |
| 25 | Base Unit Price: | `oe_line.base_ut_price` |
| 27 | Calculation Value: | `oe_line.calc_value` |
| 28 | Combinable | `oe_line.combinable` |
| 30 | Manual Price Overide | `oe_line.manual_price_overide` |
| 43 | Order Unit Size: | `oe_line.unit_size` |
| 44 | Qty Ordered In Order Units: | `oe_line.unit_quantity` |
| 71 | Saved Line Item | `saved_line_item` |
| 85 | Pricing UOM: | `oe_line.pricing_unit` |
| 86 | Pricing Unit Size: | `oe_line.pricing_unit_size` |
| 163 | One Time Price | `oe_line_last_margin_price.one_time_price` |
| 316 | Used Strategic Pricing Flag | `oe_line.used_strategic_pricing_flag` |
| 529 | Tariff Percent: | `oe_line.tariff_percent` |
| calc | Pricing Option: | `if(pricing_option = 1, "By Component", if(pricing_option = 2,  "By Assembly Using Component Prices", if(pricing_option = 3, "By Assembly", "N/A")))` |
| calc | Tariff Unit Price: | `if((NOT ISNULL(tariff_percent)) AND tariff_percent> 0 AND (NOT ISNULL(tariff_detail_uid)) AND tariff_detail_uid > 0, ( (unit_price / ( 1 + (tariff_percent / 100) ))  * (tariff_percent / 100) ) , 0)` |
| calc | Qty Ordered In Pricing Units: | `unit_quantity * unit_size  /  pricing_unit_size` |

### `TP_PRICES.price_page` (Prices)

- Update table: `price_page`
- Tables in the SELECT: `price_page`, `inv_mast`, `price_family`

| Field | Stored in | Basis |
|---|---|---|
| `price_page_uid` | `price_page.price_page_uid` | column |
| `calculation_method_cd` | `price_page.calculation_method_cd` | column |
| `effective_date` | `price_page.effective_date` | column |
| `description` | `price_page.description` | column |
| `expiration_date` | `price_page.expiration_date` | column |
| `customer_id` | `price_page.customer_id` | probed |
| `supplier_id` | `price_page.supplier_id` | column |
| `product_group_id` | `price_page.product_group_id` | column |
| `price_family_id` | `price_family.price_family_id` | column |
| `mfg_class_id` | `price_page.mfg_class_id` | column |
| `item_id` | `inv_mast.item_id` | column |
| `customer_part_no` | `price_page.customer_part_no` | column |
| `discount_group_id` | `price_page.discount_group_id` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Price Page UID: | `price_page.price_page_uid` |
| 5 | Supplier ID: | `price_page.supplier_id` |
| 7 | Discount Group ID: | `price_page.discount_group_id` |
| 8 | Price Page Description: | `price_page.description` |
| 9 | Effective Dates: | `price_page.effective_date` |
| 10 | Calculation Method: | `price_page.calculation_method_cd` |
| 14 | to | `price_page.expiration_date` |

### `TP_PRICES.contract_info` (Prices)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `contract_line_no` | ? | no_sql |
| `contract_no` | ? | no_sql |
| `vendor_auth_no` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Contract #: | `contract_no` |
| 2 | Contract Line #: | `contract_line_no` |

### `LINE_NOTE.line_note` (Order Line Notes)

- Update table: `oe_line_notepad`
- Tables in the SELECT: `oe_line_notepad`, `note_area`, `notepad_class`

| Field | Stored in | Basis |
|---|---|---|
| `note` | `oe_line_notepad.note` | column |
| `note_id` | `oe_line_notepad.note_id` | column |
| `topic` | `oe_line_notepad.topic` | column |
| `notepad_class_desc` | `notepad_class.notepad_class_desc` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Note ID | `oe_line_notepad.note_id` |
| 5 | Topic | `oe_line_notepad.topic` |
| 6 | Note | `oe_line_notepad.note` |
| 15 | Class | `notepad_class.notepad_class_desc` |

### `TABPAGE_LINE_TAX.tabpage_line_tax` (Taxes)

- Update table: `oe_line_tax`
- Tables in the SELECT: `oe_line_tax`, `oe_line`, `tax_jurisdiction`, `inv_mast`, `oe_line_rma`, `invoice_line`, `invoice_line_taxes`

| Field | Stored in | Basis |
|---|---|---|
| `jurisdiction_id` | `oe_line_tax.jurisdiction_id` | column |
| `taxable` | `oe_line_tax.taxable` | column |
| `delete_flag` | `oe_line_tax.delete_flag` | probed |
| `jurisdiction_desc` | `tax_jurisdiction.jurisdiction_desc` | column |
| `flat_fee_amount` | `tax_jurisdiction.flat_fee_amount` | column |
| `item_id` | `inv_mast.item_id` | column |
| `item_desc` | `inv_mast.item_desc` | column |
| `compute_1` | computed: `(computed in the datawindow)` | dw_name |
| `tax_in_hundred` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Jurisdiction ID | `oe_line_tax.jurisdiction_id` |
| 2 | Item ID: | `inv_mast.item_id` |
| 3 | Item Desc | `inv_mast.item_desc` |
| 4 | Jurisdiction Description | `tax_jurisdiction.jurisdiction_desc` |
| 5 | Taxable | `oe_line_tax.taxable` |
| 6 | Delete | `oe_line_tax.delete_flag` |
| 19 | Flat Rate Amount | `tax_jurisdiction.flat_fee_amount` |
| calc | Tax Percentage | `tax_percentage` |

### `TABPAGE_COST.costs` (Costs)

- Update table: `oe_line`
- Tables in the SELECT: `oe_line`, `inv_loc`, `inv_mast`, `product_group`, `item_uom`, `inventory_supplier`, `inventory_supplier_x_loc`, `tpcx_dead_stock`, `supplier`, `inv_loc_stock_status`, `inv_mast_assem_info`, `oe_line_hose_assembly`, `oe_line_last_margin_price`, `address`, `oe_hdr`, `revision_transaction`, `p21_view_getrevisionlotquantity`, `item_revision`, `oe_line_po`, `job_price_line`, `oe_line_promise_date`, `oe_line_labor`, `operation`, `service_labor`, `carrier_contract_line`, `carrier_contract_z_line`, `oe_line_room`, `room`, `oe_line_notepad`, `room_area`, `p21_view_oe_line_anticipated_allocation_summary`, `oe_line_lot_billing`, `restricted_class`, `transfer_hdr`, `oe_line_rma`, `invoice_line`, `price_page`, `price_family`, `shipping_route`

| Field | Stored in | Basis |
|---|---|---|
| `sales_cost` | `oe_line.sales_cost` | column |
| `sales_cost_profit` | computed: `CASE oe_line.extended_price WHEN 0 THEN 0 ELSE (oe_line.extended_price - (( oe_line.sales_cost / oe_line.pricing_unit_size ) * oe_line.qty_ordered)) / oe_line.extended_price * 100 END` | alias |
| `commission_cost` | `oe_line.commission_cost` | column |
| `commission_cost_profit` | computed: `CASE oe_line.extended_price WHEN 0 THEN 0 ELSE (oe_line.extended_price - (( oe_line.commission_cost / oe_line.pricing_unit_size ) * oe_line.qty_ordered)) / oe_line.extended_price * 100 END` | alias |
| `other_cost` | `oe_line.other_cost` | column |
| `other_cost_profit` | computed: `CASE oe_line.extended_price WHEN 0 THEN 0 ELSE (oe_line.extended_price - (( oe_line.other_cost / oe_line.pricing_unit_size ) * oe_line.qty_ordered)) / oe_line.extended_price * 100 END` | alias |
| `po_cost` | `oe_line.po_cost` | column |
| `po_cost_profit` | computed: `100.00` | alias |
| `unit_price` | `oe_line.unit_price` | column |
| `oe_order_item_id` | `inv_mast.item_id` | probed |
| `cost_price_page_desc` | computed: `NULL` | probed |
| `unit_quantity` | `oe_line.unit_quantity` | column |
| `unit_of_measure` | `oe_line.unit_of_measure` | column |
| `pricing_unit` | `oe_line.pricing_unit` | column |
| `item_desc` | `inv_mast.item_desc` | column |
| `commission_cost_edited` | `oe_line.commission_cost_edited` | column |
| `other_cost_edited` | `oe_line.other_cost_edited` | column |
| `unit_size` | `oe_line.unit_size` | column |
| `pricing_unit_size` | `oe_line.pricing_unit_size` | column |
| `next_ut_price` | `oe_line.next_ut_price` | column |
| `next_break` | `oe_line.next_break` | column |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Item ID: | `inv_mast.item_id` |
| 3 | Order UOM: | `oe_line.unit_of_measure` |
| 5 | Unit Price: | `oe_line.unit_price` |
| 7 | Item Desc | `inv_mast.item_desc` |
| 10 | Order Cost: | `oe_line.sales_cost` |
| 43 | Order Unit Size: | `oe_line.unit_size` |
| 44 | Unit Quantity: | `oe_line.unit_quantity` |
| 46 | Next Break: | `oe_line.next_break` |
| 47 | Next Ut Price: | `oe_line.next_ut_price` |
| 61 | Other Cost: | `oe_line.other_cost` |
| 62 | Commission Cost: | `oe_line.commission_cost` |
| 64 | Sales Cost Profit | `sales_cost_profit` |
| 65 | Commission Cost Profit | `commission_cost_profit` |
| 66 | Other Cost Profit | `other_cost_profit` |
| 68 | Commission Cost Edited | `oe_line.commission_cost_edited` |
| 69 | Other Cost Edited | `oe_line.other_cost_edited` |
| 82 | Purchase Order Cost: | `oe_line.po_cost` |
| 84 | Po Cost Profit | `po_cost_profit` |
| 85 | Pricing UOM: | `oe_line.pricing_unit` |
| 86 | Pricing Unit Size: | `oe_line.pricing_unit_size` |
| 115 | Order Cost Edited | `oe_line.order_cost_edited` |
| 266 | Cost Page Description: | `price_page.description` |
| calc | Exted Other Cost | `other_cost/pricing_unit_size * unit_quantity * unit_size` |
| calc | Extd Sales Cost | `sales_cost / pricing_unit_size *  unit_quantity * unit_size` |
| calc | Extd Commission Cost | `commission_cost/pricing_unit_size * unit_quantity * unit_size` |
| calc | Extd Po Cost | `po_cost/pricing_unit_size  *  unit_quantity * unit_size` |
| calc | Cf Ext Carrier Invoice Cost | `carrier_invoice_cost/pricing_unit_size * unit_quantity * unit_size` |

### `TABPAGE_RELEASE.tabpage_release` (Schedules)

- Update table: `oe_line_schedule`
- Tables in the SELECT: `oe_line_schedule`, `oe_line`, `inv_mast`

| Field | Stored in | Basis |
|---|---|---|
| `release_date` | `oe_line_schedule.release_date` | column |
| `unit_release_qty` | computed: `CAST((oe_line_schedule.release_qty / oe_line.unit_size) AS Decimal(19,9))` | probed |
| `expedite_value` | `oe_line_schedule.expedite_value` | column |
| `expedite_type` | `oe_line_schedule.expedite_type` | column |
| `pick_value` | `oe_line_schedule.pick_value` | column |
| `pick_type` | `oe_line_schedule.pick_type` | column |
| `disposition` | `oe_line_schedule.disposition` | column |
| `unit_allocated_qty` | computed: `CAST((oe_line_schedule.allocated_qty / oe_line.unit_size) AS Decimal(19,9))` | probed |
| `release_status_flag` | `oe_line_schedule.release_status_flag` | column |
| `item_id` | `inv_mast.item_id` | column |
| `item_desc` | `inv_mast.item_desc` | column |
| `unit_of_measure` | `oe_line.unit_of_measure` | column |
| `qty_available` | computed: `0.000000000` | probed |
| `qty_ordered` | computed: `0.000000000` | probed |
| `unit_qty_picked` | computed: `(computed in the datawindow)` | probed |
| `unit_qty_invoiced` | computed: `(computed in the datawindow)` | probed |
| `unit_qty_staged` | computed: `(computed in the datawindow)` | probed |
| `unit_qty_canceled` | computed: `(computed in the datawindow)` | probed |
| `unit_qty_bo` | computed: `(computed in the datawindow)` | probed |
| `cf_complete` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_unit_release_qty_display` | computed: `(computed in the datawindow)` | dw_name |
| `total_allocated` | computed: `(computed in the datawindow)` | probed |
| `total_bo_qty` | computed: `(computed in the datawindow)` | probed |
| `cf_total_unit_canceled` | computed: `(computed in the datawindow)` | dw_name |
| `total_release_qty` | computed: `(computed in the datawindow)` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 1 | ReleaseDate | `oe_line_schedule.release_date` |
| 4 | Item ID: | `inv_mast.item_id` |
| 8 | Expedite Time | `oe_line_schedule.expedite_value` |
| 9 | Expedite Type | `oe_line_schedule.expedite_type` |
| 10 | Pick Time | `oe_line_schedule.pick_value` |
| 11 | Pick Type | `oe_line_schedule.pick_type` |
| 19 | Qty Ordered | `compute_0019` |
| 20 | Qty Available | `compute_0020` |
| 21 | Item Desc | `inv_mast.item_desc` |
| 24 | Unit Release Qty | `compute_0024` |
| 25 | Unit Allocated Qty | `compute_0025` |
| 26 | Disp | `oe_line_schedule.disposition` |
| 31 | Unit Of Measure | `oe_line.unit_of_measure` |
| 33 | Orig Allocated | `orig_allocated` |
| 38 | ReleaseStatus | `oe_line_schedule.release_status_flag` |
| calc | Unit Qty Picked | `( qty_picked  /  unit_size )` |
| calc | Unit Qty Invoiced | `( qty_invoiced  /  unit_size )` |
| calc | Unit Qty Staged | `( qty_staged /  unit_size )` |
| calc | Unit Qty Canceled | `"if( disposition = ~"C~", unit_release_qty - unit_allocated_qty - unit_qty_picked - unit_qty_invoiced - unit_qty_staged, qty_canceled / unit_size)  "` |

### `TABPAGE_LOT.tabpage_lot` (Lot)

- Update table: `document_line_lot`
- Tables in the SELECT: `document_line_lot`

| Field | Stored in | Basis |
|---|---|---|
| `trans_type` | computed: `''` | probed |
| `lot_cd` | `document_line_lot.lot_cd` | column |
| `unit_quantity` | `document_line_lot.unit_quantity` | column |
| `unit_of_measure` | `document_line_lot.unit_of_measure` | column |
| `transfer_whole_belt_flag` | computed: `'N'` | alias |
| `unit_qty_allocated` | computed: `0.000000000` | probed |
| `expiration_date` | computed: `GetDate()` | alias |
| `item_id` | computed: `''` | alias |
| `dimension_id` | computed: `''` | alias |
| `item_desc` | computed: `''` | alias |
| `split_belt_flag` | computed: `'N'` | probed |
| `commingling_lot_no` | computed: `NULL` | alias |
| `compute_user_defined_qty` | computed: `(computed in the datawindow)` | dw_name |
| `unit_applied` | computed: `(computed in the datawindow)` | probed |
| `unit_orig_qty` | computed: `(computed in the datawindow)` | probed |
| `posted_qty` | computed: `(computed in the datawindow)` | probed |
| `total_qty_posted1` | computed: `(computed in the datawindow)` | probed |
| `total_qty_posted` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |
| `qty_posted` | computed: `(computed in the datawindow)` | probed |
| `qty_required` | computed: `(computed in the datawindow)` | probed |
| `delta_unit_quantity` | computed: `(computed in the datawindow)` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Lot | `document_line_lot.lot_cd` |
| 7 | Unit Quantity | `document_line_lot.unit_quantity` |
| 8 | UOM | `document_line_lot.unit_of_measure` |
| 15 | Item ID: | `item_id` |
| 16 | Item Desc | `item_desc` |
| 26 | Unit Qty Allocated | `unit_qty_allocated` |
| 44 | Expiration Date | `expiration_date` |
| calc | Picked/Shipped | `qty_applied/unit_size` |

### `TP_ITEMNOTES.tp_itemnotes` (Item Notes)

- Update table: `note`
- Tables in the SELECT: `note`, `note_area`, `code_p21`, `notepad_class`

| Field | Stored in | Basis |
|---|---|---|
| `note` | `note.note` | column |
| `note_uid` | `note.note_uid` | column |
| `topic` | `note.topic` | column |
| `notepad_class_desc` | `notepad_class.notepad_class_desc` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Note ID | `note.note_uid` |
| 4 | Topic | `note.topic` |
| 5 | Note | `note.note` |
| 16 | Class | `notepad_class.notepad_class_desc` |

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

### `TABPAGE_ASSMOPTIONS.assmoptions` (Assembly Options)

- Update table: `assembly_hdr`
- Tables in the SELECT: `assembly_hdr`, `inv_mast`

| Field | Stored in | Basis |
|---|---|---|
| `time_to_make` | computed: `dbo.P21_fn_convert_minutes_to_hours_format(assembly_hdr.minutes_to_make)` | probed |
| `assembly_class_uid` | `assembly_hdr.assembly_class_uid` | column |
| `hose_overall_length` | `assembly_hdr.hose_overall_length` | column |
| `hose_assembly_flag` | `assembly_hdr.hose_assembly_flag` | column |
| `hose_unit_of_measure` | `assembly_hdr.hose_unit_of_measure` | column |
| `pricing_option` | `assembly_hdr.pricing_option` | column |
| `inv_mast_item_id` | `inv_mast.item_id` | probed |
| `prorate_cost_by` | `assembly_hdr.prorate_cost_by` | column |
| `default_disposition` | `assembly_hdr.default_disposition` | column |
| `cost_of_disassembly` | `assembly_hdr.cost_of_disassembly` | column |
| `assembly_usage_accumulation` | `assembly_hdr.assembly_usage_accumulation` | column |
| `allow_disassembly` | `assembly_hdr.allow_disassembly` | column |
| `delete_flag` | `assembly_hdr.delete_flag` | column |
| `item_desc` | `inv_mast.item_desc` | column |
| `production_order_processing` | `assembly_hdr.production_order_processing` | column |
| `print_return_to_stock_components` | `assembly_hdr.print_return_to_stock_components` | column |
| `print_incomplete_assemblies` | `assembly_hdr.print_incomplete_assemblies` | column |
| `price_return_to_stock_components` | `assembly_hdr.price_return_to_stock_components` | column |
| `calc_component_service_level` | `assembly_hdr.calc_component_service_level` | column |
| `auto_create_prod_order` | `assembly_hdr.auto_create_prod_order` | column |
| `assembly_for_stock` | `assembly_hdr.assembly_for_stock` | column |
| `allow_oe_add_components` | `assembly_hdr.allow_oe_add_components` | column |
| `ship_incomplete_assemblies` | `assembly_hdr.ship_incomplete_assemblies` | column |
| `print_compnts_on_pick_ticket` | `assembly_hdr.print_compnts_on_pick_ticket` | column |
| `print_components_on_invoice` | `assembly_hdr.print_components_on_invoice` | column |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Item ID: | `inv_mast.item_id` |
| 4 | Ship Incomplete Assemblies | `assembly_hdr.ship_incomplete_assemblies` |
| 5 | Print Compnts On Pick Ticket | `assembly_hdr.print_compnts_on_pick_ticket` |
| 6 | Print Components On Invoice | `assembly_hdr.print_components_on_invoice` |
| 7 | Default Disposition: | `assembly_hdr.default_disposition` |
| 13 | Allow Oe Add Components | `assembly_hdr.allow_oe_add_components` |
| 14 | Production Order Processing | `assembly_hdr.production_order_processing` |
| 15 | Auto Create Prod Order | `assembly_hdr.auto_create_prod_order` |
| 16 | Pricing Option: | `assembly_hdr.pricing_option` |
| 17 | Delete Flag | `assembly_hdr.delete_flag` |
| 18 | Item Desc | `inv_mast.item_desc` |
| 30 | Print Incomplete Assemblies | `assembly_hdr.print_incomplete_assemblies` |
| 32 | Assembly For Stock | `assembly_hdr.assembly_for_stock` |
| 33 | Accumulate Usage: | `assembly_hdr.assembly_usage_accumulation` |
| 34 | Calc Component Service Level | `assembly_hdr.calc_component_service_level` |
| 35 | Allow Disassembly | `assembly_hdr.allow_disassembly` |
| 36 | Disassembly Cost: | `assembly_hdr.cost_of_disassembly` |
| 37 | Prorate Cost By: | `assembly_hdr.prorate_cost_by` |
| 38 | Print Return To Stock Components | `assembly_hdr.print_return_to_stock_components` |
| 39 | Price Return To Stock Components | `assembly_hdr.price_return_to_stock_components` |
| 42 | Hose Assembly Flag | `assembly_hdr.hose_assembly_flag` |
| 43 | Overall Length: | `assembly_hdr.hose_overall_length` |
| 44 | Unit of Measure: | `assembly_hdr.hose_unit_of_measure` |
| 49 | Assembly Class: | `assembly_hdr.assembly_class_uid` |
| 50 | Time To Make: | `time_to_make` |

### `BUY_SELL_HISTORY.buy_sell_history_past_sell_prices_hdr` (Buy/Sell)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `c_gp` | ? | no_sql |
| `cc_unit_of_measure` | ? | no_sql |
| `cbx_include_quotes` | ? | no_sql |
| `cc_gross_profit_base` | ? | no_sql |
| `item_id` | ? | no_sql |
| `item_desc` | ? | no_sql |
| `c_unit_price` | ? | no_sql |
| `cf_dfflag` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Item ID: | `inv_mast.item_id` |
| 2 | Item Desc | `inv_mast.item_desc` |
| 3 | Unit Price: | `c_unit_price` |
| 4 | GP (%): | `c_gp` |
| 5 | Cbx Include Quotes | `cbx_include_quotes` |
| 6 | Gross Profit Basis: | `cc_gross_profit_base` |
| 7 | Unit of Measure: | `cc_unit_of_measure` |

### `BUY_SELL_HISTORY.buy_sell_history_past_sell_prices` (Buy/Sell)

- Update table: `oe_line`
- Tables in the SELECT: `oe_line`, `oe_hdr`, `inv_mast`, `currency_line`

| Field | Stored in | Basis |
|---|---|---|
| `order_no` | `oe_line.order_no` | column |
| `po_no` | `oe_hdr.po_no` | probed |
| `date_created` | `oe_line.date_created` | column |
| `qty_ordered` | computed: `CASE :UOM WHEN '' THEN CASE unit_size WHEN 0 THEN 0 ELSE CAST(oe_line.qty_ordered / unit_size AS Decimal(19,9)) END WHEN oe_line.unit_of_measure THEN CASE unit_size WHEN 0 THEN 0 ELSE CAST(oe_line.qty_ordered / unit_size AS Decimal(19,9)) END ELSE CASE :UomSize WHEN 0 THEN 0 ELSE CAST(oe_line.qty_ordered / :UomSize AS Decimal(19,9)) END END` | probed |
| `unit_of_measure` | computed: `CASE :UOM WHEN '' THEN oe_line.unit_of_measure ELSE :UOM END` | probed |
| `projected_order` | `oe_hdr.projected_order` | column |
| `unit_price` | computed: `CASE :UOM WHEN '' THEN CASE pricing_unit_size WHEN 0 THEN 0 ELSE CAST((oe_line.unit_price / pricing_unit_size) * unit_size AS Decimal(19,9)) END WHEN oe_line.unit_of_measure THEN CASE pricing_unit_size WHEN 0 THEN 0 ELSE CAST((oe_line.unit_price / pricing_unit_size) * unit_size AS Decimal(19,9)) END ELSE CASE pricing_unit_size WHEN 0 THEN 0 ELSE CAST((unit_price / pricing_unit_size) * :UomSize AS Decimal(19,9)) END END` | probed |
| `c_gross_profit` | computed: `CASE WHEN unit_price = 0 THEN 0 WHEN pricing_unit_size = 0 THEN 0 ELSE CAST(((((unit_price / pricing_unit_size) - :CurrentCostInEaches) / (unit_price / pricing_unit_size) ) * 100) AS Decimal(19,9)) END` | alias |
| `rowfocusindicatorcol` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Order No | `oe_line.order_no` |
| 3 | PO Number | `oe_hdr.po_no` |
| 4 | Date Created | `oe_line.date_created` |
| 5 | Quantity | `oe_line.qty_ordered` |
| 6 | UOM | `oe_line.unit_of_measure` |
| 7 | Quote | `oe_hdr.projected_order` |
| 8 | Unit Price | `oe_line.unit_price` |
| 10 | Current Gross Profit % | `c_gross_profit` |

### `BUY_SELL_HISTORY.buy_sell_history_past_costs_hdr` (Buy/Sell)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `cc_include_rfq` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Type: | `cc_include_rfq` |

### `BUY_SELL_HISTORY.buy_sell_history_past_costs` (Buy/Sell)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `date_due` | ? | no_sql |
| `po_no` | ? | no_sql |
| `c_transaction_type` | ? | no_sql |
| `name` | ? | no_sql |
| `qty_ordered` | ? | no_sql |
| `unit_of_measure` | ? | no_sql |
| `unit_price` | ? | no_sql |
| `qty_received` | ? | no_sql |
| `expected_date` | ? | no_sql |
| `complete` | ? | no_sql |
| `rowfocusindicatorcol` | ? | no_sql |
| `cf_dfflag` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Expected Date | `po_line.date_due` |
| 2 | Transaction Number | `po_line.po_no` |
| 3 | Supplier/Source Location | `address.name` |
| 4 | Qty On PO | `po_line.qty_ordered` |
| 5 | UOM | `po_line.unit_of_measure` |
| 6 | Cost Per | `po_line.unit_price` |
| 7 | Open Qty | `po_line.qty_received` |
| 8 | Entry Date | `po_line.date_due` |
| 9 | Complete | `po_line.complete` |
| 11 | Transaction Type | `c_transaction_type` |

### `TABPAGE_POS.tabpage_pos` (POs)

- Update table: `system_setting` (tool reported system_setting, the first FROM table of a read-only grid; treat as read-only)
- Tables in the SELECT: `system_setting`, `po_hdr`, `po_line`, `oe_line_po`, `inv_mast`, `address`, `po_line_schedule`, `supplier`, `inventory_supplier`, `inventory_supplier_x_loc`, `vendor_rfq_hdr`, `vendor_rfq_hdr_x_po_hdr`, `vendor_rfq_line`, `vessel_receipts_line`, `vessel_receipts_hdr`, `vessel_receipts_container`, `item_uom`

| Field | Stored in | Basis |
|---|---|---|
| `cc_isrfq` | computed: `CASE po_hdr.po_type WHEN 'Q' THEN 'Y' ELSE 'N' END` | alias |
| `po_no` | `po_line.po_no` | column |
| `control_no` | computed: `COALESCE(vendor_rfq_hdr.control_no, vendor_rfq_hdr_rfq_unconverted.control_no)` | alias |
| `po_hdr_location_id` | `po_hdr.location_id` | probed |
| `address_name` | `address.name` | probed |
| `order_date` | `po_hdr.order_date` | column |
| `release_no` | `po_line_schedule.release_no` | alias |
| `date_due` | computed: `IsNull(po_line_schedule.release_date, po_line.date_due)` | alias |
| `cc_lead_time` | computed: `CASE supplier.lead_time_source WHEN 'ITEM' THEN inventory_supplier_x_loc.average_lead_time WHEN 'SUPPLIER' THEN supplier.average_lead_time END` | alias |
| `unit_of_measure` | `po_line.unit_of_measure` | column |
| `unit_price_display` | `po_line.unit_price_display` | column |
| `extended_cost` | computed: `CAST(IsNull(po_line_schedule.release_qty, po_line.unit_quantity * po_line.unit_size) * po_line.unit_price_display/po_line.pricing_unit_size AS decimal(19,9))` | alias |
| `converted_from_rfq_number` | `po_hdr.po_no` | probed |
| `delivery_info` | `vendor_rfq_line.delivery_info` | column |
| `compute_1` | computed: `(computed in the datawindow)` | dw_name |
| `qty_open` | computed: `(computed in the datawindow)` | probed |
| `cf_open_gallons` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 3 | PO Number | `po_line.po_no` |
| 4 | Supplier Name | `address.name` |
| 5 | PO Date | `po_hdr.order_date` |
| 7 | UOM | `po_line.unit_of_measure` |
| 10 | ExpectedDate | `po_line.date_due` |
| 11 | Unit Cost | `po_line.unit_price_display` |
| 12 | Extended Cost | `extended_cost` |
| 13 | PO Location | `po_hdr.location_id` |
| 15 | ReleaseNumber | `po_line_schedule.release_no` |
| 18 | RFQ ControlNumber | `vendor_rfq_hdr.control_no` |
| 19 | RFQ | `cc_isRFQ` |
| 20 | Lead Time | `cc_lead_time` |
| 21 | Converted From RFQ Number | `converted_from_rfq_number` |
| 22 | RFQ Delivery Information | `vendor_rfq_line.delivery_info` |
| calc | Open Quantity | `(unit_quantity  -  (( qty_received + container_qty_open) /  unit_size ))` |

### `TABPAGE_POS.tabpage_pos_hdr` (POs)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `cc_show_all` | ? | no_sql |
| `item_id` | ? | no_sql |
| `item_desc` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Type: | `cc_show_all` |
| 2 | Item ID: | `item_id` |
| 3 | Item Desc | `item_desc` |

### `TP_LINEPROMISEDATE.tp_linepromisedate` (Promise Dates)

- Update table: `oe_line_promise_date`
- Tables in the SELECT: `oe_line_promise_date`, `oe_line`, `inv_mast`

| Field | Stored in | Basis |
|---|---|---|
| `original_promise_date` | `oe_line_promise_date.original_promise_date` | column |
| `promise_date` | `oe_line_promise_date.promise_date` | column |
| `aro_days` | `oe_line_promise_date.aro_days` | column |
| `extended_desc` | `oe_line_promise_date.extended_desc` | column |
| `item_id` | `inv_mast.item_id` | column |
| `item_desc` | `inv_mast.item_desc` | column |
| `promise_date_edited_date` | `oe_line_promise_date.promise_date_edited_date` | column |

| # | Label | table.column / expression |
|---|---|---|
| 3 | Original Est Ship Date: | `oe_line_promise_date.original_promise_date` |
| 4 | Current Est Ship Date: | `oe_line_promise_date.promise_date` |
| 6 | Days After Receipt of Order (ARO): | `oe_line_promise_date.aro_days` |
| 12 | Date Edited: | `oe_line_promise_date.promise_date_edited_date` |
| 13 | Est Ship Date Notes: | `oe_line_promise_date.extended_desc` |
| 14 | Item ID: | `inv_mast.item_id` |
| 15 | Item Desc | `inv_mast.item_desc` |

### `TABPAGE_TRANSFERS.tabpage_transfers` (Transfers)

- Update table: `transfer_hdr`
- Tables in the SELECT: `transfer_hdr`, `transfer_line`, `location`, `inv_mast`, `oe_line_po`

| Field | Stored in | Basis |
|---|---|---|
| `item_id` | `inv_mast.item_id` | column |
| `item_desc` | `inv_mast.item_desc` | column |
| `transfer_no` | `transfer_hdr.transfer_no` | column |
| `date_created` | `transfer_hdr.date_created` | column |
| `from_location_name` | `location.location_name` | probed |
| `to_location_name` | `location.location_name` | probed |
| `unit_quantity` | `transfer_line.unit_quantity` | column |
| `unit_of_measure` | `transfer_line.unit_of_measure` | column |
| `cf_arrow` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Item Id | `inv_mast.item_id` |
| 2 | Item Desc | `inv_mast.item_desc` |
| 3 | Transfer Number | `transfer_hdr.transfer_no` |
| 4 | Date | `transfer_hdr.date_created` |
| 5 | From Location | `location.location_name` |
| 6 | To Location | `location.location_name` |
| 7 | Transfer Qty | `transfer_line.unit_quantity` |
| 8 | UOM | `transfer_line.unit_of_measure` |

### `TABPAGE_LINESHIPMENT.tabpage_lineshipment` (Item Shipments)

- Update table: `oe_hdr`
- Tables in the SELECT: `oe_hdr`, `oe_line`, `oe_pick_ticket`, `oe_pick_ticket_detail`, `clippership_return_<id>`, `shipment`, `code_p21`, `product_group`, `customer_terms`, `p21_view_shipped_ups_package_details`

| Field | Stored in | Basis |
|---|---|---|
| `c_tracking_no` | computed: `CASE WHEN (oe_pick_ticket_detail.ship_quantity = 0 AND oe_pick_ticket.invoice_id_when_shipped > 0) THEN '* * UNDERSHIPPED * *' ELSE COALESCE(clippership_return_<id>.tracking_no, drv_shipment.tracking_number, oe_pick_ticket.tracking_no) END` | alias |
| `shipment_transaction_no` | computed: `CASE ptshipment.transaction_type_cd WHEN 222 THEN oe_hdr.order_no ELSE oe_pick_ticket.pick_ticket_no END` | probed |
| `oe_pick_ticket_print_date` | `oe_pick_ticket.print_date` | probed |
| `c_carrier` | computed: `CASE WHEN (oe_pick_ticket_detail.ship_quantity = 0 AND oe_pick_ticket.invoice_id_when_shipped > 0) THEN NULL ELSE COALESCE(clippership_return_<id>.carrier_name, address.name) END` | alias |
| `unit_of_measure` | computed: `COALESCE(oe_pick_ticket_detail.unit_of_measure, oe_line.unit_of_measure)` | alias |
| `oe_pick_ticket_ship_date` | computed: `CASE WHEN(oe_pick_ticket_detail.ship_quantity = 0 AND oe_pick_ticket.invoice_id_when_shipped > 0) THEN NULL ELSE oe_pick_ticket.ship_date END` | probed |
| `invoice_no` | computed: `CASE WHEN(oe_pick_ticket_detail.ship_quantity = 0 AND oe_pick_ticket.invoice_id_when_shipped > 0) THEN 0 ELSE COALESCE(oe_pick_ticket.invoice_no, oe_hdr.invoice_no) END` | alias |
| `shipment_type_display` | computed: `CASE WHEN oe_pick_ticket_type_cd = 1921 THEN 'Parts Pick Ticket' WHEN oe_pick_ticket_type_cd = 1922 THEN 'Service Pick Ticket' WHEN oe_pick_ticket.direct_shipment = 'Y' THEN 'Direct Shipment' WHEN oe_pick_ticket.auxiliary = 'Y' THEN 'Auxiliary Pick Ticket' WHEN oe_pick_ticket.pick_and_hold = 'Y' THEN CASE WHEN oe_hdr.packing_basis = 'Tag and Hold' THEN 'Tag And Hold' ELSE 'Pick And Hold' END ELSE CASE ptshipment.transaction_type_cd WHEN 222 THEN 'Shipped via Order Entry' ELSE 'Regular Pick Ticket' END END + CASE WHEN COALESCE(clippership_return_<id>.clippership_return_uid, 0) < > 0 THEN ' (Clippership)' WHEN COALESCE(ptshipment.shipment_uid, 0) < > 0 THEN ' (' + carriertype.code_description + ')' ELSE '' END` | alias |
| `rowfocusindicatorcol` | computed: `(computed in the datawindow)` | probed |
| `quantity` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 2 | Print Date | `oe_pick_ticket.print_date` |
| 3 | Carrier | `c_carrier` |
| 4 | Tracking Number | `c_tracking_no` |
| 7 | Oe Pick Ticket Ship Date | `oe_pick_ticket.ship_date` |
| 8 | Invoice | `oe_pick_ticket.invoice_no` |
| 14 | UOM | `oe_pick_ticket_detail.unit_of_measure` |
| 17 | Shipment Type | `shipment_type_display` |
| 18 | Pick Ticket Number | `transaction_no` |
| calc | Quantity | `if( isNull( invoice_no ),  oe_pick_ticket_detail_print_quantity  /   oe_pick_ticket_detail_unit_size ,  oe_pick_ticket_detail_ship_quantity   /   oe_pick_ticket_detail_unit_size )` |

### `TABPAGE_STOCK.stock_avail` (Stock Avail)

- Update table: `none reported` (tool reported 'clause*/' (misparse of SQL comments; treat as unknown))
- Tables in the SELECT: `inv_loc`, `address`, `inv_mast`, `item_uom`, `location`, `inv_loc_stock_status`, `vessel_receipts_line`, `vessel_receipts_hdr`, `po_line`, `po_hdr`, `transfer_days`

| Field | Stored in | Basis |
|---|---|---|
| `company_id` | `inv_loc.company_id` | column |
| `location_id` | `inv_loc.location_id` | column |
| `address_name` | `address.name` | probed |
| `unit_of_measure` | `item_uom.unit_of_measure` | column |
| `days` | `transfer_days.days` | column |
| `shipment_date` | computed: `dbo.p21_fn_get_next_scheduled_transfer_date(GETDATE(), inv_loc.location_id, :to_location)` | alias |
| `item_id` | `inv_mast.item_id` | column |
| `item_desc` | `inv_mast.item_desc` | column |
| `available` | computed: `(computed in the datawindow)` | probed |
| `allocated` | computed: `(computed in the datawindow)` | probed |
| `backordered` | computed: `(computed in the datawindow)` | probed |
| `purchased` | computed: `(computed in the datawindow)` | probed |
| `in_transit` | computed: `(computed in the datawindow)` | probed |
| `cf_qty_on_vessel` | computed: `(computed in the datawindow)` | dw_name |
| `compute_1` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Location ID | `inv_loc.location_id` |
| 2 | Name | `address.name` |
| 3 | Item ID: | `inv_mast.item_id` |
| 4 | Item Desc | `inv_mast.item_desc` |
| 5 | Company ID | `inv_loc.company_id` |
| 6 | UOM | `item_uom.unit_of_measure` |
| 14 | Days In Transit | `transfer_days.days` |
| 15 | Next Transfer Ship Date | `shipment_date` |
| calc | Available | `IF(IsNull( qty_available ) OR qty_available < 0 , 0, qty_available)` |
| calc | Allocated | `IF(IsNull( qty_allocated ) OR  qty_allocated < 0 , 0 , qty_allocated)` |
| calc | On BO | `IF(IsNull( qty_on_bo ) OR qty_on_bo < 0 ,  0,  qty_on_bo)` |
| calc | On PO | `IF(IsNull( qty_on_po ) OR qty_on_po < 0 ,  0,  qty_on_po)` |
| calc | In Transit | `IF(IsNull( qty_in_transit ) OR qty_in_transit < 0 ,  0,  qty_in_transit)` |

### `TABPAGE_STOCK.checkbox` (Stock Avail)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `show_all` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Show All | `cbx_show_all` |

### `TABPAGE_POSXFERS.posxfers_hdr` (POs/Xfers)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `cc_show_all` | ? | no_sql |
| `item_id` | ? | no_sql |
| `item_desc` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Type: | `cc_show_all` |
| 2 | Item ID: | `item_id` |
| 3 | Item Desc | `item_desc` |

### `TABPAGE_POSXFERS.posxfers` (POs/Xfers)

- Update table: `oe_line_po`
- Tables in the SELECT: `oe_line_po`, `po_hdr`, `po_line`, `inv_mast`, `address`, `supplier`, `inventory_supplier`, `inventory_supplier_x_loc`, `vendor_rfq_hdr`, `vendor_rfq_hdr_x_po_hdr`, `vendor_rfq_line`, `po_line_schedule`, `transfer_hdr`, `transfer_line`, `company`, `vessel_receipts_hdr`, `vessel_receipts_line`, `vessel_receipts_container`

| Field | Stored in | Basis |
|---|---|---|
| `cc_isrfq` | computed: `CASE po_hdr.po_type WHEN 'Q' THEN 'Y' ELSE 'N' END` | alias |
| `oe_line_po_po_no` | `oe_line_po.po_no` | probed |
| `control_no` | computed: `COALESCE(vendor_rfq_hdr.control_no, vendor_rfq_hdr_rfq_unconverted.control_no)` | probed |
| `po_line_number` | `oe_line_po.po_line_number` | column |
| `supplier_name` | `address.name` | probed |
| `oe_transfer_reserve_flag` | computed: `'N'` | alias |
| `unit_of_measure` | `po_line.unit_of_measure` | column |
| `c_container_unit_qty_received` | computed: `(computed in the datawindow)` | dw_name |
| `cc_lead_time` | computed: `CASE supplier.lead_time_source WHEN 'ITEM' THEN inventory_supplier_x_loc.average_lead_time WHEN 'SUPPLIER' THEN supplier.average_lead_time END` | alias |
| `po_line_date_due` | computed: `COALESCE(drv_po_line_schedule.release_date, po_line.date_due)` | probed |
| `completed` | `oe_line_po.completed` | column |
| `converted_from_rfq_number` | `po_hdr.po_no` | probed |
| `delivery_info` | `vendor_rfq_line.delivery_info` | column |
| `cf_spaces` | computed: `(computed in the datawindow)` | dw_name |
| `type` | computed: `(computed in the datawindow)` | probed |
| `qty_remaining` | computed: `(computed in the datawindow)` | probed |
| `cf_releases` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Purchase Order /Transfer Number | `oe_line_po.po_no` |
| 2 | Line Number | `oe_line_po.po_line_number` |
| 6 | Date Due | `po_line.date_due` |
| 7 | UOM | `po_line.unit_of_measure` |
| 15 | Complete | `oe_line_po.completed` |
| 17 | Supplier Name | `address.name` |
| 18 | RFQ Control Number | `vendor_rfq_hdr.control_no` |
| 19 | RFQ | `cc_isRFQ` |
| 20 | Lead Time | `cc_lead_time` |
| 21 | Converted From RFQ Number | `converted_from_rfq_number` |
| 22 | RFQ Delivery Information | `vendor_rfq_line.delivery_info` |
| 33 | Container Qty | `c_container_unit_qty_received` |
| 37 | OE TransferReserve | `transfer_hdr.oe_transfer_reserve_flag` |
| calc | Type | `"CASE( connection_type   WHEN 'P' THEN 'Purchase Order'  WHEN 'Q' THEN 'Vendor RFQ'  WHEN 'T','X' THEN 'Transfer'  WHEN 'V' THEN 'Container'  ELSE '')  "` |
| calc | Quantity Remaining | `if(completed = 'Y', 0, ( qty_ordered - qty_received) /  unit_size )` |
| calc | Remaining Releases | `if(completed = 'Y', 0, releases)` |

### `TABPAGE_ORDERS.open_orders_checkbox` (Orders)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `show_all` | ? | no_sql |
| `show_orders` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Show All | `show_all` |
| 2 | Show Orders | `show_orders` |

### `TABPAGE_ORDERS.open_orders` (Orders)

- Update table: `system_setting` (tool reported system_setting, the first FROM table of a read-only grid; treat as read-only)
- Tables in the SELECT: `system_setting`, `oe_line`, `oe_hdr`, `inv_mast`, `address`, `item_uom`

| Field | Stored in | Basis |
|---|---|---|
| `item_id` | `inv_mast.item_id` | column |
| `item_desc` | `inv_mast.item_desc` | column |
| `order_no` | `oe_hdr.order_no` | column |
| `location_id` | `oe_hdr.location_id` | column |
| `address_name` | `address.name` | probed |
| `unit_quantity` | `oe_line.unit_quantity` | column |
| `unit_of_measure` | `oe_line.unit_of_measure` | column |
| `disposition` | `oe_line.disposition` | column |
| `projected_order` | `oe_hdr.projected_order` | column |
| `allocated_qty` | computed: `(computed in the datawindow)` | probed |
| `invoiced_qty` | computed: `(computed in the datawindow)` | probed |
| `open_qty` | computed: `(computed in the datawindow)` | probed |
| `cf_unit_quantity_gallons` | computed: `(computed in the datawindow)` | dw_name |
| `cf_qty_allocated_gallons` | computed: `(computed in the datawindow)` | dw_name |
| `cf_gallons_invoiced` | computed: `(computed in the datawindow)` | dw_name |
| `cf_open_qty_gallons` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Order Number | `oe_hdr.order_no` |
| 2 | Customer Name | `address.name` |
| 3 | Qty Ordered | `oe_line.unit_quantity` |
| 4 | UOM | `oe_line.unit_of_measure` |
| 5 | Disp | `oe_line.disposition` |
| 9 | Item ID: | `inv_mast.item_id` |
| 10 | Item Desc | `inv_mast.item_desc` |
| 12 | Quote | `oe_hdr.projected_order` |
| 14 | Location | `oe_hdr.location_id` |
| calc | Qty Allocated | `((qty_allocated + qty_on_pick_tickets + qty_staged)  /  unit_size)` |
| calc | Qty Invoiced | `qty_invoiced  /  unit_size` |
| calc | Qty Open | `if((order_type = 1877),((unit_quantity*unit_size)  -  qty_invoiced)/unit_size, ( (  unit_quantity  *  unit_size  )  -  ( qty_invoiced + qty_allocated + qty_canceled + qty_on_pick_tickets + qty_staged ) )  /  unit_size)` |

### `TABPAGE_SALESHISTORY.tabpage_saleshistory` (Sales History)

- Update table: `system_setting` (tool reported system_setting, the first FROM table of a read-only grid; treat as read-only)
- Tables in the SELECT: `system_setting`, `invoice_line`, `invoice_hdr`, `inv_mast`, `job_price_line`, `job_price_hdr`, `oe_hdr`, `currency_line`, `invoice_line_taxes`, `customer`, `rebill_invoice_reason`, `item_uom`

| Field | Stored in | Basis |
|---|---|---|
| `ship2_name` | `invoice_hdr.ship2_name` | column |
| `order_date` | `invoice_hdr.order_date` | column |
| `order_no` | `invoice_hdr.order_no` | column |
| `invoice_date` | `invoice_hdr.invoice_date` | probed |
| `invoice_no` | `invoice_hdr.invoice_no` | column |
| `prod_order_adjustment_invoice` | computed: `CASE invoice_hdr.source_type_cd WHEN 2871 THEN 'Y' ELSE 'N' END` | alias |
| `location_id` | `invoice_hdr.sales_location_id` | probed |
| `unit_of_measure` | `invoice_line.unit_of_measure` | column |
| `pricing_unit` | `invoice_line.pricing_unit` | column |
| `unit_price` | `invoice_line.unit_price` | column |
| `extended_price` | `invoice_line.extended_price` | column |
| `c_comparison_cost` | computed: `CASE customer.invoice_comp_cost_cd_tier1 WHEN 2110 THEN CASE WHEN (invoice_line.commission_cost * invoice_line.pricing_unit_size <> 0) THEN invoice_line.commission_cost * invoice_line.pricing_unit_size ELSE CASE customer.invoice_comp_cost_cd_tier2 WHEN 2111 THEN CASE WHEN (CASE invoice_line.qty_shipped WHEN 0 THEN 0 ELSE CAST(invoice_line.cogs_amount / (invoice_line.qty_shipped / invoice_line.pricing_unit_size) AS Decimal(19,9)) END) <> 0 THEN invoice_line.cogs_amount / (invoice_line.qty_shipped / invoice_line.pricing_unit_size) ELSE invoice_line.other_cost * invoice_line.pricing_unit_size END WHEN 1195 THEN CASE WHEN (invoice_line.other_cost * invoice_line.pricing_unit_size <> 0) THEN invoice_line.other_cost * invoice_line.pricing_unit_size ELSE (CASE invoice_line.qty_shipped WHEN 0 THEN 0 ELSE CAST(invoice_line.cogs_amount / (invoice_line.qty_shipped / invoice_line.pricing_unit_size) AS Decimal(19,9)) END) END END END WHEN 2111 THEN CASE WHEN (CASE invoice_line.qty_shipped WHEN 0 THEN 0 ELSE CAST(invoice_line.cogs_amount / (invoice_line.qty_shipped / invoice_line.pricing_unit_size) AS Decimal(19,9)) END) <> 0 THEN invoice_line.cogs_amount / (invoice_line.qty_shipped / invoice_line.pricing_unit_size) ELSE CASE customer.invoice_comp_cost_cd_tier2 WHEN 2110 THEN CASE WHEN (invoice_line.commission_cost * invoice_line.pricing_unit_size <> 0) THEN invoice_line.commission_cost * invoice_line.pricing_unit_size ELSE invoice_line.other_cost * invoice_line.pricing_unit_size END WHEN 1195 THEN CASE WHEN (invoice_line.other_cost * invoice_line.pricing_unit_size <> 0) THEN invoice_line.other_cost * invoice_line.pricing_unit_size ELSE invoice_line.commission_cost * invoice_line.pricing_unit_size END END END WHEN 1195 THEN CASE WHEN (invoice_line.other_cost * invoice_line.pricing_unit_size <> 0) THEN invoice_line.other_cost * invoice_line.pricing_unit_size ELSE CASE customer.invoice_comp_cost_cd_tier2 WHEN 2110 THEN CASE WHEN (invoice_line.commission_cost * invoice_line.pricing_unit_size <> 0) THEN invoice_line.commission_cost * invoice_line.pricing_unit_size ELSE (CASE invoice_line.qty_shipped WHEN 0 THEN 0 ELSE CAST(invoice_line.cogs_amount / (invoice_line.qty_shipped / invoice_line.pricing_unit_size) AS Decimal(19,9)) END) END WHEN 2111 THEN CASE WHEN (CASE invoice_line.qty_shipped WHEN 0 THEN 0 ELSE CAST(invoice_line.cogs_amount / (invoice_line.qty_shipped / invoice_line.pricing_unit_size) AS Decimal(19,9)) END) <> 0 THEN invoice_line.cogs_amount / (invoice_line.qty_shipped / invoice_line.pricing_unit_size) ELSE invoice_line.commission_cost * invoice_line.pricing_unit_size END END END END` | alias |
| `c_extended_comparison_cost` | computed: `CASE customer.invoice_comp_cost_cd_tier1 WHEN 2110 THEN CASE WHEN (invoice_line.commission_cost * invoice_line.qty_shipped <> 0) THEN invoice_line.commission_cost * invoice_line.qty_shipped ELSE CASE customer.invoice_comp_cost_cd_tier2 WHEN 2111 THEN CASE WHEN (invoice_line.cogs_amount <> 0) THEN invoice_line.cogs_amount ELSE invoice_line.other_cost * invoice_line.qty_shipped END WHEN 1195 THEN CASE WHEN (invoice_line.other_cost * invoice_line.qty_shipped <> 0) THEN invoice_line.other_cost * invoice_line.qty_shipped ELSE invoice_line.cogs_amount END END END WHEN 2111 THEN CASE WHEN (invoice_line.cogs_amount <> 0) THEN invoice_line.cogs_amount ELSE CASE customer.invoice_comp_cost_cd_tier2 WHEN 2110 THEN CASE WHEN (invoice_line.commission_cost * invoice_line.qty_shipped <> 0) THEN invoice_line.commission_cost * invoice_line.qty_shipped ELSE invoice_line.other_cost * invoice_line.qty_shipped END WHEN 1195 THEN CASE WHEN (invoice_line.other_cost * invoice_line.qty_shipped <> 0) THEN invoice_line.other_cost * invoice_line.qty_shipped ELSE invoice_line.commission_cost * invoice_line.qty_shipped END END END WHEN 1195 THEN CASE WHEN (invoice_line.other_cost * invoice_line.qty_shipped <> 0) THEN invoice_line.other_cost * invoice_line.qty_shipped ELSE CASE customer.invoice_comp_cost_cd_tier2 WHEN 2110 THEN CASE WHEN (invoice_line.commission_cost * invoice_line.qty_shipped <> 0) THEN invoice_line.commission_cost * invoice_line.qty_shipped ELSE invoice_line.cogs_amount END WHEN 2111 THEN CASE WHEN (invoice_line.cogs_amount <> 0) THEN invoice_line.cogs_amount ELSE invoice_line.commission_cost * invoice_line.qty_shipped END END END END` | alias |
| `c_taxable` | `derv_taxable.taxable` | alias |
| `c_direct_ship` | computed: `CASE WHEN invoice_hdr.source_type_cd IN (1129,1924) THEN 'Y' ELSE 'N' END` | alias |
| `c_unitcost` | computed: `CASE qty_shipped WHEN 0 THEN 0 ELSE (CASE :cost_type WHEN 2 THEN invoice_line.commission_cost * invoice_line.qty_shipped WHEN 3 THEN invoice_line.other_cost * invoice_line.qty_shipped ELSE invoice_line.cogs_amount END) / (invoice_line.qty_shipped / invoice_line.pricing_unit_size) END` | alias |
| `cogs_amount` | computed: `CASE :cost_type WHEN 2 THEN invoice_line.commission_cost * invoice_line.qty_shipped WHEN 3 THEN invoice_line.other_cost * invoice_line.qty_shipped ELSE invoice_line.cogs_amount END` | alias |
| `contract_no` | `job_price_hdr.contract_no` | column |
| `job_description` | `job_price_hdr.job_description` | column |
| `line_no` | `job_price_line.line_no` | column |
| `cf_arrow` | computed: `(computed in the datawindow)` | dw_name |
| `ordered` | computed: `(computed in the datawindow)` | probed |
| `shipped` | computed: `(computed in the datawindow)` | probed |
| `profit` | computed: `(computed in the datawindow)` | probed |
| `cf_tariff_unit_price` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Invoice Date | `invoice_hdr.invoice_date` |
| 2 | Invoice Number | `invoice_hdr.invoice_no` |
| 5 | Unit Price | `invoice_line.unit_price` |
| 6 | OrdUOM | `invoice_line.unit_of_measure` |
| 7 | ExtendedPrice | `invoice_line.extended_price` |
| 8 | OrderNumber | `invoice_hdr.order_no` |
| 9 | Contract Ln # | `job_price_line.line_no` |
| 10 | Contract No | `job_price_hdr.contract_no` |
| 11 | Contract Description | `job_price_hdr.job_description` |
| 12 | Extended Cost | `invoice_line.cogs_amount` |
| 13 | Ship To Name | `invoice_hdr.ship2_name` |
| 17 | PrcUOM | `invoice_line.pricing_unit` |
| 19 | Location | `invoice_hdr.sales_location_id` |
| 20 | OrderDate | `invoice_hdr.order_date` |
| 22 | Unit Cost | `c_unitcost` |
| 23 | ComparisonCost | `c_comparison_cost` |
| 24 | Ext ComparisonCost | `c_extended_comparison_cost` |
| 25 | Taxable | `c_taxable` |
| 26 | DS | `c_direct_ship` |
| calc | Quantity Ordered | `IF (IsNull(qty_requested), 0, qty_requested /  order_unit_size)` |
| calc | Quantity Shipped | `IF (IsNull(qty_shipped), 0, qty_shipped / order_unit_size)` |
| calc | Profit % | `(( extended_price -  cogs_amount ) /  extended_price ) * 100` |

### `TABPAGE_SALESHISTORY.external` (Sales History)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `item_id` | ? | no_sql |
| `item_desc` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Item ID: | `item_id` |
| 2 | Item Desc | `item_desc` |

### `TABPAGE_PRODUCTIONORDER.tabpage_productionorder` (Production Order)

- Update table: `prod_order_hdr`
- Tables in the SELECT: `prod_order_hdr`, `prod_order_line`, `prod_order_line_link`, `oe_line_schedule`, `oe_line`

| Field | Stored in | Basis |
|---|---|---|
| `prod_order_number` | `prod_order_line_link.prod_order_number` | column |
| `prod_order_line_num` | `prod_order_line_link.prod_order_line_number` | probed |
| `qty_to_make` | `prod_order_line.qty_to_make` | probed |
| `qty_completed` | `prod_order_line.qty_completed` | column |
| `start_date` | `prod_order_line.start_date` | column |
| `committed_start_date` | `prod_order_line.committed_start_date` | column |
| `end_date` | `prod_order_line.end_date` | column |
| `expected_completion_date` | `prod_order_hdr.expected_completion_date` | column |
| `comment_date` | `prod_order_line.comment_date` | column |
| `release` | computed: `CASE prod_order_line_link.trans_type WHEN 'S' THEN 'Y' ELSE 'N' END` | alias |
| `release_date` | `oe_line_schedule.release_date` | column |
| `rowfocusindicatorcol` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Prod Order Number | `prod_order_line_link.prod_order_number` |
| 2 | Prod Order Line Num | `prod_order_line_link.prod_order_line_number` |
| 3 | Qty To Make | `prod_order_line.qty_to_make` |
| 4 | Qty Completed | `prod_order_line.qty_completed` |
| 6 | Expected Completion Date | `prod_order_hdr.expected_completion_date` |
| 7 | Release Date | `oe_line_schedule.release_date` |
| 8 | Release | `oe_line_schedule.release` |
| 9 | Committed Start Date | `prod_order_line.committed_start_date` |
| 10 | Start Date | `prod_order_line.start_date` |
| 11 | End Date | `prod_order_line.end_date` |
| 12 | Comment Date | `prod_order_line.comment_date` |

### `DOCUMENT_LINK_DETAIL.document_link_detail_detail` (Document Links)

- Update table: `document_link`
- Tables in the SELECT: `document_link`, `document_link_area`, `inv_mast`, `ship_to`, `document_link_entity_req`

| Field | Stored in | Basis |
|---|---|---|
| `link_name` | `document_link.link_name` | column |
| `link_path` | `document_link.link_path` | probed |
| `row_status_flag` | `document_link.row_status_flag` | column |
| `mandatory_flag` | `document_link.mandatory_flag` | probed |
| `user_print_flag` | computed: `COALESCE (dler_ship_to.print_flag, dler_customer.print_flag, 'N')` | alias |
| `user_fax_flag` | computed: `COALESCE (dler_ship_to.fax_flag, dler_customer.fax_flag, 'N')` | alias |
| `user_email_flag` | computed: `COALESCE (dler_ship_to.email_flag, dler_customer.email_flag, 'N')` | alias |
| `outside_use_flag` | `document_link.outside_use_flag` | column |
| `send_outside_use_print_flag` | computed: `COALESCE (dler_ship_to.send_outside_use_print_flag, dler_customer.send_outside_use_print_flag, 'N')` | probed |
| `document_link_uid` | `document_link.document_link_uid` | column |
| `send_outside_use_email_flag` | computed: `COALESCE (dler_ship_to.send_outside_use_email_flag, dler_customer.send_outside_use_email_flag, 'N')` | probed |
| `send_outside_use_fax_flag` | computed: `COALESCE (dler_ship_to.send_outside_use_fax_flag, dler_customer.send_outside_use_fax_flag, 'N')` | probed |
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
| 36 | OU-Print | `dler_ship_to.send_outside_use_print_flag` |
| 37 | OU-Fax | `dler_ship_to.send_outside_use_fax_flag` |
| 38 | OU-Email | `dler_ship_to.send_outside_use_email_flag` |
| calc | Document Linked to | `IF ( key2_cd = 'lot_cd', if(isnull(key2_value),'',key2_value), IF ( key1_cd = 'inv_mast_uid', if(isnull(item_id),'',item_id), if(isnull(key1_value),'',key1_value) ) + IF ( IsNull(key2_value), '', '/' + key2_value + IF ( IsNull(key3_value), '', '/' + key3_value)) )` |
| calc | Form | `if( display_area_cd = 2284, 'RFQ', '') + if(display_area_cd = 2285, 'PO','')  + if(display_area_cd = 709, 'Quote','') + if(display_area_cd = 999, 'Packing List','') + if(display_area_cd = 998, 'Order Acknowledgment','') + if(display_area_cd = 2750, 'Production Order','') + if(display_area_cd = 995, 'Invoice', '') + if(display_area_cd = 3376, 'Builder Selection Sheet', '') + if(display_area_cd = 3451, 'Service Order Parts Pick Tickets', '') + if(display_area_cd = 3452, 'Service Order Pick Tickets', '') + if(display_area_cd = 3453, 'Sales Order Pick Ticket', '')  + if(display_area_cd = 1319, 'Order Entry/RMA', '')` |

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
| `TP_SHIPPING` | Shipping | `shipment_header` | datawindow never instantiated (tab not enabled) |
| `TP_JOBCONTROLCONTACT` | Job Control Contact | `tp_jobcontrolcontact` | datawindow never instantiated (tab not enabled) |
| `TP_JOBNOTES` | Job/Contract Notes | `tp_jobnotes` | datawindow never instantiated (tab not enabled) |
| `TP_CONSIGNMENTUSAGE` | Consignment Usage | `consignment_usage` | datawindow never instantiated (tab not enabled) |
| `JOBCONTROLHDRNOTESTABPG` | Job Control Notes | `jobcontrolhdrnotestabpg` | datawindow never instantiated (tab not enabled) |
| `REASONCODESHDR` | Reason Codes | `reasoncodeshdr` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_7` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_7 does not exist.); hidden placeholder page |
| `TABPAGE_6` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_6 does not exist.); hidden placeholder page |
| `TABPAGE_5` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_5 does not exist.); hidden placeholder page |
| `TABPAGE_4` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_4 does not exist.); hidden placeholder page |
| `TABPAGE_3` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_3 does not exist.); hidden placeholder page |
| `TABPAGE_8` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_8 does not exist.); hidden placeholder page |
| `TABPAGE_2` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_2 does not exist.); hidden placeholder page |
| `TP_ITEMS` | Items | `d_dw_quickmode_d_dw_oe_line_dataentry` | SQL Information is disabled for this datawindow (Menu m_sqlinformation is not enabled) |
| `TP_ITEMS` | Items | `panel` | datawindow never instantiated (tab not enabled) |
| `TP_SUBSTITUTE` | Substitute | `substitute` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_COST` | Costs | `cost_page_contract` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_SERIAL` | Serial | `serial` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_LOT_BIN_XREF` | Lot/Bin | `tabpage_lot_bin_xref` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_BIN` | Bin | `tabpage_bin` | datawindow never instantiated (tab not enabled) |
| `TP_CUSTPARTNONOTES` | Customer Part Number Notes | `tp_custpartnonotes` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_WILLCALL` | Will Call | `tabpage_willcall` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_LINKS` | PO Links | `links_for_order_hdr` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_LINKS` | PO Links | `links_for_order` | datawindow never instantiated (tab not enabled) |
| `TP_TAGS` | Tags | `tp_tags_tdl_header` | datawindow never instantiated (tab not enabled) |
| `TP_TAGS` | Tags | `tp_tags_dlt` | datawindow never instantiated (tab not enabled) |
| `REASONCODESLINE` | Reason Codes | `reasoncodesline` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_PROCESS` | Process | `tabpage_process` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_PROCESS` | Process | `tabpage_process_dw_2` | datawindow never instantiated (tab not enabled) |
| `COSTCODES` | Cost Codes | `costcodes` | datawindow never instantiated (tab not enabled) |
| `DOCUMENT_LINK_DETAIL` | Document Links | `document_link_forms` | datawindow never instantiated (tab not enabled) |
| `TIMESTAMPDETAIL` | Timestamp | `timestampdetail_dw_audittrail` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_23` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_23 does not exist.); hidden placeholder page |
| `TABPAGE_22` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_22 does not exist.); hidden placeholder page |
| `TABPAGE_21` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_21 does not exist.); hidden placeholder page |
| `TABPAGE_20` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_20 does not exist.); hidden placeholder page |
| `TABPAGE_19` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_19 does not exist.); hidden placeholder page |
| `TABPAGE_18` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_18 does not exist.); hidden placeholder page |
| `TABPAGE_24` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_24 does not exist.); hidden placeholder page |
| `TABPAGE_17` |  | `tp_17_dw_17` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_17` |  | `dw_hosedata` | datawindow never instantiated (tab not enabled) |
