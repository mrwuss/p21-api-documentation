# Production Order Entry (`ProductionOrder`)

- Window class: `w_production_order_sheet`; menu class: `m_productionorderentry`
- Tabs: 56; datawindows mapped: 23; unreachable entries: 40

## Tab overview

| Tab | Caption | Datawindows mapped | Tables in the SELECT |
|---|---|---|---|
| `TABPAGE_1` | Production Order | `tp_1_dw_1` | address, company, location, prod_order_hdr, prod_pick_ticket_hdr, system_setting, users |
| `TP_PICKTICKET` | Pick Ticket | `pick_ticket` | inv_mast, prod_order_hdr, prod_order_line, prod_order_line_component, prod_pick_ticket_detail, prod_pick_ticket_hdr, service_labor |
| `DOCUMENT_LINK` | Document Links | `document_link` | document_link, document_link_area, document_link_entity_req, inv_mast |
| `PROD_ORDER_HDR_NOTE_TAB` | Production Order Notes | `prod_order_hdr_note_tab` | code_p21, note, note_area, notepad_class |
| `COMPLETION` | Processing | `completion` | code_p21, inv_mast, prod_order_line, prod_order_line_process |
| `TIMESTAMP` | Audit Trail | `timestamp`, `audit_trail` | p21_view_audit_trail_prod_order_hdr_<id> |
| `TABPAGE_17` | Assembly Items | `tp_17_dw_17` | assembly_hdr, inv_loc, inv_mast, item_revision, oe_hdr, oe_hdr_progress_billing, oe_line, process_x_transaction, process_x_transaction_detail, prod_order_hdr, prod_order_line, prod_order_line_link, prod_order_line_process, revision_transaction |
| `TABPAGE_18` | Components | `components` | address, assembly_hdr, code_p21, inv_loc, inv_loc_stock_status, inv_mast, inv_mast_assem_info, item_revision, location, operation, p21_view_contacts, p21_view_getrevisionlotquantity, prod_line_component_labor, prod_order_hdr, prod_order_line, prod_order_line_component, prod_order_line_link, prodorder_department, revision_transaction, service_labor, system_setting, work_center, work_center_x_service_labor |
| `TABPAGE_19` | Component Detail | `componentdetail` | address, assembly_hdr, code_p21, inv_loc, inv_loc_stock_status, inv_mast, inv_mast_assem_info, item_revision, location, operation, p21_view_contacts, p21_view_getrevisionlotquantity, prod_line_component_labor, prod_order_hdr, prod_order_line, prod_order_line_component, prod_order_line_link, prodorder_department, revision_transaction, service_labor, system_setting, work_center, work_center_x_service_labor |
| `TABPAGE_20` | Assembly Item Options | `tp_20_dw_20` | assembly_hdr, inv_loc, inv_mast, prod_order_line |
| `TABPAGE_TRANSACTIONS_TO_ASSIGN` | Transactions To Assign | `tabpage_transactions_to_assign` | item_revision, prod_order_hdr, prod_order_line, prod_order_line_link, revision_transaction |
| `TABPAGE_ASSEMBLY_ITEM_NOTES` | Assembly Item Notes | `tabpage_assembly_item_notes` | inv_mast, note, note_area, notepad_class |
| `DOCUMENT_LINK_DETAIL` | Document Links | `document_link_detail_detail` | document_link, document_link_area, document_link_entity_req, inv_mast |
| `TP_ASSEMBLY_DETAILS` | Assembly Details | `tp_assembly_details` | assembly_hdr, inv_loc, inv_mast, item_revision, oe_hdr, oe_hdr_progress_billing, oe_line, process_x_transaction, process_x_transaction_detail, prod_order_hdr, prod_order_line, prod_order_line_link, prod_order_line_process, revision_transaction |
| `TP_ASSEMBLYCOSTS` | Costs | `tp_assemblycosts` | assembly_hdr, inv_loc, inv_mast, item_revision, oe_hdr, oe_hdr_progress_billing, oe_line, process_x_transaction, process_x_transaction_detail, prod_order_hdr, prod_order_line, prod_order_line_link, prod_order_line_process, revision_transaction |
| `TP_FREIGHTCOSTS` | Freight Costs | `tp_freightcosts` | inv_mast, prod_order_line_comp_frght, prod_order_line_component |
| `PROD_ORDER_LINE_NOTE_TAB` | Production Order Line Notes | `prod_order_line_note_tab` | code_p21, note, note_area, notepad_class |
| `TABPAGE_OELINENOTEASSEMBLY` | Order Line Assembly Notes | `tabpage_oelinenoteassembly` | note_area, notepad_class, oe_line, oe_line_notepad, prod_order_line, prod_order_line_link |
| `TABPAGE_OELINENOTECOMPONENT` | Order Line Component Notes | `tabpage_oelinenotecomponent` | note_area, notepad_class, oe_line, oe_line_notepad, prod_ord_line_compnt_x_oe_line, prod_order_line_component |
| `TABPAGE_STOCK` | Stock Avail | `stock_avail`, `checkbox` | address, inv_loc, inv_loc_stock_status, inv_mast, item_uom, location, po_hdr, po_line, transfer_days, vessel_receipts_hdr, vessel_receipts_line |
| `TIMESTAMPDETAIL` | Timestamp | `timestampdetail` |  |

## Datawindows

### `TABPAGE_1.tp_1_dw_1` (Production Order)

- Update table: `prod_order_hdr`
- Tables in the SELECT: `prod_pick_ticket_hdr`, `prod_order_hdr`, `company`, `address`, `users`, `location`, `system_setting`

