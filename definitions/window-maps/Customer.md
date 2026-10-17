# Customer Maintenance (`Customer`)

- Window class: `w_customer_maint_sheet`; menu class: `m_customermaintenance`
- Tabs: 33; datawindows mapped: 31; unreachable entries: 5

## Tab overview

| Tab | Caption | Datawindows mapped | Tables in the SELECT |
|---|---|---|---|
| `TABPAGE_1` | Customer Information | `tp_1_dw_1` | address, company, contacts, crm_contact_information, cust_part_no_group_hdr, customer, customer_cons_inv_cardlock, customer_freight_display, customer_vat, data_identifier_group, freight_charge, invoice_batch, lead_source, partner_program, ship_to, sic, trackabout_rental_bracket |
| `TABPAGE_2` | Accounts | `tp_2_dw_2` | address, company, contacts, crm_contact_information, cust_part_no_group_hdr, customer, customer_cons_inv_cardlock, customer_freight_display, customer_vat, data_identifier_group, freight_charge, invoice_batch, lead_source, partner_program, ship_to, sic, trackabout_rental_bracket |
| `TABPAGE_4` | Credit | `tp_4_dw_4` | address, company, contacts, crm_contact_information, cust_part_no_group_hdr, customer, customer_cons_inv_cardlock, customer_freight_display, customer_vat, data_identifier_group, freight_charge, invoice_batch, lead_source, partner_program, ship_to, sic, trackabout_rental_bracket |
| `TABPAGE_5` | Physical Address And Phone | `tp_5_dw_5` | address, company, contacts, crm_contact_information, cust_part_no_group_hdr, customer, customer_cons_inv_cardlock, customer_freight_display, customer_vat, data_identifier_group, freight_charge, invoice_batch, lead_source, partner_program, ship_to, sic, trackabout_rental_bracket |
| `TABPAGE_6` | OE Options | `tp_6_dw_6` | address, company, contacts, crm_contact_information, cust_part_no_group_hdr, customer, customer_cons_inv_cardlock, customer_freight_display, customer_vat, data_identifier_group, freight_charge, invoice_batch, lead_source, partner_program, ship_to, sic, trackabout_rental_bracket |
| `TABPAGE_7` | Sales Pricing | `tp_7_dw_7`, `tp_7_dw_price_library` | address, company, contacts, crm_contact_information, cust_part_no_group_hdr, customer, customer_cons_inv_cardlock, customer_freight_display, customer_vat, data_identifier_group, freight_charge, invoice_batch, lead_source, partner_program, price_library, price_library_x_cust_x_cmpy, ship_to, sic, trackabout_rental_bracket |
| `TABPAGE_8` | Billing | `tp_8_dw_8` | address, company, contacts, crm_contact_information, cust_part_no_group_hdr, customer, customer_cons_inv_cardlock, customer_freight_display, customer_vat, data_identifier_group, freight_charge, invoice_batch, lead_source, partner_program, ship_to, sic, trackabout_rental_bracket |
| `GENERAL` | General | `general` | address, company, contacts, crm_contact_information, cust_part_no_group_hdr, customer, customer_cons_inv_cardlock, customer_freight_display, customer_vat, data_identifier_group, freight_charge, invoice_batch, lead_source, partner_program, ship_to, sic, trackabout_rental_bracket |
| `CLASSES` | Classes | `classes` | address, company, contacts, crm_contact_information, cust_part_no_group_hdr, customer, customer_cons_inv_cardlock, customer_freight_display, customer_vat, data_identifier_group, freight_charge, invoice_batch, lead_source, partner_program, ship_to, sic, trackabout_rental_bracket |
| `TAX` | Tax | `tax` | address, company, contacts, crm_contact_information, cust_part_no_group_hdr, customer, customer_cons_inv_cardlock, customer_freight_display, customer_vat, data_identifier_group, freight_charge, invoice_batch, lead_source, partner_program, ship_to, sic, trackabout_rental_bracket |
| `LINKS` | Contacts | `links` |  |
| `TERRITORY` | Territory | `territory` |  |
| `SHIP_TO_GENERAL` | Ship To Info (General) | `ship_to_general` | branch, customer, document_link_entity_req, freight_code, ship_to, shipping_route |
| `SHIP_TO_DELIVERY` | Ship To Info (Delivery) | `ship_to_delivery` | branch, customer, document_link_entity_req, freight_code, ship_to, shipping_route |
| `SHIP_TO_LABELS` | Ship To Labels | `ship_to_labels`, `ship_to_labels_dw_0` | address, code_p21, company, contacts, crm_contact_information, cust_part_no_group_hdr, customer, customer_cons_inv_cardlock, customer_freight_display, customer_vat, data_identifier_group, freight_charge, invoice_batch, label_definition, label_definition_x_customer, lead_source, partner_program, ship_to, sic, trackabout_rental_bracket |
| `SHIP_TOS` | Ship Tos | `ship_tos` | address, crm_contact_information, customer, ship_to |
| `EDI` | Electronic Data Interchange | `edi`, `editransactions`, `editransdetail` | code_p21, customer, customer_edi_setting, customer_edi_transaction |
| `DOCUMENT_LINK` | Document Links | `document_link` | document_link, document_link_area, document_link_entity_req, inv_mast |
| `TP_CUSTOMERSTRATGICPRICING` | Customer Strategic Pricing | `customer_strategic_pricing` | customer, customer_category, customer_strategic_pricing |
| `CUSTOMERSALESREP` | Salesrep | `customersalesrep` | contacts, customer_salesrep |
| `TP_PAYMENTACCOUNT` | Payment Account | `tp_paymentaccount` | code_p21, company, customer, payment_account, payment_account_x_customer, payment_types |
| `TP_DEALERTYPE` | Dealer Type | `tp_dealertype` | address, company, customer_x_dealer_type, dealer_type |
| `CUSTOMERFORMTAB` | Forms | `customerformtab` | customer_form_template |
| `TP_CUSTOMERMERGEAUDIT` | Merge Tracking | `customer_merge_audit` | customer, customer_merge_audit |
| `TP_EMAILDEFAULTS` | Email Defaults | `customer_email_defaults` | code_p21, customer_email_defaults |
| `TIMESTAMP` | Audit Trail | `audit_trail`, `timestamp` | p21_view_audit_trail_customer_<id> |

## Datawindows

### `TABPAGE_1.tp_1_dw_1` (Customer Information)

- Update table: `customer`
- Tables in the SELECT: `customer`, `company`, `address`, `invoice_batch`, `contacts`, `sic`, `ship_to`, `cust_part_no_group_hdr`, `data_identifier_group`, `lead_source`, `freight_charge`, `crm_contact_information`, `customer_freight_display`, `customer_cons_inv_cardlock`, `customer_vat`, `partner_program`, `trackabout_rental_bracket`

