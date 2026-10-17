# Item Maintenance (`Item`)

- Window class: `w_inventory_sheet`; menu class: `m_inventorymastermaintenance`
- Tabs: 47; datawindows mapped: 40; unreachable entries: 12

## Tab overview

| Tab | Caption | Datawindows mapped | Tables in the SELECT |
|---|---|---|---|
| `TABPAGE_1` | General | `tp_1_dw_1` | discount_group, inv_mast, inv_mast_intrastat, inv_mast_lot, inv_mast_msds, inv_mast_taxinfo, manufacturer_program_type, price_family, wee_tax_code |
| `TABPAGE_2` | Unit Info | `tp_2_dw_2` | inv_mast, item_uom, unit_of_measure |
| `TABPAGE_3` | Alternate Code | `tp_3_dw_3` | alternate_code, inv_mast |
| `TABPAGE_4` | Conversion | `tp_4_dw_4` | inv_mast, item_conversion |
| `TABPAGE_5` | Default Prices | `tp_5_dw_5` | discount_group, inv_mast, inv_mast_intrastat, inv_mast_lot, inv_mast_msds, inv_mast_taxinfo, manufacturer_program_type, price_family, wee_tax_code |
| `TABPAGE_6` | Supplier List | `tp_6_dw_6` | division, inv_mast, inv_supp_auto_update_price, inventory_supplier, inventory_supplier_trade, manufacturing_class, supplier |
| `TABPAGE_7` | Supplier Detail | `tp_7_dw_7` | division, inv_mast, inv_supp_auto_update_price, inventory_supplier, inventory_supplier_trade, manufacturing_class, supplier |
| `TABPAGE_8` | Substitutes | `tp_8_dw_8` | inv_mast, inv_sub |
| `TABPAGE_ACCESSORYITEMS` | Accessory Items | `tabpage_accessoryitems` | inv_accessory, inv_mast |
| `TABPAGE_LOT` | Lot | `tabpage_lot` | inv_mast, inv_mast_lot, lot_attribute_group |
| `WEIGHT_VOLUME` | Measurements | `weight` | discount_group, inv_mast, inv_mast_intrastat, inv_mast_lot, inv_mast_msds, inv_mast_taxinfo, manufacturer_program_type, price_family, wee_tax_code |
| `ITEM_NOTES` | Item Notes | `item_notes` | inv_mast, note, note_area, notepad_class |
| `TABPAGE_CLASSES` | Classes | `classes` | discount_group, inv_mast, inv_mast_intrastat, inv_mast_lot, inv_mast_msds, inv_mast_taxinfo, manufacturer_program_type, price_family, wee_tax_code |
| `TABPAGE_LINKS` | Links | `tabpage_links` | inv_mast_links |
| `TABPAGE_KEYWORDS` | Keywords | `tabpage_keywords` | discount_group, inv_mast, inv_mast_intrastat, inv_mast_lot, inv_mast_msds, inv_mast_taxinfo, manufacturer_program_type, price_family, wee_tax_code |
| `TABPAGE_PRODREQ` | Production Requirements | `prodreq` | inv_mast_assem_info |
| `TABPAGE_PACKAGETYPE` | Package Type | `tabpage_packagetype_dw_2` | inv_mast, item_package_type, package_type, system_setting |
| `TABPAGE_PROBLEMCODE` | Problem Code | `tabpage_problemcode` | inv_mast, problem_code, problem_code_x_inv_mast |
| `TABPAGE_SUPPLIER_UNIT_INFO` | Supplier Unit Info | `tabpage_supplier_unit_info` | inv_mast, inventory_supplier, inventory_supplier_x_uom, item_uom, supplier, unit_of_measure |
| `TP_ITEM_INTERNATIONAL` | International | `tp_item_international` | company, inv_mast_trade, part_type_trade |
| `DOCUMENT_LINK` | Document Links | `document_link` | document_link, document_link_area, document_link_entity_req, inv_mast |
| `ITEMCATEGORYLIST` | Item Categories | `itemcategorylist` | item_category, item_category_x_inv_mast |
| `TP_STRATEGICPRICING` | Strategic Pricing | `strategic_pricing`, `core_status_family_detail` | company, core_status_family_detail, core_status_family_hdr, inv_mast, inv_mast_strategic_pricing |
| `TABPAGE_INTEGRATION` | Integration | `tabpage_integration` | inv_mast_x_integration, p21_integration, p21_integration_x_company |
| `TIMESTAMP` | Audit Trail | `timestamp`, `audit_trail` | p21_view_audit_trail_inv_mast_<id> |
| `TABPAGE_17` | Location List | `invloclist` | bin, bin_type, company, inv_loc, inv_loc_price_multiplier, inv_mast, inv_mast_x_company, item_putaway_attribute, location, price_family, product_group, tax_group_hdr |
| `TABPAGE_18` | Location Detail | `inv_loc_detail` | bin, bin_type, company, inv_loc, inv_loc_price_multiplier, inv_mast, inv_mast_x_company, item_putaway_attribute, location, price_family, product_group, tax_group_hdr |
| `TABPAGE_19` | Tax | `tp_19_dw_19` | company, tax_group_hdr, tax_group_line, tax_jurisdiction |
| `TABPAGE_20` | Price | `inv_loc_prices` | bin, bin_type, company, inv_loc, inv_loc_price_multiplier, inv_mast, inv_mast_x_company, item_putaway_attribute, location, price_family, product_group, tax_group_hdr |
| `TABPAGE_21` | Cost | `tp_21_dw_21` | bin, bin_type, company, inv_loc, inv_loc_price_multiplier, inv_mast, inv_mast_x_company, item_putaway_attribute, location, price_family, product_group, tax_group_hdr |
| `TABPAGE_22` | Usage | `tp_22_dw_22` | bin, bin_type, company, inv_loc, inv_loc_price_multiplier, inv_mast, inv_mast_x_company, item_putaway_attribute, location, price_family, product_group, tax_group_hdr |
| `TABPAGE_23` | Replenishment | `tp_23_dw_23` | bin, bin_type, company, inv_loc, inv_loc_price_multiplier, inv_mast, inv_mast_x_company, item_putaway_attribute, location, price_family, product_group, tax_group_hdr |
| `TABPAGE_24` | GL Accounts | `inv_loc_accounts` | bin, bin_type, company, inv_loc, inv_loc_price_multiplier, inv_mast, inv_mast_x_company, item_putaway_attribute, location, price_family, product_group, tax_group_hdr |
| `SUPPLIER_X_LOCATION` | Supplier by Location | `supplier_x_location` | division, inv_loc, inventory_supplier, inventory_supplier_x_loc, location, supplier, vendor_edi_transaction, vendor_supplier |
| `TABPAGE_LEADDATA` | Lead Data | `tabpage_leaddata` | inv_mast, item_lead_time, location, supplier |
| `TABPAGE_PROCESSING` | Processing | `tabpage_processing` | company, inv_loc, inv_loc_msp, location, process |
| `ITEM_VMI` | VMI | `item_vmi` | division, inv_loc, inventory_supplier, inventory_supplier_x_loc, location, supplier, vendor_edi_transaction, vendor_supplier |
| `TIMESTAMPDETAIL` | Timestamp | `timestampdetail` |  |

## Datawindows

### `TABPAGE_1.tp_1_dw_1` (General)

- Update table: `inv_mast`
- Tables in the SELECT: `inv_mast`, `discount_group`, `inv_mast_lot`, `price_family`, `manufacturer_program_type`, `inv_mast_msds`, `inv_mast_intrastat`, `inv_mast_taxinfo`, `wee_tax_code`

| Field | Stored in | Basis |
|---|---|---|
| `item_id` | `inv_mast.item_id` | probed |
| `item_desc` | `inv_mast.item_desc` | probed |
| `sales_discount_group_id` | `inv_mast.default_sales_discount_group` | probed |
| `purchase_discount_group_id` | `inv_mast.default_purchase_disc_group` | probed |
| `short_code` | `inv_mast.short_code` | probed |
| `extended_desc` | `inv_mast.extended_desc` | probed |
| `redemption_item_flag` | `inv_mast.redemption_item_flag` | probed |
| `redemption_value` | `inv_mast.redemption_value` | probed |
| `currency_id` | `inv_mast.currency_id` | probed |
| `serialized` | `inv_mast.serialized` | probed |
| `track_lots` | `inv_mast.track_lots` | probed |
| `inv_mast_other_charge_item` | `inv_mast.other_charge_item` | probed |
| `update_via_pricing_service` | `inv_mast.update_via_pricing_service` | probed |
| `use_tags_flag` | `inv_mast.use_tags_flag` | probed |
| `cylinder_item_flag` | `inv_mast.cylinder_item_flag` | probed |
| `product_type` | `inv_mast.product_type` | probed |
| `item_type_cd` | `inv_mast.item_type_cd` | probed |
| `parent_item_id` | `inv_mast.item_id` | probed |
| `commodity_cd` | `inv_mast_intrastat.commodity_cd` | probed |
| `cpq_item_flag` | `inv_mast.cpq_item_flag` | probed |
| `cpq_configurator_id` | `inv_mast.cpq_configurator_id` | probed |
| `delete_flag` | `inv_mast.delete_flag` | probed |
| `vendor_consigned` | `inv_mast.vendor_consigned` | probed |
| `override_specific_costing` | `inv_mast.override_specific_costing` | probed |
| `use_oc_tax_rules_flag` | `inv_mast.use_oc_tax_rules_flag` | probed |
| `drum_pickup_flag` | `inv_mast.drum_pickup_flag` | probed |
| `price_family_id` | `price_family.price_family_id` | probed |
| `spa_item_flag` | `inv_mast.spa_item_flag` | probed |
| `avail_for_sch_delivery_flag` | `inv_mast.avail_for_sch_delivery_flag` | probed |
| `use_revisions_flag` | `inv_mast.use_revisions_flag` | probed |
| `manufacturer_program_type_uid` | `inv_mast.manufacturer_program_type_uid` | probed |
| `manufacturer_program_type_pct` | `inv_mast.manufacturer_program_type_pct` | probed |
| `haz_mat_flag` | `inv_mast.haz_mat_flag` | probed |
| `msds_flag` | `inv_mast_msds.msds_flag` | probed |
| `wee_taxable_flag` | `inv_mast_taxinfo.wee_taxable_flag` | probed |
| `wee_tax_code_uid` | `inv_mast_taxinfo.wee_tax_code_uid` | probed |
| `iva_taxable_flag` | `inv_mast.iva_taxable_flag` | probed |
| `pumpoff_item` | `inv_mast.pumpoff_item` | probed |
| `pumpoff_uom` | `inv_mast.pumpoff_uom` | probed |
| `sample_item_flag` | `inv_mast.sample_item_flag` | probed |
| `jm_dts_fulfillment_flag` | `inv_mast.jm_dts_fulfillment_flag` | probed |
| `sample_item_id` | `inv_mast.item_id` | probed |
| `brand_type` | `inv_mast.brand_type` | probed |
| `iqs_item_flag` | `inv_mast.iqs_item_flag` | probed |
| `rental_item_flag` | `inv_mast.rental_item_flag` | probed |
| `rental_item_uid` | `inv_mast.rental_item_uid` | probed |
| `parent_item_desc` | `inv_mast.item_desc` | probed |
| `sales_discount_group_desc` | `discount_group.discount_group_description` | probed |
| `purchase_discount_group_desc` | `discount_group.discount_group_description` | probed |
| `rationalized` | computed: `CASE WHEN inv_mast.tpcx_status IS NOT NULL AND inv_mast.tpcx_status > 0 THEN 'Y' ELSE 'N' END` | probed |
| `price_family_desc` | `price_family.price_family_desc` | probed |
| `default_selling_unit` | computed: `(computed in the datawindow)` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Item ID: | `inv_mast.item_id` |
| 2 | Item Desc | `inv_mast.item_desc` |
| 3 | Delete Flag | `inv_mast.delete_flag` |
| 4 | Weight | `inv_mast.weight` |
| 5 | Net Weight | `inv_mast.net_weight` |
| 9 | Cube | `inv_mast.cube` |
| 11 | Date Inactive | `inv_mast.date_inactive` |
| 13 | Catch Weight Indicator | `inv_mast.catch_weight_indicator` |
| 17 | Track Serial Numbers: | `inv_mast.serialized` |
| 18 | Product Type: | `inv_mast.product_type` |
| 22 | Short Code: | `inv_mast.short_code` |
| 23 | Track Lots | `inv_mast.track_lots` |
| 39 | Sales Group: | `inv_mast.default_sales_discount_group` |
| 40 | Purchase Group: | `inv_mast.default_purchase_disc_group` |
| 45 | Extended Desc: | `inv_mast.extended_desc` |
| 46 | Sales Discount Group Desc | `inv_mast.discount_group_description` |
| 47 | Purchase Discount Group Desc | `inv_mast.discount_group_description` |
| 50 | Inv Mast Other Charge Item | `inv_mast.other_charge_item` |
| 52 | Update Via Pricing Service | `inv_mast.update_via_pricing_service` |
| 59 | Haz Mat Flag | `inv_mast.haz_mat_flag` |
| 60 | Inv Mast Uid | `inv_mast.inv_mast_uid` |
| 63 | Rationalized | `rationalized` |
| 66 | Use Tags Flag | `inv_mast.use_tags_flag` |
| 74 | Override Specific Costing | `inv_mast.override_specific_costing` |
| 81 | Default Price Family ID: | `price_family.price_family_id` |
| 82 | Price Family Desc | `price_family.price_family_desc` |
| 83 | Spa Item Flag | `inv_mast.spa_item_flag` |
| 93 | Use Oc Tax Rules Flag | `inv_mast.use_oc_tax_rules_flag` |

