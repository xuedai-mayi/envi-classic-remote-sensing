# 实验十：数字形态学处理证据预设

本预设适用于老师数据包含 `IKN Nj Pan.bmp`、`cat_Original_Image.jpg` 和带 `.HDR` 的 `AA` 多光谱影像的实验十。必须先从实际指导书核对文件名、公式和参数；指导书有差异时，以指导书为准并记录差异。

旧 benchmark 的 50 张过程图把多个动作合并展示，且未单独证明 Gray 模式、四种二值形态学运算和若干 Band Math 变量映射。为满足“每一步截图”，本预设采用 96 个独立 ENVI 状态。参数窗口与运行结果必须分开截图。

## 冻结规则

- `type` 映射到 `StageRequirement.evidence_type`。
- `params` 中列出的键必须写入 `capture_evidence.parameters`，值必须来自当次实际界面。
- `formula` 保留指导书原始表达式，不自行改成语义相近的另一种写法。
- 结果截图中应同时保留 ENVI 显示窗口标题或图层标识；对比截图应使原图与处理结果同时可见。
- 01–96 均为本 benchmark 的必需阶段。若老师指导书不要求 56–64 的思考题实机验证，可在计划冻结前标记为“指导书差异”并改为单独的可验证输出预览，但不得无说明删除。

## 阶段表