| Field | Stored in | Basis |
|---|---|---|
| `company_id` | `customer.company_id` | column |
| `customer_id` | `customer.customer_id` | column |
| `customer_name` | `address.name` | probed |
| `mail_address1` | `address.mail_address1` | column |
| `mail_address2` | `address.mail_address2` | column |
| `mail_city` | `address.mail_city` | column |
| `mail_state` | `address.mail_state` | column |
| `mail_postal_code` | `address.mail_postal_code` | column |
| `customer_cod_required_flag` | `customer.cod_required_flag` | probed |
| `mail_country` | `address.mail_country` | column |
| `customer_fob_required_flag` | `customer.fob_required_flag` | probed |
| `salesrep_id` | `customer.salesrep_id` | column |
| `customer_type_cd` | `customer.customer_type_cd` | column |
| `lead_source_id` | `customer.lead_source_id` | column |
| `wee_taxable_flag` | `customer_vat.wee_taxable_flag` | alias |
| `wee_collected_account_no` | `customer_vat.wee_collected_account_no` | column |
| `corp_address_id` | `address.corp_address_id` | column |
| `billing_address_id` | `address.billing_address_id` | column |
| `terms_id` | `customer.terms_id` | column |
| `service_terms_id` | `customer.service_terms_id` | column |
| `shipping_address` | `address.shipping_address` | column |
| `delete_flag` | `customer.delete_flag` | probed |
| `currency_id` | `customer.currency_id` | column |
| `date_acct_opened` | `customer.date_acct_opened` | column |
| `consolidated_ship_to_id` | `customer.consolidated_ship_to_id` | column |
| `parker_customer_cd` | `customer.parker_customer_cd` | column |
| `web_enabled_flag` | `customer.web_enabled_flag` | column |
| `pedigree_customer` | `customer.pedigree_customer` | column |
| `last_hard_touch_date` | `crm_contact_information.last_hard_touch_date` | column |
| `national_flag` | `customer.national_account_flag` | alias |
| `legal_name` | `customer.legal_name` | column |
| `calculate_item_surcharge_flag` | `customer.calculate_item_surcharge_flag` | alias |
| `salesrep_name` | computed: `(contacts_a.last_name + ', ' + contacts_a.first_name + ' ' + COALESCE(contacts_a.mi, ''))` | alias |
| `company_name` | `company.company_name` | column |
| `source_description` | `lead_source.source_description` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Company ID: | `customer.company_id` |
| 2 | Company Name | `company.company_name` |
| 3 | Customer ID: | `customer.customer_id` |
| 8 | Sales Terms: | `customer.terms_id` |
| 9 | Salesrep ID: | `customer.salesrep_id` |
| 17 | Delete Flag | `customer.delete_flag` |
| 21 | Customer Name | `address.name` |
| 22 | Mail Address 1: | `address.mail_address1` |
| 23 | Mail Address 2: | `address.mail_address2` |
| 24 | Mail City/State/Zip: | `address.mail_city` |
| 25 | Mail State | `address.mail_state` |
| 26 | Mail Postal Code | `address.mail_postal_code` |
| 27 | Mail Country: | `address.mail_country` |
| 48 | Corp Address ID: | `address.corp_address_id` |
| 53 | Shipping Address | `address.shipping_address` |
| 63 | Billing Address ID: | `address.billing_address_id` |
| 97 | Salesrep Name | `compute_0097` |
| 155 | Date Account Opened: | `customer.date_acct_opened` |
| 173 | Customer Type: | `customer.customer_type_cd` |
| 174 | Lead Source ID: | `customer.lead_source_id` |
| 181 | Source Description | `lead_source.source_description` |
| 183 | Service Terms: | `customer.service_terms_id` |
| 188 | Web Enabled Flag | `customer.web_enabled_flag` |
| 189 | Parker Customer Code: | `customer.parker_customer_cd` |
| 198 | Pedigree Customer | `customer.pedigree_customer` |
| 201 | Last Hard Touch: | `crm_contact_information.last_hard_touch_date` |
| 262 | Calculate Item Surcharge Flag | `customer.calculate_item_surcharge_flag` |

### `TABPAGE_2.tp_2_dw_2` (Accounts)

- Update table: `customer`
- Tables in the SELECT: `customer`, `company`, `address`, `invoice_batch`, `contacts`, `sic`, `ship_to`, `cust_part_no_group_hdr`, `data_identifier_group`, `lead_source`, `freight_charge`, `crm_contact_information`, `customer_freight_display`, `customer_cons_inv_cardlock`, `customer_vat`, `partner_program`, `trackabout_rental_bracket`

| Field | Stored in | Basis |
|---|---|---|
| `ar_account_no` | `customer.ar_account_no` | column |
| `pending_payment_account_no` | `customer.pending_payment_account_no` | column |
| `revenue_account_no` | `customer.revenue_account_no` | column |
| `cos_account_no` | `customer.cos_account_no` | column |
| `allowed_account_no` | `customer.allowed_account_no` | column |
| `terms_account_no` | `customer.terms_account_no` | column |
| `freight_account_no` | `customer.freight_account_no` | column |
| `brokerage_account_no` | `customer.brokerage_account_no` | column |
| `deferred_revenue_account_no` | `customer.deferred_revenue_account_no` | column |
| `finance_chg_revenue_account_no` | `customer.finance_chg_revenue_account_no` | probed |
| `dealer_wrrty_claims_account_no` | `customer.dealer_wrrty_claims_account_no` | column |
| `cfn_cost_goods_sold_acct` | computed: `(computed in the datawindow)` | dw_name |
| `cfn_receivable_acct` | computed: `(computed in the datawindow)` | dw_name |
| `cfn_revenue_acct` | computed: `(computed in the datawindow)` | dw_name |
| `allowed_account_no_desc` | computed: `' '` | probed |
| `ar_account_no_desc` | computed: `' '` | probed |
| `brokerage_account_no_desc` | computed: `' '` | probed |
| `deferred_revenue_account_no_desc` | computed: `' '` | probed |
| `terms_account_no_desc` | computed: `' '` | probed |
| `cos_account_no_desc` | computed: `' '` | probed |
| `revenue_account_no_desc` | computed: `' '` | probed |
| `pending_payment_account_no_desc` | computed: `' '` | probed |
| `freight_account_no_desc` | computed: `' '` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 12 | AR Account: | `customer.ar_account_no` |
| 13 | Revenue Account: | `customer.revenue_account_no` |
| 14 | Cost Of Sales Account: | `customer.cos_account_no` |
| 15 | Allowed Account: | `customer.allowed_account_no` |
| 16 | Terms Account: | `customer.terms_account_no` |
| 37 | Freight Account: | `customer.freight_account_no` |
| 38 | Brokerage Account: | `customer.brokerage_account_no` |
| 84 | Ar Account No Desc | `compute_0084` |
| 85 | Revenue Account No Desc | `compute_0085` |
| 86 | Cos Account No Desc | `compute_0086` |
| 87 | Allowed Account No Desc | `compute_0087` |
| 88 | Terms Account No Desc | `compute_0088` |
| 89 | Freight Account No Desc | `compute_0089` |
| 90 | Brokerage Account No Desc | `compute_0090` |
| 106 | Deferred Revenue Account: | `customer.deferred_revenue_account_no` |
| 107 | Deferred Revenue Account No Desc | `deferred_revent_account_desc` |
| 137 | Pending Payments Account: | `customer.pending_payment_account_no` |
| 138 | Pending Payment Account No Desc | `compute_0124` |

### `TABPAGE_4.tp_4_dw_4` (Credit)

- Update table: `customer`
- Tables in the SELECT: `customer`, `company`, `address`, `invoice_batch`, `contacts`, `sic`, `ship_to`, `cust_part_no_group_hdr`, `data_identifier_group`, `lead_source`, `freight_charge`, `crm_contact_information`, `customer_freight_display`, `customer_cons_inv_cardlock`, `customer_vat`, `partner_program`, `trackabout_rental_bracket`

| Field | Stored in | Basis |
|---|---|---|
| `customer_credit_status` | `customer.credit_status` | probed |
| `customer_credit_limit_per_order` | `customer.credit_limit_per_order` | probed |
| `customer_credit_limit_check_at_shipment` | `customer.credit_limit_check_at_shipment` | probed |
| `credit_limit` | `customer.credit_limit` | column |
| `credit_limit_used` | `customer.credit_limit_used` | column |
| `highest_credit_limit_used` | `customer.highest_credit_limit_used` | column |

| # | Label | table.column / expression |
|---|---|---|
| 6 | Credit Limit: | `customer.credit_limit` |
| 7 | Credit Limit Used: | `customer.credit_limit_used` |
| 64 | Credit Limit Per Order: | `customer.credit_limit_per_order` |
| 71 | Customer Credit Limit Check At Shipment | `customer.credit_limit_check_at_shipment` |
| 101 | Highest Credit Limit Used: | `customer.highest_credit_limit_used` |
| 105 | Credit Status: | `customer.credit_status` |

### `TABPAGE_5.tp_5_dw_5` (Physical Address And Phone)

- Update table: `customer`
- Tables in the SELECT: `customer`, `company`, `address`, `invoice_batch`, `contacts`, `sic`, `ship_to`, `cust_part_no_group_hdr`, `data_identifier_group`, `lead_source`, `freight_charge`, `crm_contact_information`, `customer_freight_display`, `customer_cons_inv_cardlock`, `customer_vat`, `partner_program`, `trackabout_rental_bracket`

| Field | Stored in | Basis |
|---|---|---|
| `phys_address1` | `address.phys_address1` | column |
| `phys_address2` | `address.phys_address2` | probed |
| `phys_city` | `address.phys_city` | column |
| `phys_state` | `address.phys_state` | column |
| `phys_postal_code` | `address.phys_postal_code` | column |
| `phys_country` | `address.phys_country` | column |
| `central_phone_number` | `address.central_phone_number` | column |
| `central_fax_number` | `address.central_fax_number` | column |
| `central_watts_number` | `address.central_watts_number` | column |
| `email_address` | `address.email_address` | column |
| `url` | `address.url` | column |