| Field | Stored in | Basis |
|---|---|---|
| `prod_order_number` | `prod_order_hdr.prod_order_number` | probed |
| `source_loc_id` | `prod_order_hdr.source_location_id` | probed |
| `order_date` | `prod_order_hdr.order_date` | probed |
| `required_date` | `prod_order_hdr.required_date` | probed |
| `expedite_date` | `prod_order_hdr.expedite_date` | probed |
| `expected_completion_date` | `prod_order_hdr.expected_completion_date` | probed |
| `release_date` | `prod_order_hdr.release_date` | probed |
| `prod_order_hdr_comment` | `prod_order_hdr.comment` | probed |
| `company_id` | `prod_order_hdr.company_id` | probed |
| `assemble_disassemble` | `prod_order_hdr.assemble_disassemble` | probed |
| `approved` | `prod_order_hdr.approved` | probed |
| `process_doclinks` | computed: `'Y'` | probed |
| `cancel` | `prod_order_hdr.cancel` | probed |
| `include_associated_prod_orders` | `system_setting.value` | probed |
| `create_auto_transfer` | `prod_order_hdr.create_auto_transfer` | probed |
| `print_form` | computed: `'N'` | probed |
| `priority` | `prod_order_hdr.priority` | probed |
| `fax_form` | computed: `'N'` | probed |
| `c_email_form` | computed: `'N'` | probed |
| `print_pick_ticket` | computed: `'N'` | probed |
| `fax_pick_ticket` | computed: `'N'` | probed |
| `email_pick_ticket` | computed: `'N'` | probed |
| `inventory_location_id` | `prod_order_hdr.inventory_location_id` | probed |
| `entered_by` | `prod_order_hdr.entered_by` | probed |
| `company_name` | `company.company_name` | probed |
| `source_loc_name` | `address.name` | probed |
| `taker_name` | `users.name` | probed |
| `complete` | `prod_order_hdr.complete` | probed |
| `drawings_complete` | `prod_order_hdr.drawings_complete` | probed |
| `associated_location_name` | `location.location_name` | probed |
| `printed` | `prod_order_hdr.printed` | probed |
| `actual_freight_cost` | `prod_order_hdr.actual_freight_cost` | probed |
| `estimated_freight_cost` | `prod_order_hdr.estimated_freight_cost` | probed |
| `status` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Production Order Number: | `prod_order_hdr.prod_order_number` |
| 2 | Company ID: | `prod_order_hdr.company_id` |
| 3 | Make Loc: | `prod_order_hdr.source_location_id` |
| 4 | Order Date: | `prod_order_hdr.order_date` |
| 5 | Customer Required Date: | `prod_order_hdr.required_date` |
| 6 | Expected Completion Date | `prod_order_hdr.expected_completion_date` |
| 7 | Approved | `prod_order_hdr.approved` |
| 8 | Complete | `prod_order_hdr.complete` |
| 10 | Cancel | `prod_order_hdr.cancel` |
| 11 | Comment: | `prod_order_hdr.comment` |
| 12 | Scheduler: | `prod_order_hdr.entered_by` |
| 16 | Printed: | `prod_order_hdr.printed` |
| 20 | Company Name | `company.company_name` |
| 21 | Source Loc Name | `address.name` |
| 22 | Taker Name | `users.name` |
| 23 | Print Form | `compute_print_form` |
| 24 | Create Auto Transfer | `prod_order_hdr.create_auto_transfer` |
| 25 | Fax Form | `fax_form` |
| 26 | Total Disassemby Cost: | `cost_to_disassemble` |
| 27 | C Email Form | `c_email_form` |
| 30 | Print Pick Ticket | `print_pick_ticket` |
| 31 | Fax Pick Ticket | `fax_pick_ticket` |
| 32 | Email Pick Ticket | `email_pick_ticket` |
| 35 | Inventory Location ID: | `prod_order_hdr.inventory_location_id` |
| 36 | Associated Location Name | `associated_location.location_name` |
| 37 | Expedite Date: | `prod_order_hdr.expedite_date` |
| 38 | Estimated Freight Cost: | `prod_order_hdr.estimated_freight_cost` |
| 39 | Actual Freight Cost: | `prod_order_hdr.actual_freight_cost` |
| 44 | Drawings Complete: | `prod_order_hdr.drawings_complete` |
| 45 | Process Doclinks | `process_doclinks` |
| calc | Status: | `if (cancel = 'Y' ,'Cancelled',if(complete = 'Y','Completed',if(prod_pick_ticket_printed = 'Y', 'Pick Ticket(s) Printed', if(printed='Y','Production Order Form Printed',if(approved='Y','Approved','Unapproved')))))` |

### `TP_PICKTICKET.pick_ticket` (Pick Ticket)

- Update table: `prod_order_hdr`
- Tables in the SELECT: `prod_order_hdr`, `prod_pick_ticket_hdr`, `prod_pick_ticket_detail`, `inv_mast`, `prod_order_line`, `prod_order_line_component`, `service_labor`

| Field | Stored in | Basis |
|---|---|---|
| `prod_pick_ticket_number` | `prod_pick_ticket_hdr.prod_pick_ticket_number` | column |
| `item_id` | `inv_mast.item_id` | probed |
| `item_desc` | `inv_mast.item_desc` | probed |
| `unit_of_measure` | `prod_pick_ticket_detail.unit_of_measure` | column |
| `status` | computed: `CASE WHEN prod_pick_ticket_detail.sku_qty_picked =0 AND prod_pick_ticket_detail.sku_qty_confirmed =0 AND prod_pick_ticket_detail.sku_qty_completed = 0 THEN 'Cancelled' WHEN prod_pick_ticket_hdr.row_status_flag = 1268 THEN 'Picked' WHEN prod_pick_ticket_detail.sku_qty_picked >0 AND prod_pick_ticket_detail.sku_qty_confirmed =0 AND prod_pick_ticket_detail.sku_qty_completed = 0 THEN 'Printed' WHEN prod_pick_ticket_detail.sku_qty_picked >0 AND prod_pick_ticket_detail.sku_qty_confirmed >0 AND prod_pick_ticket_detail.sku_qty_completed = 0 THEN 'Staged' WHEN prod_pick_ticket_detail.sku_qty_picked >0 AND prod_pick_ticket_detail.sku_qty_confirmed >0 AND prod_pick_ticket_detail.sku_qty_completed > 0 THEN 'Picking' WHEN prod_pick_ticket_detail.sku_qty_picked >0 AND prod_pick_ticket_detail.sku_qty_confirmed =0 AND prod_pick_ticket_detail.sku_qty_completed > 0 THEN 'Picked' ELSE 'Picking' END` | alias |
| `unit_ordered` | computed: `(computed in the datawindow)` | probed |
| `unit_allocated` | computed: `(computed in the datawindow)` | probed |
| `unit_staged` | computed: `(computed in the datawindow)` | probed |
| `unit_picked` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Pick Ticket Number | `prod_pick_ticket_hdr.prod_pick_ticket_number` |
| 2 | Item ID | `inv_mast.item_id` |
| 3 | Item Desc | `inv_mast.item_desc` |
| 4 | UOM | `prod_pick_ticket_detail.unit_of_measure` |
| 9 | Status | `status` |
| calc | Qty Requested | `if(unit_size <=0, 0 , qty_requested /unit_size )` |
| calc | Qty On Pick Ticket | `if(unit_size <=0, 0 ,  sku_qty_picked /unit_size )` |
| calc | Qty Confirmed | `if(unit_size <=0, 0 , sku_qty_confirmed/unit_size )` |
| calc | Qty Completed | `if(unit_size <=0, 0 , sku_qty_completed/unit_size )` |

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

