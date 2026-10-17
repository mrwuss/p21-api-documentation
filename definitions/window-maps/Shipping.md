# Shipping (`Shipping`)

- Window class: `w_ship_sheet`; menu class: `m_shipping`
- Tabs: 41; datawindows mapped: 22; unreachable entries: 27

## Tab overview

| Tab | Caption | Datawindows mapped | Tables in the SELECT |
|---|---|---|---|
| `TABPAGE_1` | Shipment | `tp_1_dw_1` | address, company, company_strategic_pricing, contacts, currency_line, cust_defaults, customer, customer_strategic_pricing, customer_terms, freight_code, group_pick_ticket_detail, group_pick_ticket_hdr, invoice_batch, location, location_packing_options, oe_hdr, oe_hdr_progress_billing, oe_line, oe_line_service, oe_pick_ticket, oe_pick_ticket_detail, oe_pick_ticket_ups, product_group, ship_to, shipping_route, system_setting, terms |
| `TABPAGE_3` | Customer Notes | `tp_3_dw_3` | customer_notepad, note_area, notepad_class |
| `TABPAGE_5` | Remittance | `tp_5_dw_5`, `dw_totals`, `tp_5_dw_req_pymt` | address, ar_payment_details, check_payment_details, currency_hdr, currency_line, epf_transaction_detail, oe_hdr, p21_view_ar_payment_details, p21_view_creditcard_payment_details, payment_account, payment_account_x_transaction, payment_types, remittances, ship_to, shipping_route |
| `TABPAGE_6` | Order Notes | `tp_6_dw_6` | note_area, notepad_class, oe_hdr_notepad |
| `HDR_NOTE` | Invoice Notes | `hdr_note` | invoice_hdr_notepad, note_area, notepad_class |
| `TABPAGE_SHIPTO` | Ship To | `tabpage_shipto` | address, company, company_strategic_pricing, contacts, currency_line, cust_defaults, customer, customer_strategic_pricing, customer_terms, freight_code, group_pick_ticket_detail, group_pick_ticket_hdr, invoice_batch, location, location_packing_options, oe_hdr, oe_hdr_progress_billing, oe_line, oe_line_service, oe_pick_ticket, oe_pick_ticket_detail, oe_pick_ticket_ups, product_group, ship_to, shipping_route, system_setting, terms |
| `TABPAGE_FREIGHT` | Out Freight | `tabpage_freight` | address, company, company_strategic_pricing, contacts, currency_line, cust_defaults, customer, customer_strategic_pricing, customer_terms, freight_code, group_pick_ticket_detail, group_pick_ticket_hdr, invoice_batch, location, location_packing_options, oe_hdr, oe_hdr_progress_billing, oe_line, oe_line_service, oe_pick_ticket, oe_pick_ticket_detail, oe_pick_ticket_ups, product_group, ship_to, shipping_route, system_setting, terms |
| `TABPAGE_TAX` | Tax | `tabpage_tax` | oe_hdr_tax, tax_jurisdiction |
| `TABPAGE_ORDERBINS` | Order Bins | `tabpage_orderbins` | bin, document_line_bin, oe_pick_ticket |
| `DOCUMENT_LINK` | Document Links | `document_link`, `document_link_forms` | document_link, document_link_area, document_link_entity_req, inv_mast |
| `TP_SHIPMENTINFO` | Shipment Info | `transport_shipping_info` | transport_shipping_info |
| `TIMESTAMP` | Audit Trail | `timestamp`, `audit_trail` | p21_view_audit_trail_oe_pick_ticket_<id> |
| `TABPAGE_17` | Items | `tabpage_ship` | carrier_cube_factor, inv_loc, inv_loc_stock_status, inv_mast, item_revision, oe_hdr, oe_hdr_progress_billing, oe_line, oe_line_service, oe_line_service_part, oe_pick_ticket, oe_pick_ticket_detail, p21_view_getrevisionlotquantity, revision_transaction, service_inv_mast, system_setting |
| `TABPAGE_21` | Order Line Notes | `tp_21_dw_21` | note_area, notepad_class, oe_line_notepad |
| `TABPAGE_LINE_FREIGHT` | In Freight | `tabpage_line_freight` | carrier_cube_factor, inv_loc, inv_loc_stock_status, inv_mast, item_revision, oe_hdr, oe_hdr_progress_billing, oe_line, oe_line_service, oe_line_service_part, oe_pick_ticket, oe_pick_ticket_detail, p21_view_getrevisionlotquantity, revision_transaction, service_inv_mast, system_setting |
| `TABPAGE_LINE_TAX` | Taxes | `tabpage_line_tax` | inv_mast, oe_line, oe_line_tax, tax_jurisdiction |
| `DOCUMENT_LINK_DETAIL` | Document Links | `document_link_detail_detail` | document_link, document_link_area, document_link_entity_req, inv_mast, ship_to |
| `TIMESTAMPDETAIL` | Timestamp | `timestampdetail` |  |