| # | Label | table.column / expression |
|---|---|---|
| 28 | Physical Address 1: | `address.phys_address1` |
| 29 | Physical Address 2: | `address.phys_address2` |
| 30 | Physical City/State/Zip: | `address.phys_city` |
| 31 | Phys State | `address.phys_state` |
| 32 | Phys Postal Code | `address.phys_postal_code` |
| 33 | Physical Country: | `address.phys_country` |
| 34 | Phone Number: | `address.central_phone_number` |
| 35 | Fax Number: | `address.central_fax_number` |
| 62 | Central Toll Free Number: | `address.central_watts_number` |
| 125 | E-mail Address: | `address.email_address` |
| 126 | URL: | `address.url` |

### `TABPAGE_6.tp_6_dw_6` (OE Options)

- Update table: `customer`
- Tables in the SELECT: `customer`, `company`, `address`, `invoice_batch`, `contacts`, `sic`, `ship_to`, `cust_part_no_group_hdr`, `data_identifier_group`, `lead_source`, `freight_charge`, `crm_contact_information`, `customer_freight_display`, `customer_cons_inv_cardlock`, `customer_vat`, `partner_program`, `trackabout_rental_bracket`

| Field | Stored in | Basis |
|---|---|---|
| `acceptable_wait_time` | `customer.acceptable_wait_time` | column |
| `promise_date_buffer` | `customer.promise_date_buffer` | column |
| `days_until_quote_expires` | `customer.days_until_quote_expires` | column |
| `customer_default_disposition` | `customer.default_disposition` | probed |
| `limit_max_shipments_per_order` | `customer.limit_max_shipments_per_order` | column |
| `minimum_order_dollar_amount` | `customer.minimum_order_dollar_amount` | column |
| `preferred_location_id` | `ship_to.preferred_location_id` | column |
| `manufacturer_rebate_loc` | `customer.manufacturer_rebate_loc` | probed |
| `default_rebate_location_id` | `customer.default_rebate_location_id` | column |
| `manufacturer_distributor_no` | `customer.manufacturer_distributor_no` | column |
| `cust_part_no_group_no` | `cust_part_no_group_hdr.cust_part_no_group_no` | column |
| `manufacturer_program_type_pct` | `customer.manufacturer_program_type_pct` | column |
| `order_priority_uid` | `customer.order_priority_uid` | column |
| `customer_override_revenue_by_item` | `customer.override_revenue_by_item` | probed |
| `customer_order_acknowledgments` | `customer.order_acknowledgments` | probed |
| `po_no_required` | `customer.po_no_required` | column |
| `job_number_required_flag` | `customer.job_number_required_flag` | column |
| `override_profit_limit` | `customer.override_profit_limit` | column |
| `minimum_order_line_profit` | `customer.minimum_order_line_profit` | column |
| `maximum_order_line_profit` | `customer.maximum_order_line_profit` | column |
| `minimum_order_profit` | `customer.minimum_order_profit` | column |
| `maximum_order_profit` | `customer.maximum_order_profit` | column |
| `customer_pick_ticket_type` | `customer.pick_ticket_type` | probed |
| `include_non_alloc_on_pick_tix` | `customer.include_non_alloc_on_pick_tix` | column |
| `exclude_canceld_from_pick_tix` | `customer.exclude_canceld_from_pick_tix` | column |
| `print_packinglist_in_shipping` | `customer.print_packinglist_in_shipping` | column |
| `print_prices_on_packinglist` | `customer.print_prices_on_packinglist` | probed |
| `print_lot_attrib_on_packlist` | `customer.print_lot_attrib_on_packlist` | column |
| `include_non_alloc_on_pack_list` | `customer.include_non_alloc_on_pack_list` | column |
| `exclude_canceld_from_pack_list` | `customer.exclude_canceld_from_pack_list` | column |
| `freight_charge_id` | `freight_charge.freight_charge_id` | column |
| `special_labeling_flag` | `customer.special_labeling_flag` | column |
| `special_packaging_flag` | `customer.special_packaging_flag` | column |
| `so_po_no_required_flag` | `customer.so_po_no_required_flag` | column |
| `partner_program_uid` | `partner_program.partner_program_uid` | column |
| `partner_program_desc` | `partner_program.partner_program_desc` | column |
| `drum_deposit_flag` | `customer.drum_deposit_flag` | column |
| `prnt_crtn_lbl_after_finalize` | `customer.prnt_carton_label_after_final_pkg_flag` | probed |
| `prnt_ship_lbl_after_finalize` | `customer.prnt_shipping_lbl_after_final_pkg_flag` | probed |
| `override_fc_receipt_defaults` | `customer.override_fc_receipt_defaults` | column |
| `fc_receipt_default_print` | `customer.fc_receipt_default_print` | column |
| `fc_receipt_default_email` | `customer.fc_receipt_default_email` | column |
| `fc_receipt_default_unpriced` | `customer.fc_receipt_default_unpriced` | column |
| `fc_receipt_default_skinny` | `customer.fc_receipt_default_skinny` | column |
| `default_rebate_location_name` | computed: `' '` | alias |
| `location_name` | computed: `' '` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 46 | Acceptable Wait Time (Days): | `customer.acceptable_wait_time` |
| 57 | Location Name | `compute_0057` |
| 66 | Customer Order Acknowledgments | `customer.order_acknowledgments` |
| 70 | Maximum Shipments Per Order: | `customer.limit_max_shipments_per_order` |
| 74 | Minimum Order Dollar Amount: | `customer.minimum_order_dollar_amount` |
| 82 | Default Disposition: | `customer.default_disposition` |
| 96 | Default Source Location ID: | `ship_to.preferred_location_id` |
| 108 | Customer Override Revenue By Item | `customer.override_revenue_by_item` |
| 109 | Customer Pick Ticket Type | `customer.pick_ticket_type` |
| 124 | Po No Required | `customer.po_no_required` |
| 139 | Print Prices On Packinglist | `customer.print_prices_on_packinglist` |
| 144 | Default Rebate Location ID: | `customer.default_rebate_location_id` |
| 145 | Default Rebate Location Name | `default_rebate_location_name` |
| 147 | Override Profit Limit | `customer.override_profit_limit` |
| 148 | Minimum Order Line Percent: | `customer.minimum_order_line_profit` |
| 149 | Maximum Order Line Percent: | `customer.maximum_order_line_profit` |
| 150 | Minimum Order Percent: | `customer.minimum_order_profit` |
| 151 | Maximum Order Percent: | `customer.maximum_order_profit` |
| 152 | Include non-allocated items on: | `customer.include_non_alloc_on_pick_tix` |
| 153 | Exclude Canceld From Pick Tix | `customer.exclude_canceld_from_pick_tix` |
| 157 | Include non-allocated items on: | `customer.include_non_alloc_on_pack_list` |
| 158 | Exclude Canceld From Pack List | `customer.exclude_canceld_from_pack_list` |
| 159 | Print Packinglist In Shipping | `customer.print_packinglist_in_shipping` |
| 172 | Print Lot Attrib On Packlist | `customer.print_lot_attrib_on_packlist` |
| 187 | Job Number Required Flag | `customer.job_number_required_flag` |
| 192 | Promise Date Buffer (Days): | `customer.promise_date_buffer` |
| 193 | Number of days before quotes expire (Days): | `customer.days_until_quote_expires` |
| 194 | Order Priority ID: | `customer.order_priority_uid` |
| 200 | Freight/Handling Charge: | `freight_charge.freight_charge_id` |
| 206 | Special Labeling Flag | `customer.special_labeling_flag` |
| 207 | Special Packaging Flag | `customer.special_packaging_flag` |
| 216 | So Po No Required Flag | `customer.so_po_no_required_flag` |
| 239 | Drum Deposit Flag | `customer.drum_deposit_flag` |
| 241 | Prnt Crtn Lbl After Finalize | `customer.prnt_carton_label_after_final_pkg_flag` |
| 242 | Prnt Ship Lbl After Finalize | `customer.prnt_shipping_lbl_after_final_pkg_flag` |
| 248 | Override Fc Receipt Defaults | `customer.override_fc_receipt_defaults` |
| 249 | Fc Receipt Default Print | `customer.fc_receipt_default_print` |
| 250 | Fc Receipt Default Email | `customer.fc_receipt_default_email` |
| 251 | Fc Receipt Default Unpriced | `customer.fc_receipt_default_unpriced` |
| 252 | Fc Receipt Default Skinny | `customer.fc_receipt_default_skinny` |

### `TABPAGE_7.tp_7_dw_7` (Sales Pricing)

- Update table: `customer`
- Tables in the SELECT: `customer`, `company`, `address`, `invoice_batch`, `contacts`, `sic`, `ship_to`, `cust_part_no_group_hdr`, `data_identifier_group`, `lead_source`, `freight_charge`, `crm_contact_information`, `customer_freight_display`, `customer_cons_inv_cardlock`, `customer_vat`, `partner_program`, `trackabout_rental_bracket`

