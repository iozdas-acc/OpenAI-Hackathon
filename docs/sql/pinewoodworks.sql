CREATE SCHEMA IF NOT EXISTS pinewoodworks;

CREATE TABLE pinewoodworks.legacy_item_catalog (
  item_no VARCHAR(30) PRIMARY KEY,
  item_desc TEXT NOT NULL,
  item_class VARCHAR(10) NOT NULL CHECK (item_class IN ('ASM', 'BUY', 'KIT', 'PKG', 'MISC')),
  status_code CHAR(1) NOT NULL CHECK (status_code IN ('A', 'H', 'S', 'R', 'D')),
  stock_uom VARCHAR(10) NOT NULL,
  source_flag CHAR(1) NOT NULL CHECK (source_flag IN ('M', 'P', 'T', 'O')),
  family_rollup_code VARCHAR(20),
  eng_rev_text VARCHAR(40),
  site_mask VARCHAR(50),
  catalog_group VARCHAR(20),
  product_line VARCHAR(20),
  taxable_flag CHAR(1) NOT NULL DEFAULT 'Y' CHECK (taxable_flag IN ('Y', 'N')),
  created_on DATE NOT NULL DEFAULT CURRENT_DATE
);

CREATE TABLE pinewoodworks.legacy_recipe_lines (
  recipe_line_id BIGSERIAL PRIMARY KEY,
  top_item_no VARCHAR(30) NOT NULL REFERENCES pinewoodworks.legacy_item_catalog(item_no),
  line_item_no VARCHAR(30) REFERENCES pinewoodworks.legacy_item_catalog(item_no),
  site_ref VARCHAR(20) NOT NULL,
  recipe_variant VARCHAR(20),
  line_seq INTEGER NOT NULL,
  qty_per NUMERIC(18,4),
  qty_basis_text VARCHAR(100),
  yield_loss_code VARCHAR(20),
  scrap_basis_text VARCHAR(100),
  optional_flag CHAR(1) NOT NULL DEFAULT 'N' CHECK (optional_flag IN ('Y', 'N')),
  substitute_group VARCHAR(20),
  effective_note VARCHAR(100),
  revision_note VARCHAR(100),
  comment_text TEXT,
  CONSTRAINT legacy_recipe_lines_qty_chk CHECK (qty_per IS NULL OR qty_per > 0),
  CONSTRAINT legacy_recipe_lines_uq UNIQUE (top_item_no, site_ref, line_seq, recipe_variant)
);

CREATE TABLE pinewoodworks.legacy_stock_snapshot (
  snapshot_id BIGSERIAL PRIMARY KEY,
  item_no VARCHAR(30) NOT NULL REFERENCES pinewoodworks.legacy_item_catalog(item_no),
  site_whse_code VARCHAR(20) NOT NULL,
  avail_code VARCHAR(5) NOT NULL CHECK (avail_code IN ('AVL', 'HLD', 'QA', 'MRB', 'REL')),
  on_hand_qty NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (on_hand_qty >= 0),
  committed_qty NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (committed_qty >= 0),
  reserved_qty NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (reserved_qty >= 0),
  disposition_code VARCHAR(20),
  owner_code VARCHAR(20),
  cycle_count_flag CHAR(1) NOT NULL DEFAULT 'N' CHECK (cycle_count_flag IN ('Y', 'N')),
  as_of_date DATE NOT NULL,
  comments TEXT
);

CREATE TABLE pinewoodworks.legacy_job_ticket (
  job_id VARCHAR(20) PRIMARY KEY,
  item_no VARCHAR(30) NOT NULL REFERENCES pinewoodworks.legacy_item_catalog(item_no),
  job_class VARCHAR(10) NOT NULL CHECK (job_class IN ('STD', 'HOT', 'RMA', 'KIT', 'RWK')),
  phase_code VARCHAR(10) NOT NULL,
  close_flag CHAR(1) NOT NULL DEFAULT 'N' CHECK (close_flag IN ('Y', 'N')),
  work_center_site VARCHAR(20) NOT NULL,
  requested_qty NUMERIC(18,4) NOT NULL CHECK (requested_qty > 0),
  good_qty NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (good_qty >= 0),
  reject_qty NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (reject_qty >= 0),
  need_by_date DATE,
  dispatch_date DATE,
  planner_badge VARCHAR(20),
  route_hint VARCHAR(20),
  expedite_note TEXT,
  ops_comment TEXT,
  created_on DATE NOT NULL DEFAULT CURRENT_DATE
);