### `TABPAGE_2.tp_2_dw_2` (Unit Info)

- Update table: `item_uom`
- Tables in the SELECT: `item_uom`, `unit_of_measure`, `inv_mast`

| Field | Stored in | Basis |
|---|---|---|
| `unit_id` | `item_uom.unit_of_measure` | probed |
| `unit_size` | `item_uom.unit_size` | column |
| `default_sales_unit` | computed: `CASE WHEN inv_mast.default_selling_unit = item_uom.unit_of_measure THEN 'Y' ELSE 'N' END` | alias |
| `sales_pricing_unit` | computed: `CASE WHEN inv_mast.sales_pricing_unit = item_uom.unit_of_measure THEN 'Y' ELSE 'N' END` | alias |
| `default_purchasing_unit` | computed: `CASE WHEN inv_mast.default_purchasing_unit = item_uom.unit_of_measure THEN 'Y' ELSE 'N' END` | alias |
| `purchase_pricing_unit` | computed: `CASE WHEN inv_mast.purchase_pricing_unit = item_uom.unit_of_measure THEN 'Y' ELSE 'N' END` | alias |
| `base_unit_flag` | computed: `CASE WHEN inv_mast.base_unit = item_uom.unit_of_measure THEN 'Y' ELSE 'N' END` | alias |
| `base_unit_is_item_uom` | computed: `CASE WHEN inv_mast.base_unit = item_uom.unit_of_measure THEN 'Y' ELSE 'N' END` | alias |
| `delete_flag` | `item_uom.delete_flag` | probed |
| `unit_description` | `unit_of_measure.unit_description` | column |
| `unit_of_measure` | `item_uom.unit_of_measure` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Unit of Measure | `item_uom.unit_of_measure` |
| 2 | Delete Flag | `item_uom.delete_flag` |
| 6 | Unit Size | `item_uom.unit_size` |
| 9 | Unit Description | `unit_of_measure.unit_description` |
| 10 | Purchase Pricing Unit | `inv_mast.purchase_pricing_unit` |
| 11 | Sales Pricing Unit | `inv_mast.sales_pricing_unit` |
| 13 | Default Sales Unit | `default_sales_unit` |
| 14 | Default Purchase Unit | `inv_mast.default_purchasing_unit` |
| 18 | Base Unit | `base_unit_flag` |
| 19 | Base Unit Is Item UOM | `base_unit_is_item_uom` |

### `TABPAGE_3.tp_3_dw_3` (Alternate Code)

- Update table: `alternate_code`
- Tables in the SELECT: `alternate_code`, `inv_mast`

| Field | Stored in | Basis |
|---|---|---|
| `alternate_code` | `alternate_code.alternate_code` | probed |
| `delete_flag` | `alternate_code.delete_flag` | column |
| `row_no` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Alternate Code | `alternate_code.alternate_code` |
| 4 | Delete Flag | `alternate_code.delete_flag` |

### `TABPAGE_4.tp_4_dw_4` (Conversion)

- Update table: `item_conversion`
- Tables in the SELECT: `item_conversion`, `inv_mast`

| Field | Stored in | Basis |
|---|---|---|
| `compute_convert_quantities` | computed: `''` | alias |
| `from_uom` | `item_conversion.from_uom` | column |
| `to_uom` | `item_conversion.to_uom` | column |
| `round` | `item_conversion.round` | column |
| `accumulate` | `item_conversion.accumulate` | column |
| `print_on_pick_ticket` | `item_conversion.print_on_pick_ticket` | column |
| `print_on_order_ack` | `item_conversion.print_on_order_ack` | column |
| `print_on_invoice` | `item_conversion.print_on_invoice` | column |
| `print_on_po` | `item_conversion.print_on_po` | column |
| `print_on_prod_order` | `item_conversion.print_on_prod_order` | column |
| `convert_at_oe` | `item_conversion.convert_at_oe` | column |
| `convert_at_po` | `item_conversion.convert_at_po` | column |
| `delete_flag` | `item_conversion.delete_flag` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | FromUOM | `item_conversion.from_uom` |
| 3 | To UOM | `item_conversion.to_uom` |
| 4 | Round | `item_conversion.round` |
| 5 | Accumulate | `item_conversion.accumulate` |
| 6 | Print Conversion On Pick Tickets | `item_conversion.print_on_pick_ticket` |
| 7 | Print Conversion On Order Acks | `item_conversion.print_on_order_ack` |
| 8 | Print Conversion On Invoices | `item_conversion.print_on_invoice` |
| 9 | Print Conversion On Purchase Orders | `item_conversion.print_on_po` |
| 10 | Convert At Order Entry | `item_conversion.convert_at_oe` |
| 11 | Convert At PO Entry | `item_conversion.convert_at_po` |
| 12 | Delete | `item_conversion.delete_flag` |
| 17 | Compute Convert Quantities | `compute_convert_quantities` |
| 19 | Print Conversion OnProduction Orders | `item_conversion.print_on_prod_order` |

### `TABPAGE_5.tp_5_dw_5` (Default Prices)

- Update table: `inv_mast`
- Tables in the SELECT: `inv_mast`, `discount_group`, `inv_mast_lot`, `price_family`, `manufacturer_program_type`, `inv_mast_msds`, `inv_mast_intrastat`, `inv_mast_taxinfo`, `wee_tax_code`

| Field | Stored in | Basis |
|---|---|---|
| `price1` | `inv_mast.price1` | column |
| `price2` | `inv_mast.price2` | column |
| `price3` | `inv_mast.price3` | column |
| `price4` | `inv_mast.price4` | column |
| `price5` | `inv_mast.price5` | column |
| `price6` | `inv_mast.price6` | column |
| `price7` | `inv_mast.price7` | column |
| `price8` | `inv_mast.price8` | column |
| `price9` | `inv_mast.price9` | column |
| `price10` | `inv_mast.price10` | column |
| `c_unit_of_measure` | computed: `' '` | alias |
| `c_unit_size` | computed: `0.0000` | alias |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 29 | Price 1: | `inv_mast.price1` |
| 30 | Price 2: | `inv_mast.price2` |
| 31 | Price 3: | `inv_mast.price3` |
| 32 | Price 4: | `inv_mast.price4` |
| 33 | Price 5: | `inv_mast.price5` |
| 34 | Price 6: | `inv_mast.price6` |
| 35 | Price 7: | `inv_mast.price7` |
| 36 | Price 8: | `inv_mast.price8` |
| 37 | Price 9: | `inv_mast.price9` |
| 38 | Price 10: | `inv_mast.price10` |
| 56 | Default Sales Pricing Unit: | `c_unit_of_measure` |
| 57 | Unit Size: | `c_unit_size` |

### `TABPAGE_6.tp_6_dw_6` (Supplier List)

- Update table: `inventory_supplier`
- Tables in the SELECT: `inventory_supplier`, `inv_mast`, `supplier`, `division`, `manufacturing_class`, `inv_supp_auto_update_price`, `inventory_supplier_trade`

| Field | Stored in | Basis |
|---|---|---|
| `supplier_id` | `inventory_supplier.supplier_id` | probed |
| `division_id` | `inventory_supplier.division_id` | probed |
| `delete_flag` | `inventory_supplier.delete_flag` | probed |
| `supplier_name` | `supplier.supplier_name` | probed |
| `division_name` | computed: `division_name` | probed |
| `cf_chgd_certificate_of_origin_exp_date` | computed: `(computed in the datawindow)` | probed |
| `cf_edited_trade_cols` | computed: `(computed in the datawindow)` | probed |
| `cf_chgd_certificate_of_origin_file_path` | computed: `(computed in the datawindow)` | probed |
| `cf_chgd_country_of_origin` | computed: `(computed in the datawindow)` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Supplier ID | `inventory_supplier.supplier_id` |
| 2 | Supplier Name | `supplier.supplier_name` |
| 3 | Division ID | `inventory_supplier.division_id` |
| 4 | Division Name | `inventory_supplier.division_name` |
| 8 | Delete | `inventory_supplier.delete_flag` |

### `TABPAGE_7.tp_7_dw_7` (Supplier Detail)

- Update table: `inventory_supplier`
- Tables in the SELECT: `inventory_supplier`, `inv_mast`, `supplier`, `division`, `manufacturing_class`, `inv_supp_auto_update_price`, `inventory_supplier_trade`

