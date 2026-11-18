#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ply_strip.py — 剥离 OpenMVS 输出 PLY 中的可变长属性

用途
----
OpenMVS 输出的稠密点云 PLY 为每个顶点附加两个可变长属性，分别记录该点被哪些
视图观测及对应权重：

    property list ... view_indices
    property list ... view_weights

CloudCompare 的 PLY 解析器不支持可变长属性，加载时报告 `nothing to load`。
本工具仅保留 x, y, z（float32）、red, green, blue（uint8）与 nx, ny, nz（float32），
固定为 27 字节/顶点，输出体积约为原始文件的 43%，可被 CloudCompare 正常加载。

调用方式
--------
    python ply_strip.py scene_dense.ply scene_dense_clean.ply

输入须为 OpenMVS 输出的 binary_little_endian 格式 PLY。脚本按 4 字节/项跳读两个
可变长属性（OpenMVS 2.3.0 的导出格式即为此）；若目标版本的元素宽度不同，调整下方
两处 `pos += 1 + c * 4` 中的乘数即可。
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
        pos += 1 + c * 4        # view_indices：1 字节计数 + c 项
        c = data[pos]
        pos += 1 + c * 4        # view_weights：1 字节计数 + c 项
        if len(chunk) >= CHUNK:
            out.write(b''.join(chunk))
            chunk = []
    out.write(b''.join(chunk))
    out.close()
    return n


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('用法：python ply_strip.py <输入.ply> <输出.ply>')
        sys.exit(2)
    count = strip_lists(sys.argv[1], sys.argv[2])
    print('完成：%d 个顶点，27 字节/顶点' % count)
