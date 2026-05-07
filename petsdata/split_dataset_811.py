"""
数据集分割脚本

【模块职责】
将原始数据集按照 8:1:1 的比例分割为训练集、验证集和测试集，
并支持 XML 标注格式到 YOLO 格式的转换。

【功能概览】
1. 数据集分割：将图片和标注文件按比例分配到 train/val/test 目录
2. 格式转换：将 PASCAL VOC XML 格式转换为 YOLO TXT 格式
3. 目录结构初始化：创建标准 YOLO 数据集目录结构

【数据集目录结构】
输入（原始数据）：
petsdata/
├── images/           # 原始图片目录
│   ├── cat_001.jpg
│   └── ...
└── annotations/
    └── xmls/         # XML 标注文件（可选）

输出（分割后）：
petsdata/
├── images/
│   ├── train/        # 训练集图片
│   ├── val/          # 验证集图片
│   └── test/         # 测试集图片
└── labels/
    ├── train/        # 训练集标注
    ├── val/          # 验证集标注
    └── test/         # 测试集标注

【YOLO 标注格式】
每行一个目标，格式为：
<class_id> <x_center> <y_center> <width> <height>

- class_id: 类别索引（从 0 开始）
- x_center, y_center: 目标中心点坐标（归一化到 0-1）
- width, height: 目标宽高（归一化到 0-1）

【使用方式】
python split_dataset_811.py --src "petsdata/images" --seed 42
python split_dataset_811.py --src "petsdata/images" --convert-xml --xml-dir "petsdata/annotations/xmls"
"""

import os
import random
import shutil
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
from tqdm import tqdm


# =============================================================================
# 配置常量
# =============================================================================
# 默认分割比例：8:1:1
# TRAIN_RATIO: 训练集占比 80%
# VAL_RATIO: 验证集占比 10%
# TEST_RATIO: 测试集占比 10%
TRAIN_RATIO = 0.8
VAL_RATIO = 0.1
TEST_RATIO = 0.1

# 支持的图片扩展名
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}


def parse_args():
    """
    解析命令行参数

    【参数说明】
    --src: 源图片目录路径（必需）
    --seed: 随机种子，确保分割可复现（默认: 42）
    --convert-xml: 是否将 XML 标注转换为 YOLO 格式
    --xml-dir: XML 标注文件目录

    【返回】
    argparse.Namespace 对象，包含解析后的参数
    """
    parser = argparse.ArgumentParser(
        description='数据集分割脚本：将数据集分为训练集、验证集、测试集'
    )
    parser.add_argument(
        '--src',
        type=str,
        required=True,
        help='源图片目录路径'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='随机种子，用于确保分割可复现（默认: 42）'
    )
    parser.add_argument(
        '--convert-xml',
        action='store_true',
        help='是否将 XML 标注转换为 YOLO 格式'
    )
    parser.add_argument(
        '--xml-dir',
        type=str,
        default=None,
        help='XML 标注文件目录'
    )
    return parser.parse_args()


def create_directories(src_dir):
    """
    创建输出目录结构

    【功能】在源目录同级创建标准的 YOLO 数据集目录结构

    【目录结构】
    src_dir/../images/
        train/
        val/
        test/
    src_dir/../labels/
        train/
        val/
        test/

    【参数】
    - src_dir: 源图片目录路径

    【返回】
    包含所有目标目录路径的字典
    """
    # 获取父目录
    parent_dir = Path(src_dir).parent

    # 定义目标目录
    dirs = {
        'train_images': parent_dir / 'images' / 'train',
        'val_images': parent_dir / 'images' / 'val',
        'test_images': parent_dir / 'images' / 'test',
        'train_labels': parent_dir / 'labels' / 'train',
        'val_labels': parent_dir / 'labels' / 'val',
        'test_labels': parent_dir / 'labels' / 'test',
    }

    # 创建所有目录
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)

    return dirs


def get_image_files(src_dir):
    """
    获取源目录中的所有图片文件

    【功能】扫描源目录，返回所有图片文件路径列表

    【参数】
    - src_dir: 源图片目录路径

    【返回】
    图片文件路径列表

    【过滤规则】
    只包含扩展名在 IMAGE_EXTENSIONS 中的文件
    """
    src_path = Path(src_dir)
    image_files = []

    for file_path in src_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
            image_files.append(file_path)

    return sorted(image_files)


