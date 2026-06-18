-- OriginalEngine — as-built schema (auto-generated from SQLAlchemy models)
-- 63 tables · dialect: PostgreSQL
-- Source of truth: models.py (do not hand-edit; regenerate)

CREATE TABLE audit_event (
	event_id VARCHAR(36) NOT NULL, 
	event_ts TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	event_type VARCHAR(80) NOT NULL, 
	entity_type VARCHAR(80) NOT NULL, 
	entity_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36), 
	actor_id VARCHAR(120) NOT NULL, 
	before_state_hash VARCHAR(64), 
	after_state_hash VARCHAR(64) NOT NULL, 
	source_artifact_id VARCHAR(36), 
	prev_event_hash VARCHAR(64), 
	event_hash VARCHAR(64) NOT NULL, 
	success_status VARCHAR(20) NOT NULL, 
	reason_note TEXT, 
	PRIMARY KEY (event_id), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(source_artifact_id) REFERENCES source_artifact (artifact_id)
);

CREATE TABLE bid_line (
	bid_line_id VARCHAR(36) NOT NULL, 
	submission_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	round_id VARCHAR(36) NOT NULL, 
	supplier_id VARCHAR(36) NOT NULL, 
	dc_id VARCHAR(36) NOT NULL, 
	lot_id VARCHAR(36) NOT NULL, 
	item_id VARCHAR(36) NOT NULL, 
	tf_id VARCHAR(36) NOT NULL, 
	currency_code VARCHAR(3) NOT NULL, 
	price_basis price_basis_enum NOT NULL, 
	submitted_all_in_case NUMERIC(18, 6), 
	fob_case NUMERIC(18, 6), 
	freight_case NUMERIC(18, 6), 
	fuel_case NUMERIC(18, 6), 
	accessorial_case NUMERIC(18, 6), 
	item_discount_case NUMERIC(18, 6), 
	shrink_case NUMERIC(18, 6), 
	commercial_conditions_text TEXT, 
	moq_cases NUMERIC(18, 3), 
	volume_minimum_cases NUMERIC(18, 3), 
	exclusivity_required_flag BOOLEAN NOT NULL, 
	effective_date_start DATE, 
	effective_date_end DATE, 
	loading_location_id VARCHAR(36), 
	validity_status bid_status_enum NOT NULL, 
	source_row_number INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	bid_line_status bid_line_status_enum, 
	is_scoreable BOOLEAN DEFAULT 0 NOT NULL, 
	is_awardable BOOLEAN DEFAULT 0 NOT NULL, 
	incomplete_reason_code bid_line_incomplete_reason_enum, 
	leverage_signal_flag BOOLEAN DEFAULT 0 NOT NULL, 
	leverage_signal_reason bid_line_leverage_reason_enum, 
	best_in_class_signal_flag BOOLEAN DEFAULT 0 NOT NULL, 
	follow_up_recommended_flag BOOLEAN DEFAULT 0 NOT NULL, 
	PRIMARY KEY (bid_line_id), 
	CONSTRAINT uq_bid_line_cell_per_submission UNIQUE (submission_id, dc_id, lot_id, item_id, tf_id), 
	CONSTRAINT uq_bid_line_identity_full UNIQUE (bid_line_id, cycle_id, round_id, supplier_id, dc_id, lot_id, item_id, tf_id), 
	CONSTRAINT fk_bidline_to_submission_identity FOREIGN KEY(submission_id, cycle_id, round_id, supplier_id) REFERENCES bid_submission (submission_id, cycle_id, round_id, supplier_id), 
	CONSTRAINT fk_bidline_lot_in_cycle FOREIGN KEY(lot_id, cycle_id) REFERENCES cycle_lot (lot_id, cycle_id), 
	CONSTRAINT fk_bidline_tf_in_cycle FOREIGN KEY(tf_id, cycle_id) REFERENCES cycle_tf (tf_id, cycle_id), 
	CONSTRAINT fk_bidline_item_in_lot FOREIGN KEY(lot_id, item_id) REFERENCES cycle_lot_item (lot_id, item_id), 
	CONSTRAINT fk_bidline_loc_belongs_to_supplier FOREIGN KEY(loading_location_id, supplier_id) REFERENCES loading_location (location_id, supplier_id), 
	CONSTRAINT ck_bid_all_in_positive CHECK (submitted_all_in_case IS NULL OR submitted_all_in_case > 0), 
	CONSTRAINT ck_bid_fob_positive CHECK (fob_case IS NULL OR fob_case > 0), 
	FOREIGN KEY(dc_id) REFERENCES dc_master_db (dc_id)
);
CREATE INDEX ix_bid_line_cell ON bid_line (cycle_id, round_id, dc_id, lot_id, item_id, tf_id);

CREATE TABLE bid_submission (
	submission_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	round_id VARCHAR(36) NOT NULL, 
	supplier_id VARCHAR(36) NOT NULL, 
	source_artifact_id VARCHAR(36) NOT NULL, 
	submitted_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	version_number INTEGER NOT NULL, 
	overall_status submission_status_enum NOT NULL, 
	standard_terms_accepted BOOLEAN NOT NULL, 
	terms_exceptions_text TEXT, 
	PRIMARY KEY (submission_id), 
	CONSTRAINT uq_submission_identity_quad UNIQUE (submission_id, cycle_id, round_id, supplier_id), 
	CONSTRAINT fk_submission_round_in_cycle FOREIGN KEY(round_id, cycle_id) REFERENCES cycle_round (round_id, cycle_id), 
	CONSTRAINT fk_submission_artifact_provenance FOREIGN KEY(source_artifact_id, cycle_id, round_id, supplier_id) REFERENCES source_artifact (artifact_id, cycle_id, round_id, supplier_id), 
	CONSTRAINT ck_submission_version_positive CHECK (version_number > 0), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id)
);

CREATE TABLE calculation_run (
	calc_run_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	round_id VARCHAR(36), 
	run_type calc_run_type_enum NOT NULL, 
	status calc_run_status_enum NOT NULL, 
	source_snapshot_id VARCHAR(36), 
	metric_version_id VARCHAR(36), 
	scenario_config_version_id VARCHAR(36), 
	engine_release_id VARCHAR(36), 
	run_started_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	run_finished_at TIMESTAMP WITHOUT TIME ZONE, 
	run_by VARCHAR(120) NOT NULL, 
	input_hash_manifest TEXT, 
	output_hash_manifest TEXT, 
	error_log TEXT, 
	execution_contract execution_contract_enum, 
	upstream_calc_run_id VARCHAR(36), 
	PRIMARY KEY (calc_run_id), 
	CONSTRAINT fk_calcrun_round_in_cycle FOREIGN KEY(round_id, cycle_id) REFERENCES cycle_round (round_id, cycle_id), 
	CONSTRAINT uq_calcrun_identity_triple UNIQUE (calc_run_id, cycle_id, round_id), 
	CONSTRAINT uq_calcrun_identity_metric_quad UNIQUE (calc_run_id, cycle_id, round_id, metric_version_id), 
	CONSTRAINT ck_calcrun_success_completeness CHECK ((status IN ('SUCCEEDED','FINAL_APPROVED') AND run_finished_at IS NOT NULL   AND source_snapshot_id IS NOT NULL   AND metric_version_id IS NOT NULL   AND scenario_config_version_id IS NOT NULL   AND engine_release_id IS NOT NULL) OR status NOT IN ('SUCCEEDED','FINAL_APPROVED')), 
	CONSTRAINT ck_calcrun_failed_has_errorlog CHECK ((status = 'FAILED' AND error_log IS NOT NULL) OR (status != 'FAILED' AND (error_log IS NULL OR length(error_log) >= 0))), 
	CONSTRAINT ck_calcrun_final_has_output_manifest CHECK (status != 'FINAL_APPROVED' OR output_hash_manifest IS NOT NULL), 
	CONSTRAINT ck_calcrun_round_required_for_round_scoped_types CHECK (run_type NOT IN ('ROUND_ANALYSIS','CAT_MAN_RERUN','FINAL_ALIGNED','SCENARIO_A_BENCHMARK') OR round_id IS NOT NULL), 
	CONSTRAINT ck_calcrun_scenario_a_requires_upstream CHECK ((execution_contract = 'GOVERNED_SCENARIO_A'     AND upstream_calc_run_id IS NOT NULL) OR ((execution_contract IS NULL       OR execution_contract <> 'GOVERNED_SCENARIO_A')     AND upstream_calc_run_id IS NULL)), 
	CONSTRAINT ck_calcrun_contract_matches_run_type CHECK (execution_contract IS NULL OR (execution_contract = 'GOVERNED_CANDIDATE_ANALYSIS'     AND run_type = 'ROUND_ANALYSIS') OR (execution_contract = 'GOVERNED_SCENARIO_A'     AND run_type = 'SCENARIO_A_BENCHMARK')), 
	CONSTRAINT ck_calcrun_success_has_input_manifest CHECK (status NOT IN ('SUCCEEDED','FINAL_APPROVED') OR input_hash_manifest IS NOT NULL), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(source_snapshot_id) REFERENCES normalization_run (normalization_run_id), 
	FOREIGN KEY(metric_version_id) REFERENCES metric_definition_version (metric_version_id), 
	FOREIGN KEY(scenario_config_version_id) REFERENCES scenario_config_version (scenario_config_version_id), 
	FOREIGN KEY(engine_release_id) REFERENCES engine_release (engine_release_id), 
	FOREIGN KEY(upstream_calc_run_id) REFERENCES calculation_run (calc_run_id)
);

