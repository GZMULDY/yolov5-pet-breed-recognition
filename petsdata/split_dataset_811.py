#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按 8:1:1 比例将图片划分为 train/val/test 三个集合，并在每个集合下
创建 images/ 与 labels/ 子目录（labels 目录为空，便于之后自行放置标签）。

默认源目录为：d:\\yolov5-5.0\\yolov5-5.0\\petsdata\\images
脚本只会处理源目录根部的图片文件（忽略 train/val/test 子目录）。

使用示例：
    # 先看分配结果但不实际移动（演练）
    python split_dataset_811.py --src "d:\\yolov5-5.0\\yolov5-5.0\\petsdata\\images" --dry-run

    # 实际移动文件（默认移动），可设置随机种子确保可复现
    python split_dataset_811.py --src "d:\\yolov5-5.0\\yolov5-5.0\\petsdata\\images" --seed 2024

    # 如果想复制而不是移动（保留原始目录中的文件）
    python split_dataset_811.py --src "d:\\yolov5-5.0\\yolov5-5.0\\petsdata\\images" --copy

目录结构示例（执行后）：
    petsdata/images/
      ├── train/
      │     ├── images/   # 训练集图片
      │     └── labels/   # 留空，之后放置对应标签
      ├── val/
      │     ├── images/
      │     └── labels/
      └── test/
            ├── images/
            └── labels/
