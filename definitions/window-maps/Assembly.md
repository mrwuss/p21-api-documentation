# Assembly Maintenance (`Assembly`)

- Window class: `w_assembly_maint_sheet`; menu class: `m_assemblymaintenance`
- Tabs: 26; datawindows mapped: 8; unreachable entries: 21

## Tab overview

| Tab | Caption | Datawindows mapped | Tables in the SELECT |
|---|---|---|---|
| `TABPAGE_1` | Assembly | `assemblyhdr` | assembly_class, assembly_hdr, inv_mast |
| `DOCUMENT_LINK` | Document Links | `document_link` | document_link, document_link_area, document_link_entity_req, inv_mast |
| `TIMESTAMP` | Audit Trail | `timestamp`, `audit_trail` | p21_view_audit_trail_assembly_hdr_<id> |
| `TABPAGE_17` | Components | `tp_17_dw_17` | assembly_hdr, assembly_line, inv_mast, inv_mast_assem_info, item_revision, operation, service_labor |
| `DOCUMENT_LINK_DETAIL` | Document Links | `document_link_detail_detail` | document_link, document_link_area, document_link_entity_req, inv_mast |
| `TP_COMPONENTITEMNOTES` | Component Item Notes | `tp_componentitemnotes` | code_p21, note, note_area, notepad_class |
| `TIMESTAMPDETAIL` | Timestamp | `timestampdetail` |  |

## Datawindows

### `TABPAGE_1.assemblyhdr` (Assembly)

- Update table: `assembly_hdr`
- Tables in the SELECT: `assembly_hdr`, `inv_mast`, `assembly_class`

| Field | Stored in | Basis |
|---|---|---|
| `inv_mast_item_id` | `inv_mast.item_id` | probed |
| `revision_level` | computed: `(the tool names item_revision.revision_level; the SELECT does not read it)` | probed |
| `pricing_option` | `assembly_hdr.pricing_option` | probed |
| `default_disposition` | `assembly_hdr.default_disposition` | probed |
| `assembly_usage_accumulation` | `assembly_hdr.assembly_usage_accumulation` | probed |
| `prorate_cost_by` | `assembly_hdr.prorate_cost_by` | probed |
| `allow_disassembly` | `assembly_hdr.allow_disassembly` | probed |
| `cost_of_disassembly` | `assembly_hdr.cost_of_disassembly` | probed |
| `hose_assembly_flag` | `assembly_hdr.hose_assembly_flag` | probed |
| `hose_overall_length` | `assembly_hdr.hose_overall_length` | probed |
| `hose_unit_of_measure` | `assembly_hdr.hose_unit_of_measure` | probed |
| `time_to_make` | computed: `dbo.P21_fn_convert_minutes_to_hours_format(assembly_hdr.minutes_to_make)` | probed |
| `assembly_class_uid` | `assembly_hdr.assembly_class_uid` | probed |
| `production_order_processing` | `assembly_hdr.production_order_processing` | probed |
| `assembly_for_stock` | `assembly_hdr.assembly_for_stock` | probed |
| `allow_oe_add_components` | `assembly_hdr.allow_oe_add_components` | probed |
| `auto_create_prod_order` | `assembly_hdr.auto_create_prod_order` | probed |
| `price_return_to_stock_components` | `assembly_hdr.price_return_to_stock_components` | probed |
| `print_return_to_stock_components` | `assembly_hdr.print_return_to_stock_components` | probed |
| `print_compnts_on_pick_ticket` | `assembly_hdr.print_compnts_on_pick_ticket` | probed |
| `print_components_on_invoice` | `assembly_hdr.print_components_on_invoice` | probed |
| `calc_component_service_level` | `assembly_hdr.calc_component_service_level` | probed |
| `print_incomplete_assemblies` | `assembly_hdr.print_incomplete_assemblies` | probed |
| `ship_incomplete_assemblies` | `assembly_hdr.ship_incomplete_assemblies` | probed |
| `do_not_bulk_edit_flag` | `assembly_hdr.do_not_bulk_edit_flag` | probed |
| `print_traveler_with_prodorder` | `assembly_hdr.print_traveler_with_prodorder` | probed |
| `delete_flag` | `assembly_hdr.delete_flag` | probed |
| `pack_by` | `assembly_hdr.pack_by` | probed |
| `include_components_on_edi_856` | `assembly_hdr.include_components_on_edi_856` | probed |
| `exclude_prod_order_from_scp_flag` | `assembly_hdr.exclude_prod_order_from_scp_flag` | probed |
| `scheduling_type_cd` | `assembly_hdr.scheduling_type_cd` | probed |
| `item_desc` | `inv_mast.item_desc` | probed |
| `copy_item_id` | computed: `''` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | probed |

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
| 40 | Copy Item Id | `cc_copy_item_id` |
| 42 | Hose Assembly Flag | `assembly_hdr.hose_assembly_flag` |
| 43 | Overall Length: | `assembly_hdr.hose_overall_length` |
| 44 | Unit of Measure: | `assembly_hdr.hose_unit_of_measure` |
| 50 | Print Traveler With Prodorder | `assembly_hdr.print_traveler_with_prodorder` |
| 52 | Do Not Bulk Edit Flag | `assembly_hdr.do_not_bulk_edit_flag` |
| 53 | Assembly Class: | `assembly_hdr.assembly_class_uid` |
| 54 | Pack By: | `assembly_hdr.pack_by` |
| 56 | Time To Make: | `time_to_make` |
| 57 | Include Components On Edi 856 | `assembly_hdr.include_components_on_edi_856` |

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
| 25 | Mandatory | `document_link.mandatory_flag` |
| calc | Document Linked to | `IF ( key2_cd = 'lot_cd', if(isnull(key2_value),'',key2_value), IF ( key1_cd = 'inv_mast_uid', if(isnull(item_id),'',item_id), if(isnull(key1_value),'',key1_value) ) + IF ( IsNull(key2_value), '', '/' + key2_value + IF ( IsNull(key3_value), '', '/' + key3_value)) )` |

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