CREATE TABLE calculation_run_input (
	calc_run_input_id VARCHAR(36) NOT NULL, 
	calc_run_id VARCHAR(36) NOT NULL, 
	input_type calc_run_input_type_enum NOT NULL, 
	source_entity_type VARCHAR(80) NOT NULL, 
	source_entity_reference TEXT NOT NULL, 
	canonical_hash VARCHAR(128) NOT NULL, 
	row_count INTEGER, 
	included_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (calc_run_input_id), 
	CONSTRAINT uq_calcrun_input_one_per_type UNIQUE (calc_run_id, input_type), 
	CONSTRAINT ck_calcrun_input_row_count_nonneg CHECK (row_count IS NULL OR row_count >= 0), 
	CONSTRAINT ck_calcrun_input_hash_min_length CHECK (length(canonical_hash) >= 8), 
	FOREIGN KEY(calc_run_id) REFERENCES calculation_run (calc_run_id)
);

CREATE TABLE capacity_constraint (
	capacity_constraint_id VARCHAR(36) NOT NULL, 
	capacity_statement_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	scope_type capacity_scope_type_enum NOT NULL, 
	dc_id VARCHAR(36), 
	lot_id VARCHAR(36), 
	tf_id VARCHAR(36), 
	max_weekly_cases NUMERIC(18, 3), 
	max_period_cases NUMERIC(18, 3), 
	conditions_text TEXT, 
	PRIMARY KEY (capacity_constraint_id), 
	CONSTRAINT fk_capcon_stmt_cycle FOREIGN KEY(capacity_statement_id, cycle_id) REFERENCES capacity_statement (capacity_statement_id, cycle_id), 
	CONSTRAINT fk_capcon_lot_in_cycle FOREIGN KEY(lot_id, cycle_id) REFERENCES cycle_lot (lot_id, cycle_id), 
	CONSTRAINT fk_capcon_tf_in_cycle FOREIGN KEY(tf_id, cycle_id) REFERENCES cycle_tf (tf_id, cycle_id), 
	CONSTRAINT ck_capacity_scope_field_match CHECK ((scope_type = 'CELL'        AND dc_id IS NOT NULL AND lot_id IS NOT NULL AND tf_id IS NOT NULL) OR (scope_type = 'DC_TF'    AND dc_id IS NOT NULL AND lot_id IS NULL     AND tf_id IS NOT NULL) OR (scope_type = 'LOT_TF'   AND dc_id IS NULL     AND lot_id IS NOT NULL AND tf_id IS NOT NULL) OR (scope_type = 'SUPPLIER_TF' AND dc_id IS NULL AND lot_id IS NULL     AND tf_id IS NOT NULL) OR (scope_type = 'TOTAL_CYCLE' AND dc_id IS NULL AND lot_id IS NULL     AND tf_id IS NULL)), 
	CONSTRAINT ck_capacity_has_a_max CHECK (max_weekly_cases IS NOT NULL OR max_period_cases IS NOT NULL), 
	CONSTRAINT ck_capacity_weekly_nonneg CHECK (max_weekly_cases IS NULL OR max_weekly_cases >= 0), 
	CONSTRAINT ck_capacity_period_nonneg CHECK (max_period_cases IS NULL OR max_period_cases >= 0), 
	FOREIGN KEY(dc_id) REFERENCES dc_master_db (dc_id)
);

CREATE TABLE capacity_statement (
	capacity_statement_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	round_id VARCHAR(36), 
	supplier_id VARCHAR(36) NOT NULL, 
	submission_id VARCHAR(36), 
	source_artifact_id VARCHAR(36) NOT NULL, 
	status capacity_statement_status_enum NOT NULL, 
	effective_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	notes TEXT, 
	PRIMARY KEY (capacity_statement_id), 
	CONSTRAINT fk_capacity_stmt_round_in_cycle FOREIGN KEY(round_id, cycle_id) REFERENCES cycle_round (round_id, cycle_id), 
	CONSTRAINT fk_capstmt_artifact_cycle_supplier FOREIGN KEY(source_artifact_id, cycle_id, supplier_id) REFERENCES source_artifact (artifact_id, cycle_id, supplier_id), 
	CONSTRAINT fk_capstmt_artifact_round_match FOREIGN KEY(source_artifact_id, round_id) REFERENCES source_artifact (artifact_id, round_id), 
	CONSTRAINT fk_capstmt_submission_identity FOREIGN KEY(submission_id, cycle_id, round_id, supplier_id) REFERENCES bid_submission (submission_id, cycle_id, round_id, supplier_id), 
	CONSTRAINT ck_capstmt_submission_requires_round CHECK (submission_id IS NULL OR round_id IS NOT NULL), 
	CONSTRAINT uq_capstmt_id_cycle UNIQUE (capacity_statement_id, cycle_id), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id)
);

CREATE TABLE commercial_lot_market_delta (
	delta_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	reference_item_id VARCHAR(36), 
	target_item_id VARCHAR(36), 
	dc_id VARCHAR(36), 
	supplier_id VARCHAR(36), 
	timeframe_label VARCHAR(120), 
	last_contracted_reference_fob NUMERIC(18, 6), 
	last_contracted_target_fob NUMERIC(18, 6), 
	delta_value NUMERIC(18, 6) NOT NULL, 
	delta_type cpm_lot_delta_type_enum NOT NULL, 
	source_contract VARCHAR(120), 
	source_date DATE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(120) NOT NULL, 
	PRIMARY KEY (delta_id), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(reference_item_id) REFERENCES item_master (item_id), 
	FOREIGN KEY(target_item_id) REFERENCES item_master (item_id), 
	FOREIGN KEY(dc_id) REFERENCES dc_master_db (dc_id), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id)
);
CREATE INDEX ix_cpm_lot_delta_cycle ON commercial_lot_market_delta (cycle_id);

CREATE TABLE commercial_market_kickoff_snapshot (
	snapshot_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	market_reference_id VARCHAR(36), 
	reference_name VARCHAR(120) NOT NULL, 
	reference_basis VARCHAR(60), 
	lot_label VARCHAR(120), 
	location VARCHAR(120), 
	market_price NUMERIC(18, 6) NOT NULL, 
	market_as_of_date DATE NOT NULL, 
	captured_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	captured_by VARCHAR(120) NOT NULL, 
	source_notes TEXT, 
	PRIMARY KEY (snapshot_id), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(market_reference_id) REFERENCES commercial_market_reference (market_reference_id)
);
CREATE INDEX ix_cpm_kickoff_cycle ON commercial_market_kickoff_snapshot (cycle_id);

CREATE TABLE commercial_market_proxy_basis (
	proxy_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	pricing_model_id VARCHAR(36), 
	target_item_id VARCHAR(36), 
	reference_market_fob NUMERIC(18, 6) NOT NULL, 
	historical_contract_delta NUMERIC(18, 6) NOT NULL, 
	target_lot_proxy_fob NUMERIC(18, 6) NOT NULL, 
	delta_type cpm_proxy_delta_type_enum NOT NULL, 
	delta_basis cpm_proxy_delta_basis_enum NOT NULL, 
	fallback_level_used INTEGER NOT NULL, 
	confidence_level cpm_proxy_confidence_enum NOT NULL, 
	manual_override_flag BOOLEAN NOT NULL, 
	manual_override_reason TEXT, 
	delta_source_contract VARCHAR(120), 
	delta_source_date DATE, 
	notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(120) NOT NULL, 
	PRIMARY KEY (proxy_id), 
	CONSTRAINT ck_cpm_proxy_fallback_range CHECK (fallback_level_used >= 1 AND fallback_level_used <= 5), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(pricing_model_id) REFERENCES commercial_pricing_model (pricing_model_id), 
	FOREIGN KEY(target_item_id) REFERENCES item_master (item_id)
);
CREATE INDEX ix_cpm_proxy_cycle ON commercial_market_proxy_basis (cycle_id);

CREATE TABLE commercial_market_reference (
	market_reference_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	reference_source VARCHAR(120) NOT NULL, 
	reference_commodity VARCHAR(120), 
	reference_pack VARCHAR(120), 
	reference_region VARCHAR(120), 
	reference_price_type VARCHAR(60), 
	market_reference_price NUMERIC(18, 6), 
	market_reference_mid NUMERIC(18, 6), 
	derived_trailing_mid NUMERIC(18, 6), 
	awarded_spread NUMERIC(18, 6), 
	reset_cadence cpm_reset_cadence_enum, 
	trigger_band_pct NUMERIC(9, 6), 
	trigger_confirmation_days INTEGER, 
	collar_floor NUMERIC(18, 6), 
	collar_cap NUMERIC(18, 6), 
	freight_passthrough BOOLEAN NOT NULL, 
	as_of_date DATE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(120) NOT NULL, 
	PRIMARY KEY (market_reference_id), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id)
);
CREATE INDEX ix_cpm_market_ref_cycle ON commercial_market_reference (cycle_id, reference_source);

CREATE TABLE commercial_price_component (
	component_id VARCHAR(36) NOT NULL, 
	pricing_model_id VARCHAR(36) NOT NULL, 
	component_type cpm_component_type_enum NOT NULL, 
	plane cpm_component_plane_enum NOT NULL, 
	component_value NUMERIC(18, 6), 
	notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (component_id), 
	FOREIGN KEY(pricing_model_id) REFERENCES commercial_pricing_model (pricing_model_id)
);
CREATE INDEX ix_cpm_component_model ON commercial_price_component (pricing_model_id, plane);

