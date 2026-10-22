# 使用指引配图来源

所有图片复用本地系统已有项目 `zsjd_2` 的真实素材和输出，未使用生成图片。
项目 ID：`7b94347c-7015-420d-a1de-da89c4b3faad`。

| 文件 | 现有资源 ID / 来源 | 用途 |
| --- | --- | --- |
| edge.webp | input: 4417444e-0c6c-467e-975d-d0b495ffdddc | 上传准备、提取 Mask 前 |
| mask.webp | mask: 327b6584-9e0a-45ca-b2db-737b8c59b88b | 提取结果、纹理填充前 |
| texture.webp | texture: 08fadbfd-e11c-4434-a673-c30d0d0725b2 | 上传准备、纹理填充 |
| part.webp | part: c2f59f8b-fe6a-4554-b77e-47da95bc186c | 纹理填充结果、合成前 |
| background.webp | background: b5b4f767-29e1-4764-a840-cc8690755390 | 上传准备、合成前 |
| dataset.webp | dataset: bbef5b0e-61ef-49d2-8906-eea5123dacfe，zsjd_2_20260817_00001.jpg | 合成结果、下载结果 |
| download.webp | 当前结果阅览页「批量下载」菜单截图（2026-10-22） | 图片与标签的下载入口 |

处理仅包括等比缩小、WebP 压缩与菜单截图裁切，保持 Mask 像素和零件透明通道。
合成图片的生成记录确认背景为 `161729.jpg`，与此处背景素材一致。
静态配图通过 Vite 打包，不依赖项目 ID、存储路径或项目是否被保留；不改变已有素材和任务。