| Field | Stored in | Basis |
|---|---|---|
| `manufacturing_class_id` | `inventory_supplier.manufacturing_class_id` | probed |
| `supplier_part_no` | `inventory_supplier.supplier_part_no` | probed |
| `catalog_name` | `inventory_supplier.catalog_name` | probed |
| `inventory_supplier_catalog_page` | `inventory_supplier.catalog_page` | probed |
| `list_price` | `inventory_supplier.list_price` | probed |
| `cost` | `inventory_supplier.cost` | probed |
| `supplier_sort_code` | `inventory_supplier.supplier_sort_code` | probed |
| `buyback_supplier_part_no` | `inventory_supplier.buyback_supplier_part_no` | probed |
| `buyback_uom` | `inventory_supplier.buyback_uom` | probed |
| `future_cost` | `inventory_supplier.future_cost` | probed |
| `effective_date` | `inventory_supplier.effective_date` | probed |
| `delete_flag` | `inventory_supplier.delete_flag` | probed |
| `upc_code` | `inventory_supplier.upc_code` | probed |
| `ean_code` | `inventory_supplier.ean_code` | probed |
| `supplier_msds` | `inventory_supplier.msds` | probed |
| `parker_part_length` | `inventory_supplier.parker_part_length` | probed |
| `contract_number` | `inventory_supplier.contract_number` | probed |
| `auto_update_prices_flag` | computed: `(the tool names inventory_supplier.auto_update_prices_flag; the SELECT does not read it)` | probed |
| `auto_update_prices_source_flag` | computed: `(the tool names inventory_supplier.auto_update_prices_source_flag; the SELECT does not read it)` | probed |
| `certificate_of_origin_file_path` | `inventory_supplier_trade.certificate_of_origin_file_path` | probed |
| `certificate_of_origin_exp_date` | `inventory_supplier_trade.certificate_of_origin_exp_date` | probed |
| `country_of_origin` | `inventory_supplier_trade.country_of_origin` | probed |
| `supplier_id` | `inventory_supplier.supplier_id` | probed |
| `manufacturing_class_desc` | `manufacturing_class.manufacturing_class_desc` | probed |
| `supplier_name` | `supplier.supplier_name` | probed |
| `c_unit_of_measure` | computed: `' '` | probed |
| `c_unit_size` | computed: `0.000000000` | probed |
| `cf_rowinfo` | computed: `(computed in the datawindow)` | probed |
| `cf_edited_trade_cols` | computed: `(computed in the datawindow)` | probed |
| `cf_chgd_certificate_of_origin_file_path` | computed: `(computed in the datawindow)` | probed |
| `cf_chgd_certificate_of_origin_exp_date` | computed: `(computed in the datawindow)` | probed |
| `cf_chgd_country_of_origin` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Supplier Id | `inventory_supplier.supplier_id` |
| 2 | Supplier Name | `supplier.supplier_name` |
| 5 | Catalog Name: | `inventory_supplier.catalog_name` |
| 6 | Catalog Page: | `inventory_supplier.catalog_page` |
| 7 | SDS: | `inventory_supplier.msds` |
| 8 | Delete Flag | `inventory_supplier.delete_flag` |
| 12 | Supplier Part Number: | `inventory_supplier.supplier_part_no` |
| 13 | Supplier Sort Code: | `inventory_supplier.supplier_sort_code` |
| 14 | List Price: | `inventory_supplier.list_price` |
| 15 | Cost: | `inventory_supplier.cost` |
| 16 | Manufacturing Class ID: | `inventory_supplier.manufacturing_class_id` |
| 17 | Manufacturing Class Desc | `manufacturing_class.manufacturing_class_desc` |
| 20 | UPC Code: | `inventory_supplier.upc_code` |
| 25 | Default Purchase Pricing Unit: | `c_unit_of_measure` |
| 26 | Unit Size: | `inventory_supplier.c_unit_size` |
| 31 | Contract Number: | `inventory_supplier.contract_number` |
| 33 | Parker Part Length: | `inventory_supplier.parker_part_length` |
| 35 | Future Cost: | `inventory_supplier.future_cost` |
| 36 | Effective Date: | `inventory_supplier.effective_date` |
| 41 | Certificate of Origin: | `inventory_supplier_trade.certificate_of_origin_file_path` |
| 42 | Certificate of Origin Expiration Date: | `inventory_supplier_trade.certificate_of_origin_exp_date` |
| 46 | Country Of Origin: | `inventory_supplier_trade.country_of_origin` |
| 48 | EAN Code: | `inventory_supplier.ean_code` |
| calc | Cf Rowinfo | `'Row ' + string(getrow()) + ' of ' + String(rowcount())` |

### `TABPAGE_8.tp_8_dw_8` (Substitutes)

- Update table: `inv_sub`
- Tables in the SELECT: `inv_sub`, `inv_mast`

| Field | Stored in | Basis |
|---|---|---|
| `sub_id` | `inv_mast.item_id` | probed |
| `sub_desc` | `inv_sub.sub_desc` | column |
| `interchangeable` | `inv_sub.interchangeable` | column |
| `delete_flag` | `inv_sub.delete_flag` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Substitute ID | `inv_mast_sub.item_id` |
| 4 | Description | `inv_sub.sub_desc` |
| 5 | Delete | `inv_sub.delete_flag` |
| 9 | Interchangeable | `inv_sub.interchangeable` |

### `TABPAGE_ACCESSORYITEMS.tabpage_accessoryitems` (Accessory Items)

- Update table: `inv_accessory`
- Tables in the SELECT: `inv_accessory`, `inv_mast`

| Field | Stored in | Basis |
|---|---|---|
| `item_id` | `inv_mast.item_id` | column |
| `child_unit_quantity` | `inv_accessory.child_unit_quantity` | probed |
| `child_uom_code_no` | `inv_accessory.child_uom_code_no` | column |
| `parent_unit_quantity` | `inv_accessory.parent_unit_quantity` | column |
| `parent_uom_code_no` | `inv_accessory.parent_uom_code_no` | column |
| `auto_populate_quantity` | `inv_accessory.auto_populate_quantity` | probed |
| `scale_to_parent_quantity` | `inv_accessory.scale_to_parent_quantity` | column |
| `link_qty_to_parent_flag` | `inv_accessory.link_qty_to_parent_flag` | column |
| `delete_flag` | computed: `'N'` | alias |
| `item_desc` | `inv_mast.item_desc` | column |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Item ID | `inv_mast.item_id` |
| 2 | Item Desc | `inv_mast.item_desc` |
| 3 | Auto-Populate Qty | `inv_accessory.auto_populate_quantity` |
| 4 | Unit Quantity | `inv_accessory.child_unit_quantity` |
| 5 | Unit of Measure | `inv_accessory.child_uom_code_no` |
| 6 | Scale To Parent Qty | `inv_accessory.scale_to_parent_quantity` |
| 7 | Parent Unit Quantity | `inv_accessory.parent_unit_quantity` |
| 8 | Parent Unit of Measure | `inv_accessory.parent_uom_code_no` |
| 12 | Delete | `delete_flag` |

### `TABPAGE_LOT.tabpage_lot` (Lot)

- Update table: `inv_mast_lot`
- Tables in the SELECT: `inv_mast_lot`, `inv_mast`, `lot_attribute_group`

| Field | Stored in | Basis |
|---|---|---|
| `use_system_setting_lot_assign` | `inv_mast_lot.use_system_setting_lot_assign` | column |
| `auto_assign_lots` | `inv_mast_lot.auto_assign_lots` | column |
| `lot_assignment_required` | `inv_mast_lot.lot_assignment_required` | column |
| `item_lot_exp_warning_days` | `inv_mast_lot.item_lot_exp_warning_days` | column |
| `assignment_option` | `inv_mast_lot.assignment_option` | column |
| `use_lot_cost_as_inventory_cost` | `inv_mast_lot.use_lot_cost_as_inventory_cost` | column |
| `lot_attribute_group_cd` | `lot_attribute_group.lot_attribute_group_cd` | column |
| `use_last_customer_lot_flag` | `inv_mast_lot.use_last_customer_lot_flag` | column |
| `belt_item_flag` | `inv_mast_lot.belt_item_flag` | column |
| `belt_remnant_length` | `inv_mast_lot.belt_remnant_length` | column |
| `belt_remnant_width` | `inv_mast_lot.belt_remnant_width` | probed |
| `minimum_belt_width_increment` | `inv_mast_lot.minimum_belt_width_increment` | column |
| `purchasing_belt_width` | `inv_mast_lot.purchasing_belt_width` | column |
| `purchasing_belt_length` | `inv_mast_lot.purchasing_belt_length` | column |
| `use_lot_pricing_flag` | `inv_mast_lot.use_lot_pricing_flag` | column |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 3 | Auto Assign Lots | `inv_mast_lot.auto_assign_lots` |
| 4 | Lot assignment option: | `inv_mast_lot.assignment_option` |
| 5 | Lot Assignment Required | `inv_mast_lot.lot_assignment_required` |
| 6 | Use Lot Cost As Inventory Cost | `inv_mast_lot.use_lot_cost_as_inventory_cost` |
| 7 | Use System Setting Lot Assign | `inv_mast_lot.use_system_setting_lot_assign` |
| 13 | Lot Attribute Group: | `lot_attribute_group.lot_attribute_group_cd` |
| 15 | Use Last Customer Lot Flag | `inv_mast_lot.use_last_customer_lot_flag` |
| 16 | Lot expiration warning days: | `inv_mast_lot.item_lot_exp_warning_days` |

### `WEIGHT_VOLUME.weight` (Measurements)

- Update table: `inv_mast`
- Tables in the SELECT: `inv_mast`, `discount_group`, `inv_mast_lot`, `price_family`, `manufacturer_program_type`, `inv_mast_msds`, `inv_mast_intrastat`, `inv_mast_taxinfo`, `wee_tax_code`

| Field | Stored in | Basis |
|---|---|---|
| `catch_weight_indicator` | `inv_mast.catch_weight_indicator` | column |
| `catch_lot_weight_flag` | `inv_mast.catch_lot_weight_flag` | column |
| `weight` | `inv_mast.weight` | column |
| `net_weight` | `inv_mast.net_weight` | column |
| `cube` | `inv_mast.cube` | column |
| `purchasing_weight` | `inv_mast.purchasing_weight` | column |
| `net_mass_in_kgs` | `inv_mast_intrastat.net_mass_in_kgs` | column |
| `supplementary_uom` | `inv_mast_intrastat.supplementary_uom` | column |
| `length` | `inv_mast.length` | column |
| `width` | `inv_mast.width` | column |
| `height` | `inv_mast.height` | column |
| `packing_weight_tracking_option` | `inv_mast.packing_weight_tracking_option` | column |
| `dflt_dimension_scale` | `inv_mast.dflt_dimension_scale` | column |
| `supplementary_value` | `inv_mast_intrastat.supplementary_value` | column |