CREATE TABLE commercial_pricing_formula_audit (
	audit_id VARCHAR(36) NOT NULL, 
	pricing_model_id VARCHAR(36) NOT NULL, 
	formula_type cpm_formula_type_enum NOT NULL, 
	formula_inputs TEXT, 
	source_rows TEXT, 
	market_reference_id VARCHAR(36), 
	proxy_id VARCHAR(36), 
	user_override_applied BOOLEAN NOT NULL, 
	user_override_reason TEXT, 
	calculated_value NUMERIC(18, 6) NOT NULL, 
	raw_value_link NUMERIC(18, 6), 
	derived_value_link NUMERIC(18, 6), 
	formula_version VARCHAR(40) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(120) NOT NULL, 
	PRIMARY KEY (audit_id), 
	FOREIGN KEY(pricing_model_id) REFERENCES commercial_pricing_model (pricing_model_id), 
	FOREIGN KEY(market_reference_id) REFERENCES commercial_market_reference (market_reference_id), 
	FOREIGN KEY(proxy_id) REFERENCES commercial_market_proxy_basis (proxy_id)
);
CREATE INDEX ix_cpm_audit_model ON commercial_pricing_formula_audit (pricing_model_id);

CREATE TABLE commercial_pricing_model (
	pricing_model_id VARCHAR(36) NOT NULL, 
	pricing_run_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	dc_id VARCHAR(36) NOT NULL, 
	item_id VARCHAR(36) NOT NULL, 
	supplier_id VARCHAR(36), 
	window_id VARCHAR(36), 
	pricing_model_type cpm_model_type_enum NOT NULL, 
	lane cpm_lane_enum NOT NULL, 
	routing_basis cpm_routing_basis_enum, 
	market_reference_id VARCHAR(36), 
	raw_supplier_value NUMERIC(18, 6), 
	system_derived_value NUMERIC(18, 6), 
	normalized_comparable_value NUMERIC(18, 6), 
	raw_routing_basis VARCHAR(40), 
	normalization_status cpm_normalization_status_enum NOT NULL, 
	override_value NUMERIC(18, 6), 
	override_reason TEXT, 
	override_user VARCHAR(120), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(120) NOT NULL, 
	PRIMARY KEY (pricing_model_id), 
	CONSTRAINT uq_cpm_priced_offer_grain UNIQUE (cycle_id, dc_id, item_id, supplier_id, window_id, pricing_model_type), 
	CONSTRAINT ck_cpm_normalized_nonneg CHECK (normalized_comparable_value IS NULL OR normalized_comparable_value >= 0), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(dc_id) REFERENCES dc_master_db (dc_id), 
	FOREIGN KEY(item_id) REFERENCES item_master (item_id), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id), 
	FOREIGN KEY(window_id) REFERENCES commercial_pricing_window (window_id), 
	FOREIGN KEY(market_reference_id) REFERENCES commercial_market_reference (market_reference_id)
);
CREATE INDEX ix_cpm_cycle_grain ON commercial_pricing_model (cycle_id, dc_id, item_id);
CREATE INDEX ix_cpm_run ON commercial_pricing_model (pricing_run_id);

CREATE TABLE commercial_pricing_validation_issue (
	issue_id VARCHAR(36) NOT NULL, 
	pricing_run_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36), 
	pricing_model_id VARCHAR(36), 
	issue_code cpm_issue_code_enum NOT NULL, 
	severity cpm_issue_severity_enum NOT NULL, 
	field_name TEXT, 
	raw_value TEXT, 
	message TEXT NOT NULL, 
	action_needed TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (issue_id), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(pricing_model_id) REFERENCES commercial_pricing_model (pricing_model_id)
);
CREATE INDEX ix_cpm_issue_run_severity ON commercial_pricing_validation_issue (pricing_run_id, severity);

CREATE TABLE commercial_pricing_window (
	window_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	label cpm_window_label_enum NOT NULL, 
	window_start DATE NOT NULL, 
	window_end DATE NOT NULL, 
	source_owner VARCHAR(120) NOT NULL, 
	commodity_id VARCHAR(36), 
	subcommodity_id VARCHAR(36), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(120) NOT NULL, 
	PRIMARY KEY (window_id), 
	CONSTRAINT ck_cpm_window_range CHECK (window_end >= window_start), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id)
);
CREATE INDEX ix_cpm_window_cycle ON commercial_pricing_window (cycle_id, label);

CREATE TABLE commercial_qdp (
	qdp_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	pricing_model_id VARCHAR(36), 
	qdp_basis cpm_qdp_basis_enum NOT NULL, 
	qdp_rate NUMERIC(9, 6), 
	qdp_value NUMERIC(18, 6), 
	qdp_source VARCHAR(120) NOT NULL, 
	applies_before_discount BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(120) NOT NULL, 
	PRIMARY KEY (qdp_id), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(pricing_model_id) REFERENCES commercial_pricing_model (pricing_model_id)
);
CREATE INDEX ix_cpm_qdp_cycle ON commercial_qdp (cycle_id);

CREATE TABLE commodity_master_db (
	commodity_id VARCHAR(36) NOT NULL, 
	commodity_code VARCHAR(40) NOT NULL, 
	commodity_name VARCHAR(120) NOT NULL, 
	abbreviation VARCHAR(20), 
	active_flag BOOLEAN NOT NULL, 
	PRIMARY KEY (commodity_id), 
	UNIQUE (commodity_code), 
	UNIQUE (commodity_name)
);

CREATE TABLE cycle_invited_supplier (
	cycle_id VARCHAR(36) NOT NULL, 
	supplier_id VARCHAR(36) NOT NULL, 
	invited_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	invited_by VARCHAR(120) NOT NULL, 
	PRIMARY KEY (cycle_id, supplier_id), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id)
);

CREATE TABLE cycle_item_scope (
	cycle_id VARCHAR(36) NOT NULL, 
	item_id VARCHAR(36) NOT NULL, 
	commodity_id VARCHAR(36) NOT NULL, 
	subcommodity_id VARCHAR(36), 
	inclusion_status cycle_item_inclusion_enum NOT NULL, 
	rationale TEXT, 
	added_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	added_by VARCHAR(120) NOT NULL, 
	PRIMARY KEY (cycle_id, item_id), 
	CONSTRAINT fk_scope_cycle_commodity FOREIGN KEY(cycle_id, commodity_id) REFERENCES rfp_cycle (cycle_id, commodity_id), 
	CONSTRAINT fk_scope_cycle_subcom FOREIGN KEY(cycle_id, subcommodity_id) REFERENCES rfp_cycle (cycle_id, subcommodity_id), 
	CONSTRAINT fk_scope_item_commodity FOREIGN KEY(item_id, commodity_id) REFERENCES item_master (item_id, commodity_id), 
	CONSTRAINT fk_scope_item_subcom FOREIGN KEY(item_id, subcommodity_id) REFERENCES item_master (item_id, subcommodity_id), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(item_id) REFERENCES item_master (item_id)
);

CREATE TABLE cycle_lot (
	lot_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	lot_code VARCHAR(40) NOT NULL, 
	lot_name VARCHAR(120) NOT NULL, 
	rationale TEXT, 
	active_flag BOOLEAN NOT NULL, 
	PRIMARY KEY (lot_id), 
	CONSTRAINT uq_lot_code_per_cycle UNIQUE (cycle_id, lot_code), 
	CONSTRAINT uq_lot_cycle_pair UNIQUE (lot_id, cycle_id), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id)
);

CREATE TABLE cycle_lot_item (
	lot_item_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	lot_id VARCHAR(36) NOT NULL, 
	item_id VARCHAR(36) NOT NULL, 
	required_flag BOOLEAN NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (lot_item_id), 
	CONSTRAINT uq_item_per_lot UNIQUE (lot_id, item_id), 
	CONSTRAINT uq_one_lot_per_item_per_cycle UNIQUE (cycle_id, item_id), 
	CONSTRAINT fk_lotitem_lot_in_cycle FOREIGN KEY(lot_id, cycle_id) REFERENCES cycle_lot (lot_id, cycle_id), 
	CONSTRAINT fk_lotitem_in_cycle_scope FOREIGN KEY(cycle_id, item_id) REFERENCES cycle_item_scope (cycle_id, item_id)
);

CREATE TABLE cycle_projected_volume (
	volume_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	dc_id VARCHAR(36) NOT NULL, 
	item_id VARCHAR(36) NOT NULL, 
	tf_id VARCHAR(36) NOT NULL, 
	volume_input_method volume_input_method_enum NOT NULL, 
	projected_weekly_cases NUMERIC(18, 3), 
	projected_period_cases NUMERIC(18, 3) NOT NULL, 
	growth_override_pct NUMERIC(9, 6), 
	normalization_run_id VARCHAR(36), 
	PRIMARY KEY (volume_id), 
	CONSTRAINT uq_volume_cell UNIQUE (cycle_id, dc_id, item_id, tf_id), 
	CONSTRAINT fk_volume_tf_in_cycle FOREIGN KEY(tf_id, cycle_id) REFERENCES cycle_tf (tf_id, cycle_id), 
	CONSTRAINT fk_volume_item_in_cycle_scope FOREIGN KEY(cycle_id, item_id) REFERENCES cycle_item_scope (cycle_id, item_id), 
	CONSTRAINT ck_volume_method_consistency CHECK ((volume_input_method = 'WEEKLY_X_WEEKS' AND projected_weekly_cases IS NOT NULL) OR (volume_input_method = 'DIRECT_PERIOD_CASES' AND projected_weekly_cases IS NULL)), 
	CONSTRAINT ck_volume_period_nonneg CHECK (projected_period_cases >= 0), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(dc_id) REFERENCES dc_master_db (dc_id), 
	FOREIGN KEY(normalization_run_id) REFERENCES normalization_run (normalization_run_id)
);