- Update table: `p21_view_audit_trail_assembly_hdr_<id>`
- Tables in the SELECT: `p21_view_audit_trail_assembly_hdr_<id>`
- Mapped off-tab: the API could not select this tab (HTTP 400: Multiple tabs have a name or display text of TIMESTAMP.); SQL Information reads an instantiated datawindow whichever tab is active

| Field | Stored in | Basis |
|---|---|---|
| `item_id` | `p21_view_audit_trail_assembly_hdr_<id>.item_id` | probed |
| `column_description` | `p21_view_audit_trail_assembly_hdr_<id>.column_description` | probed |
| `old_value` | `p21_view_audit_trail_assembly_hdr_<id>.old_value` | probed |
| `new_value` | `p21_view_audit_trail_assembly_hdr_<id>.new_value` | probed |
| `date_created` | `p21_view_audit_trail_assembly_hdr_<id>.date_created` | probed |
| `created_by` | `p21_view_audit_trail_assembly_hdr_<id>.created_by` | probed |
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
| calc | Assembly Item ID | `"IF ((source_area_cd = 1763 and key1_cd = 'service_labor_uid'), item_id,  IF (source_area_cd = 950, key1_value,  IF (key2_cd = 'item_service_uid',  Item_id + ' / ALL / ALL',  IF ( key2_cd = 'lot_cd', key2_value,   IF ( Len(auxiliary_value) > 0 AND source_area_cd IN (1544, 1250, 2531), auxiliary_value,  IF (source_area_cd = 1314 and table_changed = 'inv_mast_strategic_pricing', item_id + '/' + key3_value + IF (IsNull(key2_value), '', '/' + auxiliary_value),  IF ( key1_cd = 'inv_mast_uid', item_id, key1_value ) + IF ( IsNull ( key2_value) AND source_area_cd <> 1314, '', ' / ' + IF ( key2_cd = 'inv_mast_uid', item_id, IF ( IsNull ( key2_value ), 'ALL', key2_value ) )  + IF ( IsNull (key3_value) AND source_area_cd <> 1314, '', ' / ' + IF ( key3_cd = 'inv_mast_uid', item_id, IF ( IsNull ( key3_value ), 'ALL', key3_value ) ) ) )  ) ) ) ) ) )"` |
| calc | 'Sub Line No | `` |

### `TABPAGE_17.tp_17_dw_17` (Components)

- Update table: `assembly_line`
- Tables in the SELECT: `assembly_line`, `assembly_hdr`, `inv_mast`, `service_labor`, `inv_mast_assem_info`, `operation`, `item_revision`

