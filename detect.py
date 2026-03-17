"""YOLOv5 检测脚本（detect.py）
功能：对图片/视频/摄像头/网络流进行目标检测，可保存结果图像与标签。
核心流程：
- 解析命令行参数并建立输出目录
- 选择设备与加载模型（支持半精度 FP16）
- 构建数据源（单图、文件夹、视频或实时流）
- 前向推理、执行非极大值抑制（NMS）
- 可视化并按需保存检测结果与标签文件
"""
import argparse
import time
from pathlib import Path

import cv2
import torch
import torch.backends.cudnn as cudnn
from numpy import random

from models.experimental import attempt_load
from utils.datasets import LoadStreams, LoadImages
from utils.general import check_img_size, check_requirements, check_imshow, non_max_suppression, apply_classifier, \
    scale_coords, xyxy2xywh, strip_optimizer, set_logging, increment_path
from utils.plots import plot_one_box
from utils.torch_utils import select_device, load_classifier, time_synchronized


def detect(save_img=False):
    """
    运行一次检测流程。
    参数:
        save_img: 是否保存推理后的图像。实际由 opt.nosave 和输入源类型共同决定。
    说明:
        - 支持图片/文件夹/视频/摄像头/网络流作为输入。
        - 输出目录结构为 opt.project/opt.name，并在需要时保存 labels/*.txt。
    """
    source, weights, view_img, save_txt, imgsz = opt.source, opt.weights, opt.view_img, opt.save_txt, opt.img_size
    # 若未开启 --nosave 且输入不是 .txt（路径列表），则保存推理后的图片/视频帧
    save_img = not opt.nosave and not source.endswith('.txt')  # 是否保存可视化结果
    webcam = source.isnumeric() or source.endswith('.txt') or source.lower().startswith(
        ('rtsp://', 'rtmp://', 'http://', 'https://'))
    # 输入源判断：数字代表摄像头；.txt 为路径列表；以 rtsp/rtmp/http/https 开头视为网络流

    # Directories
    # 输出目录：若已存在且 --exist-ok 未指定，则自动递增目录名
    save_dir = Path(increment_path(Path(opt.project) / opt.name, exist_ok=opt.exist_ok))  # increment run
    # 创建 labels 子目录（当需要保存 txt 标签时）
    (save_dir / 'labels' if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # 创建输出目录

    # Initialize
    set_logging()
    device = select_device(opt.device)
    half = device.type != 'cpu'  # 半精度仅在 CUDA 上支持

    # Load model
    # 加载模型并检查输入尺寸与步幅（stride）；如启用半精度则转为 FP16
    model = attempt_load(weights, map_location=device)  # load FP32 model
    stride = int(model.stride.max())  # 模型步幅，决定允许的输入尺寸对齐
    imgsz = check_img_size(imgsz, s=stride)  # 检查/修正输入尺寸
    if half:
        model.half()  # 切换为 FP16

    # Second-stage classifier
    # 二次分类器（可选）：在检测之后再做分类，默认关闭
    classify = False
    if classify:
        modelc = load_classifier(name='resnet101', n=2)  # 初始化分类器
        modelc.load_state_dict(torch.load('weights/resnet101.pt', map_location=device, weights_only=False)['model']).to(device).eval()

    # Set Dataloader
    # 构建数据源：摄像头/流使用 LoadStreams；否则使用 LoadImages（可遍历文件/文件夹/视频）
    vid_path, vid_writer = None, None
    if webcam:
        view_img = check_imshow()  # 检查当前环境是否支持窗口显示
        cudnn.benchmark = True  # 常尺寸推理加速
        dataset = LoadStreams(source, img_size=imgsz, stride=stride)
    else:
        dataset = LoadImages(source, img_size=imgsz, stride=stride)

    # Get names and colors
    # 类别名与随机颜色（用于绘制可视化框）
    names = model.module.names if hasattr(model, 'module') else model.names
    colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]

    # Run inference
    if device.type != 'cpu':
        model(torch.zeros(1, 3, imgsz, imgsz).to(device).type_as(next(model.parameters())))  # 预热一次（CUDA）
    t0 = time.time()
    for path, img, im0s, vid_cap in dataset:
        # 将 numpy 图像转为张量，归一化到 [0,1] 并按需转换精度
        img = torch.from_numpy(img).to(device)
        img = img.half() if half else img.float()  # uint8 -> fp16/fp32
        img /= 255.0  # 像素归一化
        if img.ndimension() == 3:
            img = img.unsqueeze(0)  # 增加 batch 维度

        # Inference
        t1 = time_synchronized()
        pred = model(img, augment=opt.augment)[0]  # 前向推理（支持增强推理）

        # Apply NMS
        # 非极大值抑制（NMS）：按阈值过滤与合并重叠框，可选择类别无关 NMS
        pred = non_max_suppression(pred, opt.conf_thres, opt.iou_thres, classes=opt.classes, agnostic=opt.agnostic_nms)
        t2 = time_synchronized()

        # Apply Classifier
        if classify:
            pred = apply_classifier(pred, modelc, img, im0s)  # 若启用：对检测框再做分类校正

        # Process detections
        for i, det in enumerate(pred):  # detections per image
            if webcam:  # batch_size >= 1
                p, s, im0, frame = path[i], '%g: ' % i, im0s[i].copy(), dataset.count
            else:
                p, s, im0, frame = path, '', im0s, getattr(dataset, 'frame', 0)

            p = Path(p)  # to Path
            save_path = str(save_dir / p.name)  # 可视化输出路径
            txt_path = str(save_dir / 'labels' / p.stem) + ('' if dataset.mode == 'image' else f'_{frame}')  # 标签输出路径
            s += '%gx%g ' % img.shape[2:]  # 打印输入尺寸
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # 归一化尺度（w,h,w,h）
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()  # 映射回原图尺寸

                # Print results
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # 打印每类数量

                # Write results
                for *xyxy, conf, cls in reversed(det):
                    if save_txt:  # Write to file
                        xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # 归一化 xywh（相对原图）
                        line = (cls, *xywh, conf) if opt.save_conf else (cls, *xywh)  # 标签格式：带/不带置信度
                        with open(txt_path + '.txt', 'a') as f:
                            f.write(('%g ' * len(line)).rstrip() % line + '\n')

                    if save_img or view_img:  # 绘制检测框到图像（可视化）
                        label = f'{names[int(cls)]} {conf:.2f}'
                        plot_one_box(xyxy, im0, label=label, color=colors[int(cls)], line_thickness=3)

            # 输出时间统计（推理 + NMS）
            print(f'{s}Done. ({t2 - t1:.3f}s)')

            # 显示窗口（可选）
            if view_img:
                cv2.imshow(str(p), im0)
                cv2.waitKey(1)  # 1 millisecond

            # 保存结果图像或视频
            if save_img:
                if dataset.mode == 'image':
                    cv2.imwrite(save_path, im0)
                else:  # 'video' or 'stream'
                    if vid_path != save_path:  # 新的视频文件，需重新创建写入器
                        vid_path = save_path
                        if isinstance(vid_writer, cv2.VideoWriter):
                            vid_writer.release()  # 释放上一个写入器
                        if vid_cap:  # video
                            fps = vid_cap.get(cv2.CAP_PROP_FPS)
                            w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        else:  # stream
                            fps, w, h = 30, im0.shape[1], im0.shape[0]
                            save_path += '.mp4'
                        vid_writer = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                    vid_writer.write(im0)

    if save_txt or save_img:
        # 结果摘要：显示保存的标签文件数量与输出目录
        s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
        print(f"Results saved to {save_dir}{s}")

    print(f'Done. ({time.time() - t0:.3f}s)')


