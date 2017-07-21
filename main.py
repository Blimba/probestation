#
#   Modular Probe Station Script
#
#   Author: Bart Limburg
#   Version: 12 July 2017
#
#   Usage:
#
#       This script file takes care of automated movement over devices.
#       For every device, 1 or more script files are called (explained below)
#
#       The script can import a file with a list of devices to loop over.
#       A csv file should be supplied. For example: a1,b2,g6
#       This would loop over those 3 devices. However, also ranges can be supplied
#       For example: a,c-e,f30-h3 would perform the entire column a (from the minimum row to the maximum row, defined below)
#       followed by the entire columns c, d and e. Lastly, it loops over devices f30 to the maximum number in column f,
#       do the entire column g, then from the minimum row of column h, to h3.
#       Lastly, supply * to loop over all devices on the defined chip.
#
#       More explanation can be found in the chip.py documentation
#
#       Your experiment script should have two basic functions:
#
#       def init():
#           In this function, define the instrument(s) that you will use. For example:
#           return qt.instruments.create('femto_dlpca_200','FEMTO_DLPCA_200',dev=1)
#           It is possible to return multiple devices, or perform other actions in this function
#
#       def start(instr,name,dev):
#           This function is called by the main script for every device over which it loops.
#           The instrument(s) returned by the init function are passed to the function.
#           In addition, the experiment name "name" and the current device "dev" are also passed.
#           This function is the heart of the script. Perform whatever you want to do for each device here.
#           For example, measure your IVtraces, perform electroburning, electroannealing, or whatever.
#           Optionally, the function may return a (list of) value(s) that will be saved in an expinfo file.
#           If you return the word "STOP" (or the word you set in the user customisable section below) the experiment
#           will stop automated movement and quit the application.
#
#       optionally, your script may contain the following function:
#
#       def end(instr,name):
#           This function is called after all devices have been looped over. Your instruments and the experiment name are passed to the function.
#           If your instruments require a shutdown command (or you want to terminate other things), do so here.
#
import os
import re
import inspect
import time
qtlab_dir = os.getcwd()  # the qtlab folder.
script_dir =  os.path.dirname(inspect.getabsfile(lambda x: 0))  # use a little cheat to get the script path.
try: os.chdir(script_dir)
except: raise SystemError("Error: Script directory not found! This is kind of impossible.")
from imports.chip import Chip
from imports.experiment import Experiment
from imports.cascade import Cascade
from imports.arduino import SignalSwitch
import imports.data as d
d.basepath = '%s%s\\%s' % (d.basepath, time.strftime('%Y'), script_dir.split('\\')[-1])
try: os.chdir(qtlab_dir)
except: raise SystemError("Error: QTLab directory not found! This is also kind of impossible.")
os.chdir(script_dir)
#################################
#                               #
#   USER CUSTOMISABLE SECTION   #
#                               #
#################################

# give the experiment name. This is used in all data files
name = raw_input("Experiment codename? ")

# load the chip object
chip = Chip(name=name,template='2T.ini')

# load the signal switch. Does signal switching automatically based on the name of the script file. Be careful: starting your scriptname with HP will make the signal switch to HP!
signal_switch = SignalSwitch()

# loads a chip design. See imports/chip.py documentation on how to make templates for chips
#if not chip.load_template('2T.ini', ignore_hidden=False):  # ignore the hidden devices (e.g. for the T2 chip, don't run experiments on row 38)
     #if the template cannot be found, we cannot run any experiments
    #raise SystemError('Chip template not found in directory (%s).' % os.getcwd())
#chip.define_devices('p24-w38', (0,0), (400, 200))  # manually design a chip without a template file (only use this for new designs)
#chip.limit_range('q23-w38')  # use this to cut up a standard design chip into quarters

# load the devices that should run on the current chip. Device ranges are treated by COLUMNS. i.e.:
# 'a' -> run the entire column a (as defined in the template)
# 'a-c' -> run the entire columns a, b and c
# 'b3-6' -> run column b from row 3 to 6 (i.e., b3, b4, b5 and b6)
# 'b15-c3' -> run column b from row 15 until the end of the column (as defined in the template), and column c from the beginning until c3.
# you may define multiple ranges by comma seperation (i.e., 'a3-5, b6, f').
# you may run a device multiple times: 'a1,a1'
chip.load_devices('a1')

# alternatively, load the devices from a csv file (given the same syntax as defined above)
# chip.load_from_file('exp_devices.csv')