def split_dataset(image_files, seed=42):
    """
    将图片文件列表分割为训练集、验证集、测试集

    【算法流程】
    1. 设置随机种子，确保可复现
    2. 打乱文件列表
    3. 按比例计算分割点
    4. 分割列表

    【参数】
    - image_files: 图片文件路径列表
    - seed: 随机种子

    【返回】
    (train_files, val_files, test_files) 三个列表

    【示例】
    假设 100 张图片：
    - train: 80 张
    - val: 10 张
    - test: 10 张
    """
    # 设置随机种子，确保每次运行结果相同
    random.seed(seed)

    # 复制列表并打乱顺序
    shuffled = image_files.copy()
    random.shuffle(shuffled)

    # 计算分割点
    total = len(shuffled)
    train_end = int(total * TRAIN_RATIO)
    val_end = train_end + int(total * VAL_RATIO)

    # 分割列表
    train_files = shuffled[:train_end]
    val_files = shuffled[train_end:val_end]
    test_files = shuffled[val_end:]

    return train_files, val_files, test_files


def copy_files(file_list, target_dir):
    """
    复制文件到目标目录

    【功能】将文件列表中的所有文件复制到目标目录

    【参数】
    - file_list: 文件路径列表
    - target_dir: 目标目录路径

    【进度显示】
    使用 tqdm 显示进度条
    """
    target_path = Path(target_dir)

    for file_path in tqdm(file_list, desc=f"复制到 {target_dir}"):
        shutil.copy2(file_path, target_path / file_path.name)


def convert_xml_to_yolo(xml_path, output_path, class_names=None):
    """
    将 PASCAL VOC XML 格式标注转换为 YOLO TXT 格式

    【PASCAL VOC XML 格式】
    <annotation>
        <size>
            <width>640</width>
            <height>480</height>
        </size>
        <object>
            <name>cat</name>
            <bndbox>
                <xmin>100</xmin>
                <ymin>100</ymin>
                <xmax>300</xmax>
                <ymax>300</ymax>
            </bndbox>
        </object>
    </annotation>

    【YOLO TXT 格式】
    <class_id> <x_center> <y_center> <width> <height>
    例如: 0 0.3125 0.4167 0.3125 0.4167

    【坐标转换公式】
    x_center = (xmin + xmax) / 2 / image_width
    y_center = (ymin + ymax) / 2 / image_height
    width = (xmax - xmin) / image_width
    height = (ymax - ymin) / image_height

    【参数】
    - xml_path: XML 文件路径
    - output_path: 输出 TXT 文件路径
    - class_names: 类别名称列表，用于将名称映射为 ID

    【返回】
    转换成功返回 True，失败返回 False
    """
    try:
        # 解析 XML 文件
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # -------------------------------------------------------------------------
        # 获取图片尺寸
        # -------------------------------------------------------------------------
        size = root.find('size')
        if size is None:
            print(f"警告: {xml_path} 缺少 size 信息")
            return False

        img_width = int(size.find('width').text)
        img_height = int(size.find('height').text)

        # -------------------------------------------------------------------------
        # 解析目标并转换坐标
        # -------------------------------------------------------------------------
        lines = []

        for obj in root.findall('object'):
            # 获取类别名称
            name = obj.find('name').text

            # 将类别名称映射为 ID
            if class_names:
                if name not in class_names:
                    # 新类别，添加到列表
                    class_names.append(name)
                class_id = class_names.index(name)
            else:
                class_id = 0  # 单类别检测

            # 获取边界框坐标
            bbox = obj.find('bndbox')
            xmin = float(bbox.find('xmin').text)
            ymin = float(bbox.find('ymin').text)
            xmax = float(bbox.find('xmax').text)
            ymax = float(bbox.find('ymax').text)

            # -------------------------------------------------------------------------
            # 转换为 YOLO 格式（归一化坐标）
            # -------------------------------------------------------------------------
            # 中心点坐标
            x_center = (xmin + xmax) / 2 / img_width
            y_center = (ymin + ymax) / 2 / img_height

            # 宽高
            bbox_width = (xmax - xmin) / img_width
            bbox_height = (ymax - ymin) / img_height

            # 确保坐标在 0-1 范围内
            x_center = max(0, min(1, x_center))
            y_center = max(0, min(1, y_center))
            bbox_width = max(0, min(1, bbox_width))
            bbox_height = max(0, min(1, bbox_height))

            lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {bbox_width:.6f} {bbox_height:.6f}")

        # -------------------------------------------------------------------------
        # 写入 TXT 文件
        # -------------------------------------------------------------------------
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))

        return True

    except Exception as e:
        print(f"转换失败 {xml_path}: {e}")
        return False


