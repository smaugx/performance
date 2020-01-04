#!/usr/bin/env python
# -*- coding:utf8 -*-

import time
import sys
import copy

class CpuWatch(object):
    def __init__(self, time_step):
        self.cpufile_ = '/proc/stat'
        self.watch_time_step_ = time_step  # 60 s
        return

    # 采集cpu信息
    '''
    /proc/pid/stat 第14、15、16、17列对应进程用户态消耗(user)、内核态消耗(sys)、用户态等待子进程的消耗(user_child)、内核态等待子进程的消耗(sys_child)
    utime=1587 该任务在用户态运行的时间，单位为jiffies
    stime=1 该任务在核心态运行的时间，单位为jiffies
    cutime=0 累计的该任务的所有的waited-for进程曾经在用户态运行的时间，单位为jiffies
    cstime=0 累计的该任务的所有的waited-for进程曾经在核心态运行的时间，单位为jiffies

    pid_cpu_usage = (t2_pid - t1_pid) / (t2_all - t1_all)
    '''
    def read_cpu(self, pid=None):
        cpu_info = {}
        cpufile = self.cpufile_
        pid_cpufile = None
        if pid:
            pid_cpufile = '/proc/{0}/stat'.format(pid)

        with open(cpufile, 'r') as fin:
            for line in fin:
                line_fields = line.split()
                if line_fields[0] != "cpu":
                    continue
                total = 0
                for field in line_fields:
                    if field == "cpu":
                        continue
                    total += int(field)
    
                cpu_info = {
                    "User": int(line_fields[1]),
                    "Sys": int(line_fields[3]),
                    "Idle": int(line_fields[4]),
                    "Steal": int(line_fields[8]),
                    "Wait": int(line_fields[5]),
                    "Total": total
                }
            fin.close()

        if pid != None:
            with open(pid_cpufile, 'r') as fin:
                pid_cpu = 0
                for line in fin:
                    line_fields = line.split()
                    pid_cpu += int(line_fields[13])
                    pid_cpu += int(line_fields[14])
                    pid_cpu += int(line_fields[15])
                    pid_cpu += int(line_fields[16])
                    break
                cpu_info['Pid'] = pid_cpu
                fin.close()

        return cpu_info

    def get_avg_cpu(self, cpu_info_old, cpu_info):
        if not cpu_info_old or not cpu_info:
            return None

        result = {}
        if set(cpu_info.keys()) != set(cpu_info_old.keys()):
            return None

        delta_total = cpu_info["Total"]  -   cpu_info_old["Total"]
        delta_user  = cpu_info["User"]   -   cpu_info_old["User"]
        delta_sys   = cpu_info["Sys"]    -   cpu_info_old["Sys"]
        delta_idle  = cpu_info["Idle"]   -   cpu_info_old["Idle"]
        delta_wait  = cpu_info["Wait"]   -   cpu_info_old["Wait"]
        delta_steal = cpu_info["Steal"]  -   cpu_info_old["Steal"]
        
        if cpu_info.get('Pid') and cpu_info_old.get('Pid'):
            delta_pid_cpu = cpu_info['Pid'] - cpu_info_old['Pid']

        result = {
            "cpu_user": int(float(delta_user)/float(delta_total) * 100),
            "cpu_sys": int(float(delta_sys)/float(delta_total) * 100),
            "cpu_wait": int(float(delta_wait)/float(delta_total) * 100),
            "cpu_steal": int(float(delta_steal)/float(delta_total) * 100),
            "cpu_idle": int(float(delta_idle)/float(delta_total) * 100),
            "cpu_util": int(float(delta_total - delta_idle - delta_wait - delta_steal)/float(delta_total) * 100),
            "cpu_pid": int(float(delta_pid_cpu)/float(delta_total) * 100)
            }
        print(result)
        return result

    def run(self, pid=None):
        cpu_info_old = {}
        while True:
            if not cpu_info_old:
                cpu_info_old = self.read_cpu(pid=pid)
            time.sleep(self.watch_time_step_)
            cpu_info = self.read_cpu(pid=pid)

            result = self.get_avg_cpu(cpu_info_old, cpu_info)
            print(result)
            cpu_info_old = copy.deepcopy(cpu_info)

if __name__ == '__main__':
    pid = None
    if len(sys.argv) == 2:
        pid = int(sys.argv[1])

    cpu_watcher = CpuWatch(time_step = 5)
    cpu_watcher.run(pid = pid)


