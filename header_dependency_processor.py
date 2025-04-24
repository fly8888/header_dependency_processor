# -*- coding: utf-8 -*-
import re
import os
import shutil
from collections import defaultdict
import logging
import sys

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
        # 添加系统结构体列表
        system_structs = {
            # 基础图形相关
            'CGPoint', '_CGPoint', 'CGSize', '_CGSize', 'CGRect', '_CGRect',
            'CGAffineTransform', '_CGAffineTransform', 'CGVector', '_CGVector',
            
            # Foundation 相关
            'NSRange', '_NSRange', 'NSDirectionalEdgeInsets', '_NSDirectionalEdgeInsets',
            
            # UIKit 相关
            'UIEdgeInsets', '_UIEdgeInsets', 'UIOffset', '_UIOffset',
            'UIRectEdge', '_UIRectEdge', 'UIFloatRange', '_UIFloatRange',
            
            # 文本相关
            'CGGlyph', '_CGGlyph', 'CGFont', '_CGFont',
            
            # CoreVideo 相关
            'CVBuffer', '_CVBuffer', 'CVImageBuffer', '_CVImageBuffer',
            'CVPixelBuffer', '_CVPixelBuffer', 'CVTime', '_CVTime',
            'CVTimeStamp', '_CVTimeStamp', '__CVBuffer',
            
            # 其他常见系统结构体
            'dispatch_time_t', 'dispatch_queue_t', 'dispatch_group_t',
            'CFRange', '_CFRange', 'CFRunLoopRef', '_CFRunLoopRef',
            'CMTime', '_CMTime', 'CMTimeRange', '_CMTimeRange',
            'CLLocationCoordinate2D', '_CLLocationCoordinate2D',
            'CATransform3D', '_CATransform3D'
        }
        
        # 删除 .cxx_destruct 方法
        content = re.sub(r'\s*-\s*\(void\)\.cxx_destruct\s*;', '', content)
        
        # 替换 CDUnknownBlockType 为 id
        content = content.replace('CDUnknownBlockType', 'id')
        
        content = content.replace('#import <ProtobufLite/WXPBGeneratedMessage.h>', '#import "WXPBGeneratedMessage.h"')
        
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
            
        # 处理结构体声明（在成员变量和属性中）
        content = re.sub(
            r'struct\s+(_?\w+)\s+(\w+);',
            lambda m: f'id {m.group(1)} /*  struct {m.group(2)}  */;'
            if m.group(1) not in system_structs else m.group(0),
            content
        )
        
        # 处理方法参数中的结构体
        content = re.sub(
            r':\s*\((struct\s+_?\w+\s*\*?)\)',
            lambda m: f': (id /*  {m.group(1)}  */)'
            if not any(s in m.group(1) for s in system_structs) else m.group(0),
            content
        )
        
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
        
        output_path = os.path.join(self.output_dir, header_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        if os.path.exists(output_path):
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

    def process_wx_header(self, wx_header_path):
        """从WXHeader.h处理所有导入的头文件"""
        self.logger.info(f"Processing Header.h from: {wx_header_path}")
        
        if not os.path.exists(wx_header_path):
            self.logger.error(f"Header.h not found at {wx_header_path}")
            return

        try:

            with open(wx_header_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取所有导入语句
            import_pattern = r'#import\s+"([^"]+)"'
            headers_to_process = re.findall(import_pattern, content)
            
            self.logger.info(f"Found {len(headers_to_process)} headers to process")
            
            # 处理每个头文件
            for header in headers_to_process:
                if not os.path.exists(os.path.join(self.output_dir, header)):
                    self.logger.info(f"Processing: {header}")
                    self.process_all_dependencies(header)
                else:
                    self.logger.info(f"Skipping existing header: {header}")
                    
        except Exception as e:
            self.logger.error(f"Error processing WXHeader.h: {str(e)}")
            raise

def main():
    args = sys.argv[1:]
    # 配置参数
    source_headers_dir = args[0] #原始头文件文件夹
    output_dir = args[1]         #目的文件夹
    wx_header_path = args[2]     #自己的头文件
    
    try:
        processor = HeaderProcessor(source_headers_dir, output_dir)
        processor.process_wx_header(wx_header_path)
        
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    main()