## Datawindows

### `TABPAGE_1.tp_1_dw_1` (Shipment)

- Update table: `oe_pick_ticket`
- Tables in the SELECT: `oe_hdr`, `oe_pick_ticket`, `company`, `customer`, `cust_defaults`, `ship_to`, `terms`, `invoice_batch`, `contacts`, `freight_code`, `shipping_route`, `currency_line`, `oe_pick_ticket_detail`, `oe_line`, `oe_line_service`, `group_pick_ticket_detail`, `group_pick_ticket_hdr`, `oe_hdr_progress_billing`, `location`, `company_strategic_pricing`, `address`, `customer_strategic_pricing`, `oe_pick_ticket_ups`, `customer_terms`, `product_group`, `system_setting`, `location_packing_options`

| Field | Stored in | Basis |
|---|---|---|
| `pick_ticket_no` | `oe_pick_ticket.pick_ticket_no` | probed |
| `carrier_id` | `oe_pick_ticket.carrier_id` | column |
| `tracking_no` | `oe_pick_ticket.tracking_no` | column |
| `printpackinglist` | computed: `' '` | alias |
| `print_label` | computed: `' '` | probed |
| `instructions` | `oe_pick_ticket.instructions` | column |
| `print_invoice` | computed: `' '` | alias |
| `create_invoice` | computed: `CASE WHEN oe_pick_ticket.pick_and_hold = 'Y' THEN 'N' WHEN (oe_pick_ticket.oe_pick_ticket_type_cd = 1921 OR oe_pick_ticket.oe_pick_ticket_type_cd = 1922) THEN 'N' WHEN system_setting.VALUE = 'Y' THEN 'Y' ELSE 'N' END` | alias |
| `front_counter_tax` | `oe_pick_ticket.front_counter_tax` | column |
| `fax_invoice` | computed: `' '` | alias |
| `email_invoice` | computed: `'N'` | alias |
| `fax_packinglist` | computed: `' '` | alias |
| `ship_route` | `shipping_route.route_code` | probed |
| `email_packinglist` | computed: `'N'` | alias |
| `delete_flag` | `oe_pick_ticket.delete_flag` | column |
| `confirmable_row_status_flag` | `oe_pick_ticket.confirmable_row_status_flag` | column |
| `capture_signature` | computed: `'N'` | probed |
| `receiver_name` | computed: `''` | alias |
| `ship_through_quickship` | computed: `'N'` | alias |
| `c_send_edi_753_flag` | computed: `'N'` | alias |
| `send_ucc128info` | `customer.send_ucc128info` | column |
| `print_ucc128_labels` | computed: `'N'` | alias |
| `print_carton_labels` | computed: `COALESCE(customer.prnt_carton_label_after_final_pkg_flag, COALESCE(location_packing_options.prnt_carton_label_after_final_pkg_flag, 'N'))` | alias |
| `rfnav_pick_status_cd` | `oe_pick_ticket.rfnav_pick_status_cd` | column |
| `rfnav_stop_no` | `oe_pick_ticket.rfnav_stop_no` | column |
| `period` | computed: `0` | alias |
| `year_for_period` | computed: `0` | alias |
| `ship_date` | `oe_pick_ticket.ship_date` | column |
| `invoice_batch_number` | `invoice_batch.invoice_batch_number` | column |
| `freight_cd` | `freight_code.freight_cd` | column |
| `customer_id` | computed: `COALESCE(drv_oe_pick_ticket_detail.item_bill_to_id, oe_hdr.customer_id)` | alias |
| `order_no` | `oe_pick_ticket.order_no` | column |
| `order_date` | `oe_hdr.order_date` | column |
| `location_id` | `oe_pick_ticket.location_id` | probed |
| `invoice_no` | `oe_pick_ticket.invoice_no` | column |
| `invoice_batch_desc` | `invoice_batch.invoice_batch_desc` | column |
| `customer_name` | `address.name` | alias |
| `name` | computed: `' '` | alias |
| `freight_desc` | `freight_code.freight_desc` | column |
| `c_po_no` | computed: `(computed in the datawindow)` | dw_name |
| `cf_picktickettype` | computed: `(computed in the datawindow)` | dw_name |
| `contact_name` | computed: `(computed in the datawindow)` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Pick Ticket Number: | `oe_pick_ticket.pick_ticket_no` |
| 2 | Order Number: | `oe_pick_ticket.order_no` |
| 3 | Customer ID: | `oe_hdr.customer_id` |
| 4 | Order Date: | `oe_hdr.order_date` |
| 5 | Ship Date: | `oe_pick_ticket.ship_date` |
| 15 | Invoice Number: | `oe_pick_ticket.invoice_no` |
| 16 | Carrier Tracking Number: | `oe_pick_ticket.tracking_no` |
| 17 | Carrier: | `oe_pick_ticket.carrier_id` |
| 20 | Customer Name | `address.name` |
| 21 | Name | `address.name` |
| 24 | Instructions: | `oe_pick_ticket.instructions` |
| 44 | Print Label | `print_label` |
| 46 | Year: | `year_for_period` |
| 47 | Period: | `period` |
| 51 | Location ID: | `oe_pick_ticket.location_id` |
| 53 | Delete Flag | `oe_pick_ticket.delete_flag` |
| 61 | Sales Branch ID: | `branch_id` |
| 62 | Branch Desc | `branch_desc` |
| 63 | Front Counter Tax | `oe_pick_ticket.front_counter_tax` |
| 66 | Route: | `shipping_route.route_code` |
| 75 | Create Invoice | `create_invoice` |
| 76 | Printpackinglist | `PrintPackingList` |
| 79 | Freight Cd: | `freight_code.freight_cd` |
| 80 | Freight Desc: | `freight_code.freight_desc` |
| 84 | Fax Packinglist | `fax_packinglist` |
| 86 | Invoice Batch Number: | `invoice_batch.invoice_batch_number` |
| 87 | Invoice Batch Desc | `invoice_batch.invoice_batch_desc` |
| 91 | Email Packinglist | `email_packinglist` |
| 126 | Send Ucc128info | `customer.send_ucc128info` |
| 128 | Print Ucc128 Labels | `print_ucc128_labels` |
| 131 | Print Carton Labels | `print_carton_labels` |
| 132 | C Send Edi 753 Flag | `c_send_edi_753_flag` |
| calc | PO Number: | `"IF(IsNull(po_no), ~"~", RightTrim(po_no)) +  IF((ISNull(po_no_append) OR (po_no_append = ~"-1~") OR (po_no_append = ~"~")),` |
| calc | Cf Picktickettype | `"If( pick_and_hold = 'Y', ~"PICK AND HOLD~",      if( oe_pick_ticket_type_cd = 1921, ~"PARTS PICK TICKET~",         if( oe_pick_ticket_type_cd = 1922, ~"SERVICE PICK TICKET~", ~" ~") ) )"` |