| # | Label | table.column / expression |
|---|---|---|
| 4 | Gross Weight: | `inv_mast.weight` |
| 5 | SKU Net Weight: | `inv_mast.net_weight` |
| 9 | SKU Volume: | `inv_mast.cube` |
| 13 | Catch Weight Indicator | `inv_mast.catch_weight_indicator` |
| 14 | Purchasing Weight: | `inv_mast.purchasing_weight` |
| 87 | Length: | `inv_mast.length` |
| 88 | Width: | `inv_mast.width` |
| 89 | Height: | `inv_mast.height` |
| 137 | Track Weight Using: | `inv_mast.packing_weight_tracking_option` |

### `ITEM_NOTES.item_notes` (Item Notes)

- Update table: `note_area`
- Tables in the SELECT: `note_area`, `note`, `inv_mast`, `notepad_class`

| Field | Stored in | Basis |
|---|---|---|
| `note` | `note.note` | probed |
| `note_id` | `note.note_uid` | probed |
| `topic` | `note.topic` | column |
| `notepad_class_desc` | `notepad_class.notepad_class_desc` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Note ID | `note.note_uid` |
| 2 | Topic | `note.topic` |
| 3 | Note | `note.note` |
| 5 | Class | `notepad_class.notepad_class_desc` |

### `TABPAGE_CLASSES.classes` (Classes)

- Update table: `inv_mast`
- Tables in the SELECT: `inv_mast`, `discount_group`, `inv_mast_lot`, `price_family`, `manufacturer_program_type`, `inv_mast_msds`, `inv_mast_intrastat`, `inv_mast_taxinfo`, `wee_tax_code`

| Field | Stored in | Basis |
|---|---|---|
| `commission_class_id` | `inv_mast.commission_class_id` | column |
| `service_commission_class_id` | `inv_mast.service_commission_class_id` | column |
| `tag_hold_class_uid` | `inv_mast.tag_hold_class_uid` | column |
| `class_id1` | `inv_mast.class_id1` | column |
| `class_id2` | `inv_mast.class_id2` | column |
| `class_id3` | `inv_mast.class_id3` | column |
| `class_id4` | `inv_mast.class_id4` | column |
| `class_id5` | `inv_mast.class_id5` | probed |
| `item_sales_tax_class` | `inv_mast.item_sales_tax_class` | column |
| `parker_product_cd` | `inv_mast.parker_product_cd` | column |
| `commodity_code` | `inv_mast.commodity_code` | column |
| `type_of_sale` | `inv_mast.type_of_sale` | probed |
| `ecc_enabled_flag` | `inv_mast.ecc_enabled_flag` | column |
| `conoco_division_class_id` | `inv_mast.conoco_division_class_id` | column |
| `buy_get_class` | `inv_mast.buy_get_class` | column |
| `bol_class` | `inv_mast.bol_class` | column |
| `service_class_id` | `inv_mast.service_class_id` | column |

| # | Label | table.column / expression |
|---|---|---|
| 24 | Class 1: | `inv_mast.class_id1` |
| 25 | Class 2: | `inv_mast.class_id2` |
| 26 | Stocked For Customer | `inv_mast.class_id3` |
| 27 | Class 4: | `inv_mast.class_id4` |
| 28 | Return Status | `inv_mast.class_id5` |
| 49 | Commission Class Id | `inv_mast.commission_class_id` |
| 68 | Tag and Hold Class: | `inv_mast.tag_hold_class_uid` |
| 73 | Service Commission Class: | `inv_mast.service_commission_class_id` |
| 76 | Parker Product Code: | `inv_mast.parker_product_cd` |
| 78 | Commodity Code: | `inv_mast.commodity_code` |
| 120 | Type of Sale Code: | `inv_mast.type_of_sale` |
| 138 | BOL Class: | `inv_mast.bol_class` |
| 142 | Ecc Enabled Flag | `inv_mast.ecc_enabled_flag` |

### `TABPAGE_LINKS.tabpage_links` (Links)

- Update table: `inv_mast_links`
- Tables in the SELECT: `inv_mast_links`

| Field | Stored in | Basis |
|---|---|---|
| `link_name` | `inv_mast_links.link_name` | column |
| `link_path` | `inv_mast_links.link_path` | column |
| `link_area` | `inv_mast_links.link_area` | column |
| `row_status_flag` | `inv_mast_links.row_status_flag` | column |
| `inv_mast_links_uid` | `inv_mast_links.inv_mast_links_uid` | column |
| `cf_spaces` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Link ID | `inv_mast_links.inv_mast_links_uid` |
| 3 | Link Name | `inv_mast_links.link_name` |
| 4 | Link Path | `inv_mast_links.link_path` |
| 5 | Link Area | `inv_mast_links.link_area` |
| 6 | Status | `inv_mast_links.row_status_flag` |

### `TABPAGE_KEYWORDS.tabpage_keywords` (Keywords)

- Update table: `inv_mast`
- Tables in the SELECT: `inv_mast`, `discount_group`, `inv_mast_lot`, `price_family`, `manufacturer_program_type`, `inv_mast_msds`, `inv_mast_intrastat`, `inv_mast_taxinfo`, `wee_tax_code`

| Field | Stored in | Basis |
|---|---|---|
| `keywords` | `inv_mast.keywords` | column |

| # | Label | table.column / expression |
|---|---|---|
| 64 | Keywords: | `inv_mast.keywords` |

### `TABPAGE_PRODREQ.prodreq` (Production Requirements)

- Update table: `inv_mast_assem_info`
- Tables in the SELECT: `inv_mast_assem_info`

| Field | Stored in | Basis |
|---|---|---|
| `component_type` | `inv_mast_assem_info.component_type` | column |
| `hose_fitting_uom` | `inv_mast_assem_info.hose_fitting_uom` | column |
| `hose_fitting_d_length` | `inv_mast_assem_info.hose_fitting_d_length` | column |

| # | Label | table.column / expression |
|---|---|---|
| 3 | Component type: | `inv_mast_assem_info.component_type` |
| 4 | D Length: | `inv_mast_assem_info.hose_fitting_d_length` |
| 5 | Unit of measure: | `inv_mast_assem_info.hose_fitting_uom` |

### `TABPAGE_PACKAGETYPE.tabpage_packagetype_dw_2` (Package Type)

- Update table: `item_package_type`
- Tables in the SELECT: `item_package_type`, `inv_mast`, `package_type`, `system_setting`

| Field | Stored in | Basis |
|---|---|---|
| `package_type_id` | `package_type.package_type_id` | column |
| `item_package_qty` | `item_package_type.item_package_qty` | column |
| `item_package_uom` | `item_package_type.item_package_uom` | column |
| `item_pkg_gross_weight` | computed: `0.0` | alias |
| `item_net_volume` | `item_package_type.item_net_volume` | column |
| `row_status_flag` | `item_package_type.row_status_flag` | column |
| `item_pkg_tare_weight` | `item_package_type.item_pkg_tare_weight` | column |
| `system_defined_weight_uom` | `system_setting.value` | alias |
| `system_defined_volume_uom` | `system_setting.value` | alias |
| `rowind` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 4 | Package Type | `package_type.package_type_id` |
| 7 | Default Qty | `item_package_type.item_package_qty` |
| 8 | UOM | `item_package_type.item_package_uom` |
| 9 | Tare Weight | `item_package_type.item_pkg_tare_weight` |
| 10 | Item Package Volume | `item_package_type.item_net_volume` |
| 11 | Status | `item_package_type.row_status_flag` |
| 16 | Weight UOM | `system_defined_weight_uom` |
| 17 | Volume UOM | `system_defined_volume_uom` |
| 20 | Gross Weight | `item_pkg_gross_weight` |

### `TABPAGE_PROBLEMCODE.tabpage_problemcode` (Problem Code)

- Update table: `problem_code_x_inv_mast`
- Tables in the SELECT: `problem_code_x_inv_mast`, `problem_code`, `inv_mast`

| Field | Stored in | Basis |
|---|---|---|
| `problem_code_id` | `problem_code.problem_code_id` | column |
| `row_status_flag` | `problem_code_x_inv_mast.row_status_flag` | column |
| `problem_code_desc` | `problem_code.problem_code_desc` | column |
| `compute_1` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 4 | Status | `problem_code_x_inv_mast.row_status_flag` |
| 12 | Problem ID | `problem_code.problem_code_id` |
| 13 | Problem Desc | `problem_code.problem_code_desc` |

### `TABPAGE_SUPPLIER_UNIT_INFO.tabpage_supplier_unit_info` (Supplier Unit Info)

- Update table: `inventory_supplier_x_uom`
- Tables in the SELECT: `item_uom`, `inv_mast`, `unit_of_measure`, `inventory_supplier`, `supplier`, `inventory_supplier_x_uom`

| Field | Stored in | Basis |
|---|---|---|
| `supplier_unit_of_measure` | `inventory_supplier_x_uom.supplier_unit_of_measure` | column |
| `gtin_code` | `inventory_supplier_x_uom.gtin_code` | column |
| `supplier_id` | `inventory_supplier.supplier_id` | column |
| `supplier_name` | `supplier.supplier_name` | column |
| `unit_of_measure` | `item_uom.unit_of_measure` | column |
| `unit_description` | `unit_of_measure.unit_description` | column |
| `cf_space` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 2 | Unit OfMeasure | `item_uom.unit_of_measure` |
| 3 | Unit Description | `unit_of_measure.unit_description` |
| 4 | Supplier ID | `inventory_supplier.supplier_id` |
| 5 | Supplier Name | `supplier.supplier_name` |
| 6 | Supplier Unit Of Measure | `inventory_supplier_x_uom.supplier_unit_of_measure` |
| 14 | GTIN | `inventory_supplier_x_uom.gtin_code` |

### `TP_ITEM_INTERNATIONAL.tp_item_international` (International)

- Update table: `inv_mast_trade`
- Tables in the SELECT: `inv_mast_trade`, `company`, `part_type_trade`

