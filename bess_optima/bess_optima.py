"""
bess_optima.optimizer
Sizes the BESS and generates optimal dispatch strategy for Peak Shaving.
"""

import numpy as np

def optimize_bess(grid_power_profile: list, eta: float = 0.92) -> dict:
    T = len(grid_power_profile)
    p_net = np.array(grid_power_profile)
    
    # پارامترهای ظرفیت پیشنهادی
    peak_val = np.max(p_net)
    target_shave_mw = 0.35 * peak_val
    
    p_rated_mw = round(target_shave_mw, 2)
    e_rated_mwh = round(p_rated_mw * 3.5, 2)  # ۳.۵ ساعت ذخیره‌سازی
    
    p_ch = np.zeros(T)
    p_dis = np.zeros(T)
    soc = np.zeros(T)
    current_soc = 0.5 * e_rated_mwh
    
    p_modified = []
    
    for t in range(T):
        val = p_net[t]
        
        # شارژ هنگام تولید مازاد خورشیدی
        if val < 0 and current_soc < 0.90 * e_rated_mwh:
            ch = min(abs(val), p_rated_mw, (0.90 * e_rated_mwh - current_soc) / eta)
            p_ch[t] = ch
            current_soc += ch * eta
            
        # دشارژ در ساعات پیک شبانه
        elif val > (peak_val - target_shave_mw) and current_soc > 0.15 * e_rated_mwh:
            dis = min(val - (peak_val - target_shave_mw), p_rated_mw, (current_soc - 0.15 * e_rated_mwh) * eta)
            p_dis[t] = dis
            current_soc -= dis / eta
            
        soc[t] = current_soc
        p_modified.append(val + p_ch[t] - p_dis[t])
        
    return {
        "p_rated_mw": p_rated_mw,
        "e_rated_mwh": e_rated_mwh,
        "p_grid_before": p_net.tolist(),
        "p_grid_after": p_modified,
        "peak_shaved_mw": round(peak_val - max(p_modified), 2)
    }