if __name__ == '__main__':
    # 命令行参数解析：各项参数含义见中文注释
    parser = argparse.ArgumentParser()
    # 权重文件路径：可传入多个 .pt，按顺序运行
    parser.add_argument('--weights', nargs='+', type=str, default='yolov5s.pt', help='模型权重路径，可传入多个')
    # 输入源：文件/文件夹/视频路径，或 0 代表摄像头；也支持 .txt 列表与网络流
    parser.add_argument('--source', type=str, default='data/images', help='输入源（文件/文件夹/视频/摄像头/流）')  # file/folder, 0 for webcam
    # 推理图像尺寸：建议为 32 的倍数，受模型 stride 约束
    parser.add_argument('--img-size', type=int, default=640, help='推理尺寸（像素）')
    # 置信度阈值：低于此值的预测将被过滤
    parser.add_argument('--conf-thres', type=float, default=0.25, help='目标置信度阈值')
    # NMS IoU 阈值：框重叠超过此阈值的预测将被抑制
    parser.add_argument('--iou-thres', type=float, default=0.45, help='NMS 的 IoU 阈值')
    # 设备选择：如 '0'、'0,1' 或 'cpu'
    parser.add_argument('--device', default='', help='CUDA 设备索引或 cpu')
    # 是否显示窗口
    parser.add_argument('--view-img', action='store_true', help='显示推理结果窗口')
    # 是否保存 txt 标签（归一化 xywh）
    parser.add_argument('--save-txt', action='store_true', help='将检测结果保存为 *.txt 标签')
    # 标签中是否附带置信度
    parser.add_argument('--save-conf', action='store_true', help='在标签中保存置信度')
    # 不保存任何图像/视频
    parser.add_argument('--nosave', action='store_true', help='不保存可视化图像或视频')
    # 只保留指定类别：如 --classes 0 或 --classes 0 2 3
    parser.add_argument('--classes', nargs='+', type=int, help='按类别过滤输出')
    # 类别无关 NMS：将不同类别的框也参与互相抑制
    parser.add_argument('--agnostic-nms', action='store_true', help='启用类别无关的 NMS')
    # 增强推理：多尺度/翻转等，可提升精度但会更慢
    parser.add_argument('--augment', action='store_true', help='开启增强推理')
    # 更新所有模型：用于修复部分警告，逐个运行 detect 并清理优化器信息
    parser.add_argument('--update', action='store_true', help='更新所有模型权重')
    # 输出项目与名称：最终保存路径为 runs/detect/name
    parser.add_argument('--project', default='runs/detect', help='结果保存的项目目录')
    parser.add_argument('--name', default='exp', help='结果保存的子目录名称')
    # 若目录已存在则不递增
    parser.add_argument('--exist-ok', action='store_true', help='若目录已存在则允许覆盖而不递增')
    opt = parser.parse_args()
    print(opt)
    check_requirements(exclude=('pycocotools', 'thop'))

    with torch.no_grad():
        if opt.update:  # 更新所有模型（修复 SourceChangeWarning）
            for opt.weights in ['yolov5s.pt', 'yolov5m.pt', 'yolov5l.pt', 'yolov5x.pt']:
                detect()
                strip_optimizer(opt.weights)
        else:
            detect()
