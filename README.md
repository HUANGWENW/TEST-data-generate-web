# 零件数据生成系统

这是一个面向可信内网/VPN环境、多端浏览器访问的零件数据生成工作台，技术栈为：

- Vue 3 + Element Plus
- FastAPI
- RQ + Redis
- PostgreSQL
- 本地/NAS 文件存储
- Docker Compose

## 功能范围

当前版本已经打通以下流程：

1. 创建项目。
2. 上传 GEN 文件、边缘图、已有 Mask、背景图和纹理图。
3. 保存待解析的 DXF 文件，为后续 DXF 转边缘图算法预留入口。
4. 从 GEN 文件提取 mask。
5. 从黑白边缘图提取 mask。
6. 使用纹理将 mask 转为透明零件 PNG。
7. 随机、紧凑、混合布局合成数据集。
8. 输出 YOLO HBB、YOLO OBB 或 COCO segmentation 标签。
9. 查看项目任务、生成结果和性能统计。
10. 拖拽文件或文件夹批量上传素材。
11. 批量下载图片、标签 TXT 或图片与标签组合 ZIP。

> 当前版本没有应用层登录和项目权限隔离。所有能够访问服务的用户均可查看全部项目，建议仅部署在可信公司 VPN 内，不要直接暴露到公网。

## 本地启动

```bash
cd part_dataset_studio
docker compose up --build
```

访问：

- 前端页面：http://localhost:8080
- 后端 API：http://localhost:8000/api/health
- FastAPI 文档：http://localhost:8000/docs

## VPN 服务器部署

服务器需要安装 Git 和 Docker（含 Docker Compose）。

```bash
git clone https://github.com/HUANGWENW/TEST-data-generate-web.git
cd TEST-data-generate-web
cp .env.example .env
docker compose up -d --build
```

部署完成后，VPN 用户访问：

```text
http://服务器内网IP:8080
```

健康检查：

```text
http://服务器内网IP:8080/api/health
```

服务器防火墙只需允许公司 VPN 网段访问 TCP 8080。不要向用户或公网开放 PostgreSQL 5432、Redis 6379；后端 8000 也无需供普通用户直接访问。

更新版本：

```bash
git pull
docker compose up -d --build
```

停止服务：

```bash
docker compose down
```

项目图片与生成结果保存在仓库目录下的 `storage/`，PostgreSQL 数据保存在 Docker 卷 `postgres_data`。服务器迁移或备份时必须同时备份这两部分。

## 推荐使用流程

1. 在项目页新建项目。
2. 上传输入文件：
   - `input`：GEN 文件或黑白边缘图
   - `mask`：直接进入第二步的已有 Mask
   - `dxf`：待后续解析为边缘图的 DXF 文件
   - `background`：合成背景图
   - `texture`：钢板纹理图
3. 进入“生成流程”：
   - 提交 mask 提取任务
   - 提交透明零件生成任务
   - 提交数据集生成任务
4. 在“项目任务”或“任务中心”查看进度。
5. 输出文件保存在 `storage/projects/{project_id}/` 下。

### Mask 与透明零件的分辨率

- 第二步默认保留输入 Mask 的宽高和 alpha 像素，不再自动将最长边缩到 1000 px。
- “输出最长边”设为 `0` 表示保留原尺寸；正数表示按此上限等比缩小，不会放大。API 参数为 `max_side_pixels`，默认 `0`。例如 11992 × 2475 的 Mask 默认输出同尺寸 RGBA PNG；显式设置 `1000` 时输出 1000 × 206。
- 纹理小于 Mask 时，“随机裁剪”模式通过平铺补足，不会为了适应纹理而缩小 Mask；关闭随机裁剪时，将纹理缩放至 Mask 宽高。
- 第三步会先计算零件的最终可放置尺寸，再进行一次缩放，避免原尺寸零件配合大倍率时创建过大的中间图片。合成图仍受所选背景分辨率限制。
- 第一步边缘图以源图像素填充闭合外轮廓，并按嵌套层级保留孔洞；输出裁剪到各零件包围框加 5 px 留白，不进行缩放。边缘可选自动识别、白线黑底或黑线白底；自动模式把像素占比较少的颜色视为细线。
- “断点修补核”使用闭运算修补小断点，参数名 `dilation_size` 为兼容旧客户端保留，但不再永久膨胀后仅取内部区域。`1` 表示不修补，默认 `3`。过大的值可能合并邻近轮廓或填掉细孔。相交、重合切割线需先在源图中整理为独立闭合轮廓。
- “最小面积”对应 `min_area`，单位 px²，默认 5000，只用于过滤零件，不单独过滤内孔。没有符合条件的闭合轮廓时，任务会明确失败并提示检查参数。
- 历史 Mask、透明零件和数据集不会自动修复。更新后应从第一步重新提取并选择新 Mask，再执行第二、三步。已缩小的零件即使再放大，也不能恢复源图细节。

回归验证（安装 `backend/requirements.txt` 后，在仓库根目录执行）：

```bash
python -m unittest discover -s backend/tests -v
```

## 输出目录

```text
storage/projects/{project_id}/
├─ uploads/
├─ dxfs/
├─ masks/
├─ parts/
├─ backgrounds/
├─ textures/
├─ synthetic/
│  └─ {task_id}/
│     ├─ images/
│     ├─ labels/
│     ├─ annotations/
│     └─ data.yaml
├─ previews/
└─ exports/
```

## 任务类型

- `extract_gen_masks`：GEN 文件解析并提取 mask
- `extract_edge_masks`：黑白边缘图提取 mask
- `masks_to_parts`：mask + texture 生成透明零件
- `generate_dataset`：合成图片并输出标签

## 后续建议

- 接入 GEN 解析流程。
- 增加登录和权限。
- 增加人工质量检查页面，叠加显示 HBB、OBB、COCO mask。
- 将本地存储切换为 NAS 或 MinIO。