"""

import argparse
import os
import random
import shutil
import sys
import math
import re
from typing import List, Tuple

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def is_image_file(name: str) -> bool:
    ext = os.path.splitext(name)[1].lower()
    return ext in IMAGE_EXTS


def collect_root_images(src: str) -> List[str]:
    """仅收集源目录根部的图片文件，忽略子目录。返回文件名列表。"""
    files = []
    for entry in os.listdir(src):
        full = os.path.join(src, entry)
        if os.path.isfile(full) and is_image_file(entry):
            files.append(entry)
    return files


def ensure_split_dirs(src: str) -> None:
    """在 src 下创建 train/val/test 的 images 与 labels 子目录。"""
    for split in ("train", "val", "test"):
        img_dir = os.path.join(src, split, "images")
        lbl_dir = os.path.join(src, split, "labels")
        os.makedirs(img_dir, exist_ok=True)
        os.makedirs(lbl_dir, exist_ok=True)


def normalize_case(name: str, mode: str) -> str:
    if mode == "lower":
        return name.lower()
    if mode == "upper":
        return name.upper()
    return name


def extract_breed_from_stem(stem: str) -> str:
    # 提取末尾 "_数字" 之前的部分，保留内部下划线，例如 "great_pyrenees_171" -> "great_pyrenees"
    m = re.match(r"(.+)_\d+$", stem)
    return m.group(1) if m else stem


def derive_classes(files: List[str], case_mode: str) -> List[str]:
    classes_set = set()
    for f in files:
        stem = os.path.splitext(f)[0]
        breed = extract_breed_from_stem(stem)
        classes_set.add(normalize_case(breed, case_mode))
    return sorted(classes_set)


def write_classes_files(src: str, classes: List[str], filename: str) -> None:
    content = "\n".join(classes) + ("\n" if classes else "")
    for split in ("train", "val", "test"):
        lbl_dir = os.path.join(src, split, "labels")
        os.makedirs(lbl_dir, exist_ok=True)
        path = os.path.join(lbl_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


def collect_split_images(src_dir: str) -> List[str]:
    names: List[str] = []
    for split in ("train", "val", "test"):
        img_dir = os.path.join(src_dir, split, "images")
        if os.path.isdir(img_dir):
            for entry in os.listdir(img_dir):
                full = os.path.join(img_dir, entry)
                if os.path.isfile(full) and is_image_file(entry):
                    names.append(entry)
    return names

# ---- XML -> YOLO 转换辅助函数 ----

def build_xml_index(xmls_dir: str):
    index = {}
    if not os.path.isdir(xmls_dir):
        return index
    for entry in os.listdir(xmls_dir):
        if entry.lower().endswith(".xml"):
            index[os.path.splitext(entry)[0].lower()] = os.path.join(xmls_dir, entry)
    return index


def parse_voc_xml(xml_path: str):
    try:
        import xml.etree.ElementTree as ET
        root = ET.parse(xml_path).getroot()
        w = int(root.find("./size/width").text)
        h = int(root.find("./size/height").text)
        objs = []
        for obj in root.findall("object"):
            name = (obj.find("name").text or "").strip().lower()
            b = obj.find("bndbox")
            xmin = float(b.find("xmin").text)
            ymin = float(b.find("ymin").text)
            xmax = float(b.find("xmax").text)
            ymax = float(b.find("ymax").text)
            objs.append((name, xmin, ymin, xmax, ymax, w, h))
        return objs
    except Exception as e:
        print(f"解析XML失败：{xml_path} -> {e}")
        return []


def voc_to_yolo_lines(objects, class_name: str, class_to_id: dict):
    lines = []
    cls_id = class_to_id.get(class_name)
    if cls_id is None:
        return lines, {class_name}
    for _name, xmin, ymin, xmax, ymax, w, h in objects:
        cx = ((xmin + xmax) / 2.0) / w
        cy = ((ymin + ymax) / 2.0) / h
        bw = (xmax - xmin) / w
        bh = (ymax - ymin) / h
        cx = max(0.0, min(1.0, cx))
        cy = max(0.0, min(1.0, cy))
        bw = max(0.0, min(1.0, bw))
        bh = max(0.0, min(1.0, bh))
        lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")
    return lines, {class_name}


def convert_split_xml_to_yolo(src_dir: str, split: str, xml_index: dict, class_mode: str, class_to_id: dict, dry_run: bool, class_case: str):
    img_dir = os.path.join(src_dir, split, "images")
    lbl_dir = os.path.join(src_dir, split, "labels")
    os.makedirs(lbl_dir, exist_ok=True)
    created = 0
    missing = 0
    classes_seen = set()
    if not os.path.isdir(img_dir):
        return created, missing, classes_seen
    for entry in os.listdir(img_dir):
        if not is_image_file(entry):
            continue
        stem = os.path.splitext(entry)[0]
        xml_key = stem.lower()
        xml_path = xml_index.get(xml_key)
        if not xml_path:
            missing += 1
            print(f"未找到XML：{entry} -> {xml_key}.xml")
            continue
        objects = parse_voc_xml(xml_path)
        if class_mode == "species":
            # 使用XML中的cat/dog
            label_name = objects[0][0] if objects else None
            if not label_name:
                lines, names_encountered = [], set()
            else:
                label_name = normalize_case(label_name, class_case)
                lines, names_encountered = voc_to_yolo_lines(objects, label_name, class_to_id)
        else:
            # 使用品种名（从文件名去掉末尾索引）
            breed = normalize_case(extract_breed_from_stem(stem), class_case)
            lines, names_encountered = voc_to_yolo_lines(objects, breed, class_to_id)
        classes_seen |= names_encountered
        out_path = os.path.join(lbl_dir, f"{os.path.splitext(entry)[0]}.txt")
        if dry_run:
            preview = lines[0] if lines else "(空)"
            print(f"[DRY] 写入 {split}/labels/{os.path.basename(out_path)} -> {preview} ...")
        else:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + ("\n" if lines else ""))
        created += 1
    return created, missing, classes_seen


def convert_all_splits_xml_to_yolo(src_dir: str, xml_dir: str, dry_run: bool, class_mode: str, class_to_id: dict, class_case: str):
    xml_index = build_xml_index(xml_dir)
    total_created = 0
    total_missing = 0
    all_classes = set()
    for split in ("train", "val", "test"):
        created, missing, seen = convert_split_xml_to_yolo(src_dir, split, xml_index, class_mode, class_to_id, dry_run, class_case)
        total_created += created
        total_missing += missing
        all_classes |= seen
    print(f"XML转换完成：labels写入目标={total_created}，未找到XML={total_missing}")
    return sorted(all_classes), class_to_id


def compute_counts(total: int, ratios: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """用向下取整确保总数一致：train, val, test。"""
    r_sum = sum(ratios)
    train = math.floor(total * ratios[0] / r_sum)
    val = math.floor(total * ratios[1] / r_sum)
    test = total - train - val
    return train, val, test


def move_or_copy(src_dir: str, files: List[str], dest_split: str, copy: bool, dry_run: bool) -> None:
    dest_images_dir = os.path.join(src_dir, dest_split, "images")
    for fname in files:
        src_path = os.path.join(src_dir, fname)
        dst_path = os.path.join(dest_images_dir, fname)
        if dry_run:
            print(f"[DRY] {fname} -> {dest_split}/images/")
            continue
        if copy:
            shutil.copy2(src_path, dst_path)
        else:
            shutil.move(src_path, dst_path)


def split_dataset(src: str, ratios: Tuple[int, int, int], seed: int, copy: bool, dry_run: bool, class_case: str, classes_file: str, only_classes: bool, xml_dir: str, convert_xml: bool, convert_only: bool, class_mode: str) -> None:
    if not os.path.isdir(src):
        print(f"源目录不存在：{src}")
        sys.exit(1)

    ensure_split_dirs(src)

    # 如果仅执行 XML->YOLO 转换
    if convert_only:
        if class_mode == "species":
            classes = ["cat", "dog"]
        else:
            # 从现有 splits 的图片推导品种列表
            classes = derive_classes(collect_split_images(src), class_case)
        if dry_run:
            print(f"[DRY] 将在各 labels/ 写入类列表 '{classes_file}': {', '.join(classes) if classes else '(空)'}")
        else:
            write_classes_files(src, classes, classes_file)
        class_to_id = {name: i for i, name in enumerate(classes)}
        convert_all_splits_xml_to_yolo(src, xml_dir, dry_run, class_mode, class_to_id, class_case)
        print("已仅执行XML->YOLO转换，并在各 labels/ 写入类列表文件。")
        return

    root_images = collect_root_images(src)
    total = len(root_images)

    # 写入类别列表：根据 class_mode 决定是物种还是品种
    if convert_xml:
        if class_mode == "species":
            classes = ["cat", "dog"]
        else:
            source_files_for_classes = root_images if total > 0 else collect_split_images(src)
            classes = derive_classes(source_files_for_classes, class_case)
    else:
        source_files_for_classes = root_images if total > 0 else collect_split_images(src)
        classes = derive_classes(source_files_for_classes, class_case)

    if dry_run:
        print(f"[DRY] 将在各 labels/ 写入类列表文件 '{classes_file}': {', '.join(classes) if classes else '(空)'}")
    else:
        write_classes_files(src, classes, classes_file)

    if only_classes:
        if dry_run:
            print("[DRY] 仅预览类别列表写入，不进行图片划分。")
        else:
            print(f"已在 train/val/test 的 labels/ 目录写入 '{classes_file}'，未进行图片划分。")
        return

    if total == 0:
        print("源目录根部没有可处理的图片文件（或已全部移动）。")
        # 即使没有可划分的图片，也可以按现有 splits 执行 XML 转换
        if convert_xml:
            class_to_id = {name: i for i, name in enumerate(classes)}
            convert_all_splits_xml_to_yolo(src, xml_dir, dry_run, class_mode, class_to_id, class_case)
        return

    rnd = random.Random(seed)
    rnd.shuffle(root_images)

    train_n, val_n, test_n = compute_counts(total, ratios)
    train_files = root_images[:train_n]
    val_files = root_images[train_n: train_n + val_n]
    test_files = root_images[train_n + val_n:]

    print(f"总计图片：{total}（train={train_n}, val={val_n}, test={test_n}），seed={seed}")

    move_or_copy(src, train_files, "train", copy, dry_run)
    move_or_copy(src, val_files, "val", copy, dry_run)
    move_or_copy(src, test_files, "test", copy, dry_run)

    # 完成划分后，如需将 XML 转为 YOLO labels
    if convert_xml:
        class_to_id = {name: i for i, name in enumerate(classes)}
        convert_all_splits_xml_to_yolo(src, xml_dir, dry_run, class_mode, class_to_id, class_case)

    if dry_run:
        print("演练完成（未作任何改动）。")
    else:
        op = "复制" if copy else "移动"
        print(f"{op}完成：train={len(train_files)}, val={len(val_files)}, test={len(test_files)}")
        msg = "并转换XML为YOLO labels，" if convert_xml else ""
        print(f"labels/ 目录已创建，{msg}并写入目标类列表文件。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="按 8:1:1 比例划分图片到 train/val/test，并创建 images/labels 结构与类别列表文件")
    parser.add_argument("--src", type=str, default=r"d:\\yolov5-5.0\\yolov5-5.0\\petsdata\\images",
                        help="源图片目录（包含待划分的图片，且会在其下创建 train/val/test 子目录）")
    parser.add_argument("--seed", type=int, default=42, help="随机种子（确保划分可复现）")
    parser.add_argument("--copy", action="store_true", help="复制而不是移动（保留源目录中的文件）")
    parser.add_argument("--dry-run", action="store_true", help="演练模式，仅打印将进行的操作，不实际执行")
    parser.add_argument("--classes-file", type=str, default="classes.txt", help="在每个 labels/ 目录下生成的类别列表文件名")
    parser.add_argument("--class-case", type=str, default="lower", choices=["lower", "upper", "keep"], help="类别名大小写规范：lower/upper/keep")
    parser.add_argument("--only-classes", action="store_true", help="仅生成类别列表文件，不进行图片划分")
    parser.add_argument("--xml-dir", type=str, default=r"d:\\yolov5-5.0\\yolov5-5.0\\petsdata\\annotations\\xmls", help="Pascal VOC XML 标注目录")
    parser.add_argument("--convert-xml", action="store_true", help="将 annotations/xmls 转成 YOLO labels，按 train/val/test 对齐写入")
    parser.add_argument("--convert-only", action="store_true", help="仅执行 XML->YOLO 转换，不做图片划分")
    parser.add_argument("--class-mode", type=str, default="breed", choices=["species", "breed"], help="类别模式：species（cat/dog）或 breed（37品种）")

    # 固定为 8:1:1，如需自定义可改这里（或扩展为命令行参数）
    ratios = (8, 1, 1)

    args = parser.parse_args()
    split_dataset(src=args.src, ratios=ratios, seed=args.seed, copy=args.copy, dry_run=args.dry_run, class_case=args.class_case, classes_file=args.classes_file, only_classes=args.only_classes, xml_dir=args.xml_dir, convert_xml=args.convert_xml, convert_only=args.convert_only, class_mode=args.class_mode)