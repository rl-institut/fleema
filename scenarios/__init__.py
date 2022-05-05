# simulation parameters for fleet management are set

[basic]
# basic parameters for the simulation
# ===========================
# definition of regional type to use for simulating driving behaviour
# efficiency of charging points
# timesteps (should stay at 15 min, best results)
# number of days to simulate, max: 14, suggested: 14 for best results
# minimum soc allowed before fast charging event is triggered
# grid_timeseries enables additional outputs, options: true, false

regio_type = LR_Zentr
eta_cp =  1
stepsize = 15
start_date = 2021-09-17
end_date = 2021-09-30
soc_min = 0.2
grid_timeseries = false
grid_timeseries_by_usecase = false

[rampup_ev]

# ramp up of electric vehicles
# ===========================
# number of cars for each type that are simulated
BEV_mini = 10
BEV_medium = 10
BEV_luxury = 10
PHEV_mini = 10
PHEV_medium = 10
PHEV_luxury = 10

[tech_data_cc_slow]

# charging capacity of each car type for AC-charging
# ===========================
# max. charging capacity in kW

BEV_mini = 11
BEV_medium = 22
BEV_luxury = 50
PHEV_mini = 3.7
PHEV_medium = 11
PHEV_luxury = 11

[tech_data_cc_fast]

# charging capacity of each car type for DC-charging
# ===========================
# max. charging capacity in kW
# PHEV are not capable of DC-charging

BEV_mini = 50
BEV_medium = 50
BEV_luxury = 150
PHEV_mini = 0
PHEV_medium = 0
PHEV_luxury = 0

[tech_data_bc]

# battery capacity of each car type
# ===========================
# battery capacity in kWh

BEV_mini = 30
BEV_medium = 65
BEV_luxury = 90
PHEV_mini = 20
PHEV_medium = 20
PHEV_luxury = 20

[tech_data_ec]

# energy consumption of each car type
# ===========================
# average energy consumption in kWh/km

BEV_mini = 0.13
BEV_medium = 0.16
BEV_luxury = 0.2
PHEV_mini = 0.16
PHEV_medium = 0.16
PHEV_luxury = 0.16

[charging_probabilities]

# charging probabilities for all locations
# ===========================
# share of private charging at home/work, 1 equals 100%

slow = charging_point_probability.csv
fast = fast_charging_probability.csv
private_charging_home = 0.5
private_charging_work = 0.7


[sim_params]

# simulation parameters
# ===========================
# parameters for running the simulation on your pc

num_threads = 1
seed = 3