### `TABPAGE_3.tp_3_dw_3` (Customer Notes)

- Update table: `customer_notepad`
- Tables in the SELECT: `customer_notepad`, `note_area`, `notepad_class`

| Field | Stored in | Basis |
|---|---|---|
| `note` | `customer_notepad.note` | column |
| `note_id` | `customer_notepad.note_id` | column |
| `topic` | `customer_notepad.topic` | column |
| `notepad_class_desc` | `notepad_class.notepad_class_desc` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Note ID | `customer_notepad.note_id` |
| 2 | Topic | `customer_notepad.topic` |
| 3 | Note | `customer_notepad.note` |
| 5 | Class | `notepad_class.notepad_class_desc` |

### `TABPAGE_5.tp_5_dw_5` (Remittance)

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
| `switch_issue_number` | `p21_view_creditcard_payment_details.switch_issue_number` | probed |
| `multi_currency_id` | `ar_payment_details.multi_currency_id` | column |
| `multi_currency_payment_amount` | `ar_payment_details.multi_currency_payment_amount` | column |
| `rental_payment_amt` | computed: `0` | alias |
| `exchange_date` | computed: `COALESCE(ar_payment_details.exchange_rate_override_date, ar_payment_details.date_created)` | alias |
| `cc_swipe` | computed: `' '` | alias |
| `override_surcharge` | `ar_payment_details.override_surcharge` | column |
| `memo_amount` | `ar_payment_details.memo_amount` | column |
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
| 22 | Cf Pay Total | `ar_payment_details.cf_pay_total` |
| 24 | AP Credit Memo: | `ar_payment_details.memo_amount` |
| 25 | Cc Swipe | `cc_swipe` |
| 27 | Authorized Amount: | `p21_view_creditcard_payment_details.auth_amount` |
| 37 | Payment Amount Home | `p21_view_ar_payment_details.payment_amount_home` |
| 38 | Auth Amount Home | `p21_view_creditcard_payment_details.auth_amount_home` |
| 48 | Cash Pymt Amt: | `c_cash_pymt_amt` |
| 50 | CC Number: | `cc_creditcard_number` |
| 53 | Switch Issue Number | `p21_view_creditcard_payment_details.switch_issue_number` |
| 81 | Rental Amount: | `rental_payment_amt` |
| 83 | Override Surcharge | `ar_payment_details.override_surcharge` |
| calc | Cf Rowinfo | `'Payment ' + string(getrow()) + ' of ' + String(rowcount())` |

