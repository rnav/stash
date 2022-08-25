#!/usr/bin/python3

######################################################################
# purr_tb.py : A utility for validating whether the sum of the
#              values of the PURR register across the active threads
#              of cores over a time iterval matches the number of
#              timebase ticks for that interval. Also, display spurr,
#              idle_purr and idle_spurr values.
#
# Authors:
#         Kamalesh Babulal <kamalesh@linux.vnet.ibm.com>
#         Gautham R. Shenoy <ego@linux.vnet.ibm.com>
#         Naveen N. Rao <naveen.n.rao@linux.vnet.ibm.com>
#
# Based off of: https://github.com/gautshen/misc/blob/master/purr_tb.py
#
# (C) Copyright IBM Corp, 2022
######################################################################
import os, time, subprocess, getopt, sys

online_cpus=[]
purr={}
spurr={}
idle_purr={}
idle_spurr={}
purr_new={}
spurr_new={}
idle_purr_new={}
idle_spurr_new={}
cores_list = {}

###################################################
# Computes the list of online CPUs
###################################################
def get_online_cpus():
    with open('/proc/cpuinfo', 'r') as f:
        for line in f.readlines():
            if line.startswith('processor'):
                cpu = int(line.split()[2])
                online_cpus.append(cpu)

########################################################################
# Returns a string of online threads of the core @tl from the cores_map
########################################################################
def stringify(tl):
    retstring='['
    for t in tl:
        if int(t) in online_cpus:
            retstring = retstring + "%3d," %(int(t))
    last_comma_id=retstring.rfind(',')
    retstring = retstring[0:last_comma_id] + "]"
    return retstring

########################################################################
# Determines the map of active cores to their constituent threads
# from the ppc64_cpu utility
#
# The map is saved in the global variable cores_list{}
########################################################################
def get_core_map():
    cores_str = str(subprocess.check_output('ppc64_cpu --info', shell=True)).split('\\n')
    active_cores_list = map(lambda c:c.replace('*', ''),
                            filter(lambda c:c.find('*') >= 0, cores_str))
    idx = 0
    for core in active_cores_list:
        if (core.find('Core') == -1):
            continue
        tmp = core.split(':')[1]
        tmp = ' '.join(tmp.split())
        tmp = tmp.split('\'')[0].replace('\\n', '').split(" ")
        cores_list[idx] = tmp
        idx = idx + 1

########################################################################
#  Prints the following banner:
#  =========================================
#  Core      tb(apprx)    purr
#  =========================================
########################################################################
def print_banner():
    banner = ""
    header = ""
    if len(cores_list) == 0:
        return

    banner = "Core"
    mystring = "Core%02d %s" %(0, stringify(cores_list[0]))

    paddinglen = len(mystring) - len(banner)
    padding = "".join([' ' for i  in range(0, paddinglen)])
    banner = banner + padding + "\t%s\t%10s\t%10s\t%10s\t%10s" %("tb(apprx)", "purr", "spurr", "idle_purr", "idle_spurr")
    header = "".join(['=' for i in range(0, len(banner) + 32)])

    print(header)
    print(banner)
    print(header)

########################################################################
#  For a CPU @c, read the value for @file from sysfs
########################################################################    
def read_sysfs(c, file):
    cpu = str(c)
    with open('/sys/devices/system/cpu/cpu'+cpu+'/'+file) as f:
        val = int(f.readline().rstrip('\n'), 16)
    return val

def help():
    print('monitor.py -i <interval seconds> -s <samples count>\n')

########################################################################
# Parse commandline options and update the value of samples and
# interval
########################################################################    
def parse_cmdline():
    samples=10
    interval=1 #seconds
    try:
        options, others = getopt.getopt(
                sys.argv[1:],
                'hi:s:',
                ['interval=',
                 'samples='])
    except getopt.GetoptError as err:
        help()
        sys.exit(1)

    for opt, arg in options:
        if opt in ('-i', '--interval'):
            interval = int(arg)
        elif opt in ('-s', '--samples'):
            samples = int(arg)
        elif opt in ('-h', '--help'):
            help()
            sys.exit(0)
    return interval, samples

#####################################################################
# For each time interval, compute the sum of purr increments for each
# online thread in each active core and print the sum of purr
# increments in comparison with the tb ticks elapsed in that interval.
#
# Expectation:
# sum of purr increments in an active core == elapsed tb-ticks
#####################################################################
def validate():
    for i in range(0, samples):
        old_sec = int(time.time())
        for cpu in online_cpus:
            purr[cpu] = read_sysfs(cpu, 'purr')
            spurr[cpu] = read_sysfs(cpu, 'spurr')
            idle_purr[cpu] = read_sysfs(cpu, 'idle_purr')
            idle_spurr[cpu] = read_sysfs(cpu, 'idle_spurr')

        time.sleep(interval)

        now_sec = int(time.time())
        delta_sec = now_sec - old_sec
        delta_tb = delta_sec * 512000000
        for cpu in online_cpus:
            purr_new[cpu] = read_sysfs(cpu, 'purr')
            spurr_new[cpu] = read_sysfs(cpu, 'spurr')
            idle_purr_new[cpu] = read_sysfs(cpu, 'idle_purr')
            idle_spurr_new[cpu] = read_sysfs(cpu, 'idle_spurr')

        for key,value in cores_list.items():
            purr_total = 0
            spurr_total = 0
            idle_purr_total = 0
            idle_spurr_total = 0
            for cpustr in value:
                cpu = int (cpustr)
                if cpu not in online_cpus:
                    continue
                purr_total += purr_new[cpu] - purr[cpu]
                spurr_total += spurr_new[cpu] - spurr[cpu]
                idle_purr_total += idle_purr_new[cpu] - idle_purr[cpu]
                idle_spurr_total += idle_spurr_new[cpu] - idle_spurr[cpu]
            print("core%02d %s\t%d\t%10d\t%10d\t%10d\t%10d" % (key, stringify(cores_list[key]), delta_tb, purr_total, spurr_total, idle_purr_total, idle_spurr_total))
        print("")


interval,samples=parse_cmdline()
get_online_cpus()
get_core_map()
print_banner()
validate()

sys.exit(0)
