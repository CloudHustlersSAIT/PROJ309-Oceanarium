"""
Generate an Oceanarium ERD v5.0 .drawio file.

Usage:
    python3 generate_erd.py
    # produces oceanarium-erd-v5.0.drawio in the same directory

Then export to PNG:
    drawio --export --format png --scale 2 \
        --output oceanarium-erd-v5.0.png oceanarium-erd-v5.0.drawio
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

# ── Geometry helpers ──

COL_W = 250
ROW_H = 26
HDR_H = 30
DOMAIN_PAD = 30
DOMAIN_TOP_PAD = 40
TABLE_GAP_X = 30
TABLE_GAP_Y = 30


@dataclass
class Col:
    name: str
    dtype: str
    key: str = ""  # "PK", "FK", "UK", or ""


@dataclass
class Table:
    name: str
    cols: list[Col]
    x: int = 0
    y: int = 0

    @property
    def w(self):
        return COL_W

    @property
    def h(self):
        return HDR_H + ROW_H * len(self.cols)


@dataclass
class Domain:
    name: str
    color: str
    tables: list[str]
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0


@dataclass
class Rel:
    src_table: str
    src_col: str
    tgt_table: str


# ── Badge colors ──

BADGE = {
    "PK": "#e84393",
    "FK": "#27ae60",
    "UK": "#2980b9",
}

# ── Schema definition ──

TABLES: dict[str, Table] = {}


def tbl(name, *cols):
    t = Table(name, list(cols))
    TABLES[name] = t
    return t


def pk(name, dtype="INT"):
    return Col(name, dtype, "PK")


def fk(name, dtype="INT"):
    return Col(name, dtype, "FK")


def uk(name, dtype):
    return Col(name, dtype, "UK")


def col(name, dtype):
    return Col(name, dtype)


# fmt: off

tbl("customers",
    pk("id"), uk("clorian_client_id", "VARCHAR"),
    col("first_name", "VARCHAR"), col("last_name", "VARCHAR"), col("email", "VARCHAR"))

tbl("tours",
    pk("id"), uk("clorian_product_id", "INT"),
    col("name", "VARCHAR"), col("description", "TEXT"), col("duration", "INT"))

tbl("languages",
    pk("id"), uk("code", "VARCHAR"), col("name", "VARCHAR"))

tbl("users",
    pk("id"), uk("username", "VARCHAR"), uk("email", "VARCHAR"),
    col("password_hash", "VARCHAR"), col("full_name", "VARCHAR"),
    col("role", "VARCHAR"), col("is_active", "BOOLEAN"), col("created_at", "TIMESTAMPTZ"))

tbl("guides",
    pk("id"), col("first_name", "VARCHAR"), col("last_name", "VARCHAR"),
    col("email", "VARCHAR"), col("phone", "VARCHAR"),
    col("guide_rating", "DECIMAL"), col("is_active", "BOOLEAN"))

tbl("availability_patterns",
    pk("id"), fk("guide_id"), col("timezone", "VARCHAR"))

tbl("poll_execution",
    pk("id"), col("window_start", "TIMESTAMPTZ"), col("window_end", "TIMESTAMPTZ"),
    col("executed_at", "TIMESTAMPTZ"), col("finished_at", "TIMESTAMPTZ"),
    col("status", "VARCHAR"), col("seed", "INT"),
    col("generated_total", "INT"), col("generated_created", "INT"),
    col("generated_updated", "INT"), col("generated_unchanged", "INT"),
    col("error_message", "TEXT"))

tbl("poll_staging",
    pk("id"), fk("poll_execution_id"),
    col("entity_type", "VARCHAR"), col("external_id", "VARCHAR"),
    col("scenario", "VARCHAR"), col("payload_json", "JSONB"),
    col("created_at", "TIMESTAMPTZ"), col("processed_at", "TIMESTAMPTZ"),
    col("processed_status", "VARCHAR"), col("processed_error", "TEXT"))

tbl("availability_slots",
    pk("id"), fk("pattern_id"),
    col("day_of_week", "VARCHAR"), col("start_time", "TIME"), col("end_time", "TIME"))

tbl("availability_exceptions",
    pk("id"), fk("pattern_id"),
    col("date", "DATE"), col("type", "VARCHAR"), col("reason", "VARCHAR"))

tbl("guide_languages",
    fk("guide_id"), fk("language_id"))

tbl("guide_tour_types",
    fk("guide_id"), fk("tour_id"))

tbl("sync_logs",
    pk("id"), fk("poll_execution_id"),
    col("started_at", "TIMESTAMPTZ"), col("finished_at", "TIMESTAMPTZ"),
    col("new_count", "INT"), col("changed_count", "INT"),
    col("cancelled_count", "INT"), col("status", "VARCHAR"), col("errors", "TEXT"))

tbl("schedule",
    pk("id"), fk("guide_id"), fk("tour_id"),
    col("language_code", "VARCHAR"), col("event_start_datetime", "TIMESTAMPTZ"),
    col("event_end_datetime", "TIMESTAMPTZ"), col("status", "VARCHAR"),
    col("created_at", "TIMESTAMPTZ"))

tbl("reservations",
    pk("id"), uk("clorian_reservation_id", "VARCHAR"),
    col("clorian_purchase_id", "INT"),
    fk("customer_id"), fk("tour_id"), fk("schedule_id"),
    col("language_code", "VARCHAR"), col("event_start_datetime", "TIMESTAMPTZ"),
    col("status", "VARCHAR"), col("current_ticket_num", "INT"),
    col("clorian_created_at", "TIMESTAMPTZ"), col("clorian_modified_at", "TIMESTAMPTZ"),
    col("created_at", "TIMESTAMPTZ"))

tbl("reservation_versions",
    pk("id"), fk("reservation_id"),
    col("hash", "VARCHAR"), col("status", "VARCHAR"),
    col("current_ticket_num", "INT"), col("language_code", "VARCHAR"),
    col("event_start_datetime", "TIMESTAMPTZ"),
    col("received_at", "TIMESTAMPTZ"), col("valid_from", "TIMESTAMPTZ"),
    fk("poll_execution_id"))

tbl("tickets",
    pk("id"), uk("clorian_ticket_id", "VARCHAR"),
    fk("reservation_id"),
    col("buyer_type_id", "INT"), col("buyer_type_name", "VARCHAR"),
    col("start_datetime", "TIMESTAMPTZ"), col("end_datetime", "TIMESTAMPTZ"),
    col("ticket_status", "VARCHAR"), col("price", "DECIMAL"),
    col("venue_id", "INT"), col("venue_name", "VARCHAR"),
    col("clorian_created_at", "TIMESTAMPTZ"), col("clorian_modified_at", "TIMESTAMPTZ"),
    col("created_at", "TIMESTAMPTZ"))

tbl("surveys",
    pk("id"), fk("customer_id"), fk("guide_id"), fk("reservation_id"),
    col("comment", "TEXT"), col("rating", "INT"))

tbl("notifications",
    pk("id"), col("event_type", "VARCHAR"),
    fk("schedule_id"), fk("guide_id"), fk("user_id"),
    col("channel", "VARCHAR"), col("status", "VARCHAR"),
    col("message", "TEXT"), col("sent_at", "TIMESTAMPTZ"),
    col("created_at", "TIMESTAMPTZ"))

tbl("tour_assignment_logs",
    pk("id"), fk("schedule_id"), fk("guide_id"),
    col("assigned_at", "TIMESTAMPTZ"), col("assigned_by", "VARCHAR"),
    col("assignment_type", "VARCHAR"), col("action", "VARCHAR"))

# fmt: on

# ── Domains ──

DOMAINS = [
    Domain("Reservation Domain", "#e84393", ["customers", "reservations", "reservation_versions", "tickets"]),
    Domain("Tour & Scheduling Domain", "#00b894", ["tours", "schedule"]),
    Domain("Guide Domain", "#e17055", ["guides", "languages", "guide_languages", "guide_tour_types"]),
    Domain(
        "Availability Domain", "#6c5ce7", ["availability_patterns", "availability_slots", "availability_exceptions"]
    ),
    Domain("Feedback Domain", "#f39c12", ["surveys"]),
    Domain("Notification Domain", "#0984e3", ["notifications"]),
    Domain(
        "Sync / Operational Domain", "#2d3436", ["poll_execution", "poll_staging", "sync_logs", "tour_assignment_logs"]
    ),
    Domain("Auth / Standalone", "#636e72", ["users"]),
]

# ── Relationships ──

RELS = [
    Rel("reservations", "customer_id", "customers"),
    Rel("reservations", "tour_id", "tours"),
    Rel("reservations", "schedule_id", "schedule"),
    Rel("tickets", "reservation_id", "reservations"),
    Rel("reservation_versions", "reservation_id", "reservations"),
    Rel("reservation_versions", "poll_execution_id", "poll_execution"),
    Rel("schedule", "guide_id", "guides"),
    Rel("schedule", "tour_id", "tours"),
    Rel("guide_languages", "guide_id", "guides"),
    Rel("guide_languages", "language_id", "languages"),
    Rel("guide_tour_types", "guide_id", "guides"),
    Rel("guide_tour_types", "tour_id", "tours"),
    Rel("availability_patterns", "guide_id", "guides"),
    Rel("availability_slots", "pattern_id", "availability_patterns"),
    Rel("availability_exceptions", "pattern_id", "availability_patterns"),
    Rel("surveys", "customer_id", "customers"),
    Rel("surveys", "guide_id", "guides"),
    Rel("surveys", "reservation_id", "reservations"),
    Rel("notifications", "schedule_id", "schedule"),
    Rel("notifications", "guide_id", "guides"),
    Rel("notifications", "user_id", "users"),
    Rel("poll_staging", "poll_execution_id", "poll_execution"),
    Rel("sync_logs", "poll_execution_id", "poll_execution"),
    Rel("tour_assignment_logs", "schedule_id", "schedule"),
    Rel("tour_assignment_logs", "guide_id", "guides"),
]

# ── Layout: position tables in domain groups ──

LAYOUT = {
    # Reservation domain (top-left, 2x2 grid)
    "customers": (50, 100),
    "reservation_versions": (330, 100),
    "reservations": (50, 440),
    "tickets": (330, 440),
    # Tour & Scheduling (center-top)
    "tours": (660, 100),
    "schedule": (660, 320),
    # Guide domain (right-top, 2x2 grid)
    "guides": (980, 100),
    "languages": (1260, 100),
    "guide_languages": (980, 360),
    "guide_tour_types": (1260, 250),
    # Auth (far right-top)
    "users": (1540, 100),
    # Feedback (below tour domain)
    "surveys": (660, 640),
    # Notification (below guide left)
    "notifications": (980, 510),
    # Availability (below guide right + auth)
    "availability_patterns": (1260, 500),
    "availability_slots": (1540, 500),
    "availability_exceptions": (1260, 680),
    # Sync domain (bottom row)
    "poll_execution": (50, 960),
    "poll_staging": (330, 960),
    "sync_logs": (660, 960),
    "tour_assignment_logs": (980, 960),
}

for name, (x, y) in LAYOUT.items():
    TABLES[name].x = x
    TABLES[name].y = y


def compute_domain_bounds(domain: Domain):
    pad = DOMAIN_PAD
    top_pad = DOMAIN_TOP_PAD
    tbls = [TABLES[n] for n in domain.tables]
    x0 = min(t.x for t in tbls) - pad
    y0 = min(t.y for t in tbls) - top_pad
    x1 = max(t.x + t.w for t in tbls) + pad
    y1 = max(t.y + t.h for t in tbls) + pad
    domain.x, domain.y, domain.w, domain.h = x0, y0, x1 - x0, y1 - y0


for d in DOMAINS:
    compute_domain_bounds(d)


# ── mxGraph XML generation ──


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


_id_counter = 2


def next_id():
    global _id_counter
    _id_counter += 1
    return str(_id_counter)


def build_drawio():
    mx = ET.Element("mxfile", host="app.diagrams.net", type="device")
    diagram = ET.SubElement(mx, "diagram", name="ERD v5.0", id="erd")
    model = ET.SubElement(
        diagram,
        "mxGraphModel",
        dx="0",
        dy="0",
        grid="1",
        gridSize="10",
        guides="1",
        tooltips="1",
        connect="1",
        arrows="1",
        fold="1",
        page="0",
        pageScale="1",
        pageWidth="2400",
        pageHeight="1200",
        math="0",
        shadow="0",
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    table_ids: dict[str, str] = {}
    col_ids: dict[str, dict[str, str]] = {}

    # Title (centered above all content)
    all_right = max(t.x + t.w for t in TABLES.values())
    title_id = next_id()
    title_cell = ET.SubElement(root, "mxCell", id=title_id, value="Oceanarium Database Schema", parent="1", vertex="1")
    title_cell.set(
        "style",
        "text;html=1;align=center;verticalAlign=middle;resizable=0;points=[];"
        "autosize=1;strokeColor=none;fillColor=none;"
        "fontSize=24;fontStyle=1;fontColor=#2d3436;fontFamily=Helvetica;",
    )
    title_geo = ET.SubElement(title_cell, "mxGeometry", x="0", y="5", width=str(int(all_right)), height="40")
    title_geo.set("as", "geometry")

    # Draw domain groups
    for dom in DOMAINS:
        did = next_id()
        cell = ET.SubElement(root, "mxCell", id=did, value=esc(dom.name), parent="1", vertex="1")
        style = (
            f"rounded=1;whiteSpace=wrap;html=1;fillColor=none;"
            f"strokeColor={dom.color};strokeWidth=2;dashed=0;"
            f"verticalAlign=top;align=left;fontSize=13;fontStyle=1;"
            f"fontColor={dom.color};spacingTop=5;spacingLeft=10;"
            f"fontFamily=Helvetica;"
        )
        cell.set("style", style)
        ET.SubElement(cell, "mxGeometry", x=str(dom.x), y=str(dom.y), width=str(dom.w), height=str(dom.h)).set(
            "as", "geometry"
        )

    # Draw tables
    for tname, tbl in TABLES.items():
        tid = next_id()
        table_ids[tname] = tid
        col_ids[tname] = {}

        hdr_color = "#636e72"
        for dom in DOMAINS:
            if tname in dom.tables:
                hdr_color = dom.color
                break

        # Table container
        cell = ET.SubElement(root, "mxCell", id=tid, value="", parent="1", vertex="1")
        style = (
            f"shape=table;startSize={HDR_H};container=1;collapsible=0;"
            f"childLayout=tableLayout;fixedRows=1;rowLines=1;fontStyle=1;"
            f"strokeColor=#c0c0c0;fillColor={hdr_color};"
            f"fontSize=13;fontColor=#ffffff;fontFamily=Helvetica;"
            f"align=center;resizeLast=1;html=1;"
        )
        cell.set("style", style)
        geo = ET.SubElement(cell, "mxGeometry", x=str(tbl.x), y=str(tbl.y), width=str(tbl.w), height=str(tbl.h))
        geo.set("as", "geometry")

        # Table name label (inside the header area)
        lbl_id = next_id()
        lbl = ET.SubElement(root, "mxCell", id=lbl_id, value=esc(tname), parent=tid, vertex="1")
        lbl.set(
            "style",
            f"shape=partialRectangle;overflow=hidden;connectable=0;"
            f"fillColor={hdr_color};top=0;left=0;bottom=0;right=0;"
            f"fontStyle=1;fontSize=13;fontColor=#ffffff;"
            f"fontFamily=Helvetica;align=center;html=1;",
        )
        lbl_geo = ET.SubElement(lbl, "mxGeometry", width=str(tbl.w), height=str(HDR_H))
        lbl_geo.set("as", "geometry")

        # Columns
        for i, col in enumerate(tbl.cols):
            row_id = next_id()
            row_y = HDR_H + i * ROW_H

            # Row container
            row_cell = ET.SubElement(root, "mxCell", id=row_id, value="", parent=tid, vertex="1")
            row_cell.set(
                "style",
                "shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;"
                "swimlaneBody=0;fillColor=none;collapsible=0;"
                "dropTarget=0;points=[[0,0.5],[1,0.5]];"
                "portConstraint=eastwest;top=0;left=0;right=0;bottom=0;"
                "fontFamily=Helvetica;fontSize=11;html=1;",
            )
            row_geo = ET.SubElement(row_cell, "mxGeometry", y=str(row_y), width=str(tbl.w), height=str(ROW_H))
            row_geo.set("as", "geometry")

            col_ids[tname][col.name] = row_id

            badge_w = 32
            type_w = 85
            name_w = tbl.w - badge_w - type_w

            # Badge cell (PK/FK/UK)
            badge_id = next_id()
            badge_color = BADGE.get(col.key, "")
            badge_val = f"<b>{col.key}</b>" if col.key else ""
            badge_fill = badge_color if col.key else "none"
            badge_font = "#ffffff" if col.key else "#ffffff"

            badge_cell = ET.SubElement(root, "mxCell", id=badge_id, value=badge_val, parent=row_id, vertex="1")
            badge_cell.set(
                "style",
                f"shape=partialRectangle;overflow=hidden;connectable=0;"
                f"fillColor={badge_fill};top=0;left=0;bottom=0;right=0;"
                f"fontSize=9;fontStyle=1;fontColor={badge_font};"
                f"fontFamily=Helvetica;align=center;html=1;",
            )
            bg = ET.SubElement(badge_cell, "mxGeometry", width=str(badge_w), height=str(ROW_H))
            bg.set("as", "geometry")

            # Column name cell
            cname_id = next_id()
            cname_cell = ET.SubElement(root, "mxCell", id=cname_id, value=esc(col.name), parent=row_id, vertex="1")
            cname_cell.set(
                "style",
                "shape=partialRectangle;overflow=hidden;connectable=0;"
                "fillColor=none;top=0;left=0;bottom=0;right=0;"
                "fontSize=11;fontColor=#2d3436;"
                "fontFamily=Helvetica;align=left;spacingLeft=4;html=1;",
            )
            cg = ET.SubElement(cname_cell, "mxGeometry", x=str(badge_w), width=str(name_w), height=str(ROW_H))
            cg.set("as", "geometry")

            # Data type cell
            dtype_id = next_id()
            dtype_cell = ET.SubElement(root, "mxCell", id=dtype_id, value=esc(col.dtype), parent=row_id, vertex="1")
            dtype_cell.set(
                "style",
                "shape=partialRectangle;overflow=hidden;connectable=0;"
                "fillColor=none;top=0;left=0;bottom=0;right=0;"
                "fontSize=10;fontColor=#8395a7;"
                "fontFamily=Helvetica;align=right;spacingRight=4;html=1;",
            )
            dg = ET.SubElement(dtype_cell, "mxGeometry", x=str(badge_w + name_w), width=str(type_w), height=str(ROW_H))
            dg.set("as", "geometry")

    return mx


def main():
    root = build_drawio()
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    out = Path(__file__).parent / "oceanarium-erd-v5.0.drawio"
    tree.write(str(out), encoding="UTF-8", xml_declaration=True)
    print(f"Generated: {out}")


if __name__ == "__main__":
    main()