| Field | Stored in | Basis |
|---|---|---|
| `trade_type` | `part_type_trade.trade_type` | column |
| `broker_description` | `inv_mast_trade.broker_description` | column |
| `import_uom` | `inv_mast_trade.import_uom` | column |
| `import_tariff_amount` | `inv_mast_trade.import_tariff_amount` | column |
| `export_tariff_amount` | `inv_mast_trade.export_tariff_amount` | column |
| `added_value` | `inv_mast_trade.added_value` | column |
| `preference_criterion` | `inv_mast_trade.preference_criterion` | column |
| `producer_flag` | `inv_mast_trade.producer_flag` | column |
| `net_cost_flag` | `inv_mast_trade.net_cost_flag` | column |
| `tax_class` | `inv_mast_trade.tax_class` | column |
| `nafta_class` | `inv_mast_trade.nafta_class` | column |
| `import_tariff_number` | `inv_mast_trade.import_tariff_number` | column |
| `export_tariff_number` | `inv_mast_trade.export_tariff_number` | column |
| `scrap_tariff_number` | `inv_mast_trade.scrap_tariff_number` | column |
| `lacey_intended_use` | `inv_mast_trade.lacey_intended_use` | column |
| `schedule_b_number` | `inv_mast_trade.schedule_b_number` | column |
| `hts_classification` | `inv_mast_trade.hts_classification` | column |
| `harmonized_tax` | `inv_mast_trade.harmonized_tax` | column |
| `eccn` | `inv_mast_trade.eccn` | probed |
| `joint_production_flag` | `inv_mast_trade.joint_production_flag` | column |
| `producer_evidence` | `inv_mast_trade.producer_evidence` | probed |
| `regional_value_calc_method` | `inv_mast_trade.regional_value_calc_method` | column |
| `regional_value_calc_start_date` | `inv_mast_trade.regional_value_calc_start_date` | column |
| `regional_value_calc_end_date` | `inv_mast_trade.regional_value_calc_end_date` | column |
| `company_id` | `inv_mast_trade.company_id` | column |
| `company_name` | `company.company_name` | column |
| `trade_type_desc` | `part_type_trade.trade_type_desc` | column |
| `cf_rowinfo` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 3 | Company Id: | `inv_mast_trade.company_id` |
| 4 | Company Name | `company.company_name` |
| 7 | Part Type: | `part_type_trade.trade_type` |
| 8 | Trade Type Desc | `part_type_trade.trade_type_desc` |
| 9 | Broker Description: | `inv_mast_trade.broker_description` |
| 10 | Import UOM: | `inv_mast_trade.import_uom` |
| 11 | Import Tariff Amount: | `inv_mast_trade.import_tariff_amount` |
| 12 | Export Tariff Amount: | `inv_mast_trade.export_tariff_amount` |
| 13 | Added Value: | `inv_mast_trade.added_value` |
| 14 | USMCA Class: | `inv_mast_trade.nafta_class` |
| 15 | Import Tariff Number: | `inv_mast_trade.import_tariff_number` |
| 16 | Export Tariff Number: | `inv_mast_trade.export_tariff_number` |
| 17 | Scrap Tariff Number: | `inv_mast_trade.scrap_tariff_number` |
| 18 | Lacey Intended Use: | `inv_mast_trade.lacey_intended_use` |
| 19 | Schedule B Number: | `inv_mast_trade.schedule_b_number` |
| 20 | HTS Classification: | `inv_mast_trade.hts_classification` |
| 21 | Tax Class: | `inv_mast_trade.tax_class` |
| 22 | Harmonized Tax: | `inv_mast_trade.harmonized_tax` |
| 23 | Preference Criterion: | `inv_mast_trade.preference_criterion` |
| 24 | Producer Flag | `inv_mast_trade.producer_flag` |
| 25 | Net Cost Flag | `inv_mast_trade.net_cost_flag` |
| 30 | ECCN: | `inv_mast_trade.eccn` |
| 31 | Joint Production Flag | `inv_mast_trade.joint_production_flag` |
| 32 | Producer Evidence: | `inv_mast_trade.producer_evidence` |
| 33 | Regional Value Calc Method: | `inv_mast_trade.regional_value_calc_method` |
| 34 | Regional Value Calc Start Date: | `inv_mast_trade.regional_value_calc_start_date` |
| 35 | Regional Value Calc End Date: | `inv_mast_trade.regional_value_calc_end_date` |
| calc | Cf Rowinfo | `'Row ' + string(getrow()) + ' of ' + String(rowcount())` |

### `DOCUMENT_LINK.document_link` (Document Links)

- Update table: `document_link`
- Tables in the SELECT: `document_link`, `document_link_area`, `inv_mast`, `document_link_entity_req`

| Field | Stored in | Basis |
|---|---|---|
| `link_name` | `document_link.link_name` | probed |
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
| calc | Document Linked to | `IF ( key2_cd = 'lot_cd', if(isnull(key2_value),'',key2_value), IF ( key1_cd = 'inv_mast_uid', if(isnull(item_id),'',item_id), if(isnull(key1_value),'',key1_value) ) + IF ( IsNull(key2_value), '', '/' + key2_value + IF ( IsNull(key3_value), '', '/' + key3_value)) )` |

### `ITEMCATEGORYLIST.itemcategorylist` (Item Categories)

- Update table: `item_category_x_inv_mast`
- Tables in the SELECT: `item_category_x_inv_mast`, `item_category`

| Field | Stored in | Basis |
|---|---|---|
| `item_category_id` | `item_category.item_category_id` | probed |
| `display_desc` | `item_category_x_inv_mast.display_desc` | column |
| `display_on_web_flag` | `item_category_x_inv_mast.display_on_web_flag` | probed |
| `delete_flag` | `item_category_x_inv_mast.delete_flag` | column |
| `item_category_desc` | `item_category.item_category_desc` | column |
| `cf_rowfocusindicator` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 5 | Display On Web | `item_category_x_inv_mast.display_on_web_flag` |
| 6 | Delete Flag | `item_category_x_inv_mast.delete_flag` |
| 11 | Item Category ID | `item_category.item_category_id` |
| 12 | Item Category Description | `item_category.item_category_desc` |
| 15 | Item Description | `item_category_x_inv_mast.display_desc` |

### `TP_STRATEGICPRICING.strategic_pricing` (Strategic Pricing)

- Update table: `inv_mast_strategic_pricing`
- Tables in the SELECT: `inv_mast_strategic_pricing`, `company`

| Field | Stored in | Basis |
|---|---|---|
| `core_status_cd` | `inv_mast_strategic_pricing.core_status_cd` | column |
| `item_coreness_factor` | `inv_mast_strategic_pricing.item_coreness_factor` | column |
| `company_id` | `inv_mast_strategic_pricing.company_id` | column |
| `company_name` | `company.company_name` | column |

| # | Label | table.column / expression |
|---|---|---|
| 3 | Company ID | `inv_mast_strategic_pricing.company_id` |
| 5 | Core Status | `inv_mast_strategic_pricing.core_status_cd` |
| 10 | Company Name | `company.company_name` |
| 13 | Item Coreness Factor | `inv_mast_strategic_pricing.item_coreness_factor` |

### `TP_STRATEGICPRICING.core_status_family_detail` (Strategic Pricing)

- Update table: `core_status_family_detail`
- Tables in the SELECT: `core_status_family_detail`, `inv_mast`, `core_status_family_hdr`

| Field | Stored in | Basis |
|---|---|---|
| `core_family_id` | `core_status_family_hdr.core_family_id` | column |
| `core_family_desc` | `core_status_family_hdr.core_family_desc` | column |

| # | Label | table.column / expression |
|---|---|---|
| 11 | Core Status Family ID: | `core_status_family_hdr.core_family_id` |
| 12 | Core Family Desc | `core_status_family_hdr.core_family_desc` |

### `TABPAGE_INTEGRATION.tabpage_integration` (Integration)

- Update table: `inv_mast_x_integration`
- Tables in the SELECT: `inv_mast_x_integration`, `p21_integration_x_company`, `p21_integration`

| Field | Stored in | Basis |
|---|---|---|
| `sync_flag` | `inv_mast_x_integration.sync_flag` | column |
| `external_id` | `inv_mast_x_integration.external_id` | column |
| `name` | `p21_integration.name` | column |
| `company_id` | `p21_integration_x_company.company_id` | column |

| # | Label | table.column / expression |
|---|---|---|
| 4 | Sync To Integration | `inv_mast_x_integration.sync_flag` |
| 10 | Integration Name | `p21_integration.name` |
| 11 | Company ID | `p21_integration_x_company.company_id` |

### `TIMESTAMP.timestamp` (Audit Trail)

- Update table: `none (external source)`
- Mapped off-tab: the API could not select this tab (HTTP 400: Multiple tabs have a name or display text of TIMESTAMP.); SQL Information reads an instantiated datawindow whichever tab is active

| Field | Stored in | Basis |
|---|---|---|
| `date_created` | ? | no_sql |
| `date_last_modified` | ? | no_sql |
| `created_by` | ? | no_sql |
| `last_maintained_by` | ? | no_sql |
| `last_pricing_service_date` | ? | no_sql |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Date Created: | `date_created` |
| 2 | Created By: | `created_by` |
| 3 | Date Last Modified: | `date_last_modified` |
| 4 | Last Maintained By: | `last_maintained_by` |
| 5 | Last Pricing Service Date: | `last_pricing_service_date` |

### `TIMESTAMP.audit_trail` (Audit Trail)

- Update table: `p21_view_audit_trail_inv_mast_<id>`
- Tables in the SELECT: `p21_view_audit_trail_inv_mast_<id>`
- Mapped off-tab: the API could not select this tab (HTTP 400: Multiple tabs have a name or display text of TIMESTAMP.); SQL Information reads an instantiated datawindow whichever tab is active

| Field | Stored in | Basis |
|---|---|---|
| `column_description` | `p21_view_audit_trail_inv_mast_<id>.column_description` | probed |
| `old_value` | `p21_view_audit_trail_inv_mast_<id>.old_value` | probed |
| `new_value` | `p21_view_audit_trail_inv_mast_<id>.new_value` | probed |
| `date_created` | `p21_view_audit_trail_inv_mast_<id>.date_created` | probed |
| `created_by` | `p21_view_audit_trail_inv_mast_<id>.created_by` | probed |
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
| calc | Item ID / Location ID / Supplier ID | `"IF ((source_area_cd = 1763 and key1_cd = 'service_labor_uid'), item_id,  IF (source_area_cd = 950, key1_value,  IF (key2_cd = 'item_service_uid',  Item_id + ' / ALL / ALL',  IF ( key2_cd = 'lot_cd', key2_value,   IF ( Len(auxiliary_value) > 0 AND source_area_cd IN (1544, 1250, 2531), auxiliary_value,  IF (source_area_cd = 1314 and table_changed = 'inv_mast_strategic_pricing', item_id + '/' + key3_value + IF (IsNull(key2_value), '', '/' + auxiliary_value),  IF ( key1_cd = 'inv_mast_uid', item_id, key1_value ) + IF ( IsNull ( key2_value) AND source_area_cd <> 1314, '', ' / ' + IF ( key2_cd = 'inv_mast_uid', item_id, IF ( IsNull ( key2_value ), 'ALL', key2_value ) )  + IF ( IsNull (key3_value) AND source_area_cd <> 1314, '', ' / ' + IF ( key3_cd = 'inv_mast_uid', item_id, IF ( IsNull ( key3_value ), 'ALL', key3_value ) ) ) )  ) ) ) ) ) )"` |
| calc | 'Sub Line No | `` |

### `TABPAGE_17.invloclist` (Location List)

- Update table: `inv_loc`
- Tables in the SELECT: `inv_loc`, `company`, `inv_mast`, `location`, `product_group`, `tax_group_hdr`, `bin`, `bin_type`, `item_putaway_attribute`, `inv_mast_x_company`, `price_family`, `inv_loc_price_multiplier`