| Field | Stored in | Basis |
|---|---|---|
| `pricing_method_cd` | `customer.pricing_method_cd` | probed |
| `source_price_cd` | `customer.source_price_cd` | column |
| `multiplier` | `customer.multiplier` | probed |
| `express_pricing_flag` | `customer.express_pricing_flag` | column |
| `lowest_across_libraries_flag` | `customer.lowest_across_libraries_flag` | column |
| `job_pricing` | `customer.job_pricing` | column |
| `always_use_job_price` | `customer.always_use_job_price` | column |
| `allow_non_job_item` | `customer.allow_non_job_item` | column |
| `prompt_for_non_job_item` | `customer.prompt_for_non_job_item` | column |
| `allow_exceed_job_qty` | `customer.allow_exceed_job_qty` | column |
| `allow_item_level_contract_flag` | `customer.allow_item_level_contract_flag` | column |
| `use_last_margin_pricing_flag` | `customer.use_last_margin_pricing_flag` | column |
| `invoice_comp_cost_cd_tier1` | `customer.invoice_comp_cost_cd_tier1` | column |
| `invoice_comp_cost_cd_tier2` | `customer.invoice_comp_cost_cd_tier2` | column |
| `invoice_comp_cost_cd_tier3` | `customer.invoice_comp_cost_cd_tier3` | column |
| `use_vendor_contracts_flag` | `customer.use_vendor_contracts_flag` | alias |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 120 | Pricing Method: | `customer.pricing_method_cd` |
| 121 | Source Price: | `customer.source_price_cd` |
| 122 | Multiplier: | `customer.multiplier` |
| 140 | Job Pricing | `customer.job_pricing` |
| 165 | Always Use Job Price | `customer.always_use_job_price` |
| 166 | Allow Non Job Item | `customer.allow_non_job_item` |
| 167 | Prompt For Non Job Item | `customer.prompt_for_non_job_item` |
| 168 | Allow Exceed Job Qty | `customer.allow_exceed_job_qty` |
| 182 | Allow Item Level Contract Flag | `customer.allow_item_level_contract_flag` |
| 190 | Use Last Margin Pricing Flag | `customer.use_last_margin_pricing_flag` |
| 191 | Invoice Comp Cost Cd Tier1 | `customer.invoice_comp_cost_cd_tier1` |
| 195 | Invoice Comp Cost Cd Tier2 | `customer.invoice_comp_cost_cd_tier2` |
| 196 | Invoice Comp Cost Cd Tier3 | `customer.invoice_comp_cost_cd_tier3` |
| 197 | Use Vendor Contracts Flag | `customer.use_vendor_contracts_flag` |
| 253 | Express Pricing Flag | `customer.express_pricing_flag` |
| 257 | Lowest Across Libraries Flag | `customer.lowest_across_libraries_flag` |

### `TABPAGE_7.tp_7_dw_price_library` (Sales Pricing)

- Update table: `price_library_x_cust_x_cmpy`
- Tables in the SELECT: `price_library_x_cust_x_cmpy`, `price_library`

| Field | Stored in | Basis |
|---|---|---|
| `price_library_id` | `price_library.price_library_id` | column |
| `sequence_number` | `price_library_x_cust_x_cmpy.sequence_number` | column |
| `row_status_flag` | `price_library_x_cust_x_cmpy.row_status_flag` | probed |
| `description` | `price_library.description` | column |

| # | Label | table.column / expression |
|---|---|---|
| 5 | Sequence | `price_library_x_cust_x_cmpy.sequence_number` |
| 6 | Status | `price_library_x_cust_x_cmpy.row_status_flag` |
| 10 | Sales Pricing Library ID | `price_library.price_library_id` |
| 11 | Description | `price_library.description` |

### `TABPAGE_8.tp_8_dw_8` (Billing)

- Update table: `customer`
- Tables in the SELECT: `customer`, `company`, `address`, `invoice_batch`, `contacts`, `sic`, `ship_to`, `cust_part_no_group_hdr`, `data_identifier_group`, `lead_source`, `freight_charge`, `crm_contact_information`, `customer_freight_display`, `customer_cons_inv_cardlock`, `customer_vat`, `partner_program`, `trackabout_rental_bracket`

| Field | Stored in | Basis |
|---|---|---|
| `bill_to_contact_id` | `customer.bill_to_contact_id` | column |
| `invoice_type` | `address.invoice_type` | column |
| `invoice_print_qty` | `customer.invoice_print_qty` | column |
| `invoice_batch_number` | `invoice_batch.invoice_batch_number` | column |
| `lot_bill_summary_on_invoices` | `customer.lot_bill_summary_on_invoices` | probed |
| `print_lot_attrib_on_invoice` | `customer.print_lot_attrib_on_invoice` | column |
| `downpayment_percentage` | `customer.downpayment_percentage` | column |
| `req_pymt_upon_release_of_items` | `customer.req_pymt_upon_release_of_items` | column |
| `include_dp_summary_on_invoices` | `customer.include_dp_summary_on_invoices` | column |
| `days_overdue_for_credit_hold` | `customer.days_overdue_for_credit_hold` | column |
| `xmit_invoice_cd` | `customer.xmit_invoice_cd` | column |
| `order_disc_type` | `customer.order_disc_type` | alias |
| `order_disc_factor` | `customer.order_disc_factor` | alias |
| `advanced_billing_flag` | `customer.advanced_billing_flag` | column |
| `send_einvoice_flag` | `customer.send_einvoice_flag` | column |
| `australian_business_no` | `customer.australian_business_no` | column |
| `invoice_batch_desc` | `invoice_batch.invoice_batch_desc` | column |
| `contact_name` | computed: `' '` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 55 | Invoice Type: | `address.invoice_type` |
| 68 | Bill To Contact ID: | `customer.bill_to_contact_id` |
| 99 | Contact Name | `compute_0099` |
| 117 | Invoice Print Quantity: | `customer.invoice_print_qty` |
| 130 | Lot Bill Summary On Invoices | `customer.lot_bill_summary_on_invoices` |
| 133 | Invoice Batch Number: | `invoice_batch.invoice_batch_number` |
| 134 | Invoice Batch Desc | `invoice_batch.invoice_batch_desc` |
| 171 | Print Lot Attrib On Invoice | `customer.print_lot_attrib_on_invoice` |
| 184 | Downpayment %: | `customer.downpayment_percentage` |
| 185 | Req Pymt Upon Release Of Items | `customer.req_pymt_upon_release_of_items` |
| 186 | Include Dp Summary On Invoices | `customer.include_dp_summary_on_invoices` |
| 212 | Days Overdue for Credit Hold: | `customer.days_overdue_for_credit_hold` |
| 254 | Group Invoice Email/Fax By: | `customer.xmit_invoice_cd` |

### `GENERAL.general` (General)

- Update table: `customer`
- Tables in the SELECT: `customer`, `company`, `address`, `invoice_batch`, `contacts`, `sic`, `ship_to`, `cust_part_no_group_hdr`, `data_identifier_group`, `lead_source`, `freight_charge`, `crm_contact_information`, `customer_freight_display`, `customer_cons_inv_cardlock`, `customer_vat`, `partner_program`, `trackabout_rental_bracket`

| Field | Stored in | Basis |
|---|---|---|
| `generate_customer_statements` | `customer.generate_customer_statements` | column |
| `open_item_balance_forward` | `customer.open_item_balance_forward` | column |
| `generate_statements_by` | `customer.generate_statements_by` | column |
| `statement_batch_number` | `invoice_batch.invoice_batch_number` | alias |
| `sic_code` | `customer.sic_code` | column |
| `use_sys_ups_handling_chrg_flag` | `customer.use_sys_ups_handling_chrg_flag` | column |
| `taxable_flag` | `customer.taxable_flag` | column |
| `ups_handling_charge` | `customer.ups_handling_charge` | column |
| `floor_plan_account` | `customer.floor_plan_account` | column |
| `include_freight_in_price` | `customer_freight_display.include_freight_in_price` | alias |
| `statement_frequency_id` | `customer.statement_frequency_id` | column |
| `statement_batch_desc` | `invoice_batch.invoice_batch_desc` | probed |
| `sic_description` | `sic.sic_description` | column |

