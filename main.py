"""
main.py
اسکریپت اصلی اجرای BESS-Grid-Optima
"""

import numpy as np
import pandapower as pp

import warnings

warnings.filterwarnings("ignore", message=".*numba.*")

# ماژول‌های داخلی پروژه
from geo_export import export_to_geopackage
from network_builder import create_north_khorasan_grid
from optimizer import run_bess_optimization
from visualizer import plot_optimization_workflow, plot_technical_analysis


def run_pipeline():
    print("==========================================================")
    print("      BESS-Grid-Optima: North Khorasan 20kV System        ")
    print("==========================================================")

    # گام ۱: ساخت شبکه و دریافت اطلاعات پایه
    net, load_profile, solar_profile = create_north_khorasan_grid()
    hours = list(range(24))

    # گام ۲: شبیه‌سازی ۲۴ ساعته اولیه (بدون باتری)
    print("[*] Running 24-step baseline AC power flow...")
    base_load_mw = []
    v_base_bus1 = []
    feeder_loading_base = []

    critical_bus_idx = 1  # باس بحرانی انتهای فیدر (Bus_1_NK)

    for h in hours:
        # اعمال ضریب بار ساعتی
        net.load.p_mw = net.load.sn_mva * 0.9 * load_profile[h]
        if len(net.sgen) > 0:
            net.sgen.p_mw = net.sgen.sn_mva * solar_profile[h]

        pp.runpp(net, enforce_q_lims=False)

        base_load_mw.append(float(net.load.p_mw.sum()))
        v_base_bus1.append(float(net.res_bus.vm_pu.loc[critical_bus_idx]))
        feeder_loading_base.append(float(net.res_line.loading_percent.max()))

    # گام ۳: اجرای بهینه‌سازی ظرفیت و دیسپچ باتری
    print("[*] Optimizing BESS capacity and dispatch schedule...")
    opt_results = run_bess_optimization(
        net, base_load_mw, critical_bus=critical_bus_idx
    )

    bess_mw = opt_results["bess_mw"]
    bess_mwh = opt_results["bess_mwh"]
    peak_shaving_mw = opt_results["peak_shaving_mw"]
    bess_dispatch = opt_results[
        "dispatch_mw"
    ]  # توان مثبت: دیسشارژ، توان منفی: شارژ
    soc_series = opt_results.get(
        "soc_series",
        [
            50
            + 35 * np.sin((h - 8) / 3.5)
            if 8 <= h <= 22
            else 50 - 15 * np.cos(h / 3)
            for h in hours
        ],
    )

    # گام ۴: شبیه‌سازی ۲۴ ساعته شبکه با ورود باتری
    print("[*] Simulating post-BESS grid response across 24 hours...")
    net_load_mw = []
    v_bess_bus1 = []
    feeder_loading_bess = []

    # اضافه کردن باتری به شبکه به عنوان ژنراتور استاتیک (sgen)
    bess_gen_idx = pp.create_sgen(
        net,
        bus=critical_bus_idx,
        p_mw=0.0,
        q_mvar=0.0,
        name="BESS_Storage_Unit",
    )

    for h in hours:
        net.load.p_mw = net.load.sn_mva * 0.9 * load_profile[h]
        if len(net.sgen) > 1:
            net.sgen.at[0, "p_mw"] = float(net.sgen.sn_mva.loc[0] * solar_profile[h])

        # تزریق توان باتری (مثبت = دیسشارژ به شبکه)
        net.sgen.at[bess_gen_idx, "p_mw"] = float(bess_dispatch[h])

        pp.runpp(net, numba=False)

        net_load_mw.append(
            float(net.load.p_mw.sum() - net.sgen.p_mw.loc[bess_gen_idx])
        )
        v_bess_bus1.append(float(net.res_bus.vm_pu.loc[critical_bus_idx]))
        feeder_loading_bess.append(float(net.res_line.loading_percent.max()))

    # گام ۵: خروجی به فایل GeoPackage برای نمایش مکانی در QGIS
    print("[*] Exporting GIS spatial layers...")
    export_to_geopackage(net, bess_bus=critical_bus_idx, bess_mw=bess_mw)

    # گام ۶: تولید خودکار نمودارهای تحلیلی و معماری پروژه
    print("[*] Generating technical dashboards and algorithm diagrams...")
    base_feeder_mw = [(net.load.sn_mva.sum() * 0.9 * lp) for lp in load_profile]

    plot_technical_analysis(
        hours=hours,
        base_load_mw=base_feeder_mw,
        opt_load_mw=net_load_mw,
        bess_p_mw=bess_dispatch,
        opt_v_pu=v_bess_bus1
    )

    plot_optimization_workflow(output_path="bess_workflow_architecture.png")

    print("\n" + "=" * 58)
    print("                    EXECUTION SUMMARY                     ")
    print("=" * 58)
    print(f" • Critical Bus Identified: Bus {critical_bus_idx} ({net.bus.name.loc[critical_bus_idx]})")
    print(f" • Optimal BESS Capacity:   {bess_mwh:.2f} MWh / {bess_mw:.2f} MW")
    print(f" • Peak Load Reduction:     {peak_shaving_mw:.2f} MW")
    print(" • Generated Files:")
    print("    ├── North_Khorasan_BESS_Optima.gpkg (GIS layers)")
    print("    ├── bess_technical_analysis.png     (4-Panel Dynamic Curves)")
    print("    └── bess_workflow_architecture.png  (Optimization Flowchart)")
    print("=" * 58)


if __name__ == "__main__":
    run_pipeline()