def process_annotations(image_files, src_xml_dir, target_label_dir, class_names=None):
    """
    处理标注文件

    【功能】将图片对应的 XML 标注文件转换为 YOLO 格式

    【处理逻辑】
    对于每张图片：
    1. 查找对应的 XML 文件（同名，扩展名为 .xml）
    2. 转换为 YOLO 格式
    3. 保存到目标目录

    【参数】
    - image_files: 图片文件列表
    - src_xml_dir: XML 文件源目录
    - target_label_dir: 标签输出目录
    - class_names: 类别名称列表（会被更新）

    【注意】
    如果找不到对应的 XML 文件，会跳过该图片
    """
    xml_dir = Path(src_xml_dir)
    label_dir = Path(target_label_dir)

    for img_path in tqdm(image_files, desc=f"处理标注到 {target_label_dir}"):
        # 查找对应的 XML 文件
        xml_path = xml_dir / f"{img_path.stem}.xml"

        if xml_path.exists():
            # 转换并保存
            output_path = label_dir / f"{img_path.stem}.txt"
            convert_xml_to_yolo(xml_path, output_path, class_names)


def generate_classes_file(parent_dir, class_names):
    """
    生成类别名称文件

    【功能】将类别列表保存到 classes.txt 文件

    【文件格式】
    每行一个类别名称，行号即为类别 ID

    【参数】
    - parent_dir: 输出目录
    - class_names: 类别名称列表
    """
    if class_names:
        output_path = Path(parent_dir) / 'classes.txt'
        with open(output_path, 'w', encoding='utf-8') as f:
            for name in class_names:
                f.write(f"{name}\n")
        print(f"生成类别文件: {output_path}")
        print(f"类别列表: {class_names}")


def main():
    """
    主函数

    【执行流程】
    1. 解析命令行参数
    2. 创建输出目录
    3. 获取图片文件列表
    4. 分割数据集
    5. 复制图片到目标目录
    6. 处理标注文件（可选）
    7. 生成类别文件

    【输出统计】
    显示每个子集的图片数量和占比
    """
    # -------------------------------------------------------------------------
    # 步骤 1: 解析参数
    # -------------------------------------------------------------------------
    args = parse_args()

    print("=" * 60)
    print("数据集分割脚本")
    print("=" * 60)
    print(f"源目录: {args.src}")
    print(f"随机种子: {args.seed}")
    print(f"分割比例: {TRAIN_RATIO}:{VAL_RATIO}:{TEST_RATIO}")
    print(f"转换 XML: {args.convert_xml}")
    if args.convert_xml:
        print(f"XML 目录: {args.xml_dir}")
    print("=" * 60)

    # -------------------------------------------------------------------------
    # 步骤 2: 创建目录
    # -------------------------------------------------------------------------
    dirs = create_directories(args.src)
    parent_dir = Path(args.src).parent

    # -------------------------------------------------------------------------
    # 步骤 3: 获取图片列表
    # -------------------------------------------------------------------------
    image_files = get_image_files(args.src)
    total_images = len(image_files)

    if total_images == 0:
        print(f"错误: 在 {args.src} 中未找到图片文件")
        return

    print(f"共找到 {total_images} 张图片")

    # -------------------------------------------------------------------------
    # 步骤 4: 分割数据集
    # -------------------------------------------------------------------------
    train_files, val_files, test_files = split_dataset(image_files, args.seed)

    print(f"\n分割结果:")
    print(f"  训练集: {len(train_files)} 张 ({len(train_files)/total_images*100:.1f}%)")
    print(f"  验证集: {len(val_files)} 张 ({len(val_files)/total_images*100:.1f}%)")
    print(f"  测试集: {len(test_files)} 张 ({len(test_files)/total_images*100:.1f}%)")

    # -------------------------------------------------------------------------
    # 步骤 5: 复制图片
    # -------------------------------------------------------------------------
    print("\n开始复制图片...")
    copy_files(train_files, dirs['train_images'])
    copy_files(val_files, dirs['val_images'])
    copy_files(test_files, dirs['test_images'])

    # -------------------------------------------------------------------------
    # 步骤 6: 处理标注文件（可选）
    # -------------------------------------------------------------------------
    class_names = []

    if args.convert_xml and args.xml_dir:
        print("\n开始转换标注文件...")
        process_annotations(train_files, args.xml_dir, dirs['train_labels'], class_names)
        process_annotations(val_files, args.xml_dir, dirs['val_labels'], class_names)
        process_annotations(test_files, args.xml_dir, dirs['test_labels'], class_names)

        # -------------------------------------------------------------------------
        # 步骤 7: 生成类别文件
        # -------------------------------------------------------------------------
        generate_classes_file(parent_dir, class_names)

    print("\n" + "=" * 60)
    print("数据集分割完成！")
    print(f"输出目录: {parent_dir}")
    print("=" * 60)


# =============================================================================
# 脚本入口
# =============================================================================
if __name__ == "__main__":
    main()