| Field | Stored in | Basis |
|---|---|---|
| `location_id` | `inv_loc.location_id` | probed |
| `stockable` | `inv_loc.stockable` | probed |
| `sellable` | `inv_loc.sellable` | probed |
| `buy` | `inv_loc.buy` | probed |
| `make` | `inv_loc.make` | probed |
| `requisition` | `inv_loc.requisition` | probed |
| `periods_to_supply_max` | `inv_loc.periods_to_supply_max` | probed |
| `periods_to_supply_min` | `inv_loc.periods_to_supply_min` | probed |
| `discontinued` | `inv_loc.discontinued` | probed |
| `delete_flag` | `inv_loc.delete_flag` | probed |
| `company_id` | `inv_loc.company_id` | probed |
| `company_name` | `company.company_name` | probed |
| `location_name` | `location.location_name` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Location ID | `inv_loc.location_id` |
| 2 | Company ID | `inv_loc.company_id` |
| 12 | Sellable | `inv_loc.sellable` |
| 13 | Company Name | `company.company_name` |
| 19 | Stockable | `inv_loc.stockable` |
| 48 | Location Name | `location.location_name` |
| 61 | Bin | `inv_loc.primary_bin` |
| 71 | Requisition | `inv_loc.requisition` |
| 78 | Buy | `inv_loc.buy` |
| 79 | Make | `inv_loc.make` |
| 88 | Discontinued | `inv_loc.discontinued` |
| 116 | Delete | `inv_loc.delete_flag` |

### `TABPAGE_18.inv_loc_detail` (Location Detail)

- Update table: `inv_loc`
- Tables in the SELECT: `inv_loc`, `company`, `inv_mast`, `location`, `product_group`, `tax_group_hdr`, `bin`, `bin_type`, `item_putaway_attribute`, `inv_mast_x_company`, `price_family`, `inv_loc_price_multiplier`

| Field | Stored in | Basis |
|---|---|---|
| `product_group_id` | `inv_loc.product_group_id` | probed |
| `sales_discount_group_id` | `inv_loc.sales_discount_group` | probed |
| `purchase_discount_group_id` | `inv_loc.purchase_discount_group` | probed |
| `tax_group_id` | `inv_loc.tax_group_id` | probed |
| `price_family_id` | `price_family.price_family_id` | probed |
| `pumpoff_item` | `inv_loc.pumpoff_item` | probed |
| `pumpoff_uom` | `inv_loc.pumpoff_uom` | probed |
| `default_in_oe` | `inv_loc.default_in_oe` | probed |
| `track_bins` | `inv_loc.track_bins` | probed |
| `bin` | `inv_loc.primary_bin` | probed |
| `allow_ds_discontinued_items` | `inv_loc.allow_ds_discontinued_items` | probed |
| `allow_sp_discontinued_items` | `inv_loc.allow_sp_discontinued_items` | probed |
| `default_shipment` | `inv_loc.default_shipment` | probed |
| `loc_item_type_cd` | `inv_loc.loc_item_type_cd` | probed |
| `main_bulk_location_flag` | `inv_loc.main_bulk_location_flag` | probed |
| `cardlock_product_id` | `inv_loc.cardlock_product_id` | probed |
| `iva_taxable_flag` | `inv_loc.iva_taxable_flag` | probed |
| `max_liability` | `inv_loc.max_liability` | probed |
| `max_transfer_qty` | `inv_loc.max_transfer_qty` | probed |
| `iqs_item_flag` | `inv_loc.iqs_item_flag` | probed |
| `slab_track_bins_flag` | `inv_loc.slab_track_bins_flag` | probed |
| `ta_rental_tax_group_id` | `inv_loc.ta_rental_tax_group_id` | probed |
| `deadstock_flag` | `inv_loc.deadstock_flag` | probed |
| `company_id` | `inv_loc.company_id` | probed |
| `location_id` | `inv_loc.location_id` | probed |
| `location_name` | `location.location_name` | probed |
| `purchase_discount_group_desc` | computed: `' '` | probed |
| `company_name` | `company.company_name` | probed |
| `sales_discount_group_desc` | computed: `' '` | probed |
| `price_family_desc` | `price_family.price_family_desc` | probed |
| `tax_group_description` | `tax_group_hdr.tax_group_description` | probed |
| `product_group_desc` | `product_group.product_group_desc` | probed |
| `computedummytosetfocus` | computed: `''` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Location ID: | `inv_loc.location_id` |
| 2 | Company ID: | `inv_loc.company_id` |
| 13 | Company Name | `company.company_name` |
| 22 | Product Group ID: | `inv_loc.product_group_id` |
| 26 | Product Group Desc | `product_group.product_group_desc` |
| 29 | Purchase Discount Group: | `inv_loc.purchase_discount_group` |
| 30 | Sales Discount Group: | `inv_loc.sales_discount_group` |
| 33 | Purchase Discount Group Desc | `purchase_discount_group_desc` |
| 34 | Sales Discount Group Desc | `sales_discount_group_desc` |
| 46 | Track Bins | `inv_loc.track_bins` |
| 48 | Location Name | `location.location_name` |
| 61 | Primary Bin: | `inv_loc.primary_bin` |
| 63 | Tax Group ID: | `inv_loc.tax_group_id` |
| 64 | Tax Group Description | `tax_group_hdr.tax_group_description` |
| 70 | Computedummytosetfocus | `computedummytosetfocus` |
| 77 | Deadstock Flag | `inv_loc.deadstock_flag` |
| 81 | Bin Type: | `bin_type.bin_type` |
| 82 | Putable Flag | `bin_type.putable_flag` |
| 83 | Pickable Flag | `bin_type.pickable_flag` |
| 89 | Allow Ds Discontinued Items | `inv_loc.allow_ds_discontinued_items` |
| 90 | Allow Sp Discontinued Items | `inv_loc.allow_sp_discontinued_items` |
| 127 | Price Family ID: | `price_family.price_family_id` |
| 128 | Price Family Desc | `price_family.price_family_desc` |
| 177 | Max Liability: | `inv_loc.max_liability` |
| 178 | Max Transfer Qty: | `inv_loc.max_transfer_qty` |

### `TABPAGE_19.tp_19_dw_19` (Tax)

- Update table: `tax_jurisdiction`
- Tables in the SELECT: `tax_jurisdiction`, `tax_group_line`, `tax_group_hdr`, `company`

| Field | Stored in | Basis |
|---|---|---|
| `company_id` | `tax_group_hdr.company_id` | column |
| `tax_group_id` | `tax_group_hdr.tax_group_id` | column |
| `company_name` | `company.company_name` | column |
| `tax_group_description` | `tax_group_hdr.tax_group_description` | column |
| `jurisdiction_id` | `tax_group_line.jurisdiction_id` | column |
| `jurisdiction_desc` | `tax_jurisdiction.jurisdiction_desc` | column |
| `tax_percentage` | `tax_jurisdiction.tax_percentage` | probed |
| `flat_fee_amount` | `tax_jurisdiction.flat_fee_amount` | column |
| `tax_group_line_taxable` | `tax_group_line.taxable` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Company ID: | `tax_group_hdr.company_id` |
| 2 | Tax Group ID: | `tax_group_hdr.tax_group_id` |
| 3 | Jurisdiction ID | `tax_group_line.jurisdiction_id` |
| 4 | Jurisdiction Description | `tax_jurisdiction.jurisdiction_desc` |
| 5 | Tax Percentage | `tax_jurisdiction.tax_percentage` |
| 9 | Company Name | `company.company_name` |
| 10 | Tax Group Description | `tax_group_hdr.tax_group_description` |
| 11 | Taxable | `tax_group_line.taxable` |
| 12 | Flat Rate Amount | `tax_jurisdiction.flat_fee_amount` |

### `TABPAGE_20.inv_loc_prices` (Price)

- Update table: `inv_loc`
- Tables in the SELECT: `inv_loc`, `company`, `inv_mast`, `location`, `product_group`, `tax_group_hdr`, `bin`, `bin_type`, `item_putaway_attribute`, `inv_mast_x_company`, `price_family`, `inv_loc_price_multiplier`

| Field | Stored in | Basis |
|---|---|---|
| `multiplier_1` | `inv_loc_price_multiplier.multiplier_1` | column |
| `price1` | `inv_loc.price1` | column |
| `multiplier_2` | `inv_loc_price_multiplier.multiplier_2` | column |
| `price2` | `inv_loc.price2` | column |
| `multiplier_3` | `inv_loc_price_multiplier.multiplier_3` | column |
| `price3` | `inv_loc.price3` | column |
| `multiplier_4` | `inv_loc_price_multiplier.multiplier_4` | probed |
| `price4` | `inv_loc.price4` | column |
| `multiplier_5` | `inv_loc_price_multiplier.multiplier_5` | column |
| `price5` | `inv_loc.price5` | column |
| `multiplier_6` | `inv_loc_price_multiplier.multiplier_6` | column |
| `price6` | `inv_loc.price6` | column |
| `multiplier_7` | `inv_loc_price_multiplier.multiplier_7` | column |
| `price7` | `inv_loc.price7` | column |
| `multiplier_8` | `inv_loc_price_multiplier.multiplier_8` | column |
| `price8` | `inv_loc.price8` | column |
| `multiplier_9` | `inv_loc_price_multiplier.multiplier_9` | column |
| `price9` | `inv_loc.price9` | column |
| `multiplier_10` | `inv_loc_price_multiplier.multiplier_10` | column |
| `price10` | `inv_loc.price10` | column |
| `computedummytosetfocus2` | computed: `(computed in the datawindow)` | dw_name |
| `location_id` | `inv_loc.location_id` | column |
| `company_id` | `inv_loc.company_id` | column |
| `c_unit_of_measure` | computed: `(computed in the datawindow)` | dw_name |
| `company_name` | `company.company_name` | column |
| `location_name` | `location.location_name` | column |
| `c_unit_size` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Location ID: | `inv_loc.location_id` |
| 2 | Company ID: | `inv_loc.company_id` |
| 13 | Company Name | `company.company_name` |
| 36 | Price 1: | `inv_loc.price1` |
| 37 | Price 2: | `inv_loc.price2` |
| 38 | Price 3: | `inv_loc.price3` |
| 39 | Price 4: | `inv_loc.price4` |
| 40 | Price 5: | `inv_loc.price5` |
| 41 | Price 6: | `inv_loc.price6` |
| 42 | Price 7: | `inv_loc.price7` |
| 43 | Price 8: | `inv_loc.price8` |
| 44 | Price 9: | `inv_loc.price9` |
| 45 | Price 10: | `inv_loc.price10` |
| 48 | Location Name | `location.location_name` |
| 49 | Unit Size: | `sales_price_unit_size` |
| 50 | Default Sales Pricing Unit: | `sales_price_unit` |
| 70 | Computedummytosetfocus2 | `computedummytosetfocus` |

### `TABPAGE_21.tp_21_dw_21` (Cost)

- Update table: `inv_loc`
- Tables in the SELECT: `inv_loc`, `company`, `inv_mast`, `location`, `product_group`, `tax_group_hdr`, `bin`, `bin_type`, `item_putaway_attribute`, `inv_mast_x_company`, `price_family`, `inv_loc_price_multiplier`