### `PROD_ORDER_HDR_NOTE_TAB.prod_order_hdr_note_tab` (Production Order Notes)

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

### `COMPLETION.completion` (Processing)

- Update table: `prod_order_line_process`
- Tables in the SELECT: `prod_order_line_process`, `prod_order_line`, `inv_mast`, `code_p21`

| Field | Stored in | Basis |
|---|---|---|
| `item_id` | `inv_mast.item_id` | column |
| `line_number` | `prod_order_line.line_number` | column |
| `sequence_number` | `prod_order_line_process.sequence_number` | column |
| `date_created` | `prod_order_line_process.date_created` | column |
| `qty_completed` | `prod_order_line_process.qty_completed` | column |
| `material_cost` | `prod_order_line_process.material_cost` | column |
| `labor_cost` | `prod_order_line_process.labor_cost` | column |
| `labor_cost_indirect` | `prod_order_line_process.labor_cost_indirect` | column |
| `other_charge_cost` | `prod_order_line_process.other_charge_cost` | column |
| `freight_cost` | `prod_order_line_process.freight_cost` | column |
| `process_cost` | `prod_order_line_process.process_cost` | column |
| `additional_material` | `prod_order_line_process.additional_material` | column |
| `additional_labor` | `prod_order_line_process.additional_labor` | column |
| `additional_labor_indirect` | `prod_order_line_process.additional_labor_indirect` | column |
| `additional_other_charge` | `prod_order_line_process.additional_other_charge` | column |
| `additional_freight` | `prod_order_line_process.additional_freight` | column |
| `cf_rowindicator` | computed: `(computed in the datawindow)` | dw_name |
| `cf_production_cost` | computed: `(computed in the datawindow)` | dw_name |
| `cf_adjusted_production_cost` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |
| `cf_qty_completed_total` | computed: `(computed in the datawindow)` | dw_name |
| `cf_material_cost_total` | computed: `(computed in the datawindow)` | dw_name |
| `cf_labor_cost_total` | computed: `(computed in the datawindow)` | dw_name |
| `cf_labor_cost_indirect_total` | computed: `(computed in the datawindow)` | dw_name |
| `cf_other_charge_cost_total` | computed: `(computed in the datawindow)` | dw_name |
| `cf_freight_cost_total` | computed: `(computed in the datawindow)` | dw_name |
| `cf_process_cost_total` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_production_cost` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_additional_material` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_additional_labor` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_additional_labor_indirect` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_additional_other_charge` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_additional_freight` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_adjusted_production_cost` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 3 | CompletionNumber | `prod_order_line_process.sequence_number` |
| 4 | QuantityCompleted | `prod_order_line_process.qty_completed` |
| 5 | Material Cost | `prod_order_line_process.material_cost` |
| 6 | DirectLabor Cost | `prod_order_line_process.labor_cost` |
| 7 | Freight Cost | `prod_order_line_process.freight_cost` |
| 8 | OtherCharge Cost | `prod_order_line_process.other_charge_cost` |
| 9 | Process Cost | `prod_order_line_process.process_cost` |
| 11 | CompletionDate | `prod_order_line_process.date_created` |
| 15 | Additional DirectLabor Cost | `prod_order_line_process.additional_labor` |
| 16 | AdditionalFreight Cost | `prod_order_line_process.additional_freight` |
| 17 | AdditionalMaterial Cost | `prod_order_line_process.additional_material` |
| 18 | Additional OtherCharge Cost | `prod_order_line_process.additional_other_charge` |
| 19 | Line Number | `prod_order_line.line_number` |
| 20 | Assembly Item ID | `inv_mast.item_id` |
| 25 | IndirectLabor Cost | `prod_order_line_process.labor_cost_indirect` |
| 26 | Additional IndirectLabor Cost | `prod_order_line_process.additional_labor_indirect` |
| calc | Total Production Cost | `material_cost + labor_cost + labor_cost_indirect +  other_charge_cost + freight_cost + process_cost` |
| calc | Adjusted Production Cost | `IF(IF(IsNull(additional_labor), 0, additional_labor) <> 0 OR IF(IsNull(additional_labor_indirect), 0, additional_labor_indirect) <> 0 OR IF(IsNull(additional_freight), 0, additional_freight) <> 0 OR IF(IsNull(additional_material), 0, additional_material) <> 0 OR IF(IsNull(additional_other_charge), 0, additional_other_charge) <> 0, cf_production_cost + IF(IsNull(additional_material), 0, additional_material) + IF(IsNull(additional_labor), 0, additional_labor) + IF(IsNull(additional_labor_indirect), 0, additional_labor_indirect) + IF(IsNull(additional_other_charge), 0, additional_other_charge), 0) + IF(IsNull(additional_freight), 0, additional_freight)` |

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

### `TIMESTAMP.audit_trail` (Audit Trail)

- Update table: `p21_view_audit_trail_prod_order_hdr_<id>`
- Tables in the SELECT: `p21_view_audit_trail_prod_order_hdr_<id>`

| Field | Stored in | Basis |
|---|---|---|
| `line_no` | `p21_view_audit_trail_prod_order_hdr_<id>.line_no` | probed |
| `item_id` | `p21_view_audit_trail_prod_order_hdr_<id>.item_id` | probed |
| `column_description` | `p21_view_audit_trail_prod_order_hdr_<id>.column_description` | probed |
| `old_value` | `p21_view_audit_trail_prod_order_hdr_<id>.old_value` | probed |
| `new_value` | `p21_view_audit_trail_prod_order_hdr_<id>.new_value` | probed |
| `date_created` | `p21_view_audit_trail_prod_order_hdr_<id>.date_created` | probed |
| `created_by` | `p21_view_audit_trail_prod_order_hdr_<id>.created_by` | probed |
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
| 21 | 'Item IDIF (source_area_cd | `950, 'Process', IF(source_area_cd = 1302, 'Component ID', 'Item ID'))' = item_id` |
| calc | Production Order Number | `"IF ((source_area_cd = 1763 and key1_cd = 'service_labor_uid'), item_id,  IF (source_area_cd = 950, key1_value,  IF (key2_cd = 'item_service_uid',  Item_id + ' / ALL / ALL',  IF ( key2_cd = 'lot_cd', key2_value,   IF ( Len(auxiliary_value) > 0 AND source_area_cd IN (1544, 1250, 2531), auxiliary_value,  IF (source_area_cd = 1314 and table_changed = 'inv_mast_strategic_pricing', item_id + '/' + key3_value + IF (IsNull(key2_value), '', '/' + auxiliary_value),  IF ( key1_cd = 'inv_mast_uid', item_id, key1_value ) + IF ( IsNull ( key2_value) AND source_area_cd <> 1314, '', ' / ' + IF ( key2_cd = 'inv_mast_uid', item_id, IF ( IsNull ( key2_value ), 'ALL', key2_value ) )  + IF ( IsNull (key3_value) AND source_area_cd <> 1314, '', ' / ' + IF ( key3_cd = 'inv_mast_uid', item_id, IF ( IsNull ( key3_value ), 'ALL', key3_value ) ) ) )  ) ) ) ) ) )"` |
| calc | 'Sub Line No | `` |

