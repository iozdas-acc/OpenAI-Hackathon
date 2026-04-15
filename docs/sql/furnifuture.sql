CREATE SCHEMA IF NOT EXISTS furnifuture;

CREATE TABLE furnifuture.erp_material_master (
  material_id VARCHAR(30) PRIMARY KEY,
  material_description TEXT NOT NULL,
  material_type_code VARCHAR(10) NOT NULL CHECK (material_type_code IN ('FG', 'HALB', 'ROH', 'PHAN', 'PKG')),
  lifecycle_status VARCHAR(12) NOT NULL CHECK (lifecycle_status IN ('DESIGN', 'RELEASED', 'BLOCKED', 'OBSOLETE')),
  base_uom VARCHAR(10) NOT NULL,
  procurement_type CHAR(1) NOT NULL CHECK (procurement_type IN ('E', 'F', 'X')),
  planning_strategy_code VARCHAR(10) NOT NULL,
  revision_code VARCHAR(12),
  default_plant_code VARCHAR(10),
  material_group VARCHAR(20),
  engineering_owner VARCHAR(50),
  is_serial_tracked BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE furnifuture.erp_bom_component (
  bom_component_id BIGSERIAL PRIMARY KEY,
  parent_material_id VARCHAR(30) NOT NULL REFERENCES furnifuture.erp_material_master(material_id),
  component_material_id VARCHAR(30) NOT NULL REFERENCES furnifuture.erp_material_master(material_id),
  plant_code VARCHAR(10) NOT NULL,
  alternative_bom_no VARCHAR(10) NOT NULL DEFAULT '01',
  line_no INTEGER NOT NULL,
  component_qty NUMERIC(18,4) NOT NULL CHECK (component_qty > 0),
  component_uom VARCHAR(10) NOT NULL,
  component_scrap_pct NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (component_scrap_pct >= 0 AND component_scrap_pct <= 100),
  phantom_item_flag BOOLEAN NOT NULL DEFAULT FALSE,
  component_strategy_code VARCHAR(20) NOT NULL CHECK (component_strategy_code IN ('STOCK', 'PHANTOM', 'NON_STOCK', 'SUBSTITUTE')),
  valid_from_date DATE NOT NULL,
  valid_to_date DATE,
  backflush_flag BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT erp_bom_component_uq UNIQUE (parent_material_id, plant_code, alternative_bom_no, line_no, valid_from_date),
  CONSTRAINT erp_bom_component_date_chk CHECK (valid_to_date IS NULL OR valid_to_date >= valid_from_date)
);

CREATE TABLE furnifuture.erp_inventory_balance (
  inventory_balance_id BIGSERIAL PRIMARY KEY,
  material_id VARCHAR(30) NOT NULL REFERENCES furnifuture.erp_material_master(material_id),
  plant_code VARCHAR(10) NOT NULL,
  storage_location_code VARCHAR(10) NOT NULL,
  stock_status_code VARCHAR(5) NOT NULL CHECK (stock_status_code IN ('UNR', 'QI', 'BLK', 'TRN')),
  unrestricted_qty NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (unrestricted_qty >= 0),
  quality_qty NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (quality_qty >= 0),
  blocked_qty NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (blocked_qty >= 0),
  transfer_qty NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (transfer_qty >= 0),
  special_stock_indicator VARCHAR(4),
  lot_no VARCHAR(30),
  snapshot_ts TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE furnifuture.erp_production_order (
  production_order_id VARCHAR(20) PRIMARY KEY,
  material_id VARCHAR(30) NOT NULL REFERENCES furnifuture.erp_material_master(material_id),
  plant_code VARCHAR(10) NOT NULL,
  order_type_code VARCHAR(10) NOT NULL CHECK (order_type_code IN ('PP01', 'REWK', 'ENGR', 'PROTO')),
  order_status_code VARCHAR(10) NOT NULL CHECK (order_status_code IN ('CRTD', 'REL', 'PCNF', 'CNF', 'TECO')),
  planned_qty NUMERIC(18,4) NOT NULL CHECK (planned_qty > 0),
  released_qty NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (released_qty >= 0),
  confirmed_qty NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (confirmed_qty >= 0),
  scrapped_qty NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (scrapped_qty >= 0),
  scheduled_start_ts TIMESTAMPTZ,
  scheduled_end_ts TIMESTAMPTZ,
  routing_version VARCHAR(12),
  planner_code VARCHAR(20),
  reservation_profile VARCHAR(20),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
