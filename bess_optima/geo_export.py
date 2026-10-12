"""
geo_export.py
اکسپورت لایه‌های مکانی شبکه (Buses, Lines, BESS) به فرمت GeoPackage
"""

import ast
import json
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point


def _extract_bus_coords(net, bus_idx):
    default_coords = {
        0: (57.3200, 37.4700),  # Substation 63/20kV
        1: (57.3550, 37.4920),  # Critical BESS Bus
        2: (57.3380, 37.4810),  # Midway Node
        3: (57.3620, 37.4650),  # Solar Node
    }

    if hasattr(net, "bus_geodata") and bus_idx in net.bus_geodata.index:
        row = net.bus_geodata.loc[bus_idx]

        # 1. ستون‌های x و y
        if "x" in row and "y" in row and pd.notna(row["x"]) and pd.notna(row["y"]):
            try:
                return float(row["x"]), float(row["y"])
            except Exception:
                pass

        # 2. ستون coords
        if "coords" in row and pd.notna(row["coords"]):
            val = row["coords"]
            if isinstance(val, (list, tuple)) and len(val) >= 2:
                return float(val[0]), float(val[1])
            if isinstance(val, str):
                try:
                    p = ast.literal_eval(val)
                    if isinstance(p, (list, tuple)) and len(p) >= 2:
                        return float(p[0]), float(p[1])
                except Exception:
                    pass

        # 3. ستون geometry یا geo
        for col in ["geometry", "geo"]:
            if col in row and pd.notna(row[col]):
                val = row[col]
                if isinstance(val, str):
                    try:
                        val = json.loads(val)
                    except Exception:
                        try:
                            val = ast.literal_eval(val)
                        except Exception:
                            pass

                if isinstance(val, dict) and "coordinates" in val:
                    c = val["coordinates"]
                    return float(c[0]), float(c[1])
                elif (
                    hasattr(val, "x")
                    and hasattr(val, "y")
                    and pd.notna(val.x)
                    and pd.notna(val.y)
                ):
                    return float(val.x), float(val.y)

    return default_coords.get(bus_idx, (57.3200 + bus_idx * 0.01, 37.4700))


def export_to_geopackage(
    net,
    bess_bus,
    bess_mw,
    output_path="North_Khorasan_BESS_Optima.gpkg",
    crs="EPSG:4326",
):
    bus_records = []
    for idx, row in net.bus.iterrows():
        x, y = _extract_bus_coords(net, idx)
        vm_pu = (
            float(net.res_bus.vm_pu.loc[idx])
            if hasattr(net, "res_bus") and idx in net.res_bus.index
            else 1.0
        )
        bus_records.append(
            {
                "bus_id": int(idx),
                "name": str(row.get("name", f"Bus_{idx}")),
                "vn_kv": float(row["vn_kv"]),
                "vm_pu": round(vm_pu, 4),
                "geometry": Point(x, y),
            }
        )
    gdf_buses = gpd.GeoDataFrame(bus_records, crs=crs)
    gdf_buses.to_file(output_path, layer="buses", driver="GPKG")

    line_records = []
    for idx, row in net.line.iterrows():
        fb = int(row["from_bus"])
        tb = int(row["to_bus"])
        x1, y1 = _extract_bus_coords(net, fb)
        x2, y2 = _extract_bus_coords(net, tb)
        loading = (
            float(net.res_line.loading_percent.loc[idx])
            if hasattr(net, "res_line") and idx in net.res_line.index
            else 0.0
        )
        line_records.append(
            {
                "line_id": int(idx),
                "name": str(row.get("name", f"Line_{idx}")),
                "from_bus": fb,
                "to_bus": tb,
                "length_km": float(row["length_km"]),
                "loading_percent": round(loading, 2),
                "geometry": LineString([(x1, y1), (x2, y2)]),
            }
        )
    gdf_lines = gpd.GeoDataFrame(line_records, crs=crs)
    gdf_lines.to_file(output_path, layer="lines", driver="GPKG")

    bx, by = _extract_bus_coords(net, bess_bus)
    bess_records = [
        {
            "bess_id": 1,
            "connected_bus": int(bess_bus),
            "capacity_mw": float(bess_mw),
            "status": "Operational / Peak Shaving",
            "geometry": Point(bx, by),
        }
    ]
    gdf_bess = gpd.GeoDataFrame(bess_records, crs=crs)
    gdf_bess.to_file(output_path, layer="bess_location", driver="GPKG")

    print(f"[✓] Spatial layers exported successfully to: {output_path}")
