# -*- coding: utf-8 -*-
import re
import os
import shutil
from collections import defaultdict
import logging

class HeaderProcessor:
    def __init__(self, headers_dir, output_dir):
        self.headers_dir = headers_dir
        self.output_dir = output_dir
        self.analyzed_files = set()
        self.dependency_graph = defaultdict(set)
        self.all_protocols = set()
        self.system_frameworks = {'Foundation', 'UIKit', 'CoreGraphics', 'QuartzCore'}
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('header_processing.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 初始化输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def _clean_header_content(self, content):
        """清理头文件内容"""
        # 删除 .cxx_destruct 方法
        content = re.sub(r'\s*-\s*\(void\)\.cxx_destruct\s*;', '', content)
        
        # 替换 CDUnknownBlockType 为 id
        content = content.replace('CDUnknownBlockType', 'id')
        
        # 修改协议声明，处理各种情况
        content = re.sub(r'@protocol\s+(\w+)\s*<[^>]+>', r'@protocol \1', content)

        
        # 删除 NSObject-Protocol.h 的导入
        content = re.sub(r'#import\s+"NSObject-Protocol\.h"', '', content)
        
        # 删除类声明中的协议列表
        content = re.sub(r'(@interface\s+\w+\s*:\s*\w+)\s*<[^>]+>', r'\1', content)
        
        
        # 确保基础框架的引入
        framework_imports = set()
        if 'UIKit' in content:
            framework_imports.add('#import <UIKit/UIKit.h>')
        if 'NS' in content:
            framework_imports.add('#import <Foundation/Foundation.h>')
            
        # 在文件开头添加框架引入
        if framework_imports:
            content = '\n'.join(sorted(framework_imports)) + '\n\n' + content
            
        return content

    def _process_imports(self, content):
        """处理导入语句"""
        imports = set()
        
        # 处理 #import 语句
        import_pattern = r'#import\s+[<"](.+?)[>"]'
        for match in re.finditer(import_pattern, content):
            import_path = match.group(1)
            if not any(fw in import_path for fw in self.system_frameworks):
                imports.add(import_path)
                
        # 处理 @class 声明
        class_pattern = r'@class\s+([^;]+);'
        for match in re.finditer(class_pattern, content):
            classes = [c.strip() for c in match.group(1).split(',')]
            for class_name in classes:
                header_file = f"{class_name}.h"
                if os.path.exists(os.path.join(self.headers_dir, header_file)):
                    imports.add(header_file)
                    
        return imports

    def _find_protocol_dependencies(self, content):
        """查找协议依赖"""
        protocol_pattern = r'@protocol\s+(\w+)|<(\w+)[^>]*>'
        protocols = set()
        
        for match in re.finditer(protocol_pattern, content):
            protocol_name = match.group(1) or match.group(2)
            if protocol_name != 'NSObject':
                protocols.add(protocol_name)
                # 检查协议头文件
                protocol_files = [
                    f"{protocol_name}-Protocol.h",
                    f"{protocol_name}Protocol.h",
                    f"{protocol_name}.h"
                ]
                for protocol_file in protocol_files:
                    if os.path.exists(os.path.join(self.headers_dir, protocol_file)):
                        self.dependency_graph[protocol_file].add(protocol_file)
                        break
                        
        return protocols

    def process_header(self, header_path):
        """处理单个头文件"""
        if header_path in self.analyzed_files:
            return
            
        self.analyzed_files.add(header_path)
        full_path = os.path.join(self.headers_dir, header_path)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 处理内容
            content = self._clean_header_content(content)
            
            # 分析依赖
            imports = self._process_imports(content)
            protocols = self._find_protocol_dependencies(content)
            
            # 更新依赖图
            self.dependency_graph[header_path].update(imports)
            self.all_protocols.update(protocols)
            
            # 保存处理后的文件
            output_path = os.path.join(self.output_dir, header_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            # 递归处理依赖
            for dep in imports:
                self.process_header(dep)
                
        except Exception as e:
            self.logger.error(f"Error processing {header_path}: {str(e)}")

    def process_all_dependencies(self, start_header):
        """处理所有依赖"""
        self.logger.info(f"Starting to process {start_header}")
        self.process_header(start_header)
        
        # 打印处理摘要
        self.print_summary()

    def print_summary(self):
        """打印处理摘要"""
        self.logger.info("\n=== Processing Summary ===")
        self.logger.info(f"Total files processed: {len(self.analyzed_files)}")
        self.logger.info(f"Total protocols found: {len(self.all_protocols)}")
        
        self.logger.info("\nProcessed files:")
        for file in sorted(self.analyzed_files):
            self.logger.info(f"  - {file}")
            deps = self.dependency_graph[file]
            if deps:
                for dep in sorted(deps):
                    self.logger.info(f"    └─ {dep}")

def main():
    # 配置参数
    headers_dir = ""
    target_header = ""
    output_dir = ""
    
    try:
        processor = HeaderProcessor(headers_dir, output_dir)
        processor.process_all_dependencies(target_header)
        
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    main()