| # | Label | table.column / expression |
|---|---|---|
| 4 | Taxable Flag | `customer.taxable_flag` |
| 65 | Statement Type: | `customer.open_item_balance_forward` |
| 72 | Generate Customer Statements | `customer.generate_customer_statements` |
| 73 | Primary SIC Code: | `customer.sic_code` |
| 80 | Sic Description | `sic.sic_description` |
| 81 | Floor Plan Account | `customer.floor_plan_account` |
| 98 | Statement Frequency: | `customer.statement_frequency_id` |
| 135 | Generate Statements by: | `customer.generate_statements_by` |
| 136 | Print Zero Dollar Customers | `customer.print_zero_dollar_customers` |
| 142 | Statement Batch Number: | `statement_batch_number` |
| 143 | Statement Batch Desc | `statement_batch_desc` |
| 209 | Use Sys Ups Handling Chrg Flag | `customer.use_sys_ups_handling_chrg_flag` |
| 210 | UPS/AgileShip Charge: | `customer.ups_handling_charge` |

### `CLASSES.classes` (Classes)

- Update table: `customer`
- Tables in the SELECT: `customer`, `company`, `address`, `invoice_batch`, `contacts`, `sic`, `ship_to`, `cust_part_no_group_hdr`, `data_identifier_group`, `lead_source`, `freight_charge`, `crm_contact_information`, `customer_freight_display`, `customer_cons_inv_cardlock`, `customer_vat`, `partner_program`, `trackabout_rental_bracket`

| Field | Stored in | Basis |
|---|---|---|
| `customer_class_1id` | `customer.class_1id` | probed |
| `customer_class_2id` | `customer.class_2id` | probed |
| `customer_class_3id` | `customer.class_3id` | probed |
| `customer_class_4id` | `customer.class_4id` | probed |
| `customer_class_5id` | `customer.class_5id` | probed |
| `rental_bracket_id` | `trackabout_rental_bracket.rental_bracket_id` | column |

| # | Label | table.column / expression |
|---|---|---|
| 39 | Class 1 ID: | `customer.class_1id` |
| 40 | Class 2 ID: | `customer.class_2id` |
| 41 | Class 3 ID: | `customer.class_3id` |
| 42 | Class 4 ID: | `customer.class_4id` |
| 43 | Class 5 ID: | `customer.class_5id` |

### `TAX.tax` (Tax)

- Update table: `customer`
- Tables in the SELECT: `customer`, `company`, `address`, `invoice_batch`, `contacts`, `sic`, `ship_to`, `cust_part_no_group_hdr`, `data_identifier_group`, `lead_source`, `freight_charge`, `crm_contact_information`, `customer_freight_display`, `customer_cons_inv_cardlock`, `customer_vat`, `partner_program`, `trackabout_rental_bracket`

| Field | Stored in | Basis |
|---|---|---|
| `customer_resale_certificate` | `customer.resale_certificate` | probed |
| `state_excise_tax_exemption_no` | `customer.state_excise_tax_exemption_no` | column |
| `federal_exemption_number` | `customer.federal_exemption_number` | column |
| `other_exemption_number` | `customer.other_exemption_number` | column |
| `sales_tax_payable_account_no` | `customer.sales_tax_payable_account_no` | column |
| `customer_tax_class` | `customer.customer_tax_class` | column |

| # | Label | table.column / expression |
|---|---|---|
| 5 | State Sales Tax Exemption Number: | `customer.resale_certificate` |
| 78 | Federal Excise Tax Exemption Number: | `customer.federal_exemption_number` |
| 79 | Other Exemption Number: | `customer.other_exemption_number` |
| 103 | State Excise Tax Exemption Number: | `customer.state_excise_tax_exemption_no` |

### `LINKS.links` (Contacts)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `contact_id` | ? | no_sql |
| `contact_type_cd` | ? | no_sql |
| `contact_link_id` | ? | no_sql |
| `email_address` | ? | no_sql |
| `statement_contact` | ? | no_sql |
| `row_status_flag` | ? | no_sql |
| `pedigree_contact` | ? | no_sql |
| `contact_link_name` | ? | no_sql |
| `title` | ? | no_sql |
| `direct_phone` | ? | no_sql |
| `phone_ext` | ? | no_sql |
| `direct_fax` | ? | no_sql |
| `fax_ext` | ? | no_sql |
| `last_hard_touch_date` | ? | no_sql |
| `contacts_delete_flag` | ? | no_sql |
| `cf_spaces` | ? | no_sql |
| `cf_contact_name` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Contact ID | `contacts.id` |
| 2 | Contact Type | `contact_type_cd` |
| 5 | Link Name | `contact_link_name` |
| 6 | Status | `row_status_flag` |
| 8 | Contact Link | `contact_link_id` |
| 23 | StatementContact | `statement_contact` |
| 24 | ContactStatus | `contacts.delete_flag` |
| 25 | Title | `contacts.title` |
| 26 | Direct Phone | `contacts.direct_phone` |
| 27 | Direct Fax | `contacts.direct_fax` |
| 28 | Email Address | `contacts.email_address` |
| 29 | Ext | `contacts.phone_ext` |
| 30 | Ext | `contacts.fax_ext` |
| 32 | Last Touch | `crm_contact_information.last_hard_touch_date` |
| calc | Contact Name | `contacts_last_name + ', ' + contacts_first_name   + if( Isnull(contacts_mi ) OR contacts_mi  = '' , '', ', ' +  contacts_mi + '.' )` |

### `TERRITORY.territory` (Territory)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `territory_id` | ? | no_sql |
| `territory_type_cd` | ? | no_sql |
| `link_id` | ? | no_sql |
| `row_status_flag` | ? | no_sql |
| `territory_desc` | ? | no_sql |
| `link_name` | ? | no_sql |
| `compute_1` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Territory ID | `territory_id` |
| 3 | Type | `territory_type_cd` |
| 6 | ID | `link_id` |
| 7 | Name | `link_name` |
| 11 | Status | `row_status_flag` |
| 15 | Description | `territory_desc` |

### `SHIP_TO_GENERAL.ship_to_general` (Ship To Info (General))

- Update table: `ship_to`
- Tables in the SELECT: `ship_to`, `branch`, `customer`, `freight_code`, `shipping_route`, `document_link_entity_req`

| Field | Stored in | Basis |
|---|---|---|
| `default_branch` | `ship_to.default_branch` | column |
| `state_exemption_number` | `ship_to.state_exemption_number` | column |
| `state_excise_tax_exemption_no` | `ship_to.state_excise_tax_exemption_no` | column |
| `federal_exemption_number` | `ship_to.federal_exemption_number` | column |
| `other_exemption_number` | `ship_to.other_exemption_number` | column |
| `freight_cd` | `freight_code.freight_cd` | column |
| `packing_basis` | `ship_to.packing_basis` | column |
| `fob` | `ship_to.fob` | column |
| `over_tolerance_percentage` | `customer.over_tolerance_percentage` | column |
| `under_tolerance_percentage` | `customer.under_tolerance_percentage` | column |
| `require_lot_documentation_flag` | `document_link_entity_req.require_lot_documentation_flag` | alias |
| `print_flag` | `document_link_entity_req.print_flag` | alias |
| `send_outside_use_docs_flag` | `document_link_entity_req.send_outside_use_docs_flag` | alias |
| `fax_flag` | `document_link_entity_req.fax_flag` | probed |
| `send_outside_use_print_flag` | `document_link_entity_req.send_outside_use_print_flag` | alias |
| `email_flag` | `document_link_entity_req.email_flag` | alias |
| `send_outside_use_fax_flag` | `document_link_entity_req.send_outside_use_fax_flag` | alias |
| `number_of_copies` | `document_link_entity_req.number_of_copies` | alias |
| `outside_use_number_of_copies` | `document_link_entity_req.outside_use_number_of_copies` | column |
| `send_outside_use_email_flag` | `document_link_entity_req.send_outside_use_email_flag` | alias |
| `order_priority_uid` | `ship_to.order_priority_uid` | column |
| `scan_and_pack_flag` | `ship_to.scan_and_pack_flag` | column |
| `branch_description` | `branch.branch_description` | column |
| `freight_desc` | `freight_code.freight_desc` | column |