### `TABPAGE_17.tp_17_dw_17` (Assembly Items)

- Update table: `prod_order_line`
- Tables in the SELECT: `prod_order_line`, `inv_mast`, `prod_order_hdr`, `inv_loc`, `assembly_hdr`, `oe_hdr`, `oe_hdr_progress_billing`, `oe_line`, `prod_order_line_link`, `revision_transaction`, `item_revision`, `process_x_transaction`, `process_x_transaction_detail`, `prod_order_line_process`

| Field | Stored in | Basis |
|---|---|---|
| `assembly_item_id` | `inv_mast.item_id` | probed |
| `assembly_item_desc` | `inv_mast.item_desc` | probed |
| `trans_revision_level` | `item_revision.revision_level` | alias |
| `process_cd` | `process_x_transaction.process_cd` | column |
| `qty_to_make` | `prod_order_line.qty_to_make` | column |
| `required_date` | `prod_order_line.required_date` | column |
| `expedite_date` | `prod_order_line.expedite_date` | column |
| `hose_overall_length` | `prod_order_line.hose_overall_length` | column |
| `hose_uom` | `prod_order_line.hose_uom` | column |
| `deposit_bin` | `prod_order_line.deposit_bin` | probed |
| `cancel` | `prod_order_line.cancel` | probed |
| `design_complete_flag` | `prod_order_line.design_complete_flag` | probed |
| `operation_sequence_set` | `prod_order_line.operation_sequence_set` | column |
| `qty_completed` | `prod_order_line.qty_completed` | column |
| `completed` | `prod_order_line.completed` | column |
| `c_expected_completion_date` | computed: `cast(NULL AS datetime)` | alias |
| `compute_1` | `inv_mast.item_id` | position |
| `item_id` | `inv_mast.item_id` | column |
| `qty_allocated` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Assembly Item ID | `inv_mast.item_id` |
| 4 | Qty To Make | `prod_order_line.qty_to_make` |
| 5 | Qty Completed | `prod_order_line.qty_completed` |
| 6 | Complete | `prod_order_line.completed` |
| 7 | Cancel | `prod_order_line.cancel` |
| 11 | Assembly Item Desc | `inv_mast.item_desc` |
| 32 | Deposit Bin | `prod_order_line.deposit_bin` |
| 36 | Overall Length | `prod_order_line.hose_overall_length` |
| 37 | UOM | `prod_order_line.hose_uom` |
| 42 | Expected Date | `c_expected_completion_date` |
| 46 | Required Date | `prod_order_line.required_date` |
| 47 | Expedite Date | `prod_order_line.expedite_date` |
| 61 | Route Code | `process_x_transaction.process_cd` |
| 63 | Design Complete | `prod_order_line.design_complete_flag` |

### `TABPAGE_18.components` (Components)

- Update table: `prod_order_line_component`
- Tables in the SELECT: `prod_order_line_component`, `inv_mast`, `prod_order_line`, `prod_order_hdr`, `address`, `inv_loc`, `location`, `inv_loc_stock_status`, `inv_mast_assem_info`, `service_labor`, `code_p21`, `operation`, `prod_line_component_labor`, `revision_transaction`, `item_revision`, `p21_view_getrevisionlotquantity`, `system_setting`, `assembly_hdr`, `prod_order_line_link`, `work_center`, `work_center_x_service_labor`, `prodorder_department`, `p21_view_contacts`

| Field | Stored in | Basis |
|---|---|---|
| `item_id_service_labor_id` | computed: `COALESCE(service_labor.service_labor_id, inv_mast.item_id)` | probed |
| `trans_revision_level` | `item_revision.revision_level` | alias |
| `source_location_id` | `prod_order_line_component.source_location_id` | column |
| `operation_cd` | `operation.operation_cd` | column |
| `qty_needed` | `prod_order_line_component.qty_needed` | column |
| `cut_length` | `prod_order_line_component.component_cut_length` | probed |
| `loose_ship_flag` | `prod_order_line_component.loose_ship_flag` | alias |
| `qty_per_assembly` | `prod_order_line_component.qty_per_assembly` | column |
| `estimated_labor_cost` | `prod_line_component_labor.estimated_labor_cost` | column |
| `estimated_material_cost` | `prod_line_component_labor.estimated_material_cost` | probed |
| `unit_of_measure` | `prod_order_line_component.unit_of_measure` | column |
| `disposition` | `prod_order_line_component.disposition` | column |
| `units_used` | computed: `0.0000` | alias |
| `operation_start_date` | `prod_order_line_component.operation_start_date` | column |
| `operation_end_date` | `prod_order_line_component.operation_end_date` | column |
| `concurrent_capacity` | `prod_order_line_component.concurrent_capacity` | probed |
| `technician_id` | `prod_order_line_component.technician_id` | column |
| `previous_operation` | `prod_order_line_component.previous_operation` | column |
| `operation_sequence` | `prod_order_line_component.operation_sequence` | column |
| `next_operation` | `prod_order_line_component.next_operation` | column |
| `c_placeholder` | computed: `' '` | alias |
| `item_id` | `inv_mast.item_id` | column |
| `item_desc` | `inv_mast.item_desc` | probed |
| `cut_length_edited_flag` | `prod_order_line_component.cut_length_edited_flag` | column |
| `units_requested` | `prod_order_line_component.units_requested` | column |
| `complete` | `prod_order_line_component.complete` | column |
| `cf_expandableindicator` | computed: `(computed in the datawindow)` | dw_name |
| `uom_qty_available` | computed: `(computed in the datawindow)` | probed |
| `pricing_unit` | computed: `(computed in the datawindow)` | probed |
| `pricing_unit_size` | computed: `(computed in the datawindow)` | probed |
| `temporary_item` | computed: `(computed in the datawindow)` | probed |
| `source_loc_id` | computed: `(computed in the datawindow)` | probed |
| `lot_bill` | computed: `(computed in the datawindow)` | probed |
| `cf_alloweditestimatedmaterialcost` | computed: `(computed in the datawindow)` | dw_name |
| `cf_progressbill` | computed: `(computed in the datawindow)` | dw_name |
| `calc_units_requested` | computed: `(computed in the datawindow)` | probed |
| `cf_laborcomponentscount` | computed: `(computed in the datawindow)` | dw_name |
| `cf_sumoperationsequence` | computed: `(computed in the datawindow)` | dw_name |
| `sum_qty_used` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 6 | SourceLocation | `prod_order_line_component.source_location_id` |
| 12 | UOM | `prod_order_line_component.unit_of_measure` |
| 14 | Disp | `prod_order_line_component.disposition` |
| 24 | Item Desc | `inv_mast.item_desc` |
| 32 | QuantityRequested | `prod_order_line_component.units_requested` |
| 34 | QuantityUsed | `units_used` |
| 35 | Qty PerAssembly | `prod_order_line_component.qty_per_assembly` |
| 39 | Complete | `prod_order_line_component.complete` |
| 62 | Cut Length | `prod_order_line_component.component_cut_length` |
| 63 | Edited | `prod_order_line_component.cut_length_edited_flag` |
| 68 | QuantityNeeded | `prod_order_line_component.qty_needed` |
| 84 | Operation | `operation.operation_cd` |
| 89 | Est MaterialCost | `prod_line_component_labor.estimated_material_cost` |
| 102 | LooseShip | `prod_order_line_component.loose_ship_flag` |
| 106 | Item ID | `item_id_service_labor_id` |
| calc | Cf Expandableindicator | `if(  sub_assembly = "Y" or  sub_assembly = 'S', '+', '')` |
| calc | Quantity Available | `If(qty_available / unit_size < 0 , 0, qty_available / unit_size)` |

