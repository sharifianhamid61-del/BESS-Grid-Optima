"""
network_builder.py
مدل‌سازی توپولوژی شبکه ۲۰ کیلوولت خراسان شمالی (بجنورد) و پروفیل‌های بار و تابش ۲۴ ساعته
"""

import numpy as np
import pandapower as pp


def create_north_khorasan_grid():
    """ایجاد شبکه توزیع شعاعی ۲۰ کیلوولت، شین‌ها، خطوط، بارها و پروفیل‌های ۲۴ ساعته"""
    net = pp.create_empty_network(name="North_Khorasan_20kV_Distribution_Grid")

    # 1. تعریف شین‌ها (Buses) با مختصات جغرافیایی منطقه بجنورد
    # Bus 0: پست فوق توزیع ۶۳/۲۰ کیلوولت (Substation / Slack)
    b0 = pp.create_bus(
        net, vn_kv=20.0, name="Substation_63_20kV", geodata=(57.3200, 37.4700)
    )

    # Bus 1: انتهای فیدر توزیع - نقطه افت ولتاژ بحرانی و کاندیدای BESS
    b1 = pp.create_bus(
        net, vn_kv=20.0, name="Bus_1_NK_Critical", geodata=(57.3550, 37.4920)
    )

    # Bus 2: شین میانی فیدر و مصرف‌کننده بار صنعتی/عمومی
    b2 = pp.create_bus(
        net, vn_kv=20.0, name="Bus_2_NK_Midway", geodata=(57.3380, 37.4810)
    )

    # Bus 3: شین شاخه خورشیدی / مصرف‌کننده کشاورزی
    b3 = pp.create_bus(
        net, vn_kv=20.0, name="Bus_3_NK_SolarNode", geodata=(57.3620, 37.4650)
    )

    # 2. منبع بالادست (Slack / Grid Infeed) در پست ۶۳/۲۰
    pp.create_ext_grid(net, bus=b0, vm_pu=1.02, name="Upstream_Grid_63kV")

    # 3. خطوط هوایی شبکه توزیع ۲۰ کیلوولت (هادی Hawk / ACSR)
    pp.create_line_from_parameters(
        net,
        from_bus=b0,
        to_bus=b2,
        length_km=6.5,
        r_ohm_per_km=0.27,
        x_ohm_per_km=0.35,
        c_nf_per_km=10.0,
        max_i_ka=0.35,
        name="Feeder_Main_Trunk",
    )

    pp.create_line_from_parameters(
        net,
        from_bus=b2,
        to_bus=b1,
        length_km=8.2,
        r_ohm_per_km=0.35,
        x_ohm_per_km=0.38,
        c_nf_per_km=9.5,
        max_i_ka=0.28,
        name="Feeder_Critical_End",
    )

    pp.create_line_from_parameters(
        net,
        from_bus=b2,
        to_bus=b3,
        length_km=5.0,
        r_ohm_per_km=0.35,
        x_ohm_per_km=0.38,
        c_nf_per_km=9.5,
        max_i_ka=0.28,
        name="Feeder_Solar_Branch",
    )

    # 4. بارهای پایه‌ای متصل به شین‌ها (Base Loads)
    # ضریب توان فرضی: 0.90 تا 0.92
    pp.create_load(
        net,
        bus=b1,
        p_mw=3.8,
        q_mvar=1.8,
        sn_mva=4.2,
        name="Load_Critical_EndBus",
    )
    pp.create_load(
        net, bus=b2, p_mw=2.5, q_mvar=1.1, sn_mva=2.8, name="Load_Midway_Node"
    )
    pp.create_load(
        net,
        bus=b3,
        p_mw=1.8,
        q_mvar=0.8,
        sn_mva=2.0,
        name="Load_Agricultural_Branch",
    )

    # 5. نیروگاه خورشیدی فتوولتائیک محلی در شین ۳
    pp.create_sgen(
        net,
        bus=b3,
        p_mw=1.5,
        q_mvar=0.0,
        sn_mva=1.8,
        name="Solar_Farm_NK_1.5MW",
    )

    # 6. ضرایب پروفیل ۲۴ ساعته نرمال‌شده بار منطقه (خراسان شمالی - پیک تابستان/پاییز)
    load_profile = [
        0.48,
        0.44,
        0.42,
        0.41,
        0.43,
        0.50,  # ساعت ۰ الی ۵: کم‌باری شبانه (Valley)
        0.62,
        0.75,
        0.86,
        0.91,
        0.95,
        0.98,  # ساعت ۶ الی ۱۱: بار صعودی صبحگاهی
        1.00,
        0.97,
        0.92,
        0.88,
        0.86,
        0.90,  # ساعت ۱۲ الی ۱۷: پیک نیمروزی
        1.06,
        1.12,
        1.10,
        0.98,
        0.82,
        0.62,  # ساعت ۱۸ الی ۲۳: پیک شبانه شدید
    ]

    # ضرایب پروفیل تولید خورشیدی ۲۴ ساعته
    solar_profile = [
        0.00,
        0.00,
        0.00,
        0.00,
        0.00,
        0.05,  # 00-05
        0.22,
        0.52,
        0.78,
        0.95,
        1.00,
        0.96,  # 06-11
        0.88,
        0.74,
        0.55,
        0.30,
        0.08,
        0.00,  # 12-17
        0.00,
        0.00,
        0.00,
        0.00,
        0.00,
        0.00,  # 18-23
    ]

    return net, load_profile, solar_profile