| # | Label | table.column / expression |
|---|---|---|
| 4 | Default Branch: | `ship_to.default_branch` |
| 5 | Federal Excise Tax Exemption Number: | `ship_to.federal_exemption_number` |
| 6 | State Sales Tax Exemption Number: | `ship_to.state_exemption_number` |
| 7 | Other Exemption Number: | `ship_to.other_exemption_number` |
| 12 | FOB: | `ship_to.fob` |
| 26 | Packing Basis: | `ship_to.packing_basis` |
| 31 | Branch Description | `branch.branch_description` |
| 35 | State Excise Tax Exemption Number: | `ship_to.state_excise_tax_exemption_no` |
| 44 | Default Freight Code: | `freight_code.freight_cd` |
| 45 | Freight Desc | `freight_code.freight_desc` |
| 52 | Tolerance Percentage - Over %: | `customer.over_tolerance_percentage` |
| 53 | Tolerance Percentage - Under %: | `customer.under_tolerance_percentage` |
| 54 | Require Lot Documentation: | `document_link_entity_req.require_lot_documentation_flag` |
| 55 | Print Flag | `document_link_entity_req.print_flag` |
| 56 | Fax Flag | `document_link_entity_req.fax_flag` |
| 57 | Email Flag | `document_link_entity_req.email_flag` |
| 58 | Number of Copies: | `document_link_entity_req.number_of_copies` |
| 62 | Send Outside Use Documents: | `document_link_entity_req.send_outside_use_docs_flag` |
| 63 | Send Outside Use Print Flag | `document_link_entity_req.send_outside_use_print_flag` |
| 64 | Send Outside Use Fax Flag | `document_link_entity_req.send_outside_use_fax_flag` |
| 65 | Send Outside Use Email Flag | `document_link_entity_req.send_outside_use_email_flag` |
| 66 | Number of Copies: | `document_link_entity_req.outside_use_number_of_copies` |
| 68 | Order Priority ID: | `ship_to.order_priority_uid` |
| 72 | Scan And Pack Flag | `ship_to.scan_and_pack_flag` |

### `SHIP_TO_DELIVERY.ship_to_delivery` (Ship To Info (Delivery))

- Update table: `ship_to`
- Tables in the SELECT: `ship_to`, `branch`, `customer`, `freight_code`, `shipping_route`, `document_link_entity_req`

| Field | Stored in | Basis |
|---|---|---|
| `delivery_instructions` | `ship_to.delivery_instructions` | column |
| `default_carrier_id` | `ship_to.default_carrier_id` | column |
| `route` | `shipping_route.route_code` | probed |
| `acceptable_wait_time` | `ship_to.acceptable_wait_time` | column |

| # | Label | table.column / expression |
|---|---|---|
| 11 | Default Carrier: | `ship_to.default_carrier_id` |
| 13 | Delivery Instructions: | `ship_to.delivery_instructions` |
| 18 | Route: | `shipping_route.route_code` |
| 20 | Acceptable Wait Time (Days): | `ship_to.acceptable_wait_time` |

### `SHIP_TO_LABELS.ship_to_labels` (Ship To Labels)

- Update table: `label_definition_x_customer`
- Tables in the SELECT: `label_definition_x_customer`, `label_definition`, `code_p21`

| Field | Stored in | Basis |
|---|---|---|
| `label_definition_id` | computed: `label_definition_id` | probed |
| `code_description` | `code_p21.code_description` | probed |
| `label_definition_desc` | computed: `label_definition_desc` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 6 | Label Definition ID | `label_definition_x_customer.label_definition_id` |
| 7 | Label Definition Description | `label_definition_x_customer.label_definition_desc` |
| 8 | Label Type | `code_p21.code_description` |

### `SHIP_TO_LABELS.ship_to_labels_dw_0` (Ship To Labels)

- Update table: `customer`
- Tables in the SELECT: `customer`, `company`, `address`, `invoice_batch`, `contacts`, `sic`, `ship_to`, `cust_part_no_group_hdr`, `data_identifier_group`, `lead_source`, `freight_charge`, `crm_contact_information`, `customer_freight_display`, `customer_cons_inv_cardlock`, `customer_vat`, `partner_program`, `trackabout_rental_bracket`

| Field | Stored in | Basis |
|---|---|---|
| `data_identifier_group_id` | `data_identifier_group.data_identifier_group_id` | column |
| `data_identifier_group_desc` | `data_identifier_group.data_identifier_group_desc` | column |

| # | Label | table.column / expression |
|---|---|---|
| 176 | Data Identifier Group ID: | `data_identifier_group.data_identifier_group_id` |
| 177 | Data Identifier Group Desc | `data_identifier_group.data_identifier_group_desc` |

### `SHIP_TOS.ship_tos` (Ship Tos)

- Update table: `ship_to`
- Tables in the SELECT: `ship_to`, `customer`, `address`, `crm_contact_information`

| Field | Stored in | Basis |
|---|---|---|
| `ship_to_id` | `ship_to.ship_to_id` | column |
| `name` | `address.name` | probed |
| `last_hard_touch_date` | `crm_contact_information.last_hard_touch_date` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Ship To ID | `ship_to.ship_to_id` |
| 2 | Name | `address.name` |
| 3 | Invoice Type | `ship_to.invoice_type` |
| 4 | Customer Pick Ticket Type | `ship_to.pick_ticket_type` |
| 5 | Company Id | `ship_to.company_id` |
| 6 | Delete Flag (Ship to) | `ship_to.delete_flag` |
| 13 | L. Touch | `crm_contact_information.last_hard_touch_date` |

### `EDI.edi` (Electronic Data Interchange)

- Update table: `customer_edi_setting`
- Tables in the SELECT: `customer`, `customer_edi_setting`

| Field | Stored in | Basis |
|---|---|---|
| `interchg_receiver_id` | `customer.interchg_receiver_id` | column |
| `intl_san` | `customer.intl_san` | column |
| `trading_partner_name` | `customer.trading_partner_name` | column |
| `passport_customer_id` | `customer.passport_customer_id` | column |
| `edi_interchange_id_qualifier` | `customer_edi_setting.edi_interchange_id_qualifier` | column |
| `edi_interchange_id` | `customer_edi_setting.edi_interchange_id` | probed |
| `application_code` | `customer_edi_setting.application_code` | column |
| `element_separator` | `customer_edi_setting.element_separator` | probed |
| `send_ucc128info` | `customer.send_ucc128info` | column |
| `mfr_no` | `customer.mfr_no` | column |
| `ucc128_form_filename` | `customer.ucc128_form_filename` | column |
| `append_line_feed_flag` | `customer_edi_setting.append_line_feed_flag` | column |
| `functional_ack_flag` | `customer_edi_setting.functional_ack_flag` | column |
| `sub_element_separator` | `customer_edi_setting.sub_element_separator` | column |
| `testing_mode_flag` | `customer_edi_setting.testing_mode_flag` | column |
| `segment_terminator` | `customer_edi_setting.segment_terminator` | column |
| `eighty_column_line_break_flag` | `customer_edi_setting.eighty_column_line_break_flag` | column |
| `repetition_separator` | `customer_edi_setting.repetition_separator` | column |
| `validate_x12_document_flag` | `customer_edi_setting.validate_x12_document_flag` | column |
| `prnt_ucc128_lbl_after_finalize` | `customer.prnt_ucc128_label_after_final_pkg_flag` | probed |
| `use_scan_pack_flag` | `customer.use_scan_pack_flag` | column |

| # | Label | table.column / expression |
|---|---|---|
| 4 | Interchg Receiver ID (SAN): | `customer.interchg_receiver_id` |
| 5 | Int'l SAN: | `customer.intl_san` |
| 6 | Trading Partner Name: | `customer.trading_partner_name` |
| 7 | Passport Customer ID: | `customer.passport_customer_id` |
| 8 | EDI Interchange ID Qualifier: | `customer_edi_setting.edi_interchange_id_qualifier` |
| 9 | EDI Interchange ID: | `customer_edi_setting.edi_interchange_id` |
| 10 | Application Code: | `customer_edi_setting.application_code` |
| 11 | Element Separator: | `customer_edi_setting.element_separator` |
| 12 | Sub Element Separator: | `customer_edi_setting.sub_element_separator` |
| 13 | Segment Terminator: | `customer_edi_setting.segment_terminator` |
| 14 | Repetition Separator: | `customer_edi_setting.repetition_separator` |
| 15 | Append Line Feed Flag | `customer_edi_setting.append_line_feed_flag` |
| 16 | Functional Ack Flag | `customer_edi_setting.functional_ack_flag` |
| 17 | Testing Mode Flag | `customer_edi_setting.testing_mode_flag` |
| 18 | Eighty Column Line Break Flag | `customer_edi_setting.eighty_column_line_break_flag` |
| 19 | Validate X12 Document Flag | `customer_edi_setting.validate_x12_document_flag` |
| 26 | Send Ucc128info | `customer.send_ucc128info` |
| 27 | Manufacturer ID Number: | `customer.mfr_no` |
| 28 | GS1-128 Label Form Filename: | `customer.ucc128_form_filename` |
| 29 | Prnt Ucc128 Lbl After Finalize | `customer.prnt_ucc128_label_after_final_pkg_flag` |

