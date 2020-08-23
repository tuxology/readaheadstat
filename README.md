# Read Ahead Cache Stats

This tool shows the performance of the read ahead mechanism in your FS, specifically
higlighting ununsed pages in the cache and how long they have remained there. Cache 
misses in read-ahead cache reduces the performance of a FS call and can be an important
metric in understanding how moden architectures affect such metrics in the system.

## `readaheadstat.bt`

This tool requires [`bpftrace`](https://github.com/iovisor/bpftrace) to be installed on the system

```
$ sudo ./readaheadstat.bt

Attaching 5 probes...
^C
Readahead unused pages: 15816

Readahead used page age (ms):
@age_ms:
[0]                 2216 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                     |
[1]                   74 |@                                                   |
[2, 4)               152 |@@                                                  |
[4, 8)               553 |@@@@@@@                                             |
[8, 16)              116 |@                                                   |
[16, 32)              81 |@                                                   |
[32, 64)              79 |@                                                   |
[64, 128)             88 |@                                                   |
[128, 256)           601 |@@@@@@@@                                            |
[256, 512)           157 |@@                                                  |
[512, 1K)            107 |@                                                   |
[1K, 2K)             136 |@                                                   |
[2K, 4K)            3689 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|
[4K, 8K)              82 |@                                                   |
[8K, 16K)           1170 |@@@@@@@@@@@@@@@@                                    |
```

## `readaheadstat.py`

This tool requires [BCC](https://github.com/iovisor/bcc) to be installed on your system

```
$ sudo ./readaheadstat.py

Tracing... Hit Ctrl-C to end.
^C
Read-ahead unused pages: 3630
Histogram of read-ahead used page age (ms)
==========================================
     ms                  : count     distribution
         0 -> 1          : 136      |*****************                       |
         2 -> 3          : 0        |                                        |
         4 -> 7          : 0        |                                        |
         8 -> 15         : 1        |                                        |
        16 -> 31         : 0        |                                        |
        32 -> 63         : 0        |                                        |
        64 -> 127        : 0        |                                        |
       128 -> 255        : 0        |                                        |
       256 -> 511        : 43       |*****                                   |
       512 -> 1023       : 0        |                                        |
      1024 -> 2047       : 312      |****************************************|
```