### `TABPAGE_5.dw_totals` (Remittance)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `c_dp_to_apply` | ? | no_sql |
| `c_prev_pymt_not_appd` | ? | no_sql |
| `c_prev_open_inv_total` | ? | no_sql |
| `c_open_dp_inv_amt` | ? | no_sql |
| `c_unapplied_dp` | ? | no_sql |
| `amount_tendered` | ? | no_sql |
| `tax` | ? | no_sql |
| `sub_total` | ? | no_sql |
| `balance` | ? | no_sql |
| `cf_sugg_pymt` | ? | no_sql |
| `cf_downpayment_remaining` | ? | no_sql |
| `invoice_total` | ? | no_sql |
| `downpayment_remaining` | ? | no_sql |
| `total_due` | ? | no_sql |
| `balance_t1` | ? | no_sql |
| `cf_prorated_amount` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Ship Total: | `sub_total` |
| 2 | Tax: | `tax` |
| 5 | Amt Tendered: | `amount_tendered` |
| 13 | DP To Apply: | `c_dp_to_apply` |
| 14 | Unapplied Pymt: | `c_unapplied_dp` |
| 16 | Open DP Inv Amt: | `c_open_dp_inv_amt` |
| calc | Balance: | `cf_sugg_pymt  -  amount_tendered` |
| calc | Sugg Pymt for Inv: | `if(sub_total  +  tax+ if(isnull(total_wee_tax), 0, total_wee_tax) + if(isnull(total_eco_fee), 0, total_eco_fee)  -  c_dp_to_apply - bldr_allowance_remaining < 0, 0, sub_total  +  tax + if(isnull(total_wee_tax), 0, total_wee_tax)  +  if(isnull(total_eco_fee), 0, total_eco_fee) -  c_dp_to_apply - bldr_allowance_remaining) + if(isNull(c_price_rounding_offset), 0, c_price_rounding_offset)` |

### `TABPAGE_5.tp_5_dw_req_pymt` (Remittance)

- Update table: `oe_hdr`
- Tables in the SELECT: `oe_hdr`, `address`, `shipping_route`, `currency_line`, `ship_to`

| Field | Stored in | Basis |
|---|---|---|
| `req_pymt_upon_release_flag` | `oe_hdr.req_pymt_upon_release_flag` | column |

| # | Label | table.column / expression |
|---|---|---|
| 68 | Req Pymt Upon Release Flag | `oe_hdr.req_pymt_upon_release_flag` |

### `TABPAGE_6.tp_6_dw_6` (Order Notes)

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

### `HDR_NOTE.hdr_note` (Invoice Notes)

- Update table: `invoice_hdr_notepad`
- Tables in the SELECT: `invoice_hdr_notepad`, `note_area`, `notepad_class`

| Field | Stored in | Basis |
|---|---|---|
| `note` | `invoice_hdr_notepad.note` | column |
| `note_id` | `invoice_hdr_notepad.note_id` | column |
| `topic` | `invoice_hdr_notepad.topic` | column |
| `notepad_class_desc` | `notepad_class.notepad_class_desc` | column |

| # | Label | table.column / expression |
|---|---|---|
| 2 | Note ID | `invoice_hdr_notepad.note_id` |
| 3 | Topic | `invoice_hdr_notepad.topic` |
| 4 | Note | `invoice_hdr_notepad.note` |
| 14 | Class | `notepad_class.notepad_class_desc` |

### `TABPAGE_SHIPTO.tabpage_shipto` (Ship To)