### `EDI.editransactions` (Electronic Data Interchange)

- Update table: `customer_edi_transaction`
- Tables in the SELECT: `customer_edi_transaction`, `code_p21`

| Field | Stored in | Basis |
|---|---|---|
| `row_status_flag` | `customer_edi_transaction.row_status_flag` | column |
| `code_description` | `code_p21.code_description` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 5 | Status | `customer_edi_transaction.row_status_flag` |
| 9 | eBusiness Transaction Set | `code_p21.code_description` |

### `EDI.editransdetail` (Electronic Data Interchange)

- Update table: `none (external source)`

| Field | Stored in | Basis |
|---|---|---|
| `transaction_map_name` | ? | no_sql |
| `override_trading_partner_flag` | ? | no_sql |
| `edi_interchange_id_qualifier` | ? | no_sql |
| `edi_interchange_id` | ? | no_sql |
| `application_code` | ? | no_sql |
| `override_your_edi_id_flag` | ? | no_sql |
| `your_edi_interchange_id_qual` | ? | no_sql |
| `your_edi_interchange_id` | ? | no_sql |
| `your_application_code` | ? | no_sql |
| `transaction_map_name_t` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Transaction Map Name | `transaction_map_name` |
| 2 | Override Trading Partner Flag | `override_trading_partner_flag` |
| 3 | EDI Interchange ID Qualifier: | `edi_interchange_id_qualifier` |
| 4 | EDI Interchange ID: | `edi_interchange_id` |
| 5 | Application Code: | `application_code` |
| 10 | Override Your Edi Id Flag | `override_your_edi_id_flag` |
| 11 | EDI Interchange ID Qualifier: | `your_edi_interchange_id_qual` |
| 12 | EDI Interchange ID: | `your_edi_interchange_id` |
| 13 | Application Code: | `your_application_code` |
| calc | Transaction Map Name T | `IF ( IsNull(edi_transaction), 'Transaction', LookUpDisplay(edi_transaction ) ) + ' Map Name:'` |

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
| `date_last_modified` | `document_link.date_last_modified` | column |
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
| 14 | Date Last Modified | `document_link.date_last_modified` |
| 24 | Outside Use | `document_link.outside_use_flag` |
| 25 | Mandatory | `document_link.mandatory_flag` |
| calc | Document Linked to | `IF ( key2_cd = 'lot_cd', if(isnull(key2_value),'',key2_value), IF ( key1_cd = 'inv_mast_uid', if(isnull(item_id),'',item_id), if(isnull(key1_value),'',key1_value) ) + IF ( IsNull(key2_value), '', '/' + key2_value + IF ( IsNull(key3_value), '', '/' + key3_value)) )` |

### `TP_CUSTOMERSTRATGICPRICING.customer_strategic_pricing` (Customer Strategic Pricing)

- Update table: `customer_strategic_pricing`
- Tables in the SELECT: `customer_strategic_pricing`, `customer_category`, `customer`

| Field | Stored in | Basis |
|---|---|---|
| `warehouse_size_cd` | `customer_strategic_pricing.warehouse_size_cd` | column |
| `retail_size_cd` | `customer_strategic_pricing.retail_size_cd` | column |
| `customer_category_id` | `customer_category.customer_category_id` | column |
| `list_price_option_cd` | `customer_strategic_pricing.list_price_option_cd` | probed |
| `freight_charge_option_cd` | `customer_strategic_pricing.freight_charge_option_cd` | column |
| `pricing_customer_id` | `customer_strategic_pricing.pricing_customer_id` | column |
| `customer_sensitivity_cd` | `customer_strategic_pricing.customer_sensitivity_cd` | column |
| `pricing_customer_name` | `customer.customer_name` | probed |
| `customer_category_desc` | `customer_category.customer_category_desc` | column |
| `warehouse_size_update_date` | `customer_strategic_pricing.warehouse_size_update_date` | column |
| `retail_size_update_date` | `customer_strategic_pricing.retail_size_update_date` | column |
| `cust_sensitivity_update_date` | `customer_strategic_pricing.cust_sensitivity_update_date` | column |

| # | Label | table.column / expression |
|---|---|---|
| 4 | Warehouse Customer Size: | `customer_strategic_pricing.warehouse_size_cd` |
| 5 | Update Date: | `customer_strategic_pricing.warehouse_size_update_date` |
| 6 | Retail Customer Size: | `customer_strategic_pricing.retail_size_cd` |
| 7 | Update Date: | `customer_strategic_pricing.retail_size_update_date` |
| 9 | Customer Category ID: | `customer_strategic_pricing.customer_category_id` |
| 10 | Customer Category Desc | `customer_strategic_pricing.customer_category_desc` |
| 11 | List Price/Cost Option: | `customer_strategic_pricing.list_price_option_cd` |
| 12 | Freight Charge Option: | `customer_strategic_pricing.freight_charge_option_cd` |
| 13 | Pricing Customer ID: | `customer_strategic_pricing.pricing_customer_id` |
| 14 | Pricing Customer Name | `pricing_customer.customer_name` |

### `CUSTOMERSALESREP.customersalesrep` (Salesrep)

- Update table: `customer_salesrep`
- Tables in the SELECT: `customer_salesrep`, `contacts`

| Field | Stored in | Basis |
|---|---|---|
| `salesrep_id` | `customer_salesrep.salesrep_id` | column |
| `salesrep_name` | computed: `(contacts.last_name + ', ' + contacts.first_name + ' ' + COALESCE(contacts.mi, ''))` | alias |
| `commission_percentage` | `customer_salesrep.commission_percentage` | probed |
| `primary_salesrep_flag` | `customer_salesrep.primary_salesrep_flag` | column |
| `row_status_flag` | `customer_salesrep.row_status_flag` | column |
| `compute_1` | computed: `(computed in the datawindow)` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 3 | Salesrep ID | `customer_salesrep.salesrep_id` |
| 4 | Percentage | `customer_salesrep.commission_percentage` |
| 5 | Status | `customer_salesrep.row_status_flag` |
| 11 | Salesrep Name | `salesrep_name` |
| 12 | Primary Salesrep | `customer_salesrep.primary_salesrep_flag` |

### `TP_PAYMENTACCOUNT.tp_paymentaccount` (Payment Account)

- Update table: `payment_account_x_customer`
- Tables in the SELECT: `payment_account_x_customer`, `payment_account`, `code_p21`, `customer`, `company`, `payment_types`

| Field | Stored in | Basis |
|---|---|---|
| `payment_acct_desc` | `payment_account.payment_acct_desc` | column |
| `payment_acct_type_cd` | `payment_account.payment_acct_type_cd` | column |
| `payment_type_id` | `payment_account_x_customer.payment_type_id` | column |
| `payment_acct_id` | `payment_account.payment_acct_id` | column |
| `acct_no_desc` | computed: `'xxxxxxxxxxxx' + right(payment_account.acct_no, 4)` | probed |
| `acct_expiration_date` | `payment_account.acct_expiration_date` | column |
| `extended_acct_info` | `payment_account.extended_acct_info` | column |
| `default_for_customer_flag` | `payment_account_x_customer.default_for_customer_flag` | column |
| `row_status_flag` | `payment_account_x_customer.row_status_flag` | column |
| `automatic_payment_flag` | `payment_account_x_customer.automatic_payment_flag` | column |
| `automatic_payment_limit` | `payment_account_x_customer.automatic_payment_limit` | probed |
| `customer_id` | `payment_account_x_customer.customer_id` | column |
| `company_id` | `payment_account_x_customer.company_id` | column |
| `customer_name` | `customer.customer_name` | column |
| `company_name` | `company.company_name` | column |

| # | Label | table.column / expression |
|---|---|---|
| 3 | Customer ID: | `payment_account_x_customer.customer_id` |
| 4 | Customer Name | `customer.customer_name` |
| 5 | Company ID: | `payment_account_x_customer.company_id` |
| 6 | Company Name | `company.company_name` |
| 7 | Payment Type: | `payment_account_x_customer.payment_type_id` |
| 11 | Row Status Flag | `payment_account_x_customer.row_status_flag` |
| 16 | Payment Account ID: | `payment_account.payment_acct_id` |
| 17 | Description: | `payment_account.payment_acct_desc` |
| 18 | System Defined Payment Type: | `payment_account.payment_acct_type_cd` |
| 21 | Extended Acct Info: | `payment_account.extended_acct_info` |
| 22 | Expiration: | `payment_account.acct_expiration_date` |
| 28 | Account Number: | `acct_no_display` |

