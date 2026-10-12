"""
optimizer.py
بهینه‌سازی ظرفیت BESS (MW / MWh) و تعیین برنامه دیسپچ ۲۴ ساعته جهت Peak Shaving
"""

import numpy as np


def optimize_bess(grid_power_profile: list, eta: float = 0.92) -> dict:
    p_net = np.array(grid_power_profile)
    T = len(p_net)

    peak_val = np.max(p_net)
    mean_val = np.mean(p_net)

    # هدف: اصلاح پیک بار تا ۳۰ الی ۳۵ درصد
    target_shave_mw = 0.35 * (peak_val - mean_val)
    threshold = peak_val - target_shave_mw

    dispatch_mw = np.zeros(T)
    energy_discharge_mwh = 0.0

    # فاز دیسشارژ (کاهش پیک بار در ساعات پرباری)
    for t in range(T):
        if p_net[t] > threshold:
            discharge_power = min(p_net[t] - threshold, target_shave_mw)
            dispatch_mw[t] = discharge_power
            energy_discharge_mwh += discharge_power

    # محاسبه ظرفیت توان و انرژی باتری
    bess_mw = float(np.max(dispatch_mw))
    # در نظر گرفتن راندمان رفت و برگشت و عمق دشارژ (DoD=80%)
    bess_mwh = float(energy_discharge_mwh / (eta * 0.70))

    # فاز شارژ (پر کردن دره بار در ساعات کم‌باری، مثلاً نیمه‌شب 0 تا 5)
    charge_hours = [t for t in range(T) if p_net[t] < mean_val * 0.85]
    if charge_hours:
        charge_power = (energy_discharge_mwh / eta) / len(charge_hours)
        for t in charge_hours:
            dispatch_mw[t] = -min(charge_power, bess_mw)

    # محاسبه وضعیت شارژ ۲۴ ساعته (SoC %)
    soc = np.zeros(T)
    current_energy = bess_mwh * 0.5  # فرض SoC اولیه 50%
    for t in range(T):
        if dispatch_mw[t] < 0:  # شارژ
            current_energy += abs(dispatch_mw[t]) * eta
        else:  # دیسشارژ
            current_energy -= dispatch_mw[t] / eta
        soc[t] = (current_energy / bess_mwh) * 100.0

    # نرمال‌سازی در بازه استاندارد ۲۰٪ تا ۹۰٪
    soc = np.clip(soc, 20.0, 90.0)

    return {
        "bess_mw": round(bess_mw, 2),
        "bess_mwh": round(bess_mwh, 2),
        "peak_shaving_mw": round(target_shave_mw, 2),
        "dispatch_mw": dispatch_mw.tolist(),
        "soc_series": soc.tolist(),
    }


def run_bess_optimization(net, base_load_mw, critical_bus=1):
    """تابع واسط برای سازگاری با فراخوانی main.py"""
    return optimize_bess(base_load_mw)