- Update table: `oe_pick_ticket`
- Tables in the SELECT: `oe_hdr`, `oe_pick_ticket`, `company`, `customer`, `cust_defaults`, `ship_to`, `terms`, `invoice_batch`, `contacts`, `freight_code`, `shipping_route`, `currency_line`, `oe_pick_ticket_detail`, `oe_line`, `oe_line_service`, `group_pick_ticket_detail`, `group_pick_ticket_hdr`, `oe_hdr_progress_billing`, `location`, `company_strategic_pricing`, `address`, `customer_strategic_pricing`, `oe_pick_ticket_ups`, `customer_terms`, `product_group`, `system_setting`, `location_packing_options`

| Field | Stored in | Basis |
|---|---|---|
| `address_id` | `oe_hdr.address_id` | column |
| `contact_id` | `oe_hdr.contact_id` | column |
| `ship2_add1` | `oe_hdr.ship2_add1` | probed |
| `ship2_add2` | `oe_hdr.ship2_add2` | column |
| `ship2_city` | `oe_hdr.ship2_city` | column |
| `ship2_name` | `oe_hdr.ship2_name` | column |
| `ship2_state` | `oe_hdr.ship2_state` | column |
| `ship2_zip` | `oe_hdr.ship2_zip` | column |
| `ship2_country` | `oe_hdr.ship2_country` | column |
| `contact_name` | computed: `(computed in the datawindow)` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 8 | Ship To Name: | `oe_hdr.ship2_name` |
| 9 | Ship To Address: | `oe_hdr.ship2_add1` |
| 10 | Ship2 Add2 | `oe_hdr.ship2_add2` |
| 11 | Ship To City/State/Zip/Country: | `oe_hdr.ship2_city` |
| 12 | Ship2 State | `oe_hdr.ship2_state` |
| 13 | Ship2 Zip | `oe_hdr.ship2_zip` |
| 14 | Ship2 Country | `oe_hdr.ship2_country` |
| 18 | Ship To ID: | `oe_hdr.address_id` |
| 19 | Contact ID: | `oe_hdr.contact_id` |
| calc | Contact Name | `trim(first_name) + " " + if(isNull(mi),"",mi + "." ) + " " + trim(last_name)` |

### `TABPAGE_FREIGHT.tabpage_freight` (Out Freight)

- Update table: `oe_pick_ticket`
- Tables in the SELECT: `oe_hdr`, `oe_pick_ticket`, `company`, `customer`, `cust_defaults`, `ship_to`, `terms`, `invoice_batch`, `contacts`, `freight_code`, `shipping_route`, `currency_line`, `oe_pick_ticket_detail`, `oe_line`, `oe_line_service`, `group_pick_ticket_detail`, `group_pick_ticket_hdr`, `oe_hdr_progress_billing`, `location`, `company_strategic_pricing`, `address`, `customer_strategic_pricing`, `oe_pick_ticket_ups`, `customer_terms`, `product_group`, `system_setting`, `location_packing_options`

| Field | Stored in | Basis |
|---|---|---|
| `freight_cd` | `freight_code.freight_cd` | column |
| `freight_out` | `oe_pick_ticket.freight_out` | column |
| `use_strategic_freight` | computed: `CASE WHEN ((address.carrier_strategic_freight_flag = 'Y' OR address.carrier_strategic_freight_flag = 'I' OR address.carrier_strategic_freight_flag = 'O') AND address.carrier_strategic_freight_flag IS NOT NULL AND address.carrier_strategic_freight_flag IS NOT NULL AND customer_strategic_pricing.freight_charge_option_cd IS NOT NULL) THEN CASE WHEN customer_strategic_pricing.freight_charge_option_cd = 2630 THEN 'Y' ELSE 'N' END ELSE 'N' END` | alias |
| `freight_desc` | `freight_code.freight_desc` | column |

| # | Label | table.column / expression |
|---|---|---|
| 7 | Outgoing Freight: | `oe_pick_ticket.freight_out` |
| 79 | Freight Code: | `freight_code.freight_cd` |
| 80 | Freight Desc | `freight_code.freight_desc` |
| 109 | Use Strategic Freight | `use_strategic_freight` |

### `TABPAGE_TAX.tabpage_tax` (Tax)

- Update table: `oe_hdr_tax`
- Tables in the SELECT: `oe_hdr_tax`, `tax_jurisdiction`

| Field | Stored in | Basis |
|---|---|---|
| `jurisdiction_id` | `oe_hdr_tax.jurisdiction_id` | column |
| `taxable` | `oe_hdr_tax.taxable` | column |
| `jurisdiction_desc` | `tax_jurisdiction.jurisdiction_desc` | column |
| `flat_fee_amount` | `tax_jurisdiction.flat_fee_amount` | column |
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

### `TABPAGE_ORDERBINS.tabpage_orderbins` (Order Bins)