CREATE TABLE cycle_round (
	round_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	round_number INTEGER NOT NULL, 
	status VARCHAR(40) NOT NULL, 
	round_status round_status_enum, 
	is_final BOOLEAN NOT NULL, 
	invite_due_at TIMESTAMP WITHOUT TIME ZONE, 
	bid_due_at TIMESTAMP WITHOUT TIME ZONE, 
	meeting_due_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (round_id), 
	CONSTRAINT uq_round_number_per_cycle UNIQUE (cycle_id, round_number), 
	CONSTRAINT uq_round_cycle_pair UNIQUE (round_id, cycle_id), 
	CONSTRAINT ck_round_number_positive CHECK (round_number > 0), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id)
);

CREATE TABLE cycle_tf (
	tf_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	tf_code VARCHAR(20) NOT NULL, 
	tf_name VARCHAR(120) NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	week_count INTEGER NOT NULL, 
	rationale TEXT, 
	PRIMARY KEY (tf_id), 
	CONSTRAINT uq_tf_code_per_cycle UNIQUE (cycle_id, tf_code), 
	CONSTRAINT uq_tf_cycle_pair UNIQUE (tf_id, cycle_id), 
	CONSTRAINT ck_tf_week_count_positive CHECK (week_count > 0), 
	CONSTRAINT ck_tf_date_range_positive CHECK (end_date > start_date), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id)
);

CREATE TABLE dc_alias (
	dc_alias_id VARCHAR(36) NOT NULL, 
	alias_text TEXT NOT NULL, 
	normalized_alias_text TEXT NOT NULL, 
	dc_id VARCHAR(36) NOT NULL, 
	source dc_alias_source_enum NOT NULL, 
	created_by VARCHAR(120) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	active_flag BOOLEAN NOT NULL, 
	notes TEXT, 
	active_from TIMESTAMP WITHOUT TIME ZONE, 
	active_until TIMESTAMP WITHOUT TIME ZONE, 
	deactivated_by VARCHAR(120), 
	deactivated_at TIMESTAMP WITHOUT TIME ZONE, 
	deactivation_reason TEXT, 
	PRIMARY KEY (dc_alias_id), 
	CONSTRAINT ck_dc_alias_deactivation_consistency CHECK ((active_flag = 1 AND deactivated_at IS NULL AND deactivated_by IS NULL AND deactivation_reason IS NULL) OR (active_flag = 0 AND deactivated_at IS NOT NULL AND deactivated_by IS NOT NULL AND deactivation_reason IS NOT NULL)), 
	FOREIGN KEY(dc_id) REFERENCES dc_master_db (dc_id)
);
CREATE UNIQUE INDEX uq_dc_alias_normalized_active ON dc_alias (normalized_alias_text) WHERE active_flag = TRUE;

CREATE TABLE dc_master_db (
	dc_id VARCHAR(36) NOT NULL, 
	dc_code VARCHAR(10) NOT NULL, 
	dc_name VARCHAR(120) NOT NULL, 
	region VARCHAR(40), 
	division VARCHAR(40), 
	active_flag BOOLEAN NOT NULL, 
	PRIMARY KEY (dc_id), 
	UNIQUE (dc_code), 
	UNIQUE (dc_name)
);

CREATE TABLE decision_note (
	note_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	round_id VARCHAR(36), 
	scenario_run_id VARCHAR(36), 
	supplier_id VARCHAR(36), 
	dc_id VARCHAR(36), 
	lot_id VARCHAR(36), 
	tf_id VARCHAR(36), 
	author VARCHAR(120) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	note_text TEXT NOT NULL, 
	PRIMARY KEY (note_id), 
	CONSTRAINT ck_decision_note_text_not_empty CHECK (length(note_text) > 0), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(round_id) REFERENCES cycle_round (round_id), 
	FOREIGN KEY(scenario_run_id) REFERENCES calculation_run (calc_run_id), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id), 
	FOREIGN KEY(dc_id) REFERENCES dc_master_db (dc_id), 
	FOREIGN KEY(lot_id) REFERENCES cycle_lot (lot_id), 
	FOREIGN KEY(tf_id) REFERENCES cycle_tf (tf_id)
);

CREATE TABLE eligibility_exception (
	exception_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	supplier_id VARCHAR(36) NOT NULL, 
	dc_id VARCHAR(36) NOT NULL, 
	lot_id VARCHAR(36) NOT NULL, 
	tf_id VARCHAR(36) NOT NULL, 
	exception_type eligibility_exception_type_enum NOT NULL, 
	rationale TEXT NOT NULL, 
	approver_actor_id VARCHAR(120) NOT NULL, 
	approved_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	evidence_reference TEXT, 
	active BOOLEAN NOT NULL, 
	PRIMARY KEY (exception_id), 
	CONSTRAINT uq_exception_per_cell_type UNIQUE (cycle_id, supplier_id, dc_id, lot_id, tf_id, exception_type), 
	CONSTRAINT fk_exception_lot_in_cycle FOREIGN KEY(lot_id, cycle_id) REFERENCES cycle_lot (lot_id, cycle_id), 
	CONSTRAINT fk_exception_tf_in_cycle FOREIGN KEY(tf_id, cycle_id) REFERENCES cycle_tf (tf_id, cycle_id), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id), 
	FOREIGN KEY(dc_id) REFERENCES dc_master_db (dc_id)
);

CREATE TABLE eligibility_gate_result (
	eligibility_gate_result_id VARCHAR(36) NOT NULL, 
	eligibility_result_id VARCHAR(36) NOT NULL, 
	calc_run_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	round_id VARCHAR(36) NOT NULL, 
	submission_id VARCHAR(36), 
	supplier_id VARCHAR(36) NOT NULL, 
	dc_id VARCHAR(36) NOT NULL, 
	lot_id VARCHAR(36) NOT NULL, 
	tf_id VARCHAR(36) NOT NULL, 
	gate_code eligibility_gate_code_enum NOT NULL, 
	gate_status eligibility_gate_status_enum NOT NULL, 
	reason_code eligibility_reason_enum, 
	reason_detail TEXT, 
	evidence_reference TEXT, 
	evaluated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (eligibility_gate_result_id), 
	CONSTRAINT uq_gate_per_eligibility_result UNIQUE (eligibility_result_id, gate_code), 
	CONSTRAINT fk_gate_calc_run_identity FOREIGN KEY(calc_run_id, cycle_id, round_id) REFERENCES calculation_run (calc_run_id, cycle_id, round_id), 
	CONSTRAINT fk_gate_eligibility_full_identity FOREIGN KEY(eligibility_result_id, calc_run_id, cycle_id, round_id, supplier_id, dc_id, lot_id, tf_id) REFERENCES eligibility_result (eligibility_result_id, calc_run_id, cycle_id, round_id, supplier_id, dc_id, lot_id, tf_id), 
	CONSTRAINT fk_gate_submission_identity FOREIGN KEY(submission_id, cycle_id, round_id, supplier_id) REFERENCES bid_submission (submission_id, cycle_id, round_id, supplier_id), 
	CONSTRAINT ck_gate_deferred_only_for_capacity CHECK (gate_status != 'DEFERRED_SCENARIO' OR gate_code = 'CAPACITY'), 
	CONSTRAINT ck_gate_blocked_has_reason CHECK (gate_status != 'BLOCKED' OR reason_code IS NOT NULL), 
	CONSTRAINT ck_gate_pass_or_na_has_no_reason CHECK (gate_status NOT IN ('PASS','NOT_APPLICABLE') OR reason_code IS NULL), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id), 
	FOREIGN KEY(dc_id) REFERENCES dc_master_db (dc_id)
);

CREATE TABLE eligibility_result (
	eligibility_result_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	round_id VARCHAR(36) NOT NULL, 
	calc_run_id VARCHAR(36) NOT NULL, 
	submission_id VARCHAR(36), 
	supplier_id VARCHAR(36) NOT NULL, 
	dc_id VARCHAR(36) NOT NULL, 
	lot_id VARCHAR(36) NOT NULL, 
	tf_id VARCHAR(36) NOT NULL, 
	is_eligible BOOLEAN NOT NULL, 
	reason_code eligibility_reason_enum NOT NULL, 
	reason_detail TEXT, 
	input_snapshot_reference TEXT, 
	evaluated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	eligibility_scope eligibility_scope_enum NOT NULL, 
	requires_scenario_capacity_validation BOOLEAN NOT NULL, 
	PRIMARY KEY (eligibility_result_id), 
	CONSTRAINT uq_eligibility_per_cell_per_run UNIQUE (cycle_id, round_id, calc_run_id, supplier_id, dc_id, lot_id, tf_id), 
	CONSTRAINT uq_eligibility_result_full_identity UNIQUE (eligibility_result_id, calc_run_id, cycle_id, round_id, supplier_id, dc_id, lot_id, tf_id), 
	CONSTRAINT fk_eligibility_lot_in_cycle FOREIGN KEY(lot_id, cycle_id) REFERENCES cycle_lot (lot_id, cycle_id), 
	CONSTRAINT fk_eligibility_tf_in_cycle FOREIGN KEY(tf_id, cycle_id) REFERENCES cycle_tf (tf_id, cycle_id), 
	CONSTRAINT fk_eligibility_round_in_cycle FOREIGN KEY(round_id, cycle_id) REFERENCES cycle_round (round_id, cycle_id), 
	CONSTRAINT fk_eligibility_calc_run_identity FOREIGN KEY(calc_run_id, cycle_id, round_id) REFERENCES calculation_run (calc_run_id, cycle_id, round_id), 
	CONSTRAINT fk_eligibility_submission_identity FOREIGN KEY(submission_id, cycle_id, round_id, supplier_id) REFERENCES bid_submission (submission_id, cycle_id, round_id, supplier_id), 
	CONSTRAINT ck_eligibility_true_requires_eligible_reason_and_submission CHECK ((is_eligible = 0) OR (reason_code = 'ELIGIBLE' AND submission_id IS NOT NULL)), 
	CONSTRAINT ck_eligibility_reason_eligible_requires_true_and_submission CHECK ((reason_code != 'ELIGIBLE') OR (is_eligible = 1 AND submission_id IS NOT NULL)), 
	CONSTRAINT ck_eligibility_null_submission_blocks_eligible CHECK ((submission_id IS NOT NULL) OR (is_eligible = 0)), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id), 
	FOREIGN KEY(dc_id) REFERENCES dc_master_db (dc_id)
);