# add experiments to the chip. The device ranges are treated as SQUARES. So: b3-c4 includes devices b3, b4, c3 and c4.
chip.add_experiment("ADwin_resistance",'a1-w37')
chip.add_experiment("HP_gatetrace",'a1-w37')  # signal switch will autoswitch to the HP here!
chip.add_experiment("ADwin_electroburn",'a1-w37')
chip.add_experiment("ADwin_IV_cycles",'a1-w37')
chip.add_experiment("HP_gatetrace",'a1-w37')  # signal switch will autoswitch to the HP here!

exp_stop_code = 'STOP'  # if this word is output by an experiment, the main script halts
exp_skip_code = 'SKIP'  # if this word is output by an experiment, the remaining experiments are skipped and the next device will run.
exp_run_code = 'RUN'  # if this word is output by an experiment, it will run the experiment that it output next in the outputlist (e.g., return ['RUN','ADwin_IV_cycles',dev])

# load the saved position of the cascade (set to False to input the current position if you moved the cascade manually)
load_saved_position = False

# start from the current position of cascade (set to false to start from the beginning of the list)
start_at_current_position = False

# if run_skipped_devices is set to true, and the current position of the cascade is not on the beginning of the list
# then we would go back to the beginning of the list after completing it. Otherwise, we stop at the end of the list
# for example, we are running column b, but the cascade is currently at device b3. When set to true,
# we would go from b3 to the end of the column, and then run b1 and b2. When set to false, b1 and b2 are not run.
run_skipped_devices = False

# when return_to_start is set to True, the cascade moves back to the starting device after completing the exp
return_to_start = False

#########################################
#                                       #
#   END OF USER CUSTOMISABLE SECTION    #
#                                       #
#########################################
os.chdir(qtlab_dir)

# load the cascade instrument
cascade = Cascade()

print("Please make sure that the cascade probes are in the contact setting!")
# try to find the current position of the cascade from the file.
if not cascade.store_position_file(filename='%s/positioning/%s.dat' % (script_dir, name)) or not load_saved_position:
    # current position not found, ask the user for the current position of the cascade
    cont = False
    while not cont:
        current_dev = raw_input('Current device? ')
        pos = chip.get_device_position(current_dev)
        if pos[0] == -1 and pos[1] == -1:
            print("Please input a device that is on the chip.")
        else:
            cont = True
    cascade.position = chip.get_device_position(current_dev)

# get the current device from the cascade position
current_dev = chip.get_device_from_position(cascade.position)

#############################################
#                                           #
#           START THE MEASUREMENT           #
#                                           #
#############################################

cascade.down()  #put the probes down. Ideally, you'd check if they were safe before starting, but it doesnt look like the cascade supports this.

if start_at_current_position:
    chip.start_at_device(current_dev, run_skipped_devices)  # sort the chip devices list to start at the current device (and either skip the devices or add them to the end of the list)

# loop over all devices that were loaded by the user
cont = True
for dev in chip:
    # run the experiments that were loaded by the user
    for experiment in chip.experiments:
        if dev in experiment:  # if the experiment should be run on the current device:
            # move the cascade to the new device position. The class checks if it is already at the current position and moves only when it needs to
            cascade.move_abs(chip.get_device_position(dev))
            # correct the signal switch settings hp / adwin
            settings = experiment.get_switch_settings()
            if not settings:
                settings = signal_switch.load_settings(experiment.script)  # load the signal switch settings
            signal_switch.route_settings(settings)
            # run the experiment
            output = experiment.run(dev)
            # handle experiment outputs
            if exp_stop_code in output:
                cont = False
                break
            if exp_skip_code in output:
                break
            while exp_run_code in output:
                # running extra experiments if required
                index = output.index(exp_run_code)
                try:
                    script = output[index+1]
                    device = output[index+2]
                except:
                    pass
                if not device or not re.match('([a-zA-Z]+)([0-9]+)',device):
                    device = dev
                if not script:
                    break
                exp = Experiment(script, name, device)
                cascade.move_abs(chip.get_device_position(device))
                output = exp.run(device)

    if not cont:
        break

# route the switch back to adwin for other people.
signal_switch.route(1,'ADWIN')
signal_switch.route(2,'ADWIN')
signal_switch.route(3,'ADWIN')

if return_to_start:
    cascade.move_abs(chip.get_device_position(chip.devices[0])) #move back to the front
#cascade.up()  # put the probes up, so that we see the measurement is completed.

for experiment in chip.experiments:
    experiment.end()