### `TABPAGE_19.componentdetail` (Component Detail)

- Update table: `prod_order_line_component`
- Tables in the SELECT: `prod_order_line_component`, `inv_mast`, `prod_order_line`, `prod_order_hdr`, `address`, `inv_loc`, `location`, `inv_loc_stock_status`, `inv_mast_assem_info`, `service_labor`, `code_p21`, `operation`, `prod_line_component_labor`, `revision_transaction`, `item_revision`, `p21_view_getrevisionlotquantity`, `system_setting`, `assembly_hdr`, `prod_order_line_link`, `work_center`, `work_center_x_service_labor`, `prodorder_department`, `p21_view_contacts`

| Field | Stored in | Basis |
|---|---|---|
| `extended_desc` | `prod_order_line_component.extended_desc` | column |
| `source_location_id` | `prod_order_line_component.source_location_id` | column |
| `supplier_id` | `prod_order_line_component.supplier_id` | column |
| `division_id` | `prod_order_line_component.division_id` | column |
| `unit_cost` | `prod_order_line_component.unit_cost` | column |
| `po_cost` | `prod_order_line_component.po_cost` | column |
| `original_completion_date` | `prod_order_line_component.original_completion_date` | column |
| `completion_date` | `prod_order_line_component.completion_date` | column |
| `operation_start_date` | `prod_order_line_component.operation_start_date` | column |
| `operation_end_date` | `prod_order_line_component.operation_end_date` | column |
| `unit_of_measure` | `prod_order_line_component.unit_of_measure` | column |
| `disposition` | `prod_order_line_component.disposition` | column |
| `qty_needed` | `prod_order_line_component.qty_needed` | column |
| `cut_length` | `prod_order_line_component.component_cut_length` | probed |
| `qty_per_assembly` | `prod_order_line_component.qty_per_assembly` | column |
| `units_allocated` | computed: `0.0000` | probed |
| `required_date` | `prod_order_line_component.required_date` | column |
| `expedite_date` | `prod_order_line_component.expedite_date` | column |
| `component_type` | computed: `CASE COALESCE(prod_order_line.hose_assembly_flag, 'N') WHEN 'Y' THEN COALESCE(inv_mast_assem_info.component_type, 300) ELSE 300 END` | alias |
| `item_desc` | `inv_mast.item_desc` | probed |
| `item_id_service_labor_id` | computed: `COALESCE(service_labor.service_labor_id, inv_mast.item_id)` | probed |
| `division_name` | `address.name` | probed |
| `supplier_name` | `address.name` | probed |
| `location_name` | `location.location_name` | column |
| `unit_cost_edited` | `prod_order_line_component.unit_cost_edited` | column |
| `backflush_flag` | `prod_order_line_component.backflush_flag` | column |
| `taxable` | `prod_order_line_component.taxable` | column |
| `other_charge` | `prod_order_line_component.other_charge` | column |
| `units_requested` | `prod_order_line_component.units_requested` | column |
| `units_used` | computed: `0.0000` | alias |
| `cut_length_edited_flag` | `prod_order_line_component.cut_length_edited_flag` | column |
| `po_cost_t` | `prod_order_line_component.po_cost` | probed |
| `units_confirmed` | computed: `(computed in the datawindow)` | probed |
| `units_canceled` | computed: `(computed in the datawindow)` | probed |
| `uom_qty_available` | computed: `(computed in the datawindow)` | probed |
| `units_picked` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 6 | Source Location ID: | `prod_order_line_component.source_location_id` |
| 7 | Extended Description: | `prod_order_line_component.extended_desc` |
| 12 | UOM: | `prod_order_line_component.unit_of_measure` |
| 14 | Disp: | `prod_order_line_component.disposition` |
| 15 | Supplier ID: | `prod_order_line_component.supplier_id` |
| 16 | Division ID: | `prod_order_line_component.division_id` |
| 17 | Taxable | `prod_order_line_component.taxable` |
| 18 | Other Charge | `prod_order_line_component.other_charge` |
| 19 | Unit Cost: | `prod_order_line_component.unit_cost` |
| 20 | Po Cost | `prod_order_line_component.po_cost` |
| 24 | Item Desc | `inv_mast.item_desc` |
| 28 | Location Name | `address.name` |
| 29 | Supplier Name | `address.name` |
| 30 | Division Name | `address.name` |
| 32 | Qty Requested: | `prod_order_line_component.units_requested` |
| 33 | Qty Allocated: | `units_allocated` |
| 34 | Qty Used: | `units_used` |
| 35 | Qty Per Assembly: | `prod_order_line_component.qty_per_assembly` |
| 62 | Cut Length: | `prod_order_line_component.component_cut_length` |
| 63 | Cut Length Edited Flag | `prod_order_line_component.cut_length_edited_flag` |
| 64 | Type: | `inv_mast_assem_info.component_type` |
| 68 | Qty Needed: | `prod_order_line_component.qty_needed` |
| 71 | Current Expected Completion Date: | `prod_order_line_component.completion_date` |
| 72 | Original Expected Completion Date: | `prod_order_line_component.original_completion_date` |
| 74 | Required Date: | `prod_order_line_component.required_date` |
| 75 | Expedite Date: | `prod_order_line_component.expedite_date` |
| 95 | Backflush Flag | `prod_order_line_component.backflush_flag` |
| 103 | Unit Cost Edited | `prod_order_line_component.unit_cost_edited` |
| 106 | Item ID: | `item_id_service_labor_id` |
| calc | Po Cost T | `IF(other_charge = 'Y', "Other Charge Amount: ", "PO Cost: ")` |
| calc | Qty Confirmed: | `"If( qty_confirmed   /  unit_size < 0 ,      0,      qty_confirmed  /  unit_size  )"` |
| calc | Qty Canceled: | `if(disposition = "C", units_requested  -  units_allocated  - units_confirmed -  units_used - qty_on_pick_tickets/unit_size, qty_canceled / unit_size)` |
| calc | Qty Available: | `"If( qty_available   /  unit_size < 0 ,      0,      qty_available  /  unit_size  )"` |
| calc | Qty Picked: | `qty_on_pick_tickets  /  unit_size` |

