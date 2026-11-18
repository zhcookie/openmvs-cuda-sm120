# logs/ —— 真实日志留档

这些是这台机器上编译与首次运行时**原样保存**的日志，用于对照排查、也用于证明 `bin/` 的来源。个人路径已脱敏（`C:\Users\zhc` → `C:\Users\<user>`），其余未改。

| 文件 | 是什么 | 关键行 |
|---|---|---|
| `vcpkg_openmvs.log` | vcpkg 编译安装 openmvs 的完整输出 | `-- Found CUDA V13.1.80`、`openmvs[...]:x64-windows-sm120@2.3.0#1`、`All requested installations completed successfully in: 6.8 min` |
| `DensifyPointCloud-261001041708000CB9.log` | `DensifyPointCloud.exe` 首次冒烟运行自写的日志（文件名里的时间戳由程序生成） | `OpenMVS x64 v2.3.0`、`Build date: Oct  1 2026, 04:01:14`、`SSE & AVX compatible CPU & OS detected` |

日志文件名的构成：`<工具名>-<YYMMDDHHMMSS><随机后缀>.log`，由 OpenMVS 自己在工作目录生成，不是本仓库命名的。

## 怎么用

- 你编出来的东西报 `named symbol not found` → 对照 `vcpkg_openmvs.log` 里有没有 `-- Found CUDA` 和三元组后缀 `:x64-windows-sm120`。若后缀只写了 `:x64-windows`，说明三元组没用上，编出来还是默认架构。
- 你的 exe 起不来 → 看 `DensifyPointCloud-*.log` 的头部，确认它打印的版本与 build date 是不是你以为的那份。
