#
# Copyright (c) 2013-2015 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from django.utils.translation import ugettext_lazy as _


PLATFORM_CPU_TYPE = "Platform"
VSWITCH_CPU_TYPE = "Vswitch"
SHARED_CPU_TYPE = "Shared"
VMS_CPU_TYPE = "VMs"
NONE_CPU_TYPE = "None"

CPU_TYPE_LIST = [PLATFORM_CPU_TYPE, VSWITCH_CPU_TYPE,
                 SHARED_CPU_TYPE, VMS_CPU_TYPE,
                 NONE_CPU_TYPE]


PLATFORM_CPU_TYPE_FORMAT = _("Platform")
VSWITCH_CPU_TYPE_FORMAT = _("vSwitch")
SHARED_CPU_TYPE_FORMAT = _("Shared")
VMS_CPU_TYPE_FORMAT = _("VMs")
NONE_CPU_TYPE_FORMAT = _("None")

CPU_TYPE_FORMATS = {PLATFORM_CPU_TYPE: PLATFORM_CPU_TYPE_FORMAT,
                    VSWITCH_CPU_TYPE: VSWITCH_CPU_TYPE_FORMAT,
                    SHARED_CPU_TYPE: SHARED_CPU_TYPE_FORMAT,
                    VMS_CPU_TYPE: VMS_CPU_TYPE_FORMAT,
                    NONE_CPU_TYPE: NONE_CPU_TYPE_FORMAT}


class CpuFunction(object):
    def __init__(self, function):
        self.allocated_function = function
        self.socket_cores = {}
        self.socket_cores_number = {}


class CpuProfile(object):
    class CpuConfigure(object):
        def __init__(self):
            self.platform = 0
            self.vswitch = 0
            self.shared = 0
            self.vms = 0
            self.numa_node = 0

    # cpus is a list of icpu sorted by numa_node, core and thread
    # if not sorted, provide nodes list so it can be sorted here
    def __init__(self, cpus, nodes=None):
        if nodes:
            cpus = CpuProfile.sort_cpu_by_numa_node(cpus, nodes)

        cores = []

        self.number_of_cpu = 0
        self.cores_per_cpu = 0
        self.hyper_thread = False
        self.processors = []
        cur_processor = None

        for cpu in cpus:
            key = '{0}-{1}'.format(cpu.numa_node, cpu.core)
            if key not in cores:
                cores.append(key)
            else:
                self.hyper_thread = True
                continue

            if cur_processor is None \
                    or cur_processor.numa_node != cpu.numa_node:
                cur_processor = CpuProfile.CpuConfigure()
                cur_processor.numa_node = cpu.numa_node
                self.processors.append(cur_processor)

            if cpu.allocated_function == PLATFORM_CPU_TYPE:
                cur_processor.platform += 1
            elif cpu.allocated_function == VSWITCH_CPU_TYPE:
                cur_processor.vswitch += 1
            elif cpu.allocated_function == SHARED_CPU_TYPE:
                cur_processor.shared += 1
            elif cpu.allocated_function == VMS_CPU_TYPE:
                cur_processor.vms += 1

        self.cores_per_cpu = len(cores)
        self.number_of_cpu = len(self.processors)

    @staticmethod
    def sort_cpu_by_numa_node(cpus, nodes):
        newlist = []
        for node in nodes:
            for cpu in cpus:
                if cpu.numa_node == node.numa_node:
                    newlist.append(cpu)
        return newlist


class HostCpuProfile(CpuProfile):
    def __init__(self, personality, cpus, nodes=None):
        super(HostCpuProfile, self).__init__(cpus, nodes)
        self.personality = personality

    # see if a cpu profile is applicable to this host
    def profile_applicable(self, profile):
        if self.number_of_cpu == profile.number_of_cpu and \
                self.cores_per_cpu == profile.cores_per_cpu:
            return self.check_profile_core_functions(profile)
        else:
            return False

        return not True

    def check_profile_core_functions(self, profile):
        platform_cores = 0
        vswitch_cores = 0
        shared_cores = 0
        vm_cores = 0
        for cpu in profile.processors:
            platform_cores += cpu.platform
            vswitch_cores += cpu.vswitch
            shared_cores += cpu.shared
            vm_cores += cpu.vms

        result = True
        if platform_cores == 0:
            result = False
        elif 'compute' in self.personality and vswitch_cores == 0:
            result = False
        elif 'compute' in self.personality and vm_cores == 0:
            result = False
        return result