- Update table: `document_line_bin`
- Tables in the SELECT: `document_line_bin`, `bin`, `oe_pick_ticket`

| Field | Stored in | Basis |
|---|---|---|
| `bin_cd` | `document_line_bin.bin_cd` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Bin | `document_line_bin.bin_cd` |

### `DOCUMENT_LINK.document_link` (Document Links)

- Update table: `document_link`
- Tables in the SELECT: `document_link`, `document_link_area`, `inv_mast`, `document_link_entity_req`

| Field | Stored in | Basis |
|---|---|---|
| `link_name` | `document_link.link_name` | column |
| `link_path` | `document_link.link_path` | column |
| `row_status_flag` | `document_link.row_status_flag` | column |
| `mandatory_flag` | `document_link.mandatory_flag` | probed |
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

### `TP_SHIPMENTINFO.transport_shipping_info` (Shipment Info)

- Update table: `transport_shipping_info`
- Tables in the SELECT: `transport_shipping_info`

| Field | Stored in | Basis |
|---|---|---|
| `trailer_no` | `transport_shipping_info.trailer_no` | column |
| `shipment_gross_weight` | `transport_shipping_info.shipment_gross_weight` | probed |
| `internal_transaction_no` | `transport_shipping_info.internal_transaction_no` | column |
| `bill_of_lading_no` | `transport_shipping_info.bill_of_lading_no` | column |
| `commercial_invoice_no` | `transport_shipping_info.commercial_invoice_no` | column |

| # | Label | table.column / expression |
|---|---|---|
| 3 | Trailer Number: | `transport_shipping_info.trailer_no` |
| 4 | Shipment Gross Weight: | `transport_shipping_info.shipment_gross_weight` |
| 5 | Internal Transaction Number (ITN): | `transport_shipping_info.internal_transaction_no` |
| 11 | Bill of Lading Number: | `transport_shipping_info.bill_of_lading_no` |
| 12 | Proforma Invoice Number: | `transport_shipping_info.commercial_invoice_no` |

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

- Update table: `p21_view_audit_trail_oe_pick_ticket_<id>`
- Tables in the SELECT: `p21_view_audit_trail_oe_pick_ticket_<id>`
- Mapped off-tab: the API could not select this tab (HTTP 400: Multiple tabs have a name or display text of TIMESTAMP.); SQL Information reads an instantiated datawindow whichever tab is active

| Field | Stored in | Basis |
|---|---|---|
| `item_id` | `p21_view_audit_trail_oe_pick_ticket_<id>.item_id` | probed |
| `column_description` | `p21_view_audit_trail_oe_pick_ticket_<id>.column_description` | probed |
| `old_value` | `p21_view_audit_trail_oe_pick_ticket_<id>.old_value` | probed |
| `new_value` | `p21_view_audit_trail_oe_pick_ticket_<id>.new_value` | probed |
| `date_created` | `p21_view_audit_trail_oe_pick_ticket_<id>.date_created` | probed |
| `created_by` | `p21_view_audit_trail_oe_pick_ticket_<id>.created_by` | probed |
| `cf_display_key` | computed: `(computed in the datawindow)` | dw_name |
| `cf_sub_line_no` | computed: `(computed in the datawindow)` | dw_name |
| `cf_line_no_visible` | computed: `(computed in the datawindow)` | dw_name |
| `cf_item_id_visible` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 5 | Column Changed | `column_description` |
| 14 | Old Value | `old_value` |
| 15 | New Value | `new_value` |
| 18 | Date Created | `date_created` |
| 19 | Created By | `created_by` |
| 21 | 'Item IDIF (source_area_cd = 950, 'Process', IF(source_area_cd = 1302, 'Component ID', 'Item ID'))' | `item_id` |
| calc | Key Values | `"IF ((source_area_cd = 1763 and key1_cd = 'service_labor_uid'), item_id,  IF (source_area_cd = 950, key1_value,  IF (key2_cd = 'item_service_uid',  Item_id + ' / ALL / ALL',  IF ( key2_cd = 'lot_cd', key2_value,   IF ( Len(auxiliary_value) > 0 AND source_area_cd IN (1544, 1250, 2531), auxiliary_value,  IF (source_area_cd = 1314 and table_changed = 'inv_mast_strategic_pricing', item_id + '/' + key3_value + IF (IsNull(key2_value), '', '/' + auxiliary_value),  IF ( key1_cd = 'inv_mast_uid', item_id, key1_value ) + IF ( IsNull ( key2_value) AND source_area_cd <> 1314, '', ' / ' + IF ( key2_cd = 'inv_mast_uid', item_id, IF ( IsNull ( key2_value ), 'ALL', key2_value ) )  + IF ( IsNull (key3_value) AND source_area_cd <> 1314, '', ' / ' + IF ( key3_cd = 'inv_mast_uid', item_id, IF ( IsNull ( key3_value ), 'ALL', key3_value ) ) ) )  ) ) ) ) ) )"` |
| calc | 'Sub Line No | `` |