| Field | Stored in | Basis |
|---|---|---|
| `item_id_service_labor_id` | computed: `COALESCE(service_labor.service_labor_id, inv_mast_comp.item_id)` | probed |
| `revision_level` | `item_revision.revision_level` | probed |
| `component_type` | computed: `CASE assembly_hdr.hose_assembly_flag WHEN 'Y' THEN inv_mast_assem_info.component_type ELSE 300 END` | probed |
| `operation_cd` | `operation.operation_cd` | probed |
| `qty_needed` | `assembly_line.qty_needed` | probed |
| `component_cut_length` | `assembly_line.component_cut_length` | probed |
| `cut_length_edited_flag` | `assembly_line.cut_length_edited_flag` | probed |
| `quantity` | `assembly_line.quantity` | probed |
| `unit_of_measure` | `assembly_line.unit_of_measure` | probed |
| `date_offset_days` | `assembly_line.date_offset_days` | probed |
| `backflush_flag` | `assembly_line.backflush_flag` | probed |
| `loose_ship_flag` | `assembly_line.loose_ship_flag` | probed |
| `previous_operation` | `assembly_line.previous_operation` | probed |
| `delete_flag` | `assembly_line.delete_flag` | probed |
| `next_operation` | `assembly_line.next_operation` | probed |
| `item_desc` | computed: `COALESCE(service_labor.service_labor_desc, inv_mast_comp.item_desc)` | probed |
| `cf_expandableindicator` | computed: `(computed in the datawindow)` | probed |
| `cf_prodorderflag` | computed: `(computed in the datawindow)` | probed |
| `cf_yesorno` | computed: `(computed in the datawindow)` | probed |
| `cf_dfflag` | computed: `(computed in the datawindow)` | probed |

| # | Label | table.column / expression |
|---|---|---|
| 2 | Description | `inv_mast_comp.item_desc` |
| 3 | Qty Per Assembly | `assembly_line.quantity` |
| 4 | Delete | `assembly_line.delete_flag` |
| 12 | UOM | `assembly_line.unit_of_measure` |
| 17 | Cut Length | `assembly_line.component_cut_length` |
| 18 | Edited | `assembly_line.cut_length_edited_flag` |
| 19 | ComponentType | `inv_mast_assem_info.component_type` |
| 22 | Qty Needed | `assembly_line.qty_needed` |
| 28 | Operation | `operation.operation_cd` |
| 29 | Date Offset No of Days | `assembly_line.date_offset_days` |
| 36 | Backflush | `assembly_line.backflush_flag` |
| 42 | LooseShip | `assembly_line.loose_ship_flag` |
| 43 | Item Id Service Labor Id | `item_id_service_labor_id` |
| calc | Cf Expandableindicator | `if(sub_assembly = 'Y', '+', '')` |

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
| 25 | Mandatory | `document_link.mandatory_flag` |
| calc | Document Linked to | `IF ( key2_cd = 'lot_cd', if(isnull(key2_value),'',key2_value), IF ( key1_cd = 'inv_mast_uid', if(isnull(item_id),'',item_id), if(isnull(key1_value),'',key1_value) ) + IF ( IsNull(key2_value), '', '/' + key2_value + IF ( IsNull(key3_value), '', '/' + key3_value)) )` |

### `TP_COMPONENTITEMNOTES.tp_componentitemnotes` (Component Item Notes)

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
| `ROUTING_TABPAGE` | Routing | `process` | datawindow never instantiated (tab not enabled) |
| `ROUTING_TABPAGE` | Routing | `stage_x_process` | datawindow never instantiated (tab not enabled) |
| `PROCESSDETAIL_TABPAGE` | Process Detail | `processdetail_tabpage` | datawindow never instantiated (tab not enabled) |
| `ROUTENOTESTABPAGE` | Route Notes | `routenotestabpage` | datawindow never instantiated (tab not enabled) |
| `PROCESSNOTESTABPAGE` | Process Notes | `processnotestabpage` | datawindow never instantiated (tab not enabled) |
| `TP_ASSEMBLYITEMNOTES` | Assembly Item Notes | `tp_assemblyitemnotes` | datawindow never instantiated (tab not enabled) |
| `TABPAGE_18` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_19` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_20` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_21` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_22` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_23` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TABPAGE_24` | none | - | tab has no datawindow in the API definition and cannot be selected (HTTP 400: Tab page is invisible and cannot be selected); hidden placeholder page |
| `TIMESTAMPDETAIL` | Timestamp | `timestampdetail_dw_audittrail` | datawindow never instantiated (tab not enabled) |
