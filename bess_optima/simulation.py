"""
bess_optima.simulation
Time-series power flow analysis to find voltage violations and critical nodes.
"""

import pandas as pd
import pandapower as pp

def run_timeseries_powerflow(net: pp.pandapowerNet, profiles: pd.DataFrame) -> dict:
    timesteps = len(profiles)
    monitored_buses = net.bus.index[net.bus.vn_kv == 20.0]
    
    vm_results = pd.DataFrame(index=range(timesteps), columns=monitored_buses)
    substation_active_power = []
    
    base_load_p = net.load.p_mw.copy()
    base_sgen_p = net.sgen.p_mw.copy()
    
    for t in range(timesteps):
        net.load.p_mw = base_load_p * profiles.loc[t, "load"]
        net.sgen.p_mw = base_sgen_p * profiles.loc[t, "pv"]
        
        pp.runpp(net, enforce_q_lims=True, calculate_voltage_angles=False)
        
        vm_results.loc[t, :] = net.res_bus.loc[monitored_buses, "vm_pu"]
        substation_active_power.append(net.res_ext_grid["p_mw"].sum())
        
    # ریست مقادیر پایه
    net.load.p_mw = base_load_p
    net.sgen.p_mw = base_sgen_p
    
    # شناسایی باسبار با بیشترین انحراف ولتاژ
    deviations = (vm_results - 1.0).abs().sum(axis=0)
    critical_bus_id = deviations.idxmax()
    
    return {
        "voltage_matrix": vm_results,
        "grid_power": substation_active_power,
        "critical_bus": critical_bus_id,
        "max_voltage": vm_results.max().max(),
        "min_voltage": vm_results.min().min()
    }