### `TABPAGE_17.tabpage_ship` (Items)

- Update table: `oe_pick_ticket_detail`
- Tables in the SELECT: `oe_pick_ticket_detail`, `oe_pick_ticket`, `inv_mast`, `inv_loc`, `oe_hdr`, `oe_line`, `system_setting`, `inv_loc_stock_status`, `oe_line_service`, `service_inv_mast`, `oe_line_service_part`, `oe_hdr_progress_billing`, `revision_transaction`, `item_revision`, `p21_view_getrevisionlotquantity`, `carrier_cube_factor`

| Field | Stored in | Basis |
|---|---|---|
| `oe_order_item_id` | `inv_mast.item_id` | probed |
| `trans_revision_level` | `item_revision.revision_level` | alias |
| `unit_quantity` | computed: `0.000000000` | alias |
| `disposition` | computed: `''` | alias |
| `unit_of_measure` | computed: `''` | alias |
| `rfnav_pick_status_cd` | `oe_pick_ticket_detail.rfnav_pick_status_cd` | column |
| `line_id` | `oe_pick_ticket_detail.line_number` | probed |
| `item_desc` | `inv_mast.item_desc` | column |
| `units_picked` | computed: `CAST(Round(oe_pick_ticket_detail.print_quantity / oe_pick_ticket_detail.unit_size, 9) AS Decimal(19,9))` | alias |
| `c_releaseline` | computed: `CASE WHEN oe_pick_ticket_detail.release_no > 0 THEN 'Y' ELSE 'N' END` | alias |
| `cf_expandableindicator` | computed: `(computed in the datawindow)` | dw_name |
| `qty_available_display` | computed: `(computed in the datawindow)` | probed |
| `compute_1` | computed: `(computed in the datawindow)` | dw_name |
| `undershipped_qty` | computed: `(computed in the datawindow)` | probed |
| `line_item_price` | computed: `(computed in the datawindow)` | probed |
| `new_pick_qty` | computed: `(computed in the datawindow)` | probed |
| `total_amount` | computed: `(computed in the datawindow)` | probed |
| `new_invoice_qty` | computed: `(computed in the datawindow)` | probed |
| `sched_oeline_print_qty` | computed: `(computed in the datawindow)` | probed |
| `sum_price` | computed: `(computed in the datawindow)` | dw_name |
| `qty_available` | computed: `(computed in the datawindow)` | probed |
| `sched_total_ordered_qty` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Item ID | `inv_mast.item_id` |
| 11 | Item Description | `inv_mast.item_desc` |
| 37 | Disp | `oe_line.disposition` |
| 42 | UOM | `oe_pick_ticket_detail.unit_of_measure` |
| 44 | QuantityShipped | `oe_line.unit_quantity` |
| 65 | QuantityPicked | `units_picked` |
| 100 | Serial Number | `service_inv_mast.serial_number` |
| 101 | Release | `c_releaseline` |
| calc | = if(((oe_line_assembly in ('B', 'P'))) or (lot_bill | `'Y'), "+","")` |
| calc | Quantity Available | `"/* qty_available_display */  if(oe_pick_ticket_type_cd = 1922, 1,      if (qty_available < 0 OR IsNull (qty_available), 0, qty_available))"` |

### `TABPAGE_21.tp_21_dw_21` (Order Line Notes)

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

### `TABPAGE_LINE_FREIGHT.tabpage_line_freight` (In Freight)

- Update table: `oe_pick_ticket_detail`
- Tables in the SELECT: `oe_pick_ticket_detail`, `oe_pick_ticket`, `inv_mast`, `inv_loc`, `oe_hdr`, `oe_line`, `system_setting`, `inv_loc_stock_status`, `oe_line_service`, `service_inv_mast`, `oe_line_service_part`, `oe_hdr_progress_billing`, `revision_transaction`, `item_revision`, `p21_view_getrevisionlotquantity`, `carrier_cube_factor`

| Field | Stored in | Basis |
|---|---|---|
| `freight_in` | `oe_pick_ticket_detail.freight_in` | column |
| `use_strategic_freight` | computed: `''` | alias |
| `c_freight_edited` | computed: `'N'` | alias |
| `item_id` | `inv_mast.item_id` | column |
| `item_desc` | `inv_mast.item_desc` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Item ID: | `inv_mast.item_id` |
| 11 | Item Desc | `inv_mast.item_desc` |
| 59 | Incoming Freight: | `oe_pick_ticket_detail.freight_in` |
| 83 | C Freight Edited | `c_freight_edited` |
| 115 | Use Strategic Freight | `use_strategic_freight` |

### `TABPAGE_LINE_TAX.tabpage_line_tax` (Taxes)

- Update table: `oe_line_tax`
- Tables in the SELECT: `oe_line_tax`, `oe_line`, `tax_jurisdiction`, `inv_mast`

| Field | Stored in | Basis |
|---|---|---|
| `jurisdiction_id` | `oe_line_tax.jurisdiction_id` | column |
| `taxable` | `oe_line_tax.taxable` | column |
| `delete_flag` | `oe_line_tax.delete_flag` | probed |
| `item_id` | `inv_mast.item_id` | column |
| `item_desc` | `inv_mast.item_desc` | column |
| `jurisdiction_desc` | `tax_jurisdiction.jurisdiction_desc` | column |
| `tax_percentage` | `tax_jurisdiction.tax_percentage` | column |
| `flat_fee_amount` | `tax_jurisdiction.flat_fee_amount` | column |
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
| 12 | Tax Percentage | `tax_jurisdiction.tax_percentage` |
| 20 | Flat Rate Amount | `tax_jurisdiction.flat_fee_amount` |

### `DOCUMENT_LINK_DETAIL.document_link_detail_detail` (Document Links)

- Update table: `document_link`
- Tables in the SELECT: `document_link`, `document_link_area`, `inv_mast`, `ship_to`, `document_link_entity_req`

| Field | Stored in | Basis |
|---|---|---|
| `link_name` | `document_link.link_name` | probed |
| `link_path` | `document_link.link_path` | column |
| `row_status_flag` | `document_link.row_status_flag` | column |
| `mandatory_flag` | `document_link.mandatory_flag` | column |
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
| `TABPAGE_2` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_2 does not exist.); hidden placeholder page |
| `TABPAGE_4` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_4 does not exist.); hidden placeholder page |
| `TABPAGE_7` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_8` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TP_SHIPPING` | Shipping | `shipment_header` | datawindow never instantiated (tab not enabled) |
| `REASONCODESHDR` | Reason Codes | `reasoncodeshdr` | datawindow never instantiated (tab not enabled) |
| `TP_SCANPACK` | Scan and Pack | `scan_pack_container_hdr` | skipped: TP_SCANPACK hangs the Shipping window over the API |
| `TABPAGE_18` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_18 does not exist.); hidden placeholder page |
| `TABPAGE_19` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_19 does not exist.); hidden placeholder page |
| `TABPAGE_20` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_20 does not exist.); hidden placeholder page |
| `TABPAGE_22` | Pricing | `prices` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_22` | Pricing | `tp_22_dw_price_page` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_23` | Undership | `tp_23_dw_23` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_24` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_24 does not exist.); hidden placeholder page |
| `CUST_PARTNO_NOTES` | Customer Part Number Notes | `cust_partno_notes` | datawindow never instantiated (tab not enabled) |
| `ITEM_NOTES` | Item Notes | `item_notes` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_SERIAL` | Serial | `serial` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_LOT` | Lot | `tabpage_lot` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_LOT_BIN_XREF` | Lot/Bin | `tabpage_lot_bin_xref` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_BIN` | Bin | `tabpage_bin` | datawindow never instantiated (tab not enabled) |
| `REASONCODESLINE` | Reason Codes | `reasoncodesline` | datawindow never instantiated (tab not enabled) |
| `DOCUMENT_LINK_DETAIL` | Document Links | `document_link_forms` | datawindow never instantiated (tab not enabled) |
| `TP_TAGS` | Tags | `tp_tags_tdl_header` | datawindow never instantiated (tab not enabled) |
| `TP_TAGS` | Tags | `tp_tags_dlt` | datawindow never instantiated (tab not enabled) |
| `TP_TAGS_VIEW` | Tag Results | `tp_tags_view` | datawindow never instantiated (tab not enabled) |
| `TP_SHIPPART` | Parts | `tp_shippart` | datawindow never instantiated (tab not enabled) |
| `TIMESTAMPDETAIL` | Timestamp | `timestampdetail_dw_audittrail` | datawindow never instantiated (tab not enabled) |