CREATE TABLE engine_release (
	engine_release_id VARCHAR(36) NOT NULL, 
	release_label VARCHAR(60) NOT NULL, 
	git_commit_sha VARCHAR(64) NOT NULL, 
	status engine_release_status_enum NOT NULL, 
	released_at TIMESTAMP WITHOUT TIME ZONE, 
	test_status VARCHAR(40), 
	notes TEXT, 
	PRIMARY KEY (engine_release_id), 
	CONSTRAINT uq_engine_release_label UNIQUE (release_label), 
	CONSTRAINT uq_engine_release_sha UNIQUE (git_commit_sha), 
	CONSTRAINT ck_engine_released_requires_timestamp CHECK ((status IN ('RELEASED','DEPRECATED') AND released_at IS NOT NULL) OR status IN ('DRAFT','TESTED')), 
	CONSTRAINT ck_engine_sha_min_length CHECK (length(git_commit_sha) >= 7)
);

CREATE TABLE fiscal_date_conversion (
	calendar_date DATE NOT NULL, 
	fiscal_year INTEGER NOT NULL, 
	fiscal_quarter_number INTEGER NOT NULL, 
	fiscal_quarter_label VARCHAR(20), 
	fiscal_period_number INTEGER NOT NULL, 
	fiscal_period_label VARCHAR(20), 
	fiscal_period_week_number INTEGER NOT NULL, 
	fiscal_week_number INTEGER NOT NULL, 
	fiscal_week_label VARCHAR(20), 
	source_calendar_id VARCHAR(36), 
	source_file TEXT, 
	loaded_at TIMESTAMP WITHOUT TIME ZONE, 
	loaded_by VARCHAR(120), 
	PRIMARY KEY (calendar_date), 
	CONSTRAINT ck_fiscal_date_quarter_range CHECK (fiscal_quarter_number >= 1 AND fiscal_quarter_number <= 4), 
	CONSTRAINT ck_fiscal_date_period_range CHECK (fiscal_period_number >= 1 AND fiscal_period_number <= 13), 
	CONSTRAINT ck_fiscal_date_period_week_range CHECK (fiscal_period_week_number >= 1 AND fiscal_period_week_number <= 5), 
	CONSTRAINT ck_fiscal_date_week_range CHECK (fiscal_week_number >= 1 AND fiscal_week_number <= 53)
);

CREATE TABLE historical_award_assignment (
	assignment_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	dc_id VARCHAR(36) NOT NULL, 
	item_id VARCHAR(36) NOT NULL, 
	supplier_id VARCHAR(36) NOT NULL, 
	effective_start_date DATE NOT NULL, 
	effective_end_date DATE NOT NULL, 
	awarded_volume_cases NUMERIC(18, 6) NOT NULL, 
	weekly_volume_cases NUMERIC(18, 6), 
	nat_local_tag hac_nat_local_enum, 
	conv_org_tag hac_conv_org_enum, 
	rpc_required_flag BOOLEAN, 
	rpc_size_text TEXT, 
	source_artifact TEXT, 
	source_sheet TEXT, 
	source_row INTEGER, 
	ingestion_run_id VARCHAR(36) NOT NULL, 
	award_round_id VARCHAR(36), 
	incumbent_flag BOOLEAN, 
	notes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(120) NOT NULL, 
	PRIMARY KEY (assignment_id), 
	CONSTRAINT uq_historical_award_assignment_identity UNIQUE (cycle_id, dc_id, item_id, supplier_id, effective_start_date, effective_end_date), 
	CONSTRAINT ck_historical_award_date_range CHECK (effective_end_date >= effective_start_date), 
	CONSTRAINT ck_historical_award_volume_nonneg CHECK (awarded_volume_cases >= 0), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(dc_id) REFERENCES dc_master_db (dc_id), 
	FOREIGN KEY(item_id) REFERENCES item_master (item_id), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id), 
	FOREIGN KEY(award_round_id) REFERENCES cycle_round (round_id)
);

CREATE TABLE historical_awarded_cost_ingestion_issue (
	issue_id VARCHAR(36) NOT NULL, 
	ingestion_run_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36), 
	source_artifact TEXT, 
	source_sheet TEXT, 
	source_row INTEGER, 
	field_name TEXT, 
	issue_code historical_ingestion_issue_code_enum NOT NULL, 
	severity historical_ingestion_issue_severity_enum NOT NULL, 
	raw_value TEXT, 
	normalized_value TEXT, 
	message TEXT NOT NULL, 
	action_needed TEXT, 
	resolved_status historical_ingestion_issue_resolved_status_enum NOT NULL, 
	resolved_by VARCHAR(120), 
	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	assignment_id VARCHAR(36), 
	PRIMARY KEY (issue_id), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(assignment_id) REFERENCES historical_award_assignment (assignment_id)
);
CREATE INDEX ix_hac_ingestion_issue_cycle_resolved ON historical_awarded_cost_ingestion_issue (cycle_id, resolved_status);
CREATE INDEX ix_hac_ingestion_issue_run_severity ON historical_awarded_cost_ingestion_issue (ingestion_run_id, severity);