| ID | type | action / caption | params |
|---|---|---|---|
| `01-open-ikn` | result | 打开并显示 IKN Nj Pan 原始影像 | `input_file`, `display_mode` |
| `02-open-convolution` | tool | 打开 Convolutions and Morphology 工具 | `menu_path` |
| `03-gaussian-7x7-parameter` | parameter | 设置 Gaussian Low Pass 7×7 卷积核 | `filter`, `kernel_size` |
| `04-gaussian-output-parameter` | parameter | 选择输入波段并设置高斯低通输出 | `input_band`, `output_name` |
| `05-gaussian-result` | result | 显示高斯低通结果 | `output_name` |
| `06-open-laplacian` | tool | 选择 Laplacian 卷积算子 | `filter` |
| `07-laplacian-3x3-parameter` | parameter | 设置 Laplacian 3×3 参数 | `filter`, `kernel_size` |
| `08-laplacian-output-parameter` | parameter | 设置拉普拉斯输入与输出 | `input_band`, `output_name` |
| `09-laplacian-result` | result | 显示拉普拉斯梯度结果 | `output_name` |
| `10-add-formula` | parameter | 输入梯度影像与原图相加公式 | `formula` |
| `11-add-band-mapping` | parameter | 映射 b1、b2 并设置锐化输出 | `formula`, `b1`, `b2`, `output_name` |
| `12-sharpen-comparison` | comparison | 对比原始影像与锐化结果 | `original`, `processed` |
| `13-threshold-formula` | parameter | 输入阈值分割公式 b1 ge 250 | `formula`, `threshold` |
| `14-threshold-mapping-output` | parameter | 映射阈值输入并设置 IKN Nj Pan_seg 输出 | `b1`, `output_name` |
| `15-threshold-result` | result | 显示初始二值分割结果 | `output_name` |
| `16-open-morphology` | tool | 打开 Morphology 操作界面 | `menu_path` |
| `17-binary-erode-parameter` | parameter | 设置 Binary 腐蚀 3×3、轮次 1、R 波段 | `operation`, `data_type`, `kernel_size`, `iterations`, `band` |
| `18-binary-erode-result` | result | 显示二值腐蚀结果 | `operation` |
| `19-binary-dilate-parameter` | parameter | 设置 Binary 膨胀 3×3、轮次 1、R 波段 | `operation`, `data_type`, `kernel_size`, `iterations`, `band` |
| `20-binary-dilate-result` | result | 显示二值膨胀结果 | `operation` |
| `21-binary-open-parameter` | parameter | 设置 Binary 开运算 3×3、轮次 1、R 波段 | `operation`, `data_type`, `kernel_size`, `iterations`, `band` |
| `22-binary-open-result` | result | 显示二值开运算结果 | `operation` |
| `23-binary-close-parameter` | parameter | 设置 Binary 闭运算 3×3、轮次 1、R 波段 | `operation`, `data_type`, `kernel_size`, `iterations`, `band` |
| `24-binary-close-result` | result | 显示二值闭运算结果 | `operation` |
| `25-binary-four-way-comparison` | comparison | 同屏比较初始、腐蚀、膨胀、开与闭结果 | `layers` |
| `26-gray-input` | result | 打开 IKN Nj Pan_seg 的 R 波段 | `input_file`, `band` |
| `27-gray-morphology-parameter` | parameter | 设置 Gray 类型、轮次 2 的灰度形态学 | `data_type`, `iterations`, `band`, `kernel_size` |
| `28-gray-result-comparison` | comparison | 连接显示并比较灰度形态学前后结果 | `original`, `processed` |
| `29-open-cat-rgb` | result | 以 RGB 打开彩色猫原图 | `input_file`, `display_mode` |
| `30-cat-erode-3x3-parameter` | parameter | 设置 Value 腐蚀 3×3、轮次 1 | `operation`, `data_type`, `kernel_size`, `iterations` |
| `31-cat-erode-3x3-result` | result | 显示彩色猫 3×3 腐蚀结果 | `operation` |
| `32-difference-3x3-formula` | parameter | 输入原图减 3×3 腐蚀图公式 b1-b2 | `formula` |
| `33-difference-3x3-mapping` | parameter | 映射原图与 3×3 腐蚀结果 | `b1`, `b2`, `output_name` |
| `34-difference-3x3-result` | result | 显示 3×3 腐蚀差值结果 | `output_name` |
| `35-cat-erode-5x5-parameter` | parameter | 把结构元素改为 5×5 并执行腐蚀 | `operation`, `data_type`, `kernel_size`, `iterations` |
| `36-cat-erode-5x5-result` | result | 显示彩色猫 5×5 腐蚀结果 | `operation` |
| `37-difference-5x5-formula` | parameter | 输入原图减 5×5 腐蚀图公式 b1-b2 | `formula` |
| `38-difference-5x5-mapping` | parameter | 映射原图与 5×5 腐蚀结果 | `b1`, `b2`, `output_name` |
| `39-difference-5x5-result` | comparison | 对比 3×3 与 5×5 腐蚀差值 | `layers` |
| `40-cat-dilate-parameter` | parameter | 设置 Value 膨胀 3×3、轮次 1 | `operation`, `data_type`, `kernel_size`, `iterations` |
| `41-cat-dilate-result` | result | 显示彩色猫膨胀结果 | `operation` |
| `42-original-quick-stats` | tool | 对猫原图执行 Quick Stats | `input_layer`, `menu_path` |
| `43-dilated-quick-stats` | tool | 对膨胀图执行 Quick Stats | `input_layer`, `menu_path` |
| `44-histogram-comparison` | comparison | 对比原图与膨胀图的 R、B 高亮端直方图 | `bands`, `layers` |
| `45-highlight-r-formula` | parameter | 输入 R 通道高光响应公式 250-float(b1) | `formula`, `band` |
| `46-highlight-r-mapping` | parameter | 映射膨胀图 R 通道并设置输出 | `b1`, `output_name` |
| `47-highlight-r-result` | result | 显示 R 通道高光响应 | `output_name` |
| `48-highlight-b-mapping` | parameter | 将同一公式映射到 B 通道 | `formula`, `b1`, `band`, `output_name` |
| `49-highlight-b-result` | result | 显示 B 通道高光响应 | `output_name` |
| `50-highlight-add-formula` | parameter | 输入 R、B 高光响应相加公式 b1+b2 | `formula` |
| `51-highlight-add-mapping` | parameter | 映射 R、B 响应并设置输出 | `b1`, `b2`, `output_name` |
| `52-highlight-add-result` | result | 显示 R、B 高光响应叠加结果 | `output_name` |
| `53-highlight-mask-formula` | parameter | 输入原图与候选高光组合公式 b1*(b2 ge 1) | `formula` |
| `54-highlight-mask-mapping` | parameter | 映射原图与候选高光掩膜 | `b1`, `b2`, `output_name` |
| `55-highlight-extraction-result` | result | 显示猫眼高光提取结果 | `output_name` |
| `56-left-eye-roi` | parameter | 仅圈定左眼高光 ROI | `roi_name`, `target` |
| `57-both-eyes-roi` | parameter | 完成左右眼 ROI 范围 | `roi_names`, `targets` |
| `58-save-eye-roi` | output | 保存猫眼 ROI | `output_name` |
| `59-roi-to-mask-parameter` | parameter | 把双眼 ROI 转换为 Mask | `roi_names`, `mask_value`, `output_name` |
| `60-eye-mask-result` | result | 显示猫眼高光 Mask | `output_name` |
| `61-mask-normalize-formula` | parameter | 输入双眼 Mask 统一值的 Band Math 公式 | `formula`, `inputs` |
| `62-mask-normalize-result` | result | 显示统一后的猫眼 Mask | `output_name` |
| `63-remove-highlight-formula` | parameter | 输入仅修改 Mask 内像元的高光去除公式 | `formula`, `original`, `mask`, `repair_source` |
| `64-remove-highlight-comparison` | comparison | 对比原图与去除猫眼高光后的图像 | `original`, `processed` |
| `65-open-aa-band5` | result | 打开 AA 并显示第 5 波段 | `input_file`, `band` |
| `66-open-density-slice` | tool | 打开 Density Slice | `menu_path`, `band` |
| `67-density-slice-parameter` | parameter | 保留默认密度分割参数 | `band`, `ranges` |
| `68-density-slice-result` | result | 显示第 5 波段密度分割结果 | `band` |
| `69-density-threshold-formula` | parameter | 输入 (b5 lt 28)*(b5 gt 2) | `formula`, `lower`, `upper` |
| `70-density-threshold-mapping` | parameter | 映射 AA 各波段并设置阈值输出 | `bands`, `output_name` |
| `71-density-threshold-result` | result | 显示灰度范围二值候选区 | `output_name` |
| `72-density-open-parameter` | parameter | 设置 Binary 3×3 开运算 | `operation`, `data_type`, `kernel_size`, `iterations` |
| `73-density-open-result` | result | 显示密度分割开运算结果 | `operation` |
| `74-density-close-parameter` | parameter | 设置 Binary 3×3 闭运算 | `operation`, `data_type`, `kernel_size`, `iterations` |
| `75-density-close-result` | result | 显示密度分割闭运算结果 | `operation` |
| `76-density-open-close-comparison` | comparison | 对比原始候选区、开运算和闭运算结果 | `layers` |
| `77-open-aa-water-workflow` | result | 重新打开 AA 水体提取输入 | `input_file`, `bands` |
| `78-water-formula` | parameter | 输入水体提取公式 b5/b2 eq 0 | `formula` |
| `79-water-band-mapping` | parameter | 映射 AA 第 5、2 波段并设置 AA_water | `b5`, `b2`, `output_name` |
| `80-water-mask-result` | result | 显示初始 AA_water 水体掩膜 | `output_name` |
| `81-water-erode-parameter` | parameter | 设置水体掩膜腐蚀参数 | `operation`, `data_type`, `kernel_size`, `iterations` |
| `82-water-erode-result` | result | 显示水体掩膜腐蚀结果 | `operation` |
| `83-water-density-class-output` | parameter | 密度分割并选择按类别输出 | `input_layer`, `output_distribution`, `output_name` |
| `84-water-class-result` | result | 显示密度分割类别图像 | `output_name` |
| `85-open-segmentation` | tool | 打开 Post Classification Segmentation | `menu_path` |
| `86-segmentation-parameter` | parameter | 设置 8 邻域、最小像元数 100 | `neighborhood`, `minimum_pixels`, `output_name` |
| `87-segmentation-label-result` | result | 显示区域标识结果 | `output_name` |
| `88-yangtze-cursor-query` | tool | 用 Cursor Location/Value 判读长江区域标识值 | `cursor_location`, `label_value` |
| `89-yangtze-formula` | parameter | 输入长江区域提取公式 b1 eq 1 | `formula`, `label_value` |
| `90-yangtze-band-mapping` | parameter | 映射区域标识图并设置长江输出 | `b1`, `output_name` |
| `91-yangtze-result-comparison` | comparison | 对比原始影像、水体掩膜与长江主体 | `layers` |
| `92-open-raster-to-vector` | tool | 打开 Vector > Raster to Vector | `menu_path` |
| `93-raster-to-vector-parameter` | parameter | 选择处理后的 AA_water、DN=1 与 AA_water_vec 输出 | `input_layer`, `dn`, `output_name` |
| `94-vector-result` | result | 显示生成的水体矢量层 | `output_name` |
| `95-export-shapefile-parameter` | parameter | 在 Vector Layer List 导出 AA_water_vecs.shp | `layer`, `format`, `output_name` |
| `96-shapefile-output` | output | 显示导出完成的矢量层并登记 Shapefile 组成文件 | `output_name`, `component_files` |

## 输出登记

至少登记：锐化影像、`IKN Nj Pan_seg`、四种二值形态学结果、彩色腐蚀/膨胀结果、猫眼掩膜或修复结果、密度分割开闭结果、`AA_water`、区域标识结果、长江主体栅格、`AA_water_vec` 和 Shapefile 的 `.shp/.shx/.dbf/.prj`（存在者逐一登记）。

外部 GIS 复核不由 ENVI MCP 越权操作。全自动模式应使用可审计的 GDAL/OGR 读取 Shapefile 并生成矢量预览与几何统计；如果课程明确要求 ArcGIS/MapInfo 界面截图，再调用专用 GIS 自动化能力或标记为需要人工补证，不能伪装成 ENVI 截图。