### `TABPAGE_20.tp_20_dw_20` (Assembly Item Options)

- Update table: `prod_order_line`
- Tables in the SELECT: `prod_order_line`, `assembly_hdr`, `inv_mast`, `inv_loc`

| Field | Stored in | Basis |
|---|---|---|
| `pricing_option` | `assembly_hdr.pricing_option` | column |
| `default_disposition` | `prod_order_line.default_disposition` | column |
| `cost_to_disassemble` | `prod_order_line.cost_to_disassemble` | column |
| `hose_assembly_flag` | `assembly_hdr.hose_assembly_flag` | column |
| `assembly_class_uid` | `assembly_hdr.assembly_class_uid` | column |
| `auto_create_prod_order` | `assembly_hdr.auto_create_prod_order` | column |
| `print_incomplete_assemblies` | `prod_order_line.print_incomplete_assemblies` | column |
| `ship_incomplete_assemblies` | `prod_order_line.ship_incomplete_assemblies` | column |
| `print_compnts_on_pick_ticket` | `prod_order_line.print_compnts_on_pick_ticket` | column |
| `print_components_on_invoice` | `prod_order_line.print_components_on_invoice` | column |
| `print_return_to_stock_components` | `prod_order_line.print_return_to_stock_components` | column |
| `price_return_to_stock_components` | `prod_order_line.price_return_to_stock_components` | column |
| `exclude_prod_order_from_scp_flag` | `prod_order_line.exclude_prod_order_from_scp_flag` | column |
| `scheduling_type_cd` | `prod_order_line.scheduling_type_cd` | column |
| `item_desc` | `inv_mast.item_desc` | column |
| `inv_mast_item_id` | `inv_mast.item_id` | probed |
| `production_order_processing` | `assembly_hdr.production_order_processing` | column |
| `assembly_usage_accumulation` | `assembly_hdr.assembly_usage_accumulation` | column |
| `assembly_for_stock` | `prod_order_line.assembly_for_stock` | column |
| `calc_component_service_level` | `assembly_hdr.calc_component_service_level` | column |
| `print_traveler_with_prodorder` | `assembly_hdr.print_traveler_with_prodorder` | column |
| `allow_oe_add_components` | `assembly_hdr.allow_oe_add_components` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Item ID: | `inv_mast.item_id` |
| 4 | Ship Incomplete Assemblies | `prod_order_line.ship_incomplete_assemblies` |
| 5 | Print Compnts On Pick Ticket | `prod_order_line.print_compnts_on_pick_ticket` |
| 6 | Print Components On Invoice | `prod_order_line.print_components_on_invoice` |
| 7 | Default Disposition: | `prod_order_line.default_disposition` |
| 13 | Allow Oe Add Components | `assembly_hdr.allow_oe_add_components` |
| 14 | Production Order Processing | `assembly_hdr.production_order_processing` |
| 15 | Auto Create Prod Order | `assembly_hdr.auto_create_prod_order` |
| 16 | Pricing Option: | `assembly_hdr.pricing_option` |
| 18 | Item Desc | `inv_mast.item_desc` |
| 22 | Accumulate Usage: | `assembly_hdr.assembly_usage_accumulation` |
| 23 | Calc Component Service Level | `assembly_hdr.calc_component_service_level` |
| 30 | Print Incomplete Assemblies | `prod_order_line.print_incomplete_assemblies` |
| 32 | Assembly For Stock | `prod_order_line.assembly_for_stock` |
| 34 | Print Return To Stock Components | `prod_order_line.print_return_to_stock_components` |
| 35 | Price Return To Stock Components | `prod_order_line.price_return_to_stock_components` |
| 36 | Hose Assembly Flag | `assembly_hdr.hose_assembly_flag` |
| 37 | Print Traveler With Prodorder | `assembly_hdr.print_traveler_with_prodorder` |
| 38 | Assembly Class: | `assembly_hdr.assembly_class_uid` |

### `TABPAGE_TRANSACTIONS_TO_ASSIGN.tabpage_transactions_to_assign` (Transactions To Assign)

- Update table: `prod_order_line_link`
- Tables in the SELECT: `prod_order_line`, `revision_transaction`, `item_revision`, `prod_order_line_link`, `prod_order_hdr`

