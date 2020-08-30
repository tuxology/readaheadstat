#!/usr/bin/python3
# @lint-avoid-python-3-compatibility-imports
#
# readaheadstat     Count unused pages in read ahead cache with age
#                   For Linux, uses bpftrace, eBPF
#
# Copyright (c) 2020 Suchakra Sharma <suchakra@gmail.com>
# Licensed under the Apache License, Version 2.0 (the "License")
#
# 20-Aug-2020   Suchakra Sharma   Created this.

from __future__ import print_function
from bcc import BPF
import bcc
from time import sleep
from influxdb import InfluxDBClient
import ctypes as ct

program = """
#include <uapi/linux/ptrace.h>
#include <linux/mm_types.h>

BPF_HASH(flag, u32, u8); // used to track if we are in do_page_cache_readahead()
BPF_HASH(birth, struct page*, u64); // used to track timestamps of cache alloc'ed page
BPF_ARRAY(pages); // increment/decrement readahead pages
BPF_HISTOGRAM(dist);

int entry__do_page_cache_readahead(struct pt_regs *ctx) {
    u32 pid;
    u8 one = 1;
    pid = bpf_get_current_pid_tgid();
    flag.update(&pid, &one);
    return 0;
}

int exit__do_page_cache_readahead(struct pt_regs *ctx) {
    u32 pid;
    u8 zero = 0;
    pid = bpf_get_current_pid_tgid();
    flag.update(&pid, &zero);
    return 0;
}

int exit__page_cache_alloc(struct pt_regs *ctx) {
    u32 pid;
    u64 ts;
    struct page *retval = (struct page*) PT_REGS_RC(ctx);
    u32 zero = 0; // static key for accessing pages[0]
    pid = bpf_get_current_pid_tgid();
    u8 *f = flag.lookup(&pid);
    if (f != NULL && *f == 1) {
        ts = bpf_ktime_get_ns();
        birth.update(&retval, &ts);

        u64 *count = pages.lookup(&zero);
        if (count) (*count)++; // increment read ahead pages count
    }
    return 0;
}

int entry_mark_page_accessed(struct pt_regs *ctx) {
    u64 ts, delta;
    struct page *arg0 = (struct page *) PT_REGS_PARM1(ctx);
    u32 zero = 0; // static key for accessing pages[0]
    u64 *bts = birth.lookup(&arg0);
    if (bts != NULL) {
        delta = bpf_ktime_get_ns() - *bts;
        dist.increment(bpf_log2l(delta/1000000));

        u64 *count = pages.lookup(&zero);
        if (count) (*count)--; // decrement read ahead pages count

        birth.delete(&arg0); // remove the entry from hashmap
    }
    return 0;
}
"""
do_exit = 0
b = BPF(text=program)
b.attach_kprobe(event="__do_page_cache_readahead", fn_name="entry__do_page_cache_readahead")
b.attach_kretprobe(event="__do_page_cache_readahead", fn_name="exit__do_page_cache_readahead")
b.attach_kretprobe(event="__page_cache_alloc", fn_name="exit__page_cache_alloc")
b.attach_kprobe(event="mark_page_accessed", fn_name="entry_mark_page_accessed")

dbClient = InfluxDBClient('localhost', 8086, 'root', 'root', 'ReadAHead')

# Write the time series data points into database - user login details
dbClient.create_database('ReadAHead')

while (1):    
    try:
	    sleep(5)
    except KeyboardInterrupt:
	    pass; do_exit = 1
    usedPage = 0
    for k, v in b["dist"].items():
        usedPage = usedPage + v.value
        logEvents= [{"measurement":"eBPF",
         "fields":
         {
         "{category}".format(category = k.value):v.value,
         }
         }
         ]

        dbClient.write_points(logEvents)
        #print(logEvents)
    b["dist"].print_log2_hist("usecs")
    logEvents= [{"measurement":"eBPF",
          "fields":
          {
          "unused":b["pages"][ct.c_ulong(0)].value,
          "used":usedPage
          }
          }
          ]
    dbClient.write_points(logEvents)
    if do_exit:
        exit()
