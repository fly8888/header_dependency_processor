# 头文件依赖处理器

## 项目简介
这是一个用于处理和优化 Objective-C 头文件依赖关系的 Python 工具。它可以分析头文件之间的依赖关系，清理头文件内容，并生成优化后的头文件。

## 主要功能
- 分析头文件间的依赖关系
- 清理和优化头文件内容
- 处理框架导入和协议依赖
- 生成依赖关系图
- 提供详细的处理日志

## 使用方法
1. 配置参数：
   ```python
   headers_dir = "原始头文件目录路径"
   target_header = "需要处理的目标头文件"
   output_dir = "输出目录路径"
   ```

2. 运行程序：
   ```bash
   python header_dependency_processor.py
   ```

## 功能特性
- 自动清理 .cxx_destruct 方法
- 替换 CDUnknownBlockType 为 id
- 优化协议声明
- 处理系统框架导入
- 分析并处理 @class 声明
- 递归处理所有依赖关系

## 日志输出
程序会生成详细的处理日志，包含：
- 处理的文件总数
- 发现的协议总数
- 每个文件的依赖关系树

## 系统要求
- Python 3.x
- 操作系统：跨平台支持

## 注意事项
- 请确保输入路径中包含所有需要处理的头文件
- 建议在处理前备份原始文件 