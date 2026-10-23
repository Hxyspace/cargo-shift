# Cargo Shift

<p align="center">
  <img src="assets/metadata/cargo_shift.png" width="232" height="320" alt="Cargo Shift cover art">
</p>

Cargo Shift 是一款面向 NES/Famicom 的单人推箱子游戏，包含 18 个原创关卡。项目使用 C 与 6502 汇编编写，通过 cc65 构建为 Mapper 0（NROM-256）ROM。

[关卡设计](docs/LEVELS.md) · [MIT License](LICENSE)

## 构建

需要 GNU Make、POSIX shell，以及包含 NES 目标和运行库的完整 [cc65](https://cc65.github.io/) 工具链：

```sh
make
```

ROM 输出到 `build/cargo_shift.nes`。如果 `cl65` 不在 `PATH` 中，可以指定其位置：

```sh
make CL65=/absolute/path/to/cc65/bin/cl65
```

也可以下载并在项目内构建经过验证的 cc65 版本：

```sh
make bootstrap
make
```

`make bootstrap` 需要 Git、网络和系统 C 编译器，工具链会保存在被 Git 忽略的 `.tools/cc65/`。普通构建不需要 Python 或网络。

> [!NOTE]
> 请保留 Makefile 中禁用 `OptDupLoads` 的参数；固定版本 cc65 在启用该优化时会错误编译游戏逻辑。

## 开发

| 命令 | 用途 |
| --- | --- |
| `make verify` | 运行规则测试、ROM 格式和内存预算检查 |
| `make test` | 只运行主机端游戏逻辑测试 |
| `make assets` | 从 PNG 和关卡 JSON 重新生成运行时资源 |
| `make solve` | 重新求解关卡并更新测试解答 |
| `make clean` | 删除构建产物 |

修改图片或关卡时需要 Python 3 和 Pillow：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
make assets PYTHON=.venv/bin/python
make solve PYTHON=.venv/bin/python
make verify PYTHON=.venv/bin/python
```

可编辑资源位于 `assets/cargo_shift/`，生成结果位于 `assets/generated/`。生成结果已提交到仓库，因此正常构建不需要 Pillow。地图格式、生成方式和难度数据见 [docs/LEVELS.md](docs/LEVELS.md)。

## 技术规格

| 项目 | 配置 |
| --- | --- |
| 制式 | NTSC；PAL 尚未验证 |
| Mapper | 0 / NROM-256 |
| ROM | 32 KiB PRG + 8 KiB CHR |
| RAM | 仅使用主机内部 RAM |
| 存档 | 无 |

固定 cc65 revision `555282497c3ecf8b313d87d5973093af19c35bd5` 构建出的 ROM SHA-256：

```text
d1a6deb7528d5349b69b02fe918fba8fa9e7fdfbd5d8be455d6b9d173d7545ef
```

## 许可证

本项目以 [MIT License](LICENSE) 发布。
