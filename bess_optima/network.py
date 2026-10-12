"""
bess_optima.network
Builds the North Khorasan MV feeder with realistic GIS geodata (EPSG:4326).
"""

import numpy as np
import pandas as pd
import pandapower as pp

def generate_regional_profiles(timesteps: int = 24) -> pd.DataFrame:
    """
    تولید پروفیل‌های نرمال‌شده بار و تابش متناسب با منطقه خراسان شمالی (بجنورد)
    """
    hours = np.arange(timesteps)
    
    # پروفیل بار: پیک مصرف در غروب و ابتدای شب
    load_curve = 0.35 + 0.35 * np.sin((hours - 6) * np.pi / 12)**2 + 0.30 * (hours >= 18) * (hours <= 22)
    load_curve = np.clip(load_curve, 0.2, 1.0)
    
    # پروفیل خورشیدی: تابش شدید بین ۱۰:۰۰ تا ۱۵:۰۰
    pv_curve = np.maximum(0, np.sin((hours - 5.5) * np.pi / 13.5))**2
    pv_curve[hours < 6] = 0.0
    pv_curve[hours > 19] = 0.0
    
    return pd.DataFrame({"load": load_curve, "pv": pv_curve})


def build_north_khorasan_grid() -> pp.pandapowerNet:
    """
    شبکه توزیع ۲۰ کیلوولت شعاعی با مختصات جغرافیایی دقیق در دشت بجنورد / خراسان شمالی
    """
    net = pp.create_empty_network(name="North_Khorasan_Distribution_Feeder")
    
    # شین پست فوق توزیع ۱۳۲ کیلوولت
    b0 = pp.create_bus(net, vn_kv=132.0, name="Substation_132kV_Bojnourd", geodata=(57.3210, 37.4750))
    
    # شین‌های ۲۰ کیلوولت فیدر خروجی
    bus_coords = [
        (57.3225, 37.4765),  # Bus 1: شین خروجی ترانس
        (57.3380, 37.4850),  # Bus 2: منطقه صنعتی / حاشیه شهر
        (57.3520, 37.4930),  # Bus 3: ناحیه دارای نیروگاه خورشیدی ۱
        (57.3690, 37.5020),  # Bus 4: بار ترکیبی کشاورزی / مسکونی
        (57.3850, 37.5110),  # Bus 5: انتهای فیدر (نیروگاه خورشیدی ۲)
    ]
    
    buses = [b0]
    for i, (lon, lat) in enumerate(bus_coords, start=1):
        b_id = pp.create_bus(net, vn_kv=20.0, name=f"Bus_{i}_NK", geodata=(lon, lat))
        buses.append(b_id)
        
    # اتصال به شبکه انتقال بالا‌دست
    pp.create_ext_grid(net, bus=buses[0], vm_pu=1.02, name="Khorasan_Regional_Grid")
    
    # ترانسفورماتور فوق توزیع ۱۳۲/۲۰ کیلوولت
    pp.create_transformer(net, hv_bus=buses[0], lv_bus=buses[1],
                           std_type="25 MVA 110/20 kV", name="NK_Grid_Transformer")
    
    # خطوط انتقال ۲۰ کیلوولت
    for i in range(1, 5):
        pp.create_line(net, from_bus=buses[i], to_bus=buses[i+1], length_km=2.1,
                       std_type="NAYY 4x150 SE", name=f"Line_{i}_{i+1}")
        
    # بارهای متصل به فیدر
    pp.create_load(net, bus=buses[3], p_mw=2.2, q_mvar=0.5, name="Load_Industrial_Bus3")
    pp.create_load(net, bus=buses[4], p_mw=3.0, q_mvar=0.7, name="Load_Agricultural_Bus4")
    pp.create_load(net, bus=buses[5], p_mw=1.8, q_mvar=0.4, name="Load_Rural_Bus5")
    
    # مزارع خورشیدی
    pp.create_sgen(net, bus=buses[3], p_mw=3.0, q_mvar=0.0, name="Solar_Plant_Bus3")
    pp.create_sgen(net, bus=buses[5], p_mw=4.8, q_mvar=0.0, name="Solar_Plant_FeederEnd")
    
    return net