| Field | Stored in | Basis |
|---|---|---|
| `c_moving_average_cost` | computed: `(computed in the datawindow)` | dw_name |
| `c_standard_cost` | computed: `(computed in the datawindow)` | dw_name |
| `compute_last_rec_po_cost` | computed: `0.000000000` | alias |
| `location_id` | `inv_loc.location_id` | column |
| `c_unit_size` | computed: `(computed in the datawindow)` | dw_name |
| `c_unit_of_measure` | computed: `(computed in the datawindow)` | dw_name |
| `company_id` | `inv_loc.company_id` | column |
| `location_name` | `location.location_name` | probed |
| `company_name` | `company.company_name` | column |
| `next_due_in_po_date` | `inv_loc.next_due_in_po_date` | column |
| `c_scaled_landed_cost_amt_paid` | computed: `0.000000000` | alias |
| `c_scaled_landed_cost_amt` | computed: `0.000000000` | alias |
| `c_next_due_in_po_cost` | computed: `0.000000000` | alias |
| `cf_landed_cost_percentage` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Location ID: | `inv_loc.location_id` |
| 2 | Company ID: | `inv_loc.company_id` |
| 9 | Date Due In: | `inv_loc.next_due_in_po_date` |
| 13 | Company Name | `company.company_name` |
| 48 | Location Name | `location.location_name` |
| 57 | Standard Cost: | `compute_unkown1` |
| 58 | Moving Average Cost: | `compute_unkown2` |
| 59 | Default Purchase Pricing Unit: | `purchase_price_unit` |
| 60 | Unit Size: | `purchase_price_unit_size` |
| 69 | Last Received PO Cost: | `compute_last_rec_po_cost` |
| 80 | Next Due In PO Cost: | `c_next_due_in_po_cost` |
| 98 | Landed Cost: | `c_scaled_landed_cost_amt` |
| 133 | Actual Landed Cost: | `c_scaled_landed_cost_amt_paid` |
| calc | Landed Cost Percentage: | `if(compute_last_rec_po_cost > 0,  c_scaled_landed_cost_amt / compute_last_rec_po_cost, 0) * 100` |

### `TABPAGE_22.tp_22_dw_22` (Usage)

- Update table: `inv_loc`
- Tables in the SELECT: `inv_loc`, `company`, `inv_mast`, `location`, `product_group`, `tax_group_hdr`, `bin`, `bin_type`, `item_putaway_attribute`, `inv_mast_x_company`, `price_family`, `inv_loc_price_multiplier`

| Field | Stored in | Basis |
|---|---|---|
| `period_first_stocked` | `inv_loc.period_first_stocked` | column |
| `year_first_stocked` | `inv_loc.year_first_stocked` | column |
| `usage_lock` | `inv_loc.usage_lock` | column |
| `usage_lock_period` | `inv_loc.usage_lock_period` | column |
| `usage_lock_year` | `inv_loc.usage_lock_year` | column |
| `location_id` | `inv_loc.location_id` | column |
| `company_id` | `inv_loc.company_id` | column |
| `location_name` | `location.location_name` | column |
| `company_name` | `company.company_name` | column |
| `date_last_counted` | `inv_loc.date_last_counted` | column |
| `cycle_count_qty` | `inv_loc.cycle_count_qty` | column |
| `cycle_count_no` | `inv_loc.cycle_count_no` | column |
| `base_unit` | `inv_mast.base_unit` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Location Id | `inv_loc.location_id` |
| 2 | Company Id | `inv_loc.company_id` |
| 13 | Company Name | `company.company_name` |
| 48 | Location Name | `location.location_name` |
| 52 | Period First Stocked: | `inv_loc.period_first_stocked` |
| 53 | Year First Stocked: | `inv_loc.year_first_stocked` |
| 54 | Usage Lock | `inv_loc.usage_lock` |
| 55 | Usage Lock Period: | `inv_loc.usage_lock_period` |
| 56 | Usage Lock Year: | `inv_loc.usage_lock_year` |
| 73 | Date Last Counted: | `inv_loc.date_last_counted` |
| 183 | Cycle Count Number: | `inv_loc.cycle_count_no` |
| 184 | Cycle Count Quantity: | `inv_loc.cycle_count_qty` |
| 185 | Base Unit | `inv_mast.base_unit` |

### `TABPAGE_23.tp_23_dw_23` (Replenishment)

- Update table: `inv_loc`
- Tables in the SELECT: `inv_loc`, `company`, `inv_mast`, `location`, `product_group`, `tax_group_hdr`, `bin`, `bin_type`, `item_putaway_attribute`, `inv_mast_x_company`, `price_family`, `inv_loc_price_multiplier`

| Field | Stored in | Basis |
|---|---|---|
| `replenishment_location_id` | `inv_loc.replenishment_location` | probed |
| `replen_method` | `inv_loc.replenishment_method` | probed |
| `drp_item_flag` | `inv_loc.drp_item_flag` | column |
| `protected_stock_qty` | `inv_loc.protected_stock_qty` | column |
| `inv_min` | `inv_loc.inv_min` | column |
| `inv_max` | `inv_loc.inv_max` | column |
| `purchase_class_id` | `inv_loc.purchase_class` | probed |
| `putaway_rank` | `inv_loc.putaway_rank` | column |
| `item_putaway_attribute_id` | `item_putaway_attribute.item_putaway_attribute_id` | column |
| `periods_to_supply_min` | `inv_loc.periods_to_supply_min` | column |
| `periods_to_supply_max` | `inv_loc.periods_to_supply_max` | column |
| `safety_stock_type` | `inv_loc.safety_stock_type` | column |
| `service_level_measure` | `inv_loc.service_level_measure` | column |
| `service_level_pct_goal` | `inv_loc.service_level_pct_goal` | column |
| `safety_stock` | `inv_loc.safety_stock` | column |
| `deviation_lookback_pds` | `inv_loc.deviation_lookback_pds` | column |
| `deviation_mult_one_pd` | `inv_loc.deviation_mult_one_pd` | column |
| `deviation_mult_two_pd` | `inv_loc.deviation_mult_two_pd` | column |
| `deviation_mult_three_pd` | `inv_loc.deviation_mult_three_pd` | column |
| `min_safety_stock_days` | `inv_loc.min_safety_stock_days` | column |
| `max_safety_stock_days` | `inv_loc.max_safety_stock_days` | column |
| `crit_item_deviation_mult` | `inv_loc.crit_item_deviation_mult` | column |
| `crit_min_safety_stock_days` | `inv_loc.crit_min_safety_stock_days` | column |
| `crit_max_safety_stock_days` | `inv_loc.crit_max_safety_stock_days` | column |
| `critical_item_flag` | `inv_loc.critical_item_flag` | column |
| `months_in_season` | `inv_loc.months_in_season` | column |
| `demand_pattern_behavior_cd` | `inv_loc.demand_pattern_behavior_cd` | column |
| `demand_pattern_cd` | `inv_loc.demand_pattern_cd` | column |
| `pattern_like_location_id` | `inv_loc.pattern_like_location_id` | column |
| `c_behaves_like_item_id` | `inv_mast.item_id` | alias |
| `behaves_like_lock_flag` | `inv_loc.behaves_like_lock_flag` | column |
| `behaves_like_lock_period` | `inv_loc.behaves_like_lock_period` | column |
| `behaves_like_lock_year` | `inv_loc.behaves_like_lock_year` | column |
| `company_id` | `inv_loc.company_id` | probed |
| `location_id` | `inv_loc.location_id` | column |
| `location_name` | `location.location_name` | column |
| `company_company_name` | `company.company_name` | probed |
| `replenishment_location_name` | computed: `' '` | alias |
| `service_level` | computed: `0.000000000` | alias |
| `demand_pattern_evaluation_date` | `inv_loc.demand_pattern_evaluation_date` | column |
| `current_forecast_usage` | computed: `0.000000000` | alias |
| `pattern_manually_edited_flag` | `inv_loc.pattern_manually_edited_flag` | column |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Location ID: | `inv_loc.location_id` |
| 2 | Company ID: | `inv_loc.company_id` |
| 13 | Company Company Name | `company.company_name` |
| 16 | Min/Order Point: | `inv_loc.inv_min` |
| 17 | Max/Order Quantity: | `inv_loc.inv_max` |
| 18 | Safety Stock Days: | `inv_loc.safety_stock` |
| 20 | Replenishment Location: | `inv_loc.replenishment_location` |
| 21 | Number Of Periods In Season: | `inv_loc.months_in_season` |
| 23 | ABC Class: | `inv_loc.purchase_class` |
| 32 | Replenishment Methods: | `inv_loc.replenishment_method` |
| 47 | Replenishment Location Name | `replenishment_location_name` |
| 48 | Location Name | `location.location_name` |
| 62 | Current Forecast Usage: | `current_forecast_usage` |
| 65 | Service Level: | `inv_loc.service_level` |
| 75 | TPCx Protected Qty: | `inv_loc.protected_stock_qty` |
| 84 | EOQ Period Min: | `inv_loc.periods_to_supply_min` |
| 85 | EOQ Period Max: | `inv_loc.periods_to_supply_max` |
| 86 | Putaway Rank: | `inv_loc.putaway_rank` |
| 91 | Safety Stock In Terms of: | `inv_loc.safety_stock_type` |
| 92 | Customer Service Measure: | `inv_loc.service_level_measure` |
| 93 | Service Level % Goal: | `inv_loc.service_level_pct_goal` |
| 99 | Edited | `inv_loc.pattern_manually_edited_flag` |
| 100 | Demand Pattern Behavior Cd | `inv_loc.demand_pattern_behavior_cd` |
| 102 | Behaves Like Location ID: | `inv_loc.pattern_like_location_id` |
| 104 | Demand Pattern: | `inv_loc.demand_pattern_cd` |
| 105 | Behaves Like Item ID: | `c_behaves_like_item_id` |
| 106 | Behaves Like Lock Flag | `inv_loc.behaves_like_lock_flag` |
| 107 | Lock Period / Year: | `inv_loc.behaves_like_lock_period` |
| 108 | Behaves Like Lock Year | `inv_loc.behaves_like_lock_year` |
| 110 | Putaway Attribute: | `item_putaway_attribute.item_putaway_attribute_id` |
| 111 | Pattern Last Evaluation Date: | `inv_loc.demand_pattern_evaluation_date` |
| 171 | Drp Item Flag | `inv_loc.drp_item_flag` |
| 188 | Deviation Lookback Periods: | `inv_loc.deviation_lookback_pds` |
| 189 | 1 Period: | `inv_loc.deviation_mult_one_pd` |
| 190 | 2 Periods: | `inv_loc.deviation_mult_two_pd` |
| 191 | 3+ Periods: | `inv_loc.deviation_mult_three_pd` |
| 192 | Min Safety Stock Days: | `inv_loc.min_safety_stock_days` |
| 193 | Max Safety Stock Days: | `inv_loc.max_safety_stock_days` |
| 194 | Critical Item Deviation Multiplier: | `inv_loc.crit_item_deviation_mult` |
| 195 | Critical Min Safety Stock Days: | `inv_loc.crit_min_safety_stock_days` |
| 196 | Critical Max Safety Stock Days: | `inv_loc.crit_max_safety_stock_days` |
| 197 | Critical Item Flag | `inv_loc.critical_item_flag` |
| calc | Deviation Multiplier Cf | `"Deviation Multiplier for Usage > Forecast Past " + if(IsNull(deviation_lookback_pds), 0, deviation_lookback_pds) + " Periods"` |