CREATE TABLE historical_awarded_price_basis (
	price_basis_id VARCHAR(36) NOT NULL, 
	assignment_id VARCHAR(36) NOT NULL, 
	routing_basis hac_routing_basis_enum NOT NULL, 
	awarded_price_per_case NUMERIC(18, 6) NOT NULL, 
	preferred_basis_flag BOOLEAN NOT NULL, 
	preferred_basis_source TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (price_basis_id), 
	CONSTRAINT uq_historical_price_basis_per_assignment UNIQUE (assignment_id, routing_basis), 
	CONSTRAINT ck_historical_price_nonneg CHECK (awarded_price_per_case >= 0), 
	FOREIGN KEY(assignment_id) REFERENCES historical_award_assignment (assignment_id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX uq_historical_price_basis_one_preferred ON historical_awarded_price_basis (assignment_id) WHERE preferred_basis_flag = TRUE;

CREATE TABLE item_alias (
	item_alias_id VARCHAR(36) NOT NULL, 
	alias_text TEXT NOT NULL, 
	normalized_alias_text TEXT NOT NULL, 
	item_id VARCHAR(36) NOT NULL, 
	alias_type item_alias_type_enum NOT NULL, 
	source item_alias_source_enum NOT NULL, 
	created_by VARCHAR(120) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	active_flag BOOLEAN NOT NULL, 
	notes TEXT, 
	commodity_id VARCHAR(36), 
	subcommodity_id VARCHAR(36), 
	active_from TIMESTAMP WITHOUT TIME ZONE, 
	active_until TIMESTAMP WITHOUT TIME ZONE, 
	deactivated_by VARCHAR(120), 
	deactivated_at TIMESTAMP WITHOUT TIME ZONE, 
	deactivation_reason TEXT, 
	PRIMARY KEY (item_alias_id), 
	CONSTRAINT ck_item_alias_deactivation_consistency CHECK ((active_flag = 1 AND deactivated_at IS NULL AND deactivated_by IS NULL AND deactivation_reason IS NULL) OR (active_flag = 0 AND deactivated_at IS NOT NULL AND deactivated_by IS NOT NULL AND deactivation_reason IS NOT NULL)), 
	FOREIGN KEY(item_id) REFERENCES item_master (item_id), 
	FOREIGN KEY(commodity_id) REFERENCES commodity_master_db (commodity_id), 
	FOREIGN KEY(subcommodity_id) REFERENCES subcommodity_master (subcommodity_id)
);
CREATE UNIQUE INDEX uq_item_alias_norm_typed_active ON item_alias (alias_type, normalized_alias_text, COALESCE(commodity_id, '__GLOBAL__'), COALESCE(subcommodity_id, '__ANY__')) WHERE active_flag = TRUE;

CREATE TABLE item_master (
	item_id VARCHAR(36) NOT NULL, 
	upc VARCHAR(40), 
	item_code VARCHAR(60) NOT NULL, 
	description VARCHAR(300) NOT NULL, 
	pack_desc VARCHAR(60), 
	commodity_id VARCHAR(36) NOT NULL, 
	subcommodity_id VARCHAR(36), 
	active_start DATE, 
	active_end DATE, 
	PRIMARY KEY (item_id), 
	CONSTRAINT fk_item_subcom_in_commodity FOREIGN KEY(subcommodity_id, commodity_id) REFERENCES subcommodity_master (subcommodity_id, commodity_id), 
	CONSTRAINT uq_item_commodity_pair UNIQUE (item_id, commodity_id), 
	CONSTRAINT uq_item_subcom_pair UNIQUE (item_id, subcommodity_id), 
	UNIQUE (upc), 
	UNIQUE (item_code), 
	FOREIGN KEY(commodity_id) REFERENCES commodity_master_db (commodity_id)
);

CREATE TABLE landed_cost_result (
	landed_cost_result_id VARCHAR(36) NOT NULL, 
	calc_run_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	round_id VARCHAR(36) NOT NULL, 
	bid_line_id VARCHAR(36) NOT NULL, 
	supplier_id VARCHAR(36) NOT NULL, 
	dc_id VARCHAR(36) NOT NULL, 
	lot_id VARCHAR(36) NOT NULL, 
	item_id VARCHAR(36) NOT NULL, 
	tf_id VARCHAR(36) NOT NULL, 
	metric_version_id VARCHAR(36) NOT NULL, 
	landed_cost_mode landed_cost_mode_enum NOT NULL, 
	is_cost_awardable BOOLEAN NOT NULL, 
	blocking_reason_code landed_cost_blocking_reason_enum, 
	blocking_reason_detail TEXT, 
	submitted_all_in_case NUMERIC(18, 6), 
	reconstructed_all_in_case NUMERIC(18, 6), 
	authoritative_landed_cost_case NUMERIC(18, 6), 
	variance_case NUMERIC(18, 6), 
	tolerance_case_used NUMERIC(18, 6) NOT NULL, 
	loading_location_id VARCHAR(36), 
	loading_location_valid_flag BOOLEAN NOT NULL, 
	formula_version_reference VARCHAR(120) NOT NULL, 
	calculated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (landed_cost_result_id), 
	CONSTRAINT uq_landed_cost_per_bidline_per_run UNIQUE (calc_run_id, bid_line_id), 
	CONSTRAINT fk_landed_cost_calc_run_identity FOREIGN KEY(calc_run_id, cycle_id, round_id) REFERENCES calculation_run (calc_run_id, cycle_id, round_id), 
	CONSTRAINT fk_landed_cost_metric_matches_run FOREIGN KEY(calc_run_id, cycle_id, round_id, metric_version_id) REFERENCES calculation_run (calc_run_id, cycle_id, round_id, metric_version_id), 
	CONSTRAINT fk_landed_cost_bidline_full_identity FOREIGN KEY(bid_line_id, cycle_id, round_id, supplier_id, dc_id, lot_id, item_id, tf_id) REFERENCES bid_line (bid_line_id, cycle_id, round_id, supplier_id, dc_id, lot_id, item_id, tf_id), 
	CONSTRAINT fk_landed_cost_loc_belongs_to_supplier FOREIGN KEY(loading_location_id, supplier_id) REFERENCES loading_location (location_id, supplier_id), 
	CONSTRAINT ck_landed_cost_tol_nonneg CHECK (tolerance_case_used >= 0), 
	CONSTRAINT ck_landed_cost_awardable_shape CHECK ((is_cost_awardable = 0) OR (landed_cost_mode IN ('DIRECT_ALL_IN','RECONCILED_ALL_IN','RECONSTRUCTED_APPROVED') AND authoritative_landed_cost_case IS NOT NULL AND authoritative_landed_cost_case > 0 AND blocking_reason_code IS NULL)), 
	CONSTRAINT ck_landed_cost_nonawardable_shape CHECK ((is_cost_awardable = 1) OR (landed_cost_mode IN ('MISMATCH_BLOCKED','FOB_PREVIEW_ONLY') AND authoritative_landed_cost_case IS NULL AND blocking_reason_code IS NOT NULL)), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id), 
	FOREIGN KEY(dc_id) REFERENCES dc_master_db (dc_id), 
	FOREIGN KEY(metric_version_id) REFERENCES metric_definition_version (metric_version_id)
);

CREATE TABLE loading_location (
	location_id VARCHAR(36) NOT NULL, 
	supplier_id VARCHAR(36) NOT NULL, 
	location_name VARCHAR(160) NOT NULL, 
	address_line VARCHAR(300), 
	city VARCHAR(80) NOT NULL, 
	country_code VARCHAR(2) NOT NULL, 
	region_code VARCHAR(10), 
	postal_code VARCHAR(20), 
	active_start DATE, 
	active_end DATE, 
	evidence_reference TEXT, 
	active_flag BOOLEAN NOT NULL, 
	PRIMARY KEY (location_id), 
	CONSTRAINT uq_loc_supplier_pair UNIQUE (location_id, supplier_id), 
	CONSTRAINT ck_loc_country_code_two_char CHECK (length(country_code) = 2), 
	CONSTRAINT ck_loc_active_dates_ordered CHECK (active_end IS NULL OR active_start IS NULL OR active_end >= active_start), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id)
);
CREATE UNIQUE INDEX uq_loc_supplier_name_geo ON loading_location (supplier_id, location_name, country_code, COALESCE(region_code, ''), city);

CREATE TABLE master_data_quarantine (
	quarantine_id VARCHAR(36) NOT NULL, 
	source_artifact TEXT NOT NULL, 
	source_sheet TEXT NOT NULL, 
	source_row INTEGER NOT NULL, 
	raw_value TEXT NOT NULL, 
	normalized_value TEXT NOT NULL, 
	domain quarantine_domain_enum NOT NULL, 
	rejection_reason quarantine_rejection_reason_enum NOT NULL, 
	candidate_matches_json TEXT, 
	ingestion_run_id VARCHAR(80) NOT NULL, 
	cycle_id VARCHAR(36), 
	resolved_action quarantine_resolved_action_enum, 
	analyst_resolution quarantine_resolution_enum NOT NULL, 
	resolved_alias_id VARCHAR(36), 
	resolved_to_target_id VARCHAR(36), 
	resolved_by VARCHAR(120), 
	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	notes TEXT, 
	PRIMARY KEY (quarantine_id), 
	CONSTRAINT uq_quarantine_source_row_domain UNIQUE (source_artifact, source_sheet, source_row, domain), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id)
);

CREATE TABLE metric_definition_version (
	metric_version_id VARCHAR(36) NOT NULL, 
	formula_family VARCHAR(80) NOT NULL, 
	version_code VARCHAR(40) NOT NULL, 
	status metric_status_enum NOT NULL, 
	expression_text TEXT NOT NULL, 
	effective_from TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	approved_by VARCHAR(120), 
	tolerance_abs NUMERIC(18, 6), 
	tolerance_pct NUMERIC(9, 6), 
	PRIMARY KEY (metric_version_id), 
	CONSTRAINT uq_formula_family_version UNIQUE (formula_family, version_code)
);

CREATE TABLE normalization_run (
	normalization_run_id VARCHAR(36) NOT NULL, 
	dataset_type normalization_dataset_type_enum NOT NULL, 
	cycle_id VARCHAR(36), 
	status normalization_status_enum NOT NULL, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	approved_by VARCHAR(120), 
	PRIMARY KEY (normalization_run_id), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id)
);

CREATE TABLE normalization_run_source (
	normalization_run_id VARCHAR(36) NOT NULL, 
	source_artifact_id VARCHAR(36) NOT NULL, 
	source_role normalization_source_role_enum NOT NULL, 
	added_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (normalization_run_id, source_artifact_id), 
	FOREIGN KEY(normalization_run_id) REFERENCES normalization_run (normalization_run_id), 
	FOREIGN KEY(source_artifact_id) REFERENCES source_artifact (artifact_id)
);

CREATE TABLE normalized_volume_scope (
	scope_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	source_row_id VARCHAR(36) NOT NULL, 
	dc_id VARCHAR(36) NOT NULL, 
	item_id VARCHAR(36) NOT NULL, 
	supplier_id VARCHAR(36), 
	commodity_id VARCHAR(36), 
	subcommodity_id VARCHAR(36), 
	source_type vsp_norm_source_type_enum NOT NULL, 
	precedence_rank INTEGER NOT NULL, 
	timeframe_start_date DATE NOT NULL, 
	timeframe_end_date DATE NOT NULL, 
	volume_measure NUMERIC(18, 6) NOT NULL, 
	unit_of_measure VARCHAR(40) NOT NULL, 
	fiscal_year INTEGER, 
	fiscal_period_number INTEGER, 
	routing_basis vsp_norm_routing_basis_enum, 
	active_demand_flag BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(120) NOT NULL, 
	PRIMARY KEY (scope_id), 
	CONSTRAINT ck_vsp_norm_volume_nonneg CHECK (volume_measure >= 0), 
	CONSTRAINT ck_vsp_norm_timeframe_range CHECK (timeframe_end_date >= timeframe_start_date), 
	CONSTRAINT ck_vsp_norm_precedence_range CHECK (precedence_rank >= 1 AND precedence_rank <= 4), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(source_row_id) REFERENCES volume_scope_source_row (source_row_id), 
	FOREIGN KEY(dc_id) REFERENCES dc_master_db (dc_id), 
	FOREIGN KEY(item_id) REFERENCES item_master (item_id), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id)
);
CREATE INDEX ix_vsp_norm_cycle_grain ON normalized_volume_scope (cycle_id, dc_id, item_id);

CREATE TABLE rfp_cycle (
	cycle_id VARCHAR(36) NOT NULL, 
	cycle_code VARCHAR(40) NOT NULL, 
	cycle_name VARCHAR(120) NOT NULL, 
	commodity_id VARCHAR(36) NOT NULL, 
	subcommodity_id VARCHAR(36), 
	status cycle_status_enum NOT NULL, 
	why_now TEXT NOT NULL, 
	target_effective_date DATE NOT NULL, 
	target_savings_amt NUMERIC(18, 2), 
	round_count INTEGER NOT NULL, 
	owner_actor_id VARCHAR(120), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(120) NOT NULL, 
	PRIMARY KEY (cycle_id), 
	CONSTRAINT ck_cycle_round_count_range CHECK (round_count BETWEEN 2 AND 6), 
	CONSTRAINT fk_cycle_subcom_in_commodity FOREIGN KEY(subcommodity_id, commodity_id) REFERENCES subcommodity_master (subcommodity_id, commodity_id), 
	CONSTRAINT uq_cycle_commodity_pair UNIQUE (cycle_id, commodity_id), 
	CONSTRAINT uq_cycle_subcom_pair UNIQUE (cycle_id, subcommodity_id), 
	UNIQUE (cycle_code), 
	FOREIGN KEY(commodity_id) REFERENCES commodity_master_db (commodity_id)
);

