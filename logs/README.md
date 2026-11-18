# logs/ 目录说明

本目录保存本机编译与首次运行产生的原始日志，用于对照排错，并作为 `bin/` 目录来源的记录。个人路径已脱敏处理，`C:\Users\zhc` 替换为 `C:\Users\<user>`，其余内容未作修改。

| 文件 | 内容 | 关键记录 |
|---|---|---|
| `vcpkg_openmvs.log` | vcpkg 编译安装 openmvs 的完整输出 | `-- Found CUDA V13.1.80`；`openmvs[...]:x64-windows-sm120@2.3.0#1`；`All requested installations completed successfully in: 6.8 min` |
| `DensifyPointCloud-261001041708000CB9.log` | `DensifyPointCloud.exe` 首次运行自动生成的日志 | `OpenMVS x64 v2.3.0`；`Build date: Oct  1 2026, 04:01:14`；`SSE & AVX compatible CPU & OS detected` |

日志文件名格式为 `<工具名>-<YYMMDDHHMMSS><随机后缀>.log`，由 OpenMVS 在工作目录自动生成，命名规则来自程序本身。

## 使用方式

- 自建二进制报 `named symbol not found` 时，核对 `vcpkg_openmvs.log` 中是否存在 `-- Found CUDA` 记录，以及安装包的架构后缀是否为 `:x64-windows-sm120`。后缀为 `:x64-windows` 表示三元组未生效，产物仍为默认架构。
- 需确认某个可执行文件的版本时，查看其运行目录下生成的 `DensifyPointCloud-*.log` 头部，其中记录版本号与构建日期。
