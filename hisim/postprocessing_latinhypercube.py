import globals
import numpy as np
import pandas as pd
import json
import os
import pickle
import seaborn as sns

#plot stuff
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator

class PostProcessor:
    def __init__(self,
                 folder_name : str, #folder has to be in results
                 json_file_name : str,
                 pickle_file_name:str,
                 start_date : str, #in
                 end_date : str,
                 heat_map_precision_factor: int,
                 plot_heat_map=True,
                 plot_all_houses=True,
                 plot_sfh=False,
                 plot_mfh=False,
                 plot_strategy_all=True,
                 plot_strategy_own_consumption=True,
                 plot_strategy_seasonal_storage=True,
                 plot_strategy_peak_shave_into_grid =True,
                 plot_own_consumption=False,
                 plot_autarky=False,
                 plot_battery_and_pv=False,
                 plot_h2_storage_relative_demand=False,
                 plot_h2_storage_relative_battery=False,
                 plot_peak_shaving_demand_accurancy=False,
                 plot_peak_shaving_generation_accurancy=False,
                 plot_net_present_value=True,
                 electricity_price_from_grid_household=0.3205,
                 electricity_price_into_grid_household=0.3205,
                 interest_rate=0.0542,
                 time_frame_to_look_at=20):
        self.folder_name=folder_name
        self.start_date = start_date
        self.end_date = end_date
        self.json_file_name = json_file_name
        self.pickle_file_name = pickle_file_name
        self.heat_map_precision_factor = heat_map_precision_factor
        self.electricity_price_from_grid_household = electricity_price_from_grid_household
        self.electricity_price_into_grid_household = electricity_price_into_grid_household
        self.interest_rate = interest_rate
        self.time_frame_to_look_at =time_frame_to_look_at

        self.flags_plots ={"plot_heat_map": plot_heat_map}
        self.flags_houses = {"plot_all_houses": plot_all_houses,
                              "plot_sfh": plot_sfh,
                              "plot_mfh": plot_mfh}
        self.flags_strategy= {"plot_strategy_all": plot_strategy_all,
                              "plot_strategy_own_consumption": plot_strategy_own_consumption,
                              "plot_strategy_seasonal_storage": plot_strategy_seasonal_storage,
                              "plot_strategy_peak_shave_into_grid": plot_strategy_peak_shave_into_grid}
        self.flags_components={"plot_battery_and_pv": plot_battery_and_pv,
                              "plot_h2_storage_relative_demand": plot_h2_storage_relative_demand,
                               "plot_h2_storage_relative_battery": plot_h2_storage_relative_battery,
                               "plot_peak_shaving_demand_accurancy": plot_peak_shaving_demand_accurancy,
                               "plot_peak_shaving_generation_accurancy": plot_peak_shaving_generation_accurancy,
                               "plot_net_present_value" : plot_net_present_value}
        self.flags_kpis={"plot_own_consumption":plot_own_consumption,
                         "plot_autarky":plot_autarky,
                         "plot_net_present_value": plot_net_present_value}
    def get_json_data(self,new_list,target_matrix):

        for a in  range(len(new_list)):
            newrow = []
            #soemtimes cfg isn't saved. idk why
            try :
                json.load(open(os.path.join(globals.HISIMPATH["results"], ""+str(new_list[a])+"/"+str(self.json_file_name)+".json")))
            except OSError:
                print("Error:not found: "+(os.path.join(globals.HISIMPATH["results"], ""+str(new_list[a])+"/"+str(self.json_file_name)+".json"))+"")
                continue
            json_data=json.load(open(os.path.join(globals.HISIMPATH["results"], ""+str(new_list[a])+"/"+str(self.json_file_name)+".json")))#
            newrow.append(json_data.get("Components", {}).get("Weather", {}).get("location", None ))
            housetype=(json_data.get("Components", {}).get("CSVLoaderWW", {}).get("csv_filename", None ))
            if "mfh" in housetype:
                newrow.append("mfh")
            elif "sfh" in housetype:
                newrow.append("sfh")
            else:
                print("Error: not efh or mfh is the housetype")
            newrow.append(json_data.get("Components", {}).get("CSVLoaderWW", {}).get("multiplier", None ))
            newrow.append(json_data.get("Components", {}).get("CSVLoaderHW", {}).get("multiplier", None ))
            newrow.append(json_data.get("Components", {}).get("CSVLoaderEL", {}).get("multiplier", None ))
            newrow.append(json_data.get("Components", {}).get("PVSystem", {}).get("power", None ))
            newrow.append(json_data.get("Components", {}).get("AdvancedBattery", {}).get("capacity", None ))
            newrow.append(json_data.get("Components", {}).get("HeatPumpHplib", {}).get("p_th_set", None ))
            newrow.append(json_data.get("Components", {}).get("GasHeater", {}).get("power_max", None ))
            newrow.append(json_data.get("Components", {}).get("CHP", {}).get("p_el_max", None ))
            newrow.append(json_data.get("Components", {}).get("Electrolyzer", {}).get("power_electrolyzer", None ))
            newrow.append(json_data.get("Components", {}).get("HeatStorage", {}).get("V_SP_heating_water", None ))
            newrow.append(json_data.get("Components", {}).get("HeatStorage", {}).get("V_SP_warm_water", None ))
            newrow.append(json_data.get("Components", {}).get("HydrogenStorage", {}).get("max_capacity", None ))
            newrow.append(json_data.get("Components", {}).get("Controller", {}).get("strategy", None ))
            newrow.append(json_data.get("Components", {}).get("Controller", {}).get("percentage_to_shave", None ))
            newrow.append(json_data.get("Components", {}).get("Controller", {}).get("limit_to_shave", None))
            target_matrix = np.vstack([target_matrix, newrow])
        return target_matrix


    def get_all_relevant_folders(self):
        folder_list=os.listdir(os.path.join(globals.HISIMPATH["results"]))
        new_list=[]
        start_date = int(self.start_date.replace("_", ""))
        end_date = int(self.end_date.replace("_", ""))
        a=0
        while a < len(folder_list):
            a=a+1
            if self.folder_name in folder_list[a-1]:
                split_string=folder_list[a-1].split("_",20)
                if "." in split_string[len(split_string)-1]:
                    variable = int(folder_list[a - 1].replace(self.folder_name, "").replace(split_string[len(split_string)-1],"").replace("_", ""))
                else:
                    variable=int(folder_list[a-1].replace(self.folder_name,"").replace("_",""))
                if start_date <= variable and variable<=end_date:
                    new_list.append(folder_list[a-1])
        return new_list

    def get_pickle_informations(self,new_list,key_performance_indicators,target_matrix):
        b=0
        for a in  range(len(new_list)):
            newrow = []
            objects=[]

            #soemtimes pickle isn't saved. idk why
            try:
                with open((os.path.join(globals.HISIMPATH["results"],
                                        "" + str(new_list[a]) + "/" + str(self.pickle_file_name) + ".pkl")),
                          "rb") as openfile:
                    try:
                        objects.append(pickle.load(openfile))
                        b=b+1
                    except OSError:
                        print(self.pickle_file_name)
                    #Here starts Calculation of Parameters
                    A = (objects[0]['results'].T.T)
                    sum_Produced_Elect_pv= sum((A["PVSystem - ElectricityOutput [Electricity - W]"]))
                    sum_Demand_Elect_house = sum((A["CSVLoaderEL - electricity demand, house [W] [Electricity - W]"]))

                    '''
                    sum_Electricity_From_Grid=sum(x for x in A["Controller - ElectricityToOrFromGrid [Electricity - W]"] if x > 0)
                    #weird thing, which only happens if Electrolyzer is in system. Than out of some reason electricity goes into grid, when it shouldnt.
                    #but rest of the values or right
                    sum_Electricity_Into_Grid=0
                    sum_Electricity_From_Grid=0
                    variable_to_watch_weird_elect_thing=0
                    for x, y in zip(A["Controller - ElectricityToOrFromGrid [Electricity - W]"],A["Controller - ElectricityToOrFromBatteryTarget [Electricity - W]"]):
                        if x<0 and y<0:
                            sum_Electricity_From_Grid=sum_Electricity_From_Grid-y
                            variable_to_watch_weird_elect_thing=1
                            continue
                        elif x>0:
                            sum_Electricity_From_Grid=sum_Electricity_From_Grid+x
                        elif x<0:
                            sum_Electricity_Into_Grid=sum_Electricity_Into_Grid-x
                    if variable_to_watch_weird_elect_thing==1:
                        if "Electrolyzer - Unused Power [Electricity - W]" in A:
                            print("watchout-electrolyzer is acting weird")
                        else:
                            print("other component is acting werid")

                    '''
                    sum_Electricity_From_Grid=sum(x for x in A["Controller - ElectricityToOrFromGrid [Electricity - W]"] if x > 0)
                    sum_Electricity_Into_Grid = -sum(x for x in A["Controller - ElectricityToOrFromGrid [Electricity - W]"] if x < 0)

                    if "AdvancedBattery - AC Battery Power [Electricity - W]" in A:
                        sum_Demand_Battery= sum(x for x in A["AdvancedBattery - AC Battery Power [Electricity - W]"] if x > 0)
                    else:
                        sum_Demand_Battery = 0
                    if "AdvancedBattery - AC Battery Power [Electricity - W]" in A:
                        sum_Produced_Elect_Battery= sum(x for x in A["AdvancedBattery - AC Battery Power [Electricity - W]"] if x < 0)
                    else:
                        sum_Produced_Elect_Battery = 0

                    if "HeatPumpHplib - ElectricalInputPower [Electricity - W]" in A:
                        sum_Demand_Elect_heat_pump= sum((A["HeatPumpHplib - ElectricalInputPower [Electricity - W]"]))
                    else:
                        sum_Demand_Elect_heat_pump = 0

                    if "Electrolyzer - Unused Power [Electricity - W]" in A:
                        sum_Demand_Elect_electrolyzer= sum((A["Controller - ElectricityToElectrolyzerTarget [Electricity - W]"])) - sum((A["Electrolyzer - Unused Power [Electricity - W]"]))

                    else:
                        sum_Demand_Elect_electrolyzer = 0

                    if "CHP - ElectricityOutput [Electricity - W]" in A:
                        sum_Produced_Elect_chp= sum((A["CHP - ElectricityOutput [Electricity - W]"]))
                    else:
                        sum_Produced_Elect_chp = 0

                    if "CHP - ElectricityOutput [Electricity - W]" in A:
                        sum_Produced_Elect_chp= sum((A["CHP - ElectricityOutput [Electricity - W]"]))
                    else:
                        sum_Produced_Elect_chp = 0

                    if "CHP - ElectricityOutput [Electricity - W]" in A:
                        sum_Produced_Elect_chp= sum((A["CHP - ElectricityOutput [Electricity - W]"]))
                    else:
                        sum_Produced_Elect_chp = 0

                    sum_Demand=sum_Demand_Elect_heat_pump+sum_Demand_Elect_house+sum_Demand_Elect_electrolyzer+sum_Demand_Battery

                    sum_Produced=sum_Produced_Elect_pv+sum_Produced_Elect_Battery+sum_Produced_Elect_chp

                    own_consumption=(sum_Produced_Elect_pv-sum_Electricity_Into_Grid)/(sum_Produced_Elect_pv)
                    autarky=(sum_Demand - sum_Electricity_From_Grid) / (sum_Demand)

                    own_consumption=(sum_Produced-sum_Electricity_Into_Grid)/sum_Produced

                    bat_size=target_matrix[b,6]#kwh
                    cost_bat=(1374.6 * bat_size ** (-0.203))* bat_size

                    pv_size=target_matrix[b,5] #kW
                    if pv_size == None:
                        pv_size=0
                        cost_pv=0
                    else:
                        pv_size = target_matrix[b, 5] / 1000
                        cost_pv=(2095.8 * pv_size ** (-0.166))* pv_size

                    chp_size=target_matrix[b,9] #kW
                    if chp_size == None:
                        chp_size=0
                        cost_chp=0
                    else:
                        chp_size = target_matrix[b, 9] / 1000
                        cost_chp=(25689 * chp_size ** (-0.581))* chp_size


                    h2_storage_size=target_matrix[b,13] #in liters, need to be changed into MWH!!
                    if h2_storage_size == None:
                        h2_storage_size=0
                        cost_h2_storage=0
                    else:
                        h2_storage_size = target_matrix[b, 13]
                        cost_h2_storage = (14990 * h2_storage_size ** (-0.079)) * h2_storage_size

                    electrolzer_size=target_matrix[b,10]#in liters, need to be changed into MWH!!
                    if electrolzer_size == None:
                        electrolzer_size=0
                        cost_chp=0
                        cost_electrolyzer=0
                    else:
                        electrolzer_size = target_matrix[b, 10]
                        cost_electrolyzer = (5012.9 * electrolzer_size ** (-0.054)) * electrolzer_size

                    if pv_size<10:
                        electricity_prize_into_grid=0.0769
                    elif pv_size<40 and pv_size>10:
                        electricity_prize_into_grid = 0.0747
                    elif pv_size>40:
                        electricity_prize_into_grid = 0.0587

                    cost_total_investment= cost_bat + cost_pv + cost_chp + cost_h2_storage + cost_electrolyzer
                    #choose here electricity prize# has to be added!
                    income_delta= (0.25/1000)*(-sum_Electricity_From_Grid* self.electricity_price_from_grid_household + sum_Electricity_Into_Grid *electricity_prize_into_grid)

                    net_present_value_with_bat= - cost_total_investment + income_delta*(1+self.interest_rate)**(self.time_frame_to_look_at)

                    if "CHP - ElectricityOutput [Electricity - W]" in A:
                        if "HeatPumpHplib - ElectricalInputPower [Electricity - W]" in A:
                            pass

                    net_present_value_without_bat= 0 +0
                    if own_consumption > 1:
                        print("owncumption is bigger than one :" +str(own_consumption))
                        own_consumption=1
                    elif own_consumption <  0:
                        print("owncumption is smaller than one :" + str(own_consumption))
                        own_consumption=0.001
                    if autarky > 1:
                        print("autarky is bigger than one :" +str(autarky))
                        autarky=1
                    elif autarky <  0:
                        print("autarky is smaller than one :" + str(autarky))
                        autarky=0.001

                    newrow.append(own_consumption) #own_consumption
                    newrow.append(autarky) #autarky
                    newrow.append(net_present_value)
                    key_performance_indicators = np.vstack([key_performance_indicators, newrow])

            except OSError:
                print("Error:not found: "+(os.path.join(globals.HISIMPATH["results"], ""+str(new_list[a])+"/"+str(self.pickle_file_name)+".pickle"))+"")
                continue
        return key_performance_indicators


    def transform_data_for_plot(self,target_matrix,key_performance_indicators,kpi,component):
        breaker=False
        num_rows, num_cols = target_matrix.shape
        if num_rows ==1:
            breaker=True
            return 0, 0 ,0, breaker
        x = 0
        x_axis = []
        y_axis = []
        own_consumption = []
        autarky = []
        while x < (num_rows - 1):
            x = x + 1
            if component in "plot_battery_and_pv":
                x_axis.append((target_matrix[x, 5] / 1000) / target_matrix[x, 4])  # in kW/kW
                y_axis.append(target_matrix[x, 6] / (target_matrix[x, 4]))  # in kWh/kw
            elif component in "plot_net_present_value":
                x_axis.append((target_matrix[x, 5] / 1000) / target_matrix[x, 4])  # in kW/kW
                y_axis.append(target_matrix[x, 6] / (target_matrix[x, 4]))  # in kWh/kw

            elif component in "plot_h2_storage_relative_demand":
                if target_matrix[x, 13] == None or target_matrix[x, 13] == 0:
                    breaker = True
                    return 1, 0 ,0, breaker
                else:
                    x_axis.append((target_matrix[x, 5]/1000) / target_matrix[x, 6])  # in kW/kW
                    y_axis.append(target_matrix[x, 13]/(target_matrix[x, 4])) # in kWh/kw
            elif component in "plot_h2_storage_relative_battery":
                if target_matrix[x, 13] == None or target_matrix[x, 13] == 0:
                    breaker = True
                    return 1, 0 ,0, breaker
                else:
                    x_axis.append((target_matrix[x, 5]/1000) / target_matrix[x, 4])  # in kW/kW
                    y_axis.append(target_matrix[x, 13]/(target_matrix[x, 6])) # in kWh/kw
            elif component in "plot_peak_shaving_generation_accurancy":
                print("stop")

            else:
                print("no component to print choosed")
                return 1, 0, 0, breaker
        x_axis = np.around(np.array(x_axis), decimals=2)
        y_axis = np.around(np.array(y_axis), decimals=2)
        if kpi == "OwnConsumption":
            key_to_look_at = key_performance_indicators[1::, 0]
        elif kpi == "Autarky":
            key_to_look_at = key_performance_indicators[1::, 1]
        elif kpi == "NetPresentValue":
            key_to_look_at = key_performance_indicators[1::, 2]

        # Set up Matrix and fill with values-Has to be done bec. of Latin Hypercube design
        plot_boundaries = [[((min(x_axis))), (max(x_axis))],
                           [(min(y_axis)), (max(y_axis))]]
        precision_x_axis = (plot_boundaries[(0)][1] - plot_boundaries[(0)][0]) / self.heat_map_precision_factor
        precision_y_axis = (plot_boundaries[(1)][1] - plot_boundaries[(1)][0]) / self.heat_map_precision_factor
        grid = np.full([self.heat_map_precision_factor+1, self.heat_map_precision_factor+1], 0.0)
        x = 0
        while x < (len(x_axis)):
            x_index = round((x_axis[x] - plot_boundaries[(0)][0]) / precision_x_axis)
            y_index = round((y_axis[x] - plot_boundaries[(1)][0]) / precision_y_axis)



            if grid[y_index, x_index] == 0:
                grid[y_index, x_index] = float(key_to_look_at[x])
            else:
                grid[y_index, x_index] = ((grid[y_index, x_index]) + float(key_to_look_at[x]))/ 2
            x = x + 1
        Z =grid
        x= np.arange (plot_boundaries[(0)][0], plot_boundaries[(0)][1], precision_x_axis)
        y= np.arange (plot_boundaries[(1)][0], plot_boundaries[(1)][1], precision_y_axis)
        return Z, x, y, breaker


    def sort_out_because_of_house_choosing(self,target_matrix,key_performance_indicators,x ):
        breaker= False
        if x=="plot_all_houses":
            target_matrix_new = target_matrix
            key_performance_indicators_new = key_performance_indicators
        elif x=="plot_sfh":
            target_matrix_new = np.delete(target_matrix, np.where(target_matrix == "mfh")[0], 0)
            key_performance_indicators_new = np.delete(key_performance_indicators,
                                                       np.where(target_matrix == "mfh")[0], 0)

        elif x=="plot_mfh":
            target_matrix_new = np.delete(target_matrix, np.where(target_matrix == "sfh")[0], 0)
            key_performance_indicators_new = np.delete(key_performance_indicators,
                                                       np.where(target_matrix == "sfh")[0], 0)
        else:
            breaker= True
            return 0 , 0 , breaker
        return target_matrix_new, key_performance_indicators_new, breaker
    def sort_out_because_of_strategy_choosing(self,target_matrix,key_performance_indicators,y):
        breaker= False
        if y=="plot_strategy_all":
            target_matrix_new = target_matrix.copy()
            key_performance_indicators_new = key_performance_indicators.copy()
        elif y=="plot_strategy_own_consumption":

            B =(target_matrix[np.any(target_matrix == "Weather", axis=1)])
            A = (target_matrix[np.any(target_matrix == "optimize_own_consumption", axis=1)])
            target_matrix_new=np.append(B,A,axis=0)

            C = key_performance_indicators.copy()
            i=0
            while i < (len(target_matrix[:,14])-1):
                i=i+1
                if target_matrix[i,14] != "optimize_own_consumption":
                    C[i,0] = "delete"
            key_performance_indicators_new = np.delete(C, np.where(C == "delete")[0], 0)






        elif y=="plot_strategy_seasonal_storage":

            B =(target_matrix[np.any(target_matrix == "Weather", axis=1)])
            A = (target_matrix[np.any(target_matrix == "seasonal_storage", axis=1)])
            target_matrix_new=np.append(B,A,axis=0)
            key_performance_indicators_new=key_performance_indicators.copy()
            i=0
            while i < (len(target_matrix[:,14])-1):
                i=i+1
                if target_matrix[i,14] != "seasonal_storage":
                    key_performance_indicators_new[i,0] = "delete"

            key_performance_indicators_new = np.delete(key_performance_indicators_new, np.where(key_performance_indicators_new == "delete")[0], 0)


        elif y=="plot_strategy_peak_shave_into_grid":

            B =(target_matrix[np.any(target_matrix == "Weather", axis=1)])
            A = (target_matrix[np.any(target_matrix == "peak_shaving_into_grid", axis=1)])
            target_matrix_new=np.append(B,A,axis=0)
            key_performance_indicators_new=key_performance_indicators.copy()
            i=0
            while i < (len(target_matrix[:,14])-1):
                i=i+1
                if target_matrix[i,14] != "peak_shaving_into_grid":
                    key_performance_indicators_new[i,0] = "delete"

            key_performance_indicators_new = np.delete(key_performance_indicators_new, np.where(key_performance_indicators_new == "delete")[0], 0)
        else:
            breaker= True
            return 0, 0, breaker
        #elif self.flags["plot_strategy_peak_shave_into_grid"]:
            #pass
        return target_matrix_new , key_performance_indicators_new, breaker


    def calculate_correlations(self,target_matrix,key_performance_indicators):
        for house in self.flags_houses:
            target_matrix_new_after_house, key_performance_indicators_new_after_house, breaker = self.sort_out_because_of_house_choosing(
                target_matrix=target_matrix, key_performance_indicators=key_performance_indicators, x=house)
            if breaker:
                continue
    def analyze_salib(self):
        pass
    def plot_heat_map(self,target_matrix,key_performance_indicators):

        for kpi in key_performance_indicators[0,:]:
            if kpi== "OwnConsumption" and self.flags_kpis.get("plot_own_consumption")==True:
                pass
            elif kpi == "Autarky" and self.flags_kpis.get("plot_autarky") == True:
                pass
            elif kpi == "NetPresentValue" and self.flags_kpis.get("plot_net_present_value") == True:
                pass
            else:
                continue
            for house in self.flags_houses:
                if self.flags_houses[house]==False:
                    continue
                target_matrix_new_after_house, key_performance_indicators_new_after_house, breaker=self.sort_out_because_of_house_choosing(target_matrix=target_matrix,key_performance_indicators=key_performance_indicators, x=house)
                if breaker:
                    continue
                for strategy in self.flags_strategy:
                    if self.flags_strategy[strategy] == False:
                        continue
                    target_matrix_after_stragey, key_performance_indicators_new_after_strategy, breaker= self.sort_out_because_of_strategy_choosing(target_matrix=target_matrix_new_after_house, key_performance_indicators=key_performance_indicators_new_after_house,y=strategy )
                    if breaker:
                        continue
                    for component in self.flags_components:
                        if self.flags_components[component] == False:
                            continue
                        Z, x ,y, breaker=self.transform_data_for_plot(target_matrix=target_matrix_after_stragey, key_performance_indicators=key_performance_indicators_new_after_strategy,kpi=kpi,component=component)
                        if breaker == True and Z==0:
                            print(""+house+" with "+strategy+" has no simulation results and can't be printed")
                            continue
                        elif breaker == True and Z==1:
                            continue
                        fig, ax = plt.subplots()
                        if component == "plot_net_present_value":
                            cax = ax.pcolormesh(Z, cmap="YlGnBu")  # vmax=1 for own consumption good
                        else:
                            cax=ax.pcolormesh(Z,cmap="YlGnBu",vmin=0)   #vmax=1 for own consumption good
                        cbar = fig.colorbar(cax)
                        cbar.ax.set_ylabel(kpi)

                        ax.set_xticks(range(len(x)))
                        ax.set_yticks(range(len(y)))

                        ax.set_xticklabels(list(np.round(x,1)))
                        ax.set_yticklabels(list(np.round(y,1)))
                        ax.set_title("" + house + " with " + strategy + "")
                        #ax.set_xticklabels(xticklabels)

                        if component == "plot_h2_storage_relative_demand":
                            plt.xlabel('PV-Power kWp/Battery-Capacity kWh')
                            plt.ylabel('H2 Storage in litres / MWh')
                        elif component == "plot_h2_storage_relative_battery":
                            plt.xlabel('PV-Power kWp/Demand MWh')
                            plt.ylabel('H2 Storage in litres / BatteryCapacity kWh')
                        elif component == "plot_net_present_value":
                            plt.xlabel('PV-Power kWp/Demand MWh')
                            plt.ylabel('H2 Storage in litres / BatteryCapacity kWh')
                        else:
                            plt.xlabel('PV-Power kWp/MWh')
                            plt.ylabel('Battery-Capacity kWh/MWh')

                    #hier ne ebsser Abrufung bauen!!!!
                        plt.savefig(""+component+"_" + house + " _with_" + strategy + ".png")
                        plt.show()



                    '''
                    fig, ax = plt.subplots()
                    sns.set_theme()
                    uniform_data = Z
                    sns.heatmap(uniform_data,vmin=0, vmax=1, cbar_kws={'label': kpi}, cmap="YlGnBu")
                    ax.set(xlabel='PV-Power kWp/MWh', ylabel='Battery-Capacity kWp/MWh')
                    ax.set_title(""+house+" with " +strategy+"")
                    ax.set_xlim(min(x),max(x))
                    ax.set_xticks(range(0,int(max(x))))

                    ax.set_ylim(min(y), max(y))
                    ax.set_yticks(range(0,int(max(y))))

                    ax.invert_yaxis()

                    plt.show()
                    '''






    def run(self):
        #I am working with numpy array instead of dict, bec. can be made better to grafics.
        #Names are not consistent in Components, so hard to automize
        target_matrix= np.array(["Weather",
                                 "HouseType",
                                 "WarmWaterDemand",
                                 "HeatingWaterDemand",
                                 "ElectricityDemand",
                                 "PVSystemPower",
                                 "BatteryCapacity",
                                 "HeatPumpPower",
                                 "GasHeaterPower",
                                 "CHPPower",
                                 "ElectrolyzerPower",
                                 "HeatStorageVolume",
                                 "WarmWaterStorageVolume",
                                 "HydrogenStorageVolume",
                                 "ControlStrategy",
                                 "PercentageToShave",
                                 "LimitToShave"])

        key_performance_indicators=np.array(["OwnConsumption",
                                             "Autarky",
                                             "NetPresentValue"
                                             ])
        new_list = self.get_all_relevant_folders()
        target_matrix=self.get_json_data(new_list,target_matrix)

        key_performance_indicators=self.get_pickle_informations(new_list,key_performance_indicators,target_matrix)
        #self.calculate_correlations(key_performance_indicators,target_matrix)
        self.plot_heat_map(target_matrix,key_performance_indicators)
        self.analyze_salib()


my_Post_Processor=PostProcessor(folder_name="basic_household_implicit_salib_household_",
                                json_file_name="cfg",
                                pickle_file_name="data",
                                start_date="20211201_100100",
                                end_date="20211204_150000",
                                heat_map_precision_factor=30)
my_Post_Processor.run()
#f=open("HiSim/hisim/results/basic_household_implicit_hyper_cube_20211113_130857/cfg.json",)
#data = json.load(f)

'''
Metalworking 14
development
Water treatment
Producing industry
Manufacturing industry 3
Hotel
Health care services
Services 2
Chemical industry
Waste disposal 4
Woodworking industry 2
Building materials 1
Woodworking industry 3
Furniture retail 3
Gravel 4
Production 2
Quarry 4
Polymer processing 2
Sawmill 1
Garden 2
School 35
(Pre-)School 1
Other 8
Zoo
Event hall 4
Graveyard 2
Office building 15
Water pump 5
Swimming Pool 4
Gym 2
Library 1
Tunnel 1
Firefighters 1
Trailer park
Garage
toolmanufactor # aber nicht so als Name
electroplating # aber nicht so als anmae
'''