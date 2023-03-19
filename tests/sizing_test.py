from testing import adsp
import sys

# ==========set input file ############### 
opt = adsp.SizingOptimization(input_filename=sys.argv[1])
# ==============Run Sizing Optimization===========
opt.run()
wingloading = opt.cb.wing_loading
powerloading = opt.cb.power_loading
mass_opt = opt.cb.mass_total_out
# ==================== Sizing Matrix ===================
constraint_diagram = opt.run_sizing_matrix_plot(wingloading_opt=wingloading, 
                                  powerloading_opt=powerloading)
opt.report.add_constraint_diagram(constraint_diagram)

# ============= Save Figure for Mass Break Down===============
mass_breakdown = opt.get_mass_break_down(mass_opt = mass_opt)
opt.report.add_mass_breakdown(mass_breakdown)

# ================== Payload Range trade off ===============
specific_energy_sweep = [ 300, 700, 1000]
payload_sweep = [0,  500, 1154]
payload_range_tradeoff = opt.plot_range_payload(specific_energy_sweep, 
                                payload_sweep, mass_opt)
opt.report.add_payload_range_tradeoff(payload_range_tradeoff)

# ====================== Stall and Maximum Speed Trade off ===============
stall_max_speed_tradeoff = opt.run_stall_speed_max_speed_carpet_plot(powerloading_opt=powerloading, 
                                                  mass_opt=mass_opt)
opt.report.add_stall_max_speed_tradeoff(stall_max_speed_tradeoff)

# =================== saving report =====================
opt.save_report('')
    

#  ==========================Carpet Plot for evaluaiton ========
carpet_plot = opt.run_carpet_plot(wingloading_min=800, wingloading_max=2000,
                            powerloading_min=9, powerloading_max=20)
carpet_plot.write_image("Carpet_plot.png")
    
    
    
    