def compress_range(c_list):
    c_list.append(999)
    c_list.sort()
    c_sep = ""
    c_item = ""
    c_str = ""
    pn = 0
    for n in c_list:
        if not c_item:
            c_item = "%s" % n
        else:
            if n > (pn + 1):
                if int(pn) == int(c_item):
                    c_str = "%s%s%s" % (c_str, c_sep, c_item)
                else:
                    c_str = "%s%s%s-%s" % (c_str, c_sep, c_item, pn)
                c_sep = ","
                c_item = "%s" % n
        pn = n
    return c_str


def restructure_host_cpu_data(host):
    host.core_assignment = []
    if host.cpus:
        host.cpu_model = host.cpus[0].cpu_model
        host.sockets = len(host.nodes)
        host.hyperthreading = "No"
        host.physical_cores = {}

        core_assignment = {}
        number_of_cores = {}

        for cpu in host.cpus:
            if cpu.numa_node not in host.physical_cores:
                host.physical_cores[cpu.numa_node] = 0
            if cpu.thread == 0:
                host.physical_cores[cpu.numa_node] += 1
            elif cpu.thread > 0:
                host.hyperthreading = "Yes"

            if cpu.allocated_function is None:
                cpu.allocated_function = NONE_CPU_TYPE

            if cpu.allocated_function not in core_assignment:
                core_assignment[cpu.allocated_function] = {}
                number_of_cores[cpu.allocated_function] = {}
            if cpu.numa_node not in core_assignment[cpu.allocated_function]:
                core_assignment[cpu.allocated_function][cpu.numa_node] = [
                    int(cpu.cpu)]
                number_of_cores[cpu.allocated_function][cpu.numa_node] = 1
            else:
                core_assignment[cpu.allocated_function][cpu.numa_node].append(
                    int(cpu.cpu))
                number_of_cores[cpu.allocated_function][cpu.numa_node] += 1

        for f in CPU_TYPE_LIST:
            cpufunction = CpuFunction(f)
            if f in core_assignment:
                host.core_assignment.append(cpufunction)
                for s, cores in core_assignment[f].items():
                    cpufunction.socket_cores[s] = compress_range(cores)
                    cpufunction.socket_cores_number[s] = number_of_cores[f][s]
            else:
                if (f == PLATFORM_CPU_TYPE or
                    (hasattr(host, 'subfunctions') and
                     'compute' in host.subfunctions)):
                    if f != NONE_CPU_TYPE:
                        host.core_assignment.append(cpufunction)
                        for s in range(0, len(host.nodes)):
                            cpufunction.socket_cores[s] = ""
                            cpufunction.socket_cores_number[s] = 0


def check_core_functions(personality, icpus):
    platform_cores = 0
    vswitch_cores = 0
    shared_vcpu_cores = 0
    vm_cores = 0
    for cpu in icpus:
        allocated_function = cpu.allocated_function
        if allocated_function == PLATFORM_CPU_TYPE:
            platform_cores += 1
        elif allocated_function == VSWITCH_CPU_TYPE:
            vswitch_cores += 1
        elif allocated_function == SHARED_CPU_TYPE:
            shared_vcpu_cores += 1
        elif allocated_function == VMS_CPU_TYPE:
            vm_cores += 1

    # No limiations for shared_vcpu cores
    error_string = ""
    if platform_cores == 0:
        error_string = "There must be at least one" \
                       " core for %s." % PLATFORM_CPU_TYPE_FORMAT
    elif 'compute' in personality and vswitch_cores == 0:
        error_string = "There must be at least one" \
                       " core for %s." % VSWITCH_CPU_TYPE_FORMAT
    elif 'compute' in personality and vm_cores == 0:
        error_string = "There must be at least one" \
                       " core for %s." % VMS_CPU_TYPE_FORMAT
    return error_string
