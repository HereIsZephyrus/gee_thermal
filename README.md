# GEE Thermal 地表温度与气象数据处理系统

[English](#english) | [中文](#中文)

! This Doc is archived by AI
---

<a name="english"></a>

## English

### Overview

A Python-based geospatial data processing system that leverages **Google Earth Engine (GEE)** to calculate land surface temperature (LST) and meteorological parameters. The system supports batch processing, persistent task monitoring, and automatic data download from Google Drive.

**Supported Data Sources:**
- **Landsat 4/5/7/8/9**: Land Surface Temperature (LST) using SMW algorithm (30m resolution)
- **MODIS MOD11A1**: Daily LST products (1km resolution)  
- **ERA5-Land**: Hourly meteorological data including wind, temperature, and radiation (11km resolution)

---

### Prerequisites

- Python 3.11+
- Google Cloud Platform account with GEE access
- Google Drive API enabled
- Conda (recommended for environment management)

---

### Installation

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd gee_thermal
```

#### 2. Create Conda Environment

```bash
conda env create -f environment.yml
conda activate gee
```

#### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
PROJECT_NAME=<your-gee-project-name>
DRIVE_FOLDER_ID=<your-google-drive-folder-id>
DRIVE_FOLDER_NAME=<your-drive-folder-name>
IMAGE_COLLECTION_PATH=<local-path-to-store-downloaded-images>
QUALITY_FILE_PATH=<local-path-for-quality-records-csv>
TRACKER_FOLDER_PATH=<local-path-for-task-tracker-files>
CREDENTIALS_FILE_PATH=<path-to-google-oauth-credentials>
```

---

### Google Authentication Setup

This project requires two types of Google authentication:

#### Step 1: Google Earth Engine Authentication

1. Open and run `gee_auth_script.ipynb` in Jupyter Notebook
2. Follow the prompts to authenticate with your Google account
3. Grant access to Google Earth Engine

#### Step 2: Google Drive API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google Drive API**
4. Create OAuth 2.0 credentials:
   - Navigate to **APIs & Services > Credentials**
   - Click **Create Credentials > OAuth client ID**
   - Select **Desktop application**
   - Download the JSON file
5. Rename the downloaded file to `client_secrets.json` and place it in the project root
6. Create the settings file:

```bash
cp settings.yaml.example settings.yaml
```

#### Step 3: First-time Authentication

On the first run, you will be prompted to authenticate via browser. The credentials will be saved to the path specified in `CREDENTIALS_FILE_PATH`.

---

### Usage

#### Calculate and Download LST Images (Landsat)

```bash
# Process a year range
python -m src lst <start_year> <end_year>

# Example: Process 2020-2023
python -m src lst 2020 2023

# Process specific dates from a CSV file
python -m src lst <start_year> <end_year> <check_days_file.csv>
```

#### Calculate and Download ERA5 Meteorological Data

```bash
python -m src era5 <check_days_file.csv>
```

#### Calculate and Download MODIS Thermal Data

```bash
python -m src thermal <check_days_file.csv>
```

#### Check Days File Format

The CSV file should have the following format:

```csv
year,month,day
2020,6,15
2020,7,20
2021,8,10
```

---

### Output Structure

```
IMAGE_COLLECTION_PATH/
├── wuhanshi-2020-01.tif
├── wuhanshi-2020-02.tif
├── ...
└── missing.txt          # Records months with no available data

TRACKER_FOLDER_PATH/
├── wuhanshi-2020-01.pkl  # Active task trackers
└── ...

QUALITY_FILE_PATH         # CSV with image quality metrics
```

---

### Troubleshooting

| Issue | Solution |
|-------|----------|
| GEE authentication failed | Re-run `gee_auth_script.ipynb` |
| Drive API quota exceeded | Wait 24 hours or request quota increase |
| Task stuck in RUNNING | Check GEE Task Manager in Code Editor |
| Download incomplete | Tracker will auto-retry on next run |

---

<a name="中文"></a>

## 中文

### 概述

这是一个基于 **Google Earth Engine (GEE)** 的地理空间数据处理系统，用于计算地表温度（LST）和气象参数。系统支持批量处理、持久化任务监控，以及从 Google Drive 自动下载数据。

**支持的数据源：**
- **Landsat 4/5/7/8/9**：使用 SMW 算法计算地表温度（30m 分辨率）
- **MODIS MOD11A1**：每日地表温度产品（1km 分辨率）
- **ERA5-Land**：逐小时气象数据，包括风速、温度和辐射（11km 分辨率）

---

### 环境要求

- Python 3.8+
- 具有 GEE 访问权限的 Google Cloud Platform 账户
- 已启用 Google Drive API
- Conda（推荐用于环境管理）

---

### 安装步骤

#### 1. 克隆仓库

```bash
git clone <repository-url>
cd gee_thermal
```

#### 2. 创建 Conda 环境

```bash
conda env create -f environment.yml
conda activate gee
```

#### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
PROJECT_NAME=<你的GEE项目名称>
DRIVE_FOLDER_ID=<你的Google Drive文件夹ID>
DRIVE_FOLDER_NAME=<你的Drive文件夹名称>
IMAGE_COLLECTION_PATH=<本地图像存储路径>
QUALITY_FILE_PATH=<质量记录CSV文件路径>
TRACKER_FOLDER_PATH=<任务追踪器文件夹路径>
CREDENTIALS_FILE_PATH=<Google OAuth凭证文件路径>
```

---

### Google 认证配置

本项目需要两种 Google 认证：

#### 步骤一：Google Earth Engine 认证

1. 在 Jupyter Notebook 中打开并运行 `gee_auth_script.ipynb`
2. 按照提示使用 Google 账户进行认证
3. 授予 Google Earth Engine 访问权限

#### 步骤二：Google Drive API 配置

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 **Google Drive API**
4. 创建 OAuth 2.0 凭证：
   - 导航至 **APIs & Services > Credentials**
   - 点击 **Create Credentials > OAuth client ID**
   - 选择 **Desktop application**
   - 下载 JSON 文件
5. 将下载的文件重命名为 `client_secrets.json` 并放置在项目根目录
6. 创建配置文件：

```bash
cp settings.yaml.example settings.yaml
```

#### 步骤三：首次认证

首次运行时，系统会提示通过浏览器进行认证。凭证将保存到 `CREDENTIALS_FILE_PATH` 指定的路径。

---

### 使用方法

#### 计算并下载 LST 图像（Landsat）

```bash
# 处理年份范围
python -m src lst <起始年份> <结束年份>

# 示例：处理 2020-2023 年
python -m src lst 2020 2023

# 使用 CSV 文件处理特定日期
python -m src lst <起始年份> <结束年份> <日期文件.csv>
```

#### 计算并下载 ERA5 气象数据

```bash
python -m src era5 <日期文件.csv>
```

#### 计算并下载 MODIS 热红外数据

```bash
python -m src thermal <日期文件.csv>
```

#### 日期文件格式

CSV 文件应包含以下格式：

```csv
year,month,day
2020,6,15
2020,7,20
2021,8,10
```

---

### 输出结构

```
IMAGE_COLLECTION_PATH/
├── wuhanshi-2020-01.tif
├── wuhanshi-2020-02.tif
├── ...
└── missing.txt          # 记录无可用数据的月份

TRACKER_FOLDER_PATH/
├── wuhanshi-2020-01.pkl  # 活跃的任务追踪器
└── ...

QUALITY_FILE_PATH         # 包含图像质量指标的 CSV 文件
```

---
## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
