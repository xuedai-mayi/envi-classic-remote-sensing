# 实验九：图像锐化——38 图验收清单

本预设依据实验指导书和用户提供的完整参考成品建立。参考成品为 23 页、38 图，因此本实验的 `min_screenshots` 至少为 38；每个阶段必须使用唯一截图。阶段标题可直接转化为报告图题，但参数与结果必须来自本次实际运行。

## 数据角色

- `显卡_7221390.jpg`：RGB 显示，绿波段用于 h1/h2/h3/h4 梯度卷积。
- `EE_sobel la.bmp`：Sobel、Laplacian、高斯低通后 Laplacian 锐化。
- 南京图像 `AA`：定向滤波，以 4、3、2 波段显示。

指导书中卷积核矩阵可能以图片呈现。必须从指导书页面或可靠原始材料读取 h1–h4 的实际矩阵，不能凭记忆补写。

## A. 梯度算子锐化

| 顺序 | stage_id | 必须显示的证据 |
|---:|---|---|
| 1 | `01-gpu-original-rgb` | 显卡图像原始 RGB 显示 |
| 2 | `02-user-defined-entry` | Filter → Convolutions and Morphology → Convolutions → User Defined 入口或已打开的工具 |
| 3 | `03-h1-kernel-parameters` | 3×3 h1 完整矩阵、绿波段和输出设置 |
| 4 | `04-h2-kernel-parameters` | 3×3 h2 完整矩阵、绿波段和输出设置 |
| 5 | `05-h1-h2-linked-compare` | h1 与 h2 梯度响应的连接对比 |
| 6 | `06-h1-h2-bandmath-mapping` | Band Math `b1+b2` 及 b1、b2 变量映射 |
| 7 | `07-h1-h2-sum-compare` | h1+h2、h1、h2 三者对比 |
| 8 | `08-h3-sobel-kernel-parameters` | Sobel h3 完整矩阵及处理设置 |
| 9 | `09-h4-sobel-kernel-parameters` | Sobel h4 完整矩阵及处理设置 |
| 10 | `10-h3-h4-bandmath-mapping` | h3+h4 的表达式与变量映射 |
| 11 | `11-simple-vs-sobel-gradient-compare` | h3+h4 与 h1+h2 结果对比 |

## B. Sobel 与 Laplacian 锐化

| 顺序 | stage_id | 必须显示的证据 |
|---:|---|---|
| 12 | `12-ee-original` | `EE_sobel la.bmp` 原始图像 |
| 13 | `13-sobel-tool-parameters` | Sobel 菜单、工具与 Apply to File 参数 |
| 14 | `14-sobel-gradient-result` | Sobel 梯度图像结果 |
| 15 | `15-sobel-add-bandmath-mapping` | 原图 + Sobel 梯度的 `b1+b2` 与变量映射 |
| 16 | `16-sobel-sharpened-result` | Sobel 加和锐化结果 |
| 17 | `17-sobel-three-way-compare` | 原图、Sobel 梯度、加和结果对比 |
| 18 | `18-laplacian-tool-parameters` | Laplacian 菜单、默认卷积核与输出设置 |
| 19 | `19-laplacian-gradient-result` | Laplacian 梯度图像 |
| 20 | `20-laplacian-add-bandmath-mapping` | 原图 + Laplacian 梯度的表达式与映射 |
| 21 | `21-laplacian-sharpened-result` | Laplacian 加和锐化结果 |
| 22 | `22-laplacian-three-way-compare` | 加和结果、梯度图、原图对比 |
| 23 | `23-gaussian-lowpass-parameters` | Gaussian Low Pass 菜单、核和输出设置 |
| 24 | `24-gaussian-lowpass-result` | 高斯低通结果 |
| 25 | `25-lowpass-laplacian-sharpened` | 低通后计算 Laplacian 并加回最初原图的结果 |
| 26 | `26-laplacian-difference-bandmath` | 两种 Laplacian 流程执行 `b1-b2` 的表达式与变量映射 |
| 27 | `27-laplacian-difference-equalized` | 差值图均衡化拉伸后的可视对比 |

注意第 25 阶段 Band Math 中“原始图像”仍是最初的 `EE_sobel la.bmp`，不是高斯低通结果。第 26 阶段要在 `parameters` 中明确 b1、b2 分别对应哪条流程。

## C. 定向滤波

| 顺序 | stage_id | 必须显示的证据 |
|---:|---|---|
| 28 | `28-aa-original-432` | 南京 AA 原始图像，以 4、3、2 显示 |
| 29 | `29-directional-angle-30` | Directional 工具的 30° 方向角 |
| 30 | `30-directional-kernel-3x3` | 3×3 定向卷积核参数与输出设置 |
| 31 | `31-directional-gradient-3x3` | 3×3 定向滤波梯度图，以 4、3、2 显示 |
| 32 | `32-directional-add-bandmath-3x3` | 原图与 3×3 梯度图加和的表达式与映射 |
| 33 | `33-directional-sharpened-3x3` | 3×3 定向滤波加和锐化结果 |
| 34 | `34-directional-kernel-5x5` | 5×5 定向卷积核参数与输出设置 |
| 35 | `35-directional-3x3-vs-5x5` | 3×3 与 5×5 定向滤波结果对比 |
| 36 | `36-directional-sharpened-5x5` | 5×5 梯度加和锐化结果 |
| 37 | `37-aa-original-vs-5x5` | AA 原图与 5×5 锐化结果对比 |
| 38 | `38-directional-kernel-difference` | 3×3 与 5×5 处理差异图，经指导书要求的拉伸后显示 |

## 证据门禁参数

```json
{
  "required_stages": [
    "01-gpu-original-rgb",
    "02-user-defined-entry",
    "03-h1-kernel-parameters",
    "04-h2-kernel-parameters",
    "05-h1-h2-linked-compare",
    "06-h1-h2-bandmath-mapping",
    "07-h1-h2-sum-compare",
    "08-h3-sobel-kernel-parameters",
    "09-h4-sobel-kernel-parameters",
    "10-h3-h4-bandmath-mapping",
    "11-simple-vs-sobel-gradient-compare",
    "12-ee-original",
    "13-sobel-tool-parameters",
    "14-sobel-gradient-result",
    "15-sobel-add-bandmath-mapping",
    "16-sobel-sharpened-result",
    "17-sobel-three-way-compare",
    "18-laplacian-tool-parameters",
    "19-laplacian-gradient-result",
    "20-laplacian-add-bandmath-mapping",
    "21-laplacian-sharpened-result",
    "22-laplacian-three-way-compare",
    "23-gaussian-lowpass-parameters",
    "24-gaussian-lowpass-result",
    "25-lowpass-laplacian-sharpened",
    "26-laplacian-difference-bandmath",
    "27-laplacian-difference-equalized",
    "28-aa-original-432",
    "29-directional-angle-30",
    "30-directional-kernel-3x3",
    "31-directional-gradient-3x3",
    "32-directional-add-bandmath-3x3",
    "33-directional-sharpened-3x3",
    "34-directional-kernel-5x5",
    "35-directional-3x3-vs-5x5",
    "36-directional-sharpened-5x5",
    "37-aa-original-vs-5x5",
    "38-directional-kernel-difference"
  ],
  "min_screenshots": 38,
  "require_output": true
}
```

输出登记至少覆盖 h1、h2、h1+h2、h3、h4、h3+h4、Sobel 梯度及锐化、Laplacian 梯度及锐化、高斯低通与低通后 Laplacian、两种 Laplacian 差值、3×3/5×5 定向梯度和锐化结果。
