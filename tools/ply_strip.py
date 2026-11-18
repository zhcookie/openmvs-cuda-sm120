#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ply_strip.py —— 剥离 OpenMVS PLY 输出里的可变长 `property list` 字段

为什么需要它
------------
OpenMVS 的稠密点云 PLY 每个点后面跟两个可变长列表（该点被哪些相机看到 + 对应权重）：

    property list ... view_indices
    property list ... view_weights

CloudCompare 的 PLY 解析器不支持可变长属性，打开直接报 `nothing to load`。
本脚本只保留 x,y,z (float32) + red,green,blue (uint8) + nx,ny,nz (float32)，
共 27 字节/点，文件体积约降到原来的 43%，CloudCompare 正常加载。

用法
----
    python ply_strip.py scene_dense.ply scene_dense_clean.ply

输入必须是 OpenMVS 输出的 binary_little_endian PLY。脚本按 **4 字节/项** 跳读
两个列表（OpenMVS 2.3.0 的实际导出格式即如此）；若你的版本元素宽度不同，
只需改下面两行 `pos += 1 + c * 4` 里的倍数。
"""

import struct
import sys


def strip_lists(src_path, dst_path):
    f = open(src_path, 'rb')
    n = 0
    while True:
        line = f.readline()
        s = line.strip()
        if s.startswith(b'element vertex'):
            n = int(s.split()[-1])
        if s == b'end_header':
            break

    out = open(dst_path, 'wb')
    out.write(b'ply\nformat binary_little_endian 1.0\n')
    out.write(('element vertex %d\n' % n).encode())
    for prop in [b'x', b'y', b'z']:
        out.write(b'property float32 ' + prop + b'\n')
    for prop in [b'red', b'green', b'blue']:
        out.write(b'property uint8 ' + prop + b'\n')
    for prop in [b'nx', b'ny', b'nz']:
        out.write(b'property float32 ' + prop + b'\n')
    out.write(b'end_header\n')

    data = f.read()
    f.close()
    pos = 0
    chunk = []
    CHUNK = 200000
    for i in range(n):
        chunk.append(data[pos:pos + 27])
        pos += 27
        c = data[pos]
        pos += 1 + c * 4        # view_indices: 1 字节计数 + c 项
        c = data[pos]
        pos += 1 + c * 4        # view_weights: 1 字节计数 + c 项
        if len(chunk) >= CHUNK:
            out.write(b''.join(chunk))
            chunk = []
    out.write(b''.join(chunk))
    out.close()
    return n


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('usage: python ply_strip.py <input.ply> <output.ply>')
        sys.exit(2)
    count = strip_lists(sys.argv[1], sys.argv[2])
    print('done: %d vertices (%d bytes/vertex)' % (count, 27))