| Field | Stored in | Basis |
|---|---|---|
| `assigned` | computed: `'Y'` | alias |
| `required_date` | computed: `current_timestamp` | alias |
| `promise_date` | computed: `cast(NULL AS datetime)` | alias |
| `trans_number` | `prod_order_line_link.trans_number` | probed |
| `line_number` | `prod_order_line_link.line_number` | probed |
| `release_number` | computed: `NULL` | probed |
| `component_number` | computed: `NULL` | probed |
| `customer_id` | `prod_order_line_link.customer_id` | probed |
| `customer_name` | computed: `' '` | alias |
| `qty_allocated` | `prod_order_line_link.qty_allocated` | probed |
| `qty_remaining` | computed: `0.0000` | alias |
| `cf_spaces` | computed: `(computed in the datawindow)` | dw_name |
| `cf_transaction_type` | computed: `(computed in the datawindow)` | dw_name |
| `qty_to_assign` | computed: `(computed in the datawindow)` | probed |
| `compute_1` | `prod_order_line_link.prod_order_number` | position |
| `qty_remain_sum` | computed: `(computed in the datawindow)` | probed |
| `qty_asso_sum` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 8 | Original Assigned | `original_assigned` |
| 9 | Assigned | `assigned` |
| 13 | Trans Number | `prod_order_line_link.trans_number` |
| 14 | LineNumber | `prod_order_line_link.line_number` |
| 15 | Customer ID | `prod_order_line_link.customer_id` |
| 16 | Customer Name | `customer_name` |
| 17 | Required Date | `prod_order_line_link.required_date` |
| 18 | Qty Remaining | `prod_order_line_link.qty_remaining` |
| 19 | Qty Allocated | `prod_order_line_link.qty_allocated` |
| 20 | Retrieve Open Transactions | `retrieve_open_transactions` |
| 23 | Promise Date | `promise_date` |
| 26 | ReleaseNumber | `release_number` |
| 27 | ComponentNumber | `component_number` |
| calc | Transaction Type | `CASE(trans_type WHEN 'P' THEN 'Production Order' WHEN 'O' THEN 'Sales Order' WHEN 'S' THEN 'Release Schedule' ELSE trans_type)` |
| calc | Qty To Assign | `if(assigned = 'Y', if(trans_type = 'P', if(quantity - qty_completed > 0, quantity - qty_completed, qty_remaining), qty_remaining), 0)` |

### `TABPAGE_ASSEMBLY_ITEM_NOTES.tabpage_assembly_item_notes` (Assembly Item Notes)

- Update table: `note_area`
- Tables in the SELECT: `note_area`, `note`, `inv_mast`, `notepad_class`

| Field | Stored in | Basis |
|---|---|---|
| `note` | `note.note` | column |
| `note_id` | `note.note_uid` | probed |
| `topic` | `note.topic` | column |
| `notepad_class_desc` | `notepad_class.notepad_class_desc` | column |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Note ID | `note.note_uid` |
| 2 | Topic | `note.topic` |
| 3 | Note | `note.note` |
| 5 | Class | `notepad_class.notepad_class_desc` |

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

### `TP_ASSEMBLY_DETAILS.tp_assembly_details` (Assembly Details)

- Update table: `prod_order_line`
- Tables in the SELECT: `prod_order_line`, `inv_mast`, `prod_order_hdr`, `inv_loc`, `assembly_hdr`, `oe_hdr`, `oe_hdr_progress_billing`, `oe_line`, `prod_order_line_link`, `revision_transaction`, `item_revision`, `process_x_transaction`, `process_x_transaction_detail`, `prod_order_line_process`

| Field | Stored in | Basis |
|---|---|---|
| `extended_desc` | `prod_order_line.extended_desc` | column |
| `comment_date` | `prod_order_line.comment_date` | column |
| `assembly_item_id` | `inv_mast.item_id` | probed |
| `committed_start_date` | `prod_order_line.committed_start_date` | column |
| `end_date` | `prod_order_line.end_date` | column |
| `start_date` | `prod_order_line.start_date` | column |
| `assembly_item_desc` | `inv_mast.item_desc` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 1 | Assembly Item ID: | `inv_mast.item_id` |
| 11 | Assembly Item Desc | `inv_mast.item_desc` |
| 38 | Committed Start Date: | `prod_order_line.committed_start_date` |
| 39 | Actual Start Date: | `prod_order_line.start_date` |
| 40 | Actual End Date: | `prod_order_line.end_date` |
| 41 | Comment Date: | `prod_order_line.comment_date` |
| 77 | Extended Description: | `prod_order_line.extended_desc` |

### `TP_ASSEMBLYCOSTS.tp_assemblycosts` (Costs)

- Update table: `prod_order_line`
- Tables in the SELECT: `prod_order_line`, `inv_mast`, `prod_order_hdr`, `inv_loc`, `assembly_hdr`, `oe_hdr`, `oe_hdr_progress_billing`, `oe_line`, `prod_order_line_link`, `revision_transaction`, `item_revision`, `process_x_transaction`, `process_x_transaction_detail`, `prod_order_line_process`

| Field | Stored in | Basis |
|---|---|---|
| `estimated_freight_cost` | `prod_order_line.estimated_freight_cost` | column |
| `actual_freight_cost` | `prod_order_line.actual_freight_cost` | column |
| `estimated_other_charge_cost` | computed: `0.000000000` | probed |
| `estimated_labor_cost_indirect` | computed: `0.0000` | alias |
| `estimated_labor_cost_direct` | computed: `0.0000` | probed |
| `estimated_process_cost` | `prod_order_line.estimated_process_cost` | column |
| `other_charge_cost` | computed: `0.000000000` | probed |
| `msp_cost` | computed: `0.000000000` | probed |
| `actual_labor_cost_indirect` | computed: `0.0000` | alias |
| `actual_labor_cost_direct` | computed: `0.0000` | alias |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 48 | Direct Labor Cost: | `estimated_labor_cost_direct` |
| 49 | Direct Labor Cost: | `actual_labor_cost_direct` |
| 52 | Freight Cost: | `prod_order_line.estimated_freight_cost` |
| 53 | Freight Cost: | `prod_order_line.actual_freight_cost` |
| 64 | Process Cost: | `msp_cost` |
| 65 | Other Charge Cost: | `other_charge_cost` |
| 66 | Other Charge Cost: | `estimated_other_charge_cost` |
| 74 | Process Cost: | `prod_order_line.estimated_process_cost` |
| 78 | Indirect Labor Cost: | `estimated_labor_cost_indirect` |
| 79 | Indirect Labor Cost: | `actual_labor_cost_indirect` |
| calc | Total Production Cost: | `"if( isNull( estimated_labor_cost_direct ), 0, estimated_labor_cost_direct ) +  if( isNull( estimated_material_cost ), 0, estimated_material_cost )  + if( isNull( estimated_freight_cost ), 0, estimated_freight_cost ) +   if( isNull(  estimated_process_cost  ), 0,  estimated_process_cost )  + if( isNull(  estimated_labor_cost_indirect  ), 0,  estimated_labor_cost_indirect ) "` |
| calc | Cf Estimated Material Cost | `if(IsNull(estimated_material_cost), 0, estimated_material_cost) - if(IsNull(estimated_other_charge_cost), 0, estimated_other_charge_cost )` |
| calc | Cf Actual Material Cost | `if(IsNull(actual_material_cost), 0, actual_material_cost) - if(IsNull(other_charge_cost ), 0, other_charge_cost )` |
| calc | Total Production Cost: | `actual_labor_cost_direct +  actual_material_cost +  actual_freight_cost + if(isnull(msp_cost), 0, msp_cost)  + if( isNull(  actual_labor_cost_indirect  ), 0,  actual_labor_cost_indirect )` |

