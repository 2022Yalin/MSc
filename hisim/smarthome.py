import json
import os
import ast
import inspect
import sys
from components import weather
from components import building
from components import heat_pump_hplib
from components import controller
from components import storage
from components import pvs
from components import advanced_battery
from components import configuration
from components import chp_system
from components.hydrogen_generator import Electrolyzer ,HydrogenStorage
from components.demand_el import CSVLoader
from components.configuration import HydrogenStorageConfig, ElectrolyzerConfig
import simulator as sim
import loadtypes

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import cfg_automator

__authors__ = "Vitor Hugo Bellotto Zago"
__copyright__ = "Copyright 2021, the House Infrastructure Project"
__credits__ = ["Noah Pflugradt"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Vitor Hugo Bellotto Zago"
__email__ = "vitor.zago@rwth-aachen.de"
__status__ = "development"



def smarthome_setup(my_sim):


    ##### System Parameters #####

    # Set simulation parameters
    year = 2021
    seconds_per_timestep = 60

    # Set weather
    location = "Aachen"

    # Set occupancy
    occupancy_profile = "CH01"

    # Set building
    building_code = "DE.N.SFH.05.Gen.ReEx.001.002"
    building_class = "medium"
    initial_temperature = 23

    # Set photovoltaic system
    time = 2019

    load_module_data = False
    module_name = "Hanwha_HSL60P6_PA_4_250T__2013_"
    integrateInverter = True
    inverter_name = "ABB__MICRO_0_25_I_OUTD_US_208_208V__CEC_2014_"
    # Set Battery

    # Set CHP
    min_operation_time = 60
    min_idle_time = 15
    gas_type = "Hydrogen"
    # Set Electrolyzer
    electrolyzer_c = ElectrolyzerConfig()

    # Set Hydrogen Storage
    hydrogen_storage_c = HydrogenStorageConfig()

    ##### Build Components #####

    # Build system parameters
    my_sim_params: sim.SimulationParameters = sim.SimulationParameters.full_year(year=year,
                                                                                 seconds_per_timestep=seconds_per_timestep)
    my_sim.set_parameters(my_sim_params)

    # ElectricityDemand
    csv_load_power_demand = CSVLoader(component_name="csv_load_power",
                                      csv_filename="Lastprofile/SOSO/Orginal/EFH_Bestand_TRY_5_Profile_1min.csv",
                                      column=0,
                                      loadtype=loadtypes.LoadTypes.Electricity,
                                      unit=loadtypes.Units.Watt,
                                      column_name="power_demand",
                                      simulation_parameters=my_sim_params,
                                      multiplier=6)
    my_sim.add_component(csv_load_power_demand)



    # Build Weather
    my_weather = weather.Weather(location=location)
    my_sim.add_component(my_weather)

    # Build CHP
    my_chp = chp_system.CHP(min_operation_time=min_operation_time,
                            min_idle_time=min_idle_time,
                            gas_type=gas_type)

    # Build Electrolyzer

    my_electrolyzer = Electrolyzer(component_name="Electrolyzer",
                                   config=electrolyzer_c,
                                   seconds_per_timestep=my_sim_params.seconds_per_timestep)
    my_hydrogen_storage = HydrogenStorage(component_name="HydrogenStorage",
                                          config=hydrogen_storage_c,
                                          seconds_per_timestep=my_sim_params.seconds_per_timestep)
    # Build Controller
    my_controller = controller.Controller(strategy="seasonal_storage")

    my_photovoltaic_system = pvs.PVSystem(time=time,
                                          location=location,
                                          power=power,
                                          load_module_data=load_module_data,
                                          module_name=module_name,
                                          integrateInverter=integrateInverter,
                                          inverter_name=inverter_name,
                                          sim_params=my_sim_params)
    my_photovoltaic_system.connect_input(my_photovoltaic_system.TemperatureOutside,
                                         my_weather.ComponentName,
                                         my_weather.TemperatureOutside)
    my_photovoltaic_system.connect_input(my_photovoltaic_system.DirectNormalIrradiance,
                                         my_weather.ComponentName,
                                         my_weather.DirectNormalIrradiance)
    my_photovoltaic_system.connect_input(my_photovoltaic_system.DirectNormalIrradianceExtra,
                                         my_weather.ComponentName,
                                         my_weather.DirectNormalIrradianceExtra)
    my_photovoltaic_system.connect_input(my_photovoltaic_system.DiffuseHorizontalIrradiance,
                                         my_weather.ComponentName,
                                         my_weather.DiffuseHorizontalIrradiance)
    my_photovoltaic_system.connect_input(my_photovoltaic_system.GlobalHorizontalIrradiance,
                                         my_weather.ComponentName,
                                         my_weather.GlobalHorizontalIrradiance)
    my_photovoltaic_system.connect_input(my_photovoltaic_system.Azimuth,
                                         my_weather.ComponentName,
                                         my_weather.Azimuth)
    my_photovoltaic_system.connect_input(my_photovoltaic_system.ApparentZenith,
                                         my_weather.ComponentName,
                                         my_weather.ApparentZenith)
    my_photovoltaic_system.connect_input(my_photovoltaic_system.WindSpeed,
                                         my_weather.ComponentName,
                                         my_weather.WindSpeed)
    my_sim.add_component(my_photovoltaic_system)



    my_controller.connect_input(my_controller.ElectricityConsumptionBuilding,
                                csv_load_power_demand.ComponentName,
                                csv_load_power_demand.Output1)

    my_controller.connect_input(my_controller.ElectricityOutputPvs,
                                my_photovoltaic_system.ComponentName,
                                my_photovoltaic_system.ElectricityOutput)

    my_electrolyzer.connect_input(my_electrolyzer.ElectricityInput,
                                  my_controller.ComponentName,
                                  my_controller.ElectricityToElectrolyzerTarget)

    my_electrolyzer.connect_input(my_electrolyzer.HydrogenNotStored,
                                  my_hydrogen_storage.ComponentName,
                                  my_hydrogen_storage.HydrogenNotStored)

    my_controller.connect_input(my_controller.ElectricityToElectrolyzerReal,
                                my_electrolyzer.ComponentName,
                                my_electrolyzer.UnusedPower)
    my_controller.connect_input(my_controller.ElectricityFromCHPReal,
                                my_chp.ComponentName,
                                my_chp.ElectricityOutput)

    my_hydrogen_storage.connect_input(my_hydrogen_storage.ChargingHydrogenAmount,
                                      my_electrolyzer.ComponentName,
                                      my_electrolyzer.HydrogenOutput)
    my_hydrogen_storage.connect_input(my_hydrogen_storage.DischargingHydrogenAmountTarget,
                                      my_chp.ComponentName,
                                      my_chp.GasDemandTarget)

    my_chp.connect_input(my_chp.HydrogenNotReleased,
                         my_hydrogen_storage.ComponentName,
                         my_hydrogen_storage.HydrogenNotReleased)

    my_chp.connect_input(my_chp.ControlSignal,
                         my_controller.ComponentName,
                         my_controller.ControlSignalChp)
    my_chp.connect_input(my_chp.ElectricityFromCHPTarget,
                         my_controller.ComponentName,
                         my_controller.ElectricityFromCHPTarget)

    # my_sim.add_component(my_battery)

    my_sim.add_component(my_controller)

    my_sim.add_component(my_chp)
    my_sim.add_component(my_electrolyzer)
    my_sim.add_component(my_hydrogen_storage)



if __name__ == '__main__':
    list_for_PV_size = [1, 5, 10, 20, 50, 100]*1000
    for index_b, pv_power in enumerate(list_for_PV_size):
        global power
        power=pv_power
        command_line = "python hisim.py smarthome smarthome_setup"
        os.system(command_line)