### `TP_DEALERTYPE.tp_dealertype` (Dealer Type)

- Update table: `customer_x_dealer_type`
- Tables in the SELECT: `customer_x_dealer_type`, `dealer_type`, `company`, `address`

| Field | Stored in | Basis |
|---|---|---|
| `dealer_type_id` | `dealer_type.dealer_type_id` | column |
| `row_status_flag` | `customer_x_dealer_type.row_status_flag` | probed |
| `dealer_type_description` | `dealer_type.dealer_type_description` | column |
| `cf_rfi` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 5 | Status | `customer_x_dealer_type.row_status_flag` |
| 10 | Dealer Type ID | `dealer_type.dealer_type_id` |
| 11 | Description | `dealer_type.dealer_type_description` |

### `CUSTOMERFORMTAB.customerformtab` (Forms)

- Update table: `customer_form_template`
- Tables in the SELECT: `customer_form_template`

| Field | Stored in | Basis |
|---|---|---|
| `order_ack_filename` | `customer_form_template.order_ack_filename` | column |
| `rma_filename` | `customer_form_template.rma_filename` | column |
| `packing_list_filename` | `customer_form_template.packing_list_filename` | column |
| `packing_list_priced_filename` | `customer_form_template.packing_list_priced_filename` | column |
| `invoice_filename` | `customer_form_template.invoice_filename` | column |
| `cons_inv_summary_filename` | `customer_form_template.cons_inv_summary_filename` | column |
| `cons_inv_detail_filename` | `customer_form_template.cons_inv_detail_filename` | column |
| `statement_filename` | `customer_form_template.statement_filename` | column |
| `service_order_filename` | `customer_form_template.service_order_filename` | column |
| `service_order_rcpt_filename` | `customer_form_template.service_order_rcpt_filename` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 4 | Quote/Order Acknowledgement | `customer_form_template.order_ack_filename` |
| 5 | RMA Acknowledgement | `customer_form_template.rma_filename` |
| 6 | Packing List - Unpriced | `customer_form_template.packing_list_filename` |
| 7 | Invoice | `customer_form_template.invoice_filename` |
| 8 | Statement | `customer_form_template.statement_filename` |
| 13 | Consolidated Summary Invoice | `customer_form_template.cons_inv_summary_filename` |
| 14 | Consolidated Detail Invoice | `customer_form_template.cons_inv_detail_filename` |
| 15 | Packing List - Priced | `customer_form_template.packing_list_priced_filename` |
| 16 | Service Order | `customer_form_template.service_order_filename` |
| 17 | Service Order Receipt | `customer_form_template.service_order_rcpt_filename` |

### `TP_CUSTOMERMERGEAUDIT.customer_merge_audit` (Merge Tracking)

- Update table: `customer_merge_audit`
- Tables in the SELECT: `customer_merge_audit`, `customer`

| Field | Stored in | Basis |
|---|---|---|
| `customer_merge_run` | `customer_merge_audit.customer_merge_run` | column |
| `company_id` | `customer_merge_audit.company_id` | column |
| `source_customer_id` | `customer_merge_audit.source_customer_id` | probed |
| `source_customer_name` | `customer.customer_name` | alias |
| `target_customer_id` | `customer_merge_audit.target_customer_id` | column |
| `target_customer_name` | `customer.customer_name` | alias |
| `processed_flag` | `customer_merge_audit.processed_flag` | column |
| `date_created` | `customer_merge_audit.date_created` | column |
| `merged_by` | `customer_merge_audit.created_by` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 2 | Merge Run | `customer_merge_audit.customer_merge_run` |
| 3 | Company ID | `customer_merge_audit.company_id` |
| 4 | Source Customer ID | `customer_merge_audit.source_customer_id` |
| 5 | Target Customer ID | `customer_merge_audit.target_customer_id` |
| 6 | Process Result | `customer_merge_audit.processed_flag` |
| 7 | Merged Date | `customer_merge_audit.date_created` |
| 9 | Source Customer Name | `customer.customer_name` |
| 10 | Target Customer Name | `customer.customer_name` |
| 11 | Merged By | `customer_merge_audit.created_by` |

### `TP_EMAILDEFAULTS.customer_email_defaults` (Email Defaults)

- Update table: `customer_email_defaults`
- Tables in the SELECT: `customer_email_defaults`, `code_p21`

| Field | Stored in | Basis |
|---|---|---|
| `email_subject` | `customer_email_defaults.subject` | probed |
| `copy` | `customer_email_defaults.copy` | column |
| `blind_copy` | `customer_email_defaults.blind_copy` | column |
| `memo` | `customer_email_defaults.memo` | column |
| `cc_user` | `customer_email_defaults.cc_user` | column |
| `cc_salesrep` | `customer_email_defaults.cc_salesrep` | column |
| `cc_taker` | `customer_email_defaults.cc_taker` | column |
| `bc_user` | `customer_email_defaults.bc_user` | column |
| `bc_salesrep` | `customer_email_defaults.bc_salesrep` | column |
| `bc_taker` | `customer_email_defaults.bc_taker` | column |
| `form_type_cd_desc` | `code_p21.code_description` | alias |

| # | Label | table.column / expression |
|---|---|---|
| 5 | Email Subject | `customer_email_defaults.subject` |
| 6 | Cc | `customer_email_defaults.copy` |
| 7 | Bcc | `customer_email_defaults.blind_copy` |
| 8 | Memo | `customer_email_defaults.memo` |
| 9 | Cc User | `customer_email_defaults.cc_user` |
| 10 | Cc Salesrep | `customer_email_defaults.cc_salesrep` |
| 11 | Cc Taker | `customer_email_defaults.cc_taker` |
| 12 | Bcc User | `customer_email_defaults.bc_user` |
| 13 | Bcc Salesrep | `customer_email_defaults.bc_salesrep` |
| 14 | Bcc Taker | `customer_email_defaults.bc_taker` |
| 19 | Form Type | `form_type_cd_desc` |

### `TIMESTAMP.audit_trail` (Audit Trail)

- Update table: `p21_view_audit_trail_customer_<id>`
- Tables in the SELECT: `p21_view_audit_trail_customer_<id>`

| Field | Stored in | Basis |
|---|---|---|
| `column_description` | `p21_view_audit_trail_customer_<id>.column_description` | probed |
| `old_value` | `p21_view_audit_trail_customer_<id>.old_value` | probed |
| `new_value` | `p21_view_audit_trail_customer_<id>.new_value` | probed |
| `date_created` | `p21_view_audit_trail_customer_<id>.date_created` | probed |
| `created_by` | `p21_view_audit_trail_customer_<id>.created_by` | probed |
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
| calc | Company ID / Customer ID | `"IF ((source_area_cd = 1763 and key1_cd = 'service_labor_uid'), item_id,  IF (source_area_cd = 950, key1_value,  IF (key2_cd = 'item_service_uid',  Item_id + ' / ALL / ALL',  IF ( key2_cd = 'lot_cd', key2_value,   IF ( Len(auxiliary_value) > 0 AND source_area_cd IN (1544, 1250, 2531), auxiliary_value,  IF (source_area_cd = 1314 and table_changed = 'inv_mast_strategic_pricing', item_id + '/' + key3_value + IF (IsNull(key2_value), '', '/' + auxiliary_value),  IF ( key1_cd = 'inv_mast_uid', item_id, key1_value ) + IF ( IsNull ( key2_value) AND source_area_cd <> 1314, '', ' / ' + IF ( key2_cd = 'inv_mast_uid', item_id, IF ( IsNull ( key2_value ), 'ALL', key2_value ) )  + IF ( IsNull (key3_value) AND source_area_cd <> 1314, '', ' / ' + IF ( key3_cd = 'inv_mast_uid', item_id, IF ( IsNull ( key3_value ), 'ALL', key3_value ) ) ) )  ) ) ) ) ) )"` |
| calc | 'Sub Line No | `` |

### `TIMESTAMP.timestamp` (Audit Trail)

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
| `TABPAGE_3` | Finance Charges | `tp_3_dw_3` | datawindow never instantiated (tab not enabled) |
| `CUSTOMER_NOTES` | Customer Notes | `customer_notes` | datawindow never instantiated (tab not enabled) |
| `TP_CONTRACTCLASS` | Contract Classification | `contract_class` | datawindow never instantiated (tab not enabled) |
| `TP_CUSTOMERGPO` | GPO | `customer_gpo` | datawindow never instantiated (tab not enabled) |
| `TP_CONTRACTINFO` | Contract | `contract_info` | datawindow never instantiated (tab not enabled) |