### `TP_FREIGHTCOSTS.tp_freightcosts` (Freight Costs)

- Update table: `prod_order_line_comp_frght`
- Tables in the SELECT: `prod_order_line_comp_frght`, `prod_order_line_component`, `inv_mast`

| Field | Stored in | Basis |
|---|---|---|
| `po_no` | `prod_order_line_comp_frght.po_no` | probed |
| `transfer_no` | `prod_order_line_comp_frght.transfer_no` | column |
| `assembly_item_id` | `inv_mast.item_id` | probed |
| `component_item_id` | `inv_mast.item_id` | probed |
| `freight_cost` | `prod_order_line_comp_frght.freight_cost` | column |
| `assembly_item_desc` | `inv_mast.item_desc` | probed |
| `component_item_desc` | `inv_mast.item_desc` | probed |
| `compute_1` | `prod_order_line_comp_frght.po_no` | position |
| `cf_adjustment` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_freight` | computed: `(computed in the datawindow)` | dw_name |
| `cf_total_adjustment` | computed: `(computed in the datawindow)` | dw_name |
| `cf_dfflag` | computed: `(computed in the datawindow)` | dw_name |

| # | Label | table.column / expression |
|---|---|---|
| 1 | PO Number | `prod_order_line_comp_frght.po_no` |
| 2 | Transfer Number | `prod_order_line_comp_frght.transfer_no` |
| 3 | Assembly Item | `assembly_inv_mast.item_id` |
| 4 | Description | `assembly_inv_mast.item_desc` |
| 5 | Component Item | `component_inv_mast.item_id` |
| 6 | Description | `component_inv_mast.item_desc` |
| 7 | Freight Cost | `prod_order_line_comp_frght.freight_cost` |

### `PROD_ORDER_LINE_NOTE_TAB.prod_order_line_note_tab` (Production Order Line Notes)

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

### `TABPAGE_OELINENOTEASSEMBLY.tabpage_oelinenoteassembly` (Order Line Assembly Notes)

- Update table: `oe_line_notepad`
- Tables in the SELECT: `oe_line_notepad`, `oe_line`, `prod_order_line_link`, `prod_order_line`, `note_area`, `notepad_class`

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

### `TABPAGE_OELINENOTECOMPONENT.tabpage_oelinenotecomponent` (Order Line Component Notes)

- Update table: `oe_line_notepad`
- Tables in the SELECT: `oe_line_notepad`, `oe_line`, `prod_ord_line_compnt_x_oe_line`, `prod_order_line_component`, `note_area`, `notepad_class`

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
| `compute_1` | `inv_loc.location_id` | position |
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
| `TABPAGE_2` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_3` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_4` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_5` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_6` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_7` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_8` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_21` |  | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab with name or display text of TABPAGE_21 does not exist.); hidden placeholder page |
| `TABPAGE_22` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_23` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_24` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_ITEM_NOTES` | Component Item Notes | `tabpage_item_notes` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_COMPONENT_SERIAL` | Component Serial | `component_serial` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_COMPONENT_LOT` | Component Lot | `tabpage_component_lot` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_COMPONENT_LOT_BIN_XREF` | Component Lot/Bin | `tabpage_component_lot_bin_xref` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_COMPONENT_BIN` | Component Bin | `tabpage_component_bin` | datawindow never instantiated (tab not enabled) |
| `TP_COMPONENT_TAGS` | Component Tags | `tp_tags_tdl_header` | datawindow never instantiated (tab not enabled) |
| `TP_COMPONENT_TAGS` | Component Tags | `tp_tags_dlt` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_ASSEMBLY_SERIAL` | Assembly Serial | `serial` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_ASSEMBLY_LOT` | Assembly Lot | `tabpage_assembly_lot` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_ASSEMBLY_LOT_BIN_XREF` | Assembly Lot/Bin | `tabpage_assembly_lot_bin_xref` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_ASSEMBLY_BIN` | Assembly Bin | `tabpage_assembly_bin` | datawindow never instantiated (tab not enabled) |
| `TP_ASSEMBLY_TAGS` | Assembly Tags | `tp_tags_tdl_header` | datawindow never instantiated (tab not enabled) |
| `TP_ASSEMBLY_TAGS` | Assembly Tags | `tp_tags_dlt` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_POS` | PO Links | `links_for_prod_order_hdr` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_POS` | PO Links | `links_for_prod_order` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_PRODUCTIONORDER` | Production Order | `productionorder` | datawindow never instantiated (tab not enabled) |
| `TP_LABOR` | Labor | `tp_labor` | datawindow never instantiated (tab not enabled) |
| `TP_LABORDETAIL` | Labor Detail | `tp_labordetail` | datawindow never instantiated (tab not enabled) |
| `TP_LABORSCHEDULEDISPLAY` | Posted Labor Detail | `tp_laborscheduledisplay` | datawindow never instantiated (tab not enabled) |
| `ROUTING_TABPAGE` | Routing | `process_x_transaction` | datawindow never instantiated (tab not enabled) |
| `ROUTING_TABPAGE` | Routing | `process_x_transaction_detail` | datawindow never instantiated (tab not enabled) |
| `PROCESSDETAIL_TABPAGE` | Process Detail | `processdetail_tabpage` | datawindow never instantiated (tab not enabled) |
| `PROCESSORDERDETAIL_TABPAGE` | Process Order Detail | `processorderdetail_tabpage` | datawindow never instantiated (tab not enabled) |
| `PROCESSPO_TABPAGE` | Process POs | `processpo_tabpage` | datawindow never instantiated (tab not enabled) |
| `PROCESSPOLINENOTE_TABPAGE` | PO Line Notes | `processpolinenote_tabpage` | datawindow never instantiated (tab not enabled) |
| `ROUTENOTESTABPAGE` | Route Notes | `routenotestabpage` | datawindow never instantiated (tab not enabled) |
| `PROCESSNOTESTABPAGE` | Process Notes | `processnotestabpage` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_POSXFERS` | POs/Xfers | `pos/xfers` | datawindow never instantiated (tab not enabled) |
| `TIMESTAMPDETAIL` | Timestamp | `timestampdetail_dw_audittrail` | datawindow never instantiated (tab not enabled) |