CREATE TABLE round_analysis_snapshot (
	snapshot_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	round_id VARCHAR(36) NOT NULL, 
	calc_run_id VARCHAR(36) NOT NULL, 
	snapshot_label VARCHAR(160) NOT NULL, 
	is_canonical BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(120) NOT NULL, 
	PRIMARY KEY (snapshot_id), 
	CONSTRAINT fk_ras_round_in_cycle FOREIGN KEY(round_id, cycle_id) REFERENCES cycle_round (round_id, cycle_id), 
	CONSTRAINT uq_ras_one_link_per_run_per_round UNIQUE (cycle_id, round_id, calc_run_id), 
	CONSTRAINT ck_ras_label_not_empty CHECK (length(snapshot_label) > 0), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(calc_run_id) REFERENCES calculation_run (calc_run_id)
);

CREATE TABLE round_feedback_issued (
	feedback_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	round_id VARCHAR(36) NOT NULL, 
	supplier_id VARCHAR(36) NOT NULL, 
	feedback_text TEXT NOT NULL, 
	drafted_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	drafted_by VARCHAR(120) NOT NULL, 
	status round_feedback_draft_status_enum NOT NULL, 
	PRIMARY KEY (feedback_id), 
	CONSTRAINT fk_rfi_round_in_cycle FOREIGN KEY(round_id, cycle_id) REFERENCES cycle_round (round_id, cycle_id), 
	CONSTRAINT ck_rfi_feedback_text_not_empty CHECK (length(feedback_text) > 0), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id)
);
CREATE INDEX ix_rfi_cycle_round_supplier ON round_feedback_issued (cycle_id, round_id, supplier_id);

CREATE TABLE round_field_reduction_decision (
	decision_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	round_id VARCHAR(36) NOT NULL, 
	next_round_invitation_list_json TEXT NOT NULL, 
	decided_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	decided_by VARCHAR(120) NOT NULL, 
	rationale_text TEXT, 
	PRIMARY KEY (decision_id), 
	CONSTRAINT fk_rfrd_round_in_cycle FOREIGN KEY(round_id, cycle_id) REFERENCES cycle_round (round_id, cycle_id), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id)
);
CREATE INDEX ix_rfrd_cycle_round ON round_field_reduction_decision (cycle_id, round_id);

CREATE TABLE round_supplier_participation (
	participation_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	round_id VARCHAR(36) NOT NULL, 
	supplier_id VARCHAR(36) NOT NULL, 
	participation_status round_participation_status_enum NOT NULL, 
	decision_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	decided_by VARCHAR(120) NOT NULL, 
	decision_reason_text TEXT, 
	PRIMARY KEY (participation_id), 
	CONSTRAINT fk_rsp_round_in_cycle FOREIGN KEY(round_id, cycle_id) REFERENCES cycle_round (round_id, cycle_id), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id)
);
CREATE INDEX ix_rsp_cycle_round_supplier ON round_supplier_participation (cycle_id, round_id, supplier_id);

CREATE TABLE scenario_a_capacity_usage (
	capacity_usage_id VARCHAR(36) NOT NULL, 
	scenario_run_id VARCHAR(36) NOT NULL, 
	supplier_id VARCHAR(36) NOT NULL, 
	capacity_statement_id VARCHAR(36) NOT NULL, 
	capacity_constraint_id VARCHAR(36) NOT NULL, 
	scope_type scenario_a_capacity_scope_type_enum NOT NULL, 
	capacity_limit_period_cases NUMERIC(18, 3) NOT NULL, 
	assigned_usage_period_cases NUMERIC(18, 3) NOT NULL, 
	remaining_capacity_cases NUMERIC(18, 3) NOT NULL, 
	constraint_satisfied BOOLEAN NOT NULL, 
	PRIMARY KEY (capacity_usage_id), 
	CONSTRAINT uq_scenario_a_capacity_usage_per_constraint UNIQUE (scenario_run_id, capacity_constraint_id), 
	CONSTRAINT ck_scenario_a_capacity_usage_non_negative CHECK (capacity_limit_period_cases >= 0 AND assigned_usage_period_cases >= 0), 
	CONSTRAINT ck_scenario_a_capacity_usage_arithmetic CHECK (remaining_capacity_cases =     capacity_limit_period_cases - assigned_usage_period_cases), 
	CONSTRAINT ck_scenario_a_capacity_usage_satisfied_consistent CHECK ((constraint_satisfied = 1     AND assigned_usage_period_cases <= capacity_limit_period_cases) OR (constraint_satisfied = 0     AND assigned_usage_period_cases > capacity_limit_period_cases)), 
	FOREIGN KEY(scenario_run_id) REFERENCES calculation_run (calc_run_id), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id), 
	FOREIGN KEY(capacity_statement_id) REFERENCES capacity_statement (capacity_statement_id), 
	FOREIGN KEY(capacity_constraint_id) REFERENCES capacity_constraint (capacity_constraint_id)
);

CREATE TABLE scenario_a_cell_assignment (
	cell_assignment_id VARCHAR(36) NOT NULL, 
	scenario_run_id VARCHAR(36) NOT NULL, 
	dc_id VARCHAR(36) NOT NULL, 
	lot_id VARCHAR(36) NOT NULL, 
	tf_id VARCHAR(36) NOT NULL, 
	assignment_status scenario_a_assignment_status_enum NOT NULL, 
	supplier_id VARCHAR(36), 
	upstream_eligibility_result_id VARCHAR(36), 
	cell_period_cases NUMERIC(18, 3) NOT NULL, 
	cell_spend NUMERIC(18, 6), 
	PRIMARY KEY (cell_assignment_id), 
	CONSTRAINT uq_scenario_a_cell_assignment_cell UNIQUE (scenario_run_id, dc_id, lot_id, tf_id), 
	CONSTRAINT ck_scenario_a_cell_assignment_status_shape CHECK ((assignment_status = 'AWARDED'     AND supplier_id IS NOT NULL     AND cell_spend IS NOT NULL AND cell_spend > 0     AND upstream_eligibility_result_id IS NOT NULL) OR (assignment_status = 'NO_FEASIBLE_ASSIGNMENT'     AND supplier_id IS NULL     AND cell_spend IS NULL     AND upstream_eligibility_result_id IS NULL)), 
	CONSTRAINT ck_scenario_a_cell_period_cases_positive CHECK (cell_period_cases > 0), 
	FOREIGN KEY(scenario_run_id) REFERENCES calculation_run (calc_run_id), 
	FOREIGN KEY(dc_id) REFERENCES dc_master_db (dc_id), 
	FOREIGN KEY(lot_id) REFERENCES cycle_lot (lot_id), 
	FOREIGN KEY(tf_id) REFERENCES cycle_tf (tf_id), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id), 
	FOREIGN KEY(upstream_eligibility_result_id) REFERENCES eligibility_result (eligibility_result_id)
);

CREATE TABLE scenario_a_line_detail (
	line_detail_id VARCHAR(36) NOT NULL, 
	scenario_run_id VARCHAR(36) NOT NULL, 
	dc_id VARCHAR(36) NOT NULL, 
	lot_id VARCHAR(36) NOT NULL, 
	tf_id VARCHAR(36) NOT NULL, 
	item_id VARCHAR(36) NOT NULL, 
	supplier_id VARCHAR(36) NOT NULL, 
	upstream_landed_cost_result_id VARCHAR(36) NOT NULL, 
	projected_period_cases NUMERIC(18, 3) NOT NULL, 
	authoritative_landed_cost_case NUMERIC(18, 6) NOT NULL, 
	line_spend NUMERIC(18, 6) NOT NULL, 
	PRIMARY KEY (line_detail_id), 
	CONSTRAINT uq_scenario_a_line_detail_cell_item UNIQUE (scenario_run_id, dc_id, lot_id, tf_id, item_id), 
	CONSTRAINT ck_scenario_a_line_detail_positive CHECK (projected_period_cases > 0 AND authoritative_landed_cost_case > 0 AND line_spend > 0), 
	FOREIGN KEY(scenario_run_id) REFERENCES calculation_run (calc_run_id), 
	FOREIGN KEY(dc_id) REFERENCES dc_master_db (dc_id), 
	FOREIGN KEY(lot_id) REFERENCES cycle_lot (lot_id), 
	FOREIGN KEY(tf_id) REFERENCES cycle_tf (tf_id), 
	FOREIGN KEY(item_id) REFERENCES item_master (item_id), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id), 
	FOREIGN KEY(upstream_landed_cost_result_id) REFERENCES landed_cost_result (landed_cost_result_id)
);

CREATE TABLE scenario_a_result (
	scenario_run_id VARCHAR(36) NOT NULL, 
	upstream_calc_run_id VARCHAR(36) NOT NULL, 
	scenario_code scenario_a_code_enum NOT NULL, 
	solve_status scenario_a_solve_status_enum NOT NULL, 
	objective_total_spend NUMERIC(18, 6), 
	solver_version_reference VARCHAR(120) NOT NULL, 
	calculated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (scenario_run_id), 
	CONSTRAINT ck_scenario_a_result_status_objective CHECK ((solve_status = 'FEASIBLE'     AND objective_total_spend IS NOT NULL     AND objective_total_spend > 0) OR (solve_status = 'INFEASIBLE'     AND objective_total_spend IS NULL)), 
	FOREIGN KEY(scenario_run_id) REFERENCES calculation_run (calc_run_id), 
	FOREIGN KEY(upstream_calc_run_id) REFERENCES calculation_run (calc_run_id)
);