### `TABPAGE_24.inv_loc_accounts` (GL Accounts)

- Update table: `inv_loc`
- Tables in the SELECT: `inv_loc`, `company`, `inv_mast`, `location`, `product_group`, `tax_group_hdr`, `bin`, `bin_type`, `item_putaway_attribute`, `inv_mast_x_company`, `price_family`, `inv_loc_price_multiplier`

| Field | Stored in | Basis |
|---|---|---|
| `gl_account_no` | `inv_loc.gl_account_no` | column |
| `revenue_account_no` | `inv_loc.revenue_account_no` | column |
| `cos_account_no` | `inv_loc.cos_account_no` | probed |
| `ta_rental_revenue_account_no` | `inv_loc.ta_rental_revenue_account_no` | column |
| `company_id` | `inv_loc.company_id` | column |
| `location_id` | `inv_loc.location_id` | column |
| `revenue_account_no_desc` | computed: `' '` | alias |
| `gl_account_no_desc` | computed: `' '` | probed |
| `cos_account_no_desc` | computed: `' '` | alias |
| `company_name` | `company.company_name` | column |
| `location_name` | `location.location_name` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Location ID: | `inv_loc.location_id` |
| 2 | Company ID: | `inv_loc.company_id` |
| 6 | '1if(requisition = "Y", "Requisition Expense Acct:", "Asset Account:")' | `inv_loc.gl_account_no` |
| 10 | Revenue Account: | `inv_loc.revenue_account_no` |
| 11 | COS Account: | `inv_loc.cos_account_no` |
| 13 | Company Name | `company.company_name` |
| 24 | Gl Account No Desc | `gl_account_no_desc` |
| 25 | Revenue Account No Desc | `revenue_account_no_desc` |
| 35 | Cos Account No Desc | `cos_account_no_desc` |
| 48 | Location Name | `location.location_name` |

### `SUPPLIER_X_LOCATION.supplier_x_location` (Supplier by Location)

- Update table: `inventory_supplier_x_loc`
- Tables in the SELECT: `inventory_supplier_x_loc`, `inventory_supplier`, `supplier`, `division`, `inv_loc`, `location`, `vendor_supplier`, `vendor_edi_transaction`

| Field | Stored in | Basis |
|---|---|---|
| `location_id` | `inventory_supplier_x_loc.location_id` | column |
| `supplier_id` | `inventory_supplier.supplier_id` | probed |
| `division_id` | `inventory_supplier.division_id` | column |
| `average_lead_time` | `inventory_supplier_x_loc.average_lead_time` | column |
| `loc_list_price` | `inventory_supplier_x_loc.loc_list_price` | column |
| `loc_cost` | `inventory_supplier_x_loc.loc_cost` | column |
| `primary_supplier` | `inventory_supplier_x_loc.primary_supplier` | column |
| `loc_contract_number` | `inventory_supplier_x_loc.loc_contract_number` | column |
| `row_status_flag` | `inventory_supplier_x_loc.row_status_flag` | column |
| `future_cost` | `inventory_supplier_x_loc.future_cost` | column |
| `effective_date` | `inventory_supplier_x_loc.effective_date` | column |
| `manual_lead_time` | `inventory_supplier_x_loc.manual_lead_time` | column |
| `supplier_name` | `supplier.supplier_name` | probed |
| `division_name` | `division.division_name` | column |
| `compute_1` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 3 | Location ID | `inventory_supplier_x_loc.location_id` |
| 4 | PrimarySupplier | `inventory_supplier_x_loc.primary_supplier` |
| 5 | AverageLead Time | `inventory_supplier_x_loc.average_lead_time` |
| 6 | Status | `inventory_supplier_x_loc.row_status_flag` |
| 10 | Supplier ID | `inventory_supplier.supplier_id` |
| 11 | Supplier Name | `supplier.supplier_name` |
| 12 | Division ID | `inventory_supplier.division_id` |
| 13 | Division Name | `division.division_name` |
| 21 | LocationList Price | `inventory_supplier_x_loc.loc_list_price` |
| 22 | LocationCost | `inventory_supplier_x_loc.loc_cost` |
| 23 | LocationContract Number | `inventory_supplier_x_loc.loc_contract_number` |
| 33 | Future Cost | `inventory_supplier_x_loc.future_cost` |
| 34 | EffectiveDate | `inventory_supplier_x_loc.effective_date` |
| 37 | PublishedLead Time | `inventory_supplier_x_loc.manual_lead_time` |

### `TABPAGE_LEADDATA.tabpage_leaddata` (Lead Data)

- Update table: `item_lead_time`
- Tables in the SELECT: `item_lead_time`, `inv_mast`, `location`, `supplier`

| Field | Stored in | Basis |
|---|---|---|
| `actual_lead_days` | `item_lead_time.actual_lead_days` | column |
| `item_id` | `inv_mast.item_id` | column |
| `location_id` | `item_lead_time.location_id` | column |
| `supplier_id` | `item_lead_time.supplier_id` | column |
| `location_name` | `location.location_name` | column |
| `supplier_name` | `supplier.supplier_name` | column |
| `item_desc` | `inv_mast.item_desc` | column |
| `po_no` | `item_lead_time.po_no` | column |
| `po_date` | `item_lead_time.po_date` | column |
| `receipt_number` | `item_lead_time.receipt_number` | column |
| `receipt_date` | `item_lead_time.receipt_date` | column |
| `estimated_lead_days` | `item_lead_time.estimated_lead_days` | column |
| `edited` | `item_lead_time.edited` | column |
| `compute_1` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 2 | Item ID: | `inv_mast.item_id` |
| 3 | Location ID: | `item_lead_time.location_id` |
| 4 | Supplier ID: | `item_lead_time.supplier_id` |
| 5 | Receipt Number | `item_lead_time.receipt_number` |
| 6 | Receipt Date | `item_lead_time.receipt_date` |
| 7 | PO Number | `item_lead_time.po_no` |
| 8 | PO Date | `item_lead_time.po_date` |
| 15 | Actual Lead Days | `item_lead_time.actual_lead_days` |
| 16 | Estimated Lead Days | `item_lead_time.estimated_lead_days` |
| 17 | Edited | `item_lead_time.edited` |
| 18 | Item Desc | `inv_mast.item_desc` |
| 19 | Location Name | `location.location_name` |
| 20 | Supplier Name | `supplier.supplier_name` |
| calc | Compute 1 | `If( IsNull(Abs( estimated_lead_days -  actual_lead_days ) /  estimated_lead_days ), 0,  Abs( estimated_lead_days -  actual_lead_days ) /  estimated_lead_days )` |

### `TABPAGE_PROCESSING.tabpage_processing` (Processing)

- Update table: `inv_loc_msp`
- Tables in the SELECT: `inv_loc`, `location`, `company`, `inv_loc_msp`, `process`

| Field | Stored in | Basis |
|---|---|---|
| `company_id` | `company.company_id` | column |
| `company_name` | `company.company_name` | column |
| `location_id` | `inv_loc.location_id` | column |
| `location_name` | `location.location_name` | column |
| `receipt_process_flag` | `inv_loc_msp.receipt_process_flag` | column |
| `receipt_process_code` | `process.process_code` | probed |
| `receipt_process_name` | `process.process_name` | probed |
| `compute_1` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 3 | Location ID | `inv_loc_msp.location_id` |
| 4 | Create QA/QCProcess Upon Receipt | `inv_loc_msp.receipt_process_flag` |
| 10 | Location Name | `location.location_name` |
| 11 | Company ID | `company.company_id` |
| 12 | Company Name | `company.company_name` |
| 13 | Route Code | `process.process_code` |
| 14 | Route Name | `process.process_name` |

### `ITEM_VMI.item_vmi` (VMI)

- Update table: `inventory_supplier_x_loc`
- Tables in the SELECT: `inventory_supplier_x_loc`, `inventory_supplier`, `supplier`, `division`, `inv_loc`, `location`, `vendor_supplier`, `vendor_edi_transaction`

| Field | Stored in | Basis |
|---|---|---|
| `override_vmi_status` | `inventory_supplier_x_loc.override_vmi_status` | column |
| `override_vmi_status_flag` | `inventory_supplier_x_loc.override_vmi_status_flag` | column |
| `override_beg_date` | `inventory_supplier_x_loc.override_beg_date` | column |
| `override_end_date` | `inventory_supplier_x_loc.override_end_date` | column |
| `vmi_status` | `inventory_supplier_x_loc.vmi_status` | probed |
| `vmi_last_send_date` | `inventory_supplier_x_loc.vmi_last_send_date` | column |
| `location_id` | `inventory_supplier_x_loc.location_id` | column |
| `supplier_id` | `inventory_supplier.supplier_id` | column |
| `location_name` | `location.location_name` | column |
| `supplier_name` | `supplier.supplier_name` | column |

| # | Label | table.column / expression |
|---|---|---|
| 3 | Location ID: | `inventory_supplier_x_loc.location_id` |
| 10 | Supplier ID: | `inventory_supplier.supplier_id` |
| 11 | Supplier Name | `supplier.supplier_name` |
| 18 | VMI Status: | `inventory_supplier_x_loc.vmi_status` |
| 25 | Override Vmi Status Flag | `inventory_supplier_x_loc.override_vmi_status_flag` |
| 26 | Start Date: | `inventory_supplier_x_loc.override_beg_date` |
| 27 | End Date: | `inventory_supplier_x_loc.override_end_date` |
| 28 | 852 Last Send Date: | `inventory_supplier_x_loc.vmi_last_send_date` |
| 29 | Location Name | `location.location_name` |
| 30 | Override VMI Status: | `inventory_supplier_x_loc.override_vmi_status` |

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
| `LINE_ITEM_TERMS` | Line Item Terms | `line_item_terms` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_PACKAGETYPE` | Package Type | `tabpage_packagetype` | SQL Information is disabled for this datawindow (Menu m_sqlinformation is not enabled) |
| `ITEM_SERVICE` | Service | `item_service` | datawindow never instantiated (tab not enabled) |
| `ITEM_SERVICE` | Service | `item_service_dw_2` | datawindow never instantiated (tab not enabled) |
| `ITEM_SERVICE_PART_LIST` | Parts List | `item_service_part_list` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_LABOR` | Labor | `tabpage_labor` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_ALARMCODE` | Alarm Code | `tabpage_alarmcode` | datawindow never instantiated (tab not enabled) |
| `ITEM_SERVICE_CONTRACT` | Contract Detail | `item_service_contract` | datawindow never instantiated (tab not enabled) |
| `SUPPLIER_PRICING_SERVICE` | Supplier Pricing Service | `supplier_pricing_service` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_CONTROLLEDSUBSTANCE` | Controlled Substance | `tabpage_controlledsubstance` | datawindow never instantiated (tab not enabled) |
| `SUPPLIER_X_LOC_PRICING_SERVICE` | Supplier Pricing Service | `supplier_x_loc_pricing_service` | datawindow never instantiated (tab not enabled) |
| `TIMESTAMPDETAIL` | Timestamp | `timestampdetail_dw_audittrail` | datawindow never instantiated (tab not enabled) |