CREATE TABLE scenario_config_version (
	scenario_config_version_id VARCHAR(36) NOT NULL, 
	config_label VARCHAR(120) NOT NULL, 
	version_code VARCHAR(40) NOT NULL, 
	status scenario_config_status_enum NOT NULL, 
	parameters_json TEXT NOT NULL, 
	effective_from TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	approved_by VARCHAR(120), 
	PRIMARY KEY (scenario_config_version_id), 
	CONSTRAINT uq_scenario_config_label_version UNIQUE (config_label, version_code)
);

CREATE TABLE source_artifact (
	artifact_id VARCHAR(36) NOT NULL, 
	artifact_type source_artifact_type_enum NOT NULL, 
	file_name VARCHAR(300) NOT NULL, 
	file_hash_sha256 VARCHAR(64) NOT NULL, 
	received_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	location_reference VARCHAR(500), 
	status source_artifact_status_enum NOT NULL, 
	cycle_id VARCHAR(36), 
	round_id VARCHAR(36), 
	supplier_id VARCHAR(36), 
	created_by VARCHAR(120) NOT NULL, 
	PRIMARY KEY (artifact_id), 
	CONSTRAINT fk_artifact_round_in_cycle FOREIGN KEY(round_id, cycle_id) REFERENCES cycle_round (round_id, cycle_id), 
	CONSTRAINT ck_artifact_bid_provenance CHECK (artifact_type <> 'BID_SUBMISSION' OR (cycle_id IS NOT NULL AND round_id IS NOT NULL AND supplier_id IS NOT NULL)), 
	CONSTRAINT ck_artifact_capacity_provenance CHECK (artifact_type <> 'CAPACITY_EVIDENCE' OR (cycle_id IS NOT NULL AND supplier_id IS NOT NULL)), 
	CONSTRAINT uq_artifact_identity_quad UNIQUE (artifact_id, cycle_id, round_id, supplier_id), 
	CONSTRAINT uq_artifact_cycle_supplier UNIQUE (artifact_id, cycle_id, supplier_id), 
	CONSTRAINT uq_artifact_round UNIQUE (artifact_id, round_id), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id)
);

CREATE TABLE subcommodity_master (
	subcommodity_id VARCHAR(36) NOT NULL, 
	commodity_id VARCHAR(36) NOT NULL, 
	subcommodity_code VARCHAR(40) NOT NULL, 
	subcommodity_name VARCHAR(120) NOT NULL, 
	active_flag BOOLEAN NOT NULL, 
	PRIMARY KEY (subcommodity_id), 
	CONSTRAINT uq_subcom_code_per_commodity UNIQUE (commodity_id, subcommodity_code), 
	CONSTRAINT uq_subcom_commodity_pair UNIQUE (subcommodity_id, commodity_id), 
	FOREIGN KEY(commodity_id) REFERENCES commodity_master_db (commodity_id)
);

CREATE TABLE supplier_alias (
	supplier_alias_id VARCHAR(36) NOT NULL, 
	alias_text TEXT NOT NULL, 
	normalized_alias_text TEXT NOT NULL, 
	supplier_id VARCHAR(36) NOT NULL, 
	alias_type supplier_alias_type_enum NOT NULL, 
	source supplier_alias_source_enum NOT NULL, 
	created_by VARCHAR(120) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	active_flag BOOLEAN NOT NULL, 
	notes TEXT, 
	active_from TIMESTAMP WITHOUT TIME ZONE, 
	active_until TIMESTAMP WITHOUT TIME ZONE, 
	deactivated_by VARCHAR(120), 
	deactivated_at TIMESTAMP WITHOUT TIME ZONE, 
	deactivation_reason TEXT, 
	PRIMARY KEY (supplier_alias_id), 
	CONSTRAINT ck_supplier_alias_deactivation_consistency CHECK ((active_flag = 1 AND deactivated_at IS NULL AND deactivated_by IS NULL AND deactivation_reason IS NULL) OR (active_flag = 0 AND deactivated_at IS NOT NULL AND deactivated_by IS NOT NULL AND deactivation_reason IS NOT NULL)), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id)
);
CREATE UNIQUE INDEX uq_supplier_alias_norm_typed_active ON supplier_alias (alias_type, normalized_alias_text) WHERE active_flag = TRUE;

CREATE TABLE supplier_capability (
	capability_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	supplier_id VARCHAR(36) NOT NULL, 
	dc_id VARCHAR(36) NOT NULL, 
	lot_id VARCHAR(36) NOT NULL, 
	tf_id VARCHAR(36) NOT NULL, 
	status capability_status_enum NOT NULL, 
	evidence_reference TEXT, 
	confirmed_by_actor_id VARCHAR(120), 
	confirmed_at TIMESTAMP WITHOUT TIME ZONE, 
	notes TEXT, 
	PRIMARY KEY (capability_id), 
	CONSTRAINT uq_capability_per_cell UNIQUE (cycle_id, supplier_id, dc_id, lot_id, tf_id), 
	CONSTRAINT fk_capability_lot_in_cycle FOREIGN KEY(lot_id, cycle_id) REFERENCES cycle_lot (lot_id, cycle_id), 
	CONSTRAINT fk_capability_tf_in_cycle FOREIGN KEY(tf_id, cycle_id) REFERENCES cycle_tf (tf_id, cycle_id), 
	CONSTRAINT ck_capability_confirmed_requires_evidence CHECK (status <> 'CONFIRMED_CAPABLE' OR (evidence_reference IS NOT NULL AND confirmed_by_actor_id IS NOT NULL AND confirmed_at IS NOT NULL)), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(supplier_id) REFERENCES supplier_master (supplier_id), 
	FOREIGN KEY(dc_id) REFERENCES dc_master_db (dc_id)
);

CREATE TABLE supplier_master (
	supplier_id VARCHAR(36) NOT NULL, 
	canonical_name VARCHAR(200) NOT NULL, 
	aliases TEXT, 
	active_flag BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (supplier_id), 
	UNIQUE (canonical_name)
);

CREATE TABLE volume_scope_override (
	override_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	source_row_id VARCHAR(36), 
	scope_id VARCHAR(36), 
	affected_scope_desc TEXT NOT NULL, 
	source_type vsp_override_source_type_enum NOT NULL, 
	original_value NUMERIC(18, 6), 
	override_value NUMERIC(18, 6), 
	reason_note TEXT NOT NULL, 
	override_user VARCHAR(120) NOT NULL, 
	override_timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	approval_status vsp_override_approval_enum NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (override_id), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(source_row_id) REFERENCES volume_scope_source_row (source_row_id), 
	FOREIGN KEY(scope_id) REFERENCES normalized_volume_scope (scope_id)
);
CREATE INDEX ix_vsp_override_cycle ON volume_scope_override (cycle_id, source_type);

CREATE TABLE volume_scope_prep_issue (
	issue_id VARCHAR(36) NOT NULL, 
	ingestion_run_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36), 
	source_row_id VARCHAR(36), 
	input_class vsp_issue_input_class_enum, 
	issue_code vsp_issue_code_enum NOT NULL, 
	severity vsp_issue_severity_enum NOT NULL, 
	field_name TEXT, 
	raw_value TEXT, 
	normalized_value TEXT, 
	message TEXT NOT NULL, 
	action_needed TEXT, 
	resolved_status vsp_issue_resolved_status_enum NOT NULL, 
	resolved_by VARCHAR(120), 
	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	source_artifact TEXT, 
	source_sheet TEXT, 
	source_row INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (issue_id), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id), 
	FOREIGN KEY(source_row_id) REFERENCES volume_scope_source_row (source_row_id)
);
CREATE INDEX ix_vsp_issue_cycle_resolved ON volume_scope_prep_issue (cycle_id, resolved_status);
CREATE INDEX ix_vsp_issue_run_severity ON volume_scope_prep_issue (ingestion_run_id, severity);

CREATE TABLE volume_scope_source_row (
	source_row_id VARCHAR(36) NOT NULL, 
	cycle_id VARCHAR(36) NOT NULL, 
	ingestion_run_id VARCHAR(36) NOT NULL, 
	input_class vsp_input_class_enum NOT NULL, 
	source_type vsp_source_type_enum NOT NULL, 
	precedence_rank INTEGER, 
	raw_dc_text TEXT, 
	raw_item_text TEXT, 
	raw_supplier_text TEXT, 
	resolved_dc_id VARCHAR(36), 
	resolved_item_id VARCHAR(36), 
	resolved_supplier_id VARCHAR(36), 
	commodity_id VARCHAR(36), 
	subcommodity_id VARCHAR(36), 
	timeframe_start_date DATE, 
	timeframe_end_date DATE, 
	volume_measure NUMERIC(18, 6), 
	unit_of_measure VARCHAR(40), 
	routing_basis vsp_routing_basis_enum, 
	zero_reason vsp_zero_reason_enum, 
	status vsp_source_status_enum NOT NULL, 
	active_demand_flag BOOLEAN NOT NULL, 
	source_artifact TEXT, 
	source_sheet TEXT, 
	source_row INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_by VARCHAR(120) NOT NULL, 
	PRIMARY KEY (source_row_id), 
	CONSTRAINT ck_vsp_source_timeframe_range CHECK (timeframe_end_date IS NULL OR timeframe_start_date IS NULL OR timeframe_end_date >= timeframe_start_date), 
	CONSTRAINT ck_vsp_capacity_never_active_demand CHECK (input_class = 'DEMAND' OR active_demand_flag = 0), 
	FOREIGN KEY(cycle_id) REFERENCES rfp_cycle (cycle_id)
);
CREATE INDEX ix_vsp_source_cycle_active ON volume_scope_source_row (cycle_id, active_demand_flag);
CREATE INDEX ix_vsp_source_run_status ON volume_scope_source_row (ingestion_run_id, status);

